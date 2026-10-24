import pandas as pd
import pytest
from pydantic import TypeAdapter

from vogelring_analytics.datasets import DatasetStore
from vogelring_analytics.transforms import Op, TransformError, apply_ops, describe_ops

OPS = TypeAdapter(list[Op])


def _df():
    return pd.DataFrame({
        "ring": ["A", "A", "B", "C"],
        "date": pd.to_datetime(["2024-05-01", "2024-11-03", "2025-02-10", "2025-06-30"]),
        "place": ["F, Ostpark", "OF, Hafen", "F, Ostpark", "F, Ostpark"],
        "lat": [50.12, 50.10, 50.12, 50.12], "lon": [8.70, 8.76, 8.70, 8.70],
        "ringing_lat": [50.12] * 4, "ringing_lon": [8.70] * 4,
    })


def test_filter_derive_group(tmp_path):
    store = DatasetStore(tmp_path)
    ops = OPS.validate_python([
        {"op": "derive", "column": "jahr", "kind": "year", "source": "date"},
        {"op": "derive", "column": "saison", "kind": "season", "source": "date"},
        {"op": "derive", "column": "km", "kind": "distance_km", "lat_column": "ringing_lat", "lon_column": "ringing_lon", "lat2_column": "lat", "lon2_column": "lon"},
        {"op": "filter", "column": "place", "condition": "contains", "value": "ostpark"},
        {"op": "group", "by": ["jahr"], "aggregations": [{"func": "count"}, {"column": "ring", "func": "count_distinct", "as": "voegel"}]},
        {"op": "sort", "by": ["jahr"], "descending": False},
    ])
    out = apply_ops(_df(), ops, store)
    assert out.columns.tolist() == ["jahr", "Anzahl", "voegel"]
    assert out["Anzahl"].tolist() == [1, 2] and out["voegel"].tolist() == [1, 2]
    assert "gefiltert" in describe_ops(ops) and "zusammengefasst" in describe_ops(ops)


def test_bucket_pivot_join(tmp_path):
    store = DatasetStore(tmp_path)
    other = store.save(pd.DataFrame({"ring": ["A", "B"], "art": ["Kanadagans", "Graugans"]}), name="arten", sql="")
    ops = OPS.validate_python([
        {"op": "derive", "column": "km", "kind": "distance_km", "lat_column": "ringing_lat", "lon_column": "ringing_lon", "lat2_column": "lat", "lon2_column": "lon"},
        {"op": "derive", "column": "klasse", "kind": "bucket", "source": "km", "edges": [0, 1, 5, 20]},
        {"op": "join", "other_dataset_id": other.id, "on": ["ring"], "how": "left"},
        {"op": "pivot", "index": "art", "columns": "klasse", "func": "count"},
    ])
    out = apply_ops(_df(), ops, store)
    assert "0–1" in out.columns and "1–5" in out.columns
    assert out.loc[out["art"] == "Kanadagans", "1–5"].iloc[0] == 1


def test_errors(tmp_path):
    store = DatasetStore(tmp_path)
    with pytest.raises(TransformError):
        apply_ops(_df(), OPS.validate_python([{"op": "select", "columns": ["nope"]}]), store)
    with pytest.raises(TransformError):
        apply_ops(_df(), OPS.validate_python([{"op": "filter", "column": "lat", "condition": "between", "value": [1]}]), store)
