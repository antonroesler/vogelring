from pydantic import BaseModel, Field, field_serializer
from datetime import date as _date
from uuid import uuid4


class Sighting(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid4()))
    excel_id: int | None = None
    species: str | None = None
    ring: str | None = None
    reading: str | None = None
    date: _date | None = None
    place: str | None = None
    group_size: int | None = None
    comment: str | None = None
    melder: str | None = None
    melded: bool | None = None
    lat: float | None = None
    lon: float | None = None

    @field_serializer("date")
    def serialize_date(self, v: _date | None, _info):
        return v.isoformat() if v else None


class BirdMeta(BaseModel):
    species: str | None = None
    ring: str | None = None
    sighting_count: int | None = None
    last_seen: _date | None = None
    first_seen: _date | None = None
    other_species_identifications: dict[str, int] | None = None
    sightings: list[Sighting] | None = None

    def __hash__(self):
        return hash(self.ring)

    def __eq__(self, other):
        if not isinstance(other, BirdMeta):
            return False
        return self.ring == other.ring

    @field_serializer("last_seen")
    def serialize_last_seen(self, v: _date | None, _info):
        return v.isoformat() if v else None

    @field_serializer("first_seen")
    def serialize_first_seen(self, v: _date | None, _info):
        return v.isoformat() if v else None
