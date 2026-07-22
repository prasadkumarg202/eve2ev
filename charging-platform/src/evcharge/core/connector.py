"""Connector base class and registry.

A connector is one data source. It implements the five-stage contract from
the platform spec — ``download → transform → validate → deduplicate → load``
— and knows nothing about any other source.

Adding a vendor means subclassing :class:`BaseConnector`, implementing
``download`` and ``transform``, and decorating with ``@register``. The
remaining three stages have working defaults that suit most sources.

Legal posture is declared, not assumed: every connector states its
``access_mode`` and ``terms_url``. :meth:`BaseConnector.preflight` refuses to
run a connector marked ``FORBIDDEN``, so an unauthorised source cannot be
executed by accident.
"""

from __future__ import annotations

import abc
import time
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, ClassVar

from .schema import SourceTier, Station

# --------------------------------------------------------------------------- #
# Legal / access posture
# --------------------------------------------------------------------------- #


class AccessMode(str, Enum):
    """How this source is legally accessed."""

    OPEN_DATA = "open_data"  # public licence (ODbL, CC-BY, Govt OGD)
    OFFICIAL_API = "official_api"  # documented public API
    OCPI = "ocpi"  # OCPI credentials exchanged with the CPO
    PARTNER_AGREEMENT = "partner_agreement"  # contractual feed
    USER_SUBMITTED = "user_submitted"  # our own users
    RESTRICTED = "restricted"  # allowed, but with storage limits
    FORBIDDEN = "forbidden"  # ToS prohibits programmatic access


#: Modes a run is permitted to execute.
_RUNNABLE = {
    AccessMode.OPEN_DATA,
    AccessMode.OFFICIAL_API,
    AccessMode.OCPI,
    AccessMode.PARTNER_AGREEMENT,
    AccessMode.USER_SUBMITTED,
    AccessMode.RESTRICTED,
}


class ConnectorNotAuthorised(RuntimeError):
    """Raised when a connector lacks legal clearance or credentials."""


@dataclass(slots=True)
class RunStats:
    """What one connector run actually did."""

    vendor: str
    downloaded: int = 0
    transformed: int = 0
    valid: int = 0
    rejected: int = 0
    deduped: int = 0
    loaded: int = 0
    started_at: float = field(default_factory=time.monotonic)
    duration_s: float = 0.0
    errors: list[str] = field(default_factory=list)

    def finish(self) -> RunStats:
        self.duration_s = round(time.monotonic() - self.started_at, 2)
        return self

    @property
    def rejection_rate(self) -> float:
        seen = self.transformed or 1
        return round(self.rejected / seen, 3)

    def summary(self) -> str:
        return (
            f"{self.vendor}: downloaded={self.downloaded} valid={self.valid} "
            f"rejected={self.rejected} ({self.rejection_rate:.1%}) "
            f"loaded={self.loaded} in {self.duration_s}s"
        )


# --------------------------------------------------------------------------- #
# Base connector
# --------------------------------------------------------------------------- #


class BaseConnector(abc.ABC):
    """Adapter for a single upstream source."""

    #: Unique slug; becomes ``Station.vendor``.
    vendor: ClassVar[str]
    #: Human-readable source name.
    display_name: ClassVar[str] = ""
    #: Trust rank used when merging conflicting records.
    tier: ClassVar[SourceTier] = SourceTier.COMMUNITY
    #: Legal basis for accessing this source.
    access_mode: ClassVar[AccessMode] = AccessMode.FORBIDDEN
    #: Link to the terms relied upon — reviewable by a human.
    terms_url: ClassVar[str | None] = None
    #: Env vars that must be present before the connector can run.
    required_credentials: ClassVar[tuple[str, ...]] = ()
    #: Fields this source must not persist (e.g. Google Places content).
    non_cacheable_fields: ClassVar[frozenset[str]] = frozenset()

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}
        self.stats = RunStats(vendor=self.vendor)

    # ---- required of every source ------------------------------------- #
    @abc.abstractmethod
    async def download(self) -> Iterable[dict[str, Any]]:
        """Fetch raw upstream payloads. One dict per upstream station."""

    @abc.abstractmethod
    def transform(self, raw: dict[str, Any]) -> Station | None:
        """Map one raw payload to a :class:`Station`, or ``None`` to skip."""

    # ---- sensible defaults, overridable ------------------------------- #
    def validate(self, station: Station) -> bool:
        """Accept or reject a transformed station.

        Pydantic has already enforced structure and the India bbox by this
        point; this hook is for source-specific business rules.
        """
        return bool(station.vendor_station_id)

    def deduplicate(self, stations: Sequence[Station]) -> list[Station]:
        """Collapse duplicates *within this source*.

        Cross-source merging is the platform's job (see ``core.dedupe``);
        here we only drop records repeating the same vendor id, keeping the
        most complete instance.
        """
        best: dict[str, Station] = {}
        for st in stations:
            key = st.merge_key()
            incumbent = best.get(key)
            if incumbent is None or st.completeness > incumbent.completeness:
                best[key] = st
        self.stats.deduped = len(stations) - len(best)
        return list(best.values())

    async def load(self, stations: Sequence[Station]) -> int:
        """Hand records to the platform sink.

        Default is a no-op returning the count, so a connector can be
        exercised end-to-end before any database exists.
        """
        return len(stations)

    # ---- orchestration ------------------------------------------------- #
    def preflight(self) -> None:
        """Refuse to run without a legal basis and credentials.

        Called before any network access. This is the guard that keeps a
        source whose terms prohibit automated access from ever executing.
        """
        if self.access_mode not in _RUNNABLE:
            raise ConnectorNotAuthorised(
                f"{self.vendor}: access_mode={self.access_mode.value} — "
                f"not runnable. Obtain an API/OCPI agreement first."
                + (f" Terms: {self.terms_url}" if self.terms_url else "")
            )
        missing = [k for k in self.required_credentials if not self.config.get(k)]
        if missing:
            raise ConnectorNotAuthorised(
                f"{self.vendor}: missing credentials {missing}. "
                f"Set them in config or environment."
            )

    async def run(self) -> tuple[list[Station], RunStats]:
        """Execute the full five-stage pipeline for this source."""
        self.preflight()

        raws = list(await self.download())
        self.stats.downloaded = len(raws)

        stations: list[Station] = []
        for raw in raws:
            try:
                station = self.transform(raw)
            except Exception as exc:  # noqa: BLE001 - one bad row must not kill a run
                self.stats.rejected += 1
                if len(self.stats.errors) < 25:
                    self.stats.errors.append(f"transform: {exc}")
                continue
            if station is None:
                continue
            self.stats.transformed += 1
            if not self.validate(station):
                self.stats.rejected += 1
                continue
            station.vendor = self.vendor
            station.source_tier = self.tier
            stations.append(station)

        self.stats.valid = len(stations)
        stations = self.deduplicate(stations)
        self.stats.loaded = await self.load(stations)
        return stations, self.stats.finish()


# --------------------------------------------------------------------------- #
# Registry
# --------------------------------------------------------------------------- #

_REGISTRY: dict[str, type[BaseConnector]] = {}


def register(cls: type[BaseConnector]) -> type[BaseConnector]:
    """Class decorator adding a connector to the global registry."""
    slug = getattr(cls, "vendor", "")
    if not slug:
        raise ValueError(f"{cls.__name__} must define a `vendor` slug")
    if slug in _REGISTRY and _REGISTRY[slug] is not cls:
        raise ValueError(f"duplicate connector slug: {slug}")
    _REGISTRY[slug] = cls
    return cls


def get_connector(slug: str) -> type[BaseConnector]:
    if slug not in _REGISTRY:
        raise KeyError(f"unknown connector {slug!r}; registered: {sorted(_REGISTRY)}")
    return _REGISTRY[slug]


def available_connectors(runnable_only: bool = False) -> list[str]:
    """Registered connector slugs, optionally only those legally runnable."""
    if not runnable_only:
        return sorted(_REGISTRY)
    return sorted(s for s, c in _REGISTRY.items() if c.access_mode in _RUNNABLE)
