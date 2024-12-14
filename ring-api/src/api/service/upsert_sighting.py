from api.db import loader
from api.models.sightings import Sighting
from aws_lambda_powertools import Logger

logger = Logger()


def add_sighting(sighting: Sighting):
    logger.info(f"Adding sighting {sighting.id}")
    loader.get_sightings().append(sighting)
    loader.save_sightings()


def update_sighting(sighting: Sighting):
    logger.info(f"Updating sighting {sighting.id}")
    data = loader.get_sightings()
    for i, s in enumerate(data):
        if s.id == sighting.id:
            data[i] = sighting
            break
    loader.save_sightings()


def delete_sighting(id: str):
    logger.info(f"Deleting sighting {id}")
    loader.save_sightings([s for s in loader.get_sightings() if s.id != id])
