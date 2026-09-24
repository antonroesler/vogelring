"""
Places API router
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from ...database.connection import get_db
from ...database.user_models import User
from ...utils.auth import get_current_user
from ..services.suggestion_service import SuggestionService

router = APIRouter()


@router.get("/places", response_model=List[str])
async def get_place_name_list(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get list of all place names for autocomplete"""
    service = SuggestionService(db)
    return service.get_place_name_list(current_user.org_id)
