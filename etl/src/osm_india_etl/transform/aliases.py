"""Alias generation for :class:`~osm_india_etl.models.LocationRecord`.

Aliases are alternative spellings a user might type when searching for a
location. They come from three sources:

1. OSM alias tags (:data:`~osm_india_etl.constants.ALIAS_TAG_KEYS`) present in
   ``rec.tags`` or ``rec.names`` — values may be ``;``-separated per OSM
   convention.
2. Transliteration variants of every captured ``name:*`` value.
3. A small built-in map of well-known Indian renamings (Bengaluru/Bangalore,
   Mumbai/Bombay, ...), applied in both directions.

The canonical name itself is excluded; the result is a sorted, case-insensitively
de-duplicated list.
"""

from __future__ import annotations

from osm_india_etl.constants import ALIAS_TAG_KEYS
from osm_india_etl.models import LocationRecord

from .normalize import is_latin, transliterate

# Well-known official renamings (old name <-> new name). Kept small and
# high-confidence; both directions are generated below.
_RENAMED_PAIRS: tuple[tuple[str, str], ...] = (
    ("Bengaluru", "Bangalore"),
    ("Mumbai", "Bombay"),
    ("Kolkata", "Calcutta"),
    ("Chennai", "Madras"),
    ("Puducherry", "Pondicherry"),
    ("Varanasi", "Banaras"),
    ("Kochi", "Cochin"),
    ("Thiruvananthapuram", "Trivandrum"),
    ("Prayagraj", "Allahabad"),
    ("Vadodara", "Baroda"),
    ("Guwahati", "Gauhati"),
    ("Kanpur", "Cawnpore"),
    ("Mysuru", "Mysore"),
    ("Mangaluru", "Mangalore"),
    ("Belagavi", "Belgaum"),
    ("Vijayawada", "Bezawada"),
    ("Shimla", "Simla"),
    ("Odisha", "Orissa"),
    ("Uttarakhand", "Uttaranchal"),
)

INDIA_SYNONYMS: dict[str, str] = {}
for _new, _old in _RENAMED_PAIRS:
    INDIA_SYNONYMS[_new.lower()] = _old
    INDIA_SYNONYMS[_old.lower()] = _new


def _split_values(raw: str) -> list[str]:
    """Split an OSM multi-value tag (``;`` separated) into clean parts."""
    return [part.strip() for part in raw.split(";") if part.strip()]


def generate_aliases(rec: LocationRecord) -> list[str]:
    """Return a sorted, de-duplicated alias list for *rec*.

    Existing ``rec.aliases`` entries are preserved (merged in), so the function
    is safe to run after a dedupe pass unioned aliases from merged records.
    """
    candidates: list[str] = list(rec.aliases)

    # 1. OSM alias tags from both the raw tag dict and the captured names.
    for key in ALIAS_TAG_KEYS:
        for source in (rec.tags, rec.names):
            raw = source.get(key, "")
            if raw:
                candidates.extend(_split_values(raw))

    # 2. Transliteration variants of every name value.
    name_values = [rec.name, *rec.names.values()]
    for value in name_values:
        if value and not is_latin(value):
            ascii_variant = transliterate(value)
            if ascii_variant:
                candidates.append(ascii_variant)

    # 3. Built-in India synonym map (checked against names and aliases found).
    for value in (*name_values, rec.name_en, *candidates):
        if not value:
            continue
        mapped = INDIA_SYNONYMS.get(value.strip().lower())
        if mapped:
            candidates.append(mapped)

    # De-duplicate case-insensitively, excluding the canonical name(s).
    canonical = {rec.name.strip().lower(), rec.name_en.strip().lower(), ""}
    seen: set[str] = set()
    result: list[str] = []
    for value in candidates:
        cleaned = value.strip()
        key = cleaned.lower()
        if key in canonical or key in seen:
            continue
        seen.add(key)
        result.append(cleaned)

    return sorted(result)
