"""
Database setup and teardown utilities for testing
"""
import pytest
import tempfile
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.connection import Base
from src.database.models import Sighting, Ringing, FamilyTreeEntry


class DatabaseTestUtils:
    """Utilities for database testing setup and teardown"""
    
    @staticmethod
    def create_test_engine(database_url=None):
        """Create a test database engine"""
        if database_url is None:
            database_url = "sqlite:///:memory:"
        
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False} if "sqlite" in database_url else {},
            poolclass=StaticPool if "sqlite" in database_url else None,
            echo=False  # Set to True for SQL debugging
        )
        return engine
    
    @staticmethod
    def create_test_session(engine):
        """Create a test database session"""
        TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        return TestingSessionLocal()
    
    @staticmethod
    def setup_test_database(engine):
        """Set up test database with all tables"""
        Base.metadata.create_all(bind=engine)
    
    @staticmethod
    def teardown_test_database(engine):
        """Tear down test database"""
        Base.metadata.drop_all(bind=engine)
    
    @staticmethod
    def truncate_all_tables(session):
        """Truncate all tables in the test database"""
        try:
            # For SQLite, we need to delete from tables in the right order
            session.execute(text("DELETE FROM sightings"))
            session.execute(text("DELETE FROM family_tree_entries"))
            session.execute(text("DELETE FROM ringings"))
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
    
    @staticmethod
    def get_table_counts(session):
        """Get counts of all tables"""
        return {
            'sightings': session.query(Sighting).count(),
            'ringings': session.query(Ringing).count(),
            'family_tree_entries': session.query(FamilyTreeEntry).count()
        }
    
    @staticmethod
    def verify_database_integrity(session):
        """Verify database integrity constraints"""
        integrity_issues = []
        
        # Check for duplicate ring numbers in ringings
        duplicate_rings = session.execute(text("""
            SELECT ring, COUNT(*) as count 
            FROM ringings 
            GROUP BY ring 
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if duplicate_rings:
            integrity_issues.append(f"Duplicate rings in ringings table: {duplicate_rings}")
        
        # Check for duplicate ring numbers in family_tree_entries
        duplicate_family_rings = session.execute(text("""
            SELECT ring, COUNT(*) as count 
            FROM family_tree_entries 
            GROUP BY ring 
            HAVING COUNT(*) > 1
        """)).fetchall()
        
        if duplicate_family_rings:
            integrity_issues.append(f"Duplicate rings in family_tree_entries table: {duplicate_family_rings}")
        
        # Check for sightings with rings that don't exist in ringings
        orphaned_sightings = session.execute(text("""
            SELECT COUNT(*) as count
            FROM sightings s
            LEFT JOIN ringings r ON s.ring = r.ring
            WHERE s.ring IS NOT NULL AND r.ring IS NULL
        """)).fetchone()
        
        if orphaned_sightings and orphaned_sightings[0] > 0:
            integrity_issues.append(f"Orphaned sightings (ring not in ringings): {orphaned_sightings[0]}")
        
        return {
            'valid': len(integrity_issues) == 0,
            'issues': integrity_issues
        }
    
    @staticmethod
    def create_sample_data(session):
        """Create sample data for testing"""
        from uuid import uuid4
        from datetime import date
        
        # Create sample ringings
        ringings = [
            Ringing(
                id=uuid4(),
                ring="SAMPLE001",
                ring_scheme="EURING",
                species="Larus ridibundus",
                date=date(2023, 5, 15),
                place="Sample Location A",
                lat=52.5200,
                lon=13.4050,
                ringer="Sample Ringer A",
                sex=1,
                age=2
            ),
            Ringing(
                id=uuid4(),
                ring="SAMPLE002",
                ring_scheme="EURING",
                species="Larus canus",
                date=date(2023, 6, 20),
                place="Sample Location B",
                lat=52.5300,
                lon=13.4100,
                ringer="Sample Ringer B",
                sex=2,
                age=1
            )
        ]
        
        # Create sample sightings
        sightings = [
            Sighting(
                id=uuid4(),
                excel_id=2001,
                species="Larus ridibundus",
                ring="SAMPLE001",
                date=date(2023, 7, 10),
                place="Sample Observation Site A",
                lat=52.5250,
                lon=13.4075,
                melder="Sample Observer A"
            ),
            Sighting(
                id=uuid4(),
                excel_id=2002,
                species="Larus canus",
                ring="SAMPLE002",
                date=date(2023, 8, 15),
                place="Sample Observation Site B",
                lat=52.5350,
                lon=13.4125,
                melder="Sample Observer B"
            ),
            Sighting(
                id=uuid4(),
                excel_id=2003,
                species="Larus ridibundus",
                date=date(2023, 9, 20),
                place="Sample Observation Site C",
                lat=52.5400,
                lon=13.4150,
                melder="Sample Observer C"
            )
        ]
        
        # Create sample family tree entries
        family_entries = [
            FamilyTreeEntry(
                id=uuid4(),
                ring="SAMPLE001",
                partners=[{"ring": "SAMPLE002", "year": 2023, "confirmed": True}],
                children=[{"ring": "SAMPLE003", "year": 2023, "confirmed": True}],
                parents=[]
            )
        ]
        
        # Add all data to session
        for ringing in ringings:
            session.add(ringing)
        for sighting in sightings:
            session.add(sighting)
        for entry in family_entries:
            session.add(entry)
        
        session.commit()
        
        return {
            'ringings': len(ringings),
            'sightings': len(sightings),
            'family_entries': len(family_entries)
        }


class TestDatabaseSetupUtils:
    """Test the database setup utilities"""
    
    def test_create_test_engine(self):
        """Test creating a test database engine"""
        engine = DatabaseTestUtils.create_test_engine()
        assert engine is not None
        
        # Test with custom URL
        engine_custom = DatabaseTestUtils.create_test_engine("sqlite:///test.db")
        assert engine_custom is not None
    
    def test_setup_and_teardown_database(self):
        """Test database setup and teardown"""
        engine = DatabaseTestUtils.create_test_engine()
        
        # Setup database
        DatabaseTestUtils.setup_test_database(engine)
        
        # Verify tables exist
        from sqlalchemy import inspect
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        
        assert 'sightings' in table_names
        assert 'ringings' in table_names
        assert 'family_tree_entries' in table_names
        
        # Teardown database
        DatabaseTestUtils.teardown_test_database(engine)
        
        # Verify tables are gone
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        assert len(table_names) == 0
    
    def test_create_and_use_session(self):
        """Test creating and using a database session"""
        engine = DatabaseTestUtils.create_test_engine()
        DatabaseTestUtils.setup_test_database(engine)
        
        session = DatabaseTestUtils.create_test_session(engine)
        
        # Test basic query
        count = session.query(Sighting).count()
        assert count == 0
        
        session.close()
        DatabaseTestUtils.teardown_test_database(engine)
    
    def test_truncate_all_tables(self):
        """Test truncating all tables"""
        engine = DatabaseTestUtils.create_test_engine()
        DatabaseTestUtils.setup_test_database(engine)
        session = DatabaseTestUtils.create_test_session(engine)
        
        # Create sample data
        sample_counts = DatabaseTestUtils.create_sample_data(session)
        
        # Verify data was created
        counts_before = DatabaseTestUtils.get_table_counts(session)
        assert counts_before['sightings'] > 0
        assert counts_before['ringings'] > 0
        
        # Truncate tables
        DatabaseTestUtils.truncate_all_tables(session)
        
        # Verify tables are empty
        counts_after = DatabaseTestUtils.get_table_counts(session)
        assert counts_after['sightings'] == 0
        assert counts_after['ringings'] == 0
        assert counts_after['family_tree_entries'] == 0
        
        session.close()
        DatabaseTestUtils.teardown_test_database(engine)
    
    def test_verify_database_integrity(self):
        """Test database integrity verification"""
        engine = DatabaseTestUtils.create_test_engine()
        DatabaseTestUtils.setup_test_database(engine)
        session = DatabaseTestUtils.create_test_session(engine)
        
        # Create sample data
        DatabaseTestUtils.create_sample_data(session)
        
        # Verify integrity
        integrity_result = DatabaseTestUtils.verify_database_integrity(session)
        assert integrity_result['valid'] is True
        assert len(integrity_result['issues']) == 0
        
        session.close()
        DatabaseTestUtils.teardown_test_database(engine)
    
    def test_get_table_counts(self):
        """Test getting table counts"""
        engine = DatabaseTestUtils.create_test_engine()
        DatabaseTestUtils.setup_test_database(engine)
        session = DatabaseTestUtils.create_test_session(engine)
        
        # Initially empty
        counts = DatabaseTestUtils.get_table_counts(session)
        assert counts['sightings'] == 0
        assert counts['ringings'] == 0
        assert counts['family_tree_entries'] == 0
        
        # Create sample data
        sample_counts = DatabaseTestUtils.create_sample_data(session)
        
        # Check counts match
        counts = DatabaseTestUtils.get_table_counts(session)
        assert counts['sightings'] == sample_counts['sightings']
        assert counts['ringings'] == sample_counts['ringings']
        assert counts['family_tree_entries'] == sample_counts['family_entries']
        
        session.close()
        DatabaseTestUtils.teardown_test_database(engine)
    
    def test_create_sample_data(self):
        """Test creating sample data"""
        engine = DatabaseTestUtils.create_test_engine()
        DatabaseTestUtils.setup_test_database(engine)
        session = DatabaseTestUtils.create_test_session(engine)
        
        # Create sample data
        sample_counts = DatabaseTestUtils.create_sample_data(session)
        
        # Verify data was created
        assert sample_counts['ringings'] > 0
        assert sample_counts['sightings'] > 0
        assert sample_counts['family_entries'] > 0
        
        # Verify actual counts in database
        actual_counts = DatabaseTestUtils.get_table_counts(session)
        assert actual_counts['ringings'] == sample_counts['ringings']
        assert actual_counts['sightings'] == sample_counts['sightings']
        assert actual_counts['family_tree_entries'] == sample_counts['family_entries']
        
        session.close()
        DatabaseTestUtils.teardown_test_database(engine)


class TestDatabasePerformanceUtils:
    """Test database performance utilities"""
    
    def test_bulk_insert_performance(self):
        """Test bulk insert performance"""
        engine = DatabaseTestUtils.create_test_engine()
        DatabaseTestUtils.setup_test_database(engine)
        session = DatabaseTestUtils.create_test_session(engine)
        
        # Create a larger dataset for performance testing
        from uuid import uuid4
        from datetime import date
        
        bulk_sightings = []
        for i in range(100):
            bulk_sightings.append(Sighting(
                id=uuid4(),
                excel_id=3000 + i,
                species=f"Test Species {i % 5}",
                ring=f"BULK{i:03d}",
                date=date(2023, 5, 15),
                place=f"Test Location {i % 10}",
                melder=f"Test Observer {i % 3}"
            ))
        
        # Bulk insert
        session.add_all(bulk_sightings)
        session.commit()
        
        # Verify all records were inserted
        count = session.query(Sighting).count()
        assert count == 100
        
        session.close()
        DatabaseTestUtils.teardown_test_database(engine)
    
    def test_query_performance_with_indexes(self):
        """Test query performance with indexed columns"""
        engine = DatabaseTestUtils.create_test_engine()
        DatabaseTestUtils.setup_test_database(engine)
        session = DatabaseTestUtils.create_test_session(engine)
        
        # Create sample data
        DatabaseTestUtils.create_sample_data(session)
        
        # Test indexed queries (these should be fast)
        # Query by ring (indexed)
        result = session.query(Sighting).filter(Sighting.ring == "SAMPLE001").first()
        assert result is not None
        
        # Query by species (indexed)
        results = session.query(Sighting).filter(Sighting.species == "Larus ridibundus").all()
        assert len(results) > 0
        
        # Query by place (indexed)
        results = session.query(Sighting).filter(Sighting.place.like("%Sample%")).all()
        assert len(results) > 0
        
        session.close()
        DatabaseTestUtils.teardown_test_database(engine)


# Pytest fixtures for easy use in other test files
@pytest.fixture
def db_utils():
    """Provide database utilities as a fixture"""
    return DatabaseTestUtils


@pytest.fixture
def test_engine():
    """Provide a test database engine"""
    return DatabaseTestUtils.create_test_engine()


@pytest.fixture
def test_session_with_data(test_engine):
    """Provide a test session with sample data"""
    DatabaseTestUtils.setup_test_database(test_engine)
    session = DatabaseTestUtils.create_test_session(test_engine)
    DatabaseTestUtils.create_sample_data(session)
    
    yield session
    
    session.close()
    DatabaseTestUtils.teardown_test_database(test_engine)