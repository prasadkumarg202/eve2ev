"""EXTRACT stage: parse ``.osm.pbf`` files with pyosmium into Parquet.

For every OSM object whose tags match one of the enabled extraction rules
(admin boundaries, places, highways, buildings, postcodes) a
:class:`~osm_india_etl.models.LocationRecord` is built and appended — in
batches — to one Parquet file per input ``.pbf`` (schema =
:data:`~osm_india_etl.constants.LOCATION_COLUMNS`).

Heavy dependencies (``osmium``, ``pyarrow``) are imported lazily/guarded so
the pure tag-mapping helpers (:func:`tags_to_record`) stay importable in
environments where those wheels are absent (e.g. unit tests).
"""

from __future__ import annotations

import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import Any

from .config import Settings, get_settings
from .constants import (
    ADMIN_LEVEL_TO_TYPE,
    INDIA_BBOX,
    LOCATION_COLUMNS,
    NAME_TAG_KEYS,
    PLACE_TAG_TO_TYPE,
    POSTCODE_KEYS,
    OSMType,
    PlaceType,
    classify_highway,
)
from .logging_setup import StageTimer, log
from .models import LocationRecord

# --------------------------------------------------------------------------- #
# Guarded heavy imports
# --------------------------------------------------------------------------- #
try:  # pragma: no cover - trivially environment dependent
    import osmium
except ImportError:  # pragma: no cover
    osmium = None  # type: ignore[assignment]

_HandlerBase: type = osmium.SimpleHandler if osmium is not None else object

#: Relation ``type`` values that pyosmium's area assembler turns into areas.
#: Relations tagged with these are emitted by ``LocationHandler.area`` (with
#: geometry) rather than ``LocationHandler.relation``.
AREA_RELATION_TYPES = frozenset({"multipolygon", "boundary"})


# --------------------------------------------------------------------------- #
# Pure helpers (no osmium / pyarrow needed — unit-testable)
# --------------------------------------------------------------------------- #
def in_india_bbox(lon: float, lat: float) -> bool:
    """Coordinate sanity guard: is (lon, lat) inside the India bounding box?"""
    minlon, minlat, maxlon, maxlat = INDIA_BBOX
    return minlon <= lon <= maxlon and minlat <= lat <= maxlat


def _parse_admin_level(raw: str | None) -> int | None:
    """Parse an ``admin_level`` tag value, tolerating junk like ``'4;6'``."""
    if not raw:
        return None
    try:
        return int(raw.split(";")[0].strip())
    except (ValueError, AttributeError):
        return None


def _classify_admin(tags: dict[str, str], settings: Settings) -> tuple[PlaceType, int] | None:
    """Map a ``boundary=administrative`` object to (PlaceType, admin_level)."""
    if tags.get("boundary") != "administrative":
        return None
    level = _parse_admin_level(tags.get("admin_level"))
    if level is None:
        return None
    wanted = settings.extract.admin_levels
    if wanted and level not in wanted:
        return None
    place_type: PlaceType | None = None
    if wanted:
        # Config may name the tier explicitly (e.g. {7: "tehsil"}).
        try:
            place_type = PlaceType(wanted[level])
        except ValueError:
            place_type = None
    if place_type is None:
        place_type = ADMIN_LEVEL_TO_TYPE.get(level, PlaceType.UNKNOWN)
    return place_type, level


def _extract_pincode(tags: dict[str, str]) -> str | None:
    """Return the first postal code found among :data:`POSTCODE_KEYS`."""
    for key in POSTCODE_KEYS:
        value = tags.get(key, "").strip()
        if value:
            return value
    return None


def _collect_names(tags: dict[str, str]) -> dict[str, str]:
    """Pick the name tags worth keeping (see :data:`NAME_TAG_KEYS`)."""
    return {k: tags[k] for k in NAME_TAG_KEYS if tags.get(k)}


def tags_to_record(
    osm_type: OSMType,
    osm_id: int,
    tags: dict[str, str],
    settings: Settings,
) -> LocationRecord | None:
    """Map raw OSM tags to a :class:`LocationRecord` (or ``None`` if the
    object matches no enabled extraction rule).

    Classification precedence: admin boundary > place > highway > building >
    postcode-only carrier. A postcode found on *any* emitted record is stored
    in ``rec.pincode`` regardless of which rule matched.

    Pure function: needs no osmium runtime, so it is directly unit-testable.
    """
    ext = settings.extract
    place_type: PlaceType | None = None
    admin_level: int | None = None

    if ext.extract_admin:
        admin = _classify_admin(tags, settings)
        if admin is not None:
            place_type, admin_level = admin

    if place_type is None and ext.extract_places and tags.get("place"):
        place_type = PLACE_TAG_TO_TYPE.get(tags["place"])

    if (
        place_type is None
        and ext.extract_highways
        and osm_type is OSMType.WAY
        and tags.get("highway")
    ):
        place_type = classify_highway(tags["highway"])

    if place_type is None and ext.extract_buildings and tags.get("building"):
        place_type = PlaceType.BUILDING

    pincode = _extract_pincode(tags)

    if place_type is None:
        if ext.extract_postcodes and pincode:
            # Object carries nothing but a postal code — emit it as one.
            place_type = PlaceType.POSTAL_CODE
        else:
            return None

    record = LocationRecord(
        osm_id=osm_id,
        osm_type=osm_type,
        place_type=place_type,
        admin_level=admin_level,
    )
    record.names = _collect_names(tags)
    record.name = (
        record.names.get("name")
        or record.names.get("name:en")
        or next(iter(record.names.values()), "")
    )
    record.name_en = record.names.get("name:en", "")
    record.pincode = pincode
    if place_type is PlaceType.POSTAL_CODE and not record.name:
        record.name = pincode or ""
    record.tags = dict(tags)
    return record


# --------------------------------------------------------------------------- #
# Parquet batch writer (lazy pyarrow)
# --------------------------------------------------------------------------- #
def _arrow_schema() -> Any:
    """Build the pyarrow schema matching :data:`LOCATION_COLUMNS` exactly."""
    import pyarrow as pa

    types: dict[str, Any] = {
        "osm_id": pa.int64(),
        "admin_level": pa.int32(),
        "latitude": pa.float64(),
        "longitude": pa.float64(),
        "area_sqkm": pa.float64(),
    }
    return pa.schema([(col, types.get(col, pa.string())) for col in LOCATION_COLUMNS])


class ParquetBatchWriter:
    """Accumulates row dicts and flushes them in batches to a growing
    Parquet file via :class:`pyarrow.parquet.ParquetWriter`."""

    def __init__(self, out_path: Path, batch_size: int) -> None:
        import pyarrow.parquet as pq

        self.out_path = out_path
        self.batch_size = max(int(batch_size), 1)
        self.schema = _arrow_schema()
        self._writer = pq.ParquetWriter(str(out_path), self.schema, compression="zstd")
        self._rows: list[dict[str, Any]] = []
        self.total_rows = 0

    def add(self, row: dict[str, Any]) -> None:
        self._rows.append(row)
        if len(self._rows) >= self.batch_size:
            self.flush()

    def flush(self) -> None:
        if not self._rows:
            return
        import pyarrow as pa

        table = pa.Table.from_pylist(self._rows, schema=self.schema)
        self._writer.write_table(table)
        self.total_rows += len(self._rows)
        self._rows.clear()

    def close(self) -> None:
        self.flush()
        self._writer.close()

    def __enter__(self) -> ParquetBatchWriter:
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self.close()


# --------------------------------------------------------------------------- #
# Osmium handler
# --------------------------------------------------------------------------- #
class LocationHandler(_HandlerBase):
    """pyosmium handler that converts matching OSM objects into
    :class:`LocationRecord` rows and streams them into a Parquet writer."""

    def __init__(self, settings: Settings, source_file: str, writer: ParquetBatchWriter) -> None:
        if osmium is None:  # pragma: no cover - environment dependent
            raise RuntimeError("pyosmium is not installed; `pip install osmium` to run extract")
        super().__init__()
        self.settings = settings
        self.source_file = source_file
        self.writer = writer
        self.wkt_factory = osmium.geom.WKTFactory()
        self.emitted = 0
        self.skipped_out_of_bbox = 0
        self.geometry_failures = 0
        self.areas_emitted = 0
        self.skipped_boundary_ways = 0

    # ---- shared plumbing ---------------------------------------------- #
    def _emit(self, record: LocationRecord) -> None:
        record.source_file = self.source_file
        self.writer.add(record.to_row())
        self.emitted += 1

    @staticmethod
    def _tags(obj: Any) -> dict[str, str]:
        return {t.k: t.v for t in obj.tags}

    # ---- callbacks ----------------------------------------------------- #
    def node(self, n: Any) -> None:
        record = tags_to_record(OSMType.NODE, n.id, self._tags(n), self.settings)
        if record is None:
            return
        if n.location.valid():
            lon, lat = n.location.lon, n.location.lat
            if not in_india_bbox(lon, lat):
                self.skipped_out_of_bbox += 1
                return
            record.longitude = lon
            record.latitude = lat
            record.geometry_wkt = f"POINT({lon} {lat})"
        self._emit(record)

    def way(self, w: Any) -> None:
        tags = self._tags(w)
        # A `boundary=administrative` way is a *segment* of a boundary, not an
        # admin unit — the relation carries the entity. Emitting these yields
        # hundreds of nameless phantom "states" and border-line "countries"
        # (e.g. "China-India LAC") that pollute hierarchy resolution.
        # Genuine closed-way admin areas still arrive via `area()`.
        if tags.get("boundary") == "administrative":
            self.skipped_boundary_ways += 1
            return
        record = tags_to_record(OSMType.WAY, w.id, tags, self.settings)
        if record is None:
            return
        try:
            record.geometry_wkt = self.wkt_factory.create_linestring(w)
        except Exception:
            # Missing node locations / degenerate geometry — transform stage
            # will rebuild geometry later.
            self.geometry_failures += 1
            record.geometry_wkt = None
        centroid = self._way_centroid(w)
        if centroid is not None:
            record.longitude, record.latitude = centroid
        self._emit(record)

    def relation(self, r: Any) -> None:
        tags = self._tags(r)
        # Area-typed relations (the overwhelming majority of admin boundaries)
        # are emitted by `area()` instead, with assembled multipolygon
        # geometry. Emitting here too would duplicate every boundary.
        if tags.get("type") in AREA_RELATION_TYPES:
            return
        record = tags_to_record(OSMType.RELATION, r.id, tags, self.settings)
        if record is None:
            return
        record.geometry_wkt = None
        self._emit(record)

    def area(self, a: Any) -> None:
        """Assembled multipolygon areas.

        pyosmium scans the file twice when this callback exists and hands back
        areas built from both closed ways and multipolygon/boundary relations.
        Way-derived areas are skipped — `way()` already emitted those — so this
        callback is the single source of geometry for boundary relations.
        """
        tags = self._tags(a)
        # Way-derived areas were already emitted by `way()` — except admin
        # boundaries, which `way()` deliberately skips, so a genuinely
        # closed-way admin area is only captured here.
        if a.from_way() and tags.get("boundary") != "administrative":
            return
        osm_type = OSMType.WAY if a.from_way() else OSMType.RELATION
        record = tags_to_record(osm_type, a.orig_id(), tags, self.settings)
        if record is None:
            return
        try:
            record.geometry_wkt = self.wkt_factory.create_multipolygon(a)
        except Exception:
            # Broken/unclosed rings — keep the record, transform falls back to
            # proximity-based parenting.
            self.geometry_failures += 1
            record.geometry_wkt = None
        self._emit(record)
        self.areas_emitted += 1

    # ---- geometry helpers ---------------------------------------------- #
    def _way_centroid(self, w: Any) -> tuple[float, float] | None:
        """Average of the way's valid node locations (rough representative
        point), with the INDIA_BBOX sanity guard applied."""
        try:
            lons: list[float] = []
            lats: list[float] = []
            for node_ref in w.nodes:
                loc = node_ref.location
                if loc.valid():
                    lons.append(loc.lon)
                    lats.append(loc.lat)
            if not lons:
                return None
            lon = sum(lons) / len(lons)
            lat = sum(lats) / len(lats)
        except Exception:
            return None
        if not in_india_bbox(lon, lat):
            return None
        return lon, lat


# --------------------------------------------------------------------------- #
# Per-file driver
# --------------------------------------------------------------------------- #
def _parquet_name(pbf_path: Path) -> str:
    return f"{pbf_path.name.replace('.osm.pbf', '')}.parquet"


def extract_file(pbf_path: Path, settings: Settings) -> Path:
    """Extract one ``.osm.pbf`` file into a Parquet file and return its path."""
    if osmium is None:  # pragma: no cover - environment dependent
        raise RuntimeError("pyosmium is not installed; `pip install osmium` to run extract")

    out_dir = settings.path("parquet")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / _parquet_name(pbf_path)

    with StageTimer(f"extract {pbf_path.name}") as timer:
        with ParquetBatchWriter(out_path, settings.extract.batch_size) as writer:
            handler = LocationHandler(settings, pbf_path.name, writer)
            handler.apply_file(str(pbf_path), locations=True, idx="flex_mem")
        timer.add(writer.total_rows)
        if handler.skipped_out_of_bbox:
            log.warning(
                f"{pbf_path.name}: skipped {handler.skipped_out_of_bbox:,} "
                "records outside INDIA_BBOX"
            )
        if handler.geometry_failures:
            log.debug(
                f"{pbf_path.name}: {handler.geometry_failures:,} geometries deferred "
                "to transform stage"
            )
    return out_path


def _extract_worker(pbf_path: Path, settings: Settings) -> str:
    """Module-level worker (picklable) for :class:`ProcessPoolExecutor`."""
    return str(extract_file(pbf_path, settings))


# --------------------------------------------------------------------------- #
# Stage entry point
# --------------------------------------------------------------------------- #
def run_extract(
    settings: Settings | None = None,
    files: list[Path] | None = None,
) -> list[Path]:
    """Run the EXTRACT stage over every ``*.osm.pbf`` in ``paths.raw``
    (or an explicit file list), in parallel, and return the Parquet paths."""
    settings = settings or get_settings()

    if files is None:
        files = sorted(settings.path("raw").glob("*.osm.pbf"))
    if not files:
        log.warning(f"run_extract: no .osm.pbf files found in {settings.path('raw')}")
        return []

    workers = max(1, min(settings.worker_count, len(files)))
    log.info(f"EXTRACT: {len(files)} file(s) with {workers} worker(s)")

    results: list[Path] = []
    start = time.perf_counter()
    with StageTimer("extract stage", total=len(files)) as timer:
        with ProcessPoolExecutor(max_workers=workers) as pool:
            future_to_file = {pool.submit(_extract_worker, f, settings): f for f in files}
            done = 0
            for future in as_completed(future_to_file):
                pbf = future_to_file[future]
                try:
                    results.append(Path(future.result()))
                except Exception as exc:
                    log.error(f"extract failed for {pbf.name}: {exc!r}")
                    raise
                done += 1
                timer.add()
                elapsed = time.perf_counter() - start
                eta = (elapsed / done) * (len(files) - done)
                log.info(
                    f"EXTRACT progress: {done}/{len(files)} files "
                    f"({done / len(files):.0%}) | elapsed={elapsed:,.0f}s | eta={eta:,.0f}s"
                )

    return sorted(results)


__all__ = [
    "LocationHandler",
    "ParquetBatchWriter",
    "extract_file",
    "in_india_bbox",
    "run_extract",
    "tags_to_record",
]
