import pandas as pd
import pytest

from vogelring_analytics import runtime
from vogelring_analytics.datasets import DatasetStore
from vogelring_analytics.definitions import DefinitionStore
from vogelring_analytics.views import ViewError, ViewSpec, build_view, preview_view


class FakeResult:
    def __init__(self, df):
        self.df, self.truncated = df, False
        self.rows = [tuple(r) for r in df.itertuples(index=False)]

    def to_frame(self):
        return self.df


class FakeDB:
    """Returns canned frames depending on the SQL shape; records every call."""

    def __init__(self):
        self.calls = []

    async def query(self, sql, params=None, max_rows=None):
        self.calls.append((sql, list(params or ()), max_rows))
        if "COUNT(*) AS n, MIN(place) AS name" in sql:  # excluded-place centroid
            return FakeResult(pd.DataFrame({"lat": [50.12], "lon": [8.70], "n": [44], "name": ["F, Ostpark"]}))
        if " AS value FROM (" in sql:  # aggregate
            if "AS species" in sql:
                return FakeResult(pd.DataFrame({"month": [5, 5, 6], "species": ["Kanadagans", "Graugans", "Kanadagans"], "value": [3, 2, 4]}))
            return FakeResult(pd.DataFrame({"month": [5, 6, 7], "value": [3, 5, 1]}))
        return FakeResult(pd.DataFrame({  # raw rows
            "id": ["a", "b", "c"], "ring": ["A", "A", "B"], "date": pd.to_datetime(["2025-05-03", "2025-06-10", "2025-07-01"]),
            "place": ["F, Ostpark", "OF, Hafen", "F, Ostpark"], "species": ["Kanadagans", "Kanadagans", "Graugans"],
            "lat": [50.12, 50.10, 50.12], "lon": [8.70, 8.76, 8.70], "status": [None, "MG", None], "age": [1, 1, 2],
            "ringing_place": ["F, Ostpark", "F, Ostpark", "OF, Hafen"], "ringing_date": pd.to_datetime(["2020-06-01"] * 3),
            "ringing_lat": [50.12, 50.12, 50.10], "ringing_lon": [8.70, 8.70, 8.76], "km_from_ringing": [0.0, 4.6, 4.6],
            "melder": ["IR"] * 3,
        }))


@pytest.fixture
def env(tmp_path, monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(runtime, "database", lambda: db)
    monkeypatch.setattr(runtime, "datasets", lambda: DatasetStore(tmp_path / "ds"))
    monkeypatch.setattr(runtime, "definitions", lambda: DefinitionStore(tmp_path / "defs.json"))
    return db


async def test_chart_view_aggregate(env):
    spec = ViewSpec(kind="chart", chart_kind="stacked_bar", metric={"kind": "birds"}, dimension="month", color="species",
                    filters={"species": ["Kanadagans", "Graugans"], "places": ["Ostpark"], "years": [2025]}, annotate_moult=True, show_totals=True)
    r = await build_view(spec)
    assert r.visual_kind == "chart" and r.visual_spec.kind == "stacked_bar" and r.visual_spec.month_axis is True
    assert r.visual_spec.x == "month" and r.visual_spec.y == "value" and r.visual_spec.series_column == "species" and r.visual_spec.color_by == "species"
    assert r.model["categories"][0] == "Jan" and {s["name"] for s in r.model["series"]} == {"Kanadagans", "Graugans"}
    assert r.model["annotations"][0]["label"] == "Mauserzeit" and r.model["annotations"][0]["from"] == "Mai"
    assert r.description.startswith("Anzahl verschiedener Vögel je Monat und Art; Sichtungen der Arten Kanadagans und Graugans")
    assert "species IN ('Kanadagans', 'Graugans')" in r.sql and "%s" not in r.sql
    assert runtime.datasets().meta(r.dataset_id).description == r.description
    assert spec.describe().startswith("Gestapeltes Balkendiagramm: Anzahl verschiedener Vögel je Monat, Farbe nach Art – Sichtungen")
    assert r.visual_spec.title == "Anzahl verschiedener Vögel je Monat und Art" and "Ostpark" in r.visual_spec.subtitle


async def test_chart_view_errors(env):
    with pytest.raises(ValueError):
        ViewSpec(kind="chart", chart_kind="timeline")  # needs x_column/series_column
    with pytest.raises(ViewError, match="Heatmap"):
        await build_view(ViewSpec(kind="chart", chart_kind="heatmap", dimension="month"))
    with pytest.raises(ViewError, match="nicht verfügbar"):
        await build_view(ViewSpec(kind="chart", source="relationships", dimension="month"))
    with pytest.raises(ViewError, match="Unbekannte Datenquelle"):
        await build_view(ViewSpec(source="nope"))


async def test_raw_row_chart_timeline(env):
    r = await build_view(ViewSpec(kind="chart", chart_kind="timeline", x_column="date", series_column="ring", color_column="species", filters={"rings": ["A", "B"]}))
    assert r.visual_kind == "chart" and r.model["kind"] == "timeline" and r.model["rows"] == ["A", "B"]
    assert r.visual_spec.color_by == "species" and r.row_count == 3
    sql, params, _ = env.calls[-1]
    assert sql.startswith("SELECT date, ring, species, place, status FROM (") and params == ["A", "B"]


async def test_map_view(env):
    spec = ViewSpec(kind="map", filters={"species": ["Kanadagans"], "exclude_places": ["Rebstock"]}, map={"color_mode": "season", "show_ringing_sites": True, "tracks": True, "labels": True})
    r = await build_view(spec)
    assert r.visual_kind == "map" and r.visual_spec.title.startswith("Karte: Sichtungen der Art Kanadagans")
    names = [p.name for p in r.visual_spec.points]
    assert names == ["Sichtungen", "Beringungsort"] and r.visual_spec.points[1].shape == "triangle" and r.visual_spec.tracks
    assert r.visual_spec.markers[0].legend_label == "F, Ostpark (ausgeschlossen)" and "44 Sichtungen" in r.visual_spec.footnote
    assert r.model["legend"]["title"] == "Jahreszeit der Sichtung" and len(r.model["layers"]) == 4
    assert any("Rebstock" in d for d in [r.description]) and "place NOT ILIKE '%Rebstock%'" in r.sql
    assert spec.describe().startswith("Karte (Bewegungen): Sichtungen der Art Kanadagans, ohne ‚Rebstock‘")


async def test_map_bubbles_and_errors(env):
    r = await build_view(ViewSpec(kind="map", map={"bubbles_by_place": True, "color_mode": "fixed"}))
    p = r.visual_spec.points[0]
    assert p.dedupe == "column" and p.dedupe_column == "place" and p.label is None  # place names only on request
    r = await build_view(ViewSpec(kind="map", map={"bubbles_by_place": True, "color_mode": "fixed", "labels": True}))
    assert r.visual_spec.points[0].label.column == "place"
    with pytest.raises(ViewError, match="keine Koordinaten"):
        await build_view(ViewSpec(kind="map", source="relationships"))
    with pytest.raises(ViewError, match="color_column"):
        await build_view(ViewSpec(kind="map", map={"color_mode": "category"}))


async def test_table_views(env):
    r = await build_view(ViewSpec(kind="table", filters={"places": ["Ostpark"]}, table_limit=2))
    assert r.visual_kind == "table" and [c.name for c in r.visual_spec.columns][:3] == ["date", "ring", "species"]
    assert r.model["columns"][1]["label"] == "Ring" and r.model["shown_rows"] == 2 and r.model["total_rows"] == 3
    g = await build_view(ViewSpec(kind="table", group_by=["month"], metric={"kind": "sightings"}, totals_row=True))
    assert [c["label"] for c in g.model["columns"]] == ["Monat", "Anzahl Sichtungen"] and g.model["totals"][1] == "9"
    assert g.visual_spec.title == "Anzahl Sichtungen je Monat"
    pv = await preview_view(ViewSpec(kind="table"), max_rows=100)
    assert env.calls[-1][2] == 100 and pv.row_count == 3
