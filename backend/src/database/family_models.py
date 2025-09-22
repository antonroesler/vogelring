"""
Family relationship models for PostgreSQL database

This module defines the relational model for bird family relationships,
replacing the old nested JSON structure from DynamoDB.
"""

from sqlalchemy import (
    Column,
    String,
    Integer,
    Date,
    ForeignKey,
    UniqueConstraint,
    Index,
    Enum as SQLEnum,
    TIMESTAMP,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from uuid import uuid4
import enum

from .connection import Base
from .models import GUID


class RelationshipType(enum.Enum):
    """Types of relationships between birds"""

    BREEDING_PARTNER = "breeding_partner"  # Ist Brutpartner von
    PARENT_OF = "parent_of"  # Ist Elternteil von
    CHILD_OF = "child_of"  # Ist Kind von
    SIBLING_OF = "sibling_of"  # Ist Nestgeschwister von


class BirdRelationship(Base):
    """
    Represents a relationship between two birds.

    This model stores all types of relationships between birds:
    - Breeding partners (symmetric relationship)
    - Parent-child relationships (asymmetric)
    - Sibling relationships (symmetric)

    Each relationship is directional, so symmetric relationships
    (partners, siblings) will have two entries in the database.
    """

    __tablename__ = "bird_relationships"

    # Primary key
    id = Column(GUID(), primary_key=True, default=uuid4)

    # The two birds in the relationship
    bird1_ring = Column(String(50), nullable=False, index=True)  # The subject bird
    bird2_ring = Column(String(50), nullable=False, index=True)  # The related bird

    # Relationship metadata
    _relationship_type = Column(
        "relationship_type", String(50), nullable=False, index=True
    )

    @property
    def relationship_type(self) -> RelationshipType:
        """Get relationship type as enum"""
        return RelationshipType(self._relationship_type)

    @relationship_type.setter
    def relationship_type(self, value: RelationshipType):
        """Set relationship type from enum"""
        self._relationship_type = value.value

    year = Column(
        Integer, nullable=False, index=True
    )  # Year when relationship was observed/valid

    # Connection to observations (optional)
    sighting1_id = Column(GUID(), ForeignKey("sightings.id", ondelete="SET NULL"))
    sighting2_id = Column(GUID(), ForeignKey("sightings.id", ondelete="SET NULL"))

    # Connection to ringings (optional)
    ringing1_id = Column(GUID(), ForeignKey("ringings.id", ondelete="SET NULL"))
    ringing2_id = Column(GUID(), ForeignKey("ringings.id", ondelete="SET NULL"))

    # Metadata
    notes = Column(String(500))  # Optional notes about the relationship
    confidence = Column(String(20))  # e.g., "confirmed", "probable", "possible"
    source = Column(
        String(100)
    )  # e.g., "field_observation", "nest_monitoring", "ringing"

    # Audit fields
    created_at = Column(TIMESTAMP, server_default=func.current_timestamp())
    created_by = Column(String(100))  # User who created the record
    updated_at = Column(
        TIMESTAMP,
        server_default=func.current_timestamp(),
        onupdate=func.current_timestamp(),
    )

    # Relationships to other tables
    sighting1 = relationship(
        "Sighting", foreign_keys=[sighting1_id], backref="relationships_as_bird1"
    )
    sighting2 = relationship(
        "Sighting", foreign_keys=[sighting2_id], backref="relationships_as_bird2"
    )
    ringing1 = relationship(
        "Ringing", foreign_keys=[ringing1_id], backref="relationships_as_bird1"
    )
    ringing2 = relationship(
        "Ringing", foreign_keys=[ringing2_id], backref="relationships_as_bird2"
    )

    # Table constraints and indexes
    __table_args__ = (
        # Prevent duplicate relationships for the same birds in the same year
        UniqueConstraint(
            "bird1_ring",
            "bird2_ring",
            "relationship_type",
            "year",
            "sighting1_id",
            "sighting2_id",
            "ringing1_id",
            "ringing2_id",
            name="uq_bird_relationship",
        ),
        # Performance indexes
        Index("idx_bird_relationships_bird1_year", "bird1_ring", "year"),
        Index("idx_bird_relationships_bird2_year", "bird2_ring", "year"),
        Index("idx_bird_relationships_type_year", "relationship_type", "year"),
        Index("idx_bird_relationships_bird1_type", "bird1_ring", "relationship_type"),
        Index("idx_bird_relationships_bird2_type", "bird2_ring", "relationship_type"),
        # Composite index for finding all relationships of a bird in a year
        Index(
            "idx_bird_relationships_bird1_year_type",
            "bird1_ring",
            "year",
            "relationship_type",
        ),
        Index(
            "idx_bird_relationships_bird2_year_type",
            "bird2_ring",
            "year",
            "relationship_type",
        ),
    )

    def __repr__(self):
        return f"<BirdRelationship({self.bird1_ring} {self.relationship_type.value} {self.bird2_ring} in {self.year})>"


# Note: BreedingEvent and BreedingEventRelationship tables were removed as they're not needed.
# All relationship grouping can be done at the application level using timestamps or shared IDs.
