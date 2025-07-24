from api.db import loader
from collections import Counter


def get_species_name_list(user: str) -> list[str]:
    """Returns a list of all species names. Ordered by frequency of sightings."""
    sightings = loader.get_sightings(user=user)
    species_names = [sighting.species for sighting in sightings if sighting.species and len(sighting.species) > 0]
    species_counts = Counter(species_names)
    return [species for species, _ in species_counts.most_common()]
