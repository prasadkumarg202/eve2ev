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
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from osm_india_etl.config import Settings, get_settings
from osm_india_etl.constants import LOCATION_COLUMNS
from osm_india_etl.logging_setup import StageTimer, log
from osm_india_etl.models import LocationRecord

from .aliases import generate_aliases
from .dedupe import deduplicate
from .geometry import compute_geometry
from .hierarchy import HierarchyResolver, build_hierarchy, is_parent_candidate
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

#: Input size above which TRANSFORM switches to the streaming implementation.
#: One zone (~70 MB parquet) fits in RAM; several do not.
STREAMING_THRESHOLD_BYTES = 150 * 1024 * 1024


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


def _iter_row_batches(path: Path, batch_size: int) -> Iterator[list[dict[str, Any]]]:
    """Yield row dicts from a Parquet file in bounded batches.

    Uses PyArrow's batch reader so a multi-GB file is never materialised;
    falls back to Polars slicing when PyArrow is unavailable.
    """
    if pq is not None:
        parquet_file = pq.ParquetFile(path)
        for batch in parquet_file.iter_batches(batch_size=batch_size):
            yield batch.to_pylist()
        return
    frame = pl.read_parquet(path)
    for start in range(0, frame.height, batch_size):
        yield frame.slice(start, batch_size).to_dicts()


def _enrich(rec: LocationRecord, cfg: Any) -> None:
    """Per-record enrichment shared by both transform strategies."""
    if cfg.compute_geometry:
        compute_geometry(rec)
    if cfg.normalize_names:
        normalize_record(rec, cfg.default_language)
    if cfg.generate_aliases:
        rec.aliases = generate_aliases(rec)


def run_transform_streaming(
    settings: Settings,
    files: list[Path],
    out_path: Path,
    # 25k measured at ~500 MB peak with no throughput penalty versus 100k
    # (~1 GB); larger batches buy nothing but memory pressure here.
    batch_size: int = 25_000,
) -> Path:
    """Memory-bounded TRANSFORM for datasets too large to hold in RAM.

    Two passes over the per-zone Parquet:

    1. Collect only *parent candidates* (admin areas — see
       :func:`is_parent_candidate`). These are a tiny fraction of a typical
       extract (~6k of 314k for the north-eastern zone), so they fit
       comfortably in memory. They are enriched, deduped, and linked to each
       other exactly as before.
    2. Stream every remaining record in batches, enrich it, attach ancestry
       from the pre-built resolver, and append it straight to the output.

    Peak memory is therefore ``parents + one batch`` rather than the entire
    dataset. The in-memory path (:func:`run_transform`) stays the default for
    small inputs because it can dedupe globally across all tiers.
    """
    if pq is None:
        raise RuntimeError("streaming transform requires pyarrow")

    cfg = settings.transform
    from ..extract import ParquetBatchWriter  # local import: avoids a cycle

    # ---- pass 1: parent candidates only --------------------------------
    parents: list[LocationRecord] = []
    for path in files:
        for rows in _iter_row_batches(path, batch_size):
            for row in rows:
                rec = LocationRecord.from_row(row)
                if is_parent_candidate(rec):
                    parents.append(rec)
    log.info(f"streaming: {len(parents):,} parent candidates held in memory")

    for rec in parents:
        _enrich(rec, cfg)
    if cfg.detect_duplicates:
        before = len(parents)
        parents = deduplicate(parents, cfg.dedupe_distance_m)
        log.info(f"dedupe (parents): {before:,} -> {len(parents):,}")

    build_hierarchy(parents)
    resolver = HierarchyResolver(parents)
    parent_ids = {p.location_id for p in parents}

    # ---- pass 2: stream everything, writing as we go -------------------
    counts: Counter[str] = Counter()
    written = 0
    with ParquetBatchWriter(out_path, batch_size) as writer:
        for rec in parents:  # already fully resolved
            writer.add(rec.to_row())
            counts[rec.place_type.value] += 1
            written += 1

        for path in files:
            for rows in _iter_row_batches(path, batch_size):
                for row in rows:
                    rec = LocationRecord.from_row(row)
                    if rec.location_id in parent_ids:
                        continue  # emitted above
                    if is_parent_candidate(rec):
                        continue  # dropped as a duplicate in pass 1
                    _enrich(rec, cfg)
                    resolver.attach(rec)
                    writer.add(rec.to_row())
                    counts[rec.place_type.value] += 1
                    written += 1

    for place_type, count in counts.most_common():
        log.info(f"  {place_type:<15} {count:>10,}")
    log.info(f"wrote {written:,} records -> {out_path}")
    return out_path


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

    # The in-memory path peaked at ~2 GB for a single 315k-record zone, so
    # all-India (~15x) would exhaust most machines. Switch to the streaming
    # implementation once the input is large enough to matter.
    total_bytes = sum(p.stat().st_size for p in files)
    streaming = getattr(cfg, "streaming", None)
    if streaming is None:
        streaming = total_bytes > STREAMING_THRESHOLD_BYTES
    if streaming and pq is not None and files:
        log.info(
            f"transform: streaming mode "
            f"({total_bytes / 1_048_576:.0f} MB input across {len(files)} file(s))"
        )
        with StageTimer("transform") as timer:
            result = run_transform_streaming(settings, files, out_path)
            timer.add(1)
        return result

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
