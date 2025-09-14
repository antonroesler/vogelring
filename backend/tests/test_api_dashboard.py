"""
API endpoint tests for dashboard
"""
import pytest
from datetime import date, timedelta


class TestDashboardAPI:
    """Test dashboard API endpoints"""
    
    def test_get_dashboard_empty(self, client):
        """Test getting dashboard data when database is empty"""
        response = client.get("/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        assert "overview" in data
        assert "top_species" in data
        assert "top_locations" in data
        assert "daily_activity" in data
        assert "generated_at" in data
        
        # Check overview structure
        overview = data["overview"]
        assert overview["total_sightings"] == 0
        assert overview["total_ringings"] == 0
        assert overview["total_species"] == 0
        assert overview["recent_sightings"] == 0
        assert overview["recent_ringings"] == 0
        assert overview["recent_species"] == 0
        assert overview["period_days"] == 30  # default
        
        # Empty lists
        assert data["top_species"] == []
        assert data["top_locations"] == []
        assert isinstance(data["daily_activity"], dict)
    
    def test_get_dashboard_with_data(self, client, multiple_test_sightings, multiple_test_ringings):
        """Test getting dashboard data with existing data"""
        response = client.get("/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Should have some data
        overview = data["overview"]
        assert overview["total_sightings"] == 3
        assert overview["total_ringings"] == 3
        assert overview["total_species"] >= 1
        
        # Now the test data should be in the recent period (last 30 days)
        # since we updated the fixtures to use current dates
        assert len(data["top_species"]) >= 1
        assert len(data["top_locations"]) >= 1
        
        # Check structure of top species
        if data["top_species"]:
            species = data["top_species"][0]
            assert "species" in species
            assert "count" in species
            assert isinstance(species["count"], int)
        
        # Check structure of top locations
        if data["top_locations"]:
            location = data["top_locations"][0]
            assert "location" in location
            assert "count" in location
            assert isinstance(location["count"], int)
    
    def test_get_dashboard_with_custom_period(self, client, multiple_test_sightings):
        """Test getting dashboard data with custom time period"""
        response = client.get("/api/dashboard?days=7")
        assert response.status_code == 200
        data = response.json()
        
        assert data["overview"]["period_days"] == 7
        
        # Test with maximum period
        response = client.get("/api/dashboard?days=365")
        assert response.status_code == 200
        data = response.json()
        assert data["overview"]["period_days"] == 365
    
    def test_get_dashboard_invalid_period(self, client):
        """Test dashboard with invalid period parameters"""
        # Too small
        response = client.get("/api/dashboard?days=0")
        assert response.status_code == 422
        
        # Too large
        response = client.get("/api/dashboard?days=400")
        assert response.status_code == 422
    
    def test_get_dashboard_summary_empty(self, client):
        """Test getting dashboard summary when database is empty"""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        
        assert "totals" in data
        assert "date_ranges" in data
        
        totals = data["totals"]
        assert totals["sightings"] == 0
        assert totals["ringings"] == 0
        
        date_ranges = data["date_ranges"]
        assert "sightings" in date_ranges
        assert "ringings" in date_ranges
        assert date_ranges["sightings"]["earliest"] is None
        assert date_ranges["sightings"]["latest"] is None
    
    def test_get_dashboard_summary_with_data(self, client, multiple_test_sightings, multiple_test_ringings):
        """Test getting dashboard summary with existing data"""
        response = client.get("/api/dashboard/summary")
        assert response.status_code == 200
        data = response.json()
        
        totals = data["totals"]
        assert totals["sightings"] == 3
        assert totals["ringings"] == 3
        
        date_ranges = data["date_ranges"]
        assert date_ranges["sightings"]["earliest"] is not None
        assert date_ranges["sightings"]["latest"] is not None
        assert date_ranges["ringings"]["earliest"] is not None
        assert date_ranges["ringings"]["latest"] is not None
        
        # Validate date format (ISO format)
        earliest_sighting = date_ranges["sightings"]["earliest"]
        assert len(earliest_sighting) == 10  # YYYY-MM-DD format
        assert earliest_sighting.count("-") == 2
    
    def test_dashboard_daily_activity_structure(self, client, multiple_test_sightings):
        """Test that daily activity data has correct structure"""
        response = client.get("/api/dashboard?days=7")
        assert response.status_code == 200
        data = response.json()
        
        daily_activity = data["daily_activity"]
        assert isinstance(daily_activity, dict)
        
        # Should have entries for the last 7 days
        today = date.today()
        for i in range(7):
            check_date = today - timedelta(days=i)
            date_str = str(check_date)
            assert date_str in daily_activity
            assert isinstance(daily_activity[date_str], int)
            assert daily_activity[date_str] >= 0
    
    def test_dashboard_performance_with_large_dataset(self, client, test_db):
        """Test dashboard performance with a larger dataset"""
        from src.database.models import Sighting
        from uuid import uuid4
        from datetime import date, timedelta
        
        # Create a larger dataset (100 sightings)
        base_date = date.today() - timedelta(days=30)
        sightings = []
        
        for i in range(100):
            sighting = Sighting(
                id=uuid4(),
                species=f"Species {i % 10}",  # 10 different species
                place=f"Location {i % 5}",    # 5 different locations
                date=base_date + timedelta(days=i % 30),
                excel_id=2000 + i
            )
            sightings.append(sighting)
        
        test_db.add_all(sightings)
        test_db.commit()
        
        # Test that dashboard still responds quickly
        response = client.get("/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Should have aggregated the data correctly
        assert data["overview"]["total_sightings"] == 100
        assert len(data["top_species"]) <= 10  # Limited to top 10
        assert len(data["top_locations"]) <= 10  # Limited to top 10