import pytest

from vogelring_analytics import runtime
from vogelring_analytics.definitions import Definition, DefinitionStore
from vogelring_analytics.sources import (
    DIMENSIONS,
    METRICS,
    SOURCES,
    FilterSpec,
    SourceError,
    build_aggregate_sql,
    build_rows_sql,
    compile_filters,
    describe_filters,
    describe_sources,
    get_source,
)


@pytest.fixture
def defs(tmp_path, monkeypatch):
    store = DefinitionStore(tmp_path / "defs.json")
    store.save(Definition(name="Nordufer", kind="place_group", description="", values=["Mainkai", "Weseler Werft"]))
    store.save(Definition(name="Mauserzeit", kind="period", description="", values=["5-7"]))
    store.save(Definition(name="Kerngruppe", kind="ring_group", description="", values=["A1", "B2"]))
    monkeypatch.setattr(runtime, "definitions", lambda: store)
    return store


def test_empty_filter_is_true():
    sql, params = compile_filters(get_source("sightings"), FilterSpec())
    assert sql == "TRUE" and params == []
    assert describe_filters(FilterSpec(), get_source("sightings")) == "alle Sichtungen"


def test_compile_filters_sightings(defs):
    f = FilterSpec(species=["Kanadagans"], places=["Ostpark"], exclude_places=["Rebstock"], place_groups=["Nordufer"], rings=["X1"], ring_groups=["Kerngruppe"],
                   date_from="2025-05-01", date_to="2025-07-31", months=[5, 6, 7], seasons=["apr_jun"], periods=["Mauserzeit"], years=[2024, 2025],
                   status=["MG"], age=[1], sex=[2], melder=["IR"], ringing_age=[1, 3], around_place="Ostpark", around_place_km=3, only_with_coords=True, only_exact_location=True)
    sql, params = compile_filters(get_source("sightings"), f)
    assert "species IN (%s)" in sql and params[0] == "Kanadagans"
    assert "place ILIKE %s" in sql and "%Ostpark%" in params
    assert "place NOT ILIKE %s" in sql and "%Rebstock%" in params
    assert "(place ILIKE '%Mainkai%' OR place ILIKE '%Weseler Werft%')" in sql
    assert "ring IN (%s)" in sql and "(ring IN ('A1', 'B2'))" in sql
    assert "date >= %s::date" in sql and "date <= %s::date" in sql
    assert "EXTRACT(MONTH FROM date) IN (5, 6, 7)" in sql and "IN (4, 5, 6)" in sql
    assert "EXTRACT(YEAR FROM date) IN (2024, 2025)" in sql
    assert "status IN (%s)" in sql and "age IN (%s)" in sql and "sex IN (%s)" in sql and "melder IN (%s)" in sql and "ringing_age IN (%s, %s)" in sql
    assert "SELECT AVG(lat) FROM v_sightings WHERE place ILIKE %s" in sql and params[-1] == 3
    assert "(lat IS NOT NULL AND lon IS NOT NULL)" in sql and "is_exact_location IS TRUE" in sql
    assert ";" not in sql


def test_custom_sql_guard():
    s = get_source("sightings")
    sql, _ = compile_filters(s, FilterSpec(custom_sql="large_group_size > 10 AND comment ILIKE '%Familie; 3%'"))
    assert "(large_group_size > 10" in sql
    for bad in ("1=1; DROP TABLE x", "ring IN (SELECT email FROM users)", "pg_sleep(10) IS NULL"):
        with pytest.raises(SourceError):
            compile_filters(s, FilterSpec(custom_sql=bad))


def test_unsupported_filters_raise_german(defs):
    with pytest.raises(SourceError, match="Beziehungen"):
        compile_filters(get_source("relationships"), FilterSpec(species=["Graugans"]))
    with pytest.raises(SourceError, match="nicht verfügbar"):
        compile_filters(get_source("ringings"), FilterSpec(melder=["IR"]))
    # rings on relationships hit both columns
    sql, params = compile_filters(get_source("relationships"), FilterSpec(rings=["A", "B"], years=[2024]))
    assert "bird1_ring IN (%s, %s) OR bird2_ring IN (%s, %s)" in sql and "year IN (2024)" in sql and params == ["A", "B", "A", "B"]
    with pytest.raises(SourceError, match="JJJJ-MM-TT"):
        compile_filters(get_source("sightings"), FilterSpec(date_from="01.05.2025"))
    with pytest.raises(SourceError, match="Unbekannte Definition"):
        compile_filters(get_source("sightings"), FilterSpec(place_groups=["Gibtsnicht"]))


def test_describe_filters_german(defs):
    f = FilterSpec(species=["Kanadagans"], places=["Ostpark"], months=[5, 6, 7], years=[2025], only_with_coords=True)
    assert describe_filters(f, get_source("sightings")) == "Sichtungen der Art Kanadagans, an Orten mit ‚Ostpark‘ im Namen, in den Monaten Mai–Juli, im Jahr 2025, nur mit Koordinaten"
    f2 = FilterSpec(species=["Graugans", "Nilgans"], place_groups=["Nordufer"], year_from=2019, year_to=2025, seasons=["nov_jan"], status=["BV"], exclude_places=["Ostpark"])
    assert describe_filters(f2, get_source("sightings")) == "Sichtungen der Arten Graugans und Nilgans, im Gebiet ‚Nordufer‘, ohne ‚Ostpark‘, in der Jahreszeit Nov–Jan, 2019–2025, mit Status Brutvogel"
    assert describe_filters(FilterSpec(ringing_places=["Ostpark"]), get_source("birds")) == "Vögel beringt in ‚Ostpark‘"


def test_build_aggregate_sql_shape():
    s = get_source("sightings")
    sql, params = build_aggregate_sql(s, FilterSpec(species=["Kanadagans"]), "birds", None, ["month", "species"])
    assert sql.startswith("SELECT EXTRACT(MONTH FROM date)::int AS month, COALESCE(species, 'unbekannt') AS species, COUNT(DISTINCT ring) AS value FROM (SELECT ")
    assert "WHERE species IN (%s) GROUP BY 1, 2 ORDER BY 1, 2" in sql and params == ["Kanadagans"]
    sql, _ = build_aggregate_sql(s, FilterSpec(), "sightings", None, ["season"])
    assert "ORDER BY MIN(CASE WHEN EXTRACT(MONTH FROM date) IN (11, 12, 1) THEN 1" in sql
    sql, _ = build_aggregate_sql(s, FilterSpec(), "mean", "large_group_size", [])
    assert sql.startswith("SELECT AVG(large_group_size) AS value FROM") and "GROUP BY" not in sql
    sql, _ = build_aggregate_sql(get_source("birds"), FilterSpec(), "median", "max_km", ["ringing_year"])
    assert "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY max_km)" in sql and "{date}" not in sql
    with pytest.raises(SourceError, match="braucht eine Spalte"):
        build_aggregate_sql(s, FilterSpec(), "sum", None, ["month"])
    with pytest.raises(SourceError, match="nicht verfügbar"):
        build_aggregate_sql(get_source("relationships"), FilterSpec(), "sightings", None, ["month"])
    with pytest.raises(SourceError, match="nicht verfügbar"):
        build_aggregate_sql(get_source("relationships"), FilterSpec(), "birds", None, ["year"])


def test_build_rows_sql():
    s = get_source("sightings")
    sql, params = build_rows_sql(s, FilterSpec(rings=["A"]), ["ring", "date", "lat", "lon"], limit=10)
    assert sql.endswith("WHERE ring IN (%s) ORDER BY date LIMIT 10") and params == ["A"]
    with pytest.raises(SourceError):
        build_rows_sql(s, FilterSpec(), ["nope"])
    sql, _ = build_rows_sql(get_source("relationships"), FilterSpec())
    assert "ORDER BY" not in sql


def test_dimensions_and_describe():
    for d in DIMENSIONS.values():
        for key in d.sources:
            assert "{" not in d.expr(SOURCES[key])
    desc = describe_sources()
    assert {s["key"] for s in desc["sources"]} == set(SOURCES)
    sightings = next(s for s in desc["sources"] if s["key"] == "sightings")
    assert "species" in sightings["filters"] and "month" in sightings["dimensions"] and "birds" in sightings["metrics"]
    rel = next(s for s in desc["sources"] if s["key"] == "relationships")
    assert "species" not in rel["filters"] and "birds" not in rel["metrics"] and "year" in rel["dimensions"]
    assert all(m["label"] for m in desc["metrics"]) and len(desc["filters"]) > 15
    assert set(METRICS) >= {"sightings", "birds", "observation_days", "median"}
