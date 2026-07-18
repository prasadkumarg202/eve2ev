"""Name normalization for :class:`~osm_india_etl.models.LocationRecord`.

Fills the derived name columns (``name_en``, ``name_native``, ``name_title``,
``name_lower``, ``name_ascii``, ``search_name``, ``slug``) used by search
(FTS / trigram) and by the exporters.

Third-party helpers (``unidecode``, ``python-slugify``) are optional: pure
Python fallbacks based on Unicode NFKD decomposition keep this module (and the
test-suite) importable in a minimal environment.
"""

from __future__ import annotations

import re
import unicodedata

from osm_india_etl.constants import NAME_TAG_KEYS
from osm_india_etl.models import LocationRecord

# --------------------------------------------------------------------------- #
# Optional dependencies with pure-python fallbacks
# --------------------------------------------------------------------------- #
try:  # pragma: no cover - trivial import guard
    from unidecode import unidecode as _unidecode

    HAS_UNIDECODE = True
except ImportError:  # pragma: no cover
    HAS_UNIDECODE = False

    def _unidecode(text: str) -> str:
        """ASCII-fold via NFKD decomposition (drops non-decomposable scripts)."""
        decomposed = unicodedata.normalize("NFKD", text)
        without_marks = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
        return without_marks.encode("ascii", "ignore").decode("ascii")


try:  # pragma: no cover - trivial import guard
    from slugify import slugify as _slugify

    HAS_SLUGIFY = True
except ImportError:  # pragma: no cover
    HAS_SLUGIFY = False

    _SLUG_STRIP_RE = re.compile(r"[^a-z0-9]+")

    def _slugify(text: str) -> str:
        """Minimal slugifier: ASCII-fold, lowercase, dash-separate."""
        folded = _unidecode(text).lower()
        return _SLUG_STRIP_RE.sub("-", folded).strip("-")


_PUNCT_RE = re.compile(r"[^\w\s]", re.UNICODE)
_WS_RE = re.compile(r"\s+")

# Latin script upper bound: Basic Latin + Latin-1 + Latin Extended-A/B.
_LATIN_MAX_CODEPOINT = 0x024F


def transliterate(text: str) -> str:
    """Return a best-effort ASCII transliteration of *text*."""
    return _unidecode(text).strip()


def is_latin(text: str) -> bool:
    """True when every alphabetic character of *text* is in a Latin block."""
    return all(ord(ch) <= _LATIN_MAX_CODEPOINT for ch in text if ch.isalpha())


def _title_case(text: str) -> str:
    """Title-case each word while preserving inner capitals (``NH 44`` stays)."""
    return " ".join(word[:1].upper() + word[1:] for word in text.split())


def make_search_name(text: str) -> str:
    """Lowercase, strip punctuation, collapse whitespace — the FTS/trigram key."""
    lowered = _PUNCT_RE.sub(" ", text.lower())
    return _WS_RE.sub(" ", lowered).strip()


def _best_native_name(rec: LocationRecord) -> str:
    """Pick the best non-Latin script name (primary name first, then name:*)."""
    if rec.name and not is_latin(rec.name):
        return rec.name
    for key in NAME_TAG_KEYS:
        value = rec.names.get(key, "")
        if value and not is_latin(value):
            return value
    # Any remaining non-latin value (keys outside the curated list).
    for value in rec.names.values():
        if value and not is_latin(value):
            return value
    return ""


def normalize_record(rec: LocationRecord, default_language: str = "en") -> None:
    """Populate all derived name fields of *rec* in place.

    Resolution order for the English name: an explicit ``name:<lang>`` tag
    (``name:en`` by default), then the primary ``name`` when already Latin,
    then a transliteration of the primary name.
    """
    lang_key = f"name:{default_language}"
    explicit = (rec.names.get(lang_key) or rec.tags.get(lang_key) or "").strip()
    primary = rec.name.strip()

    if explicit:
        name_en = explicit
    elif primary and is_latin(primary):
        name_en = primary
    else:
        name_en = transliterate(primary)

    rec.name_en = name_en
    rec.name_native = _best_native_name(rec)

    base = name_en or primary
    rec.name_title = _title_case(base)
    rec.name_lower = base.lower()
    rec.name_ascii = transliterate(base)

    search_source = rec.name_ascii or base
    rec.search_name = make_search_name(search_source)
    rec.slug = _slugify(base)
