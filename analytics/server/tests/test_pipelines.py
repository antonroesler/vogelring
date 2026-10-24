import sys
import types
from dataclasses import dataclass

import pandas as pd
import pytest

from vogelring_analytics import pipelines, runtime, visual_service
from vogelring_analytics.datasets import DatasetStore
from vogelring_analytics.pipelines import Parameter, PipelineError, PipelineSpec, builtin_specs, describe_pipeline, run_pipeline, substitute, validate_params


def _spec(**kw):
    base = {"name": "t", "description": "Test.", "parameters": [], "steps": [{"id": "s1", "kind": "export", "spec": {"dataset_id": "x"}}]}
    base.update(kw)
    return PipelineSpec.model_validate(base)


def test_substitute_typed_and_string_and_sql():
    params = {"ort": "O'Park", "jahr": 2025, "arten": ["Graugans", "Nilgans"], "leer": None}
    steps = {"a": {"dataset_id": "ds_1", "summary": {"n": 3}}}
    out = substitute({"t": "{{ort}} {{jahr}}", "y": "{{jahr}}", "l": "{{arten}}", "sql": "place ILIKE '%' || {{ort|sql}} || '%' AND x IN {{arten|sql}}", "ds": "$steps.a.dataset_id", "n": "$steps.a.summary.n", "none": "{{leer}}", "nested": ["{{ort}}", {"k": "{{jahr}}"}]}, params, steps)
    assert out["t"] == "O'Park 2025" and out["y"] == 2025 and out["l"] == ["Graugans", "Nilgans"]
    assert out["sql"] == "place ILIKE '%' || 'O''Park' || '%' AND x IN ('Graugans', 'Nilgans')"
    assert out["ds"] == "ds_1" and out["n"] == 3 and "none" not in out and out["nested"] == ["O'Park", {"k": 2025}]
    with pytest.raises(PipelineError):
        substitute("{{unbekannt}}", params)
    with pytest.raises(PipelineError):
        substitute("$steps.b.dataset_id", params, steps)
    with pytest.raises(PipelineError):
        substitute("$steps.a.nope", params, steps)


def test_validate_params_defaults_required_coercion():
    spec = _spec(parameters=[
        {"name": "ort", "label": "Ort", "type": "place"},
        {"name": "art", "label": "Art", "type": "species", "required": False},
        {"name": "jahr", "label": "Jahr", "type": "year"},
        {"name": "zeitraum", "label": "Zeitraum", "type": "year_range", "default": "2020-2018"},
        {"name": "monate", "label": "Monate", "type": "period", "required": False},
        {"name": "ok", "label": "Ja/Nein", "type": "boolean", "default": "nein"},
        {"name": "km", "label": "km", "type": "number", "default": "5"},
        {"name": "wahl", "label": "Wahl", "type": "choice", "choices": ["a", "b"], "default": "a"},
    ])
    v = validate_params(spec, {"ort": " Ostpark ", "jahr": "2025", "monate": "5,6, 7"})
    assert v == {"ort": "Ostpark", "art": None, "jahr": 2025, "zeitraum": {"from": 2018, "to": 2020}, "monate": {"months": [5, 6, 7]}, "ok": False, "km": 5, "wahl": "a"}
    assert validate_params(spec, {"ort": "x", "jahr": 2025, "monate": "2025-05-01..2025-07-31"})["monate"] == {"date_from": "2025-05-01", "date_to": "2025-07-31"}
    with pytest.raises(PipelineError, match="Jahr"):
        validate_params(spec, {"ort": "x"})
    with pytest.raises(PipelineError, match="nicht erlaubt"):
        validate_params(spec, {"ort": "x", "jahr": 2025, "wahl": "c"})
    with pytest.raises(PipelineError, match="Unbekannte Parameter"):
        validate_params(spec, {"ort": "x", "jahr": 2025, "foo": 1})
    with pytest.raises(ValueError):
        Parameter(name="1bad", label="x", type="text")


def test_spec_validation_and_describe():
    with pytest.raises(ValueError, match="eindeutig"):
        _spec(steps=[{"id": "a", "kind": "export", "spec": {}}, {"id": "a", "kind": "export", "spec": {}}])
    with pytest.raises(ValueError, match="unbekannte Analyse"):
        _spec(steps=[{"id": "a", "kind": "analysis", "spec": {"name": "nope"}}])
    with pytest.raises(ValueError, match="outputs"):
        _spec(outputs=["zz"])
    d = describe_pipeline(_spec(parameters=[{"name": "ort", "label": "Ort", "type": "place", "required": False}]))
    assert "Ort (optional)" in d and "Export" in d


def test_builtin_pipelines_validate():
    specs = builtin_specs()
    assert [s.name for s in specs] == ["Saison im Überblick", "Vogel-Steckbrief", "Woher kommen die Vögel?"]
    for s in specs:
        assert s.outputs and all(o in {st.id for st in s.steps} for o in s.outputs)
        # every placeholder refers to a declared parameter
        import json, re
        names = {p.name for p in s.parameters}
        used = set(re.findall(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)", json.dumps(s.model_dump())))
        assert used <= names, (s.name, used - names)


# ---------------------------------------------------------------- run_pipeline with stubs


@dataclass
class _Meta:
    id: str
    title: str | None
    dataset_ids: list


@dataclass
class _Out:
    meta: _Meta
    urls: dict
    summary: dict
    data_basis: str = ""


@dataclass
class _ViewResult:
    dataset_id: str
    visual_kind: str
    visual_spec: object
    description: str = "Alle Sichtungen."
    row_count: int = 3


@pytest.fixture
def env(tmp_path, monkeypatch):
    store = DatasetStore(tmp_path / "ds")
    monkeypatch.setattr(runtime, "datasets", lambda: store)
    monkeypatch.setattr(pipelines, "settings", types.SimpleNamespace(exports_dir=tmp_path, public_base_url="https://x.test"))
    created = []

    async def fake_create_visual(kind, spec_obj, *, visual_id=None, patch=None, view_id=None):
        created.append((kind, spec_obj))
        ds = getattr(spec_obj, "dataset_id", None) or "ds_view"
        return _Out(meta=_Meta(id=f"vz_{len(created)}", title=getattr(spec_obj, "title", None), dataset_ids=[ds]), urls={"png_url": "u"}, summary={"categories": 4})

    monkeypatch.setattr(visual_service, "create_visual", fake_create_visual)

    class FakeViewSpec:
        @classmethod
        def model_validate(cls, d):
            if d.get("fail"):
                raise ValueError("kaputt")
            return types.SimpleNamespace(title=d.get("title"))

    async def fake_build_view(vs):
        return _ViewResult(dataset_id="ds_view", visual_kind="chart", visual_spec=types.SimpleNamespace(title=vs.title, dataset_id="ds_view"))

    fake_views = types.ModuleType("vogelring_analytics.views")
    fake_views.ViewSpec = FakeViewSpec
    fake_views.build_view = fake_build_view
    monkeypatch.setitem(sys.modules, "vogelring_analytics.views", fake_views)
    import vogelring_analytics as _pkg
    monkeypatch.setattr(_pkg, "views", fake_views, raising=False)  # `from . import views` resolves the package attribute first

    async def fake_seasonality(place, species, year_from, year_to):
        meta = store.save(pd.DataFrame({"jahr": [2024, 2025], "monat": [5, 6], "individuen": [3, 5]}), name="Saison", sql="SELECT 1", description=f"Saison {place}")
        return {"filters": place, "summary": {"peak_month": "Juni"}, "dataset_id": meta.id}

    from vogelring_analytics import analysis

    monkeypatch.setattr(analysis, "seasonality", fake_seasonality)
    return store, created


async def test_run_pipeline_success(env):
    store, created = env
    spec = PipelineSpec.model_validate({
        "name": "Demo", "description": "Demo.", "parameters": [{"name": "ort", "label": "Ort", "type": "place"}, {"name": "jahr", "label": "Jahr", "type": "year", "default": 2025}],
        "steps": [
            {"id": "a", "kind": "analysis", "spec": {"name": "seasonality", "args": {"place": "{{ort}}", "year_from": "{{jahr}}"}}},
            {"id": "v", "kind": "view", "spec": {"title": "Ansicht {{ort}}"}},
            {"id": "c", "kind": "chart", "spec": {"kind": "bar", "dataset_id": "$steps.a.dataset_id", "x": "monat", "y": "individuen", "title": "{{ort}} {{jahr}}"}},
            {"id": "t", "kind": "transform", "spec": {"dataset_id": "$steps.a.dataset_id", "ops": [{"op": "filter", "column": "jahr", "condition": "==", "value": 2025}], "name": "Nur {{jahr}}"}},
            {"id": "x", "kind": "export", "spec": {"dataset_id": "$steps.t.dataset_id", "filename": "Saison {{ort}}"}},
        ],
        "outputs": ["c", "x"],
    })
    res = await run_pipeline(spec, {"ort": "Ostpark"})
    assert res.status == "ok" and res.error is None, res.log
    assert len(res.log) == 5 and res.log[0].startswith("Schritt 1/5") and "Analyse" in res.log[0]
    assert [a["step_id"] for a in res.artifacts] == ["c", "x"]
    assert created[1][1].title == "Ostpark 2025" and created[0][1].title == "Ansicht Ostpark"
    export = res.artifacts[1]
    assert export["url"].startswith("https://x.test/files/Saison_Ostpark_") and export["rows"] == 1
    assert res.params == {"ort": "Ostpark", "jahr": 2025} and res.to_dict()["status"] == "ok"


async def test_run_pipeline_stops_on_error(env):
    spec = PipelineSpec.model_validate({
        "name": "Fehler", "description": "x", "parameters": [],
        "steps": [
            {"id": "a", "kind": "analysis", "spec": {"name": "seasonality", "args": {"place": "P"}}},
            {"id": "bad", "kind": "chart", "spec": {"kind": "bar", "dataset_id": "$steps.a.dataset_id"}},
            {"id": "never", "kind": "export", "spec": {"dataset_id": "$steps.a.dataset_id"}},
        ],
    })
    res = await run_pipeline(spec, {})
    assert res.status == "error" and res.error.startswith("Schritt 2/3") and "ungültig" in res.error
    assert len(res.log) == 2 and res.log[1].startswith("Schritt 2/3: Fehler")
    assert res.artifacts == []
    res2 = await run_pipeline(spec, {"nope": 1})
    assert res2.status == "error" and "Unbekannte Parameter" in res2.error


async def test_run_pipeline_unknown_analysis_arg(env):
    spec = PipelineSpec.model_validate({"name": "F", "description": "x", "steps": [{"id": "a", "kind": "analysis", "spec": {"name": "seasonality", "args": {"planet": "Mars"}}}]})
    res = await run_pipeline(spec, {})
    assert res.status == "error" and "planet" in res.error


def test_substitute_dotted_and_optional_lists():
    params = {"jahre": {"from": 2020, "to": 2024}, "art": None, "zeit": {"months": [5, 6]}}
    out = substitute({"filters": {"year_from": "{{jahre.from}}", "year_to": "{{jahre.to}}", "species": ["{{art}}"], "months": "{{zeit.months}}", "places": ["Ostpark", "{{art}}"]}}, params)
    assert out["filters"] == {"year_from": 2020, "year_to": 2024, "species": [], "months": [5, 6], "places": ["Ostpark"]}
    assert substitute("Jahre {{jahre.from}}–{{jahre.to}}", params) == "Jahre 2020–2024"


def test_substitute_drops_empty_optional_keys():
    out = substitute({"filters": {"months": "{{zeit.months}}", "species": ["{{art}}"], "years": [2025]}}, {"zeit": {"date_from": "2025-05-01", "date_to": "2025-07-31"}, "art": None})
    assert out == {"filters": {"species": [], "years": [2025]}}
