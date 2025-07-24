from api.db import loader
from api.models.sightings import Sighting
from api.models.responses import FriendResponse, AnalyticsBirdMeta, SeenStatus
from api.service.get_bird import get_bird_by_ring
from collections import defaultdict


def get_all_sightings_from_ring(ring: str, user: str) -> list[Sighting]:
    return sorted(
        [sighting for sighting in loader.get_sightings(user=user) if sighting.ring == ring], key=lambda x: x.date
    )


def get_friends_from_ring(
    ring: str,
    user: str,
    min_shared_sightings: int = 2,
) -> FriendResponse:
    sightings = get_all_sightings_from_ring(ring, user)
    place_dates = [(sighting.place, sighting.date) for sighting in sightings]
    seen_together = []
    # Get all other sightings that were one the same date and same place for any place date in place_dates
    friends = defaultdict(list)

    for sighting in loader.get_sightings(user=user):
        if (sighting.place, sighting.date) in place_dates and sighting.ring != ring and sighting.ring is not None:
            friends[sighting.ring].append(sighting.place)
            seen_together.append(sighting.id)

    # Filter friends with at least 2 shared sightings, then get top 10
    filtered_friends = {k: v for k, v in friends.items() if len(v) >= min_shared_sightings}
    top_friends = sorted(filtered_friends.items(), key=lambda x: len(x[1]), reverse=True)[:10]
    friends = [
        AnalyticsBirdMeta(
            **get_bird_by_ring(t_ring, user=user).model_dump(), count=len(friends[t_ring]), places=list(set(places))
        )
        for t_ring, places in top_friends
    ]
    bird = get_bird_by_ring(ring)

    # Get seen status for each sighting
    seen_status = {sighting.id: SeenStatus.CURRENT_BIRD for sighting in sightings}
    for friend in friends:
        for sighting in friend.sightings:
            seen_status[sighting.id] = (
                SeenStatus.SEEN_TOGETHER if sighting.id in seen_together else SeenStatus.SEEN_SEPARATE
            )
    print("Seen status:")
    print(seen_status)
    return FriendResponse(bird=bird, friends=friends, seen_status=seen_status)


if __name__ == "__main__":
    from pprint import pprint

    pprint(get_friends_from_ring("280705").model_dump())
