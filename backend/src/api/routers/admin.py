"""
Admin endpoints for organization and user management
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import List, Optional

from ...database.connection import get_db
from ...database.user_models import User
from ...database.organization_models import Organization
from ...database.organization_repository import UserRepository, OrganizationRepository
from ...utils.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


# Pydantic models for API
class OrganizationResponse(BaseModel):
    """Organization response model"""

    id: str
    name: str
    description: Optional[str]
    contact_email: Optional[str]
    contact_phone: Optional[str]
    address: Optional[str]
    is_active: bool
    user_count: int

    class Config:
        from_attributes = True


class OrganizationCreate(BaseModel):
    """Organization creation model"""

    name: str
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: bool = True


class OrganizationUpdate(BaseModel):
    """Organization update model"""

    name: Optional[str] = None
    description: Optional[str] = None
    contact_email: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    is_active: Optional[bool] = None


class UserResponse(BaseModel):
    """User response model for admin"""

    id: str
    email: str
    display_name: Optional[str]
    org_id: str
    organization_name: str
    is_admin: bool
    is_active: bool

    class Config:
        from_attributes = True


class UserAssignOrganization(BaseModel):
    """User organization assignment model"""

    user_id: str
    org_id: str


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency to require admin privileges"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin privileges required")
    return current_user


# Organization Management Endpoints


@router.get("/organizations", response_model=List[OrganizationResponse])
async def list_organizations(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all organizations (admin only)"""
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)

    organizations = org_repo.get_all(skip=skip, limit=limit)

    # Add user count to each organization
    result = []
    for org in organizations:
        users = user_repo.get_organization_users(org.id)
        org_data = OrganizationResponse.from_orm(org)
        org_data.user_count = len(users)
        result.append(org_data)

    return result


@router.post("/organizations", response_model=OrganizationResponse)
async def create_organization(
    org_data: OrganizationCreate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Create new organization (admin only)"""
    org_repo = OrganizationRepository(db)

    # Check if organization name already exists
    existing_org = org_repo.get_by_name(org_data.name)
    if existing_org:
        raise HTTPException(
            status_code=400, detail="Organization with this name already exists"
        )

    org = org_repo.create(**org_data.dict())

    org_response = OrganizationResponse.from_orm(org)
    org_response.user_count = 0
    return org_response


@router.get("/organizations/{org_id}", response_model=OrganizationResponse)
async def get_organization(
    org_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get organization details (admin only)"""
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)

    org = org_repo.get_by_id(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    users = user_repo.get_organization_users(org_id)

    org_response = OrganizationResponse.from_orm(org)
    org_response.user_count = len(users)
    return org_response


@router.put("/organizations/{org_id}", response_model=OrganizationResponse)
async def update_organization(
    org_id: str,
    org_data: OrganizationUpdate,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Update organization (admin only)"""
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)

    # Check if new name conflicts with existing organization
    if org_data.name:
        existing_org = org_repo.get_by_name(org_data.name)
        if existing_org and existing_org.id != org_id:
            raise HTTPException(
                status_code=400, detail="Organization with this name already exists"
            )

    org = org_repo.update(org_id, **org_data.dict(exclude_unset=True))
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    users = user_repo.get_organization_users(org_id)

    org_response = OrganizationResponse.from_orm(org)
    org_response.user_count = len(users)
    return org_response


@router.delete("/organizations/{org_id}")
async def delete_organization(
    org_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Delete organization (admin only)"""
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)

    # Check if organization has users
    users = user_repo.get_organization_users(org_id)
    if users:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete organization with {len(users)} users. Please reassign users first.",
        )

    success = org_repo.delete(org_id)
    if not success:
        raise HTTPException(status_code=404, detail="Organization not found")

    return {"message": "Organization deleted successfully"}


# User Management Endpoints


@router.get("/organizations/{org_id}/users", response_model=List[UserResponse])
async def list_organization_users(
    org_id: str,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List users in an organization (admin only)"""
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)

    # Verify organization exists
    org = org_repo.get_by_id(org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    users = user_repo.get_organization_users(org_id)

    result = []
    for user in users:
        user_data = UserResponse.from_orm(user)
        user_data.organization_name = org.name
        result.append(user_data)

    return result


@router.post("/users/assign-organization")
async def assign_user_to_organization(
    assignment: UserAssignOrganization,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Assign user to organization (admin only)"""
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)

    # Verify organization exists
    org = org_repo.get_by_id(assignment.org_id)
    if not org:
        raise HTTPException(status_code=404, detail="Organization not found")

    # Assign user to organization
    user = user_repo.assign_to_organization(assignment.user_id, assignment.org_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return {
        "message": f"User {user.email} assigned to organization {org.name}",
        "user_id": user.id,
        "org_id": org.id,
    }


@router.get("/users", response_model=List[UserResponse])
async def list_all_users(
    skip: int = 0,
    limit: int = 100,
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """List all users across all organizations (admin only)"""
    from sqlalchemy import func

    # Get users with their organization names
    users_with_orgs = (
        db.query(User, Organization.name.label("organization_name"))
        .join(Organization, User.org_id == Organization.id)
        .offset(skip)
        .limit(limit)
        .all()
    )

    result = []
    for user, org_name in users_with_orgs:
        user_data = UserResponse.from_orm(user)
        user_data.organization_name = org_name
        result.append(user_data)

    return result


# Admin Status Endpoints


@router.get("/status")
async def admin_status(
    admin_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    """Get admin dashboard status (admin only)"""
    org_repo = OrganizationRepository(db)
    user_repo = UserRepository(db)

    # Get counts
    total_orgs = len(org_repo.get_all())
    total_users = (
        len(user_repo.get_admin_users())
        + len(db.query(User).all())
        - len(user_repo.get_admin_users())
    )
    admin_users = len(user_repo.get_admin_users())

    return {
        "admin_user": {
            "id": str(admin_user.id),
            "email": admin_user.email,
            "organization": admin_user.organization.name
            if admin_user.organization
            else None,
        },
        "statistics": {
            "total_organizations": total_orgs,
            "total_users": total_users,
            "admin_users": admin_users,
        },
    }
