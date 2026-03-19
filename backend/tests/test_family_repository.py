"""
Unit tests for FamilyRepository — unidirectional relationship storage.

Tests verify:
- child_of type no longer exists
- create_relationship normalizes symmetric types (bird1_ring < bird2_ring)
- get_partners works for both directions
- get_parents uses parent_of with bird2_ring (not child_of)
- get_siblings works for both directions
- display_type helper returns correct perspective-based label
"""

import pytest
from uuid import uuid4
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.connection import Base
from src.database.family_models import BirdRelationship, RelationshipType
from src.database.family_repository import FamilyRepository


# ----------- Fixtures -----------

TEST_DATABASE_URL = "sqlite:///:memory:"

test_engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestSession = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

TEST_ORG_ID = str(uuid4())


@pytest.fixture()
def db():
    Base.metadata.create_all(bind=test_engine)
    session = TestSession()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture()
def repo(db):
    return FamilyRepository(db)


# ----------- RelationshipType enum -----------

def test_child_of_removed_from_enum():
    """child_of must not exist in RelationshipType enum."""
    types = [t.value for t in RelationshipType]
    assert "child_of" not in types


def test_required_types_exist():
    """breeding_partner, parent_of, sibling_of must exist."""
    values = {t.value for t in RelationshipType}
    assert "breeding_partner" in values
    assert "parent_of" in values
    assert "sibling_of" in values


# ----------- Symmetric normalization -----------

def test_create_breeding_partner_normalizes_order(repo):
    """breeding_partner should always store bird1_ring < bird2_ring."""
    rel = repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="Z999",
        bird2_ring="A001",
        relationship_type=RelationshipType.BREEDING_PARTNER,
        year=2026,
    )
    # After normalization: A001 < Z999 alphabetically
    assert rel.bird1_ring == "A001"
    assert rel.bird2_ring == "Z999"


def test_create_sibling_normalizes_order(repo):
    """sibling_of should always store bird1_ring < bird2_ring."""
    rel = repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="V345",
        bird2_ring="V123",
        relationship_type=RelationshipType.SIBLING_OF,
        year=2026,
    )
    assert rel.bird1_ring == "V123"
    assert rel.bird2_ring == "V345"


def test_create_parent_of_keeps_direction(repo):
    """parent_of should NOT be normalized — bird1 is always parent."""
    rel = repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="Z_PARENT",
        bird2_ring="A_CHILD",
        relationship_type=RelationshipType.PARENT_OF,
        year=2026,
    )
    # parent_of is NOT symmetric — keep original direction
    assert rel.bird1_ring == "Z_PARENT"
    assert rel.bird2_ring == "A_CHILD"


# ----------- get_partners (both directions) -----------

def test_get_partners_as_bird1(repo):
    """get_partners returns partner when bird is bird1."""
    repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="A001",
        bird2_ring="B002",
        relationship_type=RelationshipType.BREEDING_PARTNER,
        year=2026,
    )
    partners = repo.get_partners(TEST_ORG_ID, "A001")
    rings = [p["ring"] for p in partners]
    assert "B002" in rings


def test_get_partners_as_bird2(repo):
    """get_partners returns partner when bird is bird2."""
    repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="A001",
        bird2_ring="B002",
        relationship_type=RelationshipType.BREEDING_PARTNER,
        year=2026,
    )
    # B002 is bird2 — should still find A001 as their partner
    partners = repo.get_partners(TEST_ORG_ID, "B002")
    rings = [p["ring"] for p in partners]
    assert "A001" in rings


# ----------- get_parents (bird2 in parent_of) -----------

def test_get_parents_finds_parent_via_parent_of(repo):
    """get_parents returns parent from parent_of record where bird is bird2."""
    repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="PARENT_A",
        bird2_ring="CHILD_B",
        relationship_type=RelationshipType.PARENT_OF,
        year=2026,
    )
    parents = repo.get_parents(TEST_ORG_ID, "CHILD_B")
    rings = [p["ring"] for p in parents]
    assert "PARENT_A" in rings


def test_get_parents_does_not_find_child_as_parent(repo):
    """get_parents does not return the child as its own parent."""
    repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="PARENT_A",
        bird2_ring="CHILD_B",
        relationship_type=RelationshipType.PARENT_OF,
        year=2026,
    )
    parents = repo.get_parents(TEST_ORG_ID, "PARENT_A")
    rings = [p["ring"] for p in parents]
    assert "CHILD_B" not in rings
    assert "PARENT_A" not in rings


# ----------- get_children (bird1 in parent_of) -----------

def test_get_children_finds_child_via_parent_of(repo):
    """get_children returns child from parent_of where bird is bird1 (parent)."""
    repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="PARENT_A",
        bird2_ring="CHILD_B",
        relationship_type=RelationshipType.PARENT_OF,
        year=2026,
    )
    children = repo.get_children(TEST_ORG_ID, "PARENT_A")
    rings = [c["ring"] for c in children]
    assert "CHILD_B" in rings


# ----------- get_siblings (both directions) -----------

def test_get_siblings_as_bird1(repo):
    """get_siblings returns sibling when bird is bird1."""
    repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="A001",
        bird2_ring="B002",
        relationship_type=RelationshipType.SIBLING_OF,
        year=2026,
    )
    siblings = repo.get_siblings(TEST_ORG_ID, "A001")
    rings = [s["ring"] for s in siblings]
    assert "B002" in rings


def test_get_siblings_as_bird2(repo):
    """get_siblings returns sibling when bird is bird2."""
    repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="A001",
        bird2_ring="B002",
        relationship_type=RelationshipType.SIBLING_OF,
        year=2026,
    )
    siblings = repo.get_siblings(TEST_ORG_ID, "B002")
    rings = [s["ring"] for s in siblings]
    assert "A001" in rings


# ----------- display_type helper -----------

def test_display_type_parent_perspective(repo):
    """_get_display_type returns 'parent_of' when queried bird is bird1 (parent)."""
    rel = repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="PARENT_A",
        bird2_ring="CHILD_B",
        relationship_type=RelationshipType.PARENT_OF,
        year=2026,
    )
    assert repo._get_display_type(rel, "PARENT_A") == "parent_of"


def test_display_type_child_perspective(repo):
    """_get_display_type returns 'child_of' when queried bird is bird2 (child)."""
    rel = repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="PARENT_A",
        bird2_ring="CHILD_B",
        relationship_type=RelationshipType.PARENT_OF,
        year=2026,
    )
    assert repo._get_display_type(rel, "CHILD_B") == "child_of"


def test_display_type_partner(repo):
    """_get_display_type returns 'breeding_partner' from either direction."""
    rel = repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="A001",
        bird2_ring="B002",
        relationship_type=RelationshipType.BREEDING_PARTNER,
        year=2026,
    )
    assert repo._get_display_type(rel, "A001") == "breeding_partner"
    assert repo._get_display_type(rel, "B002") == "breeding_partner"


def test_display_type_sibling(repo):
    """_get_display_type returns 'sibling_of' from either direction."""
    rel = repo.create_relationship(
        org_id=TEST_ORG_ID,
        bird1_ring="A001",
        bird2_ring="B002",
        relationship_type=RelationshipType.SIBLING_OF,
        year=2026,
    )
    assert repo._get_display_type(rel, "A001") == "sibling_of"
    assert repo._get_display_type(rel, "B002") == "sibling_of"
