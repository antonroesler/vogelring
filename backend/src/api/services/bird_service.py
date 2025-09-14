"""
Bird service layer for bird-centric operations (bird meta by ring)
"""
from collections import Counter
import logging
from typing import Dict, Any, List

from sqlalchemy.orm import Session

from ...database.repositories import SightingRepository, RingingRepository

logger = logging.getLogger(__name__)


class BirdService:
    """Service for bird operations using PostgreSQL"""

    def __init__(self, db: Session):
        self.db = db
        self.sighting_repository = SightingRepository(db)
        self.ringing_repository = RingingRepository(db)

    def get_bird_meta_by_ring(self, ring: str) -> Dict[str, Any]:
        """Get bird metadata for a specific ring in the shape expected by the frontend"""
        # Get all sightings for this ring
        sightings = self.sighting_repository.get_by_ring(ring)

        # Get ringing data if available
        ringing = self.ringing_repository.get_by_ring(ring)

        if not sightings and not ringing:
            return {
                "ring": ring,
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
                    "date": s.date.isoformat() if s.date else None,
                    "place": s.place,
                    "area": s.area,
                    "lat": float(s.lat) if s.lat is not None else None,
                    "lon": float(s.lon) if s.lon is not None else None,
                    "is_exact_location": s.is_exact_location,
                    "partner": s.partner,
                    "status": s.status,
                    "age": s.age,
                    "melder": s.melder,
                    "melded": s.melded,
                }
            )

        # Get partners from family tree (placeholder for now)
        partners: List[Dict[str, Any]] = []

        return {
            "ring": ring,
            "species": species,
            "sighting_count": len(sightings),
            "last_seen": last_seen.isoformat() if last_seen else None,
            "first_seen": first_seen.isoformat() if first_seen else None,
            "other_species_identifications": dict(other_species)
            if other_species
            else None,
            "sightings": sighting_dicts,
            "partners": partners,
        }

    def get_bird_suggestions_by_partial_reading(
        self, partial_reading: str
    ) -> List[Dict[str, Any]]:
        """Return a list of bird suggestions by partial ring reading.
        Partial reading can be only front, back, outer or middle reading."""

        # Normalize partial reading (replace ... and … with *)
        partial_reading = partial_reading.replace("...", "*").replace("…", "*")

        # Get all sightings from the database
        all_sightings = self.sighting_repository.get_all()

        suggestions = {}

        for sighting in all_sightings:
            if len(suggestions) >= 30:  # Limit to 30 suggestions
                break

            if sighting.ring and self._is_suggestion(partial_reading, sighting.ring):
                if sighting.ring not in suggestions:
                    suggestions[sighting.ring] = {
                        "ring": sighting.ring,
                        "species": [sighting.species],
                        "sighting_count": 1,
                        "last_seen": sighting.date,
                        "first_seen": sighting.date,
                    }
                else:
                    suggestions[sighting.ring]["sighting_count"] += 1
                    suggestions[sighting.ring]["species"].append(sighting.species)
                    suggestions[sighting.ring]["last_seen"] = self._max_or_none(
                        suggestions[sighting.ring]["last_seen"], sighting.date
                    )
                    suggestions[sighting.ring]["first_seen"] = self._min_or_none(
                        suggestions[sighting.ring]["first_seen"], sighting.date
                    )

        # Convert to the expected format
        suggestion_birds = []
        for suggestion in suggestions.values():
            # Find most common species
            from collections import Counter

            species_counter = Counter(suggestion["species"])
            most_common_species = (
                species_counter.most_common(1)[0][0] if species_counter else None
            )

            suggestion_birds.append(
                {
                    "ring": suggestion["ring"],
                    "species": most_common_species,
                    "sighting_count": suggestion["sighting_count"],
                    "last_seen": suggestion["last_seen"].isoformat()
                    if suggestion["last_seen"]
                    else None,
                    "first_seen": suggestion["first_seen"].isoformat()
                    if suggestion["first_seen"]
                    else None,
                }
            )

        # Sort by sighting count descending
        return sorted(suggestion_birds, key=lambda x: x["sighting_count"], reverse=True)

    def _is_suggestion(self, partial_reading: str, ring: str) -> bool:
        """Check if a ring matches the partial reading pattern"""
        # Case 1: Partial reading is missing both outer endings *8043*
        if partial_reading.startswith("*") and partial_reading.endswith("*"):
            if partial_reading[1:-1] in ring:
                return True
        # Case 2: Partial reading is missing ending 280*
        elif partial_reading.endswith("*"):
            if ring.startswith(partial_reading[:-1]):
                return True
        # Case 3: Partial reading is missing starting *35
        elif partial_reading.startswith("*"):
            if ring.endswith(partial_reading[1:]):
                return True
        # Case 4: Partial reading is missing middle 28*35
        elif "*" in partial_reading:
            start, end = partial_reading.split("*", 1)  # Split only on first *
            if ring.startswith(start) and ring.endswith(end):
                return True
        return False

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
