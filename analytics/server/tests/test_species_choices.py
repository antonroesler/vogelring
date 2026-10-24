from vogelring_analytics.sources import RING_SPECIES, FilterSpec, SOURCES, choices_context, species_name, species_name_sql


def test_species_mapping_loaded():
    assert RING_SPECIES["01660"] == "Kanadagans"
    assert species_name("01660") == "Kanadagans"
    assert species_name("Graugans") == "Graugans"
    assert species_name(None) is None


def test_species_sql_in_sources():
    expr = species_name_sql("species")
    assert expr.startswith("COALESCE(") and "->> species" in expr and "%%" not in expr.replace("%%", "")
    assert "AS species, species AS species_code" in SOURCES["ringings"].base_sql
    assert "AS ringed_as_species" in SOURCES["sightings"].base_sql
    assert "MAX(ringed_as_species)" in SOURCES["birds"].base_sql and "COALESCE(" in SOURCES["birds"].base_sql
    assert "'" not in RING_SPECIES.get("01660", "")  # literal stays SQL-safe


def test_choices_context_drops_own_column_filters():
    f = FilterSpec(species=["Kanadagans"], places=["Ostpark"], years=[2025])
    ctx = choices_context("species", f)
    assert ctx is not None and ctx.species == [] and ctx.places == ["Ostpark"] and ctx.years == [2025]
    ctx = choices_context("place", FilterSpec(places=["Ostpark"], exclude_places=["Nord"]))
    assert ctx is None  # nothing left to narrow by
    assert choices_context("species", None) is None
    assert choices_context("year", FilterSpec(years=[2024], species=["Graugans"])).years == []
