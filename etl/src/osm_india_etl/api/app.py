"""FastAPI application factory for the OSM India location API.

Run with::

    uvicorn osm_india_etl.api.app:app --host 0.0.0.0 --port 8000

The fastapi import is guarded: this module always imports, but
:func:`create_app` raises a clear error when fastapi is missing and the
module-level ``app`` is ``None`` in that case.
"""

from __future__ import annotations

from typing import Any

from ..config import Settings, get_settings
from ..logging_setup import log
from ..search.engine import SearchEngine
from . import deps
from .schemas import (
    AutocompleteItem,
    HealthOut,
    LocationOut,
    Paginated,
    ReverseGeocodeOut,
    SearchResponse,
)

__all__ = ["create_app", "app"]

# route path -> entity table name
_TIER_ROUTES: dict[str, str] = {
    "states": "states",
    "districts": "districts",
    "mandals": "mandals",
    "villages": "villages",
    "towns": "towns",
    "cities": "cities",
    "streets": "streets",
    "postalcodes": "postal_codes",
}


def create_app(settings: Settings | None = None) -> "Any":
    """Build the FastAPI app (engine is opened lazily on first request)."""
    try:
        from fastapi import FastAPI, HTTPException, Query
        from fastapi.middleware.cors import CORSMiddleware
    except ImportError as exc:  # pragma: no cover - env without fastapi
        raise RuntimeError(
            "fastapi is required for the API layer: pip install fastapi uvicorn"
        ) from exc

    cfg = settings or get_settings()
    app = FastAPI(title=cfg.api.title, version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cfg.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Engine is created on first use so importing this module never touches
    # the database. When explicit settings are passed (tests), a dedicated
    # engine is built for them; otherwise the process-wide singleton is used.
    holder: dict[str, SearchEngine] = {}

    def engine() -> SearchEngine:
        if "engine" not in holder:
            holder["engine"] = SearchEngine(cfg) if settings is not None else deps.get_engine()
        return holder["engine"]

    # ------------------------------------------------------------------ #
    # Core endpoints
    # ------------------------------------------------------------------ #
    @app.get("/health", response_model=HealthOut)
    def health() -> HealthOut:
        return HealthOut(status="ok", backend=cfg.api.backend, title=cfg.api.title)

    @app.get("/search", response_model=SearchResponse)
    def search(
        q: str = Query(..., min_length=1, description="Free-text location query"),
        type: str | None = Query(None, description="Filter by place_type"),
        limit: int = Query(20, ge=1, le=200),
    ) -> SearchResponse:
        results = engine().search(q, place_type=type, limit=limit)
        return SearchResponse(
            query=q,
            count=len(results),
            results=[LocationOut.model_validate(r) for r in results],
        )

    @app.get("/autocomplete", response_model=list[AutocompleteItem])
    def autocomplete(
        q: str = Query(..., min_length=1, description="Name prefix"),
        limit: int | None = Query(None, ge=1, le=100),
    ) -> list[AutocompleteItem]:
        rows = engine().autocomplete(q, limit=limit)
        return [AutocompleteItem.model_validate(r) for r in rows]

    @app.get("/reverse-geocode", response_model=ReverseGeocodeOut)
    def reverse_geocode(
        lat: float = Query(..., ge=-90, le=90),
        lng: float = Query(..., ge=-180, le=180),
    ) -> ReverseGeocodeOut:
        row = engine().reverse_geocode(lat, lng)
        return ReverseGeocodeOut(
            query_lat=lat,
            query_lng=lng,
            result=LocationOut.model_validate(row) if row else None,
        )

    @app.get("/nearby", response_model=list[LocationOut])
    def nearby(
        lat: float = Query(..., ge=-90, le=90),
        lng: float = Query(..., ge=-180, le=180),
        radius_km: float = Query(5.0, gt=0, le=500),
        type: str | None = Query(None, description="Filter by place_type"),
        limit: int = Query(50, ge=1, le=1000),
    ) -> list[LocationOut]:
        rows = engine().nearby(lat, lng, radius_km=radius_km, place_type=type, limit=limit)
        return [LocationOut.model_validate(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Tier listing endpoints (paginated)
    # ------------------------------------------------------------------ #
    def _make_tier_route(table: str):
        def list_tier(
            limit: int = Query(100, ge=1, le=1000),
            offset: int = Query(0, ge=0),
            parent_id: str | None = Query(None, description="Filter by parent location_id"),
        ) -> Paginated:
            try:
                rows = engine().list_by_type(table, limit=limit, offset=offset, parent_id=parent_id)
            except ValueError as exc:
                raise HTTPException(status_code=404, detail=str(exc)) from exc
            return Paginated(
                table=table,
                limit=limit,
                offset=offset,
                count=len(rows),
                items=[LocationOut.model_validate(r) for r in rows],
            )

        return list_tier

    for route, table in _TIER_ROUTES.items():
        app.get(f"/{route}", response_model=Paginated, name=f"list_{table}")(
            _make_tier_route(table)
        )

    return app


# Module-level ASGI entry point: `uvicorn osm_india_etl.api.app:app`.
try:
    app = create_app()
except Exception as _exc:  # pragma: no cover - fastapi/config missing
    log.warning(f"API app not created at import time: {_exc}")
    app = None
