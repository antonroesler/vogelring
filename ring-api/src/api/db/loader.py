from api.db.io import get_reader, get_writer, get_version_reader
from api.models.sightings import Sighting
from aws_lambda_powertools import Logger
import time
from api.utils import user_sighting_file

logger = Logger()
cache = {}
current_version = None
last_check = None


def update_current_version(v: str) -> None:
    global current_version
    logger.info(f"Updating current version to {v}")
    current_version = v


def is_latest_version(file: str) -> bool:
    global last_check
    if last_check is None or time.time() - last_check > 10:
        last_check = time.time()
        version = get_version_reader()(file)
        if version != current_version:
            logger.info(f"New version {version} detected for {file}, current version is {current_version}")
        return False
    logger.debug(f"File {file} is at latest version {current_version}")
    return True


def get_sightings(user: str) -> list[Sighting]:
    """Returns birds table as python dict. If files is not cached in the lambda function, it will be downloaded from S3."""
    if cache.get(user_sighting_file(user)) and is_latest_version(user_sighting_file(user)):
        logger.info(f"Returning {len(cache[user_sighting_file(user)])} sightings from cache")
        return cache[user_sighting_file(user)]
    logger.info(f"Loading sightings from {user_sighting_file(user)}")
    cache[user_sighting_file(user)], new_version = get_reader()(user_sighting_file(user))
    update_current_version(new_version)
    logger.info(f"Loaded {len(cache[user_sighting_file(user)])} sightings from file")
    return cache[user_sighting_file(user)]


def save_sightings(user: str, data: list[Sighting] | None = None) -> None:
    """Save birds table from cache to S3."""
    if user_sighting_file(user) not in cache:
        logger.warning("Attempting to save sightings but file is not cached")
        raise AssertionError("Sightings file not cached")

    if data:
        logger.info(f"Updating cache with {len(data)} sightings")
        cache[user_sighting_file(user)] = data

    logger.info(f"Saving {len(cache[user_sighting_file(user)])} sightings to {user_sighting_file(user)}")
    new_version = get_writer()(user_sighting_file(user), cache[user_sighting_file(user)])
    update_current_version(new_version)
    logger.info(f"Successfully saved sightings with version {current_version}")


if __name__ == "__main__":
    print(get_sightings(user="test  ")[:10])
