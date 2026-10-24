"""Gated, rollbackable writes to the Vogelring database.

Workflow: `plan()` is a dry run on the read-only pool – it resolves every affected row and records the exact
before/after values in a changeset (status `proposed`). `apply()` runs later, after the user approved the tool call
in the chat: one transaction on a separate, column-restricted role, re-checking that every row still looks like the
recorded `before` state. `rollback()` restores the recorded `before` values the same way. Nothing is ever deleted.
"""

from __future__ import annotations

import logging
import math
import re
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Annotated, Any, Literal, Union
from uuid import UUID

import pandas as pd
from psycopg_pool import AsyncConnectionPool
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from . import runtime
from .events import bus
from .settings import settings

log = logging.getLogger(__name__)


class WriteError(ValueError):
    """User-facing (German)."""


# ---------------------------------------------------------------- domain constants (mirror backend/src/utils/color_rings.py)

COLOR_PALETTE: dict[str, tuple[str, tuple[str, ...]]] = {
    "white": ("weiß", ("w", "weiss")),
    "black": ("schwarz", ("s", "n")),
    "red": ("rot", ("r",)),
    "orange": ("orange", ("o",)),
    "yellow": ("gelb", ("y", "ge")),
    "lightgreen": ("hellgrün", ("hg", "hellgruen", "lime")),
    "darkgreen": ("dunkelgrün", ("dg", "g", "gruen", "grün", "dunkelgruen")),
    "lightblue": ("hellblau", ("hb",)),
    "darkblue": ("dunkelblau", ("db", "b", "blau")),
    "violet": ("violett", ("v", "lila")),
    "pink": ("rosa", ("p", "pink")),
    "brown": ("braun", ("br",)),
    "grey": ("grau", ("gr",)),
}
_TOKEN_TO_COLOR: dict[str, str] = {}
for _key, (_label, _abbrevs) in COLOR_PALETTE.items():
    for _token in (_key, _label, *_abbrevs):
        _TOKEN_TO_COLOR[_token.lower()] = _key
MARK_TYPES = ("leg", "neck", "wing")
LEGS = ("left", "right")


def color_key(token: str | None, what: str = "Farbe") -> str | None:
    if token in (None, ""):
        return None
    key = _TOKEN_TO_COLOR.get(str(token).strip().lower())
    if not key:
        raise WriteError(f"Unbekannte {what} „{token}“. Erlaubt: " + ", ".join(f"{k} ({v[0]})" for k, v in COLOR_PALETTE.items()))
    return key


def color_label(key: str | None) -> str:
    return COLOR_PALETTE.get(key or "", (key or "leer", ()))[0] if key else "leer"


def normalize_code(code: str | None) -> str | None:
    if code is None:
        return None
    norm = re.sub(r"\s+", "", str(code)).upper()
    return norm or None


# ---------------------------------------------------------------- editable columns (whitelist = the only names that ever reach SQL)

EDITABLE: dict[str, dict[str, str]] = {
    "sightings": {
        "species": "text", "ring": "text", "reading": "text", "place": "text", "area": "text", "status": "text", "age": "int",
        "sex": "int", "melder": "text", "melded": "bool", "partner": "text", "pair": "text", "comment": "text", "habitat": "text",
        "field_fruit": "text", "color_ring_color": "color", "color_ring_text_color": "color", "color_ring_code": "code",
        "lat": "num", "lon": "num", "is_exact_location": "bool", "date": "date", "large_group_size": "int",
        "small_group_size": "int", "breed_size": "int", "family_size": "int",
    },
    "ringings": {"species": "text", "place": "text", "ringer": "text", "age": "int", "sex": "int", "status": "text", "comment": "text", "lat": "num", "lon": "num", "date": "date"},
    "color_rings": {"ring": "text", "ring_color": "color", "text_color": "color", "code": "code", "mark_type": "text", "leg": "text", "project": "text", "comment": "text"},
}
DISPLAY_COLS = {"sightings": ["date", "place", "species", "ring", "reading"], "ringings": ["ring", "date", "place", "species"], "color_rings": ["ring", "ring_color", "text_color", "code"]}
FIELD_LABELS = {
    "species": "Art", "ring": "Metallring", "reading": "Ablesung", "place": "Ort", "area": "Fläche", "status": "Status", "age": "Alter",
    "sex": "Geschlecht", "melder": "Melder", "melded": "gemeldet", "partner": "Partner", "pair": "Paar", "comment": "Kommentar",
    "habitat": "Habitat", "field_fruit": "Feldfrucht", "color_ring_color": "Ringfarbe", "color_ring_text_color": "Schriftfarbe",
    "color_ring_code": "Farbringcode", "lat": "Breite", "lon": "Länge", "is_exact_location": "Koordinate exakt", "date": "Datum",
    "large_group_size": "Gruppengröße (groß)", "small_group_size": "Gruppengröße (klein)", "breed_size": "Brutgröße", "family_size": "Familiengröße",
    "ringer": "Beringer", "ring_color": "Ringfarbe", "text_color": "Schriftfarbe", "code": "Code", "mark_type": "Markierungsart", "leg": "Bein", "project": "Projekt",
}
TABLE_LABELS = {"sightings": "Sichtungen", "ringings": "Beringungen", "color_rings": "Farbring-Register"}
_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


def _coerce(table: str, col: str, value: Any) -> Any:
    """Validate/normalise a value for a whitelisted column; None clears the field."""
    if col not in EDITABLE[table]:
        raise WriteError(f"Feld „{col}“ darf in {TABLE_LABELS[table]} nicht geändert werden. Erlaubt: {', '.join(EDITABLE[table])}")
    if value is None or (isinstance(value, str) and value.strip() == ""):
        return None
    kind = EDITABLE[table][col]
    try:
        if kind == "text":
            return str(value).strip()
        if kind == "int":
            return int(value)
        if kind == "num":
            return round(float(value), 6)
        if kind == "bool":
            if isinstance(value, str):
                return value.strip().lower() in ("1", "true", "ja", "yes", "wahr")
            return bool(value)
        if kind == "date":
            return date.fromisoformat(str(value)[:10]).isoformat()
        if kind == "color":
            return color_key(value, FIELD_LABELS.get(col, col))
        if kind == "code":
            return normalize_code(str(value))
    except (TypeError, ValueError) as exc:
        raise WriteError(f"Ungültiger Wert für {FIELD_LABELS.get(col, col)}: {value!r} ({exc})") from exc
    raise WriteError(f"Unbekannter Feldtyp für {col}")


def _norm(v: Any) -> Any:
    """Comparable JSON-safe form of a DB value (used for before/after checks)."""
    if v is None or v is pd.NaT:
        return None
    if isinstance(v, float) and math.isnan(v):
        return None
    if isinstance(v, bool):
        return v
    if isinstance(v, Decimal):
        f = float(v)
        return int(f) if f.is_integer() else round(f, 6)
    if isinstance(v, (int,)):
        return int(v)
    if isinstance(v, float):
        return int(v) if v.is_integer() else round(v, 6)
    if isinstance(v, (datetime, pd.Timestamp)):
        return pd.Timestamp(v).strftime("%Y-%m-%d") if pd.Timestamp(v) == pd.Timestamp(v).normalize() else pd.Timestamp(v).isoformat()
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, UUID):
        return str(v)
    if hasattr(v, "item"):
        return _norm(v.item())
    return v


def _label_val(col: str, v: Any) -> str:
    if v is None or v == "":
        return "leer"
    if col in ("color_ring_color", "color_ring_text_color", "ring_color", "text_color"):
        return color_label(v)
    if isinstance(v, bool):
        return "ja" if v else "nein"
    return str(v)


# ---------------------------------------------------------------- operations


class _Op(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)


class Target(_Op):
    table: Literal["sightings", "ringings"] = "sightings"
    ids: list[str] | None = Field(None, description="Konkrete Datensatz-IDs (Sichtungs-UUIDs) – sicherste Auswahl.")
    ring: str | None = Field(None, description="Nur Zeilen mit diesem Metallring (exakt).")
    reading: str | None = Field(None, description="Nur Zeilen mit dieser Ablesung (exakt).")
    place: str | None = Field(None, description="Nur Zeilen mit diesem Ort (exakt).")
    species: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    place_group: str | None = Field(None, description="Gespeicherte Ortsgruppe (Definition).")

    @model_validator(mode="after")
    def _some_filter(self) -> "Target":
        if not any([self.ids, self.ring, self.reading, self.place, self.species, self.date_from, self.date_to, self.place_group]):
            raise ValueError("Eine Auswahl braucht mindestens einen Filter (ids, ring, reading, place, species, Zeitraum oder place_group).")
        return self

    def describe(self) -> str:
        bits = []
        if self.ids:
            bits.append(f"{len(self.ids)} ausgewählte Datensätze")
        if self.ring:
            bits.append(f"Metallring {self.ring}")
        if self.reading:
            bits.append(f"Ablesung {self.reading}")
        if self.place:
            bits.append(f"Ort „{self.place}“")
        if self.place_group:
            bits.append(f"Ortsgruppe „{self.place_group}“")
        if self.species:
            bits.append(f"Art {self.species}")
        if self.date_from or self.date_to:
            bits.append(f"Zeitraum {self.date_from or '…'} bis {self.date_to or '…'}")
        return f"{TABLE_LABELS[self.table]} mit " + ", ".join(bits)


class SetFields(_Op):
    op: Literal["set_fields"]
    target: Target
    set: dict[str, Any] = Field(..., min_length=1, description="Feld → neuer Wert (null löscht den Wert).")

    def describe(self) -> str:
        changes = ", ".join(f"{FIELD_LABELS.get(k, k)} → {_label_val(k, v)}" for k, v in self.set.items())
        return f"{self.target.describe()}: {changes}"


class RenamePlace(_Op):
    op: Literal["rename_place"]
    from_place: str = Field(..., alias="from", description="Bisherige Schreibweise (exakt).")
    to_place: str = Field(..., alias="to", description="Neue Schreibweise.")
    area_from: str | None = Field(None, description="Optional: nur Zeilen mit dieser Fläche.")
    area_to: str | None = Field(None, description="Optional: Fläche ebenfalls umbenennen.")
    tables: list[Literal["sightings", "ringings"]] = Field(default_factory=lambda: ["sightings", "ringings"])

    def describe(self) -> str:
        s = f"Ort „{self.from_place}“ → „{self.to_place}“"
        if self.area_to is not None:
            s += f", Fläche → „{self.area_to}“"
        return s + " (" + ", ".join(TABLE_LABELS[t] for t in self.tables) + ")"


class ConvertToColorRing(_Op):
    op: Literal["convert_to_color_ring"]
    value: str = Field(..., description="Der bisher als Ring/Ablesung gespeicherte Wert, z. B. 'W408'.")
    ring_color: str = Field(..., description="Ringfarbe (Palette: white, black, red, orange, yellow, lightgreen, darkgreen, lightblue, darkblue, violet, pink, brown, grey – oder deutsch).")
    text_color: str | None = None
    code: str | None = Field(None, description="Inschrift (Standard: value).")
    keep_metal_ring: bool = Field(False, description="Metallring-Feld unverändert lassen (true), oder leeren, wenn es den Farbringwert enthält (false).")
    set_reading_to_code: bool = Field(True, description="Ablesung auf den Code setzen.")
    register_ring: bool = Field(True, alias="register", description="Farbring im Register (color_rings) anlegen/aktualisieren.")
    metal_ring: str | None = Field(None, description="Bekannter Metallring des Vogels (für das Register).")
    mark_type: Literal["leg", "neck", "wing"] | None = None
    leg: Literal["left", "right"] | None = None
    date_from: str | None = None
    date_to: str | None = None
    place: str | None = None

    def describe(self) -> str:
        return f"„{self.value}“ als Farbring {color_label(color_key(self.ring_color))}{' / ' + color_label(color_key(self.text_color)) if self.text_color else ''} {normalize_code(self.code or self.value)}"


class UpsertColorRing(_Op):
    op: Literal["upsert_color_ring"]
    ring: str | None = Field(None, description="Metallring (optional).")
    ring_color: str
    text_color: str | None = None
    code: str
    mark_type: Literal["leg", "neck", "wing"] | None = None
    leg: Literal["left", "right"] | None = None
    project: str | None = None
    comment: str | None = None

    def describe(self) -> str:
        return f"Farbring {color_label(color_key(self.ring_color))} {normalize_code(self.code)}{' (Metallring ' + self.ring + ')' if self.ring else ''} im Register"


class MergeReadingToRing(_Op):
    op: Literal["merge_reading_to_ring"]
    reading: str = Field(..., description="Ablesung ohne Ring, z. B. '...23886'.")
    ring: str = Field(..., description="Der Metallring, dem diese Ablesung zugeordnet wird.")
    clear_reading: bool = Field(False, description="Ablesung danach leeren.")

    def describe(self) -> str:
        return f"Sichtungen mit Ablesung „{self.reading}“ ohne Ring → Metallring {self.ring}" + (", Ablesung geleert" if self.clear_reading else "")


Operation = Annotated[Union[SetFields, RenamePlace, ConvertToColorRing, UpsertColorRing, MergeReadingToRing], Field(discriminator="op")]


# ---------------------------------------------------------------- planning (dry run)

SELECT_COLS = {
    "sightings": ["id", "org_id", "date", "place", "species", "ring", "reading"],
    "ringings": ["id", "org_id", "ring", "date", "place", "species"],
    "color_rings": ["id", "org_id", "ring", "ring_color", "text_color", "code", "mark_type", "leg", "project", "comment"],
}


def _check_ident(name: str) -> str:
    if not _IDENT.match(name):
        raise WriteError(f"Ungültiger Bezeichner {name!r}")
    return name


def write_org() -> str:
    """Every plan/apply/rollback is scoped to exactly this organisation (env WRITE_ORG_ID)."""
    org = settings.write_org_id
    if not org:
        raise WriteError("Schreiben ist nicht freigeschaltet: WRITE_ORG_ID (Organisation) fehlt auf dem Server.")
    try:
        return str(UUID(org))
    except ValueError as exc:
        raise WriteError("WRITE_ORG_ID ist keine gültige UUID.") from exc


async def _select(table: str, cols: list[str], where: list[str], params: list[Any], *, scoped: bool = True) -> list[dict[str, Any]]:
    """Read rows via the read-only pool (parameterised; identifiers from the whitelist only), scoped to the write org."""
    for c in cols:
        _check_ident(c)
    where = list(where)
    params = list(params)
    if scoped:
        where.append("org_id = %s::uuid")
        params.append(write_org())
    sql = f"SELECT {', '.join(cols)} FROM {_check_ident(table)} WHERE {' AND '.join(where) if where else 'TRUE'} ORDER BY 1"
    res = await runtime.database().query(sql, params=tuple(params) if params else None, max_rows=settings.write_max_rows + 1)
    return [dict(zip(res.columns, r)) for r in res.rows]


async def _outside_scope(table: str, where: list[str], params: list[Any]) -> int:
    """How many rows would match without the organisation scope (shown so the user understands the numbers)."""
    rows = await _select(table, ["id", "org_id"], where, params, scoped=False)
    org = write_org()
    return sum(1 for r in rows if str(r.get("org_id")) != org)


def _target_where(t: Target) -> tuple[list[str], list[Any]]:
    where, params = [], []
    if t.ids:
        where.append("id = ANY(%s::uuid[])")
        params.append(list(t.ids))
    if t.ring:
        where.append("ring = %s"); params.append(t.ring.strip())
    if t.reading:
        where.append("reading = %s"); params.append(t.reading.strip())
    if t.place:
        where.append("place = %s"); params.append(t.place.strip())
    if t.species:
        where.append("species = %s"); params.append(t.species.strip())
    if t.date_from:
        where.append("date >= %s::date"); params.append(t.date_from)
    if t.date_to:
        where.append("date <= %s::date"); params.append(t.date_to)
    if t.place_group:
        d = runtime.definitions().get(t.place_group)
        if d is None or d.kind != "place_group":
            raise WriteError(f"Ortsgruppe „{t.place_group}“ ist nicht gespeichert.")
        where.append(runtime.definitions().expand_one(d, "place"))
    return where, params


def _item(table: str, row: dict[str, Any], changes: dict[str, Any], op_index: int, action: str = "update") -> dict[str, Any] | None:
    before = {c: _norm(row.get(c)) for c in changes}
    after = {c: _norm(v) for c, v in changes.items()}
    diff = {c: after[c] for c in changes if before[c] != after[c]}
    if action == "update" and not diff:
        return None
    return {
        "table": table, "id": str(row.get("id")) if row.get("id") is not None else None, "org_id": str(row.get("org_id")) if row.get("org_id") else None,
        "key": {c: _norm(row.get(c)) for c in DISPLAY_COLS[table] if c in row}, "before": {c: before[c] for c in diff} if action == "update" else {},
        "after": diff if action == "update" else after, "op": op_index, "action": action,
    }


async def _plan_set_fields(op: SetFields, i: int) -> tuple[list[dict], dict, list[str]]:
    table = op.target.table
    changes = {c: _coerce(table, c, v) for c, v in op.set.items()}
    where, params = _target_where(op.target)
    rows = await _select(table, SELECT_COLS[table] + [c for c in changes if c not in SELECT_COLS[table]], where, params)
    items = [it for r in rows if (it := _item(table, r, changes, i))]
    outside = await _outside_scope(table, where, params)
    return items, {"description": op.describe(), "matched": len(rows), "rows": len(items), "skipped": len(rows) - len(items), "outside_org": outside}, ([f"{outside} weitere Datensätze gehören einer anderen Organisation und werden nicht angefasst."] if outside else [])


async def _plan_rename_place(op: RenamePlace, i: int) -> tuple[list[dict], dict, list[str]]:
    items: list[dict] = []
    matched = 0
    outside = 0
    for table in op.tables:
        where, params = ["place = %s"], [op.from_place.strip()]
        changes: dict[str, Any] = {"place": _coerce(table, "place", op.to_place)}
        if table == "sightings" and op.area_from is not None:
            where.append("area = %s"); params.append(op.area_from)
        if table == "sightings" and op.area_to is not None:
            changes["area"] = _coerce(table, "area", op.area_to)
        cols = SELECT_COLS[table] + [c for c in changes if c not in SELECT_COLS[table]]
        rows = await _select(table, cols, where, params)
        matched += len(rows)
        outside += await _outside_scope(table, where, params)
        items += [it for r in rows if (it := _item(table, r, changes, i))]
    warnings = []
    if not matched:
        warnings.append(f"Kein Datensatz hat den Ort „{op.from_place}“ (exakte Schreibweise).")
    if outside:
        warnings.append(f"{outside} weitere Datensätze mit diesem Ort gehören einer anderen Organisation und werden nicht angefasst.")
    return items, {"description": op.describe(), "matched": matched, "rows": len(items), "skipped": matched - len(items), "outside_org": outside}, warnings


async def _registry_lookup(ring_color: str, text_color: str | None, code: str, metal: str | None) -> tuple[dict | None, dict | None]:
    by_identity = await _select("color_rings", SELECT_COLS["color_rings"], ["ring_color = %s", "COALESCE(text_color, '') = %s", "code = %s"], [ring_color, text_color or "", code])
    by_ring = await _select("color_rings", SELECT_COLS["color_rings"], ["ring = %s"], [metal]) if metal else []
    return (by_identity[0] if by_identity else None), (by_ring[0] if by_ring else None)


async def _plan_upsert_registry(ring_color: str, text_color: str | None, code: str, metal: str | None, extra: dict[str, Any], org_id: str | None, i: int) -> tuple[list[dict], list[str]]:
    ident, by_ring = await _registry_lookup(ring_color, text_color, code, metal)
    warnings: list[str] = []
    if by_ring and (not ident or str(by_ring["id"]) != str(ident["id"])):
        raise WriteError(f"Metallring {metal} ist im Farbring-Register bereits einem anderen Farbring zugeordnet ({color_label(by_ring['ring_color'])} {by_ring['code']}). Bitte zuerst klären.")
    fields = {"ring": metal, "ring_color": ring_color, "text_color": text_color, "code": code, **{k: v for k, v in extra.items() if v is not None}}
    if ident:
        changes = {k: v for k, v in fields.items() if k != "ring" or metal}
        it = _item("color_rings", ident, changes, i)
        return ([it] if it else []), warnings
    org_id = write_org()
    return [{"table": "color_rings", "id": None, "org_id": org_id, "key": {"ring_color": ring_color, "code": code}, "before": {}, "after": {"org_id": org_id, **fields}, "op": i, "action": "insert"}], warnings


async def _plan_convert(op: ConvertToColorRing, i: int) -> tuple[list[dict], dict, list[str]]:
    ring_color = color_key(op.ring_color, "Ringfarbe")
    text_color = color_key(op.text_color, "Schriftfarbe")
    code = normalize_code(op.code or op.value)
    value = op.value.strip()
    where, params = ["(ring = %s OR reading = %s)"], [value, value]
    if op.date_from:
        where.append("date >= %s::date"); params.append(op.date_from)
    if op.date_to:
        where.append("date <= %s::date"); params.append(op.date_to)
    if op.place:
        where.append("place = %s"); params.append(op.place)
    cols = SELECT_COLS["sightings"] + ["color_ring_color", "color_ring_text_color", "color_ring_code"]
    rows = await _select("sightings", cols, where, params)
    warnings: list[str] = []
    outside = await _outside_scope("sightings", where, params)
    if not rows:
        warnings.append(f"Keine Sichtung hat „{value}“ als Ring oder Ablesung.")
    if outside:
        warnings.append(f"{outside} weitere Sichtungen mit „{value}“ gehören einer anderen Organisation und werden nicht angefasst.")
    ringed = await _select("ringings", ["id", "ring"], ["ring = %s"], [value])
    is_metal = bool(ringed)
    if is_metal and not op.keep_metal_ring:
        warnings.append(f"„{value}“ existiert als Beringung (Metallring) – das Ringfeld wird deshalb NICHT geleert.")
    items: list[dict] = []
    for r in rows:
        changes: dict[str, Any] = {"color_ring_color": ring_color, "color_ring_text_color": text_color, "color_ring_code": code}
        if op.set_reading_to_code:
            changes["reading"] = code
        if not op.keep_metal_ring and not is_metal and _norm(r.get("ring")) == value:
            changes["ring"] = op.metal_ring or None
        elif op.metal_ring and _norm(r.get("ring")) in (None, value):
            changes["ring"] = op.metal_ring
        if it := _item("sightings", r, changes, i):
            items.append(it)
    if op.register_ring:
        metal = op.metal_ring or (value if is_metal else None)
        reg_items, w = await _plan_upsert_registry(ring_color, text_color, code, metal, {"mark_type": op.mark_type, "leg": op.leg}, write_org(), i)
        items += reg_items
        warnings += w
    return items, {"description": op.describe(), "matched": len(rows), "rows": len(items), "skipped": len(rows) - len([x for x in items if x["table"] == "sightings"]), "outside_org": outside}, warnings


async def _plan_upsert(op: UpsertColorRing, i: int) -> tuple[list[dict], dict, list[str]]:
    ring_color = color_key(op.ring_color, "Ringfarbe")
    text_color = color_key(op.text_color, "Schriftfarbe")
    code = normalize_code(op.code)
    items, warnings = await _plan_upsert_registry(ring_color, text_color, code, op.ring.strip() if op.ring else None, {"mark_type": op.mark_type, "leg": op.leg, "project": op.project, "comment": op.comment}, write_org(), i)
    return items, {"description": op.describe(), "matched": 1, "rows": len(items), "skipped": 1 - len(items)}, warnings


async def _plan_merge(op: MergeReadingToRing, i: int) -> tuple[list[dict], dict, list[str]]:
    rows = await _select("sightings", SELECT_COLS["sightings"], ["reading = %s", "ring IS NULL"], [op.reading.strip()])
    changes: dict[str, Any] = {"ring": op.ring.strip()}
    if op.clear_reading:
        changes["reading"] = None
    items = [it for r in rows if (it := _item("sightings", r, changes, i))]
    warnings = [] if rows else [f"Keine Sichtung mit Ablesung „{op.reading}“ ohne Ring."]
    outside = await _outside_scope("sightings", ["reading = %s", "ring IS NULL"], [op.reading.strip()])
    if outside:
        warnings.append(f"{outside} weitere Sichtungen mit dieser Ablesung gehören einer anderen Organisation und werden nicht angefasst.")
    known = await _select("ringings", ["id", "ring"], ["ring = %s"], [op.ring.strip()])
    if not known:
        warnings.append(f"Metallring {op.ring} hat keine Beringung in der Datenbank.")
    return items, {"description": op.describe(), "matched": len(rows), "rows": len(items), "skipped": len(rows) - len(items)}, warnings


_PLANNERS = {SetFields: _plan_set_fields, RenamePlace: _plan_rename_place, ConvertToColorRing: _plan_convert, UpsertColorRing: _plan_upsert, MergeReadingToRing: _plan_merge}


def _summarise(ops: list[Any], per_op: list[dict], items: list[dict]) -> dict[str, Any]:
    field_changes: dict[str, dict[str, int]] = {}
    lines = []
    for i, (op, info) in enumerate(zip(ops, per_op)):
        op_items = [it for it in items if it["op"] == i]
        counts: dict[str, int] = {}
        examples: dict[str, set] = {}
        for it in op_items:
            for c, v in it["after"].items():
                if it["action"] == "insert" and c == "org_id":
                    continue
                counts[c] = counts.get(c, 0) + 1
                examples.setdefault(c, set()).add((_label_val(c, it["before"].get(c)) if it["action"] == "update" else "neu") + " → " + _label_val(c, v))
        by_table: dict[str, int] = {}
        for it in op_items:
            by_table[it["table"]] = by_table.get(it["table"], 0) + 1
        what = ", ".join(f"{n} {TABLE_LABELS[t]}" for t, n in by_table.items()) or "keine Änderung"
        change_txt = "; ".join(f"{FIELD_LABELS.get(c, c)}: {' | '.join(sorted(ex)[:3])}{' …' if len(ex) > 3 else ''} ({counts[c]}×)" for c, ex in examples.items())
        lines.append(f"{i + 1}. {info['description']} – {what}" + (f": {change_txt}" if change_txt else "") + (f" – {info['skipped']} bereits so, übersprungen" if info.get("skipped") else ""))
        field_changes[str(i)] = counts
    return {"lines": lines, "field_changes": field_changes, "total_rows": len(items), "tables": sorted({it["table"] for it in items})}


async def plan(operations: list[Operation], reason: str, by: str = "agent") -> dict[str, Any]:
    """Dry run: resolve every affected row and store a proposed changeset. Never writes."""
    if not operations:
        raise WriteError("Keine Operationen angegeben.")
    if not reason or len(reason.strip()) < 5:
        raise WriteError("Bitte einen Grund angeben (reason), der im Protokoll erscheint.")
    write_org()
    items: list[dict] = []
    per_op: list[dict] = []
    warnings: list[str] = []
    for i, op in enumerate(operations):
        planner = _PLANNERS[type(op)]
        op_items, info, w = await planner(op, i)
        items += op_items
        per_op.append(info)
        warnings += w
    if len(items) > settings.write_max_rows:
        raise WriteError(f"Zu viele Änderungen auf einmal ({len(items)} > {settings.write_max_rows}). Bitte in kleinere Schritte teilen (z. B. nach Zeitraum).")
    org = write_org()
    if any(it.get("org_id") and it["org_id"] != org for it in items):
        raise WriteError("Interner Fehler: ein Datensatz außerhalb der Organisation ist in den Vorschlag geraten. Abbruch.")
    # duplicate row targets across operations → last wins is confusing; refuse
    seen: dict[tuple, int] = {}
    for it in items:
        if it["id"]:
            k = (it["table"], it["id"])
            if k in seen and seen[k] != it["op"]:
                raise WriteError(f"Datensatz {it['id']} wird von mehreren Operationen geändert. Bitte zusammenfassen.")
            seen[k] = it["op"]
    summary = _summarise(operations, per_op, items)
    summary["org_id"] = org
    summary["outside_org"] = sum(int(p.get("outside_org", 0) or 0) for p in per_op)
    summary["lines"].append(f"Organisation: {org} – nur Datensätze dieser Organisation werden geändert.")
    if not items:
        warnings.append("Es würde sich nichts ändern.")
    cat = runtime.catalog()
    doc = {
        "status": "proposed", "reason": reason.strip(), "by": by, "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "applied_at": None, "rolled_back_at": None, "last_error": None, "org_id": org,
        "operations": [op.model_dump(mode="json", by_alias=True, exclude_none=True) for op in operations],
        "per_op": per_op, "summary": summary, "warnings": warnings, "items": items, "row_count": len(items),
    }
    title = f"{len(items)} Änderungen: " + (summary["lines"][0][3:80] if summary["lines"] else reason[:60])
    item = cat.put("changeset", doc, title=title, description=reason.strip()[:200], owner=by, tags=["proposed"])
    bus.publish("changeset.proposed", f"Änderungsvorschlag: {title}", id=item.id, changeset_id=item.id, rows=len(items), by=by)
    return _out(item.id, doc)


def _out(cid: str, doc: dict[str, Any], *, include_items: int = 5) -> dict[str, Any]:
    d = {k: v for k, v in doc.items() if k != "items"}
    d["changeset_id"] = cid
    d["preview_url"] = f"{settings.public_base_url}/changes/{cid}"
    d["examples"] = doc["items"][:include_items]
    d["plain_summary"] = "\n".join(doc["summary"].get("lines", [])) + (f"\nHinweise: {' '.join(doc['warnings'])}" if doc.get("warnings") else "")
    return d


def get(cid: str, *, include_items: int = 5) -> dict[str, Any]:
    item = runtime.catalog().get("changeset", cid)
    return _out(cid, item.doc, include_items=include_items)


def get_full(cid: str) -> dict[str, Any]:
    item = runtime.catalog().get("changeset", cid)
    return {"changeset_id": cid, "title": item.title, "preview_url": f"{settings.public_base_url}/changes/{cid}", **item.doc}


def list_changes(limit: int = 20, status: str | None = None) -> list[dict[str, Any]]:
    out = []
    for it in runtime.catalog().list("changeset", limit=limit * 3 if status else limit):
        if status and it.doc.get("status") != status:
            continue
        out.append({"changeset_id": it.id, "title": it.title, "status": it.doc.get("status"), "reason": it.doc.get("reason"), "rows": it.doc.get("row_count"), "by": it.doc.get("by"), "created_at": it.doc.get("created_at"), "applied_at": it.doc.get("applied_at"), "preview_url": f"{settings.public_base_url}/changes/{it.id}"})
        if len(out) >= limit:
            break
    return out


# ---------------------------------------------------------------- apply / rollback (write pool)

_write_pool: AsyncConnectionPool | None = None


def write_pool() -> AsyncConnectionPool:
    global _write_pool
    if not settings.write_database_url:
        raise WriteError("Schreiben ist auf diesem Server nicht freigeschaltet (WRITE_DATABASE_URL fehlt). Auswertungen bleiben möglich.")
    if _write_pool is None:
        _write_pool = AsyncConnectionPool(settings.write_database_url, min_size=0, max_size=2, open=False, kwargs={"autocommit": False})
    return _write_pool


async def _ensure_open(pool: Any) -> None:
    opener = getattr(pool, "open", None)
    if opener is not None and not getattr(pool, "_opened", False):
        try:
            await opener()
        except TypeError:
            pass
        try:
            pool._opened = True
        except Exception:
            pass


def _save(cid: str, doc: dict[str, Any]) -> None:
    cat = runtime.catalog()
    item = cat.get("changeset", cid)
    cat.put("changeset", doc, id=cid, title=item.title, description=item.description, owner=item.owner, tags=[doc.get("status", "proposed")])


async def _read_row(conn: Any, table: str, cols: list[str], row_id: str) -> dict[str, Any] | None:
    cur = await conn.execute(f"SELECT {', '.join(cols)} FROM {table} WHERE id = %s AND org_id = %s::uuid FOR UPDATE", (row_id, write_org()))
    row = await cur.fetchone()
    if row is None:
        return None
    return dict(zip(cols, row))


def _mismatch(expected: dict[str, Any], current: dict[str, Any]) -> list[str]:
    return [f"{FIELD_LABELS.get(c, c)}: erwartet {_label_val(c, v)}, jetzt {_label_val(c, _norm(current.get(c)))}" for c, v in expected.items() if _norm(current.get(c)) != v]


async def _write_items(conn: Any, items: list[dict], direction: Literal["apply", "rollback"], cid: str) -> list[dict[str, Any]]:
    """Apply (`after`) or restore (`before`) values; verify the current state first. Returns manual steps (rollback of inserts)."""
    manual: list[dict[str, Any]] = []
    await conn.execute("SET LOCAL statement_timeout = %s", (settings.statement_timeout_ms,))
    for n, it in enumerate(items, start=1):
        table = _check_ident(it["table"])
        if it["action"] == "insert":
            if direction == "rollback":
                manual.append({"table": table, "id": it.get("inserted_id"), "note": "Registereintrag wurde neu angelegt und kann nicht automatisch gelöscht werden (kein DELETE-Recht). Bitte in vogelring.com unter Farbringe löschen, falls gewünscht.", "row": it["after"]})
                continue
            cols = [_check_ident(c) for c in it["after"]]
            if it["after"].get("org_id") != write_org():
                raise WriteError("Registereintrag außerhalb der Organisation – Abbruch.")
            for c in cols:
                if c != "org_id" and c not in EDITABLE["color_rings"]:
                    raise WriteError(f"Spalte {c} darf nicht geschrieben werden.")
            cur = await conn.execute(f"INSERT INTO {table} ({', '.join(cols)}) VALUES ({', '.join(['%s'] * len(cols))}) RETURNING id", tuple(it["after"][c] for c in cols))
            row = await cur.fetchone()
            it["inserted_id"] = str(row[0]) if row else None
            continue
        expected = it["before"] if direction == "apply" else it["after"]
        target = it["after"] if direction == "apply" else it["before"]
        cols = [_check_ident(c) for c in target]
        for c in cols:
            if c not in EDITABLE[table]:
                raise WriteError(f"Spalte {c} darf in {TABLE_LABELS[table]} nicht geschrieben werden.")
        current = await _read_row(conn, table, cols, it["id"])
        if current is None:
            raise WriteError(f"Änderung {n}: Datensatz {it['id']} ({TABLE_LABELS[table]}) existiert nicht mehr. Nichts wurde geändert.")
        if problems := _mismatch(expected, current):
            raise WriteError(f"Änderung {n}: Datensatz {it['id']} ({TABLE_LABELS[table]}, {it.get('key')}) wurde zwischenzeitlich verändert – {'; '.join(problems)}. Nichts wurde geändert; bitte neu planen.")
        sets = ", ".join(f"{c} = %s" for c in cols) + ", updated_at = CURRENT_TIMESTAMP"
        cur = await conn.execute(f"UPDATE {table} SET {sets} WHERE id = %s AND org_id = %s::uuid", tuple(target[c] for c in cols) + (it["id"], write_org()))
        if getattr(cur, "rowcount", 1) != 1:
            raise WriteError(f"Änderung {n}: Datensatz {it['id']} wurde nicht genau einmal aktualisiert (rowcount={getattr(cur, 'rowcount', None)}). Abbruch.")
        check = await _read_row(conn, table, cols, it["id"])
        if check is None or _mismatch(target, check):
            raise WriteError(f"Änderung {n}: Datensatz {it['id']} hat nach dem Schreiben nicht den erwarteten Wert. Abbruch.")
    return manual


def _check_status(doc: dict[str, Any], expected: str, cid: str) -> None:
    if doc.get("status") != expected:
        raise WriteError(f"Änderungsvorschlag {cid} hat den Status „{doc.get('status')}“, erwartet „{expected}“.")


async def apply(cid: str, by: str = "agent", pool: Any | None = None) -> dict[str, Any]:
    cat = runtime.catalog()
    doc = dict(cat.get("changeset", cid).doc)
    _check_status(doc, "proposed", cid)
    created = datetime.fromisoformat(doc["created_at"])
    if datetime.now(timezone.utc) - created > timedelta(minutes=settings.write_proposal_ttl_min):
        raise WriteError(f"Der Vorschlag ist älter als {settings.write_proposal_ttl_min} Minuten. Bitte neu planen (propose_changes), damit die Vorher-Werte aktuell sind.")
    if not doc["items"]:
        raise WriteError("Der Vorschlag enthält keine Änderungen.")
    pool = pool or write_pool()
    await _ensure_open(pool)
    log.warning("APPLY changeset %s by %s: %d rows (%s)", cid, by, len(doc["items"]), doc.get("reason"))
    try:
        async with pool.connection() as conn:
            async with conn.transaction():
                await _write_items(conn, doc["items"], "apply", cid)
    except WriteError as exc:
        doc["last_error"] = str(exc)
        _save(cid, doc)
        bus.publish("changeset.failed", f"Änderung abgebrochen: {str(exc)[:120]}", id=cid, changeset_id=cid, by=by)
        raise
    except Exception as exc:
        doc["last_error"] = f"Datenbankfehler: {str(exc)[:300]}"
        _save(cid, doc)
        log.exception("apply failed for %s", cid)
        bus.publish("changeset.failed", "Änderung abgebrochen (Datenbankfehler)", id=cid, changeset_id=cid, by=by)
        raise WriteError(doc["last_error"]) from exc
    doc["status"] = "applied"
    doc["applied_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc["applied_by"] = by
    doc["last_error"] = None
    _save(cid, doc)
    bus.publish("changeset.applied", f"Änderung übernommen: {len(doc['items'])} Datensätze", id=cid, changeset_id=cid, rows=len(doc["items"]), by=by)
    log.warning("APPLIED changeset %s by %s", cid, by)
    return _out(cid, doc)


async def rollback(cid: str, by: str = "agent", pool: Any | None = None) -> dict[str, Any]:
    cat = runtime.catalog()
    doc = dict(cat.get("changeset", cid).doc)
    _check_status(doc, "applied", cid)
    pool = pool or write_pool()
    await _ensure_open(pool)
    log.warning("ROLLBACK changeset %s by %s: %d rows", cid, by, len(doc["items"]))
    try:
        async with pool.connection() as conn:
            async with conn.transaction():
                manual = await _write_items(conn, doc["items"], "rollback", cid)
    except WriteError as exc:
        doc["last_error"] = str(exc)
        _save(cid, doc)
        raise
    except Exception as exc:
        doc["last_error"] = f"Datenbankfehler: {str(exc)[:300]}"
        _save(cid, doc)
        log.exception("rollback failed for %s", cid)
        raise WriteError(doc["last_error"]) from exc
    doc["status"] = "rolled_back"
    doc["rolled_back_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    doc["rolled_back_by"] = by
    doc["manual_steps"] = manual
    doc["last_error"] = None
    _save(cid, doc)
    bus.publish("changeset.rolled_back", f"Änderung zurückgenommen: {len(doc['items']) - len(manual)} Datensätze", id=cid, changeset_id=cid, by=by, manual_steps=len(manual))
    log.warning("ROLLED BACK changeset %s by %s (%d manual steps)", cid, by, len(manual))
    out = _out(cid, doc)
    out["manual_steps"] = manual
    return out


def writes_enabled() -> bool:
    return bool(settings.write_database_url) and bool(settings.write_org_id)
