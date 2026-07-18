"""Fuzzy string ranking.

Uses :mod:`rapidfuzz` when installed; otherwise falls back to
:class:`difflib.SequenceMatcher` so ranking still works (slower, pure python).
Scores are normalized to 0..100 (higher = better).
"""

from __future__ import annotations

from difflib import SequenceMatcher

try:  # pragma: no cover - exercised only when rapidfuzz is installed
    from rapidfuzz import fuzz as _rf_fuzz
    from rapidfuzz.distance import Levenshtein as _rf_levenshtein
except ImportError:  # pragma: no cover - fallback path covered by tests
    _rf_fuzz = None
    _rf_levenshtein = None

__all__ = ["rank", "score", "levenshtein", "HAS_RAPIDFUZZ"]

HAS_RAPIDFUZZ = _rf_fuzz is not None


def score(query: str, candidate: str) -> float:
    """Similarity score in ``[0, 100]`` between ``query`` and ``candidate``.

    With rapidfuzz this blends ``WRatio`` (handles partial/token matches)
    with a plain ratio; without it, uses ``SequenceMatcher`` plus a prefix
    bonus so prefixes of long names are not unfairly punished.
    """
    q = query.strip().lower()
    c = candidate.strip().lower()
    if not q or not c:
        return 0.0
    if q == c:
        return 100.0
    if _rf_fuzz is not None:
        return float(max(_rf_fuzz.WRatio(q, c), _rf_fuzz.ratio(q, c)))
    base = SequenceMatcher(None, q, c).ratio() * 100.0
    if c.startswith(q) or q.startswith(c):
        # Prefix affinity, comparable to rapidfuzz partial_ratio behaviour.
        base = max(base, 90.0 * min(len(q), len(c)) / max(len(q), len(c)) + 10.0)
    return min(base, 100.0)


def rank(query: str, candidates: list[str] | tuple[str, ...]) -> list[tuple[str, float]]:
    """Rank ``candidates`` against ``query``.

    Returns ``[(candidate, score)]`` sorted by score descending (stable for
    equal scores, preserving input order).
    """
    scored = [(cand, score(query, cand)) for cand in candidates]
    scored.sort(key=lambda pair: pair[1], reverse=True)
    return scored


def levenshtein(a: str, b: str) -> int:
    """Levenshtein edit distance between ``a`` and ``b``."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    if _rf_levenshtein is not None:
        return int(_rf_levenshtein.distance(a, b))
    return _levenshtein_py(a, b)


def _levenshtein_py(a: str, b: str) -> int:
    """Classic two-row dynamic-programming edit distance."""
    if len(a) < len(b):
        a, b = b, a
    previous = list(range(len(b) + 1))
    for i, ca in enumerate(a, start=1):
        current = [i]
        for j, cb in enumerate(b, start=1):
            insert = current[j - 1] + 1
            delete = previous[j] + 1
            substitute = previous[j - 1] + (ca != cb)
            current.append(min(insert, delete, substitute))
        previous = current
    return previous[-1]
