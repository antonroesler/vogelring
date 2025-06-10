from typing import Literal
from pydantic import BaseModel


class FamilyPartner(BaseModel):
    ring: str
    year: int


class FamilyChild(BaseModel):
    ring: str
    year: int | None = None  # Year of hatching


class FamilyParent(BaseModel):
    ring: str
    sex: Literal["M", "W", "U"]


class FamilyTreeEntry(BaseModel):
    """Stores relationship of a bird to its relatives"""

    ring: str
    partners: list[FamilyPartner] = list()
    children: list[FamilyChild] = list()
    parents: list[FamilyParent] = list()
