# osm-india-etl

Production-grade ETL that downloads, processes, and imports the **complete OpenStreetMap dataset for India** into a queryable location database — every state, district, subdistrict (taluk / mandal / tehsil), village, town, city, ward, locality, neighbourhood, street, road, highway, optional building footprints, and postal code — with full parent→child hierarchy, multilingual names and aliases, geometry, and stable OSM identifiers.

## Objective

Build a single, authoritative, offline-usable location database of India:

- **Administrative hierarchy** — Country → State → District → Subdistrict (taluk/mandal/tehsil) → Municipality/City → Town → Village → Ward/Suburb → Locality/Neighbourhood, derived from `boundary=administrative` (`admin_level` 2–10) and `place=*` tags.
- **Transport network** — streets, roads, and highways classified from `highway=*`.
- **Buildings** — optional (`extract.extract_buildings`, off by default because footprints dominate extract size).
- **Postal codes** — from `addr:postcode` / `postal_code` / `postcode`.
- **Names & aliases** — primary, English, native-script, and regional-language names (`name:hi`, `name:te`, `name:ta`, …), plus generated aliases from `alt_name`, `old_name`, `official_name`, etc.
- **Geometry** — WKT geometry, centroid lat/lon, bounding box, and polygon area (km²).
- **Provenance** — OSM id/type, raw tags, and the source `.osm.pbf` file for every record.

## Architecture

```text
Geofabrik discovery ──> download ──> extract ──> transform ──> load ──> export
   (zone .osm.pbf)      (resume,     (pyosmium   (normalize,   (SQLite  (CSV,
                         retry,       streaming   aliases,      DuckDB   GeoJSON,
                         checksum)    → Parquet)  dedupe,       PostGIS) Parquet)
                                                  geometry,
                                                  hierarchy)          │
                                                                      ▼
                                                        FastAPI + search layer
                                                  (FTS5 / trigram / fuzzy / phonetic)
```

1. **Download** — dynamically discovers regional zone extracts (`southern-zone`, `northern-zone`, …) from the [Geofabrik India index](https://download.geofabrik.de/asia/india/), falling back to the full `india-latest.osm.pbf`. Downloads are streamed, resumable, retried with exponential backoff, and verified against `.md5` sidecars.
2. **Extract** — streams each `.osm.pbf` with **pyosmium**, classifying nodes/ways/relations into location entities and flushing batches (200k records by default) to per-zone Parquet.
3. **Transform** — name normalization (title/lower/ASCII/search forms, slug), alias generation, duplicate detection (same-name places within `dedupe_distance_m`), geometry computation (centroid/bbox/area), and hierarchy resolution (each record gets `parent_id`, ancestor chain, denormalized `state_name`/`district_name`).
4. **Load** — materializes per-tier entity tables (`states`, `districts`, `mandals`, `villages`, …) plus shared `locations`, `geometry`, and `aliases` tables into SQLite / DuckDB / PostGIS.
5. **Export** — writes Parquet, CSV, and GeoJSON deliverables.
6. **Serve / Search** — a FastAPI app with full-text (SQLite FTS5), trigram (`pg_trgm` on PostGIS), fuzzy (rapidfuzz), and phonetic (jellyfish) search.

See [docs/architecture.md](docs/architecture.md) for diagrams and the data model, and [docs/folder-structure.md](docs/folder-structure.md) for the annotated tree.

## Folder structure

```text
osm-india-etl/
├── config/
│   └── config.yaml            # all pipeline settings (env-overridable via OSM_*)
├── docs/
│   ├── architecture.md        # pipeline & data-model documentation
│   └── folder-structure.md    # annotated project tree
├── src/
│   └── osm_india_etl/
│       ├── __init__.py
│       ├── config.py          # typed settings loader (YAML + OSM_* env overrides)
│       ├── constants.py       # tag→entity mappings, admin levels, output schema
│       ├── models.py          # LocationRecord, DownloadItem, Checkpoint
│       ├── logging_setup.py   # loguru + rich logging configuration
│       ├── download.py        # Geofabrik discovery + resumable downloads
│       ├── extract.py         # pyosmium streaming extraction → Parquet
│       ├── transform/         # normalize, aliases, dedupe, geometry, hierarchy
│       ├── load.py            # SQLite / DuckDB / PostGIS loaders
│       ├── exporters/         # CSV / GeoJSON / Parquet exporters
│       ├── api/               # FastAPI app (osm_india_etl.api.app:app)
│       ├── search/            # FTS5 / trigram / fuzzy / phonetic search
│       ├── pipeline/          # stage orchestration + checkpointing
│       ├── utils/             # shared helpers
│       └── cli.py             # Typer CLI (console script: osm-india-etl)
├── tests/                     # pytest suite
├── downloads/                 # .osm.pbf extracts (raw/ inside) — gitignored
├── parquet/                   # per-zone extracted Parquet — gitignored
├── processed/                 # unified outputs, SQLite/DuckDB — gitignored
├── checkpoints/               # pipeline recovery state — gitignored
├── logs/                      # run logs — gitignored
├── sql/                       # generated/auxiliary SQL
├── main.py                    # CLI entry point (python main.py <command>)
├── pyproject.toml             # project + dependencies (managed with uv)
├── requirements.txt           # pip fallback mirror of runtime deps
├── Dockerfile                 # multi-stage ETL + API image
├── docker-compose.yml         # postgis + etl + api stack
├── Makefile                   # convenience targets
└── .env.example               # environment override template
```

## Quickstart

Requires **Python 3.12+** and [uv](https://docs.astral.sh/uv/).

```bash
git clone <repo-url> osm-india-etl
cd osm-india-etl

# Install everything into .venv
uv sync

# Optional: environment overrides
cp .env.example .env

# Sanity-check configuration and environment
uv run python main.py validate

# Run the complete pipeline (download → extract → transform → load → export)
uv run python main.py run

# Serve the location API on http://localhost:8000
uv run python main.py serve
```

Without uv, `pip install -r requirements.txt && pip install -e .` works as a fallback.

The console script is equivalent to `python main.py`:

```bash
uv run osm-india-etl run
```

## CLI reference

All commands: `python main.py <command>` (or `osm-india-etl <command>`). Add `--help` to any command for its options.

| Command | Description | Example |
|---|---|---|
| `download` | Discover zone extracts on Geofabrik and download them (resume + retry + MD5 verification). | `python main.py download` |
| `extract` | Stream downloaded `.osm.pbf` files with pyosmium into per-zone Parquet. | `python main.py extract` |
| `transform` | Normalize names, generate aliases, dedupe, compute geometry, build the hierarchy; writes the unified dataset. | `python main.py transform` |
| `load` | Load unified records into the configured databases (SQLite / DuckDB / PostGIS) as entity tables. | `python main.py load` |
| `export` | Write the configured export formats (Parquet, CSV, GeoJSON, SQLite, DuckDB, PostGIS). | `python main.py export` |
| `run` | Execute the full pipeline end-to-end; resumes from the last checkpoint. | `python main.py run` |
| `rebuild` | Full pipeline from scratch, ignoring existing checkpoints/outputs. | `python main.py rebuild` |
| `validate` | Validate configuration, environment, schema, and (when present) outputs. | `python main.py validate` |
| `serve` | Start the FastAPI location API (`osm_india_etl.api.app:app`). | `python main.py serve` |
| `search` | Query the built database from the command line. | `python main.py search "Kukatpally"` |

## Configuration

All settings live in [`config/config.yaml`](config/config.yaml), loaded into typed Pydantic models by `osm_india_etl.config`. Sections:

| Section | Purpose |
|---|---|
| `project` | Project/country identity (`India`, ISO `IN`). |
| `source` | Geofabrik base URL, country fallback URL, file pattern, preferred zones, checksum/size verification. |
| `paths` | Directory layout: `downloads`, `raw`, `processed`, `parquet`, `logs`, `sql`, `checkpoints`. |
| `download` | Concurrency, chunk size, retries, backoff, timeout, resume. |
| `extract` | Entity family toggles (admin / places / highways / buildings / postcodes), batch size, `admin_level` → tier map. |
| `transform` | Name normalization, alias generation, dedupe distance (m), geometry computation, default language. |
| `export` | Output formats and format options (CSV delimiter, GeoJSON simplification). |
| `database` | PostGIS connection + SQLite/DuckDB file paths. |
| `search` | FTS5 / trigram / fuzzy / phonetic toggles, autocomplete limit. |
| `api` | Bind host/port, title, backend (`sqlite` \| `duckdb` \| `postgis`), CORS. |
| `runtime` | Worker count (`0` = all cores), log level, rich progress. |

### Environment overrides

Every key can be overridden with an environment variable prefixed `OSM_`, using `__` for nesting (see `.env.example`). Values are coerced to bool/int/float/list automatically.

```bash
OSM_DOWNLOAD__CONCURRENCY=6        # download.concurrency
OSM_EXTRACT__EXTRACT_BUILDINGS=true
OSM_RUNTIME__WORKERS=8
OSM_API__BACKEND=postgis
OSM_CONFIG=config/other.yaml       # point at an alternate config file
```

PostGIS connection variables (used when `postgis` is an export format or `load` targets PostGIS):

```bash
OSM_DATABASE__HOST=localhost       # docker compose sets this to "postgis"
OSM_DATABASE__PORT=5432
OSM_DATABASE__NAME=osm_india
OSM_DATABASE__USER=osm
OSM_DATABASE__PASSWORD=osm
```

## Data source

Data comes from [Geofabrik](https://download.geofabrik.de/asia/india/) India **regional zone extracts** (`.osm.pbf`): southern, northern, western, eastern, central, and north-eastern zones. Zones are **discovered dynamically** from the index page (matching `source.file_pattern`), so new or renamed extracts are picked up automatically; if discovery yields nothing, the pipeline falls back to the full `india-latest.osm.pbf`. Downloads support **resume** (HTTP range requests), **retry with exponential backoff**, and **MD5 checksum + size verification** against Geofabrik's `.md5` sidecar files.

## Output formats

Configured via `export.formats`:

| Format | Location | Notes |
|---|---|---|
| Parquet | `parquet/` (per-zone) and `processed/locations.parquet` (unified) | Canonical interchange format; schema is `constants.LOCATION_COLUMNS`. |
| CSV | `processed/` | One file per entity table; delimiter configurable. |
| GeoJSON | `processed/` | Feature collections with WKT-derived geometries; optional simplification. |
| SQLite | `processed/osm_india.sqlite` | Entity tables + FTS5 index; default API backend. |
| DuckDB | `processed/osm_india.duckdb` | Analytical queries over the same tables. |
| PostGIS | server-side | Add `postgis` to `export.formats` (or run `load`); geometries as PostGIS types, `pg_trgm` for trigram search. |

Entity tables: `states`, `districts`, `subdistricts`, `mandals`, `taluks`, `villages`, `towns`, `cities`, `wards`, `localities`, `neighbourhoods`, `streets`, `roads`, `highways`, `buildings`, `postal_codes` — plus shared `locations`, `geometry`, and `aliases` tables.

## API

`python main.py serve` starts the FastAPI app (`osm_india_etl.api.app:app`) on `api.host:api.port` (default `0.0.0.0:8000`). Interactive docs at `/docs`.

| Endpoint | Description |
|---|---|
| `GET /search` | Full search across all entities (FTS + fuzzy + phonetic ranking). |
| `GET /autocomplete` | Prefix/typeahead suggestions (limit: `search.autocomplete_limit`). |
| `GET /reverse-geocode` | Nearest known location for a lat/lon. |
| `GET /nearby` | Locations within a radius of a point. |
| `GET /states` | List states / union territories. |
| `GET /districts` | List districts (filterable by state). |
| `GET /mandals` | List mandals / taluks / subdistricts. |
| `GET /villages` | List villages. |
| `GET /towns` | List towns. |
| `GET /cities` | List cities / municipalities. |
| `GET /streets` | List streets / roads. |
| `GET /postalcodes` | List / look up postal codes (PIN codes). |
| `GET /health` | Liveness + backend status. |

## Search features

- **SQLite FTS5** — full-text index over `search_name`, names, and aliases (default backend).
- **Trigram** — `pg_trgm` similarity when the backend is PostGIS.
- **Fuzzy** — rapidfuzz partial/token ratio and Levenshtein edit distance for misspellings ("Hyderbad" → "Hyderabad").
- **Phonetic** — jellyfish metaphone/soundex matching for transliteration variants ("Vizag"/"Vishakapatnam" style queries).
- All toggles live under `search:` in `config/config.yaml`.

## Docker

```bash
# Build ETL + API images
make docker-build            # or: docker build -t osm-india-etl .

# Full stack: PostGIS + one-shot ETL + API on :8000
cp .env.example .env
docker compose up -d --build

# Run just the pipeline against PostGIS
docker compose run --rm etl run

# Any CLI command works as the container argument
docker compose run --rm etl validate
docker compose run --rm etl download
```

Details:

- The image's `ENTRYPOINT` is `python main.py`, so the container command is any CLI command (`CMD` defaults to `validate`).
- The `api` build target (`docker build --target api …`) defaults to `serve`; you can also override the entrypoint with `uvicorn osm_india_etl.api.app:app --host 0.0.0.0 --port 8000`.
- Compose wires `OSM_DATABASE__HOST=postgis` and bind-mounts `./downloads`, `./processed`, `./parquet`, `./checkpoints`, and `./logs` so data and resume state persist on the host. PostGIS data lives in the named volume `pgdata`.

## Performance & hardware

Processing all of India is a heavyweight job — plan for it:

- **Download size** — the six zone extracts total multiple GB (the full `india-latest.osm.pbf` alone is > 1.5 GB and growing); with buildings enabled the extracted dataset multiplies several-fold.
- **Disk** — budget **≥ 50 GB free**: raw `.pbf` + per-zone Parquet + unified Parquet + SQLite/DuckDB/exports all coexist.
- **RAM** — 8 GB is a workable minimum with default settings; **16 GB+ recommended**. Extraction streams with pyosmium and flushes every `extract.batch_size` (200k) records, so memory stays bounded; the transform stage (dedupe + hierarchy joins over the unified dataset) is the peak-RAM phase.
- **CPU** — stages parallelize **per zone** (multiprocessing); `runtime.workers: 0` uses all cores. Fewer workers reduce peak memory.
- **Buildings** — leave `extract.extract_buildings: false` unless you need footprints; it is the single biggest cost lever.
- **Network** — Geofabrik throttles aggressively at high parallelism; the default `download.concurrency: 3` is deliberate.

## Recovery & checkpointing

The pipeline persists a JSON `Checkpoint` (stage, completed files, completed stages, stats) to `checkpoints/` after each stage/file:

- `python main.py run` **resumes** — completed downloads are skipped (size/MD5 verified), fully extracted zones are not re-parsed, finished stages are not repeated.
- Interrupted downloads resume mid-file via HTTP range requests (`download.resume: true`).
- `python main.py rebuild` ignores checkpoints and reprocesses everything from scratch.
- To reset manually, delete `checkpoints/` (and any partial outputs you want regenerated).

## Troubleshooting

| Symptom | Cause / fix |
|---|---|
| `validate` fails on config | YAML syntax or a bad `OSM_*` override — remember nested keys use double underscores (`OSM_DATABASE__HOST`, not `OSM_DATABASE_HOST`). |
| Downloads stall or 429/403 from Geofabrik | Lower `OSM_DOWNLOAD__CONCURRENCY`, keep retries/backoff enabled; Geofabrik rate-limits parallel clients. |
| Checksum mismatch after download | Partial/corrupt file — delete the affected file in `downloads/` and re-run `download`; resume + `.md5` verification will repair it. |
| `osmium` / `shapely` import errors from source builds | Install the geo system libraries (`libgeos-dev libproj-dev gdal-bin libgdal-dev`) or use the Docker image, which bundles them. |
| Out-of-memory during transform | Reduce `OSM_RUNTIME__WORKERS`, keep buildings disabled, and ensure swap is available; transform is the peak-RAM stage. |
| `load` cannot reach PostGIS | Check `OSM_DATABASE__*` vars; in Docker Compose the host is `postgis`, not `localhost`. Wait for the `postgis` healthcheck to pass. |
| API returns empty results | The backend database hasn't been built — run `python main.py run` (or at least `load`) first, and confirm `OSM_API__BACKEND` points at the database you built. |
| Port 8000 or 5432 already in use | Change the published port in `docker-compose.yml`, or `OSM_API__PORT` for local serving. |
| Stale/partial outputs after an aborted run | `python main.py rebuild`, or delete `checkpoints/` plus the affected output directory and re-run. |

## Development

```bash
uv sync --all-extras     # includes dev tools (pytest, ruff, mypy)
make test                # pytest
make lint                # ruff check
```

## License

MIT
