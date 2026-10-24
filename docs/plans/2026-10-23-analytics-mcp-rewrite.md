# Analytics MCP rewrite (chat.vogelring.com charts & maps)

**Date:** 2026-10-23 · **Status:** deployed 2026-10-23 (milestones 1–4 done); see Open items

## Why

The LibreChat analytics tooling (`/mnt/ssd/apps/librechat/chart-server/server.py`, untracked on the Pi)
makes the model write raw matplotlib code per request. Results are unreliable (blank maps, metres on
axes, HOT-OSM clutter, 1–3 MB PNGs), there is no house style, download links 302 into a Cloudflare
Access login because `charts.vogelring.com` has no tunnel ingress, and the DB reader role can read
`users`/`organizations`.

Mined from Mongo (600 user messages, 232 conversations): ~60 % of requests are maps or charts with
precise, recurring conventions (season colours, ringing site = triangle, recapture = circle, bubble
size = individuals per place, movement lines, excluded place marked with a star + footnote, place
labels beside points, stacked monthly bars with fixed colour/stack order, follow-up edits of titles).

## Decisions (agreed 2026-10-23)

- Code lives in this repo: `analytics-mcp/` (Python 3.12, uv, MCP SDK 2.x, streamable HTTP).
- Typed, declarative tools only. The model never writes Python. Gaps become server features.
- Browser rendering: one HTML template per visual (Leaflet + CARTO light, ECharts 6 with a house
  theme matching the Vue app). Headless Chromium (Playwright) screenshots it for the inline PNG
  (2× DPR) and PDF; the same page is served as the interactive version.
- Interactive pages and high-quality exports (PNG 2×, PDF, formatted XLSX/CSV) are required.

## Architecture

```
analytics-mcp/
  pyproject.toml            uv project, hatchling
  Dockerfile                FROM mcr.microsoft.com/playwright/python:<ver>-noble (arm64 ok)
  src/vogelring_analytics/
    app.py                  Starlette app: /mcp (MCPServer), /viz/{id}[.png|.pdf], /files/{name}, /health
    server.py               MCPServer, tools, resources, lifespan (db pool + browser)
    settings.py             env config
    db.py                   psycopg pool; read-only tx, statement_timeout, row cap, SQL guard
    datasets.py             DataFrame store on disk: id -> parquet + meta; preview/stats helpers
    schema.py               curated German data dictionary (resource + tool)
    specs.py                Pydantic specs: MapSpec, ChartSpec (validated tool input)
    tools_query.py          query_sql, get_dataset, describe_schema, export_dataset
    tools_map.py            create_map
    tools_chart.py          create_chart
    tools_visual.py         update_visual (merge-patch + re-render), list_visuals
    render/
      browser.py            Playwright singleton, render(spec) -> png/pdf, warm tiles
      templates/map.html    Leaflet + markercluster + legend + scalebar + labels + export buttons
      templates/chart.html  ECharts 6 + theme + export buttons
      static/               vendored leaflet 1.9.4, markercluster 1.5.3, echarts 6.1.0, theme.js
    exporters.py            formatted xlsx (openpyxl), csv
  tests/                    spec validation, sql guard, dataset store, render smoke (chromium)
  scripts/golden.py         renders golden scenarios from real requests into golden/*.png
  sql/grants.sql            tightened librechat_reader grants
  prompt/vogelring-analyst.md  new LibreChat agent prompt (German)
```

### Data flow

`query_sql(sql, name)` → runs in a read-only transaction (statement_timeout 30 s, ≤ 50 000 rows),
stores the result as a dataset, returns `dataset_id`, columns with types, row count, 25-row preview,
per-column stats. `create_map` / `create_chart` take `dataset_id` (or inline `rows` for tiny data),
never files. `update_visual(visual_id, patch)` applies a JSON merge-patch to the stored spec and
re-renders, so "ändere den Titel" costs one call. Every visual returns: inline PNG (ImageContent),
`interactive_url`, `png_url`, `pdf_url`, `visual_id`, and a short textual summary of what was drawn
(counts per legend class) so the model can describe it honestly.

### Map spec (highlights)

- `points[]`: dataset + lat/lon columns, `shape` (circle | triangle | star | square),
  `color` = `{mode: season | category | individual | fixed, column?, palette?}`,
  `size` = `{column?, min, max}` (bubble by count), `label` = `{column, font_size, placement}`,
  `cluster` bool, `opacity`.
- `tracks[]`: polylines per `group_column` ordered by `order_column` (bird movement), arrows optional.
- `flows[]`: aggregated lines between places with weight (movement directions).
- `markers[]`: fixed symbols with label (e.g. Ostpark ★).
- `legend` `{title, position}`, `footnote`, `title`, `subtitle`, `zoom` (auto | 8–16), `basemap`
  (light | dark | osm), `fit_padding`.
- Built-in **season palette** (Ingo's convention): Nov–Jan `#1E3A8A`, Feb–Mär `#F2C230`,
  Apr–Jun `#2E8B57`, Jul–Okt `#D7263D`. Species palette from `frontend/src/utils/colors.ts`.
- Cartography rules in the template: auto-fit with padding, CARTO light `@2x` tiles, scale bar,
  small attribution, halo'd labels with collision avoidance, triangles/stars as SVG markers with
  white stroke, cluster only when > 300 points unless requested.

### Chart spec (highlights)

`kind` (bar | stacked_bar | line | area | scatter | heatmap | pie | histogram), `x`, `y` or
`series` (column or list), `group_by` + `stack_order`, `colors` map, `sort`, `horizontal`,
`show_values`, `show_totals`, `axis` titles, `month_axis` (German month names), `annotations`
(vertical bands e.g. Mauser Jun–Jul). House theme: Inter, `#00436C` text, dashed split lines,
no axis lines, theme palette `#228096 #37906D #D07B4D #EAD054 #00436C #69AC91 #9BC8B6 #DC9C7A`.

### Serving & security

- Visuals and exports live under `/data/viz/<id>/`. IDs are 12-char random tokens. Pages are
  served by the same container; public URL `https://charts.vogelring.com/viz/<id>` behind the
  existing Cloudflare Access app (needs ingress `charts.vogelring.com → http://localhost:8001` in
  `/etc/cloudflared/config.yml`). Retention 180 days.
- DB: new grants file revokes `users`, `organizations`, `sighting_exports*` from `librechat_reader`,
  sets `default_transaction_read_only` and `statement_timeout` on the role. Password moves from
  compose into `.env`.
- SQL guard: single statement, must start with `SELECT`/`WITH`, no `;`, rejects `pg_` catalogs.
  Real enforcement is the read-only role.

### LibreChat integration

`librechat.yaml`: `mcpServers.vogelring-analytics` → `type: streamable-http`,
`url: http://analytics-mcp:8000/mcp`, `mcpSettings.allowedAddresses` updated. The agent prompt is
rewritten around analysis semantics (what the data can and cannot say, jargon, places, Mauser) and
the new tools; all "which Python variables exist" content is dropped.

## Milestones

1. Scaffold, settings, db + SQL guard, datasets store, query/describe/export tools, Starlette
   serving, tests. Dev against the Pi DB via SSH tunnel.
2. Chart template + theme, `create_chart`, `update_visual`, PNG/PDF export, golden charts.
3. Map template (layers, legend, labels, tracks, flows, markers), `create_map`, golden maps.
4. Prompt rewrite, Dockerfile + compose service, grants, tunnel ingress, LibreChat config,
   deploy, verify from the chat with the real golden prompts.

## Open items (after deploy)

- Verify from the chat UI (behind Cloudflare Access) with the real golden prompts; adjust the prompt
  if the model picks poor specs. Agent `Voglring` now runs on claude-sonnet-4-6; `gpt-6.1-sol` via the
  ChatGPT endpoint is the zero-API-cost alternative (switch in the agent settings).
- CARTO key is referrer-locked to vogelring.com; tiles are proxied with `TILE_REFERER`. Cleaner: add
  charts.vogelring.com to the key's allowed referrers in the CARTO dashboard.
- Retention/GC of `/data/viz` and `/data/datasets` is not implemented yet (RETENTION_DAYS unused).
- Dense label clusters (e.g. Heilbronn) still overlap; a leader-line layout or auto-zoom would help.
- The old `chart-server` directory and `tile_cache`/`chart_exports` volumes on the Pi can be deleted
  once the new server has been used for a while (`docker volume rm librechat_tile_cache librechat_chart_exports`).

## Golden scenarios (from real requests)

1. Map: Kanadagänse Mai/Jun Ostpark → all recaptures, season colours, legend "Wiederfunde".
2. Map: ringing site ▲ + recaptures ● per individual colour (Nilgänse W-Ringe).
3. Map: bubbles per place sized by distinct individuals, 28 km around Frankfurt.
4. Map: recaptures > 50 km with place labels (font 12) beside points.
5. Map: Ostpark excluded, marked ★, footnote with count, zoom 14.
6. Map: movement flows between Mauser sites (black lines, weighted).
7. Chart: stacked monthly bar Ostparkvogel vs Fremdvogel with totals.
8. Chart: stacked monthly bar by place with fixed colours and stack order.
9. Chart: distinct individuals per place, top 20, horizontal.
10. Chart: mean distinct places per month with Mauser band.
11. Table/export: ring × place matrix as XLSX.
12. Revise: change title, change a colour, change zoom on an existing visual.


## Phase 2 (2026-10-24): "best possible chat" build-out

Audience decision: Ingo and other ornithologists without computer background. Every answer explains in
plain German what was counted and how it was filtered ("So bin ich vorgegangen"); reports carry an
auto-generated "So wurde gezählt" section built from per-dataset plain-language descriptions.

### LibreChat (config on the Pi, `librechat.yaml` / `docker-compose.yml`)
- Agent capabilities: tools, actions, artifacts, ask_user_question, memory, skills, subagents,
  deferred_tools, context, file_search (execute_code dropped: needs the paid code-interpreter key).
- `memory:` block (validKeys begriffe/vorlieben/projekte/orte/person, memory agent = ChatGPT/gpt-6-luna).
- `interface.schedules` (Scheduled Chats, experimental) + `SCHEDULES_SINGLE_PROCESS=true`.
- Deployment skills mounted from `/mnt/ssd/apps/librechat/skills` → `/app/skill`
  (source: `analytics-mcp/skills/*/SKILL.md`, synced by `deploy/pi-deploy.sh`).
- Agent "Voglring": artifacts=default, subagents (self), skills_scope=all, memory_scope=user,
  ask_user_question tool, all MCP tools, conversation starters, new prompt.

### analytics-mcp v0.2.0
- `definitions.py`: named executable definitions (place_group, ring_group, period, filter, note),
  `{{Name}}` / `{{Name:column}}` macros expanded in `query_sql`; tools save/list/delete_definition.
- Datasets carry `description` (plain language) + `source`; `query_sql`/`transform_dataset` take it.
- `transforms.py`: typed ops (filter, select, rename, derive year/month/season/distance_km/bucket/ratio…,
  group, sort, head, distinct, pivot, join, rank) → `transform_dataset`.
- `analysis.py`: bird_profile, cohort_resighting, site_fidelity, dispersal, seasonality, companions,
  whats_new, data_quality (10 checks) – each with `how_to_read` and dataset ids.
- Charts: timeline, calendar, sankey (cycle-safe), boxplot, graph (components + edge types),
  `facet_column` small multiples. Tables: `create_table` (German formats, ring links, bars, totals,
  sortable page). `?embed=1` chrome-less page for artifacts/iframes.
- `reports.py`: `create_report` → HTML, A4 PDF (page numbers), DOCX; key findings box, numbered
  figures/tables, recommendations, "So wurde gezählt" from dataset facts, SQL appendix.
- `gc.py`: retention (RETENTION_DAYS, default 180) sparing anything referenced by reports.
- Tests: 38 passing (`uv run pytest`).

### Open
- Cloudflare Access: `/viz`, `/reports`, `/static`, `/tiles`, `/files` on charts.vogelring.com should be
  reachable without login (unguessable ids) so artifacts/iframes and shared links work; `/mcp` stays protected.
- Verify Scheduled Chats + memory end-to-end in the UI; decide whether Ingo's role gets SCHEDULES.CREATE.
- Dense label clusters on maps; CARTO key referrer for charts.vogelring.com.
