"""
Places API router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...database.connection import get_db
from ..services.suggestion_service import SuggestionService

router = APIRouter()


@router.get("/places", response_model=List[str])
async def get_place_name_list(db: Session = Depends(get_db)):
    """Get list of all place names for autocomplete"""
    service = SuggestionService(db)
    return service.get_place_name_list()
