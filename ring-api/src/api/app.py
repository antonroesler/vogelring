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
from api.version import __version__
from api import service
from api.models.sightings import BirdMeta, Sighting
from typing import Optional
import json


app = APIGatewayRestResolver(enable_validation=True)
logger = Logger()
metrics = Metrics(namespace="Powertools")

app.enable_swagger(path="/swagger")

headers = {
    "Access-Control-Allow-Origin": "https://vogelring.com",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token,Accept",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE,OPTIONS",
    "Access-Control-Allow-Credentials": "true",
    "Access-Control-Max-Age": "300",
}


@app.exception_handler(ValidationError)
def handle_validation_error(error: ValidationError):
    return Response(status_code=400, body=json.dumps(error.errors()), headers=headers)


@app.get("/health")
def health():
    logger.info("Health API - HTTP 200")
    return Response(status_code=200, body=json.dumps({"message": "healthy", "version": __version__}), headers=headers)


@app.get("/sightings/count")
def get_sightings_count() -> int:
    logger.info("Get sightings count")
    return Response(status_code=200, body=json.dumps(service.get_sightings_count()), headers=headers)


@app.get("/sightings/<id>")
def get_sighting_by_id(id: str) -> Sighting | None:
    logger.info(f"Get sighting by id: {id}")
    sighting = service.get_sighting_by_id(id)
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
    page = int(app.current_event.query_string_parameters.get("page", "1"))
    per_page = int(app.current_event.query_string_parameters.get("per_page", "100"))
    start_date = app.current_event.query_string_parameters.get("start_date", None)
    end_date = app.current_event.query_string_parameters.get("end_date", None)
    species = app.current_event.query_string_parameters.get("species", None)
    place = app.current_event.query_string_parameters.get("place", None)
    logger.info(f"Get sightings page {page} with {per_page} per page")

    sightings = service.get_sightings()

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
        status_code=200, body=json.dumps([sighting.model_dump() for sighting in sightings]), headers=headers
    )


@app.get("/birds/suggestions/<partial_reading>")
def get_bird_suggestions_by_partial_reading(partial_reading: str) -> list[BirdMeta]:
    logger.info(f"Get bird suggestions by partial reading: {partial_reading}")
    if partial_reading == "":
        raise BadRequestError("Partial reading is required")
    if not any([c in partial_reading for c in ["*", "…", "..."]]):
        raise BadRequestError("Partial reading must contain exactly one wildcard symbol: * or … or ...")
    suggestions = service.get_bird_suggestions_by_partial_reading(partial_reading)
    if suggestions is None:
        raise NotFoundError(f"No suggestions found for partial reading: {partial_reading}")
    return Response(status_code=200, body=json.dumps([bird.model_dump() for bird in suggestions]), headers=headers)


@app.get("/birds/<ring>")
def get_bird_by_ring(ring: str) -> BirdMeta | None:
    logger.info(f"Get bird by ring: {ring}")
    if ring == "suggestions":
        return get_bird_suggestions_by_partial_reading("")
    bird = service.get_bird_by_ring(ring)
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
        service.add_sighting(sighting)
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
    if service.get_sighting_by_id(sighting.id) is None:
        raise NotFoundError(f"Sighting with id {sighting.id} not found")
    service.update_sighting(sighting)
    return Response(status_code=200, body=json.dumps(sighting.model_dump()), headers=headers)


@app.delete("/sightings/<id>")
def delete_sighting(id: str):
    logger.info(f"Delete sighting: {id}")
    if service.get_sighting_by_id(id) is None:
        raise NotFoundError(f"Sighting with id {id} not found")
    service.delete_sighting(id)
    return Response(status_code=204, headers=headers)


@app.get("/cache/invalidate")
def invalidate_cache():
    logger.info("Invalidate cache")
    service.invalidate_cache()
    return Response(status_code=200, headers=headers)


# Analytics


@app.get("/analytics/history/<ring>")
def get_all_sightings_from_ring(ring: str) -> list[Sighting]:
    logger.info(f"Get all history from ring: {ring}")
    return Response(status_code=200, body=json.dumps(service.get_all_sightings_from_ring(ring)), headers=headers)


@app.get("/analytics/groups/<ring>")
def get_groups_from_ring(ring: str) -> FriendResponse:
    logger.info(f"Get groups from ring: {ring}")
    friends = service.get_friends_from_ring(ring)
    return Response(status_code=200, body=json.dumps(friends.model_dump()), headers=headers)


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Event: {event}")

    # For OPTIONS requests (preflight)
    if event["httpMethod"] == "OPTIONS":
        return Response(status_code=200, headers=headers, body="")

    return app.resolve(event, context)
