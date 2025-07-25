from pydantic import BaseModel, Field, field_serializer, field_validator
from datetime import date as _date
from uuid import uuid4
from enum import Enum
from typing import Literal


class BirdStatus(str, Enum):
    BV = "BV"  # Brutvogel
    MG = "MG"  # Mausergast
    NB = "NB"  # Nichtbrüter
    RV = "RV"  # Reviervogel


class BirdAge(str, Enum):
    AD = "ad"  # Adult
    DJ = "dj"  # Juvenile
    VJ = "vj"  # Vorjährig
    JUV = "juv"  # Juvenile


class PairType(str, Enum):
    PAIRED = "x"  # verpaart
    FAMILY = "F"  # Familie
    SCHOOL = "S"  # Schule


class Sighting(BaseModel):
    # General
    id: str = Field(default_factory=lambda: str(uuid4()))
    excel_id: int | None = None
    comment: str | None = None

    # Bird
    species: str | None = None
    ring: str | None = None
    reading: str | None = None
    age: BirdAge | None = None
    sex: Literal["M", "W"] | None = None

    # Date
    date: _date | None = None

    # Group - with validators to handle empty strings
    large_group_size: int | None = None
    small_group_size: int | None = None
    partner: str | None = None  # Partner Ring
    breed_size: int | None = None
    family_size: int | None = None
    pair: PairType | None = None

    # Status
    status: BirdStatus | None = None

    # Meldung
    melder: str | None = None
    melded: bool | None = None

    # Place
    place: str | None = None  # Place Name
    area: str | None = None  # Special Area within the place
    lat: float | None = None
    lon: float | None = None
    is_exact_location: bool | None = False
    habitat: str | None = None  # Habitat Type
    field_fruit: str | None = None  # Field Fruit Type

    @field_validator("large_group_size", "small_group_size", "breed_size", "family_size", mode="before")
    @classmethod
    def validate_numeric_fields(cls, v):
        """Convert empty strings to None for numeric fields"""
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return None
            try:
                return int(v)
            except (ValueError, TypeError):
                return None
        return v

    @field_validator(
        "species",
        "ring",
        "reading",
        "partner",
        "comment",
        "melder",
        "place",
        "area",
        "habitat",
        "field_fruit",
        mode="before",
    )
    @classmethod
    def validate_string_fields(cls, v):
        """Convert empty strings to None for string fields"""
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            v = v.strip()
            if v == "":
                return None
        return v

    @field_serializer("date")
    def serialize_date(self, v: _date | None, _info):
        return v.isoformat() if v else None


class Partner(BaseModel):
    ring: str
    year: int

    def __hash__(self):
        return hash((self.ring, self.year))

    def __eq__(self, other):
        return self.ring == other.ring and self.year == other.year


class BirdMeta(BaseModel):
    species: str | None = None
    ring: str | None = None
    sighting_count: int | None = None
    last_seen: _date | None = None
    first_seen: _date | None = None
    other_species_identifications: dict[str, int] | None = None
    sightings: list[Sighting] | None = None
    partners: list[Partner] | None = None

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


class SuggestionBird(BaseModel):
    ring: str
    species: str
    sighting_count: int
    last_seen: _date
    first_seen: _date

    @field_serializer("last_seen")
    def serialize_last_seen(self, v: _date | None, _info):
        return v.isoformat() if v else None

    @field_serializer("first_seen")
    def serialize_first_seen(self, v: _date | None, _info):
        return v.isoformat() if v else None
