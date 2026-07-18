"""Helpers to build SQLite FTS5 MATCH expressions and LIKE fallbacks.

FTS5 has its own query mini-language, so user input must be sanitized:
each term is wrapped in double quotes (with embedded quotes doubled) and
suffixed with ``*`` for prefix matching.
"""

from __future__ import annotations

import re

__all__ = [
    "sanitize_term",
    "fts_prefix_query",
    "fts_exact_query",
    "like_pattern",
    "trigrams",
    "trigram_like_clauses",
]

# Characters meaningful to the FTS5 query parser that we never pass through.
_TERM_SPLIT_RE = re.compile(r"[^\w]+", flags=re.UNICODE)


def sanitize_term(term: str) -> str:
    """Quote a single term for FTS5 (doubling embedded double quotes)."""
    return '"' + term.replace('"', '""') + '"'


def _terms(query: str) -> list[str]:
    """Split free text into plain word terms (drops FTS5 operators)."""
    return [t for t in _TERM_SPLIT_RE.split(query.strip()) if t]


def fts_prefix_query(query: str) -> str:
    """Build an FTS5 MATCH string where every term is a prefix match.

    ``"navi mum"`` -> ``'"navi"* "mum"*'`` (implicit AND between terms).
    Returns ``""`` when no usable terms remain.
    """
    return " ".join(f"{sanitize_term(t)}*" for t in _terms(query))


def fts_exact_query(query: str) -> str:
    """Build an FTS5 MATCH string of exact (non-prefix) terms."""
    return " ".join(sanitize_term(t) for t in _terms(query))


def like_pattern(query: str, *, prefix_only: bool = False) -> str:
    """Escape ``%``/``_`` and build a LIKE pattern (``ESCAPE '\\'`` assumed).

    ``prefix_only=True`` -> ``query%``, else ``%query%``.
    """
    escaped = (
        query.strip()
        .replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )
    return f"{escaped}%" if prefix_only else f"%{escaped}%"


def trigrams(text: str) -> list[str]:
    """Character trigrams of the lowercased, whitespace-collapsed text."""
    norm = re.sub(r"\s+", " ", text.strip().lower())
    if len(norm) < 3:
        return [norm] if norm else []
    return [norm[i : i + 3] for i in range(len(norm) - 2)]


def trigram_like_clauses(
    query: str, column: str = "search_name", max_grams: int = 6
) -> tuple[str, list[str]]:
    """Trigram-ish fallback: OR of LIKE clauses over the query's trigrams.

    Returns ``(sql_fragment, params)`` — e.g.
    ``("(search_name LIKE ? ESCAPE '\\' OR ...)", ['%ban%', ...])``.
    Useful when the FTS table is unavailable; recall-oriented (callers
    should rerank with :mod:`osm_india_etl.search.fuzzy`).
    """
    grams = trigrams(query)[:max_grams]
    if not grams:
        return "", []
    clause = " OR ".join(f"{column} LIKE ? ESCAPE '\\'" for _ in grams)
    params = [like_pattern(g) for g in grams]
    return f"({clause})", params
