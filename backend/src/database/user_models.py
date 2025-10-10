"""
User models for multi-user support
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    TIMESTAMP,
    ForeignKey,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from .connection import Base
from .models import GUID, get_json_type


class User(Base):
    """User model for multi-user support"""

    __tablename__ = "users"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)

    # Cloudflare Zero Trust fields
    cf_sub = Column(
        String(255), unique=True, nullable=False, index=True
    )  # Cloudflare subject
    email = Column(String(255), unique=True, nullable=False, index=True)

    # User profile fields
    display_name = Column(String(100))

    # Organization relationship
    org_id = Column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)

    # Admin privileges (NOT editable via API for security)
    is_admin = Column(Boolean, default=False, nullable=False)

    # Account management
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    last_login = Column(TIMESTAMP)

    # Settings (JSON for flexibility)
    preferences = Column(get_json_type(), default={})

    # Relationships
    organization = relationship("Organization", back_populates="users")

    def __repr__(self):
        return f"<User({self.email})>"
