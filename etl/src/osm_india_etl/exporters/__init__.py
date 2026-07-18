"""EXPORT stage: write the canonical locations dataset to file formats.

File formats (parquet / csv / geojson) are produced here under
``processed/exports/``. Database formats (sqlite / duckdb / postgis) belong to
:mod:`osm_india_etl.load`; when they appear in ``settings.export.formats``,
:func:`run_export` delegates to the loader and merges the resulting paths so
callers get a single ``{format: path}`` mapping.
"""

from __future__ import annotations

from pathlib import Path

from ..config import Settings, get_settings
from ..logging_setup import StageTimer, log
from .geojson import to_geojson
from .tabular import iter_parquet_rows, to_csv, to_parquet

__all__ = ["iter_parquet_rows", "run_export", "to_csv", "to_geojson", "to_parquet"]

# Formats materialized as plain files by this package.
FILE_FORMATS: frozenset[str] = frozenset({"parquet", "csv", "geojson"})
# Formats materialized as databases by osm_india_etl.load.
DB_FORMATS: frozenset[str] = frozenset({"sqlite", "duckdb", "postgis"})


def run_export(
    settings: Settings | None = None,
    locations_parquet: Path | None = None,
) -> dict[str, Path]:
    """Export the locations dataset to every configured format.

    Args:
        settings: Optional settings override (defaults to the cached singleton).
        locations_parquet: Source Parquet file (defaults to
            ``processed/locations.parquet`` produced by the TRANSFORM stage).

    Returns:
        Mapping of format name to the written path. Database formats found in
        ``settings.export.formats`` are handled by the LOAD stage and included
        here when they produce a path (postgis loads remotely and yields none).
    """
    settings = settings or get_settings()
    src = Path(locations_parquet) if locations_parquet else (
        settings.path("processed") / "locations.parquet"
    )
    out_dir = settings.path("processed") / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    formats = list(dict.fromkeys(settings.export.formats))  # de-dupe, keep order
    results: dict[str, Path] = {}

    with StageTimer("export", total=len(formats)) as timer:
        for fmt in formats:
            if fmt not in FILE_FORMATS:
                if fmt not in DB_FORMATS:
                    log.warning("Unknown export format '{}' — skipping", fmt)
                continue
            if fmt == "parquet":
                results["parquet"] = to_parquet(src, out_dir / "locations.parquet")
            elif fmt == "csv":
                results["csv"] = to_csv(
                    src, out_dir / "locations.csv", delimiter=settings.export.csv_delimiter
                )
            elif fmt == "geojson":
                results["geojson"] = to_geojson(
                    src,
                    out_dir / "locations.geojson",
                    simplify_tolerance=settings.export.geojson_simplify_tolerance,
                )
            timer.add()
            log.info("Exported {} -> {}", fmt, results[fmt])

        if any(fmt in DB_FORMATS for fmt in formats):
            from ..load import run_load  # local import to avoid a cycle

            for fmt, path in run_load(settings, src).items():
                if path is not None:
                    results[fmt] = path

    return results
