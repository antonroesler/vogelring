import pandas as pd
import pytest

from vogelring_analytics.charts import ChartBuildError, build_chart_model
from vogelring_analytics.datasets import DatasetStore
from vogelring_analytics.maps import MapBuildError, build_map_model
from vogelring_analytics.specs import ChartSpec, MapSpec


@pytest.fixture
def store(tmp_path):
    return DatasetStore(tmp_path)


def _sightings():
    return pd.DataFrame({
        "ring": ["A", "A", "B", "B", "C"],
        "date": pd.to_datetime(["2025-05-10", "2025-11-02", "2025-02-14", "2025-08-01", None]),
        "place": ["F, Ostpark", "OF, Mainufer", "F, Ostpark", "F, Rebstockpark", "F, Ostpark"],
        "species": ["Kanadagans", "Kanadagans", "Graugans", "Graugans", "Nilgans"],
        "lat": [50.12, 50.10, 50.12, 50.13, None],
        "lon": [8.70, 8.76, 8.70, 8.62, 8.70],
        "n": [3, 1, 2, 5, 1],
    })


def test_stacked_month_chart():
    df = pd.DataFrame({"monat": [1, 1, 2, 5], "ort": ["Ostpark", "Rebstock", "Ostpark", "Ostpark"], "v": [3, 2, 4, 1]})
    spec = ChartSpec(kind="stacked_bar", dataset_id="x", x="monat", y="v", series_column="ort", month_axis=True, show_totals=True,
                     stack_order=["Rebstock", "Ostpark"], colors={"Ostpark": "#2E8B57"}, annotations=[{"kind": "band", "from": 5, "to": 6, "label": "Mauser"}])
    model, summary = build_chart_model(spec, df)
    assert model["categories"] == ["Jan", "Feb", "Mär", "Apr", "Mai", "Jun", "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]
    assert [s["name"] for s in model["series"]] == ["Rebstock", "Ostpark"]
    assert model["series"][1]["color"] == "#2E8B57" and model["series"][1]["data"][0] == 3
    assert model["totals"][0] == 5 and model["totals"][4] == 1
    assert model["annotations"][0]["from"] == "Mai" and model["annotations"][0]["to"] == "Jun"
    assert summary["grand_total"] == 10


def test_count_and_sort_limit():
    df = _sightings()
    spec = ChartSpec(kind="bar", dataset_id="x", x="place", aggregate="count_distinct", y="ring", sort="desc", limit=2, horizontal=True)
    model, summary = build_chart_model(spec, df)
    assert model["categories"][0] == "F, Ostpark" and model["series"][0]["data"][0] == 3
    assert len(model["categories"]) == 2 and "begrenzt" in summary["notes"][0]


def test_chart_errors():
    with pytest.raises(ChartBuildError):
        build_chart_model(ChartSpec(kind="bar", dataset_id="x", x="nope", aggregate="count"), _sightings())
    with pytest.raises(ValueError):
        ChartSpec(kind="bar", dataset_id="x", x="place")  # y missing


def test_map_season_and_markers(store):
    meta = store.save(_sightings(), name="s", sql="")
    spec = MapSpec(title="t", points=[{"dataset_id": meta.id, "color": {"mode": "season"}, "shape": "circle", "label": {"column": "place"}}],
                   markers=[{"lat": 50.12, "lon": 8.70, "legend_label": "Ostpark"}], legend={"title": "Wiederfunde"})
    model, summary = build_map_model(spec, store)
    pts = model["layers"][0]["features"]
    assert len(pts) == 4 and summary["layers"][0]["classes"]["Apr–Jun"] == 1
    assert {e["label"] for e in model["legend"]["entries"]} >= {"Nov–Jan", "Feb–Mär", "Apr–Jun", "Jul–Okt", "Ostpark"}
    assert sum(1 for p in pts if "label" in p) == 3  # deduped labels: Ostpark, OF, Rebstock
    assert "1 Zeilen ohne Koordinaten" in summary["notes"][0]


def test_map_dedupe_column_and_tracks(store):
    meta = store.save(_sightings(), name="s", sql="")
    spec = MapSpec(points=[{"dataset_id": meta.id, "dedupe": "column", "dedupe_column": "place", "color": {"mode": "fixed", "label": "Orte"}}],
                   tracks=[{"dataset_id": meta.id, "group_column": "ring", "order_column": "date"}])
    model, summary = build_map_model(spec, store)
    assert summary["layers"][0]["points"] == 3
    assert summary["layers"][1]["tracks"] == 2  # A and B move; C has no coords
    assert model["layers"][1]["lines"][0]["coords"][0] == [50.12, 8.7]


def test_map_requires_layers_and_coords(store):
    with pytest.raises(ValueError):
        MapSpec(title="empty")
    meta = store.save(pd.DataFrame({"lat": [None], "lon": [None]}), name="s", sql="")
    with pytest.raises(MapBuildError):
        build_map_model(MapSpec(points=[{"dataset_id": meta.id}]), store)
