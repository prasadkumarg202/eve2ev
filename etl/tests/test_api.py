"""API tests: FastAPI app wired to a temp sqlite database."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("fastapi")

from fastapi.testclient import TestClient  # noqa: E402

from osm_india_etl.api.app import create_app  # noqa: E402
from osm_india_etl.config import Settings  # noqa: E402
from test_search import build_test_db  # noqa: E402


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    db = tmp_path / "osm_api_test.sqlite"
    build_test_db(db)
    settings = Settings.model_validate(
        {
            "database": {"sqlite_path": str(db)},
            "api": {"backend": "sqlite", "cors_origins": ["*"]},
        }
    )
    return TestClient(create_app(settings))


class TestApi:
    def test_health(self, client: TestClient) -> None:
        resp = client.get("/health")
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "ok"
        assert body["backend"] == "sqlite"

    def test_search_returns_json(self, client: TestClient) -> None:
        resp = client.get("/search", params={"q": "bang"})
        assert resp.status_code == 200
        body = resp.json()
        assert body["query"] == "bang"
        assert body["count"] >= 1
        top = body["results"][0]
        assert top["name"] == "Bengaluru"
        assert top["score"] is not None

    def test_search_requires_query(self, client: TestClient) -> None:
        assert client.get("/search").status_code == 422

    def test_autocomplete(self, client: TestClient) -> None:
        resp = client.get("/autocomplete", params={"q": "che"})
        assert resp.status_code == 200
        names = [item["name"] for item in resp.json()]
        assert "Chennai" in names

    def test_reverse_geocode(self, client: TestClient) -> None:
        resp = client.get("/reverse-geocode", params={"lat": 12.9715, "lng": 77.595})
        assert resp.status_code == 200
        body = resp.json()
        assert body["result"] is not None
        assert body["result"]["name"] == "Bengaluru"

    def test_nearby(self, client: TestClient) -> None:
        resp = client.get(
            "/nearby", params={"lat": 12.9716, "lng": 77.5946, "radius_km": 10}
        )
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()]
        assert "Bengaluru" in names and "Chennai" not in names

    def test_tier_listing_paginated(self, client: TestClient) -> None:
        resp = client.get("/cities", params={"limit": 1, "offset": 0})
        assert resp.status_code == 200
        body = resp.json()
        assert body["table"] == "cities"
        assert body["count"] == 1 and len(body["items"]) == 1

    def test_states_endpoint(self, client: TestClient) -> None:
        resp = client.get("/states")
        assert resp.status_code == 200
        names = [r["name"] for r in resp.json()["items"]]
        assert "Karnataka" in names

    def test_all_tier_routes_exist(self, client: TestClient) -> None:
        for route in (
            "states", "districts", "mandals", "villages",
            "towns", "cities", "streets", "postalcodes",
        ):
            assert client.get(f"/{route}").status_code == 200
