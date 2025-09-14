"""
Suggestions API router
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import Dict, List

from ...database.connection import get_db
from ..services.suggestion_service import SuggestionService

router = APIRouter()

@router.get("/suggestions")
async def get_suggestions(db: Session = Depends(get_db)):
    """Get all suggestion lists for autocomplete fields"""
    service = SuggestionService(db)
    return service.get_suggestion_lists()

@router.get("/suggestions/species")
async def get_species_suggestions(db: Session = Depends(get_db)):
    """Get species name suggestions ordered by frequency"""
    service = SuggestionService(db)
    return {"species": service.get_species_name_list()}

@router.get("/suggestions/places")
async def get_place_suggestions(db: Session = Depends(get_db)):
    """Get place name suggestions ordered by frequency"""
    service = SuggestionService(db)
    return {"places": service.get_place_name_list()}

@router.get("/suggestions/habitats")
async def get_habitat_suggestions(db: Session = Depends(get_db)):
    """Get habitat suggestions ordered by frequency"""
    service = SuggestionService(db)
    return {"habitats": service.get_habitat_list()}

@router.get("/suggestions/melders")
async def get_melder_suggestions(db: Session = Depends(get_db)):
    """Get melder suggestions ordered by frequency"""
    service = SuggestionService(db)
    return {"melders": service.get_melder_list()}

@router.get("/suggestions/field_fruits")
async def get_field_fruit_suggestions(db: Session = Depends(get_db)):
    """Get field fruit suggestions ordered by frequency"""
    service = SuggestionService(db)
    return {"field_fruits": service.get_field_fruit_list()}

@router.get("/suggestions/ringers")
async def get_ringer_suggestions(db: Session = Depends(get_db)):
    """Get ringer suggestions"""
    service = SuggestionService(db)
    return {"ringers": service.get_ringer_list()}