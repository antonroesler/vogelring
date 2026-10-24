"""REST routes for the Tableau-style engine: sources, views, workbooks, pipelines, decks, reports."""

from __future__ import annotations

import logging
from typing import Any

from pydantic import ValidationError
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route

from . import engine, runtime
from .api import body, err, ok, user_of, validation_message
from .decks import DeckSpec
from .reports import ReportSpec
from .sources import FilterSpec, SourceError, choices, describe_sources, get_source
from .views import dimension_options
from .workbooks import WorkbookSpec

log = logging.getLogger(__name__)


async def _handle(coro):
    try:
        return ok(await coro)
    except engine.EngineError as exc:
        return err(str(exc))
    except KeyError as exc:
        return err(str(exc), 404)
    except SourceError as exc:
        return err(str(exc))
    except Exception as exc:  # keep the app usable; details in the log
        log.exception("api failure")
        return err(f"Interner Fehler: {str(exc)[:200]}", 500)


# ---------------------------------------------------------------- sources


async def api_sources(request: Request) -> Response:
    return ok(describe_sources())


async def api_dimensions(request: Request) -> Response:
    return ok({"items": dimension_options(request.path_params["source"])})


async def api_choices(request: Request) -> Response:
    """GET ?q=&limit= lists global counts; POST {q, limit, filters} lists counts within the other active filters."""
    source, column = request.path_params["source"], request.path_params["column"]
    data = await body(request) if request.method == "POST" else {}
    q = data.get("q") if data.get("q") is not None else request.query_params.get("q", "")
    limit = int(data.get("limit") or request.query_params.get("limit", "50"))
    try:
        get_source(source)
        filters = FilterSpec.model_validate(data.get("filters") or {}) if data.get("filters") else None
        items = await choices(source, column, search=q or "", limit=min(limit, 500), filters=filters)
    except (SourceError, ValidationError) as exc:
        return err(str(exc) if isinstance(exc, SourceError) else validation_message(exc))
    return ok({"items": items})


# ---------------------------------------------------------------- views


async def api_view_preview(request: Request) -> Response:
    data = await body(request)
    try:
        spec = engine.parse_view(data.get("spec") or data)
    except engine.EngineError as exc:
        return err(str(exc))
    return await _handle(engine.preview(spec, max_rows=int(data.get("max_rows") or 5000)))


async def api_view_create(request: Request) -> Response:
    data = await body(request)
    try:
        spec = engine.parse_view(data.get("spec") or {})
    except engine.EngineError as exc:
        return err(str(exc))

    async def run():
        out = await engine.create_view(spec, title=data.get("title"), owner=user_of(request), project=data.get("project", ""), tags=data.get("tags") or [], render=bool(data.get("render", True)), by=user_of(request) or "app")
        out.pop("_inline", None)
        return out

    return await _handle(run())


async def api_view_update(request: Request) -> Response:
    data = await body(request)
    vid = request.path_params["id"]

    async def run():
        if "spec" in data:
            spec = engine.parse_view(data["spec"])
            item = runtime.catalog().get("view", vid)
            out = await engine.create_view(spec, title=data.get("title") or item.title, owner=item.owner, project=item.project, tags=item.tags, view_id=vid, render=bool(data.get("render", True)), by=user_of(request) or "app")
        else:
            out = await engine.update_view(vid, data.get("patch") or {}, by=user_of(request) or "app")
        out.pop("_inline", None)
        return out

    return await _handle(run())


async def api_views_list(request: Request) -> Response:
    q = request.query_params
    items = runtime.catalog().list("view", limit=min(int(q.get("limit", "50")), 500), search=q.get("q", ""), project=q.get("project", ""))
    return ok({"items": [engine.view_summary(i) for i in items]})


# ---------------------------------------------------------------- workbooks


async def api_workbook_save(request: Request) -> Response:
    data = await body(request)
    wid = request.path_params.get("id")
    try:
        spec = engine.parse_workbook(data.get("spec") or data)
        item = engine.save_workbook(spec, workbook_id=wid, owner=user_of(request), project=data.get("project", ""), tags=data.get("tags") or [], by=user_of(request) or "app")
    except engine.EngineError as exc:
        return err(str(exc))
    return ok(item.full())


async def api_workbook_render(request: Request) -> Response:
    wid = request.path_params["id"]
    render = request.query_params.get("render", "1") == "1"

    async def run():
        out = await engine.render_workbook_by_id(wid, render=render)
        out.pop("_result", None)
        out.pop("_spec", None)
        return out

    return await _handle(run())


async def api_workbook_report(request: Request) -> Response:
    return await _handle(engine.workbook_report(request.path_params["id"]))


async def api_workbook_deck(request: Request) -> Response:
    return await _handle(engine.workbook_deck(request.path_params["id"]))


# ---------------------------------------------------------------- pipelines


async def api_pipelines_list(request: Request) -> Response:
    q = request.query_params
    items = runtime.catalog().list("pipeline", limit=min(int(q.get("limit", "100")), 500), search=q.get("q", ""))
    return ok({"items": [engine.pipeline_summary(i) for i in items]})


async def api_pipeline_save(request: Request) -> Response:
    data = await body(request)
    pid = request.path_params.get("id")
    try:
        spec = engine.parse_pipeline(data.get("spec") or data)
        item = engine.save_pipeline(spec, pipeline_id=pid, owner=user_of(request), project=data.get("project", ""), by=user_of(request) or "app")
    except engine.EngineError as exc:
        return err(str(exc))
    return ok(engine.pipeline_summary(item))


async def api_pipeline_run(request: Request) -> Response:
    data = await body(request)
    return await _handle(engine.run_pipeline_by_id(request.path_params["id"], data.get("params") or {}, by=user_of(request) or "app"))


async def api_runs_list(request: Request) -> Response:
    q = request.query_params
    items = runtime.catalog().list("run", limit=min(int(q.get("limit", "30")), 300), search=q.get("q", ""))
    pid = q.get("pipeline")
    return ok({"items": [i.full() for i in items if not pid or i.doc.get("pipeline_id") == pid]})


# ---------------------------------------------------------------- groups (gespeicherte Auswahlen)


async def api_groups_list(request: Request) -> Response:
    q = request.query_params
    return ok({"items": engine.list_groups(limit=min(int(q.get("limit", "200")), 500), search=q.get("q", ""))})


async def api_group_create(request: Request) -> Response:
    data = await body(request)
    try:
        spec = engine.parse_group(data.get("spec") or data)
        return ok(engine.create_group(spec, owner=user_of(request), project=data.get("project", ""), by=user_of(request) or "app"))
    except engine.EngineError as exc:
        return err(str(exc))


async def api_group_get(request: Request) -> Response:
    try:
        return ok(engine.get_group(request.path_params["id"]))
    except KeyError as exc:
        return err(str(exc), 404)


async def api_group_update(request: Request) -> Response:
    data = await body(request)
    gid = request.path_params["id"]
    try:
        if "spec" in data:
            spec = engine.parse_group(data["spec"])
            item = runtime.catalog().get("group", gid)
            return ok(engine.create_group(spec, group_id=gid, owner=item.owner, project=item.project, by=user_of(request) or "app"))
        return ok(engine.update_group(gid, data.get("patch") or {}, by=user_of(request) or "app"))
    except engine.EngineError as exc:
        return err(str(exc))
    except KeyError as exc:
        return err(str(exc), 404)


async def api_group_exclude(request: Request) -> Response:
    data = await body(request)
    try:
        return ok(engine.set_group_exclusions(request.path_params["id"], [str(x) for x in (data.get("ids") or [])], bool(data.get("excluded", True)), by=user_of(request) or "app"))
    except engine.EngineError as exc:
        return err(str(exc))
    except KeyError as exc:
        return err(str(exc), 404)


async def api_group_summary(request: Request) -> Response:
    return await _handle(engine.group_stats(request.path_params["id"]))


async def api_group_preview(request: Request) -> Response:
    q = request.query_params
    return await _handle(engine.group_preview(request.path_params["id"], limit=int(q.get("limit", "50")), offset=int(q.get("offset", "0")), with_excluded=q.get("with_excluded") == "1"))


async def api_groups_compare(request: Request) -> Response:
    data = await body(request)
    ids = [str(x) for x in (data.get("group_ids") or data.get("ids") or [])]
    return await _handle(engine.compare_groups(ids, metric=data.get("metric") or "sightings", dimension=data.get("dimension") or "year", chart_kind=data.get("chart_kind") or "bar", title=data.get("title"), save=bool(data.get("save")), by=user_of(request) or "app"))


async def api_groups_import_legacy(request: Request) -> Response:
    data = await body(request)
    directory = data.get("dir") or request.query_params.get("dir") or "/data/legacy_datasets"
    try:
        return ok(engine.import_legacy_groups(directory, by=user_of(request) or "app"))
    except engine.EngineError as exc:
        return err(str(exc))


# ---------------------------------------------------------------- reports / decks


async def api_report_create(request: Request) -> Response:
    data = await body(request)
    try:
        spec = ReportSpec.model_validate(data.get("spec") or data)
    except ValidationError as exc:
        return err("Bericht ungültig: " + validation_message(exc))
    return await _handle(engine.create_report(spec, by=user_of(request) or "app"))


async def api_decks_list(request: Request) -> Response:
    return ok({"items": [engine.deck_summary(m) for m in runtime.decks().list(min(int(request.query_params.get("limit", "30")), 200))]})


async def api_deck_create(request: Request) -> Response:
    data = await body(request)
    if data.get("report_id"):
        return await _handle(engine.deck_from_report_id(data["report_id"], by=user_of(request) or "app"))
    try:
        spec = DeckSpec.model_validate(data.get("spec") or data)
    except ValidationError as exc:
        return err("Präsentation ungültig: " + validation_message(exc))
    return await _handle(engine.create_deck(spec, by=user_of(request) or "app"))


routes: list[Route] = [
    Route("/api/sources", api_sources),
    Route("/api/sources/{source}/dimensions", api_dimensions),
    Route("/api/sources/{source}/choices/{column}", api_choices, methods=["GET", "POST"]),
    Route("/api/views", api_views_list),
    Route("/api/views/preview", api_view_preview, methods=["POST"]),
    Route("/api/views", api_view_create, methods=["POST"]),
    Route("/api/views/{id}", api_view_update, methods=["PUT", "PATCH"]),
    Route("/api/workbooks", api_workbook_save, methods=["POST"]),
    Route("/api/workbooks/{id}", api_workbook_save, methods=["PUT"]),
    Route("/api/workbooks/{id}/render", api_workbook_render, methods=["POST", "GET"]),
    Route("/api/workbooks/{id}/report", api_workbook_report, methods=["POST"]),
    Route("/api/workbooks/{id}/deck", api_workbook_deck, methods=["POST"]),
    Route("/api/pipelines", api_pipelines_list),
    Route("/api/pipelines", api_pipeline_save, methods=["POST"]),
    Route("/api/pipelines/{id}", api_pipeline_save, methods=["PUT"]),
    Route("/api/pipelines/{id}/run", api_pipeline_run, methods=["POST"]),
    Route("/api/runs", api_runs_list),
    Route("/api/groups", api_groups_list),
    Route("/api/groups", api_group_create, methods=["POST"]),
    Route("/api/groups/compare", api_groups_compare, methods=["POST"]),
    Route("/api/groups/import-legacy", api_groups_import_legacy, methods=["POST"]),
    Route("/api/groups/{id}", api_group_get),
    Route("/api/groups/{id}", api_group_update, methods=["PUT", "PATCH"]),
    Route("/api/groups/{id}/summary", api_group_summary),
    Route("/api/groups/{id}/preview", api_group_preview),
    Route("/api/groups/{id}/exclude", api_group_exclude, methods=["POST"]),
    Route("/api/reports", api_report_create, methods=["POST"]),
    Route("/api/decks", api_decks_list),
    Route("/api/decks", api_deck_create, methods=["POST"]),
]
