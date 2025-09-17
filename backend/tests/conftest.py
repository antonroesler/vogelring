"""
Test configuration and fixtures
"""

import pytest
import os
from datetime import date, datetime
from uuid import uuid4
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

# Set testing environment variable
os.environ["TESTING"] = "true"

from src.database.connection import Base, get_db
from src.database.models import Sighting, Ringing
from src.main import app


# Test database URL - use in-memory SQLite for tests
TEST_DATABASE_URL = "sqlite:///:memory:"

# Create test engine with special configuration for SQLite
test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="function")
def test_db():
    """Create a test database session"""
    # Create tables
    Base.metadata.create_all(bind=test_engine)

    # Create session
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Drop tables after test
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(scope="function")
def client(test_db):
    """Create a test client with test database"""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    # Clean up
    app.dependency_overrides.clear()


@pytest.fixture
def sample_ringing_data():
    """Sample ringing data for testing"""
    return {
        "ring": "TEST001",
        "ring_scheme": "EURING",
        "species": "Larus ridibundus",
        "date": date(2023, 5, 15),
        "place": "Test Location",
        "lat": 52.5200,
        "lon": 13.4050,
        "ringer": "Test Ringer",
        "sex": 1,
        "age": 2,
        "status": "alive",
    }


@pytest.fixture
def sample_sighting_data():
    """Sample sighting data for testing"""
    return {
        "excel_id": 1001,
        "comment": "Test sighting comment",
        "species": "Larus ridibundus",
        "ring": "TEST001",
        "reading": "TEST001",
        "age": "adult",
        "sex": "M",
        "date": date(2023, 6, 20),
        "large_group_size": 5,
        "small_group_size": 2,
        "partner": "TEST002",
        "breed_size": 1,
        "family_size": 3,
        "pair": "yes",
        "status": "alive",
        "melder": "Test Observer",
        "melded": True,
        "place": "Test Observation Site",
        "area": "Test Area",
        "lat": 52.5300,
        "lon": 13.4100,
        "is_exact_location": True,
        "habitat": "wetland",
        "field_fruit": "none",
    }


@pytest.fixture
def sample_family_tree_data():
    """Sample family tree data for testing"""
    return {
        "ring": "TEST001",
        "partners": [{"ring": "TEST002", "year": 2023, "confirmed": True}],
        "children": [{"ring": "TEST003", "year": 2023, "confirmed": True}],
        "parents": [],
    }


@pytest.fixture
def create_test_ringing(test_db, sample_ringing_data):
    """Create a test ringing record in the database"""
    ringing = Ringing(id=uuid4(), **sample_ringing_data)
    test_db.add(ringing)
    test_db.commit()
    test_db.refresh(ringing)
    return ringing


@pytest.fixture
def create_test_sighting(test_db, sample_sighting_data):
    """Create a test sighting record in the database"""
    sighting = Sighting(id=uuid4(), **sample_sighting_data)
    test_db.add(sighting)
    test_db.commit()
    test_db.refresh(sighting)
    return sighting


@pytest.fixture
def multiple_test_sightings(test_db):
    """Create multiple test sightings for testing pagination and filtering"""
    from datetime import timedelta

    today = date.today()

    sightings_data = [
        {
            "excel_id": 1001,
            "species": "Larus ridibundus",
            "ring": "TEST001",
            "date": today - timedelta(days=5),
            "place": "Location A",
            "lat": 52.5200,
            "lon": 13.4050,
        },
        {
            "excel_id": 1002,
            "species": "Larus canus",
            "ring": "TEST002",
            "date": today - timedelta(days=10),
            "place": "Location B",
            "lat": 52.5300,
            "lon": 13.4100,
        },
        {
            "excel_id": 1003,
            "species": "Larus ridibundus",
            "ring": "TEST003",
            "date": today - timedelta(days=15),
            "place": "Location A",
            "lat": 52.5250,
            "lon": 13.4075,
        },
    ]

    sightings = []
    for data in sightings_data:
        sighting = Sighting(id=uuid4(), **data)
        test_db.add(sighting)
        sightings.append(sighting)

    test_db.commit()
    for sighting in sightings:
        test_db.refresh(sighting)

    return sightings


@pytest.fixture
def multiple_test_ringings(test_db):
    """Create multiple test ringings for testing pagination and filtering"""
    from datetime import timedelta

    today = date.today()

    ringings_data = [
        {
            "ring": "TEST001",
            "ring_scheme": "EURING",
            "species": "Larus ridibundus",
            "date": today - timedelta(days=5),
            "place": "Location A",
            "lat": 52.5200,
            "lon": 13.4050,
            "ringer": "Ringer A",
            "sex": 1,
            "age": 2,
        },
        {
            "ring": "TEST002",
            "ring_scheme": "EURING",
            "species": "Larus canus",
            "date": today - timedelta(days=10),
            "place": "Location B",
            "lat": 52.5300,
            "lon": 13.4100,
            "ringer": "Ringer B",
            "sex": 2,
            "age": 1,
        },
        {
            "ring": "TEST003",
            "ring_scheme": "EURING",
            "species": "Larus ridibundus",
            "date": today - timedelta(days=15),
            "place": "Location A",
            "lat": 52.5250,
            "lon": 13.4075,
            "ringer": "Ringer A",
            "sex": 1,
            "age": 3,
        },
    ]

    ringings = []
    for data in ringings_data:
        ringing = Ringing(id=uuid4(), **data)
        test_db.add(ringing)
        ringings.append(ringing)

    test_db.commit()
    for ringing in ringings:
        test_db.refresh(ringing)

    return ringings
