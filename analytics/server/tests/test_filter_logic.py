"""Boolean composition (any_of/none_of), bird-level selection (birds_of) and group set operations."""

import pytest

from vogelring_analytics import engine, runtime
from vogelring_analytics.catalog import Catalog
from vogelring_analytics.definitions import DefinitionStore
from vogelring_analytics.groups import GroupSpec, group_condition
from vogelring_analytics.sources import FilterBlock, FilterFields, FilterSpec, SourceError, compile_filters, describe_filters, describe_sources, get_source


@pytest.fixture
def cat(tmp_path, monkeypatch):
    c = Catalog(tmp_path / "c.sqlite")
    monkeypatch.setattr(runtime, "catalog", lambda: c)
    monkeypatch.setattr(runtime, "definitions", lambda: DefinitionStore(tmp_path / "defs.json"))
    return c


S = get_source("sightings")


def test_any_of_and_none_of():
    f = FilterSpec(places=["Ostpark"], any_of=[{"months": [5, 6]}, {"months": [4], "status": ["MG"]}], none_of=[{"melder": ["XY"]}])
    sql, params = compile_filters(S, f)
    assert sql == "(place ILIKE %s) AND ((EXTRACT(MONTH FROM date) IN (5, 6)) OR (EXTRACT(MONTH FROM date) IN (4) AND status IN (%s))) AND NOT ((melder IN (%s)))"
    assert params == ["%Ostpark%", "MG", "XY"]
    d = describe_filters(f, S)
    assert d == "Sichtungen an Orten mit ‚Ostpark‘ im Namen, entweder (in den Monaten Mai–Juni) oder (in den Monaten April, mit Status Mausergast), aber nicht (gemeldet von XY)"
    # empty alternatives are ignored, a single alternative has no „entweder“
    f = FilterSpec(any_of=[{}, {"years": [2025]}])
    sql, _ = compile_filters(S, f)
    assert sql == "((EXTRACT(YEAR FROM date) IN (2025)))"
    assert describe_filters(f, S) == "Sichtungen (im Jahr 2025)"
    assert FilterSpec(any_of=[{}]).is_empty() is False and FilterSpec().is_empty()
    with pytest.raises(ValueError):
        FilterSpec(any_of=[{"any_of": []}])  # only one level of nesting in the schema


def test_birds_of_subquery():
    f = FilterSpec(birds_of={"places": ["Ostpark"], "months": [5, 6]}, years=[2025])
    sql, params = compile_filters(S, f)
    assert sql.startswith("EXTRACT(YEAR FROM date) IN (2025) AND ring IN (SELECT DISTINCT ring FROM (SELECT id, ring,")
    assert sql.endswith("WHERE ring IS NOT NULL AND (place ILIKE %s) AND EXTRACT(MONTH FROM date) IN (5, 6))")
    assert params == ["%Ostpark%"]
    assert describe_filters(f, S) == "Sichtungen im Jahr 2025, von Vögeln mit mindestens einer Sichtung an Orten mit ‚Ostpark‘ im Namen, in den Monaten Mai–Juni"
    # works on the other sources too: birds source (one row per ring) and relationships (either ring)
    sql, _ = compile_filters(get_source("birds"), FilterSpec(birds_not_of={"places": ["Ostpark"]}))
    assert sql.startswith("NOT ring IN (SELECT DISTINCT ring")
    assert describe_filters(FilterSpec(birds_not_of={"places": ["Ostpark"]}), get_source("birds")) == "Vögel ohne jede Sichtung an Orten mit ‚Ostpark‘ im Namen"
    sql, params = compile_filters(get_source("relationships"), FilterSpec(birds_of={"places": ["Ostpark"]}))
    assert sql.startswith("(bird1_ring IN (SELECT") and " OR bird2_ring IN (SELECT" in sql and params == ["%Ostpark%", "%Ostpark%"]
    # an empty block means no restriction
    assert compile_filters(S, FilterSpec(birds_of={}))[0] == "TRUE"


def test_bird_group_scope(cat):
    g = engine.create_group(GroupSpec(name="Mausergäste Ostpark", scope="birds", filters={"places": ["Ostpark"], "any_of": [{"months": [5, 6]}, {"months": [4], "status": ["MG"]}]}, excluded_ids=["bad1"]))
    assert g["scope"] == "birds"
    assert g["describe"] == "alle Sichtungen der Vögel mit mindestens einer Sichtung an Orten mit ‚Ostpark‘ im Namen, entweder (in den Monaten Mai–Juni) oder (in den Monaten April, mit Status Mausergast), ohne einen von Hand ausgeschlossenen Eintrag"
    sql, params = group_condition(S, GroupSpec.model_validate(cat.get("group", g["id"]).doc))
    assert sql.startswith("(ring IN (SELECT DISTINCT ring FROM (") and "place ILIKE %s" in sql and sql.endswith("AND NOT (id::text IN (%s)))")
    assert params == ["%Ostpark%", "MG", "bad1"]
    # „where else do these birds turn up“ = plain view over the group; the Ostpark filter lives only inside the subquery
    sql, params = compile_filters(S, FilterSpec(groups=[g["id"]]))
    assert sql.count("place ILIKE") == 1 and "SELECT DISTINCT ring" in sql
    # ring list only → bird group of exactly these rings
    r = engine.create_group(GroupSpec(name="Zwei Ringe", scope="birds", ring_list=["A1", "A2"]))
    sql, params = group_condition(S, GroupSpec.model_validate(cat.get("group", r["id"]).doc))
    assert "WHERE ring IS NOT NULL AND (ring IN (%s, %s))" in sql and params == ["A1", "A2"]
    assert engine.get_group(r["id"])["describe"] == "alle Sichtungen der Vögel mit mindestens einer Sichtung der Ringe A1, A2"
    with pytest.raises(ValueError):
        GroupSpec(name="x", scope="places")


def test_group_set_operations(cat):
    # legacy sightings-level groups keep their plain conditions; new groups are bird groups by default
    a = engine.create_group(GroupSpec(name="A", scope="sightings", filters={"species": ["Graugans"]}))
    b = engine.create_group(GroupSpec(name="B", scope="sightings", filters={"places": ["Ostpark"]}))
    c = engine.create_group(GroupSpec(name="C", scope="sightings", filters={"years": [2025]}))
    assert engine.create_group(GroupSpec(name="D", filters={"years": [2024]}))["scope"] == "birds"
    sql, params = compile_filters(S, FilterSpec(all_groups=[a["id"], "B"]))
    assert sql == "((species IN (%s)) AND ((place ILIKE %s)))" and params == ["Graugans", "%Ostpark%"]
    sql, params = compile_filters(S, FilterSpec(groups=[a["id"]], exclude_groups=[b["id"], c["id"]]))
    assert sql == "(species IN (%s)) AND NOT (((place ILIKE %s)) OR (EXTRACT(YEAR FROM date) IN (2025)))" and params == ["Graugans", "%Ostpark%"]
    assert describe_filters(FilterSpec(all_groups=[a["id"], b["id"]]), S) == "Sichtungen zugleich in den Gruppen ‚A‘ und ‚B‘"
    assert describe_filters(FilterSpec(groups=[a["id"]], exclude_groups=[b["id"]]), S) == "Sichtungen aus der Gruppe ‚A‘, nicht aus der Gruppe ‚B‘"
    # engine.combine_groups builds referencing groups
    u = engine.combine_groups("A oder B", "union", [a["id"], b["id"]])
    assert u["doc"]["filters"] == {"groups": [a["id"], b["id"]]} and u["description"] == "Alles aus „A“ oder „B“"
    i = engine.combine_groups("A und B", "intersection", ["A", "B"], scope="birds")
    assert i["doc"]["filters"] == {"all_groups": [a["id"], b["id"]]} and i["scope"] == "birds"
    d = engine.combine_groups("A ohne B und C", "difference", [a["id"], b["id"], c["id"]])
    assert d["doc"]["filters"] == {"groups": [a["id"]], "exclude_groups": [b["id"], c["id"]]}
    assert d["describe"] == "alle Sichtungen der Vögel mit mindestens einer Sichtung aus der Gruppe ‚A‘, nicht aus den Gruppen ‚B‘ oder ‚C‘"
    sql, _ = compile_filters(S, FilterSpec(groups=[d["id"]]))
    assert "NOT (((place ILIKE %s)) OR (EXTRACT(YEAR FROM date) IN (2025)))" in sql
    with pytest.raises(engine.EngineError, match="mindestens zwei"):
        engine.combine_groups("x", "union", [a["id"]])
    with pytest.raises(engine.EngineError, match="Unbekannte Verknüpfung"):
        engine.combine_groups("x", "xor", [a["id"], b["id"]])


def test_nesting_limit_and_sources_meta(cat):
    # a group referencing itself through birds_of is caught by the group depth guard
    cat.put("group", {"name": "Loop", "filters": {"birds_of": {"groups": ["Loop"]}}}, id="grp_loop", title="Loop")
    with pytest.raises(SourceError, match="Ebenen"):
        compile_filters(S, FilterSpec(groups=["grp_loop"]))
    info = describe_sources()
    names = [f["name"] for f in info["filters"]]
    for n in ("all_groups", "exclude_groups", "any_of", "none_of", "birds_of", "birds_not_of"):
        assert n in names
    by_key = {s["key"]: s for s in info["sources"]}
    assert "birds_of" in by_key["sightings"]["filters"] and "any_of" in by_key["ringings"]["filters"]
    assert "groups" not in by_key["relationships"]["filters"] and "birds_of" in by_key["relationships"]["filters"]
    # schema stays non-recursive (LibreChat's zod conversion): FilterSpec → FilterBlock → FilterFields
    assert set(FilterSpec.model_json_schema()["$defs"]) >= {"FilterBlock", "FilterFields"}
    assert isinstance(FilterSpec(birds_of={"any_of": [{"years": [2024]}]}).birds_of, FilterBlock)
    assert isinstance(FilterSpec(any_of=[{"years": [2024]}]).any_of[0], FilterFields)


@pytest.mark.asyncio
async def test_bird_group_stats_and_preview_flags(cat, monkeypatch):
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
                return R(["n", "birds", "places", "first", "last"], [(40, 5, 9, dt.date(2020, 5, 1), dt.date(2025, 7, 9))])
            if "AS k, COUNT(*) AS n, COUNT(DISTINCT ring)" in sql:
                return R(["k", "n", "birds"], [("Graugans", 40, 5)])
            if "COALESCE(status" in sql:
                return R(["k", "n"], [("MG", 7)])
            if "EXTRACT(YEAR FROM date)::int AS k" in sql:
                return R(["k", "n"], [(2025, 40)])
            if sql.startswith("SELECT COUNT(*)"):
                return R(["count"], [(12,)])
            return R(engine.GROUP_PREVIEW_COLUMNS + ["matches"], [("id1", dt.date(2025, 6, 9), "278924", "Graugans", "F, Ostpark", "MG", 1, "IR", "F, Ostpark", True), ("id2", dt.date(2025, 9, 1), "278924", "Graugans", "Hanau", None, 1, "IR", "F, Ostpark", False)])

    db = DB()
    monkeypatch.setattr(runtime, "database", lambda: db)
    g = engine.create_group(GroupSpec(name="Mauser", scope="birds", filters={"places": ["Ostpark"], "months": [5, 6]}))
    st = await engine.group_stats(g["id"])
    assert st["scope"] == "birds" and st["sightings"] == 40 and st["matching_sightings"] == 12
    assert any("SELECT COUNT(*) FROM" in s and s.endswith("AND ((place ILIKE %s) AND EXTRACT(MONTH FROM date) IN (5, 6))") for s, _ in db.sql)
    pv = await engine.group_preview(g["id"], limit=10)
    assert pv["scope"] == "birds" and pv["rows"][0]["matches"] is True and pv["rows"][1]["matches"] is False
    sql, params = db.sql[-1]
    assert ", (((place ILIKE %s) AND EXTRACT(MONTH FROM date) IN (5, 6))) AS matches FROM" in sql and params == ["%Ostpark%", "%Ostpark%"]
    # legacy sightings-scope groups report no matching count
    g2 = engine.create_group(GroupSpec(name="Plain", scope="sightings", filters={"places": ["Ostpark"]}))
    st2 = await engine.group_stats(g2["id"])
    assert st2["scope"] == "sightings" and st2["matching_sightings"] is None
