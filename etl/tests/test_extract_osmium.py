"""Osmium parse-path tests.

These exercise :class:`LocationHandler` against a real OSM file rather than
hand-built records. The rest of the suite constructs ``LocationRecord``
objects directly, which cannot catch geometry regressions in the extract
stage — notably boundary relations losing their multipolygon geometry, which
silently breaks hierarchy resolution downstream.
"""

from __future__ import annotations

import pytest

from osm_india_etl.config import get_settings
from osm_india_etl.models import LocationRecord
from osm_india_etl.transform.geometry import compute_geometry
from osm_india_etl.transform.hierarchy import build_hierarchy

osmium = pytest.importorskip("osmium", reason="pyosmium not installed")

from osm_india_etl.extract import LocationHandler  # noqa: E402

# A 1°x1° Karnataka-ish boundary relation (admin_level=4) with Bengaluru as a
# place=city node inside it, plus a closed building way.
FIXTURE_OSM = """<?xml version='1.0' encoding='UTF-8'?>
<osm version="0.6" generator="test">
 <node id="1" lat="12.97" lon="77.59" version="1">
  <tag k="place" v="city"/><tag k="name" v="Bengaluru"/>
 </node>
 <node id="10" lat="12.0" lon="77.0" version="1"/>
 <node id="11" lat="13.0" lon="77.0" version="1"/>
 <node id="12" lat="13.0" lon="78.0" version="1"/>
 <node id="13" lat="12.0" lon="78.0" version="1"/>
 <node id="20" lat="12.4" lon="77.4" version="1"/>
 <node id="21" lat="12.5" lon="77.4" version="1"/>
 <node id="22" lat="12.5" lon="77.5" version="1"/>
 <node id="23" lat="12.4" lon="77.5" version="1"/>
 <way id="100" version="1">
  <nd ref="10"/><nd ref="11"/><nd ref="12"/><nd ref="13"/><nd ref="10"/>
 </way>
 <way id="101" version="1">
  <nd ref="20"/><nd ref="21"/><nd ref="22"/><nd ref="23"/><nd ref="20"/>
  <tag k="building" v="yes"/><tag k="name" v="Mall"/>
 </way>
 <relation id="500" version="1">
  <member type="way" ref="100" role="outer"/>
  <tag k="type" v="boundary"/><tag k="boundary" v="administrative"/>
  <tag k="admin_level" v="4"/><tag k="name" v="Karnataka"/>
 </relation>
</osm>
"""


class _CapturingWriter:
    """Stand-in for ParquetBatchWriter that keeps rows in memory."""

    def __init__(self) -> None:
        self.rows: list[dict] = []

    def add(self, row: dict) -> None:
        self.rows.append(row)


@pytest.fixture
def extracted(tmp_path):
    osm_file = tmp_path / "fixture.osm"
    osm_file.write_text(FIXTURE_OSM, encoding="utf-8")

    writer = _CapturingWriter()
    handler = LocationHandler(get_settings(), "fixture.osm", writer)
    handler.apply_file(str(osm_file), locations=True)

    records = [LocationRecord.from_row(row) for row in writer.rows]
    return handler, records


def _by_name(records, name):
    return next(r for r in records if r.name == name)


def test_boundary_relation_gets_multipolygon_geometry(extracted):
    """Regression: admin boundaries are relations; without an area() callback
    they were emitted with geometry_wkt=None, nulling the whole hierarchy."""
    _, records = extracted
    karnataka = _by_name(records, "Karnataka")

    assert karnataka.osm_type.value == "relation"
    assert karnataka.geometry_wkt is not None
    assert karnataka.geometry_wkt.startswith("MULTIPOLYGON")


def test_area_relation_emitted_exactly_once(extracted):
    """area() fires in addition to relation(); emitting from both duplicates
    every boundary in the output."""
    handler, records = extracted
    assert handler.areas_emitted == 1
    assert len([r for r in records if r.name == "Karnataka"]) == 1


def test_relation_geometry_yields_centroid_bbox_and_area(extracted):
    _, records = extracted
    karnataka = _by_name(records, "Karnataka")
    compute_geometry(karnataka)

    assert karnataka.latitude == pytest.approx(12.5, abs=0.01)
    assert karnataka.longitude == pytest.approx(77.5, abs=0.01)
    assert karnataka.bbox == pytest.approx((77.0, 12.0, 78.0, 13.0))
    # ~111km x ~108km at 12.5°N
    assert karnataka.area_sqkm == pytest.approx(12_000, rel=0.1)


def test_city_resolves_into_containing_state(extracted):
    """The end-to-end payoff: containment-based parenting only works when the
    boundary relation carries real polygon geometry."""
    _, records = extracted
    for rec in records:
        compute_geometry(rec)
    build_hierarchy(records)

    bengaluru = _by_name(records, "Bengaluru")
    karnataka = _by_name(records, "Karnataka")

    assert bengaluru.parent_id == karnataka.location_id
    assert bengaluru.state_name == "Karnataka"
