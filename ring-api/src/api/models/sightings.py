from pydantic import BaseModel, Field
from datetime import date as _date
from uuid import uuid4


class Sighting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    species: str | None = None
    ring: str | None = None
    reading: str | None = None
    date: _date | None = None
    place: str | None = None
    group_size: int | None = None
    comment: str | None = None
    melder: str | None = None
    melded: bool | None = None
    lan: float | None = None
    lon: float | None = None


class BirdMeta(BaseModel):
    species: str
    ring: str
    sighting_count: int
    last_seen: _date
    first_seen: _date
    other_species_identifications: dict[str, int]

    def __hash__(self):
        return hash(self.ring)

    def __eq__(self, other):
        if not isinstance(other, BirdMeta):
            return False
        return self.ring == other.ring
