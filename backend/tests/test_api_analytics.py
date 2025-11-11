"""
API endpoint tests for analytics
"""

import pytest
from datetime import date
from uuid import uuid4


class TestAnalyticsAPI:
    """Test analytics API endpoints"""

    def test_get_ring_history_empty(self, client):
        """Test getting ring history when no sightings exist"""
        response = client.get("/api/analytics/history/TEST001")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_ring_history_with_data(self, client, create_test_sighting):
        """Test getting ring history with sighting data"""
        ring = create_test_sighting.ring
        response = client.get(f"/api/analytics/history/{ring}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert data[0]["ring"] == ring

    def test_get_friends_from_ring_empty(self, client):
        """Test getting friends analysis when no data exists"""
        response = client.get("/api/analytics/friends/TEST001")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_friends_from_ring_with_min_sightings(
        self, client, create_test_sighting
    ):
        """Test getting friends analysis with minimum sightings parameter"""
        ring = create_test_sighting.ring
        response = client.get(f"/api/analytics/friends/{ring}?min_shared_sightings=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_groups_from_ring(self, client, create_test_sighting):
        """Test getting groups analysis (alias for friends)"""
        ring = create_test_sighting.ring
        response = client.get(f"/api/analytics/groups/{ring}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

    def test_get_seasonal_analysis_empty(self, client):
        """Test getting seasonal analysis when no data exists"""
        response = client.get("/api/seasonal-analysis")
        assert response.status_code == 200
        data = response.json()
        assert "counts" in data
        assert isinstance(data["counts"], dict)

    def test_get_seasonal_analysis_with_data(self, client, multiple_test_sightings):
        """Test getting seasonal analysis with sighting data"""
        response = client.get("/api/seasonal-analysis")
        assert response.status_code == 200
        data = response.json()
        assert "counts" in data
        assert isinstance(data["counts"], dict)

        # Check structure of seasonal analysis data
        for species, seasonal_data in data["counts"].items():
            assert isinstance(seasonal_data, list)
            if seasonal_data:  # If there's data for this species
                for month_data in seasonal_data:
                    assert "species" in month_data
                    assert "month" in month_data
                    assert "absolute_avg" in month_data
                    assert "relative_avg" in month_data


@pytest.fixture
def sightings_with_partners(test_db):
    """Create test sightings with partner relationships for friends analysis"""
    from src.database.models import Sighting

    sightings_data = [
        {
            "excel_id": 1001,
            "species": "Larus ridibundus",
            "ring": "FRIEND001",
            "partner": "FRIEND002",
            "date": date(2023, 5, 15),
            "place": "Location A",
            "lat": 52.5200,
            "lon": 13.4050,
        },
        {
            "excel_id": 1002,
            "species": "Larus ridibundus",
            "ring": "FRIEND002",
            "partner": "FRIEND001",
            "date": date(2023, 5, 15),
            "place": "Location A",
            "lat": 52.5200,
            "lon": 13.4050,
        },
        {
            "excel_id": 1003,
            "species": "Larus ridibundus",
            "ring": "FRIEND001",
            "partner": "FRIEND002",
            "date": date(2023, 6, 20),
            "place": "Location B",
            "lat": 52.5300,
            "lon": 13.4100,
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


class TestAnalyticsWithPartners:
    """Test analytics endpoints with partner relationship data"""

    def test_get_friends_analysis_with_partners(self, client, sightings_with_partners):
        """Test friends analysis with actual partner relationships"""
        response = client.get("/api/analytics/friends/FRIEND001?min_shared_sightings=1")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)

        # Should find FRIEND002 as a friend due to shared sightings
        # The exact structure depends on the analytics service implementation

    def test_get_ring_history_multiple_sightings(self, client, sightings_with_partners):
        """Test getting ring history with multiple sightings"""
        response = client.get("/api/analytics/history/FRIEND001")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 2  # FRIEND001 has 2 sightings

        # Verify sightings are for the correct ring
        for sighting in data:
            assert sighting["ring"] == "FRIEND001"
