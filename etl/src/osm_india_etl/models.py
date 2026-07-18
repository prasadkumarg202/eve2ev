"""Core in-memory data contract shared across the whole pipeline.

`LocationRecord` is the single source of truth for a location entity as it
flows extract → transform → load/export. It serializes to the columnar schema
declared in :data:`osm_india_etl.constants.LOCATION_COLUMNS`.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from .constants import LOCATION_COLUMNS, OSMType, PlaceType


def make_location_id(osm_type: OSMType | str, osm_id: int) -> str:
    """Deterministic, collision-free id, e.g. ``n123``, ``w456``, ``r789``."""
    t = osm_type.value if isinstance(osm_type, OSMType) else str(osm_type)
    return f"{t[0]}{osm_id}"


@dataclass(slots=True)
class LocationRecord:
    """A single normalized location entity."""

    osm_id: int
    osm_type: OSMType
    place_type: PlaceType = PlaceType.UNKNOWN
    admin_level: int | None = None

    name: str = ""
    name_en: str = ""
    name_native: str = ""
    name_title: str = ""
    name_lower: str = ""
    name_ascii: str = ""
    search_name: str = ""
    slug: str = ""

    names: dict[str, str] = field(default_factory=dict)   # all name:* tags
    aliases: list[str] = field(default_factory=list)

    pincode: str | None = None
    latitude: float | None = None
    longitude: float | None = None

    geometry_wkt: str | None = None
    bbox: tuple[float, float, float, float] | None = None
    area_sqkm: float = 0.0

    parent_id: str | None = None
    parent_type: PlaceType | None = None
    hierarchy: list[str] = field(default_factory=list)     # ancestor location_ids
    state_name: str | None = None
    district_name: str | None = None

    tags: dict[str, str] = field(default_factory=dict)
    source_file: str = ""

    # ---- derived ----
    @property
    def location_id(self) -> str:
        return make_location_id(self.osm_type, self.osm_id)

    @property
    def rank(self) -> int:
        from .constants import TYPE_RANK

        return TYPE_RANK.get(self.place_type, 100)

    # ---- serialization ----
    def to_row(self) -> dict[str, Any]:
        """Flatten to the canonical columnar schema (JSON for nested fields)."""
        return {
            "location_id": self.location_id,
            "osm_id": self.osm_id,
            "osm_type": self.osm_type.value,
            "place_type": self.place_type.value,
            "admin_level": self.admin_level,
            "name": self.name,
            "name_en": self.name_en,
            "name_native": self.name_native,
            "name_title": self.name_title,
            "name_lower": self.name_lower,
            "name_ascii": self.name_ascii,
            "search_name": self.search_name,
            "slug": self.slug,
            "names_json": json.dumps(self.names, ensure_ascii=False),
            "aliases_json": json.dumps(self.aliases, ensure_ascii=False),
            "pincode": self.pincode,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "geometry_wkt": self.geometry_wkt,
            "bbox_json": json.dumps(list(self.bbox)) if self.bbox else None,
            "area_sqkm": self.area_sqkm,
            "parent_id": self.parent_id,
            "parent_type": self.parent_type.value if self.parent_type else None,
            "hierarchy_json": json.dumps(self.hierarchy),
            "state_name": self.state_name,
            "district_name": self.district_name,
            "tags_json": json.dumps(self.tags, ensure_ascii=False),
            "source_file": self.source_file,
        }

    @classmethod
    def from_row(cls, row: dict[str, Any]) -> LocationRecord:
        """Rebuild from a columnar row (inverse of :meth:`to_row`)."""

        def jload(val: Any, default: Any) -> Any:
            if val is None or val == "":
                return default
            if isinstance(val, (dict, list)):
                return val
            try:
                return json.loads(val)
            except (json.JSONDecodeError, TypeError):
                return default

        bbox = jload(row.get("bbox_json"), None)
        parent_type = row.get("parent_type")
        return cls(
            osm_id=int(row["osm_id"]),
            osm_type=OSMType(row["osm_type"]),
            place_type=PlaceType(row.get("place_type", "unknown")),
            admin_level=row.get("admin_level"),
            name=row.get("name", "") or "",
            name_en=row.get("name_en", "") or "",
            name_native=row.get("name_native", "") or "",
            name_title=row.get("name_title", "") or "",
            name_lower=row.get("name_lower", "") or "",
            name_ascii=row.get("name_ascii", "") or "",
            search_name=row.get("search_name", "") or "",
            slug=row.get("slug", "") or "",
            names=jload(row.get("names_json"), {}),
            aliases=jload(row.get("aliases_json"), []),
            pincode=row.get("pincode"),
            latitude=row.get("latitude"),
            longitude=row.get("longitude"),
            geometry_wkt=row.get("geometry_wkt"),
            bbox=tuple(bbox) if bbox else None,  # type: ignore[arg-type]
            area_sqkm=float(row.get("area_sqkm") or 0.0),
            parent_id=row.get("parent_id"),
            parent_type=PlaceType(parent_type) if parent_type else None,
            hierarchy=jload(row.get("hierarchy_json"), []),
            state_name=row.get("state_name"),
            district_name=row.get("district_name"),
            tags=jload(row.get("tags_json"), {}),
            source_file=row.get("source_file", "") or "",
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(self)


# Sanity check kept close to the schema so drift is caught immediately in tests.
_EXPECTED = set(LOCATION_COLUMNS)


def validate_schema() -> None:
    produced = set(LocationRecord(osm_id=1, osm_type=OSMType.NODE).to_row().keys())
    missing = _EXPECTED - produced
    extra = produced - _EXPECTED
    if missing or extra:  # pragma: no cover - defensive
        raise RuntimeError(f"LocationRecord schema drift. missing={missing} extra={extra}")


@dataclass(slots=True)
class DownloadItem:
    """A discovered downloadable OSM extract."""

    filename: str
    url: str
    size: int | None = None
    md5_url: str | None = None
    md5: str | None = None

    @property
    def zone(self) -> str:
        return self.filename.replace(".osm.pbf", "")


@dataclass(slots=True)
class Checkpoint:
    """Pipeline recovery state, persisted as JSON after each stage/file."""

    stage: str = "init"
    completed_files: list[str] = field(default_factory=list)
    completed_stages: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    def to_json(self) -> str:
        return json.dumps(asdict(self), indent=2)

    @classmethod
    def from_json(cls, text: str) -> Checkpoint:
        data = json.loads(text)
        return cls(**data)
