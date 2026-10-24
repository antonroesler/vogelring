"""Gruppen: saved, named, reusable selections of sightings (the old app's „Datasets“).

A group is a ``FilterSpec`` plus an optional explicit ring list and hand-picked exclusions, stored in the catalog
(kind ``group``). Groups compose with everything else through ``FilterSpec.groups``: a view, workbook tile or
pipeline step that names a group inherits its selection, several groups form a union, and the dimension ``group``
splits results by group so Ingo can compare them side by side.
"""

from __future__ import annotations

import contextvars
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from . import runtime
from .sources import SOURCES, FilterSpec, Source, SourceError, _in, compile_filters, filter_bits, get_source, ring_in_subquery

MAX_DEPTH = 3
_depth: contextvars.ContextVar[int] = contextvars.ContextVar("group_depth", default=0)

DEFAULT_COLORS = ["#00436C", "#228096", "#37906D", "#D07B4D", "#8E6C8A", "#C9A227", "#5B7DB1", "#A64D79"]
_HEX = re.compile(r"^#[0-9a-fA-F]{6}$")


class GroupError(ValueError):
    """German, user-facing."""


class GroupSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(..., min_length=1, max_length=120, description="Kurzer Name, z. B. „Graugänse Ostpark als Jungvögel beringt“.")
    description: str = Field("", description="Worum es bei der Gruppe geht (Alltagssprache).")
    scope: Literal["sightings", "birds"] = Field(
        "birds",
        description="Immer 'birds': Eine Gruppe ist eine Vogelgruppe – alle Sichtungen der Vögel, die mindestens eine passende Sichtung haben („Mausergäste Ostpark“ zeigt überall, wo diese Vögel sonst noch auftauchen). 'sightings' (nur die passenden Sichtungen) gibt es nur noch für alte Gruppen; für Sichtungsauswahlen nutzt man die Filter einer Ansicht.",
    )
    filters: FilterSpec = Field(default_factory=FilterSpec, description="Die gespeicherte Auswahl (wie in einer Ansicht); mit any_of/none_of für Oder- und Ausschluss-Logik.")
    ring_list: list[str] = Field(default_factory=list, description="Zusätzlich: nur diese Ringnummern (für Gruppen, die aus einer Ringliste bestehen).")
    excluded_ids: list[str] = Field(default_factory=list, description="Einzelne Sichtungen (IDs), die von Hand ausgeschlossen wurden.")
    color: str | None = Field(None, description="Hex-Farbe für Vergleiche, z. B. #228096.")
    tags: list[str] = Field(default_factory=list)

    @field_validator("name")
    @classmethod
    def _strip(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Name fehlt.")
        return v

    @field_validator("color")
    @classmethod
    def _color(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if not _HEX.match(v):
            raise ValueError("Farbe muss eine Hex-Farbe wie #228096 sein.")
        return v.upper()

    @field_validator("ring_list", "excluded_ids")
    @classmethod
    def _clean_list(cls, v: list[str]) -> list[str]:
        out: list[str] = []
        for x in v:
            s = str(x).strip()
            if s and s not in out:
                out.append(s)
        return out

    def is_empty(self) -> bool:
        return self.filters.is_empty() and not self.ring_list

    def describe(self) -> str:
        """German one-liner of the selection."""
        source = get_source("sightings")
        bits = list(filter_bits(self.filters, source))
        if self.ring_list:
            n = len(self.ring_list)
            bits.append(f"der Ringe {', '.join(self.ring_list)}" if n <= 5 else f"von {n} aufgelisteten Ringen")
        if self.scope == "birds":
            sel = "alle Sichtungen der Vögel mit mindestens einer Sichtung " + ", ".join(bits) if bits else "alle Sichtungen aller Vögel"
        else:
            sel = "Sichtungen " + ", ".join(bits) if bits else "alle Sichtungen"
        if self.excluded_ids:
            n = len(self.excluded_ids)
            sel += ", ohne einen von Hand ausgeschlossenen Eintrag" if n == 1 else f", ohne {n} von Hand ausgeschlossene Einträge"
        return sel


# ---------------------------------------------------------------- lookup


def resolve_group(ref: str) -> tuple[Any, GroupSpec]:
    """Catalog item + parsed spec for a group id or (case-insensitive) name."""
    cat = runtime.catalog()
    ref = (ref or "").strip()
    if not ref:
        raise SourceError("Gruppe fehlt.")
    item = None
    if cat.exists("group", ref):
        item = cat.get("group", ref)
    else:
        for cand in cat.list("group", limit=500, search=ref):
            if cand.title.strip().lower() == ref.lower():
                item = cand
                break
    if item is None:
        known = ", ".join(i.title for i in cat.list("group", limit=20)) or "–"
        raise SourceError(f"Unbekannte Gruppe „{ref}“. Bekannt: {known}.")
    try:
        return item, GroupSpec.model_validate(item.doc)
    except ValueError as exc:
        raise SourceError(f"Gruppe „{item.title}“ ist ungültig: {exc}") from exc


def group_titles(refs: list[str]) -> list[str]:
    out = []
    for r in refs:
        try:
            out.append(resolve_group(r)[0].title)
        except SourceError:
            out.append(r)
    return out


# ---------------------------------------------------------------- SQL


def defining_condition(source: Source, spec: GroupSpec) -> tuple[str, list[Any]]:
    """The group's own rule (filters AND ring list) over a source – for bird groups this is what makes a bird a member."""
    depth = _depth.get()
    if depth >= MAX_DEPTH:
        raise SourceError("Gruppen dürfen höchstens drei Ebenen tief ineinander verweisen.")
    token = _depth.set(depth + 1)
    try:
        where, params = compile_filters(source, spec.filters)
    finally:
        _depth.reset(token)
    parts = [] if where == "TRUE" else [where]
    if spec.ring_list:
        if not source.ring_column or not source.has(source.ring_column):
            raise SourceError(f"Ringliste der Gruppe ist für die Datenquelle „{source.label}“ nicht anwendbar.")
        parts.append(_in(source.ring_column, list(spec.ring_list), params))
    return ("(" + " AND ".join(parts) + ")" if parts else "TRUE"), params


def group_condition(source: Source, spec: GroupSpec, *, with_exclusions: bool = True) -> tuple[str, list[Any]]:
    """Boolean SQL for one group over a source.

    scope=sightings: rule AND NOT excluded. scope=birds: ring IN (birds with a sighting matching the rule) AND NOT excluded.
    """
    if spec.scope == "birds":
        s = SOURCES["sightings"]
        inner, params = defining_condition(s, spec)
        sub = f"(SELECT DISTINCT ring FROM ({s.base_sql}) b WHERE ring IS NOT NULL AND {inner})"
        cond, params = ring_in_subquery(source, sub, params, what="Vogelgruppe")
        parts = [cond]
    else:
        cond, params = defining_condition(source, spec)
        parts = [] if cond == "TRUE" else [cond]
    if with_exclusions and spec.excluded_ids and source.has("id"):
        parts.append("NOT (" + _in("id::text", list(spec.excluded_ids), params) + ")")
    if not parts:
        return "TRUE", params
    if len(parts) == 1 and parts[0].startswith("("):
        return parts[0], params
    return "(" + " AND ".join(parts) + ")", params


def group_union_sql(source: Source, refs: list[str]) -> tuple[str, list[Any]]:
    """OR of the named groups' conditions (used by FilterSpec.groups)."""
    conds: list[str] = []
    params: list[Any] = []
    for r in refs:
        _, spec = resolve_group(r)
        c, p = group_condition(source, spec)
        conds.append(c)
        params.extend(p)
    if not conds:
        return "TRUE", []
    return ("(" + " OR ".join(conds) + ")") if len(conds) > 1 else conds[0], params


def group_intersection_sql(source: Source, refs: list[str]) -> tuple[str, list[Any]]:
    """AND of the named groups' conditions (used by FilterSpec.all_groups)."""
    conds: list[str] = []
    params: list[Any] = []
    for r in refs:
        _, spec = resolve_group(r)
        c, p = group_condition(source, spec)
        conds.append(c)
        params.extend(p)
    if not conds:
        return "TRUE", []
    return ("(" + " AND ".join(conds) + ")") if len(conds) > 1 else conds[0], params


def group_case_sql(source: Source, refs: list[str]) -> tuple[str, list[Any]]:
    """CASE expression labelling each row with the first matching group's name (dimension „Gruppe“)."""
    whens: list[str] = []
    params: list[Any] = []
    for r in refs:
        item, spec = resolve_group(r)
        c, p = group_condition(source, spec)
        whens.append(f"WHEN {c} THEN %s")
        params.extend(p)
        params.append(item.title)
    return "CASE " + " ".join(whens) + " ELSE 'andere' END", params


def group_colors(refs: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i, r in enumerate(refs):
        try:
            item, spec = resolve_group(r)
        except SourceError:
            continue
        out[item.title] = spec.color or DEFAULT_COLORS[i % len(DEFAULT_COLORS)]
    return out


# ---------------------------------------------------------------- legacy import (Streamlit „Datasets“)


def legacy_id(name: str) -> str:
    return "grp_" + hashlib.sha1(name.strip().lower().encode("utf-8")).hexdigest()[:12]


def legacy_to_spec(doc: dict[str, Any]) -> tuple[GroupSpec, list[str]]:
    """Map a legacy dataset JSON to a GroupSpec; returns (spec, notes about filters that could not be mapped 1:1)."""
    f: dict[str, Any] = {}
    ring_list: list[str] = []
    notes: list[str] = []

    def add(key: str, values: list[Any]) -> None:
        f.setdefault(key, [])
        for v in values:
            if v not in f[key]:
                f[key].append(v)

    for flt in doc.get("filters") or []:
        t, col = flt.get("type"), flt.get("column")
        val = flt.get("value")
        vals = [v for v in (flt.get("values") or []) if v not in (None, "")]
        if t == "equals" and val not in (None, ""):
            vals = [val]
        if t in ("equals", "multi"):
            if not vals:
                notes.append(f"Leerer Filter auf „{col}“ übersprungen.")
                continue
            if col == "species":
                add("species", [str(v) for v in vals])
            elif col == "status":
                add("status", [str(v) for v in vals])
            elif col == "place":
                add("places", [str(v) for v in vals])
                notes.append(f"Ort „{', '.join(map(str, vals))}“ wird als Namensteil gesucht (früher: genauer Name).")
            elif col == "ringing_place":
                add("ringing_places", [str(v) for v in vals])
            elif col == "ringing_age":
                try:
                    add("ringing_age", [int(float(v)) for v in vals])
                except (TypeError, ValueError):
                    notes.append(f"Beringungsalter „{vals}“ nicht lesbar – übersprungen.")
            elif col == "ring":
                for v in vals:
                    s = str(v).strip()
                    if s and s not in ring_list:
                        ring_list.append(s)
            elif col == "melder":
                add("melder", [str(v) for v in vals])
            elif col == "age":
                try:
                    add("age", [int(float(v)) for v in vals])
                except (TypeError, ValueError):
                    notes.append(f"Alter „{vals}“ nicht lesbar – übersprungen.")
            else:
                notes.append(f"Filter „{t}“ auf „{col}“ ({vals}) hat keine Entsprechung – übersprungen.")
        elif t == "contains":
            s = str(val or "").strip().strip(".")
            if col == "ring" and s:
                add("ring_contains", [s])
            elif col == "place" and s:
                add("places", [s])
            elif col == "ringing_place" and s:
                add("ringing_places", [s])
            else:
                notes.append(f"Filter „enthält“ auf „{col}“ ({val!r}) hat keine Entsprechung – übersprungen.")
        elif t == "date_range":
            lo, hi = flt.get("min"), flt.get("max")
            if col != "date":
                notes.append(f"Datumsbereich auf „{col}“ hat keine Entsprechung – übersprungen.")
                continue
            if lo:
                f["date_from"] = str(lo)[:10]
            if hi:
                f["date_to"] = str(hi)[:10]
            if not lo and not hi:
                notes.append("Leerer Datumsbereich übersprungen (keine Einschränkung).")
        else:
            notes.append(f"Unbekannter Filtertyp „{t}“ auf „{col}“ – übersprungen.")

    try:
        filters = FilterSpec.model_validate(f)
    except ValueError as exc:
        raise GroupError(f"Filter der Gruppe „{doc.get('name')}“ ungültig: {exc}") from exc
    name = str(doc.get("name") or "").strip() or "Unbenannte Gruppe"
    spec = GroupSpec(
        name=name,
        description=str(doc.get("description") or "").strip(),
        filters=filters,
        ring_list=ring_list,
        excluded_ids=[str(x) for x in (doc.get("excluded_ids") or [])],
        tags=["Import"],
    )
    return spec, notes


def read_legacy_dir(directory: Path) -> list[tuple[str, dict[str, Any]]]:
    out = []
    for p in sorted(Path(directory).glob("*.json")):
        try:
            out.append((p.name, json.loads(p.read_text(encoding="utf-8"))))
        except (OSError, ValueError) as exc:
            raise GroupError(f"{p.name}: nicht lesbar ({exc})") from exc
    return out
