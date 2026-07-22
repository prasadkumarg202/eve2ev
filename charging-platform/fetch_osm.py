"""One-off: pull real charging stations from OSM and dump canonical JSON.

Usage: python fetch_osm.py <state> [<state> ...]
Writes out/osm_stations.json
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from evcharge.connectors.osm import OSMChargingConnector  # noqa: E402

OUT = Path(__file__).parent / "out"


async def main(states: list[str]) -> None:
    OUT.mkdir(exist_ok=True)
    connector = OSMChargingConnector({"states": states})
    stations, stats = await connector.run()

    print(stats.summary())
    if stats.errors:
        print(f"errors ({len(stats.errors)}):")
        for err in stats.errors[:5]:
            print("  ", err)

    rows = [s.model_dump(mode="json") for s in stations]
    path = OUT / "osm_stations.json"
    path.write_text(json.dumps(rows, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"wrote {len(rows)} stations -> {path}")

    by_state: dict[str, int] = {}
    for s in stations:
        by_state[s.address.state] = by_state.get(s.address.state, 0) + 1
    for state, count in sorted(by_state.items(), key=lambda kv: -kv[1]):
        print(f"  {state:<20} {count:>5}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:] or ["Karnataka"]))
