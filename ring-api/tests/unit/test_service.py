import os

os.environ["SIGHTINGS_FILE"] = "sightings.test.pkl"

from datetime import date as _date
from api import service
from api.models.sightings import BirdMeta, Sighting

valid_sighting_id = "05d0991f-fd82-4912-9a69-13b5ccf9c6ba"


def test_get_sighting_by_id():
    assert service.get_sighting_by_id(valid_sighting_id) is not None


def test_get_sighting_by_id_returns_sighting():
    assert isinstance(service.get_sighting_by_id(valid_sighting_id), Sighting)


def test_get_sighting_by_id_returns_none_if_sighting_not_found():
    assert service.get_sighting_by_id("not_found") is None


def test_get_sighting_by_id_returns_sighting_with_correct_id():
    assert service.get_sighting_by_id(valid_sighting_id).id == valid_sighting_id


def test_get_sightings():
    assert len(service.get_sightings()) > 0


def test_get_sightings_returns_list():
    assert isinstance(service.get_sightings(), list)


def test_get_sightings_returns_list_of_sightings():
    assert all(isinstance(sighting, Sighting) for sighting in service.get_sightings())


def test_get_sightings_paginated_returns_correct_number_of_sightings():
    assert len(service.get_sightings(page=1, per_page=10)) == 10
    assert len(service.get_sightings(page=2, per_page=10)) == 10
    assert len(service.get_sightings(page=3, per_page=10)) == 10


def test_get_sightings_paginated_returns_correct_number_of_sightings_with_custom_per_page():
    assert len(service.get_sightings(page=1, per_page=50)) == 50
    assert len(service.get_sightings(page=2, per_page=50)) == 50
    assert len(service.get_sightings(page=3, per_page=50)) == 50


def test_get_sightings_paginated_returns_correct_entries():
    full_sightings = service.get_sightings()
    assert service.get_sightings(page=1, per_page=100) == full_sightings[:100]
    assert service.get_sightings(page=2, per_page=100) == full_sightings[100:200]
    assert service.get_sightings(page=3, per_page=100) == full_sightings[200:300]


def test_get_sightings_paginated_returns_all_sightings_if_per_page_is_none():
    assert service.get_sightings(page=1, per_page=None) == service.get_sightings()


def test_get_sightings_count():
    assert service.get_sightings_count() == len(service.get_sightings())


def test_get_sightings_by_species():
    assert len(service.get_sightings_by_species("Kanadagans")) > 0


def test_get_sightings_by_species_returns_list():
    assert isinstance(service.get_sightings_by_species("Kanadagans"), list)


def test_get_sightings_by_species_returns_list_of_sightings():
    assert all(isinstance(sighting, Sighting) for sighting in service.get_sightings_by_species("Kanadagans"))


def test_get_sightings_by_species_returns_sightings_with_correct_species():
    assert all(sighting.species == "Kanadagans" for sighting in service.get_sightings_by_species("Kanadagans"))


def test_get_sightings_by_ring():
    assert len(service.get_sightings_by_ring("281935")) > 0


def test_get_sightings_by_ring_returns_list():
    assert isinstance(service.get_sightings_by_ring("281935"), list)


def test_get_sightings_by_ring_returns_list_of_sightings():
    assert all(isinstance(sighting, Sighting) for sighting in service.get_sightings_by_ring("281935"))


def test_get_sightings_by_date():
    assert len(service.get_sightings_by_date(_date(2019, 12, 15))) > 0


def test_get_sightings_by_date_returns_list():
    assert isinstance(service.get_sightings_by_date(_date(2019, 12, 15)), list)


def test_get_sightings_by_date_returns_list_of_sightings():
    assert all(isinstance(sighting, Sighting) for sighting in service.get_sightings_by_date(_date(2019, 12, 15)))


def test_get_sightings_by_date_range():
    assert len(service.get_sightings_by_date_range(_date(2019, 12, 1), _date(2019, 12, 31))) == 104


def test_get_sightings_by_date_range_returns_sightings_with_correct_date_range():
    sightings = service.get_sightings_by_date_range(_date(2019, 12, 1), _date(2019, 12, 31))
    assert all(sighting.date >= _date(2019, 12, 1) and sighting.date <= _date(2019, 12, 31) for sighting in sightings)


def test_get_sightings_by_date_range_returns_sightings_in_correct_order():
    sightings = service.get_sightings_by_date_range(_date(2019, 12, 1), _date(2019, 12, 31))
    assert all(sighting.date <= sighting.date for sighting in sightings)


def test_get_bird_meta_by_ring():
    assert service.get_bird_by_ring("281935") is not None


def test_get_bird_meta_by_ring_returns_none_if_bird_not_found():
    assert service.get_bird_by_ring("not_found") is None


def test_get_bird_meta_by_ring_returns_bird_meta():
    assert isinstance(service.get_bird_by_ring("281935"), BirdMeta)


def test_get_bird_meta_by_ring_returns_bird_meta_with_correct_info():
    bird = service.get_bird_by_ring("281935")
    assert bird.ring == "281935"
    assert bird.species == "Kanadagans"
    assert bird.sighting_count == 21
    assert bird.last_seen == _date(2024, 8, 4)
    assert bird.first_seen == _date(2020, 2, 15)
    assert bird.other_species_identifications == {}


def test_get_bird_suggestions_by_reading():
    suggestions = service.get_bird_suggestions_by_partial_reading("281935")
    assert len(suggestions) > 0
    assert all(isinstance(suggestion, BirdMeta) for suggestion in suggestions)
    assert all(suggestion.ring == "281935" for suggestion in suggestions)


def test_get_bird_suggestions_by_partial_back_reading():
    suggestions = service.get_bird_suggestions_by_partial_reading("...935")
    assert len(suggestions) > 0
    assert all(isinstance(suggestion, BirdMeta) for suggestion in suggestions)
    assert all(suggestion.ring.endswith("935") for suggestion in suggestions)


def test_get_bird_suggestions_by_partial_back_reading_triple_dot():
    suggestions = service.get_bird_suggestions_by_partial_reading("…935")
    assert len(suggestions) > 0
    assert all(isinstance(suggestion, BirdMeta) for suggestion in suggestions)
    assert all(suggestion.ring.endswith("935") for suggestion in suggestions)


def test_get_bird_suggestions_by_partial_front_reading():
    suggestions = service.get_bird_suggestions_by_partial_reading("28193...")
    assert len(suggestions) > 0
    assert all(isinstance(suggestion, BirdMeta) for suggestion in suggestions)
    assert all(suggestion.ring.startswith("28193") for suggestion in suggestions)


def test_get_bird_suggestions_by_partial_mid_reading():
    suggestions = service.get_bird_suggestions_by_partial_reading("281...35")
    assert len(suggestions) > 0
    assert all(isinstance(suggestion, BirdMeta) for suggestion in suggestions)
    assert all(suggestion.ring.startswith("281") and suggestion.ring.endswith("35") for suggestion in suggestions)


def test_get_bird_suggestions_by_partial_outer_reading():
    suggestions = service.get_bird_suggestions_by_partial_reading("...8193...")
    assert len(suggestions) > 0
    assert all(isinstance(suggestion, BirdMeta) for suggestion in suggestions)
    assert all("8193" in suggestion.ring for suggestion in suggestions)


def test_suggestion_count_each_bird_only_once():
    suggestions = service.get_bird_suggestions_by_partial_reading("27484*")
    assert len(suggestions) == len(set(suggestions))
