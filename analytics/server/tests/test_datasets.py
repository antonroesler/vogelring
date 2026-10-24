import pandas as pd

from vogelring_analytics.datasets import DatasetStore, column_summary, preview_table


def test_roundtrip(tmp_path):
    store = DatasetStore(tmp_path)
    df = pd.DataFrame({"ring": ["A1", "A2"], "n": [1, 2], "date": pd.to_datetime(["2025-05-01", "2025-06-02"])})
    meta = store.save(df, name="t", sql="SELECT 1")
    assert meta.id.startswith("ds_") and meta.row_count == 2
    assert [c["type"] for c in meta.columns] == ["text", "int", "date"]
    loaded = store.load(meta.id)
    assert loaded.equals(df)
    assert store.list()[0].id == meta.id
    assert store.exists(meta.id) and not store.exists("ds_nope")


def test_preview_and_summary():
    df = pd.DataFrame({"place": ["a", "b", "a"], "v": [1.5, None, 3.0]})
    text = preview_table(df, n=2)
    assert text.splitlines()[0] == "place | v"
    assert "1 weitere" in text
    summary = column_summary(df)
    assert summary[0]["distinct"] == 2 and summary[1]["non_null"] == 2
