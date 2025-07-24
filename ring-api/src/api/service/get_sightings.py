from datetime import date as _date
from api.db import loader
from api.models.sightings import Sighting
from api.utils import distance


def get_sighting_by_id(id: str, user: str) -> Sighting | None:
    """Returns sighting by id or None if sighting is not found."""
    return next((sighting for sighting in loader.get_sightings(user=user) if sighting.id == id), None)


def get_sightings(user: str) -> list[Sighting]:
    """Returns all sightings."""
    return loader.get_sightings(user=user)


def get_sightings_count(user: str) -> int:
    """Returns the total number of sightings."""
    return len(loader.get_sightings(user=user))


def get_sightings_by_species(species: str, user: str) -> list[Sighting]:
    """Returns all sightings for a given species."""
    return [sighting for sighting in loader.get_sightings(user=user) if sighting.species == species]


def get_sightings_by_ring(ring: str, user: str) -> list[Sighting]:
    """Returns all sightings for a given ring."""
    return [sighting for sighting in loader.get_sightings(user=user) if sighting.ring == ring]


def get_sightings_by_date(date: _date, user: str) -> list[Sighting]:
    """Returns all sightings for a given date."""
    return [sighting for sighting in loader.get_sightings(user=user) if sighting.date == date]


def get_sightings_by_date_range(start: _date, end: _date, user: str) -> list[Sighting]:
    """Returns all sightings for a given date range."""
    return [sighting for sighting in loader.get_sightings(user=user) if sighting.date and start <= sighting.date <= end]


def get_next_sighting_id(user: str) -> str:
    """Returns the next sighting id."""
    return str(len(loader.get_sightings(user=user)) + 1)


def get_sightings_by_radius(lat: float, lon: float, radius_m: int, user: str) -> list[Sighting]:
    """Returns all sightings within a given radius."""
    sightings_with_location = [
        sighting for sighting in loader.get_sightings(user=user) if sighting.lat and sighting.lon
    ]
    return [
        sighting for sighting in sightings_with_location if distance(sighting.lat, sighting.lon, lat, lon) <= radius_m
    ]


if __name__ == "__main__":
    valid_sighting_id = "a543c698-917c-4218-b385-9d78839aad18"
    print(get_sighting_by_id(valid_sighting_id, user="test"))
