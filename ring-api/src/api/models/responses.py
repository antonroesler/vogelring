from pydantic import BaseModel
from api.models.sightings import BirdMeta
from enum import Enum


class SeenStatus(str, Enum):
    CURRENT_BIRD = "CURRENT_BIRD"
    SEEN_TOGETHER = "SEEN_TOGETHER"
    SEEN_SEPARATE = "SEEN_SEPARATE"


class AnalyticsBirdMeta(BirdMeta):
    count: int
    places: list[str]


class FriendResponse(BaseModel):
    bird: BirdMeta
    friends: list[AnalyticsBirdMeta]
    seen_status: dict[str, SeenStatus]  # Sighting id to seen status
