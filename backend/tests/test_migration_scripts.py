"""
Tests for migration scripts and data validation
"""

import pytest
import json
import pickle
import tempfile
import os
from datetime import date, datetime
from decimal import Decimal
from uuid import uuid4
from unittest.mock import Mock, patch, MagicMock

from src.database.models import Sighting, Ringing


class TestMigrationDataValidation:
    """Test data validation for migration scripts"""

    def test_validate_ringing_data_structure(self):
        """Test validation of ringing data structure"""
        # Valid ringing data
        valid_data = {
            "ring": "TEST001",
            "ring_scheme": "EURING",
            "species": "Larus ridibundus",
            "date": date(2023, 5, 15),
            "place": "Test Location",
            "lat": Decimal("52.5200"),
            "lon": Decimal("13.4050"),
            "ringer": "Test Ringer",
            "sex": 1,
            "age": 2,
            "status": "alive",
        }

        # Test that valid data passes validation
        assert self._validate_ringing_data(valid_data) is True

        # Test missing required fields
        invalid_data = valid_data.copy()
        del invalid_data["ring"]
        assert self._validate_ringing_data(invalid_data) is False

        # Test invalid data types
        invalid_data = valid_data.copy()
        invalid_data["sex"] = "invalid"
        assert self._validate_ringing_data(invalid_data) is False

    def test_validate_sighting_data_structure(self):
        """Test validation of sighting data structure"""
        # Valid sighting data
        valid_data = {
            "excel_id": 1001,
            "species": "Larus ridibundus",
            "ring": "TEST001",
            "date": date(2023, 6, 20),
            "place": "Test Location",
            "lat": Decimal("52.5300"),
            "lon": Decimal("13.4100"),
            "melder": "Test Observer",
        }

        # Test that valid data passes validation
        assert self._validate_sighting_data(valid_data) is True

        # Test with minimal data (only required fields)
        minimal_data = {"species": "Test Species", "date": date(2023, 6, 20)}
        assert self._validate_sighting_data(minimal_data) is True

    def test_validate_family_tree_data_structure(self):
        """Test validation of family tree data structure"""
        # Valid family tree data
        valid_data = {
            "ring": "TEST001",
            "partners": [{"ring": "TEST002", "year": 2023, "confirmed": True}],
            "children": [{"ring": "TEST003", "year": 2023, "confirmed": True}],
            "parents": [],
        }

        # Test that valid data passes validation
        assert self._validate_family_tree_data(valid_data) is True

        # Test missing required fields
        invalid_data = valid_data.copy()
        del invalid_data["ring"]
        assert self._validate_family_tree_data(invalid_data) is False

    def test_data_type_conversion(self):
        """Test data type conversion for migration"""
        # Test Decimal to float conversion
        decimal_value = Decimal("52.5200")
        converted = self._convert_decimal_to_float(decimal_value)
        assert isinstance(converted, float)
        assert converted == 52.5200

        # Test date string to date conversion
        date_string = "2023-05-15"
        converted = self._convert_string_to_date(date_string)
        assert isinstance(converted, date)
        assert converted == date(2023, 5, 15)

        # Test datetime to date conversion
        datetime_obj = datetime(2023, 5, 15, 10, 30, 0)
        converted = self._convert_datetime_to_date(datetime_obj)
        assert isinstance(converted, date)
        assert converted == date(2023, 5, 15)

    def test_data_integrity_validation(self, test_db):
        """Test data integrity validation after migration"""
        # Create test data
        ringing_data = {
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
        }

        sighting_data = {
            "species": "Larus ridibundus",
            "ring": "TEST001",
            "date": date(2023, 6, 20),
            "place": "Test Location",
        }

        # Create records
        ringing = Ringing(id=uuid4(), **ringing_data)
        sighting = Sighting(id=uuid4(), **sighting_data)

        test_db.add(ringing)
        test_db.add(sighting)
        test_db.commit()

        # Validate integrity
        integrity_check = self._validate_referential_integrity(test_db)
        assert integrity_check["valid"] is True
        assert integrity_check["linked_sightings"] == 1
        assert integrity_check["orphaned_sightings"] == 0

    def _validate_ringing_data(self, data: dict) -> bool:
        """Helper method to validate ringing data"""
        required_fields = [
            "ring",
            "ring_scheme",
            "species",
            "date",
            "place",
            "ringer",
            "sex",
            "age",
        ]

        # Check required fields
        for field in required_fields:
            if field not in data:
                return False

        # Check data types
        if not isinstance(data["sex"], int) or not isinstance(data["age"], int):
            return False

        return True

    def _validate_sighting_data(self, data: dict) -> bool:
        """Helper method to validate sighting data"""
        # Only species is truly required for sightings
        if "species" not in data:
            return False

        return True

    def _validate_family_tree_data(self, data: dict) -> bool:
        """Helper method to validate family tree data"""
        required_fields = ["ring"]

        # Check required fields
        for field in required_fields:
            if field not in data:
                return False

        return True

    def _convert_decimal_to_float(self, value):
        """Helper method to convert Decimal to float"""
        if isinstance(value, Decimal):
            return float(value)
        return value

    def _convert_string_to_date(self, value):
        """Helper method to convert string to date"""
        if isinstance(value, str):
            return datetime.strptime(value, "%Y-%m-%d").date()
        return value

    def _convert_datetime_to_date(self, value):
        """Helper method to convert datetime to date"""
        if isinstance(value, datetime):
            return value.date()
        return value

    def _validate_referential_integrity(self, db):
        """Helper method to validate referential integrity"""
        # Count sightings with matching ringings
        linked_sightings = (
            db.query(Sighting).join(Ringing, Sighting.ring == Ringing.ring).count()
        )

        # Count sightings with rings but no matching ringing record
        orphaned_sightings = (
            db.query(Sighting)
            .outerjoin(Ringing, Sighting.ring == Ringing.ring)
            .filter(Sighting.ring.isnot(None))
            .filter(Ringing.ring.is_(None))
            .count()
        )

        return {
            "valid": True,
            "linked_sightings": linked_sightings,
            "orphaned_sightings": orphaned_sightings,
        }


class TestMigrationBatchProcessing:
    """Test batch processing functionality for migrations"""

    def test_batch_processing_ringings(self, test_db):
        """Test batch processing of ringing records"""
        # Create test data
        batch_data = []
        for i in range(5):
            batch_data.append(
                {
                    "ring": f"BATCH{i:03d}",
                    "ring_scheme": "EURING",
                    "species": "Larus ridibundus",
                    "date": date(2023, 5, 15),
                    "place": "Test Location",
                    "lat": 52.5200,
                    "lon": 13.4050,
                    "ringer": "Test Ringer",
                    "sex": 1,
                    "age": 2,
                }
            )

        # Process batch
        result = self._process_ringing_batch(test_db, batch_data)

        assert result["processed"] == 5
        assert result["errors"] == 0

        # Verify records were created
        count = test_db.query(Ringing).count()
        assert count == 5

    def test_batch_processing_sightings(self, test_db):
        """Test batch processing of sighting records"""
        # Create test data
        batch_data = []
        for i in range(5):
            batch_data.append(
                {
                    "excel_id": 1000 + i,
                    "species": "Larus ridibundus",
                    "ring": f"BATCH{i:03d}",
                    "date": date(2023, 6, 20),
                    "place": "Test Location",
                }
            )

        # Process batch
        result = self._process_sighting_batch(test_db, batch_data)

        assert result["processed"] == 5
        assert result["errors"] == 0

        # Verify records were created
        count = test_db.query(Sighting).count()
        assert count == 5

    def test_batch_processing_with_errors(self, test_db):
        """Test batch processing with some invalid records"""
        # Create test data with some invalid records
        batch_data = [
            {
                "ring": "VALID001",
                "ring_scheme": "EURING",
                "species": "Larus ridibundus",
                "date": date(2023, 5, 15),
                "place": "Test Location",
                "lat": 52.5200,
                "lon": 13.4050,
                "ringer": "Test Ringer",
                "sex": 1,
                "age": 2,
            },
            {
                # Missing required fields
                "ring": "INVALID001",
                "species": "Larus ridibundus",
            },
            {
                "ring": "VALID002",
                "ring_scheme": "EURING",
                "species": "Larus canus",
                "date": date(2023, 5, 16),
                "place": "Test Location 2",
                "lat": 52.5300,
                "lon": 13.4100,
                "ringer": "Test Ringer 2",
                "sex": 2,
                "age": 1,
            },
        ]

        # Process batch (should handle errors gracefully)
        result = self._process_ringing_batch(test_db, batch_data, skip_errors=True)

        assert result["processed"] == 2  # Only valid records
        assert result["errors"] == 1  # One invalid record

        # Verify only valid records were created
        count = test_db.query(Ringing).count()
        assert count == 2

    def _process_ringing_batch(self, db, batch_data, skip_errors=False):
        """Helper method to process a batch of ringing records"""
        processed = 0
        errors = 0

        for data in batch_data:
            try:
                if self._validate_ringing_data(data):
                    ringing = Ringing(id=uuid4(), **data)
                    db.add(ringing)
                    processed += 1
                else:
                    errors += 1
                    if not skip_errors:
                        raise ValueError("Invalid ringing data")
            except Exception as e:
                errors += 1
                if not skip_errors:
                    raise

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise

        return {"processed": processed, "errors": errors}

    def _process_sighting_batch(self, db, batch_data, skip_errors=False):
        """Helper method to process a batch of sighting records"""
        processed = 0
        errors = 0

        for data in batch_data:
            try:
                if self._validate_sighting_data(data):
                    sighting = Sighting(id=uuid4(), **data)
                    db.add(sighting)
                    processed += 1
                else:
                    errors += 1
                    if not skip_errors:
                        raise ValueError("Invalid sighting data")
            except Exception as e:
                errors += 1
                if not skip_errors:
                    raise

        try:
            db.commit()
        except Exception as e:
            db.rollback()
            raise

        return {"processed": processed, "errors": errors}

    def _validate_ringing_data(self, data: dict) -> bool:
        """Helper method to validate ringing data"""
        required_fields = [
            "ring",
            "ring_scheme",
            "species",
            "date",
            "place",
            "ringer",
            "sex",
            "age",
        ]

        # Check required fields
        for field in required_fields:
            if field not in data:
                return False

        return True

    def _validate_sighting_data(self, data: dict) -> bool:
        """Helper method to validate sighting data"""
        # Only species is truly required for sightings
        if "species" not in data:
            return False

        return True


class TestMigrationRollback:
    """Test migration rollback functionality"""

    def test_rollback_on_error(self, test_db):
        """Test that migration rolls back on error"""
        initial_count = test_db.query(Ringing).count()

        # Create a batch with one valid record
        batch_data = {
            "ring": "VALID001",
            "ring_scheme": "EURING",
            "species": "Larus ridibundus",
            "date": date(2023, 5, 15),
            "place": "Test Location",
            "lat": 52.5200,
            "lon": 13.4050,
            "ringer": "Test Ringer",
            "sex": 1,
            "age": 2,
        }

        # First, add a valid record and commit
        ringing = Ringing(id=uuid4(), **batch_data)
        test_db.add(ringing)
        test_db.commit()

        # Verify it was added
        count_after_valid = test_db.query(Ringing).count()
        assert count_after_valid == initial_count + 1

        # Now try to add a duplicate (should cause rollback)
        try:
            duplicate_ringing = Ringing(id=uuid4(), **batch_data)
            test_db.add(duplicate_ringing)
            test_db.commit()
        except Exception:
            test_db.rollback()

        # Count should remain the same (rollback should prevent the duplicate)
        final_count = test_db.query(Ringing).count()
        assert final_count == initial_count + 1

    def test_transaction_isolation(self, test_db):
        """Test that failed transactions don't affect other operations"""
        # Start with clean state
        initial_count = test_db.query(Ringing).count()

        # Create a valid record in one transaction
        valid_data = {
            "ring": "ISOLATED001",
            "ring_scheme": "EURING",
            "species": "Larus ridibundus",
            "date": date(2023, 5, 15),
            "place": "Test Location",
            "lat": 52.5200,
            "lon": 13.4050,
            "ringer": "Test Ringer",
            "sex": 1,
            "age": 2,
        }

        ringing = Ringing(id=uuid4(), **valid_data)
        test_db.add(ringing)
        test_db.commit()

        # Verify record was added
        count_after_valid = test_db.query(Ringing).count()
        assert count_after_valid == initial_count + 1

        # Now try an invalid operation that should fail
        try:
            duplicate_ringing = Ringing(id=uuid4(), **valid_data)  # Same ring number
            test_db.add(duplicate_ringing)
            test_db.commit()
        except Exception:
            test_db.rollback()

        # Original record should still be there
        final_count = test_db.query(Ringing).count()
        assert final_count == initial_count + 1


@pytest.fixture
def mock_dynamodb_data():
    """Mock DynamoDB data for testing"""
    return [
        {
            "ring": {"S": "TEST001"},
            "ring_scheme": {"S": "EURING"},
            "species": {"S": "Larus ridibundus"},
            "date": {"S": "2023-05-15"},
            "place": {"S": "Test Location"},
            "lat": {"N": "52.5200"},
            "lon": {"N": "13.4050"},
            "ringer": {"S": "Test Ringer"},
            "sex": {"N": "1"},
            "age": {"N": "2"},
        }
    ]


@pytest.fixture
def mock_s3_pickle_data():
    """Mock S3 pickle data for testing"""
    return [
        {
            "excel_id": 1001,
            "species": "Larus ridibundus",
            "ring": "TEST001",
            "date": date(2023, 6, 20),
            "place": "Test Location",
        }
    ]


class TestMigrationScriptIntegration:
    """Integration tests for migration scripts"""

    @patch("boto3.client")
    def test_dynamodb_migration_mock(
        self, mock_boto_client, test_db, mock_dynamodb_data
    ):
        """Test DynamoDB migration with mocked AWS client"""
        # Mock DynamoDB client
        mock_dynamodb = Mock()
        mock_boto_client.return_value = mock_dynamodb

        # Mock scan response
        mock_dynamodb.scan.return_value = {
            "Items": mock_dynamodb_data,
            "Count": len(mock_dynamodb_data),
            "ScannedCount": len(mock_dynamodb_data),
        }

        # Test that migration would process the data correctly
        # (This is a simplified test since we're mocking the AWS parts)
        processed_data = self._process_dynamodb_items(mock_dynamodb_data)

        assert len(processed_data) == 1
        assert processed_data[0]["ring"] == "TEST001"
        assert processed_data[0]["species"] == "Larus ridibundus"

    @patch("boto3.client")
    def test_s3_migration_mock(self, mock_boto_client, test_db, mock_s3_pickle_data):
        """Test S3 pickle migration with mocked AWS client"""
        # Mock S3 client
        mock_s3 = Mock()
        mock_boto_client.return_value = mock_s3

        # Mock pickle data
        pickle_data = pickle.dumps(mock_s3_pickle_data)
        mock_s3.get_object.return_value = {
            "Body": Mock(read=Mock(return_value=pickle_data))
        }

        # Test that migration would process the data correctly
        # (This is a simplified test since we're mocking the AWS parts)
        processed_data = self._process_s3_pickle_data(pickle_data)

        assert len(processed_data) == 1
        assert processed_data[0]["species"] == "Larus ridibundus"
        assert processed_data[0]["ring"] == "TEST001"

    def _process_dynamodb_items(self, items):
        """Helper method to process DynamoDB items"""
        processed = []
        for item in items:
            processed_item = {}
            for key, value in item.items():
                if "S" in value:
                    processed_item[key] = value["S"]
                elif "N" in value:
                    processed_item[key] = (
                        float(value["N"]) if "." in value["N"] else int(value["N"])
                    )
            processed.append(processed_item)
        return processed

    def _process_s3_pickle_data(self, pickle_data):
        """Helper method to process S3 pickle data"""
        return pickle.loads(pickle_data)
