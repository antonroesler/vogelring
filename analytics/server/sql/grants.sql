-- Tighten the LibreChat analytics role. Run as the vogelring superuser:
--   docker exec -i vogelring-postgres psql -U vogelring -d vogelring < analytics/server/sql/grants.sql
-- Idempotent.

REVOKE ALL ON TABLE users, organizations, sighting_exports, sighting_export_items FROM librechat_reader;
GRANT SELECT ON TABLE sightings, ringings, color_rings, bird_relationships TO librechat_reader;
GRANT SELECT ON v_sightings, bird_partners, bird_parents, bird_children, bird_siblings, bird_family_tree TO librechat_reader;

-- Hard limits regardless of what the application sends.
ALTER ROLE librechat_reader SET default_transaction_read_only = on;
ALTER ROLE librechat_reader SET statement_timeout = '45s';
ALTER ROLE librechat_reader SET idle_in_transaction_session_timeout = '60s';
ALTER ROLE librechat_reader SET search_path = public;
