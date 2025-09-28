"""
Pydantic models for migration scripts
These mirror the models from the Lambda API
"""

from pydantic import BaseModel, Field, field_validator
from datetime import date as DateType
from uuid import uuid4
from enum import Enum
from typing import Literal, Optional, List
from decimal import Decimal


class BirdStatus(str, Enum):
    BV = "BV"  # Brutvogel
    MG = "MG"  # Mausergast
    NB = "NB"  # Nichtbrüter
    RV = "RV"  # Reviervogel
    TOTFUND = "TF"  # Totfund


class BirdAge(str, Enum):
    AD = "ad"  # Adult
    DJ = "dj"  # Juvenile
    VJ = "vj"  # Vorjährig
    JUV = "juv"  # Juvenile


class PairType(str, Enum):
    PAIRED = "x"  # verpaart
    FAMILY = "F"  # Familie
    SCHOOL = "S"  # Schule


class Ringing(BaseModel):
    """Ringing model for DynamoDB migration"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    ring: str
    ring_scheme: str
    species: str
    date: DateType
    place: str
    lat: float
    lon: float
    ringer: str
    sex: int
    age: int
    status: Optional[BirdStatus] = None

    @field_validator("lat", "lon", mode="before")
    @classmethod
    def convert_decimal_to_float(cls, v):
        """Convert DynamoDB Decimal to float"""
        if isinstance(v, Decimal):
            return float(v)
        return v


class FamilyPartner(BaseModel):
    ring: str
    year: int


class FamilyChild(BaseModel):
    ring: str
    year: Optional[int] = None


class FamilyParent(BaseModel):
    ring: str
    sex: Literal["M", "W", "U"]


class FamilyTreeEntry(BaseModel):
    """Family tree entry model for DynamoDB migration"""

    ring: str
    partners: List[FamilyPartner] = []
    children: List[FamilyChild] = []
    parents: List[FamilyParent] = []


class Sighting(BaseModel):
    """Sighting model for S3 pickle migration"""

    id: str = Field(default_factory=lambda: str(uuid4()))
    excel_id: Optional[int] = None
    comment: Optional[str] = None
    species: Optional[str] = None
    ring: Optional[str] = None
    reading: Optional[str] = None
    age: Optional[BirdAge] = None
    sex: Optional[Literal["M", "W"]] = None
    date: Optional[DateType] = None
    large_group_size: Optional[int] = None
    small_group_size: Optional[int] = None
    partner: Optional[str] = None
    breed_size: Optional[int] = None
    family_size: Optional[int] = None
    pair: Optional[PairType] = None
    status: Optional[BirdStatus] = None
    melder: Optional[str] = None
    melded: Optional[bool] = None
    place: Optional[str] = None
    area: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    is_exact_location: Optional[bool] = False
    habitat: Optional[str] = None
    field_fruit: Optional[str] = None

    @field_validator(
        "large_group_size",
        "small_group_size",
        "breed_size",
        "family_size",
        mode="before",
    )
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
