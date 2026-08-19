-- Runs automatically on first container start (docker-entrypoint-initdb.d),
-- only against an empty data volume. Idempotent, so it's harmless if the
-- postgis/postgis image's own init already created this.
CREATE EXTENSION IF NOT EXISTS postgis;
