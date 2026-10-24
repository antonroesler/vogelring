"""A *view* is one chart, map or table built from a source + filters + encoding (Tableau worksheet, simplified).

``build_view`` compiles the view to read-only SQL, stores the result as a dataset with a plain-German description
and returns the fully populated Chart/Map/TableSpec plus the renderer model. Rendering PNG/PDF is left to the
caller (visual service), so previews in the web app can use the model directly.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from . import palette, runtime
from .analysis import render_sql
from .charts import build_chart_model
from .maps import build_map_model
from .binning import BinSpec, bin_dimension, bin_key_labels, bin_options, bin_values, binnable, code_labels, describe_bins, is_bin_dimension, resolve_dimension, with_width
from .sources import (
    DIMENSIONS,
    Dimension,
    FilterSpec,
    Source,
    SourceError,
    build_aggregate_sql,
    build_rows_sql,
    compile_filters,
    describe_filters,
    get_dimension,
    get_metric,
    get_source,
)
from .specs import AnnotationSpec, ChartKind, ChartSpec, ColorSpec, ColumnSpec, LabelSpec, LegendSpec, MapSpec, MarkerSpec, PointLayer, SizeSpec, TableSpec, TrackLayer
from .tables import auto_label, build_table_model

RAW_ROW_KINDS = {"timeline", "calendar", "scatter", "boxplot", "sankey", "graph", "histogram"}
_MAP_COLUMNS = {
    "sightings": ["id", "ring", "date", "place", "species", "lat", "lon", "status", "age", "ringing_place", "ringing_date", "ringing_lat", "ringing_lon", "km_from_ringing"],
    "ringings": ["ring", "date", "place", "species", "lat", "lon", "ringer", "age", "status"],
    "birds": ["ring", "species", "ringing_date", "ringing_place", "ringing_lat", "ringing_lon", "sightings", "first_sighting", "last_sighting", "places", "max_km"],
}
_TABLE_DEFAULT_COLUMNS = {
    "sightings": ["date", "ring", "species", "place", "status", "age", "melder", "ringing_place"],
    "ringings": ["date", "ring", "species", "place", "ringer", "age"],
    "birds": ["ring", "species", "ringing_date", "ringing_place", "sightings", "first_sighting", "last_sighting", "places", "max_km"],
    "relationships": ["bird1_ring", "relationship_type", "bird2_ring", "year", "confidence"],
}
CHART_KIND_LABELS = {
    "bar": "Balkendiagramm", "stacked_bar": "Gestapeltes Balkendiagramm", "line": "Liniendiagramm", "area": "Flächendiagramm",
    "scatter": "Streudiagramm", "pie": "Kreisdiagramm", "heatmap": "Heatmap", "histogram": "Histogramm", "timeline": "Zeitstrahl",
    "calendar": "Kalender", "sankey": "Flussdiagramm", "boxplot": "Boxplot", "graph": "Netzdiagramm",
}


class ViewError(ValueError):
    pass


class _Spec(BaseModel):
    model_config = ConfigDict(extra="forbid")


class MetricSpec(_Spec):
    kind: str = Field("sightings", description="sightings · birds · observation_days · places · sum · mean · median · min · max · count_distinct")
    column: str | None = Field(None, description="Spalte für sum/mean/median/min/max/count_distinct.")


class MapOptions(_Spec):
    color_mode: Literal["season", "species", "individual", "category", "year", "fixed"] = "season"
    color_column: str | None = Field(None, description="Spalte für color_mode=category (z. B. place, status).")
    color_value: str | None = Field(None, description="Hex-Farbe für color_mode=fixed.")
    show_ringing_sites: bool = Field(True, description="Beringungsorte als Dreiecke einzeichnen (Quellen mit Beringungskoordinaten).")
    tracks: bool = Field(False, description="Bewegungslinien je Vogel (chronologisch).")
    bubbles_by_place: bool = Field(False, description="Ein Kreis je Ort, Größe = Anzahl verschiedener Vögel.")
    labels: bool = Field(False, description="Ortsnamen beschriften (Standard aus – bei vielen Orten unleserlich; nur auf Wunsch).")
    cluster: bool | None = None
    basemap: Literal["light", "dark", "osm", "voyager"] = "light"
    zoom: int | None = Field(None, ge=5, le=18)
    center: tuple[float, float] | None = None
    bounds: list[list[float]] | None = Field(None, description="Fester Kartenausschnitt [[lat, lon], [lat, lon]] (Südwest, Nordost) für Bild, PDF und Berichte – in Erkunden per „Ausschnitt übernehmen“. Standard: automatisch an die Daten angepasst, einzelne weit entfernte Punkte bleiben außerhalb (Fußnote).")
    fit: Literal["auto", "all"] = Field("auto", description="auto: Ausschnitt um den Großteil der Punkte (Ausreißer außerhalb, in der Fußnote genannt). all: alle Punkte im Bild.")
    markers: list[MarkerSpec] = Field(default_factory=list)
    exclude_star: bool = Field(True, description="Ausgeschlossene Orte (filters.exclude_places) mit Stern markieren.")
    legend_title: str | None = None
    point_size: float = Field(9, ge=2, le=60)


class ViewSpec(_Spec):
    kind: Literal["chart", "map", "table"] = "chart"
    source: str = Field("sightings", description="sightings · ringings · birds · relationships")
    filters: FilterSpec = Field(default_factory=FilterSpec)
    title: str | None = None
    subtitle: str | None = Field(None, description="Standard: Beschreibung der Auswahl in Alltagssprache.")
    # chart
    chart_kind: ChartKind = "bar"
    metric: MetricSpec = Field(default_factory=MetricSpec, description="Was gezählt wird.")
    dimension: str = Field("month", description="Aufteilen nach (x-Achse / Kategorien).")
    color: str | None = Field(None, description="Farbe nach (Serien), z. B. species, place, year.")
    facet: str | None = Field(None, description="Kacheln nach (kleine Vielfache).")
    sort: Literal["none", "asc", "desc", "x"] = "none"
    limit: int | None = Field(None, ge=1, le=500)
    show_values: bool = False
    show_totals: bool = False
    stack: bool | None = None
    colors: dict[str, str] | None = None
    annotations: list[AnnotationSpec] = Field(default_factory=list)
    annotate_moult: bool = Field(False, description="Mauserzeit Mai–Juli als Band markieren (bei Aufteilung nach Monat).")
    bins: list[BinSpec] = Field(default_factory=list, description="Klassen für Zahlen-/Datumsspalten, die als Aufteilung, Farbe, Kachel, group_by, Fluss-/Netzknoten, Boxplot-Kategorie oder Zeitstrahl-Zeile dienen (Spaltenname als Schlüssel, z. B. dimension='km_from_ringing' + bins=[{column:'km_from_ringing', width:10}]). Ohne Eintrag: automatisch etwa 8 runde Klassen bzw. Jahr.")
    # raw-row chart kinds (timeline, calendar, scatter, boxplot, sankey, graph, histogram)
    x_column: str | None = Field(None, description="Datums-/Wertspalte für Zeitstrahl, Kalender, Streu-, Boxplot, Histogramm.")
    series_column: str | None = Field(None, description="Zeilen des Zeitstrahls (z. B. ring) bzw. Gruppen.")
    y_column: str | None = Field(None, description="Wertspalte für Streu-/Boxplot bzw. Gewicht für Fluss/Netz.")
    color_column: str | None = Field(None, description="Farbspalte des Zeitstrahls.")
    source_column: str | None = Field(None, description="Fluss/Netz: Startknoten (z. B. ringing_place).")
    target_column: str | None = Field(None, description="Fluss/Netz: Zielknoten (z. B. place).")
    edge_label_column: str | None = None
    # map
    map: MapOptions = Field(default_factory=MapOptions)
    # table
    columns: list[str] | None = Field(None, description="Tabellenspalten (Standard je Quelle).")
    group_by: list[str] | None = Field(None, description="Tabelle zusammenfassen nach diesen Aufteilungen (mit metric).")
    sort_by: str | None = None
    sort_desc: bool = True
    table_limit: int = Field(50, ge=1, le=300)
    totals_row: bool = False
    highlight_max: list[str] = Field(default_factory=list)
    # size
    width: int | None = Field(None, ge=500, le=2400)
    height: int | None = Field(None, ge=350, le=2000)

    @model_validator(mode="after")
    def _check(self) -> "ViewSpec":
        cols = [b.column for b in self.bins]
        if len(set(cols)) != len(cols):
            raise ValueError("bins: jede Spalte nur einmal angeben.")
        if self.kind == "chart" and self.chart_kind in RAW_ROW_KINDS:
            k = self.chart_kind
            if k in ("timeline", "calendar", "histogram", "scatter", "boxplot") and not self.x_column:
                raise ValueError(f"{CHART_KIND_LABELS[k]} braucht x_column (Datums- bzw. Wertspalte, z. B. 'date').")
            if k == "timeline" and not self.series_column:
                raise ValueError("Zeitstrahl braucht series_column (eine Zeile je Wert, z. B. 'ring' oder 'place').")
            if k in ("scatter", "boxplot") and not self.y_column:
                raise ValueError(f"{CHART_KIND_LABELS[k]} braucht y_column.")
            if k in ("sankey", "graph") and not (self.source_column and self.target_column):
                raise ValueError(f"{CHART_KIND_LABELS[k]} braucht source_column und target_column.")
        return self

    # ---------------------------------------------------------------- wording
    def bin_map(self) -> dict[str, BinSpec]:
        return {b.column: b for b in self.bins}

    def dim(self, key: str, source: Source | None = None) -> Dimension:
        """Predefined dimension or a binned column of the source (label only needs no DB round trip)."""
        return resolve_dimension(source or get_source(self.source), key, self.bin_map())

    def metric_label(self, source: Source | None = None) -> str:
        source = source or get_source(self.source)
        return get_metric(self.metric.kind).label_for(self.metric.column, source)

    def describe(self) -> str:
        """German one-liner for lists and the activity log."""
        source = get_source(self.source)
        sel = describe_filters(self.filters, source)
        if self.kind == "map":
            what = "Karte"
            if self.map.bubbles_by_place:
                what += " (Kreise je Ort)"
            elif self.map.tracks:
                what += " (Bewegungen)"
            return f"{what}: {sel}"
        if self.kind == "table":
            if self.group_by:
                return f"Tabelle: {self.metric_label(source)} je {' und '.join(self.dim(g, source).label for g in self.group_by)} – {sel}"
            return f"Tabelle: {sel}"
        label = CHART_KIND_LABELS.get(self.chart_kind, "Diagramm")
        if self.chart_kind in RAW_ROW_KINDS:
            return f"{label}: {sel}"
        parts = f"{label}: {self.metric_label(source)} je {self.dim(self.dimension, source).label}"
        if self.color:
            parts += f", Farbe nach {self.dim(self.color, source).label}"
        if self.facet:
            parts += f", Kacheln je {self.dim(self.facet, source).label}"
        return f"{parts} – {sel}"


@dataclass
class ViewResult:
    dataset_id: str
    visual_kind: str  # chart | map | table
    visual_spec: ChartSpec | MapSpec | TableSpec
    model: dict[str, Any]
    summary: dict[str, Any]
    sql: str
    description: str
    row_count: int
    notes: list[str] = field(default_factory=list)

    def spec_dict(self) -> dict[str, Any]:
        return self.visual_spec.model_dump(mode="json", by_alias=True, exclude_none=True)


# ---------------------------------------------------------------- helpers


def _cap(s: str) -> str:
    return s[:1].upper() + s[1:] if s else s


async def _query(sql: str, params: list[Any], *, max_rows: int | None = None):
    db = runtime.database()
    kwargs: dict[str, Any] = {"params": tuple(params) if params else None}
    if max_rows:
        kwargs["max_rows"] = max_rows
    try:
        return await db.query(sql, **kwargs)
    except Exception as exc:  # SqlRejected or DB errors → German message, original text kept for the agent
        raise ViewError(f"Abfrage fehlgeschlagen: {str(exc).strip()[:300]}") from exc


def _save(df, *, name: str, sql: str, params: list[Any], description: str, truncated: bool) -> Any:
    readable = render_sql(sql, params)
    return runtime.datasets().save(df, name=name, sql=readable, description=description, source="view", truncated=truncated), readable


def _color_by(spec: ViewSpec) -> str:
    keys = {spec.dimension, spec.color or ""}
    if "species" in keys or "ringed_as_species" in keys:
        return "species"
    if "season" in keys:
        return "season"
    return "theme"


def _raw_color_by(spec: ViewSpec) -> str:
    if spec.chart_kind in ("sankey", "graph"):
        return "theme"
    if spec.color_column in ("species", "ringed_as_species"):
        return "species"
    if spec.color == "season" or spec.color_column == "season":
        return "season"
    return "theme"


def _chart_title(spec: ViewSpec, source: Source) -> str:
    if spec.title:
        return spec.title
    if spec.chart_kind in RAW_ROW_KINDS:
        return f"{CHART_KIND_LABELS[spec.chart_kind]}: {_cap(describe_filters(spec.filters, source))}"
    t = f"{spec.metric_label(source)} je {spec.dim(spec.dimension, source).label}"
    if spec.color:
        t += f" und {spec.dim(spec.color, source).label}"
    return t


# ---------------------------------------------------------------- binning glue

_RAW_CATEGORY_ROLES: dict[str, tuple[str, ...]] = {
    "sankey": ("source_column", "target_column"),
    "graph": ("source_column", "target_column", "edge_label_column"),
    "boxplot": ("x_column",),
    "timeline": ("series_column", "color_column"),
    "scatter": ("color_column",),
    "histogram": ("x_column",),  # only with an explicit BinSpec – np.histogram bins otherwise
}


async def _resolve_dims(spec: ViewSpec, source: Source, keys: list[str]) -> tuple[list[Dimension], dict[str, BinSpec]]:
    """Dimension objects for the keys; binned numeric columns without width get one from the observed MIN/MAX."""
    bins = spec.bin_map()
    dims: list[Dimension] = []
    for k in keys:
        if is_bin_dimension(source, k):
            col = source.column(k)
            assert col is not None
            b = bins.get(k) or BinSpec(column=k)
            if b.is_auto and col.type != "date":
                where, params = compile_filters(source, spec.filters)
                res = await _query(f"SELECT MIN({k}) AS lo, MAX({k}) AS hi, percentile_disc(0.95) WITHIN GROUP (ORDER BY {k}) AS p95 FROM ({source.base_sql}) s WHERE {where}", params)
                lo, hi, p95 = (res.rows[0][0], res.rows[0][1], res.rows[0][2]) if res.rows else (None, None, None)
                b = with_width(b, None if lo is None else float(lo), None if hi is None else float(hi), col, None if p95 is None else float(p95))
            bins[k] = b
            dims.append(bin_dimension(source, col, b))
        else:
            dims.append(get_dimension(k))
    return dims, bins


def _label_bins(df, dims: list[Dimension], bins: dict[str, BinSpec], source: Source) -> dict[str, list[str]]:
    """Replace SQL bin keys by labels in place; returns the label order per column for the chart builder."""
    order: dict[str, list[str]] = {}
    for d in dims:
        if d.key in df.columns and is_bin_dimension(source, d.key):
            col = source.column(d.key)
            assert col is not None
            labels, label_order = bin_key_labels(df[d.key], bins[d.key], col)
            df[d.key] = labels
            if label_order:
                order[d.key] = label_order
    return order


def _bin_raw_columns(spec: ViewSpec, source: Source, df) -> tuple[dict[str, str], dict[str, list[str]], list[str]]:
    """Add ``<col>_klasse`` / ``<col>_label`` columns for numeric, date and coded columns used as categories.

    Returns (role → column to use, label order per new column, notes)."""
    bins = spec.bin_map()
    roles = {r: getattr(spec, r) for r in ("x_column", "series_column", "y_column", "color_column", "source_column", "target_column", "edge_label_column")}
    order: dict[str, list[str]] = {}
    notes: list[str] = []
    done: dict[str, str] = {}
    for role in _RAW_CATEGORY_ROLES.get(spec.chart_kind, ()):
        c = roles.get(role)
        if not c or c not in df.columns:
            continue
        if c in done:
            roles[role] = done[c]
            continue
        col = source.column(c)
        if col is None:
            continue
        if binnable(col) and (spec.chart_kind != "histogram" or c in bins):
            labels, label_order, used = bin_values(df[c], bins.get(c) or BinSpec(column=c), col)
            new = f"{c}_klasse"
            df[new] = labels
            order[new] = label_order
            if c not in bins:
                notes.append(f"„{col.label}“ automatisch eingeteilt: {describe_bins(used, col)} (über bins anpassbar).")
            done[c] = new
            roles[role] = new
        else:
            labels = code_labels(df[c], col, source)
            if labels is not None:
                new = f"{c}_label"
                df[new] = labels
                done[c] = new
                roles[role] = new
    return roles, order, notes


# ---------------------------------------------------------------- chart


async def _build_chart(spec: ViewSpec, source: Source, max_rows: int | None) -> ViewResult:
    subtitle = spec.subtitle if spec.subtitle is not None else _cap(describe_filters(spec.filters, source))
    size: dict[str, Any] = {k: v for k, v in (("width", spec.width), ("height", spec.height)) if v}
    if spec.chart_kind in RAW_ROW_KINDS:
        needed = [c for c in (spec.x_column, spec.series_column, spec.y_column, spec.color_column, spec.source_column, spec.target_column, spec.edge_label_column) if c]
        extra = [c for c in ("ring", "date", "place", "species", "status") if source.has(c)]
        cols = list(dict.fromkeys(needed + extra))
        try:
            sql, params = build_rows_sql(source, spec.filters, cols)
        except SourceError as exc:
            raise ViewError(str(exc)) from exc
        res = await _query(sql, params, max_rows=max_rows)
        df = res.to_frame()
        roles, order, bin_notes = _bin_raw_columns(spec, source, df)
        description = f"{_cap(describe_filters(spec.filters, source))}; jede Zeile ist eine {source.label[:-2] if source.label.endswith('en') else source.label}."
        meta, readable = _save(df, name=_chart_title(spec, source), sql=sql, params=params, description=description, truncated=res.truncated)
        kind = spec.chart_kind
        aggregate = "count" if kind == "calendar" and spec.metric.kind == "sightings" else ("count_distinct" if kind == "calendar" else "none")
        extra_kwargs: dict[str, Any] = {}
        if kind == "histogram" and roles["x_column"] != spec.x_column:  # explicit classes → counted bar chart
            kind, aggregate = "bar", "count"
            col = source.column(spec.x_column or "")
            extra_kwargs = {"x_axis": {"title": col.label if col else spec.x_column}, "y_axis": {"title": "Anzahl", "format": "integer"}}
        cs = ChartSpec(
            kind=kind, dataset_id=meta.id, title=_chart_title(spec, source), subtitle=subtitle,
            x=roles["x_column"], y=roles["y_column"], series_column=roles["series_column"], color_column=roles["color_column"],
            source_column=roles["source_column"], target_column=roles["target_column"], edge_label_column=roles["edge_label_column"],
            color_by=_raw_color_by(spec), colors=spec.colors, sort=spec.sort, limit=spec.limit, aggregate=aggregate,
            annotations=spec.annotations, category_order=order or None, **extra_kwargs, **size,
        )
        if spec.chart_kind == "calendar" and spec.metric.kind == "birds":
            cs.y = "ring"
        if spec.chart_kind == "timeline" and spec.color_column is None and spec.color:
            cs.color_by = "season" if spec.color == "season" else cs.color_by
        try:
            model, summary = build_chart_model(cs, df)
        except ValueError as exc:
            raise ViewError(str(exc)) from exc
        return ViewResult(meta.id, "chart", cs, model, summary, readable, description, int(len(df)), bin_notes + list(summary.get("notes") or []))

    keys = [spec.dimension] + ([spec.color] if spec.color else []) + ([spec.facet] if spec.facet else [])
    if spec.chart_kind == "heatmap" and not spec.color:
        raise ViewError("Heatmap braucht eine Aufteilung (dimension) und eine zweite für die Zeilen (color).")
    if spec.chart_kind == "pie" and spec.color:
        raise ViewError("Kreisdiagramm: nur eine Aufteilung (dimension), keine Farbe nach.")
    try:
        dims, bins = await _resolve_dims(spec, source, keys)
        sql, params = build_aggregate_sql(source, spec.filters, spec.metric.kind, spec.metric.column, list(dims))
    except SourceError as exc:
        raise ViewError(str(exc)) from exc
    res = await _query(sql, params, max_rows=max_rows)
    df = res.to_frame()
    order = _label_bins(df, dims, bins, source)
    metric_label = spec.metric_label(source)
    description = f"{metric_label} je {' und '.join(d.label for d in dims)}; {describe_filters(spec.filters, source)}."
    meta, readable = _save(df, name=_chart_title(spec, source), sql=sql, params=params, description=description, truncated=res.truncated)

    dim = dims[0]
    annotations = list(spec.annotations)
    if spec.annotate_moult and dim.is_month:
        annotations.append(AnnotationSpec(kind="band", **{"from": 5}, to=7, label="Mauserzeit", color="#228096"))
    colors = spec.colors
    if spec.color == "season" and not colors:
        colors = {s["label"]: s["color"] for s in palette.SEASONS}
    patterns = None
    if "group" in (spec.dimension, spec.color) and spec.filters.groups:
        from .groups import group_categories, group_colors, group_patterns  # lazy

        patterns = group_patterns(spec.filters.groups) or None
        if not colors:
            colors = group_colors(spec.filters.groups) or None
        if patterns:
            # a combined category („A + B“) takes the first member's colour; the renderer stripes the second over it
            colors = {**{k: v[0] for k, v in patterns.items()}, **(colors or {})}
        order["group"] = group_categories(spec.filters.groups)
    kind = spec.chart_kind
    cs_kwargs: dict[str, Any] = dict(
        kind=kind, dataset_id=meta.id, title=_chart_title(spec, source), subtitle=subtitle, x=spec.dimension, y="value",
        series_column=spec.color, facet_column=spec.facet, aggregate="none", month_axis=dim.is_month, sort=spec.sort, limit=spec.limit,
        show_values=spec.show_values, show_totals=spec.show_totals, stack=spec.stack, colors=colors, patterns=patterns, color_by=_color_by(spec),
        annotations=annotations, legend_title=dims[1].label if spec.color else None, category_order=order or None, **size,
    )
    cs_kwargs["y_axis"] = {"title": metric_label, "format": "integer" if spec.metric.kind in ("sightings", "birds", "observation_days", "places", "rows", "count_distinct") else "number"}
    cs_kwargs["x_axis"] = {"title": None if dim.is_month else dim.label}
    if kind == "heatmap":
        cs_kwargs.update(heat_value="value", y=None, series_column=spec.color, facet_column=None, aggregate="sum")
    if kind == "pie":
        cs_kwargs.update(series_column=None, legend_title=None)
    if spec.sort == "none" and not dim.is_month and not dim.is_time and dim.text and not dim.order_sql and kind in ("bar", "stacked_bar", "pie"):
        cs_kwargs["sort"] = "desc"  # categorical rankings read better sorted
    try:
        cs = ChartSpec(**cs_kwargs)
        model, summary = build_chart_model(cs, df)
    except ValueError as exc:
        raise ViewError(str(exc)) from exc
    return ViewResult(meta.id, "chart", cs, model, summary, readable, description, int(len(df)), list(summary.get("notes") or []))


# ---------------------------------------------------------------- map


async def _excluded_markers(places: list[str]) -> tuple[list[MarkerSpec], list[str]]:
    markers: list[MarkerSpec] = []
    notes: list[str] = []
    for p in places:
        sql = "SELECT AVG(lat) AS lat, AVG(lon) AS lon, COUNT(*) AS n, MIN(place) AS name FROM v_sightings WHERE place ILIKE %s AND lat IS NOT NULL AND date IS NOT NULL"
        res = await _query(sql, ["%" + p.strip("%") + "%"])
        if not res.rows or res.rows[0][0] is None:
            continue
        lat, lon, n, name = res.rows[0]
        markers.append(MarkerSpec(lat=float(lat), lon=float(lon), shape="star", color="#00436C", size=26, legend_label=f"{name} (ausgeschlossen)"))
        notes.append(f"{int(n)} Sichtungen in ‚{name}‘ ausgeschlossen")
    return markers, notes


async def _build_map(spec: ViewSpec, source: Source, max_rows: int | None) -> ViewResult:
    if not source.lat_column:
        raise ViewError(f"Die Datenquelle „{source.label}“ hat keine Koordinaten für eine Karte.")
    o = spec.map
    cols = _MAP_COLUMNS.get(source.key) or [c.name for c in source.columns]
    if o.color_mode == "category" and o.color_column and o.color_column not in cols and source.has(o.color_column):
        cols = cols + [o.color_column]
    try:
        sql, params = build_rows_sql(source, spec.filters, cols)
    except SourceError as exc:
        raise ViewError(str(exc)) from exc
    res = await _query(sql, params, max_rows=max_rows)
    df = res.to_frame()
    sel = describe_filters(spec.filters, source)
    description = f"{_cap(sel)}; eine Zeile je {('Sichtung' if source.key == 'sightings' else 'Beringung' if source.key == 'ringings' else 'Vogel')}, mit Koordinaten für die Karte."
    title = spec.title or f"Karte: {_cap(sel)}"
    meta, readable = _save(df, name=title, sql=sql, params=params, description=description, truncated=res.truncated)

    lat, lon = source.lat_column, source.lon_column
    date_col = source.default_date_column or "date"
    if o.color_mode == "category":
        if not o.color_column:
            raise ViewError("color_mode=category braucht color_column (z. B. place, status).")
        color = ColorSpec(mode="category", column=o.color_column)
    elif o.color_mode == "fixed":
        color = ColorSpec(mode="fixed", value=o.color_value or palette.THEME["secondary"], label="Sichtungen" if source.key == "sightings" else source.label)
    elif o.color_mode == "individual":
        color = ColorSpec(mode="individual", column="ring")
    else:
        color = ColorSpec(mode=o.color_mode, column=date_col if o.color_mode in ("season", "year") else None)

    points: list[PointLayer] = []
    tracks: list[TrackLayer] = []
    if o.bubbles_by_place:
        place_col = source.place_column or "place"
        points.append(PointLayer(dataset_id=meta.id, name="Orte", lat_column=lat, lon_column=lon, shape="circle", color=color if o.color_mode != "season" else ColorSpec(mode="fixed", value=palette.THEME["secondary"], label="Ort (Größe = Anzahl Vögel)"),
                                 size=SizeSpec(min=8, max=44), dedupe="column", dedupe_column=place_col, date_column=date_col, label=LabelSpec(column=place_col, font_size=11) if o.labels else None, cluster=False))
    else:
        dedupe = "none" if (o.color_mode == "individual" or o.tracks) else "coords_per_group"
        points.append(PointLayer(dataset_id=meta.id, name="Sichtungen" if source.key == "sightings" else source.label, lat_column=lat, lon_column=lon, shape="circle", color=color,
                                 size=SizeSpec(min=o.point_size), dedupe=dedupe, date_column=date_col, label=LabelSpec(column=source.place_column, font_size=12) if (o.labels and source.place_column) else None, cluster=o.cluster))
    if o.show_ringing_sites and source.key == "sightings":
        points.append(PointLayer(dataset_id=meta.id, name="Beringungsort", lat_column="ringing_lat", lon_column="ringing_lon", shape="triangle", size=SizeSpec(min=14),
                                 color=ColorSpec(mode="fixed", value=palette.THEME["primary"], label="Beringungsort"), dedupe="coords", date_column="ringing_date", opacity=0.95))
    if o.tracks and source.has("ring") and source.key == "sightings":
        tracks.append(TrackLayer(dataset_id=meta.id, name="Bewegungen", group_column="ring", order_column=date_col, lat_column=lat, lon_column=lon, width=1.5, opacity=0.6))

    markers = list(o.markers)
    notes: list[str] = []
    if o.exclude_star and spec.filters.exclude_places:
        extra_markers, notes = await _excluded_markers(spec.filters.exclude_places)
        markers += extra_markers
    footnote = "; ".join(notes) if notes else None

    size: dict[str, Any] = {k: v for k, v in (("width", spec.width), ("height", spec.height)) if v}
    legend_title = o.legend_title or {"season": "Jahreszeit der Sichtung", "species": "Art", "individual": "Vögel", "year": "Jahr", "category": auto_label(o.color_column or ""), "fixed": None}[o.color_mode]
    try:
        ms = MapSpec(title=title, subtitle=spec.subtitle if spec.subtitle is not None else ("Kreis = Sichtung, Dreieck = Beringungsort" if (o.show_ringing_sites and source.key == "sightings" and not o.bubbles_by_place) else None),
                     points=points, tracks=tracks, markers=markers, legend=LegendSpec(title=legend_title), footnote=footnote, zoom=o.zoom, center=o.center, bounds=o.bounds, fit=o.fit, basemap=o.basemap, **size)
        model, summary = build_map_model(ms, runtime.datasets())
    except ValueError as exc:
        raise ViewError(str(exc)) from exc
    all_notes = notes + list(summary.get("notes") or [])
    return ViewResult(meta.id, "map", ms, model, summary, readable, description, int(len(df)), all_notes)


# ---------------------------------------------------------------- table


async def _build_table(spec: ViewSpec, source: Source, max_rows: int | None) -> ViewResult:
    sel = describe_filters(spec.filters, source)
    size: dict[str, Any] = {"width": spec.width} if spec.width else {}
    if spec.group_by:
        try:
            dims, bins = await _resolve_dims(spec, source, spec.group_by)
            sql, params = build_aggregate_sql(source, spec.filters, spec.metric.kind, spec.metric.column, list(dims))
        except SourceError as exc:
            raise ViewError(str(exc)) from exc
        res = await _query(sql, params, max_rows=max_rows)
        df = res.to_frame()
        _label_bins(df, dims, bins, source)
        metric_label = spec.metric_label(source)
        df = df.rename(columns={"value": metric_label})
        for d in dims:
            df = df.rename(columns={d.key: d.label})
        joined = " und ".join(d.label for d in dims)
        description = f"{metric_label} je {joined}; {sel}."
        title = spec.title or f"{metric_label} je {joined}"
        meta, readable = _save(df, name=title, sql=sql, params=params, description=description, truncated=res.truncated)
        columns = [ColumnSpec(name=str(c), label=str(c)) for c in df.columns]
        sort_by = spec.sort_by or (metric_label if spec.sort != "none" else None)
        highlight = [metric_label] if not spec.highlight_max else spec.highlight_max
    else:
        cols = spec.columns or _TABLE_DEFAULT_COLUMNS.get(source.key) or [c.name for c in source.columns]
        try:
            sql, params = build_rows_sql(source, spec.filters, cols)
        except SourceError as exc:
            raise ViewError(str(exc)) from exc
        res = await _query(sql, params, max_rows=max_rows)
        df = res.to_frame()
        description = f"{_cap(sel)} (eine Zeile je Eintrag)."
        title = spec.title or _cap(sel)
        meta, readable = _save(df, name=title, sql=sql, params=params, description=description, truncated=res.truncated)
        columns = [ColumnSpec(name=c) for c in cols]
        sort_by = spec.sort_by if spec.sort_by in df.columns else None
        highlight = spec.highlight_max
    try:
        ts = TableSpec(dataset_id=meta.id, title=title, subtitle=spec.subtitle if spec.subtitle is not None else (_cap(sel) if spec.group_by else None),
                       columns=columns, sort_by=sort_by, sort_desc=spec.sort_desc, limit=spec.table_limit, totals_row=spec.totals_row, highlight_max=highlight, **size)
        model, summary = build_table_model(ts, df)
    except ValueError as exc:
        raise ViewError(str(exc)) from exc
    return ViewResult(meta.id, "table", ts, model, summary, readable, description, int(len(df)), list(summary.get("notes") or []))


# ---------------------------------------------------------------- entry points


async def build_view(spec: ViewSpec, *, max_rows: int | None = None) -> ViewResult:
    """Compile, query, store the dataset and build the visual spec + model (no PNG rendering)."""
    try:
        source = get_source(spec.source)
    except SourceError as exc:
        raise ViewError(str(exc)) from exc
    if spec.kind == "map":
        return await _build_map(spec, source, max_rows)
    if spec.kind == "table":
        return await _build_table(spec, source, max_rows)
    return await _build_chart(spec, source, max_rows)


async def preview_view(spec: ViewSpec, max_rows: int = 5000) -> ViewResult:
    """Same as build_view with a row cap, for live previews in the web app."""
    return await build_view(spec, max_rows=max_rows)


def dimension_options(source_key: str) -> list[dict[str, Any]]:
    """Predefined dimensions plus the source's numeric/date columns (kind=bin → the UI shows the class controls)."""
    source = get_source(source_key)
    items: list[dict[str, Any]] = [{"key": d.key, "label": d.label, "kind": "dimension"} for d in DIMENSIONS.values() if source.key in d.sources]
    return items + bin_options(source)
