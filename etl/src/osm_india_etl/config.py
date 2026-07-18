"""Typed configuration: loads ``config/config.yaml`` and applies environment
overrides (prefix ``OSM_``, nested delimiter ``__``).

Example override:
    OSM_DATABASE__HOST=db.internal  OSM_DOWNLOAD__CONCURRENCY=6
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

# Project root = two levels above this file (src/osm_india_etl/config.py -> root).
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_CONFIG_PATH = PROJECT_ROOT / "config" / "config.yaml"


# --------------------------------------------------------------------------- #
# Section models
# --------------------------------------------------------------------------- #
class ProjectCfg(BaseModel):
    name: str = "osm-india-etl"
    country: str = "India"
    country_iso: str = "IN"


class SourceCfg(BaseModel):
    base_url: str = "https://download.geofabrik.de/asia/india/"
    country_fallback_url: str = "https://download.geofabrik.de/asia/india-latest.osm.pbf"
    file_pattern: str = r".*\.osm\.pbf$"
    preferred_zones: list[str] = Field(default_factory=list)
    verify_checksum: bool = True
    verify_size: bool = True


class PathsCfg(BaseModel):
    downloads: str = "downloads"
    raw: str = "downloads/raw"
    processed: str = "processed"
    parquet: str = "parquet"
    logs: str = "logs"
    sql: str = "sql"
    checkpoints: str = "checkpoints"


class DownloadCfg(BaseModel):
    concurrency: int = 3
    chunk_size: int = 1_048_576
    max_retries: int = 5
    backoff_factor: float = 2.0
    timeout_seconds: int = 120
    resume: bool = True


class ExtractCfg(BaseModel):
    extract_admin: bool = True
    extract_places: bool = True
    extract_highways: bool = True
    extract_buildings: bool = False
    extract_postcodes: bool = True
    batch_size: int = 200_000
    admin_levels: dict[int, str] = Field(default_factory=dict)


class TransformCfg(BaseModel):
    normalize_names: bool = True
    generate_aliases: bool = True
    detect_duplicates: bool = True
    dedupe_distance_m: float = 150.0
    compute_geometry: bool = True
    default_language: str = "en"


class ExportCfg(BaseModel):
    formats: list[str] = Field(default_factory=lambda: ["parquet", "csv", "geojson", "sqlite", "duckdb"])
    csv_delimiter: str = ","
    geojson_simplify_tolerance: float = 0.0


class DatabaseCfg(BaseModel):
    driver: str = "postgresql"
    host: str = "localhost"
    port: int = 5432
    name: str = "osm_india"
    user: str = "osm"
    password: str = "osm"
    schema_: str = Field("public", alias="schema")
    sqlite_path: str = "processed/osm_india.sqlite"
    duckdb_path: str = "processed/osm_india.duckdb"

    model_config = {"populate_by_name": True}

    @property
    def sqlalchemy_url(self) -> str:
        return (
            f"postgresql+psycopg://{self.user}:{self.password}"
            f"@{self.host}:{self.port}/{self.name}"
        )


class SearchCfg(BaseModel):
    fts: bool = True
    trigram: bool = True
    fuzzy: bool = True
    phonetic: bool = True
    autocomplete_limit: int = 10


class ApiCfg(BaseModel):
    host: str = "0.0.0.0"
    port: int = 8000
    title: str = "OSM India Location API"
    backend: str = "sqlite"
    cors_origins: list[str] = Field(default_factory=lambda: ["*"])


class RuntimeCfg(BaseModel):
    workers: int = 0
    log_level: str = "INFO"
    rich_progress: bool = True


class Settings(BaseModel):
    project: ProjectCfg = Field(default_factory=ProjectCfg)
    source: SourceCfg = Field(default_factory=SourceCfg)
    paths: PathsCfg = Field(default_factory=PathsCfg)
    download: DownloadCfg = Field(default_factory=DownloadCfg)
    extract: ExtractCfg = Field(default_factory=ExtractCfg)
    transform: TransformCfg = Field(default_factory=TransformCfg)
    export: ExportCfg = Field(default_factory=ExportCfg)
    database: DatabaseCfg = Field(default_factory=DatabaseCfg)
    search: SearchCfg = Field(default_factory=SearchCfg)
    api: ApiCfg = Field(default_factory=ApiCfg)
    runtime: RuntimeCfg = Field(default_factory=RuntimeCfg)

    # ---- path helpers (absolute, auto-created) ----
    root: Path = PROJECT_ROOT

    def path(self, key: str) -> Path:
        rel = getattr(self.paths, key)
        p = (self.root / rel).resolve()
        return p

    def ensure_dirs(self) -> None:
        for key in type(self.paths).model_fields:
            self.path(key).mkdir(parents=True, exist_ok=True)

    @property
    def worker_count(self) -> int:
        return self.runtime.workers or (os.cpu_count() or 4)


# --------------------------------------------------------------------------- #
# Loading + env overrides
# --------------------------------------------------------------------------- #
def _apply_env_overrides(data: dict[str, Any], prefix: str = "OSM_") -> dict[str, Any]:
    """Override nested keys from env vars: OSM_SECTION__KEY=value."""
    for env_key, raw in os.environ.items():
        if not env_key.startswith(prefix):
            continue
        path = env_key[len(prefix):].lower().split("__")
        node: dict[str, Any] = data
        for part in path[:-1]:
            node = node.setdefault(part, {})  # type: ignore[assignment]
            if not isinstance(node, dict):
                break
        else:
            node[path[-1]] = _coerce(raw)
    return data


def _coerce(raw: str) -> Any:
    low = raw.lower()
    if low in {"true", "false"}:
        return low == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        pass
    if "," in raw:
        return [x.strip() for x in raw.split(",") if x.strip()]
    return raw


def load_settings(config_path: str | Path | None = None) -> Settings:
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    data: dict[str, Any] = {}
    if path.exists():
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    data = _apply_env_overrides(data)
    settings = Settings.model_validate(data)
    settings.ensure_dirs()
    return settings


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Cached settings singleton (respects OSM_CONFIG for an alternate file)."""
    return load_settings(os.environ.get("OSM_CONFIG"))
