"""Unit tests for the pure tag-mapping helpers in ``osm_india_etl.extract``.

These tests need no ``.pbf`` fixtures and no osmium/pyarrow runtime — the
heavy imports in ``extract.py`` are guarded, so ``tags_to_record`` and
friends import cleanly on their own.
"""

from __future__ import annotations

from osm_india_etl.config import Settings
from osm_india_etl.constants import LOCATION_COLUMNS, OSMType, PlaceType
from osm_india_etl.extract import in_india_bbox, tags_to_record


def make_settings(**extract_overrides: object) -> Settings:
    """Build default Settings (no config file / no dir creation) with
    optional ``extract`` section overrides."""
    settings = Settings()
    for key, value in extract_overrides.items():
        setattr(settings.extract, key, value)
    return settings


# --------------------------------------------------------------------------- #
# Admin boundaries
# --------------------------------------------------------------------------- #
def test_admin_boundary_level_4_is_state() -> None:
    tags = {
        "boundary": "administrative",
        "admin_level": "4",
        "name": "Karnataka",
        "name:kn": "ಕರ್ನಾಟಕ",
    }
    rec = tags_to_record(OSMType.RELATION, 304776, tags, make_settings())
    assert rec is not None
    assert rec.place_type is PlaceType.STATE
    assert rec.admin_level == 4
    assert rec.name == "Karnataka"
    assert rec.names["name:kn"] == "ಕರ್ನಾಟಕ"
    assert rec.tags["boundary"] == "administrative"
    assert rec.location_id == "r304776"


def test_admin_boundary_level_6_is_district() -> None:
    tags = {"boundary": "administrative", "admin_level": "6", "name": "Mysuru"}
    rec = tags_to_record(OSMType.RELATION, 42, tags, make_settings())
    assert rec is not None
    assert rec.place_type is PlaceType.DISTRICT
    assert rec.admin_level == 6


def test_admin_extraction_respects_flag() -> None:
    tags = {"boundary": "administrative", "admin_level": "4", "name": "Kerala"}
    rec = tags_to_record(OSMType.RELATION, 7, tags, make_settings(extract_admin=False))
    assert rec is None


# --------------------------------------------------------------------------- #
# place=*
# --------------------------------------------------------------------------- #
def test_place_city_maps_to_city() -> None:
    tags = {"place": "city", "name": "Bengaluru", "name:en": "Bengaluru"}
    rec = tags_to_record(OSMType.NODE, 17027465, tags, make_settings())
    assert rec is not None
    assert rec.place_type is PlaceType.CITY
    assert rec.name == "Bengaluru"
    assert rec.name_en == "Bengaluru"


def test_place_village_maps_to_village() -> None:
    rec = tags_to_record(
        OSMType.NODE, 5, {"place": "village", "name": "Melukote"}, make_settings()
    )
    assert rec is not None
    assert rec.place_type is PlaceType.VILLAGE


# --------------------------------------------------------------------------- #
# highway=*
# --------------------------------------------------------------------------- #
def test_highway_residential_way_is_street() -> None:
    tags = {"highway": "residential", "name": "MG Road"}
    rec = tags_to_record(OSMType.WAY, 1234, tags, make_settings())
    assert rec is not None
    assert rec.place_type is PlaceType.STREET
    assert rec.name == "MG Road"


def test_highway_primary_way_is_highway() -> None:
    rec = tags_to_record(OSMType.WAY, 9, {"highway": "primary"}, make_settings())
    assert rec is not None
    assert rec.place_type is PlaceType.HIGHWAY


def test_highway_on_node_is_ignored() -> None:
    """highway extraction only applies to ways (nodes carry crossings etc.)."""
    rec = tags_to_record(OSMType.NODE, 9, {"highway": "residential"}, make_settings())
    assert rec is None


# --------------------------------------------------------------------------- #
# Postcodes
# --------------------------------------------------------------------------- #
def test_postcode_only_node_becomes_postal_code_record() -> None:
    rec = tags_to_record(OSMType.NODE, 88, {"addr:postcode": "560001"}, make_settings())
    assert rec is not None
    assert rec.place_type is PlaceType.POSTAL_CODE
    assert rec.pincode == "560001"
    assert rec.name == "560001"


def test_postcode_is_attached_to_place_records() -> None:
    tags = {"place": "suburb", "name": "Indiranagar", "addr:postcode": "560038"}
    rec = tags_to_record(OSMType.NODE, 3, tags, make_settings())
    assert rec is not None
    assert rec.place_type is PlaceType.SUBURB
    assert rec.pincode == "560038"


def test_postcode_only_node_dropped_when_disabled() -> None:
    rec = tags_to_record(
        OSMType.NODE, 88, {"postal_code": "560001"}, make_settings(extract_postcodes=False)
    )
    assert rec is None


# --------------------------------------------------------------------------- #
# Buildings
# --------------------------------------------------------------------------- #
def test_building_skipped_by_default() -> None:
    rec = tags_to_record(OSMType.WAY, 11, {"building": "yes"}, make_settings())
    assert rec is None


def test_building_extracted_when_enabled() -> None:
    rec = tags_to_record(
        OSMType.WAY, 11, {"building": "yes", "name": "Vidhana Soudha"},
        make_settings(extract_buildings=True),
    )
    assert rec is not None
    assert rec.place_type is PlaceType.BUILDING


# --------------------------------------------------------------------------- #
# Negatives / schema / bbox guard
# --------------------------------------------------------------------------- #
def test_irrelevant_tags_return_none() -> None:
    tags = {"amenity": "cafe", "cuisine": "coffee_shop", "natural": "tree"}
    assert tags_to_record(OSMType.NODE, 1, tags, make_settings()) is None
    assert tags_to_record(OSMType.NODE, 2, {}, make_settings()) is None


def test_record_row_matches_location_columns() -> None:
    rec = tags_to_record(OSMType.NODE, 5, {"place": "town", "name": "Hassan"}, make_settings())
    assert rec is not None
    assert tuple(rec.to_row().keys()) == LOCATION_COLUMNS


def test_india_bbox_guard() -> None:
    assert in_india_bbox(77.59, 12.97)          # Bengaluru
    assert not in_india_bbox(-0.12, 51.5)       # London
    assert not in_india_bbox(77.59, 55.0)       # latitude out of range
