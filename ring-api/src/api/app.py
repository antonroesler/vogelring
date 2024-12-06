from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext
from aws_lambda_powertools.logging import correlation_paths
from aws_lambda_powertools import Logger
from aws_lambda_powertools.event_handler.exceptions import (
    NotFoundError,
)
from aws_lambda_powertools import Metrics

from api.version import __version__
from api import service
from api.models.sightings import BirdMeta, Sighting

app = APIGatewayRestResolver()
logger = Logger()
metrics = Metrics(namespace="Powertools")

app.enable_swagger(path="/swagger")


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
    return sighting


@app.get("/sightings")
def get_sightings() -> list[Sighting]:
    # Get query parameters from the request
    query_params = app.current_event.query_string_parameters or {}
    page = query_params.get("page", "1")
    per_page = query_params.get("per_page", None)

    # Convert parameters to integers
    page = int(page)
    per_page = int(per_page) if per_page else None

    logger.info(f"Get sightings page {page} with {per_page} per page")
    sightings = service.get_sightings(page, per_page)
    return sightings


@app.get("/birds/<ring>")
def get_bird_by_ring(ring: str) -> BirdMeta | None:
    logger.info(f"Get bird by ring: {ring}")
    bird = service.get_bird_by_ring(ring)
    return bird


@app.get("/birds/suggestions/<partial_reading>")
def get_bird_suggestions_by_partial_reading(partial_reading: str) -> list[BirdMeta]:
    logger.info(f"Get bird suggestions by partial reading: {partial_reading}")
    return service.get_bird_suggestions_by_partial_reading(partial_reading)


@logger.inject_lambda_context(correlation_id_path=correlation_paths.API_GATEWAY_REST)
@metrics.log_metrics(capture_cold_start_metric=True)
def lambda_handler(event: dict, context: LambdaContext) -> dict:
    logger.info(f"Event: {event}")
    return app.resolve(event, context)
