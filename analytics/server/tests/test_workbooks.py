import sys
import types
from dataclasses import dataclass

import pytest
from pydantic import BaseModel

from vogelring_analytics import visual_service
from vogelring_analytics.workbooks import TileSpec, WorkbookSpec, merge_filters, render_workbook, workbook_to_deck, workbook_to_report


class F(BaseModel):
    species: list[str] | None = None
    places: list[str] | None = None
    year_from: int | None = None
    radius: dict | None = None


def test_merge_filters_dicts_and_models():
    base = {"species": ["Graugans"], "year_from": 2024, "places": [], "radius": {"km": 5}}
    over = {"species": ["Nilgans", "Graugans"], "year_from": 2019, "places": ["Ostpark"], "radius": {"km": 20, "lat": 50.1}}
    m = merge_filters(base, over)
    assert m == {"species": ["Graugans", "Nilgans"], "year_from": 2024, "places": ["Ostpark"], "radius": {"km": 5, "lat": 50.1}}
    fm = merge_filters(F(species=["Graugans"]), F(species=["Nilgans"], year_from=2020))
    assert isinstance(fm, F) and fm.species == ["Graugans", "Nilgans"] and fm.year_from == 2020
    assert merge_filters({}, {"places": ["x"]}) == {"places": ["x"]}


def test_tile_validation():
    with pytest.raises(ValueError):
        TileSpec()
    with pytest.raises(ValueError):
        TileSpec(view_id="vw_1", view={"kind": "chart"})
    assert TileSpec(view_id="vw_1").w == 6


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
    data_basis: str = "Alle Sichtungen 2025."


@dataclass
class _ViewResult:
    dataset_id: str
    visual_kind: str
    visual_spec: object
    description: str
    row_count: int = 1


class _Catalog:
    def __init__(self):
        self.docs = {("view", "vw_1"): types.SimpleNamespace(doc={"kind": "chart", "title": "Gespeichert", "filters": {"species": ["Nilgans"]}})}

    def get(self, kind, id):
        try:
            return self.docs[(kind, id)]
        except KeyError:
            raise KeyError(f"Unbekannte {kind}-ID: {id}")


@pytest.fixture
def stubs(monkeypatch):
    seen = []

    class FakeViewSpec:
        @classmethod
        def model_validate(cls, d):
            if d.get("kind") == "broken":
                raise ValueError("kaputt")
            return types.SimpleNamespace(**d)

    async def fake_build_view(vs):
        seen.append(vs)
        if getattr(vs, "explode", False):
            raise RuntimeError("Datenbank weg")
        return _ViewResult(dataset_id="ds_1", visual_kind="chart", visual_spec=types.SimpleNamespace(title=vs.title, dataset_id="ds_1"), description=f"Daten für {vs.title}")

    async def fake_create_visual(kind, spec_obj, *, visual_id=None, patch=None, view_id=None):
        return _Out(meta=_Meta(id=f"vz_{spec_obj.title}", title=spec_obj.title, dataset_ids=["ds_1"]), urls={}, summary={})

    fake_views = types.ModuleType("vogelring_analytics.views")
    fake_views.ViewSpec = FakeViewSpec
    fake_views.build_view = fake_build_view
    monkeypatch.setitem(sys.modules, "vogelring_analytics.views", fake_views)
    import vogelring_analytics as _pkg
    monkeypatch.setattr(_pkg, "views", fake_views, raising=False)  # `from . import views` resolves the package attribute first
    monkeypatch.setattr(visual_service, "create_visual", fake_create_visual)
    return seen


async def test_render_workbook_and_exports(stubs):
    spec = WorkbookSpec(title="Mappe", description="Test", filters={"species": ["Graugans"], "year_from": 2025}, tiles=[
        {"view_id": "vw_1", "note": "Erste Kachel."},
        {"view": {"kind": "chart", "title": "Inline", "filters": {"places": ["Ostpark"]}}, "title": "Eigener Titel", "w": 12},
        {"view": {"kind": "broken"}},
        {"view": {"kind": "chart", "title": "Boom", "explode": True}},
    ])
    res = await render_workbook(spec, catalog=_Catalog())
    assert [t.error is None for t in res.tiles] == [True, True, False, False]
    assert stubs[0].filters == {"species": ["Graugans", "Nilgans"], "year_from": 2025}
    assert stubs[1].filters == {"places": ["Ostpark"], "species": ["Graugans"], "year_from": 2025} and stubs[1].title == "Eigener Titel"
    assert res.visual_ids == ["vz_Gespeichert", "vz_Eigener Titel"]
    assert "ungültig" in res.tiles[2].error and "Datenbank weg" in res.tiles[3].error

    rep = workbook_to_report(spec, res)
    assert rep.title == "Mappe" and [s.heading for s in rep.sections] == ["Gespeichert", "Eigener Titel"]
    assert rep.sections[0].text == "Erste Kachel." and rep.sections[1].text == "Daten für Eigener Titel"
    assert rep.sections[0].visual_ids == ["vz_Gespeichert"]

    deck = workbook_to_deck(spec, res)
    assert deck["slides"][0]["kind"] == "title" and [s["kind"] for s in deck["slides"][1:]] == ["figure", "figure"]
    assert deck["slides"][1]["visual_ids"] == ["vz_Gespeichert"] and deck["slides"][1]["caption"] == "Erste Kachel."


async def test_render_workbook_without_rendering(stubs):
    spec = WorkbookSpec(title="M", tiles=[{"view": {"kind": "chart", "title": "A"}}])
    res = await render_workbook(spec, catalog=_Catalog(), render=False)
    assert res.tiles[0].visual is None and res.tiles[0].result.dataset_id == "ds_1" and res.visual_ids == []
