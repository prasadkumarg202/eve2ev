"""Fetch specific states from OSM and upsert them into Supabase.

Usage:
    python sync_states.py Telangana Delhi Gujarat Rajasthan

Safe to re-run: the sink upserts on a stable slug, so repeat syncs update
rather than duplicate.
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from evcharge.connectors.osm import OSMChargingConnector  # noqa: E402
from evcharge.core.sink import SupabaseSink  # noqa: E402

OUT = Path(__file__).parent / "out"


async def main(states: list[str]) -> None:
    if not states:
        print("usage: python sync_states.py <State> [<State> ...]")
        return

    print(f"fetching {len(states)} state(s): {', '.join(states)}")
    connector = OSMChargingConnector({"states": states})
    stations, stats = await connector.run()
    print(stats.summary())
    for err in stats.errors:
        print("  ERROR:", err)

    if not stations:
        print("nothing fetched; aborting load")
        return

    by_state: dict[str, int] = {}
    for s in stations:
        by_state[s.address.state] = by_state.get(s.address.state, 0) + 1
    for state, count in sorted(by_state.items(), key=lambda kv: -kv[1]):
        print(f"  {state:<20} {count:>5}")

    OUT.mkdir(exist_ok=True)
    (OUT / "sync_last.json").write_text(
        json.dumps([s.model_dump(mode="json") for s in stations], ensure_ascii=False),
        encoding="utf-8",
    )

    result = await SupabaseSink().load(stations)
    print(f"load: {result}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
