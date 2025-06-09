from api.db import loader
from api.models.sightings import Sighting
from api.service.family import add_partner_relationship_from_sighting
from aws_lambda_powertools import Logger

logger = Logger()


def add_sighting(sighting: Sighting):
    logger.info(f"Adding sighting {sighting.id}")
    loader.get_sightings().append(sighting)
    loader.save_sightings()
    
    # Add partner relationship if partner is specified
    if sighting.ring and sighting.partner and sighting.date:
        try:
            add_partner_relationship_from_sighting(
                sighting.ring, 
                sighting.partner, 
                sighting.date.year
            )
            logger.info(f"Added partner relationship: {sighting.ring} <-> {sighting.partner} ({sighting.date.year})")
        except Exception as e:
            logger.error(f"Failed to add partner relationship for sighting {sighting.id}: {str(e)}")


def update_sighting(sighting: Sighting):
    logger.info(f"Updating sighting {sighting.id}")
    data = loader.get_sightings()
    old_sighting = None
    
    for i, s in enumerate(data):
        if s.id == sighting.id:
            old_sighting = s
            data[i] = sighting
            break
    
    loader.save_sightings()
    
    # Add partner relationship if partner is specified and this is a new partner relationship
    if sighting.ring and sighting.partner and sighting.date:
        # Only add if this is a new partner relationship (different from old one)
        if not old_sighting or old_sighting.partner != sighting.partner:
            try:
                add_partner_relationship_from_sighting(
                    sighting.ring, 
                    sighting.partner, 
                    sighting.date.year
                )
                logger.info(f"Added partner relationship: {sighting.ring} <-> {sighting.partner} ({sighting.date.year})")
            except Exception as e:
                logger.error(f"Failed to add partner relationship for sighting {sighting.id}: {str(e)}")


def delete_sighting(id: str):
    logger.info(f"Deleting sighting {id}")
    loader.save_sightings([s for s in loader.get_sightings() if s.id != id])