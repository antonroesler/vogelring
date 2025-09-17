"""
Database integration tests for repository operations
"""

import pytest
from datetime import date
from uuid import uuid4

from src.database.repositories import (
    SightingRepository,
    RingingRepository,
    FamilyTreeRepository,
)
from src.database.models import Sighting, Ringing


class TestSightingRepository:
    """Test sighting repository operations"""

    def test_create_sighting(self, test_db, sample_sighting_data):
        """Test creating a sighting"""
        repo = SightingRepository(test_db)
        sighting = repo.create(**sample_sighting_data)

        assert sighting.id is not None
        assert sighting.species == "Larus ridibundus"
        assert sighting.ring == "TEST001"
        assert sighting.place == "Test Observation Site"

    def test_get_by_id(self, test_db, create_test_sighting):
        """Test getting sighting by ID"""
        repo = SightingRepository(test_db)
        sighting = repo.get_by_id(str(create_test_sighting.id))

        assert sighting is not None
        assert sighting.id == create_test_sighting.id
        assert sighting.species == create_test_sighting.species

    def test_get_by_id_not_found(self, test_db):
        """Test getting non-existent sighting"""
        repo = SightingRepository(test_db)
        sighting = repo.get_by_id(str(uuid4()))

        assert sighting is None

    def test_update_sighting(self, test_db, create_test_sighting):
        """Test updating a sighting"""
        repo = SightingRepository(test_db)
        updated_sighting = repo.update(
            str(create_test_sighting.id),
            species="Updated Species",
            comment="Updated comment",
        )

        assert updated_sighting is not None
        assert updated_sighting.species == "Updated Species"
        assert updated_sighting.comment == "Updated comment"
        # Original data should be preserved
        assert updated_sighting.ring == create_test_sighting.ring

    def test_delete_sighting(self, test_db, create_test_sighting):
        """Test deleting a sighting"""
        repo = SightingRepository(test_db)
        sighting_id = str(create_test_sighting.id)

        # Verify sighting exists
        assert repo.get_by_id(sighting_id) is not None

        # Delete sighting
        result = repo.delete(sighting_id)
        assert result is True

        # Verify sighting is deleted
        assert repo.get_by_id(sighting_id) is None

    def test_get_all_empty(self, test_db):
        """Test getting all sightings when database is empty"""
        repo = SightingRepository(test_db)
        sightings = repo.get_all()

        assert sightings == []

    def test_get_all_with_data(self, test_db, multiple_test_sightings):
        """Test getting all sightings with data"""
        repo = SightingRepository(test_db)
        sightings = repo.get_all()

        assert len(sightings) == 3
        # Should be ordered by date descending
        assert sightings[0].date >= sightings[1].date >= sightings[2].date

    def test_get_all_with_pagination(self, test_db, multiple_test_sightings):
        """Test getting sightings with pagination"""
        repo = SightingRepository(test_db)

        # Get first page
        page1 = repo.get_all(limit=2, offset=0)
        assert len(page1) == 2

        # Get second page
        page2 = repo.get_all(limit=2, offset=2)
        assert len(page2) == 1

        # Verify no overlap
        page1_ids = {s.id for s in page1}
        page2_ids = {s.id for s in page2}
        assert page1_ids.isdisjoint(page2_ids)

    def test_get_by_ring(self, test_db, multiple_test_sightings):
        """Test getting sightings by ring"""
        repo = SightingRepository(test_db)
        sightings = repo.get_by_ring("TEST001")

        assert len(sightings) == 1
        assert sightings[0].ring == "TEST001"

    def test_get_by_species(self, test_db, multiple_test_sightings):
        """Test getting sightings by species"""
        repo = SightingRepository(test_db)
        sightings = repo.get_by_species("Larus ridibundus")

        assert len(sightings) == 2
        for sighting in sightings:
            assert sighting.species == "Larus ridibundus"

    def test_get_by_place(self, test_db, multiple_test_sightings):
        """Test getting sightings by place"""
        repo = SightingRepository(test_db)
        sightings = repo.get_by_place("Location A")

        assert len(sightings) == 2
        for sighting in sightings:
            assert sighting.place == "Location A"

    def test_get_by_date_range(self, test_db, multiple_test_sightings):
        """Test getting sightings by date range"""
        from datetime import timedelta

        repo = SightingRepository(test_db)
        today = date.today()
        start_date = today - timedelta(days=30)
        end_date = today

        sightings = repo.get_by_date_range(start_date, end_date)

        assert len(sightings) >= 2  # Should find at least 2 sightings in this range
        for sighting in sightings:
            assert start_date <= sighting.date <= end_date

    def test_search_sightings_multiple_filters(self, test_db, multiple_test_sightings):
        """Test searching sightings with multiple filters"""
        repo = SightingRepository(test_db)

        # Filter by species and place
        sightings = repo.search_sightings(
            {"species": "Larus ridibundus", "place": "Location A"}
        )

        assert len(sightings) == 2
        for sighting in sightings:
            assert sighting.species == "Larus ridibundus"
            assert sighting.place == "Location A"

    def test_get_autocomplete_suggestions(self, test_db, multiple_test_sightings):
        """Test autocomplete suggestions"""
        repo = SightingRepository(test_db)

        # Test species suggestions
        suggestions = repo.get_autocomplete_suggestions("species", "Larus")
        assert len(suggestions) == 2
        assert "Larus ridibundus" in suggestions
        assert "Larus canus" in suggestions

        # Test place suggestions
        suggestions = repo.get_autocomplete_suggestions("place", "Location")
        assert len(suggestions) == 2
        assert "Location A" in suggestions
        assert "Location B" in suggestions

    def test_get_species_list(self, test_db, multiple_test_sightings):
        """Test getting species list"""
        repo = SightingRepository(test_db)
        species_list = repo.get_species_list()

        assert len(species_list) == 2
        assert "Larus ridibundus" in species_list
        assert "Larus canus" in species_list

    def test_get_statistics(self, test_db, multiple_test_sightings):
        """Test getting sighting statistics"""
        repo = SightingRepository(test_db)
        stats = repo.get_statistics()

        assert stats["total_sightings"] == 3
        assert stats["unique_species"] == 2
        assert stats["unique_places"] == 2
        assert stats["date_range"]["earliest"] is not None
        assert stats["date_range"]["latest"] is not None

    def test_get_enriched_sightings(
        self, test_db, create_test_sighting, create_test_ringing
    ):
        """Test getting enriched sightings with ringing data"""
        repo = SightingRepository(test_db)
        sightings = repo.get_enriched_sightings()

        assert len(sightings) == 1
        sighting = sightings[0]
        assert sighting.ring == "TEST001"
        # The ringing_data relationship should be loaded
        assert hasattr(sighting, "ringing_data")


class TestRingingRepository:
    """Test ringing repository operations"""

    def test_create_ringing(self, test_db, sample_ringing_data):
        """Test creating a ringing"""
        repo = RingingRepository(test_db)
        ringing = repo.create(**sample_ringing_data)

        assert ringing.id is not None
        assert ringing.ring == "TEST001"
        assert ringing.species == "Larus ridibundus"
        assert ringing.ringer == "Test Ringer"

    def test_get_by_ring(self, test_db, create_test_ringing):
        """Test getting ringing by ring number"""
        repo = RingingRepository(test_db)
        ringing = repo.get_by_ring(create_test_ringing.ring)

        assert ringing is not None
        assert ringing.ring == create_test_ringing.ring
        assert ringing.species == create_test_ringing.species

    def test_get_by_ring_not_found(self, test_db):
        """Test getting non-existent ringing"""
        repo = RingingRepository(test_db)
        ringing = repo.get_by_ring("NONEXISTENT")

        assert ringing is None

    def test_upsert_ringing_create(self, test_db, sample_ringing_data):
        """Test upserting a new ringing"""
        repo = RingingRepository(test_db)
        # Remove ring from sample data to avoid conflict
        data = sample_ringing_data.copy()
        data.pop("ring", None)
        ringing = repo.upsert_ringing("NEWTEST001", **data)

        assert ringing.ring == "NEWTEST001"
        assert ringing.species == sample_ringing_data["species"]

    def test_upsert_ringing_update(self, test_db, create_test_ringing):
        """Test upserting an existing ringing"""
        repo = RingingRepository(test_db)
        ring = create_test_ringing.ring

        updated_ringing = repo.upsert_ringing(
            ring, species="Updated Species", ringer="Updated Ringer"
        )

        assert updated_ringing.ring == ring
        assert updated_ringing.species == "Updated Species"
        assert updated_ringing.ringer == "Updated Ringer"
        # Should be the same record
        assert updated_ringing.id == create_test_ringing.id

    def test_get_by_species(self, test_db, multiple_test_ringings):
        """Test getting ringings by species"""
        repo = RingingRepository(test_db)
        ringings = repo.get_by_species("Larus ridibundus")

        assert len(ringings) == 2
        for ringing in ringings:
            assert ringing.species == "Larus ridibundus"

    def test_get_by_ringer(self, test_db, multiple_test_ringings):
        """Test getting ringings by ringer"""
        repo = RingingRepository(test_db)
        ringings = repo.get_by_ringer("Ringer A")

        assert len(ringings) == 2
        for ringing in ringings:
            assert ringing.ringer == "Ringer A"

    def test_search_ringings_multiple_filters(self, test_db, multiple_test_ringings):
        """Test searching ringings with multiple filters"""
        repo = RingingRepository(test_db)

        # Filter by species and ringer
        ringings = repo.search_ringings(
            {"species": "Larus ridibundus", "ringer": "Ringer A"}
        )

        assert len(ringings) == 2
        for ringing in ringings:
            assert ringing.species == "Larus ridibundus"
            assert ringing.ringer == "Ringer A"

    def test_get_statistics(self, test_db, multiple_test_ringings):
        """Test getting ringing statistics"""
        repo = RingingRepository(test_db)
        stats = repo.get_statistics()

        assert stats["total_ringings"] == 3
        assert stats["unique_species"] == 2
        assert stats["unique_ringers"] == 2
        assert stats["unique_places"] == 2


class TestDatabaseIntegrity:
    """Test database integrity and constraints"""

    def test_unique_ring_constraint_ringing(self, test_db, sample_ringing_data):
        """Test that ring numbers are unique in ringings table"""
        repo = RingingRepository(test_db)

        # Create first ringing
        repo.create(**sample_ringing_data)

        # Try to create another with same ring - should raise IntegrityError
        with pytest.raises(Exception):  # IntegrityError or similar
            repo.create(**sample_ringing_data)

    def test_unique_ring_constraint_family_tree(self, test_db, sample_family_tree_data):
        """Test that ring numbers are unique in family tree table"""
        repo = FamilyTreeRepository(test_db)

        # Create first entry
        repo.create(**sample_family_tree_data)

        # Try to create another with same ring - should raise IntegrityError
        with pytest.raises(Exception):  # IntegrityError or similar
            repo.create(**sample_family_tree_data)

    def test_database_rollback_on_error(self, test_db, sample_ringing_data):
        """Test that database rolls back on error"""
        repo = RingingRepository(test_db)

        # Create first ringing
        repo.create(**sample_ringing_data)
        initial_count = test_db.query(Ringing).count()

        # Try to create duplicate - should fail and rollback
        try:
            repo.create(**sample_ringing_data)
        except Exception:
            pass

        # Count should remain the same
        final_count = test_db.query(Ringing).count()
        assert final_count == initial_count

    def test_cascade_relationships(
        self, test_db, create_test_sighting, create_test_ringing
    ):
        """Test that relationships work correctly"""
        # Both sighting and ringing have the same ring number
        assert create_test_sighting.ring == create_test_ringing.ring

        # Test that we can query the relationship
        sighting_with_ringing = (
            test_db.query(Sighting)
            .filter(Sighting.id == create_test_sighting.id)
            .first()
        )

        assert sighting_with_ringing is not None
        # The relationship should be accessible
        assert hasattr(sighting_with_ringing, "ringing_data")


class TestDatabasePerformance:
    """Test database performance and indexing"""

    def test_indexed_queries_performance(self, test_db, multiple_test_sightings):
        """Test that indexed queries perform well"""
        repo = SightingRepository(test_db)

        # These queries should use indexes and complete quickly
        # We're not measuring time here, just ensuring they work

        # Query by ring (indexed)
        sightings = repo.get_by_ring("TEST001")
        assert isinstance(sightings, list)

        # Query by species (indexed)
        sightings = repo.get_by_species("Larus ridibundus")
        assert isinstance(sightings, list)

        # Query by place (indexed)
        sightings = repo.get_by_place("Location A")
        assert isinstance(sightings, list)

        # Query by date range (indexed)
        sightings = repo.get_by_date_range(date(2023, 1, 1), date(2023, 12, 31))
        assert isinstance(sightings, list)

    def test_autocomplete_performance(self, test_db, multiple_test_sightings):
        """Test autocomplete query performance"""
        repo = SightingRepository(test_db)

        # Autocomplete queries should be fast
        suggestions = repo.get_autocomplete_suggestions("species", "L", limit=10)
        assert isinstance(suggestions, list)

        suggestions = repo.get_autocomplete_suggestions("place", "Loc", limit=10)
        assert isinstance(suggestions, list)
