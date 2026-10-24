"""Typed visual specifications (tool inputs). Validation errors are surfaced to the model."""

from __future__ import annotations

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

HexColor = Annotated[str, Field(pattern=r"^#[0-9a-fA-F]{6}$", description="Hex colour like #D7263D")]


class _Spec(BaseModel):
    model_config = ConfigDict(extra="forbid")


# ---------------------------------------------------------------- shared


class ColorSpec(_Spec):
    mode: Literal["fixed", "season", "category", "individual", "species", "year"] = Field(
        "fixed",
        description=(
            "fixed: one colour. season: Ingo's convention by month of `column` (Nov–Jan dunkelblau, Feb–Mär gelb, "
            "Apr–Jun grün, Jul–Okt rot). category: distinct values of `column` get palette colours. "
            "individual: one colour per bird (`column`, default ring). species: species colours of the app. "
            "year: one colour per year of a date column."
        ),
    )
    column: str | None = Field(None, description="Column driving the colour (date for season/year, ring for individual, any text for category).")
    value: HexColor | None = Field(None, description="Colour for mode=fixed. Default theme teal.")
    palette: dict[str, HexColor] | None = Field(None, description="Explicit value→colour mapping (category/individual/species).")
    order: list[str] | None = Field(None, description="Legend/category order (category mode).")
    label: str | None = Field(None, description="Legend label for mode=fixed (e.g. 'Wiederfund').")


class SizeSpec(_Spec):
    column: str | None = Field(None, description="Numeric column scaling marker size (e.g. Anzahl Individuen). None = constant size.")
    min: float = Field(7, ge=2, le=60, description="Marker diameter in px (constant size or lower bound).")
    max: float = Field(30, ge=2, le=120, description="Upper bound diameter in px when `column` is set.")
    scale: Literal["sqrt", "linear"] = "sqrt"


class LabelSpec(_Spec):
    column: str = Field(..., description="Column to print next to the marker (e.g. place, ring).")
    font_size: int = Field(12, ge=8, le=40)
    placement: Literal["auto", "right", "left", "top", "bottom"] = "auto"
    only_values: list[str] | None = Field(None, description="Only label rows whose value is in this list.")
    dedupe: bool = Field(True, description="Print each distinct label text only once (first occurrence).")


Shape = Literal["circle", "triangle", "star", "square", "diamond"]


class PointLayer(_Spec):
    dataset_id: str
    name: str | None = Field(None, description="Layer/legend name, e.g. 'Wiederfunde' or 'Beringungsorte'.")
    lat_column: str = "lat"
    lon_column: str = "lon"
    shape: Shape = "circle"
    color: ColorSpec = Field(default_factory=ColorSpec)
    size: SizeSpec = Field(default_factory=SizeSpec)
    label: LabelSpec | None = None
    opacity: float = Field(0.9, ge=0.1, le=1)
    date_column: str = Field("date", description="Used by season/year colouring and tooltips.")
    tooltip_columns: list[str] | None = Field(None, description="Columns shown on hover (default: ring, date, place, species if present).")
    cluster: bool | None = Field(None, description="Cluster overlapping markers. Default: only when >400 points.")
    dedupe: Literal["none", "coords", "coords_per_group", "column"] = Field(
        "none",
        description=(
            "Collapse rows into one marker: coords = same coordinates (~10 m), coords_per_group = same coordinates per colour "
            "class, column = same value of dedupe_column (e.g. place; marker placed at the mean coordinate). Marker size then "
            "reflects the number of distinct rings (or rows) unless size.column is set."
        ),
    )
    dedupe_column: str | None = Field(None, description="Grouping column for dedupe=column (e.g. place).")


class TrackLayer(_Spec):
    dataset_id: str
    name: str | None = None
    group_column: str = Field("ring", description="One polyline per distinct value (e.g. per bird).")
    order_column: str = Field("date", description="Sort key along the line.")
    lat_column: str = "lat"
    lon_column: str = "lon"
    color: ColorSpec = Field(default_factory=lambda: ColorSpec(mode="individual", column="ring"))
    width: float = Field(2, ge=0.5, le=10)
    opacity: float = Field(0.8, ge=0.1, le=1)
    arrows: bool = True


class FlowLayer(_Spec):
    dataset_id: str
    name: str | None = None
    from_lat_column: str
    from_lon_column: str
    to_lat_column: str
    to_lon_column: str
    weight_column: str | None = Field(None, description="Numeric column for line width (e.g. Anzahl Vögel).")
    color: HexColor = "#222222"
    min_width: float = Field(1, ge=0.2, le=10)
    max_width: float = Field(8, ge=0.5, le=30)
    opacity: float = Field(0.75, ge=0.1, le=1)
    arrows: bool = True
    label_column: str | None = Field(None, description="Optional column printed at the line midpoint.")


class MarkerSpec(_Spec):
    lat: float
    lon: float
    shape: Shape = "star"
    color: HexColor = "#00436C"
    size: float = Field(24, ge=6, le=80)
    label: str | None = None
    legend_label: str | None = Field(None, description="Entry in the legend, e.g. 'Ostpark (ausgeschlossen)'.")


class LegendSpec(_Spec):
    title: str | None = None
    show: bool = True
    position: Literal["topright", "topleft", "bottomright", "bottomleft"] = "topright"


class MapSpec(_Spec):
    title: str | None = Field(None, description="Headline printed above the map.")
    subtitle: str | None = None
    points: list[PointLayer] = Field(default_factory=list)
    tracks: list[TrackLayer] = Field(default_factory=list)
    flows: list[FlowLayer] = Field(default_factory=list)
    markers: list[MarkerSpec] = Field(default_factory=list)
    legend: LegendSpec = Field(default_factory=LegendSpec)
    footnote: str | None = Field(None, description="Small text under the map, e.g. counts of hidden points.")
    zoom: int | None = Field(None, ge=5, le=18, description="Fixed zoom. Default: fit to data.")
    center: tuple[float, float] | None = Field(None, description="[lat, lon] centre when zoom is fixed.")
    basemap: Literal["light", "dark", "osm", "voyager"] = "light"
    width: int = Field(1400, ge=600, le=2400)
    height: int = Field(900, ge=400, le=2000)
    fit_padding: int = Field(48, ge=0, le=200)
    scale_bar: bool = True

    @model_validator(mode="after")
    def _has_layers(self) -> "MapSpec":
        if not (self.points or self.tracks or self.flows or self.markers):
            raise ValueError("A map needs at least one layer (points, tracks, flows or markers).")
        return self


# ---------------------------------------------------------------- charts


class AxisSpec(_Spec):
    title: str | None = None
    min: float | None = None
    max: float | None = None
    format: Literal["number", "percent", "integer"] = "number"


class AnnotationSpec(_Spec):
    kind: Literal["band", "line"] = "band"
    from_: str | float = Field(..., alias="from", description="Category value or number where the band/line starts.")
    to: str | float | None = Field(None, description="End category/number (band only).")
    label: str | None = None
    color: HexColor = "#228096"

    model_config = ConfigDict(extra="forbid", populate_by_name=True)


ChartKind = Literal[
    "bar", "stacked_bar", "line", "area", "scatter", "pie", "heatmap", "histogram",
    "timeline", "calendar", "sankey", "boxplot", "graph",
]


class ChartSpec(_Spec):
    kind: ChartKind
    dataset_id: str
    title: str | None = None
    subtitle: str | None = None
    x: str | None = Field(None, description="Column for the x axis / categories (for pie: the slice label; timeline/calendar: the date column). Not used by sankey/graph.")
    y: str | list[str] | None = Field(
        None,
        description="Value column(s). Several columns = several series (wide format). None with aggregate=count counts rows.",
    )
    series_column: str | None = Field(None, description="Long format: column whose distinct values become series (e.g. place).")
    aggregate: Literal["none", "sum", "count", "mean", "count_distinct"] = Field(
        "none", description="How to combine rows sharing the same x (and series). count_distinct needs `y`."
    )
    stack: bool | None = Field(None, description="Stack series (default true for stacked_bar/area).")
    stack_order: list[str] | None = Field(None, description="Series order bottom→top (stacked) or left→right.")
    colors: dict[str, HexColor] | None = Field(None, description="Series/category → colour.")
    color_by: Literal["theme", "species", "season"] = Field("theme", description="Default palette when `colors` is not given.")
    sort: Literal["none", "asc", "desc", "x"] = Field("none", description="Sort categories by total value or by x.")
    limit: int | None = Field(None, ge=1, le=500, description="Keep only the first N categories after sorting (Top N).")
    horizontal: bool = False
    show_values: bool = Field(False, description="Print values on bars/points.")
    show_totals: bool = Field(False, description="Print stack totals above stacked bars.")
    month_axis: bool = Field(False, description="x holds month numbers 1–12: show German month names, fill missing months.")
    x_axis: AxisSpec = Field(default_factory=AxisSpec)
    y_axis: AxisSpec = Field(default_factory=AxisSpec)
    annotations: list[AnnotationSpec] = Field(default_factory=list)
    legend_title: str | None = None
    footnote: str | None = None
    width: int = Field(1200, ge=500, le=2400)
    height: int = Field(700, ge=350, le=1600)
    bins: int | None = Field(None, ge=2, le=200, description="histogram only")
    heat_value: str | None = Field(None, description="heatmap: value column; x = columns axis, series_column = rows axis.")
    facet_column: str | None = Field(
        None,
        description="Small multiples: one sub-chart per distinct value of this column (bar/stacked_bar/line/area), max 12 facets, shared axes.",
    )
    facet_columns: int = Field(3, ge=1, le=4, description="Facets per row.")
    # timeline
    end_column: str | None = Field(None, description="timeline: optional end date column → draws ranges instead of dots.")
    color_column: str | None = Field(None, description="timeline/scatter: column driving the dot colour (category), e.g. place or species.")
    # sankey / graph
    source_column: str | None = Field(None, description="sankey/graph: column with the start node (e.g. Beringungsort).")
    target_column: str | None = Field(None, description="sankey/graph: column with the end node (e.g. Wiederfundort).")
    edge_label_column: str | None = Field(None, description="graph: column shown on the edge (e.g. relationship type).")
    max_nodes: int = Field(60, ge=5, le=300, description="sankey/graph: keep the strongest N nodes.")
    category_order: dict[str, list[str]] | None = Field(None, description="Fixed order of category labels per column (binned classes); categories not listed follow alphabetically.")

    @model_validator(mode="after")
    def _check(self) -> "ChartSpec":
        k = self.kind
        if k not in ("sankey", "graph") and not self.x:
            raise ValueError("x is required (category/date column).")
        if k == "heatmap" and not (self.series_column and self.heat_value):
            raise ValueError("heatmap needs x (columns), series_column (rows) and heat_value.")
        if k == "pie" and self.series_column:
            raise ValueError("pie uses x (labels) and y (values) only.")
        if k in ("sankey", "graph") and not (self.source_column and self.target_column):
            raise ValueError(f"{k} needs source_column and target_column (y = weight column, optional).")
        if k == "timeline" and not self.series_column:
            raise ValueError("timeline needs x (date column) and series_column (one row per value, e.g. ring).")
        if k == "boxplot" and not self.y:
            raise ValueError("boxplot needs x (category) and y (numeric column).")
        if k == "calendar" and self.y is None and self.aggregate not in ("count", "count_distinct"):
            self.aggregate = "count"
        exempt = ("histogram", "heatmap", "timeline", "calendar", "sankey", "graph")
        if self.y is None and self.aggregate != "count" and k not in exempt:
            raise ValueError("y is required unless aggregate='count'.")
        if self.aggregate == "count_distinct" and not self.y:
            raise ValueError("count_distinct needs y (the column whose distinct values are counted).")
        if self.facet_column and k not in ("bar", "stacked_bar", "line", "area"):
            raise ValueError("facet_column works with bar, stacked_bar, line and area only.")
        return self


# ---------------------------------------------------------------- tables


class ColumnSpec(_Spec):
    name: str = Field(..., description="Dataset column.")
    label: str | None = Field(None, description="Header text (German). Default: column name.")
    format: Literal["auto", "text", "integer", "number", "percent", "date", "link_ring", "link_sighting"] = Field(
        "auto", description="percent expects 0–100; link_ring renders the ring as a vogelring.com link; link_sighting the sighting id."
    )
    decimals: int | None = Field(None, ge=0, le=6)
    align: Literal["auto", "left", "right", "center"] = "auto"
    width: int | None = Field(None, ge=40, le=600, description="Column width in px.")
    bar: bool = Field(False, description="Draw an in-cell bar proportional to the value (numeric columns).")


class TableSpec(_Spec):
    dataset_id: str
    title: str | None = None
    subtitle: str | None = None
    columns: list[ColumnSpec] | None = Field(None, description="Columns to show, in order. Default: all.")
    sort_by: str | None = None
    sort_desc: bool = True
    limit: int = Field(50, ge=1, le=300, description="Rows rendered (the XLSX export always has all rows).")
    totals_row: bool = Field(False, description="Sum numeric columns in a final row.")
    highlight_max: list[str] = Field(default_factory=list, description="Columns whose maximum cell is highlighted.")
    row_number: bool = Field(True, description="Show a rank/row-number column.")
    footnote: str | None = None
    width: int = Field(1100, ge=500, le=2400)
    font_size: int = Field(13, ge=10, le=18)


class VisualPatch(_Spec):
    """JSON merge patch for update_visual: keys mirror the spec, null deletes."""

    model_config = ConfigDict(extra="allow")
