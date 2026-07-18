"""Tests for the SQLite LOAD path.

Uses only the standard-library ``sqlite3`` module: records are fed to
``load_sqlite`` directly (bypassing Parquet) so the test runs without
pyarrow/polars/duckdb/postgres installed.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from osm_india_etl.config import Settings
from osm_india_etl.constants import OSMType, PlaceType
from osm_india_etl.load import load_sqlite
from osm_india_etl.models import LocationRecord


def _records() -> list[LocationRecord]:
    """A tiny state -> district -> {city, village} hierarchy."""
    state = LocationRecord(
        osm_id=100,
        osm_type=OSMType.RELATION,
        place_type=PlaceType.STATE,
        admin_level=4,
        name="Telangana",
        search_name="telangana",
        latitude=17.8,
        longitude=79.1,
        geometry_wkt="POINT(79.1 17.8)",
    )
    district = LocationRecord(
        osm_id=200,
        osm_type=OSMType.RELATION,
        place_type=PlaceType.DISTRICT,
        admin_level=6,
        name="Hyderabad District",
        search_name="hyderabad district",
        latitude=17.4,
        longitude=78.5,
        geometry_wkt="POINT(78.5 17.4)",
        parent_id=state.location_id,
        parent_type=PlaceType.STATE,
        state_name="Telangana",
    )
    city = LocationRecord(
        osm_id=300,
        osm_type=OSMType.NODE,
        place_type=PlaceType.CITY,
        name="Hyderabad",
        search_name="hyderabad",
        aliases=["Bhagyanagar", "Cyberabad"],
        pincode="500001",
        latitude=17.385,
        longitude=78.4867,
        geometry_wkt="POINT(78.4867 17.385)",
        parent_id=district.location_id,
        parent_type=PlaceType.DISTRICT,
        state_name="Telangana",
        district_name="Hyderabad District",
    )
    village = LocationRecord(
        osm_id=400,
        osm_type=OSMType.NODE,
        place_type=PlaceType.VILLAGE,
        name="Shamirpet",
        search_name="shamirpet",
        pincode="500078",
        latitude=17.6,
        longitude=78.57,
        geometry_wkt="POINT(78.57 17.6)",
        parent_id=district.location_id,
        parent_type=PlaceType.DISTRICT,
        state_name="Telangana",
        district_name="Hyderabad District",
    )
    return [state, district, city, village]


@pytest.fixture()
def settings(tmp_path: Path) -> Settings:
    """Settings rooted in a temp dir so the sqlite db lands in tmp_path."""
    return Settings(root=tmp_path)


def _count(conn: sqlite3.Connection, table: str) -> int:
    return conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]


def test_load_sqlite_row_counts(settings: Settings) -> None:
    db_path = load_sqlite(settings, records=_records())
    assert db_path.exists()

    conn = sqlite3.connect(db_path)
    try:
        assert _count(conn, "locations") == 4
        assert _count(conn, "states") == 1
        assert _count(conn, "districts") == 1
        assert _count(conn, "cities") == 1
        assert _count(conn, "villages") == 1
        assert _count(conn, "towns") == 0
        # Aux tables: 2 aliases for Hyderabad; geometry row for every record.
        assert _count(conn, "aliases") == 2
        assert _count(conn, "geometry") == 4
    finally:
        conn.close()


def test_load_sqlite_bucket_projection(settings: Settings) -> None:
    db_path = load_sqlite(settings, records=_records())
    conn = sqlite3.connect(db_path)
    try:
        row = conn.execute(
            "SELECT location_id, osm_id, name, pincode, parent_id FROM cities"
        ).fetchone()
        assert row == ("n300", 300, "Hyderabad", "500001", "r200")
        # Unified table carries the denormalized ancestry.
        state_name, district_name = conn.execute(
            "SELECT state_name, district_name FROM locations WHERE location_id = 'n300'"
        ).fetchone()
        assert (state_name, district_name) == ("Telangana", "Hyderabad District")
    finally:
        conn.close()


def test_fts_match_returns_seeded_city(settings: Settings) -> None:
    db_path = load_sqlite(settings, records=_records())
    conn = sqlite3.connect(db_path)
    try:
        names = {
            r[0]
            for r in conn.execute(
                "SELECT l.name FROM locations_fts f "
                "JOIN locations l ON l.rowid = f.rowid "
                "WHERE locations_fts MATCH 'hyderabad'"
            )
        }
        assert "Hyderabad" in names

        # Alias text is indexed too: the historical name finds the city.
        alias_hits = conn.execute(
            "SELECT l.name FROM locations_fts f "
            "JOIN locations l ON l.rowid = f.rowid "
            "WHERE locations_fts MATCH 'bhagyanagar'"
        ).fetchall()
        assert alias_hits == [("Hyderabad",)]
    finally:
        conn.close()
