"""
Ringing service layer - migrated from AWS Lambda to use PostgreSQL
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session

from ...database.repositories import RingingRepository
from ...database.models import Ringing as RingingDB

logger = logging.getLogger(__name__)


class RingingService:
    """Service for ringing operations using PostgreSQL"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = RingingRepository(db)
    
    def get_ringing_by_ring(self, ring: str) -> Optional[RingingDB]:
        """Get ringing by ring number"""
        return self.repository.get_by_ring(ring)
    
    def get_all_ringings(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[RingingDB]:
        """Get all ringings with optional pagination"""
        return self.repository.get_all(limit=limit, offset=offset)
    
    def get_ringings_by_species(self, species: str) -> List[RingingDB]:
        """Get all ringings for a specific species"""
        return self.repository.get_by_species(species)
    
    def get_ringings_by_ringer(self, ringer: str) -> List[RingingDB]:
        """Get all ringings by a specific ringer"""
        return self.repository.get_by_ringer(ringer)
    
    def get_ringings_by_place(self, place: str) -> List[RingingDB]:
        """Get all ringings at a specific place"""
        return self.repository.get_by_place(place)
    
    def get_ringings_by_date_range(self, start_date: date, end_date: date) -> List[RingingDB]:
        """Get ringings within a date range"""
        return self.repository.get_by_date_range(start_date, end_date)
    
    def search_ringings(self, filters: Dict[str, Any]) -> List[RingingDB]:
        """Search ringings with multiple filters"""
        return self.repository.search_ringings(filters)
    
    def upsert_ringing(self, ringing_data: Dict[str, Any]) -> RingingDB:
        """Insert or update a ringing record"""
        try:
            ring = ringing_data.get('ring')
            if not ring:
                raise ValueError("Ring number is required")
            
            # Remove ring from data since it's passed separately to upsert_ringing
            ring_data = {k: v for k, v in ringing_data.items() if k != 'ring'}
            
            ringing = self.repository.upsert_ringing(ring, **ring_data)
            logger.info(f"Upserted ringing for ring {ring}")
            return ringing
            
        except Exception as e:
            logger.error(f"Error upserting ringing: {e}")
            raise
    
    def delete_ringing(self, ring: str) -> bool:
        """Delete a ringing record by ring number"""
        try:
            ringing = self.repository.get_by_ring(ring)
            if not ringing:
                # Return True even if ring doesn't exist (matches original behavior)
                logger.info(f"Ring {ring} not found, but delete operation considered successful")
                return True
            
            result = self.repository.delete(ringing.id)
            if result:
                logger.info(f"Deleted ringing for ring {ring}")
            return result
            
        except Exception as e:
            logger.error(f"Error deleting ringing for ring {ring}: {e}")
            raise
    
    def get_ringings_count(self) -> int:
        """Get total count of ringings"""
        return self.db.query(RingingDB).count()
    
    # Autocomplete and suggestion methods
    def get_autocomplete_suggestions(self, field: str, query: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions for a field"""
        return self.repository.get_autocomplete_suggestions(field, query, limit)
    
    def get_species_list(self) -> List[str]:
        """Get list of all unique species from ringings"""
        return self.repository.get_species_list()
    
    def get_ringer_list(self) -> List[str]:
        """Get list of all unique ringers"""
        return self.repository.get_ringer_list()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about ringings"""
        return self.repository.get_statistics()
    
    def get_entry_list_ringings(self, filters: Dict[str, Any], limit: Optional[int] = None, offset: Optional[int] = None) -> List[RingingDB]:
        """Get ringings for entry list filtered to target species"""
        return self.repository.get_entry_list_ringings(filters, limit=limit, offset=offset)
    
    def get_entry_list_ringings_count(self, filters: Dict[str, Any]) -> int:
        """Get count of ringings for entry list filtered to target species"""
        return self.repository.get_entry_list_ringings_count(filters)