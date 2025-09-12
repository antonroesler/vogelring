"""
Suggestion service layer - migrated from AWS Lambda to use PostgreSQL
"""
import logging
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct
from collections import Counter

from ...database.repositories import SightingRepository, RingingRepository
from ...database.models import Sighting as SightingDB, Ringing as RingingDB
from ...utils.cache import cached

logger = logging.getLogger(__name__)


class SuggestionService:
    """Service for autocomplete and suggestion operations using PostgreSQL"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sighting_repository = SightingRepository(db)
        self.ringing_repository = RingingRepository(db)
    
    @cached(ttl=600)  # Cache for 10 minutes
    def get_suggestion_lists(self) -> Dict[str, List[str]]:
        """Get lists of all suggestions for places, species, habitats, and melders ordered by frequency"""
        
        # Get places ordered by frequency
        places_query = (self.db.query(SightingDB.place, func.count(SightingDB.place).label('count'))
                       .filter(SightingDB.place.isnot(None))
                       .filter(SightingDB.place != '')
                       .group_by(SightingDB.place)
                       .order_by(func.count(SightingDB.place).desc())
                       .all())
        places = [result[0] for result in places_query]
        
        # Get species ordered by frequency (combine from sightings and ringings)
        sighting_species = (self.db.query(SightingDB.species, func.count(SightingDB.species).label('count'))
                           .filter(SightingDB.species.isnot(None))
                           .filter(SightingDB.species != '')
                           .group_by(SightingDB.species)
                           .all())
        
        ringing_species = (self.db.query(RingingDB.species, func.count(RingingDB.species).label('count'))
                          .filter(RingingDB.species.isnot(None))
                          .filter(RingingDB.species != '')
                          .group_by(RingingDB.species)
                          .all())
        
        # Combine species counts
        species_counts = Counter()
        for species, count in sighting_species:
            species_counts[species] += count
        for species, count in ringing_species:
            species_counts[species] += count
        
        species = [species for species, _ in species_counts.most_common()]
        
        # Get habitats ordered by frequency
        habitats_query = (self.db.query(SightingDB.habitat, func.count(SightingDB.habitat).label('count'))
                         .filter(SightingDB.habitat.isnot(None))
                         .filter(SightingDB.habitat != '')
                         .group_by(SightingDB.habitat)
                         .order_by(func.count(SightingDB.habitat).desc())
                         .all())
        habitats = [result[0] for result in habitats_query]
        
        # Get melders ordered by frequency
        melders_query = (self.db.query(SightingDB.melder, func.count(SightingDB.melder).label('count'))
                        .filter(SightingDB.melder.isnot(None))
                        .filter(SightingDB.melder != '')
                        .group_by(SightingDB.melder)
                        .order_by(func.count(SightingDB.melder).desc())
                        .all())
        melders = [result[0] for result in melders_query]
        
        # Get field fruits ordered by frequency
        field_fruits_query = (self.db.query(SightingDB.field_fruit, func.count(SightingDB.field_fruit).label('count'))
                             .filter(SightingDB.field_fruit.isnot(None))
                             .filter(SightingDB.field_fruit != '')
                             .group_by(SightingDB.field_fruit)
                             .order_by(func.count(SightingDB.field_fruit).desc())
                             .all())
        field_fruits = [result[0] for result in field_fruits_query]
        
        # Get ringers ordered by frequency
        ringers_query = (self.db.query(RingingDB.ringer, func.count(RingingDB.ringer).label('count'))
                        .filter(RingingDB.ringer.isnot(None))
                        .filter(RingingDB.ringer != '')
                        .group_by(RingingDB.ringer)
                        .order_by(func.count(RingingDB.ringer).desc())
                        .all())
        ringers = [result[0] for result in ringers_query]
        
        return {
            "places": places,
            "species": species,
            "habitats": habitats,
            "melders": melders,
            "field_fruits": field_fruits,
            "ringers": ringers,
        }
    
    @cached(ttl=600)  # Cache for 10 minutes
    def get_species_name_list(self) -> List[str]:
        """Get list of all species names ordered by frequency of sightings"""
        species_query = (self.db.query(SightingDB.species, func.count(SightingDB.species).label('count'))
                        .filter(SightingDB.species.isnot(None))
                        .filter(SightingDB.species != '')
                        .group_by(SightingDB.species)
                        .order_by(func.count(SightingDB.species).desc())
                        .all())
        
        return [result[0] for result in species_query]
    
    @cached(ttl=600)  # Cache for 10 minutes
    def get_place_name_list(self) -> List[str]:
        """Get list of all place names ordered by frequency of sightings"""
        places_query = (self.db.query(SightingDB.place, func.count(SightingDB.place).label('count'))
                       .filter(SightingDB.place.isnot(None))
                       .filter(SightingDB.place != '')
                       .group_by(SightingDB.place)
                       .order_by(func.count(SightingDB.place).desc())
                       .all())
        
        return [result[0] for result in places_query]
    
    @cached(ttl=600)  # Cache for 10 minutes
    def get_ringer_list(self) -> List[str]:
        """Get list of all unique ringers"""
        return self.ringing_repository.get_ringer_list()
    
    @cached(ttl=600)  # Cache for 10 minutes
    def get_habitat_list(self) -> List[str]:
        """Get list of all unique habitats ordered by frequency"""
        habitats_query = (self.db.query(SightingDB.habitat, func.count(SightingDB.habitat).label('count'))
                         .filter(SightingDB.habitat.isnot(None))
                         .filter(SightingDB.habitat != '')
                         .group_by(SightingDB.habitat)
                         .order_by(func.count(SightingDB.habitat).desc())
                         .all())
        
        return [result[0] for result in habitats_query]
    
    @cached(ttl=600)  # Cache for 10 minutes
    def get_melder_list(self) -> List[str]:
        """Get list of all unique melders ordered by frequency"""
        melders_query = (self.db.query(SightingDB.melder, func.count(SightingDB.melder).label('count'))
                        .filter(SightingDB.melder.isnot(None))
                        .filter(SightingDB.melder != '')
                        .group_by(SightingDB.melder)
                        .order_by(func.count(SightingDB.melder).desc())
                        .all())
        
        return [result[0] for result in melders_query]
    
    @cached(ttl=600)  # Cache for 10 minutes
    def get_field_fruit_list(self) -> List[str]:
        """Get list of all unique field fruits ordered by frequency"""
        field_fruits_query = (self.db.query(SightingDB.field_fruit, func.count(SightingDB.field_fruit).label('count'))
                             .filter(SightingDB.field_fruit.isnot(None))
                             .filter(SightingDB.field_fruit != '')
                             .group_by(SightingDB.field_fruit)
                             .order_by(func.count(SightingDB.field_fruit).desc())
                             .all())
        
        return [result[0] for result in field_fruits_query]