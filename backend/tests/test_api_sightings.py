"""
API endpoint tests for sightings
"""

from uuid import uuid4


class TestSightingsAPI:
    """Test sightings API endpoints"""

    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "unhealthy"]
        assert "database" in data
        assert "version" in data

    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Vogelring API"
        assert data["version"] == "1.0.0"

    def test_get_sightings_count_empty(self, client):
        """Test getting sightings count when database is empty"""
        response = client.get("/api/sightings/count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_get_sightings_count_with_data(self, client, multiple_test_sightings):
        """Test getting sightings count with data"""
        response = client.get("/api/sightings/count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_get_sightings_empty(self, client):
        """Test getting sightings when database is empty"""
        response = client.get("/api/sightings")
        assert response.status_code == 200
        data = response.json()
        assert data["sightings"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 100

    def test_get_sightings_with_data(self, client, multiple_test_sightings):
        """Test getting sightings with data"""
        response = client.get("/api/sightings")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sightings"]) == 3
        assert data["pagination"]["total"] == 3
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 100

        # Check that sightings have expected fields
        sighting = data["sightings"][0]
        assert "id" in sighting
        assert "species" in sighting
        assert "ring" in sighting
        assert "date" in sighting
        assert "place" in sighting

    def test_get_sightings_pagination(self, client, multiple_test_sightings):
        """Test sightings pagination"""
        # Get first page with limit of 2
        response = client.get("/api/sightings?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sightings"]) == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 2
        assert data["pagination"]["total"] == 3
        assert data["pagination"]["pages"] == 2

        # Get second page
        response = client.get("/api/sightings?page=2&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sightings"]) == 1
        assert data["pagination"]["page"] == 2

    def test_get_sightings_with_filters(self, client, multiple_test_sightings):
        """Test getting sightings with filters"""
        # Filter by species
        response = client.get("/api/sightings?species=Larus ridibundus")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sightings"]) == 2  # Two sightings with this species

        # Filter by place
        response = client.get("/api/sightings?place=Location A")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sightings"]) == 2  # Two sightings at Location A

        # Filter by ring
        response = client.get("/api/sightings?ring=TEST001")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sightings"]) == 1
        assert data["sightings"][0]["ring"] == "TEST001"

    def test_get_sighting_by_id(self, client, create_test_sighting):
        """Test getting a specific sighting by ID"""
        sighting_id = str(create_test_sighting.id)
        response = client.get(f"/api/sightings/{sighting_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sighting_id
        assert data["species"] == "Larus ridibundus"
        assert data["ring"] == "TEST001"

    def test_get_sighting_by_id_not_found(self, client):
        """Test getting a non-existent sighting"""
        fake_id = str(uuid4())
        response = client.get(f"/api/sightings/{fake_id}")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Sighting not found"

    def test_create_sighting(self, client, sample_sighting_data):
        """Test creating a new sighting"""
        # Remove id from sample data if present
        sighting_data = sample_sighting_data.copy()
        if "id" in sighting_data:
            del sighting_data["id"]

        # Convert date to string for JSON serialization
        sighting_data["date"] = sighting_data["date"].isoformat()

        response = client.post("/api/sightings", json=sighting_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["species"] == "Larus ridibundus"
        assert data["ring"] == "TEST001"
        assert data["place"] == "Test Observation Site"

    def test_create_sighting_minimal_data(self, client):
        """Test creating a sighting with minimal required data"""
        minimal_data = {"species": "Test Species", "date": "2023-06-01"}

        response = client.post("/api/sightings", json=minimal_data)
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["species"] == "Test Species"

    def test_update_sighting(self, client, create_test_sighting):
        """Test updating an existing sighting"""
        sighting_id = str(create_test_sighting.id)
        update_data = {
            "id": sighting_id,
            "species": "Updated Species",
            "comment": "Updated comment",
        }

        response = client.put("/api/sightings", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == sighting_id
        assert data["species"] == "Updated Species"
        assert data["comment"] == "Updated comment"
        # Original data should be preserved
        assert data["ring"] == "TEST001"

    def test_update_sighting_not_found(self, client):
        """Test updating a non-existent sighting"""
        fake_id = str(uuid4())
        update_data = {"id": fake_id, "species": "Updated Species"}

        response = client.put("/api/sightings", json=update_data)
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Sighting not found"

    def test_delete_sighting(self, client, create_test_sighting):
        """Test deleting a sighting"""
        sighting_id = str(create_test_sighting.id)

        # Verify sighting exists
        response = client.get(f"/api/sightings/{sighting_id}")
        assert response.status_code == 200

        # Delete sighting
        response = client.delete(f"/api/sightings/{sighting_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Sighting deleted successfully"

        # Verify sighting is deleted
        response = client.get(f"/api/sightings/{sighting_id}")
        assert response.status_code == 404

    def test_delete_sighting_not_found(self, client):
        """Test deleting a non-existent sighting"""
        fake_id = str(uuid4())
        response = client.delete(f"/api/sightings/{fake_id}")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Sighting not found"

    def test_get_sightings_statistics(self, client, multiple_test_sightings):
        """Test getting sightings statistics"""
        response = client.get("/api/sightings/statistics")
        assert response.status_code == 200
        data = response.json()
        # Statistics should contain basic counts and information
        assert isinstance(data, dict)

    def test_get_sightings_by_radius(self, client, multiple_test_sightings):
        """Test getting sightings within a radius"""
        # Use coordinates near Location A (52.5200, 13.4050)
        response = client.get(
            "/api/sightings/radius?lat=52.5200&lon=13.4050&radius_m=1000"
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        # Should find sightings within 1km of the location

    def test_get_autocomplete_suggestions(self, client, multiple_test_sightings):
        """Test autocomplete suggestions"""
        # Test species autocomplete
        response = client.get("/api/sightings/autocomplete/species?q=Larus")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

        # Test place autocomplete
        response = client.get("/api/sightings/autocomplete/place?q=Location")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    def test_get_autocomplete_suggestions_with_limit(
        self, client, multiple_test_sightings
    ):
        """Test autocomplete suggestions with limit"""
        response = client.get("/api/sightings/autocomplete/species?q=Larus&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) <= 1

    def test_get_enriched_sightings(
        self, client, create_test_sighting, create_test_ringing
    ):
        """Test getting enriched sightings with ringing data"""
        response = client.get("/api/sightings?enriched=true")
        assert response.status_code == 200
        data = response.json()
        assert len(data["sightings"]) == 1
        # The enriched sighting should include ringing data if available
        sighting = data["sightings"][0]
        assert "id" in sighting
        assert sighting["ring"] == "TEST001"
