from api import conf
from api.db.io import get_reader, get_writer, get_version_reader
from api.models.sightings import Sighting
from aws_lambda_powertools import Logger

logger = Logger()
cache = {}
current_version = None


def update_current_version(v: str) -> None:
    global current_version
    logger.info(f"Updating current version to {v}")
    current_version = v


def is_latest_version(file: str) -> bool:
    version = get_version_reader()(file)
    if version != current_version:
        logger.info(f"New version {version} detected for {file}, current version is {current_version}")
        return False
    logger.debug(f"File {file} is at latest version {current_version}")
    return True


def get_sightings() -> list[Sighting]:
    """Returns birds table as python dict. If files is not cached in the lambda function, it will be downloaded from S3."""
    if cache.get(conf.SIGHTINGS_FILE) and is_latest_version(conf.SIGHTINGS_FILE):
        logger.info(f"Returning {len(cache[conf.SIGHTINGS_FILE])} sightings from cache")
        return cache[conf.SIGHTINGS_FILE]
    logger.info(f"Loading sightings from {conf.SIGHTINGS_FILE}")
    cache[conf.SIGHTINGS_FILE], new_version = get_reader()(conf.SIGHTINGS_FILE)
    update_current_version(new_version)
    logger.info(f"Loaded {len(cache[conf.SIGHTINGS_FILE])} sightings from file")
    return cache[conf.SIGHTINGS_FILE]


def save_sightings(data: list[Sighting] | None = None) -> None:
    """Save birds table from cache to S3."""
    if conf.SIGHTINGS_FILE not in cache:
        logger.warning("Attempting to save sightings but file is not cached")
        raise AssertionError("Sightings file not cached")

    if data:
        logger.info(f"Updating cache with {len(data)} sightings")
        cache[conf.SIGHTINGS_FILE] = data

    logger.info(f"Saving {len(cache[conf.SIGHTINGS_FILE])} sightings to {conf.SIGHTINGS_FILE}")
    new_version = get_writer()(conf.SIGHTINGS_FILE, cache[conf.SIGHTINGS_FILE])
    update_current_version(new_version)
    logger.info(f"Successfully saved sightings with version {current_version}")


if __name__ == "__main__":
    print(get_sightings()[:10])
