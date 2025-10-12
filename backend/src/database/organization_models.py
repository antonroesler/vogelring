"""
Organization models for multi-tenant support
"""

from sqlalchemy import (
    Column,
    String,
    Boolean,
    TIMESTAMP,
    Text,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4

from .connection import Base
from .models import GUID, get_json_type


class Organization(Base):
    """Organization model for multi-tenant support"""

    __tablename__ = "organizations"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)

    # Organization details
    name = Column(String(200), nullable=False, index=True)
    description = Column(Text)

    # Contact information
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    address = Column(Text)

    # Organization settings
    is_active = Column(Boolean, default=True)
    settings = Column(get_json_type(), default={})  # Organization-specific settings

    # Metadata
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships
    users = relationship("User", back_populates="organization")

    def __repr__(self):
        return f"<Organization({self.name})>"
