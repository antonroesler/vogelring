"""
Authentication endpoints
"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from ...database.connection import get_db
from ...database.user_models import User
from ...utils.auth import get_current_user, get_db_with_org

router = APIRouter(prefix="/auth", tags=["auth"])


class UserResponse(BaseModel):
    """User response model"""

    id: str
    email: str
    display_name: Optional[str]
    org_id: str
    organization_name: Optional[str]
    is_admin: bool
    is_active: bool

    class Config:
        from_attributes = True


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserResponse:
    """Get current user information"""
    # Load the organization relationship
    from sqlalchemy.orm import joinedload

    user_with_org = (
        db.query(User)
        .options(joinedload(User.organization))
        .filter(User.id == current_user.id)
        .first()
    )

    return UserResponse(
        id=str(user_with_org.id),
        email=user_with_org.email,
        display_name=user_with_org.display_name,
        org_id=str(user_with_org.org_id),
        organization_name=user_with_org.organization.name
        if user_with_org.organization
        else None,
        is_admin=user_with_org.is_admin,
        is_active=user_with_org.is_active,
    )


@router.get("/status")
async def auth_status(request: Request):
    """Get authentication status and available headers (for debugging)"""
    headers = dict(request.headers)

    # Filter sensitive headers for logging
    safe_headers = {
        k: v for k, v in headers.items() if not k.lower().startswith("cf-access-jwt")
    }

    return {
        "development_mode": request.app.state.development_mode
        if hasattr(request.app.state, "development_mode")
        else False,
        "headers_present": {
            "cf_email": "cf-access-authenticated-user-email" in headers,
            "cf_jwt": "cf-access-jwt" in headers,
        },
        "safe_headers": safe_headers,
    }


@router.get("/test-org-data")
async def test_org_data(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db_with_org),
):
    """Test endpoint to verify organization data isolation"""
    from ...database.user_aware_repositories import (
        OrganizationAwareSightingRepository,
        OrganizationAwareRingingRepository,
    )
    from sqlalchemy.orm import joinedload

    # Load user with organization relationship
    user_with_org = (
        db.query(User)
        .options(joinedload(User.organization))
        .filter(User.id == current_user.id)
        .first()
    )

    sighting_repo = OrganizationAwareSightingRepository(db, current_user)
    ringing_repo = OrganizationAwareRingingRepository(db, current_user)

    return {
        "user": {
            "id": str(user_with_org.id),
            "email": user_with_org.email,
            "display_name": user_with_org.display_name,
            "is_admin": user_with_org.is_admin,
        },
        "organization": {
            "id": str(user_with_org.org_id),
            "name": user_with_org.organization.name
            if user_with_org.organization
            else None,
        },
        "data_counts": {
            "sightings": sighting_repo.count(),
            "ringings": ringing_repo.count(),
        },
    }
