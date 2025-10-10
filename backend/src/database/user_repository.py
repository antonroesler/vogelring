"""
User-aware repository base classes and utilities
"""

import logging
from typing import List, Optional, Dict, Any, TypeVar, Generic
from sqlalchemy.orm import Session
from sqlalchemy import and_, text
from sqlalchemy.exc import IntegrityError

from .user_models import User

logger = logging.getLogger(__name__)

T = TypeVar("T")


class UserAwareRepository(Generic[T]):
    """Base repository class with user context awareness"""

    def __init__(self, db: Session, model_class, current_user: User):
        self.db = db
        self.model_class = model_class
        self.current_user = current_user

        # Set user context in database session for RLS
        self._set_user_context()

    def _set_user_context(self):
        """Set user context in database session for RLS"""
        try:
            self.db.execute(
                text("SET app.current_user_id = :user_id"),
                {"user_id": str(self.current_user.id)},
            )
        except Exception as e:
            logger.error(f"Failed to set user context: {e}")
            raise

    def _get_user_filter(self):
        """Get user filter for queries"""
        return self.model_class.user_id == self.current_user.id

    def get_by_id(self, id: str) -> Optional[T]:
        """Get record by ID (user-filtered)"""
        return (
            self.db.query(self.model_class)
            .filter(and_(self.model_class.id == id, self._get_user_filter()))
            .first()
        )

    def get_all(self, skip: int = 0, limit: int = 100) -> List[T]:
        """Get all records for current user"""
        return (
            self.db.query(self.model_class)
            .filter(self._get_user_filter())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def count(self) -> int:
        """Count records for current user"""
        return self.db.query(self.model_class).filter(self._get_user_filter()).count()

    def create(self, **kwargs) -> T:
        """Create new record for current user"""
        try:
            # Ensure user_id is set to current user
            kwargs["user_id"] = self.current_user.id

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
        """Update record by ID (user-filtered)"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None

            # Don't allow changing user_id
            kwargs.pop("user_id", None)

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
        """Delete record by ID (user-filtered)"""
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

    def get_or_create_by_cf_sub(self, cf_sub: str, email: str, **kwargs) -> User:
        """Get or create user by Cloudflare subject"""
        user = self.get_by_cf_sub(cf_sub)
        if not user:
            user = self.create(
                cf_sub=cf_sub,
                email=email,
                display_name=kwargs.get("display_name", email.split("@")[0]),
                **kwargs,
            )
        else:
            # Update email if changed
            if user.email != email:
                user.email = email
                self.db.commit()

        return user
