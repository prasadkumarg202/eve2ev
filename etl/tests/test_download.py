"""Network-free tests for :mod:`osm_india_etl.download`.

Covers HTML-index parsing/discovery, md5 verification, and resume-offset
logic. No test opens a socket — everything runs on in-memory strings and
temporary files.
"""

from __future__ import annotations

import hashlib
from pathlib import Path

from osm_india_etl.download import (
    _fallback_item,
    _file_md5,
    _parse_index,
    _resume_offset,
    _verify_file,
)
from osm_india_etl.models import DownloadItem

BASE_URL = "https://download.geofabrik.de/asia/india/"

PREFERRED_ZONES = [
    "southern-zone",
    "northern-zone",
    "western-zone",
    "eastern-zone",
    "central-zone",
    "north-eastern-zone",
]

# Geofabrik-style directory index: 6 zone extracts (alphabetical, as served),
# md5 sidecars for most, plus assorted non-pbf noise links.
SAMPLE_HTML = """
<html><head><title>Index of /asia/india/</title></head><body>
<table>
<tr><td><a href="../">Parent Directory</a></td></tr>
<tr><td><a href="central-zone-latest.osm.pbf">central-zone-latest.osm.pbf</a></td></tr>
<tr><td><a href="central-zone-latest.osm.pbf.md5">central-zone-latest.osm.pbf.md5</a></td></tr>
<tr><td><a href="eastern-zone-latest.osm.pbf">eastern-zone-latest.osm.pbf</a></td></tr>
<tr><td><a href="eastern-zone-latest.osm.pbf.md5">eastern-zone-latest.osm.pbf.md5</a></td></tr>
<tr><td><a href="north-eastern-zone-latest.osm.pbf">north-eastern-zone-latest.osm.pbf</a></td></tr>
<tr><td><a href="north-eastern-zone-latest.osm.pbf.md5">north-eastern-zone-latest.osm.pbf.md5</a></td></tr>
<tr><td><a href="northern-zone-latest.osm.pbf">northern-zone-latest.osm.pbf</a></td></tr>
<tr><td><a href="northern-zone-latest.osm.pbf.md5">northern-zone-latest.osm.pbf.md5</a></td></tr>
<tr><td><a href="southern-zone-latest.osm.pbf">southern-zone-latest.osm.pbf</a></td></tr>
<tr><td><a href="southern-zone-latest.osm.pbf.md5">southern-zone-latest.osm.pbf.md5</a></td></tr>
<tr><td><a href="western-zone-latest.osm.pbf">western-zone-latest.osm.pbf</a></td></tr>
<tr><td><a href="southern-zone.poly">southern-zone.poly</a></td></tr>
<tr><td><a href="southern-zone-latest-free.shp.zip">shapefiles</a></td></tr>
<tr><td><a href="southern-zone.kml">southern-zone.kml</a></td></tr>
<tr><td><a href="southern-zone-updates/">updates dir</a></td></tr>
<tr><td><a href="orphan.osm.pbf.md5">orphan sidecar without a pbf</a></td></tr>
</table>
</body></html>
"""

EXPECTED_FILENAMES = {
    "central-zone-latest.osm.pbf",
    "eastern-zone-latest.osm.pbf",
    "north-eastern-zone-latest.osm.pbf",
    "northern-zone-latest.osm.pbf",
    "southern-zone-latest.osm.pbf",
    "western-zone-latest.osm.pbf",
}


# --------------------------------------------------------------------------- #
# Index parsing / discovery
# --------------------------------------------------------------------------- #
def test_parse_index_recognizes_six_zone_files() -> None:
    items = _parse_index(SAMPLE_HTML, BASE_URL)
    assert len(items) == 6
    assert {it.filename for it in items} == EXPECTED_FILENAMES
    for it in items:
        assert isinstance(it, DownloadItem)
        assert it.url == f"{BASE_URL}{it.filename}"


def test_parse_index_ignores_non_pbf_links() -> None:
    items = _parse_index(SAMPLE_HTML, BASE_URL)
    filenames = {it.filename for it in items}
    for bad in (
        "southern-zone.poly",
        "southern-zone-latest-free.shp.zip",
        "southern-zone.kml",
        "orphan.osm.pbf.md5",
    ):
        assert bad not in filenames
    assert not any(it.filename.endswith(".md5") for it in items)


def test_parse_index_attaches_md5_sidecars() -> None:
    items = {it.filename: it for it in _parse_index(SAMPLE_HTML, BASE_URL)}
    southern = items["southern-zone-latest.osm.pbf"]
    assert southern.md5_url == f"{BASE_URL}southern-zone-latest.osm.pbf.md5"
    # western-zone has no sidecar in the sample index.
    assert items["western-zone-latest.osm.pbf"].md5_url is None
    # All other zones carry their sidecar URL.
    for name, it in items.items():
        if name != "western-zone-latest.osm.pbf":
            assert it.md5_url == f"{BASE_URL}{name}.md5"


def test_parse_index_applies_preferred_ordering() -> None:
    items = _parse_index(SAMPLE_HTML, BASE_URL, preferred_zones=PREFERRED_ZONES)
    stems = [it.filename.removesuffix("-latest.osm.pbf") for it in items]
    assert stems == PREFERRED_ZONES


def test_parse_index_puts_unpreferred_files_last() -> None:
    extra = SAMPLE_HTML.replace(
        "</table>",
        '<tr><td><a href="andhra-pradesh-latest.osm.pbf">ap</a></td></tr></table>',
    )
    items = _parse_index(extra, BASE_URL, preferred_zones=PREFERRED_ZONES)
    assert len(items) == 7
    assert items[-1].filename == "andhra-pradesh-latest.osm.pbf"
    stems = [it.filename.removesuffix("-latest.osm.pbf") for it in items[:6]]
    assert stems == PREFERRED_ZONES


def test_parse_index_empty_when_no_pbf_links() -> None:
    html = '<html><body><a href="readme.txt">readme</a><a href="../">up</a></body></html>'
    assert _parse_index(html, BASE_URL) == []


def test_fallback_item_derives_filename_and_md5() -> None:
    url = "https://download.geofabrik.de/asia/india-latest.osm.pbf"
    item = _fallback_item(url)
    assert item.filename == "india-latest.osm.pbf"
    assert item.url == url
    assert item.md5_url == f"{url}.md5"
    assert item.zone == "india-latest"


# --------------------------------------------------------------------------- #
# md5 verification
# --------------------------------------------------------------------------- #
def test_file_md5_matches_hashlib(tmp_path: Path) -> None:
    payload = b"osm india etl download verification payload" * 100
    target = tmp_path / "sample.osm.pbf"
    target.write_bytes(payload)
    expected = hashlib.md5(payload).hexdigest()
    assert _file_md5(target) == expected
    assert _file_md5(target, chunk_size=7) == expected  # chunking must not change digest


def test_verify_file_passes_on_matching_expectations(tmp_path: Path) -> None:
    payload = b"verified bytes"
    target = tmp_path / "ok.osm.pbf"
    target.write_bytes(payload)
    reason = _verify_file(
        target,
        expected_size=len(payload),
        expected_md5=hashlib.md5(payload).hexdigest(),
    )
    assert reason is None


def test_verify_file_reports_mismatches(tmp_path: Path) -> None:
    target = tmp_path / "bad.osm.pbf"
    target.write_bytes(b"actual content")
    assert "size mismatch" in (_verify_file(target, expected_size=999, expected_md5=None) or "")
    assert "md5 mismatch" in (
        _verify_file(target, expected_size=None, expected_md5="0" * 32) or ""
    )
    missing = tmp_path / "nope.osm.pbf"
    assert _verify_file(missing, expected_size=None, expected_md5=None) == "file missing"


# --------------------------------------------------------------------------- #
# Resume offset
# --------------------------------------------------------------------------- #
def test_resume_offset_uses_partial_size(tmp_path: Path) -> None:
    part = tmp_path / "southern-zone-latest.osm.pbf.part"
    part.write_bytes(b"x" * 1234)
    assert _resume_offset(part, resume=True) == 1234


def test_resume_offset_zero_when_resume_disabled(tmp_path: Path) -> None:
    part = tmp_path / "northern-zone-latest.osm.pbf.part"
    part.write_bytes(b"x" * 512)
    assert _resume_offset(part, resume=False) == 0


def test_resume_offset_zero_when_no_partial(tmp_path: Path) -> None:
    part = tmp_path / "missing.osm.pbf.part"
    assert _resume_offset(part, resume=True) == 0
