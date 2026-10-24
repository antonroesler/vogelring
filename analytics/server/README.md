# Vogelring analytics server

Python package `vogelring_analytics`, deployed as the `analytics-mcp` compose service (see `../README.md`).

MCP server behind chat.vogelring.com: read-only SQL datasets, charts (ECharts), maps (Leaflet + CARTO),
exports (XLSX/CSV), rendered headlessly to PNG/PDF and served as interactive pages.

```
cd analytics/server
uv sync --extra test && uv run playwright install chromium
DATA_DIR=./data DATABASE_URL=postgresql://... PUBLIC_BASE_URL=http://127.0.0.1:8000 uv run python -m vogelring_analytics.app
uv run pytest
uv run python scripts/golden.py            # renders golden scenarios into golden/out
```

Endpoints: `/mcp` (streamable HTTP), `/viz/<id>` (interactive), `/viz/<id>.png|.pdf|.xlsx`, `/files/<name>`,
`/tiles/<style>/z/x/y.png` (cached basemap proxy), `/health`.
Tools: `describe_schema`, `query_sql`, `get_dataset`, `list_datasets`, `export_dataset`, `create_chart`,
`create_map`, `update_visual`, `list_visuals`.

Env: `DATABASE_URL`, `DATA_DIR`, `PUBLIC_BASE_URL`, `CARTO_BASEMAP_KEY`, `TILE_REFERER`, `PORT`,
`MCP_ALLOWED_HOSTS`, `MAX_ROWS`, `STATEMENT_TIMEOUT_MS`, `RENDER_TIMEOUT_S`.
`WEB_DIR` (set to `/app/web` in the image) points at the built web app from `../web`.
See `docs/plans/2026-10-23-analytics-mcp-rewrite.md` and `docs/plans/2026-10-24-analytics-2-0.md` (repo root).
