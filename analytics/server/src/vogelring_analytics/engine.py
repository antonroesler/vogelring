"""Service layer shared by the MCP tools and the REST API, so the agent and the web app behave identically.

Every operation here writes to the shared stores/catalog and publishes an event, which is what makes the live
mirror work: whatever the agent does in the chat shows up in the app, and vice versa.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from pydantic import ValidationError

from . import runtime
from .catalog import CatalogItem
from .decks import DeckBuildError, DeckSpec, build_deck, deck_from_report, deck_urls
from .events import bus
from .pipelines import PipelineError, PipelineSpec, describe_pipeline, run_pipeline, validate_params
from .reports import ReportBuildError, ReportSpec, build_report_model, write_docx
from .settings import settings
from .groups import GroupError, GroupSpec, defining_condition, group_condition, legacy_id, legacy_to_spec, read_legacy_dir, resolve_group
from .sources import FilterSpec, SourceError, get_source
from .views import ViewError, ViewSpec, build_view, preview_view
from .visual_service import VisualError, VisualOut, create_visual, kind_of, visual_urls
from .visuals import merge_patch
from .workbooks import WorkbookSpec, render_workbook, workbook_to_deck, workbook_to_report

log = logging.getLogger(__name__)


class EngineError(ValueError):
    """User-facing (German) error."""


def validation_message(exc: ValidationError) -> str:
    return "; ".join(".".join(str(p) for p in e["loc"]) + ": " + e["msg"] for e in exc.errors())


def _item_out(item: CatalogItem, **extra: Any) -> dict[str, Any]:
    return {**item.full(), **extra}


# ---------------------------------------------------------------- views


def parse_view(doc: dict[str, Any]) -> ViewSpec:
    try:
        return ViewSpec.model_validate(doc)
    except ValidationError as exc:
        raise EngineError(f"Ansicht ungültig: {validation_message(exc)}") from exc


async def preview(spec: ViewSpec, max_rows: int = 5000) -> dict[str, Any]:
    """Build the model without rendering or saving – for the live builder in the app."""
    try:
        res = await preview_view(spec, max_rows=max_rows)
    except (ViewError, ValueError) as exc:
        raise EngineError(str(exc)) from exc
    return {"kind": res.visual_kind, "model": res.model, "summary": res.summary, "dataset_id": res.dataset_id, "description": res.description, "row_count": res.row_count, "sql": res.sql, "notes": res.notes, "visual_spec": res.spec_dict(), "describe": spec.describe()}


async def create_view(spec: ViewSpec, *, title: str | None = None, owner: str = "", project: str = "", tags: list[str] | None = None, view_id: str | None = None, render: bool = True, by: str = "") -> dict[str, Any]:
    """Save a view in the catalog and (optionally) render it to a visual. Re-saving with view_id updates in place."""
    cat = runtime.catalog()
    label = title or spec.title or spec.describe()
    doc = spec.model_dump(mode="json", by_alias=True, exclude_none=True)
    prev = cat.get("view", view_id) if view_id and cat.exists("view", view_id) else None
    visual: VisualOut | None = None
    result = None
    extra: dict[str, Any] = dict(prev.extra) if prev else {}
    if render:
        try:
            result = await build_view(spec)
            kind = result.visual_kind or kind_of(result.visual_spec)
            visual = await create_visual(kind, result.visual_spec, visual_id=extra.get("visual_id"), view_id=view_id)
        except (ViewError, VisualError, ValueError) as exc:
            raise EngineError(str(exc)) from exc
        extra.update({"visual_id": visual.meta.id, "dataset_id": result.dataset_id, "description": result.description, "summary": result.summary, "row_count": result.row_count})
    item = cat.put("view", doc, id=view_id, title=label, description=(result.description if result else extra.get("description", "")), owner=owner, project=project, tags=tags or [], extra=extra)
    bus.publish("view.updated" if prev else "view.created", f"Ansicht {'aktualisiert' if prev else 'erstellt'}: {label}", id=item.id, view_id=item.id, visual_id=extra.get("visual_id"), kind=spec.kind, by=by or owner or "agent")
    out = _item_out(item)
    if visual:
        out["visual"] = {"visual_id": visual.meta.id, "kind": visual.kind, "summary": visual.summary, "data_basis": visual.data_basis, **visual.urls}
        out["_inline"] = (visual.inline, visual.inline_mime)
    return out


async def update_view(view_id: str, patch: dict[str, Any], *, by: str = "") -> dict[str, Any]:
    cat = runtime.catalog()
    item = cat.get("view", view_id)
    merged = merge_patch(item.doc, patch)
    spec = parse_view(merged)
    return await create_view(spec, title=patch.get("title") or item.title, owner=item.owner, project=item.project, tags=item.tags, view_id=view_id, by=by)


def view_summary(item: CatalogItem) -> dict[str, Any]:
    d = item.summary()
    d["visual_id"] = item.extra.get("visual_id")
    d["kind"] = item.doc.get("kind", "chart")
    d["source"] = item.doc.get("source", "sightings")
    if d["visual_id"]:
        d.update(visual_urls(d["visual_id"]))
    return d


# ---------------------------------------------------------------- workbooks


def parse_workbook(doc: dict[str, Any]) -> WorkbookSpec:
    try:
        return WorkbookSpec.model_validate(doc)
    except ValidationError as exc:
        raise EngineError(f"Mappe ungültig: {validation_message(exc)}") from exc


def save_workbook(spec: WorkbookSpec, *, workbook_id: str | None = None, owner: str = "", project: str = "", tags: list[str] | None = None, by: str = "") -> CatalogItem:
    cat = runtime.catalog()
    prev = workbook_id and cat.exists("workbook", workbook_id)
    item = cat.put("workbook", spec.model_dump(mode="json", by_alias=True, exclude_none=True), id=workbook_id, title=spec.title, description=spec.description, owner=owner, project=project, tags=tags or [])
    bus.publish("workbook.updated" if prev else "workbook.created", f"Mappe {'aktualisiert' if prev else 'erstellt'}: {spec.title}", id=item.id, workbook_id=item.id, tiles=len(spec.tiles), by=by or owner or "agent")
    return item


async def render_workbook_by_id(workbook_id: str, *, render: bool = True) -> dict[str, Any]:
    cat = runtime.catalog()
    item = cat.get("workbook", workbook_id)
    spec = parse_workbook(item.doc)
    try:
        res = await render_workbook(spec, catalog=cat, render=render)
    except (ViewError, VisualError, ValueError) as exc:
        raise EngineError(str(exc)) from exc
    tiles = []
    for t in res.tiles:
        tile: dict[str, Any] = {"tile": t.tile.model_dump(mode="json", exclude_none=True), "error": t.error}
        if t.result is not None:
            tile.update({"kind": t.result.visual_kind, "model": t.result.model, "summary": t.result.summary, "dataset_id": t.result.dataset_id, "description": t.result.description, "row_count": t.result.row_count, "title": t.tile.title or getattr(t.view_spec, "title", None) or (t.view_spec.describe() if hasattr(t.view_spec, "describe") else "")})
        if t.visual is not None:
            tile["visual"] = {"visual_id": t.visual.meta.id, **t.visual.urls}
        tiles.append(tile)
    if render:
        cat.put("workbook", item.doc, id=item.id, title=item.title, description=item.description, owner=item.owner, project=item.project, tags=item.tags,
                extra={"last_render": {"visual_ids": res.visual_ids, "tiles": [{"visual_id": t.get("visual", {}).get("visual_id"), "dataset_id": t.get("dataset_id"), "error": t.get("error")} for t in tiles]}})
    return {"workbook": item.summary(), "spec": spec.model_dump(mode="json", exclude_none=True), "tiles": tiles, "visual_ids": res.visual_ids, "_result": res, "_spec": spec}


async def workbook_report(workbook_id: str) -> dict[str, Any]:
    r = await render_workbook_by_id(workbook_id)
    spec = workbook_to_report(r["_spec"], r["_result"])
    return await create_report(spec)


async def workbook_deck(workbook_id: str) -> dict[str, Any]:
    r = await render_workbook_by_id(workbook_id)
    return await create_deck(DeckSpec.model_validate(workbook_to_deck(r["_spec"], r["_result"])))


# ---------------------------------------------------------------- reports


async def create_report(spec: ReportSpec, *, by: str = "") -> dict[str, Any]:
    visuals, datasets, store = runtime.visuals(), runtime.datasets(), runtime.reports()
    try:
        model, summary = build_report_model(spec, visuals, datasets)
    except (ReportBuildError, KeyError) as exc:
        raise EngineError(str(exc)) from exc
    dataset_ids = [d["id"] for d in model["datasets"]]
    visual_ids = [it["id"] for s in model["sections"] for it in s["blocks"] if it.get("id")]
    meta = store.create(spec.model_dump(mode="json", by_alias=True, exclude_none=True), model, {"title": spec.title, "visual_ids": visual_ids, "dataset_ids": dataset_ids, "sections": len(model["sections"])})
    base = settings.public_base_url
    files: dict[str, str] = {"html": f"{base}/reports/{meta.id}"}
    try:
        pdf = await runtime.renderer().render_pdf(f"/reports/{meta.id}?print=1", title=spec.title)
        store.write_bytes(meta.id, "report.pdf", pdf)
        files["pdf"] = f"{base}/reports/{meta.id}.pdf"
    except Exception as exc:
        log.exception("report pdf failed")
        files["pdf_error"] = str(exc)[:200]
    try:
        write_docx(model, store.dir(meta.id) / "report.docx", visuals)
        files["docx"] = f"{base}/reports/{meta.id}.docx"
    except Exception as exc:
        log.exception("report docx failed")
        files["docx_error"] = str(exc)[:200]
    bus.publish("report.created", f"Bericht erstellt: {spec.title}", report_id=meta.id, id=meta.id, **{k: v for k, v in files.items() if not k.endswith("_error")}, by=by or "agent")
    return {"report_id": meta.id, "title": spec.title, **files, **summary}


# ---------------------------------------------------------------- decks


async def create_deck(spec: DeckSpec, *, by: str = "") -> dict[str, Any]:
    try:
        meta = build_deck(spec, visuals=runtime.visuals(), datasets=runtime.datasets(), store=runtime.decks())
    except (DeckBuildError, KeyError) as exc:
        raise EngineError(str(exc)) from exc
    return {"deck_id": meta.id, "title": meta.title, "slides": meta.slides, **deck_urls(meta.id)}


async def deck_from_report_id(report_id: str, *, by: str = "") -> dict[str, Any]:
    store = runtime.reports()
    if not store.exists(report_id):
        raise EngineError(f"Unbekannter Bericht: {report_id}")
    spec = deck_from_report(store.model(report_id))
    return await create_deck(spec, by=by)


def deck_summary(meta) -> dict[str, Any]:
    return {"deck_id": meta.id, "title": meta.title, "created_at": meta.created_at, "slides": meta.slides, **deck_urls(meta.id)}


# ---------------------------------------------------------------- pipelines


def parse_pipeline(doc: dict[str, Any]) -> PipelineSpec:
    try:
        return PipelineSpec.model_validate(doc)
    except ValidationError as exc:
        raise EngineError(f"Auswertung ungültig: {validation_message(exc)}") from exc


def save_pipeline(spec: PipelineSpec, *, pipeline_id: str | None = None, owner: str = "", project: str = "", by: str = "") -> CatalogItem:
    cat = runtime.catalog()
    prev = pipeline_id and cat.exists("pipeline", pipeline_id)
    item = cat.put("pipeline", spec.model_dump(mode="json", by_alias=True, exclude_none=True), id=pipeline_id, title=spec.name, description=spec.description, owner=owner, project=project, tags=spec.tags)
    bus.publish("pipeline.updated" if prev else "pipeline.created", f"Auswertung {'aktualisiert' if prev else 'angelegt'}: {spec.name}", id=item.id, pipeline_id=item.id, by=by or owner or "agent")
    return item


def pipeline_summary(item: CatalogItem) -> dict[str, Any]:
    d = item.summary()
    d["parameters"] = item.doc.get("parameters", [])
    d["icon"] = item.doc.get("icon")
    d["steps"] = len(item.doc.get("steps", []))
    try:
        d["describe"] = describe_pipeline(PipelineSpec.model_validate(item.doc))
    except ValidationError:
        d["describe"] = item.description
    return d


async def run_pipeline_by_id(pipeline_id: str, params: dict[str, Any] | None, *, by: str = "") -> dict[str, Any]:
    cat = runtime.catalog()
    item = cat.get("pipeline", pipeline_id)
    spec = parse_pipeline(item.doc)
    try:
        clean = validate_params(spec, params or {})
    except PipelineError as exc:
        raise EngineError(str(exc)) from exc
    res = await run_pipeline(spec, clean)
    run = res.to_dict()
    run["pipeline_id"] = pipeline_id
    run["pipeline_name"] = spec.name
    cat.put("run", run, id=res.run_id, title=f"{spec.name} – {res.started_at[:16].replace('T', ' ')}", description=("Fehler: " + res.error) if res.error else "; ".join(run["log"][-3:]), owner=by, project=item.project, tags=[pipeline_id, res.status])
    return run


def seed_builtin_pipelines() -> int:
    """Insert the built-in Auswertungen once (by name) so the app has cards from day one."""
    from .pipelines import builtin_specs

    cat = runtime.catalog()
    existing = {i.title for i in cat.list("pipeline", limit=500)}
    n = 0
    for spec in builtin_specs():
        if spec.name in existing:
            continue
        cat.put("pipeline", spec.model_dump(mode="json", by_alias=True, exclude_none=True), title=spec.name, description=spec.description, owner="system", tags=spec.tags + ["eingebaut"])
        n += 1
    return n


# ---------------------------------------------------------------- notes / navigation


def save_note(text: str, *, title: str | None = None, note_id: str | None = None, project: str = "", tags: list[str] | None = None, by: str = "") -> CatalogItem:
    cat = runtime.catalog()
    prev = note_id and cat.exists("note", note_id)
    item = cat.put("note", {"text": text}, id=note_id, title=title or text.strip().splitlines()[0][:80], owner=by, project=project, tags=tags or [])
    bus.publish("note.updated" if prev else "note.created", f"Notiz: {item.title}", id=item.id, project=project, by=by or "agent")
    return item


ROUTES = {"group": "gruppen", "view": "ansichten", "workbook": "mappen", "pipeline": "auswertungen", "run": "ergebnisse", "report": "berichte", "deck": "praesentationen", "visual": "grafiken", "dataset": "daten", "page": ""}


def show_in_app(target: str, oid: str | None = None, *, title: str | None = None, by: str = "agent") -> dict[str, Any]:
    labels = {"group": "Gruppe", "view": "Ansicht", "workbook": "Mappe", "pipeline": "Auswertung", "run": "Ergebnis", "report": "Bericht", "deck": "Präsentation", "visual": "Grafik", "dataset": "Datensatz", "page": "Seite"}
    bus.publish("navigate", title or f"Zeige {labels.get(target, target)}", target=target, id=oid, by=by)
    return {"ok": True, "url": f"{settings.public_base_url}/app/#/{ROUTES.get(target, target)}/{oid}" if oid else f"{settings.public_base_url}/app/"}


# ---------------------------------------------------------------- groups (gespeicherte Auswahlen)

GROUP_METRICS = {"sightings": "Sichtungen", "birds": "Vögel"}
_FILTER_DEFAULTS = FilterSpec().model_dump()
GROUP_DIMENSIONS = ("group", "year", "month", "season", "status", "place", "age", "ringing_place", "distance_class", "year_month")


def parse_group(doc: dict[str, Any]) -> GroupSpec:
    try:
        return GroupSpec.model_validate(doc)
    except ValidationError as exc:
        raise EngineError(f"Gruppe ungültig: {validation_message(exc)}") from exc


def group_summary(item: CatalogItem) -> dict[str, Any]:
    """Cheap list entry (no DB access)."""
    d = item.summary()
    doc = item.doc or {}
    f = doc.get("filters") or {}
    try:
        spec = GroupSpec.model_validate(doc)
        describe = spec.describe()
    except ValidationError:
        describe = "ungültige Gruppe"
    d.update({
        "name": item.title, "color": doc.get("color"), "describe": describe, "scope": doc.get("scope") or "sightings", "ring_count": len(doc.get("ring_list") or []),
        "excluded_count": len(doc.get("excluded_ids") or []), "filter_count": sum(1 for k, v in f.items() if v not in (None, [], "", False) and v != _FILTER_DEFAULTS.get(k)),
        "stats": (item.extra or {}).get("stats"),
    })
    return d


def create_group(spec: GroupSpec, *, group_id: str | None = None, owner: str = "", project: str = "", by: str = "", extra: dict[str, Any] | None = None) -> dict[str, Any]:
    cat = runtime.catalog()
    prev = cat.get("group", group_id) if group_id and cat.exists("group", group_id) else None
    doc = spec.model_dump(mode="json", exclude_none=True, exclude_defaults=True)  # compact: only what was set
    ex = dict(prev.extra) if prev else {}
    if extra:
        ex.update(extra)
    ex.pop("stats", None)  # recomputed on the next summary request
    item = cat.put("group", doc, id=group_id, title=spec.name, description=spec.description, owner=owner, project=project, tags=spec.tags, extra=ex)
    bus.publish("group.updated" if prev else "group.created", f"Gruppe {'aktualisiert' if prev else 'angelegt'}: {spec.name}", id=item.id, group_id=item.id, describe=spec.describe(), by=by or owner or "agent")
    return {**group_summary(item), "doc": item.doc}


def update_group(group_id: str, patch: dict[str, Any], *, by: str = "") -> dict[str, Any]:
    cat = runtime.catalog()
    item = cat.get("group", group_id)
    spec = parse_group(merge_patch(item.doc, patch))
    return create_group(spec, group_id=group_id, owner=item.owner, project=item.project, by=by)


def get_group(group_id: str) -> dict[str, Any]:
    item = runtime.catalog().get("group", group_id)
    return {**group_summary(item), "doc": item.doc}


def list_groups(limit: int = 100, search: str = "") -> list[dict[str, Any]]:
    return [group_summary(i) for i in runtime.catalog().list("group", limit=limit, search=search)]


def set_group_exclusions(group_id: str, ids: list[str], excluded: bool, *, by: str = "") -> dict[str, Any]:
    """Exclude or re-include individual sightings by id."""
    item = runtime.catalog().get("group", group_id)
    cur = [str(x) for x in (item.doc.get("excluded_ids") or [])]
    ids = [str(x).strip() for x in ids if str(x).strip()]
    new = cur + [x for x in ids if x not in cur] if excluded else [x for x in cur if x not in ids]
    return update_group(group_id, {"excluded_ids": new}, by=by)


async def group_stats(group_id: str) -> dict[str, Any]:
    """Live numbers from the read-only database; cached in the item's extra for the list page."""
    cat = runtime.catalog()
    item, spec = resolve_group(group_id)
    source = get_source("sightings")
    try:
        cond, params = group_condition(source, spec)
    except SourceError as exc:
        raise EngineError(str(exc)) from exc
    db = runtime.database()
    base = f"FROM ({source.base_sql}) s WHERE {cond}"
    matching: int | None = None
    try:
        tot = await db.query(f"SELECT COUNT(*) AS n, COUNT(DISTINCT ring) AS birds, COUNT(DISTINCT place) AS places, MIN(date) AS first, MAX(date) AS last {base}", params=tuple(params))
        if spec.scope == "birds":
            inner, iparams = defining_condition(source, spec)
            m = await db.query(f"SELECT COUNT(*) {base} AND {inner}", params=tuple(params) + tuple(iparams))
            matching = int(m.rows[0][0] or 0) if m.rows else 0
        sp = await db.query(f"SELECT COALESCE(species, 'unbekannt') AS k, COUNT(*) AS n, COUNT(DISTINCT ring) AS birds {base} GROUP BY 1 ORDER BY 2 DESC LIMIT 8", params=tuple(params))
        st = await db.query(f"SELECT COALESCE(status, 'ohne') AS k, COUNT(*) AS n {base} GROUP BY 1 ORDER BY 2 DESC LIMIT 8", params=tuple(params))
        yr = await db.query(f"SELECT EXTRACT(YEAR FROM date)::int AS k, COUNT(*) AS n {base} GROUP BY 1 ORDER BY 1", params=tuple(params))
    except Exception as exc:
        raise EngineError(f"Abfrage fehlgeschlagen: {str(exc).strip()[:300]}") from exc

    def _v(x: Any) -> Any:
        x = x.item() if hasattr(x, "item") else x
        return x.isoformat()[:10] if hasattr(x, "isoformat") else x

    row = tot.rows[0] if tot.rows else (0, 0, 0, None, None)
    stats = {
        "scope": spec.scope, "matching_sightings": matching,
        "sightings": int(row[0] or 0), "birds": int(row[1] or 0), "places": int(row[2] or 0), "first": _v(row[3]), "last": _v(row[4]),
        "species": [{"label": _v(k), "sightings": int(n), "birds": int(b)} for k, n, b in sp.rows],
        "status": [{"label": _v(k), "sightings": int(n)} for k, n in st.rows],
        "years": [{"year": int(_v(k)), "sightings": int(n)} for k, n in yr.rows if k is not None],
        "computed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    ex = dict(item.extra)
    ex["stats"] = stats
    cat.put("group", item.doc, id=item.id, title=item.title, description=item.description, owner=item.owner, project=item.project, tags=item.tags, extra=ex)
    return {"group_id": item.id, "name": item.title, "describe": spec.describe(), **stats}


GROUP_PREVIEW_COLUMNS = ["id", "date", "ring", "species", "place", "status", "age", "melder", "ringing_place"]


async def group_preview(group_id: str, *, limit: int = 50, offset: int = 0, with_excluded: bool = False) -> dict[str, Any]:
    """Rows of the group (paged). with_excluded=True also returns hand-excluded rows, flagged, so they can be re-included."""
    item, spec = resolve_group(group_id)
    source = get_source("sightings")
    try:
        cond, params = group_condition(source, spec, with_exclusions=not with_excluded)
    except SourceError as exc:
        raise EngineError(str(exc)) from exc
    limit = max(1, min(int(limit), 500))
    offset = max(0, int(offset))
    cols = ", ".join(GROUP_PREVIEW_COLUMNS)
    sel_params: list[Any] = []
    if spec.scope == "birds":
        # flag the rows that themselves satisfy the rule (the „defining“ sightings) vs. the birds' other sightings
        inner, sel_params = defining_condition(source, spec)
        cols += f", ({inner}) AS matches"
    db = runtime.database()
    try:
        cnt = await db.query(f"SELECT COUNT(*) FROM ({source.base_sql}) s WHERE {cond}", params=tuple(params))
        res = await db.query(f"SELECT {cols} FROM ({source.base_sql}) s WHERE {cond} ORDER BY date DESC, ring LIMIT {limit} OFFSET {offset}", params=tuple(sel_params) + tuple(params))
    except Exception as exc:
        raise EngineError(f"Abfrage fehlgeschlagen: {str(exc).strip()[:300]}") from exc
    excluded = set(spec.excluded_ids)
    rows = []
    for r in res.rows:
        d = {}
        for k, v in zip(res.columns, r):
            v = v.item() if hasattr(v, "item") else v
            d[k] = v.isoformat()[:10] if hasattr(v, "isoformat") else (str(v) if k == "id" else v)
        d["excluded"] = d["id"] in excluded
        rows.append(d)
    return {"group_id": item.id, "name": item.title, "scope": spec.scope, "columns": GROUP_PREVIEW_COLUMNS, "rows": rows, "total": int(cnt.rows[0][0]) if cnt.rows else 0, "offset": offset, "limit": limit, "with_excluded": with_excluded}


COMBINE_OPS = {"union": "Vereinigung", "intersection": "Schnittmenge", "difference": "Differenz"}


def combine_groups(name: str, op: str, group_ids: list[str], *, scope: str = "sightings", description: str = "", color: str | None = None, by: str = "") -> dict[str, Any]:
    """A new group built from existing ones: union (in at least one), intersection (in all), difference (first minus the rest).

    The new group references the others, so it follows their later changes."""
    if op not in COMBINE_OPS:
        raise EngineError(f"Unbekannte Verknüpfung „{op}“. Erlaubt: {', '.join(COMBINE_OPS)}.")
    try:
        items = [resolve_group(g)[0] for g in group_ids if g and str(g).strip()]
    except SourceError as exc:
        raise EngineError(str(exc)) from exc
    if len(items) < 2:
        raise EngineError("Bitte mindestens zwei Gruppen angeben.")
    ids = [i.id for i in items]
    names = [i.title for i in items]
    if op == "union":
        filters: dict[str, Any] = {"groups": ids}
        auto = "Alles aus " + " oder ".join(f"„{n}“" for n in names)
    elif op == "intersection":
        filters = {"all_groups": ids}
        auto = "Nur, was zugleich in " + " und ".join(f"„{n}“" for n in names) + " liegt"
    else:
        filters = {"groups": ids[:1], "exclude_groups": ids[1:]}
        auto = f"„{names[0]}“ ohne " + " und ohne ".join(f"„{n}“" for n in names[1:])
    spec = parse_group({"name": name, "description": description or auto, "filters": filters, "scope": scope, "color": color, "tags": ["Verknüpfung"]})
    return create_group(spec, by=by)


def compare_spec(group_ids: list[str], *, metric: str = "sightings", dimension: str = "year", chart_kind: str = "bar", title: str | None = None) -> ViewSpec:
    """A view that puts several groups side by side: dimension „Gruppe“ alone, or any dimension with colour = Gruppe."""
    ids = [g for g in group_ids if g and str(g).strip()]
    if not ids:
        raise EngineError("Bitte mindestens eine Gruppe angeben.")
    if dimension not in GROUP_DIMENSIONS:
        raise EngineError(f"Aufteilung „{dimension}“ ist für Vergleiche nicht vorgesehen. Erlaubt: {', '.join(GROUP_DIMENSIONS)}.")
    kwargs: dict[str, Any] = {"metric": {"kind": metric}, "filters": {"groups": ids}, "chart_kind": chart_kind, "show_values": True}
    if dimension == "group":
        kwargs["dimension"] = "group"
    else:
        kwargs.update({"dimension": dimension, "color": "group"})
        if chart_kind == "bar":
            kwargs["chart_kind"] = "bar"
    if title:
        kwargs["title"] = title
    return parse_view({"kind": "chart", "source": "sightings", **kwargs})


async def compare_groups(group_ids: list[str], *, metric: str = "sightings", dimension: str = "year", chart_kind: str = "bar", title: str | None = None, save: bool = False, by: str = "") -> dict[str, Any]:
    spec = compare_spec(group_ids, metric=metric, dimension=dimension, chart_kind=chart_kind, title=title)
    names = [resolve_group(g)[0].title for g in group_ids]
    label = title or f"Vergleich: {' · '.join(names)}"
    if save:
        return await create_view(spec, title=label, by=by)
    out = await preview(spec)
    out["title"] = label
    out["spec"] = spec.model_dump(mode="json", exclude_none=True)
    return out


def import_legacy_groups(directory: str | Any, *, by: str = "import") -> dict[str, Any]:
    """Port the old app's dataset JSONs; idempotent (ids derive from the legacy name), never silently drops filters."""
    from pathlib import Path

    d = Path(directory)
    if not d.is_dir():
        raise EngineError(f"Verzeichnis nicht gefunden: {d}")
    try:
        files = read_legacy_dir(d)
    except GroupError as exc:
        raise EngineError(str(exc)) from exc
    cat = runtime.catalog()
    results = []
    for fname, doc in files:
        try:
            spec, notes = legacy_to_spec(doc)
        except GroupError as exc:
            results.append({"file": fname, "status": "error", "error": str(exc)})
            continue
        gid = legacy_id(spec.name)
        existed = cat.exists("group", gid)
        if existed:
            prev = cat.get("group", gid)
            keep = GroupSpec.model_validate(prev.doc)
            spec.color = keep.color or spec.color  # colours chosen in the app survive re-imports
            if keep.description and not spec.description:
                spec.description = keep.description
        out = create_group(spec, group_id=gid, by=by, extra={"legacy_file": fname, "legacy_name": doc.get("name"), "import_notes": notes})
        results.append({"file": fname, "status": "updated" if existed else "created", "group_id": out["id"], "name": spec.name, "describe": spec.describe(), "notes": notes, "empty": spec.is_empty()})
    bus.publish("log", f"{len(results)} alte Gruppen importiert", by=by)
    return {"count": len(results), "items": results}
