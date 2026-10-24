# Vogelring analytics

Analytics for Vogelring: an MCP server for the LibreChat agent at chat.vogelring.com and the
analytics web app at analytics.vogelring.com. Both ship as one Docker image.

| Folder | Contents |
|--------|----------|
| `server/` | Python 3.12 package `vogelring_analytics` (uv): MCP tools, SQL datasets, charts, maps, exports, tests, golden renders |
| `web/` | Vue 3 + Vite web app, built into the image and served from `WEB_DIR` |
| `agent/` | LibreChat agent prompt (`prompt/vogelring-analyst.md`) and skills (`skills/*/SKILL.md`) |
| `deploy/` | Pi deploy script and the snippets merged into the LibreChat compose file, `librechat.yaml` and cloudflared |
| `Dockerfile` | Multi-stage build: node builds `web/`, then the Playwright Python image runs the server |

## Development

```
cd analytics/server && uv sync --extra test && uv run pytest
cd analytics/web && npm ci && npm run dev
```

See `server/README.md` for running the server locally and the environment variables.

## Deploy

```
analytics/deploy/pi-deploy.sh [pi-host]
```

The script syncs `analytics/` to `/mnt/ssd/apps/librechat/analytics` on the Pi and syncs the agent
skills and prompt. It then builds and restarts the `analytics-mcp` compose service and restarts LibreChat.
On the first run it migrates the compose file from the old `analytics-mcp/` layout, keeping a backup in
`/mnt/ssd/apps/librechat/backups/`. It also retires the old Streamlit container.

| Hostname | Pi port | Notes |
|----------|---------|-------|
| analytics.vogelring.com | 8501 | web app |
| charts.vogelring.com | 8001 | alias, `PUBLIC_BASE_URL` for links from the chat |
