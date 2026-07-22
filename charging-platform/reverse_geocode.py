"""Fill missing city/district/pin_code on stations via OSM Nominatim.

Stations imported from OSM charging nodes almost never carry ``addr:city``,
which makes city-level area search impossible. This backfills the address
from each station's coordinates.

Nominatim's usage policy allows an absolute maximum of 1 request/second with
an identifying User-Agent. That is respected here; ~500 stations takes ~9
minutes. Results are cached to disk so a re-run costs nothing.
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).parent / "src"))

from evcharge.core.normalize import canonical_state  # noqa: E402
from evcharge.core.sink import _load_env_file  # noqa: E402

NOMINATIM = "https://nominatim.openstreetmap.org/reverse"
USER_AGENT = "ev2ev-charging-etl/1.0 (contact: prasadkumar.g202@gmail.com)"
RATE_LIMIT_S = 1.1  # policy is 1 req/s; leave headroom
CACHE = Path(__file__).parent / "out" / "reverse_cache.json"

# Nominatim address keys that can stand in for "city", best first.
_CITY_KEYS = (
    "city", "town", "municipality", "village", "suburb",
    "city_district", "county",
)
_DISTRICT_KEYS = ("state_district", "county", "district")


def pick(address: dict[str, str], keys: tuple[str, ...]) -> str | None:
    for key in keys:
        value = (address.get(key) or "").strip()
        if value:
            return value
    return None


async def main() -> None:
    _load_env_file(Path(__file__).parent / ".env")
    url = os.environ["SUPABASE_URL"].rstrip("/")
    key = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
    headers = {"apikey": key, "Authorization": f"Bearer {key}"}

    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.get(
            f"{url}/rest/v1/stations",
            params={"select": "id,slug,latitude,longitude,city,district,pin_code"},
            headers=headers,
        )
        resp.raise_for_status()
        stations = resp.json()

    todo = [s for s in stations if not (s.get("city") or "").strip()]
    print(f"{len(stations)} stations, {len(todo)} missing city")

    cache: dict[str, dict] = {}
    if CACHE.is_file():
        cache = json.loads(CACHE.read_text(encoding="utf-8"))
        print(f"cache hits available: {len(cache)}")

    updates: list[dict] = []
    async with httpx.AsyncClient(
        timeout=45, headers={"User-Agent": USER_AGENT}
    ) as client:
        for i, station in enumerate(todo, 1):
            sid = station["id"]
            if sid in cache:
                address = cache[sid]
            else:
                try:
                    r = await client.get(
                        NOMINATIM,
                        params={
                            "lat": station["latitude"],
                            "lon": station["longitude"],
                            "format": "jsonv2",
                            "zoom": 14,
                            "addressdetails": 1,
                        },
                    )
                    r.raise_for_status()
                    address = (r.json() or {}).get("address", {}) or {}
                except (httpx.HTTPError, ValueError) as exc:
                    print(f"  [{i}/{len(todo)}] {station['slug'][:30]}: {exc}")
                    address = {}
                cache[sid] = address
                await asyncio.sleep(RATE_LIMIT_S)

            city = pick(address, _CITY_KEYS)
            district = pick(address, _DISTRICT_KEYS)
            state = canonical_state(address.get("state"))
            pin = (address.get("postcode") or "").strip() or None

            if city or district or pin:
                updates.append(
                    {
                        "id": sid,
                        "city": city,
                        "district": district,
                        "state": state,
                        "pin_code": pin,
                    }
                )
            if i % 25 == 0:
                print(f"  [{i}/{len(todo)}] resolved={len(updates)}")
                CACHE.parent.mkdir(exist_ok=True)
                CACHE.write_text(json.dumps(cache), encoding="utf-8")

    CACHE.parent.mkdir(exist_ok=True)
    CACHE.write_text(json.dumps(cache), encoding="utf-8")
    print(f"resolved {len(updates)} addresses; writing back")

    # PATCH one row at a time: PostgREST bulk upsert would need every column.
    written = 0
    async with httpx.AsyncClient(timeout=60) as client:
        for u in updates:
            body = {k: v for k, v in u.items() if k != "id" and v}
            if not body:
                continue
            r = await client.patch(
                f"{url}/rest/v1/stations",
                params={"id": f"eq.{u['id']}"},
                headers={**headers, "Content-Type": "application/json"},
                json=body,
            )
            if r.status_code < 300:
                written += 1
    print(f"updated {written} stations")


if __name__ == "__main__":
    asyncio.run(main())
