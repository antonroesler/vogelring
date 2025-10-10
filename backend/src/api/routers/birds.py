"""
Birds API router
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...utils.auth import get_current_user, get_db_with_org
from ...database.user_models import User
from ..services.bird_service import BirdService

router = APIRouter()


@router.get("/birds/{ring}")
async def get_bird_by_ring(
    ring: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_with_org),
):
    """Get bird information by ring number

    Returns a BirdMeta-like structure expected by the frontend, including:
    - species (string or null)
    - ring (string)
    - sighting_count (int)
    - first_seen (ISO date or null)
    - last_seen (ISO date or null)
    - other_species_identifications (dict or null)
    - sightings (list of sightings with id, species, ring, date, place, lat, lon, area, status, age, reading, partner, is_exact_location)
    - partners (list, currently empty placeholder)
    """
    service = BirdService(db)
    bird = service.get_bird_meta_by_ring(ring)
    if not bird:
        # Fallback empty response
        return {
            "ring": ring,
            "species": None,
            "sighting_count": 0,
            "last_seen": None,
            "first_seen": None,
            "other_species_identifications": None,
            "sightings": [],
            "partners": [],
        }
    return bird


@router.get("/birds/suggestions/{partial_reading}")
async def get_bird_suggestions_by_partial_reading(
    partial_reading: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_with_org),
):
    """Get bird suggestions by partial ring reading"""
    if not partial_reading or len(partial_reading) < 2:
        raise HTTPException(
            status_code=400, detail="Partial reading must be at least 2 characters long"
        )

    # Add wildcards if not present
    if not any(c in partial_reading for c in ["*", "…", "..."]):
        partial_reading = f"*{partial_reading}*"

    # Get bird suggestions using the service
    service = BirdService(db)
    suggestions = service.get_bird_suggestions_by_partial_reading(partial_reading)

    return suggestions
