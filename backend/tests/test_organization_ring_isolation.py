"""The same birds can be copied between organizations without leaking joins."""

from uuid import uuid4

import pytest
from sqlalchemy.exc import IntegrityError

from src.database.models import Ringing, Sighting
from src.database.family_models import BirdRelationship, RelationshipType
from src.database.repositories import SightingRepository, RingingRepository
from src.api.services.suggestion_service import SuggestionService


def test_copied_birds_have_independent_ringings_and_enrichment(
    test_db, sample_ringing_data
):
    source, target = uuid4(), uuid4()
    a = Ringing(**sample_ringing_data, org_id=source)
    b = Ringing(**{**sample_ringing_data, "sex": 2}, org_id=target)
    sa = Sighting(ring=a.ring, org_id=source)
    sb = Sighting(ring=b.ring, org_id=target)
    test_db.add_all([a, b, sa, sb])
    test_db.commit()
    test_db.expire_all()

    assert sa.ringing_data.id == a.id
    assert sb.ringing_data.id == b.id
    assert [s.id for s in a.sightings] == [sa.id]
    assert [s.id for s in b.sightings] == [sb.id]
    enriched = SightingRepository(test_db).get_enriched_sightings(target, limit=1)
    assert len(enriched) == 1
    assert enriched[0].ringing_data.sex == 2

    test_db.add(Ringing(**sample_ringing_data, org_id=target))
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()


def test_other_organizations_ringing_is_not_attached(test_db, sample_ringing_data):
    a = Ringing(**sample_ringing_data, org_id=uuid4())
    s = Sighting(ring=a.ring, org_id=uuid4())
    test_db.add_all([a, s])
    test_db.commit()
    test_db.expire_all()
    assert s.ringing_data is None
    assert a.sightings == []
    assert (
        SightingRepository(test_db).get_enriched_sightings(s.org_id)[0].ringing_data
        is None
    )


def test_relationship_uniqueness_is_per_organization(test_db):
    source, target = uuid4(), uuid4()
    values = dict(
        bird1_ring="A",
        bird2_ring="B",
        relationship_type=RelationshipType.BREEDING_PARTNER,
        year=2026,
    )
    test_db.add_all(
        [
            BirdRelationship(**values, org_id=source),
            BirdRelationship(**values, org_id=target),
        ]
    )
    test_db.commit()
    assert test_db.query(BirdRelationship).count() == 2
    test_db.add(BirdRelationship(**values, org_id=target))
    with pytest.raises(IntegrityError):
        test_db.commit()
    test_db.rollback()


def test_statistics_and_cached_suggestions_are_scoped(test_db, sample_ringing_data):
    source, target = uuid4(), uuid4()
    test_db.add_all(
        [
            Ringing(
                **{**sample_ringing_data, "ringer": "Source Ringer"}, org_id=source
            ),
            Ringing(
                **{**sample_ringing_data, "ringer": "Target Ringer"}, org_id=target
            ),
            Sighting(
                org_id=source,
                ring="SOURCE",
                place="Source Place",
                species="Source Species",
            ),
            Sighting(
                org_id=target,
                ring="TARGET",
                place="Target Place",
                species="Target Species",
            ),
        ]
    )
    test_db.commit()
    sightings = SightingRepository(test_db)
    ringings = RingingRepository(test_db)
    for org, label in [(source, "Source"), (target, "Target"), (source, "Source")]:
        assert sightings.get_statistics(org)["total_sightings"] == 1
        assert ringings.get_statistics(org)["total_ringings"] == 1
        assert sightings.get_place_list(org) == [f"{label} Place"]
        assert sightings.get_species_list(org) == [f"{label} Species"]
        assert sightings.get_ring_list(org) == [label.upper()]
        assert ringings.get_ringer_list(org) == [f"{label} Ringer"]
        assert SuggestionService(test_db).get_ringer_list(org) == [f"{label} Ringer"]
        assert sightings.get_autocomplete_suggestions(org, "place", label) == [
            f"{label} Place"
        ]
        assert ringings.get_autocomplete_suggestions(org, "ringer", label) == [
            f"{label} Ringer"
        ]
