"""Administrative hierarchy construction.

Assigns ``parent_id`` / ``parent_type`` / ``hierarchy`` (ordered ancestor
location_ids, root first) plus the denormalized ``state_name`` and
``district_name`` columns.

Strategy
--------
Records are processed in :data:`~osm_india_etl.constants.TYPE_RANK` order
(country → state → ... → building) so every candidate parent is fully linked
before its children are resolved. For each record the parent is:

1. **Containment** (preferred, requires Shapely): the smallest-area admin
   polygon of a strictly higher tier that contains the record's centroid,
   found via an ``STRtree`` spatial index.
2. **Proximity fallback** (pure python, also used when Shapely or polygon
   geometry is unavailable): the nearest higher-tier record by haversine
   centroid distance, preferring the deepest tier available (a village
   attaches to the nearest sub-district before the nearest state).
"""

from __future__ import annotations

from collections import defaultdict

from osm_india_etl.constants import PlaceType
from osm_india_etl.models import LocationRecord

from .geometry import haversine_km

try:  # pragma: no cover - trivial import guard
    from shapely import wkt as _shapely_wkt
    from shapely.errors import ShapelyError as _ShapelyError
    from shapely.geometry import Point as _Point
    from shapely.strtree import STRtree as _STRtree

    HAS_SHAPELY = True
except ImportError:  # pragma: no cover
    HAS_SHAPELY = False

# Tiers eligible to act as containment parents (admin-style areas).
_PARENT_TYPES = {
    PlaceType.COUNTRY,
    PlaceType.STATE,
    PlaceType.DIVISION,
    PlaceType.DISTRICT,
    PlaceType.SUBDISTRICT,
    PlaceType.TALUK,
    PlaceType.MANDAL,
    PlaceType.TEHSIL,
    PlaceType.MUNICIPALITY,
    PlaceType.CITY,
    PlaceType.TOWN,
    PlaceType.VILLAGE,
    PlaceType.WARD,
    PlaceType.SUBURB,
    PlaceType.NEIGHBOURHOOD,
}


class _ContainmentIndex:
    """STRtree over parent-candidate polygons (only built when Shapely exists)."""

    def __init__(self, records: list[LocationRecord]) -> None:
        self._records: list[LocationRecord] = []
        self._areas: list[float] = []
        geometries = []
        for rec in records:
            if rec.place_type not in _PARENT_TYPES or not rec.geometry_wkt:
                continue
            try:
                geom = _shapely_wkt.loads(rec.geometry_wkt)
            except (_ShapelyError, ValueError, TypeError):
                continue
            if geom.geom_type not in ("Polygon", "MultiPolygon") or geom.is_empty:
                continue
            geometries.append(geom)
            self._records.append(rec)
            self._areas.append(rec.area_sqkm or geom.area)
        self._tree = _STRtree(geometries) if geometries else None

    def __bool__(self) -> bool:
        return self._tree is not None

    def find_parent(self, rec: LocationRecord) -> LocationRecord | None:
        """Smallest containing polygon of a strictly higher tier, or None."""
        if self._tree is None or rec.latitude is None or rec.longitude is None:
            return None
        point = _Point(rec.longitude, rec.latitude)
        best: LocationRecord | None = None
        best_area = float("inf")
        for idx in self._tree.query(point, predicate="within"):
            candidate = self._records[int(idx)]
            if candidate is rec or candidate.rank >= rec.rank:
                continue
            area = self._areas[int(idx)]
            if area < best_area:
                best, best_area = candidate, area
        return best


class _ProximityIndex:
    """Nearest-higher-tier fallback based on haversine centroid distance."""

    def __init__(self, records: list[LocationRecord]) -> None:
        self._by_rank: dict[int, list[LocationRecord]] = defaultdict(list)
        for rec in records:
            if (
                rec.place_type in _PARENT_TYPES
                and rec.latitude is not None
                and rec.longitude is not None
            ):
                self._by_rank[rec.rank].append(rec)
        self._ranks = sorted(self._by_rank, reverse=True)  # deepest tier first

    def find_parent(self, rec: LocationRecord) -> LocationRecord | None:
        if rec.latitude is None or rec.longitude is None:
            return None
        for rank in self._ranks:
            if rank >= rec.rank:
                continue
            best: LocationRecord | None = None
            best_km = float("inf")
            for candidate in self._by_rank[rank]:
                if candidate is rec:
                    continue
                km = haversine_km(
                    rec.latitude, rec.longitude, candidate.latitude, candidate.longitude
                )
                if km < best_km:
                    best, best_km = candidate, km
            if best is not None:
                return best
        return None


def _display_name(rec: LocationRecord) -> str:
    return rec.name_en or rec.name


def is_parent_candidate(rec: LocationRecord) -> bool:
    """Can this record ever act as somebody's administrative parent?

    Only admin-style areas can. Streets, roads, buildings and postcodes —
    ~98% of a typical extract — never can, which is what lets the transform
    stage stream: the resolver only has to hold this subset in memory.
    """
    return rec.place_type in _PARENT_TYPES


class HierarchyResolver:
    """Reusable parent resolver built over a fixed set of parent candidates.

    Built once from the (small) set of admin areas, it can then attach
    ancestry to an unbounded stream of child records without holding them.
    """

    def __init__(self, parents: list[LocationRecord]) -> None:
        self._containment = _ContainmentIndex(parents) if HAS_SHAPELY else None
        self._proximity = _ProximityIndex(parents)
        self._by_id: dict[str, LocationRecord] = {p.location_id: p for p in parents}

    def attach(self, rec: LocationRecord) -> None:
        """Set parent_id / hierarchy / state_name / district_name in place."""
        parent: LocationRecord | None = None
        if self._containment:
            parent = self._containment.find_parent(rec)
        if parent is None:
            parent = self._proximity.find_parent(rec)

        if parent is not None and parent.location_id != rec.location_id:
            rec.parent_id = parent.location_id
            rec.parent_type = parent.place_type
            rec.hierarchy = [*parent.hierarchy, parent.location_id]

        # Denormalized ancestor names (self counts for its own tier).
        state = _display_name(rec) if rec.place_type is PlaceType.STATE else None
        district = _display_name(rec) if rec.place_type is PlaceType.DISTRICT else None
        for ancestor_id in reversed(rec.hierarchy):
            ancestor = self._by_id.get(ancestor_id)
            if ancestor is None:
                continue
            if state is None and ancestor.place_type is PlaceType.STATE:
                state = _display_name(ancestor)
            if district is None and ancestor.place_type is PlaceType.DISTRICT:
                district = _display_name(ancestor)
        rec.state_name = state
        rec.district_name = district


def build_hierarchy(records: list[LocationRecord]) -> None:
    """Link every record to its administrative ancestors, in place."""
    resolver = HierarchyResolver(records)

    # Parents first: rank ascending, larger areas before smaller at equal rank
    # so e.g. states resolve before same-ranked divisions nested inside them.
    for rec in sorted(records, key=lambda r: (r.rank, -(r.area_sqkm or 0.0))):
        resolver.attach(rec)
