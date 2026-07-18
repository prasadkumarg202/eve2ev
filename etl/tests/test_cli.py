"""Tests for the CLI and the checkpoint store (spine deps only)."""

from __future__ import annotations

from pathlib import Path

import pytest

typer = pytest.importorskip("typer")

from typer.testing import CliRunner  # noqa: E402

from osm_india_etl.cli import app  # noqa: E402
from osm_india_etl.config import Settings  # noqa: E402
from osm_india_etl.models import Checkpoint  # noqa: E402
from osm_india_etl.pipeline import CheckpointStore  # noqa: E402

runner = CliRunner()


# --------------------------------------------------------------------------- #
# CLI
# --------------------------------------------------------------------------- #
def test_help_exits_cleanly() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "validate" in result.output
    assert "run" in result.output


def test_validate_succeeds_and_reports_dependencies() -> None:
    result = runner.invoke(app, ["validate"])
    assert result.exit_code == 0, result.output
    assert "Optional dependencies" in result.output
    # Every optional heavy dep should be listed, importable or not.
    for dep in ("osmium", "duckdb", "fastapi", "polars"):
        assert dep in result.output
    assert "Resolved paths" in result.output


# --------------------------------------------------------------------------- #
# CheckpointStore
# --------------------------------------------------------------------------- #
@pytest.fixture()
def store(tmp_path: Path) -> CheckpointStore:
    settings = Settings(root=tmp_path)
    return CheckpointStore(settings)


def test_load_returns_fresh_checkpoint_when_missing(store: CheckpointStore) -> None:
    cp = store.load()
    assert cp.stage == "init"
    assert cp.completed_stages == []
    assert cp.completed_files == []


def test_mark_save_load_round_trip(store: CheckpointStore, tmp_path: Path) -> None:
    store.mark_stage_done("download")
    store.mark_file_done("india-latest.osm.pbf")
    cp = store.load()
    cp.stats["download"] = {"status": "ok", "duration_s": 1.5}
    store.save(cp)

    assert store.path == tmp_path / "checkpoints" / "state.json"
    assert store.path.exists()

    # A brand-new store must see the same persisted state.
    reloaded = CheckpointStore(Settings(root=tmp_path)).load()
    assert reloaded.stage == "download"
    assert reloaded.completed_stages == ["download"]
    assert reloaded.completed_files == ["india-latest.osm.pbf"]
    assert reloaded.stats["download"]["status"] == "ok"

    fresh_store = CheckpointStore(Settings(root=tmp_path))
    assert fresh_store.is_stage_done("download")
    assert not fresh_store.is_stage_done("extract")
    assert fresh_store.is_file_done("india-latest.osm.pbf")
    assert not fresh_store.is_file_done("other.osm.pbf")


def test_marking_is_idempotent(store: CheckpointStore) -> None:
    store.mark_stage_done("extract")
    store.mark_stage_done("extract")
    store.mark_file_done("a.pbf")
    store.mark_file_done("a.pbf")
    cp = store.load()
    assert cp.completed_stages == ["extract"]
    assert cp.completed_files == ["a.pbf"]


def test_reset_clears_state(store: CheckpointStore, tmp_path: Path) -> None:
    store.mark_stage_done("download")
    store.reset()
    cp = store.load()
    assert cp.completed_stages == []
    assert cp.stage == "init"
    # Reset persists a fresh checkpoint on disk too.
    reloaded = CheckpointStore(Settings(root=tmp_path)).load()
    assert reloaded.completed_stages == []


def test_corrupt_state_file_recovers(store: CheckpointStore) -> None:
    store.path.parent.mkdir(parents=True, exist_ok=True)
    store.path.write_text("{not json", encoding="utf-8")
    cp = store.load()
    assert isinstance(cp, Checkpoint)
    assert cp.completed_stages == []
