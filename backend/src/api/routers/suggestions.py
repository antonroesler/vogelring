"""
Suggestions API router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ...utils.auth import get_current_user
from ...database.connection import get_db
from ...database.user_models import User
from ..services.suggestion_service import SuggestionService

router = APIRouter()


@router.get("/suggestions")
async def get_all_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get all suggestion lists for autocomplete fields"""
    service = SuggestionService(db)
    return service.get_suggestion_lists(current_user.org_id)


@router.get("/suggestions/species")
async def get_species_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get species name suggestions ordered by frequency"""
    service = SuggestionService(db)
    return {"species": service.get_species_name_list(current_user.org_id)}


@router.get("/suggestions/places")
async def get_place_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get place name suggestions ordered by frequency"""
    service = SuggestionService(db)
    return {"places": service.get_place_name_list(current_user.org_id)}


@router.get("/suggestions/habitats")
async def get_habitat_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get habitat suggestions ordered by frequency"""
    service = SuggestionService(db)
    return {"habitats": service.get_habitat_list(current_user.org_id)}


@router.get("/suggestions/melders")
async def get_melder_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get melder suggestions ordered by frequency"""
    service = SuggestionService(db)
    return {"melders": service.get_melder_list(current_user.org_id)}


@router.get("/suggestions/field-fruits")
async def get_field_fruit_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get field fruit suggestions ordered by frequency"""
    service = SuggestionService(db)
    return {"field_fruits": service.get_field_fruit_list(current_user.org_id)}


@router.get("/suggestions/ringers")
async def get_ringer_suggestions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get ringer suggestions"""
    service = SuggestionService(db)
    return {"ringers": service.get_ringer_list(current_user.org_id)}
