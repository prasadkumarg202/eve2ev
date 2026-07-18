"""Convenience launcher: run the CLI without installing the package.

Usage: ``python main.py <command>`` (e.g. ``python main.py validate``).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from osm_india_etl.cli import app  # noqa: E402

if __name__ == "__main__":
    app()
