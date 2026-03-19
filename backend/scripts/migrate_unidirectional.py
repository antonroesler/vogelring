#!/usr/bin/env python3
"""
Migration: Convert relationship system to unidirectional storage.

Steps (in a single transaction):
1. Drop old UniqueConstraint (uq_bird_relationship)
2. Convert child_of records to parent_of (swap bird1/bird2)
3. Normalize symmetric records: ensure bird1_ring < bird2_ring
4. Delete duplicates (keep record with most metadata)
5. Add new tighter UniqueConstraint (bird1_ring, bird2_ring, relationship_type, year)

Reports:
- child_of records converted
- orphaned child_of records (had no matching parent_of — converted instead of deleted)
- symmetric records normalized
- duplicate records deleted

Usage:
    DATABASE_URL=postgresql://... python scripts/migrate_unidirectional.py
    # or via Docker exec on Pi:
    docker exec vogelring-api uv run python scripts/migrate_unidirectional.py
"""

import os
import sys
import logging
from sqlalchemy import create_engine, text

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


def get_database_url() -> str:
    url = os.environ.get("DATABASE_URL")
    if not url:
        logger.error("DATABASE_URL environment variable not set")
        sys.exit(1)
    return url


def run_migration(engine) -> dict:
    """Run the full migration. Returns counts dict."""
    counts = {
        "child_of_converted": 0,
        "child_of_orphaned": 0,
        "symmetric_normalized": 0,
        "duplicates_deleted": 0,
    }

    with engine.begin() as conn:
        # ---- Step 1: Drop old UniqueConstraint ----
        logger.info("Step 1: Dropping old UniqueConstraint...")
        try:
            conn.execute(text("ALTER TABLE bird_relationships DROP CONSTRAINT IF EXISTS uq_bird_relationship"))
            logger.info("  Old constraint dropped (or did not exist)")
        except Exception as e:
            logger.warning(f"  Could not drop constraint: {e} (may be named differently)")

        # ---- Step 2: Convert child_of to parent_of ----
        logger.info("Step 2: Converting child_of records to parent_of...")

        child_of_rows = conn.execute(
            text("SELECT id, bird1_ring, bird2_ring, year, org_id, sighting1_id, sighting2_id, ringing1_id, ringing2_id FROM bird_relationships WHERE relationship_type = 'child_of'")
        ).fetchall()

        logger.info(f"  Found {len(child_of_rows)} child_of records")

        for row in child_of_rows:
            row_id = row[0]
            bird1 = row[1]  # was child
            bird2 = row[2]  # was parent
            year = row[3]
            org_id = row[4]
            s1_id = row[5]
            s2_id = row[6]
            r1_id = row[7]
            r2_id = row[8]

            # Check if a matching parent_of record already exists
            existing = conn.execute(
                text("""
                    SELECT id FROM bird_relationships
                    WHERE bird1_ring = :parent AND bird2_ring = :child
                      AND relationship_type = 'parent_of'
                      AND year = :year AND org_id = :org_id
                """),
                {"parent": bird2, "child": bird1, "year": year, "org_id": org_id},
            ).fetchone()

            if existing:
                # A parent_of record exists — delete the redundant child_of
                conn.execute(text("DELETE FROM bird_relationships WHERE id = :id"), {"id": row_id})
                counts["child_of_converted"] += 1
            else:
                # Orphaned child_of — convert to parent_of by swapping birds
                conn.execute(
                    text("""
                        UPDATE bird_relationships
                        SET relationship_type = 'parent_of',
                            bird1_ring = :parent,
                            bird2_ring = :child,
                            sighting1_id = :s1,
                            sighting2_id = :s2,
                            ringing1_id = :r1,
                            ringing2_id = :r2
                        WHERE id = :id
                    """),
                    {
                        "parent": bird2,
                        "child": bird1,
                        "s1": s2_id,
                        "s2": s1_id,
                        "r1": r2_id,
                        "r2": r1_id,
                        "id": row_id,
                    },
                )
                counts["child_of_orphaned"] += 1
                logger.warning(f"  Orphaned child_of: {bird1} child_of {bird2} (year={year}) — converted to parent_of")

        logger.info(f"  Converted: {counts['child_of_converted']} deleted (had matching parent_of)")
        logger.info(f"  Orphaned: {counts['child_of_orphaned']} converted to parent_of (no matching parent_of existed)")

        # ---- Step 3: Normalize symmetric relationships ----
        logger.info("Step 3: Normalizing symmetric relationships (bird1_ring < bird2_ring)...")

        symmetric_rows = conn.execute(
            text("""
                SELECT id, bird1_ring, bird2_ring, sighting1_id, sighting2_id, ringing1_id, ringing2_id
                FROM bird_relationships
                WHERE relationship_type IN ('breeding_partner', 'sibling_of')
                  AND bird1_ring > bird2_ring
            """)
        ).fetchall()

        logger.info(f"  Found {len(symmetric_rows)} symmetric records needing normalization")

        for row in symmetric_rows:
            row_id, bird1, bird2, s1, s2, r1, r2 = row
            conn.execute(
                text("""
                    UPDATE bird_relationships
                    SET bird1_ring = :b1, bird2_ring = :b2,
                        sighting1_id = :s1, sighting2_id = :s2,
                        ringing1_id = :r1, ringing2_id = :r2
                    WHERE id = :id
                """),
                {"b1": bird2, "b2": bird1, "s1": s2, "s2": s1, "r1": r2, "r2": r1, "id": row_id},
            )
            counts["symmetric_normalized"] += 1

        logger.info(f"  Normalized: {counts['symmetric_normalized']}")

        # ---- Step 4: Delete duplicate records ----
        logger.info("Step 4: Deleting duplicate records (keep record with most metadata)...")

        # Find groups with duplicates
        dup_groups = conn.execute(
            text("""
                SELECT bird1_ring, bird2_ring, relationship_type, year, org_id, COUNT(*) as cnt
                FROM bird_relationships
                GROUP BY bird1_ring, bird2_ring, relationship_type, year, org_id
                HAVING COUNT(*) > 1
            """)
        ).fetchall()

        logger.info(f"  Found {len(dup_groups)} duplicate groups")

        for group in dup_groups:
            b1, b2, rel_type, year, org_id, cnt = group

            # Fetch all records in this group, ordered by metadata richness (more non-null fields = better)
            rows = conn.execute(
                text("""
                    SELECT id,
                           (CASE WHEN sighting1_id IS NOT NULL THEN 1 ELSE 0 END +
                            CASE WHEN sighting2_id IS NOT NULL THEN 1 ELSE 0 END +
                            CASE WHEN ringing1_id  IS NOT NULL THEN 1 ELSE 0 END +
                            CASE WHEN ringing2_id  IS NOT NULL THEN 1 ELSE 0 END +
                            CASE WHEN notes        IS NOT NULL THEN 1 ELSE 0 END) AS score
                    FROM bird_relationships
                    WHERE bird1_ring = :b1 AND bird2_ring = :b2
                      AND relationship_type = :rel_type AND year = :year AND org_id = :org_id
                    ORDER BY score DESC, created_at ASC
                """),
                {"b1": b1, "b2": b2, "rel_type": rel_type, "year": year, "org_id": org_id},
            ).fetchall()

            # Keep the first (highest score), delete the rest
            delete_ids = [r[0] for r in rows[1:]]
            for del_id in delete_ids:
                conn.execute(text("DELETE FROM bird_relationships WHERE id = :id"), {"id": del_id})
                counts["duplicates_deleted"] += 1

        logger.info(f"  Deleted: {counts['duplicates_deleted']} duplicates")

        # ---- Step 5: Add new UniqueConstraint ----
        logger.info("Step 5: Adding new UniqueConstraint (bird1_ring, bird2_ring, relationship_type, year)...")
        try:
            conn.execute(text("""
                ALTER TABLE bird_relationships
                ADD CONSTRAINT uq_bird_relationship
                UNIQUE (bird1_ring, bird2_ring, relationship_type, year)
            """))
            logger.info("  New constraint added")
        except Exception as e:
            logger.warning(f"  Could not add constraint: {e} (may already exist)")

    return counts


def main():
    logger.info("=" * 60)
    logger.info("Vogelring: Unidirectional Relationship Migration")
    logger.info("=" * 60)

    url = get_database_url()
    engine = create_engine(url)

    try:
        counts = run_migration(engine)
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise

    logger.info("")
    logger.info("=" * 60)
    logger.info("Migration complete. Summary:")
    logger.info(f"  child_of records deleted (had parent_of counterpart): {counts['child_of_converted']}")
    logger.info(f"  child_of orphans converted to parent_of:               {counts['child_of_orphaned']}")
    logger.info(f"  symmetric records normalized (bird1 < bird2):          {counts['symmetric_normalized']}")
    logger.info(f"  duplicate records deleted:                              {counts['duplicates_deleted']}")
    logger.info("=" * 60)

    if counts["child_of_orphaned"] > 0:
        logger.warning(f"WARNING: {counts['child_of_orphaned']} orphaned child_of records were converted.")
        logger.warning("Investigate these — they indicate incomplete past relationship creation.")


if __name__ == "__main__":
    main()
