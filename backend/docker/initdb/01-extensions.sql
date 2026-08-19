-- =============================================================================
-- AlgoVision — local Postgres init script
-- =============================================================================
-- Run by the postgres image on first startup (alphabetical order).
-- Installs extensions the schema needs so migrations can assume they
-- exist. Idempotent (IF NOT EXISTS).
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "citext";