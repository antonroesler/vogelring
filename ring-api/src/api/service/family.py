from typing import Literal
from api.db import dynamo
from api.models.family import FamilyChild, FamilyParent, FamilyPartner, FamilyTreeEntry
from api.utils import has_access


def get_family_tree_entry_by_ring(ring: str, user: str) -> FamilyTreeEntry | None:
    entry = dynamo.get_family_tree_entry_by_ring(ring)
    if entry is None:
        return None
    assert has_access(user, entry.ring), "User does not have access to this family tree entry"
    return entry


def delete_family_tree_entry(ring: str) -> None:
    """
    Deletes a full family tree entry from DynamoDB using its ring number.
    If the ring doesn't exist, the operation will still succeed.
    """
    dynamo.delete_family_tree_entry(ring)


def upsert_family_tree_entry(family_tree_entry: FamilyTreeEntry, user: str) -> FamilyTreeEntry:
    """
    Insert or update a family tree entry in DynamoDB.
    The ring number serves as the primary key, so this will overwrite any existing record with the same ring.
    """
    assert has_access(user, family_tree_entry.ring), "User does not have access to this family tree entry"
    dynamo.put_family_tree_entry(family_tree_entry)
    return family_tree_entry


def add_partner_to_family_tree_entry(ring: str, partner_ring: str, year: int, user: str) -> None:
    """
    Adds a partner to a family tree entry in DynamoDB.
    This creates a bidirectional relationship - both birds will have each other as partners.
    """
    for p1, p2 in [(ring, partner_ring), (partner_ring, ring)]:
        entry = get_family_tree_entry_by_ring(p1, user)
        if entry is None:
            entry = FamilyTreeEntry(ring=p1)

        # Check if this partner relationship already exists
        existing_partner = next((p for p in entry.partners if p.ring == p2 and p.year == year), None)
        if existing_partner is None:
            entry.partners.append(FamilyPartner(ring=p2, year=year))
            upsert_family_tree_entry(entry)


def add_child_relationship(
    parent_ring: str, child_ring: str, year: int, sex: Literal["M", "W", "U"], user: str
) -> None:
    """
    Adds a parent-child relationship to the family trees of both the parent and the child in DynamoDB.
    This creates a bidirectional relationship.
    """
    # Add child to parent's record
    parent_entry = get_family_tree_entry_by_ring(parent_ring, user)
    if parent_entry is None:
        parent_entry = FamilyTreeEntry(ring=parent_ring)

    # Check if this child relationship already exists
    existing_child = next((c for c in parent_entry.children if c.ring == child_ring), None)
    if existing_child is None:
        parent_entry.children.append(FamilyChild(ring=child_ring, year=year))
        upsert_family_tree_entry(parent_entry)

    # Add parent to child's record
    child_entry = get_family_tree_entry_by_ring(child_ring)
    if child_entry is None:
        child_entry = FamilyTreeEntry(ring=child_ring)

    # Check if this parent relationship already exists
    existing_parent = next((p for p in child_entry.parents if p.ring == parent_ring), None)
    if existing_parent is None:
        child_entry.parents.append(FamilyParent(ring=parent_ring, sex=sex))
        upsert_family_tree_entry(child_entry)


def add_partner_relationship_from_sighting(ring: str, partner_ring: str, year: int, user: str | None = None) -> None:
    """
    Helper function to add partner relationship when creating/updating sightings.
    This is called automatically when a sighting with a partner is created.
    """
    if ring and partner_ring and year:
        add_partner_to_family_tree_entry(ring, partner_ring, year, user)
