# Folder structure

Annotated tree of the `osm-india-etl` project. Directories marked *(generated)* are created automatically by `config.Settings.ensure_dirs()` on first run and are gitignored.

```text
osm-india-etl/
│
├── main.py                        # CLI entry point: python main.py <command>
├── pyproject.toml                 # project metadata + dependencies (uv-managed, hatchling build)
├── requirements.txt               # pip fallback mirror of runtime dependencies
├── README.md                      # project documentation
├── Makefile                       # convenience targets (install, run, serve, docker-*, ...)
├── Dockerfile                     # multi-stage image: builder / runtime (ETL) / api
├── docker-compose.yml             # postgis + etl + api stack
├── .dockerignore                  # keeps data dirs and secrets out of the image
├── .gitignore                     # Python + data-directory ignores
├── .env.example                   # OSM_* environment override template (copy to .env)
│
├── config/
│   └── config.yaml                # all pipeline settings; every key overridable via
│                                  #   OSM_<SECTION>__<KEY> environment variables
│
├── docs/
│   ├── architecture.md            # pipeline diagrams, component map, data model
│   └── folder-structure.md        # this file
│
├── src/
│   └── osm_india_etl/             # the Python package (installed as `osm-india-etl`)
│       ├── __init__.py
│       ├── config.py              # typed Settings: YAML loader + OSM_* env overrides,
│       │                          #   path resolution, get_settings() singleton
│       ├── constants.py           # PlaceType/OSMType enums, admin_level & tag mappings,
│       │                          #   LOCATION_COLUMNS schema, entity-table registry
│       ├── models.py              # LocationRecord / DownloadItem / Checkpoint contracts
│       ├── logging_setup.py       # loguru + rich logging configuration
│       ├── download.py            # Geofabrik discovery + resumable, verified downloads
│       ├── extract.py             # pyosmium streaming .osm.pbf → per-zone Parquet
│       ├── load.py                # SQLite / DuckDB / PostGIS loaders + search indexes
│       ├── cli.py                 # Typer app (console script `osm-india-etl`):
│       │                          #   download extract transform load export
│       │                          #   run rebuild validate serve search
│       ├── transform/             # transform stage
│       │                          #   name normalization, alias generation, dedupe,
│       │                          #   geometry (centroid/bbox/area), hierarchy resolution
│       ├── exporters/             # CSV / GeoJSON / Parquet exporters
│       ├── api/                   # FastAPI app — osm_india_etl.api.app:app
│       │                          #   /search /autocomplete /reverse-geocode /nearby
│       │                          #   /states /districts /mandals /villages /towns
│       │                          #   /cities /streets /postalcodes /health
│       ├── search/                # FTS5 / trigram / fuzzy / phonetic query engine
│       ├── pipeline/              # stage orchestration, per-zone multiprocessing,
│       │                          #   checkpoint persistence (run / rebuild)
│       └── utils/                 # shared helpers
│
├── tests/                         # pytest suite (pythonpath=src, asyncio auto mode)
│
├── downloads/                     # (generated) downloaded artifacts
│   └── raw/                       # (generated) .osm.pbf zone extracts + .md5 sidecars
├── parquet/                       # (generated) per-zone extracted Parquet
├── processed/                     # (generated) unified outputs:
│                                  #   locations.parquet, osm_india.sqlite,
│                                  #   osm_india.duckdb, CSV / GeoJSON exports
├── checkpoints/                   # (generated) JSON Checkpoint files for resume/recovery
├── logs/                          # (generated) run logs
└── sql/                           # (generated) auxiliary / generated SQL
```

## Conventions

- **Everything under `src/`** — the package is imported as `osm_india_etl`; tooling (`pytest`, `mypy`, Docker) adds `src/` to the path (`PYTHONPATH=/app/src` in the image).
- **Data directories are disposable** — `downloads/`, `parquet/`, `processed/`, `checkpoints/`, `logs/`, `sql/` are regenerable from the pipeline and excluded from git and the Docker build context. In Docker Compose they are bind-mounted so state persists on the host.
- **One artifact per stage** — `.osm.pbf` (download) → per-zone Parquet (extract) → `processed/locations.parquet` (transform) → databases/exports (load/export). See [architecture.md](architecture.md) for the full flow.
