"""
Repository for family relationship operations.

Storage convention (unidirectional):
- BREEDING_PARTNER: one record, bird1_ring < bird2_ring alphabetically
- PARENT_OF: one record, bird1 = parent, bird2 = child
- SIBLING_OF: one record, bird1_ring < bird2_ring alphabetically

'child_of' is derived at query time — when the perspective bird is bird2 in a PARENT_OF record.
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import or_
from uuid import UUID
import logging

from .family_models import BirdRelationship, RelationshipType

logger = logging.getLogger(__name__)

_SYMMETRIC_TYPES = {RelationshipType.BREEDING_PARTNER, RelationshipType.SIBLING_OF}


class FamilyRepository:
    """Repository for managing bird family relationships"""

    def __init__(self, db: Session):
        self.db = db

    # ============= Basic CRUD Operations =============

    def create_relationship(
        self,
        org_id: str,
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
        """Create a new bird relationship (unidirectional).

        For symmetric types (breeding_partner, sibling_of), bird1_ring is
        normalized to be alphabetically smaller than bird2_ring.
        For parent_of, bird1 is always the parent and bird2 the child.
        """
        # Normalize symmetric types: bird1_ring < bird2_ring alphabetically
        if relationship_type in _SYMMETRIC_TYPES and bird1_ring > bird2_ring:
            bird1_ring, bird2_ring = bird2_ring, bird1_ring
            sighting1_id, sighting2_id = sighting2_id, sighting1_id
            ringing1_id, ringing2_id = ringing2_id, ringing1_id

        relationship = BirdRelationship(
            org_id=org_id,
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

    def get_relationship_by_id(
        self, org_id: str, relationship_id: UUID
    ) -> Optional[BirdRelationship]:
        """Get a specific relationship by ID"""
        return (
            self.db.query(BirdRelationship)
            .filter(BirdRelationship.org_id == org_id)
            .filter(BirdRelationship.id == relationship_id)
            .first()
        )

    def delete_relationship(self, org_id: str, relationship_id: UUID) -> bool:
        """Delete a relationship by ID"""
        relationship = self.get_relationship_by_id(org_id, relationship_id)
        if relationship:
            self.db.delete(relationship)
            self.db.commit()
            return True
        return False

    # ============= Display Type Helper =============

    def _get_display_type(
        self, relationship: BirdRelationship, perspective_bird_ring: str
    ) -> str:
        """Return the display label for a relationship from a bird's perspective.

        For PARENT_OF: the parent sees 'parent_of', the child sees 'child_of'.
        Symmetric types (breeding_partner, sibling_of) look the same from both sides.
        """
        rel_type = relationship.relationship_type
        if rel_type == RelationshipType.PARENT_OF:
            if relationship.bird1_ring == perspective_bird_ring:
                return "parent_of"
            else:
                return "child_of"
        return rel_type.value

    # ============= Query Methods =============

    def get_bird_relationships(
        self,
        org_id: str,
        bird_ring: str,
        relationship_type: Optional[RelationshipType] = None,
        year: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Get all relationships for a specific bird, with display_type computed."""
        query = self.db.query(BirdRelationship).filter(
            BirdRelationship.org_id == org_id,
            or_(
                BirdRelationship.bird1_ring == bird_ring,
                BirdRelationship.bird2_ring == bird_ring,
            ),
        )

        if relationship_type:
            query = query.filter(
                BirdRelationship._relationship_type == relationship_type.value
            )

        if year:
            query = query.filter(BirdRelationship.year == year)

        relationships = query.order_by(BirdRelationship.year.desc()).all()

        return [
            {
                "id": rel.id,
                "bird1_ring": rel.bird1_ring,
                "bird2_ring": rel.bird2_ring,
                "relationship_type": rel.relationship_type.value,
                "display_type": self._get_display_type(rel, bird_ring),
                "other_ring": rel.bird2_ring if rel.bird1_ring == bird_ring else rel.bird1_ring,
                "year": rel.year,
                "confidence": rel.confidence,
                "source": rel.source,
                "notes": rel.notes,
                "sighting1_id": rel.sighting1_id,
                "sighting2_id": rel.sighting2_id,
                "ringing1_id": rel.ringing1_id,
                "ringing2_id": rel.ringing2_id,
                "created_at": rel.created_at,
                "updated_at": rel.updated_at,
            }
            for rel in relationships
        ]

    def get_all_relationships(
        self,
        org_id: str,
        relationship_type: Optional[RelationshipType] = None,
        year: Optional[int] = None,
        bird_ring: Optional[str] = None,
    ) -> List[BirdRelationship]:
        """Get all relationships with optional filters. Returns raw records (no perspective)."""
        query = self.db.query(BirdRelationship).filter(
            BirdRelationship.org_id == org_id
        )

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

        return query.order_by(BirdRelationship.created_at.desc()).all()

    def get_partners(
        self,
        org_id: str,
        bird_ring: str,
        year: Optional[int] = None,
        unique_per_year: bool = True,
    ) -> List[Dict[str, Any]]:
        """Get all breeding partners of a bird (checks both bird1 and bird2)."""
        query = self.db.query(BirdRelationship).filter(
            BirdRelationship.org_id == org_id,
            or_(
                BirdRelationship.bird1_ring == bird_ring,
                BirdRelationship.bird2_ring == bird_ring,
            ),
            BirdRelationship._relationship_type == RelationshipType.BREEDING_PARTNER.value,
        )

        if year:
            query = query.filter(BirdRelationship.year == year)

        relationships = query.order_by(BirdRelationship.year.desc()).all()

        def _other_ring(rel: BirdRelationship) -> str:
            return rel.bird2_ring if rel.bird1_ring == bird_ring else rel.bird1_ring

        if unique_per_year:
            seen: set[tuple[str, int]] = set()
            unique_partners: List[Dict[str, Any]] = []
            for rel in relationships:
                other = _other_ring(rel)
                key = (other, rel.year)
                if key not in seen:
                    seen.add(key)
                    unique_partners.append(
                        {
                            "ring": other,
                            "year": rel.year,
                            "confidence": rel.confidence,
                            "source": rel.source,
                            "notes": rel.notes,
                        }
                    )
            return unique_partners

        return [
            {
                "ring": _other_ring(rel),
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
        self, org_id: str, parent_ring: str, year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all children of a bird (bird1 is always parent in parent_of)."""
        query = self.db.query(BirdRelationship).filter(
            BirdRelationship.org_id == org_id,
            BirdRelationship.bird1_ring == parent_ring,
            BirdRelationship._relationship_type == RelationshipType.PARENT_OF.value,
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

    def get_parents(
        self, org_id: str, child_ring: str, year: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get all parents of a bird (bird2 is the child in parent_of records)."""
        query = self.db.query(BirdRelationship).filter(
            BirdRelationship.org_id == org_id,
            BirdRelationship.bird2_ring == child_ring,
            BirdRelationship._relationship_type == RelationshipType.PARENT_OF.value,
        )

        if year:
            query = query.filter(BirdRelationship.year == year)

        relationships = query.all()

        return [
            {
                "ring": rel.bird1_ring,
                "year": rel.year,
                "confidence": rel.confidence,
                "source": rel.source,
                "notes": rel.notes,
            }
            for rel in relationships
        ]

    def get_siblings(
        self,
        org_id: str,
        bird_ring: str,
        year: Optional[int] = None,
        include_half_siblings: bool = False,
    ) -> List[Dict[str, Any]]:
        """Get all siblings of a bird (checks both bird1 and bird2)."""
        if include_half_siblings:
            parents = self.get_parents(org_id, bird_ring, year)
            parent_rings = [p["ring"] for p in parents]

            if not parent_rings:
                return []

            siblings: set[tuple[str, int]] = set()
            for parent_ring in parent_rings:
                children = self.get_children(org_id, parent_ring, year)
                for child in children:
                    if child["ring"] != bird_ring:
                        siblings.add((child["ring"], child["year"]))

            return [{"ring": ring, "year": yr} for ring, yr in siblings]

        # Direct sibling relationships — check both directions
        query = self.db.query(BirdRelationship).filter(
            BirdRelationship.org_id == org_id,
            or_(
                BirdRelationship.bird1_ring == bird_ring,
                BirdRelationship.bird2_ring == bird_ring,
            ),
            BirdRelationship._relationship_type == RelationshipType.SIBLING_OF.value,
        )

        if year:
            query = query.filter(BirdRelationship.year == year)

        relationships = query.order_by(BirdRelationship.year.desc()).all()

        return [
            {
                "ring": rel.bird2_ring if rel.bird1_ring == bird_ring else rel.bird1_ring,
                "year": rel.year,
                "confidence": rel.confidence,
                "source": rel.source,
                "notes": rel.notes,
            }
            for rel in relationships
        ]
