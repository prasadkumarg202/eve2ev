"""Central logging: Loguru sink + Rich console, plus a progress/metrics helper.

Usage:
    from osm_india_etl.logging_setup import setup_logging, get_console, StageTimer
    setup_logging()
    log.info("hello")
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any

from loguru import logger as log
from rich.console import Console

_console = Console()
_configured = False


def get_console() -> Console:
    return _console


def setup_logging(
    log_dir: str | Path = "logs",
    level: str = "INFO",
    *,
    rich: bool = True,
    filename: str = "etl.log",
) -> Any:
    """Configure Loguru with a Rich-formatted stderr sink + rotating file sink."""
    global _configured
    if _configured:
        return log

    log.remove()

    if rich:
        log.add(
            lambda msg: _console.print(msg, end="", markup=False, highlight=False),
            level=level,
            format=(
                "<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | "
                "<cyan>{name}:{function}:{line}</cyan> - <level>{message}</level>"
            ),
            colorize=True,
        )
    else:
        log.add(sys.stderr, level=level)

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)
    log.add(
        log_path / filename,
        level="DEBUG",
        rotation="100 MB",
        retention="14 days",
        compression="zip",
        enqueue=True,
        backtrace=True,
        diagnose=False,
        format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    )

    _configured = True
    return log


class StageTimer:
    """Context manager that logs duration, rows/s, and resource use for a stage."""

    def __init__(self, name: str, *, total: int | None = None) -> None:
        self.name = name
        self.total = total
        self.rows = 0
        self._start = 0.0

    def __enter__(self) -> StageTimer:
        self._start = time.perf_counter()
        log.info(f"▶ {self.name} started")
        return self

    def add(self, n: int = 1) -> None:
        self.rows += n

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        elapsed = max(time.perf_counter() - self._start, 1e-9)
        rate = self.rows / elapsed
        mem = _memory_mb()
        if exc_type is None:
            log.success(
                f"✔ {self.name} done in {elapsed:.1f}s "
                f"| rows={self.rows:,} | {rate:,.0f} rows/s | mem={mem:.0f}MB"
            )
        else:
            log.error(f"✖ {self.name} failed after {elapsed:.1f}s: {exc}")


def _memory_mb() -> float:
    try:
        import psutil

        return psutil.Process().memory_info().rss / (1024 * 1024)
    except Exception:  # pragma: no cover
        return 0.0


__all__ = ["log", "setup_logging", "get_console", "StageTimer"]
