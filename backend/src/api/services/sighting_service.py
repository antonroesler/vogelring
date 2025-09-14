"""
Sighting service layer - migrated from AWS Lambda to use PostgreSQL
"""
import logging
from typing import List, Optional, Dict, Any
from datetime import date
from sqlalchemy.orm import Session
from uuid import uuid4

from ...database.repositories import SightingRepository
from ...database.models import Sighting as SightingDB

logger = logging.getLogger(__name__)


class SightingService:
    """Service for sighting operations using PostgreSQL"""
    
    def __init__(self, db: Session):
        self.db = db
        self.repository = SightingRepository(db)
    
    def get_sighting_by_id(self, sighting_id: str) -> Optional[SightingDB]:
        """Get sighting by ID"""
        return self.repository.get_by_id(sighting_id)
    
    def get_sightings(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[SightingDB]:
        """Get all sightings with optional pagination"""
        return self.repository.get_all(limit=limit, offset=offset)
    
    def get_enriched_sightings(self, limit: Optional[int] = None, offset: Optional[int] = None) -> List[SightingDB]:
        """Get sightings with ringing data joined"""
        return self.repository.get_enriched_sightings(limit=limit, offset=offset)
    
    def get_sightings_count(self) -> int:
        """Get total count of sightings"""
        return self.db.query(SightingDB).count()
    
    def get_sightings_by_species(self, species: str) -> List[SightingDB]:
        """Get all sightings for a specific species"""
        return self.repository.get_by_species(species)
    
    def get_sightings_by_ring(self, ring: str) -> List[SightingDB]:
        """Get all sightings for a specific ring"""
        return self.repository.get_by_ring(ring)
    
    def get_sightings_by_place(self, place: str) -> List[SightingDB]:
        """Get all sightings for a specific place"""
        return self.repository.get_by_place(place)
    
    def get_sightings_by_date(self, date_filter: date) -> List[SightingDB]:
        """Get all sightings for a specific date"""
        return self.repository.get_by_date_range(date_filter, date_filter)
    
    def get_sightings_by_date_range(self, start_date: date, end_date: date) -> List[SightingDB]:
        """Get sightings within a date range"""
        return self.repository.get_by_date_range(start_date, end_date)
    
    def get_sightings_by_radius(self, lat: float, lon: float, radius_m: int) -> List[SightingDB]:
        """Get sightings within a radius of a location"""
        # Get all sightings with location data
        all_sightings = self.repository.get_all()
        
        # Filter by radius using Haversine formula
        from ...utils.distance import calculate_distance
        
        result = []
        for sighting in all_sightings:
            if sighting.lat is not None and sighting.lon is not None:
                distance = calculate_distance(
                    float(sighting.lat), float(sighting.lon), lat, lon
                )
                if distance <= radius_m:
                    result.append(sighting)
        
        return result
    
    def search_sightings(self, filters: Dict[str, Any]) -> List[SightingDB]:
        """Search sightings with multiple filters"""
        return self.repository.search_sightings(filters)
    
    def add_sighting(self, sighting_data: Dict[str, Any]) -> SightingDB:
        """Create a new sighting"""
        try:
            # Generate ID if not provided
            if 'id' not in sighting_data or not sighting_data['id']:
                sighting_data['id'] = str(uuid4())
            
            sighting = self.repository.create(**sighting_data)
            logger.info(f"Created sighting {sighting.id}")
            
            # Handle partner relationship if specified
            if sighting.ring and sighting.partner and sighting.date:
                try:
                    from .family_service import FamilyService
                    family_service = FamilyService(self.db)
                    family_service.add_partner_relationship_from_sighting(
                        sighting.ring, sighting.partner, sighting.date.year
                    )
                    logger.info(f"Added partner relationship: {sighting.ring} <-> {sighting.partner} ({sighting.date.year})")
                except Exception as e:
                    logger.error(f"Failed to add partner relationship for sighting {sighting.id}: {str(e)}")
            
            return sighting
            
        except Exception as e:
            logger.error(f"Error creating sighting: {e}")
            raise
    
    def update_sighting(self, sighting_id: str, sighting_data: Dict[str, Any]) -> Optional[SightingDB]:
        """Update an existing sighting"""
        try:
            # Get old sighting for partner relationship comparison
            old_sighting = self.repository.get_by_id(sighting_id)
            if not old_sighting:
                return None
            
            # Update the sighting
            updated_sighting = self.repository.update(sighting_id, **sighting_data)
            if not updated_sighting:
                return None
            
            logger.info(f"Updated sighting {sighting_id}")
            
            # Handle partner relationship if changed
            if (updated_sighting.ring and updated_sighting.partner and updated_sighting.date and
                (not old_sighting.partner or old_sighting.partner != updated_sighting.partner)):
                try:
                    from .family_service import FamilyService
                    family_service = FamilyService(self.db)
                    family_service.add_partner_relationship_from_sighting(
                        updated_sighting.ring, updated_sighting.partner, updated_sighting.date.year
                    )
                    logger.info(f"Added partner relationship: {updated_sighting.ring} <-> {updated_sighting.partner} ({updated_sighting.date.year})")
                except Exception as e:
                    logger.error(f"Failed to add partner relationship for sighting {sighting_id}: {str(e)}")
            
            return updated_sighting
            
        except Exception as e:
            logger.error(f"Error updating sighting {sighting_id}: {e}")
            raise
    
    def delete_sighting(self, sighting_id: str) -> bool:
        """Delete a sighting"""
        try:
            result = self.repository.delete(sighting_id)
            if result:
                logger.info(f"Deleted sighting {sighting_id}")
            return result
        except Exception as e:
            logger.error(f"Error deleting sighting {sighting_id}: {e}")
            raise
    
    def get_next_sighting_id(self) -> str:
        """Generate next sighting ID (UUID-based)"""
        return str(uuid4())
    
    # Autocomplete and suggestion methods
    def get_autocomplete_suggestions(self, field: str, query: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions for a field"""
        return self.repository.get_autocomplete_suggestions(field, query, limit)
    
    def get_species_list(self) -> List[str]:
        """Get list of all unique species"""
        return self.repository.get_species_list()
    
    def get_place_list(self) -> List[str]:
        """Get list of all unique places"""
        return self.repository.get_place_list()
    
    def get_ring_list(self) -> List[str]:
        """Get list of all unique rings"""
        return self.repository.get_ring_list()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get basic statistics about sightings"""
        return self.repository.get_statistics()