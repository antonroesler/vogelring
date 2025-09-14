"""
Sightings API router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from datetime import date as DateType
from pydantic import BaseModel, Field

from ...database.connection import get_db
from ..services.sighting_service import SightingService

router = APIRouter()


class SightingCreate(BaseModel):
    """Pydantic model for creating sightings"""
    excel_id: int | None = None
    comment: str | None = None
    species: str | None = None
    ring: str | None = None
    reading: str | None = None
    age: str | None = None
    sex: str | None = None
    date: DateType | None = None
    large_group_size: int | None = None
    small_group_size: int | None = None
    partner: str | None = None
    breed_size: int | None = None
    family_size: int | None = None
    pair: str | None = None
    status: str | None = None
    melder: str | None = None
    melded: bool | None = None
    place: str | None = None
    area: str | None = None
    lat: float | None = None
    lon: float | None = None
    is_exact_location: bool | None = False
    habitat: str | None = None
    field_fruit: str | None = None


class SightingUpdate(BaseModel):
    """Pydantic model for updating sightings"""
    id: str
    excel_id: int | None = None
    comment: str | None = None
    species: str | None = None
    ring: str | None = None
    reading: str | None = None
    age: str | None = None
    sex: str | None = None
    date: DateType | None = None
    large_group_size: int | None = None
    small_group_size: int | None = None
    partner: str | None = None
    breed_size: int | None = None
    family_size: int | None = None
    pair: str | None = None
    status: str | None = None
    melder: str | None = None
    melded: bool | None = None
    place: str | None = None
    area: str | None = None
    lat: float | None = None
    lon: float | None = None
    is_exact_location: bool | None = False
    habitat: str | None = None
    field_fruit: str | None = None


@router.get("/sightings/count")
async def get_sightings_count(db: Session = Depends(get_db)):
    """Get total count of sightings"""
    service = SightingService(db)
    return {"count": service.get_sightings_count()}


@router.get("/sightings/radius")
async def get_sightings_by_radius(
    lat: float = Query(..., description="Latitude"),
    lon: float = Query(..., description="Longitude"),
    radius_m: int = Query(..., description="Radius in meters"),
    db: Session = Depends(get_db)
):
    """Get sightings within a radius of a location"""
    service = SightingService(db)
    sightings = service.get_sightings_by_radius(lat, lon, radius_m)
    return sightings


@router.get("/sightings/statistics")
async def get_sightings_statistics(db: Session = Depends(get_db)):
    """Get sightings statistics"""
    service = SightingService(db)
    return service.get_statistics()


@router.get("/sightings/autocomplete/{field}")
async def get_autocomplete_suggestions(
    field: str,
    q: str = Query(..., description="Query string"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    db: Session = Depends(get_db)
):
    """Get autocomplete suggestions for a field"""
    service = SightingService(db)
    suggestions = service.get_autocomplete_suggestions(field, q, limit)
    return {"suggestions": suggestions}


@router.get("/sightings/{id}")
async def get_sighting_by_id(
    id: str,
    db: Session = Depends(get_db)
):
    """Get a specific sighting by ID"""
    service = SightingService(db)
    sighting = service.get_sighting_by_id(id)
    if not sighting:
        raise HTTPException(status_code=404, detail="Sighting not found")
    return sighting


@router.get("/sightings")
async def get_sightings(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=10000, description="Items per page"),
    start_date: DateType | None = Query(None, description="Start date filter"),
    end_date: DateType | None = Query(None, description="End date filter"),
    species: str | None = Query(None, description="Species filter"),
    place: str | None = Query(None, description="Place filter"),
    ring: str | None = Query(None, description="Ring filter"),
    enriched: bool = Query(False, description="Include ringing data"),
    db: Session = Depends(get_db)
):
    """Get sightings - returns array for Lambda API compatibility"""
    service = SightingService(db)
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Build filters
    filters = {}
    if start_date:
        filters['start_date'] = start_date
    if end_date:
        filters['end_date'] = end_date
    if species:
        filters['species'] = species
    if place:
        filters['place'] = place
    if ring:
        filters['ring'] = ring
    
    # Get sightings
    if filters:
        sightings = service.search_sightings(filters)
        # Apply pagination manually for filtered results
        sightings = sightings[offset:offset + per_page]
    else:
        if enriched:
            sightings = service.get_enriched_sightings(limit=per_page, offset=offset)
        else:
            sightings = service.get_sightings(limit=per_page, offset=offset)
    
    # Return just the array for compatibility with original Lambda API
    return sightings


@router.post("/sightings")
async def add_sighting(
    sighting_data: SightingCreate,
    db: Session = Depends(get_db)
):
    """Create a new sighting"""
    service = SightingService(db)
    try:
        sighting = service.add_sighting(sighting_data.model_dump(exclude_unset=True))
        return sighting
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/sightings")
async def update_sighting(
    sighting_data: SightingUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing sighting"""
    service = SightingService(db)
    try:
        sighting_id = sighting_data.id
        update_data = sighting_data.model_dump(exclude={'id'}, exclude_unset=True)
        sighting = service.update_sighting(sighting_id, update_data)
        if not sighting:
            raise HTTPException(status_code=404, detail="Sighting not found")
        return sighting
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/sightings/{id}")
async def delete_sighting(
    id: str,
    db: Session = Depends(get_db)
):
    """Delete a sighting"""
    service = SightingService(db)
    try:
        success = service.delete_sighting(id)
        if not success:
            raise HTTPException(status_code=404, detail="Sighting not found")
        return {"message": "Sighting deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))