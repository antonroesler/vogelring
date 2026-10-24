"""SQLite catalog for user-facing objects (views, workbooks, pipelines, runs, decks, notes) and the activity log.

Datasets, visuals and reports keep their file stores; the catalog indexes everything the web app lists, searches
and edits. One generic `objects` table keeps the schema small: kind + id + json document + a few indexed columns.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from .datasets import new_id
from .settings import settings

KINDS = ("view", "workbook", "pipeline", "run", "deck", "note", "project", "changeset", "group")
PREFIX = {"view": "vw_", "workbook": "wb_", "pipeline": "pl_", "run": "run_", "deck": "dk_", "note": "nt_", "project": "pj_", "changeset": "chg_", "group": "grp_"}

_SCHEMA = """
CREATE TABLE IF NOT EXISTS objects (
  kind TEXT NOT NULL, id TEXT NOT NULL, title TEXT NOT NULL DEFAULT '', description TEXT NOT NULL DEFAULT '',
  owner TEXT NOT NULL DEFAULT '', project TEXT NOT NULL DEFAULT '', tags TEXT NOT NULL DEFAULT '', pinned INTEGER NOT NULL DEFAULT 0,
  json TEXT NOT NULL, extra TEXT NOT NULL DEFAULT '{}', created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  PRIMARY KEY (kind, id));
CREATE INDEX IF NOT EXISTS objects_kind_updated ON objects(kind, updated_at DESC);
CREATE INDEX IF NOT EXISTS objects_project ON objects(project);
CREATE TABLE IF NOT EXISTS activity (
  seq INTEGER PRIMARY KEY AUTOINCREMENT, at TEXT NOT NULL, type TEXT NOT NULL, title TEXT NOT NULL, json TEXT NOT NULL);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="microseconds")


@dataclass
class CatalogItem:
    kind: str
    id: str
    title: str
    description: str
    owner: str
    project: str
    tags: list[str]
    pinned: bool
    doc: dict[str, Any]
    created_at: str
    updated_at: str
    extra: dict[str, Any] = field(default_factory=dict)

    def summary(self) -> dict[str, Any]:
        return {"kind": self.kind, "id": self.id, "title": self.title, "description": self.description, "owner": self.owner, "project": self.project, "tags": self.tags, "pinned": self.pinned, "created_at": self.created_at, "updated_at": self.updated_at, "extra": self.extra}

    def full(self) -> dict[str, Any]:
        return {**self.summary(), "doc": self.doc}


class Catalog:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or (settings.data_dir / "catalog.sqlite")
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False, isolation_level=None)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA busy_timeout=5000")
        self._conn.executescript(_SCHEMA)
        cols = {r[1] for r in self._conn.execute("PRAGMA table_info(objects)").fetchall()}
        if "extra" not in cols:
            self._conn.execute("ALTER TABLE objects ADD COLUMN extra TEXT NOT NULL DEFAULT '{}'")
        self._migrate_underscore_keys()

    def _migrate_underscore_keys(self) -> None:
        """Early rows kept render metadata as `_key` inside the spec; move it to `extra` so specs validate."""
        for kind, oid, raw, raw_extra in self._conn.execute("SELECT kind, id, json, extra FROM objects WHERE json LIKE '%\"_%'").fetchall():
            try:
                doc, extra = json.loads(raw), json.loads(raw_extra or "{}")
            except Exception:
                continue
            moved = {k[1:]: v for k, v in doc.items() if k.startswith("_")}
            if not moved:
                continue
            doc = {k: v for k, v in doc.items() if not k.startswith("_")}
            extra.update(moved)
            self._conn.execute("UPDATE objects SET json=?, extra=? WHERE kind=? AND id=?", (json.dumps(doc, ensure_ascii=False, default=str), json.dumps(extra, ensure_ascii=False, default=str), kind, oid))

    # ---------------------------------------------------------------- objects
    def put(self, kind: str, doc: dict[str, Any], *, id: str | None = None, title: str = "", description: str = "", owner: str = "", project: str = "", tags: Iterable[str] = (), pinned: bool | None = None, extra: dict[str, Any] | None = None) -> CatalogItem:
        if kind not in KINDS:
            raise ValueError(f"unknown kind {kind}")
        now = _now()
        with self._lock:
            existing = self._get(kind, id) if id else None
            oid = id or new_id(PREFIX[kind])
            created = existing.created_at if existing else now
            pin = int(pinned if pinned is not None else (existing.pinned if existing else False))
            ex = extra if extra is not None else (existing.extra if existing else {})
            self._conn.execute(
                "INSERT INTO objects(kind,id,title,description,owner,project,tags,pinned,json,extra,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?) "
                "ON CONFLICT(kind,id) DO UPDATE SET title=excluded.title, description=excluded.description, owner=CASE WHEN excluded.owner='' THEN objects.owner ELSE excluded.owner END, "
                "project=excluded.project, tags=excluded.tags, pinned=excluded.pinned, json=excluded.json, extra=excluded.extra, updated_at=excluded.updated_at",
                (kind, oid, title or (existing.title if existing else ""), description or (existing.description if existing else ""), owner, project or (existing.project if existing else ""), ",".join(tags) or (",".join(existing.tags) if existing else ""), pin, json.dumps(doc, ensure_ascii=False, default=str), json.dumps(ex, ensure_ascii=False, default=str), created, now),
            )
            return self._get(kind, oid)  # type: ignore[return-value]

    def _get(self, kind: str, id: str) -> CatalogItem | None:
        row = self._conn.execute("SELECT kind,id,title,description,owner,project,tags,pinned,json,created_at,updated_at,extra FROM objects WHERE kind=? AND id=?", (kind, id)).fetchone()
        return self._row(row) if row else None

    @staticmethod
    def _row(row) -> CatalogItem:
        return CatalogItem(kind=row[0], id=row[1], title=row[2], description=row[3], owner=row[4], project=row[5], tags=[t for t in row[6].split(",") if t], pinned=bool(row[7]), doc=json.loads(row[8]), created_at=row[9], updated_at=row[10], extra=json.loads(row[11] or "{}"))

    def get(self, kind: str, id: str) -> CatalogItem:
        with self._lock:
            item = self._get(kind, id)
        if item is None:
            raise KeyError(f"Unbekannte {kind}-ID: {id}")
        return item

    def exists(self, kind: str, id: str) -> bool:
        with self._lock:
            return self._get(kind, id) is not None

    def delete(self, kind: str, id: str) -> bool:
        with self._lock:
            cur = self._conn.execute("DELETE FROM objects WHERE kind=? AND id=?", (kind, id))
            return cur.rowcount > 0

    def list(self, kind: str, *, limit: int = 50, search: str = "", project: str = "", pinned_first: bool = True, offset: int = 0) -> list[CatalogItem]:
        sql = "SELECT kind,id,title,description,owner,project,tags,pinned,json,created_at,updated_at,extra FROM objects WHERE kind=?"
        args: list[Any] = [kind]
        if search:
            sql += " AND (title LIKE ? OR description LIKE ? OR tags LIKE ?)"
            args += [f"%{search}%"] * 3
        if project:
            sql += " AND project=?"
            args.append(project)
        sql += " ORDER BY " + ("pinned DESC, " if pinned_first else "") + "updated_at DESC LIMIT ? OFFSET ?"
        args += [limit, offset]
        with self._lock:
            return [self._row(r) for r in self._conn.execute(sql, args).fetchall()]

    def set_pinned(self, kind: str, id: str, pinned: bool) -> None:
        with self._lock:
            self._conn.execute("UPDATE objects SET pinned=?, updated_at=? WHERE kind=? AND id=?", (int(pinned), _now(), kind, id))

    def counts(self) -> dict[str, int]:
        with self._lock:
            return {k: n for k, n in self._conn.execute("SELECT kind, COUNT(*) FROM objects GROUP BY kind").fetchall()}

    # ---------------------------------------------------------------- activity log
    def log_event(self, at: str, type: str, title: str, payload: dict[str, Any]) -> None:
        with self._lock:
            self._conn.execute("INSERT INTO activity(at,type,title,json) VALUES(?,?,?,?)", (at, type, title, json.dumps(payload, ensure_ascii=False, default=str)))
            self._conn.execute("DELETE FROM activity WHERE seq < (SELECT MAX(seq) FROM activity) - 5000")

    def activity(self, limit: int = 50, types: Iterable[str] = ()) -> list[dict[str, Any]]:
        sql = "SELECT seq, at, type, title, json FROM activity"
        args: list[Any] = []
        if types:
            tl = list(types)
            sql += " WHERE type IN (" + ",".join("?" * len(tl)) + ")"
            args += tl
        sql += " ORDER BY seq DESC LIMIT ?"
        args.append(limit)
        with self._lock:
            rows = self._conn.execute(sql, args).fetchall()
        return [{"seq": r[0], "at": r[1], "type": r[2], "title": r[3], **json.loads(r[4])} for r in rows]
