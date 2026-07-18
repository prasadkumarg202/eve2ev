"""Search layer: layered full-text / fuzzy / phonetic location search.

Public entry point is :class:`SearchEngine`.
"""

from __future__ import annotations

from .engine import SearchEngine, haversine_km

__all__ = ["SearchEngine", "haversine_km"]
