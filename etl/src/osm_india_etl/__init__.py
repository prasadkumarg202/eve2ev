"""osm-india-etl — production-grade OpenStreetMap ETL for India.

Public package surface. Submodules:
    config        – YAML + env configuration (Settings)
    constants     – OSM tag → entity mappings, admin-level tables
    models        – LocationRecord, enums, columnar schema
    logging_setup – Loguru + Rich logging
    download      – async discovery + resumable downloads
    extract       – pyosmium handlers → Parquet
    transform     – hierarchy, normalization, aliases, dedupe, geometry
    load          – SQLite / DuckDB / PostGIS loaders
    exporters     – CSV / Parquet / GeoJSON writers
    search        – FTS / trigram / fuzzy / phonetic
    api           – FastAPI application
    cli           – Typer command-line interface
"""

from __future__ import annotations

__version__ = "1.0.0"

__all__ = ["__version__"]
