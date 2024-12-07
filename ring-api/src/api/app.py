from aws_lambda_powertools.event_handler import APIGatewayRestResolver, Response
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.exceptions import (
    NotFoundError,
    BadRequestError,
)
from aws_lambda_powertools import Metrics
from pydantic import ValidationError

from api.version import __version__
from api import service
from api.models.sightings import BirdMeta, Sighting
from typing import Optional
import json


app = APIGatewayRestResolver()
logger = Logger()
metrics = Metrics(namespace="Powertools")

app.enable_swagger(path="/swagger")


@app.exception_handler(ValidationError)
def handle_validation_error(error: ValidationError):
    return Response(status_code=400, body=error.errors())


@app.get("/health")
def health():
    logger.info("Health API - HTTP 200")
    return {"message": "healthy", "version": __version__}


@app.get("/sightings/count")
def get_sightings_count() -> int:
    logger.info("Get sightings count")
    return service.get_sightings_count()


@app.get("/sightings/<id>")
def get_sighting_by_id(id: str) -> Sighting | None:
    logger.info(f"Get sighting by id: {id}")
    sighting = service.get_sighting_by_id(id)
    if sighting is None:
        raise NotFoundError(f"Sighting with id {id} not found")
    return sighting.model_dump()


@app.get("/sightings")
def get_sightings() -> list[Sighting]:
    # Get query parameters from the request
    query_params = app.current_event.query_string_parameters or {}
    page = query_params.get("page", "1")
    per_page = query_params.get("per_page", "100")

    # Convert parameters to integers
    try:
        page = int(page)
        if page < 1:
            raise BadRequestError("Page must be a positive integer")
    except ValueError:
        raise BadRequestError("Invalid page parameter")
    per_page = int(per_page) if str(per_page).isdigit() else None

    logger.info(f"Get sightings page {page} with {per_page} per page")
    sightings = service.get_sightings(page, per_page)
    return [sighting.model_dump() for sighting in sightings]


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
    return [bird.model_dump() for bird in suggestions]


@app.get("/birds/<ring>")
def get_bird_by_ring(ring: str) -> BirdMeta | None:
    logger.info(f"Get bird by ring: {ring}")
    if ring == "suggestions":
        return get_bird_suggestions_by_partial_reading("")
    bird = service.get_bird_by_ring(ring)
    return bird.model_dump() if bird else Response(status_code=404)


@app.post("/sightings")
def add_sighting():
    body: Optional[str] = app.current_event.body  # raw str | None
    if body is None:
        raise BadRequestError("Request body is required")
    sighting = Sighting(**json.loads(body))
    logger.info(f"Add sighting: {sighting}")
    service.add_sighting(sighting)
    return Response(status_code=201, body=sighting.model_dump())


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
    return sighting.model_dump()


@app.delete("/sightings/<id>")
def delete_sighting(id: str):
    logger.info(f"Delete sighting: {id}")
    if service.get_sighting_by_id(id) is None:
        raise NotFoundError(f"Sighting with id {id} not found")
    service.delete_sighting(id)
    return Response(status_code=204)


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Event: {event}")
    return app.resolve(event, context)
