"""Load previously-fetched OSM stations into Supabase.

Usage:
    python load_osm.py            # loads out/osm_stations.json
    python load_osm.py --fetch    # re-query Overpass first
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from evcharge.connectors.osm import OSMChargingConnector  # noqa: E402
from evcharge.core.schema import Station  # noqa: E402
from evcharge.core.sink import SupabaseSink  # noqa: E402

CACHE = Path(__file__).parent / "out" / "osm_stations.json"


async def main(refetch: bool) -> None:
    if refetch or not CACHE.is_file():
        connector = OSMChargingConnector()
        stations, stats = await connector.run()
        print(stats.summary())
        CACHE.parent.mkdir(exist_ok=True)
        CACHE.write_text(
            json.dumps([s.model_dump(mode="json") for s in stations], ensure_ascii=False),
            encoding="utf-8",
        )
    else:
        raw = json.loads(CACHE.read_text(encoding="utf-8"))
        stations = [Station.model_validate(r) for r in raw]
        print(f"loaded {len(stations)} stations from cache")

    sink = SupabaseSink()
    result = await sink.load(stations)
    print(f"load: {result}")


if __name__ == "__main__":
    asyncio.run(main("--fetch" in sys.argv))
