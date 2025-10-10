"""
Authentication utilities for development and production
"""

import os
import jwt
import logging
from typing import Optional
from fastapi import Request, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqlalchemy.sql import func

from ..database.connection import get_db
from ..database.user_models import User
from ..database.organization_models import Organization
from ..database.organization_repository import UserRepository, OrganizationRepository

logger = logging.getLogger(__name__)


def is_development_mode() -> bool:
    """Check if we're running in development mode"""
    return os.getenv("DEVELOPMENT_MODE", "false").lower() == "true"


def get_dev_user_email() -> str:
    """Get development user email from environment or default"""
    return os.getenv("DEV_USER_EMAIL", "dev@vogelring.local")


def get_dev_user_name() -> str:
    """Get development user name from environment or default"""
    return os.getenv("DEV_USER_NAME", "Development User")


def decode_cf_jwt(jwt_token: str) -> dict:
    """
    Decode Cloudflare JWT token (simplified for development)
    In production, you'd want to verify the signature properly
    """
    try:
        # For development, we'll just decode without verification
        # In production, verify with Cloudflare's public keys
        decoded = jwt.decode(jwt_token, options={"verify_signature": False})
        return decoded
    except Exception as e:
        logger.error(f"Failed to decode JWT: {e}")
        raise HTTPException(status_code=401, detail="Invalid JWT token")


async def get_current_user_dev(db: Session = Depends(get_db)) -> User:
    """Development-only user provider - creates/returns a dev user"""
    email = get_dev_user_email()
    user_repo = UserRepository(db)
    org_repo = OrganizationRepository(db)

    # Get or create default organization for development
    default_org = org_repo.get_by_name("Development Organization")
    if not default_org:
        default_org = org_repo.create(
            name="Development Organization",
            description="Default organization for development environment",
            is_active=True,
        )

    # Get or create dev user
    user = user_repo.get_by_email(email)
    if not user:
        user = user_repo.create(
            cf_sub=f"dev-{email}",
            email=email,
            display_name=get_dev_user_name(),
            org_id=default_org.id,
            is_active=True,
        )

    return user


async def get_current_user_prod(
    request: Request, db: Session = Depends(get_db)
) -> User:
    """Production user provider - extracts user from Cloudflare headers"""
    cf_email = request.headers.get("CF-Access-Authenticated-User-Email")
    cf_jwt = request.headers.get("CF-Access-JWT")

    if not cf_email or not cf_jwt:
        logger.warning("Missing Cloudflare authentication headers")
        raise HTTPException(
            status_code=401,
            detail="Authentication required - missing Cloudflare headers",
        )

    try:
        # Decode JWT to get sub claim
        jwt_payload = decode_cf_jwt(cf_jwt)
        cf_sub = jwt_payload.get("sub")

        if not cf_sub:
            raise HTTPException(
                status_code=401, detail="Invalid JWT - missing sub claim"
            )

        # Get or create user using repository
        user_repo = UserRepository(db)
        org_repo = OrganizationRepository(db)

        # Get or create default organization for production
        default_org = org_repo.get_by_name("Default Organization")
        if not default_org:
            default_org = org_repo.create(
                name="Default Organization",
                description="Default organization for new users",
                is_active=True,
            )

        user = user_repo.get_or_create_by_cf_sub(
            cf_sub=cf_sub,
            email=cf_email,
            default_org_id=default_org.id,
            display_name=cf_email.split("@")[0],
            is_active=True,
        )

        # Update last login
        user_repo.update(user.id, last_login=func.current_timestamp())

        return user

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        raise HTTPException(status_code=401, detail="Authentication failed")


async def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Get current user - production or development mode"""
    if is_development_mode():
        return await get_current_user_dev(db)
    else:
        return await get_current_user_prod(request, db)


def get_org_db_session(org_id: str, db: Session) -> Session:
    """Set organization context in database session for RLS"""
    try:
        db.execute(text("SET app.current_org_id = :org_id"), {"org_id": str(org_id)})
        return db
    except Exception as e:
        logger.error(f"Failed to set organization context: {e}")
        raise


async def get_db_with_org(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    """Get database session with organization context for RLS"""
    logger.info(
        f"Getting database session with organization context for user: {current_user.id}"
    )
    # Set LOCAL works within transaction - SQLAlchemy will start transaction on first query
    db.execute(
        text("SET LOCAL app.current_org_id = :org_id"),
        {"org_id": str(current_user.org_id)},
    )
    return db
