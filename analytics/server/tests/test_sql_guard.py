import pytest

from vogelring_analytics.db import SqlRejected, guard_sql


@pytest.mark.parametrize(
    "sql",
    [
        "SELECT * FROM v_sightings LIMIT 5",
        "  select ring, count(*) from v_sightings where place ilike '%Ostpark%' group by 1;",
        "WITH x AS (SELECT ring FROM v_sightings) SELECT * FROM x",
        "SELECT * FROM v_sightings WHERE comment = 'update later' -- note",
        "SELECT * FROM v_sightings WHERE status = 'drop'",
    ],
)
def test_accepts_read_only(sql):
    assert guard_sql(sql)


@pytest.mark.parametrize(
    "sql",
    [
        "DELETE FROM sightings",
        "SELECT 1; DROP TABLE sightings",
        "UPDATE sightings SET ring = 'x'",
        "SELECT * FROM users",
        "SELECT email FROM public.users",
        "SELECT * FROM organizations",
        "SELECT pg_sleep(10)",
        "SET statement_timeout = 0",
        "",
        "   ",
        "EXPLAIN SELECT 1",
    ],
)
def test_rejects(sql):
    with pytest.raises(SqlRejected):
        guard_sql(sql)


def test_semicolon_inside_literal_is_allowed():
    from vogelring_analytics.db import guard_sql
    assert guard_sql("SELECT STRING_AGG(place, '; ') FROM v_sightings").startswith("SELECT")
