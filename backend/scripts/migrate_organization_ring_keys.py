#!/usr/bin/env python3
"""Scope existing bird identities and view joins by organization.

Run with DATABASE_URL and --apply after a verified backup. Without --apply,
the migration executes its assertions then rolls back. Re-running is safe.
"""

import argparse
import os

import psycopg2
from psycopg2 import sql


def migrate(connection):
    with connection.cursor() as cur:
        cur.execute("SET LOCAL lock_timeout = '5s'")
        cur.execute("SET LOCAL statement_timeout = '60s'")
        cur.execute("SELECT pg_advisory_xact_lock(20260924, 1)")
        cur.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='public.ringings'::regclass AND conname='uq_ringings_org_ring'"
        )
        existing = cur.fetchone()
        if existing is None:
            cur.execute(
                "ALTER TABLE public.ringings ADD CONSTRAINT uq_ringings_org_ring UNIQUE (org_id, ring)"
            )
        else:
            assert existing[0] == "UNIQUE (org_id, ring)", existing

        cur.execute(
            "SELECT indisunique FROM pg_index WHERE indexrelid='public.ix_ringings_ring'::regclass"
        )
        if cur.fetchone()[0]:
            cur.execute("DROP INDEX public.ix_ringings_ring")
            cur.execute("CREATE INDEX ix_ringings_ring ON public.ringings (ring)")

        cur.execute(
            "SELECT pg_get_constraintdef(oid) FROM pg_constraint WHERE conrelid='public.bird_relationships'::regclass AND conname='uq_bird_relationship'"
        )
        definition = cur.fetchone()[0]
        expected = "UNIQUE (org_id, bird1_ring, bird2_ring, relationship_type, year)"
        if definition != expected:
            assert (
                definition == "UNIQUE (bird1_ring, bird2_ring, relationship_type, year)"
            ), definition
            cur.execute(
                "ALTER TABLE public.bird_relationships DROP CONSTRAINT uq_bird_relationship"
            )
            cur.execute(
                "ALTER TABLE public.bird_relationships ADD CONSTRAINT uq_bird_relationship UNIQUE (org_id, bird1_ring, bird2_ring, relationship_type, year)"
            )

        # Preserve existing view columns, filters, comments, and grants. Amend
        # only the join predicates that otherwise multiply rows after a clone.
        joins = {
            "bird_family_tree": [
                ("br", "bird1_ring", "r1"),
                ("br", "bird2_ring", "r2"),
            ],
            "v_sightings": [("s", "ring", "r")],
        }
        for view, predicates in joins.items():
            cur.execute("SELECT to_regclass(%s)", ("public." + view,))
            if cur.fetchone()[0] is None:
                continue
            cur.execute(
                "SELECT pg_get_viewdef(%s::regclass, false)", ("public." + view,)
            )
            before = cur.fetchone()[0]
            after = before
            for left, column, right in predicates:
                guard = f"{left}.org_id = {right}.org_id"
                if guard in after:
                    continue
                predicate = f"(({left}.{column})::text = ({right}.ring)::text)"
                expected_count = 2 if view == "v_sightings" else 1
                assert after.count(predicate) == expected_count, (view, predicate)
                after = after.replace(predicate, f"({predicate} AND ({guard}))")
            if after != before:
                cur.execute(
                    sql.SQL("CREATE OR REPLACE VIEW public.{} AS ").format(
                        sql.Identifier(view)
                    )
                    + sql.SQL(after)
                )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    connection = psycopg2.connect(os.environ["DATABASE_URL"])
    try:
        migrate(connection)
        if args.apply:
            connection.commit()
            print("Organization-scoped ring keys and view joins applied.")
        else:
            connection.rollback()
            print("Migration validated; rolled back (pass --apply to persist).")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
