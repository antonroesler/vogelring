"""Named, executable definitions ("Nordufer", "Mauserzeit", "Kerngruppe") shared across chats.

LibreChat's memory stores prose; this store keeps SQL-expandable definitions so a group of places,
a set of rings or a period means exactly the same thing in every analysis. Referenced in SQL as
``{{Name}}`` or ``{{Name:column}}`` and expanded before the query runs.
"""

from __future__ import annotations

import json
import re
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .settings import settings

DefinitionKind = Literal["place_group", "ring_group", "period", "filter", "note"]

_REF = re.compile(r"\{\{\s*([^{}:]+?)\s*(?::\s*([A-Za-z_][A-Za-z0-9_.]*)\s*)?\}\}")
_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_.]*$")


class DefinitionError(ValueError):
    pass


@dataclass
class Definition:
    name: str
    kind: DefinitionKind
    description: str = ""
    values: list[str] = field(default_factory=list)
    sql: str | None = None
    date_from: str | None = None
    date_to: str | None = None
    default_column: str | None = None
    created_by: str | None = None
    created_at: str = ""
    updated_at: str = ""

    def default_col(self) -> str:
        if self.default_column:
            return self.default_column
        return {"place_group": "place", "ring_group": "ring", "period": "date", "filter": "", "note": ""}[self.kind]


def _norm(name: str) -> str:
    return re.sub(r"\s+", " ", name.strip()).casefold()


def _lit(v: str) -> str:
    return "'" + str(v).replace("'", "''") + "'"


def _months(values: list[str]) -> list[int]:
    out: list[int] = []
    for v in values:
        for part in str(v).replace(";", ",").split(","):
            part = part.strip()
            if not part:
                continue
            if "-" in part and not part.startswith("-"):
                a, b = part.split("-", 1)
                a_i, b_i = int(a), int(b)
                rng = list(range(a_i, b_i + 1)) if a_i <= b_i else list(range(a_i, 13)) + list(range(1, b_i + 1))
                out += rng
            else:
                out.append(int(part))
    bad = [m for m in out if not 1 <= m <= 12]
    if bad:
        raise DefinitionError(f"Ungültige Monatsangabe: {bad}")
    return sorted(set(out))


class DefinitionStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (settings.data_dir / "definitions.json")
        self._lock = threading.Lock()
        self._items: dict[str, Definition] = {}
        self._load()

    # ---------------------------------------------------------------- persistence
    def _load(self) -> None:
        if not self.path.exists():
            return
        try:
            raw = json.loads(self.path.read_text())
        except Exception:
            return
        for item in raw.get("definitions", []):
            try:
                d = Definition(**item)
                self._items[_norm(d.name)] = d
            except TypeError:
                continue

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"definitions": [asdict(d) for d in self._items.values()]}, ensure_ascii=False, indent=1))
        tmp.replace(self.path)

    # ---------------------------------------------------------------- CRUD
    def save(self, d: Definition) -> Definition:
        name = d.name.strip()
        if not name or len(name) > 60 or "{" in name or "}" in name or ":" in name:
            raise DefinitionError("Name: 1–60 Zeichen, ohne {, } oder :.")
        if d.kind in ("place_group", "ring_group") and not d.values:
            raise DefinitionError(f"{d.kind} braucht mindestens einen Wert in values.")
        if d.kind == "period" and not (d.values or (d.date_from and d.date_to)):
            raise DefinitionError("period braucht Monate in values (z. B. ['5','6'] oder ['11-1']) oder date_from/date_to.")
        if d.kind == "period" and d.values:
            _months(d.values)
        if d.kind == "filter":
            if not d.sql or ";" in d.sql or "{{" in d.sql:
                raise DefinitionError("filter braucht ein SQL-Bool-Fragment ohne ';' und ohne verschachtelte {{…}}.")
        if d.default_column and not _IDENT.match(d.default_column):
            raise DefinitionError("default_column ist kein gültiger Spaltenname.")
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        with self._lock:
            prev = self._items.get(_norm(name))
            d.name = name
            d.created_at = prev.created_at if prev else now
            d.updated_at = now
            self._items[_norm(name)] = d
            self._save()
        return d

    def get(self, name: str) -> Definition | None:
        return self._items.get(_norm(name))

    def delete(self, name: str) -> bool:
        with self._lock:
            ok = self._items.pop(_norm(name), None) is not None
            if ok:
                self._save()
        return ok

    def list(self) -> list[Definition]:
        return sorted(self._items.values(), key=lambda d: d.name.casefold())

    # ---------------------------------------------------------------- expansion
    def expand_one(self, d: Definition, column: str | None) -> str:
        col = column or d.default_col()
        if col and not _IDENT.match(col):
            raise DefinitionError(f"Ungültige Spalte '{col}' in {{{{{d.name}:{col}}}}}.")
        if d.kind == "place_group":
            return "(" + " OR ".join(f"{col} ILIKE {_lit('%' + v.strip('%') + '%')}" for v in d.values) + ")"
        if d.kind == "ring_group":
            return f"({col} IN ({', '.join(_lit(v) for v in d.values)}))"
        if d.kind == "period":
            parts = []
            if d.values:
                parts.append(f"EXTRACT(MONTH FROM {col}) IN ({', '.join(str(m) for m in _months(d.values))})")
            if d.date_from and d.date_to:
                parts.append(f"{col} BETWEEN {_lit(d.date_from)}::date AND {_lit(d.date_to)}::date")
            return "(" + " AND ".join(parts) + ")"
        if d.kind == "filter":
            return f"({d.sql})"
        raise DefinitionError(f"'{d.name}' ist eine Notiz und kann nicht in SQL eingesetzt werden.")

    def expand(self, sql: str) -> tuple[str, list[str]]:
        used: list[str] = []

        def repl(m: re.Match[str]) -> str:
            name, col = m.group(1), m.group(2)
            d = self.get(name)
            if d is None:
                known = ", ".join(x.name for x in self.list()) or "–"
                raise DefinitionError(f"Unbekannte Definition {{{{{name}}}}}. Bekannt: {known}. Mit save_definition anlegen.")
            used.append(d.name)
            return self.expand_one(d, col)

        return _REF.sub(repl, sql), used

    def describe(self) -> str:
        items = self.list()
        if not items:
            return "Keine gespeicherten Definitionen."
        lines = ["| Name | Art | Bedeutung | Inhalt | SQL-Verwendung |", "|---|---|---|---|---|"]
        for d in items:
            content = d.sql or ", ".join(d.values) or ""
            if d.date_from and d.date_to:
                content = (content + " " if content else "") + f"{d.date_from}…{d.date_to}"
            usage = "–" if d.kind == "note" else f"{{{{{d.name}}}}}" + (f" oder {{{{{d.name}:spalte}}}}" if d.kind != "filter" else "")
            lines.append(f"| {d.name} | {d.kind} | {d.description} | {content[:80]} | {usage} |")
        return "\n".join(lines)

    def as_dicts(self) -> list[dict[str, Any]]:
        return [asdict(d) for d in self.list()]
