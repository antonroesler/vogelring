"""
API endpoint tests for ringings
"""

from datetime import date


class TestRingingsAPI:
    """Test ringings API endpoints"""

    def test_get_ringings_count_empty(self, client):
        """Test getting ringings count when database is empty"""
        response = client.get("/api/ringings/count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0

    def test_get_ringings_count_with_data(self, client, multiple_test_ringings):
        """Test getting ringings count with data"""
        response = client.get("/api/ringings/count")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 3

    def test_get_ringings_empty(self, client):
        """Test getting ringings when database is empty"""
        response = client.get("/api/ringings")
        assert response.status_code == 200
        data = response.json()
        assert data["ringings"] == []
        assert data["pagination"]["total"] == 0
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 100

    def test_get_ringings_with_data(self, client, multiple_test_ringings):
        """Test getting ringings with data"""
        response = client.get("/api/ringings")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ringings"]) == 3
        assert data["pagination"]["total"] == 3
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 100

        # Check that ringings have expected fields
        ringing = data["ringings"][0]
        assert "id" in ringing
        assert "ring" in ringing
        assert "species" in ringing
        assert "date" in ringing
        assert "place" in ringing
        assert "ringer" in ringing

    def test_get_ringings_pagination(self, client, multiple_test_ringings):
        """Test ringings pagination"""
        # Get first page with limit of 2
        response = client.get("/api/ringings?page=1&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ringings"]) == 2
        assert data["pagination"]["page"] == 1
        assert data["pagination"]["per_page"] == 2
        assert data["pagination"]["total"] == 3
        assert data["pagination"]["pages"] == 2

        # Get second page
        response = client.get("/api/ringings?page=2&per_page=2")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ringings"]) == 1
        assert data["pagination"]["page"] == 2

    def test_get_ringings_with_filters(self, client, multiple_test_ringings):
        """Test getting ringings with filters"""
        # Filter by species
        response = client.get("/api/ringings?species=Larus ridibundus")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ringings"]) == 2  # Two ringings with this species

        # Filter by place
        response = client.get("/api/ringings?place=Location A")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ringings"]) == 2  # Two ringings at Location A

        # Filter by ringer
        response = client.get("/api/ringings?ringer=Ringer A")
        assert response.status_code == 200
        data = response.json()
        assert len(data["ringings"]) == 2  # Two ringings by Ringer A

    def test_get_ringing_by_ring(self, client, create_test_ringing):
        """Test getting a specific ringing by ring number"""
        ring = create_test_ringing.ring
        response = client.get(f"/api/ringing/{ring}")
        assert response.status_code == 200
        data = response.json()
        assert data["ring"] == ring
        assert data["species"] == "Larus ridibundus"
        assert data["ringer"] == "Test Ringer"

    def test_get_ringing_by_ring_not_found(self, client):
        """Test getting a non-existent ringing"""
        fake_ring = "NONEXISTENT"
        response = client.get(f"/api/ringing/{fake_ring}")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Ringing not found"

    def test_create_ringing(self, client, sample_ringing_data):
        """Test creating a new ringing"""
        # Convert date to string for JSON serialization
        ringing_data = sample_ringing_data.copy()
        ringing_data["date"] = ringing_data["date"].isoformat()
        ringing_data["ring"] = "NEWTEST001"  # Use different ring to avoid conflicts

        response = client.post("/api/ringing", json=ringing_data)
        assert response.status_code == 200
        data = response.json()
        assert data["ring"] == "NEWTEST001"
        assert data["species"] == "Larus ridibundus"
        assert data["ringer"] == "Test Ringer"

    def test_upsert_ringing_update(self, client, create_test_ringing):
        """Test updating an existing ringing via upsert"""
        ring = create_test_ringing.ring
        update_data = {
            "ring": ring,
            "ring_scheme": "EURING",
            "species": "Updated Species",
            "date": "2023-06-01",
            "place": "Updated Location",
            "lat": 52.5000,
            "lon": 13.4000,
            "ringer": "Updated Ringer",
            "sex": 2,
            "age": 3,
        }

        response = client.post("/api/ringing", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["ring"] == ring
        assert data["species"] == "Updated Species"
        assert data["ringer"] == "Updated Ringer"

    def test_update_ringing(self, client, create_test_ringing):
        """Test updating an existing ringing"""
        ring = create_test_ringing.ring
        update_data = {
            "ring": ring,
            "species": "Updated Species",
            "ringer": "Updated Ringer",
        }

        response = client.put("/api/ringing", json=update_data)
        assert response.status_code == 200
        data = response.json()
        assert data["ring"] == ring
        assert data["species"] == "Updated Species"
        assert data["ringer"] == "Updated Ringer"

    def test_delete_ringing(self, client, create_test_ringing):
        """Test deleting a ringing"""
        ring = create_test_ringing.ring

        # Verify ringing exists
        response = client.get(f"/api/ringing/{ring}")
        assert response.status_code == 200

        # Delete ringing
        response = client.delete(f"/api/ringing/{ring}")
        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Ringing deleted successfully"
        assert data["success"] is True

        # Verify ringing is deleted
        response = client.get(f"/api/ringing/{ring}")
        assert response.status_code == 404

    def test_get_ringings_statistics(self, client, multiple_test_ringings):
        """Test getting ringings statistics"""
        response = client.get("/api/ringings/statistics")
        assert response.status_code == 200
        data = response.json()
        # Statistics should contain basic counts and information
        assert isinstance(data, dict)

    def test_get_autocomplete_suggestions(self, client, multiple_test_ringings):
        """Test autocomplete suggestions for ringings"""
        # Test species autocomplete
        response = client.get("/api/ringings/autocomplete/species?q=Larus")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

        # Test place autocomplete
        response = client.get("/api/ringings/autocomplete/place?q=Location")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

        # Test ringer autocomplete
        response = client.get("/api/ringings/autocomplete/ringer?q=Ringer")
        assert response.status_code == 200
        data = response.json()
        assert "suggestions" in data
        assert isinstance(data["suggestions"], list)

    def test_get_autocomplete_suggestions_with_limit(
        self, client, multiple_test_ringings
    ):
        """Test autocomplete suggestions with limit"""
        response = client.get("/api/ringings/autocomplete/species?q=Larus&limit=1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["suggestions"]) <= 1

    def test_create_ringing_validation_error(self, client):
        """Test creating a ringing with invalid data"""
        invalid_data = {
            "ring": "",  # Empty ring should fail
            "species": "Test Species",
            # Missing required fields
        }

        response = client.post("/api/ringing", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_date_range_filter(self, client, multiple_test_ringings):
        """Test filtering ringings by date range"""
        from datetime import timedelta

        today = date.today()

        # Filter by date range that should include some ringings (last 30 days)
        start_date = (today - timedelta(days=30)).isoformat()
        end_date = today.isoformat()
        response = client.get(
            f"/api/ringings?start_date={start_date}&end_date={end_date}"
        )
        assert response.status_code == 200
        data = response.json()
        # Should find ringings within the date range
        assert len(data["ringings"]) >= 1

        # Filter by date range that should exclude all ringings (future dates)
        future_start = (today + timedelta(days=30)).isoformat()
        future_end = (today + timedelta(days=60)).isoformat()
        response = client.get(
            f"/api/ringings?start_date={future_start}&end_date={future_end}"
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["ringings"]) == 0
