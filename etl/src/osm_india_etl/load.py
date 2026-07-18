"""LOAD stage: materialize location records into SQLite, DuckDB, and PostGIS.

All loaders consume the TRANSFORM output (``processed/locations.parquet``,
columns = :data:`~osm_india_etl.constants.LOCATION_COLUMNS`). The SQLite path
uses only the standard library; DuckDB and PostGIS dependencies are
import-guarded so their absence never breaks the rest of the pipeline.
"""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable, Iterator
from pathlib import Path
from typing import Any

from .config import Settings, get_settings
from .constants import ENTITY_TABLES, LOCATION_COLUMNS, TYPE_TO_TABLE, PlaceType
from .logging_setup import StageTimer, log
from .models import LocationRecord

__all__ = ["load_duckdb", "load_postgis", "load_sqlite", "run_load"]

# Formats this stage owns (databases, not flat files).
DB_FORMATS: tuple[str, ...] = ("sqlite", "duckdb", "postgis")

# Slim projection stored in the per-tier bucket tables.
BUCKET_COLUMNS: tuple[str, ...] = (
    "location_id",
    "osm_id",
    "name",
    "search_name",
    "pincode",
    "parent_id",
    "latitude",
    "longitude",
    "geometry_wkt",
)

# Reverse of TYPE_TO_TABLE: bucket table -> list of place_type values it holds.
TABLE_TO_TYPES: dict[str, list[str]] = {table: [] for table in ENTITY_TABLES}
for _ptype, _table in TYPE_TO_TABLE.items():
    TABLE_TO_TYPES[_table].append(_ptype.value)

# Fallback location of the checked-in DDL (repo-root ``sql/`` directory).
_SQL_FALLBACK_DIR = Path(__file__).resolve().parents[2] / "sql"


# --------------------------------------------------------------------------- #
# Shared helpers
# --------------------------------------------------------------------------- #
def _resolve_path(settings: Settings, raw: str | Path) -> Path:
    """Resolve a possibly-relative configured path against the project root."""
    p = Path(raw)
    return p if p.is_absolute() else (settings.root / p).resolve()


def _default_parquet(settings: Settings) -> Path:
    return settings.path("processed") / "locations.parquet"


def _schema_sql(settings: Settings, filename: str) -> str:
    """Read a DDL file from the configured sql dir, falling back to the repo copy."""
    for candidate in (settings.path("sql") / filename, _SQL_FALLBACK_DIR / filename):
        if candidate.exists():
            return candidate.read_text(encoding="utf-8")
    raise FileNotFoundError(f"Schema file '{filename}' not found in sql directories")


def _iter_rows(
    locations_parquet: Path | None,
    records: Iterable[LocationRecord] | None,
) -> Iterator[dict[str, Any]]:
    """Yield canonical rows from in-memory records or from the Parquet file."""
    if records is not None:
        for record in records:
            yield record.to_row()
        return
    if locations_parquet is None:
        raise ValueError("Either a locations parquet path or records must be provided")
    from .exporters.tabular import iter_parquet_rows  # local import: avoids a cycle

    yield from iter_parquet_rows(locations_parquet)


def _bucket_for(row: dict[str, Any]) -> str | None:
    """Bucket table name for a row's place_type, or None for unmapped types."""
    try:
        return TYPE_TO_TABLE.get(PlaceType(row.get("place_type") or "unknown"))
    except ValueError:
        return None


def _aliases_list(row: dict[str, Any]) -> list[str]:
    raw = row.get("aliases_json")
    if not raw:
        return []
    if isinstance(raw, list):
        return [str(a) for a in raw if a]
    try:
        parsed = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    return [str(a) for a in parsed if a] if isinstance(parsed, list) else []


# --------------------------------------------------------------------------- #
# SQLite
# --------------------------------------------------------------------------- #
def load_sqlite(
    settings: Settings | None = None,
    locations_parquet: Path | None = None,
    *,
    records: Iterable[LocationRecord] | None = None,
    batch_size: int = 20_000,
) -> Path:
    """Load locations into a fresh SQLite database (stdlib ``sqlite3`` only).

    Runs ``sql/schema_sqlite.sql``, inserts every record into the unified
    ``locations`` table and its per-tier bucket table, populates the
    ``aliases`` and ``geometry`` aux tables, and builds/optimizes the FTS5
    index (kept in sync by triggers defined in the schema).

    Args:
        settings: Optional settings override.
        locations_parquet: Source Parquet file (default: processed/locations.parquet).
        records: Optional in-memory records; bypasses Parquet entirely (used by
            tests and small incremental loads).
        batch_size: Rows per executemany/commit batch.

    Returns:
        Path of the created SQLite database.
    """
    settings = settings or get_settings()
    db_path = _resolve_path(settings, settings.database.sqlite_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()

    schema = _schema_sql(settings, "schema_sqlite.sql")
    source = locations_parquet or (None if records is not None else _default_parquet(settings))

    loc_cols = LOCATION_COLUMNS + ("aliases",)
    sql_locations = (
        f"INSERT OR IGNORE INTO locations ({', '.join(loc_cols)}) "
        f"VALUES ({', '.join('?' * len(loc_cols))})"
    )
    sql_bucket = {
        table: (
            f"INSERT OR IGNORE INTO {table} ({', '.join(BUCKET_COLUMNS)}) "
            f"VALUES ({', '.join('?' * len(BUCKET_COLUMNS))})"
        )
        for table in ENTITY_TABLES
    }
    sql_alias = "INSERT OR IGNORE INTO aliases (location_id, alias) VALUES (?, ?)"
    sql_geometry = (
        "INSERT OR IGNORE INTO geometry "
        "(location_id, geometry_wkt, bbox_json, area_sqkm, latitude, longitude) "
        "VALUES (?, ?, ?, ?, ?, ?)"
    )

    conn = sqlite3.connect(db_path)
    try:
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA synchronous = OFF")
        conn.executescript(schema)

        loc_buf: list[tuple[Any, ...]] = []
        bucket_buf: dict[str, list[tuple[Any, ...]]] = {}
        alias_buf: list[tuple[str, str]] = []
        geom_buf: list[tuple[Any, ...]] = []

        def flush() -> None:
            # locations first so FK targets exist before bucket/aux rows.
            conn.executemany(sql_locations, loc_buf)
            for table, rows in bucket_buf.items():
                conn.executemany(sql_bucket[table], rows)
            conn.executemany(sql_alias, alias_buf)
            conn.executemany(sql_geometry, geom_buf)
            conn.commit()
            loc_buf.clear()
            bucket_buf.clear()
            alias_buf.clear()
            geom_buf.clear()

        with StageTimer("load.sqlite") as timer:
            for row in _iter_rows(source, records):
                aliases = _aliases_list(row)
                loc_buf.append(
                    tuple(row.get(col) for col in LOCATION_COLUMNS) + (" ".join(aliases),)
                )
                location_id = row.get("location_id")
                bucket = _bucket_for(row)
                if bucket:
                    bucket_buf.setdefault(bucket, []).append(
                        tuple(row.get(col) for col in BUCKET_COLUMNS)
                    )
                alias_buf.extend((location_id, alias) for alias in aliases)
                if row.get("geometry_wkt") or row.get("latitude") is not None:
                    geom_buf.append(
                        (
                            location_id,
                            row.get("geometry_wkt"),
                            row.get("bbox_json"),
                            row.get("area_sqkm") or 0.0,
                            row.get("latitude"),
                            row.get("longitude"),
                        )
                    )
                timer.add()
                if len(loc_buf) >= batch_size:
                    flush()
            flush()

            # Merge FTS b-trees written by the sync triggers and refresh stats.
            conn.execute("INSERT INTO locations_fts(locations_fts) VALUES ('optimize')")
            conn.execute("ANALYZE")
            conn.commit()
    finally:
        conn.close()

    log.info("SQLite database ready -> {}", db_path)
    return db_path


# --------------------------------------------------------------------------- #
# DuckDB
# --------------------------------------------------------------------------- #
def load_duckdb(
    settings: Settings | None = None,
    locations_parquet: Path | None = None,
) -> Path:
    """Load the locations Parquet into a DuckDB database.

    Creates/replaces the ``locations`` table straight from Parquet, adds a
    spatial ``geom`` column when the DuckDB spatial extension is available,
    and defines one view per bucket table filtered by place_type.

    Returns:
        Path of the created DuckDB database.

    Raises:
        RuntimeError: if the ``duckdb`` package is not installed.
    """
    settings = settings or get_settings()
    try:
        import duckdb
    except ImportError as exc:
        raise RuntimeError("DuckDB load requires the 'duckdb' package") from exc

    source = locations_parquet or _default_parquet(settings)
    db_path = _resolve_path(settings, settings.database.duckdb_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(str(db_path))
    try:
        with StageTimer("load.duckdb"):
            spatial = False
            try:
                con.execute("INSTALL spatial")
                con.execute("LOAD spatial")
                spatial = True
            except Exception as exc:
                log.warning("DuckDB spatial extension unavailable: {}", exc)

            con.execute(
                "CREATE OR REPLACE TABLE locations AS SELECT * FROM read_parquet(?)",
                [str(source)],
            )
            if spatial:
                try:
                    con.execute("ALTER TABLE locations ADD COLUMN IF NOT EXISTS geom GEOMETRY")
                    con.execute(
                        "UPDATE locations SET geom = ST_GeomFromText(geometry_wkt) "
                        "WHERE geometry_wkt IS NOT NULL"
                    )
                except Exception as exc:
                    log.warning("DuckDB geometry materialization failed: {}", exc)

            for table, types in TABLE_TO_TYPES.items():
                type_list = ", ".join(f"'{t}'" for t in types)
                con.execute(
                    f"CREATE OR REPLACE VIEW {table} AS "
                    f"SELECT * FROM locations WHERE place_type IN ({type_list})"
                )
            count = con.execute("SELECT COUNT(*) FROM locations").fetchone()[0]
            log.info("DuckDB: {} locations, {} bucket views -> {}",
                     count, len(TABLE_TO_TYPES), db_path)
    finally:
        con.close()
    return db_path


# --------------------------------------------------------------------------- #
# PostGIS
# --------------------------------------------------------------------------- #
def load_postgis(
    settings: Settings | None = None,
    locations_parquet: Path | None = None,
    *,
    batch_size: int = 5_000,
) -> None:
    """Load locations into PostgreSQL/PostGIS via SQLAlchemy.

    Runs ``sql/schema_postgis.sql``, bulk-inserts rows in executemany batches
    (geometry populated with ``ST_GeomFromText(geometry_wkt, 4326)``), then
    fills the bucket, ``aliases`` and ``geometry`` tables server-side.

    Raises:
        RuntimeError: if SQLAlchemy (or its psycopg driver) is not installed.
    """
    settings = settings or get_settings()
    try:
        from sqlalchemy import create_engine, text
    except ImportError as exc:
        raise RuntimeError("PostGIS load requires 'sqlalchemy' and 'psycopg'") from exc

    schema_ddl = _schema_sql(settings, "schema_postgis.sql")
    source = locations_parquet or _default_parquet(settings)
    schema_name = settings.database.schema_

    insert_cols = ", ".join(LOCATION_COLUMNS) + ", geom"
    insert_vals = ", ".join(f":{col}" for col in LOCATION_COLUMNS)
    sql_insert = text(
        f"INSERT INTO locations ({insert_cols}) "
        f"VALUES ({insert_vals}, ST_GeomFromText(:geometry_wkt, 4326)) "
        "ON CONFLICT (location_id) DO NOTHING"
    )

    engine = create_engine(settings.database.sqlalchemy_url)
    try:
        with StageTimer("load.postgis") as timer, engine.begin() as conn:
            if schema_name and schema_name != "public":
                conn.exec_driver_sql(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"')
                conn.exec_driver_sql(f'SET search_path TO "{schema_name}", public')
            conn.exec_driver_sql(schema_ddl)

            batch: list[dict[str, Any]] = []

            def flush() -> None:
                if batch:
                    conn.execute(sql_insert, batch)  # executemany
                    batch.clear()

            for row in _iter_rows(source, None):
                batch.append({col: row.get(col) for col in LOCATION_COLUMNS})
                timer.add()
                if len(batch) >= batch_size:
                    flush()
            flush()

            # Server-side fills: bucket tables, aliases, geometry side table.
            for table, types in TABLE_TO_TYPES.items():
                type_list = ", ".join(f"'{t}'" for t in types)
                conn.exec_driver_sql(
                    f"INSERT INTO {table} "
                    "(location_id, osm_id, name, search_name, pincode, parent_id, geom) "
                    "SELECT l.location_id, l.osm_id, l.name, l.search_name, l.pincode, "
                    "       (SELECT p.location_id FROM locations p "
                    "         WHERE p.location_id = l.parent_id), "
                    "       l.geom "
                    f"FROM locations l WHERE l.place_type IN ({type_list}) "
                    "ON CONFLICT (location_id) DO NOTHING"
                )
            conn.exec_driver_sql(
                "INSERT INTO aliases (location_id, alias) "
                "SELECT location_id, jsonb_array_elements_text(aliases_json) "
                "FROM locations "
                "WHERE aliases_json IS NOT NULL AND jsonb_typeof(aliases_json) = 'array' "
                "ON CONFLICT DO NOTHING"
            )
            conn.exec_driver_sql(
                "INSERT INTO geometry (location_id, geom, geometry_wkt, bbox_json, area_sqkm) "
                "SELECT location_id, geom, geometry_wkt, bbox_json, area_sqkm FROM locations "
                "ON CONFLICT (location_id) DO UPDATE SET "
                "geom = EXCLUDED.geom, geometry_wkt = EXCLUDED.geometry_wkt, "
                "bbox_json = EXCLUDED.bbox_json, area_sqkm = EXCLUDED.area_sqkm"
            )
            conn.exec_driver_sql("ANALYZE locations")
        log.info("PostGIS load complete -> {}", settings.database.sqlalchemy_url)
    finally:
        engine.dispose()


# --------------------------------------------------------------------------- #
# Dispatcher
# --------------------------------------------------------------------------- #
def run_load(
    settings: Settings | None = None,
    locations_parquet: Path | None = None,
) -> dict[str, Path | None]:
    """Run every database load configured in ``settings.export.formats``.

    Formats whose optional dependency is missing are skipped with a warning
    (mapped to ``None``); genuine load errors propagate.

    Returns:
        Mapping of format -> database path (``None`` for postgis / skipped).
    """
    settings = settings or get_settings()
    source = locations_parquet or _default_parquet(settings)
    wanted = [fmt for fmt in dict.fromkeys(settings.export.formats) if fmt in DB_FORMATS]
    results: dict[str, Path | None] = {}

    with StageTimer("load", total=len(wanted)):
        for fmt in wanted:
            try:
                if fmt == "sqlite":
                    results[fmt] = load_sqlite(settings, source)
                elif fmt == "duckdb":
                    results[fmt] = load_duckdb(settings, source)
                elif fmt == "postgis":
                    load_postgis(settings, source)
                    results[fmt] = None
            except RuntimeError as exc:  # missing optional dependency
                log.warning("load.{} skipped: {}", fmt, exc)
                results[fmt] = None
    return results
