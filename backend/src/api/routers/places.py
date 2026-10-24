"""
Places API router
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ...database.connection import get_db
from ...database.user_models import User
from ...utils.auth import get_current_user
from ..services.place_service import PlaceService
from ..services.suggestion_service import SuggestionService

router = APIRouter()


class NearbyPlaceResponse(BaseModel):
    place: str
    area: Optional[str] = None
    distance_m: float
    count: int
    last_date: Optional[date] = None
    center_lat: float
    center_lon: float


class PlaceCheckResponse(BaseModel):
    known: bool
    count: int
    nearest_m: Optional[float] = None
    typical_radius_m: Optional[float] = None
    warning: bool
    message: Optional[str] = None


@router.get("/places", response_model=List[str])
async def get_place_name_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get list of all place names for autocomplete"""
    service = SuggestionService(db)
    return service.get_place_name_list(current_user.org_id)


@router.get("/places/nearby", response_model=List[NearbyPlaceResponse])
async def get_nearby_places(
    lat: float = Query(..., ge=-90, le=90, description="Latitude of the marker"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude of the marker"),
    limit: int = Query(8, ge=1, le=50),
    radius_km: float = Query(5.0, gt=0, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Known places/areas closest to a map position, nearest first.

    Based on where sightings (place + area) and ringings (place) with
    coordinates were recorded before. Lets a user place the marker first and
    pick the name they used for that spot years ago.
    """
    service = PlaceService(db)
    return service.nearby(current_user.org_id, lat, lon, limit=limit, radius_km=radius_km)


@router.get("/places/check", response_model=PlaceCheckResponse)
async def check_place_position(
    place: str = Query(..., min_length=1, description="Chosen place name"),
    lat: float = Query(..., ge=-90, le=90),
    lon: float = Query(..., ge=-180, le=180),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Check whether a marker position is plausible for a place name.

    `warning` is true when the position lies clearly outside the area where
    this place was recorded before (typical radius + 500 m tolerance). It is a
    hint only and never blocks saving.
    """
    service = PlaceService(db)
    return service.check(current_user.org_id, place, lat, lon)
