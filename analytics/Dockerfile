# Vogelring analytics: MCP server (charts, maps, exports) for LibreChat plus the analytics web app.
# Build context is analytics/ (compose: build.context: ./analytics).

# --- Stage 1: web app (Vue 3 + Vite) -> /web/dist ---------------------------------------------
# web/ always exists (README.md, .gitkeep). Until web/package.json exists the stage only
# creates an empty dist/. A real build failure still fails the image build.
FROM node:22-alpine AS web
WORKDIR /web
COPY web/ ./
RUN if [ -f package.json ]; then npm ci && npm run build; else mkdir -p dist; fi

# --- Stage 2: Python server --------------------------------------------------------------------
# Base image ships Chromium + all its system deps for arm64/amd64.
FROM mcr.microsoft.com/playwright/python:v1.64.1-noble

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DATA_DIR=/data \
    BROWSER_CACHE_DIR=/data/browser-cache \
    PLAYWRIGHT_BROWSERS_PATH=/ms-playwright \
    WEB_DIR=/app/web

COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /uvx /bin/

WORKDIR /app
COPY server/pyproject.toml server/uv.lock server/README.md ./
COPY server/src ./src
COPY server/legacy ./legacy
RUN uv sync --no-dev --frozen 2>/dev/null || uv sync --no-dev

# The base image tag must match the locked playwright version (browsers are baked into the image).
RUN uv run --no-sync python -c "from importlib.metadata import version; v = version('playwright'); assert v == '1.64.1', v; print('playwright', v)"

# Copied after the Python layers so front-end changes do not invalidate the uv sync cache.
COPY --from=web /web/dist ./web

RUN mkdir -p /data && chown -R pwuser:pwuser /data /app
USER pwuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s CMD python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4).status == 200 else 1)"
CMD ["uv", "run", "--no-sync", "python", "-m", "vogelring_analytics.app"]
