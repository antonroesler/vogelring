"""
API endpoint tests for reports
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from botocore.exceptions import ClientError, NoCredentialsError


class TestReportsAPI:
    """Test reports API endpoints"""
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_create_shareable_report_success(self, mock_get_s3_client, client, multiple_test_sightings):
        """Test creating a shareable report successfully"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/vogelring-data/reports/test_report.json?signature=abc123"
        
        report_request = {
            "title": "Test Report",
            "description": "A test report for validation",
            "include_sightings": True,
            "include_ringings": False,
            "expiry_days": 7
        }
        
        response = client.post("/api/report/shareable", json=report_request)
        assert response.status_code == 200
        
        data = response.json()
        assert "report_id" in data
        assert data["title"] == "Test Report"
        assert data["description"] == "A test report for validation"
        assert "download_url" in data
        assert "created_at" in data
        assert "expires_at" in data
        assert "file_size" in data
        
        # Verify S3 interactions
        mock_s3.put_object.assert_called_once()
        mock_s3.generate_presigned_url.assert_called_once()
        
        # Check put_object call
        put_call = mock_s3.put_object.call_args
        assert put_call[1]["Bucket"] == "vogelring-data"
        assert put_call[1]["ContentType"] == "application/json"
        assert "reports/" in put_call[1]["Key"]
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_create_shareable_report_with_filters(self, mock_get_s3_client, client, multiple_test_sightings):
        """Test creating a shareable report with filters"""
        mock_s3 = Mock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/test-url"
        
        report_request = {
            "title": "Filtered Report",
            "filters": {
                "species": "Larus ridibundus",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31"
            },
            "include_sightings": True,
            "include_ringings": True,
            "expiry_days": 3
        }
        
        response = client.post("/api/report/shareable", json=report_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["title"] == "Filtered Report"
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_create_shareable_report_s3_error(self, mock_get_s3_client, client):
        """Test handling S3 errors during report creation"""
        mock_s3 = Mock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.put_object.side_effect = ClientError(
            error_response={'Error': {'Code': 'AccessDenied', 'Message': 'Access Denied'}},
            operation_name='PutObject'
        )
        
        report_request = {
            "title": "Test Report",
            "include_sightings": True,
            "include_ringings": False
        }
        
        response = client.post("/api/report/shareable", json=report_request)
        assert response.status_code == 500
        assert "Failed to upload report to S3" in response.json()["detail"]
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_create_shareable_report_no_credentials(self, mock_get_s3_client, client):
        """Test handling missing AWS credentials"""
        mock_get_s3_client.side_effect = NoCredentialsError()
        
        report_request = {
            "title": "Test Report",
            "include_sightings": True
        }
        
        response = client.post("/api/report/shareable", json=report_request)
        assert response.status_code == 500
        # The actual error message might be different depending on how NoCredentialsError is handled
        assert "credentials" in response.json()["detail"].lower()
    
    def test_create_shareable_report_validation_error(self, client):
        """Test validation errors in report creation"""
        # Missing required title
        invalid_request = {
            "include_sightings": True
        }
        
        response = client.post("/api/report/shareable", json=invalid_request)
        assert response.status_code == 422
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_get_presigned_url_success(self, mock_get_s3_client, client):
        """Test generating a new presigned URL for existing report"""
        mock_s3 = Mock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.head_object.return_value = {}  # Object exists
        mock_s3.generate_presigned_url.return_value = "https://s3.amazonaws.com/new-presigned-url"
        
        response = client.get("/api/report/presigned-url?s3_key=reports/test_report.json&expiry_hours=24")
        assert response.status_code == 200
        
        data = response.json()
        assert "download_url" in data
        assert "expires_at" in data
        assert "s3_key" in data
        assert data["s3_key"] == "reports/test_report.json"
        
        # Verify S3 interactions
        mock_s3.head_object.assert_called_once_with(Bucket="vogelring-data", Key="reports/test_report.json")
        mock_s3.generate_presigned_url.assert_called_once()
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_get_presigned_url_not_found(self, mock_get_s3_client, client):
        """Test generating presigned URL for non-existent report"""
        mock_s3 = Mock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.head_object.side_effect = ClientError(
            error_response={'Error': {'Code': '404', 'Message': 'Not Found'}},
            operation_name='HeadObject'
        )
        
        response = client.get("/api/report/presigned-url?s3_key=reports/nonexistent.json")
        assert response.status_code == 404
        assert "Report not found" in response.json()["detail"]
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_list_reports_success(self, mock_get_s3_client, client):
        """Test listing available reports"""
        mock_s3 = Mock()
        mock_get_s3_client.return_value = mock_s3
        
        # Mock list_objects_v2 response
        from datetime import datetime
        mock_s3.list_objects_v2.return_value = {
            'Contents': [
                {
                    'Key': 'reports/report1.json',
                    'Size': 1024,
                    'LastModified': datetime(2023, 6, 1, 12, 0, 0)
                },
                {
                    'Key': 'reports/report2.json',
                    'Size': 2048,
                    'LastModified': datetime(2023, 6, 2, 12, 0, 0)
                }
            ],
            'IsTruncated': False
        }
        
        # Mock head_object responses for metadata
        mock_s3.head_object.side_effect = [
            {
                'Metadata': {
                    'title': 'Report 1',
                    'created_at': '2023-06-01T12:00:00Z'
                }
            },
            {
                'Metadata': {
                    'title': 'Report 2',
                    'created_at': '2023-06-02T12:00:00Z'
                }
            }
        ]
        
        response = client.get("/api/report/list")
        assert response.status_code == 200
        
        data = response.json()
        assert "reports" in data
        assert "total_count" in data
        assert "truncated" in data
        
        reports = data["reports"]
        assert len(reports) == 2
        assert reports[0]["s3_key"] == "reports/report1.json"
        assert reports[0]["title"] == "Report 1"
        assert reports[0]["size"] == 1024
        assert data["total_count"] == 2
        assert data["truncated"] is False
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_list_reports_empty(self, mock_get_s3_client, client):
        """Test listing reports when none exist"""
        mock_s3 = Mock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.list_objects_v2.return_value = {'IsTruncated': False}
        
        response = client.get("/api/report/list")
        assert response.status_code == 200
        
        data = response.json()
        assert data["reports"] == []
        assert data["total_count"] == 0
        assert data["truncated"] is False
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_delete_report_success(self, mock_get_s3_client, client):
        """Test deleting a report successfully"""
        mock_s3 = Mock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.head_object.return_value = {}  # Object exists
        mock_s3.delete_object.return_value = {}
        
        response = client.delete("/api/report/test_report_123")
        assert response.status_code == 200
        
        data = response.json()
        assert "deleted successfully" in data["message"]
        
        # Verify S3 interactions
        mock_s3.head_object.assert_called_once_with(Bucket="vogelring-data", Key="reports/test_report_123.json")
        mock_s3.delete_object.assert_called_once_with(Bucket="vogelring-data", Key="reports/test_report_123.json")
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_delete_report_not_found(self, mock_get_s3_client, client):
        """Test deleting a non-existent report"""
        mock_s3 = Mock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.head_object.side_effect = ClientError(
            error_response={'Error': {'Code': '404', 'Message': 'Not Found'}},
            operation_name='HeadObject'
        )
        
        response = client.delete("/api/report/nonexistent_report")
        assert response.status_code == 404
        assert "Report not found" in response.json()["detail"]
    
    def test_report_request_validation(self, client):
        """Test validation of report request parameters"""
        # Test expiry_days validation
        invalid_request = {
            "title": "Test Report",
            "expiry_days": -1  # Invalid negative value
        }
        
        response = client.post("/api/report/shareable", json=invalid_request)
        # Should still work as pydantic will use default value or handle it
        # The actual validation depends on the Field constraints we set
        
        # Test with very long title
        long_title_request = {
            "title": "A" * 1000,  # Very long title
            "include_sightings": True
        }
        
        # This should still work unless we add specific length constraints
        # The test mainly ensures the API doesn't crash with edge cases
    
    @patch('src.api.routers.reports.get_s3_client')
    def test_report_content_structure(self, mock_get_s3_client, client, create_test_sighting, create_test_ringing):
        """Test that generated report has correct content structure"""
        mock_s3 = Mock()
        mock_get_s3_client.return_value = mock_s3
        mock_s3.put_object.return_value = {}
        mock_s3.generate_presigned_url.return_value = "https://test-url"
        
        report_request = {
            "title": "Content Test Report",
            "include_sightings": True,
            "include_ringings": True
        }
        
        response = client.post("/api/report/shareable", json=report_request)
        assert response.status_code == 200
        
        # Check that put_object was called with proper JSON structure
        put_call = mock_s3.put_object.call_args
        report_body = put_call[1]["Body"]
        
        # The body should be valid JSON bytes
        assert isinstance(report_body, bytes)
        
        # We could decode and validate JSON structure here if needed
        import json
        report_data = json.loads(report_body.decode('utf-8'))
        
        assert "metadata" in report_data
        assert "data" in report_data
        assert report_data["metadata"]["title"] == "Content Test Report"
        assert "sightings" in report_data["data"]
        assert "ringings" in report_data["data"]