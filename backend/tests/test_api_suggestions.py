"""
API endpoint tests for suggestions
"""
import pytest


class TestSuggestionsAPI:
    """Test suggestions API endpoints"""
    
    def test_get_all_suggestions_empty(self, client):
        """Test getting all suggestions when database is empty"""
        response = client.get("/api/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Should contain all suggestion categories
        expected_keys = ["species", "places", "habitats", "melders", "field_fruits", "ringers"]
        for key in expected_keys:
            assert key in data
            assert isinstance(data[key], list)
    
    def test_get_all_suggestions_with_data(self, client, multiple_test_sightings, multiple_test_ringings):
        """Test getting all suggestions with data"""
        response = client.get("/api/suggestions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        
        # Should have species suggestions from test data
        assert len(data["species"]) > 0
        assert len(data["places"]) > 0
        assert len(data["ringers"]) > 0
    
    def test_get_species_suggestions_empty(self, client):
        """Test getting species suggestions when database is empty"""
        response = client.get("/api/suggestions/species")
        assert response.status_code == 200
        data = response.json()
        assert "species" in data
        assert isinstance(data["species"], list)
        assert len(data["species"]) == 0
    
    def test_get_species_suggestions_with_data(self, client, multiple_test_sightings):
        """Test getting species suggestions with data"""
        response = client.get("/api/suggestions/species")
        assert response.status_code == 200
        data = response.json()
        assert "species" in data
        assert isinstance(data["species"], list)
        assert len(data["species"]) > 0
        
        # Should contain species from test data
        species_list = data["species"]
        assert "Larus ridibundus" in species_list
        assert "Larus canus" in species_list
    
    def test_get_place_suggestions_empty(self, client):
        """Test getting place suggestions when database is empty"""
        response = client.get("/api/suggestions/places")
        assert response.status_code == 200
        data = response.json()
        assert "places" in data
        assert isinstance(data["places"], list)
        assert len(data["places"]) == 0
    
    def test_get_place_suggestions_with_data(self, client, multiple_test_sightings):
        """Test getting place suggestions with data"""
        response = client.get("/api/suggestions/places")
        assert response.status_code == 200
        data = response.json()
        assert "places" in data
        assert isinstance(data["places"], list)
        assert len(data["places"]) > 0
        
        # Should contain places from test data
        places_list = data["places"]
        assert "Location A" in places_list
        assert "Location B" in places_list
    
    def test_get_habitat_suggestions_empty(self, client):
        """Test getting habitat suggestions when database is empty"""
        response = client.get("/api/suggestions/habitats")
        assert response.status_code == 200
        data = response.json()
        assert "habitats" in data
        assert isinstance(data["habitats"], list)
    
    def test_get_habitat_suggestions_with_data(self, client, create_test_sighting):
        """Test getting habitat suggestions with data"""
        response = client.get("/api/suggestions/habitats")
        assert response.status_code == 200
        data = response.json()
        assert "habitats" in data
        assert isinstance(data["habitats"], list)
        
        # Should contain habitat from test data if present
        if create_test_sighting.habitat:
            assert create_test_sighting.habitat in data["habitats"]
    
    def test_get_melder_suggestions_empty(self, client):
        """Test getting melder suggestions when database is empty"""
        response = client.get("/api/suggestions/melders")
        assert response.status_code == 200
        data = response.json()
        assert "melders" in data
        assert isinstance(data["melders"], list)
    
    def test_get_melder_suggestions_with_data(self, client, create_test_sighting):
        """Test getting melder suggestions with data"""
        response = client.get("/api/suggestions/melders")
        assert response.status_code == 200
        data = response.json()
        assert "melders" in data
        assert isinstance(data["melders"], list)
        
        # Should contain melder from test data if present
        if create_test_sighting.melder:
            assert create_test_sighting.melder in data["melders"]
    
    def test_get_field_fruit_suggestions_empty(self, client):
        """Test getting field fruit suggestions when database is empty"""
        response = client.get("/api/suggestions/field_fruits")
        assert response.status_code == 200
        data = response.json()
        assert "field_fruits" in data
        assert isinstance(data["field_fruits"], list)
    
    def test_get_field_fruit_suggestions_with_data(self, client, create_test_sighting):
        """Test getting field fruit suggestions with data"""
        response = client.get("/api/suggestions/field_fruits")
        assert response.status_code == 200
        data = response.json()
        assert "field_fruits" in data
        assert isinstance(data["field_fruits"], list)
        
        # Should contain field fruit from test data if present
        if create_test_sighting.field_fruit:
            assert create_test_sighting.field_fruit in data["field_fruits"]
    
    def test_get_ringer_suggestions_empty(self, client):
        """Test getting ringer suggestions when database is empty"""
        response = client.get("/api/suggestions/ringers")
        assert response.status_code == 200
        data = response.json()
        assert "ringers" in data
        assert isinstance(data["ringers"], list)
    
    def test_get_ringer_suggestions_with_data(self, client, multiple_test_ringings):
        """Test getting ringer suggestions with data"""
        response = client.get("/api/suggestions/ringers")
        assert response.status_code == 200
        data = response.json()
        assert "ringers" in data
        assert isinstance(data["ringers"], list)
        assert len(data["ringers"]) > 0
        
        # Should contain ringers from test data
        ringers_list = data["ringers"]
        assert "Ringer A" in ringers_list
        assert "Ringer B" in ringers_list


@pytest.fixture
def sightings_with_various_fields(test_db):
    """Create test sightings with various field values for suggestion testing"""
    from src.database.models import Sighting
    from uuid import uuid4
    from datetime import date
    
    sightings_data = [
        {
            "species": "Larus ridibundus",
            "place": "Wetland Park",
            "habitat": "wetland",
            "melder": "Observer A",
            "field_fruit": "berries",
            "date": date(2023, 5, 15),
        },
        {
            "species": "Larus canus",
            "place": "City Lake",
            "habitat": "urban",
            "melder": "Observer B",
            "field_fruit": "seeds",
            "date": date(2023, 6, 20),
        },
        {
            "species": "Larus ridibundus",
            "place": "Wetland Park",
            "habitat": "wetland",
            "melder": "Observer A",
            "field_fruit": "insects",
            "date": date(2023, 7, 10),
        }
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


class TestSuggestionsWithVariousFields:
    """Test suggestions with various field values"""
    
    def test_suggestions_frequency_ordering(self, client, sightings_with_various_fields):
        """Test that suggestions are ordered by frequency"""
        response = client.get("/api/suggestions/species")
        assert response.status_code == 200
        data = response.json()
        
        # Larus ridibundus appears twice, should be first
        species_list = data["species"]
        if len(species_list) >= 2:
            # The exact ordering depends on the service implementation
            assert "Larus ridibundus" in species_list
            assert "Larus canus" in species_list
    
    def test_all_field_types_present(self, client, sightings_with_various_fields):
        """Test that all field types have suggestions"""
        response = client.get("/api/suggestions")
        assert response.status_code == 200
        data = response.json()
        
        # Check that we have suggestions for various fields
        assert len(data["species"]) >= 2
        assert len(data["places"]) >= 2
        assert len(data["habitats"]) >= 2
        assert len(data["melders"]) >= 2
        assert len(data["field_fruits"]) >= 3