"""
Sighting age/sex coding — the single source of truth for the RING (Vogelwarte)
EURING integer codes used by sightings.

Sightings historically stored age as German shorthand ("ad"/"dj"/"vj"/"juv")
and sex as "M"/"W". These are migrated to the same integer codes RING uses:

Age legend (EURING; same list the Ringing form uses):
    1 Nestling
    2 Fängling            (caught, age not determined / unknown)
    3 Diesjährig
    4 Nicht Diesjährig
    5 Vorjährig
    6 Älter als vorjährig
    7 3. Kalender Jahr
    8 Über 3 Jahre

Legacy Vogelring shorthand maps to codes (per Ingo, the data owner):
    Adult -> 6, Diesjährig -> 3, Vorjährig -> 5, Juvenil -> 1

Sex:
    0 unbekannt, 1 männlich, 2 weiblich

NULL age is left as NULL in the database (no age recorded) but is exported as
"2 Fängling" for RING.
"""

from __future__ import annotations

from enum import IntEnum


class SightingAge(IntEnum):
    NESTLING = 1
    FAENGLING = 2
    DIESJAEHRIG = 3
    NICHT_DIESJAEHRIG = 4
    VORJAEHRIG = 5
    AELTER_ALS_VORJAEHRIG = 6
    DRITTES_KALENDERJAHR = 7
    UEBER_DREI_JAHRE = 8


class SightingSex(IntEnum):
    UNBEKANNT = 0
    MAENNLICH = 1
    WEIBLICH = 2


# code -> "<code> <label>" as shown in the UI and the RING export.
SIGHTING_AGE_LABELS: dict[int, str] = {
    1: "1 Nestling",
    2: "2 Fängling",
    3: "3 Diesjährig",
    4: "4 Nicht Diesjährig",
    5: "5 Vorjährig",
    6: "6 Älter als vorjährig",
    7: "7 3. Kalender Jahr",
    8: "8 Über 3 Jahre",
}

SIGHTING_SEX_LABELS: dict[int, str] = {
    0: "unbekannt",
    1: "männlich",
    2: "weiblich",
}

# Legacy string value (lower-cased, trimmed) -> integer code. Used to build the
# one-time data migration and to unit-test it. Order matters for SQL CASE output.
AGE_LEGACY_CASES: list[tuple[str, int]] = [
    ("ad", 6),
    ("adult", 6),
    ("dj", 3),
    ("diesjährig", 3),
    ("vj", 5),
    ("vorjährig", 5),
    ("juv", 1),
    ("juvenil", 1),
    ("1", 1),
    ("2", 2),
    ("3", 3),
    ("4", 4),
    ("5", 5),
    ("6", 6),
    ("7", 7),
    ("8", 8),
]

SEX_LEGACY_CASES: list[tuple[str, int]] = [
    ("m", 1),
    ("w", 2),
    ("männlich", 1),
    ("weiblich", 2),
    ("0", 0),
    ("1", 1),
    ("2", 2),
]

_AGE_LEGACY_MAP = dict(AGE_LEGACY_CASES)
_SEX_LEGACY_MAP = dict(SEX_LEGACY_CASES)


def migrate_age(raw: str | int | None) -> int | None:
    """Convert a legacy sighting age value to its integer code (None if unknown/blank)."""
    if raw is None:
        return None
    val = str(raw).strip().lower()
    if val == "":
        return None
    if val in _AGE_LEGACY_MAP:
        return _AGE_LEGACY_MAP[val]
    return None


def migrate_sex(raw: str | int | None) -> int | None:
    """Convert a legacy sighting sex value to its integer code (None if unknown/blank)."""
    if raw is None:
        return None
    val = str(raw).strip().lower()
    if val == "":
        return None
    return _SEX_LEGACY_MAP.get(val)


def ring_age_label(code: int | None) -> str:
    """Age label for the RING export. NULL is exported as '2 Fängling'."""
    if code is None:
        return SIGHTING_AGE_LABELS[2]
    return SIGHTING_AGE_LABELS.get(int(code), str(code))


def ring_sex_label(code: int | None) -> str:
    """Sex label for the RING export. NULL -> 'unbekannt'."""
    if code is None:
        return SIGHTING_SEX_LABELS[0]
    return SIGHTING_SEX_LABELS.get(int(code), "unbekannt")
