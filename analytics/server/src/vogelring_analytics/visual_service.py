"""Reusable rendering pipeline for charts, maps and tables (shared by MCP tools, pipelines, workbooks, REST)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from . import runtime
from .charts import ChartBuildError, build_chart_model
from .events import bus
from .maps import MapBuildError, build_map_model
from .settings import settings
from .specs import ChartSpec, MapSpec, TableSpec
from .tables import TableBuildError, build_table_model
from .visuals import VisualMeta

log = logging.getLogger(__name__)

KIND_LABEL = {"map": "Karte", "chart": "Diagramm", "table": "Tabelle"}


class VisualError(ValueError):
    """Spec/data problem or rendering failure; the message is user-facing (German)."""


@dataclass
class VisualOut:
    meta: VisualMeta
    urls: dict[str, str]
    summary: dict[str, Any]
    inline: bytes
    inline_mime: str
    data_basis: str
    text: str
    kind: str = "chart"
    updated: bool = False
    structured: dict[str, Any] = field(default_factory=dict)


def visual_urls(visual_id: str) -> dict[str, str]:
    base = settings.public_base_url
    return {
        "interactive_url": f"{base}/viz/{visual_id}",
        "embed_url": f"{base}/viz/{visual_id}?embed=1",
        "png_url": f"{base}/viz/{visual_id}.png",
        "pdf_url": f"{base}/viz/{visual_id}.pdf",
        "xlsx_url": f"{base}/viz/{visual_id}.xlsx",
    }


def kind_of(spec_obj: ChartSpec | MapSpec | TableSpec) -> str:
    if isinstance(spec_obj, ChartSpec):
        return "chart"
    if isinstance(spec_obj, TableSpec):
        return "table"
    return "map"


def build_model(kind: str, spec_obj: ChartSpec | MapSpec | TableSpec) -> tuple[dict[str, Any], dict[str, Any], list[str]]:
    """Model + summary + dataset ids for a spec (no rendering)."""
    datasets = runtime.datasets()
    try:
        if kind == "chart":
            df = datasets.load(spec_obj.dataset_id)  # type: ignore[union-attr]
            model, summary = build_chart_model(spec_obj, df)  # type: ignore[arg-type]
            return model, summary, [spec_obj.dataset_id]  # type: ignore[union-attr]
        if kind == "table":
            df = datasets.load(spec_obj.dataset_id)  # type: ignore[union-attr]
            model, summary = build_table_model(spec_obj, df)  # type: ignore[arg-type]
            return model, summary, [spec_obj.dataset_id]  # type: ignore[union-attr]
        model, summary = build_map_model(spec_obj, datasets)  # type: ignore[arg-type]
        ids = [p.dataset_id for p in spec_obj.points] + [t.dataset_id for t in spec_obj.tracks] + [f.dataset_id for f in spec_obj.flows]  # type: ignore[union-attr]
        return model, summary, list(dict.fromkeys(ids))
    except KeyError as exc:
        raise VisualError(str(exc)) from exc
    except (ChartBuildError, MapBuildError, TableBuildError) as exc:
        raise VisualError(f"{KIND_LABEL.get(kind, kind)} konnte nicht gebaut werden: {exc}") from exc


async def create_visual(kind: str, spec_obj: ChartSpec | MapSpec | TableSpec, *, visual_id: str | None = None, patch: dict | None = None, view_id: str | None = None) -> VisualOut:
    """Build the model, store spec+model, render PNG/inline/PDF and publish an event. Identical to the former
    server._render_and_store, but returns data instead of a CallToolResult."""
    if kind not in KIND_LABEL:
        raise VisualError(f"Unbekannte Visualisierungsart: {kind}")
    datasets = runtime.datasets()
    visuals = runtime.visuals()
    spec_dict = spec_obj.model_dump(mode="json", by_alias=True, exclude_none=True)
    model, summary, dataset_ids = build_model(kind, spec_obj)

    width = int(model.get("width", getattr(spec_obj, "width", 1200)))
    height = int(model.get("height", getattr(spec_obj, "height", 700)))
    title = spec_obj.title
    if visual_id:
        meta = visuals.update(visual_id, spec_dict, model, title=title, dataset_ids=dataset_ids, width=width, height=height, summary=summary, patch=patch or {})
    else:
        meta = visuals.create(kind, spec_dict, model, title=title, dataset_ids=dataset_ids, width=width, height=height, summary=summary)

    urls = visual_urls(meta.id)
    try:
        out = await runtime.renderer().render_visual(meta.id, width, height, photographic=(kind == "map"))
    except Exception as exc:
        log.exception("render failed for %s", meta.id)
        raise VisualError(f"Rendering fehlgeschlagen: {exc}. Die interaktive Seite funktioniert evtl. trotzdem: {urls['interactive_url']}") from exc
    visuals.write_bytes(meta.id, "image.png", out.png_hi)
    visuals.write_bytes(meta.id, "inline.jpg" if out.inline_mime == "image/jpeg" else "inline.png", out.inline)
    visuals.write_bytes(meta.id, "image.pdf", out.pdf)

    label = KIND_LABEL[kind]
    notes = summary.get("notes") or []
    data_basis = ""
    try:
        data_basis = datasets.meta(dataset_ids[0]).description if dataset_ids else ""
    except KeyError:
        pass
    text = (
        f"{label} {'aktualisiert' if visual_id else 'erstellt'}: visual_id={meta.id}\n"
        f"Interaktiv: {urls['interactive_url']}\nPNG (2x): {urls['png_url']}\nPDF: {urls['pdf_url']}\n"
        f"Zusammenfassung: {json.dumps({k: v for k, v in summary.items() if k != 'notes'}, ensure_ascii=False, default=str)}"
        + (("\nHinweise: " + " ".join(notes)) if notes else "")
        + ((f"\nDatengrundlage: {data_basis}") if data_basis else "")
    )
    structured = {"visual_id": meta.id, "kind": kind, **urls, "summary": summary, "data_basis": data_basis}
    bus.publish(
        "visual.updated" if visual_id else "visual.created",
        f"{label} {'aktualisiert' if visual_id else 'erstellt'}: {title or meta.id}",
        visual_id=meta.id, kind=kind, label=title, view_id=view_id, **urls,
    )
    return VisualOut(meta=meta, urls=urls, summary=summary, inline=out.inline, inline_mime=out.inline_mime, data_basis=data_basis, text=text, kind=kind, updated=bool(visual_id), structured=structured)


async def render_view(view_spec: Any, *, visual_id: str | None = None, view_id: str | None = None) -> tuple[Any, VisualOut]:
    """views.build_view → create_visual. Returns (ViewResult, VisualOut)."""
    from . import views  # lazy: written by a sibling module

    result = await views.build_view(view_spec)
    kind = getattr(result, "visual_kind", None) or kind_of(result.visual_spec)
    out = await create_visual(kind, result.visual_spec, visual_id=visual_id, view_id=view_id)
    return result, out
