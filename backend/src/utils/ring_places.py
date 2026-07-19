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
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Optional

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "ring_places.json"


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
    """Return the RING place for a Vogelring place name, or None if unmatched."""
    return _load().get(normalize(vogelring_place))
