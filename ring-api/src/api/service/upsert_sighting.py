from api.db import loader
from api.models.sightings import Sighting


def add_sighting(sighting: Sighting):
    loader.get_sightings().append(sighting)
    loader.save_sightings()


def update_sighting(sighting: Sighting):
    data = loader.get_sightings()
    for i, s in enumerate(data):
        if s.id == sighting.id:
            data[i] = sighting
            break
    loader.save_sightings()


def delete_sighting(id: str):
    loader.save_sightings([s for s in loader.get_sightings() if s.id != id])
