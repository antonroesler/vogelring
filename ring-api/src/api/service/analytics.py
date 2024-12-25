from api.db import loader
from api.models.sightings import Sighting, BirdMeta
from api.models.responses import FriendResponse, AnalyticsBirdMeta
from api.service.get_bird import get_bird_by_ring
from collections import defaultdict


def get_all_sightings_from_ring(ring: str) -> list[Sighting]:
    return sorted([sighting for sighting in loader.get_sightings() if sighting.ring == ring], key=lambda x: x.date)


def get_friends_from_ring(ring: str, min_shared_sightings: int = 2) -> FriendResponse:
    sightings = get_all_sightings_from_ring(ring)
    place_dates = [(sighting.place, sighting.date) for sighting in sightings]
    # Get all other sightings that were one the same date and same place for any place date in place_dates
    friends = defaultdict(list)

    for sighting in loader.get_sightings():
        if (sighting.place, sighting.date) in place_dates and sighting.ring != ring:
            friends[sighting.ring].append(sighting.place)

    # Filter friends with at least 2 shared sightings, then get top 10
    filtered_friends = {k: v for k, v in friends.items() if len(v) >= min_shared_sightings}
    top_friends = sorted(filtered_friends.items(), key=lambda x: len(x[1]), reverse=True)[:10]

    return FriendResponse(
        bird=get_bird_by_ring(ring),
        friends=[
            AnalyticsBirdMeta(
                **get_bird_by_ring(t_ring).model_dump(), count=len(friends[t_ring]), places=list(set(places))
            )
            for t_ring, places in top_friends
        ],
    )


if __name__ == "__main__":
    from pprint import pprint

    pprint(get_friends_from_ring("280705").model_dump())
