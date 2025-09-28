"""
Repository for family relationship operations
"""

from typing import List, Optional, Dict, Any, Tuple
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
import logging

from .family_models import BirdRelationship, RelationshipType
from .models import Ringing

logger = logging.getLogger(__name__)


class FamilyRepository:
    """Repository for managing bird family relationships"""

    def __init__(self, db: Session):
        self.db = db

    # ============= Basic CRUD Operations =============

    def create_relationship(
        self,
        bird1_ring: str,
        bird2_ring: str,
        relationship_type: RelationshipType,
        year: int,
        sighting1_id: Optional[UUID] = None,
        sighting2_id: Optional[UUID] = None,
        ringing1_id: Optional[UUID] = None,
        ringing2_id: Optional[UUID] = None,
        notes: Optional[str] = None,
        confidence: Optional[str] = None,
        source: Optional[str] = None,
        created_by: Optional[str] = None,
    ) -> BirdRelationship:
        """Create a new bird relationship"""
        relationship = BirdRelationship(
            bird1_ring=bird1_ring,
            bird2_ring=bird2_ring,
            relationship_type=relationship_type,
            year=year,
            sighting1_id=sighting1_id,
            sighting2_id=sighting2_id,
            ringing1_id=ringing1_id,
            ringing2_id=ringing2_id,
            notes=notes,
            confidence=confidence,
            source=source,
            created_by=created_by,
        )
        self.db.add(relationship)
        self.db.commit()
        self.db.refresh(relationship)
        return relationship

    def create_symmetric_relationship(
        self,
        bird1_ring: str,
        bird2_ring: str,
        relationship_type: RelationshipType,
        year: int,
        **kwargs,
    ) -> Tuple[BirdRelationship, BirdRelationship]:
        """
        Create a symmetric relationship (partners, siblings) with entries in both directions.
        Returns both relationship records.
        """
        # Create first direction
        rel1 = self.create_relationship(
            bird1_ring=bird1_ring,
            bird2_ring=bird2_ring,
            relationship_type=relationship_type,
            year=year,
            **kwargs,
        )

        # Swap sighting and ringing IDs for reverse relationship
        reverse_kwargs = kwargs.copy()
        if "sighting1_id" in kwargs and "sighting2_id" in kwargs:
            reverse_kwargs["sighting1_id"] = kwargs.get("sighting2_id")
            reverse_kwargs["sighting2_id"] = kwargs.get("sighting1_id")
        if "ringing1_id" in kwargs and "ringing2_id" in kwargs:
            reverse_kwargs["ringing1_id"] = kwargs.get("ringing2_id")
            reverse_kwargs["ringing2_id"] = kwargs.get("ringing1_id")

        # Create reverse direction
        rel2 = self.create_relationship(
            bird1_ring=bird2_ring,
            bird2_ring=bird1_ring,
            relationship_type=relationship_type,
            year=year,
            **reverse_kwargs,
        )

        return rel1, rel2

    def get_relationship_by_id(
        self, relationship_id: UUID
    ) -> Optional[BirdRelationship]:
        """Get a specific relationship by ID"""
        return (
            self.db.query(BirdRelationship)
            .filter(BirdRelationship.id == relationship_id)
            .first()
        )

    def delete_relationship(self, relationship_id: UUID) -> bool:
        """Delete a relationship by ID"""
        relationship = self.get_relationship_by_id(relationship_id)
        if relationship:
            self.db.delete(relationship)
            self.db.commit()
            return True
        return False

    # ============= Query Methods =============

    def get_bird_relationships(
        self,
        bird_ring: str,
        relationship_type: Optional[RelationshipType] = None,
        year: Optional[int] = None,
    ) -> List[BirdRelationship]:
        """Get all relationships for a specific bird"""
        query = self.db.query(BirdRelationship).filter(
            or_(
                BirdRelationship.bird1_ring == bird_ring,
                BirdRelationship.bird2_ring == bird_ring,
            )
        )

        if relationship_type:
            query = query.filter(
                BirdRelationship._relationship_type == relationship_type.value
            )

        if year:
            query = query.filter(BirdRelationship.year == year)

        return query.order_by(BirdRelationship.year.desc()).all()

    def get_all_relationships(
        self,
        relationship_type: Optional[RelationshipType] = None,
        year: Optional[int] = None,
        bird_ring: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[BirdRelationship]:
        """Get all relationships with optional filters"""
        query = self.db.query(BirdRelationship)

        if relationship_type:
            query = query.filter(
                BirdRelationship._relationship_type == relationship_type.value
            )

        if year:
            query = query.filter(BirdRelationship.year == year)

        if bird_ring:
            query = query.filter(
                or_(
                    BirdRelationship.bird1_ring == bird_ring,
                    BirdRelationship.bird2_ring == bird_ring,
                )
            )

        return (
            query.order_by(BirdRelationship.created_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )

    def get_partners(
        self, bird_ring: str, year: Optional[int] = None, unique_per_year: bool = True
    ) -> List[Dict[str, Any]]:
        """Get all breeding partners of a bird"""
        query = self.db.query(BirdRelationship).filter(
            BirdRelationship.bird1_ring == bird_ring,
            BirdRelationship._relationship_type
            == RelationshipType.BREEDING_PARTNER.value,
        )

        if year:
            query = query.filter(BirdRelationship.year == year)

        relationships = query.order_by(BirdRelationship.year.desc()).all()

        if unique_per_year:
            # Remove duplicates per year
            seen = set()
            unique_partners = []
            for rel in relationships:
                key = (rel.bird2_ring, rel.year)
                if key not in seen:
                    seen.add(key)
                    unique_partners.append(
                        {
                            "ring": rel.bird2_ring,
                            "year": rel.year,
                            "confidence": rel.confidence,
                            "source": rel.source,
                            "notes": rel.notes,
                        }
                    )
            return unique_partners

        return [
            {
                "ring": rel.bird2_ring,
                "year": rel.year,
                "confidence": rel.confidence,
                "source": rel.source,
                "notes": rel.notes,
                "sighting1_id": rel.sighting1_id,
                "sighting2_id": rel.sighting2_id,
                "ringing1_id": rel.ringing1_id,
                "ringing2_id": rel.ringing2_id,
            }
            for rel in relationships
        ]

    def get_children(
        self, parent_ring: str, year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all children of a bird"""

        query = self.db.query(BirdRelationship).filter(
            BirdRelationship.bird1_ring == parent_ring,
            BirdRelationship._relationship_type == RelationshipType.PARENT_OF.value,
        )
        print("DEBUG: get_children")
        print(query.all())

        if year:
            query = query.filter(BirdRelationship.year == year)

        relationships = query.order_by(BirdRelationship.year.desc()).all()

        return [
            {
                "ring": rel.bird2_ring,
                "year": rel.year,
                "confidence": rel.confidence,
                "source": rel.source,
                "notes": rel.notes,
            }
            for rel in relationships
        ]

    def get_parents(
        self, child_ring: str, year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all parents of a bird"""
        query = self.db.query(BirdRelationship).filter(
            BirdRelationship.bird1_ring == child_ring,
            BirdRelationship._relationship_type == RelationshipType.CHILD_OF.value,
        )

        if year:
            query = query.filter(BirdRelationship.year == year)

        relationships = query.all()

        return [
            {
                "ring": rel.bird2_ring,
                "year": rel.year,
                "confidence": rel.confidence,
                "source": rel.source,
                "notes": rel.notes,
            }
            for rel in relationships
        ]

    def get_siblings(
        self,
        bird_ring: str,
        year: Optional[int] = None,
        include_half_siblings: bool = False,
    ) -> List[Dict[str, Any]]:
        """
        Get all siblings of a bird.
        If include_half_siblings is True, also includes birds that share only one parent.
        """
        if include_half_siblings:
            # Get parents of the bird
            parents = self.get_parents(bird_ring, year)
            parent_rings = [p["ring"] for p in parents]

            if not parent_rings:
                return []

            # Get all children of those parents
            siblings = set()
            for parent_ring in parent_rings:
                children = self.get_children(parent_ring, year)
                for child in children:
                    if child["ring"] != bird_ring:  # Exclude self
                        siblings.add((child["ring"], child["year"]))

            return [{"ring": ring, "year": year} for ring, year in siblings]
        else:
            # Direct sibling relationships only
            query = self.db.query(BirdRelationship).filter(
                BirdRelationship.bird1_ring == bird_ring,
                BirdRelationship._relationship_type
                == RelationshipType.SIBLING_OF.value,
            )

            if year:
                query = query.filter(BirdRelationship.year == year)

            relationships = query.order_by(BirdRelationship.year.desc()).all()

            return [
                {
                    "ring": rel.bird2_ring,
                    "year": rel.year,
                    "confidence": rel.confidence,
                    "source": rel.source,
                    "notes": rel.notes,
                }
                for rel in relationships
            ]
