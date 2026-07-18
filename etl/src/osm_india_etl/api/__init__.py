"""HTTP API package: FastAPI app exposing the search engine."""

from __future__ import annotations

__all__ = ["create_app"]


def __getattr__(name: str):  # pragma: no cover - convenience lazy import
    if name == "create_app":
        from .app import create_app

        return create_app
    raise AttributeError(name)
