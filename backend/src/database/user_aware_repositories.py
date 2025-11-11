"""
Organization-aware repository implementations for multi-tenant data access
"""

import logging
from typing import List, Optional, Dict, Any, Tuple
from datetime import date
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, desc

from .models import Sighting, Ringing
from .family_models import BirdRelationship
from .user_models import User
from .organization_repository import OrganizationAwareRepository

logger = logging.getLogger(__name__)


class OrganizationAwareSightingRepository(OrganizationAwareRepository[Sighting]):
    """Organization-aware sighting repository"""

    def __init__(self, db: Session, current_user: User):
        super().__init__(db, Sighting, current_user)

    def get_by_ring(self, ring: str, limit: int = 100) -> List[Sighting]:
        """Get sightings by ring number for current organization"""
        return (
            self.db.query(Sighting)
            .filter(and_(Sighting.ring == ring, self._get_org_filter()))
            .order_by(desc(Sighting.date))
            .limit(limit)
            .all()
        )

    def get_by_species(self, species: str, limit: int = 100) -> List[Sighting]:
        """Get sightings by species for current organization"""
        return (
            self.db.query(Sighting)
            .filter(and_(Sighting.species == species, self._get_org_filter()))
            .order_by(desc(Sighting.date))
            .limit(limit)
            .all()
        )

    def get_by_date_range(
        self, start_date: date, end_date: date, limit: int = 1000
    ) -> List[Sighting]:
        """Get sightings within date range for current organization"""
        return (
            self.db.query(Sighting)
            .filter(
                and_(
                    Sighting.date >= start_date,
                    Sighting.date <= end_date,
                    self._get_org_filter(),
                )
            )
            .order_by(desc(Sighting.date))
            .limit(limit)
            .all()
        )

    def search_sightings(
        self,
        ring: Optional[str] = None,
        species: Optional[str] = None,
        place: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Sighting], int]:
        """Search sightings with filters for current organization"""
        query = self.db.query(Sighting).filter(self._get_org_filter())

        # Apply filters
        if ring:
            query = query.filter(Sighting.ring.ilike(f"%{ring}%"))
        if species:
            query = query.filter(Sighting.species.ilike(f"%{species}%"))
        if place:
            query = query.filter(Sighting.place.ilike(f"%{place}%"))
        if start_date:
            query = query.filter(Sighting.date >= start_date)
        if end_date:
            query = query.filter(Sighting.date <= end_date)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        sightings = (
            query.order_by(desc(Sighting.date)).offset(offset).limit(limit).all()
        )

        return sightings, total

    def get_species_summary(self) -> List[Dict[str, Any]]:
        """Get species summary for current organization"""
        return (
            self.db.query(
                Sighting.species,
                func.count(Sighting.id).label("count"),
                func.max(Sighting.date).label("last_seen"),
                func.count(func.distinct(Sighting.ring)).label("unique_rings"),
            )
            .filter(self._get_org_filter())
            .group_by(Sighting.species)
            .order_by(desc("count"))
            .all()
        )


class OrganizationAwareRingingRepository(OrganizationAwareRepository[Ringing]):
    """Organization-aware ringing repository"""

    def __init__(self, db: Session, current_user: User):
        super().__init__(db, Ringing, current_user)

    def get_by_ring(self, ring: str) -> Optional[Ringing]:
        """Get ringing by ring number for current organization"""
        return (
            self.db.query(Ringing)
            .filter(and_(Ringing.ring == ring, self._get_org_filter()))
            .first()
        )

    def get_by_species(self, species: str, limit: int = 100) -> List[Ringing]:
        """Get ringings by species for current organization"""
        return (
            self.db.query(Ringing)
            .filter(and_(Ringing.species == species, self._get_org_filter()))
            .order_by(desc(Ringing.date))
            .limit(limit)
            .all()
        )

    def search_ringings(
        self,
        ring: Optional[str] = None,
        species: Optional[str] = None,
        place: Optional[str] = None,
        ringer: Optional[str] = None,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Tuple[List[Ringing], int]:
        """Search ringings with filters for current organization"""
        query = self.db.query(Ringing).filter(self._get_org_filter())

        # Apply filters
        if ring:
            query = query.filter(Ringing.ring.ilike(f"%{ring}%"))
        if species:
            query = query.filter(Ringing.species.ilike(f"%{species}%"))
        if place:
            query = query.filter(Ringing.place.ilike(f"%{place}%"))
        if ringer:
            query = query.filter(Ringing.ringer.ilike(f"%{ringer}%"))
        if start_date:
            query = query.filter(Ringing.date >= start_date)
        if end_date:
            query = query.filter(Ringing.date <= end_date)

        # Get total count
        total = query.count()

        # Apply pagination and ordering
        ringings = query.order_by(desc(Ringing.date)).offset(offset).limit(limit).all()

        return ringings, total

    def get_ringer_summary(self) -> List[Dict[str, Any]]:
        """Get ringer summary for current organization"""
        return (
            self.db.query(
                Ringing.ringer,
                func.count(Ringing.id).label("count"),
                func.max(Ringing.date).label("last_ringing"),
                func.count(func.distinct(Ringing.species)).label("species_count"),
            )
            .filter(self._get_org_filter())
            .group_by(Ringing.ringer)
            .order_by(desc("count"))
            .all()
        )


class OrganizationAwareFamilyRepository(OrganizationAwareRepository[BirdRelationship]):
    """Organization-aware family relationship repository"""

    def __init__(self, db: Session, current_user: User):
        super().__init__(db, BirdRelationship, current_user)

    def get_bird_relationships(self, bird_ring: str) -> List[BirdRelationship]:
        """Get all relationships for a bird for current organization"""
        return (
            self.db.query(BirdRelationship)
            .filter(
                and_(
                    or_(
                        BirdRelationship.bird1_ring == bird_ring,
                        BirdRelationship.bird2_ring == bird_ring,
                    ),
                    self._get_org_filter(),
                )
            )
            .order_by(desc(BirdRelationship.year))
            .all()
        )

    def get_breeding_partners(
        self, bird_ring: str, year: Optional[int] = None
    ) -> List[BirdRelationship]:
        """Get breeding partners for a bird for current organization"""
        query = self.db.query(BirdRelationship).filter(
            and_(
                or_(
                    BirdRelationship.bird1_ring == bird_ring,
                    BirdRelationship.bird2_ring == bird_ring,
                ),
                BirdRelationship._relationship_type == "breeding_partner",
                self._get_org_filter(),
            )
        )

        if year:
            query = query.filter(BirdRelationship.year == year)

        return query.order_by(desc(BirdRelationship.year)).all()

    def get_offspring(self, parent_ring: str) -> List[BirdRelationship]:
        """Get offspring for a parent bird for current organization"""
        return (
            self.db.query(BirdRelationship)
            .filter(
                and_(
                    BirdRelationship.bird1_ring == parent_ring,
                    BirdRelationship._relationship_type == "parent_of",
                    self._get_org_filter(),
                )
            )
            .order_by(desc(BirdRelationship.year))
            .all()
        )

    def get_parents(self, child_ring: str) -> List[BirdRelationship]:
        """Get parents for a child bird for current organization"""
        return (
            self.db.query(BirdRelationship)
            .filter(
                and_(
                    BirdRelationship.bird2_ring == child_ring,
                    BirdRelationship._relationship_type == "parent_of",
                    self._get_org_filter(),
                )
            )
            .order_by(desc(BirdRelationship.year))
            .all()
        )

    def create_symmetric_relationship(
        self,
        bird_ring_1: str,
        bird_ring_2: str,
        relationship_type: str,
        year: int,
        **kwargs,
    ) -> List[BirdRelationship]:
        """Create symmetric relationship (e.g., breeding partners, siblings) for current organization"""
        relationships = []

        try:
            # Create first relationship
            rel1 = self.create(
                bird1_ring=bird_ring_1,
                bird2_ring=bird_ring_2,
                _relationship_type=relationship_type,
                year=year,
                **kwargs,
            )
            relationships.append(rel1)

            # Create reverse relationship for symmetric types
            if relationship_type in ["breeding_partner", "sibling_of"]:
                rel2 = self.create(
                    bird1_ring=bird_ring_2,
                    bird2_ring=bird_ring_1,
                    _relationship_type=relationship_type,
                    year=year,
                    **kwargs,
                )
                relationships.append(rel2)

        except Exception as e:
            logger.error(f"Error creating symmetric relationship: {e}")
            raise

        return relationships
