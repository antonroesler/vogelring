#!/usr/bin/env python3
"""
Migration: Farbringe (color rings).

- Creates the `color_rings` registry table (also created by create_all on startup).
- Adds optional color ring columns to `sightings`:
    color_ring_color, color_ring_text_color, color_ring_code

Adding columns does not touch the v_sightings view.

Idempotent: existing table and columns are left alone.

Usage:
    DATABASE_URL=postgresql://... python scripts/migrate_color_rings.py
    # or on the Pi:
    docker exec vogelring-api uv run python scripts/migrate_color_rings.py
    docker restart vogelring-api
"""

import os
import sys
import logging
from sqlalchemy import create_engine, inspect, text

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.models import ColorRing  # noqa: E402
from src.database import organization_models  # noqa: E402,F401  (FK target)

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

SIGHTING_COLUMNS = {
    "color_ring_color": "VARCHAR(20)",
    "color_ring_text_color": "VARCHAR(20)",
    "color_ring_code": "VARCHAR(20)",
}


def migrate(engine) -> None:
    ColorRing.__table__.create(bind=engine, checkfirst=True)
    logger.info("Table color_rings present")

    existing = {c["name"] for c in inspect(engine).get_columns("sightings")}
    with engine.begin() as conn:
        for column, sql_type in SIGHTING_COLUMNS.items():
            if column in existing:
                logger.info(f"sightings.{column} already exists, skipping")
                continue
            conn.execute(text(f"ALTER TABLE sightings ADD COLUMN {column} {sql_type}"))
            logger.info(f"Added sightings.{column}")


def main() -> None:
    url = os.environ.get("DATABASE_URL")
    if not url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    migrate(create_engine(url))
    logger.info("Color ring migration complete")


if __name__ == "__main__":
    main()
