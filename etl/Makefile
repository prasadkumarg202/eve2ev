# =============================================================================
# osm-india-etl — convenience targets
#
# Requires: uv (https://docs.astral.sh/uv/), docker (for docker-* targets).
# Every pipeline target maps 1:1 to a CLI command: `python main.py <command>`.
# =============================================================================

UV      ?= uv
CLI      = $(UV) run python main.py
COMPOSE ?= docker compose
IMAGE   ?= osm-india-etl

.PHONY: help install download extract transform load export run rebuild \
        validate serve search test lint docker-build docker-up docker-down \
        clean clean-data

help: ## List available targets
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-14s %s\n", $$1, $$2}'

# ---------------------------------------------------------------- environment
install: ## Create .venv and install all dependencies (incl. dev) with uv
	$(UV) sync --all-extras

# ------------------------------------------------------------ pipeline stages
download: ## Discover and download Geofabrik India .osm.pbf extracts
	$(CLI) download

extract: ## Parse .osm.pbf files into per-zone Parquet (pyosmium)
	$(CLI) extract

transform: ## Normalize, alias, dedupe, geometry, hierarchy
	$(CLI) transform

load: ## Load unified records into SQLite / DuckDB / PostGIS
	$(CLI) load

export: ## Export to configured formats (parquet, csv, geojson, ...)
	$(CLI) export

run: ## Run the full pipeline (download -> export), checkpoint-aware
	$(CLI) run

rebuild: ## Re-run the full pipeline from scratch, ignoring checkpoints
	$(CLI) rebuild

validate: ## Validate configuration, environment, and outputs
	$(CLI) validate

serve: ## Serve the FastAPI location API (default :8000)
	$(CLI) serve

search: ## Interactive/CLI search. Usage: make search Q="hyderabad"
	$(CLI) search $(Q)

# --------------------------------------------------------------------- quality
test: ## Run the test suite
	$(UV) run pytest

lint: ## Lint with ruff
	$(UV) run ruff check src tests

# --------------------------------------------------------------------- docker
docker-build: ## Build the ETL and API images
	docker build --target runtime -t $(IMAGE):latest .
	docker build --target api -t $(IMAGE)-api:latest .

docker-up: ## Start the full compose stack (postgis + etl + api)
	$(COMPOSE) up -d --build

docker-down: ## Stop the compose stack (keeps the pgdata volume)
	$(COMPOSE) down

# --------------------------------------------------------------------- cleanup
clean: ## Remove caches and build artifacts (keeps data)
	-rm -rf .pytest_cache .ruff_cache .mypy_cache build dist *.egg-info
	-find . -type d -name "__pycache__" -not -path "./.venv/*" -exec rm -rf {} +

clean-data: ## DANGER: remove all downloaded and generated data
	-rm -rf downloads/* processed/* parquet/* logs/* checkpoints/*
