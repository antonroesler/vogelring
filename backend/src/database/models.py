"""
SQLAlchemy database models
"""

import os
from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    DECIMAL,
    Boolean,
    Text,
    TIMESTAMP,
    Index,
    JSON,
    ForeignKey,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PostgresUUID
from sqlalchemy.types import TypeDecorator, CHAR
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import uuid

from .connection import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.
    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as stringified hex values.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PostgresUUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return str(value)
            else:
                return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        else:
            if not isinstance(value, uuid.UUID):
                return uuid.UUID(value)
            return value


# Use JSON for SQLite (testing) and JSONB for PostgreSQL (production)
def get_json_type():
    """Get appropriate JSON type based on environment"""
    if os.getenv("TESTING", False):
        return JSON
    return JSONB


class Ringing(Base):
    """Ringing data model - migrated from DynamoDB"""

    __tablename__ = "ringings"

    id = Column(GUID(), primary_key=True, default=uuid4)
    ring = Column(String(50), unique=True, nullable=False, index=True)
    ring_scheme = Column(String(50), nullable=False)
    species = Column(String(100), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    place = Column(String(200), nullable=False, index=True)
    lat = Column(DECIMAL(9, 6), nullable=False)  # Latitude: -90.123456 to 90.123456
    lon = Column(DECIMAL(10, 6), nullable=False)  # Longitude: -180.123456 to 180.123456
    ringer = Column(String(100), nullable=False)
    sex = Column(Integer, nullable=False)
    age = Column(Integer, nullable=False)
    status = Column(String(10))
    comment = Column(Text)

    # Multi-tenant support
    org_id = Column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)

    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationship to sightings (one-to-many, since one ring can have multiple sightings)
    sightings = relationship(
        "Sighting",
        primaryjoin="Ringing.ring == Sighting.ring",
        foreign_keys="Sighting.ring",
        viewonly=True,
    )

    # Additional indexes for performance
    __table_args__ = (
        Index("idx_ringings_species_date", "species", "date"),
        Index("idx_ringings_place_date", "place", "date"),
        Index("idx_ringings_ringer", "ringer"),
        Index("idx_ringings_org_species_date", "org_id", "species", "date"),
        Index("idx_ringings_org_place", "org_id", "place"),
    )


class Sighting(Base):
    """Sighting data model - migrated from S3 pickle files"""

    __tablename__ = "sightings"

    id = Column(GUID(), primary_key=True, default=uuid4)
    excel_id = Column(Integer)
    comment = Column(Text)
    species = Column(String(100), index=True)
    ring = Column(String(50), index=True)
    reading = Column(String(50), index=True)
    age = Column(String(10))
    sex = Column(String(1))
    date = Column(Date, index=True)
    large_group_size = Column(Integer)
    small_group_size = Column(Integer)
    partner = Column(String(50))
    breed_size = Column(Integer)
    family_size = Column(Integer)
    pair = Column(String(10))
    status = Column(String(10))
    melder = Column(String(100))
    melded = Column(Boolean)
    place = Column(String(200), index=True)
    area = Column(String(200))
    lat = Column(DECIMAL(9, 6))  # Latitude with ~10cm precision
    lon = Column(DECIMAL(10, 6))  # Longitude with ~10cm precision
    is_exact_location = Column(Boolean, default=False)
    habitat = Column(String(100))
    field_fruit = Column(String(100))

    # Multi-tenant support
    org_id = Column(GUID(), ForeignKey("organizations.id"), nullable=False, index=True)

    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationship to ringing data (optional, based on ring match)
    # Note: This is a "loose" relationship since not all sightings have corresponding ringings
    ringing_data = relationship(
        "Ringing",
        primaryjoin="and_(Sighting.ring == Ringing.ring, Sighting.ring.isnot(None))",
        foreign_keys=[ring],
        uselist=False,
        viewonly=True,
    )

    # Additional indexes for performance
    __table_args__ = (
        Index("idx_sightings_species_date", "species", "date"),
        Index("idx_sightings_place_date", "place", "date"),
        Index("idx_sightings_ring_date", "ring", "date"),
        Index("idx_sightings_org_species_date", "org_id", "species", "date"),
        Index("idx_sightings_org_ring_date", "org_id", "ring", "date"),
        Index("idx_sightings_org_place", "org_id", "place"),
    )
