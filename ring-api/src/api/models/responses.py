from pydantic import BaseModel
from api.models.sightings import BirdMeta


class AnalyticsBirdMeta(BirdMeta):
    count: int
    places: list[str]


class FriendResponse(BaseModel):
    bird: BirdMeta
    friends: list[AnalyticsBirdMeta]
