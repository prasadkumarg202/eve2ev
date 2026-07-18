"""Geometry enrichment: centroid, bounding box and area for LocationRecords.

Uses Shapely when available. Without Shapely a small pure-python WKT reader
handles the common cases produced by the extract stage (``POINT``,
``LINESTRING`` and single-ring ``POLYGON``), so the module stays usable in a
minimal environment.

Area is an equal-area *approximation*: the polygon area in squared degrees is
scaled by ``(111.32 km)^2 * cos(latitude)`` — one degree of latitude is
~111.32 km everywhere, while one degree of longitude shrinks with
``cos(latitude)``. Within India's latitude band (6°–38° N) the error of this
local approximation is small and perfectly adequate for ranking/filtering.
"""

from __future__ import annotations

import math
import re

from osm_india_etl.models import LocationRecord

try:  # pragma: no cover - trivial import guard
    from shapely import wkt as _shapely_wkt
    from shapely.errors import ShapelyError as _ShapelyError

    HAS_SHAPELY = True
except ImportError:  # pragma: no cover
    HAS_SHAPELY = False
    _shapely_wkt = None
    _ShapelyError = Exception

#: Kilometres per degree of latitude (mean Earth radius).
KM_PER_DEG = 111.32

_EARTH_RADIUS_KM = 6371.0088

_RING_RE = re.compile(r"\(([^()]+)\)")
_NUM_RE = re.compile(r"[-+]?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two WGS84 points, in kilometres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _deg2_to_sqkm(area_deg2: float, latitude: float) -> float:
    """Convert an area in squared degrees to km² at the given latitude."""
    return abs(area_deg2) * KM_PER_DEG * KM_PER_DEG * math.cos(math.radians(latitude))


# --------------------------------------------------------------------------- #
# Pure-python WKT fallback
# --------------------------------------------------------------------------- #
def _parse_coord_ring(ring_text: str) -> list[tuple[float, float]]:
    """Parse ``"lon lat, lon lat, ..."`` into (lon, lat) tuples."""
    numbers = [float(m.group()) for m in _NUM_RE.finditer(ring_text)]
    return [(numbers[i], numbers[i + 1]) for i in range(0, len(numbers) - 1, 2)]


def _shoelace(ring: list[tuple[float, float]]) -> tuple[float, float, float]:
    """Signed shoelace area (deg²) and centroid of a closed ring."""
    area2 = 0.0
    cx = cy = 0.0
    n = len(ring)
    for i in range(n):
        x1, y1 = ring[i]
        x2, y2 = ring[(i + 1) % n]
        cross = x1 * y2 - x2 * y1
        area2 += cross
        cx += (x1 + x2) * cross
        cy += (y1 + y2) * cross
    if abs(area2) < 1e-12:  # degenerate ring: fall back to vertex mean
        mx = sum(p[0] for p in ring) / n
        my = sum(p[1] for p in ring) / n
        return 0.0, mx, my
    area = area2 / 2.0
    return area, cx / (6.0 * area), cy / (6.0 * area)


def _fallback_geometry(rec: LocationRecord, wkt_text: str) -> None:
    """Handle POINT / LINESTRING / single-ring POLYGON without Shapely."""
    head = wkt_text.lstrip().upper()
    rings = _RING_RE.findall(wkt_text)
    if not rings:
        return
    coords = _parse_coord_ring(rings[0])  # exterior ring / point / line
    if not coords:
        return

    xs = [c[0] for c in coords]
    ys = [c[1] for c in coords]
    rec.bbox = (min(xs), min(ys), max(xs), max(ys))

    if head.startswith("POINT"):
        cx, cy = coords[0]
        rec.area_sqkm = 0.0
    elif head.startswith("POLYGON"):
        area_deg2, cx, cy = _shoelace(coords)
        rec.area_sqkm = round(_deg2_to_sqkm(area_deg2, cy), 6)
    else:  # LINESTRING / MULTI* best-effort: vertex mean, no area
        cx = sum(xs) / len(xs)
        cy = sum(ys) / len(ys)
        rec.area_sqkm = 0.0

    if rec.latitude is None or rec.longitude is None:
        rec.latitude = cy
        rec.longitude = cx


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def compute_geometry(rec: LocationRecord) -> None:
    """Derive ``latitude``/``longitude`` (if missing), ``bbox`` and
    ``area_sqkm`` from ``rec.geometry_wkt`` in place.

    Records without a WKT geometry but with coordinates get a degenerate
    point bbox; anything unparseable is left untouched.
    """
    wkt_text = rec.geometry_wkt
    if not wkt_text:
        if rec.latitude is not None and rec.longitude is not None:
            rec.bbox = (rec.longitude, rec.latitude, rec.longitude, rec.latitude)
            rec.area_sqkm = rec.area_sqkm or 0.0
        return

    if not HAS_SHAPELY:
        _fallback_geometry(rec, wkt_text)
        return

    try:
        geom = _shapely_wkt.loads(wkt_text)
    except (_ShapelyError, ValueError, TypeError):
        _fallback_geometry(rec, wkt_text)
        return
    if geom.is_empty:
        return

    centroid = geom.centroid
    if rec.latitude is None or rec.longitude is None:
        rec.latitude = centroid.y
        rec.longitude = centroid.x

    rec.bbox = tuple(geom.bounds)  # type: ignore[assignment]

    if geom.geom_type in ("Polygon", "MultiPolygon"):
        rec.area_sqkm = round(_deg2_to_sqkm(geom.area, centroid.y), 6)
    else:
        rec.area_sqkm = 0.0
