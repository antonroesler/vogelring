import os
from datetime import date
from typing_extensions import Annotated
from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.exceptions import (
    NotFoundError,
    BadRequestError,
    InternalServerError,
)
from aws_lambda_powertools import Metrics
from pydantic import ValidationError
from aws_lambda_powertools.event_handler.openapi.params import Query

from api.models.responses import FriendResponse
from api.models.family import FamilyTreeEntry
from api.version import __version__
from api import service
from api.models.sightings import BirdMeta, Sighting
from api.models.ringing import Ringing
from api.service.seasonal_analysis import SeasonalAnalysis
from api.auth.cognito import get_user_context_from_token
from typing import Optional
import json
import traceback


app = APIGatewayRestResolver(enable_validation=True)
logger = Logger()
metrics = Metrics(namespace="Powertools")

app.enable_swagger(path="/swagger")

headers = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Credentials": "true",
}


def is_read_operation(method: str, path: str) -> bool:
    """Determine if the request is a read operation"""
    if method == "GET" or method == "OPTIONS":
        return True
    return False


@app.exception_handler(ValidationError)
def handle_validation_error(error: ValidationError):
    logger.error(f"Validation error: {error}")
    logger.error(f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")

    return Response(status_code=400, body=json.dumps(error.errors()), headers=headers)


@app.exception_handler(NotFoundError)
def handle_not_found_error(error: NotFoundError):
    logger.error(f"Not found error: {error}")
    return Response(status_code=404, headers=headers)


@app.get("/health")
def health():
    logger.info("Health API - HTTP 200")
    return Response(status_code=200, body=json.dumps({"message": "healthy", "version": __version__}), headers=headers)


@app.get("/sightings/count")
def get_sightings_count() -> int:
    logger.info("Get sightings count")
    return Response(
        status_code=200,
        body=json.dumps(service.get_sightings_count(user=app.current_event.get("user_id"))),
        headers=headers,
    )


@app.get("/sightings/radius")
def get_sightings_by_radius(
    lat: Annotated[float, Query(description="Latitude")],
    lon: Annotated[float, Query(description="Longitude")],
    radius_m: Annotated[int, Query(description="Radius in meters")],
) -> list[Sighting]:
    logger.info(f"Get sightings by radius: {lat}, {lon}, {radius_m}")
    lat = float(app.current_event.query_string_parameters.get("lat", "0"))
    lon = float(app.current_event.query_string_parameters.get("lon", "0"))
    radius_m = int(app.current_event.query_string_parameters.get("radius_m", "0"))
    return Response(
        status_code=200,
        body=json.dumps(
            [
                sighting.model_dump()
                for sighting in service.get_sightings_by_radius(
                    lat, lon, radius_m, user=app.current_event.get("user_id")
                )
            ]
        ),
        headers=headers,
    )


@app.get("/sightings/<id>")
def get_sighting_by_id(id: str) -> Sighting | None:
    logger.info(f"Get sighting by id: {id}")
    sighting = service.get_sighting_by_id(id, user=app.current_event.get("user_id"))
    if sighting is None:
        raise NotFoundError(f"Sighting with id {id} not found")
    return Response(status_code=200, body=json.dumps(sighting.model_dump()), headers=headers)


@app.get("/sightings")
def get_sightings(
    page: Annotated[Optional[int], Query()] = 1,
    per_page: Annotated[Optional[int], Query()] = 100,
    start_date: Annotated[Optional[date], Query(examples=["2024-01-01"])] = None,
    end_date: Annotated[Optional[date], Query(examples=["2022-03-27"])] = None,
    species: Annotated[Optional[str], Query(examples=["Kanadagans"])] = None,
    place: Annotated[Optional[str], Query(examples=["Ostpark"])] = None,
) -> list[Sighting]:
    logger.warning(f"User: {app.current_event.get('user_id')}")
    logger.warning(f"User: {app.current_event.get('user_context')}")

    page = int(app.current_event.query_string_parameters.get("page", "1"))
    per_page = int(app.current_event.query_string_parameters.get("per_page", "100"))
    start_date = app.current_event.query_string_parameters.get("start_date", None)
    end_date = app.current_event.query_string_parameters.get("end_date", None)
    species = app.current_event.query_string_parameters.get("species", None)
    place = app.current_event.query_string_parameters.get("place", None)
    logger.info(f"Get sightings page {page} with {per_page} per page")

    sightings = service.get_sightings(user=app.current_event.get("user_id"))

    if place is not None:
        logger.info(f"Filtering by place: {place}")
        sightings = [sighting for sighting in sightings if sighting.place == place]
    if species is not None:
        logger.info(f"Filtering by species: {species}")
        sightings = [sighting for sighting in sightings if sighting.species == species]
    if start_date is not None or end_date is not None:
        start_date = date.fromisoformat(start_date) if start_date else date(year=1900, month=1, day=1)
        end_date = date.fromisoformat(end_date) if end_date else date.today()
        logger.info(f"Filtering by date range: {start_date} to {end_date}")
        sightings = [sighting for sighting in sightings if sighting.date and start_date <= sighting.date <= end_date]
    if page < 1 or per_page < 1:
        raise BadRequestError("Page and per_page must be greater than 0")
    sightings = sightings[(page - 1) * per_page : page * per_page]
    return Response(
        status_code=200, body=json.dumps([sighting.model_dump() for sighting in reversed(sightings)]), headers=headers
    )


@app.get("/birds/suggestions/<partial_reading>")
def get_bird_suggestions_by_partial_reading(partial_reading: str) -> list[BirdMeta]:
    logger.info(f"Get bird suggestions by partial reading: {partial_reading}")
    if partial_reading == "":
        raise BadRequestError("Partial reading is required")
    if len(partial_reading) < 2:
        raise BadRequestError("Partial reading must be at least 2 characters long")
    if not any([c in partial_reading for c in ["*", "…", "..."]]):
        partial_reading = f"*{partial_reading}*"
    suggestions = service.get_bird_suggestions_by_partial_reading(
        partial_reading, user=app.current_event.get("user_id")
    )
    if suggestions is None:
        raise NotFoundError(f"No suggestions found for partial reading: {partial_reading}")
    return Response(
        status_code=200,
        body=json.dumps([suggestion_bird.model_dump() for suggestion_bird in suggestions]),
        headers=headers,
    )


@app.get("/birds/<ring>")
def get_bird_by_ring(ring: str) -> BirdMeta | None:
    logger.info(f"Get bird by ring: {ring}")
    if ring == "suggestions":
        return get_bird_suggestions_by_partial_reading("")
    bird = service.get_bird_by_ring(ring, user=app.current_event.get("user_id"))
    return (
        Response(status_code=200, body=json.dumps(bird.model_dump()), headers=headers)
        if bird
        else Response(status_code=404, headers=headers)
    )


@app.post("/sightings")
def add_sighting():
    body: Optional[str] = app.current_event.body  # raw str | None
    if body is None:
        raise BadRequestError("Request body is required")
    sighting = Sighting(**json.loads(body))
    logger.info(f"Add sighting: {sighting}")
    try:
        service.add_sighting(sighting, user=app.current_event.get("user_id"))
    except ValueError as e:
        logger.error(f"Error adding sighting: {e}")
        raise BadRequestError(str(e))
    except Exception as e:
        logger.error(f"Error adding sighting: {e}")
        raise InternalServerError("An error occurred while adding the sighting")
    logger.info(f"Sighting added: {sighting}")

    return Response(status_code=201, body=json.dumps(sighting.model_dump()), headers=headers)


@app.put("/sightings")
def update_sighting():
    body: Optional[str] = app.current_event.body  # raw str | None
    if body is None:
        raise BadRequestError("Request body is required")
    logger.info(f"Update sighting: {body}")
    sighting = Sighting(**json.loads(body))
    if service.get_sighting_by_id(sighting.id, user=app.current_event.get("user_id")) is None:
        raise NotFoundError(f"Sighting with id {sighting.id} not found")
    service.update_sighting(sighting, user=app.current_event.get("user_id"))
    return Response(status_code=200, body=json.dumps(sighting.model_dump()), headers=headers)


@app.delete("/sightings/<id>")
def delete_sighting(id: str):
    logger.info(f"Delete sighting: {id}")
    if service.get_sighting_by_id(id, user=app.current_event.get("user_id")) is None:
        raise NotFoundError(f"Sighting with id {id} not found")
    service.delete_sighting(id, user=app.current_event.get("user_id"))
    return Response(status_code=204, headers=headers)


@app.get("/cache/invalidate")
def invalidate_cache():
    logger.info("Invalidate cache")
    service.invalidate_cache(user=app.current_event.get("user_id"))
    return Response(status_code=200, headers=headers)


# Ringing


@app.get("/ringing/<ring>")
def get_ringing_by_ring(ring: str) -> Ringing | None:
    logger.info(f"Get ringing by ring: {ring}")
    ringing = service.get_ringing_by_ring(ring, user=app.current_event.get("user_id"))
    if ringing is None:
        raise NotFoundError(f"Ringing with ring {ring} not found")
    return Response(status_code=200, body=json.dumps(ringing.model_dump()), headers=headers)


@app.post("/ringing")
def add_ringing():
    body: Optional[str] = app.current_event.body
    if body is None:
        raise BadRequestError("Request body is required")
    logger.info(f"Add ringing: {body}")
    try:
        ringing = Ringing(**json.loads(body))
        service.upsert_ringing(ringing, user=app.current_event.get("user_id"))
        return Response(status_code=201, body=json.dumps(ringing.model_dump()), headers=headers)
    except ValidationError as e:
        logger.error(f"Validation error adding ringing: {e}")
        raise BadRequestError(str(e))
    except Exception as e:
        logger.error(f"Error adding ringing: {e}")
        raise InternalServerError("An error occurred while adding the ringing")


@app.put("/ringing")
def update_ringing():
    body: Optional[str] = app.current_event.body
    if body is None:
        raise BadRequestError("Request body is required")
    logger.info(f"Update ringing: {body}")
    try:
        ringing = Ringing(**json.loads(body))
        if service.get_ringing_by_ring(ringing.ring, user=app.current_event.get("user_id")) is None:
            raise NotFoundError(f"Ringing with ring {ringing.ring} not found")
        service.upsert_ringing(ringing, user=app.current_event.get("user_id"))
        return Response(status_code=200, body=json.dumps(ringing.model_dump()), headers=headers)
    except ValidationError as e:
        logger.error(f"Validation error updating ringing: {e}")
        raise BadRequestError(str(e))
    except Exception as e:
        logger.error(f"Error updating ringing: {e}")
        raise InternalServerError("An error occurred while updating the ringing")


@app.delete("/ringing/<ring>")
def delete_ringing(ring: str):
    logger.info(f"Delete ringing: {ring}")
    if service.get_ringing_by_ring(ring, user=app.current_event.get("user_id")) is None:
        raise NotFoundError(f"Ringing with ring {ring} not found")
    service.delete_ringing(ring, user=app.current_event.get("user_id"))
    return Response(status_code=204, headers=headers)


# Places


@app.get("/places")
def get_place_name_list() -> list[str]:
    return Response(status_code=200, body=json.dumps(service.get_place_name_list()), headers=headers)


# Species


@app.get("/species")
def get_species_name_list() -> list[str]:
    return Response(
        status_code=200,
        body=json.dumps(service.get_species_name_list(user=app.current_event.get("user_id"))),
        headers=headers,
    )


# Dashboard


@app.get("/dashboard")
def get_dashboard() -> list[Sighting]:
    logger.info("Get dashboard")
    return Response(
        status_code=200,
        body=json.dumps(service.get_dashboard(user=app.current_event.get("user_id")).model_dump()),
        headers=headers,
    )


# Analytics


@app.get("/analytics/history/<ring>")
def get_all_sightings_from_ring(ring: str) -> list[Sighting]:
    logger.info(f"Get all history from ring: {ring}")
    return Response(
        status_code=200,
        body=json.dumps(service.get_all_sightings_from_ring(ring, user=app.current_event.get("user_id"))),
        headers=headers,
    )


@app.get("/analytics/groups/<ring>")
def get_groups_from_ring(ring: str) -> FriendResponse:
    logger.info(f"Get groups from ring: {ring}")
    min_shared_sightings = int(app.current_event.query_string_parameters.get("min_shared_sightings", "2"))
    friends = service.get_friends_from_ring(
        ring, min_shared_sightings=min_shared_sightings, user=app.current_event.get("user_id")
    )
    return Response(status_code=200, body=json.dumps(friends.model_dump()), headers=headers)


# Report


@app.post("/report/shareable")
def post_shareable_report():
    body: Optional[str] = app.current_event.body
    html_content = None
    days = 30  # default value
    if body:
        try:
            request_data = json.loads(body)
            html_content = request_data.get("html")
            days = int(request_data.get("days", 30))
        except json.JSONDecodeError:
            raise BadRequestError("Invalid JSON in request body")
        except (TypeError, ValueError):
            raise BadRequestError("Invalid days value")

    try:
        assert 0 < days <= 365, "Days must be between 1 and 365"
        shareable_report = service.post_shareable_report(days, html_content, user=app.current_event.get("user_id"))
        return Response(status_code=200, body=json.dumps(shareable_report.model_dump(mode="json")), headers=headers)
    except AssertionError as e:
        raise BadRequestError(str(e))
    except Exception as e:
        logger.error(f"Error generating shareable report: {str(e)}")
        raise InternalServerError("Error generating shareable report")


# Seasonal Analysis


@app.get("/seasonal-analysis")
def get_seasonal_analysis() -> SeasonalAnalysis:
    return Response(
        status_code=200,
        body=json.dumps(service.get_seasonal_analysis(user=app.current_event.get("user_id")).model_dump()),
        headers=headers,
    )


# Family Tree


@app.get("/family/<ring>")
def get_family_by_ring(ring: str) -> FamilyTreeEntry | None:
    logger.info(f"Get family for ring: {ring}")
    ft = service.get_family_tree_entry_by_ring(ring, user=app.current_event.get("user_id"))
    if ft is None:
        raise NotFoundError(f"Family for ring {ring} not found")
    return Response(status_code=200, body=json.dumps(ft.model_dump()), headers=headers)


@app.post("/family")
def create_family_tree_entry():
    """Create a new family tree entry"""
    body: Optional[str] = app.current_event.body
    if body is None:
        raise BadRequestError("Request body is required")

    logger.info(f"Create family tree entry: {body}")
    try:
        family_entry = FamilyTreeEntry(**json.loads(body))
        result = service.upsert_family_tree_entry(family_entry, user=app.current_event.get("user_id"))
        return Response(status_code=201, body=json.dumps(result.model_dump()), headers=headers)
    except ValidationError as e:
        logger.error(f"Validation error creating family tree entry: {e}")
        raise BadRequestError(str(e))
    except Exception as e:
        logger.error(f"Error creating family tree entry: {e}")
        raise InternalServerError("An error occurred while creating the family tree entry")


@app.put("/family")
def update_family_tree_entry():
    """Update an existing family tree entry"""
    body: Optional[str] = app.current_event.body
    if body is None:
        raise BadRequestError("Request body is required")

    logger.info(f"Update family tree entry: {body}")
    try:
        family_entry = FamilyTreeEntry(**json.loads(body))
        result = service.upsert_family_tree_entry(family_entry, user=app.current_event.get("user_id"))
        return Response(status_code=200, body=json.dumps(result.model_dump()), headers=headers)
    except ValidationError as e:
        logger.error(f"Validation error updating family tree entry: {e}")
        raise BadRequestError(str(e))
    except Exception as e:
        logger.error(f"Error updating family tree entry: {e}")
        raise InternalServerError("An error occurred while updating the family tree entry")


@app.delete("/family/<ring>")
def delete_family_tree_entry(ring: str):
    """Delete a family tree entry"""
    logger.info(f"Delete family tree entry for ring: {ring}")
    try:
        service.delete_family_tree_entry(ring, user=app.current_event.get("user_id"))
        return Response(status_code=204, headers=headers)
    except Exception as e:
        logger.error(f"Error deleting family tree entry: {e}")
        raise InternalServerError("An error occurred while deleting the family tree entry")


@app.post("/family/<ring>/partners")
def add_partner_relationship(ring: str):
    """Add a partner relationship to a bird's family tree"""
    body: Optional[str] = app.current_event.body
    if body is None:
        raise BadRequestError("Request body is required")

    logger.info(f"Add partner relationship for ring {ring}: {body}")
    try:
        request_data = json.loads(body)
        partner_ring = request_data.get("partner_ring")
        year = request_data.get("year")

        if not partner_ring:
            raise BadRequestError("partner_ring is required")
        if not year:
            raise BadRequestError("year is required")

        service.add_partner_to_family_tree_entry(ring, partner_ring, int(year), user=app.current_event.get("user_id"))
        return Response(
            status_code=201, body=json.dumps({"message": "Partner relationship added successfully"}), headers=headers
        )
    except json.JSONDecodeError:
        raise BadRequestError("Invalid JSON in request body")
    except ValueError as e:
        logger.error(f"Validation error adding partner relationship: {e}")
        raise BadRequestError(str(e))
    except Exception as e:
        logger.error(f"Error adding partner relationship: {e}")
        raise InternalServerError("An error occurred while adding the partner relationship")


@app.post("/family/<ring>/children")
def add_child_relationship(ring: str):
    """Add a parent-child relationship to the family tree"""
    body: Optional[str] = app.current_event.body
    if body is None:
        raise BadRequestError("Request body is required")

    logger.info(f"Add child relationship for parent {ring}: {body}")
    try:
        request_data = json.loads(body)
        child_ring = request_data.get("child_ring")
        year = request_data.get("year")
        sex = request_data.get("sex", "U")  # Default to unknown if not provided

        if not child_ring:
            raise BadRequestError("child_ring is required")
        if not year:
            raise BadRequestError("year is required")
        if sex not in ["M", "W", "U"]:
            raise BadRequestError("sex must be 'M', 'W', or 'U'")

        service.add_child_relationship(ring, child_ring, int(year), sex, user=app.current_event.get("user_id"))
        return Response(
            status_code=201, body=json.dumps({"message": "Child relationship added successfully"}), headers=headers
        )
    except json.JSONDecodeError:
        raise BadRequestError("Invalid JSON in request body")
    except ValueError as e:
        logger.error(f"Validation error adding child relationship: {e}")
        raise BadRequestError(str(e))
    except Exception as e:
        logger.error(f"Error adding child relationship: {e}")
        raise InternalServerError("An error occurred while adding the child relationship")


# Main


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Event: {event}")

    method = event["httpMethod"]
    path = event["path"]

    # For OPTIONS requests (preflight) - handle BEFORE any other checks
    if method == "OPTIONS":
        return {"statusCode": 200, "headers": headers, "body": ""}

    # Check if this request matches the Lambda's role (reader vs writer)
    is_reader_lambda = "ReaderFunction" in context.function_name
    is_read_request = is_read_operation(method, path)

    if is_reader_lambda != is_read_request:
        logger.warning(f"Request mismatch - Reader Lambda: {is_reader_lambda}, Read Request: {is_read_request}")
        return {
            "statusCode": 403,
            "headers": headers,
            "body": json.dumps({"message": "Operation not allowed on this endpoint"}),
        }

    # Skip authentication for health check
    if path == "/health":
        return app.resolve(event, context)

    # Extract and verify JWT token - ONLY for non-OPTIONS requests
    auth_header = event["headers"].get("authorization") or event["headers"].get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        # Fallback to API key for backwards compatibility during migration
        if "x-api-key" in event["headers"] and event["headers"]["x-api-key"] == os.environ.get("API_KEY"):
            logger.info("Using API key authentication (legacy)")
            event["user_id"] = "api_key_user"  # Default user for API key access
            event["user_context"] = {"user_id": "api_key_user", "auth_method": "api_key"}
        else:
            return {
                "statusCode": 401,
                "headers": headers,
                "body": json.dumps({"message": "Unauthorized - Bearer token required"}),
            }
    else:
        # JWT authentication
        token = auth_header.split(" ")[1]
        user_context = get_user_context_from_token(
            token,
            os.environ["USER_POOL_ID"],
            os.environ["USER_POOL_CLIENT_ID"],
            os.environ.get("AWS_REGION", "eu-central-1"),
        )

        if not user_context:
            return {"statusCode": 401, "headers": headers, "body": json.dumps({"message": "Invalid or expired token"})}

        # Add user context to event for use in handlers
        event["user_id"] = user_context["user_id"]
        event["user_context"] = user_context
        logger.info(f"Authenticated user: {user_context['user_id']}")

    try:
        return app.resolve(event, context)
    except Exception as e:
        logger.exception("Error processing request")
        return {"statusCode": 500, "headers": headers, "body": json.dumps({"message": str(e)})}


@app.get("/suggestions")
def get_suggestions():
    """Get all suggestion lists for autocomplete fields"""
    return Response(
        status_code=200,
        body=json.dumps(service.get_suggestion_lists(user=app.current_event.get("user_id"))),
        headers=headers,
    )
