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
    check_connection,
)
from .models import Sighting, Ringing
from .family_models import BirdRelationship, RelationshipType
from .repositories import SightingRepository, RingingRepository
from .family_repository import FamilyRepository

__all__ = [
    # Connection utilities
    "engine",
    "SessionLocal",
    "Base",
    "get_db",
    "get_db_session",
    "create_tables",
    "drop_tables",
    "check_connection",
    # Models
    "Sighting",
    "Ringing",
    "BirdRelationship",
    "RelationshipType",
    # Repositories
    "SightingRepository",
    "RingingRepository",
    "FamilyRepository",
]
