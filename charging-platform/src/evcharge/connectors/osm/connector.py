"""OpenStreetMap charging-station connector (Overpass API).

Legal basis: OSM data is ODbL-licensed open data. Attribution is required on
any published derivative — see ``ATTRIBUTION``.

Overpass is a shared community resource. This connector queries state by
state rather than requesting all of India at once, because a single national
query for ``amenity=charging_station`` routinely exceeds Overpass's memory
ceiling and gets the caller rate-limited. Sequential per-state queries with a
courtesy delay are slower but do not abuse the endpoint.
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Iterable
from typing import Any, ClassVar

import httpx

from ...core.connector import AccessMode, BaseConnector, register
from ...core.normalize import canonical_operator, canonical_state
from ...core.schema import (
    Address,
    Amenity,
    Connector,
    ConnectorStatus,
    ConnectorType,
    PaymentMethod,
    Pricing,
    PricingModel,
    SourceTier,
    Station,
    VehicleType,
)

ATTRIBUTION = "© OpenStreetMap contributors, ODbL 1.0"

#: Overpass mirrors, tried in order.
OVERPASS_ENDPOINTS = (
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
)

#: States/UTs queried individually to stay within Overpass limits.
INDIAN_STATES = (
    "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar", "Chhattisgarh",
    "Goa", "Gujarat", "Haryana", "Himachal Pradesh", "Jharkhand", "Karnataka",
    "Kerala", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Punjab", "Rajasthan", "Sikkim",
    "Tamil Nadu", "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand",
    "West Bengal", "Delhi", "Jammu and Kashmir", "Ladakh", "Puducherry",
    "Chandigarh", "Andaman and Nicobar Islands", "Dadra and Nagar Haveli and Daman and Diu",
    "Lakshadweep",
)

_QUERY_TEMPLATE = """
[out:json][timeout:{timeout}];
area["name"="{state}"]["admin_level"~"4"]->.a;
(
  node["amenity"="charging_station"](area.a);
  way["amenity"="charging_station"](area.a);
  relation["amenity"="charging_station"](area.a);
);
out center tags;
"""

# --------------------------------------------------------------------------- #
# Tag mapping
# --------------------------------------------------------------------------- #

#: OSM socket:* suffix -> canonical connector type.
_SOCKET_MAP: dict[str, ConnectorType] = {
    "type2": ConnectorType.TYPE2,
    "type2_combo": ConnectorType.CCS2,
    "type2_cable": ConnectorType.TYPE2,
    "ccs2": ConnectorType.CCS2,
    "chademo": ConnectorType.CHADEMO,
    "gb_t": ConnectorType.GBT,
    "gbt": ConnectorType.GBT,
    "bharat_ac_001": ConnectorType.BHARAT_AC001,
    "bharat_dc_001": ConnectorType.BHARAT_DC001,
    "typee": ConnectorType.THREE_PIN,
    "domestic": ConnectorType.THREE_PIN,
}

_AMENITY_TAGS: dict[str, Amenity] = {
    "toilets": Amenity.WASHROOM,
    "restaurant": Amenity.RESTAURANT,
    "cafe": Amenity.CAFE,
    "wifi": Amenity.WIFI,
    "internet_access": Amenity.WIFI,
    "shop": Amenity.SHOPPING,
    "atm": Amenity.ATM,
    "surveillance": Amenity.CCTV,
    "parking": Amenity.PARKING,
}

_VEHICLE_TAGS: dict[str, VehicleType] = {
    "motorcar": VehicleType.CAR,
    "motorcycle": VehicleType.TWO_WHEELER,
    "scooter": VehicleType.TWO_WHEELER,
    "hgv": VehicleType.TRUCK,
    "bus": VehicleType.BUS,
    "truck": VehicleType.TRUCK,
}

_TRUE = {"yes", "true", "1", "designated"}


def _as_float(value: Any) -> float | None:
    """Parse OSM's messy numerics: '50', '50 kW', '22.0', '3.7;7.4'."""
    if value is None:
        return None
    text = str(value).strip().lower().replace("kw", "").strip()
    if ";" in text:  # multi-valued — take the highest
        parts = [_as_float(p) for p in text.split(";")]
        vals = [p for p in parts if p is not None]
        return max(vals) if vals else None
    try:
        return float(text)
    except ValueError:
        return None


def _parse_connectors(tags: dict[str, str]) -> list[Connector]:
    """Build connectors from ``socket:<type>`` / ``socket:<type>:output`` tags."""
    out: list[Connector] = []
    for key, value in tags.items():
        if not key.startswith("socket:"):
            continue
        parts = key.split(":")
        if len(parts) < 2:
            continue
        suffix = parts[1].lower()
        # socket:type2:output=22 kW carries power; socket:type2=2 carries count.
        if len(parts) > 2 and parts[2] in {"output", "voltage", "current"}:
            continue
        ctype = _SOCKET_MAP.get(suffix)
        if ctype is None:
            continue
        count = 1
        try:
            count = max(1, int(str(value).strip()))
        except (TypeError, ValueError):
            pass
        power = _as_float(tags.get(f"socket:{suffix}:output")) or _as_float(
            tags.get("charge") or tags.get("maxpower")
        )
        out.append(
            Connector(
                connector_type=ctype,
                power_kw=power,
                count=count,
                status=ConnectorStatus.UNKNOWN,  # OSM never carries live status
            )
        )

    if not out:
        # No socket:* tags — fall back to a single unknown gun so the station
        # still records its power rating.
        power = _as_float(tags.get("charge") or tags.get("maxpower"))
        if power is not None or tags.get("amenity") == "charging_station":
            out.append(Connector(connector_type=ConnectorType.UNKNOWN, power_kw=power))
    return out


def _parse_pricing(tags: dict[str, str]) -> Pricing:
    fee = (tags.get("fee") or "").strip().lower()
    if fee in {"no", "free"}:
        return Pricing(model=PricingModel.FREE)
    charge = tags.get("charge:conditional") or tags.get("charge")
    per_kwh = _as_float(charge) if charge and "kwh" in str(charge).lower() else None
    if per_kwh is not None:
        return Pricing(model=PricingModel.PER_KWH, per_kwh=per_kwh)
    if fee in _TRUE:
        return Pricing(model=PricingModel.UNKNOWN, notes=charge)
    return Pricing()


def _parse_payment(tags: dict[str, str]) -> set[PaymentMethod]:
    methods: set[PaymentMethod] = set()
    for key, value in tags.items():
        if not key.startswith("payment:") or str(value).lower() not in _TRUE:
            continue
        kind = key.split(":", 1)[1].lower()
        if "upi" in kind:
            methods.add(PaymentMethod.UPI)
        elif "card" in kind or kind in {"visa", "mastercard", "debit_cards", "credit_cards"}:
            methods.add(PaymentMethod.CARD)
        elif "app" in kind:
            methods.add(PaymentMethod.APP)
        elif "rfid" in kind:
            methods.add(PaymentMethod.RFID)
        elif "cash" in kind:
            methods.add(PaymentMethod.CASH)
    return methods


# --------------------------------------------------------------------------- #
# Connector
# --------------------------------------------------------------------------- #


@register
class OSMChargingConnector(BaseConnector):
    """Charging stations from OpenStreetMap via Overpass."""

    vendor: ClassVar[str] = "osm"
    display_name: ClassVar[str] = "OpenStreetMap"
    tier: ClassVar[SourceTier] = SourceTier.OSM
    access_mode: ClassVar[AccessMode] = AccessMode.OPEN_DATA
    terms_url: ClassVar[str] = "https://www.openstreetmap.org/copyright"

    #: Courtesy delay between state queries (Overpass is a shared resource).
    request_delay_s: float = 2.0
    query_timeout_s: int = 180
    max_retries: int = 4
    retry_backoff_s: float = 3.0

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        super().__init__(config)
        self.states: tuple[str, ...] = tuple(self.config.get("states") or INDIAN_STATES)
        self.endpoint: str = self.config.get("endpoint") or os.environ.get(
            "OVERPASS_URL", OVERPASS_ENDPOINTS[0]
        )

    async def download(self) -> Iterable[dict[str, Any]]:
        """Query Overpass state by state, tagging each element with its state."""
        elements: list[dict[str, Any]] = []
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self.query_timeout_s + 30),
            headers={"User-Agent": "ev2ev-charging-etl/1.0 (+https://ev2ev.in)"},
        ) as client:
            for index, state in enumerate(self.states):
                payload = await self._query_state(client, state)
                if payload is None:
                    continue

                for element in payload.get("elements", []):
                    element["_query_state"] = state
                    elements.append(element)

                if index + 1 < len(self.states):
                    await asyncio.sleep(self.request_delay_s)
        return elements

    async def _query_state(
        self, client: httpx.AsyncClient, state: str
    ) -> dict[str, Any] | None:
        """Run one state query, retrying transient Overpass failures.

        Overpass answers 429 (rate limited) and 504 (query slot exhausted)
        under load — both are transient and specific to large states like
        Maharashtra. Retrying with backoff and rotating mirrors recovers
        them; without this, the biggest markets are silently missing.
        """
        endpoints = [self.endpoint] + [e for e in OVERPASS_ENDPOINTS if e != self.endpoint]
        query = _QUERY_TEMPLATE.format(state=state, timeout=self.query_timeout_s)
        last_error: str = ""

        for attempt in range(self.max_retries):
            endpoint = endpoints[attempt % len(endpoints)]
            try:
                resp = await client.post(endpoint, data={"data": query})
                if resp.status_code in {429, 504, 502, 503}:
                    last_error = f"HTTP {resp.status_code} from {endpoint}"
                    await asyncio.sleep(self.retry_backoff_s * (2**attempt))
                    continue
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                last_error = str(exc).splitlines()[0]
                await asyncio.sleep(self.retry_backoff_s * (2**attempt))

        self.stats.errors.append(f"{state}: {last_error} (after {self.max_retries} attempts)")
        return None

    def transform(self, raw: dict[str, Any]) -> Station | None:
        tags: dict[str, str] = raw.get("tags") or {}
        if tags.get("amenity") != "charging_station":
            return None

        # Nodes carry lat/lon directly; ways/relations carry a `center`
        # because the query used `out center`.
        lat = raw.get("lat")
        lon = raw.get("lon")
        if lat is None or lon is None:
            centre = raw.get("center") or {}
            lat, lon = centre.get("lat"), centre.get("lon")
        if lat is None or lon is None:
            return None

        osm_type = raw.get("type", "node")
        osm_id = raw.get("id")
        if osm_id is None:
            return None

        # Canonicalise at the source boundary so every downstream consumer
        # sees one spelling per operator/state (OSM alone yields six "Tata"s).
        operator = canonical_operator(
            tags.get("operator") or tags.get("brand") or tags.get("network")
        )
        raw_state = tags.get("addr:state") or raw.get("_query_state") or ""
        state = canonical_state(raw_state) or raw_state

        amenities: set[Amenity] = set()
        for tag_key, amenity in _AMENITY_TAGS.items():
            if str(tags.get(tag_key, "")).lower() in _TRUE:
                amenities.add(amenity)
        if str(tags.get("covered", "")).lower() in _TRUE:
            amenities.add(Amenity.PARKING)

        vehicles: set[VehicleType] = set()
        for tag_key, vehicle in _VEHICLE_TAGS.items():
            if str(tags.get(tag_key, "")).lower() in _TRUE:
                vehicles.add(vehicle)

        opening = tags.get("opening_hours")
        return Station(
            vendor=self.vendor,
            vendor_station_id=f"{osm_type[0]}{osm_id}",  # n123 / w456 / r789
            source_tier=self.tier,
            operator=operator,
            name=tags.get("name") or operator or "Charging Station",
            description=tags.get("description"),
            latitude=float(lat),
            longitude=float(lon),
            address=Address(
                line1=" ".join(
                    p for p in (tags.get("addr:housenumber"), tags.get("addr:street")) if p
                ),
                city=tags.get("addr:city") or "",
                district=tags.get("addr:district"),
                state=state,
                pin_code=tags.get("addr:postcode"),
            ),
            connectors=_parse_connectors(tags),
            vehicle_types=vehicles,
            pricing=_parse_pricing(tags),
            payment_methods=_parse_payment(tags),
            amenities=amenities,
            opening_hours={"raw": opening} if opening else None,
            is_24x7=(opening or "").strip() == "24/7",
            free_parking=str(tags.get("parking:fee", "")).lower() in {"no", "free"},
            supports_ocpp=str(tags.get("ocpp", "")).lower() in _TRUE,
            external_ids={"osm": f"{osm_type}/{osm_id}"},
            raw=tags,
        )

    def validate(self, station: Station) -> bool:
        """Keep any mapped charging point that has a usable position.

        An earlier revision required a name/operator or connector detail and
        rejected 54% of live OSM data. That was wrong: a charger someone
        mapped without a name is still a real charger a driver can use, and
        it is still a valid dedupe target for a richer operator feed later.
        Thin records are expressed through ``completeness``, not discarded.
        """
        return bool(station.vendor_station_id)
