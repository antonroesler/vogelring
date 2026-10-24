"""ASGI application: web app (SPA), REST API + live events, MCP endpoint, visual/report/deck pages and downloads."""

from __future__ import annotations

import asyncio
import json
import logging
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape
from markupsafe import Markup, escape
from mcp.server.transport_security import TransportSecuritySettings
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import FileResponse, HTMLResponse, JSONResponse, PlainTextResponse, RedirectResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

from . import api, api_engine, api_writes, engine, runtime
from .events import bus
from .exporters import write_xlsx
from .gc import collect_garbage
from .server import mcp
from .settings import settings
from .tiles import close_client, tile

log = logging.getLogger(__name__)
_HERE = Path(__file__).parent
_env = Environment(loader=FileSystemLoader(_HERE / "render" / "templates"), autoescape=select_autoescape(["html"]))


def _md_inline(text: str) -> Markup:
    s = str(escape(text or ""))
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", s)
    return Markup(s)


_env.filters["md_inline"] = _md_inline

KIND_LABEL = {"map": "Karte", "chart": "Diagramm", "table": "Tabelle"}
TEMPLATE = {"map": "map.html", "chart": "chart.html", "table": "table.html"}


async def health(_: Request) -> JSONResponse:
    return JSONResponse({"status": "ok", "server": "vogelring-analytics", "version": mcp.version or ""})


def _visual_or_404(visual_id: str):
    store = runtime.visuals()
    if not store.exists(visual_id):
        return None, PlainTextResponse("Visualisierung nicht gefunden", status_code=404)
    return store, None


async def visual_page(request: Request) -> Response:
    vid = request.path_params["vid"]
    store, err = _visual_or_404(vid)
    if err:
        return err
    meta = store.meta(vid)
    model = store.model(vid)
    render = request.query_params.get("render") == "1"
    embed = request.query_params.get("embed") == "1"
    template = _env.get_template(TEMPLATE.get(meta.kind, "chart.html"))
    html = template.render(
        model=model,
        model_json=json.dumps(model, ensure_ascii=False),
        render=render,
        embed=embed,
        visual_id=vid,
        kind_label=KIND_LABEL.get(meta.kind, "Diagramm"),
        page_title=meta.title or KIND_LABEL.get(meta.kind, "Diagramm"),
        footer_right="vogelring.com · " + meta.updated_at[:10],
    )
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


async def visual_file(request: Request) -> Response:
    vid = request.path_params["vid"]
    ext = request.path_params["ext"]
    store, err = _visual_or_404(vid)
    if err:
        return err
    meta = store.meta(vid)
    stem = (meta.title or meta.kind).replace("/", "-")[:60]
    if ext in ("png", "pdf"):
        p = store.file(vid, f"image.{ext}")
        if not p:
            return PlainTextResponse("Noch nicht gerendert", status_code=404)
        return FileResponse(p, media_type="image/png" if ext == "png" else "application/pdf", filename=f"{stem}.{ext}")
    if ext == "xlsx":
        p = store.file(vid, "data.xlsx")
        if not p and meta.dataset_ids:
            datasets = runtime.datasets()
            try:
                df = datasets.load(meta.dataset_ids[0])
            except KeyError:
                return PlainTextResponse("Datensatz nicht mehr vorhanden", status_code=404)
            p = write_xlsx(df, store.dir(vid) / "data.xlsx", title=meta.title)
        if not p:
            return PlainTextResponse("Keine Daten", status_code=404)
        return FileResponse(p, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=f"{stem}.xlsx")
    if ext == "json":
        return JSONResponse({"visual_id": vid, "kind": meta.kind, "title": meta.title, "model": model_of(store, vid), "spec": store.spec(vid)})
    return PlainTextResponse("Unbekanntes Format", status_code=404)


def model_of(store, vid: str):
    return store.model(vid)


async def report_page(request: Request) -> Response:
    rid = request.path_params["rid"]
    store = runtime.reports()
    if not store.exists(rid):
        return PlainTextResponse("Bericht nicht gefunden", status_code=404)
    model = store.model(rid)
    html = _env.get_template("report.html").render(model=model, report_id=rid, print=request.query_params.get("print") == "1")
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


async def report_file(request: Request) -> Response:
    rid = request.path_params["rid"]
    ext = request.path_params["ext"]
    store = runtime.reports()
    if not store.exists(rid):
        return PlainTextResponse("Bericht nicht gefunden", status_code=404)
    meta = store.meta(rid)
    stem = re.sub(r"[^\w\- ]+", "_", meta.title)[:70].strip() or "Bericht"
    if ext == "pdf":
        p = store.file(rid, "report.pdf")
        return FileResponse(p, media_type="application/pdf", filename=f"{stem}.pdf") if p else PlainTextResponse("PDF nicht vorhanden", status_code=404)
    if ext == "docx":
        p = store.file(rid, "report.docx")
        return FileResponse(p, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document", filename=f"{stem}.docx") if p else PlainTextResponse("DOCX nicht vorhanden", status_code=404)
    return PlainTextResponse("Unbekanntes Format", status_code=404)


async def deck_file(request: Request) -> Response:
    did = request.path_params["did"]
    store = runtime.decks()
    if not store.exists(did):
        return PlainTextResponse("Präsentation nicht gefunden", status_code=404)
    meta = store.meta(did)
    p = store.file(did, "deck.pptx")
    if not p:
        return PlainTextResponse("PPTX nicht vorhanden", status_code=404)
    stem = re.sub(r"[^\w\- ]+", "_", meta.title)[:70].strip() or "Praesentation"
    return FileResponse(p, media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation", filename=f"{stem}.pptx")


async def changes_page(request: Request) -> Response:
    cid = request.path_params["cid"]
    try:
        html = api_writes.render_changes_page(_env, cid)
    except KeyError:
        return PlainTextResponse("Änderungsvorschlag nicht gefunden", status_code=404)
    return HTMLResponse(html, headers={"Cache-Control": "no-store"})


async def export_file(request: Request) -> Response:
    name = request.path_params["name"]
    if "/" in name or name.startswith(".") or ".." in name:
        return PlainTextResponse("Ungültiger Name", status_code=400)
    p = settings.exports_dir / name
    if not p.is_file():
        return PlainTextResponse("Datei nicht gefunden", status_code=404)
    return FileResponse(p, filename=name)


# ---------------------------------------------------------------- web app (SPA) with history fallback


class SPA(StaticFiles):
    """Static web app with history fallback. index.html is never cached (hashed assets are immutable anyway)."""

    async def get_response(self, path: str, scope):
        try:
            resp = await super().get_response(path, scope)
        except Exception:
            resp = await super().get_response("index.html", scope)
            resp.headers["Cache-Control"] = "no-store"
            return resp
        if path in ("", ".", "index.html") or path.endswith("/"):
            resp.headers["Cache-Control"] = "no-store"
        elif "/assets/" in path or path.startswith("assets/"):
            resp.headers["Cache-Control"] = "public, max-age=31536000, immutable"
        return resp


async def no_web(_: Request) -> Response:
    return HTMLResponse("<h1>Vogelring Analyse</h1><p>Die Web-App ist in diesem Build nicht enthalten (WEB_DIR fehlt). Die Schnittstellen unter /api, /mcp und /viz funktionieren.</p>", status_code=200)


# ---------------------------------------------------------------- lifespan

_security = TransportSecuritySettings(allowed_hosts=list(settings.allowed_hosts), allowed_origins=[])
mcp_app = mcp.streamable_http_app(transport_security=_security, json_response=False, stateless_http=True)


async def _gc_loop() -> None:
    while True:
        try:
            await asyncio.to_thread(collect_garbage)
        except Exception:
            log.exception("GC failed")
        await asyncio.sleep(6 * 3600)


@asynccontextmanager
async def lifespan(_: Starlette) -> AsyncIterator[None]:
    settings.ensure_dirs()
    cat = runtime.catalog()
    bus.bind(asyncio.get_running_loop(), persist=lambda ev: cat.log_event(ev.at, ev.type, ev.title, ev.payload))
    try:
        n = engine.seed_builtin_pipelines()
        if n:
            log.info("seeded %d built-in pipelines", n)
    except Exception:
        log.exception("seeding pipelines failed")
    gc_task = asyncio.create_task(_gc_loop())
    async with mcp.session_manager.run():
        try:
            yield
        finally:
            gc_task.cancel()
            await close_client()


web_routes: list = []
if settings.web_dir and (settings.web_dir / "index.html").exists():
    web_routes = [Mount("/app", app=SPA(directory=str(settings.web_dir), html=True), name="web")]
    index_route = Route("/", lambda r: RedirectResponse("/app/"))
else:
    index_route = Route("/", no_web)

app = Starlette(
    routes=[
        Route("/health", health),
        Mount("/static", StaticFiles(directory=str(_HERE / "render" / "static")), name="static"),
        Route("/viz/{vid}.{ext}", visual_file),
        Route("/viz/{vid}", visual_page),
        Route("/reports/{rid}.{ext}", report_file),
        Route("/reports/{rid}", report_page),
        Route("/decks/{did}.pptx", deck_file),
        Route("/changes/{cid}", changes_page),
        Route("/files/{name}", export_file),
        Route("/tiles/{style}/{z}/{x}/{y}.png", tile),
        *api_writes.routes,
        *api_engine.routes,
        *api.routes,
        *web_routes,
        index_route,
        Mount("/", app=mcp_app),
    ],
    lifespan=lifespan,
)


def main() -> None:
    import uvicorn

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    uvicorn.run("vogelring_analytics.app:app", host="0.0.0.0", port=settings.port, log_level="info")


if __name__ == "__main__":
    main()
