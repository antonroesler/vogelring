import pandas as pd
import pytest

from vogelring_analytics.charts import ChartBuildError, build_chart_model
from vogelring_analytics.specs import ChartSpec


def _df():
    return pd.DataFrame({
        "ring": ["A", "A", "A", "B", "B", "C"],
        "date": pd.to_datetime(["2024-05-01", "2024-11-03", "2025-02-10", "2025-02-11", "2025-06-30", "2025-07-01"]),
        "place": ["Ostpark", "Hafen", "Ostpark", "Ostpark", "Nidda", "Ostpark"],
        "von": ["Ostpark", "Ostpark", "Hafen", "Ostpark", "Ostpark", "Nidda"],
        "nach": ["Hafen", "Ostpark", "Ostpark", "Nidda", "Nidda", "Ostpark"],
        "km": [3.0, 3.0, 0.5, 8.0, 8.5, 12.0],
        "species": ["Kanadagans", "Kanadagans", "Kanadagans", "Graugans", "Graugans", "Nilgans"],
    })


def test_timeline():
    model, summary = build_chart_model(ChartSpec(kind="timeline", dataset_id="x", x="date", series_column="ring", color_by="season"), _df())
    assert model["rows"] == ["A", "B", "C"] and len(model["timeline"]["points"]) == 6
    assert {c["name"] for c in model["timeline"]["classes"]} == {"Apr–Jun", "Nov–Jan", "Feb–Mär", "Jul–Okt"}
    assert summary["span_days"] > 400


def test_calendar_and_boxplot():
    model, summary = build_chart_model(ChartSpec(kind="calendar", dataset_id="x", x="date"), _df())
    assert model["calendar"]["years"] == [2024, 2025] and summary["days_with_data"] == 6
    model, summary = build_chart_model(ChartSpec(kind="boxplot", dataset_id="x", x="species", y="km"), _df())
    assert model["categories"] == ["Kanadagans", "Graugans", "Nilgans"] and summary["stats"]["Graugans"]["median"] == 8.25


def test_sankey_cycle_and_graph():
    model, summary = build_chart_model(ChartSpec(kind="sankey", dataset_id="x", source_column="von", target_column="nach"), _df())
    names = [n["name"] for n in model["sankey"]["nodes"]]
    assert any(n.endswith("​") for n in names)  # cycle → bipartite
    assert summary["links"] == 5
    model, summary = build_chart_model(ChartSpec(kind="graph", dataset_id="x", source_column="von", target_column="nach", edge_label_column="species"), _df())
    assert summary["nodes"] == 3 and model["graph"]["edge_types"]


def test_facets_and_validation():
    df = _df().assign(monat=lambda d: d["date"].dt.month)
    model, summary = build_chart_model(ChartSpec(kind="bar", dataset_id="x", x="monat", aggregate="count", facet_column="species", month_axis=True), df)
    assert len(model["facets"]) == 3 and model["categories"][0] == "Jan" and summary["facets"] == ["Kanadagans", "Graugans", "Nilgans"]
    with pytest.raises(ValueError):
        ChartSpec(kind="sankey", dataset_id="x", x="date")
    with pytest.raises(ChartBuildError):
        build_chart_model(ChartSpec(kind="timeline", dataset_id="x", x="nope", series_column="ring"), _df())
