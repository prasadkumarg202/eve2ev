"""Phonetic encoders (metaphone / soundex).

Thin wrappers over :mod:`jellyfish` when it is installed, with a small pure
Python fallback so the search stack (and its tests) work without the optional
C-accelerated dependency.
"""

from __future__ import annotations

try:  # pragma: no cover - exercised only when jellyfish is installed
    import jellyfish as _jellyfish
except ImportError:  # pragma: no cover - fallback path covered by tests
    _jellyfish = None

__all__ = ["metaphone", "soundex", "phonetic_equal", "HAS_JELLYFISH"]

HAS_JELLYFISH = _jellyfish is not None

# Classic Soundex digit groups.
_SOUNDEX_CODES: dict[str, str] = {
    **dict.fromkeys("BFPV", "1"),
    **dict.fromkeys("CGJKQSXZ", "2"),
    **dict.fromkeys("DT", "3"),
    "L": "4",
    **dict.fromkeys("MN", "5"),
    "R": "6",
}

_VOWELS = set("AEIOU")


def _clean(s: str) -> str:
    """Uppercase and keep ASCII letters only."""
    return "".join(ch for ch in s.upper() if "A" <= ch <= "Z")


def soundex(s: str) -> str:
    """American Soundex code (e.g. ``soundex("Bengaluru") == "B524"``).

    Uses ``jellyfish.soundex`` when available, otherwise a pure-python
    implementation of the classic algorithm (H/W transparent, vowels reset).
    """
    if not s or not s.strip():
        return ""
    if _jellyfish is not None:
        try:
            return _jellyfish.soundex(s)
        except Exception:  # pragma: no cover - unexpected input for C impl
            pass
    return _soundex_py(s)


def _soundex_py(s: str) -> str:
    letters = _clean(s)
    if not letters:
        return ""
    first = letters[0]
    code = _SOUNDEX_CODES.get(first, "")
    out = [first]
    prev = code
    for ch in letters[1:]:
        digit = _SOUNDEX_CODES.get(ch, "")
        if ch in ("H", "W"):
            # H and W are transparent: they do not reset the previous code.
            continue
        if ch in _VOWELS:
            prev = ""
            continue
        if digit and digit != prev:
            out.append(digit)
            if len(out) == 4:
                break
        prev = digit
    return "".join(out).ljust(4, "0")


def metaphone(s: str) -> str:
    """Metaphone code; falls back to a simplified encoder without jellyfish.

    The fallback is not a full Metaphone implementation but a stable
    consonant-skeleton encoding good enough for candidate matching:
    common digraphs are folded (PH->F, SH/CH->X, CK->K, ...), vowels are
    dropped except a leading vowel, and duplicates collapsed.
    """
    if not s or not s.strip():
        return ""
    if _jellyfish is not None:
        try:
            return _jellyfish.metaphone(s)
        except Exception:  # pragma: no cover
            pass
    return _metaphone_py(s)


_DIGRAPHS: tuple[tuple[str, str], ...] = (
    ("PH", "F"),
    ("GH", "K"),
    ("SH", "X"),
    ("CH", "X"),
    ("TH", "0"),
    ("CK", "K"),
    ("SC", "S"),
    ("WH", "W"),
)


def _metaphone_py(s: str) -> str:
    letters = _clean(s)
    if not letters:
        return ""
    for old, new in _DIGRAPHS:
        letters = letters.replace(old, new)
    # Single-letter folds roughly mirroring metaphone.
    folds = str.maketrans({"C": "K", "Q": "K", "V": "F", "Z": "S", "G": "K", "D": "T", "Y": "", "W": ""})
    letters = letters.translate(folds)
    out: list[str] = []
    for i, ch in enumerate(letters):
        if ch in _VOWELS:
            if i == 0:
                out.append(ch)
            continue
        if out and out[-1] == ch:
            continue
        out.append(ch)
    return "".join(out)


def phonetic_equal(a: str, b: str) -> bool:
    """True when two strings share a metaphone or soundex code."""
    if not a or not b:
        return False
    ma, mb = metaphone(a), metaphone(b)
    if ma and ma == mb:
        return True
    sa, sb = soundex(a), soundex(b)
    return bool(sa) and sa == sb
