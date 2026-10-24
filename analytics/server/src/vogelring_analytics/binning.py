"""Klassenbildung (binning): numeric and date columns used as categories.

A raw value such as ``km_from_ringing = 139.21103`` is useless as a category. Whenever a numeric or date column is used
to split, colour or connect (dimension, color, facet, group_by, sankey/graph nodes, boxplot categories, timeline rows),
it is turned into classes:

* numeric – fixed ``width`` (0–10, 10–20, …), explicit ``edges`` (< 1, 1–5, 5–20, ≥ 20) or an automatic "nice" width
  for roughly ``count`` classes (default 8);
* date – ``year`` (default), ``month``, ``year_month`` or ``season``.

Two code paths share the labels: SQL aggregation (``bin_dimension`` yields a numeric bin key, ``bin_key_labels`` maps it
to German labels afterwards) and raw rows in pandas (``bin_values``). ``resolve_dimension`` lets a view address a
binnable column by its name wherever a predefined dimension key is accepted.
"""

from __future__ import annotations

import math
from typing import Any, Literal

import numpy as np
import pandas as pd
from pydantic import BaseModel, ConfigDict, Field, model_validator

from . import palette
from .sources import (
    _SEASON_ORDER,
    AGE_LABELS,
    DIMENSIONS,
    RINGING_AGE_LABELS,
    SEX_LABELS,
    Column,
    Dimension,
    Source,
    SourceError,
)

DatePart = Literal["year", "month", "year_month", "season"]
DATE_PART_LABELS: dict[str, str] = {"year": "Jahr", "month": "Monat", "year_month": "Jahr-Monat", "season": "Jahreszeit"}
SEASON_ORDER_LABELS: dict[int, str] = {1: "Nov–Jan", 2: "Feb–Mär", 3: "Apr–Jun", 4: "Jul–Okt"}
UNKNOWN = "unbekannt"
DEFAULT_COUNT = 8
NEEDS_BOUNDS = "__NEEDS_BOUNDS__"  # placeholder SQL until the automatic width is known
DEFAULT_UNITS: dict[str, str] = {"km_from_ringing": "km", "max_km": "km", "days_known": "Tage"}
# integer code columns shown with their German labels when used as categories (raw-row charts)
CODE_LABELS: dict[str, dict[int, str]] = {"age": AGE_LABELS, "sex": SEX_LABELS, "ringing_age": RINGING_AGE_LABELS}


class BinSpec(BaseModel):
    """How one column is divided into classes."""

    model_config = ConfigDict(extra="forbid")

    column: str = Field(description="Spalte der Datenquelle, z. B. km_from_ringing, max_km, sightings, days_known, first_sighting.")
    width: float | None = Field(None, gt=0, description="Feste Klassenbreite, z. B. 10 → 0–10, 10–20, …")
    edges: list[float] | None = Field(None, description="Eigene Klassengrenzen, aufsteigend, z. B. [1, 5, 20, 100] → < 1, 1–5, 5–20, 20–100, ≥ 100.")
    count: int | None = Field(None, ge=2, le=100, description="Ungefähre Anzahl Klassen bei automatischer Breite (Standard 8).")
    max: float | None = Field(None, description="Obergrenze: alles ab hier in einer offenen Klasse „≥ max“ (nur mit width; automatisch gesetzt, wenn wenige Ausreißer weit über dem Rest liegen).")
    date_part: DatePart | None = Field(None, description="Datumsspalten: year (Standard), month, year_month oder season.")
    unit: str | None = Field(None, max_length=12, description="Einheit in der Beschriftung, z. B. „km“ oder „Tage“.")

    @model_validator(mode="after")
    def _check(self) -> "BinSpec":
        if sum(x is not None for x in (self.width, self.edges, self.count)) > 1:
            raise ValueError("bins: nur eines von width, edges oder count angeben.")
        if self.edges is not None and (not self.edges or any(b <= a for a, b in zip(self.edges, self.edges[1:]))):
            raise ValueError("bins.edges müssen aufsteigend sein (mindestens eine Grenze).")
        if self.max is not None and self.edges is not None:
            raise ValueError("bins.max gilt nur für width/count, nicht für edges.")
        return self

    def cap(self) -> float | None:
        """The open top class starts here (aligned to the width grid)."""
        if self.max is None or not self.width:
            return None
        return math.floor(self.max / self.width) * self.width

    @property
    def is_auto(self) -> bool:
        return self.width is None and self.edges is None


# ---------------------------------------------------------------- helpers


def binnable(col: Column | None) -> bool:
    """Numeric measures, free numbers and dates – not coded integers like age/sex (those have labels)."""
    return col is not None and col.role != "coord" and (col.type in ("date", "number") or (col.type == "int" and col.role == "measure"))


def bin_columns(source: Source) -> list[Column]:
    return [c for c in source.columns if binnable(c)]


def fmt_de(x: float) -> str:
    """1234.5 → „1.234,5“, 10.0 → „10“."""
    x = float(x)
    if x.is_integer():
        return f"{int(x):,}".replace(",", ".")
    s = f"{x:,.2f}".replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return s.rstrip("0").rstrip(",")


def nice_width(lo: float, hi: float, count: int | None, integer: bool) -> float:
    """A round class width (1, 2, 2.5, 5 × 10^k) giving about ``count`` classes between lo and hi."""
    count = count or DEFAULT_COUNT
    span = hi - lo
    if not math.isfinite(span) or span <= 0:
        return 1.0
    if integer and span <= 12 and count >= span:
        return 1.0  # small counts: every value is its own class
    raw = span / count
    mag = 10 ** math.floor(math.log10(raw))
    candidates = [m * mag for m in (1, 2, 2.5, 5, 10) if not (integer and m == 2.5)]
    w = min(candidates, key=lambda c: abs(math.log(c / raw)))  # nearest round width
    return max(float(round(w)), 1.0) if integer else w


def _unit(unit: str | None) -> str:
    return f" {unit}" if unit else ""


def width_label(lo: float, width: float, integer: bool, unit: str | None, cap: float | None = None) -> str:
    if cap is not None and lo >= cap:
        return f"≥ {fmt_de(cap)}{_unit(unit)}"
    if integer and width == 1:
        return f"{fmt_de(lo)}{_unit(unit)}"
    hi = lo + width - 1 if integer else lo + width
    return f"{fmt_de(lo)}–{fmt_de(hi)}{_unit(unit)}"


def edge_label(index: int, edges: list[float], unit: str | None) -> str:
    if index <= 0:
        return f"< {fmt_de(edges[0])}{_unit(unit)}"
    if index >= len(edges):
        return f"≥ {fmt_de(edges[-1])}{_unit(unit)}"
    return f"{fmt_de(edges[index - 1])}–{fmt_de(edges[index])}{_unit(unit)}"


def with_width(spec: BinSpec, lo: float | None, hi: float | None, col: Column, p95: float | None = None) -> BinSpec:
    """Fill in the automatic width from the observed bounds (SQL path asks the DB for MIN/MAX/P95 first).

    Skewed data (a few far-away finds, most within a few km) gets its width from the 95th percentile and an open top
    class „≥ X“ for the tail, so the chart is not one tall bar followed by thirty empty classes."""
    if not spec.is_auto or col.type == "date":
        return spec
    if lo is None or hi is None:
        return spec.model_copy(update={"width": 1.0, "count": None})
    lo, hi = float(lo), float(hi)
    integer = col.type == "int"
    count = spec.count or DEFAULT_COUNT
    body = float(p95) if p95 is not None and lo < float(p95) < hi else hi
    w = nice_width(lo, body, spec.count, integer)
    update: dict[str, Any] = {"width": w, "count": None}
    if spec.max is None and (hi - lo) / w > count * 1.5:
        cap = math.floor(body / w) * w
        if cap <= math.floor(lo / w) * w:
            cap += w
        update["max"] = cap
    return spec.model_copy(update=update)


def unit_for(spec: BinSpec, col: Column) -> str | None:
    return spec.unit if spec.unit is not None else DEFAULT_UNITS.get(col.name)


def describe_bins(spec: BinSpec, col: Column) -> str:
    """Short German phrase for titles and notes."""
    if col.type == "date":
        return DATE_PART_LABELS[spec.date_part or "year"]
    unit = unit_for(spec, col)
    if spec.edges:
        return "Klassen " + ", ".join(edge_label(i, spec.edges, unit) for i in range(len(spec.edges) + 1))
    if spec.width:
        cap = spec.cap()
        return f"Klassen à {fmt_de(spec.width)}{_unit(unit)}" + (f", ab {fmt_de(cap)}{_unit(unit)} zusammengefasst" if cap is not None else "")
    return "Klassen"


def dimension_label(col: Column, spec: BinSpec) -> str:
    if col.type == "date":
        return f"{col.label} – {DATE_PART_LABELS[spec.date_part or 'year']}"
    if spec.width:
        return f"{col.label} ({describe_bins(spec, col)})"
    return f"{col.label} (Klassen)"


def _grid_expr(name: str, spec: BinSpec, col: Column) -> str:
    w = float(spec.width or 1.0)
    expr = name if (col.type == "int" and w == 1) else f"FLOOR(({name})::double precision / {w!r}) * {w!r}"
    cap = spec.cap()
    return f"LEAST({expr}, {float(cap)!r})" if cap is not None else expr


# ---------------------------------------------------------------- SQL path (aggregations)


def bin_dimension(source: Source, col: Column, spec: BinSpec) -> Dimension:
    """A Dimension whose SQL yields a *bin key* (lower bound, edge index, year …); label it with ``bin_key_labels``."""
    name, key = col.name, col.name
    label = dimension_label(col, spec)
    if col.type == "date":
        part = spec.date_part or "year"
        if part == "year":
            return Dimension(key, label, {source.key: f"EXTRACT(YEAR FROM {name})::int"}, {source.key: f"EXTRACT(YEAR FROM {name})"}, text=False)
        if part == "month":
            return Dimension(key, label, {source.key: f"EXTRACT(MONTH FROM {name})::int"}, {source.key: f"EXTRACT(MONTH FROM {name})"}, is_month=True, text=False)
        if part == "year_month":
            return Dimension(key, label, {source.key: f"TO_CHAR({name}, 'YYYY-MM')"}, {source.key: f"TO_CHAR({name}, 'YYYY-MM')"}, is_time=True)
        order = _SEASON_ORDER.format(date=name)
        return Dimension(key, label, {source.key: order}, {source.key: order}, text=False)
    if spec.edges:
        arr = ", ".join(repr(float(e)) for e in spec.edges)
        expr = f"width_bucket(({name})::double precision, ARRAY[{arr}])"
        return Dimension(key, label, {source.key: expr}, {source.key: expr}, text=False)
    if spec.width:
        expr = _grid_expr(name, spec, col)
        return Dimension(key, label, {source.key: expr}, {source.key: expr}, text=False)
    return Dimension(key, label, {source.key: NEEDS_BOUNDS}, {source.key: NEEDS_BOUNDS}, text=False)


def bin_key_labels(keys: pd.Series, spec: BinSpec, col: Column) -> tuple[pd.Series, list[str]]:
    """Map the SQL bin keys of ``bin_dimension`` to labels; returns (labels, label order). Month keys stay numeric."""
    if col.type == "date":
        part = spec.date_part or "year"
        if part == "month":
            return keys, []
        if part == "season":
            lab = keys.map(lambda k: SEASON_ORDER_LABELS.get(int(k), UNKNOWN) if pd.notna(k) else UNKNOWN)
            return lab, [SEASON_ORDER_LABELS[i] for i in (1, 2, 3, 4)] + [UNKNOWN]
        lab = keys.map(lambda k: UNKNOWN if pd.isna(k) else (str(int(k)) if isinstance(k, (int, float, np.integer, np.floating)) else str(k)))
        return lab, list(dict.fromkeys(lab.tolist()))
    unit = unit_for(spec, col)
    if spec.edges:
        edges = list(spec.edges)
        lab = keys.map(lambda k: UNKNOWN if pd.isna(k) else edge_label(int(k), edges, unit))
        order = [edge_label(i, edges, unit) for i in range(len(edges) + 1)] + [UNKNOWN]
        return lab, order
    w = float(spec.width or 1.0)
    integer = col.type == "int"
    cap = spec.cap()
    lab = keys.map(lambda k: UNKNOWN if pd.isna(k) else width_label(float(k), w, integer, unit, cap))
    numeric = pd.to_numeric(keys, errors="coerce")
    order = list(dict.fromkeys(width_label(float(k), w, integer, unit, cap) for k in sorted(set(numeric.dropna().tolist())))) + [UNKNOWN]
    return lab, order


def resolve_dimension(source: Source, key: str, bins: dict[str, BinSpec] | None = None) -> Dimension:
    """Predefined dimension key, or a binnable column of the source (with its BinSpec, default automatic)."""
    if key in DIMENSIONS:
        return DIMENSIONS[key]
    col = source.column(key)
    if not binnable(col):
        avail = [d.key for d in DIMENSIONS.values() if source.key in d.sources]
        cols = [c.name for c in bin_columns(source)]
        raise SourceError(
            f"Unbekannte Aufteilung '{key}' für „{source.label}“. Verfügbar: {', '.join(avail)}"
            + (f"; außerdem Zahlen-/Datumsspalten in Klassen: {', '.join(cols)}." if cols else ".")
        )
    assert col is not None
    spec = (bins or {}).get(key) or BinSpec(column=key)
    return bin_dimension(source, col, spec)


def is_bin_dimension(source: Source, key: str) -> bool:
    return key not in DIMENSIONS and binnable(source.column(key))


# ---------------------------------------------------------------- pandas path (raw rows)


def bin_values(values: pd.Series, spec: BinSpec, col: Column) -> tuple[pd.Series, list[str], BinSpec]:
    """Labels for raw values; returns (labels, label order, the BinSpec actually used – auto width filled in)."""
    if col.type == "date":
        dt = pd.to_datetime(values, errors="coerce")
        part = spec.date_part or "year"
        if part == "year":
            key = dt.dt.year
            lab = key.map(lambda y: UNKNOWN if pd.isna(y) else str(int(y)))
            order = [str(int(y)) for y in sorted(set(key.dropna().tolist()))]
        elif part == "month":
            key = dt.dt.month
            lab = key.map(lambda m: UNKNOWN if pd.isna(m) else palette.month_label(int(m)))
            order = [palette.month_label(m) for m in range(1, 13)]
        elif part == "year_month":
            lab = dt.dt.strftime("%Y-%m").fillna(UNKNOWN)
            order = sorted(set(lab.dropna().tolist()) - {UNKNOWN})
        else:
            season = dt.dt.month.map(lambda m: None if pd.isna(m) else (1 if int(m) in (11, 12, 1) else 2 if int(m) in (2, 3) else 3 if int(m) in (4, 5, 6) else 4))
            lab = season.map(lambda s: UNKNOWN if s is None or pd.isna(s) else SEASON_ORDER_LABELS[int(s)])
            order = [SEASON_ORDER_LABELS[i] for i in (1, 2, 3, 4)]
        return lab.astype(str), order + [UNKNOWN], spec
    v = pd.to_numeric(values, errors="coerce")
    unit = unit_for(spec, col)
    if spec.edges:
        edges = list(spec.edges)
        idx = pd.Series(np.searchsorted(np.asarray(edges, dtype=float), v.to_numpy(dtype=float), side="right"), index=v.index)
        lab = pd.Series(np.where(v.isna(), UNKNOWN, idx.map(lambda i: edge_label(int(i), edges, unit))), index=v.index)
        return lab.astype(str), [edge_label(i, edges, unit) for i in range(len(edges) + 1)] + [UNKNOWN], spec
    integer = col.type == "int"
    has = v.notna().any()
    used = spec if spec.width else with_width(spec, v.min() if has else None, v.max() if has else None, col, float(v.quantile(0.95, interpolation="lower")) if has else None)
    if used.is_auto:  # no finite values at all
        used = used.model_copy(update={"width": 1.0, "count": None})
    w = float(used.width or 1.0)
    cap = used.cap()
    lo = np.floor(v.to_numpy(dtype=float) / w) * w
    if cap is not None:
        lo = np.minimum(lo, cap)
    lo_s = pd.Series(lo, index=v.index)
    lab = pd.Series(np.where(v.isna(), UNKNOWN, lo_s.map(lambda x: width_label(float(x), w, integer, unit, cap) if pd.notna(x) else UNKNOWN)), index=v.index)
    order = list(dict.fromkeys(width_label(float(x), w, integer, unit, cap) for x in sorted(set(lo_s.dropna().tolist())))) + [UNKNOWN]
    return lab.astype(str), order, used


def code_labels(values: pd.Series, col: Column, source: Source) -> pd.Series | None:
    """German labels for coded integer columns (age, sex, ringing age) – None when the column has no code table."""
    table = RINGING_AGE_LABELS if col.name == source.ringing_age_column else CODE_LABELS.get(col.name)
    if table is None:
        return None
    return values.map(lambda v: UNKNOWN if pd.isna(v) else table.get(int(v), str(v)))


def bin_options(source: Source) -> list[dict[str, Any]]:
    """Extra entries for the dimension pickers: one per binnable column."""
    return [{"key": c.name, "label": f"{c.label} (in Klassen)", "kind": "bin", "type": c.type, "unit": DEFAULT_UNITS.get(c.name)} for c in bin_columns(source)]
