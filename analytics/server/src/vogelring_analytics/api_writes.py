"""REST routes and HTML preview for the gated write path (changesets)."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import TypeAdapter, ValidationError
from starlette.requests import Request
from starlette.responses import HTMLResponse, Response
from starlette.routing import Route

from . import writes
from .api import body, err, ok, user_of, validation_message
from .writes import Operation, WriteError

log = logging.getLogger(__name__)
_OPS = TypeAdapter(list[Operation])


async def api_plan(request: Request) -> Response:
    data = await body(request)
    try:
        ops = _OPS.validate_python(data.get("operations") or [])
    except ValidationError as exc:
        return err("Operationen ungültig: " + validation_message(exc))
    try:
        return ok(await writes.plan(ops, data.get("reason") or "", by=user_of(request) or "app"))
    except WriteError as exc:
        return err(str(exc))
    except Exception as exc:
        log.exception("plan failed")
        return err(f"Interner Fehler: {str(exc)[:200]}", 500)


async def api_list(request: Request) -> Response:
    q = request.query_params
    return ok({"items": writes.list_changes(limit=min(int(q.get("limit", "20")), 200), status=q.get("status") or None), "enabled": writes.writes_enabled()})


async def api_get(request: Request) -> Response:
    try:
        return ok(writes.get_full(request.path_params["id"]))
    except KeyError as exc:
        return err(str(exc), 404)


def _confirmed(data: dict[str, Any], cid: str) -> bool:
    return data.get("confirm") == cid


async def api_apply(request: Request) -> Response:
    cid = request.path_params["id"]
    data = await body(request)
    if not _confirmed(data, cid):
        return err("Zur Bestätigung muss der Körper {\"confirm\": \"<changeset_id>\"} enthalten.", 428)
    try:
        return ok(await writes.apply(cid, by=user_of(request) or "app"))
    except WriteError as exc:
        return err(str(exc))
    except KeyError as exc:
        return err(str(exc), 404)


async def api_rollback(request: Request) -> Response:
    cid = request.path_params["id"]
    data = await body(request)
    if not _confirmed(data, cid):
        return err("Zur Bestätigung muss der Körper {\"confirm\": \"<changeset_id>\"} enthalten.", 428)
    try:
        return ok(await writes.rollback(cid, by=user_of(request) or "app"))
    except WriteError as exc:
        return err(str(exc))
    except KeyError as exc:
        return err(str(exc), 404)


STATUS_LABEL = {"proposed": "Vorschlag – noch nicht übernommen", "applied": "Übernommen", "rolled_back": "Zurückgenommen"}


def render_changes_page(env, cid: str) -> str:
    doc = writes.get_full(cid)
    rows = []
    for it in doc.get("items", []):
        cols = sorted(set(it.get("before", {})) | set(it.get("after", {})))
        rows.append({
            "table": writes.TABLE_LABELS.get(it["table"], it["table"]), "id": it.get("id") or it.get("inserted_id"), "action": "neu" if it["action"] == "insert" else "ändern",
            "key": " · ".join(f"{writes._label_val(k, v)}" for k, v in (it.get("key") or {}).items() if v not in (None, "")),
            "link": f"https://vogelring.com/entries/{it['id']}" if it["table"] == "sightings" and it.get("id") else None,
            "changes": [{"field": writes.FIELD_LABELS.get(c, c), "before": writes._label_val(c, it.get("before", {}).get(c)) if it["action"] == "update" else "–", "after": writes._label_val(c, it.get("after", {}).get(c))} for c in cols if c != "org_id"],
        })
    return env.get_template("changes.html").render(doc=doc, rows=rows, status_label=STATUS_LABEL.get(doc.get("status"), doc.get("status")), ops=doc.get("operations", []))


routes: list[Route] = [
    Route("/api/changes", api_list),
    Route("/api/changes/plan", api_plan, methods=["POST"]),
    Route("/api/changes/{id}", api_get),
    Route("/api/changes/{id}/apply", api_apply, methods=["POST"]),
    Route("/api/changes/{id}/rollback", api_rollback, methods=["POST"]),
]
