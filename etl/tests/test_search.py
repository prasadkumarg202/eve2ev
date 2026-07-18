"""Tests for the search layer: fuzzy, phonetic, haversine, and the sqlite engine."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator
from pathlib import Path

import pytest

from osm_india_etl.search import fts as fts_helpers
from osm_india_etl.search import fuzzy, phonetic
from osm_india_etl.search.engine import SearchEngine, haversine_km

# --------------------------------------------------------------------------- #
# Pure-python unit tests
# --------------------------------------------------------------------------- #


class TestFuzzy:
    def test_rank_bangalore_matches_bengaluru(self) -> None:
        candidates = ["Bengaluru", "Chennai", "Mumbai", "Bangalore Rural"]
        ranked = fuzzy.rank("Bangalore", candidates)
        names = [name for name, _ in ranked]
        scores = dict(ranked)
        # Bengaluru must beat unrelated cities and score reasonably.
        assert names.index("Bengaluru") < names.index("Chennai")
        assert names.index("Bengaluru") < names.index("Mumbai")
        assert scores["Bengaluru"] >= 55.0
        assert scores["Bangalore Rural"] >= scores["Chennai"]

    def test_rank_sorted_desc(self) -> None:
        ranked = fuzzy.rank("delhi", ["Delhi", "New Delhi", "Kolkata"])
        assert ranked[0][0] == "Delhi"
        assert all(ranked[i][1] >= ranked[i + 1][1] for i in range(len(ranked) - 1))

    def test_exact_match_is_100(self) -> None:
        assert fuzzy.score("Pune", "pune") == 100.0

    def test_empty_scores_zero(self) -> None:
        assert fuzzy.score("", "x") == 0.0
        assert fuzzy.rank("q", []) == []

    def test_levenshtein(self) -> None:
        assert fuzzy.levenshtein("bangalore", "bengaluru") == 3
        assert fuzzy.levenshtein("abc", "abc") == 0
        assert fuzzy.levenshtein("", "abc") == 3
        assert fuzzy._levenshtein_py("kitten", "sitting") == 3


class TestPhonetic:
    def test_soundex_fallback_known_codes(self) -> None:
        # Classic reference values for the pure-python implementation.
        assert phonetic._soundex_py("Robert") == "R163"
        assert phonetic._soundex_py("Rupert") == "R163"
        assert phonetic._soundex_py("Ashcraft") == "A261"  # H/W transparency
        assert phonetic._soundex_py("Tymczak") == "T522"

    def test_soundex_bangalore_variants_agree(self) -> None:
        assert phonetic.soundex("Bangalore") == phonetic.soundex("Bengaluru")
        assert phonetic.soundex("Bangalore").startswith("B")

    def test_metaphone_fallback_bangalore_variants_agree(self) -> None:
        assert phonetic._metaphone_py("Bangalore") == phonetic._metaphone_py("Bengaluru")

    def test_metaphone_public(self) -> None:
        assert phonetic.metaphone("") == ""
        assert phonetic.metaphone("Chennai")  # non-empty code

    def test_phonetic_equal(self) -> None:
        assert phonetic.phonetic_equal("Bangalore", "Bengaluru")
        assert not phonetic.phonetic_equal("Mumbai", "Kolkata")
        assert not phonetic.phonetic_equal("", "Delhi")


class TestHaversine:
    def test_zero_distance(self) -> None:
        assert haversine_km(12.97, 77.59, 12.97, 77.59) == 0.0

    def test_bangalore_chennai(self) -> None:
        d = haversine_km(12.9716, 77.5946, 13.0827, 80.2707)
        assert 280 < d < 300

    def test_symmetry(self) -> None:
        a = haversine_km(28.61, 77.20, 19.07, 72.87)
        b = haversine_km(19.07, 72.87, 28.61, 77.20)
        assert a == pytest.approx(b)


class TestFtsHelpers:
    def test_prefix_query_quotes_and_stars(self) -> None:
        assert fts_helpers.fts_prefix_query("navi mum") == '"navi"* "mum"*'

    def test_quotes_escaped(self) -> None:
        assert '""' in fts_helpers.sanitize_term('a"b')
        assert fts_helpers.fts_prefix_query("") == ""

    def test_like_pattern_escapes_wildcards(self) -> None:
        assert fts_helpers.like_pattern("50%_off") == "%50\\%\\_off%"
        assert fts_helpers.like_pattern("che", prefix_only=True) == "che%"

    def test_trigrams(self) -> None:
        assert fts_helpers.trigrams("abcd") == ["abc", "bcd"]
        assert fts_helpers.trigrams("ab") == ["ab"]
        clause, params = fts_helpers.trigram_like_clauses("abcd")
        assert clause.count("LIKE") == 2 and len(params) == 2


# --------------------------------------------------------------------------- #
# SQLite integration
# --------------------------------------------------------------------------- #

_ROWS = [
    # (location_id, osm_id, osm_type, place_type, name, search_name, pincode,
    #  lat, lng, parent_id, state_name, district_name, aliases)
    ("n1", 1, "node", "city", "Bengaluru", "bengaluru bangalore", "560001",
     12.9716, 77.5946, "r10", "Karnataka", "Bengaluru Urban", "bangalore bengalooru"),
    ("n2", 2, "node", "city", "Chennai", "chennai madras", "600001",
     13.0827, 80.2707, "r11", "Tamil Nadu", "Chennai", "madras"),
    ("n3", 3, "node", "suburb", "Koramangala", "koramangala", "560034",
     12.9352, 77.6245, "n1", "Karnataka", "Bengaluru Urban", ""),
    ("r10", 10, "relation", "state", "Karnataka", "karnataka", None,
     15.3173, 75.7139, None, "Karnataka", None, ""),
]


def build_test_db(path: Path) -> None:
    """Create a minimal load-stage-shaped sqlite db (locations + FTS + aliases)."""
    conn = sqlite3.connect(str(path))
    conn.executescript(
        """
        CREATE TABLE locations (
            location_id TEXT PRIMARY KEY,
            osm_id INTEGER, osm_type TEXT, place_type TEXT,
            name TEXT, name_lower TEXT, search_name TEXT,
            pincode TEXT, latitude REAL, longitude REAL,
            parent_id TEXT, state_name TEXT, district_name TEXT
        );
        CREATE TABLE aliases (location_id TEXT, alias TEXT);
        """
    )
    fts_ok = True
    try:
        conn.execute("CREATE VIRTUAL TABLE locations_fts USING fts5(name, search_name, aliases)")
    except sqlite3.OperationalError:  # FTS5 not compiled in: engine falls back to LIKE
        fts_ok = False
    for i, row in enumerate(_ROWS, start=1):
        (loc, osm_id, osm_type, ptype, name, sname, pin, lat, lng, parent, state, dist, al) = row
        conn.execute(
            "INSERT INTO locations VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (loc, osm_id, osm_type, ptype, name, name.lower(), sname, pin, lat, lng, parent, state, dist),
        )
        if fts_ok:
            conn.execute(
                "INSERT INTO locations_fts(rowid, name, search_name, aliases) VALUES (?,?,?,?)",
                (i, name, sname, al),
            )
        for alias in al.split():
            conn.execute("INSERT INTO aliases VALUES (?, ?)", (loc, alias))
    conn.commit()
    conn.close()


@pytest.fixture()
def engine(tmp_path: Path) -> Generator[SearchEngine, None, None]:
    from osm_india_etl.config import Settings

    db = tmp_path / "osm_test.sqlite"
    build_test_db(db)
    settings = Settings.model_validate(
        {"database": {"sqlite_path": str(db)}, "api": {"backend": "sqlite"}}
    )
    eng = SearchEngine(settings)
    yield eng
    eng.close()


class TestSearchEngineSqlite:
    def test_search_bang_finds_bengaluru(self, engine: SearchEngine) -> None:
        results = engine.search("bang")
        assert results, "expected at least one hit for 'bang'"
        assert results[0]["name"] == "Bengaluru"
        assert results[0]["location_id"] == "n1"
        assert results[0]["state_name"] == "Karnataka"
        assert "score" in results[0] and results[0]["score"] > 0

    def test_search_type_filter(self, engine: SearchEngine) -> None:
        results = engine.search("karnataka", place_type="state")
        assert results and all(r["place_type"] == "state" for r in results)

    def test_search_empty_query(self, engine: SearchEngine) -> None:
        assert engine.search("   ") == []

    def test_phonetic_layer_matches_misspelling(self, engine: SearchEngine) -> None:
        # "bengalooroo" shares a phonetic code with Bengaluru but no substring.
        results = engine.search("bengalooroo")
        assert any(r["name"] == "Bengaluru" for r in results)

    def test_autocomplete_che(self, engine: SearchEngine) -> None:
        items = engine.autocomplete("che")
        assert items and items[0]["name"] == "Chennai"

    def test_autocomplete_respects_limit(self, engine: SearchEngine) -> None:
        assert len(engine.autocomplete("k", limit=1)) == 1

    def test_reverse_geocode_picks_nearest(self, engine: SearchEngine) -> None:
        hit = engine.reverse_geocode(12.9715, 77.5950)  # ~40 m from Bengaluru centre
        assert hit is not None
        assert hit["name"] == "Bengaluru"
        assert hit["distance_km"] < 1.0
        near_kora = engine.reverse_geocode(12.9353, 77.6246)
        assert near_kora is not None and near_kora["name"] == "Koramangala"

    def test_nearby_sorted_by_distance(self, engine: SearchEngine) -> None:
        rows = engine.nearby(12.9716, 77.5946, radius_km=10)
        names = [r["name"] for r in rows]
        assert names[0] == "Bengaluru"
        assert "Koramangala" in names
        assert "Chennai" not in names  # ~290 km away
        dists = [r["distance_km"] for r in rows]
        assert dists == sorted(dists)

    def test_list_by_type_falls_back_to_locations(self, engine: SearchEngine) -> None:
        cities = engine.list_by_type("cities", limit=10)
        assert {c["name"] for c in cities} == {"Bengaluru", "Chennai"}
        assert engine.list_by_type("cities", limit=1, offset=1)  # pagination works

    def test_list_by_type_rejects_unknown_table(self, engine: SearchEngine) -> None:
        with pytest.raises(ValueError):
            engine.list_by_type("locations; DROP TABLE locations")
