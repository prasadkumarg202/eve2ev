-- ---------------------------------------------------------------------------
-- schema_postgis.sql — production DDL for the osm-india-etl location database.
--
-- Idempotent: every statement uses IF NOT EXISTS so the script can be re-run.
-- Master table `locations` holds every record (all LOCATION_COLUMNS);
-- per-tier bucket tables hold a slim, query-optimized projection.
-- ---------------------------------------------------------------------------

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ---------------------------------------------------------------------------
-- Master table: one row per location entity (unified across all tiers).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS locations (
    location_id    TEXT PRIMARY KEY,
    osm_id         BIGINT NOT NULL,
    osm_type       TEXT NOT NULL CHECK (osm_type IN ('node', 'way', 'relation')),
    place_type     TEXT NOT NULL DEFAULT 'unknown',
    admin_level    SMALLINT,
    name           TEXT NOT NULL DEFAULT '',
    name_en        TEXT NOT NULL DEFAULT '',
    name_native    TEXT NOT NULL DEFAULT '',
    name_title     TEXT NOT NULL DEFAULT '',
    name_lower     TEXT NOT NULL DEFAULT '',
    name_ascii     TEXT NOT NULL DEFAULT '',
    search_name    TEXT NOT NULL DEFAULT '',
    slug           TEXT NOT NULL DEFAULT '',
    names_json     JSONB,
    aliases_json   JSONB,
    pincode        TEXT,
    latitude       DOUBLE PRECISION,
    longitude      DOUBLE PRECISION,
    geometry_wkt   TEXT,
    bbox_json      JSONB,
    area_sqkm      DOUBLE PRECISION NOT NULL DEFAULT 0,
    parent_id      TEXT,
    parent_type    TEXT,
    hierarchy_json JSONB,
    state_name     TEXT,
    district_name  TEXT,
    tags_json      JSONB,
    source_file    TEXT NOT NULL DEFAULT '',
    geom           geometry(Geometry, 4326),
    search_vector  tsvector GENERATED ALWAYS AS (
        to_tsvector('simple', coalesce(name, '') || ' ' || coalesce(search_name, ''))
    ) STORED
);

CREATE INDEX IF NOT EXISTS idx_locations_geom        ON locations USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_locations_search_trgm ON locations USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_locations_name_trgm   ON locations USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_locations_tsv         ON locations USING GIN (search_vector);
CREATE INDEX IF NOT EXISTS idx_locations_parent      ON locations (parent_id);
CREATE INDEX IF NOT EXISTS idx_locations_pincode     ON locations (pincode);
CREATE INDEX IF NOT EXISTS idx_locations_place_type  ON locations (place_type);
CREATE INDEX IF NOT EXISTS idx_locations_admin_level ON locations (admin_level);
CREATE INDEX IF NOT EXISTS idx_locations_slug        ON locations (slug);

-- ---------------------------------------------------------------------------
-- Auxiliary: aliases (one row per alternate name) and geometry side table.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aliases (
    location_id TEXT NOT NULL REFERENCES locations (location_id) ON DELETE CASCADE,
    alias       TEXT NOT NULL,
    PRIMARY KEY (location_id, alias)
);

CREATE INDEX IF NOT EXISTS idx_aliases_alias_trgm ON aliases USING GIN (alias gin_trgm_ops);

CREATE TABLE IF NOT EXISTS geometry (
    location_id  TEXT PRIMARY KEY REFERENCES locations (location_id) ON DELETE CASCADE,
    geom         geometry(Geometry, 4326),
    geometry_wkt TEXT,
    bbox_json    JSONB,
    area_sqkm    DOUBLE PRECISION NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_geometry_geom ON geometry USING GIST (geom);

-- ---------------------------------------------------------------------------
-- Per-tier bucket tables (slim projections of `locations`).
-- parent_id is an FK to the parent location in the master table.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS states (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_states_geom        ON states USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_states_search_trgm ON states USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_states_name_trgm   ON states USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_states_parent      ON states (parent_id);
CREATE INDEX IF NOT EXISTS idx_states_pincode     ON states (pincode);

CREATE TABLE IF NOT EXISTS districts (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_districts_geom        ON districts USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_districts_search_trgm ON districts USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_districts_name_trgm   ON districts USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_districts_parent      ON districts (parent_id);
CREATE INDEX IF NOT EXISTS idx_districts_pincode     ON districts (pincode);

CREATE TABLE IF NOT EXISTS subdistricts (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_subdistricts_geom        ON subdistricts USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_subdistricts_search_trgm ON subdistricts USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_subdistricts_name_trgm   ON subdistricts USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_subdistricts_parent      ON subdistricts (parent_id);
CREATE INDEX IF NOT EXISTS idx_subdistricts_pincode     ON subdistricts (pincode);

CREATE TABLE IF NOT EXISTS mandals (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_mandals_geom        ON mandals USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_mandals_search_trgm ON mandals USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_mandals_name_trgm   ON mandals USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_mandals_parent      ON mandals (parent_id);
CREATE INDEX IF NOT EXISTS idx_mandals_pincode     ON mandals (pincode);

CREATE TABLE IF NOT EXISTS taluks (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_taluks_geom        ON taluks USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_taluks_search_trgm ON taluks USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_taluks_name_trgm   ON taluks USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_taluks_parent      ON taluks (parent_id);
CREATE INDEX IF NOT EXISTS idx_taluks_pincode     ON taluks (pincode);

CREATE TABLE IF NOT EXISTS villages (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_villages_geom        ON villages USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_villages_search_trgm ON villages USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_villages_name_trgm   ON villages USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_villages_parent      ON villages (parent_id);
CREATE INDEX IF NOT EXISTS idx_villages_pincode     ON villages (pincode);

CREATE TABLE IF NOT EXISTS towns (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_towns_geom        ON towns USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_towns_search_trgm ON towns USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_towns_name_trgm   ON towns USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_towns_parent      ON towns (parent_id);
CREATE INDEX IF NOT EXISTS idx_towns_pincode     ON towns (pincode);

CREATE TABLE IF NOT EXISTS cities (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_cities_geom        ON cities USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_cities_search_trgm ON cities USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cities_name_trgm   ON cities USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_cities_parent      ON cities (parent_id);
CREATE INDEX IF NOT EXISTS idx_cities_pincode     ON cities (pincode);

CREATE TABLE IF NOT EXISTS wards (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_wards_geom        ON wards USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_wards_search_trgm ON wards USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_wards_name_trgm   ON wards USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_wards_parent      ON wards (parent_id);
CREATE INDEX IF NOT EXISTS idx_wards_pincode     ON wards (pincode);

CREATE TABLE IF NOT EXISTS localities (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_localities_geom        ON localities USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_localities_search_trgm ON localities USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_localities_name_trgm   ON localities USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_localities_parent      ON localities (parent_id);
CREATE INDEX IF NOT EXISTS idx_localities_pincode     ON localities (pincode);

CREATE TABLE IF NOT EXISTS neighbourhoods (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_neighbourhoods_geom        ON neighbourhoods USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_neighbourhoods_search_trgm ON neighbourhoods USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_neighbourhoods_name_trgm   ON neighbourhoods USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_neighbourhoods_parent      ON neighbourhoods (parent_id);
CREATE INDEX IF NOT EXISTS idx_neighbourhoods_pincode     ON neighbourhoods (pincode);

CREATE TABLE IF NOT EXISTS streets (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_streets_geom        ON streets USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_streets_search_trgm ON streets USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_streets_name_trgm   ON streets USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_streets_parent      ON streets (parent_id);
CREATE INDEX IF NOT EXISTS idx_streets_pincode     ON streets (pincode);

CREATE TABLE IF NOT EXISTS roads (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_roads_geom        ON roads USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_roads_search_trgm ON roads USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_roads_name_trgm   ON roads USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_roads_parent      ON roads (parent_id);
CREATE INDEX IF NOT EXISTS idx_roads_pincode     ON roads (pincode);

CREATE TABLE IF NOT EXISTS highways (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_highways_geom        ON highways USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_highways_search_trgm ON highways USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_highways_name_trgm   ON highways USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_highways_parent      ON highways (parent_id);
CREATE INDEX IF NOT EXISTS idx_highways_pincode     ON highways (pincode);

CREATE TABLE IF NOT EXISTS buildings (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_buildings_geom        ON buildings USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_buildings_search_trgm ON buildings USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_buildings_name_trgm   ON buildings USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_buildings_parent      ON buildings (parent_id);
CREATE INDEX IF NOT EXISTS idx_buildings_pincode     ON buildings (pincode);

CREATE TABLE IF NOT EXISTS postal_codes (
    id          BIGSERIAL PRIMARY KEY,
    location_id TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id      BIGINT NOT NULL,
    name        TEXT NOT NULL DEFAULT '',
    search_name TEXT NOT NULL DEFAULT '',
    pincode     TEXT,
    parent_id   TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    geom        geometry(Geometry, 4326)
);

CREATE INDEX IF NOT EXISTS idx_postal_codes_geom        ON postal_codes USING GIST (geom);
CREATE INDEX IF NOT EXISTS idx_postal_codes_search_trgm ON postal_codes USING GIN (search_name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_postal_codes_name_trgm   ON postal_codes USING GIN (name gin_trgm_ops);
CREATE INDEX IF NOT EXISTS idx_postal_codes_parent      ON postal_codes (parent_id);
CREATE INDEX IF NOT EXISTS idx_postal_codes_pincode     ON postal_codes (pincode);
