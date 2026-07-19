"""Tests for the RING place lookup + GPS-nearest "smart" fallback."""

from src.utils.ring_places import (
    lookup_place,
    names_overlap,
    smart_match_place,
)


# ---- explicit lookup ----

def test_explicit_lookup_hits_and_normalizes():
    p = lookup_place("F, Mainkai, Innenstadt")
    assert p is not None
    assert p.ring_place.startswith("Frankfurt, Mainkai")
    # Whitespace/case differences still resolve.
    assert lookup_place("  f,   mainkai,  innenstadt ") is not None


def test_explicit_lookup_miss():
    assert lookup_place("Nirgendwo, Irgendwas") is None


# ---- name overlap ----

def test_name_overlap_across_german_compound():
    # Vogelring writes one word, RING splits it — still a match.
    assert names_overlap("F, Bethmannweiher", "Frankfurt, Bethmann Weiher*[DEED, 5818]")


def test_name_overlap_rejects_unrelated():
    assert not names_overlap("F, Erlenbruch", "Frankfurt, Ostpark*[DEED, 5818)")


def test_name_overlap_ignores_generic_suffix():
    # Both end in "weiher" but the distinctive parts differ -> no match.
    assert not names_overlap(
        "F, Jacobiweiher", "Frankfurt, Rechneigrabenweiher*[DEED, 5818]"
    )


# ---- smart GPS-nearest fallback ----

def test_smart_match_hits_near_place_with_name_overlap():
    # Bethmannweiher sighting coords sit ~3 m from RING "Bethmann Weiher".
    m = smart_match_place("F, Bethmannweiher", 50.11775, 8.69082)
    assert m is not None
    assert "Bethmann" in m.ring_place


def test_smart_match_rejects_when_nearest_is_far_or_unrelated():
    # Erlenbruch: nearest RING place is ~1 km away and unrelated by name.
    assert smart_match_place("F, Erlenbruch", 50.12912, 8.72790) is None
    # Niederrad: candidates are all > 500 m away.
    assert smart_match_place("F, Niederrad", 50.08597, 8.63879) is None


def test_smart_match_requires_coordinates():
    assert smart_match_place("F, Bethmannweiher", None, None) is None
