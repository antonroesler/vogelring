from api.db import loader
from collections import Counter


def get_suggestion_lists() -> dict:
    """Returns lists of all suggestions for places, species, habitats, and melders. Ordered by frequency."""
    sightings = loader.get_sightings()

    # Helper function to count and sort values
    def get_sorted_values(field_getter) -> list[str]:
        values = [field_getter(s) for s in sightings if field_getter(s) and len(field_getter(s)) > 0]
        counts = Counter(values)
        return [value for value, _ in counts.most_common()]

    return {
        "places": get_sorted_values(lambda s: s.place),
        "species": get_sorted_values(lambda s: s.species),
        "habitats": get_sorted_values(lambda s: s.habitat),
        "melders": get_sorted_values(lambda s: s.melder),
        "field_fruits": get_sorted_values(lambda s: s.field_fruit),
    }
