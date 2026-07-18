"""TRANSFORM stage orchestration.

Reads every per-zone Parquet file produced by the extract stage
(``settings.path("parquet")/*.parquet``), rebuilds
:class:`~osm_india_etl.models.LocationRecord` objects, enriches them
(geometry → name normalization → aliases → dedupe → hierarchy, each gated by
``settings.transform`` flags), and writes one unified
``settings.path("processed")/locations.parquet`` with columns exactly
:data:`~osm_india_etl.constants.LOCATION_COLUMNS`.

Parquet I/O prefers Polars and falls back to PyArrow; at least one must be
installed to run the stage.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from osm_india_etl.config import Settings, get_settings
from osm_india_etl.constants import LOCATION_COLUMNS
from osm_india_etl.logging_setup import StageTimer, log
from osm_india_etl.models import LocationRecord

from .aliases import generate_aliases
from .dedupe import deduplicate
from .geometry import compute_geometry
from .hierarchy import build_hierarchy
from .normalize import normalize_record

try:  # pragma: no cover - trivial import guard
    import polars as pl
except ImportError:  # pragma: no cover
    pl = None  # type: ignore[assignment]

try:  # pragma: no cover - trivial import guard
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:  # pragma: no cover
    pa = None  # type: ignore[assignment]
    pq = None  # type: ignore[assignment]

OUTPUT_FILENAME = "locations.parquet"


def _require_engine() -> None:
    if pl is None and pq is None:
        raise RuntimeError(
            "The transform stage needs a Parquet engine: install 'polars' or 'pyarrow'."
        )


def _read_rows(path: Path) -> list[dict[str, Any]]:
    """Read one Parquet file into a list of plain row dicts."""
    if pl is not None:
        return pl.read_parquet(path).to_dicts()
    table = pq.read_table(path)
    return table.to_pylist()


def _write_rows(rows: list[dict[str, Any]], out_path: Path) -> None:
    """Write rows with the exact LOCATION_COLUMNS column order."""
    columns = list(LOCATION_COLUMNS)
    if pl is not None:
        if rows:
            frame = pl.from_dicts(rows, infer_schema_length=None).select(columns)
        else:
            frame = pl.DataFrame({col: [] for col in columns})
        frame.write_parquet(out_path)
        return
    if rows:
        table = pa.Table.from_pylist(rows).select(columns)
    else:
        table = pa.table({col: pa.array([], type=pa.string()) for col in columns})
    pq.write_table(table, out_path)


def run_transform(settings: Settings | None = None) -> Path:
    """Run the full TRANSFORM stage and return the output Parquet path."""
    settings = settings or get_settings()
    _require_engine()

    cfg = settings.transform
    parquet_dir = settings.path("parquet")
    processed_dir = settings.path("processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    out_path = processed_dir / OUTPUT_FILENAME

    files = sorted(p for p in parquet_dir.glob("*.parquet") if p.is_file())
    if not files:
        log.warning(f"No parquet inputs found in {parquet_dir}; writing empty output")

    with StageTimer("transform") as timer:
        # ---- read ----------------------------------------------------------
        records: list[LocationRecord] = []
        for path in files:
            rows = _read_rows(path)
            records.extend(LocationRecord.from_row(row) for row in rows)
            log.debug(f"read {len(rows):,} rows from {path.name}")
        timer.add(len(records))
        log.info(f"loaded {len(records):,} records from {len(files)} parquet file(s)")

        # ---- enrich --------------------------------------------------------
        if cfg.compute_geometry:
            for rec in records:
                compute_geometry(rec)
        if cfg.normalize_names:
            for rec in records:
                normalize_record(rec, cfg.default_language)
        if cfg.generate_aliases:
            for rec in records:
                rec.aliases = generate_aliases(rec)
        if cfg.detect_duplicates:
            before = len(records)
            records = deduplicate(records, cfg.dedupe_distance_m)
            log.info(f"dedupe: {before:,} -> {len(records):,} ({before - len(records):,} merged)")

        build_hierarchy(records)

        # ---- report --------------------------------------------------------
        counts = Counter(rec.place_type.value for rec in records)
        for place_type, count in counts.most_common():
            log.info(f"  {place_type:<15} {count:>10,}")

        # ---- write ---------------------------------------------------------
        _write_rows([rec.to_row() for rec in records], out_path)
        log.info(f"wrote {len(records):,} records -> {out_path}")

    return out_path
