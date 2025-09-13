"""
Bird service layer for bird-centric operations (bird meta by ring)
"""

import logging
from typing import Dict, Any

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

        # Determine species (prefer ringing data, fallback to most common in sightings)
        species = None
        if ringing:
            species = ringing.species
        elif sightings:
            from collections import Counter

            species_counts = Counter(s.species for s in sightings if s.species)
            if species_counts:
                species = species_counts.most_common(1)[0][0]

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
        from collections import Counter

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
        partners: list[dict] = []

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
