from typing import Counter
from api.service.get_sightings import get_sightings_by_ring, get_sightings
from api.models.sightings import BirdMeta, Partner


def get_bird_by_ring(ring: str) -> BirdMeta | None:
    """Return bird meta information by ring or None if bird is not found."""
    sightings = get_sightings_by_ring(ring)
    if not sightings:
        return None

    species_counts = Counter(sighting.species for sighting in sightings)
    most_likely_species, _ = species_counts.most_common(1)[0]
    other_species_identifications = {
        species: count
        for species, count in species_counts.items()
        if species != most_likely_species and species is not None
    }
    partners = [Partner(ring=sighting.ring, year=sighting.date.year) for sighting in sightings]
    partners = list(set(partners))

    last_seen = max(sightings, key=lambda sighting: sighting.date).date
    first_seen = min(sightings, key=lambda sighting: sighting.date).date

    return BirdMeta(
        species=most_likely_species,
        ring=ring,
        sighting_count=len(sightings),
        last_seen=last_seen,
        first_seen=first_seen,
        other_species_identifications=other_species_identifications,
        sightings=sightings,
        partners=partners,
    )


def get_unique_rings() -> list[str]:
    """Return a list of unique rings."""
    sightings = get_sightings()
    return list(set(sighting.ring for sighting in sightings if sighting.ring is not None))


def get_bird_suggestions_by_partial_reading(partial_reading: str) -> list[BirdMeta]:
    """Return a list of bird meta information suggestions by partial reading.
    Partial reading can be only front, back, outer or middle reading."""
    partial_reading = partial_reading.replace("...", "*").replace("…", "*")
    all_rings = get_unique_rings()

    # Case 1: Partial reading is outer reading *8043*
    if partial_reading.startswith("*") and partial_reading.endswith("*"):
        potential_rings = [ring for ring in all_rings if partial_reading.replace("*", "") in ring]
        return [get_bird_by_ring(ring) for ring in potential_rings]
    # Case 2: Partial reading is front reading 280*
    elif partial_reading.endswith("*"):
        potential_rings = [ring for ring in all_rings if ring.startswith(partial_reading[:-1])]
        return [get_bird_by_ring(ring) for ring in potential_rings]
    # Case 3: Partial reading is back reading *35
    elif partial_reading.startswith("*"):
        return [get_bird_by_ring(ring) for ring in all_rings if ring.endswith(partial_reading[1:])]
    # Case 4: Partial reading is middle reading 28*35
    elif "*" in partial_reading:
        start = partial_reading.split("*")[0]
        end = partial_reading.split("*")[-1]
        return [get_bird_by_ring(ring) for ring in all_rings if ring.startswith(start) and ring.endswith(end)]
    return [get_bird_by_ring(partial_reading)]


if __name__ == "__main__":
    print(get_bird_suggestions_by_partial_reading("27484*"))
