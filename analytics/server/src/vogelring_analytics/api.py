"""REST API for the Analytics 2.0 web app (/api/…) and the live event stream (/api/live).

The web app and the MCP tools are two clients of the same engine: both read and write the same stores, and every
change is published on the event bus so the app mirrors the agent in real time.
"""

from __future__ import annotations

import asyncio
import json
import logging
from typing import Any

from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response, StreamingResponse
from starlette.routing import Route

from . import runtime
from .catalog import KINDS
from .datasets import column_summary, preview_table
from .definitions import Definition, DefinitionError
from .events import bus
from .settings import settings

log = logging.getLogger(__name__)


# ---------------------------------------------------------------- helpers


def user_of(request: Request) -> str:
    """Identity from Cloudflare Access (single-tenant for now; recorded as owner)."""
    return request.headers.get("cf-access-authenticated-user-email", "") or request.headers.get("x-user-email", "")


def ok(data: Any, status: int = 200) -> JSONResponse:
    return JSONResponse(data, status_code=status, headers={"Cache-Control": "no-store"})


def err(message: str, status: int = 400, **extra: Any) -> JSONResponse:
    return JSONResponse({"error": message, **extra}, status_code=status)


async def body(request: Request) -> dict[str, Any]:
    try:
        data = await request.json()
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def validation_message(exc: ValidationError) -> str:
    return "; ".join(".".join(str(p) for p in e["loc"]) + ": " + e["msg"] for e in exc.errors())


def visual_urls(visual_id: str) -> dict[str, str]:
    base = settings.public_base_url
    return {
        "interactive_url": f"{base}/viz/{visual_id}",
        "embed_url": f"{base}/viz/{visual_id}?embed=1",
        "png_url": f"{base}/viz/{visual_id}.png",
        "pdf_url": f"{base}/viz/{visual_id}.pdf",
        "xlsx_url": f"{base}/viz/{visual_id}.xlsx",
    }


# ---------------------------------------------------------------- meta


async def api_meta(request: Request) -> Response:
    cat = runtime.catalog()
    return ok({
        "app": "Vogelring Analyse",
        "version": "2.0",
        "user": user_of(request),
        "public_base_url": settings.public_base_url,
        "chat_url": settings.chat_url,
        "chat_agent_id": settings.chat_agent_id,
        "counts": cat.counts(),
    })


async def api_events(request: Request) -> Response:
    """Server-sent events: everything that happens in the engine, for the live mirror."""
    last = request.headers.get("last-event-id") or request.query_params.get("since")
    q = bus.subscribe()

    async def gen():
        try:
            yield "retry: 3000\n\n"
            if last and last.isdigit():
                for ev in bus.since(int(last)):
                    yield ev.sse()
            while True:
                try:
                    ev = await asyncio.wait_for(q.get(), timeout=25)
                    yield ev.sse()
                except asyncio.TimeoutError:
                    yield ": ping\n\n"
                if await request.is_disconnected():
                    break
        finally:
            bus.unsubscribe(q)

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


async def api_activity(request: Request) -> Response:
    limit = int(request.query_params.get("limit", "50"))
    types = [t for t in request.query_params.get("types", "").split(",") if t]
    return ok({"items": runtime.catalog().activity(limit=min(limit, 500), types=types)})


async def api_navigate(request: Request) -> Response:
    """Lets any client (agent tool or app) steer the analytics screen: {"target": "view"|"workbook"|…, "id": …}."""
    data = await body(request)
    target, oid = data.get("target"), data.get("id")
    if not target:
        return err("target fehlt")
    bus.publish("navigate", data.get("title") or f"Zeige {target} {oid or ''}".strip(), target=target, id=oid, by=user_of(request) or "agent")
    return ok({"ok": True})


# ---------------------------------------------------------------- catalog (views, workbooks, pipelines, runs, decks, notes, projects)


async def api_catalog_list(request: Request) -> Response:
    kind = request.path_params["kind"]
    if kind not in KINDS:
        return err("Unbekannte Objektart", 404)
    q = request.query_params
    items = runtime.catalog().list(kind, limit=min(int(q.get("limit", "50")), 500), offset=int(q.get("offset", "0")), search=q.get("q", ""), project=q.get("project", ""))
    full = q.get("full") == "1"
    return ok({"items": [i.full() if full else i.summary() for i in items]})


async def api_catalog_get(request: Request) -> Response:
    kind, oid = request.path_params["kind"], request.path_params["id"]
    try:
        return ok(runtime.catalog().get(kind, oid).full())
    except KeyError as exc:
        return err(str(exc), 404)


async def api_catalog_delete(request: Request) -> Response:
    kind, oid = request.path_params["kind"], request.path_params["id"]
    cat = runtime.catalog()
    try:
        item = cat.get(kind, oid)
    except KeyError as exc:
        return err(str(exc), 404)
    cat.delete(kind, oid)
    bus.publish(f"{kind}.deleted", f"Gelöscht: {item.title or oid}", kind=kind, id=oid, by=user_of(request))
    return ok({"deleted": oid})


async def api_catalog_pin(request: Request) -> Response:
    kind, oid = request.path_params["kind"], request.path_params["id"]
    data = await body(request)
    runtime.catalog().set_pinned(kind, oid, bool(data.get("pinned", True)))
    return ok({"id": oid, "pinned": bool(data.get("pinned", True))})


async def api_note_put(request: Request) -> Response:
    """Notes are the agent's and the user's long-term project memory (markdown)."""
    data = await body(request)
    text = (data.get("text") or "").strip()
    if not text:
        return err("text fehlt")
    oid = data.get("id") or request.path_params.get("id")
    item = runtime.catalog().put("note", {"text": text}, id=oid, title=data.get("title") or text.splitlines()[0][:80], description=data.get("description", ""), owner=user_of(request), project=data.get("project", ""), tags=data.get("tags") or [], pinned=data.get("pinned"))
    bus.publish("note.updated" if oid else "note.created", f"Notiz: {item.title}", id=item.id, project=item.project, by=user_of(request) or "agent")
    return ok(item.full())


# ---------------------------------------------------------------- definitions


async def api_definitions(request: Request) -> Response:
    return ok({"items": runtime.definitions().as_dicts()})


async def api_definition_put(request: Request) -> Response:
    data = await body(request)
    try:
        d = runtime.definitions().save(Definition(**{k: v for k, v in data.items() if k in Definition.__dataclass_fields__}))
    except (DefinitionError, TypeError) as exc:
        return err(str(exc))
    bus.publish("definition.saved", f"Begriff gespeichert: {d.name}", name=d.name, kind=d.kind, by=user_of(request))
    return ok({"saved": d.name, "kind": d.kind})


async def api_definition_delete(request: Request) -> Response:
    name = request.path_params["name"]
    deleted = runtime.definitions().delete(name)
    if deleted:
        bus.publish("definition.deleted", f"Begriff gelöscht: {name}", name=name, by=user_of(request))
    return ok({"deleted": deleted})


# ---------------------------------------------------------------- datasets / visuals / reports (file stores)


async def api_datasets(request: Request) -> Response:
    limit = min(int(request.query_params.get("limit", "30")), 200)
    return ok({"items": [{"dataset_id": m.id, "name": m.name, "description": m.description, "rows": m.row_count, "columns": m.columns, "created_at": m.created_at, "source": m.source} for m in runtime.datasets().list(limit)]})


async def api_dataset(request: Request) -> Response:
    ds = request.path_params["id"]
    store = runtime.datasets()
    try:
        meta = store.meta(ds)
        df = store.load(ds)
    except KeyError as exc:
        return err(str(exc), 404)
    q = request.query_params
    limit, offset = min(int(q.get("limit", "100")), 1000), int(q.get("offset", "0"))
    page = df.iloc[offset : offset + limit]
    rows = json.loads(page.to_json(orient="records", date_format="iso", force_ascii=False))
    return ok({"dataset_id": ds, "name": meta.name, "description": meta.description, "sql": meta.sql, "rows_total": meta.row_count, "columns": meta.columns, "rows": rows, "offset": offset, "stats": column_summary(df), "preview": preview_table(df, 5)})


async def api_dataset_export(request: Request) -> Response:
    ds = request.path_params["id"]
    store = runtime.datasets()
    try:
        meta = store.meta(ds)
        df = store.load(ds)
    except KeyError as exc:
        return err(str(exc), 404)
    from .exporters import safe_filename, write_csv, write_xlsx

    fmt = (await body(request)).get("format") or request.query_params.get("format") or "xlsx"
    name = f"{safe_filename(meta.name or 'export')}_{ds[-6:]}.{fmt}"
    path = settings.exports_dir / name
    if fmt == "csv":
        write_csv(df, path)
    else:
        title = f"{meta.name} – {meta.description}" if meta.description else meta.name
        write_xlsx(df, path, title=title)
    bus.publish("export.created", f"Export erstellt: {meta.name}", dataset_id=ds, url=f"{settings.public_base_url}/files/{name}", by=user_of(request) or "app")
    return ok({"url": f"{settings.public_base_url}/files/{name}", "filename": name, "rows": int(len(df)), "format": fmt})


async def api_visuals(request: Request) -> Response:
    limit = min(int(request.query_params.get("limit", "30")), 200)
    return ok({"items": [{"visual_id": m.id, "kind": m.kind, "title": m.title, "updated_at": m.updated_at, "dataset_ids": m.dataset_ids, "width": m.width, "height": m.height, "summary": m.summary, **visual_urls(m.id)} for m in runtime.visuals().list(limit)]})


async def api_visual(request: Request) -> Response:
    vid = request.path_params["id"]
    store = runtime.visuals()
    if not store.exists(vid):
        return err("Visualisierung nicht gefunden", 404)
    m = store.meta(vid)
    return ok({"visual_id": m.id, "kind": m.kind, "title": m.title, "updated_at": m.updated_at, "dataset_ids": m.dataset_ids, "width": m.width, "height": m.height, "summary": m.summary, "spec": store.spec(vid), "model": store.model(vid), **visual_urls(m.id)})


async def api_reports(request: Request) -> Response:
    base = settings.public_base_url
    return ok({"items": [{"report_id": m.id, "title": m.title, "created_at": m.created_at, "sections": m.sections, "html": f"{base}/reports/{m.id}", "pdf": f"{base}/reports/{m.id}.pdf", "docx": f"{base}/reports/{m.id}.docx"} for m in runtime.reports().list(min(int(request.query_params.get("limit", "30")), 200))]})


# ---------------------------------------------------------------- routes (extended by api_views in app.py)

routes: list[Route] = [
    Route("/api/meta", api_meta),
    Route("/api/live", api_events),
    Route("/api/activity", api_activity),
    Route("/api/navigate", api_navigate, methods=["POST"]),
    Route("/api/definitions", api_definitions),
    Route("/api/definitions", api_definition_put, methods=["POST", "PUT"]),
    Route("/api/definitions/{name}", api_definition_delete, methods=["DELETE"]),
    Route("/api/datasets", api_datasets),
    Route("/api/datasets/{id}", api_dataset),
    Route("/api/datasets/{id}/export", api_dataset_export, methods=["POST", "GET"]),
    Route("/api/visuals", api_visuals),
    Route("/api/visuals/{id}", api_visual),
    Route("/api/reports", api_reports),
    Route("/api/notes", api_note_put, methods=["POST"]),
    Route("/api/notes/{id}", api_note_put, methods=["PUT"]),
    Route("/api/{kind}", api_catalog_list),
    Route("/api/{kind}/{id}", api_catalog_get),
    Route("/api/{kind}/{id}", api_catalog_delete, methods=["DELETE"]),
    Route("/api/{kind}/{id}/pin", api_catalog_pin, methods=["POST"]),
]
