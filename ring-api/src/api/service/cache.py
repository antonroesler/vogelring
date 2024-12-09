from api import conf
from api.db.loader import cache


def invalidate_cache():
    cache[conf.SIGHTINGS_FILE] = None
