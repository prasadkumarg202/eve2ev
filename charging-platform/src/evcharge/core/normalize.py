"""Canonicalisation of state and operator names.

Real feeds disagree about spelling. A single OSM pull produced ``TN`` and
``Tamil Nadu``; ``TATA``/``Tata power``/``Tata Power EZ Charge``;
``Ather``/``Ather Energy``/``Ather Grid``. Left alone these fragment the
data: area filters miss stations and one operator appears as six.

Matching is **token-aware, never substring**. ``"Solar Powered Charging
Station"`` contains the substring ``ola`` — a naive ``%ola%`` match folds it
into Ola Electric. Everything here matches on normalised whole tokens.
"""

from __future__ import annotations

import re
import unicodedata

__all__ = [
    "canonical_state",
    "canonical_operator",
    "normalize_name",
    "slugify",
]

_NON_ALNUM = re.compile(r"[^a-z0-9]+")

#: Generic suffixes that carry no identity, stripped before operator matching.
_NOISE_TOKENS = frozenset(
    {
        "charging", "station", "stations", "charger", "chargers", "ev",
        "evs", "electric", "point", "points", "hub", "grid", "network",
        "networks", "energy", "energies", "mobility", "power", "powered",
        "solutions", "services", "pvt", "private", "ltd", "limited", "india",
        "charge", "charging point", "fast", "hypercharger", "supercharger",
    }
)


def normalize_name(value: str | None) -> str:
    """Lowercase, strip accents, collapse to single-spaced alphanumerics."""
    if not value:
        return ""
    decomposed = unicodedata.normalize("NFKD", value)
    ascii_only = "".join(c for c in decomposed if not unicodedata.combining(c))
    return _NON_ALNUM.sub(" ", ascii_only.lower()).strip()


def slugify(value: str | None, max_len: int = 60) -> str:
    return _NON_ALNUM.sub("-", normalize_name(value)).strip("-")[:max_len]


def _identity_tokens(value: str) -> tuple[str, ...]:
    """Meaningful tokens of a name, with generic charging words removed."""
    tokens = [t for t in normalize_name(value).split() if t not in _NOISE_TOKENS]
    return tuple(tokens)


# --------------------------------------------------------------------------- #
# States and union territories
# --------------------------------------------------------------------------- #

#: Canonical name -> accepted aliases (normalised on load).
_STATE_ALIASES: dict[str, tuple[str, ...]] = {
    "Andhra Pradesh": ("ap", "andhra"),
    "Arunachal Pradesh": ("ar", "arunachal"),
    "Assam": ("as",),
    "Bihar": ("br",),
    "Chhattisgarh": ("cg", "chattisgarh", "chhatisgarh"),
    "Goa": ("ga",),
    "Gujarat": ("gj", "gujrat"),
    "Haryana": ("hr",),
    "Himachal Pradesh": ("hp", "himachal"),
    "Jharkhand": ("jh", "jharkand"),
    "Karnataka": ("ka", "karnatka", "karnataka state"),
    "Kerala": ("kl",),
    "Madhya Pradesh": ("mp", "madhya"),
    "Maharashtra": ("mh", "maharastra"),
    "Manipur": ("mn",),
    "Meghalaya": ("ml",),
    "Mizoram": ("mz",),
    "Nagaland": ("nl",),
    "Odisha": ("od", "or", "orissa"),
    "Punjab": ("pb",),
    "Rajasthan": ("rj", "rajastan"),
    "Sikkim": ("sk",),
    "Tamil Nadu": ("tn", "tamilnadu", "tamil nadu state"),
    "Telangana": ("tg", "ts", "telengana"),
    "Tripura": ("tr",),
    "Uttar Pradesh": ("up",),
    "Uttarakhand": ("uk", "ua", "uttaranchal"),
    "West Bengal": ("wb", "bengal"),
    "Delhi": ("dl", "nct of delhi", "new delhi", "national capital territory of delhi"),
    "Jammu and Kashmir": ("jk", "j k", "jammu kashmir"),
    "Ladakh": ("la",),
    "Puducherry": ("py", "pondicherry"),
    "Chandigarh": ("ch",),
    "Andaman and Nicobar Islands": ("an", "andaman nicobar", "andaman"),
    "Dadra and Nagar Haveli and Daman and Diu": ("dn", "dd", "daman diu"),
    "Lakshadweep": ("ld",),
}

_STATE_LOOKUP: dict[str, str] = {}
for _canonical, _aliases in _STATE_ALIASES.items():
    _STATE_LOOKUP[normalize_name(_canonical)] = _canonical
    for _alias in _aliases:
        _STATE_LOOKUP[normalize_name(_alias)] = _canonical


def canonical_state(value: str | None) -> str | None:
    """Return the canonical state/UT name, or ``None`` if unrecognised.

    ``None`` rather than the input: an unrecognised value is a data-quality
    signal worth surfacing, not something to pass through and pollute filters.
    """
    key = normalize_name(value)
    if not key:
        return None
    return _STATE_LOOKUP.get(key)


# --------------------------------------------------------------------------- #
# Charge point operators
# --------------------------------------------------------------------------- #

#: Canonical operator -> identity tokens that unambiguously identify it.
#: Keys are matched against *token sets*, so "Solar Powered Charging Station"
#: (tokens: {solar}) never collides with Ola (tokens: {ola}).
_OPERATOR_ALIASES: dict[str, tuple[str, ...]] = {
    "Tata Power": ("tata", "tata ez", "tata ez charge"),
    "Jio-bp Pulse": ("jio", "jio bp", "jiobp", "jio bp pulse", "pulse"),
    "Ather Grid": ("ather",),
    "Statiq": ("statiq",),
    "ChargeZone": ("chargezone", "charge zone"),
    "Bolt.Earth": ("bolt", "bolt earth", "boltearth"),
    "Zeon Charging": ("zeon",),
    "Kazam": ("kazam",),
    "GLIDA": ("glida", "fortum glida"),
    "Fortum": ("fortum",),
    "ElectriVa": ("electriva", "electri va"),
    "ChargeMOD": ("chargemod", "charge mod"),
    "Relux": ("relux", "relux electric"),
    "EVRE": ("evre",),
    "Magenta": ("magenta", "magenta chargegrid", "chargegrid"),
    "Sun Mobility": ("sun", "sunmobility"),
    "Ola Electric": ("ola",),
    "Hero Vida": ("vida", "hero vida", "hero"),
    "Honda e:swap": ("honda", "honda e swap", "honda eswap"),
    "BluSmart": ("blusmart", "blu smart"),
    "GoEC": ("goec", "go ec"),
    "goEgo": ("goego", "go ego"),
    "Shell": ("shell", "shell recharge"),
    "Indian Oil": ("indianoil", "indian oil", "iocl", "indian oils"),
    "Bharat Petroleum": ("bharat petroleum", "bpcl", "bharat"),
    "Hindustan Petroleum": ("hindustan petroleum", "hpcl", "hindustan"),
    "Nayara": ("nayara",),
    "Adani": ("adani", "adani total"),
    "Gentari": ("gentari",),
    "Tesla": ("tesla",),
    "Hyundai": ("hyundai",),
    "Mercedes-Benz": ("mercedes", "mercedes benz"),
    "Porsche": ("porsche", "porsche destination"),
    "PowerGrid": ("powergrid",),
    "EESL": ("eesl",),
    "BESCOM": ("bescom",),
    "KSEB": ("kseb", "kerala state board", "kerala state"),
    "KPTCL": ("kptcl",),
    "CESC": ("cesc",),
    "Mahavitaran": ("mahavitaran", "msedcl"),
    "Exicom": ("exicom",),
    "Okaya": ("okaya",),
    "Yulu": ("yulu",),
    "Zevfy": ("zevfy",),
    "Uplug": ("uplug",),
    "Bijlify": ("bijlify",),
    "Indofast": ("indofast",),
    "Sheru": ("sheru",),
    "Chargigo": ("chargigo",),
    "Numocity": ("numocity",),
}

#: token-tuple -> canonical operator name
_OPERATOR_LOOKUP: dict[tuple[str, ...], str] = {}
for _canonical, _aliases in _OPERATOR_ALIASES.items():
    _OPERATOR_LOOKUP.setdefault(_identity_tokens(_canonical), _canonical)
    for _alias in _aliases:
        _OPERATOR_LOOKUP.setdefault(_identity_tokens(_alias), _canonical)


def canonical_operator(value: str | None) -> str | None:
    """Fold an operator name onto its canonical form.

    Returns the original (title-cased) name when nothing matches — unlike
    states, an unknown operator is usually a genuine small business rather
    than a typo, so it is kept rather than dropped.
    """
    if not value or not value.strip():
        return None

    tokens = _identity_tokens(value)
    if not tokens:
        # Name was entirely generic ("EV Charging Station") — no identity.
        return None

    if tokens in _OPERATOR_LOOKUP:
        return _OPERATOR_LOOKUP[tokens]

    # Single distinctive token, e.g. "Ather Charging Grid" -> ("ather",)
    if len(tokens) == 1 and (tokens[0],) in _OPERATOR_LOOKUP:
        return _OPERATOR_LOOKUP[(tokens[0],)]

    # Leading-token match: "Statiq Nandagav" -> Statiq. Only accepted when the
    # leading token alone is a known operator, so multi-word business names
    # are not wrongly folded.
    if (tokens[0],) in _OPERATOR_LOOKUP:
        return _OPERATOR_LOOKUP[(tokens[0],)]

    return " ".join(w.capitalize() for w in value.split())
