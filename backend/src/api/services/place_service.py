"""
Place service: map-first place suggestions and plausibility checks.

Both features work on the recorded positions of previous sightings (place +
area + coordinates) and ringings (place + coordinates). The datasets are small
(low tens of thousands of rows), so distances are computed in Python with the
shared Haversine helper instead of in SQL.
"""

import logging
from collections import defaultdict
from dataclasses import dataclass
from datetime import date
from typing import Dict, List, Optional, Tuple

from sqlalchemy.orm import Session

from ...database.models import Ringing as RingingDB, Sighting as SightingDB
from ...utils.distance import calculate_distance

logger = logging.getLogger(__name__)

# A place is treated as "known here" if the new marker lies within its typical
# radius plus this tolerance. Typical radius never goes below the minimum.
MIN_TYPICAL_RADIUS_M = 250.0
WARNING_TOLERANCE_M = 500.0
TYPICAL_RADIUS_PERCENTILE = 0.9


@dataclass(frozen=True)
class Position:
    place: str
    area: Optional[str]
    lat: float
    lon: float
    date: Optional[date]


@dataclass
class NearbyPlace:
    place: str
    area: Optional[str]
    distance_m: float
    count: int
    last_date: Optional[date]
    center_lat: float
    center_lon: float


@dataclass
class PlaceCheck:
    known: bool
    count: int
    nearest_m: Optional[float]
    typical_radius_m: Optional[float]
    warning: bool
    message: Optional[str]


def _clean(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    value = value.strip()
    return value or None


def _percentile(values: List[float], fraction: float) -> float:
    """Nearest-rank percentile; values need not be sorted."""
    if not values:
        return 0.0
    ordered = sorted(values)
    index = max(0, min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1)))))
    return ordered[index]


def format_distance_de(distance_m: float) -> str:
    """Format metres for German UI text: '850 m' or '2,3 km'."""
    if distance_m < 1000:
        return f"{int(round(distance_m / 10.0) * 10)} m"
    km = distance_m / 1000.0
    text = f"{km:.1f}" if km < 10 else f"{km:.0f}"
    return f"{text.replace('.', ',')} km"


class PlaceService:
    """Nearby-place suggestions and place/position plausibility checks."""

    def __init__(self, db: Session):
        self.db = db

    # ---- data access -------------------------------------------------------

    def load_positions(self, org_id) -> List[Position]:
        """All recorded (place, area, lat, lon, date) tuples of an organization."""
        positions: List[Position] = []

        sighting_rows = (
            self.db.query(
                SightingDB.place,
                SightingDB.area,
                SightingDB.lat,
                SightingDB.lon,
                SightingDB.date,
            )
            .filter(SightingDB.org_id == org_id)
            .filter(SightingDB.place.isnot(None))
            .filter(SightingDB.place != "")
            .filter(SightingDB.lat.isnot(None))
            .filter(SightingDB.lon.isnot(None))
            .all()
        )
        for place, area, lat, lon, when in sighting_rows:
            place = _clean(place)
            if place is None:
                continue
            positions.append(Position(place, _clean(area), float(lat), float(lon), when))

        ringing_rows = (
            self.db.query(RingingDB.place, RingingDB.lat, RingingDB.lon, RingingDB.date)
            .filter(RingingDB.org_id == org_id)
            .filter(RingingDB.place.isnot(None))
            .filter(RingingDB.place != "")
            .filter(RingingDB.lat.isnot(None))
            .filter(RingingDB.lon.isnot(None))
            .all()
        )
        for place, lat, lon, when in ringing_rows:
            place = _clean(place)
            if place is None:
                continue
            positions.append(Position(place, None, float(lat), float(lon), when))

        return positions

    # ---- nearby suggestions ------------------------------------------------

    def nearby(
        self, org_id, lat: float, lon: float, limit: int = 8, radius_km: float = 5.0
    ) -> List[NearbyPlace]:
        """Known (place, area) combinations closest to a position, nearest first."""
        groups: Dict[Tuple[str, Optional[str]], List[Tuple[Position, float]]] = defaultdict(list)
        for pos in self.load_positions(org_id):
            distance = calculate_distance(lat, lon, pos.lat, pos.lon)
            groups[(pos.place, pos.area)].append((pos, distance))

        radius_m = radius_km * 1000.0
        results: List[NearbyPlace] = []
        for (place, area), entries in groups.items():
            nearest = min(distance for _, distance in entries)
            if nearest > radius_m:
                continue
            dates = [p.date for p, _ in entries if p.date is not None]
            results.append(
                NearbyPlace(
                    place=place,
                    area=area,
                    distance_m=round(nearest, 1),
                    count=len(entries),
                    last_date=max(dates) if dates else None,
                    center_lat=sum(p.lat for p, _ in entries) / len(entries),
                    center_lon=sum(p.lon for p, _ in entries) / len(entries),
                )
            )

        # Nearest first; for equal distances prefer the more frequently used name.
        results.sort(key=lambda r: (r.distance_m, -r.count, r.place, r.area or ""))
        return results[:limit]

    # ---- plausibility check ------------------------------------------------

    def check(self, org_id, place: str, lat: float, lon: float) -> PlaceCheck:
        """Compare a chosen place name with where that place was recorded before."""
        wanted = (_clean(place) or "").casefold()
        if not wanted:
            return PlaceCheck(False, 0, None, None, False, None)

        matching = [p for p in self.load_positions(org_id) if p.place.casefold() == wanted]
        if not matching:
            return PlaceCheck(False, 0, None, None, False, None)

        nearest_m = min(calculate_distance(lat, lon, p.lat, p.lon) for p in matching)

        center_lat = sum(p.lat for p in matching) / len(matching)
        center_lon = sum(p.lon for p in matching) / len(matching)
        spread = [calculate_distance(center_lat, center_lon, p.lat, p.lon) for p in matching]
        typical_radius_m = max(MIN_TYPICAL_RADIUS_M, _percentile(spread, TYPICAL_RADIUS_PERCENTILE))

        warning = nearest_m > typical_radius_m + WARNING_TOLERANCE_M
        message = None
        if warning:
            display_name = _clean(place) or place
            message = (
                f"Hinweis: ‚{display_name}‘ wurde bisher etwa "
                f"{format_distance_de(nearest_m)} von hier eingetragen."
            )

        return PlaceCheck(
            known=True,
            count=len(matching),
            nearest_m=round(nearest_m, 1),
            typical_radius_m=round(typical_radius_m, 1),
            warning=warning,
            message=message,
        )
