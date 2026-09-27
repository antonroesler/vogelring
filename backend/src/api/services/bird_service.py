"""
Bird service layer for bird-centric operations (bird meta by ring)
"""

from collections import Counter
import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session

from ...database.repositories import (
    ColorRingRepository,
    SightingRepository,
    RingingRepository,
)
from ...database.family_repository import FamilyRepository
from ...database.models import ColorRing
from ...utils.color_rings import matches_pattern, parse_ring_query

logger = logging.getLogger(__name__)


class BirdService:
    """Service for bird operations using PostgreSQL"""

    def __init__(self, db: Session):
        self.db = db
        self.sighting_repository = SightingRepository(db)
        self.ringing_repository = RingingRepository(db)
        self.family_repository = FamilyRepository(db)
        self.color_ring_repository = ColorRingRepository(db)

    def get_bird_meta_by_ring(self, ring: str, org_id: str) -> Dict[str, Any]:
        """Get bird metadata for a specific ring in the shape expected by the frontend"""
        color_ring = self.color_ring_repository.get_by_ring(ring, org_id)
        if color_ring:
            sightings = self.color_ring_repository.get_sightings(color_ring)
        else:
            sightings = self.sighting_repository.get_by_ring(ring, org_id)
        return self._build_meta(ring, color_ring, sightings, org_id)

    def get_bird_meta_by_color_ring(
        self, color_ring_id: str, org_id: str
    ) -> Dict[str, Any] | None:
        """Get bird metadata for a bird identified by its color ring"""
        color_ring = self.color_ring_repository.get_by_id(color_ring_id, org_id)
        if not color_ring:
            return None
        sightings = self.color_ring_repository.get_sightings(color_ring)
        return self._build_meta(color_ring.ring, color_ring, sightings, org_id)

    def _build_meta(
        self,
        ring: str | None,
        color_ring: ColorRing | None,
        sightings: list,
        org_id: str,
    ) -> Dict[str, Any]:
        ringing = self.ringing_repository.get_by_ring(ring, org_id) if ring else None
        color_ring_dict = color_ring.to_dict() if color_ring else None

        if not sightings and not ringing:
            return {
                "ring": ring,
                "color_ring": color_ring_dict,
                "species": None,
                "sighting_count": 0,
                "last_seen": None,
                "first_seen": None,
                "sightings": [],
                "partners": [],
            }

        # Determine species (prefer most common in sightings, fallback to ringing data)
        species = None
        if len(sightings) > 0:
            species_counts = Counter(s.species for s in sightings if s.species)
            if species_counts:
                species = species_counts.most_common(1)[0][0]

        if not species and ringing:
            species = ringing.species

        # Calculate dates
        sighting_dates = [s.date for s in sightings if s.date]
        first_seen = min(sighting_dates) if sighting_dates else None
        last_seen = max(sighting_dates) if sighting_dates else None

        # Include ringing date in date calculations
        if ringing and ringing.date:
            if not first_seen or ringing.date < first_seen:
                first_seen = ringing.date
            if not last_seen or ringing.date > last_seen:
                last_seen = ringing.date

        # Other species identifications from sightings

        other_species = Counter(
            s.species for s in sightings if s.species and s.species != species
        )

        # Convert sightings to dict format with fields expected by frontend
        sighting_dicts = []
        for s in sightings:
            sighting_dicts.append(
                {
                    "id": str(s.id),
                    "excel_id": s.excel_id,
                    "species": s.species,
                    "ring": s.ring,
                    "reading": s.reading,
                    "color_ring_color": s.color_ring_color,
                    "color_ring_text_color": s.color_ring_text_color,
                    "color_ring_code": s.color_ring_code,
                    "date": s.date.isoformat() if s.date else None,
                    "place": s.place,
                    "area": s.area,
                    "lat": float(s.lat) if s.lat is not None else None,
                    "lon": float(s.lon) if s.lon is not None else None,
                    "is_exact_location": s.is_exact_location,
                    "partner": s.partner,
                    "status": s.status,
                    "age": s.age,
                    "sex": s.sex,
                    "large_group_size": s.large_group_size,
                    "small_group_size": s.small_group_size,
                    "melder": s.melder,
                    "melded": s.melded,
                }
            )

        # Get partners from family tree (placeholder for now)
        partners = (
            self.family_repository.get_partners(org_id=org_id, bird_ring=ring)
            if ring
            else []
        )
        children = (
            self.family_repository.get_children(org_id=org_id, parent_ring=ring)
            if ring
            else []
        )

        return {
            "ring": ring,
            "color_ring": color_ring_dict,
            "species": species,
            "sighting_count": len(sightings),
            "last_seen": last_seen.isoformat() if last_seen else None,
            "first_seen": first_seen.isoformat() if first_seen else None,
            "other_species_identifications": dict(other_species)
            if other_species
            else None,
            "sightings": sighting_dicts,
            "partners": partners,
            "children": children,
        }

    def get_bird_suggestions_by_partial_reading(
        self, partial_reading: str, org_id: str
    ) -> List[Dict[str, Any]]:
        """Return bird suggestions for a partial ring reading.

        Matches metal rings and color rings. Accepts wildcards ("280*", "*35",
        "28*35") and an optional leading ring/text color ("rot H3E4",
        "rot/weiß H3*"). Without wildcards the reading matches a substring.
        """
        query = parse_ring_query(partial_reading)
        metal_pattern = "".join(query.tokens).upper()

        color_rings = self.color_ring_repository.get_all(org_id)
        sightings = self.sighting_repository.get_all(org_id)
        color_ring_by_ring = {cr.ring: cr for cr in color_rings if cr.ring}

        def color_ring_matches(cr: ColorRing) -> bool:
            if query.ring_color and cr.ring_color != query.ring_color:
                return False
            if query.text_color and cr.text_color not in (None, query.text_color):
                return False
            return matches_pattern(query.code_pattern, cr.code)

        # Birds keyed by metal ring, or by color ring id when the metal ring is unknown
        birds: Dict[str, Dict[str, Any]] = {}

        def bird_for(ring: str | None, cr: ColorRing | None) -> Dict[str, Any]:
            key = ring or f"cr:{cr.id}"
            if key not in birds:
                birds[key] = {
                    "ring": ring,
                    "color_ring": cr.to_dict() if cr else None,
                    "species": [],
                    "sighting_count": 0,
                    "last_seen": None,
                    "first_seen": None,
                }
            return birds[key]

        for cr in color_rings:
            if color_ring_matches(cr):
                bird_for(cr.ring, cr)
        if not query.has_color:
            for ring in {s.ring for s in sightings}:
                if ring and matches_pattern(metal_pattern, ring):
                    bird_for(ring, color_ring_by_ring.get(ring))

        color_only = {
            (cr.ring_color, cr.code): cr for cr in color_rings if not cr.ring
        }
        for sighting in sightings:
            key = sighting.ring
            if not key and sighting.color_ring_code:
                cr = color_only.get((sighting.color_ring_color, sighting.color_ring_code))
                key = f"cr:{cr.id}" if cr else None
            bird = birds.get(key) if key else None
            if not bird:
                continue
            bird["sighting_count"] += 1
            if sighting.species:
                bird["species"].append(sighting.species)
            bird["last_seen"] = self._max_or_none(bird["last_seen"], sighting.date)
            bird["first_seen"] = self._min_or_none(bird["first_seen"], sighting.date)

        suggestion_birds = []
        for bird in birds.values():
            species_counter = Counter(bird["species"])
            suggestion_birds.append(
                bird
                | {
                    "species": species_counter.most_common(1)[0][0]
                    if species_counter
                    else None,
                    "last_seen": bird["last_seen"].isoformat()
                    if bird["last_seen"]
                    else None,
                    "first_seen": bird["first_seen"].isoformat()
                    if bird["first_seen"]
                    else None,
                }
            )

        suggestion_birds.sort(key=lambda x: x["sighting_count"], reverse=True)
        return suggestion_birds[:30]

    def _max_or_none(self, a, b):
        """Return the maximum of two values, handling None values"""
        if a is None:
            return b
        if b is None:
            return a
        return max(a, b)

    def _min_or_none(self, a, b):
        """Return the minimum of two values, handling None values"""
        if a is None:
            return b
        if b is None:
            return a
        return min(a, b)
