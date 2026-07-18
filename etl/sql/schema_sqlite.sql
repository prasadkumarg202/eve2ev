-- ---------------------------------------------------------------------------
-- schema_sqlite.sql — SQLite schema for the osm-india-etl location database.
--
-- No spatial extension required: geometry is stored as WKT text plus
-- latitude/longitude reals. Full-text search is provided by an FTS5 virtual
-- table (external content on `locations`) kept in sync via triggers.
-- Idempotent: safe to re-run against an existing database.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- Master table: one row per location entity (all LOCATION_COLUMNS, plus a
-- denormalized space-joined `aliases` text column used by the FTS index).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS locations (
    location_id    TEXT PRIMARY KEY,
    osm_id         INTEGER NOT NULL,
    osm_type       TEXT NOT NULL CHECK (osm_type IN ('node', 'way', 'relation')),
    place_type     TEXT NOT NULL DEFAULT 'unknown',
    admin_level    INTEGER,
    name           TEXT NOT NULL DEFAULT '',
    name_en        TEXT NOT NULL DEFAULT '',
    name_native    TEXT NOT NULL DEFAULT '',
    name_title     TEXT NOT NULL DEFAULT '',
    name_lower     TEXT NOT NULL DEFAULT '',
    name_ascii     TEXT NOT NULL DEFAULT '',
    search_name    TEXT NOT NULL DEFAULT '',
    slug           TEXT NOT NULL DEFAULT '',
    names_json     TEXT,
    aliases_json   TEXT,
    pincode        TEXT,
    latitude       REAL,
    longitude      REAL,
    geometry_wkt   TEXT,
    bbox_json      TEXT,
    area_sqkm      REAL NOT NULL DEFAULT 0,
    parent_id      TEXT,
    parent_type    TEXT,
    hierarchy_json TEXT,
    state_name     TEXT,
    district_name  TEXT,
    tags_json      TEXT,
    source_file    TEXT NOT NULL DEFAULT '',
    aliases        TEXT NOT NULL DEFAULT ''
);

CREATE INDEX IF NOT EXISTS idx_locations_place_type ON locations (place_type);
CREATE INDEX IF NOT EXISTS idx_locations_parent     ON locations (parent_id);
CREATE INDEX IF NOT EXISTS idx_locations_pincode    ON locations (pincode);
CREATE INDEX IF NOT EXISTS idx_locations_name_lower ON locations (name_lower);
CREATE INDEX IF NOT EXISTS idx_locations_slug       ON locations (slug);

-- ---------------------------------------------------------------------------
-- Auxiliary tables.
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS aliases (
    location_id TEXT NOT NULL REFERENCES locations (location_id) ON DELETE CASCADE,
    alias       TEXT NOT NULL,
    PRIMARY KEY (location_id, alias)
);

CREATE INDEX IF NOT EXISTS idx_aliases_alias ON aliases (alias);

CREATE TABLE IF NOT EXISTS geometry (
    location_id  TEXT PRIMARY KEY REFERENCES locations (location_id) ON DELETE CASCADE,
    geometry_wkt TEXT,
    bbox_json    TEXT,
    area_sqkm    REAL NOT NULL DEFAULT 0,
    latitude     REAL,
    longitude    REAL
);

-- ---------------------------------------------------------------------------
-- Full-text search: FTS5 external-content table over (name, search_name,
-- aliases), content-linked to `locations` and synced via triggers.
-- ---------------------------------------------------------------------------
CREATE VIRTUAL TABLE IF NOT EXISTS locations_fts USING fts5(
    name,
    search_name,
    aliases,
    content='locations',
    content_rowid='rowid',
    tokenize='unicode61 remove_diacritics 2'
);

CREATE TRIGGER IF NOT EXISTS trg_locations_fts_ai AFTER INSERT ON locations BEGIN
    INSERT INTO locations_fts (rowid, name, search_name, aliases)
    VALUES (new.rowid, new.name, new.search_name, new.aliases);
END;

CREATE TRIGGER IF NOT EXISTS trg_locations_fts_ad AFTER DELETE ON locations BEGIN
    INSERT INTO locations_fts (locations_fts, rowid, name, search_name, aliases)
    VALUES ('delete', old.rowid, old.name, old.search_name, old.aliases);
END;

CREATE TRIGGER IF NOT EXISTS trg_locations_fts_au AFTER UPDATE ON locations BEGIN
    INSERT INTO locations_fts (locations_fts, rowid, name, search_name, aliases)
    VALUES ('delete', old.rowid, old.name, old.search_name, old.aliases);
    INSERT INTO locations_fts (rowid, name, search_name, aliases)
    VALUES (new.rowid, new.name, new.search_name, new.aliases);
END;

-- ---------------------------------------------------------------------------
-- Per-tier bucket tables (slim projections of `locations`).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS states (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_states_parent  ON states (parent_id);
CREATE INDEX IF NOT EXISTS idx_states_pincode ON states (pincode);
CREATE INDEX IF NOT EXISTS idx_states_search  ON states (search_name);

CREATE TABLE IF NOT EXISTS districts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_districts_parent  ON districts (parent_id);
CREATE INDEX IF NOT EXISTS idx_districts_pincode ON districts (pincode);
CREATE INDEX IF NOT EXISTS idx_districts_search  ON districts (search_name);

CREATE TABLE IF NOT EXISTS subdistricts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_subdistricts_parent  ON subdistricts (parent_id);
CREATE INDEX IF NOT EXISTS idx_subdistricts_pincode ON subdistricts (pincode);
CREATE INDEX IF NOT EXISTS idx_subdistricts_search  ON subdistricts (search_name);

CREATE TABLE IF NOT EXISTS mandals (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_mandals_parent  ON mandals (parent_id);
CREATE INDEX IF NOT EXISTS idx_mandals_pincode ON mandals (pincode);
CREATE INDEX IF NOT EXISTS idx_mandals_search  ON mandals (search_name);

CREATE TABLE IF NOT EXISTS taluks (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_taluks_parent  ON taluks (parent_id);
CREATE INDEX IF NOT EXISTS idx_taluks_pincode ON taluks (pincode);
CREATE INDEX IF NOT EXISTS idx_taluks_search  ON taluks (search_name);

CREATE TABLE IF NOT EXISTS villages (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_villages_parent  ON villages (parent_id);
CREATE INDEX IF NOT EXISTS idx_villages_pincode ON villages (pincode);
CREATE INDEX IF NOT EXISTS idx_villages_search  ON villages (search_name);

CREATE TABLE IF NOT EXISTS towns (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_towns_parent  ON towns (parent_id);
CREATE INDEX IF NOT EXISTS idx_towns_pincode ON towns (pincode);
CREATE INDEX IF NOT EXISTS idx_towns_search  ON towns (search_name);

CREATE TABLE IF NOT EXISTS cities (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_cities_parent  ON cities (parent_id);
CREATE INDEX IF NOT EXISTS idx_cities_pincode ON cities (pincode);
CREATE INDEX IF NOT EXISTS idx_cities_search  ON cities (search_name);

CREATE TABLE IF NOT EXISTS wards (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_wards_parent  ON wards (parent_id);
CREATE INDEX IF NOT EXISTS idx_wards_pincode ON wards (pincode);
CREATE INDEX IF NOT EXISTS idx_wards_search  ON wards (search_name);

CREATE TABLE IF NOT EXISTS localities (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_localities_parent  ON localities (parent_id);
CREATE INDEX IF NOT EXISTS idx_localities_pincode ON localities (pincode);
CREATE INDEX IF NOT EXISTS idx_localities_search  ON localities (search_name);

CREATE TABLE IF NOT EXISTS neighbourhoods (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_neighbourhoods_parent  ON neighbourhoods (parent_id);
CREATE INDEX IF NOT EXISTS idx_neighbourhoods_pincode ON neighbourhoods (pincode);
CREATE INDEX IF NOT EXISTS idx_neighbourhoods_search  ON neighbourhoods (search_name);

CREATE TABLE IF NOT EXISTS streets (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_streets_parent  ON streets (parent_id);
CREATE INDEX IF NOT EXISTS idx_streets_pincode ON streets (pincode);
CREATE INDEX IF NOT EXISTS idx_streets_search  ON streets (search_name);

CREATE TABLE IF NOT EXISTS roads (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_roads_parent  ON roads (parent_id);
CREATE INDEX IF NOT EXISTS idx_roads_pincode ON roads (pincode);
CREATE INDEX IF NOT EXISTS idx_roads_search  ON roads (search_name);

CREATE TABLE IF NOT EXISTS highways (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_highways_parent  ON highways (parent_id);
CREATE INDEX IF NOT EXISTS idx_highways_pincode ON highways (pincode);
CREATE INDEX IF NOT EXISTS idx_highways_search  ON highways (search_name);

CREATE TABLE IF NOT EXISTS buildings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_buildings_parent  ON buildings (parent_id);
CREATE INDEX IF NOT EXISTS idx_buildings_pincode ON buildings (pincode);
CREATE INDEX IF NOT EXISTS idx_buildings_search  ON buildings (search_name);

CREATE TABLE IF NOT EXISTS postal_codes (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id  TEXT NOT NULL UNIQUE REFERENCES locations (location_id) ON DELETE CASCADE,
    osm_id       INTEGER NOT NULL,
    name         TEXT NOT NULL DEFAULT '',
    search_name  TEXT NOT NULL DEFAULT '',
    pincode      TEXT,
    parent_id    TEXT REFERENCES locations (location_id) ON DELETE SET NULL,
    latitude     REAL,
    longitude    REAL,
    geometry_wkt TEXT
);

CREATE INDEX IF NOT EXISTS idx_postal_codes_parent  ON postal_codes (parent_id);
CREATE INDEX IF NOT EXISTS idx_postal_codes_pincode ON postal_codes (pincode);
CREATE INDEX IF NOT EXISTS idx_postal_codes_search  ON postal_codes (search_name);
