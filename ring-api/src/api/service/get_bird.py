from typing import Counter
from api.service.get_sightings import get_sightings_by_ring, get_sightings
from api.models.sightings import BirdMeta, Partner, SuggestionBird
from collections import defaultdict


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
    partners = [
        Partner(ring=sighting.partner, year=sighting.date.year)
        for sighting in sightings
        if sighting.partner is not None
    ]
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


def is_suggestion(partial_reading, ring):
    # Case 1: Partial reading is missing both outer endings *8043*
    if partial_reading.startswith("*") and partial_reading.endswith("*"):
        if partial_reading[1:-1] in ring:
            return True
    # Case 2: Partial reading is missing ending 280*
    elif partial_reading.endswith("*"):
        if ring.startswith(partial_reading[:-1]):
            return True
    # Case 3: Partial reading is missing starting *35
    elif partial_reading.startswith("*"):
        if ring.endswith(partial_reading[1:]):
            return True
    # Case 4: Partial reading is missing middle 28*35
    elif "*" in partial_reading:
        start, end = partial_reading.split("*")
        if ring.startswith(start) and ring.endswith(end):
            return True
    return False


def max_or_none(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return max(a, b)


def min_or_none(a, b):
    if a is None:
        return b
    if b is None:
        return a
    return min(a, b)


def get_bird_suggestions_by_partial_reading(partial_reading: str) -> list[SuggestionBird]:
    """Return a list of bird meta information suggestions by partial reading.
    Partial reading can be only front, back, outer or middle reading."""
    partial_reading = partial_reading.replace("...", "*").replace("…", "*")
    sightings = get_sightings()
    suggestions = dict()

    for sighting in sightings:
        if len(suggestions) >= 30:
            break
        if sighting.ring and is_suggestion(partial_reading, sighting.ring):
            if sighting.ring not in suggestions:
                suggestions[sighting.ring] = dict(
                    ring=sighting.ring,
                    species=[sighting.species],
                    sighting_count=1,
                    last_seen=sighting.date,
                    first_seen=sighting.date,
                )
            else:
                suggestions[sighting.ring]["sighting_count"] += 1
                suggestions[sighting.ring]["species"].append(sighting.species)
                suggestions[sighting.ring]["last_seen"] = max_or_none(
                    suggestions[sighting.ring]["last_seen"], sighting.date
                )
                suggestions[sighting.ring]["first_seen"] = min_or_none(
                    suggestions[sighting.ring]["first_seen"], sighting.date
                )
    suggestion_birds = [
        SuggestionBird(
            ring=suggestion["ring"],
            species=max(suggestion["species"], key=suggestion["species"].count),
            sighting_count=suggestion["sighting_count"],
            last_seen=suggestion["last_seen"],
            first_seen=suggestion["first_seen"],
        )
        for suggestion in suggestions.values()
    ]
    return sorted(suggestion_birds, key=lambda suggestion: suggestion.sighting_count, reverse=True)


if __name__ == "__main__":
    print(get_bird_suggestions_by_partial_reading("*22"))
