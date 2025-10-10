"""
Database repository layer for data access operations
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import date, datetime, timedelta
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, or_, func, desc, asc, text
from sqlalchemy.exc import IntegrityError

from .models import Sighting, Ringing
from ..utils.cache import get_cached_data

logger = logging.getLogger(__name__)


class BaseRepository:
    """Base repository class with common operations"""

    def __init__(self, db: Session, model_class):
        self.db = db
        self.model_class = model_class

    def get_by_id(self, id: str):
        """Get record by ID"""
        return self.db.query(self.model_class).filter(self.model_class.id == id).first()

    def create(self, **kwargs):
        """Create new record"""
        try:
            instance = self.model_class(**kwargs)
            self.db.add(instance)
            self.db.commit()
            return instance
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error creating {self.model_class.__name__}: {e}")
            raise

    def update(self, id: str, **kwargs):
        """Update record by ID"""
        try:
            instance = self.get_by_id(id)
            if not instance:
                return None

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

    def delete(self, id: str):
        """Delete record by ID"""
        try:
            instance = self.get_by_id(id)
            if instance:
                self.db.delete(instance)
                self.db.commit()
                return True
            return False
        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error deleting {self.model_class.__name__}: {e}")
            raise


class SightingRepository(BaseRepository):
    """Repository for sighting data operations"""

    def __init__(self, db: Session):
        super().__init__(db, Sighting)

    def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Sighting]:
        """Get all sightings with optional pagination"""
        query = self.db.query(Sighting).order_by(
            desc(Sighting.date), desc(Sighting.created_at)
        )

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    def get_enriched_sightings(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Sighting]:
        """Get sightings with ringing data joined"""
        query = (
            self.db.query(Sighting)
            .outerjoin(
                Ringing, and_(Sighting.ring == Ringing.ring, Sighting.ring.isnot(None))
            )
            .options(joinedload(Sighting.ringing_data))
            .order_by(desc(Sighting.date), desc(Sighting.created_at))
        )

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    def get_by_ring(self, ring: str) -> List[Sighting]:
        """Get all sightings for a specific ring"""
        return (
            self.db.query(Sighting)
            .filter(Sighting.ring == ring)
            .order_by(desc(Sighting.date))
            .all()
        )

    def get_by_species(self, species: str) -> List[Sighting]:
        """Get all sightings for a specific species"""
        return (
            self.db.query(Sighting)
            .filter(Sighting.species == species)
            .order_by(desc(Sighting.date))
            .all()
        )

    def get_by_place(self, place: str) -> List[Sighting]:
        """Get all sightings for a specific place"""
        return (
            self.db.query(Sighting)
            .filter(Sighting.place == place)
            .order_by(desc(Sighting.date))
            .all()
        )

    def get_by_date_range(self, start_date: date, end_date: date) -> List[Sighting]:
        """Get sightings within a date range"""
        return (
            self.db.query(Sighting)
            .filter(and_(Sighting.date >= start_date, Sighting.date <= end_date))
            .order_by(desc(Sighting.date))
            .all()
        )

    def search_sightings(self, filters: Dict[str, Any]) -> List[Sighting]:
        """Search sightings with multiple filters using optimized queries"""
        query = self.db.query(Sighting)

        # Apply filters with case-insensitive search for better performance
        if filters.get("species"):
            query = query.filter(
                func.lower(Sighting.species).like(f"%{filters['species'].lower()}%")
            )

        if filters.get("ring"):
            query = query.filter(
                func.lower(Sighting.ring).like(f"%{filters['ring'].lower()}%")
            )

        if filters.get("place"):
            query = query.filter(
                func.lower(Sighting.place).like(f"%{filters['place'].lower()}%")
            )

        if filters.get("start_date"):
            query = query.filter(Sighting.date >= filters["start_date"])

        if filters.get("end_date"):
            query = query.filter(Sighting.date <= filters["end_date"])

        if filters.get("sex"):
            query = query.filter(Sighting.sex == filters["sex"])

        if filters.get("status"):
            query = query.filter(Sighting.status == filters["status"])

        if filters.get("melder"):
            query = query.filter(
                func.lower(Sighting.melder).like(f"%{filters['melder'].lower()}%")
            )

        # Use composite index for species+date or place+date when possible
        if filters.get("species") and (
            filters.get("start_date") or filters.get("end_date")
        ):
            return query.order_by(Sighting.species, desc(Sighting.date)).all()
        elif filters.get("place") and (
            filters.get("start_date") or filters.get("end_date")
        ):
            return query.order_by(Sighting.place, desc(Sighting.date)).all()
        else:
            return query.order_by(desc(Sighting.date)).all()

    def get_autocomplete_suggestions(
        self, field: str, query: str, limit: int = 10
    ) -> List[str]:
        """Get autocomplete suggestions for a specific field using optimized case-insensitive search"""
        if not hasattr(Sighting, field):
            return []

        column = getattr(Sighting, field)
        query_lower = query.lower()

        # Use case-insensitive search with optimized indexes
        results = (
            self.db.query(column)
            .filter(
                and_(
                    column.isnot(None),
                    func.lower(column).like(
                        f"{query_lower}%"
                    ),  # Use prefix matching for better performance
                )
            )
            .distinct()
            .order_by(func.lower(column))  # Case-insensitive ordering
            .limit(limit)
            .all()
        )

        return [result[0] for result in results if result[0]]

    def get_species_list(self) -> List[str]:
        """Get list of all unique species with caching"""

        def fetch_species():
            results = (
                self.db.query(Sighting.species)
                .filter(Sighting.species.isnot(None))
                .distinct()
                .order_by(func.lower(Sighting.species))
                .all()
            )
            return [result[0] for result in results if result[0]]

        return get_cached_data("sighting_species_list", fetch_species)

    def get_place_list(self) -> List[str]:
        """Get list of all unique places with caching"""

        def fetch_places():
            results = (
                self.db.query(Sighting.place)
                .filter(Sighting.place.isnot(None))
                .distinct()
                .order_by(func.lower(Sighting.place))
                .all()
            )
            return [result[0] for result in results if result[0]]

        return get_cached_data("sighting_place_list", fetch_places)

    def get_ring_list(self) -> List[str]:
        """Get list of all unique rings with caching"""

        def fetch_rings():
            results = (
                self.db.query(Sighting.ring)
                .filter(Sighting.ring.isnot(None))
                .distinct()
                .order_by(func.lower(Sighting.ring))
                .all()
            )
            return [result[0] for result in results if result[0]]

        return get_cached_data("sighting_ring_list", fetch_rings)

    def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about sightings"""
        total_count = self.db.query(Sighting).count()

        species_count = (
            self.db.query(Sighting.species)
            .filter(Sighting.species.isnot(None))
            .distinct()
            .count()
        )

        ring_count = (
            self.db.query(Sighting.ring)
            .filter(Sighting.ring.isnot(None))
            .distinct()
            .count()
        )

        place_count = (
            self.db.query(Sighting.place)
            .filter(Sighting.place.isnot(None))
            .distinct()
            .count()
        )

        # Get date range
        date_range = (
            self.db.query(func.min(Sighting.date), func.max(Sighting.date))
            .filter(Sighting.date.isnot(None))
            .first()
        )

        return {
            "total_sightings": total_count,
            "unique_species": species_count,
            "unique_rings": ring_count,
            "unique_places": place_count,
            "date_range": {"earliest": date_range[0], "latest": date_range[1]},
        }


class RingingRepository(BaseRepository):
    """Repository for ringing data operations"""

    def __init__(self, db: Session):
        super().__init__(db, Ringing)

    def get_all(
        self, limit: Optional[int] = None, offset: Optional[int] = None
    ) -> List[Ringing]:
        """Get all ringings with optional pagination"""
        query = self.db.query(Ringing).order_by(
            desc(Ringing.date), desc(Ringing.created_at)
        )

        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    def get_by_ring(self, ring: str) -> Optional[Ringing]:
        """Get ringing by ring number"""
        return self.db.query(Ringing).filter(Ringing.ring == ring).first()

    def get_by_species(self, species: str) -> List[Ringing]:
        """Get all ringings for a specific species"""
        return (
            self.db.query(Ringing)
            .filter(Ringing.species == species)
            .order_by(desc(Ringing.date))
            .all()
        )

    def get_by_ringer(self, ringer: str) -> List[Ringing]:
        """Get all ringings by a specific ringer"""
        return (
            self.db.query(Ringing)
            .filter(Ringing.ringer == ringer)
            .order_by(desc(Ringing.date))
            .all()
        )

    def get_by_place(self, place: str) -> List[Ringing]:
        """Get all ringings at a specific place"""
        return (
            self.db.query(Ringing)
            .filter(Ringing.place == place)
            .order_by(desc(Ringing.date))
            .all()
        )

    def get_by_date_range(self, start_date: date, end_date: date) -> List[Ringing]:
        """Get ringings within a date range"""
        return (
            self.db.query(Ringing)
            .filter(and_(Ringing.date >= start_date, Ringing.date <= end_date))
            .order_by(desc(Ringing.date))
            .all()
        )

    def search_ringings(self, filters: Dict[str, Any]) -> List[Ringing]:
        """Search ringings with multiple filters using optimized queries"""
        query = self.db.query(Ringing)

        # Apply filters with case-insensitive search for better performance
        if filters.get("species"):
            query = query.filter(
                func.lower(Ringing.species).like(f"%{filters['species'].lower()}%")
            )

        if filters.get("ring"):
            query = query.filter(
                func.lower(Ringing.ring).like(f"%{filters['ring'].lower()}%")
            )

        if filters.get("place"):
            query = query.filter(
                func.lower(Ringing.place).like(f"%{filters['place'].lower()}%")
            )

        if filters.get("ringer"):
            query = query.filter(
                func.lower(Ringing.ringer).like(f"%{filters['ringer'].lower()}%")
            )

        if filters.get("start_date"):
            query = query.filter(Ringing.date >= filters["start_date"])

        if filters.get("end_date"):
            query = query.filter(Ringing.date <= filters["end_date"])

        if filters.get("sex") is not None:
            query = query.filter(Ringing.sex == filters["sex"])

        if filters.get("age") is not None:
            query = query.filter(Ringing.age == filters["age"])

        # Use composite index for species+date or ringer+date when possible
        if filters.get("species") and (
            filters.get("start_date") or filters.get("end_date")
        ):
            return query.order_by(Ringing.species, desc(Ringing.date)).all()
        elif filters.get("ringer") and (
            filters.get("start_date") or filters.get("end_date")
        ):
            return query.order_by(Ringing.ringer, desc(Ringing.date)).all()
        else:
            return query.order_by(desc(Ringing.date)).all()

    def upsert_ringing(self, ring: str, **kwargs) -> Ringing:
        """Insert or update ringing data"""
        try:
            existing = self.get_by_ring(ring)

            if existing:
                # Update existing record
                for key, value in kwargs.items():
                    if hasattr(existing, key):
                        setattr(existing, key, value)

                self.db.commit()
                self.db.refresh(existing)
                return existing
            else:
                # Create new record
                kwargs["ring"] = ring
                return self.create(**kwargs)

        except IntegrityError as e:
            self.db.rollback()
            logger.error(f"Error upserting ringing for ring {ring}: {e}")
            raise

    def get_autocomplete_suggestions(
        self, field: str, query: str, limit: int = 10
    ) -> List[str]:
        """Get autocomplete suggestions for a specific field using optimized case-insensitive search"""
        if not hasattr(Ringing, field):
            return []

        column = getattr(Ringing, field)
        query_lower = query.lower()

        # Use case-insensitive search with optimized indexes
        results = (
            self.db.query(column)
            .filter(
                and_(
                    column.isnot(None),
                    func.lower(column).like(
                        f"{query_lower}%"
                    ),  # Use prefix matching for better performance
                )
            )
            .distinct()
            .order_by(func.lower(column))  # Case-insensitive ordering
            .limit(limit)
            .all()
        )

        return [result[0] for result in results if result[0]]

    def get_species_list(self) -> List[str]:
        """Get list of all unique species from ringings with caching"""

        def fetch_species():
            results = (
                self.db.query(Ringing.species)
                .distinct()
                .order_by(func.lower(Ringing.species))
                .all()
            )
            return [result[0] for result in results]

        return get_cached_data("ringing_species_list", fetch_species)

    def get_ringer_list(self) -> List[str]:
        """Get list of all unique ringers with caching"""

        def fetch_ringers():
            results = (
                self.db.query(Ringing.ringer)
                .distinct()
                .order_by(func.lower(Ringing.ringer))
                .all()
            )
            return [result[0] for result in results]

        return get_cached_data("ringing_ringer_list", fetch_ringers)

    def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about ringings"""
        total_count = self.db.query(Ringing).count()

        species_count = self.db.query(Ringing.species).distinct().count()
        ringer_count = self.db.query(Ringing.ringer).distinct().count()
        place_count = self.db.query(Ringing.place).distinct().count()

        # Get date range
        date_range = self.db.query(
            func.min(Ringing.date), func.max(Ringing.date)
        ).first()

        return {
            "total_ringings": total_count,
            "unique_species": species_count,
            "unique_ringers": ringer_count,
            "unique_places": place_count,
            "date_range": {"earliest": date_range[0], "latest": date_range[1]},
        }

    def get_entry_list_ringings(
        self,
        filters: Dict[str, Any],
        limit: Optional[int] = None,
        offset: Optional[int] = None,
    ) -> List[Ringing]:
        """Get ringings for entry list filtered to target species"""
        # Target species codes and names
        target_species_codes = ["01660", "01610", "01520", "01700", "01670"]
        target_species_names = [
            "Kanadagans",
            "Graugans",
            "Höckerschwan",
            "Nilgans",
            "Weißwangengans",
        ]

        # Start with base query filtering to target species
        query = self.db.query(Ringing).filter(
            or_(
                Ringing.species.in_(target_species_codes),
                Ringing.species.in_(target_species_names),
            )
        )

        # Apply additional filters
        if filters.get("species"):
            query = query.filter(
                func.lower(Ringing.species).like(f"%{filters['species'].lower()}%")
            )

        if filters.get("ring"):
            query = query.filter(
                func.lower(Ringing.ring).like(f"%{filters['ring'].lower()}%")
            )

        if filters.get("place"):
            query = query.filter(
                func.lower(Ringing.place).like(f"%{filters['place'].lower()}%")
            )

        if filters.get("ringer"):
            query = query.filter(
                func.lower(Ringing.ringer).like(f"%{filters['ringer'].lower()}%")
            )

        if filters.get("start_date"):
            query = query.filter(Ringing.date >= filters["start_date"])

        if filters.get("end_date"):
            query = query.filter(Ringing.date <= filters["end_date"])

        # Order by date (newest first)
        query = query.order_by(desc(Ringing.date), desc(Ringing.created_at))

        # Apply pagination
        if offset:
            query = query.offset(offset)
        if limit:
            query = query.limit(limit)

        return query.all()

    def get_entry_list_ringings_count(self, filters: Dict[str, Any]) -> int:
        """Get count of ringings for entry list filtered to target species"""
        # Target species codes and names
        target_species_codes = ["01660", "01610", "01520", "01700", "01670"]
        target_species_names = [
            "Kanadagans",
            "Graugans",
            "Höckerschwan",
            "Nilgans",
            "Weißwangengans",
        ]

        # Start with base query filtering to target species
        query = self.db.query(Ringing).filter(
            or_(
                Ringing.species.in_(target_species_codes),
                Ringing.species.in_(target_species_names),
            )
        )

        # Apply additional filters
        if filters.get("species"):
            query = query.filter(
                func.lower(Ringing.species).like(f"%{filters['species'].lower()}%")
            )

        if filters.get("ring"):
            query = query.filter(
                func.lower(Ringing.ring).like(f"%{filters['ring'].lower()}%")
            )

        if filters.get("place"):
            query = query.filter(
                func.lower(Ringing.place).like(f"%{filters['place'].lower()}%")
            )

        if filters.get("ringer"):
            query = query.filter(
                func.lower(Ringing.ringer).like(f"%{filters['ringer'].lower()}%")
            )

        if filters.get("start_date"):
            query = query.filter(Ringing.date >= filters["start_date"])

        if filters.get("end_date"):
            query = query.filter(Ringing.date <= filters["end_date"])

        return query.count()
