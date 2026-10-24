import pandas as pd

from vogelring_analytics.datasets import DatasetStore
from vogelring_analytics.reports import ReportSpec, ReportStore, build_report_model, md_html, write_docx
from vogelring_analytics.specs import TableSpec
from vogelring_analytics.tables import build_table_model
from vogelring_analytics.visuals import VisualStore


def _df():
    return pd.DataFrame({"ring": ["A1", "B2", "C3"], "ort": ["F, Ostpark", "OF, Hafen", "F, Niddapark"], "sichtungen": [12, 7, 7], "anteil_prozent": [50.0, 29.2, 20.8], "letzte": pd.to_datetime(["2025-06-01", "2024-01-05", None])})


def test_table_model():
    spec = TableSpec(dataset_id="x", title="Top", sort_by="sichtungen", limit=2, totals_row=True, highlight_max=["sichtungen"], columns=[{"name": "ring"}, {"name": "ort", "label": "Ort"}, {"name": "sichtungen", "bar": True}, {"name": "anteil_prozent"}, {"name": "letzte"}])
    model, summary = build_table_model(spec, _df())
    assert [c["format"] for c in model["columns"]] == ["link_ring", "text", "integer", "percent", "date"]
    assert model["rows"][0][0]["href"].endswith("/birds/A1") and model["rows"][0][2]["hl"] is True
    assert model["rows"][0][3]["text"] == "50,0 %" and model["rows"][0][4]["text"] == "01.06.2025"
    assert model["totals"][2] == "19" and summary["rows_total"] == 3 and "2 von 3" in summary["notes"][0]


def test_report_model_and_docx(tmp_path):
    ds = DatasetStore(tmp_path / "ds")
    vs = VisualStore(tmp_path / "viz")
    meta = ds.save(_df(), name="Top-Orte", sql="SELECT 1", description="Alle Sichtungen im Ostpark 2025.")
    vm = vs.create("chart", {"kind": "bar"}, {"kind": "bar", "width": 1200, "height": 700}, title="Sichtungen je Ort", dataset_ids=[meta.id], width=1200, height=700, summary={})
    spec = ReportSpec(title="Ostpark 2025", question="Wie viele Vögel?", key_findings=["**12** Sichtungen", "drei Vögel"],
                      sections=[{"heading": "Ergebnis", "text": "Es wurden **drei** Vögel gesehen.\n\n- A1\n- B2\n\n| a | b |\n|---|---|\n| 1 | 2 |", "visual_ids": [vm.id], "tables": [{"dataset_id": meta.id, "caption": "Top-Orte"}]}],
                      recommendations=["Weiter beobachten."])
    model, summary = build_report_model(spec, vs, ds)
    assert summary == {"sections": 1, "figures": 1, "tables": 1, "datasets": 1}
    assert model["datasets"][0]["description"] == "Alle Sichtungen im Ostpark 2025." and model["datasets"][0]["birds"] == 3
    assert "<strong>drei</strong>" in model["sections"][0]["html"]
    rs = ReportStore(tmp_path / "rp")
    rm = rs.create(spec.model_dump(mode="json"), model, {"title": spec.title, "visual_ids": [vm.id], "dataset_ids": [meta.id], "sections": 1})
    path = write_docx(model, rs.dir(rm.id) / "report.docx", vs)
    assert path.exists() and path.stat().st_size > 10_000
    assert "<em>" in md_html("*kursiv*")
