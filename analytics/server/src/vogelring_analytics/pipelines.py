"""Pipelines („Auswertungen“): reusable, parameterised recipes the agent authors and the user runs from a form.

A pipeline is a list of typed steps (view, query, analysis, transform, chart, map, table, report, deck, export).
Step specs are JSON with ``{{param}}`` placeholders (``{{param|sql}}`` → safely quoted SQL literal) and
``$steps.<id>.<field>`` references to earlier results (e.g. ``$steps.saison.dataset_id``).
"""

from __future__ import annotations

import inspect
import logging
import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from . import runtime
from .datasets import new_id
from .events import bus
from .settings import settings

log = logging.getLogger(__name__)

ParamType = Literal["species", "place", "place_group", "group", "period", "year", "year_range", "ring", "number", "text", "choice", "date", "boolean"]
StepKind = Literal["view", "query", "analysis", "transform", "chart", "map", "table", "report", "deck", "export"]
ANALYSES = ("bird_profile", "cohort_resighting", "site_fidelity", "dispersal", "seasonality", "companions", "whats_new", "data_quality")
KIND_LABEL = {"view": "Ansicht", "query": "Abfrage", "analysis": "Analyse", "transform": "Umformung", "chart": "Diagramm", "map": "Karte", "table": "Tabelle", "report": "Bericht", "deck": "Präsentation", "export": "Export"}

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_PLACEHOLDER = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)*)\s*(?:\|\s*(sql|like)\s*)?\}\}")
_STEP_REF = re.compile(r"^\$steps\.([A-Za-z_][A-Za-z0-9_]*)\.([A-Za-z_][A-Za-z0-9_.]*)$")


class PipelineError(ValueError):
    """User-facing (German) pipeline problem."""


class _Spec(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Parameter(_Spec):
    name: str = Field(..., description="Bezeichner (für {{name}} in den Schritten).")
    label: str = Field(..., description="Beschriftung im Formular (Deutsch).")
    type: ParamType
    required: bool = True
    default: Any | None = None
    choices: list[str] | None = Field(None, description="Nur type=choice: erlaubte Werte.")
    help: str | None = Field(None, description="Hilfetext unter dem Feld.")

    @model_validator(mode="after")
    def _check(self) -> "Parameter":
        if not _IDENT.match(self.name):
            raise ValueError(f"Parametername '{self.name}' ist kein gültiger Bezeichner.")
        if self.type == "choice" and not self.choices:
            raise ValueError(f"Parameter '{self.name}': choice braucht choices.")
        return self


class Step(_Spec):
    id: str
    kind: StepKind
    spec: dict[str, Any] = Field(default_factory=dict, description="Schritt-Spezifikation mit {{param}}- und $steps.<id>.<feld>-Platzhaltern.")
    title: str | None = Field(None, description="Beschriftung im Protokoll/Ergebnis.")

    @model_validator(mode="after")
    def _check(self) -> "Step":
        if not _IDENT.match(self.id):
            raise ValueError(f"Schritt-ID '{self.id}' ist kein gültiger Bezeichner.")
        return self


class PipelineSpec(_Spec):
    name: str
    description: str = Field(..., description="Welche Frage beantwortet die Auswertung? (Deutsch, für die Karte in der App)")
    parameters: list[Parameter] = Field(default_factory=list)
    steps: list[Step] = Field(..., min_length=1)
    outputs: list[str] = Field(default_factory=list, description="Schritt-IDs, deren Ergebnisse gezeigt werden (Standard: alle Visuals/Berichte).")
    tags: list[str] = Field(default_factory=list)
    icon: str | None = Field(None, description="Material-Icon-Name für die Karte, z. B. 'mdi-map'.")

    @model_validator(mode="after")
    def _check(self) -> "PipelineSpec":
        ids = [s.id for s in self.steps]
        if len(ids) != len(set(ids)):
            raise ValueError("Schritt-IDs müssen eindeutig sein.")
        names = [p.name for p in self.parameters]
        if len(names) != len(set(names)):
            raise ValueError("Parameternamen müssen eindeutig sein.")
        unknown = [o for o in self.outputs if o not in ids]
        if unknown:
            raise ValueError(f"outputs verweist auf unbekannte Schritte: {', '.join(unknown)}")
        for s in self.steps:
            if s.kind == "analysis" and s.spec.get("name") not in ANALYSES:
                raise ValueError(f"Schritt '{s.id}': unbekannte Analyse '{s.spec.get('name')}'. Erlaubt: {', '.join(ANALYSES)}")
        return self


@dataclass
class RunResult:
    run_id: str
    status: Literal["ok", "error"]
    started_at: str
    finished_at: str
    params: dict[str, Any]
    artifacts: list[dict[str, Any]] = field(default_factory=list)
    log: list[str] = field(default_factory=list)
    error: str | None = None
    pipeline: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"run_id": self.run_id, "pipeline": self.pipeline, "status": self.status, "started_at": self.started_at, "finished_at": self.finished_at, "params": self.params, "artifacts": self.artifacts, "log": self.log, "error": self.error}


# ---------------------------------------------------------------- placeholders


def _sql_literal(v: Any) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, bool):
        return "TRUE" if v else "FALSE"
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, (list, tuple)):
        return "(" + ", ".join(_sql_literal(x) for x in v) + ")"
    return "'" + str(v).replace("'", "''") + "'"


def _lookup_step(ref: str, step_results: dict[str, Any]) -> Any:
    m = _STEP_REF.match(ref)
    if not m:
        return ref
    sid, path = m.group(1), m.group(2)
    if sid not in step_results:
        raise PipelineError(f"Verweis auf unbekannten oder noch nicht ausgeführten Schritt: {ref}")
    cur: Any = step_results[sid]
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif hasattr(cur, part):
            cur = getattr(cur, part)
        else:
            raise PipelineError(f"Schritt '{sid}' hat kein Feld '{path}' (verfügbar: {', '.join(sorted(cur.keys())) if isinstance(cur, dict) else '–'}).")
    return cur


def _param_value(name: str, params: dict[str, Any]) -> Any:
    """`{{name}}` or dotted `{{name.sub}}` (e.g. {{jahre.from}}, {{zeitraum.months}}); missing sub-keys → None."""
    head, *rest = name.split(".")
    if head not in params:
        raise PipelineError(f"Unbekannter Parameter {{{{{head}}}}}.")
    v = params[head]
    for part in rest:
        v = v.get(part) if isinstance(v, dict) else None
    return v


def substitute(obj: Any, params: dict[str, Any], step_results: dict[str, Any] | None = None) -> Any:
    """Recursive placeholder replacement. A string that is exactly one placeholder keeps the typed value."""
    step_results = step_results or {}
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for k, v in obj.items():
            sv = substitute(v, params, step_results)
            # a whole placeholder that resolves to None (optional parameter left empty) drops the key entirely,
            # so filters like "months": "{{zeitraum.months}}" simply mean "no restriction"
            if sv is None and isinstance(v, str) and _PLACEHOLDER.fullmatch(v.strip()):
                continue
            out[k] = sv
        return out
    if isinstance(obj, list):
        items = [substitute(v, params, step_results) for v in obj]
        # an optional parameter left empty must not leave a None inside a list filter (species: ["{{art}}"])
        return [v for i, v in enumerate(items) if not (v is None and isinstance(obj[i], str) and _PLACEHOLDER.fullmatch(obj[i].strip()))]
    if not isinstance(obj, str):
        return obj
    if obj.startswith("$steps."):
        return _lookup_step(obj, step_results)
    whole = _PLACEHOLDER.fullmatch(obj.strip())
    if whole:
        name, flt = whole.group(1), whole.group(2)
        v = _param_value(name, params)
        return _sql_literal(v) if flt == "sql" else (f"%{v}%" if flt == "like" else v)

    def repl(m: re.Match[str]) -> str:
        name, flt = m.group(1), m.group(2)
        v = _param_value(name, params)
        if flt == "sql":
            return _sql_literal(v)
        if flt == "like":
            return f"%{v}%"
        if isinstance(v, list):
            return ", ".join(str(x) for x in v)
        if isinstance(v, dict):
            return ", ".join(f"{k}={x}" for k, x in v.items())
        return "" if v is None else str(v)

    return _PLACEHOLDER.sub(repl, obj)


# ---------------------------------------------------------------- parameters


def _coerce(p: Parameter, v: Any) -> Any:
    t = p.type
    try:
        if t in ("species", "place", "place_group", "group", "ring", "text"):
            s = str(v).strip()
            return s or None
        if t == "choice":
            s = str(v).strip()
            if s not in (p.choices or []):
                raise PipelineError(f"„{p.label}“: '{s}' ist nicht erlaubt (erlaubt: {', '.join(p.choices or [])}).")
            return s
        if t == "year":
            y = int(v)
            if not 1900 <= y <= 2100:
                raise ValueError
            return y
        if t == "number":
            f = float(v)
            return int(f) if f.is_integer() else f
        if t == "boolean":
            if isinstance(v, str):
                return v.strip().lower() in ("1", "true", "ja", "yes", "wahr")
            return bool(v)
        if t == "date":
            return date.fromisoformat(str(v)).isoformat()
        if t == "year_range":
            if isinstance(v, dict):
                a, b = v.get("from"), v.get("to")
            elif isinstance(v, (list, tuple)) and len(v) == 2:
                a, b = v
            elif isinstance(v, str) and "-" in v:
                a, b = v.split("-", 1)
            else:
                a = b = v
            a_i, b_i = int(a), int(b)
            if a_i > b_i:
                a_i, b_i = b_i, a_i
            return {"from": a_i, "to": b_i}
        if t == "period":
            if isinstance(v, dict):
                out: dict[str, Any] = {}
                if v.get("months"):
                    out["months"] = sorted({int(m) for m in v["months"]})
                if v.get("date_from") and v.get("date_to"):
                    out["date_from"] = date.fromisoformat(str(v["date_from"])).isoformat()
                    out["date_to"] = date.fromisoformat(str(v["date_to"])).isoformat()
                if not out:
                    raise ValueError
                return out
            if isinstance(v, (list, tuple)):
                return {"months": sorted({int(m) for m in v})}
            if isinstance(v, str) and ".." in v:
                a, b = v.split("..", 1)
                return {"date_from": date.fromisoformat(a.strip()).isoformat(), "date_to": date.fromisoformat(b.strip()).isoformat()}
            if isinstance(v, str):
                return {"months": sorted({int(m) for m in re.split(r"[,\s]+", v.strip()) if m})}
            raise ValueError
    except PipelineError:
        raise
    except (TypeError, ValueError) as exc:
        raise PipelineError(f"„{p.label}“: ungültiger Wert {v!r} für Typ {t}.") from exc
    return v


def validate_params(spec: PipelineSpec, params: dict[str, Any] | None) -> dict[str, Any]:
    """Apply defaults, check required parameters and coerce types. Unknown keys are rejected."""
    params = dict(params or {})
    known = {p.name for p in spec.parameters}
    unknown = [k for k in params if k not in known]
    if unknown:
        raise PipelineError(f"Unbekannte Parameter: {', '.join(unknown)}. Erwartet: {', '.join(sorted(known)) or '–'}.")
    out: dict[str, Any] = {}
    for p in spec.parameters:
        v = params.get(p.name)
        if v is None or v == "" or v == []:
            v = p.default
        if v is None or v == "" or v == []:
            if p.required:
                raise PipelineError(f"Bitte „{p.label}“ angeben.")
            out[p.name] = None
            continue
        out[p.name] = _coerce(p, v)
    return out


def describe_pipeline(spec: PipelineSpec) -> str:
    kinds = [KIND_LABEL[s.kind] for s in spec.steps]
    params = ", ".join(p.label + ("" if p.required else " (optional)") for p in spec.parameters) or "keine Eingaben"
    return f"{spec.description} Eingaben: {params}. Schritte: {' → '.join(kinds)}."


# ---------------------------------------------------------------- execution


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


async def _maybe_await(v: Any) -> Any:
    return await v if inspect.isawaitable(v) else v


def _count_phrase(summary: dict[str, Any] | None, row_count: int | None = None) -> str:
    if summary:
        for key, label in (("rows_total", "Zeilen"), ("points", "Punkte"), ("categories", "Kategorien"), ("grand_total", "gesamt"), ("nodes", "Knoten")):
            if key in summary and isinstance(summary[key], (int, float)):
                return f"{summary[key]} {label}"
        layers = summary.get("layers")
        if isinstance(layers, list) and layers and isinstance(layers[0], dict) and "points" in layers[0]:
            return f"{sum(int(l.get('points', 0)) for l in layers if isinstance(l, dict))} Punkte"
    if row_count is not None:
        return f"{row_count} Zeilen"
    return ""


async def _run_step(step: Step, spec: dict[str, Any]) -> tuple[dict[str, Any], str]:
    """Execute one step; returns (result record, German phrase for the log)."""
    from . import visual_service  # lazy

    kind = step.kind
    if kind == "view":
        from . import views  # lazy

        vs = views.ViewSpec.model_validate(spec)
        result = await views.build_view(vs)
        vkind = getattr(result, "visual_kind", None) or visual_service.kind_of(result.visual_spec)
        out = await visual_service.create_visual(vkind, result.visual_spec)
        rec = {"kind": vkind, "visual_id": out.meta.id, "dataset_id": result.dataset_id, "title": out.meta.title, "urls": out.urls, "summary": out.summary, "description": getattr(result, "description", "")}
        return rec, f"{visual_service.KIND_LABEL[vkind]} erstellt – {_count_phrase(out.summary, getattr(result, 'row_count', None))}".rstrip(" –")

    if kind in ("chart", "map", "table"):
        from .specs import ChartSpec, MapSpec, TableSpec

        model_cls = {"chart": ChartSpec, "map": MapSpec, "table": TableSpec}[kind]
        try:
            spec_obj = model_cls.model_validate(spec)
        except Exception as exc:
            raise PipelineError(f"{KIND_LABEL[kind]} ungültig: {str(exc).splitlines()[0]}") from exc
        out = await visual_service.create_visual(kind, spec_obj)
        rec = {"kind": kind, "visual_id": out.meta.id, "dataset_id": out.meta.dataset_ids[0] if out.meta.dataset_ids else None, "title": out.meta.title, "urls": out.urls, "summary": out.summary, "description": out.data_basis}
        return rec, f"{KIND_LABEL[kind]} erstellt – {_count_phrase(out.summary)}".rstrip(" –")

    if kind == "query":
        sql = spec.get("sql")
        if not sql:
            raise PipelineError("Abfrage-Schritt ohne sql.")
        expanded, used = runtime.definitions().expand(sql)
        res = await runtime.database().query(expanded)
        df = res.to_frame()
        meta = runtime.datasets().save(df, name=spec.get("name") or step.title or "Abfrage", sql=expanded, truncated=res.truncated, description=spec.get("description", ""), extra={"definitions": used}, source="pipeline")
        rec = {"kind": "dataset", "dataset_id": meta.id, "title": meta.name, "row_count": meta.row_count, "description": meta.description}
        return rec, f"Daten geladen – {meta.row_count} Zeilen"

    if kind == "analysis":
        from . import analysis  # lazy

        fn = getattr(analysis, spec["name"])
        args = {k: v for k, v in (spec.get("args") or {}).items()}
        sig = inspect.signature(fn)
        unknown = [k for k in args if k not in sig.parameters]
        if unknown:
            raise PipelineError(f"Analyse „{spec['name']}“ kennt keine Eingabe {', '.join(unknown)}.")
        for name_, p in sig.parameters.items():  # positional parameters without defaults → None
            if name_ not in args and p.default is inspect.Parameter.empty:
                args[name_] = None
        result = await _maybe_await(fn(**args))
        rec = {"kind": "analysis", "name": spec["name"], "title": step.title or spec["name"], **(result if isinstance(result, dict) else {"result": result})}
        if "dataset_id" not in rec:
            for key in ("cohort_dataset_id", "per_bird_dataset_id", "sightings_dataset_id", "per_year_dataset_id"):
                if key in rec:
                    rec["dataset_id"] = rec[key]
                    break
        phrase = rec.get("summary") if isinstance(rec.get("summary"), str) else ""
        return rec, f"Analyse „{spec['name']}“ berechnet" + (f" – {phrase[:80]}" if phrase else "")

    if kind == "transform":
        from pydantic import TypeAdapter

        from . import transforms  # lazy

        ds_id = spec.get("dataset_id")
        if not ds_id:
            raise PipelineError("Umformungs-Schritt ohne dataset_id.")
        store = runtime.datasets()
        ops = TypeAdapter(list[transforms.Op]).validate_python(spec.get("ops") or [])
        src = store.meta(ds_id)
        df = transforms.apply_ops(store.load(ds_id), ops, store)
        desc = spec.get("description") or f"{src.description} Danach: {transforms.describe_ops(ops)}.".strip()
        meta = store.save(df, name=spec.get("name") or f"{src.name} (umgeformt)", sql=src.sql, description=desc, source="pipeline", extra={"from": ds_id})
        rec = {"kind": "dataset", "dataset_id": meta.id, "title": meta.name, "row_count": meta.row_count, "description": meta.description}
        return rec, f"Daten umgeformt – {meta.row_count} Zeilen"

    if kind == "report":
        from . import reports  # lazy

        rspec = reports.ReportSpec.model_validate(spec)
        visuals, datasets, store = runtime.visuals(), runtime.datasets(), runtime.reports()
        model, summary = reports.build_report_model(rspec, visuals, datasets)
        dataset_ids = [d["id"] for d in model["datasets"]]
        visual_ids = [it["id"] for s in model["sections"] for it in s.get("blocks", s.get("items", [])) if it.get("id")]
        meta = store.create(rspec.model_dump(mode="json", by_alias=True, exclude_none=True), model, {"title": rspec.title, "visual_ids": visual_ids, "dataset_ids": dataset_ids, "sections": len(model["sections"])})
        base = settings.public_base_url
        urls = {"html": f"{base}/reports/{meta.id}"}
        try:
            pdf = await runtime.renderer().render_pdf(f"/reports/{meta.id}?print=1", title=rspec.title)
            store.write_bytes(meta.id, "report.pdf", pdf)
            urls["pdf"] = f"{base}/reports/{meta.id}.pdf"
        except Exception as exc:
            log.exception("report pdf failed")
            urls["pdf_error"] = str(exc)[:200]
        try:
            reports.write_docx(model, store.dir(meta.id) / "report.docx", visuals)
            urls["docx"] = f"{base}/reports/{meta.id}.docx"
        except Exception as exc:
            log.exception("report docx failed")
            urls["docx_error"] = str(exc)[:200]
        bus.publish("report.created", f"Bericht erstellt: {rspec.title}", report_id=meta.id, label=rspec.title, **urls)
        rec = {"kind": "report", "report_id": meta.id, "title": rspec.title, "urls": urls, "summary": summary}
        return rec, f"Bericht erstellt – {summary.get('figures', 0)} Abbildungen, {summary.get('tables', 0)} Tabellen"

    if kind == "deck":
        try:
            from . import decks  # lazy; sibling module
        except ImportError as exc:
            raise PipelineError("Präsentationen noch nicht verfügbar.") from exc
        dspec = decks.DeckSpec.model_validate(spec)
        result = await _maybe_await(decks.build_deck(dspec))
        rec = {"kind": "deck", "title": dspec.title}
        if isinstance(result, dict):
            rec.update(result)
        else:
            for attr in ("deck_id", "urls", "slides", "path", "url", "pptx_url"):
                if hasattr(result, attr):
                    rec[attr] = getattr(result, attr)
            if "deck_id" not in rec and hasattr(result, "id"):
                rec["deck_id"] = result.id
        return rec, "Präsentation erstellt"

    if kind == "export":
        from .exporters import safe_filename, write_csv, write_xlsx

        ds_id = spec.get("dataset_id")
        if not ds_id:
            raise PipelineError("Export-Schritt ohne dataset_id.")
        store = runtime.datasets()
        df, meta = store.load(ds_id), store.meta(ds_id)
        fmt = spec.get("format", "xlsx")
        name = f"{safe_filename(spec.get('filename') or meta.name or 'export')}_{ds_id[-6:]}.{fmt}"
        path = settings.exports_dir / name
        if fmt == "xlsx":
            write_xlsx(df, path, title=spec.get("title") or (f"{meta.name} – {meta.description}" if meta.description else meta.name))
        else:
            write_csv(df, path)
        url = f"{settings.public_base_url}/files/{name}"
        rec = {"kind": "export", "dataset_id": ds_id, "title": meta.name, "filename": name, "url": url, "urls": {"download": url}, "rows": int(len(df))}
        return rec, f"Export erstellt – {len(df)} Zeilen"

    raise PipelineError(f"Unbekannte Schrittart: {kind}")


async def run_pipeline(spec: PipelineSpec, params: dict[str, Any] | None, *, run_id: str | None = None) -> RunResult:
    """Run all steps in order; stop at the first error (status 'error'), keep the artifacts produced so far."""
    run_id = run_id or new_id("run_")
    started = _now()
    try:
        values = validate_params(spec, params)
    except PipelineError as exc:
        return RunResult(run_id=run_id, pipeline=spec.name, status="error", started_at=started, finished_at=_now(), params=dict(params or {}), log=[f"Eingaben ungültig: {exc}"], error=str(exc))
    result = RunResult(run_id=run_id, pipeline=spec.name, status="ok", started_at=started, finished_at=started, params=values)
    step_results: dict[str, Any] = {}
    outputs = set(spec.outputs) or {s.id for s in spec.steps if s.kind in ("view", "chart", "map", "table", "report", "deck", "export")}
    total = len(spec.steps)
    bus.publish("pipeline.started", f"Auswertung „{spec.name}“ gestartet", run_id=run_id, pipeline=spec.name, params=values, total=len(spec.steps))
    for i, step in enumerate(spec.steps, start=1):
        label = step.title or KIND_LABEL[step.kind]
        try:
            resolved = substitute(step.spec, values, step_results)
            rec, phrase = await _run_step(step, resolved)
        except PipelineError as exc:
            result.status, result.error = "error", f"Schritt {i}/{total} ({label}): {exc}"
            result.log.append(f"Schritt {i}/{total}: Fehler – {exc}")
            bus.publish("pipeline.step", f"Schritt {i}/{total} fehlgeschlagen: {label}", run_id=run_id, step_id=step.id, status="error", error=str(exc))
            break
        except Exception as exc:  # anything else: keep the message, stop
            log.exception("pipeline step %s failed", step.id)
            msg = str(exc).strip() or exc.__class__.__name__
            result.status, result.error = "error", f"Schritt {i}/{total} ({label}): {msg[:300]}"
            result.log.append(f"Schritt {i}/{total}: Fehler – {msg[:300]}")
            bus.publish("pipeline.step", f"Schritt {i}/{total} fehlgeschlagen: {label}", run_id=run_id, step_id=step.id, status="error", error=msg[:300])
            break
        rec["step_id"] = step.id
        rec.setdefault("title", label)
        step_results[step.id] = rec
        line = f"Schritt {i}/{total}: {phrase}" if phrase else f"Schritt {i}/{total}: {label} fertig"
        result.log.append(line)
        if step.id in outputs:
            result.artifacts.append({k: v for k, v in rec.items() if k in ("step_id", "kind", "title", "dataset_id", "visual_id", "report_id", "deck_id", "urls", "summary", "description", "row_count", "rows", "url", "filename")})
        bus.publish("pipeline.step", line, run_id=run_id, pipeline=spec.name, step_id=step.id, index=i, total=total, status="ok", artifact={k: v for k, v in rec.items() if k in ("kind", "dataset_id", "visual_id", "report_id", "deck_id", "urls", "title")})
    result.finished_at = _now()
    bus.publish("pipeline.finished", f"Auswertung „{spec.name}“ {'fertig' if result.status == 'ok' else 'abgebrochen'}", run_id=run_id, pipeline=spec.name, status=result.status, artifacts=result.artifacts, error=result.error)
    return result


# ---------------------------------------------------------------- built-in pipelines (seed)

_SIGHTINGS_COLS = "ring, date, place, species, lat, lon, ringing_place, ringing_lat, ringing_lon, status, age"

BUILTIN_PIPELINES: list[dict[str, Any]] = [
    {
        "name": "Saison im Überblick",
        "description": "Wie viele Vögel waren in einem Jahr an einem Ort, in welchen Monaten – und wo genau? Monatsverlauf im Vergleich zu den Vorjahren, Karte der Sichtungen und ein kurzer Bericht.",
        "icon": "mdi-calendar-month",
        "tags": ["Saison", "Ort", "Bericht"],
        "parameters": [
            {"name": "ort", "label": "Ort", "type": "place", "help": "Teil des Ortsnamens, z. B. „Ostpark“."},
            {"name": "art", "label": "Art", "type": "species", "required": False, "help": "Leer lassen für alle Arten."},
            {"name": "jahr", "label": "Jahr", "type": "year"},
        ],
        "steps": [
            {"id": "saison", "kind": "analysis", "title": "Saisonverlauf berechnen", "spec": {"name": "seasonality", "args": {"place": "{{ort}}", "species": "{{art}}", "year_from": "{{jahr}}"}}},
            {"id": "vorjahre", "kind": "analysis", "title": "Vorjahre berechnen", "spec": {"name": "seasonality", "args": {"place": "{{ort}}", "species": "{{art}}"}}},
            {"id": "monate", "kind": "chart", "title": "Monatsverlauf", "spec": {"kind": "stacked_bar", "dataset_id": "$steps.vorjahre.dataset_id", "x": "monat", "y": "individuen", "series_column": "jahr", "month_axis": True, "title": "{{ort}}: verschiedene Vögel je Monat und Jahr", "subtitle": "Jede Ringnummer zählt je Monat einmal", "legend_title": "Jahr"}},
            {"id": "sichtungen", "kind": "query", "title": "Sichtungen des Jahres laden", "spec": {"name": "Sichtungen {{ort}} {{jahr}}", "description": "Alle Sichtungen {{jahr}} an Orten mit „{{ort}}“ im Namen, mit Koordinaten.", "sql": "SELECT " + _SIGHTINGS_COLS + " FROM v_sightings WHERE date IS NOT NULL AND lat IS NOT NULL AND place ILIKE '%' || {{ort|sql}} || '%' AND EXTRACT(YEAR FROM date) = {{jahr}}"}},
            {"id": "karte", "kind": "map", "title": "Karte der Sichtungen", "spec": {"title": "{{ort}} {{jahr}}: Sichtungen nach Jahreszeit", "points": [{"dataset_id": "$steps.sichtungen.dataset_id", "name": "Sichtungen", "color": {"mode": "season"}, "dedupe": "coords_per_group", "size": {"min": 9}}], "legend": {"title": "Jahreszeit"}}},
            {"id": "bericht", "kind": "report", "title": "Bericht", "spec": {"title": "{{ort}}: Saison {{jahr}}", "question": "Wie viele Vögel waren {{jahr}} am Ort „{{ort}}“, wann und wo?", "sections": [{"heading": "Monatsverlauf", "text": "Das Diagramm zeigt je Monat die Zahl der verschiedenen Vögel – im Vergleich zu den Vorjahren.", "visual_ids": ["$steps.monate.visual_id"]}, {"heading": "Wo wurden die Vögel gesehen?", "text": "Die Karte zeigt alle Sichtungen des Jahres, gefärbt nach Jahreszeit.", "visual_ids": ["$steps.karte.visual_id"]}], "methods_note": "Ort = alle Einträge, deren Ortsname „{{ort}}“ enthält."}},
        ],
        "outputs": ["monate", "karte", "bericht"],
    },
    {
        "name": "Vogel-Steckbrief",
        "description": "Alles über einen Vogel: Beringung, Sichtungen, Orte, Lebenslauf als Zeitstrahl, Karte seiner Wege und ein kurzer Bericht.",
        "icon": "mdi-bird",
        "tags": ["Vogel", "Ring", "Bericht"],
        "parameters": [{"name": "ring", "label": "Ringnummer", "type": "ring", "help": "Genau wie auf dem Ring, ohne Leerzeichen."}],
        "steps": [
            {"id": "profil", "kind": "analysis", "title": "Vogelprofil", "spec": {"name": "bird_profile", "args": {"ring": "{{ring}}"}}},
            {"id": "zeitstrahl", "kind": "chart", "title": "Lebenslauf", "spec": {"kind": "timeline", "dataset_id": "$steps.profil.sightings_dataset_id", "x": "date", "series_column": "place", "color_by": "season", "title": "Ring {{ring}}: wann an welchem Ort", "height": 600}},
            {"id": "karte", "kind": "map", "title": "Wege", "spec": {"title": "Ring {{ring}}: Beringungsort (▲) und Sichtungen (●)", "points": [{"dataset_id": "$steps.profil.sightings_dataset_id", "name": "Beringungsort", "lat_column": "ringing_lat", "lon_column": "ringing_lon", "shape": "triangle", "size": {"min": 16}, "color": {"mode": "fixed", "value": "#00436C", "label": "Beringungsort"}, "dedupe": "coords"}, {"dataset_id": "$steps.profil.sightings_dataset_id", "name": "Sichtungen", "color": {"mode": "season"}, "size": {"min": 9}, "label": {"column": "place", "font_size": 11}}], "tracks": [{"dataset_id": "$steps.profil.sightings_dataset_id", "group_column": "ring", "order_column": "date", "width": 1.5, "opacity": 0.6}], "legend": {"title": "Jahreszeit"}}},
            {"id": "bericht", "kind": "report", "title": "Bericht", "spec": {"title": "Steckbrief Ring {{ring}}", "question": "Wo und wann wurde der Vogel mit Ring {{ring}} gesehen?", "key_findings": ["$steps.profil.summary"], "sections": [{"heading": "Lebenslauf", "text": "Jeder Punkt ist eine Ablesung; die Farbe zeigt die Jahreszeit.", "visual_ids": ["$steps.zeitstrahl.visual_id"]}, {"heading": "Wege", "text": "Das Dreieck ist der Beringungsort, die Linien verbinden die Sichtungen in zeitlicher Reihenfolge.", "visual_ids": ["$steps.karte.visual_id"]}]}},
        ],
        "outputs": ["zeitstrahl", "karte", "bericht"],
    },
    {
        "name": "Woher kommen die Vögel?",
        "description": "Von welchen Beringungsorten stammen die Vögel einer Art, und wie weit ziehen sie? Flussdiagramm Beringungsort → weitester Fundort, Karte der weiten Funde und Tabelle der Weitwanderer.",
        "icon": "mdi-map-marker-distance",
        "tags": ["Herkunft", "Entfernung", "Karte"],
        "parameters": [
            {"name": "art", "label": "Art", "type": "species", "help": "z. B. Kanadagans"},
            {"name": "beringungsort", "label": "Beringungsort", "type": "place", "required": False, "help": "Teil des Beringungsortes; leer = alle."},
            {"name": "min_km", "label": "Mindestens km", "type": "number", "default": 5, "help": "Nur Vögel, deren weitester Fund mindestens so weit entfernt ist."},
        ],
        "steps": [
            {"id": "entfernung", "kind": "analysis", "title": "Entfernungen berechnen", "spec": {"name": "dispersal", "args": {"species": "{{art}}", "ringing_place": "{{beringungsort}}", "min_km": "{{min_km}}"}}},
            {"id": "fluss", "kind": "chart", "title": "Beringungsort → weitester Fundort", "spec": {"kind": "sankey", "dataset_id": "$steps.entfernung.per_bird_dataset_id", "source_column": "ringing_place", "target_column": "weitester_ort", "title": "{{art}}: vom Beringungsort zum weitesten Fundort (≥ {{min_km}} km)", "max_nodes": 30, "height": 800}},
            {"id": "karte", "kind": "map", "title": "Weite Funde", "spec": {"title": "{{art}}: weiteste Funde je Vogel", "flows": [{"dataset_id": "$steps.entfernung.per_bird_dataset_id", "from_lat_column": "ringing_lat", "from_lon_column": "ringing_lon", "to_lat_column": "lat", "to_lon_column": "lon", "color": "#D7263D"}], "points": [{"dataset_id": "$steps.entfernung.per_bird_dataset_id", "name": "Weitester Fund", "color": {"mode": "fixed", "value": "#D7263D", "label": "Weitester Fund"}, "label": {"column": "weitester_ort", "font_size": 11}}]}},
            {"id": "tabelle", "kind": "table", "title": "Weitwanderer", "spec": {"dataset_id": "$steps.entfernung.per_bird_dataset_id", "title": "{{art}}: die weitesten Funde", "sort_by": "max_km", "limit": 25, "columns": [{"name": "ring"}, {"name": "ringing_place", "label": "Beringungsort"}, {"name": "weitester_ort", "label": "Weitester Fundort"}, {"name": "datum_weitester_fund", "label": "Datum"}, {"name": "max_km", "label": "km", "bar": True}]}},
        ],
        "outputs": ["fluss", "karte", "tabelle"],
    },
]


def builtin_specs() -> list[PipelineSpec]:
    return [PipelineSpec.model_validate(p) for p in BUILTIN_PIPELINES]
