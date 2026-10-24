"""MCP server: tools for querying, analysing, charting, mapping, reporting and exporting Vogelring data."""

from __future__ import annotations

import base64
import json
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import date
from typing import Annotated, Any, Literal

from mcp.server import MCPServer
from mcp.server.mcpserver.exceptions import ToolError
from mcp.types import CallToolResult, ImageContent, TextContent, ToolAnnotations
from pydantic import Field, ValidationError

from . import analysis, engine, runtime
from .decks import DeckSpec
from .groups import GroupSpec, resolve_group
from .pipelines import PipelineSpec
from .sources import SourceError, choices, describe_sources
from .views import ViewSpec
from .visual_service import VisualError, VisualOut, create_visual, visual_urls
from .workbooks import WorkbookSpec
from . import writes
from .writes import Operation, WriteError
from .datasets import column_summary, preview_table
from .db import SqlRejected
from .definitions import Definition, DefinitionError, DefinitionKind
from .exporters import safe_filename, write_csv, write_xlsx
from .reports import ReportSpec
from .schema import SCHEMA_DOC
from .settings import settings
from .specs import ChartSpec, MapSpec, TableSpec
from .transforms import Op, TransformError, apply_ops, describe_ops
from .visuals import merge_patch

log = logging.getLogger(__name__)

INSTRUCTIONS = """\
Analytics-Werkzeuge für die Vogelring-Datenbank (Sichtungen beringter Gänse, Frankfurt/Rhein-Main) und die Analyse-App
(analytics.vogelring.com), die der Nutzer parallel offen haben kann: alles, was du erstellst, erscheint dort sofort.
Bevorzugter Weg (ohne SQL): create_view mit Datenquelle + Filtern + „was zählen / aufteilen nach / Farbe nach“ → Diagramm,
Karte oder Tabelle (gespeichert als Ansicht). Mehrere Ansichten → create_workbook (Mappe) → workbook_report / workbook_deck.
Wiederverwendbare Rezepte mit Parametern: save_pipeline (erscheint als Karte in der App), run_pipeline.
Fertige Analysen: bird_profile, cohort_resighting, site_fidelity, dispersal, seasonality, companions, whats_new, data_quality.
Freie Fragen: query_sql (liefert dataset_id) → create_chart / create_map / create_table → update_visual → create_report / create_deck.
Jeder Datensatz trägt eine Beschreibung in Alltagssprache; sie landet in Berichten. Begriffe des Nutzers als Definitionen
speichern (save_definition) und als {{Name}} bzw. place_groups/periods in Filtern verwenden. Mit show_in_app lenkst du den
Bildschirm des Nutzers auf das, worüber du sprichst. Du schreibst nie Rendering-Code.
Änderungen an Vogelring-Daten (z. B. Ring → Farbring umstellen, Ort umbenennen) laufen NUR über propose_changes (Probelauf,
schreibt nichts) → Ergebnis dem Nutzer in Alltagssprache erklären (Anzahl, Felder, Vorschau-Link) → apply_changes (der Nutzer
bestätigt den Aufruf im Chat). Jede übernommene Änderung ist mit rollback_changes rücknehmbar. Nie löschen.
"""


@dataclass
class AppState:
    ready: bool = True


@asynccontextmanager
async def lifespan(_: MCPServer) -> AsyncIterator[AppState]:
    settings.ensure_dirs()
    db = runtime.database()
    await db.open()
    try:
        await runtime.renderer().start()
    except Exception as exc:  # the server still answers queries without a browser
        log.exception("Renderer failed to start: %s", exc)
    try:
        yield AppState()
    finally:
        await runtime.renderer().stop()
        await db.close()


mcp = MCPServer("vogelring-analytics", instructions=INSTRUCTIONS, lifespan=lifespan, version="2.0.0")

READ_ONLY = ToolAnnotations(read_only_hint=True, open_world_hint=False)
CREATES = ToolAnnotations(read_only_hint=False, destructive_hint=False, idempotent_hint=False, open_world_hint=False)
DESTRUCTIVE = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=True, open_world_hint=False)

Description = Annotated[
    str,
    Field(
        description=(
            "Datengrundlage in Alltagssprache für Nicht-Techniker (1–2 Sätze): WAS wurde gezählt und WIE gefiltert, "
            "z. B. 'Alle Sichtungen von Kanadagänsen im Ostpark zwischen Mai und Juni 2025; jede Ablesung zählt einmal.' "
            "Wird in Berichten, Exporten und Bildunterschriften verwendet."
        )
    ),
]


_urls = visual_urls


def _dataset_payload(meta, df, preview_rows: int) -> dict[str, Any]:
    out: dict[str, Any] = {
        "dataset_id": meta.id,
        "name": meta.name,
        "description": meta.description,
        "row_count": meta.row_count,
        "columns": meta.columns,
        "preview": preview_table(df, preview_rows),
        "column_stats": column_summary(df),
    }
    if meta.truncated:
        out["warning"] = f"Result truncated to {settings.max_rows} rows. Aggregate in SQL or add filters."
    return out


# ------------------------------------------------------------------ data tools


@mcp.tool(title="Datenwörterbuch", annotations=READ_ONLY)
def describe_schema() -> str:
    """Return the data dictionary (tables, columns, conventions, pitfalls) plus the saved definitions ({{Name}} macros)."""
    return SCHEMA_DOC + "\n\n## Gespeicherte Definitionen (in SQL als {{Name}} verwendbar)\n" + runtime.definitions().describe()


@mcp.tool(title="SQL-Abfrage ausführen", annotations=READ_ONLY)
async def query_sql(
    sql: Annotated[str, Field(description="Single read-only SELECT/WITH statement (PostgreSQL). Prefer v_sightings. May use {{Definition}} macros.")],
    name: Annotated[str, Field(description="Short German name for the result, e.g. 'Wiederfunde Ostpark Mai/Jun 2025'.")] = "",
    description: Description = "",
    preview_rows: Annotated[int, Field(ge=0, le=200, description="How many rows to show inline.")] = 25,
) -> dict[str, Any]:
    """Run a read-only query. Returns a dataset_id (use it in create_chart/create_map/create_table/export_dataset), the
    columns, row count, a preview and per-column statistics. Results are capped at 50 000 rows. Always fill `description`
    in plain German so readers of reports understand the data basis."""
    db = runtime.database()
    try:
        expanded, used = runtime.definitions().expand(sql)
    except DefinitionError as exc:
        raise ToolError(str(exc)) from exc
    try:
        result = await db.query(expanded)
    except SqlRejected as exc:
        raise ToolError(f"SQL rejected: {exc}") from exc
    except Exception as exc:
        raise ToolError(f"Query failed: {str(exc).strip()}") from exc
    df = result.to_frame()
    meta = runtime.datasets().save(df, name=name or "Abfrage", sql=expanded, truncated=result.truncated, description=description, extra={"definitions": used, "sql_template": sql})
    out = _dataset_payload(meta, df, preview_rows)
    if used:
        out["definitions_used"] = used
    return out


@mcp.tool(title="Datensatz anzeigen", annotations=READ_ONLY)
def get_dataset(
    dataset_id: str,
    limit: Annotated[int, Field(ge=1, le=500)] = 100,
    offset: Annotated[int, Field(ge=0)] = 0,
    columns: Annotated[list[str] | None, Field(description="Subset of columns to show.")] = None,
) -> str:
    """Show rows of a stored dataset (paged). Use sparingly; prefer aggregating in SQL or transform_dataset."""
    try:
        df = runtime.datasets().load(dataset_id)
    except KeyError as exc:
        raise ToolError(str(exc)) from exc
    if columns:
        missing = [c for c in columns if c not in df.columns]
        if missing:
            raise ToolError(f"Unknown columns: {', '.join(missing)}")
        df = df[columns]
    page = df.iloc[offset : offset + limit]
    return f"Zeilen {offset + 1}–{offset + len(page)} von {len(df)}\n" + preview_table(page, limit)


@mcp.tool(title="Datensätze auflisten", annotations=READ_ONLY)
def list_datasets(limit: Annotated[int, Field(ge=1, le=50)] = 10) -> list[dict[str, Any]]:
    """List recently created datasets (id, name, description, rows, columns)."""
    return [
        {"dataset_id": m.id, "name": m.name, "description": m.description, "rows": m.row_count, "columns": [c["name"] for c in m.columns], "created_at": m.created_at}
        for m in runtime.datasets().list(limit)
    ]


@mcp.tool(title="Datensatz umformen", annotations=CREATES)
def transform_dataset(
    dataset_id: str,
    ops: Annotated[list[Op], Field(min_length=1, description="Steps applied in order: filter, select, rename, derive (year/month/season/distance_km/bucket/ratio…), group, sort, head, distinct, pivot, join, rank.")],
    name: Annotated[str, Field(description="German name of the result.")] = "",
    description: Description = "",
) -> dict[str, Any]:
    """Filter, group, pivot, join or derive columns on a stored dataset without SQL; returns a new dataset_id.
    Typical: derive season/month from a date, bucket distances, group by place with count_distinct ring, join two results."""
    store = runtime.datasets()
    try:
        df = store.load(dataset_id)
        src = store.meta(dataset_id)
        out = apply_ops(df, ops, store)
    except KeyError as exc:
        raise ToolError(str(exc)) from exc
    except (TransformError, ValueError, TypeError) as exc:
        raise ToolError(f"Transform failed: {exc}") from exc
    desc = description or f"{src.description} Danach: {describe_ops(ops)}.".strip()
    meta = store.save(out, name=name or f"{src.name} (umgeformt)", sql=src.sql, description=desc, source="transform", extra={"from": dataset_id, "ops": [o.model_dump(by_alias=True, exclude_none=True) for o in ops]})
    return _dataset_payload(meta, out, 25)


@mcp.tool(title="Daten exportieren", annotations=CREATES)
def export_dataset(
    dataset_id: str,
    format: Literal["xlsx", "csv"] = "xlsx",
    filename: Annotated[str | None, Field(description="File name without extension (German, descriptive).")] = None,
    title: Annotated[str | None, Field(description="Title row inside the XLSX sheet.")] = None,
) -> dict[str, Any]:
    """Write a dataset as a formatted XLSX (or CSV) file and return its download URL. Put the URL in your answer."""
    store = runtime.datasets()
    try:
        df = store.load(dataset_id)
        meta = store.meta(dataset_id)
    except KeyError as exc:
        raise ToolError(str(exc)) from exc
    base = safe_filename(filename or meta.name or "export")
    name = f"{base}_{dataset_id[-6:]}.{format}"
    path = settings.exports_dir / name
    if format == "xlsx":
        t = title or meta.name
        if meta.description:
            t = f"{t} – {meta.description}"
        write_xlsx(df, path, title=t)
    else:
        write_csv(df, path)
    return {"url": f"{settings.public_base_url}/files/{name}", "filename": name, "rows": int(len(df)), "format": format}


# ------------------------------------------------------------------ definitions


@mcp.tool(title="Definition speichern", annotations=CREATES)
def save_definition(
    name: Annotated[str, Field(description="Name wie der Nutzer ihn verwendet, z. B. 'Nordufer', 'Mauserzeit', 'Kerngruppe'.")],
    kind: Annotated[DefinitionKind, Field(description="place_group: Orte (Teilstrings) · ring_group: Ringnummern · period: Monate ['5','6'] oder ['11-1'] und/oder date_from/date_to · filter: SQL-Bool-Fragment · note: nur Wissen, kein SQL.")],
    description: Annotated[str, Field(description="Bedeutung in einem Satz, wie der Nutzer es erklärt hat.")],
    values: Annotated[list[str] | None, Field(description="Orte, Ringe oder Monate (je nach kind).")] = None,
    sql: Annotated[str | None, Field(description="Nur kind=filter: Bool-Ausdruck über v_sightings-Spalten, z. B. \"species = 'Graugans' AND age = 1\".")] = None,
    date_from: Annotated[str | None, Field(description="period: YYYY-MM-DD")] = None,
    date_to: Annotated[str | None, Field(description="period: YYYY-MM-DD")] = None,
    default_column: Annotated[str | None, Field(description="Spalte, auf die {{Name}} standardmäßig angewendet wird (place, ring, date …).")] = None,
) -> dict[str, Any]:
    """Save (or overwrite) a named definition the user explained, so every later analysis means exactly the same thing.
    Use it whenever the user says what a group, area or period means. In SQL write {{Name}} or {{Name:column}}."""
    try:
        d = runtime.definitions().save(Definition(name=name, kind=kind, description=description, values=values or [], sql=sql, date_from=date_from, date_to=date_to, default_column=default_column))
    except DefinitionError as exc:
        raise ToolError(str(exc)) from exc
    example = None if d.kind == "note" else runtime.definitions().expand_one(d, None)
    return {"saved": d.name, "kind": d.kind, "usage": None if d.kind == "note" else f"{{{{{d.name}}}}}", "expands_to": example}


@mcp.tool(title="Definitionen auflisten", annotations=READ_ONLY)
def list_definitions() -> list[dict[str, Any]]:
    """List all saved definitions (name, kind, meaning, values). Check here before asking the user what a term means."""
    return runtime.definitions().as_dicts()


@mcp.tool(title="Definition löschen", annotations=DESTRUCTIVE)
def delete_definition(name: str) -> dict[str, Any]:
    """Delete a saved definition (only when the user asks)."""
    return {"deleted": runtime.definitions().delete(name), "name": name}


# ------------------------------------------------------------------ analyses


def _analysis(coro):
    async def run():
        try:
            return await coro
        except analysis.AnalysisError as exc:
            raise ToolError(str(exc)) from exc
        except SqlRejected as exc:
            raise ToolError(f"SQL rejected: {exc}") from exc
        except Exception as exc:
            log.exception("analysis failed")
            raise ToolError(f"Analyse fehlgeschlagen: {str(exc).strip()[:300]}") from exc

    return run()


@mcp.tool(title="Vogelprofil", annotations=READ_ONLY)
async def bird_profile(ring: Annotated[str, Field(description="Exact ring number, e.g. '2845731' or 'W1234'.")]) -> dict[str, Any]:
    """Everything about one bird: ringing data, number/period of sightings, places, farthest find, seasons, partners,
    family links, colour rings. Returns sightings_dataset_id for a map (create_map) or timeline (create_chart kind=timeline)."""
    return await _analysis(analysis.bird_profile(ring))


@mcp.tool(title="Wiederfundraten je Jahrgang", annotations=READ_ONLY)
async def cohort_resighting(
    species: Annotated[str | None, Field(description="Species as ringed (ringed_as_species), e.g. 'Kanadagans'.")] = None,
    ringing_place: Annotated[str | None, Field(description="Substring of the ringing place, e.g. 'Ostpark'.")] = None,
    year_from: Annotated[int | None, Field(description="First ringing year.")] = None,
    year_to: Annotated[int | None, Field(description="Last ringing year.")] = None,
    group_by: Literal["ringing_year", "species", "ringing_place", "ringing_age"] = "ringing_year",
) -> dict[str, Any]:
    """How many ringed birds were ever resighted, how fast, how long they stayed detectable (≥1 / ≥3 years later) and how
    far they went – per ringing year, species, place or age at ringing. Returns cohort_dataset_id (chart) and per_bird_dataset_id."""
    return await _analysis(analysis.cohort_resighting(species, ringing_place, year_from, year_to, group_by))


@mcp.tool(title="Ortstreue", annotations=READ_ONLY)
async def site_fidelity(
    place: Annotated[str, Field(description="Substring of the place name, e.g. 'Ostpark'.")],
    species: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> dict[str, Any]:
    """Site fidelity for one place: per bird the share of its sightings there and the years it was present; per year the
    return rate (seen there again next year) and fidelity among birds seen anywhere next year. Returns datasets for charts."""
    return await _analysis(analysis.site_fidelity(place, species, year_from, year_to))


@mcp.tool(title="Ausbreitung / Entfernungen", annotations=READ_ONLY)
async def dispersal(
    species: str | None = None,
    ringing_place: Annotated[str | None, Field(description="Substring of the ringing place.")] = None,
    ring: Annotated[str | None, Field(description="Single bird.")] = None,
    min_km: Annotated[float, Field(ge=0, description="Only birds whose farthest find is at least this far.")] = 0,
    year_from: int | None = None,
    year_to: int | None = None,
) -> dict[str, Any]:
    """Distances between ringing site and sightings (air line): per bird the farthest find, distance classes, share over
    20/100 km, top long-distance birds. per_bird_dataset_id has ringing and farthest coordinates → create_map flows/points."""
    return await _analysis(analysis.dispersal(species, ringing_place, ring, min_km, year_from, year_to))


@mcp.tool(title="Saisonverlauf", annotations=READ_ONLY)
async def seasonality(
    place: Annotated[str | None, Field(description="Substring of the place name.")] = None,
    species: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
) -> dict[str, Any]:
    """Sightings, distinct birds and observation days per month and year; peak and quietest months; per-year peaks.
    dataset_id is long format (jahr, monat, sichtungen, individuen) → heatmap, stacked_bar (month_axis) or line per year."""
    return await _analysis(analysis.seasonality(place, species, year_from, year_to))


@mcp.tool(title="Begleiter eines Vogels", annotations=READ_ONLY)
async def companions(
    ring: str,
    window_days: Annotated[int, Field(ge=0, le=7, description="Tolerance in days around each of the bird's sighting days.")] = 0,
    min_shared_days: Annotated[int, Field(ge=1, le=100)] = 2,
) -> dict[str, Any]:
    """Which other ringed birds were seen at the same place on the same day(s) as this bird (pair/group association)."""
    return await _analysis(analysis.companions(ring, window_days, min_shared_days))


@mcp.tool(title="Was ist neu", annotations=READ_ONLY)
async def whats_new(since: Annotated[str, Field(description="Date YYYY-MM-DD; sightings from this date on.")]) -> dict[str, Any]:
    """Digest of recent sightings: counts, species, places, birds seen for the first time, new places, far recaptures,
    dead finds. Use for weekly/monthly updates and proactive hints."""
    try:
        date.fromisoformat(since)
    except ValueError as exc:
        raise ToolError("since must be YYYY-MM-DD") from exc
    return await _analysis(analysis.whats_new(since))


@mcp.tool(title="Datenqualität prüfen", annotations=READ_ONLY)
async def data_quality() -> dict[str, Any]:
    """Run all data-quality checks (missing coordinates, sightings before ringing, duplicates, species mismatches,
    unknown partner rings, implausible movements, place spelling variants …) with counts, examples and dataset_ids."""
    return await _analysis(analysis.data_quality())


# ------------------------------------------------------------------ visuals


def _visual_result(out: VisualOut) -> CallToolResult:
    return CallToolResult(
        content=[
            ImageContent(type="image", data=base64.b64encode(out.inline).decode("ascii"), mime_type=out.inline_mime),
            TextContent(type="text", text=out.text),
        ],
        structured_content=out.structured,
    )


async def _render_and_store(kind: str, spec_obj: ChartSpec | MapSpec | TableSpec, *, visual_id: str | None = None, patch: dict | None = None) -> CallToolResult:
    try:
        out = await create_visual(kind, spec_obj, visual_id=visual_id, patch=patch)
    except VisualError as exc:
        raise ToolError(str(exc)) from exc
    return _visual_result(out)


def _validation_message(exc: ValidationError) -> str:
    parts = []
    for e in exc.errors():
        loc = ".".join(str(p) for p in e["loc"])
        parts.append(f"{loc}: {e['msg']}")
    return "; ".join(parts)


@mcp.tool(title="Diagramm erstellen", annotations=CREATES)
async def create_chart(spec: ChartSpec) -> CallToolResult:
    """Render a chart from a dataset. Kinds: bar, stacked_bar, line, area, scatter, pie, heatmap, histogram, timeline
    (life history per bird: x=date, series_column=ring), calendar (sightings per day), sankey (movements: source_column →
    target_column, y=weight), boxplot (distribution per category), graph (relationships: source/target). facet_column
    splits bar/line charts into small multiples. Returns the image inline plus links (interactive, embed, PNG 2x, PDF, XLSX).
    Always include the interactive link in your answer. Use month_axis=true for month numbers, series_column for long-format
    groups (e.g. place), stack_order and colors for Ingo's fixed conventions, annotations for Mauser bands."""
    return await _render_and_store("chart", spec)


@mcp.tool(title="Karte erstellen", annotations=CREATES)
async def create_map(spec: MapSpec) -> CallToolResult:
    """Render a map from datasets with lat/lon. Layers: points (circle/triangle/star…, colour by season/individual/
    category/species, size by a count column, labels), tracks (per-bird polylines), flows (aggregated movement lines),
    markers (fixed symbols such as an excluded place ★). Returns the image inline plus links; include the interactive
    link in your answer. Typical: ringing sites as triangles + recaptures as circles coloured by season."""
    return await _render_and_store("map", spec)


@mcp.tool(title="Tabelle erstellen", annotations=CREATES)
async def create_table(spec: TableSpec) -> CallToolResult:
    """Render a formatted, sortable table (German number/date formats, ring links, optional totals row, in-cell bars,
    highlighted maxima) as image + interactive page; all rows are in the XLSX link. Use for rankings and overviews that
    should look professional in a report; for quick answers write the numbers as text instead."""
    return await _render_and_store("table", spec)


@mcp.tool(title="Visualisierung ändern", annotations=CREATES)
async def update_visual(
    visual_id: str,
    patch: Annotated[dict[str, Any], Field(description="JSON merge patch on the stored spec (same keys as create_*). null removes a key. Lists are replaced whole.")],
) -> CallToolResult:
    """Modify an existing chart/map/table (title, colours, zoom, legend, labels, …) without rebuilding it from scratch."""
    visuals = runtime.visuals()
    try:
        meta = visuals.meta(visual_id)
        current = visuals.spec(visual_id)
    except KeyError as exc:
        raise ToolError(str(exc)) from exc
    merged = merge_patch(current, patch)
    try:
        if meta.kind == "chart":
            spec_obj: ChartSpec | MapSpec | TableSpec = ChartSpec.model_validate(merged)
        elif meta.kind == "table":
            spec_obj = TableSpec.model_validate(merged)
        else:
            spec_obj = MapSpec.model_validate(merged)
    except ValidationError as exc:
        raise ToolError(f"Patch invalid: {_validation_message(exc)}") from exc
    return await _render_and_store(meta.kind, spec_obj, visual_id=visual_id, patch=patch)


@mcp.tool(title="Visualisierungen auflisten", annotations=READ_ONLY)
def list_visuals(limit: Annotated[int, Field(ge=1, le=50)] = 10) -> list[dict[str, Any]]:
    """List recent charts/maps/tables with ids and links (e.g. to reuse them in a report)."""
    return [{"visual_id": m.id, "kind": m.kind, "title": m.title, "updated_at": m.updated_at, **_urls(m.id)} for m in runtime.visuals().list(limit)]


# ------------------------------------------------------------------ reports


@mcp.tool(title="Bericht erstellen", annotations=CREATES)
async def create_report(spec: ReportSpec) -> dict[str, Any]:
    """Compose a professional report (HTML page, A4 PDF, Word DOCX) from plain-German markdown sections, existing visuals
    (visual_ids → numbered figures with captions) and datasets (→ formatted tables). Adds 'Das Wichtigste in Kürze',
    a plain-language 'So wurde gezählt' section built from the dataset descriptions, and a technical SQL appendix.
    Create all charts/maps first, then call this once. Return the PDF and Word links to the user."""
    try:
        return await engine.create_report(spec)
    except engine.EngineError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(title="Berichte auflisten", annotations=READ_ONLY)
def list_reports(limit: Annotated[int, Field(ge=1, le=50)] = 10) -> list[dict[str, Any]]:
    """List recent reports with links."""
    base = settings.public_base_url
    return [{"report_id": m.id, "title": m.title, "created_at": m.created_at, "html": f"{base}/reports/{m.id}", "pdf": f"{base}/reports/{m.id}.pdf", "docx": f"{base}/reports/{m.id}.docx"} for m in runtime.reports().list(limit)]


# ------------------------------------------------------------------ Tableau-style engine: sources, views, workbooks, pipelines, decks, notes


def _engine(coro):
    async def run():
        try:
            return await coro
        except engine.EngineError as exc:
            raise ToolError(str(exc)) from exc
        except KeyError as exc:
            raise ToolError(str(exc)) from exc
        except SourceError as exc:
            raise ToolError(str(exc)) from exc

    return run()


@mcp.tool(title="Datenquellen und Filter", annotations=READ_ONLY)
def list_sources() -> dict[str, Any]:
    """Describe the curated data sources (Sichtungen, Beringungen, Vögel, Beziehungen), their columns, the available
    metrics („was zählen“), dimensions („aufteilen nach“) and filter fields with German labels. Read this before create_view."""
    return describe_sources()


@mcp.tool(title="Filterwerte nachschlagen", annotations=READ_ONLY)
async def filter_choices(
    source: Annotated[str, Field(description="sightings | ringings | birds | relationships")] = "sightings",
    column: Annotated[str, Field(description="Column such as species, place, status, melder, year.")] = "place",
    search: Annotated[str, Field(description="Substring to narrow the values (case-insensitive).")] = "",
    limit: Annotated[int, Field(ge=1, le=500)] = 50,
) -> list[dict[str, Any]]:
    """List the distinct values of a column with counts – e.g. to find the exact place name or species spelling."""
    try:
        return await choices(source, column, search=search, limit=limit)
    except SourceError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(title="Ansicht erstellen", annotations=CREATES)
async def create_view(
    spec: ViewSpec,
    title: Annotated[str | None, Field(description="Title shown in the app (default: the auto description).")] = None,
    project: Annotated[str, Field(description="Optional project name to group work in the app.")] = "",
) -> CallToolResult:
    """The no-SQL way to analyse: pick a source, filters (species, places/place_groups, period, rings …), what to count
    (metric), how to split (dimension), colour (series) and facet; or a map / table. Runs the query, renders the visual,
    saves the view in the app (it appears there instantly) and returns image + links + view_id. Use update_view to change it."""
    try:
        out = await engine.create_view(spec, title=title, project=project, by="agent")
    except engine.EngineError as exc:
        raise ToolError(str(exc)) from exc
    inline, mime = out.pop("_inline", (b"", "image/png"))
    visual = out.get("visual", {})
    text = (
        f"Ansicht erstellt: view_id={out['id']} · visual_id={visual.get('visual_id')}\n{out['title']}\n"
        f"Interaktiv: {visual.get('interactive_url')}\nPNG: {visual.get('png_url')}\nPDF: {visual.get('pdf_url')}\n"
        f"Zusammenfassung: {json.dumps(visual.get('summary', {}), ensure_ascii=False, default=str)[:1500]}\n"
        f"Datengrundlage: {out.get('description', '')}"
    )
    structured = {"view_id": out["id"], "title": out["title"], "description": out.get("description"), **visual}
    content: list[Any] = []
    if inline:
        content.append(ImageContent(type="image", data=base64.b64encode(inline).decode("ascii"), mime_type=mime))
    content.append(TextContent(type="text", text=text))
    return CallToolResult(content=content, structured_content=structured)


@mcp.tool(title="Ansicht ändern", annotations=CREATES)
async def update_view(
    view_id: str,
    patch: Annotated[dict[str, Any], Field(description="JSON merge patch on the ViewSpec (e.g. {\"filters\": {\"years\": [2024]}, \"chart_kind\": \"line\"}). null removes a key.")],
) -> CallToolResult:
    """Change a saved view (filters, chart kind, colours, title …) and re-render it; the app updates live."""
    try:
        out = await engine.update_view(view_id, patch, by="agent")
    except engine.EngineError as exc:
        raise ToolError(str(exc)) from exc
    inline, mime = out.pop("_inline", (b"", "image/png"))
    visual = out.get("visual", {})
    text = f"Ansicht aktualisiert: view_id={out['id']} · {out['title']}\nInteraktiv: {visual.get('interactive_url')}\nDatengrundlage: {out.get('description', '')}"
    content: list[Any] = [TextContent(type="text", text=text)]
    if inline:
        content.insert(0, ImageContent(type="image", data=base64.b64encode(inline).decode("ascii"), mime_type=mime))
    return CallToolResult(content=content, structured_content={"view_id": out["id"], "title": out["title"], **visual})


@mcp.tool(title="Ansichten auflisten", annotations=READ_ONLY)
def list_views(limit: Annotated[int, Field(ge=1, le=100)] = 20, search: str = "") -> list[dict[str, Any]]:
    """Saved views in the app (id, title, kind, links) – e.g. to reuse them in a workbook."""
    return [engine.view_summary(i) for i in runtime.catalog().list("view", limit=limit, search=search)]


@mcp.tool(title="Mappe erstellen", annotations=CREATES)
async def create_workbook(
    spec: WorkbookSpec,
    workbook_id: Annotated[str | None, Field(description="Update an existing workbook instead of creating one.")] = None,
    render: Annotated[bool, Field(description="Render all tiles now (slower, but the user sees finished graphics).")] = True,
) -> dict[str, Any]:
    """A workbook („Mappe“) is a dashboard: shared filters + tiles of saved views (view_id) or inline views. Saved in the
    app; use workbook_report / workbook_deck to turn it into a PDF/DOCX report or a PPTX presentation."""
    try:
        item = engine.save_workbook(spec, workbook_id=workbook_id, by="agent")
        out: dict[str, Any] = {"workbook_id": item.id, "title": item.title, "url": f"{settings.public_base_url}/app/#/mappen/{item.id}"}
        if render:
            r = await engine.render_workbook_by_id(item.id)
            out["tiles"] = [{"title": t.get("title"), "visual_id": t.get("visual", {}).get("visual_id"), "error": t.get("error"), "summary": t.get("summary")} for t in r["tiles"]]
        return out
    except engine.EngineError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(title="Mappen auflisten", annotations=READ_ONLY)
def list_workbooks(limit: Annotated[int, Field(ge=1, le=100)] = 20, search: str = "") -> list[dict[str, Any]]:
    """Saved workbooks (id, title, number of tiles)."""
    return [{**i.summary(), "tiles": len(i.doc.get("tiles", []))} for i in runtime.catalog().list("workbook", limit=limit, search=search)]


@mcp.tool(title="Mappe als Bericht", annotations=CREATES)
async def workbook_report(workbook_id: str) -> dict[str, Any]:
    """Render a workbook and turn it into a report (PDF/DOCX): one section per tile with its note as text."""
    return await _engine(engine.workbook_report(workbook_id))


@mcp.tool(title="Mappe als Präsentation", annotations=CREATES)
async def workbook_deck(workbook_id: str) -> dict[str, Any]:
    """Render a workbook and turn it into a PowerPoint deck (one figure slide per tile)."""
    return await _engine(engine.workbook_deck(workbook_id))


@mcp.tool(title="Präsentation erstellen", annotations=CREATES)
async def create_deck(
    spec: Annotated[DeckSpec | None, Field(description="Slides: title, section, bullets, figure (visual_id), two_figures, table (dataset_id), key_findings, text.")] = None,
    report_id: Annotated[str | None, Field(description="Alternatively: build the deck from an existing report.")] = None,
) -> dict[str, Any]:
    """Professional German PowerPoint (16:9, house style) from existing visuals and datasets, or from a report."""
    if report_id:
        return await _engine(engine.deck_from_report_id(report_id, by="agent"))
    if spec is None:
        raise ToolError("spec oder report_id angeben.")
    return await _engine(engine.create_deck(spec, by="agent"))


@mcp.tool(title="Auswertung speichern", annotations=CREATES)
def save_pipeline(
    spec: PipelineSpec,
    pipeline_id: Annotated[str | None, Field(description="Update an existing pipeline.")] = None,
) -> dict[str, Any]:
    """Save a reusable, parameterised Auswertung (steps: view/query/analysis/transform/chart/map/table/report/deck/export with
    {{param}} placeholders). It appears as a card with a form in the app so the user can run it alone, anytime."""
    try:
        item = engine.save_pipeline(spec, pipeline_id=pipeline_id, by="agent")
    except engine.EngineError as exc:
        raise ToolError(str(exc)) from exc
    return {"pipeline_id": item.id, "name": item.title, "url": f"{settings.public_base_url}/app/#/auswertungen/{item.id}", "describe": engine.pipeline_summary(item)["describe"]}


@mcp.tool(title="Auswertungen auflisten", annotations=READ_ONLY)
def list_pipelines(search: str = "") -> list[dict[str, Any]]:
    """Saved Auswertungen with their parameters (run them with run_pipeline)."""
    return [engine.pipeline_summary(i) for i in runtime.catalog().list("pipeline", limit=100, search=search)]


@mcp.tool(title="Auswertung ausführen", annotations=CREATES)
async def run_pipeline(
    pipeline_id: str,
    params: Annotated[dict[str, Any], Field(description="Parameter values by name, e.g. {\"ort\": \"Ostpark\", \"jahr\": 2025}.")] = {},
) -> dict[str, Any]:
    """Run a saved Auswertung; returns the run log (German) and all artefacts (visual/report/deck ids and links)."""
    return await _engine(engine.run_pipeline_by_id(pipeline_id, params, by="agent"))


@mcp.tool(title="Gruppe anlegen", annotations=CREATES)
def create_group(
    spec: GroupSpec,
    group_id: Annotated[str | None, Field(description="Update an existing group instead of creating one.")] = None,
) -> dict[str, Any]:
    """A group („Gruppe“) is a saved, named selection of sightings the user reuses: filters (species, places, period,
    status, ringing place/age …) plus an optional explicit ring list and hand-excluded sightings. Use it everywhere via
    filters.groups=[group_id] (views, workbooks, pipelines); several groups form a union; dimension/color "group"
    compares them. Returns the group with a German description of the selection."""
    try:
        return engine.create_group(spec, group_id=group_id, by="agent")
    except engine.EngineError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(title="Gruppe ändern", annotations=CREATES)
def update_group(
    group_id: str,
    patch: Annotated[dict[str, Any], Field(description="JSON merge patch on the GroupSpec, e.g. {\"filters\": {\"years\": [2024]}, \"color\": \"#228096\"}. null removes a key.")],
) -> dict[str, Any]:
    """Change a saved group (filters, ring list, excluded sightings, name, colour); views using it pick the change up on their next render."""
    try:
        return engine.update_group(group_id, patch, by="agent")
    except (engine.EngineError, KeyError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(title="Gruppen auflisten", annotations=READ_ONLY)
def list_groups(limit: Annotated[int, Field(ge=1, le=200)] = 50, search: str = "") -> list[dict[str, Any]]:
    """Saved groups (id, name, description, German description of the selection, cached counts). Read this before
    building analyses – the user's own groups are what he usually means („die Ostpark-Gänse“)."""
    return engine.list_groups(limit=limit, search=search)


@mcp.tool(title="Gruppe lesen", annotations=READ_ONLY)
def get_group(group_id: Annotated[str, Field(description="group_id or exact name.")]) -> dict[str, Any]:
    """Full definition of a group (filters, ring list, excluded ids, colour)."""
    try:
        item, spec = resolve_group(group_id)
    except SourceError as exc:
        raise ToolError(str(exc)) from exc
    return engine.get_group(item.id)


@mcp.tool(title="Gruppe zusammenfassen", annotations=READ_ONLY)
async def group_summary(group_id: Annotated[str, Field(description="group_id or exact name.")]) -> dict[str, Any]:
    """Live numbers for a group: sightings, distinct birds, places, first/last date, species and status breakdown, sightings per year."""
    try:
        item, _ = resolve_group(group_id)
        return await engine.group_stats(item.id)
    except (engine.EngineError, SourceError) as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(title="Gruppen vergleichen", annotations=CREATES)
async def compare_groups(
    group_ids: Annotated[list[str], Field(min_length=1, description="Groups to compare (ids or exact names).")],
    metric: Annotated[Literal["sightings", "birds", "observation_days", "places"], Field(description="What to count.")] = "sightings",
    dimension: Annotated[str, Field(description="group (totals per group) or year, month, season, status, place, age, ringing_place, distance_class, year_month (then colour = group).")] = "year",
    chart_kind: Annotated[str, Field(description="bar, stacked_bar, line, area, pie (only with dimension=group), heatmap.")] = "bar",
    title: str | None = None,
    save: Annotated[bool, Field(description="Save as a view in the app (default: preview only).")] = True,
) -> dict[str, Any]:
    """Side-by-side comparison of groups as one chart (e.g. sightings per year, colour = group). With save=True the
    result is a normal view (view_id + image links) the user sees in the app immediately."""
    try:
        out = await engine.compare_groups(group_ids, metric=metric, dimension=dimension, chart_kind=chart_kind, title=title, save=save, by="agent")
    except (engine.EngineError, SourceError) as exc:
        raise ToolError(str(exc)) from exc
    out.pop("_inline", None)
    out.pop("model", None)
    return out


@mcp.tool(title="Notiz speichern", annotations=CREATES)
def save_note(
    text: Annotated[str, Field(description="Markdown. Your long-term project memory: findings, open questions, what the user cares about.")],
    title: str | None = None,
    note_id: Annotated[str | None, Field(description="Update an existing note.")] = None,
    project: str = "",
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Persist knowledge beyond this chat (visible to the user in the app under Notizen). Read list_notes at the start of
    bigger tasks to pick up where you left off."""
    item = engine.save_note(text, title=title, note_id=note_id, project=project, tags=tags, by="agent")
    return {"note_id": item.id, "title": item.title}


@mcp.tool(title="Notizen lesen", annotations=READ_ONLY)
def list_notes(project: str = "", search: str = "", limit: Annotated[int, Field(ge=1, le=100)] = 20) -> list[dict[str, Any]]:
    """Notes (long-term memory) with text."""
    return [{**i.summary(), "text": i.doc.get("text", "")} for i in runtime.catalog().list("note", limit=limit, search=search, project=project)]


@mcp.tool(title="In der App zeigen", annotations=CREATES)
def show_in_app(
    target: Annotated[Literal["group", "view", "workbook", "pipeline", "run", "report", "deck", "visual", "dataset", "page"], Field(description="What to show.")],
    id: Annotated[str | None, Field(description="The object's id (view_id, workbook_id, visual_id …) or a page name (start, live, erkunden).")] = None,
    title: str | None = None,
) -> dict[str, Any]:
    """Steer the user's analytics screen (if open) to the object you are talking about – like pointing at it."""
    return engine.show_in_app(target, id, title=title)


@mcp.tool(title="Aktivität", annotations=READ_ONLY)
def recent_activity(limit: Annotated[int, Field(ge=1, le=100)] = 20) -> list[dict[str, Any]]:
    """What happened recently in the app (by the user or by you): created views, runs, reports … Useful to resume work."""
    return runtime.catalog().activity(limit=limit)


@mcp.resource("vogelring://schema", title="Vogelring Datenwörterbuch", mime_type="text/markdown")
def schema_resource() -> str:
    return SCHEMA_DOC


# ------------------------------------------------------------------ gated writes (dry run → approval in chat → apply → rollback)

WRITES = ToolAnnotations(read_only_hint=False, destructive_hint=True, idempotent_hint=False, open_world_hint=False)


@mcp.tool(title="Änderung vorschlagen (Probelauf)", annotations=CREATES)
async def propose_changes(
    operations: Annotated[list[Operation], Field(min_length=1, description="Typed operations: set_fields, rename_place, convert_to_color_ring, upsert_color_ring, merge_reading_to_ring.")],
    reason: Annotated[str, Field(description="Why, in plain German – appears in the change log, e.g. 'W408 ist ein Farbring (weiß), kein Metallring'.")],
) -> dict[str, Any]:
    """DRY RUN – never writes. Resolves every affected record and returns: a German summary (how many records, which
    fields change from what to what), warnings, examples and a preview_url with the full before/after table.
    Explain the result to the user in plain language (counts, fields, link) and ask for confirmation BEFORE calling
    apply_changes. Proposals expire after a few hours."""
    try:
        return await writes.plan(operations, reason, by="agent")
    except WriteError as exc:
        raise ToolError(str(exc)) from exc
    except SqlRejected as exc:
        raise ToolError(f"SQL rejected: {exc}") from exc


@mcp.tool(title="Änderung übernehmen (schreibt in Vogelring)", annotations=WRITES)
async def apply_changes(changeset_id: Annotated[str, Field(description="The changeset_id from propose_changes.")]) -> dict[str, Any]:
    """WRITES to the Vogelring database: applies a proposed changeset in one transaction. LibreChat asks the user to
    approve this call – only call it after the user said yes to the proposal. Every record is re-checked against the
    recorded before-values; if anything changed meanwhile nothing is written. Can be undone with rollback_changes."""
    try:
        return await writes.apply(changeset_id, by="agent")
    except WriteError as exc:
        raise ToolError(str(exc)) from exc
    except KeyError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(title="Änderung zurücknehmen", annotations=WRITES)
async def rollback_changes(changeset_id: str) -> dict[str, Any]:
    """Restores the recorded before-values of an applied changeset (one transaction, re-checked). Newly created
    colour-ring registry rows cannot be deleted automatically and are listed as manual steps."""
    try:
        return await writes.rollback(changeset_id, by="agent")
    except WriteError as exc:
        raise ToolError(str(exc)) from exc
    except KeyError as exc:
        raise ToolError(str(exc)) from exc


@mcp.tool(title="Änderungen auflisten", annotations=READ_ONLY)
def list_changes(limit: Annotated[int, Field(ge=1, le=100)] = 20, status: Literal["proposed", "applied", "rolled_back"] | None = None) -> dict[str, Any]:
    """Change log: proposed, applied and rolled-back changesets with preview links."""
    return {"enabled": writes.writes_enabled(), "items": writes.list_changes(limit=limit, status=status)}


@mcp.tool(title="Änderung anzeigen", annotations=READ_ONLY)
def get_change(changeset_id: str, examples: Annotated[int, Field(ge=0, le=200, description="How many affected records to include.")] = 10) -> dict[str, Any]:
    """Details of one changeset (summary, warnings, affected records before → after, status)."""
    try:
        return writes.get(changeset_id, include_items=examples)
    except KeyError as exc:
        raise ToolError(str(exc)) from exc
