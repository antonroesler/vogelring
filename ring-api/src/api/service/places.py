from api.db import loader
from collections import Counter


def get_place_name_list(user: str) -> list[str]:
    """Returns a list of all place names. Ordered by frequency of sightings."""
    sightings = loader.get_sightings(user=user)
    place_names = [sighting.place for sighting in sightings if sighting.place and len(sighting.place) > 0]
    place_counts = Counter(place_names)
    return [place for place, _ in place_counts.most_common()]
