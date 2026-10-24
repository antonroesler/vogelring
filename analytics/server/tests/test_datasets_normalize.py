import json
import uuid

import pandas as pd

from vogelring_analytics.datasets import DatasetStore, normalize_frame


def test_normalize_frame_converts_uuid_and_bytes():
    u = uuid.uuid4()
    df = pd.DataFrame({"id": [u, None], "blob": [u.bytes, b"\x97\x01"], "name": ["a", "b"], "n": [1, 2]})
    out = normalize_frame(df)
    assert out["id"][0] == str(u)
    assert out["blob"][0] == str(u)
    assert out["blob"][1] == "9701"
    json.loads(out.to_json(orient="records", date_format="iso", force_ascii=False))


def test_store_roundtrip_with_uuid(tmp_path):
    store = DatasetStore(root=tmp_path)
    u = uuid.uuid4()
    meta = store.save(pd.DataFrame({"id": [u], "v": [1]}), name="t", sql="select 1")
    df = store.load(meta.id)
    assert df["id"][0] == str(u)
    json.loads(df.to_json(orient="records", date_format="iso", force_ascii=False))
