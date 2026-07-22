"""Canonical station schema.

Every connector normalises its vendor payload into :class:`Station`. This
module is the contract between sources and the rest of the platform — the
dedupe engine, the loaders, and the API all speak only this shape.

Design notes
------------
* **Enums, not free text.** Connector authors get an immediate validation
  error rather than silently writing ``"type-2"`` where the rest of the
  platform expects ``Type2``.
* **Provenance is mandatory.** ``vendor`` + ``vendor_station_id`` identify the
  upstream record; ``field_provenance`` records which source won each field
  after a merge. Without this, a wrong power rating is undebuggable.
* **Nothing is required except identity and position.** Real feeds are
  patchy: a station with only a name and a coordinate is still worth having.
  Quality is expressed via ``completeness`` rather than by rejecting rows.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# --------------------------------------------------------------------------- #
# Controlled vocabularies
# --------------------------------------------------------------------------- #


class ConnectorType(str, Enum):
    """Physical connector standards in use in India."""

    CCS2 = "CCS2"
    CHADEMO = "CHAdeMO"
    TYPE2 = "Type2"
    GBT = "GBT"
    BHARAT_AC001 = "BharatAC001"
    BHARAT_DC001 = "BharatDC001"
    THREE_PIN = "3Pin"  # ubiquitous on 2W/3W chargers
    UNKNOWN = "Unknown"


class ConnectorStatus(str, Enum):
    AVAILABLE = "available"
    OCCUPIED = "occupied"
    CHARGING = "charging"
    RESERVED = "reserved"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


class VehicleType(str, Enum):
    TWO_WHEELER = "2W"
    THREE_WHEELER = "3W"
    CAR = "4W"
    BUS = "bus"
    TRUCK = "truck"
    FLEET = "fleet"


class PaymentMethod(str, Enum):
    UPI = "UPI"
    CARD = "card"
    WALLET = "wallet"
    FASTAG = "FASTag"
    RFID = "RFID"
    APP = "app"
    CASH = "cash"
    FREE = "free"


class Amenity(str, Enum):
    RESTAURANT = "restaurant"
    DHABA = "dhaba"
    CAFE = "cafe"
    TEA = "tea"
    COFFEE = "coffee"
    FOOD_COURT = "food_court"
    HOTEL = "hotel"
    WASHROOM = "washroom"
    SHOPPING = "shopping"
    WIFI = "wifi"
    ATM = "atm"
    WHEELCHAIR = "wheelchair"
    SECURITY = "security"
    CCTV = "cctv"
    PARKING = "parking"
    LOUNGE = "lounge"


class PricingModel(str, Enum):
    FREE = "free"
    PER_KWH = "per_kwh"
    PER_MINUTE = "per_minute"
    PER_SESSION = "per_session"
    SUBSCRIPTION = "subscription"
    UNKNOWN = "unknown"


class SourceTier(int, Enum):
    """Trust ranking used to resolve conflicts during a merge.

    Lower wins. An operator describing its own hardware outranks a
    volunteer map edit, which outranks an unverified user submission.
    """

    OPERATOR = 1  # OCPI / official vendor API
    GOVERNMENT = 2  # BEE, data.gov.in, DISCOM
    OSM = 3  # OpenStreetMap
    PARTNER = 4  # bulk partner upload
    COMMUNITY = 5  # user submission, unverified


# --------------------------------------------------------------------------- #
# Value objects
# --------------------------------------------------------------------------- #


class Connector(BaseModel):
    """One physical gun."""

    model_config = ConfigDict(use_enum_values=False)

    connector_type: ConnectorType = ConnectorType.UNKNOWN
    power_kw: float | None = None
    status: ConnectorStatus = ConnectorStatus.UNKNOWN
    count: int = 1

    pricing_model: PricingModel = PricingModel.UNKNOWN
    price_per_kwh: float | None = None
    price_per_minute: float | None = None
    price_per_session: float | None = None

    vendor_connector_id: str | None = None
    last_status_update: datetime | None = None

    @field_validator("power_kw")
    @classmethod
    def _sane_power(cls, v: float | None) -> float | None:
        # Reject impossible ratings rather than storing them: 0 kW is
        # meaningless and >1 MW is a unit-conversion bug upstream (W vs kW).
        if v is None:
            return None
        if v <= 0 or v > 1000:
            return None
        return round(v, 2)

    @property
    def is_dc_fast(self) -> bool:
        return self.power_kw is not None and self.power_kw >= 50


class Address(BaseModel):
    """Postal address plus the admin hierarchy the OSM ETL resolves."""

    line1: str = ""
    line2: str | None = None
    landmark: str | None = None
    village: str | None = None
    town: str | None = None
    city: str = ""
    district: str | None = None
    state: str = ""
    country: str = "India"
    pin_code: str | None = None

    #: FK into the osm-india-etl location database, when resolved.
    osm_location_id: str | None = None

    @field_validator("pin_code")
    @classmethod
    def _valid_indian_pin(cls, v: str | None) -> str | None:
        """Indian PIN codes are exactly 6 digits and never start with 0."""
        if not v:
            return None
        digits = "".join(ch for ch in v if ch.isdigit())
        if len(digits) != 6 or digits[0] == "0":
            return None
        return digits


class Pricing(BaseModel):
    model: PricingModel = PricingModel.UNKNOWN
    per_kwh: float | None = None
    per_minute: float | None = None
    per_session: float | None = None
    parking_fee: float | None = None
    currency: str = "INR"
    notes: str | None = None


class Media(BaseModel):
    url: str
    caption: str | None = None
    source: str | None = None
    #: Google Places imagery may not be stored beyond its cache window.
    is_cacheable: bool = True


# --------------------------------------------------------------------------- #
# Station
# --------------------------------------------------------------------------- #


class Station(BaseModel):
    """The canonical record. Every connector emits these and nothing else."""

    model_config = ConfigDict(use_enum_values=False, validate_assignment=True)

    # ---- identity / provenance ----
    station_uuid: str | None = None  # assigned at load, after dedupe
    vendor: str  # connector slug, e.g. "osm"
    vendor_station_id: str  # id within that vendor's namespace
    source_tier: SourceTier = SourceTier.COMMUNITY

    operator: str | None = None
    operator_slug: str | None = None

    # ---- descriptive ----
    name: str = ""
    description: str | None = None

    # ---- position (the only truly required data) ----
    latitude: float
    longitude: float

    address: Address = Field(default_factory=Address)

    # ---- hardware ----
    connectors: list[Connector] = Field(default_factory=list)
    vehicle_types: set[VehicleType] = Field(default_factory=set)

    # ---- commercial ----
    pricing: Pricing = Field(default_factory=Pricing)
    payment_methods: set[PaymentMethod] = Field(default_factory=set)
    amenities: set[Amenity] = Field(default_factory=set)
    opening_hours: dict[str, str] | None = None
    is_24x7: bool = False
    free_parking: bool = False

    # ---- interop ----
    supports_ocpi: bool = False
    supports_ocpp: bool = False
    roaming_enabled: bool = False

    # ---- social ----
    photos: list[Media] = Field(default_factory=list)
    rating: float | None = None
    review_count: int = 0

    # ---- lifecycle ----
    is_verified: bool = False
    is_operational: bool = True
    raw: dict[str, Any] = Field(default_factory=dict, repr=False)
    external_ids: dict[str, str] = Field(default_factory=dict)
    field_provenance: dict[str, str] = Field(default_factory=dict)
    merge_confidence: float | None = None

    first_seen: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # ---- validation ----
    @model_validator(mode="after")
    def _coordinates_within_india(self) -> Station:
        """Reject coordinates outside India's bounding box.

        Swapped lat/lon is the single most common defect in EV feeds — a
        Bengaluru station arriving as (77.59, 12.97) lands in Uzbekistan.
        Catching it here stops silent geographic corruption.
        """
        lat, lon = self.latitude, self.longitude
        if not (6.0 <= lat <= 37.5) or not (68.0 <= lon <= 97.5):
            if 6.0 <= lon <= 37.5 and 68.0 <= lat <= 97.5:
                raise ValueError(
                    f"coordinates outside India but valid when swapped "
                    f"(lat={lat}, lon={lon}) — likely lat/lon transposition"
                )
            raise ValueError(f"coordinates outside India: lat={lat}, lon={lon}")
        return self

    @field_validator("rating")
    @classmethod
    def _rating_range(cls, v: float | None) -> float | None:
        if v is None:
            return None
        if not 0 <= v <= 5:
            return None
        return round(v, 2)

    # ---- derived ----
    @property
    def total_guns(self) -> int:
        return sum(c.count for c in self.connectors)

    @property
    def available_guns(self) -> int:
        return sum(c.count for c in self.connectors if c.status is ConnectorStatus.AVAILABLE)

    @property
    def max_power_kw(self) -> float | None:
        powers = [c.power_kw for c in self.connectors if c.power_kw]
        return max(powers) if powers else None

    @property
    def connector_signature(self) -> frozenset[tuple[str, float | None]]:
        """Hardware fingerprint used by the dedupe engine.

        Two records describing the same physical site should agree on the
        connector mix even when their names and coordinates differ.
        """
        return frozenset((c.connector_type.value, c.power_kw) for c in self.connectors)

    @property
    def completeness(self) -> float:
        """Fraction of high-value fields populated (0..1).

        Drives source ranking during merges and surfaces thin feeds.
        """
        checks = (
            bool(self.name),
            bool(self.operator),
            bool(self.address.city),
            bool(self.address.state),
            bool(self.address.pin_code),
            bool(self.connectors),
            self.max_power_kw is not None,
            bool(self.amenities),
            bool(self.payment_methods),
            self.pricing.model is not PricingModel.UNKNOWN,
        )
        return round(sum(checks) / len(checks), 3)

    def merge_key(self) -> str:
        """Stable cross-run identity for this upstream record."""
        return f"{self.vendor}:{self.vendor_station_id}"
