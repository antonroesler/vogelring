"""Typed dataset transformations (filter, group, pivot, join, derive) without SQL."""

from __future__ import annotations

import math
from typing import Annotated, Any, Literal, Union

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field

from . import palette
from .datasets import DatasetStore


class TransformError(ValueError):
    pass


class _Op(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FilterOp(_Op):
    op: Literal["filter"]
    column: str
    condition: Literal["==", "!=", ">", "<", ">=", "<=", "in", "not_in", "contains", "not_contains", "is_null", "not_null", "between"]
    value: Any = Field(None, description="Scalar, list (in/not_in/between) or text (contains, case-insensitive). Dates as 'YYYY-MM-DD'.")


class SelectOp(_Op):
    op: Literal["select"]
    columns: list[str]


class RenameOp(_Op):
    op: Literal["rename"]
    mapping: dict[str, str] = Field(..., description="old name → new name (German labels for charts/tables).")


class DeriveOp(_Op):
    op: Literal["derive"]
    column: str = Field(..., description="Name of the new column.")
    kind: Literal["year", "month", "month_name", "season", "weekday", "day_of_year", "days_between", "distance_km", "bucket", "ratio", "difference", "sum", "constant", "concat", "year_month"]
    source: str | None = Field(None, description="Input column (date for year/month/season/…, numeric for bucket).")
    other: str | None = Field(None, description="Second column (days_between, ratio, difference, sum, concat).")
    lat_column: str | None = None
    lon_column: str | None = None
    lat2_column: str | None = None
    lon2_column: str | None = None
    edges: list[float] | None = Field(None, description="bucket: bin edges, e.g. [0,1,5,20,100].")
    value: Any = Field(None, description="constant: the value.")
    scale: float = Field(1, description="ratio: multiply (100 for percent).")


class GroupOp(_Op):
    op: Literal["group"]
    by: list[str]
    aggregations: list["Agg"] = Field(..., min_length=1)


class Agg(_Op):
    column: str | None = Field(None, description="None with func=count counts rows.")
    func: Literal["count", "count_distinct", "sum", "mean", "median", "min", "max", "first", "last", "list"]
    as_: str | None = Field(None, alias="as", description="Output column name.")
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class SortOp(_Op):
    op: Literal["sort"]
    by: list[str]
    descending: bool = True


class HeadOp(_Op):
    op: Literal["head"]
    n: int = Field(..., ge=1, le=50000)


class DistinctOp(_Op):
    op: Literal["distinct"]
    columns: list[str] | None = None


class PivotOp(_Op):
    op: Literal["pivot"]
    index: str
    columns: str
    values: str | None = None
    func: Literal["count", "sum", "mean", "count_distinct", "max", "min"] = "sum"
    fill: float | None = 0


class JoinOp(_Op):
    op: Literal["join"]
    other_dataset_id: str
    on: list[str]
    how: Literal["inner", "left", "outer"] = "left"
    suffix: str = "_2"


class RankOp(_Op):
    op: Literal["rank"]
    column: str
    as_: str = Field("rang", alias="as")
    descending: bool = True
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


Op = Annotated[Union[FilterOp, SelectOp, RenameOp, DeriveOp, GroupOp, SortOp, HeadOp, DistinctOp, PivotOp, JoinOp, RankOp], Field(discriminator="op")]


def _col(df: pd.DataFrame, c: str | None, what: str = "column") -> str:
    if c is None or c not in df.columns:
        raise TransformError(f"{what} '{c}' not in dataset. Available: {', '.join(map(str, df.columns))}")
    return c


def _coerce_like(series: pd.Series, value: Any) -> Any:
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(value)
    if pd.api.types.is_numeric_dtype(series):
        return float(value)
    return value


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = (np.radians(pd.to_numeric(x, errors="coerce").astype(float)) for x in (lat1, lon1, lat2, lon2))
    a = np.sin((lat2 - lat1) / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    return 6371.0 * 2 * np.arcsin(np.sqrt(np.clip(a, 0, 1)))


def _apply_filter(df: pd.DataFrame, f: FilterOp) -> pd.DataFrame:
    c = _col(df, f.column)
    s = df[c]
    cond = f.condition
    if cond == "is_null":
        return df[s.isna()]
    if cond == "not_null":
        return df[s.notna()]
    if cond in ("in", "not_in"):
        vals = f.value if isinstance(f.value, list) else [f.value]
        vals = [_coerce_like(s, v) for v in vals]
        m = s.isin(vals)
        return df[m] if cond == "in" else df[~m]
    if cond in ("contains", "not_contains"):
        m = s.astype(str).str.contains(str(f.value), case=False, na=False, regex=False)
        return df[m] if cond == "contains" else df[~m]
    if cond == "between":
        if not isinstance(f.value, list) or len(f.value) != 2:
            raise TransformError("between needs value=[low, high].")
        lo, hi = (_coerce_like(s, v) for v in f.value)
        return df[(s >= lo) & (s <= hi)]
    v = _coerce_like(s, f.value)
    ops = {"==": s == v, "!=": s != v, ">": s > v, "<": s < v, ">=": s >= v, "<=": s <= v}
    return df[ops[cond]]


def _derive(df: pd.DataFrame, d: DeriveOp) -> pd.DataFrame:
    df = df.copy()
    k = d.kind
    if k in ("year", "month", "month_name", "season", "weekday", "day_of_year", "year_month"):
        src = _col(df, d.source, "source")
        t = pd.to_datetime(df[src], errors="coerce")
        if k == "year":
            df[d.column] = t.dt.year.astype("Int64")
        elif k == "month":
            df[d.column] = t.dt.month.astype("Int64")
        elif k == "month_name":
            df[d.column] = t.dt.month.map(lambda m: palette.MONTHS_DE[int(m) - 1] if pd.notna(m) else None)
        elif k == "season":
            df[d.column] = t.dt.month.map(lambda m: palette.season_for_month(int(m))["label"] if pd.notna(m) else None)
        elif k == "weekday":
            df[d.column] = t.dt.weekday.map(lambda w: ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"][int(w)] if pd.notna(w) else None)
        elif k == "day_of_year":
            df[d.column] = t.dt.dayofyear.astype("Int64")
        else:
            df[d.column] = t.dt.strftime("%Y-%m")
        return df
    if k == "days_between":
        a, b = _col(df, d.source, "source"), _col(df, d.other, "other")
        df[d.column] = (pd.to_datetime(df[b], errors="coerce") - pd.to_datetime(df[a], errors="coerce")).dt.days
        return df
    if k == "distance_km":
        for c in (d.lat_column, d.lon_column, d.lat2_column, d.lon2_column):
            _col(df, c, "coordinate column")
        df[d.column] = haversine_km(df[d.lat_column], df[d.lon_column], df[d.lat2_column], df[d.lon2_column]).round(2)
        return df
    if k == "bucket":
        src = _col(df, d.source, "source")
        if not d.edges or len(d.edges) < 2:
            raise TransformError("bucket needs edges, e.g. [0, 1, 5, 20, 100].")
        edges = list(d.edges) + [math.inf]
        labels = [f"{_n(edges[i])}–{_n(edges[i + 1])}" if edges[i + 1] != math.inf else f"> {_n(edges[i])}" for i in range(len(edges) - 1)]
        df[d.column] = pd.cut(pd.to_numeric(df[src], errors="coerce"), bins=edges, labels=labels, right=False, include_lowest=True).astype(str).replace("nan", None)
        return df
    if k in ("ratio", "difference", "sum"):
        a, b = _col(df, d.source, "source"), _col(df, d.other, "other")
        x, y = pd.to_numeric(df[a], errors="coerce"), pd.to_numeric(df[b], errors="coerce")
        df[d.column] = (x / y.replace(0, np.nan) * d.scale).round(2) if k == "ratio" else (x - y if k == "difference" else x + y)
        return df
    if k == "constant":
        df[d.column] = d.value
        return df
    if k == "concat":
        a, b = _col(df, d.source, "source"), _col(df, d.other, "other")
        df[d.column] = df[a].astype(str) + " " + df[b].astype(str)
        return df
    raise TransformError(f"Unknown derive kind {k}")


def _n(v: float) -> str:
    return str(int(v)) if float(v).is_integer() else str(v)


def _group(df: pd.DataFrame, g: GroupOp) -> pd.DataFrame:
    for c in g.by:
        _col(df, c, "group column")
    named: dict[str, tuple] = {}
    for a in g.aggregations:
        if a.func == "count" and a.column is None:
            named[a.as_ or "Anzahl"] = (g.by[0], "size")
            continue
        c = _col(df, a.column, "aggregation column")
        func = {"count": "count", "count_distinct": "nunique", "sum": "sum", "mean": "mean", "median": "median", "min": "min", "max": "max", "first": "first", "last": "last", "list": lambda s: "; ".join(dict.fromkeys(map(str, s.dropna())))}[a.func]
        default_name = {"count": f"Anzahl {c}", "count_distinct": f"Anzahl {c}", "sum": f"Summe {c}", "mean": f"Mittel {c}", "median": f"Median {c}", "min": f"Min {c}", "max": f"Max {c}", "first": c, "last": c, "list": c}[a.func]
        named[a.as_ or default_name] = (c, func)
    out = df.groupby(g.by, dropna=False).agg(**named).reset_index()
    for col in out.columns:
        if pd.api.types.is_float_dtype(out[col]):
            out[col] = out[col].round(3)
    return out


def apply_ops(df: pd.DataFrame, ops: list[Op], store: DatasetStore) -> pd.DataFrame:
    for op in ops:
        if isinstance(op, FilterOp):
            df = _apply_filter(df, op)
        elif isinstance(op, SelectOp):
            df = df[[_col(df, c) for c in op.columns]]
        elif isinstance(op, RenameOp):
            for c in op.mapping:
                _col(df, c)
            df = df.rename(columns=op.mapping)
        elif isinstance(op, DeriveOp):
            df = _derive(df, op)
        elif isinstance(op, GroupOp):
            df = _group(df, op)
        elif isinstance(op, SortOp):
            df = df.sort_values([_col(df, c) for c in op.by], ascending=not op.descending, kind="stable")
        elif isinstance(op, HeadOp):
            df = df.head(op.n)
        elif isinstance(op, DistinctOp):
            df = df.drop_duplicates(subset=[_col(df, c) for c in op.columns] if op.columns else None)
        elif isinstance(op, PivotOp):
            _col(df, op.index); _col(df, op.columns)
            if op.values is None or op.func in ("count", "count_distinct") and op.values is None:
                wide = df.groupby([op.index, op.columns]).size().unstack(op.columns)
            else:
                _col(df, op.values)
                f = {"count": "count", "count_distinct": "nunique", "sum": "sum", "mean": "mean", "max": "max", "min": "min"}[op.func]
                wide = df.pivot_table(index=op.index, columns=op.columns, values=op.values, aggfunc=f)
            if op.fill is not None:
                wide = wide.fillna(op.fill)
            wide.columns = [str(c) for c in wide.columns]
            df = wide.reset_index()
        elif isinstance(op, JoinOp):
            try:
                other = store.load(op.other_dataset_id)
            except KeyError as exc:
                raise TransformError(str(exc)) from exc
            for c in op.on:
                _col(df, c, "join column"); _col(other, c, "join column (other)")
            df = df.merge(other, on=op.on, how=op.how, suffixes=("", op.suffix))
        elif isinstance(op, RankOp):
            c = _col(df, op.column)
            df = df.copy()
            df[op.as_] = df[c].rank(ascending=not op.descending, method="min").astype("Int64")
        if len(df) > 200_000:
            raise TransformError("Result too large (> 200 000 rows). Aggregate first.")
    return df.reset_index(drop=True)


def describe_ops(ops: list[Op]) -> str:
    """Plain-German one-liner of what was done (for the dataset description)."""
    parts = []
    for op in ops:
        if isinstance(op, FilterOp):
            parts.append(f"gefiltert nach {op.column} {op.condition} {op.value if op.value is not None else ''}".strip())
        elif isinstance(op, GroupOp):
            parts.append("zusammengefasst nach " + ", ".join(op.by))
        elif isinstance(op, DeriveOp):
            parts.append(f"Spalte {op.column} berechnet ({op.kind})")
        elif isinstance(op, PivotOp):
            parts.append(f"Kreuztabelle {op.index} × {op.columns}")
        elif isinstance(op, JoinOp):
            parts.append("mit zweitem Datensatz verknüpft über " + ", ".join(op.on))
        elif isinstance(op, HeadOp):
            parts.append(f"auf {op.n} Zeilen begrenzt")
        elif isinstance(op, SortOp):
            parts.append("sortiert nach " + ", ".join(op.by))
        elif isinstance(op, DistinctOp):
            parts.append("Duplikate entfernt")
        elif isinstance(op, RankOp):
            parts.append(f"Rang nach {op.column}")
    return "; ".join(parts)
