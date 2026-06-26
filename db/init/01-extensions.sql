-- Enabled once on first container boot. Phase 0 only provisions the extensions;
-- the schema (TestRun, Observation, Case, …) lands in Phase 1.
CREATE EXTENSION IF NOT EXISTS timescaledb;
CREATE EXTENSION IF NOT EXISTS vector;
