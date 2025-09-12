# Vogelring Backend Tests

This directory contains the test suite for the Vogelring backend application. The tests are organized into different categories to ensure comprehensive coverage of the API endpoints, database operations, and migration scripts.

## Test Structure

```
tests/
├── conftest.py                     # Test configuration and fixtures
├── test_api_sightings.py          # API tests for sightings endpoints
├── test_api_ringings.py           # API tests for ringings endpoints
├── test_api_analytics.py          # API tests for analytics endpoints
├── test_api_suggestions.py        # API tests for suggestions endpoints
├── test_database_repositories.py  # Database repository integration tests
├── test_migration_scripts.py      # Migration script validation tests
├── test_database_setup.py         # Database setup and teardown utilities
└── README.md                      # This file
```

## Test Categories

### 1. API Endpoint Tests
Tests for all REST API endpoints to ensure they work correctly:

- **Sightings API** (`test_api_sightings.py`)
  - CRUD operations (Create, Read, Update, Delete)
  - Pagination and filtering
  - Autocomplete suggestions
  - Data validation
  - Error handling

- **Ringings API** (`test_api_ringings.py`)
  - CRUD operations
  - Upsert functionality
  - Pagination and filtering
  - Autocomplete suggestions
  - Data validation

- **Analytics API** (`test_api_analytics.py`)
  - Ring history analysis
  - Friends/groups analysis
  - Seasonal analysis
  - Performance with different data sets

- **Suggestions API** (`test_api_suggestions.py`)
  - Species suggestions
  - Place suggestions
  - Habitat, melder, and field fruit suggestions
  - Frequency-based ordering

### 2. Database Integration Tests
Tests for database operations and data integrity:

- **Repository Tests** (`test_database_repositories.py`)
  - CRUD operations for all repositories
  - Search and filtering functionality
  - Autocomplete queries
  - Statistics generation
  - Data relationships and joins
  - Performance with indexed queries

- **Database Setup** (`test_database_setup.py`)
  - Database creation and teardown
  - Table truncation utilities
  - Data integrity validation
  - Sample data generation
  - Performance testing utilities

### 3. Migration Script Tests
Tests for data migration and validation:

- **Migration Validation** (`test_migration_scripts.py`)
  - Data structure validation
  - Batch processing functionality
  - Error handling and rollback
  - Data type conversions
  - Referential integrity checks
  - Mock AWS service integration

## Running Tests

### Prerequisites

1. Install dependencies with uv:
   ```bash
   uv sync --extra test
   ```

2. Make sure you're in the backend directory:
   ```bash
   cd backend
   ```

### Using the Test Runner

The easiest way to run tests is using the provided test runner:

```bash
# Run all tests
python run_tests.py

# Run specific test categories
python run_tests.py --type api
python run_tests.py --type database
python run_tests.py --type migration

# Run with coverage reporting
python run_tests.py --coverage

# Run with verbose output
python run_tests.py --verbose

# Install dependencies and run tests
python run_tests.py --install-deps --coverage
```

### Using pytest directly

You can also run tests directly with uv:

```bash
# Run all tests
uv run pytest

# Run specific test files
uv run pytest tests/test_api_sightings.py
uv run pytest tests/test_database_repositories.py

# Run with coverage
uv run pytest --cov=src --cov-report=html --cov-report=term

# Run with verbose output
uv run pytest -v

# Run specific test methods
uv run pytest tests/test_api_sightings.py::TestSightingsAPI::test_create_sighting
```

## Test Configuration

### Fixtures

The `conftest.py` file contains shared fixtures used across all tests:

- `test_db`: In-memory SQLite database session
- `client`: FastAPI test client with database override
- `sample_*_data`: Sample data for different entity types
- `create_test_*`: Fixtures that create test records in the database
- `multiple_test_*`: Fixtures that create multiple test records

### Test Database

Tests use an in-memory SQLite database that is:
- Created fresh for each test function
- Automatically cleaned up after each test
- Isolated from the production database
- Fast and reliable for testing

### Environment Variables

Tests don't require any environment variables as they use mocked services and in-memory databases.

## Writing New Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test classes: `Test*`
- Test methods: `test_*`

### Example Test Structure

```python
class TestNewFeature:
    """Test new feature functionality"""
    
    def test_basic_functionality(self, client):
        """Test basic functionality"""
        response = client.get("/api/new-endpoint")
        assert response.status_code == 200
        
    def test_with_data(self, client, create_test_sighting):
        """Test with existing data"""
        response = client.get(f"/api/new-endpoint/{create_test_sighting.id}")
        assert response.status_code == 200
        
    def test_error_handling(self, client):
        """Test error handling"""
        response = client.get("/api/new-endpoint/nonexistent")
        assert response.status_code == 404
```

### Best Practices

1. **Use descriptive test names** that explain what is being tested
2. **Test both success and failure cases**
3. **Use appropriate fixtures** to set up test data
4. **Keep tests independent** - each test should work in isolation
5. **Test edge cases** and boundary conditions
6. **Use assertions that provide clear error messages**
7. **Group related tests** in classes
8. **Mock external dependencies** (AWS services, etc.)

## Coverage Reports

When running tests with coverage, reports are generated in:
- Terminal output (summary)
- `htmlcov/index.html` (detailed HTML report)

The coverage report shows:
- Line coverage for each file
- Missing lines that need tests
- Overall coverage percentage

## Continuous Integration

These tests are designed to run in CI/CD pipelines. They:
- Don't require external services
- Use in-memory databases
- Have predictable execution times
- Provide clear pass/fail results

## Troubleshooting

### Common Issues

1. **Import errors**: Make sure you're in the backend directory and the src path is correct
2. **Database errors**: Tests use in-memory SQLite, so no external database setup is needed
3. **Fixture errors**: Check that fixtures are properly defined in conftest.py
4. **Slow tests**: Database tests should be fast with in-memory SQLite

### Debug Mode

To debug failing tests:

```bash
# Run with verbose output and stop on first failure
pytest -v -x

# Run a specific test with maximum verbosity
pytest -vvv tests/test_api_sightings.py::TestSightingsAPI::test_create_sighting

# Run with pdb debugger on failures
pytest --pdb
```

## Contributing

When adding new features:

1. Write tests for new API endpoints
2. Add database tests for new repository methods
3. Update fixtures if new data structures are added
4. Ensure all tests pass before submitting changes
5. Aim for high test coverage (>90%)

The test suite is an essential part of the migration project, ensuring that the new PostgreSQL-based backend maintains the same functionality as the original AWS Lambda implementation.