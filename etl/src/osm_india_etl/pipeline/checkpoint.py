"""Persistent pipeline checkpoint store for crash-safe, resumable runs.

State lives in ``<checkpoints_dir>/state.json`` and is written atomically
(temp file + ``os.replace``) so a crash mid-write can never corrupt it.
"""

from __future__ import annotations

import os
import tempfile

from ..config import Settings
from ..logging_setup import log
from ..models import Checkpoint


class CheckpointStore:
    """Loads, mutates, and atomically persists the pipeline :class:`Checkpoint`.

    The store keeps an in-memory copy of the checkpoint so repeated
    ``mark_*`` / ``is_*`` calls do not re-read the file; every mutation is
    flushed to disk immediately.
    """

    def __init__(self, settings: Settings) -> None:
        self.path = settings.path("checkpoints") / "state.json"
        self._checkpoint: Checkpoint | None = None

    # ------------------------------------------------------------------ #
    # Persistence
    # ------------------------------------------------------------------ #
    def load(self) -> Checkpoint:
        """Return the current checkpoint, reading it from disk on first use.

        A missing or corrupt state file yields a fresh :class:`Checkpoint`
        (corruption is logged, never fatal — the pipeline simply restarts).
        """
        if self._checkpoint is not None:
            return self._checkpoint
        if self.path.exists():
            try:
                self._checkpoint = Checkpoint.from_json(
                    self.path.read_text(encoding="utf-8")
                )
            except (ValueError, TypeError, KeyError) as exc:
                log.warning(
                    f"Corrupt checkpoint at {self.path} ({exc}); starting fresh"
                )
                self._checkpoint = Checkpoint()
        else:
            self._checkpoint = Checkpoint()
        return self._checkpoint

    def save(self, cp: Checkpoint) -> None:
        """Atomically persist *cp* (temp file in the same dir + rename)."""
        self._checkpoint = cp
        self.path.parent.mkdir(parents=True, exist_ok=True)
        fd, tmp_name = tempfile.mkstemp(
            dir=str(self.path.parent), prefix=".state-", suffix=".json.tmp"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                fh.write(cp.to_json())
                fh.flush()
                os.fsync(fh.fileno())
            os.replace(tmp_name, self.path)
        except BaseException:
            # Best-effort cleanup of the orphaned temp file, then re-raise.
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    def reset(self) -> None:
        """Discard all recorded progress (in memory and on disk)."""
        self._checkpoint = Checkpoint()
        try:
            self.path.unlink()
        except FileNotFoundError:
            pass
        self.save(self._checkpoint)

    # ------------------------------------------------------------------ #
    # Stage / file bookkeeping
    # ------------------------------------------------------------------ #
    def mark_stage_done(self, stage: str) -> None:
        """Record *stage* as completed and persist immediately."""
        cp = self.load()
        if stage not in cp.completed_stages:
            cp.completed_stages.append(stage)
        cp.stage = stage
        self.save(cp)

    def mark_file_done(self, fname: str) -> None:
        """Record *fname* as fully processed and persist immediately."""
        cp = self.load()
        if fname not in cp.completed_files:
            cp.completed_files.append(fname)
        self.save(cp)

    def is_stage_done(self, stage: str) -> bool:
        return stage in self.load().completed_stages

    def is_file_done(self, fname: str) -> bool:
        return fname in self.load().completed_files


__all__ = ["CheckpointStore"]
