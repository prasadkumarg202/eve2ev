"""Supabase sink — writes canonical stations into the master database.

Connectors stay database-agnostic: they emit :class:`Station` objects and
this module is the only place that knows about Supabase or PostGIS.

Writes go through the ``import_stations`` RPC rather than PostgREST table
inserts, so geometry is constructed in Postgres (connectors never speak WKT)
and the whole batch upserts atomically.

Requires ``SUPABASE_SERVICE_ROLE_KEY`` — the anon/publishable key is
deliberately read-only on these tables.
"""

from __future__ import annotations

import os
import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import httpx

from .schema import Station

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify(value: str | None, max_len: int = 60) -> str:
    """Lowercase ASCII slug; empty string when there is nothing to slug."""
    if not value:
        return ""
    return _SLUG_RE.sub("-", value.lower()).strip("-")[:max_len]


def _load_env_file(path: Path) -> None:
    """Populate os.environ from a simple KEY=VALUE file, without overriding."""
    if not path.is_file():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


@dataclass(slots=True)
class LoadResult:
    inserted: int = 0
    updated: int = 0
    operators_added: int = 0
    batches: int = 0
    failed_batches: int = 0

    def __str__(self) -> str:
        return (
            f"inserted={self.inserted} updated={self.updated} "
            f"operators+={self.operators_added} "
            f"batches={self.batches} failed={self.failed_batches}"
        )


class SupabaseSink:
    """Upserts :class:`Station` records into the ``stations`` table."""

    def __init__(
        self,
        url: str | None = None,
        service_key: str | None = None,
        env_file: Path | None = None,
        batch_size: int = 200,
    ) -> None:
        _load_env_file(env_file or Path(__file__).resolve().parents[3] / ".env")
        self.url = (url or os.environ.get("SUPABASE_URL", "")).rstrip("/")
        self.service_key = service_key or os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
        self.batch_size = batch_size

        if not self.url or not self.service_key:
            raise RuntimeError(
                "SupabaseSink needs SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY "
                "(set them in charging-platform/.env)"
            )

    # ---- mapping ------------------------------------------------------- #
    @staticmethod
    def to_payload(station: Station) -> dict[str, object]:
        """Flatten a Station into the shape ``import_stations`` expects."""
        name = station.name or "Charging Station"
        base = slugify(name) or "station"
        return {
            # vendor id keeps the slug unique across sources and stable
            # across re-runs, so repeat loads update rather than duplicate.
            "slug": f"{base}-{station.vendor_station_id}",
            "name": name,
            "city": station.address.city or "",
            "district": station.address.district,
            "state": station.address.state or "",
            "pin_code": station.address.pin_code,
            "lat": station.latitude,
            "lon": station.longitude,
            "operator_name": station.operator,
            "operator_slug": slugify(station.operator),
            "source_id": station.vendor_station_id,
            "data_source": station.vendor,
            "external_ids": station.external_ids or {station.vendor: station.vendor_station_id},
        }

    # ---- write --------------------------------------------------------- #
    async def load(self, stations: Sequence[Station]) -> LoadResult:
        """Upsert stations in batches. Returns aggregate counts."""
        result = LoadResult()
        if not stations:
            return result

        payloads = [self.to_payload(s) for s in stations]
        # Deduplicate on slug within the batch: Postgres rejects an
        # ON CONFLICT update that hits the same row twice in one statement.
        seen: dict[str, dict[str, object]] = {}
        for item in payloads:
            seen[str(item["slug"])] = item
        payloads = list(seen.values())

        endpoint = f"{self.url}/rest/v1/rpc/import_stations"
        headers = {
            "apikey": self.service_key,
            "Authorization": f"Bearer {self.service_key}",
            "Content-Type": "application/json",
        }

        async with httpx.AsyncClient(timeout=httpx.Timeout(120.0)) as client:
            for start in range(0, len(payloads), self.batch_size):
                chunk = payloads[start : start + self.batch_size]
                result.batches += 1
                try:
                    resp = await client.post(
                        endpoint, headers=headers, json={"payload": chunk}
                    )
                    resp.raise_for_status()
                    rows = resp.json()
                except (httpx.HTTPError, ValueError) as exc:
                    result.failed_batches += 1
                    detail = getattr(getattr(exc, "response", None), "text", "")
                    print(f"  batch {result.batches} failed: {exc} {detail[:200]}")
                    continue

                row = rows[0] if isinstance(rows, list) and rows else rows or {}
                result.inserted += int(row.get("inserted") or 0)
                result.updated += int(row.get("updated") or 0)
                result.operators_added += int(row.get("operators_added") or 0)

        return result
