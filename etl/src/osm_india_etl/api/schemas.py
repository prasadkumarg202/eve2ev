"""Pydantic v2 response models for the location API."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

__all__ = [
    "LocationOut",
    "SearchResponse",
    "AutocompleteItem",
    "ReverseGeocodeOut",
    "HealthOut",
    "Paginated",
]


class LocationOut(BaseModel):
    """A single location result row."""

    model_config = ConfigDict(extra="ignore")

    location_id: str
    name: str = ""
    place_type: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    pincode: str | None = None
    state_name: str | None = None
    district_name: str | None = None
    score: float | None = Field(default=None, description="Match score 0-100 (search only)")
    distance_km: float | None = Field(default=None, description="Distance from query point")


class SearchResponse(BaseModel):
    """Envelope for /search results."""

    query: str
    count: int
    results: list[LocationOut]


class AutocompleteItem(BaseModel):
    """Lightweight completion suggestion."""

    model_config = ConfigDict(extra="ignore")

    location_id: str
    name: str = ""
    place_type: str | None = None
    state_name: str | None = None
    district_name: str | None = None


class ReverseGeocodeOut(BaseModel):
    """Nearest-location answer for a coordinate pair."""

    query_lat: float
    query_lng: float
    result: LocationOut | None = None


class HealthOut(BaseModel):
    """Service liveness / config summary."""

    status: str = "ok"
    backend: str
    title: str
    version: str = "1.0.0"


class Paginated(BaseModel):
    """Generic paginated tier listing (states, districts, ...)."""

    table: str
    limit: int
    offset: int
    count: int
    items: list[LocationOut]
