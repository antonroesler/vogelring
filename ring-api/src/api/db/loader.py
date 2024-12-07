from api import conf
from api.db.io import get_reader, get_writer
from api.models.sightings import Sighting

cache = {}


def get_sightings() -> list[Sighting]:
    """Returns birds table as python dict. If files is not cached in the lambda function, it will be downloaded from S3."""
    if cache.get(conf.SIGHTINGS_FILE):
        return cache[conf.SIGHTINGS_FILE]
    cache[conf.SIGHTINGS_FILE] = get_reader()(conf.SIGHTINGS_FILE)
    return cache[conf.SIGHTINGS_FILE]


def save_sightings(data: list[Sighting] | None = None) -> None:
    """Save birds table from cache to S3."""
    assert conf.SIGHTINGS_FILE in cache, "Sightings file not cached"
    if data:
        cache[conf.SIGHTINGS_FILE] = data
    get_writer()(conf.SIGHTINGS_FILE, cache[conf.SIGHTINGS_FILE])


if __name__ == "__main__":
    print(get_sightings()[:10])
