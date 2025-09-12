"""
Birds API router
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from ...database.connection import get_db

router = APIRouter()

@router.get("/birds/{ring}")
async def get_bird_by_ring(
    ring: str,
    db: Session = Depends(get_db)
):
    """Get bird information by ring number"""
    # TODO: Implement bird lookup logic
    return {"message": f"Get bird by ring: {ring} - to be implemented"}

@router.get("/birds/suggestions/{partial_reading}")
async def get_bird_suggestions_by_partial_reading(
    partial_reading: str,
    db: Session = Depends(get_db)
):
    """Get bird suggestions by partial ring reading"""
    if not partial_reading or len(partial_reading) < 2:
        raise HTTPException(status_code=400, detail="Partial reading must be at least 2 characters long")
    
    # Add wildcards if not present
    if not any(c in partial_reading for c in ["*", "…", "..."]):
        partial_reading = f"*{partial_reading}*"
    
    # TODO: Implement bird suggestions logic
    return {"message": f"Get bird suggestions for: {partial_reading} - to be implemented"}