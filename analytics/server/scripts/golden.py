"""Render the golden scenarios (derived from real chat requests) against a running server.

    uv run python scripts/golden.py [--url http://127.0.0.1:8000/mcp] [--out golden/out] [--only 3,5]

Each scenario runs SQL + a chart/map spec through the MCP tools and saves the inline image next to the
structured summary, so the output can be reviewed visually before deploying.
"""

from __future__ import annotations

import argparse
import asyncio
import base64
import json
from pathlib import Path

from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamable_http_client

OSTPARK_KG_2025 = """
SELECT ring, date, place, species, lat, lon, ringing_place, ringing_lat, ringing_lon, status
FROM v_sightings
WHERE ring IN (SELECT DISTINCT ring FROM v_sightings WHERE place ILIKE '%Ostpark%' AND species = 'Kanadagans'
               AND EXTRACT(MONTH FROM date) IN (5, 6) AND EXTRACT(YEAR FROM date) = 2025)
  AND date IS NOT NULL AND lat IS NOT NULL
"""

SCENARIOS: list[dict] = [
    {
        "name": "01_map_season_ostpark",
        "sql": OSTPARK_KG_2025,
        "map": {
            "title": "Wiederfunde der Kanadagänse mit Mai/Juni-Nachweis im Ostpark 2025",
            "points": [{"dataset_id": "$ds", "name": "Wiederfunde", "color": {"mode": "season"}, "size": {"min": 9}, "dedupe": "coords_per_group"}],
            "legend": {"title": "Wiederfunde"},
        },
    },
    {
        "name": "02_map_individuals_ringing_triangles",
        "sql": "SELECT ring, date, place, species, lat, lon, ringing_place, ringing_lat, ringing_lon FROM v_sightings WHERE species = 'Nilgans' AND ring LIKE 'W%' AND date IS NOT NULL AND lat IS NOT NULL",
        "map": {
            "title": "Nilgänse mit W-Ringen: Beringungsort (▲) und Wiederfunde (●)",
            "points": [
                {"dataset_id": "$ds", "name": "Beringungsort", "lat_column": "ringing_lat", "lon_column": "ringing_lon", "shape": "triangle", "size": {"min": 16}, "color": {"mode": "individual", "column": "ring"}, "dedupe": "coords_per_group"},
                {"dataset_id": "$ds", "name": "Wiederfund", "shape": "circle", "size": {"min": 10}, "color": {"mode": "individual", "column": "ring"}},
            ],
            "tracks": [{"dataset_id": "$ds", "group_column": "ring", "order_column": "date", "width": 1.5, "opacity": 0.6}],
            "legend": {"title": "Individuen"},
        },
    },
    {
        "name": "03_map_bubbles_per_place",
        "sql": """SELECT place, AVG(lat) AS lat, AVG(lon) AS lon, COUNT(DISTINCT ring) AS individuen, COUNT(*) AS sichtungen
                  FROM v_sightings WHERE species = 'Graugans' AND date IS NOT NULL AND lat IS NOT NULL
                  AND 6371 * acos(LEAST(1, cos(radians(50.11)) * cos(radians(lat)) * cos(radians(lon) - radians(8.68)) + sin(radians(50.11)) * sin(radians(lat)))) <= 28
                  GROUP BY place HAVING COUNT(DISTINCT ring) >= 3""",
        "map": {
            "title": "Graugänse: Aufenthaltsorte im Umkreis von 28 km um Frankfurt",
            "subtitle": "Kreisgröße = Anzahl verschiedener Individuen je Ort",
            "points": [{"dataset_id": "$ds", "name": "Orte", "color": {"mode": "fixed", "value": "#228096", "label": "Ort (Größe = Individuen)"}, "size": {"column": "individuen", "min": 8, "max": 44}, "label": {"column": "place", "font_size": 11}, "tooltip_columns": ["place", "individuen", "sichtungen"]}],
            "footnote": "Nur Orte mit mindestens 3 Individuen.",
        },
    },
    {
        "name": "04_map_far_recaptures_labels",
        "sql": """SELECT ring, date, place, species, lat, lon FROM v_sightings WHERE species = 'Nilgans' AND date IS NOT NULL AND lat IS NOT NULL
                  AND 6371 * acos(LEAST(1, cos(radians(50.11)) * cos(radians(lat)) * cos(radians(lon) - radians(8.68)) + sin(radians(50.11)) * sin(radians(lat)))) > 50""",
        "map": {
            "title": "Nilgans-Wiederfunde weiter als 50 km von Frankfurt",
            "points": [{"dataset_id": "$ds", "name": "Wiederfunde", "color": {"mode": "season"}, "size": {"min": 11}, "label": {"column": "place", "font_size": 12}, "dedupe": "column", "dedupe_column": "place"}],
            "markers": [{"lat": 50.11, "lon": 8.68, "shape": "star", "color": "#00436C", "size": 26, "label": "Frankfurt", "legend_label": "Frankfurt"}],
            "legend": {"title": "Wiederfunde"},
        },
    },
    {
        "name": "05_map_exclude_ostpark_star",
        "sql": OSTPARK_KG_2025 + " AND place NOT ILIKE '%Ostpark%'",
        "map": {
            "title": "Abgewanderte Kanadagänse",
            "subtitle": "Wiederfunde außerhalb des Ostparks",
            "points": [{"dataset_id": "$ds", "name": "Wiederfunde", "color": {"mode": "season"}, "size": {"min": 10}, "dedupe": "coords_per_group"}],
            "markers": [{"lat": 50.1178, "lon": 8.7147, "shape": "star", "color": "#00436C", "size": 28, "legend_label": "Ostpark (nicht dargestellt)"}],
            "zoom": 12, "center": [50.11, 8.72],
            "footnote": "Wiederfunde im Ostpark selbst sind nicht dargestellt.",
            "legend": {"title": "Wiederfunde"},
        },
    },
    {
        "name": "06_map_flows",
        "sql": """WITH s AS (SELECT DISTINCT ring, place FROM v_sightings WHERE species = 'Kanadagans' AND date IS NOT NULL AND lat IS NOT NULL),
                  pl AS (SELECT place, AVG(lat) AS lat, AVG(lon) AS lon FROM v_sightings WHERE lat IS NOT NULL GROUP BY place),
                  m AS (SELECT DISTINCT ring, place FROM s WHERE place ILIKE '%Ostpark%')
                  SELECT m.place AS von, p1.lat AS von_lat, p1.lon AS von_lon, s.place AS nach, p2.lat AS nach_lat, p2.lon AS nach_lon, COUNT(DISTINCT s.ring) AS voegel
                  FROM m JOIN s ON s.ring = m.ring AND s.place <> m.place JOIN pl p1 ON p1.place = m.place JOIN pl p2 ON p2.place = s.place
                  GROUP BY 1,2,3,4,5,6 HAVING COUNT(DISTINCT s.ring) >= 5 ORDER BY voegel DESC""",
        "map": {
            "title": "Bewegungen der Ostpark-Kanadagänse zu anderen Orten",
            "flows": [{"dataset_id": "$ds", "name": "Vögel (Linienstärke)", "from_lat_column": "von_lat", "from_lon_column": "von_lon", "to_lat_column": "nach_lat", "to_lon_column": "nach_lon", "weight_column": "voegel", "label_column": "voegel"}],
            "markers": [{"lat": 50.1178, "lon": 8.7147, "shape": "star", "color": "#2E8B57", "size": 26, "label": "Ostpark", "legend_label": "Ostpark"}],
            "footnote": "Nur Verbindungen mit mindestens 5 Individuen.",
        },
    },
    {
        "name": "07_chart_stacked_ostpark_vs_fremd",
        "sql": """WITH ost AS (SELECT DISTINCT ring FROM v_sightings WHERE species='Kanadagans' AND place ILIKE '%Ostpark%' AND EXTRACT(YEAR FROM date)=2025 AND EXTRACT(MONTH FROM date) IN (5,6))
                  SELECT EXTRACT(MONTH FROM date)::int AS monat, CASE WHEN ring IN (SELECT ring FROM ost) THEN 'Ostparkvogel' ELSE 'Fremdvogel' END AS gruppe, COUNT(DISTINCT ring) AS individuen
                  FROM v_sightings WHERE species='Kanadagans' AND place ILIKE '%Ostpark%' AND EXTRACT(YEAR FROM date)=2025 GROUP BY 1,2""",
        "chart": {"kind": "stacked_bar", "dataset_id": "$ds", "title": "Kanadagänse im Ostpark 2025: Ostpark- vs. Fremdvögel", "x": "monat", "y": "individuen", "series_column": "gruppe", "month_axis": True, "show_totals": True, "stack_order": ["Ostparkvogel", "Fremdvogel"], "colors": {"Ostparkvogel": "#228096", "Fremdvogel": "#D07B4D"}, "y_axis": {"title": "Anzahl Individuen"}},
    },
    {
        "name": "08_chart_stacked_places_fixed_colors",
        "sql": """WITH ost AS (SELECT DISTINCT ring FROM v_sightings WHERE species='Graugans' AND place ILIKE '%Ostpark%' AND EXTRACT(MONTH FROM date) IN (5,6))
                  SELECT EXTRACT(MONTH FROM date)::int AS monat, place, COUNT(DISTINCT ring) AS individuen FROM v_sightings
                  WHERE ring IN (SELECT ring FROM ost) AND date IS NOT NULL AND place IN ('F, Ostpark','F, Rebstockpark','F, Höchst, Stadtpark','F, Mainkai, Innenstadt') GROUP BY 1,2""",
        "chart": {"kind": "stacked_bar", "dataset_id": "$ds", "title": "Wiederfunde der Ostpark-Graugänse nach Ort", "x": "monat", "y": "individuen", "series_column": "place", "month_axis": True,
                  "stack_order": ["F, Ostpark", "F, Rebstockpark", "F, Höchst, Stadtpark", "F, Mainkai, Innenstadt"], "colors": {"F, Ostpark": "#2E8B57", "F, Rebstockpark": "#D7263D", "F, Höchst, Stadtpark": "#1E3A8A", "F, Mainkai, Innenstadt": "#F39C12"}, "annotations": [{"kind": "band", "from": 5, "to": 6, "label": "Mauser"}], "y_axis": {"title": "Individuen"}},
    },
    {
        "name": "09_chart_top_places_horizontal",
        "sql": "SELECT place, COUNT(DISTINCT ring) AS individuen FROM v_sightings WHERE species = 'Kanadagans' AND date IS NOT NULL GROUP BY place",
        "chart": {"kind": "bar", "dataset_id": "$ds", "title": "Kanadagänse: Orte mit den meisten Individuen", "x": "place", "y": "individuen", "sort": "desc", "limit": 20, "horizontal": True, "show_values": True, "x_axis": {"title": "Anzahl Individuen"}},
    },
    {
        "name": "10_chart_line_mobility",
        "sql": """SELECT monat, AVG(orte) AS orte_pro_vogel, COUNT(*) AS voegel FROM (SELECT ring, EXTRACT(MONTH FROM date)::int AS monat, COUNT(DISTINCT place) AS orte FROM v_sightings WHERE species='Kanadagans' AND date IS NOT NULL GROUP BY 1,2) t GROUP BY monat""",
        "chart": {"kind": "line", "dataset_id": "$ds", "title": "Räumliche Aktivität der Kanadagänse im Jahresverlauf", "subtitle": "Durchschnittliche Zahl verschiedener Orte pro Vogel und Monat", "x": "monat", "y": "orte_pro_vogel", "month_axis": True, "show_values": True, "annotations": [{"kind": "band", "from": 6, "to": 7, "label": "Mauser (Jun–Jul)"}], "y_axis": {"title": "Ø Orte pro Vogel", "min": 1}},
    },
    {
        "name": "11_chart_species_pie",
        "sql": "SELECT species, COUNT(*) AS sichtungen FROM v_sightings WHERE date IS NOT NULL GROUP BY species",
        "chart": {"kind": "pie", "dataset_id": "$ds", "title": "Sichtungen nach Art", "x": "species", "y": "sichtungen", "color_by": "species", "sort": "desc", "limit": 8},
    },
    {
        "name": "12_chart_heatmap_place_month",
        "sql": "SELECT place, EXTRACT(MONTH FROM date)::int AS monat, COUNT(DISTINCT ring) AS individuen FROM v_sightings WHERE species='Graugans' AND date IS NOT NULL AND place IN (SELECT place FROM v_sightings WHERE species='Graugans' GROUP BY place ORDER BY COUNT(*) DESC LIMIT 10) GROUP BY 1,2",
        "chart": {"kind": "heatmap", "dataset_id": "$ds", "title": "Graugänse: Individuen je Ort und Monat", "x": "monat", "series_column": "place", "heat_value": "individuen", "month_axis": True, "show_values": True, "height": 560},
    },
]


def _fill(obj, ds):
    if isinstance(obj, dict):
        return {k: _fill(v, ds) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_fill(v, ds) for v in obj]
    return ds if obj == "$ds" else obj


async def run(url: str, out: Path, only: set[str] | None) -> int:
    out.mkdir(parents=True, exist_ok=True)
    failures = 0
    async with streamable_http_client(url) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            for sc in SCENARIOS:
                if only and not any(sc["name"].startswith(o) for o in only):
                    continue
                print(f"== {sc['name']}")
                q = await s.call_tool("query_sql", {"sql": sc["sql"], "name": sc["name"]})
                if q.is_error or not q.structured_content:
                    print("   query failed:", [c.text for c in q.content if c.type == "text"][:1])
                    failures += 1
                    continue
                ds = q.structured_content["dataset_id"]
                print(f"   rows={q.structured_content['row_count']}")
                tool, spec = ("create_map", sc["map"]) if "map" in sc else ("create_chart", sc["chart"])
                res = await s.call_tool(tool, {"spec": _fill(spec, ds)})
                texts = [c.text for c in res.content if c.type == "text"]
                if res.is_error:
                    print("   FAILED:", texts[:1])
                    failures += 1
                    continue
                for c in res.content:
                    if c.type == "image":
                        ext = "jpg" if c.mime_type == "image/jpeg" else "png"
                        (out / f"{sc['name']}.{ext}").write_bytes(base64.b64decode(c.data))
                (out / f"{sc['name']}.json").write_text(json.dumps(res.structured_content, ensure_ascii=False, indent=1))
                print("   ok:", (res.structured_content or {}).get("interactive_url"))
    print(f"done, {failures} failures")
    return failures


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="http://127.0.0.1:8000/mcp")
    ap.add_argument("--out", default="golden/out")
    ap.add_argument("--only", default="")
    a = ap.parse_args()
    only = {x.strip() for x in a.only.split(",") if x.strip()} or None
    raise SystemExit(1 if asyncio.run(run(a.url, Path(a.out), only)) else 0)
