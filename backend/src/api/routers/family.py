"""
Family relationships API router (Version 2 - Relational Model)
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, cast
from datetime import date
from uuid import UUID
from pydantic import BaseModel, Field
from enum import Enum

from ...database.connection import get_db
from ...database.family_repository import FamilyRepository
from ...database.family_models import (
    RelationshipType as DBRelationshipType,
    BirdRelationship,
)

router = APIRouter(prefix="/family", tags=["family"])


# ============= Pydantic Models =============


class RelationshipType(str, Enum):
    """API enum for relationship types"""

    BREEDING_PARTNER = "breeding_partner"
    PARENT_OF = "parent_of"
    CHILD_OF = "child_of"
    SIBLING_OF = "sibling_of"


class RelationshipCreate(BaseModel):
    """Model for creating a new relationship"""

    bird1_ring: str = Field(..., description="Ring number of the first bird")
    bird2_ring: str = Field(..., description="Ring number of the second bird")
    relationship_type: RelationshipType
    year: int = Field(..., ge=1900, le=2100)
    confidence: Optional[str] = Field(None, max_length=20)
    source: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)
    sighting1_id: Optional[UUID] = None
    sighting2_id: Optional[UUID] = None
    ringing1_id: Optional[UUID] = None
    ringing2_id: Optional[UUID] = None


class SymmetricRelationshipCreate(BaseModel):
    """Model for creating symmetric relationships (partners, siblings)"""

    bird1_ring: str
    bird2_ring: str
    relationship_type: RelationshipType
    year: int = Field(..., ge=1900, le=2100)
    confidence: Optional[str] = None
    source: Optional[str] = None
    notes: Optional[str] = None


class BreedingFamilyCreate(BaseModel):
    """Model for creating a complete breeding family"""

    parent1_ring: str = Field(..., description="Ring of first parent")
    parent2_ring: Optional[str] = Field(
        None, description="Ring of second parent (optional)"
    )
    chick_rings: List[str] = Field(..., description="List of chick ring numbers")
    year: int = Field(..., ge=1900, le=2100)
    location: Optional[str] = None
    nest_id: Optional[str] = None
    source: str = Field("field_observation", max_length=100)
    notes: Optional[str] = None
    sighting_ids: Optional[Dict[str, UUID]] = Field(
        None, description="Map of ring to sighting ID"
    )
    ringing_ids: Optional[Dict[str, UUID]] = Field(
        None, description="Map of ring to ringing ID"
    )


class RelationshipUpdate(BaseModel):
    """Model for updating an existing relationship"""

    relationship_type: Optional[RelationshipType] = None
    year: Optional[int] = Field(None, ge=1900, le=2100)
    confidence: Optional[str] = Field(None, max_length=20)
    source: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)


class RelationshipResponse(BaseModel):
    """Response model for a relationship"""

    id: UUID
    bird1_ring: str
    bird2_ring: str
    relationship_type: str
    year: int
    confidence: Optional[str]
    source: Optional[str]
    notes: Optional[str]
    sighting1_id: Optional[UUID]
    sighting2_id: Optional[UUID]
    ringing1_id: Optional[UUID]
    ringing2_id: Optional[UUID]
    created_at: str
    updated_at: str


class BirdPartner(BaseModel):
    """Model for bird partner information"""

    ring: str
    year: int
    confidence: Optional[str]
    source: Optional[str]
    notes: Optional[str]


class BirdChild(BaseModel):
    """Model for bird child information"""

    ring: str
    year: int
    confidence: Optional[str]
    source: Optional[str]
    notes: Optional[str]


class BirdParent(BaseModel):
    """Model for bird parent information"""

    ring: str
    year: int
    confidence: Optional[str]
    source: Optional[str]
    notes: Optional[str]


class BirdSibling(BaseModel):
    """Model for bird sibling information"""

    ring: str
    year: int
    confidence: Optional[str]
    source: Optional[str]
    notes: Optional[str]


class FamilyTreeResponse(BaseModel):
    """Complete family tree response"""

    ring: str
    species: Optional[str]
    sex: Optional[int]
    ringing_date: Optional[str]
    ringing_place: Optional[str]
    parents: List[Dict[str, Any]]
    children: List[Dict[str, Any]]
    siblings: List[Dict[str, Any]]
    partners: List[Dict[str, Any]]


class RelationshipStatistics(BaseModel):
    """Statistics about a bird's relationships"""

    total_partners: int
    total_children: int
    total_siblings: int
    breeding_years: List[int]
    breeding_locations: List[str]
    family_size: int


class BreedingEventResponse(BaseModel):
    """Response model for breeding event"""

    id: UUID
    year: int
    location: Optional[str]
    nest_id: Optional[str]
    parent1_ring: Optional[str]
    parent2_ring: Optional[str]
    clutch_size: Optional[int]
    fledged_count: Optional[int]
    breeding_success: Optional[str]
    created_at: str


# ============= API Endpoints =============


@router.post("/relationships", response_model=RelationshipResponse)
async def create_relationship(
    relationship_data: RelationshipCreate, db: Session = Depends(get_db)
):
    """Create a new bird relationship"""
    repo = FamilyRepository(db)

    # Convert API enum to DB enum
    db_relationship_type = DBRelationshipType[
        relationship_data.relationship_type.value.upper()
    ]

    try:
        relationship = repo.create_relationship(
            bird1_ring=relationship_data.bird1_ring,
            bird2_ring=relationship_data.bird2_ring,
            relationship_type=db_relationship_type,
            year=relationship_data.year,
            confidence=relationship_data.confidence,
            source=relationship_data.source,
            notes=relationship_data.notes,
            sighting1_id=relationship_data.sighting1_id,
            sighting2_id=relationship_data.sighting2_id,
            ringing1_id=relationship_data.ringing1_id,
            ringing2_id=relationship_data.ringing2_id,
        )

        return RelationshipResponse(
            id=relationship.id,
            bird1_ring=relationship.bird1_ring,
            bird2_ring=relationship.bird2_ring,
            relationship_type=relationship.relationship_type.value,
            year=relationship.year,
            confidence=relationship.confidence,
            source=relationship.source,
            notes=relationship.notes,
            sighting1_id=relationship.sighting1_id,
            sighting2_id=relationship.sighting2_id,
            ringing1_id=relationship.ringing1_id,
            ringing2_id=relationship.ringing2_id,
            created_at=relationship.created_at.isoformat(),
            updated_at=relationship.updated_at.isoformat(),
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/relationships/symmetric")
async def create_symmetric_relationship(
    relationship_data: SymmetricRelationshipCreate, db: Session = Depends(get_db)
):
    """Create a symmetric relationship (creates entries in both directions)"""
    repo = FamilyRepository(db)

    # Validate that the relationship type is symmetric
    if relationship_data.relationship_type not in [
        RelationshipType.BREEDING_PARTNER,
        RelationshipType.SIBLING_OF,
    ]:
        raise HTTPException(
            status_code=400,
            detail="Only breeding_partner and sibling_of relationships are symmetric",
        )

    # Convert API enum to DB enum
    db_relationship_type = DBRelationshipType[
        relationship_data.relationship_type.value.upper()
    ]

    try:
        rel1, rel2 = repo.create_symmetric_relationship(
            bird1_ring=relationship_data.bird1_ring,
            bird2_ring=relationship_data.bird2_ring,
            relationship_type=db_relationship_type,
            year=relationship_data.year,
            confidence=relationship_data.confidence,
            source=relationship_data.source,
            notes=relationship_data.notes,
        )

        return {
            "message": "Symmetric relationship created successfully",
            "relationships": [
                {
                    "id": rel1.id,
                    "bird1_ring": rel1.bird1_ring,
                    "bird2_ring": rel1.bird2_ring,
                    "relationship_type": rel1.relationship_type.value,
                },
                {
                    "id": rel2.id,
                    "bird1_ring": rel2.bird1_ring,
                    "bird2_ring": rel2.bird2_ring,
                    "relationship_type": rel2.relationship_type.value,
                },
            ],
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/relationships/{bird_ring}")
async def get_bird_relationships(
    bird_ring: str,
    relationship_type: Optional[RelationshipType] = None,
    year: Optional[int] = None,
    db: Session = Depends(get_db),
):
    """Get all relationships for a specific bird"""
    repo = FamilyRepository(db)

    # Convert API enum to DB enum if provided
    db_relationship_type = None
    if relationship_type:
        db_relationship_type = DBRelationshipType[relationship_type.value.upper()]

    relationships = repo.get_bird_relationships(
        bird_ring=bird_ring, relationship_type=db_relationship_type, year=year
    )

    return [
        {
            "id": rel.id,
            "bird1_ring": rel.bird1_ring,
            "bird2_ring": rel.bird2_ring,
            "relationship_type": rel.relationship_type.value,
            "year": rel.year,
            "confidence": rel.confidence,
            "source": rel.source,
            "notes": rel.notes,
            "sighting1_id": rel.sighting1_id,
            "sighting2_id": rel.sighting2_id,
            "ringing1_id": rel.ringing1_id,
            "ringing2_id": rel.ringing2_id,
            "created_at": rel.created_at.isoformat(),
            "updated_at": rel.updated_at.isoformat(),
        }
        for rel in relationships
    ]


@router.get("/partners/{bird_ring}", response_model=List[BirdPartner])
async def get_bird_partners(
    bird_ring: str,
    year: Optional[int] = None,
    unique_per_year: bool = Query(
        True, description="Return only unique partners per year"
    ),
    db: Session = Depends(get_db),
):
    """Get all breeding partners of a bird"""
    repo = FamilyRepository(db)
    partners = repo.get_partners(bird_ring, year, unique_per_year)
    return partners


@router.get("/children/{bird_ring}", response_model=List[BirdChild])
async def get_bird_children(
    bird_ring: str, year: Optional[int] = None, db: Session = Depends(get_db)
):
    """Get all children of a bird"""
    repo = FamilyRepository(db)
    children = repo.get_children(bird_ring, year)
    return children


@router.get("/parents/{bird_ring}", response_model=List[BirdParent])
async def get_bird_parents(
    bird_ring: str, year: Optional[int] = None, db: Session = Depends(get_db)
):
    """Get all parents of a bird"""
    repo = FamilyRepository(db)
    parents = repo.get_parents(bird_ring, year)
    return parents


@router.get("/siblings/{bird_ring}", response_model=List[BirdSibling])
async def get_bird_siblings(
    bird_ring: str,
    year: Optional[int] = None,
    include_half_siblings: bool = Query(False, description="Include half-siblings"),
    db: Session = Depends(get_db),
):
    """Get all siblings of a bird"""
    repo = FamilyRepository(db)
    siblings = repo.get_siblings(bird_ring, year, include_half_siblings)
    return siblings


@router.get("/family-tree/{bird_ring}", response_model=FamilyTreeResponse)
async def get_family_tree(
    bird_ring: str,
    max_generations: int = Query(
        3, ge=1, le=5, description="Maximum generations to retrieve"
    ),
    db: Session = Depends(get_db),
):
    """Get complete family tree for a bird"""
    repo = FamilyRepository(db)

    try:
        family_tree = repo.get_family_tree(bird_ring, max_generations)
        return FamilyTreeResponse(**family_tree)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{bird_ring}", response_model=RelationshipStatistics)
async def get_relationship_statistics(bird_ring: str, db: Session = Depends(get_db)):
    """Get statistics about a bird's relationships"""
    repo = FamilyRepository(db)

    try:
        stats = repo.get_relationship_statistics(bird_ring)
        return RelationshipStatistics(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/breeding-events", response_model=List[BreedingEventResponse])
async def get_breeding_events(
    bird_ring: Optional[str] = None,
    year: Optional[int] = None,
    location: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """Get breeding events with optional filters"""
    repo = FamilyRepository(db)

    events = repo.get_breeding_events(
        bird_ring=bird_ring, year=year, location=location
    )[:limit]

    return [
        BreedingEventResponse(
            id=event.id,
            year=event.year,
            location=event.location,
            nest_id=event.nest_id,
            parent1_ring=event.parent1_ring,
            parent2_ring=event.parent2_ring,
            clutch_size=event.clutch_size,
            fledged_count=event.fledged_count,
            breeding_success=event.breeding_success,
            created_at=event.created_at.isoformat(),
        )
        for event in events
    ]


@router.put("/relationships/{relationship_id}", response_model=RelationshipResponse)
async def update_relationship(
    relationship_id: UUID,
    relationship_data: RelationshipUpdate,
    update_symmetric: bool = Query(
        False, description="Also update symmetric relationship if it exists"
    ),
    db: Session = Depends(get_db),
):
    """Update a specific relationship"""
    repo = FamilyRepository(db)

    # Get existing relationship
    existing_relationship = repo.get_relationship_by_id(relationship_id)
    if not existing_relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")

    try:
        # Store original values for symmetric update
        original_type = existing_relationship.relationship_type
        bird1_ring = existing_relationship.bird1_ring
        bird2_ring = existing_relationship.bird2_ring

        # Update only provided fields
        if relationship_data.relationship_type is not None:
            db_relationship_type = DBRelationshipType[
                relationship_data.relationship_type.value.upper()
            ]
            existing_relationship.relationship_type = db_relationship_type

        if relationship_data.year is not None:
            existing_relationship.year = relationship_data.year

        if relationship_data.confidence is not None:
            existing_relationship.confidence = relationship_data.confidence

        if relationship_data.source is not None:
            existing_relationship.source = relationship_data.source

        if relationship_data.notes is not None:
            existing_relationship.notes = relationship_data.notes

        db.commit()
        db.refresh(existing_relationship)

        # Handle symmetric update if requested and relationship type is symmetric
        if update_symmetric and original_type in [
            DBRelationshipType.BREEDING_PARTNER,
            DBRelationshipType.SIBLING_OF,
        ]:
            # Find the symmetric relationship
            symmetric_relationship = (
                db.query(BirdRelationship)
                .filter(
                    BirdRelationship.bird1_ring == bird2_ring,
                    BirdRelationship.bird2_ring == bird1_ring,
                    BirdRelationship._relationship_type == cast(str, original_type.value),
                )
                .first()
            )

            if symmetric_relationship:
                # Update symmetric relationship with same changes
                if relationship_data.relationship_type is not None:
                    symmetric_relationship.relationship_type = (
                        existing_relationship.relationship_type
                    )
                if relationship_data.year is not None:
                    symmetric_relationship.year = existing_relationship.year
                if relationship_data.confidence is not None:
                    symmetric_relationship.confidence = existing_relationship.confidence
                if relationship_data.source is not None:
                    symmetric_relationship.source = existing_relationship.source
                if relationship_data.notes is not None:
                    symmetric_relationship.notes = existing_relationship.notes

                db.commit()

        return RelationshipResponse(
            id=existing_relationship.id,
            bird1_ring=existing_relationship.bird1_ring,
            bird2_ring=existing_relationship.bird2_ring,
            relationship_type=existing_relationship.relationship_type.value,
            year=existing_relationship.year,
            confidence=existing_relationship.confidence,
            source=existing_relationship.source,
            notes=existing_relationship.notes,
            sighting1_id=existing_relationship.sighting1_id,
            sighting2_id=existing_relationship.sighting2_id,
            ringing1_id=existing_relationship.ringing1_id,
            ringing2_id=existing_relationship.ringing2_id,
            created_at=existing_relationship.created_at.isoformat(),
            updated_at=existing_relationship.updated_at.isoformat(),
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/relationships", response_model=List[RelationshipResponse])
async def get_all_relationships(
    relationship_type: Optional[RelationshipType] = None,
    year: Optional[int] = None,
    bird_ring: Optional[str] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
):
    """Get all relationships with optional filters"""
    repo = FamilyRepository(db)

    # Convert API enum to DB enum if provided
    db_relationship_type = None
    if relationship_type:
        db_relationship_type = DBRelationshipType[relationship_type.value.upper()]

    relationships = repo.get_all_relationships(
        relationship_type=db_relationship_type,
        year=year,
        bird_ring=bird_ring,
        limit=limit,
        offset=offset,
    )

    return [
        RelationshipResponse(
            id=rel.id,
            bird1_ring=rel.bird1_ring,
            bird2_ring=rel.bird2_ring,
            relationship_type=rel.relationship_type.value,
            year=rel.year,
            confidence=rel.confidence,
            source=rel.source,
            notes=rel.notes,
            sighting1_id=rel.sighting1_id,
            sighting2_id=rel.sighting2_id,
            ringing1_id=rel.ringing1_id,
            ringing2_id=rel.ringing2_id,
            created_at=rel.created_at.isoformat(),
            updated_at=rel.updated_at.isoformat(),
        )
        for rel in relationships
    ]


@router.delete("/relationships/{relationship_id}")
async def delete_relationship(
    relationship_id: UUID,
    delete_symmetric: bool = Query(
        False, description="Also delete symmetric relationship if it exists"
    ),
    db: Session = Depends(get_db),
):
    """Delete a specific relationship"""
    repo = FamilyRepository(db)

    # Get the relationship before deleting to check for symmetric counterpart
    relationship = repo.get_relationship_by_id(relationship_id)
    if not relationship:
        raise HTTPException(status_code=404, detail="Relationship not found")

    # Store info for symmetric deletion
    bird1_ring = relationship.bird1_ring
    bird2_ring = relationship.bird2_ring
    relationship_type = relationship.relationship_type

    # Delete the main relationship
    if repo.delete_relationship(relationship_id):
        # Handle symmetric deletion if requested and relationship type is symmetric
        if delete_symmetric and relationship_type in [
            DBRelationshipType.BREEDING_PARTNER,
            DBRelationshipType.SIBLING_OF,
        ]:
            # Find and delete the symmetric relationship
            symmetric_relationship = (
                db.query(BirdRelationship)
                .filter(
                    BirdRelationship.bird1_ring == bird2_ring,
                    BirdRelationship.bird2_ring == bird1_ring,
                    BirdRelationship._relationship_type == cast(str, relationship_type.value),
                )
                .first()
            )

            if symmetric_relationship:
                db.delete(symmetric_relationship)
                db.commit()
                return {
                    "message": "Relationship and its symmetric counterpart deleted successfully"
                }

        return {"message": "Relationship deleted successfully"}
    else:
        raise HTTPException(status_code=404, detail="Relationship not found")
