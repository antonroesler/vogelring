from typing import Literal
from api.db import dynamo
from api.models.family import FamilyChild, FamilyParent, FamilyPartner, FamilyTreeEntry
from datetime import date


def get_family_tree_entry_by_ring(ring: str) -> FamilyTreeEntry | None:
    return dynamo.get_family_tree_entry_by_ring(ring)


def delete_family_tree_entry(ring: str) -> None:
    """
    Deletes a full family tree entry from DynamoDB using its ring number.
    If the ring doesn't exist, the operation will still succeed.
    """
    dynamo.delete_family_tree_entry(ring)


def upsert_family_tree_entry(family_tree_entry: FamilyTreeEntry) -> FamilyTreeEntry:
    """
    Insert or update a family tree entry in DynamoDB.
    The ring number serves as the primary key, so this will overwrite any existing record with the same ring.
    """
    dynamo.put_family_tree_entry(family_tree_entry)
    return family_tree_entry


def add_partner_to_family_tree_entry(ring: str, partner_ring: str, year: int) -> None:
    """
    Adds a partner to a family tree entry in DynamoDB.
    """
    for p1, p2 in [(ring, partner_ring), (partner_ring, ring)]:
        entry = get_family_tree_entry_by_ring(p1)
        if entry is None:
            entry = FamilyTreeEntry(ring=p1)
        entry.partners.append(FamilyPartner(ring=p2, year=year))
        upsert_family_tree_entry(entry)


def add_child_relationship(parent_ring: str, child_ring: str, year: int, sex: Literal["M", "W", "U"]) -> None:
    """
    Adds a parent-child relationship to the family trees of both the parent and the child in DynamoDB.
    """
    parent_entry = get_family_tree_entry_by_ring(parent_ring)
    if parent_entry is None:
        parent_entry = FamilyTreeEntry(ring=parent_ring)
    parent_entry.children.append(FamilyChild(ring=child_ring, year=year))
    upsert_family_tree_entry(parent_entry)
    child_entry = get_family_tree_entry_by_ring(child_ring)
    if child_entry is None:
        child_entry = FamilyTreeEntry(ring=child_ring)
    child_entry.parents.append(FamilyParent(ring=parent_ring, sex=sex))
    upsert_family_tree_entry(child_entry)
