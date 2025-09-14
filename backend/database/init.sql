-- Database initialization script
-- This script creates the database schema and indexes

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- PostgreSQL performance optimizations for Raspberry Pi
-- Adjust shared_buffers for limited RAM (128MB for 8GB Pi)
ALTER SYSTEM SET shared_buffers = '128MB';
-- Reduce work_mem for limited resources
ALTER SYSTEM SET work_mem = '4MB';
-- Optimize maintenance work memory
ALTER SYSTEM SET maintenance_work_mem = '64MB';
-- Enable query plan caching
ALTER SYSTEM SET plan_cache_mode = 'auto';
-- Optimize checkpoint settings for SSD storage
ALTER SYSTEM SET checkpoint_completion_target = 0.9;
ALTER SYSTEM SET wal_buffers = '16MB';

-- Reload configuration
SELECT pg_reload_conf();

-- Performance indexes will be created after tables are created by SQLAlchemy
-- These indexes optimize the most common query patterns for autocomplete and filtering

-- Function to create performance indexes after table creation
CREATE OR REPLACE FUNCTION create_performance_indexes() RETURNS void AS $$
BEGIN
    -- Sightings table performance indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_ring_lower ON sightings(LOWER(ring)) WHERE ring IS NOT NULL;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_species_lower ON sightings(LOWER(species)) WHERE species IS NOT NULL;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_place_lower ON sightings(LOWER(place)) WHERE place IS NOT NULL;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_reading_lower ON sightings(LOWER(reading)) WHERE reading IS NOT NULL;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_melder_lower ON sightings(LOWER(melder)) WHERE melder IS NOT NULL;
    
    -- Composite indexes for common query patterns
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_species_date_desc ON sightings(species, date DESC) WHERE species IS NOT NULL AND date IS NOT NULL;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_place_date_desc ON sightings(place, date DESC) WHERE place IS NOT NULL AND date IS NOT NULL;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_ring_date_desc ON sightings(ring, date DESC) WHERE ring IS NOT NULL AND date IS NOT NULL;
    
    -- Ringings table performance indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ringings_ring_lower ON ringings(LOWER(ring));
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ringings_species_lower ON ringings(LOWER(species));
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ringings_place_lower ON ringings(LOWER(place)) WHERE place IS NOT NULL;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ringings_ringer_lower ON ringings(LOWER(ringer));
    
    -- Composite indexes for ringings
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ringings_species_date_desc ON ringings(species, date DESC);
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ringings_ringer_date_desc ON ringings(ringer, date DESC);
    
    -- Family tree entries performance indexes
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_family_tree_ring_lower ON family_tree_entries(LOWER(ring));
    
    -- GIN indexes for JSONB columns (for family tree data)
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_family_tree_partners_gin ON family_tree_entries USING GIN(partners) WHERE partners IS NOT NULL;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_family_tree_children_gin ON family_tree_entries USING GIN(children) WHERE children IS NOT NULL;
    CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_family_tree_parents_gin ON family_tree_entries USING GIN(parents) WHERE parents IS NOT NULL;
    
    RAISE NOTICE 'Performance indexes created successfully';
END;
$$ LANGUAGE plpgsql;

-- Note: The create_performance_indexes() function should be called after table creation
-- This is handled in the application startup process