"""RING place lookup — maps a Vogelring place name to its RING place + coordinates.

The mapping is maintained by Ingo in RING's geo-table export and baked into
``src/data/ring_places.json`` by ``scripts/build_ring_places.py``. The Wiederfunde
export uses it to attach the RING place name and coordinates so the Vogelwarte can
import place identity automatically instead of matching names by hand.

Place names are matched on a normalized key (whitespace collapsed, casefolded), so
minor spacing/casing differences still resolve. Unmatched places return None and the
export simply leaves the RING columns blank.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

_DATA_DIR = Path(__file__).resolve().parent.parent / "data"
_DATA_PATH = _DATA_DIR / "ring_places.json"
_GEO_PATH = _DATA_DIR / "ring_geo.json"

# Max distance for the GPS-nearest "smart" fallback.
SMART_MATCH_MAX_METERS = 500.0

# Geographic common nouns + city qualifiers that don't identify a specific place,
# so they don't count as a distinctive name overlap on their own.
_STOP_TOKENS = {
    "f", "ffm", "frankfurt", "bad", "homburg", "nsg",
    "weiher", "see", "teich", "park", "ufer", "mainufer", "main", "nidda",
    "anlage", "staustufe", "bruecke", "brücke", "insel", "hafen", "wiese",
    "ried", "altarm", "graben", "klärwerk", "klaerwerk", "kläranlage",
    "stadtpark", "damm", "nord", "süd", "sued", "ost", "west", "mitte",
}


@dataclass(frozen=True)
class RingPlace:
    vogelring_place: str
    ring_place: str
    lat: float
    lon: float


def normalize(name: str | None) -> str:
    """Normalize a place name for matching (collapse whitespace, casefold)."""
    if not name:
        return ""
    return " ".join(str(name).split()).casefold()


@lru_cache(maxsize=1)
def _load() -> dict[str, RingPlace]:
    if not _DATA_PATH.exists():
        return {}
    raw = json.loads(_DATA_PATH.read_text(encoding="utf-8"))
    return {
        key: RingPlace(
            vogelring_place=v.get("vogelring_place", ""),
            ring_place=v.get("ring_place", ""),
            lat=v["lat"],
            lon=v["lon"],
        )
        for key, v in raw.items()
    }


def lookup_place(vogelring_place: str | None) -> Optional[RingPlace]:
    """Return the explicit (Ingo-curated) RING place for a Vogelring name, else None."""
    return _load().get(normalize(vogelring_place))


@lru_cache(maxsize=1)
def _load_geo() -> list[RingPlace]:
    """All RING places with coordinates (for the GPS-nearest fallback)."""
    if not _GEO_PATH.exists():
        return []
    raw = json.loads(_GEO_PATH.read_text(encoding="utf-8"))
    return [
        RingPlace(vogelring_place="", ring_place=g["ring_place"], lat=g["lat"], lon=g["lon"])
        for g in raw
    ]


def _haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in metres."""
    r = 6371000.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def _core_and_distinctive(name: str) -> tuple[str, list[str]]:
    """Return (space-stripped core, distinctive tokens) for name-overlap matching.

    RING names carry a suffix like ``*[DEED, 5818]`` — dropped. Distinctive tokens
    are the specific name parts (>=4 chars, not a generic geo/city word), used to
    detect overlap even across German compound spellings ("Bethmannweiher" vs
    "Bethmann Weiher").
    """
    s = name.casefold()
    s = re.split(r"[\*\[\(]", s, maxsplit=1)[0]  # drop RING suffix code
    tokens = [t for t in re.split(r"[^0-9a-zäöüß]+", s) if t]
    core = "".join(tokens)
    distinctive = [
        t for t in tokens if len(t) >= 4 and not t.isdigit() and t not in _STOP_TOKENS
    ]
    return core, distinctive


def names_overlap(name_a: str, name_b: str) -> bool:
    """True if the two place names share a distinctive token (substring-aware)."""
    core_a, dist_a = _core_and_distinctive(name_a)
    core_b, dist_b = _core_and_distinctive(name_b)
    if any(t in core_b for t in dist_a):
        return True
    if any(t in core_a for t in dist_b):
        return True
    return False


def smart_match_place(
    vogelring_place: str | None, lat: float | None, lon: float | None
) -> Optional[RingPlace]:
    """GPS-nearest fallback: closest RING place within ``SMART_MATCH_MAX_METERS`` whose
    name shows a noticeable overlap with the Vogelring place name. None otherwise.

    Only for places without an explicit mapping; requires the sighting's own coords.
    Callers should flag the result as auto-suggested (unverified).
    """
    if lat is None or lon is None or not vogelring_place:
        return None
    lat, lon = float(lat), float(lon)
    candidates = []
    for place in _load_geo():
        dist = _haversine_m(lat, lon, place.lat, place.lon)
        if dist <= SMART_MATCH_MAX_METERS:
            candidates.append((dist, place))
    # Nearest first; return the closest one that also matches by name.
    for _dist, place in sorted(candidates, key=lambda c: c[0]):
        if names_overlap(vogelring_place, place.ring_place):
            return place
    return None
