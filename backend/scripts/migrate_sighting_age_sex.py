#!/usr/bin/env python3
"""
Migration: Convert sighting `age`/`sex` from legacy strings to RING/EURING
integer codes, preserving the original values in hidden DB-only columns.

Before:
    sightings.age  varchar  — "ad"/"dj"/"vj"/"juv" (+ leaked numerics "1".."8", blanks)
    sightings.sex  varchar  — "M"/"W"/NULL

After:
    sightings.age  integer  — RING codes (ad->6, dj->3, vj->5, juv->1, numeric passthrough, blank->NULL)
    sightings.sex  integer  — M->1, W->2, blank->NULL
    sightings.age_legacy varchar  — original age value (immutable audit copy)
    sightings.sex_legacy varchar  — original sex value

The mapping is imported from src.utils.sighting_coding so the export, the UI, this
migration, and its tests all share one source of truth.

Idempotent: if `age` is already integer the migration is skipped.

Usage:
    DATABASE_URL=postgresql://... python scripts/migrate_sighting_age_sex.py
    # or on the Pi:
    docker exec vogelring-api uv run python scripts/migrate_sighting_age_sex.py
"""

import os
import re
import sys
import logging
from sqlalchemy import create_engine, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.utils.sighting_coding import AGE_LEGACY_CASES, SEX_LEGACY_CASES  # noqa: E402

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    return url


def _build_case(column: str, cases: list[tuple[str, int]]) -> str:
    """Build a SQL CASE that maps legacy string values to integer codes; ELSE NULL."""
    whens = "\n".join(f"            WHEN '{key}' THEN {code}" for key, code in cases)
    return f"CASE lower(trim({column}))\n{whens}\n            ELSE NULL\n        END"


def _column_type(conn, table: str, column: str) -> str | None:
    return conn.execute(
        text(
            "SELECT data_type FROM information_schema.columns "
            "WHERE table_name = :t AND column_name = :c"
        ),
        {"t": table, "c": column},
    ).scalar()


def _capture_view(conn, name: str) -> str | None:
    """Return a view's SELECT body if it exists, with the age/sex placeholder casts
    switched to integer so the recreated UNION stays type-consistent.

    Uses exec_driver_sql (raw) because the view body contains ``::`` casts that
    SQLAlchemy's text() bind-parameter parser would choke on. ``name`` is a
    hardcoded constant, so inlining it is safe.
    """
    exists = conn.exec_driver_sql(f"SELECT to_regclass('{name}')").scalar()
    if not exists:
        return None
    body = conn.exec_driver_sql(f"SELECT pg_get_viewdef('{name}'::regclass, true)").scalar()
    body = re.sub(r"NULL::character varying\(\d+\) AS age", "NULL::integer AS age", body)
    body = re.sub(r"NULL::character varying\(\d+\) AS sex", "NULL::integer AS sex", body)
    return body.rstrip().rstrip(";")


def run_migration(engine) -> dict:
    counts: dict = {}
    with engine.begin() as conn:
        age_type = _column_type(conn, "sightings", "age")
        if age_type in ("integer", "bigint", "smallint"):
            logger.info("sightings.age is already %s — migration already applied, skipping.", age_type)
            counts["skipped"] = True
            return counts

        logger.info("Current column types: age=%s sex=%s", age_type, _column_type(conn, "sightings", "sex"))

        # ---- Pre-migration distribution (for the record) ----
        for col in ("age", "sex"):
            rows = conn.execute(
                text(f"SELECT coalesce({col}, '<null>') v, count(*) c FROM sightings GROUP BY {col} ORDER BY c DESC")
            ).fetchall()
            logger.info("Pre-migration %s distribution: %s", col, {r[0]: r[1] for r in rows})

        # ---- Step 1: add hidden legacy columns ----
        logger.info("Step 1: adding hidden legacy columns age_legacy/sex_legacy...")
        conn.execute(text("ALTER TABLE sightings ADD COLUMN IF NOT EXISTS age_legacy varchar(20)"))
        conn.execute(text("ALTER TABLE sightings ADD COLUMN IF NOT EXISTS sex_legacy varchar(10)"))

        # ---- Step 2: preserve originals ----
        logger.info("Step 2: copying original values into legacy columns...")
        counts["age_legacy_set"] = conn.execute(
            text("UPDATE sightings SET age_legacy = age WHERE age_legacy IS NULL AND age IS NOT NULL")
        ).rowcount
        counts["sex_legacy_set"] = conn.execute(
            text("UPDATE sightings SET sex_legacy = sex WHERE sex_legacy IS NULL AND sex IS NOT NULL")
        ).rowcount

        # ---- Step 2b: drop dependent view(s) blocking the ALTER (recreated below) ----
        # Only v_sightings depends on sightings.age/sex (verified via pg_depend).
        view_body = _capture_view(conn, "v_sightings")
        if view_body is not None:
            logger.info("Dropping dependent view v_sightings (will recreate with integer casts)...")
            conn.exec_driver_sql("DROP VIEW v_sightings")

        # ---- Step 3: convert column types with the shared mapping ----
        logger.info("Step 3: converting age -> integer...")
        conn.execute(
            text(
                "ALTER TABLE sightings ALTER COLUMN age TYPE integer "
                f"USING ({_build_case('age', AGE_LEGACY_CASES)})"
            )
        )
        logger.info("Step 3: converting sex -> integer...")
        conn.execute(
            text(
                "ALTER TABLE sightings ALTER COLUMN sex TYPE integer "
                f"USING ({_build_case('sex', SEX_LEGACY_CASES)})"
            )
        )

        # ---- Step 3b: recreate the view (age/sex now integer on both branches) ----
        if view_body is not None:
            conn.exec_driver_sql(f"CREATE VIEW v_sightings AS {view_body}")
            logger.info("Recreated view v_sightings.")

        # ---- Post-migration distribution ----
        for col in ("age", "sex"):
            rows = conn.execute(
                text(f"SELECT coalesce({col}::text, '<null>') v, count(*) c FROM sightings GROUP BY {col} ORDER BY c DESC")
            ).fetchall()
            logger.info("Post-migration %s distribution: %s", col, {r[0]: r[1] for r in rows})

        # ---- Sanity: any legacy value that mapped to NULL but wasn't blank ----
        dropped = conn.execute(
            text(
                "SELECT coalesce(age_legacy,'<null>') v, count(*) c FROM sightings "
                "WHERE age IS NULL AND age_legacy IS NOT NULL AND trim(age_legacy) <> '' "
                "GROUP BY age_legacy ORDER BY c DESC"
            )
        ).fetchall()
        if dropped:
            counts["age_unmapped"] = {r[0]: r[1] for r in dropped}
            logger.warning("Age legacy values that mapped to NULL (kept in age_legacy): %s", counts["age_unmapped"])

    return counts


def main():
    logger.info("=" * 60)
    logger.info("Vogelring: Sighting age/sex -> RING integer code migration")
    logger.info("=" * 60)
    engine = create_engine(get_database_url())
    try:
        counts = run_migration(engine)
    except Exception as e:
        logger.error("Migration failed: %s", e)
        raise
    logger.info("=" * 60)
    logger.info("Done. Summary: %s", counts)
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
