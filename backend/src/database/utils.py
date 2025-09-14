"""
Database utility functions and query builders
"""
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import date, datetime
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, text
from sqlalchemy.exc import SQLAlchemyError

from .models import Sighting, Ringing, FamilyTreeEntry
from .repositories import SightingRepository, RingingRepository, FamilyTreeRepository

logger = logging.getLogger(__name__)


class DatabaseUtils:
    """Utility class for common database operations"""
    
    def __init__(self, db: Session):
        self.db = db
        self.sighting_repo = SightingRepository(db)
        self.ringing_repo = RingingRepository(db)
        self.family_repo = FamilyTreeRepository(db)
    
    def get_combined_species_list(self) -> List[str]:
        """Get combined unique species list from both sightings and ringings"""
        try:
            sighting_species = set(self.sighting_repo.get_species_list())
            ringing_species = set(self.ringing_repo.get_species_list())
            
            combined = sighting_species.union(ringing_species)
            return sorted(list(combined))
        except Exception as e:
            logger.error(f"Error getting combined species list: {e}")
            return []
    
    def get_combined_place_list(self) -> List[str]:
        """Get combined unique place list from both sightings and ringings"""
        try:
            # Get places from sightings
            sighting_places = (self.db.query(Sighting.place)
                             .filter(Sighting.place.isnot(None))
                             .distinct()
                             .all())
            
            # Get places from ringings
            ringing_places = (self.db.query(Ringing.place)
                            .filter(Ringing.place.isnot(None))
                            .distinct()
                            .all())
            
            sighting_places_set = {place[0] for place in sighting_places if place[0]}
            ringing_places_set = {place[0] for place in ringing_places if place[0]}
            
            combined = sighting_places_set.union(ringing_places_set)
            return sorted(list(combined))
        except Exception as e:
            logger.error(f"Error getting combined place list: {e}")
            return []
    
    def get_bird_summary(self, ring: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive summary for a specific bird"""
        try:
            # Get ringing data
            ringing = self.ringing_repo.get_by_ring(ring)
            
            # Get all sightings
            sightings = self.sighting_repo.get_by_ring(ring)
            
            # Get family tree data
            family_tree = self.family_repo.get_by_ring(ring)
            
            if not ringing and not sightings:
                return None
            
            # Calculate summary statistics
            sighting_count = len(sightings)
            first_seen = min([s.date for s in sightings if s.date]) if sightings else None
            last_seen = max([s.date for s in sightings if s.date]) if sightings else None
            
            # Get unique places where bird was seen
            places = list(set([s.place for s in sightings if s.place]))
            
            # Get species identifications (in case of misidentifications)
            species_counts = {}
            for sighting in sightings:
                if sighting.species:
                    species_counts[sighting.species] = species_counts.get(sighting.species, 0) + 1
            
            return {
                'ring': ring,
                'ringing_data': ringing,
                'sighting_count': sighting_count,
                'first_seen': first_seen,
                'last_seen': last_seen,
                'places_seen': places,
                'species_identifications': species_counts,
                'family_tree': family_tree,
                'recent_sightings': sightings[:10] if sightings else []  # Last 10 sightings
            }
        except Exception as e:
            logger.error(f"Error getting bird summary for ring {ring}: {e}")
            return None
    
    def get_autocomplete_data(self, field: str, query: str, limit: int = 10) -> List[str]:
        """Get autocomplete suggestions from both sightings and ringings"""
        try:
            suggestions = set()
            
            # Get suggestions from sightings
            if hasattr(Sighting, field):
                sighting_suggestions = self.sighting_repo.get_autocomplete_suggestions(field, query, limit)
                suggestions.update(sighting_suggestions)
            
            # Get suggestions from ringings
            if hasattr(Ringing, field):
                ringing_suggestions = self.ringing_repo.get_autocomplete_suggestions(field, query, limit)
                suggestions.update(ringing_suggestions)
            
            # Sort and limit results
            sorted_suggestions = sorted(list(suggestions))
            return sorted_suggestions[:limit]
        except Exception as e:
            logger.error(f"Error getting autocomplete data for field {field}: {e}")
            return []
    
    def get_dashboard_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics for dashboard"""
        try:
            sighting_stats = self.sighting_repo.get_statistics()
            ringing_stats = self.ringing_repo.get_statistics()
            
            # Combined statistics
            total_birds = len(set(
                self.sighting_repo.get_ring_list() + 
                [r.ring for r in self.ringing_repo.get_all()]
            ))
            
            # Recent activity
            recent_sightings = self.sighting_repo.get_all(limit=5)
            recent_ringings = self.ringing_repo.get_all(limit=5)
            
            return {
                'sightings': sighting_stats,
                'ringings': ringing_stats,
                'total_unique_birds': total_birds,
                'recent_sightings': recent_sightings,
                'recent_ringings': recent_ringings
            }
        except Exception as e:
            logger.error(f"Error getting dashboard statistics: {e}")
            return {}
    
    def search_birds(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search for birds across all data"""
        try:
            results = []
            
            # Search by ring
            if query:
                # Search sightings by ring
                sightings = (self.db.query(Sighting)
                           .filter(Sighting.ring.ilike(f"%{query}%"))
                           .limit(limit)
                           .all())
                
                # Search ringings by ring
                ringings = (self.db.query(Ringing)
                          .filter(Ringing.ring.ilike(f"%{query}%"))
                          .limit(limit)
                          .all())
                
                # Combine and deduplicate by ring
                rings_found = set()
                
                for sighting in sightings:
                    if sighting.ring and sighting.ring not in rings_found:
                        rings_found.add(sighting.ring)
                        bird_summary = self.get_bird_summary(sighting.ring)
                        if bird_summary:
                            results.append(bird_summary)
                
                for ringing in ringings:
                    if ringing.ring not in rings_found:
                        rings_found.add(ringing.ring)
                        bird_summary = self.get_bird_summary(ringing.ring)
                        if bird_summary:
                            results.append(bird_summary)
            
            return results[:limit]
        except Exception as e:
            logger.error(f"Error searching birds with query '{query}': {e}")
            return []
    
    def get_seasonal_analysis(self, species: Optional[str] = None, 
                            year: Optional[int] = None) -> Dict[str, Any]:
        """Get seasonal analysis data"""
        try:
            query = self.db.query(Sighting).filter(Sighting.date.isnot(None))
            
            if species:
                query = query.filter(Sighting.species == species)
            
            if year:
                query = query.filter(func.extract('year', Sighting.date) == year)
            
            sightings = query.all()
            
            # Group by month
            monthly_counts = {}
            for sighting in sightings:
                if sighting.date:
                    month = sighting.date.month
                    monthly_counts[month] = monthly_counts.get(month, 0) + 1
            
            # Group by season
            seasonal_counts = {
                'spring': sum(monthly_counts.get(month, 0) for month in [3, 4, 5]),
                'summer': sum(monthly_counts.get(month, 0) for month in [6, 7, 8]),
                'autumn': sum(monthly_counts.get(month, 0) for month in [9, 10, 11]),
                'winter': sum(monthly_counts.get(month, 0) for month in [12, 1, 2])
            }
            
            return {
                'monthly_counts': monthly_counts,
                'seasonal_counts': seasonal_counts,
                'total_sightings': len(sightings),
                'species': species,
                'year': year
            }
        except Exception as e:
            logger.error(f"Error getting seasonal analysis: {e}")
            return {}
    
    def validate_data_integrity(self) -> Dict[str, Any]:
        """Validate data integrity across tables"""
        try:
            issues = []
            
            # Check for sightings with rings that don't exist in ringings
            sightings_with_rings = (self.db.query(Sighting.ring)
                                  .filter(Sighting.ring.isnot(None))
                                  .distinct()
                                  .all())
            
            ringing_rings = set(r.ring for r in self.ringing_repo.get_all())
            
            orphaned_rings = []
            for sighting_ring in sightings_with_rings:
                ring = sighting_ring[0]
                if ring not in ringing_rings:
                    orphaned_rings.append(ring)
            
            if orphaned_rings:
                issues.append({
                    'type': 'orphaned_sighting_rings',
                    'count': len(orphaned_rings),
                    'description': 'Sightings with rings that have no corresponding ringing data',
                    'examples': orphaned_rings[:10]
                })
            
            # Check for duplicate rings in ringings (should not happen due to unique constraint)
            duplicate_rings = (self.db.query(Ringing.ring, func.count(Ringing.ring))
                             .group_by(Ringing.ring)
                             .having(func.count(Ringing.ring) > 1)
                             .all())
            
            if duplicate_rings:
                issues.append({
                    'type': 'duplicate_ringing_rings',
                    'count': len(duplicate_rings),
                    'description': 'Duplicate ring numbers in ringing data',
                    'examples': [ring[0] for ring in duplicate_rings[:10]]
                })
            
            # Check for family tree entries with non-existent rings
            family_entries = self.family_repo.get_all()
            all_rings = ringing_rings.union(set(self.sighting_repo.get_ring_list()))
            
            invalid_family_refs = []
            for entry in family_entries:
                # Check if main ring exists
                if entry.ring not in all_rings:
                    invalid_family_refs.append(f"Main ring: {entry.ring}")
                
                # Check partner rings
                if entry.partners:
                    for partner in entry.partners:
                        if partner.get('ring') and partner['ring'] not in all_rings:
                            invalid_family_refs.append(f"Partner ring: {partner['ring']}")
                
                # Check children rings
                if entry.children:
                    for child in entry.children:
                        if child.get('ring') and child['ring'] not in all_rings:
                            invalid_family_refs.append(f"Child ring: {child['ring']}")
            
            if invalid_family_refs:
                issues.append({
                    'type': 'invalid_family_references',
                    'count': len(invalid_family_refs),
                    'description': 'Family tree references to non-existent rings',
                    'examples': invalid_family_refs[:10]
                })
            
            return {
                'total_issues': len(issues),
                'issues': issues,
                'validation_timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Error validating data integrity: {e}")
            return {'error': str(e)}


def create_optimized_indexes(db: Session):
    """Create additional optimized indexes for better performance"""
    try:
        # Additional composite indexes for common query patterns
        indexes = [
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_ring_species ON sightings(ring, species) WHERE ring IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_place_species ON sightings(place, species) WHERE place IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_date_species ON sightings(date, species) WHERE date IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ringings_species_place ON ringings(species, place)",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ringings_date_species ON ringings(date, species)",
            # Partial indexes for non-null values
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_reading_partial ON sightings(reading) WHERE reading IS NOT NULL",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_partner_partial ON sightings(partner) WHERE partner IS NOT NULL",
            # Text search indexes
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_sightings_comment_gin ON sightings USING gin(to_tsvector('english', comment)) WHERE comment IS NOT NULL",
        ]
        
        for index_sql in indexes:
            try:
                db.execute(text(index_sql))
                logger.info(f"Created index: {index_sql}")
            except SQLAlchemyError as e:
                logger.warning(f"Failed to create index: {index_sql}, Error: {e}")
        
        db.commit()
        logger.info("Finished creating optimized indexes")
        
    except Exception as e:
        logger.error(f"Error creating optimized indexes: {e}")
        db.rollback()
        raise