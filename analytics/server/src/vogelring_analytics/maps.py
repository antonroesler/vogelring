"""Turn a MapSpec + datasets into a renderer-agnostic map model (JSON for the Leaflet template)."""

from __future__ import annotations

import html
import math
from typing import Any

import pandas as pd

from . import palette
from .datasets import DatasetStore
from .settings import settings
from .specs import ColorSpec, FlowLayer, MapSpec, PointLayer, SizeSpec, TrackLayer

DEFAULT_TOOLTIP_COLS = ["ring", "date", "place", "species", "status", "ringing_place", "ringing_date"]


class MapBuildError(ValueError):
    pass


def _require(df: pd.DataFrame, col: str | None, what: str) -> None:
    if col and col not in df.columns:
        raise MapBuildError(f"Column '{col}' ({what}) not in dataset. Available: {', '.join(map(str, df.columns))}")


def _fmt(v: Any) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NaT:
        return ""
    if isinstance(v, pd.Timestamp):
        return v.strftime("%d.%m.%Y")
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def basemap_config(name: str) -> dict[str, Any]:
    """Tiles are served by this app's /tiles proxy (cache + key handling)."""
    attribution = "© OpenStreetMap contributors" if name == "osm" else "© OpenStreetMap contributors, © CARTO"
    return {"url": "/tiles/%s/{z}/{x}/{y}{r}.png" % name, "attribution": attribution, "subdomains": "", "retina": name != "osm"}


# ---------------------------------------------------------------- colour assignment


def _season_class(ts: Any) -> dict | None:
    if ts is None or ts is pd.NaT or (isinstance(ts, float) and math.isnan(ts)):
        return None
    try:
        month = pd.Timestamp(ts).month
    except Exception:
        return None
    return palette.season_for_month(month)


def _assign_colors(df: pd.DataFrame, color: ColorSpec, *, date_column: str, layer_name: str | None, group_col_default: str = "ring") -> tuple[pd.Series, pd.Series, list[dict[str, Any]], list[str]]:
    """Return (colour per row, class label per row, legend entries, notes)."""
    notes: list[str] = []
    n = len(df)
    if color.mode == "fixed":
        c = color.value or palette.THEME["secondary"]
        label = color.label or layer_name or "Punkte"
        return pd.Series([c] * n, index=df.index), pd.Series([label] * n, index=df.index), [{"label": label, "color": c}], notes

    if color.mode == "season":
        col = color.column or date_column
        _require(df, col, "season date column")
        classes = df[col].map(_season_class)
        labels = classes.map(lambda s: s["label"] if s else "ohne Datum")
        colors = classes.map(lambda s: s["color"] if s else "#9AA5AD")
        legend = [{"label": s["label"], "color": s["color"]} for s in palette.SEASONS if (labels == s["label"]).any()]
        if (labels == "ohne Datum").any():
            legend.append({"label": "ohne Datum", "color": "#9AA5AD"})
        return colors, labels, legend, notes

    if color.mode == "year":
        col = color.column or date_column
        _require(df, col, "year date column")
        years = pd.to_datetime(df[col], errors="coerce").dt.year
        labels = years.map(lambda y: str(int(y)) if pd.notna(y) else "ohne Datum")
        values = sorted(v for v in labels.unique() if v != "ohne Datum")
        cmap = palette.category_colors(values, color.palette)
        cmap["ohne Datum"] = "#9AA5AD"
        return labels.map(cmap), labels, [{"label": v, "color": cmap[v]} for v in values + (["ohne Datum"] if (labels == "ohne Datum").any() else [])], notes

    if color.mode == "species":
        col = color.column or ("species" if "species" in df.columns else "ringed_as_species")
        _require(df, col, "species column")
        labels = df[col].map(lambda v: _fmt(v) or "unbekannt")
        values = list(dict.fromkeys(labels.tolist()))
        cmap = {v: (color.palette or {}).get(v) or palette.species_color(v) for v in values}
        return labels.map(cmap), labels, [{"label": v, "color": cmap[v]} for v in values], notes

    # category / individual
    col = color.column or (group_col_default if color.mode == "individual" else None)
    if not col:
        raise MapBuildError("color.mode=category needs color.column.")
    _require(df, col, "colour column")
    labels = df[col].map(lambda v: _fmt(v) or "unbekannt")
    if color.order:
        values = [v for v in color.order if v in set(labels)] + [v for v in dict.fromkeys(labels.tolist()) if v not in color.order]
    elif color.mode == "category":
        values = list(labels.value_counts().index)
    else:  # individual: stable across layers of the same map (sorted ring numbers)
        values = sorted(set(labels.tolist()))
    if len(values) > len(palette.CATEGORY_PALETTE):
        notes.append(f"{len(values)} Klassen für '{col}': Farben wiederholen sich ab Klasse {len(palette.CATEGORY_PALETTE) + 1}.")
    cmap = palette.category_colors(values, color.palette)
    legend = [{"label": v, "color": cmap[v]} for v in values[:40]]
    if len(values) > 40:
        legend.append({"label": f"… {len(values) - 40} weitere", "color": "#9AA5AD"})
    return labels.map(cmap), labels, legend, notes


def _sizes(df: pd.DataFrame, size: SizeSpec) -> pd.Series:
    if not size.column:
        return pd.Series([size.min] * len(df), index=df.index)
    _require(df, size.column, "size column")
    v = pd.to_numeric(df[size.column], errors="coerce").fillna(0).clip(lower=0)
    if size.scale == "sqrt":
        v = v.pow(0.5)
    lo, hi = float(v.min()), float(v.max())
    if hi <= lo:
        return pd.Series([size.min] * len(df), index=df.index)
    return size.min + (v - lo) / (hi - lo) * (size.max - size.min)


def _tooltip(row: pd.Series, cols: list[str]) -> str:
    parts = []
    for c in cols:
        if c in row.index:
            val = _fmt(row[c])
            if val:
                parts.append(f"<b>{html.escape(str(c))}</b>: {html.escape(val)}")
    return "<br>".join(parts)


# ---------------------------------------------------------------- layers



def _is_date_col(series: pd.Series, name: str) -> bool:
    return pd.api.types.is_datetime64_any_dtype(series) or name in ("date", "ringing_date", "first_sighting", "last_sighting", "datum")


def _merged_value(series: pd.Series) -> Any:
    """Tooltip value for a merged marker: the value itself if all rows agree, otherwise a short honest summary
    (a merged marker must not look like one ring/one date – see ring E09547, 6 birds at one coordinate)."""
    vals = series.dropna()
    if vals.empty:
        return None
    uniq = list(dict.fromkeys(str(v) for v in vals))
    if len(uniq) == 1:
        return vals.iloc[0]
    if len(uniq) <= 3:
        return ", ".join(uniq)
    return f"{uniq[0]}, {uniq[1]}, … ({len(uniq)} verschiedene)"


def _merged_date(series: pd.Series) -> Any:
    vals = series.dropna()
    if vals.empty:
        return None
    if vals.nunique() == 1:
        return vals.iloc[0]
    try:
        d = pd.to_datetime(vals, errors="coerce").dropna()
        if d.empty:
            return _merged_value(series)
        lo, hi = d.min(), d.max()
        return f"{lo:%d.%m.%Y} – {hi:%d.%m.%Y}"
    except Exception:
        return _merged_value(series)


def _points_layer(layer: PointLayer, store: DatasetStore) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[str]]:
    df = store.load(layer.dataset_id)
    _require(df, layer.lat_column, "lat")
    _require(df, layer.lon_column, "lon")
    notes: list[str] = []
    total = len(df)
    df = df[pd.to_numeric(df[layer.lat_column], errors="coerce").notna() & pd.to_numeric(df[layer.lon_column], errors="coerce").notna()].copy()
    missing = total - len(df)
    if missing:
        notes.append(f"{missing} Zeilen ohne Koordinaten wurden nicht gezeichnet.")
    df["__lat"] = pd.to_numeric(df[layer.lat_column], errors="coerce")
    df["__lon"] = pd.to_numeric(df[layer.lon_column], errors="coerce")

    colors, classes, legend, cnotes = _assign_colors(df, layer.color, date_column=layer.date_column, layer_name=layer.name)
    notes += cnotes
    df["__color"], df["__class"] = colors, classes

    size_spec = layer.size
    if layer.dedupe != "none":
        if layer.dedupe == "column":
            if not layer.dedupe_column:
                raise MapBuildError("dedupe=column needs dedupe_column.")
            _require(df, layer.dedupe_column, "dedupe_column")
            keys = [layer.dedupe_column]
        else:
            df["__lat"], df["__lon"] = df["__lat"].round(4), df["__lon"].round(4)
            keys = ["__lat", "__lon"] + (["__class"] if layer.dedupe == "coords_per_group" else [])
        agg: dict[str, Any] = {"__n": ("__class", "size")}
        if layer.dedupe == "column":
            agg["__lat"] = ("__lat", "mean")
            agg["__lon"] = ("__lon", "mean")
        if "ring" in df.columns:
            agg["__individuals"] = ("ring", "nunique")
        for c in df.columns:
            if c not in keys and not c.startswith("__") and c not in agg:
                agg[c] = (c, _merged_date if _is_date_col(df[c], c) else _merged_value)
        agg["__color"] = ("__color", "first")
        if "__class" not in keys:
            agg["__class"] = ("__class", "first")
        df = df.groupby(keys, as_index=False).agg(**agg)
        if not size_spec.column:
            size_spec = SizeSpec(column="__individuals" if "__individuals" in df.columns else "__n", min=size_spec.min, max=max(size_spec.max, size_spec.min + 1), scale=size_spec.scale)
        what = f"gleicher Wert von '{layer.dedupe_column}'" if layer.dedupe == "column" else "gleiche Koordinaten"
        notes.append(f"Zusammengefasst: {what} → {len(df)} Marker (Größe = Anzahl Individuen bzw. Sichtungen).")

    df["__size"] = _sizes(df, size_spec)
    tooltip_cols = layer.tooltip_columns or [c for c in DEFAULT_TOOLTIP_COLS if c in df.columns]
    if "__n" in df.columns:
        df["Sichtungen"] = df["__n"]
        tooltip_cols = tooltip_cols + ["Sichtungen"] + (["Individuen"] if "__individuals" in df.columns else [])
        if "__individuals" in df.columns:
            df["Individuen"] = df["__individuals"]

    label_seen: set[str] = set()
    features = []
    for _, row in df.iterrows():
        f: dict[str, Any] = {
            "lat": float(row["__lat"]),
            "lon": float(row["__lon"]),
            "color": row["__color"],
            "size": round(float(row["__size"]), 1),
            "shape": layer.shape,
            "opacity": layer.opacity,
            "cls": str(row["__class"]),
            "tooltip": _tooltip(row, tooltip_cols),
        }
        if layer.label:
            _require(df, layer.label.column, "label column")
            text = _fmt(row[layer.label.column])
            ok = bool(text) and (not layer.label.only_values or text in layer.label.only_values)
            if ok and layer.label.dedupe:
                ok = text not in label_seen
                label_seen.add(text)
            if ok:
                f["label"] = text
                f["label_size"] = layer.label.font_size
                f["label_placement"] = layer.label.placement
        features.append(f)

    cluster = bool(layer.cluster)
    model = {"type": "points", "name": layer.name or "Punkte", "cluster": cluster, "shape": layer.shape, "features": features}
    class_counts = df["__class"].value_counts().to_dict()
    informative_counts = len(features) > len(class_counts)
    for entry in legend:
        entry["shape"] = layer.shape
        if informative_counts:
            entry["count"] = int(class_counts.get(entry["label"], 0))
    summary = {"layer": model["name"], "points": len(features), "classes": {k: int(v) for k, v in class_counts.items()}, "clustered": cluster}
    if "__individuals" in df.columns:
        summary["individuals_total"] = int(df["__individuals"].sum())
    return model, legend, summary, notes


def _tracks_layer(layer: TrackLayer, store: DatasetStore) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[str]]:
    df = store.load(layer.dataset_id)
    for c in (layer.group_column, layer.order_column, layer.lat_column, layer.lon_column):
        _require(df, c, "track column")
    df = df[pd.to_numeric(df[layer.lat_column], errors="coerce").notna() & pd.to_numeric(df[layer.lon_column], errors="coerce").notna()].copy()
    df = df.sort_values([layer.group_column, layer.order_column])
    colors, classes, legend, notes = _assign_colors(df, layer.color, date_column=layer.order_column, layer_name=layer.name, group_col_default=layer.group_column)
    df["__color"], df["__class"] = colors, classes
    lines = []
    for key, g in df.groupby(layer.group_column, sort=False):
        coords = [[float(a), float(b)] for a, b in zip(pd.to_numeric(g[layer.lat_column]), pd.to_numeric(g[layer.lon_column]))]
        coords = [c for i, c in enumerate(coords) if i == 0 or c != coords[i - 1]]
        if len(coords) < 2:
            continue
        first, last = g.iloc[0], g.iloc[-1]
        lines.append({
            "coords": coords,
            "color": g["__color"].iloc[0],
            "cls": str(g["__class"].iloc[0]),
            "width": layer.width,
            "opacity": layer.opacity,
            "arrows": layer.arrows,
            "tooltip": f"<b>{html.escape(_fmt(key))}</b><br>{html.escape(_fmt(first[layer.order_column]))} → {html.escape(_fmt(last[layer.order_column]))}<br>{len(coords)} Stationen",
        })
    model = {"type": "tracks", "name": layer.name or "Bewegungen", "lines": lines}
    for e in legend:
        e["shape"] = "line"
    return model, legend, {"layer": model["name"], "tracks": len(lines)}, notes


def _flows_layer(layer: FlowLayer, store: DatasetStore) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, Any], list[str]]:
    df = store.load(layer.dataset_id)
    for c in (layer.from_lat_column, layer.from_lon_column, layer.to_lat_column, layer.to_lon_column, layer.weight_column, layer.label_column):
        _require(df, c, "flow column")
    num = {c: pd.to_numeric(df[c], errors="coerce") for c in (layer.from_lat_column, layer.from_lon_column, layer.to_lat_column, layer.to_lon_column)}
    mask = pd.concat(num.values(), axis=1).notna().all(axis=1)
    df = df[mask].copy()
    if layer.weight_column:
        w = pd.to_numeric(df[layer.weight_column], errors="coerce").fillna(0).clip(lower=0)
        lo, hi = float(w.min()), float(w.max())
        widths = pd.Series([layer.min_width] * len(df), index=df.index) if hi <= lo else layer.min_width + (w.pow(0.5) - math.sqrt(lo)) / (math.sqrt(hi) - math.sqrt(lo)) * (layer.max_width - layer.min_width)
    else:
        widths = pd.Series([(layer.min_width + layer.max_width) / 2] * len(df), index=df.index)
    lines = []
    for i, (_, row) in enumerate(df.iterrows()):
        item = {
            "from": [float(row[layer.from_lat_column]), float(row[layer.from_lon_column])],
            "to": [float(row[layer.to_lat_column]), float(row[layer.to_lon_column])],
            "width": round(float(widths.iloc[i]), 2),
            "color": layer.color,
            "opacity": layer.opacity,
            "arrows": layer.arrows,
            "tooltip": _tooltip(row, [c for c in df.columns if not c.startswith("__")][:8]),
        }
        if layer.label_column:
            item["label"] = _fmt(row[layer.label_column])
        lines.append(item)
    model = {"type": "flows", "name": layer.name or "Bewegungsrichtungen", "lines": lines}
    legend = [{"label": layer.name or "Bewegungsrichtungen", "color": layer.color, "shape": "line"}]
    return model, legend, {"layer": model["name"], "flows": len(lines)}, []


# ---------------------------------------------------------------- assembly


def build_map_model(spec: MapSpec, store: DatasetStore) -> tuple[dict[str, Any], dict[str, Any]]:
    layers: list[dict[str, Any]] = []
    legend: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    notes: list[str] = []
    lats: list[float] = []
    lons: list[float] = []

    for layer in spec.points:
        m, lg, s, n = _points_layer(layer, store)
        layers.append(m)
        legend += lg
        summaries.append(s)
        notes += n
        lats += [f["lat"] for f in m["features"]]
        lons += [f["lon"] for f in m["features"]]
    for layer in spec.tracks:
        m, lg, s, n = _tracks_layer(layer, store)
        layers.append(m)
        legend += lg
        summaries.append(s)
        notes += n
        for line in m["lines"]:
            lats += [c[0] for c in line["coords"]]
            lons += [c[1] for c in line["coords"]]
    for layer in spec.flows:
        m, lg, s, n = _flows_layer(layer, store)
        layers.append(m)
        legend += lg
        summaries.append(s)
        notes += n
        for line in m["lines"]:
            lats += [line["from"][0], line["to"][0]]
            lons += [line["from"][1], line["to"][1]]
    if spec.markers:
        feats = []
        for mk in spec.markers:
            feats.append({"lat": mk.lat, "lon": mk.lon, "color": mk.color, "size": mk.size, "shape": mk.shape, "opacity": 1, "label": mk.label, "label_size": 13, "label_placement": "right", "tooltip": html.escape(mk.label or ""), "cls": mk.legend_label or mk.label or "Markierung"})
            if mk.legend_label:
                legend.append({"label": mk.legend_label, "color": mk.color, "shape": mk.shape})
            lats.append(mk.lat)
            lons.append(mk.lon)
        layers.append({"type": "markers", "name": "Markierungen", "features": feats, "cluster": False})

    # merge legend duplicates (same label+color)
    seen: set[tuple[str, str]] = set()
    merged = []
    for e in legend:
        k = (e["label"], e["color"])
        if k in seen or (e.get("shape") == "line" and any(m["label"] == e["label"] for m in merged)):
            continue
        seen.add(k)
        merged.append(e)

    bounds = None
    if lats and lons:
        bounds = [[min(lats), min(lons)], [max(lats), max(lons)]]
        if bounds[0] == bounds[1]:
            d = 0.01
            bounds = [[bounds[0][0] - d, bounds[0][1] - d], [bounds[1][0] + d, bounds[1][1] + d]]
    if not lats:
        raise MapBuildError("No drawable coordinates in any layer.")

    model = {
        "title": spec.title,
        "subtitle": spec.subtitle,
        "footnote": spec.footnote,
        "width": spec.width,
        "height": spec.height,
        "basemap": basemap_config(spec.basemap),
        "basemap_name": spec.basemap,
        "zoom": spec.zoom,
        "center": list(spec.center) if spec.center else None,
        "bounds": bounds,
        "fit_padding": spec.fit_padding,
        "scale_bar": spec.scale_bar,
        "legend": {"title": spec.legend.title, "show": spec.legend.show, "position": spec.legend.position, "entries": merged},
        "layers": layers,
    }
    summary = {"layers": summaries, "bounds": bounds, "legend": [e["label"] for e in merged], "notes": notes}
    return model, summary
