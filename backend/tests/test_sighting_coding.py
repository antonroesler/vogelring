"""
Tests for the shared sighting age/sex coding (migration mapping + export labels).
"""

import pytest

from src.utils.sighting_coding import (
    migrate_age,
    migrate_sex,
    ring_age_label,
    ring_sex_label,
)


class TestMigrateAge:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            (None, None),
            ("", None),
            ("  ", None),
            ("ad", 6),
            ("AD", 6),
            ("adult", 6),
            ("dj", 3),
            ("vj", 5),
            ("juv", 1),
            ("juvenil", 1),
            ("1", 1),
            ("2", 2),
            ("3", 3),
            ("6", 6),
            ("8", 8),
            ("weird", None),
        ],
    )
    def test_migrate_age(self, raw, expected):
        assert migrate_age(raw) == expected


class TestMigrateSex:
    @pytest.mark.parametrize(
        "raw,expected",
        [
            (None, None),
            ("", None),
            ("M", 1),
            ("m", 1),
            ("W", 2),
            ("w", 2),
            ("0", 0),
            ("1", 1),
            ("2", 2),
            ("x", None),
        ],
    )
    def test_migrate_sex(self, raw, expected):
        assert migrate_sex(raw) == expected


class TestExportLabels:
    def test_age_labels(self):
        assert ring_age_label(None) == "2 Fängling"  # empty -> Fängling for RING
        assert ring_age_label(1) == "1 Nestling"
        assert ring_age_label(3) == "3 Diesjährig"
        assert ring_age_label(6) == "6 Älter als vorjährig"
        assert ring_age_label(99) == "99"  # unknown code passes through

    def test_sex_labels(self):
        assert ring_sex_label(None) == "unbekannt"
        assert ring_sex_label(0) == "unbekannt"
        assert ring_sex_label(1) == "männlich"
        assert ring_sex_label(2) == "weiblich"
