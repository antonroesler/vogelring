import json

import pytest

from vogelring_analytics import engine, runtime
from vogelring_analytics.catalog import Catalog
from vogelring_analytics.definitions import DefinitionStore
from vogelring_analytics.events import bus
from vogelring_analytics.groups import GroupSpec, group_case_sql, group_condition, group_union_sql, legacy_id, legacy_to_spec, resolve_group
from vogelring_analytics.sources import FilterSpec, SourceError, build_aggregate_sql, build_rows_sql, compile_filters, describe_filters, describe_sources, get_source


@pytest.fixture
def cat(tmp_path, monkeypatch):
    c = Catalog(tmp_path / "c.sqlite")
    monkeypatch.setattr(runtime, "catalog", lambda: c)
    monkeypatch.setattr(runtime, "definitions", lambda: DefinitionStore(tmp_path / "defs.json"))
    return c


@pytest.fixture
def events(monkeypatch):
    seen = []
    orig = bus.publish

    def rec(type, title, **payload):
        seen.append((type, title, payload))
        return orig(type, title, **payload)

    monkeypatch.setattr(bus, "publish", rec)
    return seen


# ---------------------------------------------------------------- spec


def test_group_spec_validation():
    g = GroupSpec(name="  Ostpark  ", filters={"species": ["Graugans"]}, color="#228096", ring_list=["A", " A ", "", "B"], excluded_ids=["1", "1"])
    assert g.name == "Ostpark" and g.color == "#228096" and g.ring_list == ["A", "B"] and g.excluded_ids == ["1"]
    assert "Graugans" in g.describe() and "der Ringe A, B" in g.describe() and "ausgeschlossenen Eintrag" in g.describe()
    with pytest.raises(ValueError):
        GroupSpec(name="x", color="blue")
    with pytest.raises(ValueError):
        GroupSpec(name="   ")
    with pytest.raises(ValueError):
        GroupSpec(name="x", unknown=1)
    assert GroupSpec(name="leer").is_empty()


# ---------------------------------------------------------------- SQL composition


def test_group_condition_and_union(cat):
    a = engine.create_group(GroupSpec(name="Graugänse Ostpark", filters={"species": ["Graugans"], "places": ["Ostpark"]}, excluded_ids=["x1", "x2"]))
    b = engine.create_group(GroupSpec(name="Ringliste", ring_list=["278924", "278925"]))
    src = get_source("sightings")
    sql, params = group_condition(src, GroupSpec.model_validate(cat.get("group", a["id"]).doc))
    assert sql.startswith("(") and "species IN (%s)" in sql and "place ILIKE %s" in sql and "NOT (id::text IN (%s, %s))" in sql
    assert params == ["Graugans", "%Ostpark%", "x1", "x2"]
    sql, params = group_union_sql(src, [a["id"], "Ringliste"])  # by id and by name
    assert " OR " in sql and "ring IN (%s, %s)" in sql and params[-2:] == ["278924", "278925"]
    # through FilterSpec.groups like any view does
    sql, params = compile_filters(src, FilterSpec(groups=[b["id"]], years=[2025]))
    assert "ring IN (%s, %s)" in sql and "EXTRACT(YEAR FROM date) IN (2025)" in sql
    assert describe_filters(FilterSpec(groups=[a["id"], b["id"]]), src) == "Sichtungen aus den Gruppen ‚Graugänse Ostpark‘ oder ‚Ringliste‘"
    with pytest.raises(SourceError, match="Unbekannte Gruppe"):
        compile_filters(src, FilterSpec(groups=["gibt es nicht"]))


def test_group_dimension_case(cat):
    a = engine.create_group(GroupSpec(name="A", scope="sightings", filters={"species": ["Graugans"]}, color="#111111"))
    b = engine.create_group(GroupSpec(name="B", scope="sightings", filters={"species": ["Kanadagans"]}))
    sql, params = build_aggregate_sql(get_source("sightings"), FilterSpec(groups=[a["id"], b["id"]]), "sightings", None, ["year", "group"])
    assert "CASE WHEN (species IN (%s)) THEN %s WHEN (species IN (%s)) THEN %s ELSE 'andere' END AS group" in sql
    assert params[:4] == ["Graugans", "A", "Kanadagans", "B"]  # CASE params precede the WHERE params
    assert params[4:] == ["Graugans", "Kanadagans"]
    with pytest.raises(SourceError, match="Gruppe"):
        build_aggregate_sql(get_source("sightings"), FilterSpec(), "sightings", None, ["group"])
    from vogelring_analytics.groups import group_colors

    colors = group_colors([a["id"], b["id"]])
    assert colors["A"] == "#111111" and colors["B"].startswith("#")


def test_new_filter_fields(cat):
    src = get_source("sightings")
    sql, params = compile_filters(src, FilterSpec(ring_contains=["W"], exclude_ids=["abc"]))
    assert "ring ILIKE %s" in sql and "NOT (id::text IN (%s))" in sql and params == ["%W%", "abc"]
    assert "‚W‘ in der Ringnummer" in describe_filters(FilterSpec(ring_contains=["W"]), src)
    with pytest.raises(SourceError):
        compile_filters(get_source("relationships"), FilterSpec(exclude_ids=["1"]))
    info = describe_sources()
    names = [f["name"] for f in info["filters"]]
    assert "groups" in names and "ring_contains" in names
    sightings = next(s for s in info["sources"] if s.key == "sightings") if hasattr(info["sources"][0], "key") else next(s for s in info["sources"] if s["key"] == "sightings")
    assert "groups" in sightings["filters"] and "group" in sightings["dimensions"]
    rel = next(s for s in info["sources"] if s["key"] == "relationships")
    assert "groups" not in rel["filters"]


def test_nested_group_depth(cat):
    a = engine.create_group(GroupSpec(name="A", filters={"species": ["Graugans"]}))
    b = engine.create_group(GroupSpec(name="B", filters={"groups": [a["id"]], "years": [2025]}))
    sql, params = build_rows_sql(get_source("sightings"), FilterSpec(groups=[b["id"]]), ["ring"])
    assert "species IN (%s)" in sql and "IN (2025)" in sql
    cat.put("group", {"name": "Loop", "filters": {"groups": ["Loop"]}}, id="grp_loop", title="Loop")
    with pytest.raises(SourceError, match="drei Ebenen"):
        compile_filters(get_source("sightings"), FilterSpec(groups=["grp_loop"]))


# ---------------------------------------------------------------- engine


def test_engine_crud_and_events(cat, events):
    out = engine.create_group(GroupSpec(name="Nilgänse Neckar", description="Rhein-Neckar", filters={"species": ["Nilgans"], "ring_contains": ["W"]}, tags=["Nilgans"]), by="ingo")
    assert out["id"].startswith("grp_") and out["name"] == "Nilgänse Neckar" and out["filter_count"] == 2 and out["tags"] == ["Nilgans"]
    assert events[-1][0] == "group.created" and events[-1][2]["by"] == "ingo"
    upd = engine.update_group(out["id"], {"color": "#228096", "filters": {"years": [2024]}}, by="agent")
    assert upd["color"] == "#228096" and upd["doc"]["filters"] == {"species": ["Nilgans"], "ring_contains": ["W"], "years": [2024]}
    assert events[-1][0] == "group.updated"
    ex = engine.set_group_exclusions(out["id"], ["s1", "s2"], True)
    assert ex["doc"]["excluded_ids"] == ["s1", "s2"] and ex["excluded_count"] == 2
    ex = engine.set_group_exclusions(out["id"], ["s1"], False)
    assert ex["doc"]["excluded_ids"] == ["s2"]
    assert [g["name"] for g in engine.list_groups(search="Neckar")] == ["Nilgänse Neckar"]
    assert engine.get_group(out["id"])["describe"].startswith("alle Sichtungen der Vögel mit mindestens einer Sichtung der Art Nilgans")
    item, spec = resolve_group("nilgänse neckar")
    assert item.id == out["id"] and spec.color == "#228096"
    with pytest.raises(engine.EngineError, match="ungültig"):
        engine.update_group(out["id"], {"color": "rot"})


def test_compare_spec(cat):
    a = engine.create_group(GroupSpec(name="A", filters={"species": ["Graugans"]}))
    b = engine.create_group(GroupSpec(name="B", filters={"species": ["Kanadagans"]}))
    spec = engine.compare_spec([a["id"], b["id"]], metric="birds", dimension="year")
    assert spec.dimension == "year" and spec.color == "group" and spec.filters.groups == [a["id"], b["id"]] and spec.metric.kind == "birds"
    spec = engine.compare_spec([a["id"]], dimension="group", chart_kind="pie")
    assert spec.dimension == "group" and spec.color is None and spec.chart_kind == "pie"
    assert "Gruppe" in spec.describe()
    with pytest.raises(engine.EngineError):
        engine.compare_spec([], dimension="year")
    with pytest.raises(engine.EngineError):
        engine.compare_spec([a["id"]], dimension="melder")


@pytest.mark.asyncio
async def test_group_stats_and_preview(cat, monkeypatch):
    import datetime as dt

    class R:
        def __init__(self, columns, rows):
            self.columns, self.rows, self.truncated = columns, rows, False

    class DB:
        def __init__(self):
            self.sql = []

        async def query(self, sql, params=None, max_rows=None):
            self.sql.append((sql, list(params or ())))
            if "COUNT(DISTINCT ring) AS birds, COUNT(DISTINCT place)" in sql:
                return R(["n", "birds", "places", "first", "last"], [(12, 5, 3, dt.date(2020, 5, 1), dt.date(2025, 7, 9))])
            if "AS k, COUNT(*) AS n, COUNT(DISTINCT ring)" in sql:
                return R(["k", "n", "birds"], [("Graugans", 12, 5)])
            if "COALESCE(status" in sql:
                return R(["k", "n"], [("BV", 7), ("ohne", 5)])
            if "EXTRACT(YEAR FROM date)::int AS k" in sql:
                return R(["k", "n"], [(2024, 4), (2025, 8)])
            if sql.startswith("SELECT COUNT(*)"):
                return R(["count"], [(2,)])
            return R(engine.GROUP_PREVIEW_COLUMNS, [("id1", dt.date(2025, 7, 9), "278924", "Graugans", "F, Ostpark", "BV", 1, "IR", "F, Ostpark"), ("id2", dt.date(2025, 7, 1), "278925", "Graugans", "F, Ostpark", None, 1, "IR", "F, Ostpark")])

    db = DB()
    monkeypatch.setattr(runtime, "database", lambda: db)
    g = engine.create_group(GroupSpec(name="G", filters={"species": ["Graugans"]}, excluded_ids=["id2"]))
    st = await engine.group_stats(g["id"])
    assert st["sightings"] == 12 and st["birds"] == 5 and st["first"] == "2020-05-01" and st["last"] == "2025-07-09"
    assert st["species"][0] == {"label": "Graugans", "sightings": 12, "birds": 5} and st["years"] == [{"year": 2024, "sightings": 4}, {"year": 2025, "sightings": 8}]
    assert engine.list_groups()[0]["stats"]["sightings"] == 12  # cached for the list page
    assert all("NOT (id::text IN (%s))" in s for s, _ in db.sql)
    pv = await engine.group_preview(g["id"], limit=10, with_excluded=True)
    assert pv["total"] == 2 and pv["rows"][0]["date"] == "2025-07-09" and pv["rows"][0]["excluded"] is False and pv["rows"][1]["excluded"] is True
    assert "NOT (id::text" not in db.sql[-1][0] and "LIMIT 10 OFFSET 0" in db.sql[-1][0]

    # an unsaved definition evaluates the same way, without touching the catalog
    before = len(engine.list_groups())
    ev = await engine.evaluate_group(GroupSpec(name="Entwurf", scope="birds", filters={"species": ["Graugans"], "places": ["Palmengarten"]}), limit=5)
    assert ev["describe"].startswith("alle Sichtungen der Vögel mit mindestens einer Sichtung") and ev["scope"] == "birds"
    assert ev["stats"]["sightings"] == 12 and ev["preview"]["total"] == 2 and ev["preview"]["name"] == "Entwurf"
    assert "Palmengarten" in str(db.sql[-1][1]) and len(engine.list_groups()) == before
    ev = await engine.evaluate_group(GroupSpec(name="Entwurf"), with_rows=False)
    assert "preview" not in ev and ev["describe"] == "alle Sichtungen aller Vögel"


# ---------------------------------------------------------------- legacy port


LEGACY = {
    "name": "Gra_Ostpark_Jungvögel", "description": "Filter: Gra / Ostpark", "columns": ["id"], "id_field": "id", "excluded_ids": ["e1"],
    "filters": [
        {"type": "equals", "column": "species", "value": "Graugans"},
        {"type": "equals", "column": "ringing_age", "value": 1.0},
        {"type": "multi", "column": "ringing_place", "values": ["Frankfurt, Ostpark*[DEED, 5818)"]},
        {"type": "equals", "column": "status", "value": "BV"},
        {"type": "equals", "column": "place", "value": "F, Ostpark"},
        {"type": "multi", "column": "ring", "values": ["1", "2", "1"]},
        {"type": "contains", "column": "ring", "value": "W..."},
        {"type": "date_range", "column": "date", "min": "2020-01-01", "max": None},
        {"type": "date_range", "column": "date", "min": None, "max": None},
        {"type": "equals", "column": "weight", "value": 3},
    ],
}


def test_legacy_mapping():
    spec, notes = legacy_to_spec(LEGACY)
    f = spec.filters
    assert f.species == ["Graugans"] and f.ringing_age == [1] and f.ringing_places == ["Frankfurt, Ostpark*[DEED, 5818)"] and f.status == ["BV"]
    assert f.places == ["F, Ostpark"] and f.ring_contains == ["W"] and f.date_from == "2020-01-01" and f.date_to is None
    assert spec.ring_list == ["1", "2"] and spec.excluded_ids == ["e1"] and spec.tags == ["Import"] and spec.description == "Filter: Gra / Ostpark"
    assert any("Namensteil" in n for n in notes) and any("weight" in n for n in notes) and any("Leerer Datumsbereich" in n for n in notes)
    assert legacy_id("Graugänse") == legacy_id(" graugänse ") and legacy_id("a") != legacy_id("b") and legacy_id("x").startswith("grp_")


def test_import_legacy_idempotent(cat, tmp_path, events):
    d = tmp_path / "legacy"
    d.mkdir()
    (d / "a.json").write_text(json.dumps(LEGACY), encoding="utf-8")
    (d / "b.json").write_text(json.dumps({"name": "Leer", "filters": []}), encoding="utf-8")
    out = engine.import_legacy_groups(d)
    assert out["count"] == 2 and [r["status"] for r in out["items"]] == ["created", "created"] and out["items"][1]["empty"] is True
    gid = out["items"][0]["group_id"]
    engine.update_group(gid, {"color": "#ABCDEF"})
    out2 = engine.import_legacy_groups(d)
    assert [r["status"] for r in out2["items"]] == ["updated", "updated"] and len(cat.list("group")) == 2
    assert cat.get("group", gid).doc["color"] == "#ABCDEF"  # app-chosen colour survives re-import
    assert cat.get("group", gid).extra["legacy_file"] == "a.json" and cat.get("group", gid).extra["import_notes"]
    with pytest.raises(engine.EngineError, match="nicht gefunden"):
        engine.import_legacy_groups(tmp_path / "nope")


def test_catalog_kind_and_route():
    from vogelring_analytics.catalog import KINDS, PREFIX

    assert "group" in KINDS and PREFIX["group"] == "grp_"
    assert engine.ROUTES["group"] == "gruppen"
