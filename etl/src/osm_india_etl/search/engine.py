"""Layered location search engine over the loaded ETL database.

Query strategy (sqlite backend, the default):

1. **FTS5** exact/prefix match on ``locations_fts`` (name, search_name, aliases)
2. **Fuzzy rerank** of the candidates via rapidfuzz (difflib fallback)
3. **Trigram-ish LIKE** fallback when FTS yields nothing
4. **Phonetic** (metaphone/soundex) fallback scan when hits are scarce

DuckDB and PostGIS backends are supported with analogous SQL (guarded
imports); sqlite is fully functional with only the standard library.
"""

from __future__ import annotations

import math
import sqlite3
from typing import Any

from ..config import Settings, get_settings
from ..constants import ENTITY_TABLES, TYPE_RANK, PlaceType
from ..logging_setup import log
from . import fts as fts_helpers
from . import fuzzy, phonetic

__all__ = ["SearchEngine", "haversine_km"]

_EARTH_RADIUS_KM = 6371.0088

# Columns returned to API consumers.
_RESULT_COLUMNS = (
    "location_id",
    "name",
    "place_type",
    "latitude",
    "longitude",
    "pincode",
    "state_name",
    "district_name",
)
_SELECT_COLS = ", ".join(f"l.{c}" for c in _RESULT_COLUMNS) + ", l.search_name"

# Upper bound for the phonetic full-scan fallback (protects huge DBs).
_PHONETIC_SCAN_CAP = 20_000
# How many FTS candidates to pull before fuzzy reranking.
_CANDIDATE_MULTIPLIER = 5


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """Great-circle distance between two WGS84 points, in kilometres."""
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlmb = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlmb / 2) ** 2
    return 2 * _EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def _type_rank(place_type: str | None) -> int:
    """Hierarchy rank for a place_type string (higher = smaller tier)."""
    try:
        return TYPE_RANK.get(PlaceType(place_type), 100) if place_type else 100
    except ValueError:
        return 100


class SearchEngine:
    """Layered search over the ETL-produced location database."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()
        self.backend = (self.settings.api.backend or "sqlite").lower()
        self._conn: Any = None
        self._sa_engine: Any = None
        self._fts_available = False
        self._fts_has_location_id = False
        self._connect()

    # ------------------------------------------------------------------ #
    # Connection / dialect plumbing
    # ------------------------------------------------------------------ #
    def _connect(self) -> None:
        db = self.settings.database
        if self.backend == "sqlite":
            path = str((self.settings.root / db.sqlite_path).resolve())
            self._conn = sqlite3.connect(path, check_same_thread=False)
            self._conn.row_factory = sqlite3.Row
            self._probe_fts()
            log.debug(f"SearchEngine connected to sqlite at {path} (fts={self._fts_available})")
        elif self.backend == "duckdb":
            try:
                import duckdb
            except ImportError as exc:  # pragma: no cover - optional backend
                raise RuntimeError(
                    "backend 'duckdb' configured but the duckdb package is not installed"
                ) from exc
            path = str((self.settings.root / db.duckdb_path).resolve())
            self._conn = duckdb.connect(path, read_only=True)
            log.debug(f"SearchEngine connected to duckdb at {path}")
        elif self.backend == "postgis":
            try:
                from sqlalchemy import create_engine
            except ImportError as exc:  # pragma: no cover - optional backend
                raise RuntimeError(
                    "backend 'postgis' configured but sqlalchemy is not installed"
                ) from exc
            self._sa_engine = create_engine(db.sqlalchemy_url, pool_pre_ping=True)
            log.debug("SearchEngine connected to postgis")
        else:
            raise ValueError(f"Unknown api.backend: {self.backend!r}")

    def _probe_fts(self) -> None:
        """Detect the FTS5 table and whether it carries a location_id column."""
        try:
            row = self._conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='locations_fts'"
            ).fetchone()
            self._fts_available = row is not None
            if self._fts_available:
                cols = [r["name"] for r in self._conn.execute("PRAGMA table_info(locations_fts)")]
                self._fts_has_location_id = "location_id" in cols
        except sqlite3.Error:  # pragma: no cover - defensive
            self._fts_available = False

    def _execute(self, sql: str, params: list[Any] | tuple[Any, ...] = ()) -> list[dict[str, Any]]:
        """Run a query and return rows as plain dicts (all backends)."""
        if self.backend == "sqlite":
            cur = self._conn.execute(sql, tuple(params))
            return [dict(r) for r in cur.fetchall()]
        if self.backend == "duckdb":
            cur = self._conn.execute(sql, list(params))
            cols = [d[0] for d in cur.description]
            return [dict(zip(cols, row)) for row in cur.fetchall()]
        # postgis via sqlalchemy: translate '?' to named binds.
        from sqlalchemy import text

        named_sql, bind = _qmark_to_named(sql, list(params))
        with self._sa_engine.connect() as conn:
            result = conn.execute(text(named_sql), bind)
            return [dict(m) for m in result.mappings().all()]

    def close(self) -> None:
        """Release the underlying connection(s)."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None
        if self._sa_engine is not None:
            self._sa_engine.dispose()
            self._sa_engine = None

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def search(self, q: str, place_type: str | None = None, limit: int = 20) -> list[dict]:
        """Layered search: FTS prefix -> fuzzy rerank -> phonetic fallback."""
        q = (q or "").strip()
        if not q:
            return []
        fetch = max(limit * _CANDIDATE_MULTIPLIER, limit)
        candidates = self._fts_candidates(q, place_type, fetch)
        if not candidates and self.settings.search.trigram:
            candidates = self._like_candidates(q, place_type, fetch)
        results = self._rerank(q, candidates)
        if len(results) < min(3, limit) and self.settings.search.phonetic:
            extra = self._phonetic_candidates(q, place_type, fetch)
            results = self._rerank(q, candidates + extra, phonetic_boost=q)
        return results[:limit]

    def autocomplete(self, prefix: str, limit: int | None = None) -> list[dict]:
        """Fast prefix completion on ``search_name``."""
        prefix = (prefix or "").strip().lower()
        limit = limit or self.settings.search.autocomplete_limit
        if not prefix:
            return []
        rows: list[dict[str, Any]] = []
        if self.backend == "sqlite" and self._fts_available and self.settings.search.fts:
            match = fts_helpers.fts_prefix_query(prefix)
            if match:
                try:
                    rows = self._execute(
                        f"SELECT {_SELECT_COLS} FROM locations_fts f "
                        f"JOIN locations l ON {self._fts_join_on()} "
                        "WHERE f MATCH ? LIMIT ?",
                        [match, limit],
                    )
                except sqlite3.OperationalError as exc:  # pragma: no cover - defensive
                    log.warning(f"FTS autocomplete failed, falling back to LIKE: {exc}")
        if not rows:
            like_op = "ILIKE" if self.backend == "postgis" else "LIKE"
            pattern = fts_helpers.like_pattern(prefix, prefix_only=True)
            rows = self._execute(
                f"SELECT {_SELECT_COLS} FROM locations l "
                f"WHERE l.search_name {like_op} ? ESCAPE '\\' OR l.name_lower {like_op} ? ESCAPE '\\' "
                "ORDER BY length(l.search_name) LIMIT ?",
                [pattern, pattern, limit],
            )
        out = [self._row_to_result(r) for r in rows]
        out.sort(key=lambda r: (len(r["name"]), r["name"]))
        return out[:limit]

    def reverse_geocode(self, lat: float, lng: float) -> dict | None:
        """Nearest location, preferring smaller (more specific) admin tiers."""
        for delta in (0.02, 0.05, 0.1, 0.25, 0.5, 1.0):
            rows = self._bbox_rows(lat, lng, delta, None)
            if rows:
                scored = self._with_distance(rows, lat, lng)
                # Prefer the more specific tier among near-equidistant hits:
                # bucket distance to 250 m, then higher TYPE_RANK wins.
                scored.sort(
                    key=lambda r: (round(r["distance_km"] * 4) / 4, -_type_rank(r["place_type"]))
                )
                return scored[0]
        return None

    def nearby(
        self,
        lat: float,
        lng: float,
        radius_km: float = 5.0,
        place_type: str | None = None,
        limit: int = 50,
    ) -> list[dict]:
        """All locations within ``radius_km``, sorted by distance ascending."""
        lat_delta = radius_km / 111.32
        lng_delta = radius_km / (111.32 * max(math.cos(math.radians(lat)), 0.01))
        rows = self._bbox_rows(lat, lng, max(lat_delta, lng_delta), place_type)
        scored = self._with_distance(rows, lat, lng)
        scored = [r for r in scored if r["distance_km"] <= radius_km]
        scored.sort(key=lambda r: r["distance_km"])
        return scored[:limit]

    def list_by_type(
        self,
        table: str,
        limit: int = 100,
        offset: int = 0,
        parent_id: str | None = None,
    ) -> list[dict]:
        """Paginated listing of one tier table (states, districts, ...)."""
        if table not in ENTITY_TABLES and table != "locations":
            raise ValueError(f"Unknown entity table: {table!r}")
        where, params = "", []
        if parent_id:
            where = "WHERE l.parent_id = ?"
            params.append(parent_id)
        params += [limit, offset]
        try:
            rows = self._execute(
                f"SELECT {_SELECT_COLS} FROM {table} l {where} "
                "ORDER BY l.name LIMIT ? OFFSET ?",
                params,
            )
        except Exception as exc:
            # Tier table may not have been materialized: fall back to the
            # unified locations table filtered by the tier's place types.
            if not _is_missing_table_error(exc):
                raise
            types = [pt.value for pt, tbl in _type_to_table_items() if tbl == table]
            if not types:
                return []
            marks = ", ".join("?" for _ in types)
            filt = f"l.place_type IN ({marks})"
            if parent_id:
                filt += " AND l.parent_id = ?"
            rows = self._execute(
                f"SELECT {_SELECT_COLS} FROM locations l WHERE {filt} "
                "ORDER BY l.name LIMIT ? OFFSET ?",
                [*types, *([parent_id] if parent_id else []), limit, offset],
            )
        return [self._row_to_result(r) for r in rows]

    # ------------------------------------------------------------------ #
    # Candidate generation
    # ------------------------------------------------------------------ #
    def _fts_join_on(self) -> str:
        return "l.location_id = f.location_id" if self._fts_has_location_id else "l.rowid = f.rowid"

    def _fts_candidates(self, q: str, place_type: str | None, fetch: int) -> list[dict[str, Any]]:
        if not (self.backend == "sqlite" and self._fts_available and self.settings.search.fts):
            return self._like_candidates(q, place_type, fetch)
        match = fts_helpers.fts_prefix_query(q)
        if not match:
            return []
        type_sql, params = self._type_filter(place_type)
        try:
            return self._execute(
                f"SELECT {_SELECT_COLS} FROM locations_fts f "
                f"JOIN locations l ON {self._fts_join_on()} "
                f"WHERE f MATCH ?{type_sql} LIMIT ?",
                [match, *params, fetch],
            )
        except sqlite3.OperationalError as exc:
            log.warning(f"FTS query failed ({exc}); using LIKE fallback")
            return self._like_candidates(q, place_type, fetch)

    def _like_candidates(self, q: str, place_type: str | None, fetch: int) -> list[dict[str, Any]]:
        like_op = "ILIKE" if self.backend == "postgis" else "LIKE"
        pattern = fts_helpers.like_pattern(q.lower())
        type_sql, params = self._type_filter(place_type)
        rows = self._execute(
            f"SELECT {_SELECT_COLS} FROM locations l "
            f"WHERE (l.search_name {like_op} ? ESCAPE '\\' "
            f"OR l.name_lower {like_op} ? ESCAPE '\\'){type_sql} LIMIT ?",
            [pattern, pattern, *params, fetch],
        )
        if rows or not self.settings.search.trigram:
            return rows
        # Trigram-ish recall pass (reranked by the caller).
        clause, tri_params = fts_helpers.trigram_like_clauses(q.lower(), "l.search_name")
        if not clause:
            return []
        return self._execute(
            f"SELECT {_SELECT_COLS} FROM locations l WHERE {clause}{type_sql} LIMIT ?",
            [*tri_params, *params, fetch],
        )

    def _phonetic_candidates(self, q: str, place_type: str | None, fetch: int) -> list[dict[str, Any]]:
        """Scan (bounded) for rows whose name shares a phonetic code with q."""
        code = phonetic.metaphone(q)
        if not code:
            return []
        type_sql, params = self._type_filter(place_type)
        rows = self._execute(
            f"SELECT {_SELECT_COLS} FROM locations l WHERE 1=1{type_sql} LIMIT ?",
            [*params, _PHONETIC_SCAN_CAP],
        )
        hits = [r for r in rows if phonetic.phonetic_equal(q, r.get("name") or "")][:fetch]
        return hits

    def _type_filter(self, place_type: str | None) -> tuple[str, list[Any]]:
        if not place_type:
            return "", []
        return " AND l.place_type = ?", [place_type.strip().lower()]

    # ------------------------------------------------------------------ #
    # Scoring / shaping
    # ------------------------------------------------------------------ #
    def _rerank(
        self,
        q: str,
        rows: list[dict[str, Any]],
        phonetic_boost: str | None = None,
    ) -> list[dict]:
        seen: set[str] = set()
        out: list[dict] = []
        for row in rows:
            loc_id = str(row.get("location_id") or "")
            if loc_id in seen:
                continue
            seen.add(loc_id)
            name = row.get("name") or ""
            best = max(
                fuzzy.score(q, name),
                fuzzy.score(q, row.get("search_name") or ""),
            )
            if phonetic_boost and best < 60 and phonetic.phonetic_equal(phonetic_boost, name):
                best = max(best, 60.0)
            result = self._row_to_result(row)
            result["score"] = round(best, 2)
            out.append(result)
        out.sort(key=lambda r: r["score"], reverse=True)
        return out

    def _bbox_rows(
        self, lat: float, lng: float, delta: float, place_type: str | None
    ) -> list[dict[str, Any]]:
        type_sql, params = self._type_filter(place_type)
        return self._execute(
            f"SELECT {_SELECT_COLS} FROM locations l "
            "WHERE l.latitude BETWEEN ? AND ? AND l.longitude BETWEEN ? AND ?"
            f"{type_sql} LIMIT 5000",
            [lat - delta, lat + delta, lng - delta, lng + delta, *params],
        )

    def _with_distance(
        self, rows: list[dict[str, Any]], lat: float, lng: float
    ) -> list[dict]:
        out = []
        for row in rows:
            rlat, rlng = row.get("latitude"), row.get("longitude")
            if rlat is None or rlng is None:
                continue
            result = self._row_to_result(row)
            result["distance_km"] = round(haversine_km(lat, lng, float(rlat), float(rlng)), 4)
            out.append(result)
        return out

    @staticmethod
    def _row_to_result(row: dict[str, Any]) -> dict:
        return {col: row.get(col) for col in _RESULT_COLUMNS}


# --------------------------------------------------------------------------- #
# Small internal helpers
# --------------------------------------------------------------------------- #
def _qmark_to_named(sql: str, params: list[Any]) -> tuple[str, dict[str, Any]]:
    """Convert '?' placeholders to named binds for SQLAlchemy text()."""
    out: list[str] = []
    bind: dict[str, Any] = {}
    idx = 0
    for ch in sql:
        if ch == "?":
            key = f"p{idx}"
            out.append(f":{key}")
            bind[key] = params[idx]
            idx += 1
        else:
            out.append(ch)
    return "".join(out), bind


def _is_missing_table_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return "no such table" in msg or "does not exist" in msg or "not found" in msg


def _type_to_table_items() -> list[tuple[PlaceType, str]]:
    from ..constants import TYPE_TO_TABLE

    return list(TYPE_TO_TABLE.items())
