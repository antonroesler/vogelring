from api import conf


def user_sighting_file(user: str) -> str:
    return f"{user}/{conf.SIGHTINGS_FILE}"
