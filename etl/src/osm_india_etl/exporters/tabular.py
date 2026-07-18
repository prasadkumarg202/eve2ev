"""Tabular exporters: Parquet and CSV writers over the canonical locations file.

Both writers read the TRANSFORM stage output (``processed/locations.parquet``)
and re-emit it. Heavy dataframe libraries (polars / pyarrow) are optional and
import-guarded; :func:`to_parquet` degrades to a byte-for-byte copy when
neither is installed (the source is already Parquet).
"""

from __future__ import annotations

import shutil
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from ..logging_setup import log

__all__ = ["iter_parquet_rows", "to_csv", "to_parquet"]


def _try_import(name: str) -> Any | None:
    """Import an optional module, returning ``None`` when unavailable."""
    try:
        return __import__(name, fromlist=["_"])
    except ImportError:
        return None


def iter_parquet_rows(src: str | Path, batch_size: int = 10_000) -> Iterator[dict[str, Any]]:
    """Stream rows of a Parquet file as plain dicts.

    Prefers pyarrow (true batch streaming); falls back to polars.

    Raises:
        FileNotFoundError: if *src* does not exist.
        RuntimeError: if neither pyarrow nor polars is installed.
    """
    src = Path(src)
    if not src.exists():
        raise FileNotFoundError(f"Parquet file not found: {src}")

    pq = _try_import("pyarrow.parquet")
    if pq is not None:
        parquet_file = pq.ParquetFile(src)
        for batch in parquet_file.iter_batches(batch_size=batch_size):
            yield from batch.to_pylist()
        return

    pl = _try_import("polars")
    if pl is not None:
        yield from pl.read_parquet(src).iter_rows(named=True)
        return

    raise RuntimeError("Reading Parquet requires either 'pyarrow' or 'polars' to be installed")


def to_parquet(src_parquet: str | Path, dst: str | Path) -> Path:
    """Write the canonical locations Parquet file to *dst*.

    Uses polars (lazy sink) or pyarrow when available; otherwise copies the
    file verbatim, which is lossless because *src_parquet* is already Parquet.
    """
    src, dst = Path(src_parquet), Path(dst)
    if not src.exists():
        raise FileNotFoundError(f"Parquet file not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.resolve() == dst.resolve():
        return dst

    pl = _try_import("polars")
    if pl is not None:
        pl.scan_parquet(src).sink_parquet(dst)
        return dst

    pq = _try_import("pyarrow.parquet")
    if pq is not None:
        pq.write_table(pq.read_table(src), dst)
        return dst

    log.debug("polars/pyarrow unavailable; copying parquet verbatim -> {}", dst)
    shutil.copyfile(src, dst)
    return dst


def to_csv(src_parquet: str | Path, dst: str | Path, delimiter: str = ",") -> Path:
    """Convert the locations Parquet file to CSV at *dst*.

    Raises:
        RuntimeError: if neither polars nor pyarrow is installed.
    """
    src, dst = Path(src_parquet), Path(dst)
    if not src.exists():
        raise FileNotFoundError(f"Parquet file not found: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)

    pl = _try_import("polars")
    if pl is not None:
        pl.scan_parquet(src).sink_csv(dst, separator=delimiter)
        return dst

    pq = _try_import("pyarrow.parquet")
    pacsv = _try_import("pyarrow.csv")
    if pq is not None and pacsv is not None:
        table = pq.read_table(src)
        pacsv.write_csv(
            table,
            dst,
            write_options=pacsv.WriteOptions(include_header=True, delimiter=delimiter),
        )
        return dst

    raise RuntimeError("CSV export requires either 'polars' or 'pyarrow' to be installed")
