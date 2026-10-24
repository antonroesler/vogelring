import pytest

from vogelring_analytics.definitions import Definition, DefinitionError, DefinitionStore


@pytest.fixture
def store(tmp_path):
    return DefinitionStore(tmp_path / "defs.json")


def test_place_group_expansion(store):
    store.save(Definition(name="Nordufer", kind="place_group", description="Orte am Nordufer", values=["Mainkai", "Weseler Werft"]))
    sql, used = store.expand("SELECT * FROM v_sightings WHERE {{Nordufer}} AND {{ nordufer : ringing_place }}")
    assert "(place ILIKE '%Mainkai%' OR place ILIKE '%Weseler Werft%')" in sql
    assert "(ringing_place ILIKE '%Mainkai%'" in sql
    assert used == ["Nordufer", "Nordufer"]


def test_period_and_rings_and_filter(store):
    store.save(Definition(name="Mauserzeit", kind="period", description="", values=["5-7"]))
    store.save(Definition(name="Winter", kind="period", description="", values=["11-1"]))
    store.save(Definition(name="Kerngruppe", kind="ring_group", description="", values=["A1", "B'2"]))
    store.save(Definition(name="AltGrau", kind="filter", description="", sql="species = 'Graugans' AND age = 1"))
    sql, _ = store.expand("{{Mauserzeit}} {{Winter}} {{Kerngruppe}} {{AltGrau}}")
    assert "EXTRACT(MONTH FROM date) IN (5, 6, 7)" in sql
    assert "IN (1, 11, 12)" in sql
    assert "(ring IN ('A1', 'B''2'))" in sql
    assert "(species = 'Graugans' AND age = 1)" in sql


def test_errors_and_persistence(store, tmp_path):
    with pytest.raises(DefinitionError):
        store.expand("{{Unbekannt}}")
    with pytest.raises(DefinitionError):
        store.save(Definition(name="x", kind="filter", description="", sql="a; drop"))
    with pytest.raises(DefinitionError):
        store.save(Definition(name="leer", kind="place_group", description=""))
    store.save(Definition(name="Hinweis", kind="note", description="Innenstadt = Mainkai"))
    with pytest.raises(DefinitionError):
        store.expand("{{Hinweis}}")
    again = DefinitionStore(tmp_path / "defs.json")
    assert again.get("hinweis").description == "Innenstadt = Mainkai"
    assert again.delete("Hinweis") and again.get("Hinweis") is None
    assert "Keine" in again.describe()
