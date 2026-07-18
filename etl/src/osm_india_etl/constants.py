"""Static OSM knowledge: tag → entity mappings and India admin-level tables.

Kept dependency-free so every module (extract, transform, load, api) can
import it without pulling heavy libraries.
"""

from __future__ import annotations

from enum import Enum

# ---------------------------------------------------------------------------
# Entity taxonomy
# ---------------------------------------------------------------------------


class PlaceType(str, Enum):
    """Logical location entity types produced by the ETL."""

    COUNTRY = "country"
    STATE = "state"
    DIVISION = "division"
    DISTRICT = "district"
    SUBDISTRICT = "subdistrict"
    TALUK = "taluk"
    MANDAL = "mandal"
    TEHSIL = "tehsil"
    MUNICIPALITY = "municipality"
    CITY = "city"
    TOWN = "town"
    VILLAGE = "village"
    HAMLET = "hamlet"
    WARD = "ward"
    SUBURB = "suburb"
    LOCALITY = "locality"
    NEIGHBOURHOOD = "neighbourhood"
    COLONY = "colony"
    STREET = "street"
    ROAD = "road"
    HIGHWAY = "highway"
    BUILDING = "building"
    POSTAL_CODE = "postal_code"
    UNKNOWN = "unknown"


class OSMType(str, Enum):
    NODE = "node"
    WAY = "way"
    RELATION = "relation"


# ---------------------------------------------------------------------------
# India administrative levels (OSM `admin_level` on boundary=administrative)
# https://wiki.openstreetmap.org/wiki/Tag:boundary%3Dadministrative#India
# ---------------------------------------------------------------------------

ADMIN_LEVEL_TO_TYPE: dict[int, PlaceType] = {
    2: PlaceType.COUNTRY,
    3: PlaceType.STATE,     # some union-territory groupings
    4: PlaceType.STATE,
    5: PlaceType.DIVISION,
    6: PlaceType.DISTRICT,
    7: PlaceType.SUBDISTRICT,   # taluk / tehsil / mandal / sub-district
    8: PlaceType.MUNICIPALITY,  # city / municipality
    9: PlaceType.WARD,
    10: PlaceType.NEIGHBOURHOOD,
}

# Rank used to build the parent→child hierarchy (lower = higher in tree).
TYPE_RANK: dict[PlaceType, int] = {
    PlaceType.COUNTRY: 0,
    PlaceType.STATE: 1,
    PlaceType.DIVISION: 2,
    PlaceType.DISTRICT: 3,
    PlaceType.SUBDISTRICT: 4,
    PlaceType.TALUK: 4,
    PlaceType.MANDAL: 4,
    PlaceType.TEHSIL: 4,
    PlaceType.MUNICIPALITY: 5,
    PlaceType.CITY: 5,
    PlaceType.TOWN: 6,
    PlaceType.VILLAGE: 7,
    PlaceType.SUBURB: 8,
    PlaceType.WARD: 8,
    PlaceType.HAMLET: 9,
    PlaceType.LOCALITY: 9,
    PlaceType.NEIGHBOURHOOD: 10,
    PlaceType.COLONY: 10,
    PlaceType.STREET: 11,
    PlaceType.ROAD: 11,
    PlaceType.HIGHWAY: 11,
    PlaceType.BUILDING: 12,
    PlaceType.POSTAL_CODE: 99,
    PlaceType.UNKNOWN: 100,
}

# ---------------------------------------------------------------------------
# place=* tag → PlaceType
# ---------------------------------------------------------------------------

PLACE_TAG_TO_TYPE: dict[str, PlaceType] = {
    "country": PlaceType.COUNTRY,
    "state": PlaceType.STATE,
    "region": PlaceType.DIVISION,
    "province": PlaceType.STATE,
    "district": PlaceType.DISTRICT,
    "county": PlaceType.DISTRICT,
    "municipality": PlaceType.MUNICIPALITY,
    "city": PlaceType.CITY,
    "town": PlaceType.TOWN,
    "village": PlaceType.VILLAGE,
    "hamlet": PlaceType.HAMLET,
    "suburb": PlaceType.SUBURB,
    "quarter": PlaceType.NEIGHBOURHOOD,
    "neighbourhood": PlaceType.NEIGHBOURHOOD,
    "borough": PlaceType.WARD,
    "locality": PlaceType.LOCALITY,
    "isolated_dwelling": PlaceType.HAMLET,
    "allotments": PlaceType.COLONY,
}

# ---------------------------------------------------------------------------
# highway=* classification → PlaceType (streets vs roads vs highways)
# ---------------------------------------------------------------------------

HIGHWAY_MAJOR = {"motorway", "trunk", "primary", "motorway_link", "trunk_link", "primary_link"}
HIGHWAY_ROAD = {"secondary", "tertiary", "secondary_link", "tertiary_link", "unclassified", "road"}
HIGHWAY_STREET = {"residential", "living_street", "service", "pedestrian", "track", "footway"}


def classify_highway(value: str) -> PlaceType:
    if value in HIGHWAY_MAJOR:
        return PlaceType.HIGHWAY
    if value in HIGHWAY_ROAD:
        return PlaceType.ROAD
    if value in HIGHWAY_STREET:
        return PlaceType.STREET
    return PlaceType.ROAD


# Tags carrying a postal code.
POSTCODE_KEYS = ("addr:postcode", "postal_code", "postcode")

# Native / regional name tag keys worth capturing (India languages).
NAME_TAG_KEYS = (
    "name",
    "name:en",
    "name:hi",
    "name:kn",
    "name:ta",
    "name:te",
    "name:ml",
    "name:mr",
    "name:bn",
    "name:gu",
    "name:pa",
    "name:or",
    "name:as",
    "name:ur",
    "int_name",
    "official_name",
    "alt_name",
    "old_name",
    "loc_name",
    "short_name",
)

# Keys treated as alias sources during alias generation.
ALIAS_TAG_KEYS = ("alt_name", "old_name", "loc_name", "short_name", "official_name", "int_name")

# ---------------------------------------------------------------------------
# Output schema — canonical column order for Parquet / CSV / DB.
# Every producer (extract, transform) and consumer (load, export, api) uses this.
# ---------------------------------------------------------------------------

LOCATION_COLUMNS: tuple[str, ...] = (
    "location_id",        # deterministic id: f"{osm_type[0]}{osm_id}"
    "osm_id",
    "osm_type",           # node | way | relation
    "place_type",         # PlaceType value
    "admin_level",        # int | None
    "name",               # primary display name
    "name_en",
    "name_native",        # best native-script name
    "name_title",
    "name_lower",
    "name_ascii",
    "search_name",        # normalized, for FTS/trigram
    "slug",
    "names_json",         # all name:* tags as JSON
    "aliases_json",       # list[str] as JSON
    "pincode",
    "latitude",
    "longitude",
    "geometry_wkt",       # WKT (POINT/POLYGON/LINESTRING)
    "bbox_json",          # [minx, miny, maxx, maxy]
    "area_sqkm",          # polygon area (0 for points/lines)
    "parent_id",          # location_id of parent, or None
    "parent_type",        # PlaceType of parent, or None
    "hierarchy_json",     # ordered list of ancestor location_ids
    "state_name",         # denormalized ancestor for fast filtering
    "district_name",
    "tags_json",          # raw OSM tags as JSON
    "source_file",        # originating .osm.pbf
)

# ---------------------------------------------------------------------------
# Target relational tables (one bucket per tier + shared/auxiliary tables).
# The loader materializes these from the unified location records.
# ---------------------------------------------------------------------------

ENTITY_TABLES: tuple[str, ...] = (
    "states",
    "districts",
    "subdistricts",
    "mandals",
    "taluks",
    "villages",
    "towns",
    "cities",
    "wards",
    "localities",
    "neighbourhoods",
    "streets",
    "roads",
    "highways",
    "buildings",
    "postal_codes",
)

AUX_TABLES: tuple[str, ...] = ("locations", "geometry", "aliases")

# Which PlaceTypes land in which table bucket.
TYPE_TO_TABLE: dict[PlaceType, str] = {
    PlaceType.STATE: "states",
    PlaceType.DIVISION: "states",
    PlaceType.DISTRICT: "districts",
    PlaceType.SUBDISTRICT: "subdistricts",
    PlaceType.MANDAL: "mandals",
    PlaceType.TALUK: "taluks",
    PlaceType.TEHSIL: "subdistricts",
    PlaceType.VILLAGE: "villages",
    PlaceType.TOWN: "towns",
    PlaceType.CITY: "cities",
    PlaceType.MUNICIPALITY: "cities",
    PlaceType.WARD: "wards",
    PlaceType.LOCALITY: "localities",
    PlaceType.SUBURB: "neighbourhoods",
    PlaceType.NEIGHBOURHOOD: "neighbourhoods",
    PlaceType.HAMLET: "villages",
    PlaceType.COLONY: "localities",
    PlaceType.STREET: "streets",
    PlaceType.ROAD: "roads",
    PlaceType.HIGHWAY: "highways",
    PlaceType.BUILDING: "buildings",
    PlaceType.POSTAL_CODE: "postal_codes",
}

INDIA_BBOX = (68.0, 6.0, 98.0, 38.0)  # (minlon, minlat, maxlon, maxlat)
