from pydantic import BaseModel, Field
from datetime import date
from uuid import uuid4
from api.models.sightings import BirdStatus


class Ringing(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    ring: str
    ring_scheme: str
    species: str
    date: date
    place: str
    lat: float
    lon: float
    ringer: str
    sex: int
    age: int
    status: BirdStatus | None = None  # New optional field

    def model_dump(self, **kwargs):
        data = super().model_dump(**kwargs)
        # Convert date to ISO format string
        if data.get("date"):
            data["date"] = data["date"].isoformat()
        return data
