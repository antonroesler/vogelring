"""Turn a TableSpec + dataset into a table model (rendered by the table template, exported as XLSX)."""

from __future__ import annotations

import math
from typing import Any

import pandas as pd

from .specs import ColumnSpec, TableSpec


class TableBuildError(ValueError):
    pass


AUTO_LABELS = {
    "ring": "Ring", "species": "Art", "place": "Ort", "date": "Datum", "status": "Status", "age": "Alter", "sex": "Geschlecht",
    "ringing_place": "Beringungsort", "ringing_date": "Beringungsdatum", "ringed_as_species": "Art (Beringung)", "melder": "Melder",
    "partner": "Partner", "comment": "Kommentar", "lat": "Breite", "lon": "Länge", "km": "km", "max_km": "Max. km",
    "sichtungen": "Sichtungen", "individuen": "Individuen", "voegel": "Vögel", "anzahl": "Anzahl", "jahr": "Jahr", "monat": "Monat",
    "monat_name": "Monat", "beringt": "Beringt", "wiedergefunden": "Wiedergefunden", "wiederfundrate_prozent": "Wiederfundrate %",
    "beringungsjahr": "Beringungsjahr", "beringungsort": "Beringungsort", "art": "Art", "erste_sichtung": "Erste Sichtung",
    "letzte_sichtung": "Letzte Sichtung", "tage_bis_erste": "Tage bis 1. Sichtung", "am_ort": "Am Ort", "orte": "Orte",
    "anteil_am_ort_prozent": "Anteil am Ort %", "jahre_am_ort": "Jahre am Ort", "rueckkehrrate_prozent": "Rückkehrrate %",
    "ortstreue_unter_wiedergesehenen_prozent": "Ortstreue %", "voegel_am_ort": "Vögel am Ort", "gemeinsame_tage": "Gemeinsame Tage",
    "gemeinsame_orte": "Gemeinsame Orte", "anteil_prozent": "Anteil %", "weitester_ort": "Weitester Ort", "datum_weitester_fund": "Datum",
    "klasse": "Klasse", "beobachtungstage": "Beobachtungstage", "erste": "Erste", "letzte": "Letzte", "n": "Anzahl",
    "nach_1_jahr_noch_gesehen_prozent": "Nach 1 Jahr %", "nach_3_jahren_noch_gesehen_prozent": "Nach 3 Jahren %",
    "sichtungen_je_wiedergefundenem_vogel_median": "Sichtungen/Vogel (Median)", "tage_bis_erste_sichtung_median": "Tage bis 1. Sichtung (Median)",
    "max_entfernung_km_median": "Max. Entfernung km (Median)", "alter_bei_beringung": "Alter bei Beringung", "alter_bei_beringung_text": "Alter bei Beringung",
}


def auto_label(name: str) -> str:
    return AUTO_LABELS.get(str(name).lower(), str(name).replace("_", " ").capitalize())


def _is_num(s: pd.Series) -> bool:
    return pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)


def _auto_format(df: pd.DataFrame, col: str) -> str:
    s = df[col]
    name = str(col).lower()
    if pd.api.types.is_datetime64_any_dtype(s):
        return "date"
    if name == "ring":
        return "link_ring"
    if name == "id" and s.map(lambda v: isinstance(v, str) and len(v) == 36).all() and len(s):
        return "link_sighting"
    if _is_num(s):
        if "prozent" in name or "anteil" in name or name.endswith("_pct") or name.endswith("%"):
            return "percent"
        if pd.api.types.is_integer_dtype(s) or s.dropna().map(lambda v: float(v).is_integer()).all():
            return "integer"
        return "number"
    return "text"


def _fmt(v: Any, fmt: str, decimals: int | None) -> str:
    if v is None or (isinstance(v, float) and math.isnan(v)) or v is pd.NaT:
        return ""
    if fmt == "date":
        try:
            return pd.Timestamp(v).strftime("%d.%m.%Y")
        except Exception:
            return str(v)
    if fmt in ("integer", "number", "percent"):
        try:
            f = float(v)
        except (TypeError, ValueError):
            return str(v)
        if fmt == "integer":
            return f"{int(round(f)):,}".replace(",", ".")
        d = 1 if decimals is None else decimals
        txt = f"{f:,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
        return txt + (" %" if fmt == "percent" else "")
    if isinstance(v, float) and v.is_integer():
        return str(int(v))
    return str(v)


def build_table_model(spec: TableSpec, df: pd.DataFrame) -> tuple[dict[str, Any], dict[str, Any]]:
    cols = spec.columns or [ColumnSpec(name=str(c)) for c in df.columns]
    for c in cols:
        if c.name not in df.columns:
            raise TableBuildError(f"Column '{c.name}' not in dataset. Available: {', '.join(map(str, df.columns))}")
    if spec.sort_by:
        if spec.sort_by not in df.columns:
            raise TableBuildError(f"sort_by '{spec.sort_by}' not in dataset.")
        df = df.sort_values(spec.sort_by, ascending=not spec.sort_desc, kind="stable")
    total_rows = len(df)
    shown = df.head(spec.limit)

    columns = []
    for c in cols:
        fmt = c.format if c.format != "auto" else _auto_format(df, c.name)
        align = c.align if c.align != "auto" else ("right" if fmt in ("integer", "number", "percent") else "left")
        numeric = _is_num(df[c.name])
        col: dict[str, Any] = {"name": c.name, "label": c.label or auto_label(c.name), "format": fmt, "align": align, "numeric": numeric, "bar": c.bar and numeric}
        if c.width:
            col["width"] = c.width
        if col["bar"]:
            mx = float(pd.to_numeric(df[c.name], errors="coerce").max() or 0)
            col["max"] = mx
        if c.name in spec.highlight_max and numeric:
            col["max_value"] = float(pd.to_numeric(shown[c.name], errors="coerce").max())
        columns.append(col)

    rows = []
    for _, r in shown.iterrows():
        cells = []
        for c, col in zip(cols, columns):
            raw = r[c.name]
            cell: dict[str, Any] = {"text": _fmt(raw, col["format"], c.decimals)}
            if col["numeric"] and raw is not None and not (isinstance(raw, float) and math.isnan(raw)):
                cell["value"] = float(raw)
                if col.get("bar") and col.get("max"):
                    cell["bar"] = max(0.0, min(1.0, float(raw) / col["max"]))
                if "max_value" in col and float(raw) == col["max_value"]:
                    cell["hl"] = True
            elif pd.api.types.is_datetime64_any_dtype(df[c.name]) and raw is not pd.NaT and raw is not None:
                try:
                    cell["value"] = pd.Timestamp(raw).strftime("%Y-%m-%d")
                except Exception:
                    pass
            if col["format"] == "link_ring" and cell["text"]:
                cell["href"] = f"https://vogelring.com/birds/{cell['text']}"
            elif col["format"] == "link_sighting" and cell["text"]:
                cell["href"] = f"https://vogelring.com/entries/{cell['text']}"
            cells.append(cell)
        rows.append(cells)

    totals = None
    if spec.totals_row:
        totals = []
        for c, col in zip(cols, columns):
            if col["numeric"] and col["format"] != "percent":
                v = float(pd.to_numeric(shown[c.name], errors="coerce").sum())
                totals.append(_fmt(v, col["format"], c.decimals))
            else:
                totals.append("")
        if totals and not any(totals):
            totals = None
        elif totals:
            totals[0] = totals[0] or "Summe"

    height = 96 + 30 * (len(rows) + 1 + (1 if totals else 0)) + (28 if spec.footnote else 0) + (30 if spec.subtitle else 0)
    model = {
        "kind": "table",
        "title": spec.title,
        "subtitle": spec.subtitle,
        "footnote": spec.footnote,
        "width": spec.width,
        "height": min(max(height, 180), 2400),
        "font_size": spec.font_size,
        "row_number": spec.row_number,
        "columns": columns,
        "rows": rows,
        "totals": totals,
        "total_rows": total_rows,
        "shown_rows": len(rows),
    }
    summary = {"rows_total": total_rows, "rows_shown": len(rows), "columns": [c["label"] for c in columns]}
    if total_rows > len(rows):
        summary["notes"] = [f"{len(rows)} von {total_rows} Zeilen gezeigt; alle Zeilen stehen im XLSX-Export."]
    return model, summary
