"""Unit tests for the TRANSFORM stage — pure python, no shapely/polars needed.

Heavy pipeline dependencies (config/logging/Parquet engines) are deliberately
not imported: only the pure submodules are exercised.
"""

from __future__ import annotations

import pytest

from osm_india_etl.constants import OSMType, PlaceType
from osm_india_etl.models import LocationRecord
from osm_india_etl.transform.aliases import generate_aliases
from osm_india_etl.transform.dedupe import deduplicate
from osm_india_etl.transform.geometry import compute_geometry, haversine_km
from osm_india_etl.transform.hierarchy import build_hierarchy
from osm_india_etl.transform.normalize import normalize_record


def _record(
    osm_id: int,
    place_type: PlaceType,
    name: str,
    *,
    osm_type: OSMType = OSMType.NODE,
    lat: float | None = None,
    lng: float | None = None,
    **kwargs: object,
) -> LocationRecord:
    return LocationRecord(
        osm_id=osm_id,
        osm_type=osm_type,
        place_type=place_type,
        name=name,
        latitude=lat,
        longitude=lng,
        **kwargs,  # type: ignore[arg-type]
    )


# --------------------------------------------------------------------------- #
# normalize
# --------------------------------------------------------------------------- #
class TestNormalize:
    def test_basic_fields(self) -> None:
        rec = _record(1, PlaceType.CITY, "New Delhi", names={"name:hi": "नई दिल्ली"})
        normalize_record(rec)
        assert rec.name_en == "New Delhi"
        assert rec.name_title == "New Delhi"
        assert rec.name_lower == "new delhi"
        assert rec.name_ascii == "New Delhi"
        assert rec.search_name == "new delhi"
        assert rec.slug == "new-delhi"
        assert rec.name_native == "नई दिल्ली"

    def test_search_name_strips_punctuation_and_collapses_spaces(self) -> None:
        rec = _record(2, PlaceType.LOCALITY, "St. Thomas'   Mount")
        normalize_record(rec)
        assert rec.search_name == "st thomas mount"
        assert rec.slug == "st-thomas-mount"

    def test_prefers_explicit_name_en(self) -> None:
        rec = _record(3, PlaceType.CITY, "Bengaluru", names={"name:en": "Bengaluru City"})
        normalize_record(rec)
        assert rec.name_en == "Bengaluru City"


# --------------------------------------------------------------------------- #
# aliases
# --------------------------------------------------------------------------- #
class TestAliases:
    def test_builtin_synonym_bengaluru(self) -> None:
        rec = _record(10, PlaceType.CITY, "Bengaluru")
        normalize_record(rec)
        aliases = generate_aliases(rec)
        assert "Bangalore" in aliases
        # canonical name must be excluded
        assert "Bengaluru" not in aliases

    def test_alias_tags_and_dedupe(self) -> None:
        rec = _record(
            11,
            PlaceType.TOWN,
            "Puducherry",
            tags={"alt_name": "Pondy;Pondicherry", "old_name": "Pondicherry"},
        )
        normalize_record(rec)
        aliases = generate_aliases(rec)
        assert "Pondy" in aliases
        assert aliases.count("Pondicherry") == 1
        assert aliases == sorted(aliases)


# --------------------------------------------------------------------------- #
# geometry
# --------------------------------------------------------------------------- #
class TestGeometry:
    def test_haversine_delhi_mumbai(self) -> None:
        # New Delhi -> Mumbai is ~1150 km great-circle.
        dist = haversine_km(28.6139, 77.2090, 19.0760, 72.8777)
        assert dist == pytest.approx(1150, rel=0.03)

    def test_haversine_zero(self) -> None:
        assert haversine_km(12.97, 77.59, 12.97, 77.59) == pytest.approx(0.0, abs=1e-9)

    def test_point_wkt_sets_coords_and_bbox(self) -> None:
        rec = _record(20, PlaceType.VILLAGE, "Rampur", geometry_wkt="POINT(77.59 12.97)")
        compute_geometry(rec)
        assert rec.longitude == pytest.approx(77.59)
        assert rec.latitude == pytest.approx(12.97)
        assert rec.bbox == pytest.approx((77.59, 12.97, 77.59, 12.97))
        assert rec.area_sqkm == 0.0

    def test_polygon_wkt_area(self) -> None:
        # ~0.1 x 0.1 degree square near the equator-ish latitude 13N:
        # 11.132 km * 11.132 km * cos(13deg) ~= 120.7 km^2
        wkt = "POLYGON((77.0 13.0, 77.1 13.0, 77.1 13.1, 77.0 13.1, 77.0 13.0))"
        rec = _record(21, PlaceType.DISTRICT, "Test", osm_type=OSMType.RELATION, geometry_wkt=wkt)
        compute_geometry(rec)
        assert rec.area_sqkm == pytest.approx(120.7, rel=0.02)
        assert rec.latitude == pytest.approx(13.05, abs=0.01)
        assert rec.longitude == pytest.approx(77.05, abs=0.01)
        assert rec.bbox == pytest.approx((77.0, 13.0, 77.1, 13.1))


# --------------------------------------------------------------------------- #
# dedupe
# --------------------------------------------------------------------------- #
class TestDedupe:
    def test_merges_near_duplicates_and_unions_aliases(self) -> None:
        a = _record(
            30, PlaceType.VILLAGE, "Rampur", lat=26.5000, lng=80.3000, aliases=["Rampur Khurd"]
        )
        b = _record(
            31,
            PlaceType.VILLAGE,
            "Rampur",
            osm_type=OSMType.WAY,
            lat=26.5004,  # ~44 m north
            lng=80.3000,
            tags={"place": "village", "population": "1200"},
            aliases=["Rampur Kalan"],
        )
        far = _record(32, PlaceType.VILLAGE, "Rampur", lat=26.6000, lng=80.3000)  # ~11 km
        for rec in (a, b, far):
            normalize_record(rec)

        result = deduplicate([a, b, far], distance_m=150.0)
        assert len(result) == 2

        merged = next(r for r in result if r.latitude != far.latitude)
        # way preferred over node
        assert merged.osm_type is OSMType.WAY
        assert merged.osm_id == 31
        assert "Rampur Khurd" in merged.aliases
        assert "Rampur Kalan" in merged.aliases
        # the far same-named village survives untouched
        assert any(r.osm_id == 32 for r in result)

    def test_different_types_never_merge(self) -> None:
        a = _record(33, PlaceType.VILLAGE, "Alandur", lat=13.0, lng=80.2)
        b = _record(34, PlaceType.SUBURB, "Alandur", lat=13.0, lng=80.2)
        for rec in (a, b):
            normalize_record(rec)
        assert len(deduplicate([a, b], distance_m=150.0)) == 2

    def test_missing_coords_never_merge(self) -> None:
        a = _record(35, PlaceType.VILLAGE, "Rampur")
        b = _record(36, PlaceType.VILLAGE, "Rampur")
        for rec in (a, b):
            normalize_record(rec)
        assert len(deduplicate([a, b], distance_m=150.0)) == 2


# --------------------------------------------------------------------------- #
# hierarchy (proximity fallback path — no polygon geometry supplied)
# --------------------------------------------------------------------------- #
class TestHierarchyFallback:
    def test_village_links_through_district_to_state(self) -> None:
        state = _record(
            40, PlaceType.STATE, "Karnataka", osm_type=OSMType.RELATION, lat=14.5, lng=76.0
        )
        district = _record(
            41,
            PlaceType.DISTRICT,
            "Bengaluru Urban",
            osm_type=OSMType.RELATION,
            lat=12.97,
            lng=77.59,
        )
        village = _record(42, PlaceType.VILLAGE, "Whitefield", lat=12.9698, lng=77.7500)

        build_hierarchy([state, district, village])

        assert district.parent_id == state.location_id
        assert district.parent_type is PlaceType.STATE
        assert district.state_name == "Karnataka"

        assert village.parent_id == district.location_id
        assert village.parent_type is PlaceType.DISTRICT
        assert village.hierarchy == [state.location_id, district.location_id]
        assert village.state_name == "Karnataka"
        assert village.district_name == "Bengaluru Urban"

        # a state has no parent and denormalizes its own name
        assert state.parent_id is None
        assert state.state_name == "Karnataka"
