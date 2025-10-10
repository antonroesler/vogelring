"""
Organization-aware repository implementations for multi-tenant data access
"""

import logging
from typing import List, Optional, Dict, Any, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from sqlalchemy.exc import IntegrityError

from .user_models import User
from .organization_models import Organization

logger = logging.getLogger(__name__)

T = TypeVar("T")


class OrganizationAwareRepository(Generic[T]):
    """Base repository class with organization context awareness"""

    def __init__(self, db: Session, model_class, current_user: User):
        self.db = db
        self.model_class = model_class
        self.current_user = current_user

        # Set organization context in database session for RLS
        self._set_org_context()

    def _set_org_context(self):
        """Set organization context in database session for RLS"""
        try:
            self.db.execute(
                text("SET app.current_org_id = :org_id"),
                {"org_id": str(self.current_user.org_id)},
            )
        except Exception as e:
            logger.error(f"Failed to set organization context: {e}")
            raise

    def _get_org_filter(self):
        """Get organization filter for queries"""
        return self.model_class.org_id == self.current_user.org_id

    def get_by_id(self, id: str) -> Optional[T]:
        """Get record by ID (organization-filtered)"""
        return (
            self.db.query(self.model_class)
            .filter(and_(self.model_class.id == id, self._get_org_filter()))
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records for current organization"""
        return (
            self.db.query(self.model_class)
            .filter(self._get_org_filter())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(self) -> int:
        """Count records for current organization"""
        return self.db.query(self.model_class).filter(self._get_org_filter()).count()

    def create(self, **kwargs) -> T:
        """Create new record for current organization"""
        try:
            # Ensure org_id is set to current user's organization
            kwargs["org_id"] = self.current_user.org_id

            instance = self.model_class(**kwargs)
            self.db.add(instance)
            self.db.commit()
            self.db.refresh(instance)
            return instance
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise

    def update(self, id: str, **kwargs) -> Optional[T]:
        """Update record by ID (organization-filtered)"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None

            # Don't allow changing org_id
            kwargs.pop("org_id", None)

            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)

            self.db.commit()
            self.db.refresh(instance)
            return instance
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error updating {self.model_class.__name__}: {e}")
            raise

    def delete(self, id: str) -> bool:
        """Delete record by ID (organization-filtered)"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return False

            self.db.delete(instance)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            raise


class OrganizationRepository:
    """Repository for organization management"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: str) -> Optional[Organization]:
        """Get organization by ID"""
        return self.db.query(Organization).filter(Organization.id == org_id).first()

    def get_by_name(self, name: str) -> Optional[Organization]:
        """Get organization by name"""
        return self.db.query(Organization).filter(Organization.name == name).first()

    def get_all(self, skip: int = 0, limit: int = 100) -> List[Organization]:
        """Get all organizations (admin only)"""
        return self.db.query(Organization).offset(skip).limit(limit).all()

    def create(self, **kwargs) -> Organization:
        """Create new organization"""
        try:
            org = Organization(**kwargs)
            self.db.add(org)
            self.db.commit()
            self.db.refresh(org)
            logger.info(f"Created new organization: {org.name}")
            return org
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error creating organization: {e}")
            raise

    def update(self, org_id: str, **kwargs) -> Optional[Organization]:
        """Update organization by ID"""
        try:
            org = self.get_by_id(org_id)
            if not org:
                return None

            for key, value in kwargs.items():
                if hasattr(org, key):
                    setattr(org, key, value)

            self.db.commit()
            self.db.refresh(org)
            return org
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error updating organization: {e}")
            raise

    def delete(self, org_id: str) -> bool:
        """Delete organization by ID (admin only)"""
        try:
            org = self.get_by_id(org_id)
            if not org:
                return False

            self.db.delete(org)
            self.db.commit()
            return True
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error deleting organization: {e}")
            raise

    def get_organization_users(self, org_id: str) -> List[User]:
        """Get all users in an organization"""
        return self.db.query(User).filter(User.org_id == org_id).all()


class UserRepository:
    """Repository for user management"""

    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()

    def get_by_cf_sub(self, cf_sub: str) -> Optional[User]:
        """Get user by Cloudflare subject"""
        return self.db.query(User).filter(User.cf_sub == cf_sub).first()

    def create(self, **kwargs) -> User:
        """Create new user"""
        try:
            user = User(**kwargs)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Created new user: {user.email}")
            return user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error creating user: {e}")
            raise

    def update(self, user_id: str, **kwargs) -> Optional[User]:
        """Update user by ID"""
        try:
            user = self.get_by_id(user_id)
            if not user:
                return None

            # Prevent updating admin status via API for security
            kwargs.pop("is_admin", None)

            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)

            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error updating user: {e}")
            raise

    def get_or_create_by_cf_sub(
        self, cf_sub: str, email: str, default_org_id: str, **kwargs
    ) -> User:
        """Get or create user by Cloudflare subject"""
        user = self.get_by_cf_sub(cf_sub)
        if not user:
            user = self.create(
                cf_sub=cf_sub,
                email=email,
                org_id=default_org_id,
                display_name=kwargs.get("display_name", email.split("@")[0]),
                **kwargs,
            )
        else:
            # Update email if changed
            if user.email != email:
                user.email = email
                self.db.commit()

        return user

    def assign_to_organization(self, user_id: str, org_id: str) -> Optional[User]:
        """Assign user to organization (admin only)"""
        try:
            user = self.get_by_id(user_id)
            if not user:
                return None

            user.org_id = org_id
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error assigning user to organization: {e}")
            raise

    def get_organization_users(self, org_id: str) -> List[User]:
        """Get all users in an organization"""
        return self.db.query(User).filter(User.org_id == org_id).all()

    def get_admin_users(self) -> List[User]:
        """Get all admin users"""
        return self.db.query(User).filter(User.is_admin == True).all()
