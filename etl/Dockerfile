# syntax=docker/dockerfile:1
# =============================================================================
# osm-india-etl — multi-stage build
#
#   Stage "builder": installs the geo build toolchain + Python deps with uv
#   Stage "runtime": slim image with only runtime libs, non-root, ETL default
#   Stage "api":     same image, defaults to serving the FastAPI app
#
# Build ETL image:   docker build -t osm-india-etl .
# Build API image:   docker build --target api -t osm-india-etl-api .
# Run a command:     docker run --rm osm-india-etl run
#                    (ENTRYPOINT is `python main.py`, so the container arg is
#                    any CLI command: download | extract | transform | load |
#                    export | run | rebuild | validate | serve | search)
# =============================================================================

# ---------------------------------------------------------------------------
# Stage 1 — builder: compile-capable image that resolves and installs all
# Python dependencies into a relocatable virtualenv at /opt/venv.
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive

# System libraries required by the geo stack:
#   - libgeos-dev / libproj-dev / libgdal-dev : headers for shapely, pyproj,
#     geopandas and any source builds that fall back from wheels
#   - gdal-bin                                : GDAL CLI utilities
#   - osmium-tool                             : osmium CLI (inspect/merge .pbf)
#   - build-essential                         : C/C++ toolchain for sdists
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        libgeos-dev \
        libproj-dev \
        gdal-bin \
        libgdal-dev \
        osmium-tool \
    && rm -rf /var/lib/apt/lists/*

# uv — fast Python package manager (pin a specific tag for fully reproducible
# builds, e.g. ghcr.io/astral-sh/uv:0.8).
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV UV_LINK_MODE=copy \
    UV_COMPILE_BYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# 1) Dependencies only — this layer is cached until pyproject.toml changes.
COPY pyproject.toml README.md ./
RUN uv venv /opt/venv \
    && uv pip install --python /opt/venv/bin/python -r pyproject.toml

# 2) The package itself (provides the `osm-india-etl` console script).
COPY src ./src
COPY main.py ./
RUN uv pip install --python /opt/venv/bin/python --no-deps .

# ---------------------------------------------------------------------------
# Stage 2 — runtime: slim image, runtime shared libs only, non-root user.
# ---------------------------------------------------------------------------
FROM python:3.12-slim-bookworm AS runtime

ENV DEBIAN_FRONTEND=noninteractive

# Runtime (non -dev) counterparts of the builder libraries, plus curl for
# container healthchecks against the API.
RUN apt-get update && apt-get install -y --no-install-recommends \
        gdal-bin \
        libgdal32 \
        libgeos-c1v5 \
        libproj25 \
        osmium-tool \
        curl \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --uid 1000 etl

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
COPY --chown=etl:etl main.py ./
COPY --chown=etl:etl config ./config
COPY --chown=etl:etl src ./src

# Data directories (bind-mount or volume-mount these in production).
RUN mkdir -p downloads/raw processed parquet logs checkpoints sql \
    && chown -R etl:etl /app

ENV PATH="/opt/venv/bin:${PATH}" \
    PYTHONPATH=/app/src \
    PYTHONUNBUFFERED=1

USER etl

# Any osm-india-etl CLI command can be passed as the container argument.
ENTRYPOINT ["python", "main.py"]
CMD ["validate"]

# ---------------------------------------------------------------------------
# Stage 3 — api: identical runtime image, but defaults to serving the API.
#
#   docker build --target api -t osm-india-etl-api .
#   docker run --rm -p 8000:8000 osm-india-etl-api
#
# Equivalent alternatives (overriding the entrypoint):
#   docker run --rm -p 8000:8000 --entrypoint osm-india-etl osm-india-etl serve
#   docker run --rm -p 8000:8000 --entrypoint uvicorn osm-india-etl \
#       osm_india_etl.api.app:app --host 0.0.0.0 --port 8000
# ---------------------------------------------------------------------------
FROM runtime AS api

EXPOSE 8000

CMD ["serve"]
