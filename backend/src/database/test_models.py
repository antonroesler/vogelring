"""
Simple test script to verify database models and repositories
"""

import os
import sys
from datetime import date
from decimal import Decimal

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from database import (
    create_tables,
    get_db_session,
    check_connection,
    SightingRepository,
    RingingRepository,
    FamilyTreeRepository,
    DatabaseUtils,
)


def test_database_connection():
    """Test database connection"""
    print("Testing database connection...")
    if check_connection():
        print("✓ Database connection successful")
        return True
    else:
        print("✗ Database connection failed")
        return False


def test_create_tables():
    """Test table creation"""
    print("Testing table creation...")
    try:
        create_tables()
        print("✓ Tables created successfully")
        return True
    except Exception as e:
        print(f"✗ Table creation failed: {e}")
        return False


def test_repositories():
    """Test repository operations"""
    print("Testing repository operations...")

    try:
        with get_db_session() as db:
            # Test repositories
            sighting_repo = SightingRepository(db)
            ringing_repo = RingingRepository(db)
            family_repo = FamilyTreeRepository(db)

            # Test creating a ringing
            test_ringing = ringing_repo.create(
                ring="TEST001",
                ring_scheme="EURING",
                species="Larus ridibundus",
                date=date(2024, 1, 15),
                place="Test Location",
                lat=Decimal("52.123456"),
                lon=Decimal("4.654321"),
                ringer="Test Ringer",
                sex=1,
                age=2,
                status="BV",
            )
            print(f"✓ Created test ringing: {test_ringing.ring}")

            # Test creating a sighting
            test_sighting = sighting_repo.create(
                species="Larus ridibundus",
                ring="TEST001",
                date=date(2024, 2, 1),
                place="Test Location",
                lat=Decimal("52.123456"),
                lon=Decimal("4.654321"),
                sex="M",
                age="ad",
                comment="Test sighting",
            )
            print(f"✓ Created test sighting: {test_sighting.id}")

            # Test getting enriched sightings
            enriched_sightings = sighting_repo.get_enriched_sightings(limit=1)
            if enriched_sightings:
                print("✓ Retrieved enriched sighting with ringing data")

            # Test autocomplete
            species_suggestions = sighting_repo.get_autocomplete_suggestions(
                "species", "Larus", 5
            )
            print(
                f"✓ Species autocomplete returned {len(species_suggestions)} suggestions"
            )

            # Test statistics
            stats = sighting_repo.get_statistics()
            print(
                f"✓ Statistics: {stats['total_sightings']} sightings, {stats['unique_species']} species"
            )

            # Test family tree
            family_entry = family_repo.upsert_family_entry(
                ring="TEST001",
                partners=[{"ring": "TEST002", "year": 2024}],
                children=[{"ring": "TEST003", "year": 2024}],
            )
            print(f"✓ Created family tree entry for: {family_entry.ring}")

            # Test database utils
            db_utils = DatabaseUtils(db)
            combined_species = db_utils.get_combined_species_list()
            print(f"✓ Combined species list has {len(combined_species)} species")

            bird_summary = db_utils.get_bird_summary("TEST001")
            if bird_summary:
                print(
                    f"✓ Bird summary for TEST001: {bird_summary['sighting_count']} sightings"
                )

            # Clean up test data
            sighting_repo.delete(test_sighting.id)
            ringing_repo.delete(test_ringing.id)
            family_repo.delete(family_entry.id)
            print("✓ Cleaned up test data")

        return True

    except Exception as e:
        print(f"✗ Repository test failed: {e}")
        return False


def main():
    """Run all tests"""
    print("=== Database Models and Repositories Test ===\n")

    tests = [test_database_connection, test_create_tables, test_repositories]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"=== Test Results: {passed}/{total} tests passed ===")

    if passed == total:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed!")
        return 1


if __name__ == "__main__":
    exit(main())
