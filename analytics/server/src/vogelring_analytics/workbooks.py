"""Workbooks („Mappen“): a grid of saved or inline views with shared filters; exportable as report or deck."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator

from .events import bus


class _Spec(BaseModel):
    model_config = ConfigDict(extra="forbid")


class TileSpec(_Spec):
    view_id: str | None = Field(None, description="Gespeicherte Ansicht (Katalog-ID vw_…).")
    view: dict[str, Any] | None = Field(None, description="Inline-Ansicht (ViewSpec als JSON) statt view_id.")
    title: str | None = Field(None, description="Überschrift der Kachel (Standard: Titel der Ansicht).")
    w: int = Field(6, ge=1, le=12, description="Breite in Rasterspalten (12 = volle Breite).")
    h: int = Field(1, ge=1, le=3, description="Höhe in Rasterzeilen.")
    note: str | None = Field(None, description="Markdown-Text unter der Kachel (Einordnung für den Leser).")

    @model_validator(mode="after")
    def _one_of(self) -> "TileSpec":
        if bool(self.view_id) == bool(self.view):
            raise ValueError("Eine Kachel braucht genau eines von view_id oder view.")
        return self


class WorkbookSpec(_Spec):
    title: str
    description: str = ""
    filters: dict[str, Any] = Field(default_factory=dict, description="Gemeinsame Filter (FilterSpec als JSON) für alle Kacheln.")
    tiles: list[TileSpec] = Field(default_factory=list)
    notes: str | None = Field(None, description="Markdown-Einleitung der Mappe.")


@dataclass
class TileResult:
    tile: TileSpec
    view_spec: Any  # effective ViewSpec (shared filters merged)
    result: Any  # views.ViewResult
    visual: Any | None = None  # visual_service.VisualOut
    error: str | None = None


@dataclass
class WorkbookResult:
    spec: WorkbookSpec
    tiles: list[TileResult] = field(default_factory=list)

    @property
    def visual_ids(self) -> list[str]:
        return [t.visual.meta.id for t in self.tiles if t.visual is not None]


# ---------------------------------------------------------------- filters


def _as_dict(f: Any) -> dict[str, Any]:
    if f is None:
        return {}
    if hasattr(f, "model_dump"):
        return f.model_dump(mode="json", exclude_none=True)
    return {k: v for k, v in dict(f).items() if v is not None}


def merge_filters(base: Any, override: Any) -> Any:
    """Shared (base) filters merged over a tile's own filters: lists are unioned (order kept, base first),
    scalars from the base win when set, dicts merged recursively. Returns the base's type (FilterSpec or dict)."""
    b, o = _as_dict(base), _as_dict(override)
    merged: dict[str, Any] = dict(o)
    for k, v in b.items():
        if v is None or v == [] or v == "":
            continue
        ov = merged.get(k)
        if isinstance(v, list):
            seen = list(v) + [x for x in (ov or []) if x not in v] if isinstance(ov, list) else list(v)
            merged[k] = seen
        elif isinstance(v, dict) and isinstance(ov, dict):
            merged[k] = merge_filters(v, ov)
        else:
            merged[k] = v
    if hasattr(base, "model_validate"):
        return type(base).model_validate(merged)
    return merged


# ---------------------------------------------------------------- rendering


def _load_view_spec(tile: TileSpec, catalog: Any) -> dict[str, Any]:
    if tile.view is not None:
        return dict(tile.view)
    item = catalog.get("view", tile.view_id)
    return dict(item.doc)


def effective_view(spec: WorkbookSpec, tile: TileSpec, catalog: Any) -> Any:
    """ViewSpec instance for a tile with the workbook's shared filters applied."""
    from . import views  # lazy

    doc = _load_view_spec(tile, catalog)
    doc["filters"] = merge_filters(spec.filters, doc.get("filters") or {})
    if tile.title:
        doc["title"] = tile.title
    return views.ViewSpec.model_validate(doc)


async def render_workbook(spec: WorkbookSpec, *, catalog: Any, render: bool = True) -> WorkbookResult:
    """Build every tile (dataset + model); with render=True also create the visual files. Errors are kept per tile."""
    from . import views, visual_service  # lazy

    out = WorkbookResult(spec=spec)
    for tile in spec.tiles:
        try:
            vs = effective_view(spec, tile, catalog)
        except Exception as exc:
            out.tiles.append(TileResult(tile=tile, view_spec=None, result=None, error=f"Ansicht ungültig: {exc}"))
            continue
        try:
            result = await views.build_view(vs)
            visual = None
            if render:
                kind = getattr(result, "visual_kind", None) or visual_service.kind_of(result.visual_spec)
                visual = await visual_service.create_visual(kind, result.visual_spec, view_id=tile.view_id)
            out.tiles.append(TileResult(tile=tile, view_spec=vs, result=result, visual=visual))
        except Exception as exc:
            out.tiles.append(TileResult(tile=tile, view_spec=vs, result=None, error=str(exc)))
    ok = sum(1 for t in out.tiles if t.error is None)
    if render:  # a plain preview (app page view) is not an activity worth announcing
        bus.publish("workbook.rendered", f"Mappe „{spec.title}“ aufgebaut: {ok} von {len(spec.tiles)} Kacheln", label=spec.title, tiles=len(spec.tiles), ok=ok, visual_ids=out.visual_ids)
    return out


# ---------------------------------------------------------------- exports


def _tile_title(t: TileResult) -> str:
    return t.tile.title or getattr(t.view_spec, "title", None) or (t.visual.meta.title if t.visual else None) or "Ansicht"


def workbook_to_report(spec: WorkbookSpec, result: WorkbookResult) -> Any:
    """One report section per tile: the tile note as text, the rendered visual as a numbered figure."""
    from .reports import ReportSpec

    sections = []
    for t in result.tiles:
        if t.error is not None:
            continue
        text = t.tile.note or ""
        if not text and t.result is not None and getattr(t.result, "description", None):
            text = t.result.description
        sections.append({"heading": _tile_title(t), "text": text, "visual_ids": [t.visual.meta.id] if t.visual else []})
    if not sections:
        sections.append({"heading": "Ergebnisse", "text": "Keine Kachel konnte aufgebaut werden."})
    return ReportSpec(title=spec.title, subtitle=spec.description or None, sections=sections, methods_note=spec.notes)


def workbook_to_deck(spec: WorkbookSpec, result: WorkbookResult) -> dict[str, Any]:
    """DeckSpec-shaped dict: title slide, then one figure slide per tile (caption = tile note or data basis)."""
    slides: list[dict[str, Any]] = [{"kind": "title", "title": spec.title, "bullets": [spec.description] if spec.description else []}]
    if spec.notes:
        slides.append({"kind": "text", "title": "Einführung", "bullets": [spec.notes]})
    for t in result.tiles:
        if t.error is not None or t.visual is None:
            continue
        caption = t.tile.note or (getattr(t.result, "description", None) if t.result is not None else None) or t.visual.data_basis or None
        slides.append({"kind": "figure", "title": _tile_title(t), "visual_ids": [t.visual.meta.id], "caption": caption})
    return {"title": spec.title, "subtitle": spec.description or None, "slides": slides, "include_methods": True}
