import json
import pytest
from datetime import date
from api.app import app
from api.models.sightings import Sighting, BirdMeta


class DateJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, date):
            return obj.isoformat()
        return super().default(obj)


def create_event(method="GET", path="/health", body=None, query_params=None, path_params=None):
    event = {
        "httpMethod": method,
        "path": path,
        "headers": {},
        "queryStringParameters": query_params or {},
        "pathParameters": path_params or {},
        "body": json.dumps(body, cls=DateJSONEncoder) if body else None,
        "isBase64Encoded": False,
    }
    return event


@pytest.fixture
def sample_sighting():
    return Sighting(
        id="05d0991f-fd82-4912-9a69-14b5ccf9c6ba",
        ring="AB123",
        reading="...B123",
        date="2024-03-20",
        place="Test Place",
        melder="Test Melder",
        species="Test Bird",
        comment="Test Comment",
        lat=123.456,
        lon=78.910,
    )


@pytest.fixture
def invalid_sighting():
    return {
        "id": "05d0991f-fde2-4952-9a69-11b5ccf9c6ba",
        "ring": "AB123",
        "date": "invalid-date",  # Invalid date format
        "place": "Test Place",
        "melder": "Test Melder",
        "species": "Test Bird",
        "comment": "Test Comment",
        "lat": 123.456,
        "lon": 78.910,
    }


def test_health():
    event = create_event(path="/health")
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert "message" in body
    assert body["message"] == "healthy"
    assert "version" in body


def test_get_sightings():
    event = create_event(path="/sightings", query_params={"page": "1", "per_page": "10"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert isinstance(body, list)
    assert len(body) == 10
    assert all(Sighting(**item) for item in body)


def test_get_sightings_invalid_page():
    event = create_event(path="/sightings", query_params={"page": "invalid", "per_page": "10"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 422


def test_get_sightings_negative_page():
    event = create_event(path="/sightings", query_params={"page": "-1", "per_page": "10"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 400


def test_get_sightings_paginated_returns_correct_number_of_sightings():
    event = create_event(path="/sightings", query_params={"page": "1", "per_page": "10"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 10

    event = create_event(path="/sightings", query_params={"page": "2", "per_page": "10"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 10

    event = create_event(path="/sightings", query_params={"page": "3", "per_page": "10"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 10


def test_get_sightings_paginated_returns_correct_number_of_sightings_with_custom_per_page():
    event = create_event(path="/sightings", query_params={"page": "1", "per_page": "50"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 50

    event = create_event(path="/sightings", query_params={"page": "2", "per_page": "50"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 50

    event = create_event(path="/sightings", query_params={"page": "3", "per_page": "50"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert len(body) == 50


def test_get_sightings_paginated_returns_correct_entries():
    # Get full list of sightings
    event = create_event(path="/sightings", query_params={"page": "1", "per_page": "1000"})
    response = app.resolve(event, {})
    full_sightings = json.loads(response["body"])

    # Test first page
    event = create_event(path="/sightings", query_params={"page": "1", "per_page": "100"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body == full_sightings[:100]

    # Test second page
    event = create_event(path="/sightings", query_params={"page": "2", "per_page": "100"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body == full_sightings[100:200]

    # Test third page
    event = create_event(path="/sightings", query_params={"page": "3", "per_page": "100"})
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body == full_sightings[200:300]


def test_get_sightings_without_pagination():
    event = create_event(path="/sightings")
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert isinstance(body, list)
    assert len(body) == 100


def test_get_sightings_count():
    event = create_event(path="/sightings/count")
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    count = json.loads(response["body"])
    assert isinstance(count, int)
    assert count >= 0


def test_add_sighting(sample_sighting):
    event = create_event(method="POST", path="/sightings", body=sample_sighting.model_dump())
    response = app.resolve(event, {})
    assert response["statusCode"] == 201  # Created
    body = json.loads(response["body"])
    assert body["id"] == sample_sighting.id
    assert body["ring"] == sample_sighting.ring
    assert body["date"] == "2024-03-20"  # Date should be serialized as ISO format


def test_add_invalid_sighting(invalid_sighting):
    event = create_event(method="POST", path="/sightings", body=invalid_sighting)
    response = app.resolve(event, {})
    assert response["statusCode"] == 400


def test_get_sighting_by_id(sample_sighting):
    # First add a sighting
    add_event = create_event(method="POST", path="/sightings", body=sample_sighting.model_dump())
    app.resolve(add_event, {})

    # Then get it by id
    event = create_event(path=f"/sightings/{sample_sighting.id}")
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["id"] == sample_sighting.id


def test_get_sighting_by_id_not_found():
    event = create_event(path="/sightings/nonexistent-id")
    response = app.resolve(event, {})
    assert response["statusCode"] == 404


def test_get_bird_suggestions():
    event = create_event(path="/birds/suggestions/2903*")
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert isinstance(body, list)


def test_get_bird_suggestions_empty_query():
    event = create_event(path="/birds/suggestions/")
    response = app.resolve(event, {})
    assert response["statusCode"] == 400


def test_get_bird_suggestions_back():
    event = create_event(path="/birds/suggestions/290...")
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert isinstance(body, list)


def test_get_bird_suggestions_front():
    event = create_event(path="/birds/suggestions/...E2")
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert isinstance(body, list)


def test_get_bird_suggestions_mid():
    event = create_event(path="/birds/suggestions/12*23")
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert isinstance(body, list)


def test_get_bird_suggestions_outer():
    event = create_event(path="/birds/suggestions/...2222...")
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert isinstance(body, list)


def test_get_bird_by_ring():
    event = create_event(path="/birds/AB123")
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert isinstance(body, dict)


def test_get_bird_by_ring_not_found():
    event = create_event(path="/birds/NONEXISTENT")
    response = app.resolve(event, {})
    assert response["statusCode"] == 404


def test_update_sighting(sample_sighting):
    # First add a sighting
    add_event = create_event(method="POST", path="/sightings", body=sample_sighting.model_dump())
    app.resolve(add_event, {})

    # Update the sighting
    updated_sighting = sample_sighting.model_dump()
    updated_sighting["comment"] = "Updated comment"
    event = create_event(method="PUT", path="/sightings", body=updated_sighting)
    response = app.resolve(event, {})
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["comment"] == "Updated comment"


def test_update_nonexistent_sighting(sample_sighting):
    nonexistent_sighting = sample_sighting.model_dump()
    nonexistent_sighting["id"] = "nonexistent-id"
    event = create_event(method="PUT", path="/sightings", body=nonexistent_sighting)
    response = app.resolve(event, {})
    assert response["statusCode"] == 404


def test_delete_sighting(sample_sighting):
    # First add a sighting
    add_event = create_event(method="POST", path="/sightings", body=sample_sighting.model_dump())
    app.resolve(add_event, {})

    # Delete the sighting
    event = create_event(method="DELETE", path=f"/sightings/{sample_sighting.id}")
    response = app.resolve(event, {})
    assert response["statusCode"] == 204

    # Verify it's deleted
    get_event = create_event(path=f"/sightings/{sample_sighting.id}")
    get_response = app.resolve(get_event, {})
    assert get_response["statusCode"] == 404


def test_delete_nonexistent_sighting(sample_sighting):
    event = create_event(method="DELETE", path="/sightings/nonexistent-id")
    response = app.resolve(event, {})
    assert response["statusCode"] == 404


def test_bad_request():
    event = create_event(method="POST", path="/sightings", body=None)
    response = app.resolve(event, {})
    assert response["statusCode"] == 400


def test_not_found():
    event = create_event(path="/nonexistent-endpoint")
    response = app.resolve(event, {})
    assert response["statusCode"] == 404
