"""Typer CLI for the OSM India ETL.

All stage entrypoints (and their heavy dependencies) are imported lazily
inside command bodies, so the CLI itself imports with only the spine deps
(pyyaml, pydantic, loguru, rich, typer) installed.
"""

from __future__ import annotations

import importlib
from pathlib import Path
from typing import Any

import typer
from rich.table import Table

from .config import Settings, load_settings
from .logging_setup import get_console, log, setup_logging

app = typer.Typer(
    name="osm-india-etl",
    help="Download, process, and load OpenStreetMap data for India.",
    no_args_is_help=True,
    pretty_exceptions_show_locals=False,
)

#: Optional heavy dependencies reported by ``validate``.
OPTIONAL_DEPS: tuple[str, ...] = (
    "osmium",
    "geopandas",
    "shapely",
    "duckdb",
    "psycopg",
    "fastapi",
    "polars",
    "rapidfuzz",
)


# --------------------------------------------------------------------------- #
# Global options
# --------------------------------------------------------------------------- #
@app.callback()
def main(
    ctx: typer.Context,
    config: Path | None = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to config YAML (default: config/config.yaml).",
        exists=False,
        dir_okay=False,
    ),
    log_level: str | None = typer.Option(
        None,
        "--log-level",
        "-l",
        help="Log level (DEBUG/INFO/WARNING/ERROR); default from config.",
    ),
) -> None:
    """Resolve settings, configure logging, and stash Settings on the context."""
    try:
        settings = load_settings(config)
    except Exception as exc:  # config errors should be readable, not tracebacks
        typer.secho(f"Failed to load config: {exc}", fg=typer.colors.RED, err=True)
        raise typer.Exit(code=2) from exc
    level = (log_level or settings.runtime.log_level).upper()
    setup_logging(log_dir=settings.path("logs"), level=level, rich=settings.runtime.rich_progress)
    ctx.obj = settings


def _settings(ctx: typer.Context) -> Settings:
    assert isinstance(ctx.obj, Settings), "callback must have stored Settings"
    return ctx.obj


def _missing_extras(name: str, exc: ImportError) -> typer.Exit:
    typer.secho(
        f"The '{name}' command needs optional dependencies that are not installed "
        f"({exc}). Install the project extras, e.g.:  pip install -e .",
        fg=typer.colors.RED,
        err=True,
    )
    return typer.Exit(code=1)


def _check_marks() -> tuple[str, str]:
    """Return (ok, fail) marks: ✓/✗ where the console encoding allows, else ASCII."""
    encoding = getattr(get_console().file, "encoding", None)
    if encoding:
        try:
            "✓✗".encode(encoding)
        except (UnicodeEncodeError, LookupError):
            return "OK", "X"
    return "✓", "✗"


def _print_paths_summary(title: str, paths: list[Path]) -> None:
    table = Table(title=title, show_lines=False)
    table.add_column("#", justify="right", style="dim")
    table.add_column("File", style="cyan")
    for i, p in enumerate(paths, 1):
        table.add_row(str(i), str(p))
    get_console().print(table)


def _print_dict_summary(title: str, stats: dict[str, Any]) -> None:
    table = Table(title=title, show_lines=False)
    table.add_column("Key", style="cyan")
    table.add_column("Value")
    for key, value in stats.items():
        table.add_row(key, str(value))
    get_console().print(table)


# --------------------------------------------------------------------------- #
# Individual stage commands
# --------------------------------------------------------------------------- #
@app.command()
def download(ctx: typer.Context) -> None:
    """Download OSM .pbf extracts for India."""
    try:
        from .download import run_download
    except ImportError as exc:
        raise _missing_extras("download", exc) from exc
    files = run_download(_settings(ctx))
    _print_paths_summary(f"Downloaded {len(files)} file(s)", list(files))


@app.command()
def extract(ctx: typer.Context) -> None:
    """Extract location entities from downloaded .pbf files."""
    try:
        from .extract import run_extract
    except ImportError as exc:
        raise _missing_extras("extract", exc) from exc
    files = run_extract(_settings(ctx))
    _print_paths_summary(f"Extracted {len(files)} output file(s)", list(files))


@app.command()
def transform(ctx: typer.Context) -> None:
    """Normalize, dedupe, and enrich extracted records."""
    try:
        from .transform import run_transform
    except ImportError as exc:
        raise _missing_extras("transform", exc) from exc
    out = run_transform(_settings(ctx))
    _print_dict_summary("Transform complete", {"output": str(out)})


@app.command()
def load(ctx: typer.Context) -> None:
    """Load transformed records into the target database(s)."""
    try:
        from .load import run_load
    except ImportError as exc:
        raise _missing_extras("load", exc) from exc
    stats = run_load(_settings(ctx))
    _print_dict_summary("Load complete", dict(stats))


@app.command()
def export(ctx: typer.Context) -> None:
    """Export final datasets (parquet/csv/geojson/sqlite/duckdb)."""
    try:
        from .exporters import run_export
    except ImportError as exc:
        raise _missing_extras("export", exc) from exc
    stats = run_export(_settings(ctx))
    _print_dict_summary("Export complete", dict(stats))


# --------------------------------------------------------------------------- #
# Pipeline commands
# --------------------------------------------------------------------------- #
@app.command("run")
def run_cmd(
    ctx: typer.Context,
    stage: list[str] = typer.Option(
        [],
        "--stage",
        "-s",
        help="Run only this stage (repeatable). Default: all stages.",
    ),
    no_resume: bool = typer.Option(
        False,
        "--no-resume",
        help="Ignore the checkpoint and re-run requested stages.",
    ),
) -> None:
    """Run the full pipeline (download, extract, transform, load, export)."""
    from .pipeline.orchestrator import run_pipeline

    try:
        run_pipeline(
            settings=_settings(ctx),
            stages=list(stage) or None,
            resume=not no_resume,
        )
    except ImportError as exc:
        raise _missing_extras("run", exc) from exc
    _print_dict_summary(
        "Pipeline finished",
        {"stages": ", ".join(stage) if stage else "all", "resume": not no_resume},
    )


@app.command()
def rebuild(ctx: typer.Context) -> None:
    """Reset the checkpoint and rebuild everything from scratch."""
    from .pipeline.orchestrator import rebuild as run_rebuild

    try:
        run_rebuild(_settings(ctx))
    except ImportError as exc:
        raise _missing_extras("rebuild", exc) from exc
    _print_dict_summary("Rebuild finished", {"resume": False, "checkpoint": "reset"})


# --------------------------------------------------------------------------- #
# Diagnostics
# --------------------------------------------------------------------------- #
@app.command()
def validate(ctx: typer.Context) -> None:
    """Validate config, directories, schema, and optional dependencies."""
    settings = _settings(ctx)
    console = get_console()
    problems: list[str] = []

    # 1. Config + directories.
    try:
        settings.ensure_dirs()
        console.print("[green]OK[/green] config loaded and directories ensured")
    except Exception as exc:
        problems.append(f"directories: {exc}")
        console.print(f"[red]FAIL[/red] directory creation: {exc}")

    # 2. LocationRecord schema.
    try:
        from .models import validate_schema

        validate_schema()
        console.print("[green]OK[/green] LocationRecord schema matches LOCATION_COLUMNS")
    except Exception as exc:
        problems.append(f"schema: {exc}")
        console.print(f"[red]FAIL[/red] schema validation: {exc}")

    # 3. Optional heavy dependencies (never fatal).
    dep_table = Table(title="Optional dependencies")
    dep_table.add_column("Package", style="cyan")
    dep_table.add_column("Importable", justify="center")
    dep_table.add_column("Version")
    ok_mark, fail_mark = _check_marks()
    for name in OPTIONAL_DEPS:
        try:
            module = importlib.import_module(name)
            version = str(getattr(module, "__version__", "?"))
            dep_table.add_row(name, f"[green]{ok_mark}[/green]", version)
        except Exception as exc:  # noqa: BLE001 - report anything, crash never
            dep_table.add_row(name, f"[red]{fail_mark}[/red]", f"{type(exc).__name__}")
    console.print(dep_table)

    # 4. Resolved paths + DB targets.
    path_table = Table(title="Resolved paths and database targets")
    path_table.add_column("Key", style="cyan")
    path_table.add_column("Value")
    for key in type(settings.paths).model_fields:
        path_table.add_row(f"paths.{key}", str(settings.path(key)))
    db = settings.database
    path_table.add_row("db.postgres", f"{db.user}@{db.host}:{db.port}/{db.name} ({db.schema_})")
    path_table.add_row("db.sqlite", str((settings.root / db.sqlite_path).resolve()))
    path_table.add_row("db.duckdb", str((settings.root / db.duckdb_path).resolve()))
    path_table.add_row("api", f"{settings.api.host}:{settings.api.port} ({settings.api.backend})")
    console.print(path_table)

    if problems:
        typer.secho(f"Validation found {len(problems)} problem(s).", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    typer.secho("Validation passed.", fg=typer.colors.GREEN)


@app.command()
def serve(
    ctx: typer.Context,
    host: str | None = typer.Option(None, "--host", help="Bind host (default from config)."),
    port: int | None = typer.Option(None, "--port", help="Bind port (default from config)."),
) -> None:
    """Serve the location API with uvicorn."""
    settings = _settings(ctx)
    try:
        import uvicorn
    except ImportError as exc:
        raise _missing_extras("serve (uvicorn)", exc) from exc
    try:
        from .api.app import create_app
    except ImportError as exc:
        raise _missing_extras("serve (fastapi)", exc) from exc

    application = create_app()
    bind_host = host or settings.api.host
    bind_port = port or settings.api.port
    log.info(f"Serving API on http://{bind_host}:{bind_port}")
    uvicorn.run(application, host=bind_host, port=bind_port)


@app.command()
def search(
    ctx: typer.Context,
    query: str = typer.Argument(..., help="Free-text location query."),
    limit: int = typer.Option(10, "--limit", "-n", help="Max results to show."),
) -> None:
    """Search the built location index (manual sanity check)."""
    settings = _settings(ctx)
    try:
        from .search.engine import SearchEngine
    except ImportError as exc:
        raise _missing_extras("search", exc) from exc

    engine = SearchEngine(settings)
    results = engine.search(query, limit=limit)

    table = Table(title=f"Results for {query!r}")
    table.add_column("#", justify="right", style="dim")
    table.add_column("Name", style="cyan")
    table.add_column("Type")
    table.add_column("State")
    table.add_column("Score", justify="right")
    for i, item in enumerate(results, 1):
        row = item if isinstance(item, dict) else getattr(item, "__dict__", {})
        table.add_row(
            str(i),
            str(row.get("name", row.get("name_title", "?"))),
            str(row.get("place_type", "?")),
            str(row.get("state_name", "") or ""),
            f"{row.get('score', 0.0):.2f}" if row.get("score") is not None else "-",
        )
    get_console().print(table)
    if not results:
        typer.secho("No results.", fg=typer.colors.YELLOW)


if __name__ == "__main__":
    app()
