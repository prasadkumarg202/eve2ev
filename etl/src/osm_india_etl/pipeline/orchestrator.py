"""Pipeline orchestration: runs the ETL stages in order with checkpointing.

Every stage entrypoint is imported lazily so that a partially-built (or
uninstalled) sibling module never breaks importing the orchestrator itself.
A stage failure logs the error, persists the checkpoint, and re-raises —
the next ``run_pipeline(resume=True)`` picks up where the crash happened.
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import Any

from ..config import Settings, get_settings
from ..logging_setup import StageTimer, get_console, log
from .checkpoint import CheckpointStore

#: Canonical execution order of the ETL stages.
STAGE_ORDER: tuple[str, ...] = ("download", "extract", "transform", "load", "export")


def _load_stage_runner(stage: str) -> Callable[[Settings], Any]:
    """Lazily import and return the ``run_*`` entrypoint for *stage*.

    Raises:
        ValueError: if *stage* is not a known stage name.
        ImportError: if the stage module (or one of its heavy deps) is missing.
    """
    if stage == "download":
        from ..download import run_download

        return run_download
    if stage == "extract":
        from ..extract import run_extract

        return run_extract
    if stage == "transform":
        from ..transform import run_transform

        return run_transform
    if stage == "load":
        from ..load import run_load

        return run_load
    if stage == "export":
        from ..exporters import run_export

        return run_export
    raise ValueError(f"Unknown stage {stage!r}; expected one of {list(STAGE_ORDER)}")


def _summarize_result(result: Any) -> Any:
    """Coerce a stage's return value into JSON-serializable checkpoint stats."""
    if result is None:
        return None
    if isinstance(result, Path):
        return str(result)
    if isinstance(result, (list, tuple)):
        return {
            "count": len(result),
            "items": [_summarize_result(item) for item in result[:50]],
        }
    if isinstance(result, dict):
        return {str(k): _summarize_result(v) for k, v in result.items()}
    if isinstance(result, (str, int, float, bool)):
        return result
    return repr(result)


def run_pipeline(
    settings: Settings | None = None,
    stages: list[str] | None = None,
    resume: bool = True,
) -> None:
    """Run the requested ETL *stages* (all of them by default) in canonical order.

    Args:
        settings: Resolved settings; the cached singleton is used when ``None``.
        stages: Subset of :data:`STAGE_ORDER` to run. Order is normalized to
            the canonical order regardless of how the caller listed them.
        resume: When ``True``, stages the checkpoint already marks as done
            are skipped; when ``False`` everything requested is re-run.

    Raises:
        ValueError: on an unknown stage name.
        Exception: whatever the failing stage raised — after the checkpoint
            has been saved, so the run is resumable.
    """
    settings = settings or get_settings()
    settings.ensure_dirs()

    requested = list(stages) if stages else list(STAGE_ORDER)
    unknown = [s for s in requested if s not in STAGE_ORDER]
    if unknown:
        raise ValueError(f"Unknown stage(s) {unknown}; expected one of {list(STAGE_ORDER)}")
    ordered = [s for s in STAGE_ORDER if s in requested]

    store = CheckpointStore(settings)
    console = get_console()
    log.info(f"Pipeline starting | stages={ordered} | resume={resume}")

    for stage in ordered:
        if resume and store.is_stage_done(stage):
            log.info(f"Stage '{stage}' already complete — skipping (resume)")
            continue

        runner = _load_stage_runner(stage)

        # Record that this stage is now in flight, so a hard crash is visible.
        cp = store.load()
        cp.stage = stage
        store.save(cp)

        started = time.perf_counter()
        try:
            with console.status(f"[bold cyan]stage: {stage}[/bold cyan]"):
                with StageTimer(f"stage:{stage}"):
                    result = runner(settings)
        except Exception as exc:
            elapsed = time.perf_counter() - started
            log.error(f"Stage '{stage}' failed after {elapsed:.1f}s: {exc!r}")
            cp = store.load()
            cp.stats[stage] = {
                "status": "failed",
                "error": f"{type(exc).__name__}: {exc}",
                "duration_s": round(elapsed, 2),
            }
            store.save(cp)
            raise

        elapsed = time.perf_counter() - started
        cp = store.load()
        cp.stats[stage] = {
            "status": "ok",
            "duration_s": round(elapsed, 2),
            "result": _summarize_result(result),
        }
        store.save(cp)
        store.mark_stage_done(stage)

    log.success(f"Pipeline finished | stages={ordered}")


def rebuild(settings: Settings) -> None:
    """Wipe the checkpoint and re-run every stage from scratch."""
    store = CheckpointStore(settings)
    log.warning("Rebuild requested: resetting checkpoint and re-running all stages")
    store.reset()
    run_pipeline(settings=settings, stages=list(STAGE_ORDER), resume=False)


__all__ = ["run_pipeline", "rebuild", "STAGE_ORDER"]
