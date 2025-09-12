"""
Species API router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...database.connection import get_db
from ..services.suggestion_service import SuggestionService

router = APIRouter()

@router.get("/species", response_model=List[str])
async def get_species_name_list(db: Session = Depends(get_db)):
    """Get list of all species names for autocomplete"""
    service = SuggestionService(db)
    return service.get_species_name_list()