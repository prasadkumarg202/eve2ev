"""Duplicate detection and merging.

OSM frequently represents one real-world place several times (a ``node`` place
marker plus a ``way``/``relation`` boundary, or overlapping zone extracts).
This module collapses those into a single record:

* Candidates are grouped by ``(place_type, slug)`` — only same-typed places
  with the same normalized name can merge.
* Within a group, records whose centroids lie within ``distance_m`` of each
  other are clustered (records without coordinates never merge — many distinct
  Indian villages share a name, so proximity is the only safe signal).
* Each cluster keeps its "richest" member (relation > way > node, then most
  tags/aliases/names and presence of geometry) and unions names, aliases and
  missing scalar fields from the rest.

Pure python — distance comes from :func:`osm_india_etl.transform.geometry.haversine_km`.
"""

from __future__ import annotations

from collections import defaultdict

from osm_india_etl.constants import OSMType
from osm_india_etl.models import LocationRecord

from .geometry import haversine_km

_OSM_TYPE_PREFERENCE: dict[OSMType, int] = {
    OSMType.RELATION: 2,
    OSMType.WAY: 1,
    OSMType.NODE: 0,
}


def _richness(rec: LocationRecord) -> tuple[int, int]:
    """Sort key: (osm-type preference, information content)."""
    score = len(rec.tags) + len(rec.aliases) + len(rec.names)
    if rec.geometry_wkt:
        score += 3
    return (_OSM_TYPE_PREFERENCE.get(rec.osm_type, 0), score)


def _merge_into(winner: LocationRecord, loser: LocationRecord) -> None:
    """Fold *loser*'s information into *winner* (winner's values take priority)."""
    # Union names / tags: loser fills gaps only.
    for key, value in loser.names.items():
        winner.names.setdefault(key, value)
    for key, value in loser.tags.items():
        winner.tags.setdefault(key, value)

    # Union aliases case-insensitively; the loser's primary name becomes an
    # alias when it differs from the winner's.
    existing = {a.lower() for a in winner.aliases}
    for alias in (*loser.aliases, loser.name):
        cleaned = alias.strip()
        if cleaned and cleaned.lower() not in existing and cleaned.lower() != winner.name.lower():
            winner.aliases.append(cleaned)
            existing.add(cleaned.lower())

    # Fill missing scalars.
    if winner.pincode is None:
        winner.pincode = loser.pincode
    if winner.latitude is None or winner.longitude is None:
        winner.latitude = loser.latitude
        winner.longitude = loser.longitude
    if not winner.geometry_wkt and loser.geometry_wkt:
        winner.geometry_wkt = loser.geometry_wkt
        winner.bbox = loser.bbox
        winner.area_sqkm = loser.area_sqkm
    if winner.admin_level is None:
        winner.admin_level = loser.admin_level

    winner.aliases.sort()


def _cluster(group: list[LocationRecord], distance_m: float) -> list[list[LocationRecord]]:
    """Greedy proximity clustering inside one (place_type, slug) group."""
    clusters: list[list[LocationRecord]] = []
    for rec in group:
        if rec.latitude is None or rec.longitude is None:
            clusters.append([rec])  # unmergeable without a position
            continue
        placed = False
        for cluster in clusters:
            anchor = cluster[0]
            if anchor.latitude is None or anchor.longitude is None:
                continue
            dist_m = haversine_km(rec.latitude, rec.longitude, anchor.latitude, anchor.longitude) * 1000.0
            if dist_m <= distance_m:
                cluster.append(rec)
                placed = True
                break
        if not placed:
            clusters.append([rec])
    return clusters


def deduplicate(records: list[LocationRecord], distance_m: float) -> list[LocationRecord]:
    """Collapse near-duplicate records; returns the reduced list.

    Input order is preserved (each surviving record keeps the position of its
    cluster's first occurrence).
    """
    order: dict[str, int] = {rec.location_id: idx for idx, rec in enumerate(records)}
    groups: dict[tuple[str, str], list[LocationRecord]] = defaultdict(list)
    survivors: list[LocationRecord] = []

    for rec in records:
        key = rec.slug or rec.search_name or rec.name_lower or rec.name.lower()
        if not key:
            survivors.append(rec)  # unnamed features never merge
            continue
        groups[(rec.place_type.value, key)].append(rec)

    for group in groups.values():
        for cluster in _cluster(group, distance_m):
            winner = max(cluster, key=_richness)
            first_position = min(order[rec.location_id] for rec in cluster)
            for rec in cluster:
                if rec is not winner:
                    _merge_into(winner, rec)
            order[winner.location_id] = first_position
            survivors.append(winner)

    survivors.sort(key=lambda rec: order[rec.location_id])
    return survivors
