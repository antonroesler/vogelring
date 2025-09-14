"""
Database connection and utilities for migration
"""
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager
from typing import Generator
import sys
import os

# Import SQLAlchemy models directly
from sqlalchemy import Column, String, Integer, Date, DECIMAL, Boolean, Text, TIMESTAMP, JSON
from sqlalchemy.dialects.postgresql import UUID as PostgresUUID
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
from uuid import uuid4

# Create Base for models
Base = declarative_base()

# Define database models for migration
class RingingDB(Base):
    __tablename__ = 'ringings'
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    ring = Column(String, unique=True, nullable=False)
    ring_scheme = Column(String)
    species = Column(String)
    date = Column(Date)
    place = Column(String)
    lat = Column(DECIMAL(10, 8))
    lon = Column(DECIMAL(11, 8))
    ringer = Column(String)
    sex = Column(Integer)
    age = Column(Integer)
    status = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class SightingDB(Base):
    __tablename__ = 'sightings'
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    excel_id = Column(Integer, unique=True)
    comment = Column(Text)
    species = Column(String)
    ring = Column(String)
    reading = Column(String)
    age = Column(String)
    sex = Column(String)
    date = Column(Date)
    large_group_size = Column(Integer)
    small_group_size = Column(Integer)
    partner = Column(String)
    breed_size = Column(Integer)
    family_size = Column(Integer)
    pair = Column(String)
    status = Column(String)
    melder = Column(String)
    melded = Column(Boolean)
    place = Column(String)
    area = Column(String)
    lat = Column(DECIMAL(10, 8))
    lon = Column(DECIMAL(11, 8))
    is_exact_location = Column(Boolean, default=False)
    habitat = Column(String)
    field_fruit = Column(String)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

class FamilyTreeEntryDB(Base):
    __tablename__ = 'family_tree_entries'
    
    id = Column(PostgresUUID(as_uuid=True), primary_key=True, default=uuid4)
    ring = Column(String, unique=True, nullable=False)
    partners = Column(JSON)
    children = Column(JSON)
    parents = Column(JSON)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
from config import DATABASE_URL

logger = logging.getLogger(__name__)

# Create database engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def create_tables():
    """Create all database tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def test_connection():
    """Test database connection"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("Database connection successful")
            return True
    except SQLAlchemyError as e:
        logger.error(f"Database connection failed: {e}")
        return False


@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """Get database session with automatic cleanup"""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        raise
    finally:
        session.close()


def get_table_count(table_name: str) -> int:
    """Get count of records in a table"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            return result.scalar()
    except SQLAlchemyError as e:
        logger.error(f"Error getting count for table {table_name}: {e}")
        return 0


def truncate_table(table_name: str):
    """Truncate a table (for testing/cleanup)"""
    try:
        with engine.connect() as conn:
            conn.execute(text(f"TRUNCATE TABLE {table_name} CASCADE"))
            conn.commit()
        logger.info(f"Table {table_name} truncated successfully")
    except SQLAlchemyError as e:
        logger.error(f"Error truncating table {table_name}: {e}")
        raise


def validate_data_integrity():
    """Validate data integrity after migration"""
    issues = []
    
    try:
        with get_db_session() as session:
            # Check for duplicate rings in ringings table
            duplicate_rings = session.execute(text("""
                SELECT ring, COUNT(*) as count 
                FROM ringings 
                GROUP BY ring 
                HAVING COUNT(*) > 1
            """)).fetchall()
            
            if duplicate_rings:
                issues.append(f"Found {len(duplicate_rings)} duplicate rings in ringings table")
            
            # Check for invalid dates
            invalid_dates = session.execute(text("""
                SELECT COUNT(*) FROM ringings WHERE date IS NULL
            """)).scalar()
            
            if invalid_dates > 0:
                issues.append(f"Found {invalid_dates} ringings with NULL dates")
            
            # Check for invalid coordinates
            invalid_coords = session.execute(text("""
                SELECT COUNT(*) FROM ringings 
                WHERE lat IS NULL OR lon IS NULL 
                OR lat < -90 OR lat > 90 
                OR lon < -180 OR lon > 180
            """)).scalar()
            
            if invalid_coords > 0:
                issues.append(f"Found {invalid_coords} ringings with invalid coordinates")
            
            # Check family tree entries
            invalid_family_entries = session.execute(text("""
                SELECT COUNT(*) FROM family_tree_entries WHERE ring IS NULL
            """)).scalar()
            
            if invalid_family_entries > 0:
                issues.append(f"Found {invalid_family_entries} family tree entries with NULL rings")
    
    except SQLAlchemyError as e:
        issues.append(f"Error during data validation: {e}")
    
    return issues