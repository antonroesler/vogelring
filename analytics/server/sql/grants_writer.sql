-- Restricted write role for the gated agent write path (analytics/server/src/vogelring_analytics/writes.py).
-- Run on the Pi (replace :password):
--   docker exec -i vogelring-postgres psql -U vogelring -d vogelring -v password="'…'" < analytics/server/sql/grants_writer.sql
-- Then set WRITE_DATABASE_URL=postgresql://vogelring_agent_writer:…@vogelring-postgres:5432/vogelring in .env.analytics.
--
-- Principles: no DELETE anywhere, no DDL, column-restricted UPDATE, every change goes through a proposed →
-- approved → applied changeset with recorded before/after values (rollback restores the before values).

-- psql variables are not expanded inside DO blocks, so build the statements with \gexec
SELECT format('CREATE ROLE vogelring_agent_writer LOGIN PASSWORD %L', :'password')
WHERE NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vogelring_agent_writer') \gexec
SELECT format('ALTER ROLE vogelring_agent_writer WITH LOGIN PASSWORD %L', :'password')
WHERE EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'vogelring_agent_writer') \gexec

REVOKE ALL ON ALL TABLES IN SCHEMA public FROM vogelring_agent_writer;
REVOKE CREATE ON SCHEMA public FROM vogelring_agent_writer;
GRANT USAGE ON SCHEMA public TO vogelring_agent_writer;

-- Read what it may change (and organizations for the org check); never users.
GRANT SELECT ON sightings, ringings, color_rings, organizations TO vogelring_agent_writer;

-- Column-restricted updates (mirrors writes.EDITABLE).
GRANT UPDATE (species, ring, reading, place, area, status, age, sex, melder, melded, partner, pair, comment,
              habitat, field_fruit, color_ring_color, color_ring_text_color, color_ring_code, lat, lon,
              is_exact_location, date, large_group_size, small_group_size, breed_size, family_size, updated_at)
  ON sightings TO vogelring_agent_writer;
GRANT UPDATE (species, place, ringer, age, sex, status, comment, lat, lon, date, updated_at)
  ON ringings TO vogelring_agent_writer;
GRANT INSERT, UPDATE ON color_rings TO vogelring_agent_writer;

ALTER ROLE vogelring_agent_writer SET default_transaction_read_only = off;
ALTER ROLE vogelring_agent_writer SET statement_timeout = '30s';
ALTER ROLE vogelring_agent_writer SET lock_timeout = '5s';
