"""Classes (bins) for numeric and date columns used as categories."""

import pandas as pd
import pytest

from vogelring_analytics import runtime
from vogelring_analytics.binning import BinSpec, bin_values, fmt_de, nice_width, resolve_dimension
from vogelring_analytics.datasets import DatasetStore
from vogelring_analytics.definitions import DefinitionStore
from vogelring_analytics.sources import FilterSpec, SourceError, build_aggregate_sql, get_source
from vogelring_analytics.views import ViewSpec, build_view, dimension_options


class FakeResult:
    def __init__(self, df):
        self.df, self.truncated = df, False
        self.rows = [tuple(r) for r in df.itertuples(index=False)]

    def to_frame(self):
        return self.df


class FakeDB:
    def __init__(self):
        self.calls = []

    async def query(self, sql, params=None, max_rows=None):
        self.calls.append((sql, list(params or ()), max_rows))
        if sql.startswith("SELECT MIN(km_from_ringing) AS lo"):
            return FakeResult(pd.DataFrame({"lo": [0.3], "hi": [412.0], "p95": [380.0]}))
        if sql.startswith("SELECT MIN(sightings) AS lo"):
            return FakeResult(pd.DataFrame({"lo": [1], "hi": [9], "p95": [8]}))
        if sql.startswith("SELECT MIN(max_km) AS lo"):
            return FakeResult(pd.DataFrame({"lo": [0.0], "hi": [4050.0], "p95": [310.0]}))
        if " AS value FROM (" in sql:
            if "width_bucket" in sql:
                return FakeResult(pd.DataFrame({"km_from_ringing": [0, 1, 2, 3, 4, None], "value": [10, 20, 30, 40, 50, 5]}))
            if "FLOOR((km_from_ringing)" in sql:
                return FakeResult(pd.DataFrame({"km_from_ringing": [0.0, 50.0, 100.0, 400.0], "value": [100, 30, 20, 1]}))
            if "EXTRACT(YEAR FROM first_sighting)" in sql:
                return FakeResult(pd.DataFrame({"first_sighting": [2019, 2020, 2021], "value": [5, 7, 9]}))
            if "sightings AS sightings" in sql:
                return FakeResult(pd.DataFrame({"sightings": [1, 2, 3, 9], "value": [40, 20, 10, 1]}))
            if "LEAST(FLOOR((max_km)::double precision / 50.0) * 50.0, 300.0)" in sql:
                return FakeResult(pd.DataFrame({"max_km": [0.0, 50.0, 100.0, 300.0, None], "value": [900, 40, 20, 60, 12]}))
        return FakeResult(pd.DataFrame({  # raw rows
            "id": list("abcdef"), "ring": ["A", "A", "B", "B", "C", "C"], "date": pd.to_datetime(["2025-05-03", "2025-06-10", "2025-07-01", "2024-01-05", "2023-03-03", "2022-11-11"]),
            "place": ["Ostpark", "Hafen", "Ostpark", "Mainkai", "Hafen", "Nidda"], "species": ["Kanadagans"] * 6, "status": [None] * 6, "age": [1, 1, 2, 3, 1, 2],
            "ringing_place": ["Posthof", "Posthof", "Posthof", "Griesheim", "Griesheim", "Posthof"], "ringing_date": pd.to_datetime(["2020-06-01"] * 6),
            "km_from_ringing": [139.2, 4.9, 303.9, 0.4, 24.0, None], "lat": [50.1] * 6, "lon": [8.7] * 6, "melder": ["IR"] * 6,
        }))


@pytest.fixture
def env(tmp_path, monkeypatch):
    db = FakeDB()
    monkeypatch.setattr(runtime, "database", lambda: db)
    monkeypatch.setattr(runtime, "datasets", lambda: DatasetStore(tmp_path / "ds"))
    monkeypatch.setattr(runtime, "definitions", lambda: DefinitionStore(tmp_path / "defs.json"))
    return db


def test_labels_and_widths():
    assert fmt_de(10.0) == "10" and fmt_de(1234.5) == "1.234,5" and fmt_de(2.5) == "2,5"
    assert nice_width(0.3, 412, None, False) == 50.0  # 412/8 = 51.5 → nearest round width
    assert nice_width(0, 80, 8, False) == 10.0
    assert nice_width(1, 9, None, True) == 1.0  # small integer range: one class per value
    assert nice_width(0, 2000, 8, True) == 200.0
    col = get_source("sightings").column("km_from_ringing")
    labels, order, used = bin_values(pd.Series([139.2, 4.9, 303.9, 0.4, None]), BinSpec(column="km_from_ringing", width=100), col)
    assert labels.tolist() == ["100–200 km", "0–100 km", "300–400 km", "0–100 km", "unbekannt"]
    assert order == ["0–100 km", "100–200 km", "300–400 km", "unbekannt"]
    labels, order, _ = bin_values(pd.Series([0.5, 3, 7, 50, 200]), BinSpec(column="km_from_ringing", edges=[1, 5, 20, 100]), col)
    assert labels.tolist() == ["< 1 km", "1–5 km", "5–20 km", "20–100 km", "≥ 100 km"] and order[-2] == "≥ 100 km"
    birds = get_source("birds")
    labels, order, used = bin_values(pd.Series([1, 2, 2, 9]), BinSpec(column="sightings"), birds.column("sightings"))
    assert labels.tolist() == ["1", "2", "2", "9"] and used.width == 1.0
    labels, order, used = bin_values(pd.Series([3, 48, 120]), BinSpec(column="sightings", width=10), birds.column("sightings"))
    assert labels.tolist() == ["0–9", "40–49", "120–129"]  # integer classes are inclusive
    labels, order, _ = bin_values(pd.to_datetime(pd.Series(["2024-05-01", "2019-12-24", None])), BinSpec(column="first_sighting", date_part="season"), birds.column("first_sighting"))
    assert labels.tolist() == ["Apr–Jun", "Nov–Jan", "unbekannt"] and order[0] == "Nov–Jan"


def test_bin_dimension_sql_and_errors():
    src = get_source("sightings")
    d = resolve_dimension(src, "km_from_ringing", {"km_from_ringing": BinSpec(column="km_from_ringing", width=10)})
    assert d.label == "km vom Beringungsort (Klassen à 10 km)" and "FLOOR((km_from_ringing)::double precision / 10.0) * 10.0" in d.expr(src)
    d = resolve_dimension(src, "km_from_ringing", {"km_from_ringing": BinSpec(column="km_from_ringing", edges=[1, 5, 20])})
    assert "width_bucket((km_from_ringing)::double precision, ARRAY[1.0, 5.0, 20.0])" in d.expr(src)
    sql, _ = build_aggregate_sql(src, FilterSpec(), "sightings", None, [d])
    assert "GROUP BY 1 ORDER BY MIN(width_bucket" in sql
    birds = get_source("birds")
    d = resolve_dimension(birds, "first_sighting", {})
    assert d.label == "Erste Sichtung – Jahr" and d.expr(birds) == "EXTRACT(YEAR FROM first_sighting)::int"
    with pytest.raises(SourceError, match="braucht eine Klassenbreite"):
        build_aggregate_sql(src, FilterSpec(), "sightings", None, [resolve_dimension(src, "km_from_ringing", {})])
    with pytest.raises(SourceError, match="Zahlen-/Datumsspalten in Klassen"):
        resolve_dimension(src, "comment", {})  # free text, neither a dimension nor binnable
    assert resolve_dimension(src, "month", {}).key == "month"
    opts = dimension_options("birds")
    assert {"key": "max_km", "label": "Weitester Fund (km) (in Klassen)", "kind": "bin", "type": "number", "unit": "km"} in opts
    assert all(o["kind"] == "dimension" for o in opts if o["key"] in ("year", "species"))


async def test_aggregate_view_with_auto_width(env):
    spec = ViewSpec(kind="chart", chart_kind="bar", source="sightings", dimension="km_from_ringing", metric={"kind": "sightings"})
    r = await build_view(spec)
    assert any(c[0].startswith("SELECT MIN(km_from_ringing) AS lo") for c in env.calls)
    assert r.model["categories"] == ["0–50 km", "50–100 km", "100–150 km", "400–450 km"]
    assert r.visual_spec.sort == "none" and r.visual_spec.x_axis.title == "km vom Beringungsort (Klassen à 50 km)"
    assert r.description.startswith("Anzahl Sichtungen je km vom Beringungsort (Klassen à 50 km)")
    assert spec.describe().startswith("Balkendiagramm: Anzahl Sichtungen je km vom Beringungsort (Klassen)")


async def test_aggregate_view_with_edges_keeps_order_and_unknown(env):
    spec = ViewSpec(kind="chart", chart_kind="bar", source="sightings", dimension="km_from_ringing", bins=[{"column": "km_from_ringing", "edges": [1, 5, 20, 100]}])
    r = await build_view(spec)
    assert r.model["categories"] == ["< 1 km", "1–5 km", "5–20 km", "20–100 km", "≥ 100 km", "unbekannt"]
    assert r.model["series"][0]["data"] == [10, 20, 30, 40, 50, 5]
    assert not any("MIN(km_from_ringing) AS lo" in c[0] for c in env.calls)


async def test_table_group_by_bin_and_date_part(env):
    spec = ViewSpec(kind="table", source="birds", group_by=["first_sighting"], metric={"kind": "birds"})
    r = await build_view(spec)
    assert [c.label for c in r.visual_spec.columns][0] == "Erste Sichtung – Jahr" and r.model["rows"][0][0]["text"] == "2019"
    spec = ViewSpec(kind="chart", source="birds", dimension="sightings", metric={"kind": "birds"})
    r = await build_view(spec)
    assert r.model["categories"] == ["1", "2", "3", "9"]  # small integer range: no classes needed


async def test_sankey_bins_numeric_target_automatically(env):
    spec = ViewSpec(kind="chart", chart_kind="sankey", source="sightings", source_column="ringing_place", target_column="km_from_ringing")
    r = await build_view(spec)
    nodes = [n["label"] for n in r.model["sankey"]["nodes"]]
    assert r.visual_spec.target_column == "km_from_ringing_klasse" and r.model["sankey"]["keep_order"] is True
    assert [n for n in nodes if "km" in n] == ["0–20 km", "20–40 km", "≥ 120 km"]  # width from the 95th percentile, open top class
    assert any("automatisch eingeteilt: Klassen à 20 km, ab 120 km zusammengefasst" in n for n in r.notes)
    ds = runtime.datasets().load(r.dataset_id)
    assert "km_from_ringing_klasse" in ds.columns and "km_from_ringing" in ds.columns


async def test_boxplot_and_histogram_with_explicit_bins(env):
    spec = ViewSpec(kind="chart", chart_kind="boxplot", source="sightings", x_column="age", y_column="km_from_ringing")
    r = await build_view(spec)
    assert r.visual_spec.x == "age_label" and r.model["categories"][0] in ("adult", "diesjährig", "vorjährig")
    spec = ViewSpec(kind="chart", chart_kind="histogram", source="sightings", x_column="km_from_ringing", bins=[{"column": "km_from_ringing", "edges": [1, 20, 100]}])
    r = await build_view(spec)
    assert r.visual_spec.kind == "bar" and r.model["categories"] == ["< 1 km", "1–20 km", "20–100 km", "≥ 100 km", "unbekannt"]
    assert r.model["series"][0]["data"] == [1, 1, 1, 2, 1]


async def test_auto_width_caps_skewed_tail(env):
    spec = ViewSpec(kind="chart", chart_kind="bar", source="birds", dimension="max_km", metric={"kind": "birds"})
    r = await build_view(spec)
    assert r.model["categories"] == ["0–50 km", "50–100 km", "100–150 km", "≥ 300 km", "unbekannt"]
    assert "ab 300 km zusammengefasst" in r.visual_spec.x_axis.title
    col = get_source("birds").column("max_km")
    labels, order, used = bin_values(pd.Series([float(x) for x in range(1, 96)] + [3900.0] * 5), BinSpec(column="max_km"), col)
    assert (used.width, used.max) == (10.0, 90.0) and labels.tolist()[-1] == "≥ 90 km" and labels.tolist()[0] == "0–10 km" and order[-2:] == ["≥ 90 km", "unbekannt"]
    labels, _, used = bin_values(pd.Series([3.0, 48.0, 120.0]), BinSpec(column="max_km", width=10, max=100), col)
    assert labels.tolist() == ["0–10 km", "40–50 km", "≥ 100 km"]


def test_binspec_validation():
    with pytest.raises(ValueError):
        BinSpec(column="x", width=5, edges=[1, 2])
    with pytest.raises(ValueError):
        BinSpec(column="x", edges=[5, 1])
    with pytest.raises(ValueError, match="jede Spalte nur einmal"):
        ViewSpec(bins=[{"column": "max_km"}, {"column": "max_km", "width": 5}])
