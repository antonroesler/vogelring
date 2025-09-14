"""
Ringings API router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, Any, List
from datetime import date as DateType
from pydantic import BaseModel

from ...database.connection import get_db
from ..services.ringing_service import RingingService

router = APIRouter()


class RingingCreate(BaseModel):
    """Pydantic model for creating ringings"""
    ring: str
    ring_scheme: str
    species: str
    date: DateType
    place: str
    lat: float
    lon: float
    ringer: str
    sex: int
    age: int
    status: str | None = None


class RingingUpdate(BaseModel):
    """Pydantic model for updating ringings"""
    ring: str
    ring_scheme: str | None = None
    species: str | None = None
    date: DateType | None = None
    place: str | None = None
    lat: float | None = None
    lon: float | None = None
    ringer: str | None = None
    sex: int | None = None
    age: int | None = None
    status: str | None = None


@router.get("/ringings/count")
async def get_ringings_count(db: Session = Depends(get_db)):
    """Get total count of ringings"""
    service = RingingService(db)
    return {"count": service.get_ringings_count()}


@router.get("/ringings/statistics")
async def get_ringings_statistics(db: Session = Depends(get_db)):
    """Get ringings statistics"""
    service = RingingService(db)
    return service.get_statistics()


@router.get("/ringings/autocomplete/{field}")
async def get_autocomplete_suggestions(
    field: str,
    q: str = Query(..., description="Query string"),
    limit: int = Query(10, ge=1, le=50, description="Maximum number of suggestions"),
    db: Session = Depends(get_db)
):
    """Get autocomplete suggestions for a field"""
    service = RingingService(db)
    suggestions = service.get_autocomplete_suggestions(field, q, limit)
    return {"suggestions": suggestions}


@router.get("/ringings")
async def get_ringings(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=1000, description="Items per page"),
    start_date: DateType | None = Query(None, description="Start date filter"),
    end_date: DateType | None = Query(None, description="End date filter"),
    species: str | None = Query(None, description="Species filter"),
    place: str | None = Query(None, description="Place filter"),
    ringer: str | None = Query(None, description="Ringer filter"),
    db: Session = Depends(get_db)
):
    """Get ringings with optional filtering and pagination"""
    service = RingingService(db)
    
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
    if ringer:
        filters['ringer'] = ringer
    
    # Get ringings
    if filters:
        ringings = service.search_ringings(filters)
        # Apply pagination manually for filtered results
        total = len(ringings)
        ringings = ringings[offset:offset + per_page]
    else:
        ringings = service.get_all_ringings(limit=per_page, offset=offset)
        total = service.get_ringings_count()
    
    return {
        "ringings": ringings,
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page
        }
    }


@router.get("/ringings/entry-list")
async def get_ringings_entry_list(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(100, ge=1, le=10000, description="Items per page"),
    start_date: DateType | None = Query(None, description="Start date filter"),
    end_date: DateType | None = Query(None, description="End date filter"),
    species: str | None = Query(None, description="Species filter"),
    place: str | None = Query(None, description="Place filter"),
    ring: str | None = Query(None, description="Ring filter"),
    ringer: str | None = Query(None, description="Ringer filter"),
    db: Session = Depends(get_db)
):
    """Get ringings for entry list with server-side filtering for specific species"""
    service = RingingService(db)
    
    # Calculate offset
    offset = (page - 1) * per_page
    
    # Build filters with species filtering for target species
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
    if ringer:
        filters['ringer'] = ringer
    
    # Get filtered ringings for target species
    ringings = service.get_entry_list_ringings(filters, limit=per_page, offset=offset)
    total = service.get_entry_list_ringings_count(filters)
    
    return ringings  # Return just the array for compatibility with sightings API


@router.get("/ringing/{ring}")
async def get_ringing_by_ring(
    ring: str,
    db: Session = Depends(get_db)
):
    """Get ringing information by ring number"""
    service = RingingService(db)
    ringing = service.get_ringing_by_ring(ring)
    if not ringing:
        raise HTTPException(status_code=404, detail="Ringing not found")
    return ringing


@router.post("/ringing")
async def upsert_ringing(
    ringing_data: RingingCreate,
    db: Session = Depends(get_db)
):
    """Create or update a ringing record"""
    service = RingingService(db)
    try:
        ringing = service.upsert_ringing(ringing_data.model_dump())
        return ringing
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/ringing")
async def update_ringing(
    ringing_data: RingingUpdate,
    db: Session = Depends(get_db)
):
    """Update an existing ringing record"""
    service = RingingService(db)
    try:
        # Use upsert functionality for updates
        ringing = service.upsert_ringing(ringing_data.model_dump(exclude_unset=True))
        return ringing
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/ringing/{ring}")
async def delete_ringing(
    ring: str,
    db: Session = Depends(get_db)
):
    """Delete a ringing record"""
    service = RingingService(db)
    try:
        success = service.delete_ringing(ring)
        return {"message": "Ringing deleted successfully", "success": success}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))