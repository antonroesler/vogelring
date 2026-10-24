"""Turn a ChartSpec + dataset into a renderer-agnostic chart model (JSON for the template)."""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from . import palette
from .specs import ChartSpec


class ChartBuildError(ValueError):
    pass


def _require(df: pd.DataFrame, col: str | None, what: str) -> None:
    if col is None:
        return
    if col not in df.columns:
        raise ChartBuildError(f"Column '{col}' ({what}) not in dataset. Available: {', '.join(map(str, df.columns))}")


def _fmt_num(v: Any) -> Any:
    if v is None or (isinstance(v, float) and np.isnan(v)):
        return None
    if isinstance(v, (np.integer,)):
        return int(v)
    if isinstance(v, (np.floating, float)):
        f = float(v)
        return int(f) if f.is_integer() else round(f, 4)
    return v


def _cat_label(v: Any, month_axis: bool) -> str:
    if month_axis:
        return palette.month_label(v)
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d")
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def _aggregate(df: pd.DataFrame, spec: ChartSpec) -> pd.DataFrame:
    """Return a wide frame: index = x categories, columns = series names."""
    x = spec.x
    if spec.aggregate == "count":
        if spec.series_column:
            wide = df.groupby([x, spec.series_column], dropna=False).size().unstack(spec.series_column).fillna(0)
        else:
            wide = df.groupby(x, dropna=False).size().to_frame("Anzahl")
        return wide

    y_cols = [spec.y] if isinstance(spec.y, str) else list(spec.y or [])
    for c in y_cols:
        _require(df, c, "y")

    if spec.aggregate == "count_distinct":
        if spec.series_column:
            wide = df.groupby([x, spec.series_column], dropna=False)[y_cols[0]].nunique().unstack(spec.series_column).fillna(0)
        else:
            wide = df.groupby(x, dropna=False)[y_cols[0]].nunique().to_frame(f"Anzahl {y_cols[0]}")
        return wide

    func = {"sum": "sum", "mean": "mean", "none": "first"}[spec.aggregate]
    if spec.series_column:
        if len(y_cols) != 1:
            raise ChartBuildError("With series_column exactly one y column is needed.")
        has_dupes = df.duplicated(subset=[x, spec.series_column]).any()
        if spec.aggregate == "none" and has_dupes:
            func = "sum"
        wide = df.pivot_table(index=x, columns=spec.series_column, values=y_cols[0], aggfunc=func, dropna=False).fillna(0)
        return wide

    has_dupes = df.duplicated(subset=[x]).any()
    if spec.aggregate == "none" and has_dupes:
        func = "sum"
    wide = df.groupby(x, dropna=False)[y_cols].agg(func)
    return wide


def build_chart_model(spec: ChartSpec, df: pd.DataFrame) -> tuple[dict[str, Any], dict[str, Any]]:
    _require(df, spec.x, "x")
    _require(df, spec.series_column, "series_column")
    notes: list[str] = []
    model: dict[str, Any] = {
        "kind": spec.kind,
        "title": spec.title,
        "subtitle": spec.subtitle,
        "footnote": spec.footnote,
        "legend_title": spec.legend_title,
        "width": spec.width,
        "height": spec.height,
        "horizontal": spec.horizontal,
        "show_values": spec.show_values,
        "show_totals": spec.show_totals,
        "x_axis": spec.x_axis.model_dump(),
        "y_axis": spec.y_axis.model_dump(),
        "annotations": [],
    }

    if spec.kind == "histogram":
        vals = pd.to_numeric(df[spec.x], errors="coerce").dropna()
        counts, edges = np.histogram(vals, bins=spec.bins or 20)
        cats = [f"{_fmt_num(edges[i])}–{_fmt_num(edges[i + 1])}" for i in range(len(counts))]
        color = (spec.colors or {}).get("Anzahl") or palette.THEME["secondary"]
        model.update({"kind": "bar", "categories": cats, "series": [{"name": "Anzahl", "data": [int(c) for c in counts], "color": color}]})
        summary = {"rows": int(len(vals)), "bins": len(counts), "min": _fmt_num(vals.min()) if len(vals) else None, "max": _fmt_num(vals.max()) if len(vals) else None}
        return model, summary

    if spec.kind == "heatmap":
        _require(df, spec.heat_value, "heat_value")
        wide = df.pivot_table(index=spec.series_column, columns=spec.x, values=spec.heat_value, aggfunc="sum" if spec.aggregate in ("none", "sum") else spec.aggregate, dropna=False).fillna(0)
        if spec.month_axis:
            wide = wide.reindex(columns=range(1, 13), fill_value=0)
        cols = [_cat_label(c, spec.month_axis) for c in wide.columns]
        rows = [str(r) for r in wide.index]
        values = [[ci, ri, _fmt_num(wide.iat[ri, ci])] for ri in range(len(rows)) for ci in range(len(cols))]
        model.update({"categories": cols, "rows": rows, "heat": {"values": values, "min": _fmt_num(wide.values.min()) if wide.size else 0, "max": _fmt_num(wide.values.max()) if wide.size else 0}, "series": []})
        return model, {"rows": len(rows), "columns": len(cols), "max": model["heat"]["max"]}

    if spec.kind in _SPECIAL:
        return _SPECIAL[spec.kind](spec, df, model, notes)

    if spec.facet_column:
        return _facets(spec, df, model, notes)

    wide = _aggregate(df, spec)

    if spec.month_axis:
        idx = pd.to_numeric(pd.Series(wide.index), errors="coerce")
        wide.index = idx.values
        wide = wide.reindex(range(1, 13), fill_value=0)

    # Sorting / limiting by total
    totals = wide.sum(axis=1, numeric_only=True)
    if spec.sort in ("asc", "desc"):
        wide = wide.loc[totals.sort_values(ascending=spec.sort == "asc").index]
    elif spec.sort == "x":
        wide = wide.sort_index()
    if spec.limit:
        wide = wide.head(spec.limit)
        notes.append(f"Auf die ersten {spec.limit} Kategorien begrenzt.")

    series_names = [str(c) for c in wide.columns]
    if spec.stack_order:
        known = [s for s in spec.stack_order if s in series_names]
        missing = [s for s in spec.stack_order if s not in series_names]
        if missing:
            notes.append(f"stack_order enthält unbekannte Serien: {', '.join(missing)}")
        rest = [s for s in series_names if s not in known]
        series_names = known + rest
        wide = wide[[c for c in wide.columns if str(c) in series_names]]
        wide = wide[sorted(wide.columns, key=lambda c: series_names.index(str(c)))]

    if spec.color_by == "species":
        colors = {s: (spec.colors or {}).get(s) or palette.species_color(s) for s in series_names}
    elif spec.color_by == "season":
        season_map = {s["label"]: s["color"] for s in palette.SEASONS}
        colors = {s: (spec.colors or {}).get(s) or season_map.get(s) or palette.CATEGORY_PALETTE[i % 20] for i, s in enumerate(series_names)}
    else:
        colors = palette.category_colors(series_names, spec.colors)

    categories = [_cat_label(v, spec.month_axis) for v in wide.index]
    stack = spec.stack if spec.stack is not None else spec.kind in ("stacked_bar", "area")

    if spec.kind == "pie":
        if len(series_names) != 1:
            raise ChartBuildError("pie needs exactly one value column.")
        col = wide.columns[0]
        pie_colors = palette.category_colors(categories, spec.colors) if spec.color_by != "species" else {c: palette.species_color(c) for c in categories}
        model.update({"pie": [{"name": c, "value": _fmt_num(v), "color": pie_colors[c]} for c, v in zip(categories, wide[col].tolist())], "series": [], "categories": categories})
        return model, {"slices": len(categories), "total": _fmt_num(wide[col].sum()), "notes": notes}

    if spec.kind == "scatter":
        # numeric x; one series per series_column value (or single)
        xs = pd.to_numeric(df[spec.x], errors="coerce")
        y_col = spec.y if isinstance(spec.y, str) else (spec.y or [None])[0]
        _require(df, y_col, "y")
        ys = pd.to_numeric(df[y_col], errors="coerce")
        groups = df[spec.series_column].astype(str) if spec.series_column else pd.Series(["Werte"] * len(df), index=df.index)
        names = list(dict.fromkeys(groups.tolist()))
        colors = palette.category_colors(names, spec.colors)
        series = []
        for name in names:
            mask = (groups == name) & xs.notna() & ys.notna()
            series.append({"name": name, "data": [[_fmt_num(a), _fmt_num(b)] for a, b in zip(xs[mask], ys[mask])], "color": colors[name]})
        model.update({"categories": None, "series": series})
        return model, {"series": {s["name"]: len(s["data"]) for s in series}, "notes": notes}

    series = []
    for name, col in zip(series_names, wide.columns):
        data = [_fmt_num(v) for v in wide[col].tolist()]
        series.append({"name": name, "data": data, "color": colors[name], "stack": "total" if stack else None})
    model.update({"categories": categories, "series": series, "stack": stack})
    if spec.show_totals and stack:
        model["totals"] = [_fmt_num(v) for v in wide.sum(axis=1, numeric_only=True).tolist()]

    for a in spec.annotations:
        ann = {"kind": a.kind, "label": a.label, "color": a.color}
        ann["from"] = _cat_label(a.from_, spec.month_axis) if isinstance(a.from_, str) or spec.month_axis else a.from_
        ann["to"] = (_cat_label(a.to, spec.month_axis) if (isinstance(a.to, str) or spec.month_axis) else a.to) if a.to is not None else None
        model["annotations"].append(ann)

    summary = {
        "categories": len(categories),
        "series_totals": {s["name"]: _fmt_num(sum(v for v in s["data"] if v is not None)) for s in series},
        "grand_total": _fmt_num(float(wide.sum(numeric_only=True).sum())),
        "notes": notes,
    }
    if len(categories) <= 40:
        summary["category_totals"] = {c: _fmt_num(t) for c, t in zip(categories, wide.sum(axis=1, numeric_only=True).tolist())}
    return model, summary


# ---------------------------------------------------------------- additional kinds


def _series_colors(spec: ChartSpec, names: list[str]) -> dict[str, str]:
    if spec.color_by == "species":
        return {s: (spec.colors or {}).get(s) or palette.species_color(s) for s in names}
    if spec.color_by == "season":
        season_map = {s["label"]: s["color"] for s in palette.SEASONS}
        return {s: (spec.colors or {}).get(s) or season_map.get(s) or palette.CATEGORY_PALETTE[i % 20] for i, s in enumerate(names)}
    return palette.category_colors(names, spec.colors)


def _dates(df: pd.DataFrame, col: str) -> pd.Series:
    return pd.to_datetime(df[col], errors="coerce")


def _timeline(spec: ChartSpec, df: pd.DataFrame, model: dict, notes: list[str]) -> tuple[dict, dict]:
    """Life-history chart: one row per series_column value, dots (or ranges) along a time axis."""
    _require(df, spec.end_column, "end_column")
    _require(df, spec.color_column, "color_column")
    d = df.copy()
    d["__t"] = _dates(d, spec.x)
    d = d[d["__t"].notna()]
    if d.empty:
        raise ChartBuildError(f"No valid dates in '{spec.x}'.")
    d["__row"] = d[spec.series_column].map(lambda v: _cat_label(v, False))
    # order rows by first date (or by stack_order)
    first = d.groupby("__row")["__t"].min().sort_values()
    rows = list(first.index)
    if spec.stack_order:
        rows = [r for r in spec.stack_order if r in rows] + [r for r in rows if r not in spec.stack_order]
    if spec.limit and len(rows) > spec.limit:
        notes.append(f"Auf {spec.limit} Zeilen begrenzt (von {len(rows)}).")
        rows = rows[: spec.limit]
        d = d[d["__row"].isin(rows)]
    if spec.color_column:
        d["__cls"] = d[spec.color_column].map(lambda v: _cat_label(v, False) or "unbekannt")
        classes = list(d["__cls"].value_counts().index)
        cmap = _series_colors(spec, classes)
    elif spec.color_by == "season":
        seas = d["__t"].dt.month.map(lambda m: palette.season_for_month(m)["label"])
        d["__cls"] = seas
        classes = [x["label"] for x in palette.SEASONS if (seas == x["label"]).any()]
        cmap = {x["label"]: x["color"] for x in palette.SEASONS}
    else:
        d["__cls"] = "Sichtung"
        classes = ["Sichtung"]
        cmap = {"Sichtung": (spec.colors or {}).get("Sichtung") or palette.THEME["secondary"]}
    row_idx = {r: i for i, r in enumerate(rows)}
    tooltip_cols = [c for c in ("place", "species", "status", "age", "comment") if c in d.columns]
    points = []
    for _, r in d.iterrows():
        item = {"row": row_idx[r["__row"]], "t": r["__t"].strftime("%Y-%m-%d"), "cls": r["__cls"], "color": cmap.get(r["__cls"], "#9AA5AD")}
        if spec.end_column and pd.notna(r.get(spec.end_column)):
            item["end"] = pd.Timestamp(r[spec.end_column]).strftime("%Y-%m-%d")
        tip = [f"<b>{r['__row']}</b>", r["__t"].strftime("%d.%m.%Y")]
        tip += [f"{c}: {_cat_label(r[c], False)}" for c in tooltip_cols if pd.notna(r[c]) and str(r[c]) != ""]
        item["tip"] = "<br>".join(tip)
        points.append(item)
    model.update({
        "kind": "timeline",
        "rows": rows,
        "timeline": {"points": points, "classes": [{"name": c, "color": cmap[c]} for c in classes],
                      "min": d["__t"].min().strftime("%Y-%m-%d"), "max": d["__t"].max().strftime("%Y-%m-%d")},
        "series": [],
    })
    span_days = int((d["__t"].max() - d["__t"].min()).days)
    summary = {"rows": len(rows), "points": len(points), "from": model["timeline"]["min"], "to": model["timeline"]["max"], "span_days": span_days, "classes": {c: int((d["__cls"] == c).sum()) for c in classes}, "notes": notes}
    return model, summary


def _calendar(spec: ChartSpec, df: pd.DataFrame, model: dict, notes: list[str]) -> tuple[dict, dict]:
    """Calendar heatmap: one calendar per year, cell value = count/sum per day."""
    d = df.copy()
    d["__t"] = _dates(d, spec.x).dt.normalize()
    d = d[d["__t"].notna()]
    if d.empty:
        raise ChartBuildError(f"No valid dates in '{spec.x}'.")
    y_col = spec.y if isinstance(spec.y, str) else (spec.y or [None])[0]
    if spec.aggregate == "count_distinct":
        _require(d, y_col, "y")
        daily = d.groupby("__t")[y_col].nunique()
        value_label = f"Anzahl {y_col}"
    elif spec.aggregate in ("sum", "mean", "none") and y_col:
        _require(d, y_col, "y")
        daily = d.groupby("__t")[y_col].agg("sum" if spec.aggregate in ("sum", "none") else "mean")
        value_label = y_col
    else:
        daily = d.groupby("__t").size()
        value_label = "Anzahl"
    years = sorted(daily.index.year.unique().tolist())
    if len(years) > 8:
        notes.append(f"Nur die letzten 8 von {len(years)} Jahren gezeigt.")
        years = years[-8:]
        daily = daily[daily.index.year.isin(years)]
    values = [[t.strftime("%Y-%m-%d"), _fmt_num(v)] for t, v in daily.items()]
    model.update({"kind": "calendar", "calendar": {"years": years, "values": values, "max": _fmt_num(daily.max()), "value_label": value_label}, "series": []})
    model["height"] = max(spec.height, 120 + 175 * len(years)) if spec.height <= 700 else spec.height
    busiest = daily.idxmax()
    summary = {"years": years, "days_with_data": int(len(daily)), "total": _fmt_num(daily.sum()), "busiest_day": busiest.strftime("%Y-%m-%d"), "busiest_value": _fmt_num(daily.max()), "notes": notes}
    return model, summary


def _edges(spec: ChartSpec, df: pd.DataFrame) -> pd.DataFrame:
    _require(df, spec.source_column, "source_column")
    _require(df, spec.target_column, "target_column")
    y_col = spec.y if isinstance(spec.y, str) else (spec.y or [None])[0]
    d = df[[spec.source_column, spec.target_column] + ([y_col] if y_col else [])].copy()
    d.columns = ["source", "target"] + (["w"] if y_col else [])
    d = d.dropna(subset=["source", "target"])
    d["source"] = d["source"].map(lambda v: _cat_label(v, False))
    d["target"] = d["target"].map(lambda v: _cat_label(v, False))
    if y_col:
        d["w"] = pd.to_numeric(d["w"], errors="coerce").fillna(0)
        e = d.groupby(["source", "target"], as_index=False)["w"].sum()
    else:
        e = d.groupby(["source", "target"], as_index=False).size().rename(columns={"size": "w"})
    e = e[e["w"] > 0]
    if e.empty:
        raise ChartBuildError("No edges (source/target pairs) in the dataset.")
    return e


def _has_cycle(e: pd.DataFrame) -> bool:
    adj: dict[str, set[str]] = {}
    for s_, t_ in zip(e["source"], e["target"]):
        adj.setdefault(s_, set()).add(t_)
    state: dict[str, int] = {}

    def visit(n: str) -> bool:
        st = state.get(n, 0)
        if st == 1:
            return True
        if st == 2:
            return False
        state[n] = 1
        if any(visit(m) for m in adj.get(n, ())):
            return True
        state[n] = 2
        return False

    return any(visit(n) for n in list(adj))


def _sankey(spec: ChartSpec, df: pd.DataFrame, model: dict, notes: list[str]) -> tuple[dict, dict]:
    e = _edges(spec, df)
    strength = pd.concat([e.groupby("source")["w"].sum(), e.groupby("target")["w"].sum()]).groupby(level=0).sum().sort_values(ascending=False)
    if len(strength) > spec.max_nodes:
        keep = set(strength.head(spec.max_nodes).index)
        before = len(e)
        e = e[e["source"].isin(keep) & e["target"].isin(keep)]
        notes.append(f"Auf die {spec.max_nodes} stärksten Knoten begrenzt ({before - len(e)} Verbindungen ausgeblendet).")
    bipartite = _has_cycle(e)
    if bipartite:
        e = e.assign(target=e["target"] + "\u200b")
        notes.append("Quelle und Ziel werden als getrennte Spalten gezeigt (es gibt Hin- und Rückbewegungen).")
    nodes = list(dict.fromkeys(e["source"].tolist() + e["target"].tolist()))
    cmap = _series_colors(spec, [n.rstrip("\u200b") for n in nodes])
    model.update({
        "kind": "sankey",
        "sankey": {
            "nodes": [{"name": n, "label": n.rstrip("\u200b"), "color": cmap[n.rstrip("\u200b")]} for n in nodes],
            "links": [{"source": r.source, "target": r.target, "value": _fmt_num(r.w)} for r in e.itertuples()],
        },
        "series": [],
    })
    top = e.sort_values("w", ascending=False).head(5)
    summary = {"nodes": len(nodes), "links": int(len(e)), "total": _fmt_num(e["w"].sum()), "strongest": [f"{r.source} → {r.target.rstrip(chr(0x200b))}: {_fmt_num(r.w)}" for r in top.itertuples()], "notes": notes}
    return model, summary


def _graph(spec: ChartSpec, df: pd.DataFrame, model: dict, notes: list[str]) -> tuple[dict, dict]:
    _require(df, spec.edge_label_column, "edge_label_column")
    _require(df, spec.series_column, "series_column")
    e = _edges(spec, df)
    labels: dict[tuple[str, str], str] = {}
    if spec.edge_label_column or spec.series_column:
        col = spec.edge_label_column or spec.series_column
        for _, r in df.dropna(subset=[spec.source_column, spec.target_column]).iterrows():
            key = (_cat_label(r[spec.source_column], False), _cat_label(r[spec.target_column], False))
            labels.setdefault(key, _cat_label(r[col], False))
    degree = pd.concat([e.groupby("source")["w"].sum(), e.groupby("target")["w"].sum()]).groupby(level=0).sum().sort_values(ascending=False)
    if len(degree) > spec.max_nodes:
        keep = set(degree.head(spec.max_nodes).index)
        e = e[e["source"].isin(keep) & e["target"].isin(keep)]
        notes.append(f"Auf die {spec.max_nodes} am stärksten vernetzten Knoten begrenzt.")
        degree = degree[degree.index.isin(keep)]
    # connected components → categories/colours
    parent: dict[str, str] = {n: n for n in degree.index}

    def find(x: str) -> str:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for r in e.itertuples():
        a, b = find(r.source), find(r.target)
        if a != b:
            parent[a] = b
    comps: dict[str, int] = {}
    for n in degree.index:
        root = find(n)
        comps.setdefault(root, len(comps))
    edge_types = sorted({v for v in labels.values()}) if labels else []
    type_colors = palette.category_colors(edge_types, spec.colors) if edge_types else {}
    n_comp = len(comps)
    comp_colors = [palette.CATEGORY_PALETTE[i % len(palette.CATEGORY_PALETTE)] for i in range(n_comp)]
    nodes = [{"name": n, "value": _fmt_num(v), "category": comps[find(n)], "symbolSize": float(10 + 22 * (v / degree.max()) ** 0.5)} for n, v in degree.items()]
    links = []
    for r in e.itertuples():
        lab = labels.get((r.source, r.target)) or labels.get((r.target, r.source))
        links.append({"source": r.source, "target": r.target, "value": _fmt_num(r.w), "label": lab, "color": type_colors.get(lab) if lab else None})
    model.update({
        "kind": "graph",
        "graph": {"nodes": nodes, "links": links, "categories": [{"name": f"Gruppe {i + 1}", "color": comp_colors[i]} for i in range(n_comp)],
                   "edge_types": [{"name": t, "color": type_colors[t]} for t in edge_types], "directed": spec.kind == "graph" and bool(spec.edge_label_column)},
        "series": [],
    })
    summary = {"nodes": len(nodes), "edges": len(links), "components": n_comp, "most_connected": [f"{n}: {_fmt_num(v)}" for n, v in degree.head(5).items()], "notes": notes}
    return model, summary


def _boxplot(spec: ChartSpec, df: pd.DataFrame, model: dict, notes: list[str]) -> tuple[dict, dict]:
    y_col = spec.y if isinstance(spec.y, str) else (spec.y or [None])[0]
    _require(df, y_col, "y")
    d = df[[spec.x, y_col]].copy()
    d[y_col] = pd.to_numeric(d[y_col], errors="coerce")
    d = d.dropna()
    if d.empty:
        raise ChartBuildError("No numeric values for the boxplot.")
    d["__cat"] = d[spec.x].map(lambda v: _cat_label(v, spec.month_axis))
    cats = list(d.groupby("__cat")[y_col].median().sort_values(ascending=spec.sort != "desc").index) if spec.sort in ("asc", "desc") else list(dict.fromkeys(d["__cat"]))
    if spec.month_axis:
        cats = [m for m in palette.MONTHS_DE if m in set(cats)]
    if spec.limit:
        cats = cats[: spec.limit]
    boxes, outliers, stats = [], [], {}
    for i, c in enumerate(cats):
        v = d.loc[d["__cat"] == c, y_col].sort_values()
        q1, med, q3 = (float(v.quantile(q)) for q in (0.25, 0.5, 0.75))
        iqr = q3 - q1
        lo, hi = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        inl = v[(v >= lo) & (v <= hi)]
        boxes.append([_fmt_num(inl.min() if len(inl) else v.min()), _fmt_num(q1), _fmt_num(med), _fmt_num(q3), _fmt_num(inl.max() if len(inl) else v.max())])
        outliers += [[i, _fmt_num(o)] for o in v[(v < lo) | (v > hi)].head(50)]
        stats[c] = {"n": int(len(v)), "median": _fmt_num(med), "q1": _fmt_num(q1), "q3": _fmt_num(q3)}
    color = (spec.colors or {}).get(y_col) or palette.THEME["secondary"]
    model.update({"kind": "boxplot", "categories": cats, "box": {"data": boxes, "outliers": outliers, "color": color, "name": y_col}, "series": []})
    return model, {"categories": len(cats), "stats": stats, "notes": notes}


def _facets(spec: ChartSpec, df: pd.DataFrame, model: dict, notes: list[str]) -> tuple[dict, dict]:
    _require(df, spec.facet_column, "facet_column")
    groups = df.groupby(spec.facet_column, dropna=False)
    sizes = groups.size().sort_values(ascending=False)
    names = [k for k in sizes.index if not (isinstance(k, float) and np.isnan(k))]
    if len(names) > 12:
        notes.append(f"Nur die 12 größten von {len(names)} Facetten gezeigt.")
        names = names[:12]
    base = spec.model_copy(update={"facet_column": None})
    all_cats: list[str] = []
    facets = []
    series_union: list[str] = []
    for name in names:
        sub = groups.get_group(name)
        m, _ = build_chart_model(base, sub)
        facets.append({"name": _cat_label(name, False), "categories": m["categories"], "series": m["series"]})
        for c in m["categories"]:
            if c not in all_cats:
                all_cats.append(c)
        for s_ in m["series"]:
            if s_["name"] not in series_union:
                series_union.append(s_["name"])
    if spec.month_axis:
        all_cats = [m for m in palette.MONTHS_DE]
    elif spec.sort == "x":
        all_cats = sorted(all_cats)
    colors = _series_colors(spec, series_union)
    for f in facets:
        idx = {c: i for i, c in enumerate(f["categories"])}
        for s_ in f["series"]:
            s_["data"] = [s_["data"][idx[c]] if c in idx else None for c in all_cats]
            s_["color"] = colors[s_["name"]]
        f["categories"] = all_cats
    stack = spec.stack if spec.stack is not None else spec.kind in ("stacked_bar", "area")
    model.update({"kind": spec.kind, "categories": all_cats, "series": [{"name": s_, "color": colors[s_]} for s_ in series_union], "stack": stack,
                  "facets": facets, "facet_columns": spec.facet_columns})
    rows = -(-len(facets) // spec.facet_columns)
    model["height"] = max(spec.height, 90 + rows * 260)
    return model, {"facets": [f["name"] for f in facets], "categories": len(all_cats), "series": series_union, "notes": notes}


_SPECIAL = {"timeline": _timeline, "calendar": _calendar, "sankey": _sankey, "boxplot": _boxplot, "graph": _graph}
