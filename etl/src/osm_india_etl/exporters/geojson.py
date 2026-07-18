"""GeoJSON exporter: stream location rows into a FeatureCollection.

Geometries are decoded from the ``geometry_wkt`` column via shapely when it is
installed. Without shapely, ``POINT(lon lat)`` WKT is parsed manually and any
other geometry falls back to a point built from latitude/longitude.
"""

from __future__ import annotations

import json
import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..logging_setup import log
from .tabular import iter_parquet_rows

try:  # optional heavy dependency
    from shapely import wkt as _shapely_wkt
    from shapely.geometry import mapping as _shapely_mapping

    _HAS_SHAPELY = True
except ImportError:  # pragma: no cover - depends on environment
    _HAS_SHAPELY = False

__all__ = ["to_geojson"]

# Columns that describe geometry and therefore do not belong in `properties`.
_GEOMETRY_COLUMNS = frozenset({"geometry_wkt", "latitude", "longitude", "bbox_json"})

_POINT_WKT_RE = re.compile(
    r"^\s*POINT\s*\(\s*(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s+"
    r"(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)\s*\)\s*$",
    re.IGNORECASE,
)


def _point(lon: float, lat: float) -> dict[str, Any]:
    return {"type": "Point", "coordinates": [lon, lat]}


def _geometry_for_row(row: dict[str, Any], simplify_tolerance: float) -> dict[str, Any] | None:
    """Build a GeoJSON geometry dict for one location row (or None)."""
    wkt_text = row.get("geometry_wkt")
    if wkt_text:
        if _HAS_SHAPELY:
            try:
                geom = _shapely_wkt.loads(wkt_text)
                if simplify_tolerance > 0 and geom.geom_type not in ("Point", "MultiPoint"):
                    geom = geom.simplify(simplify_tolerance, preserve_topology=True)
                return dict(_shapely_mapping(geom))
            except Exception as exc:  # malformed WKT: fall through to manual parse
                log.debug("shapely failed to parse WKT for {}: {}", row.get("location_id"), exc)
        match = _POINT_WKT_RE.match(wkt_text)
        if match:
            return _point(float(match.group(1)), float(match.group(2)))

    latitude, longitude = row.get("latitude"), row.get("longitude")
    if latitude is not None and longitude is not None:
        return _point(float(longitude), float(latitude))
    return None


def _features(
    src_parquet: Path, simplify_tolerance: float
) -> Iterator[dict[str, Any]]:
    for row in iter_parquet_rows(src_parquet):
        yield {
            "type": "Feature",
            "id": row.get("location_id"),
            "geometry": _geometry_for_row(row, simplify_tolerance),
            "properties": {k: v for k, v in row.items() if k not in _GEOMETRY_COLUMNS},
        }


def to_geojson(
    src_parquet: str | Path,
    dst: str | Path,
    simplify_tolerance: float = 0.0,
) -> Path:
    """Stream *src_parquet* rows into a standard GeoJSON FeatureCollection.

    Features are written one per line so the output stays memory-bounded even
    for country-scale datasets while remaining a valid single JSON document.

    Args:
        src_parquet: Canonical locations Parquet file (LOCATION_COLUMNS schema).
        dst: Destination ``.geojson`` path (parent dirs are created).
        simplify_tolerance: Douglas-Peucker tolerance in degrees; ``0`` disables
            simplification (only applied when shapely is available).

    Returns:
        The destination path.
    """
    src, dst = Path(src_parquet), Path(dst)
    dst.parent.mkdir(parents=True, exist_ok=True)

    count = 0
    with dst.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write('{"type": "FeatureCollection", "features": [\n')
        for feature in _features(src, simplify_tolerance):
            if count:
                fh.write(",\n")
            fh.write(json.dumps(feature, ensure_ascii=False, default=str))
            count += 1
        fh.write("\n]}\n")

    log.info("GeoJSON export: {} features -> {}", count, dst)
    return dst
