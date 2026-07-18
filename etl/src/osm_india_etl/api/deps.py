"""FastAPI dependency providers (settings + singleton SearchEngine)."""

from __future__ import annotations

from functools import lru_cache

from ..config import Settings, get_settings
from ..search.engine import SearchEngine

__all__ = ["get_settings_dep", "get_engine", "reset_engine"]


@lru_cache(maxsize=1)
def get_settings_dep() -> Settings:
    """Cached settings for dependency injection."""
    return get_settings()


@lru_cache(maxsize=1)
def get_engine() -> SearchEngine:
    """Singleton SearchEngine shared across requests."""
    return SearchEngine(get_settings_dep())


def reset_engine() -> None:
    """Drop cached singletons (used by tests and app factories)."""
    if get_engine.cache_info().currsize:
        try:
            get_engine().close()
        except Exception:  # pragma: no cover - best effort cleanup
            pass
    get_engine.cache_clear()
    get_settings_dep.cache_clear()
