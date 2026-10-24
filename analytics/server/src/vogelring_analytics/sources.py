"""Curated data sources and Tableau-style filters compiled to read-only SQL (German labels throughout).

A *source* is a SELECT over the vogelring views/tables that yields plain column names (computed columns such as
``km_from_ringing`` included), so filters, metrics and dimensions can refer to columns by name. Every generated
statement is a single parameterised SELECT and still passes ``db.guard_sql`` before execution.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from . import palette, runtime
from .db import _FORBIDDEN, _FORBIDDEN_TABLES, _strip_comments, _strip_literals
from .definitions import DefinitionError


class SourceError(ValueError):
    """Raised for filters/metrics/dimensions that make no sense for a source (German message)."""


# ---------------------------------------------------------------- sources

HAV = (
    "6371 * acos(LEAST(1, cos(radians({a_lat})) * cos(radians({b_lat})) * cos(radians({b_lon}) - radians({a_lon})) "
    "+ sin(radians({a_lat})) * sin(radians({b_lat}))))"
)
_KM_FROM_RINGING = HAV.format(a_lat="ringing_lat", a_lon="ringing_lon", b_lat="lat", b_lon="lon")

ColumnType = Literal["text", "int", "number", "date", "bool"]
ColumnRole = Literal["dimension", "measure", "id", "coord", "meta"]


@dataclass(frozen=True)
class Column:
    name: str
    label: str
    type: ColumnType = "text"
    role: ColumnRole = "dimension"
    filterable: bool = True
    sql: str | None = None  # expression inside the base query if not a plain column


@dataclass(frozen=True)
class Source:
    key: str
    label: str  # plural noun, e.g. "Sichtungen"
    description: str
    base_sql: str
    columns: tuple[Column, ...]
    default_date_column: str | None = None
    place_column: str | None = None
    ring_column: str | None = None
    species_column: str | None = None
    lat_column: str | None = None
    lon_column: str | None = None
    ringing_place_column: str | None = None
    ringing_age_column: str | None = None
    extra: dict[str, str | None] = field(default_factory=dict)  # status/age/sex/melder/year column names

    def column(self, name: str) -> Column | None:
        for c in self.columns:
            if c.name == name:
                return c
        return None

    def has(self, name: str | None) -> bool:
        return bool(name) and self.column(name) is not None  # type: ignore[arg-type]

    def col(self, kind: str) -> str | None:
        return self.extra.get(kind)



# ---------------------------------------------------------------- RING species codes
# ringings.species (and v_sightings.ringed_as_species) hold EURING codes such as "01660"; sightings hold German names.
# The official RING code→name list is bundled (same file as frontend/src/data/ring-species.json). Unknown values pass through.

_SPECIES_FILE = Path(__file__).parent / "data" / "ring_species.json"
RING_SPECIES: dict[str, str] = json.loads(_SPECIES_FILE.read_text(encoding="utf-8")) if _SPECIES_FILE.exists() else {}
_SPECIES_JSONB = "'" + json.dumps(RING_SPECIES, ensure_ascii=False, separators=(",", ":")).replace("'", "''").replace("%", "%%") + "'::jsonb"


def species_name_sql(column: str) -> str:
    """SQL expression turning a RING code column into the German species name (names and unknown codes pass through)."""
    if not RING_SPECIES:
        return column
    return f"COALESCE({_SPECIES_JSONB} ->> {column}, {column})"


def species_name(value: str | None) -> str | None:
    return RING_SPECIES.get(value, value) if value is not None else None

def _c(name: str, label: str, type: ColumnType = "text", role: ColumnRole = "dimension", filterable: bool = True) -> Column:
    return Column(name, label, type, role, filterable)


_SIGHTING_COLUMNS = (
    _c("id", "Sichtungs-ID", "text", "id", False),
    _c("ring", "Ring", "text", "id"),
    _c("reading", "Ablesung", "text", "meta", False),
    _c("species", "Art"),
    _c("date", "Datum", "date"),
    _c("place", "Ort"),
    _c("area", "Teilfläche"),
    _c("lat", "Breite", "number", "coord", False),
    _c("lon", "Länge", "number", "coord", False),
    _c("is_exact_location", "Koordinate exakt", "bool", "meta"),
    _c("age", "Alter", "int"),
    _c("sex", "Geschlecht", "int"),
    _c("status", "Status"),
    _c("melder", "Melder"),
    _c("large_group_size", "Große Gruppe", "int", "measure", False),
    _c("small_group_size", "Kleine Gruppe", "int", "measure", False),
    _c("breed_size", "Brutgröße", "int", "measure", False),
    _c("family_size", "Familiengröße", "int", "measure", False),
    _c("partner", "Partner", "text", "meta", False),
    _c("comment", "Kommentar", "text", "meta", False),
    _c("ringing_date", "Beringungsdatum", "date"),
    _c("ringing_place", "Beringungsort"),
    _c("ringing_lat", "Beringung Breite", "number", "coord", False),
    _c("ringing_lon", "Beringung Länge", "number", "coord", False),
    _c("ringer", "Beringer"),
    _c("ring_scheme", "Ringzentrale"),
    _c("ringing_age", "Alter bei Beringung", "int"),
    _c("ringed_as_species", "Art laut Beringung"),
    _c("km_from_ringing", "km vom Beringungsort", "number", "measure", False),
)

SOURCES: dict[str, Source] = {
    "sightings": Source(
        key="sightings",
        label="Sichtungen",
        description="Jede Ablesung eines beringten Vogels an einem Ort an einem Tag, mit den Beringungsdaten des Vogels.",
        base_sql=(
            "SELECT id, ring, reading, species, date, place, area, lat, lon, is_exact_location, age, sex, status, melder, "
            "large_group_size, small_group_size, breed_size, family_size, partner, comment, ringing_date, ringing_place, "
            "ringing_lat, ringing_lon, ringer, ring_scheme, ringing_age, " + species_name_sql("ringed_as_species") + " AS ringed_as_species, "
            f"CASE WHEN lat IS NULL OR lon IS NULL OR ringing_lat IS NULL OR ringing_lon IS NULL THEN NULL ELSE {_KM_FROM_RINGING} END AS km_from_ringing "
            "FROM v_sightings WHERE date IS NOT NULL"
        ),
        columns=_SIGHTING_COLUMNS,
        default_date_column="date",
        place_column="place",
        ring_column="ring",
        species_column="species",
        lat_column="lat",
        lon_column="lon",
        ringing_place_column="ringing_place",
        ringing_age_column="ringing_age",
        extra={"status": "status", "age": "age", "sex": "sex", "melder": "melder", "km": "km_from_ringing", "exact": "is_exact_location"},
    ),
    "ringings": Source(
        key="ringings",
        label="Beringungen",
        description="Eine Zeile je Beringung: wann, wo und von wem ein Ring angelegt wurde.",
        base_sql="SELECT ring, ring_scheme, " + species_name_sql("species") + " AS species, species AS species_code, date, place, lat, lon, ringer, age, sex, status, comment FROM ringings",
        columns=(
            _c("ring", "Ring", "text", "id"),
            _c("ring_scheme", "Ringzentrale"),
            _c("species", "Art"),
            _c("species_code", "Artcode (RING)", "text", "meta", False),
            _c("date", "Beringungsdatum", "date"),
            _c("place", "Beringungsort"),
            _c("lat", "Breite", "number", "coord", False),
            _c("lon", "Länge", "number", "coord", False),
            _c("ringer", "Beringer"),
            _c("age", "Alter bei Beringung", "int"),
            _c("sex", "Geschlecht", "int"),
            _c("status", "Status"),
            _c("comment", "Kommentar", "text", "meta", False),
        ),
        default_date_column="date",
        place_column="place",
        ring_column="ring",
        species_column="species",
        lat_column="lat",
        lon_column="lon",
        ringing_place_column="place",
        ringing_age_column="age",
        extra={"status": "status", "age": None, "sex": "sex", "melder": None, "km": None, "exact": None},
    ),
    "birds": Source(
        key="birds",
        label="Vögel",
        description="Eine Zeile je Ring: Beringungsdaten, Anzahl und Zeitraum der Sichtungen, Anzahl Orte, weitester Fund.",
        base_sql=(
            "SELECT ring, " + species_name_sql("MAX(ringed_as_species)") + " AS species, MAX(ringing_date) AS ringing_date, MAX(ringing_place) AS ringing_place, "
            "MAX(ringing_lat) AS ringing_lat, MAX(ringing_lon) AS ringing_lon, MAX(ringing_age) AS ringing_age, MAX(ringer) AS ringer, "
            "COUNT(date) AS sightings, MIN(date) AS first_sighting, MAX(date) AS last_sighting, COUNT(DISTINCT place) AS places, "
            "COUNT(DISTINCT EXTRACT(YEAR FROM date)) AS years_seen, MAX(km) AS max_km, (MAX(date) - MAX(ringing_date)) AS days_known "
            f"FROM (SELECT *, CASE WHEN lat IS NULL OR lon IS NULL OR ringing_lat IS NULL OR ringing_lon IS NULL THEN NULL ELSE {_KM_FROM_RINGING} END AS km "
            "FROM v_sightings) v WHERE ring IS NOT NULL GROUP BY ring"
        ),
        columns=(
            _c("ring", "Ring", "text", "id"),
            _c("species", "Art"),
            _c("ringing_date", "Beringungsdatum", "date"),
            _c("ringing_place", "Beringungsort"),
            _c("ringing_lat", "Beringung Breite", "number", "coord", False),
            _c("ringing_lon", "Beringung Länge", "number", "coord", False),
            _c("ringing_age", "Alter bei Beringung", "int"),
            _c("ringer", "Beringer"),
            _c("sightings", "Sichtungen", "int", "measure", False),
            _c("first_sighting", "Erste Sichtung", "date"),
            _c("last_sighting", "Letzte Sichtung", "date"),
            _c("places", "Anzahl Orte", "int", "measure", False),
            _c("years_seen", "Jahre mit Sichtung", "int", "measure", False),
            _c("max_km", "Weitester Fund (km)", "number", "measure", False),
            _c("days_known", "Tage zwischen Beringung und letzter Sichtung", "int", "measure", False),
        ),
        default_date_column="ringing_date",
        place_column="ringing_place",
        ring_column="ring",
        species_column="species",
        lat_column="ringing_lat",
        lon_column="ringing_lon",
        ringing_place_column="ringing_place",
        ringing_age_column="ringing_age",
        extra={"status": None, "age": None, "sex": None, "melder": None, "km": "max_km", "exact": None},
    ),
    "relationships": Source(
        key="relationships",
        label="Beziehungen",
        description="Verwandtschafts- und Partnerbeziehungen zwischen Vögeln (gerichtet), mit Jahr und Sicherheit.",
        base_sql="SELECT bird1_ring, bird2_ring, relationship_type, year, confidence, source, notes FROM bird_relationships",
        columns=(
            _c("bird1_ring", "Ring 1", "text", "id"),
            _c("bird2_ring", "Ring 2", "text", "id"),
            _c("relationship_type", "Beziehungsart"),
            _c("year", "Jahr", "int"),
            _c("confidence", "Sicherheit"),
            _c("source", "Quelle"),
            _c("notes", "Notizen", "text", "meta", False),
        ),
        default_date_column=None,
        extra={"status": None, "age": None, "sex": None, "melder": None, "km": None, "exact": None, "year": "year"},
    ),
}


def get_source(key: str) -> Source:
    try:
        return SOURCES[key]
    except KeyError as exc:
        raise SourceError(f"Unbekannte Datenquelle '{key}'. Verfügbar: {', '.join(SOURCES)}.") from exc


# ---------------------------------------------------------------- filters

SeasonKey = Literal["nov_jan", "feb_mar", "apr_jun", "jul_okt"]
SEASON_LABELS: dict[str, str] = {s["key"]: s["label"] for s in palette.SEASONS}
SEASON_MONTHS: dict[str, tuple[int, ...]] = {s["key"]: s["months"] for s in palette.SEASONS}
AGE_LABELS = palette.SIGHTING_AGE
SEX_LABELS = {0: "unbekannt", 1: "männlich", 2: "weiblich"}
STATUS_LABELS = palette.STATUS
RINGING_AGE_LABELS = palette.RINGING_AGE

_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class _Spec(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Around(_Spec):
    lat: float
    lon: float
    km: float = Field(5, gt=0, le=2000)


class FilterSpec(_Spec):
    species: list[str] = Field(default_factory=list, description="Arten (exakte Namen, z. B. 'Kanadagans').")
    places: list[str] = Field(default_factory=list, description="Orte: Teilstring im Ortsnamen, z. B. 'Ostpark'.")
    place_groups: list[str] = Field(default_factory=list, description="Gespeicherte Ortsgruppen (Definitionen, z. B. 'Nordufer').")
    ringing_places: list[str] = Field(default_factory=list, description="Beringungsorte (Teilstring).")
    rings: list[str] = Field(default_factory=list, description="Ringnummern (exakt).")
    ring_groups: list[str] = Field(default_factory=list, description="Gespeicherte Vogelgruppen (Definitionen).")
    ring_contains: list[str] = Field(default_factory=list, description="Ringnummer enthält diesen Text (z. B. 'W' für Neckar-Nilgänse).")
    groups: list[str] = Field(default_factory=list, description="Gespeicherte Gruppen (group_id oder Name): deren Filter, Ringliste und Ausschlüsse gelten; mehrere = Vereinigung.")
    exclude_ids: list[str] = Field(default_factory=list, description="Einzelne Einträge (Sichtungs-IDs) ausschließen.")
    date_from: str | None = Field(None, description="YYYY-MM-DD")
    date_to: str | None = Field(None, description="YYYY-MM-DD")
    months: list[int] = Field(default_factory=list, description="Monatsnummern 1–12.")
    seasons: list[SeasonKey] = Field(default_factory=list, description="Jahreszeiten nach Ingos Konvention.")
    periods: list[str] = Field(default_factory=list, description="Gespeicherte Zeiträume (Definitionen, z. B. 'Mauserzeit').")
    years: list[int] = Field(default_factory=list)
    year_from: int | None = None
    year_to: int | None = None
    status: list[str] = Field(default_factory=list, description="BV, MG, NB, RV, TF")
    age: list[int] = Field(default_factory=list, description="1 adult, 2 diesjährig, 3 vorjährig, 4 juvenil")
    sex: list[int] = Field(default_factory=list, description="0 unbekannt, 1 männlich, 2 weiblich")
    melder: list[str] = Field(default_factory=list)
    ringing_age: list[int] = Field(default_factory=list, description="Alterscode bei Beringung 1–8.")
    around: Around | None = Field(None, description="Umkreis um Koordinaten.")
    around_place: str | None = Field(None, description="Umkreis um einen Ort (Teilstring); Mittelpunkt = mittlere Koordinate der Sichtungen dort.")
    around_place_km: float = Field(5, gt=0, le=2000)
    only_with_coords: bool = False
    only_exact_location: bool = False
    exclude_places: list[str] = Field(default_factory=list, description="Orte (Teilstring) ausschließen.")
    custom_sql: str | None = Field(None, description="Nur für den Agenten: zusätzliche SQL-Bedingung über Spalten der Quelle.")

    def is_empty(self) -> bool:
        return self == FilterSpec()


def _check_custom_sql(fragment: str) -> str:
    cleaned = _strip_comments(fragment).strip()
    bare = _strip_literals(cleaned)
    if not cleaned or ";" in bare or "{{" in cleaned:
        raise SourceError("Zusätzliche Bedingung: kein ';' und keine {{…}} erlaubt.")
    if m := _FORBIDDEN.search(bare):
        raise SourceError(f"Zusätzliche Bedingung: Schlüsselwort '{m.group(0)}' ist nicht erlaubt.")
    if m := _FORBIDDEN_TABLES.search(bare):
        raise SourceError(f"Zusätzliche Bedingung: Zugriff auf '{m.group(0)}' ist nicht erlaubt.")
    return cleaned


def _need(source: Source, column: str | None, what: str) -> str:
    if not column or not source.has(column):
        raise SourceError(f"Filter „{what}“ ist für die Datenquelle „{source.label}“ nicht verfügbar.")
    return column


def _definition(name: str, kind: str):
    d = runtime.definitions().get(name)
    if d is None:
        known = ", ".join(x.name for x in runtime.definitions().list()) or "–"
        raise SourceError(f"Unbekannte Definition „{name}“. Bekannt: {known}.")
    if d.kind != kind:
        raise SourceError(f"Definition „{name}“ ist vom Typ {d.kind}, erwartet wurde {kind}.")
    return d


def _ilike_any(column: str, values: list[str], params: list[Any], negate: bool = False) -> str:
    parts = []
    for v in values:
        parts.append(f"{column} {'NOT ' if negate else ''}ILIKE %s")
        params.append("%" + v.strip().strip("%") + "%")
    joiner = " AND " if negate else " OR "
    return "(" + joiner.join(parts) + ")"


def _in(column: str, values: list[Any], params: list[Any]) -> str:
    params.extend(values)
    return f"{column} IN ({', '.join(['%s'] * len(values))})"


def _validate_dates(f: FilterSpec) -> None:
    for v in (f.date_from, f.date_to):
        if v and not _DATE_RE.match(v):
            raise SourceError(f"Datum „{v}“ muss die Form JJJJ-MM-TT haben.")
    bad = [m for m in f.months if not 1 <= m <= 12]
    if bad:
        raise SourceError(f"Ungültige Monate: {bad}.")


def compile_filters(source: Source, f: FilterSpec) -> tuple[str, list[Any]]:
    """Return a parameterised boolean SQL expression over the source's column names, plus its params."""
    _validate_dates(f)
    parts: list[str] = []
    params: list[Any] = []
    date_col = source.default_date_column
    place_col = source.place_column
    ring_col = source.ring_column

    if f.species:
        parts.append(_in(_need(source, source.species_column, "Art"), f.species, params))
    if f.places:
        parts.append(_ilike_any(_need(source, place_col, "Ort"), f.places, params))
    if f.exclude_places:
        parts.append(_ilike_any(_need(source, place_col, "Ort ausschließen"), f.exclude_places, params, negate=True))
    for name in f.place_groups:
        d = _definition(name, "place_group")
        try:
            parts.append(runtime.definitions().expand_one(d, _need(source, place_col, "Ortsgruppe")))
        except DefinitionError as exc:
            raise SourceError(str(exc)) from exc
    if f.ringing_places:
        parts.append(_ilike_any(_need(source, source.ringing_place_column, "Beringungsort"), f.ringing_places, params))

    if f.rings:
        rings = [r.strip() for r in f.rings if r.strip()]
        if source.key == "relationships":
            parts.append("(" + _in("bird1_ring", rings, params) + " OR " + _in("bird2_ring", rings, params) + ")")
        else:
            parts.append(_in(_need(source, ring_col, "Ring"), rings, params))
    for name in f.ring_groups:
        d = _definition(name, "ring_group")
        expand = runtime.definitions().expand_one
        if source.key == "relationships":
            parts.append("(" + expand(d, "bird1_ring") + " OR " + expand(d, "bird2_ring") + ")")
        else:
            parts.append(expand(d, _need(source, ring_col, "Vogelgruppe")))
    if f.ring_contains:
        parts.append(_ilike_any(_need(source, ring_col, "Ring enthält"), f.ring_contains, params))
    if f.groups:
        from .groups import group_union_sql  # lazy: groups.py builds on this module

        sql, gparams = group_union_sql(source, f.groups)
        parts.append(sql)
        params.extend(gparams)
    if f.exclude_ids:
        if not source.has("id"):
            raise SourceError(f"Filter „Einträge ausschließen“ ist für die Datenquelle „{source.label}“ nicht verfügbar.")
        ids = [str(i) for i in f.exclude_ids if str(i).strip()]
        if ids:
            parts.append("NOT (" + _in("id::text", ids, params) + ")")

    if f.date_from:
        parts.append(f"{_need(source, date_col, 'Datum')} >= %s::date")
        params.append(f.date_from)
    if f.date_to:
        parts.append(f"{_need(source, date_col, 'Datum')} <= %s::date")
        params.append(f.date_to)
    if f.months:
        parts.append(f"EXTRACT(MONTH FROM {_need(source, date_col, 'Monat')}) IN ({', '.join(str(m) for m in sorted(set(f.months)))})")
    if f.seasons:
        months = sorted({m for s in f.seasons for m in SEASON_MONTHS[s]})
        parts.append(f"EXTRACT(MONTH FROM {_need(source, date_col, 'Jahreszeit')}) IN ({', '.join(map(str, months))})")
    for name in f.periods:
        d = _definition(name, "period")
        parts.append(runtime.definitions().expand_one(d, _need(source, date_col, "Zeitraum")))

    year_expr = source.col("year") or (f"EXTRACT(YEAR FROM {date_col})" if date_col else None)
    if f.years:
        if not year_expr:
            raise SourceError(f"Filter „Jahr“ ist für die Datenquelle „{source.label}“ nicht verfügbar.")
        parts.append(f"{year_expr} IN ({', '.join(str(int(y)) for y in sorted(set(f.years)))})")
    if f.year_from is not None:
        if not year_expr:
            raise SourceError(f"Filter „Jahr“ ist für die Datenquelle „{source.label}“ nicht verfügbar.")
        parts.append(f"{year_expr} >= {int(f.year_from)}")
    if f.year_to is not None:
        if not year_expr:
            raise SourceError(f"Filter „Jahr“ ist für die Datenquelle „{source.label}“ nicht verfügbar.")
        parts.append(f"{year_expr} <= {int(f.year_to)}")

    if f.status:
        parts.append(_in(_need(source, source.col("status"), "Status"), f.status, params))
    if f.age:
        parts.append(_in(_need(source, source.col("age"), "Alter"), [int(a) for a in f.age], params))
    if f.sex:
        parts.append(_in(_need(source, source.col("sex"), "Geschlecht"), [int(s) for s in f.sex], params))
    if f.melder:
        parts.append(_in(_need(source, source.col("melder"), "Melder"), f.melder, params))
    if f.ringing_age:
        parts.append(_in(_need(source, source.ringing_age_column, "Alter bei Beringung"), [int(a) for a in f.ringing_age], params))

    lat, lon = source.lat_column, source.lon_column
    if f.around:
        _need(source, lat, "Umkreis")
        parts.append(f"({lat} IS NOT NULL AND {HAV.format(a_lat='%s', a_lon='%s', b_lat=lat, b_lon=lon)} <= %s)")
        params.extend([f.around.lat, f.around.lon, f.around.km])
    if f.around_place:
        _need(source, lat, "Umkreis um Ort")
        center_lat = "(SELECT AVG(lat) FROM v_sightings WHERE place ILIKE %s AND lat IS NOT NULL)"
        center_lon = "(SELECT AVG(lon) FROM v_sightings WHERE place ILIKE %s AND lon IS NOT NULL)"
        parts.append(f"({lat} IS NOT NULL AND {HAV.format(a_lat=center_lat, a_lon=center_lon, b_lat=lat, b_lon=lon)} <= %s)")
        pat = "%" + f.around_place.strip().strip("%") + "%"
        params.extend([pat, pat, f.around_place_km])
    if f.only_with_coords:
        _need(source, lat, "nur mit Koordinaten")
        parts.append(f"({lat} IS NOT NULL AND {lon} IS NOT NULL)")
    if f.only_exact_location:
        parts.append(f"{_need(source, source.col('exact'), 'nur exakte Koordinaten')} IS TRUE")
    if f.custom_sql:
        parts.append("(" + _check_custom_sql(f.custom_sql) + ")")

    return (" AND ".join(parts) if parts else "TRUE"), params


# ---------------------------------------------------------------- German description

_MONTHS = palette.MONTHS_DE_LONG


def _quote(values: list[str]) -> str:
    return " oder ".join(f"‚{v}‘" for v in values)


def _join(values: list[str], word: str = "und") -> str:
    values = [str(v) for v in values]
    if len(values) <= 1:
        return "".join(values)
    return ", ".join(values[:-1]) + f" {word} " + values[-1]


def _fmt_date(iso: str) -> str:
    y, m, d = iso.split("-")
    return f"{d}.{m}.{y}"


def _month_phrase(months: list[int]) -> str:
    ms = sorted(set(months))
    if len(ms) > 1 and ms == list(range(ms[0], ms[-1] + 1)):
        return f"{_MONTHS[ms[0] - 1]}–{_MONTHS[ms[-1] - 1]}"
    return _join([_MONTHS[m - 1] for m in ms])


def describe_filters(f: FilterSpec, source: Source) -> str:
    """Plain German sentence of the selection for non-technical readers."""
    subject = source.label
    bits: list[str] = []
    if f.species:
        bits.append(("der Art " if len(f.species) == 1 else "der Arten ") + _join(f.species))
    if f.rings:
        bits.append(f"der Ringe {_join(f.rings)}" if len(f.rings) <= 5 else f"von {len(f.rings)} ausgewählten Ringen")
    for g in f.ring_groups:
        bits.append(f"der Vogelgruppe ‚{g}‘")
    if f.ring_contains:
        bits.append("mit " + _join([f"‚{v}‘" for v in f.ring_contains], "oder") + " in der Ringnummer")
    if f.groups:
        from .groups import group_titles  # lazy

        names = group_titles(f.groups)
        bits.append(f"aus der Gruppe ‚{names[0]}‘" if len(names) == 1 else "aus den Gruppen " + _join([f"‚{n}‘" for n in names], "oder"))
    if f.places:
        bits.append(f"an Orten mit {_quote(f.places)} im Namen")
    for g in f.place_groups:
        bits.append(f"im Gebiet ‚{g}‘")
    if f.exclude_places:
        bits.append("ohne " + " und ".join(f"‚{v}‘" for v in f.exclude_places))
    if f.ringing_places:
        bits.append(f"beringt in {_quote(f.ringing_places)}")
    if f.around:
        bits.append(f"im Umkreis von {f.around.km:g} km um ({f.around.lat:.3f}, {f.around.lon:.3f})")
    if f.around_place:
        bits.append(f"im Umkreis von {f.around_place_km:g} km um ‚{f.around_place}‘")
    if f.date_from and f.date_to:
        bits.append(f"vom {_fmt_date(f.date_from)} bis {_fmt_date(f.date_to)}")
    elif f.date_from:
        bits.append(f"ab {_fmt_date(f.date_from)}")
    elif f.date_to:
        bits.append(f"bis {_fmt_date(f.date_to)}")
    if f.months:
        bits.append(f"in den Monaten {_month_phrase(f.months)}")
    if f.seasons:
        bits.append("in der Jahreszeit " + _join([SEASON_LABELS[s] for s in f.seasons], "oder"))
    for p in f.periods:
        bits.append(f"im Zeitraum ‚{p}‘")
    if f.years:
        ys = sorted(set(f.years))
        bits.append(f"im Jahr {ys[0]}" if len(ys) == 1 else f"in den Jahren {_join(ys)}")
    if f.year_from is not None and f.year_to is not None:
        bits.append(f"{f.year_from}–{f.year_to}")
    elif f.year_from is not None:
        bits.append(f"ab {f.year_from}")
    elif f.year_to is not None:
        bits.append(f"bis {f.year_to}")
    if f.status:
        bits.append("mit Status " + _join([STATUS_LABELS.get(s, s) for s in f.status], "oder"))
    if f.age:
        bits.append("Alter " + _join([AGE_LABELS.get(a, str(a)) for a in f.age], "oder"))
    if f.sex:
        bits.append("Geschlecht " + _join([SEX_LABELS.get(s, str(s)) for s in f.sex], "oder"))
    if f.melder:
        bits.append("gemeldet von " + _join(f.melder, "oder"))
    if f.ringing_age:
        bits.append("Alter bei Beringung " + _join([RINGING_AGE_LABELS.get(a, str(a)) for a in f.ringing_age], "oder"))
    if f.only_exact_location:
        bits.append("nur mit exakter Koordinate")
    elif f.only_with_coords:
        bits.append("nur mit Koordinaten")
    if f.custom_sql:
        bits.append("mit einer zusätzlichen Bedingung")
    if f.exclude_ids:
        n = len(f.exclude_ids)
        bits.append("ohne einen von Hand ausgeschlossenen Eintrag" if n == 1 else f"ohne {n} von Hand ausgeschlossene Einträge")
    if not bits:
        return f"alle {subject}"
    return f"{subject} {', '.join(bits)}"


# ---------------------------------------------------------------- metrics & dimensions


@dataclass(frozen=True)
class Metric:
    key: str
    label: str
    sql: str  # may contain {col}
    needs_column: bool = False
    requires: tuple[str, ...] = ()  # column names the source must have

    def label_for(self, column: str | None, source: Source | None = None) -> str:
        if self.needs_column and column:
            col = source.column(column) if source else None
            return self.label.format(col=col.label if col else column)
        return self.label


METRICS: dict[str, Metric] = {
    "sightings": Metric("sightings", "Anzahl Sichtungen", "COUNT(*)"),
    "birds": Metric("birds", "Anzahl verschiedener Vögel", "COUNT(DISTINCT ring)", requires=("ring",)),
    "observation_days": Metric("observation_days", "Anzahl Beobachtungstage", "COUNT(DISTINCT date)", requires=("date",)),
    "places": Metric("places", "Anzahl Orte", "COUNT(DISTINCT place)", requires=("place",)),
    "rows": Metric("rows", "Anzahl Zeilen", "COUNT(*)"),
    "sum": Metric("sum", "Summe {col}", "SUM({col})", True),
    "mean": Metric("mean", "Mittelwert {col}", "AVG({col})", True),
    "median": Metric("median", "Median {col}", "PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY {col})", True),
    "min": Metric("min", "Minimum {col}", "MIN({col})", True),
    "max": Metric("max", "Maximum {col}", "MAX({col})", True),
    "count_distinct": Metric("count_distinct", "Anzahl verschiedener {col}", "COUNT(DISTINCT {col})", True),
}

_SEASON_CASE = "CASE WHEN EXTRACT(MONTH FROM {date}) IN (11, 12, 1) THEN 'Nov–Jan' WHEN EXTRACT(MONTH FROM {date}) IN (2, 3) THEN 'Feb–Mär' WHEN EXTRACT(MONTH FROM {date}) IN (4, 5, 6) THEN 'Apr–Jun' ELSE 'Jul–Okt' END"
_SEASON_ORDER = "CASE WHEN EXTRACT(MONTH FROM {date}) IN (11, 12, 1) THEN 1 WHEN EXTRACT(MONTH FROM {date}) IN (2, 3) THEN 2 WHEN EXTRACT(MONTH FROM {date}) IN (4, 5, 6) THEN 3 ELSE 4 END"
_WEEKDAY_CASE = "(ARRAY['So', 'Mo', 'Di', 'Mi', 'Do', 'Fr', 'Sa'])[EXTRACT(DOW FROM {date})::int + 1]"
_WEEKDAY_ORDER = "((EXTRACT(DOW FROM {date})::int + 6) % 7)"


def _case(column: str, mapping: dict[int, str], default: str = "unbekannt") -> str:
    whens = " ".join(f"WHEN {k} THEN '{v}'" for k, v in mapping.items())
    return f"CASE {column} {whens} ELSE '{default}' END"


def _distance_case(col: str) -> str:
    return (
        f"CASE WHEN {col} IS NULL THEN 'ohne Koordinaten' WHEN {col} < 1 THEN '< 1 km' WHEN {col} < 5 THEN '1–5 km' "
        f"WHEN {col} < 20 THEN '5–20 km' WHEN {col} < 100 THEN '20–100 km' ELSE '> 100 km' END"
    )


def _distance_order(col: str) -> str:
    return f"CASE WHEN {col} IS NULL THEN 9 WHEN {col} < 1 THEN 1 WHEN {col} < 5 THEN 2 WHEN {col} < 20 THEN 3 WHEN {col} < 100 THEN 4 ELSE 5 END"


@dataclass(frozen=True)
class Dimension:
    key: str
    label: str
    sql: dict[str, str]  # source key → expression ({date} = default date column of the source)
    order_sql: dict[str, str] = field(default_factory=dict)  # optional sort expression per source
    is_month: bool = False
    is_time: bool = False
    text: bool = True

    @property
    def sources(self) -> tuple[str, ...]:
        return tuple(self.sql)

    def expr(self, source: Source) -> str:
        if source.key not in self.sql:
            raise SourceError(f"Aufteilung „{self.label}“ ist für die Datenquelle „{source.label}“ nicht verfügbar.")
        return self.sql[source.key].format(date=source.default_date_column or "date")

    def order_expr(self, source: Source) -> str | None:
        tpl = self.order_sql.get(source.key)
        return tpl.format(date=source.default_date_column or "date") if tpl else None


_DATED = ("sightings", "ringings", "birds")
GROUP_PLACEHOLDER = "__GROUP_CASE__"  # replaced in build_aggregate_sql by a CASE over the filters' groups
_BY_DATE = lambda expr: {k: expr for k in _DATED}  # noqa: E731

DIMENSIONS: dict[str, Dimension] = {
    "month": Dimension("month", "Monat", _BY_DATE("EXTRACT(MONTH FROM {date})::int"), is_month=True, text=False),
    "year": Dimension("year", "Jahr", {**_BY_DATE("EXTRACT(YEAR FROM {date})::int"), "relationships": "year"}, text=False),
    "year_month": Dimension("year_month", "Jahr-Monat", _BY_DATE("TO_CHAR({date}, 'YYYY-MM')"), is_time=True),
    "season": Dimension("season", "Jahreszeit", _BY_DATE(_SEASON_CASE), _BY_DATE(_SEASON_ORDER)),
    "weekday": Dimension("weekday", "Wochentag", _BY_DATE(_WEEKDAY_CASE), _BY_DATE(_WEEKDAY_ORDER)),
    "place": Dimension("place", "Ort", {"sightings": "place", "ringings": "place"}),
    "area": Dimension("area", "Teilfläche", {"sightings": "COALESCE(area, 'unbekannt')"}),
    "species": Dimension("species", "Art", {"sightings": "COALESCE(species, 'unbekannt')", "ringings": "COALESCE(species, 'unbekannt')", "birds": "COALESCE(species, 'unbekannt')"}),
    "ringed_as_species": Dimension("ringed_as_species", "Art laut Beringung", {"sightings": "COALESCE(ringed_as_species, 'unbekannt')"}),
    "status": Dimension("status", "Status", {"sightings": "COALESCE(status, 'unbekannt')", "ringings": "COALESCE(status, 'unbekannt')"}),
    "age": Dimension("age", "Alter", {"sightings": _case("age", AGE_LABELS)}, {"sightings": "COALESCE(age, 9)"}),
    "sex": Dimension("sex", "Geschlecht", {"sightings": _case("sex", SEX_LABELS), "ringings": _case("sex", SEX_LABELS)}, {"sightings": "COALESCE(sex, 9)", "ringings": "COALESCE(sex, 9)"}),
    "melder": Dimension("melder", "Melder", {"sightings": "COALESCE(melder, 'unbekannt')"}),
    "ringing_place": Dimension("ringing_place", "Beringungsort", {"sightings": "COALESCE(ringing_place, 'unbekannt')", "birds": "COALESCE(ringing_place, 'unbekannt')", "ringings": "place"}),
    "ringing_year": Dimension("ringing_year", "Beringungsjahr", {"sightings": "EXTRACT(YEAR FROM ringing_date)::int", "birds": "EXTRACT(YEAR FROM ringing_date)::int", "ringings": "EXTRACT(YEAR FROM date)::int"}, text=False),
    "ringing_age": Dimension("ringing_age", "Alter bei Beringung", {"sightings": _case("ringing_age", RINGING_AGE_LABELS), "birds": _case("ringing_age", RINGING_AGE_LABELS), "ringings": _case("age", RINGING_AGE_LABELS)}, {"sightings": "COALESCE(ringing_age, 9)", "birds": "COALESCE(ringing_age, 9)", "ringings": "COALESCE(age, 9)"}),
    "distance_class": Dimension("distance_class", "Entfernung zum Beringungsort", {"sightings": _distance_case("km_from_ringing"), "birds": _distance_case("max_km")}, {"sightings": _distance_order("km_from_ringing"), "birds": _distance_order("max_km")}),
    "ring": Dimension("ring", "Ring", {"sightings": "ring", "ringings": "ring", "birds": "ring"}),
    "group": Dimension("group", "Gruppe", {"sightings": GROUP_PLACEHOLDER, "ringings": GROUP_PLACEHOLDER, "birds": GROUP_PLACEHOLDER}),
    "relationship_type": Dimension("relationship_type", "Beziehungsart", {"relationships": "relationship_type"}),
    "ringer": Dimension("ringer", "Beringer", {"sightings": "COALESCE(ringer, 'unbekannt')", "ringings": "COALESCE(ringer, 'unbekannt')", "birds": "COALESCE(ringer, 'unbekannt')"}),
}


def get_metric(key: str) -> Metric:
    try:
        return METRICS[key]
    except KeyError as exc:
        raise SourceError(f"Unbekannte Kennzahl '{key}'. Verfügbar: {', '.join(METRICS)}.") from exc


def get_dimension(key: str) -> Dimension:
    try:
        return DIMENSIONS[key]
    except KeyError as exc:
        raise SourceError(f"Unbekannte Aufteilung '{key}'. Verfügbar: {', '.join(DIMENSIONS)}.") from exc


def metric_sql(source: Source, metric: Metric, column: str | None) -> str:
    for req in metric.requires:
        if not source.has(req):
            raise SourceError(f"Kennzahl „{metric.label}“ ist für die Datenquelle „{source.label}“ nicht verfügbar.")
    if metric.needs_column:
        if not column or not source.has(column):
            raise SourceError(f"Kennzahl „{metric.label.format(col='…')}“ braucht eine Spalte der Datenquelle „{source.label}“ (z. B. {', '.join(c.name for c in source.columns if c.role == 'measure') or 'keine vorhanden'}).")
        return metric.sql.format(col=column)
    return metric.sql


# ---------------------------------------------------------------- SQL builders


def build_aggregate_sql(source: Source, filters: FilterSpec, metric: str, metric_column: str | None, dimensions: list[str]) -> tuple[str, list[Any]]:
    """SELECT dim1 AS key1, …, <metric> AS value FROM (<base>) s WHERE <filters> GROUP BY … ORDER BY …"""
    m = get_metric(metric)
    where, params = compile_filters(source, filters)
    dims = [get_dimension(k) for k in dimensions]
    if len({d.key for d in dims}) != len(dims):
        raise SourceError("Jede Aufteilung darf nur einmal vorkommen.")
    select: list[str] = []
    pre_params: list[Any] = []
    for d in dims:
        expr = d.expr(source)
        if d.key == "group":
            from .groups import group_case_sql  # lazy

            if not filters.groups:
                raise SourceError("Aufteilung „Gruppe“ braucht mindestens eine Gruppe im Filter (groups).")
            expr, gp = group_case_sql(source, filters.groups)
            pre_params.extend(gp)
        select.append(f"{expr} AS {d.key}")
    select.append(f"{metric_sql(source, m, metric_column)} AS value")
    params = pre_params + params
    sql = f"SELECT {', '.join(select)} FROM ({source.base_sql}) s WHERE {where}"
    if dims:
        positions = [str(i + 1) for i in range(len(dims))]
        sql += " GROUP BY " + ", ".join(positions)
        order = [f"MIN({d.order_expr(source)})" if d.order_expr(source) else p for d, p in zip(dims, positions)]
        sql += " ORDER BY " + ", ".join(order)
    return sql, params


def build_rows_sql(source: Source, filters: FilterSpec, columns: list[str] | None = None, limit: int | None = None, order_by: str | None = None) -> tuple[str, list[Any]]:
    """Raw rows of a source (maps, tables, raw-row charts)."""
    where, params = compile_filters(source, filters)
    if columns:
        missing = [c for c in columns if not source.has(c)]
        if missing:
            raise SourceError(f"Unbekannte Spalten für „{source.label}“: {', '.join(missing)}.")
        select = ", ".join(columns)
    else:
        select = ", ".join(c.name for c in source.columns)
    sql = f"SELECT {select} FROM ({source.base_sql}) s WHERE {where}"
    order_col = order_by or source.default_date_column
    if order_col and source.has(order_col) and (not columns or order_col in columns):
        sql += f" ORDER BY {order_col}"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return sql, params


# ---------------------------------------------------------------- UI / agent description

FILTER_FIELDS: list[dict[str, Any]] = [
    {"name": "species", "label": "Art", "widget": "multiselect", "choices": "species"},
    {"name": "places", "label": "Ort (Namensteil)", "widget": "multiselect", "choices": "place", "free_text": True},
    {"name": "place_groups", "label": "Ortsgruppe (Definition)", "widget": "multiselect", "choices": "definition:place_group"},
    {"name": "exclude_places", "label": "Ort ausschließen", "widget": "multiselect", "choices": "place", "free_text": True},
    {"name": "ringing_places", "label": "Beringungsort (Namensteil)", "widget": "multiselect", "choices": "ringing_place", "free_text": True},
    {"name": "rings", "label": "Ring", "widget": "multiselect", "choices": "ring", "free_text": True},
    {"name": "ring_groups", "label": "Vogelgruppe (Definition)", "widget": "multiselect", "choices": "definition:ring_group"},
    {"name": "ring_contains", "label": "Ring enthält", "widget": "multiselect", "choices": "ring", "free_text": True},
    {"name": "groups", "label": "Gruppe", "widget": "multiselect", "choices": "group"},
    {"name": "date_from", "label": "Datum von", "widget": "date"},
    {"name": "date_to", "label": "Datum bis", "widget": "date"},
    {"name": "months", "label": "Monate", "widget": "months"},
    {"name": "seasons", "label": "Jahreszeit", "widget": "seasons", "options": [{"value": k, "label": v} for k, v in SEASON_LABELS.items()]},
    {"name": "periods", "label": "Zeitraum (Definition)", "widget": "multiselect", "choices": "definition:period"},
    {"name": "years", "label": "Jahre", "widget": "multiselect", "choices": "year"},
    {"name": "year_from", "label": "Jahr von", "widget": "number"},
    {"name": "year_to", "label": "Jahr bis", "widget": "number"},
    {"name": "status", "label": "Status", "widget": "multiselect", "options": [{"value": k, "label": f"{k} – {v}"} for k, v in STATUS_LABELS.items()]},
    {"name": "age", "label": "Alter", "widget": "multiselect", "options": [{"value": k, "label": v} for k, v in AGE_LABELS.items()]},
    {"name": "sex", "label": "Geschlecht", "widget": "multiselect", "options": [{"value": k, "label": v} for k, v in SEX_LABELS.items()]},
    {"name": "melder", "label": "Melder", "widget": "multiselect", "choices": "melder"},
    {"name": "ringing_age", "label": "Alter bei Beringung", "widget": "multiselect", "options": [{"value": k, "label": v} for k, v in RINGING_AGE_LABELS.items()]},
    {"name": "around_place", "label": "Umkreis um Ort", "widget": "radius", "km_field": "around_place_km"},
    {"name": "around", "label": "Umkreis um Koordinate", "widget": "radius_coords"},
    {"name": "only_with_coords", "label": "Nur mit Koordinaten", "widget": "checkbox"},
    {"name": "only_exact_location", "label": "Nur exakte Koordinaten", "widget": "checkbox"},
]

_FILTER_SUPPORT: dict[str, str | None] = {
    "species": "species_column", "places": "place_column", "place_groups": "place_column", "exclude_places": "place_column",
    "ringing_places": "ringing_place_column", "rings": "ring_column", "ring_groups": "ring_column", "ring_contains": "ring_column", "date_from": "default_date_column",
    "date_to": "default_date_column", "months": "default_date_column", "seasons": "default_date_column", "periods": "default_date_column",
    "ringing_age": "ringing_age_column", "around": "lat_column", "around_place": "lat_column", "only_with_coords": "lat_column",
}


def _filter_supported(source: Source, name: str) -> bool:
    if name in ("years", "year_from", "year_to"):
        return bool(source.default_date_column or source.col("year"))
    if name in ("status", "age", "sex", "melder"):
        return bool(source.col(name))
    if name == "only_exact_location":
        return bool(source.col("exact"))
    if name == "groups":
        return source.key != "relationships"
    if name == "exclude_ids":
        return source.has("id")
    attr = _FILTER_SUPPORT.get(name)
    if attr is None:
        return source.key == "relationships" and name == "rings" or name == "rings"
    return bool(getattr(source, attr))


def describe_sources() -> dict[str, Any]:
    """JSON description of sources, metrics, dimensions and filter widgets for the UI and the agent."""
    return {
        "sources": [
            {
                "key": s.key,
                "label": s.label,
                "description": s.description,
                "date_column": s.default_date_column,
                "columns": [{"name": c.name, "label": c.label, "type": c.type, "role": c.role, "filterable": c.filterable} for c in s.columns],
                "filters": [f["name"] for f in FILTER_FIELDS if _filter_supported(s, f["name"]) or (s.key == "relationships" and f["name"] == "rings")],
                "dimensions": [d.key for d in DIMENSIONS.values() if s.key in d.sources],
                "metrics": [m.key for m in METRICS.values() if all(s.has(r) for r in m.requires)],
            }
            for s in SOURCES.values()
        ],
        "metrics": [{"key": m.key, "label": m.label, "needs_column": m.needs_column} for m in METRICS.values()],
        "dimensions": [{"key": d.key, "label": d.label, "sources": list(d.sources), "is_month": d.is_month, "is_time": d.is_time} for d in DIMENSIONS.values()],
        "filters": FILTER_FIELDS,
        "seasons": [{"key": k, "label": v, "months": list(SEASON_MONTHS[k])} for k, v in SEASON_LABELS.items()],
    }


_CHOICE_LABELS: dict[str, dict[Any, str]] = {"age": AGE_LABELS, "sex": SEX_LABELS, "status": STATUS_LABELS, "ringing_age": RINGING_AGE_LABELS}


# which FilterSpec fields target a column – they are ignored while listing that column's own choices
_CHOICE_OWN_FIELDS: dict[str, tuple[str, ...]] = {
    "species": ("species",),
    "place": ("places", "exclude_places"),
    "ringing_place": ("ringing_places",),
    "ring": ("rings", "ring_contains", "ring_groups"),
    "melder": ("melder",),
    "year": ("years", "year_from", "year_to"),
    "status": ("status",),
    "age": ("age",),
    "sex": ("sex",),
    "ringing_age": ("ringing_age",),
}


def choices_context(column: str, filters: FilterSpec | None) -> FilterSpec | None:
    """The filters that should narrow a column's choice list: everything except the filters on that column itself."""
    if filters is None or filters.is_empty():
        return None
    drop = _CHOICE_OWN_FIELDS.get(column, (column,))
    data = filters.model_dump(exclude_defaults=True)
    for k in drop:
        data.pop(k, None)
    ctx = FilterSpec.model_validate(data)
    return None if ctx.is_empty() else ctx


async def choices(source_key: str, column: str, search: str = "", limit: int = 50, filters: FilterSpec | None = None) -> list[dict[str, Any]]:
    """Distinct values of a column with counts (for dropdowns); parameterised ILIKE search.

    With `filters`, the counts are those of rows matching all *other* active filters, so a dropdown shows how many
    results each choice would leave (Tableau-style) instead of global totals."""
    source = get_source(source_key)
    if column == "year" and source.default_date_column:
        expr = f"EXTRACT(YEAR FROM {source.default_date_column})::int"
    elif source.has(column):
        expr = column
    else:
        raise SourceError(f"Unbekannte Spalte „{column}“ für „{source.label}“.")
    params: list[Any] = []
    where = f"{expr} IS NOT NULL"
    ctx = choices_context(column, filters)
    if ctx is not None:
        cond, cparams = compile_filters(source, ctx)
        where += f" AND ({cond})"
        params.extend(cparams)
    if search:
        where += f" AND ({expr})::text ILIKE %s"
        params.append("%" + search.strip().strip("%") + "%")
    params.append(max(1, min(int(limit), 500)))
    sql = f"SELECT {expr} AS value, COUNT(*) AS n FROM ({source.base_sql}) s WHERE {where} GROUP BY 1 ORDER BY n DESC, 1 LIMIT %s"
    res = await runtime.database().query(sql, params=tuple(params))
    labels = _CHOICE_LABELS.get(column, {})
    out = []
    for value, n in res.rows:
        v = value.item() if hasattr(value, "item") else value
        if hasattr(v, "strftime"):
            v = v.strftime("%Y-%m-%d")
        out.append({"value": v, "label": labels.get(v, f"{v}" if not labels else str(v)), "count": int(n)})
    return out
