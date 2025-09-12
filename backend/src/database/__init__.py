"""
Database package for Vogelring application
"""
from .connection import (
    engine,
    SessionLocal,
    Base,
    get_db,
    get_db_session,
    create_tables,
    drop_tables,
    check_connection
)
from .models import Sighting, Ringing, FamilyTreeEntry
from .repositories import SightingRepository, RingingRepository, FamilyTreeRepository
from .utils import DatabaseUtils, create_optimized_indexes

__all__ = [
    # Connection utilities
    'engine',
    'SessionLocal', 
    'Base',
    'get_db',
    'get_db_session',
    'create_tables',
    'drop_tables',
    'check_connection',
    # Models
    'Sighting',
    'Ringing', 
    'FamilyTreeEntry',
    # Repositories
    'SightingRepository',
    'RingingRepository',
    'FamilyTreeRepository',
    # Utils
    'DatabaseUtils',
    'create_optimized_indexes'
]