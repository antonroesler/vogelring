from api.db import dynamo
from api.models.ringing import Ringing


def get_ringing_by_ring(ring: str) -> Ringing | None:
    return dynamo.get_ringing_by_ring(ring)
