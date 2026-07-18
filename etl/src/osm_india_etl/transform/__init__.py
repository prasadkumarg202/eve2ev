"""TRANSFORM stage: geometry, normalization, aliases, dedupe, hierarchy.

Re-exports :func:`run_transform`. The import is lazy (PEP 562) so the pure
submodules (``normalize``, ``aliases``, ``geometry``, ``dedupe``,
``hierarchy``) stay importable without the pipeline's heavier dependencies
(config/logging/Parquet engines).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover
    from .pipeline import run_transform

__all__ = ["run_transform"]


def __getattr__(name: str) -> Any:
    if name == "run_transform":
        from .pipeline import run_transform

        return run_transform
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
