# Project: Vogelring

**Last Updated:** 2026-04-10

## Domain Concepts

- **Bird** — identified by its **ring** (metal leg band). Ring is primary key. Birds accumulate sightings over time.
- **Sighting (Eintrag)** — observation of a bird at a place/time. Key fields: `ring`, `reading`, `species`, `date`, `place`, `lat/lon`, `status`, `age`, `sex`, `group_size`, `partner`, `melder`, `melded`. See `vogelring-domain.md` for status/age codes.
- **Ringing (Beringung)** — initial banding event. Fields: `ring`, `ring_scheme`, `species`, `date`, `place`, `ringer`, `age`, `sex`, `status`
- **Family Relationships** — partners (by year), children, parents, siblings. Each has `year`, `confidence`, `source`, `notes`

## Technology Stack

| Layer | Stack |
|-------|-------|
| **Frontend** | Vue 3, Vuetify 3, Pinia, TypeScript, Vite 5 |
| **Maps** | Leaflet + leaflet.markercluster |
| **Charts** | ECharts via vue-echarts |
| **Backend** | FastAPI, SQLAlchemy 2, Pydantic 2, Python 3.11+ |
| **Database** | PostgreSQL 15 (Alpine) |
| **Infrastructure** | Docker Compose, Nginx reverse proxy, Cloudflare Tunnel + Zero Trust |
| **Package Mgmt** | npm (frontend), uv (backend) |

## Directory Structure

```
backend/
  src/
    api/routers/     # FastAPI route handlers (one file per domain)
    database/        # SQLAlchemy models, repositories, connection
    utils/           # Logging config, helpers
  tests/             # pytest tests
  scripts/           # Data import/migration scripts
frontend/
  src/
    api/index.ts     # Axios API layer (single file, all endpoints)
    components/      # Vue components (sightings/, map/, settings/, bird/)
    stores/          # Pinia stores (sightings, ringings, auth, version, relationships)
    views/           # Page-level components
      statistics/    # Analytics views (friends, radius, seasonal, data quality)
    types/           # TypeScript interfaces
    utils/           # Validation, age mapping, formatting helpers
    theme/           # Vuetify theme config
scripts/             # Deployment, backup, monitoring, migration
nginx/               # Nginx configs (dev + prod)
```

## Development Commands

| Task | Command |
|------|---------|
| **Full stack (Docker)** | `./dev.sh` |
| **Frontend dev** | `cd frontend && npm install && npm run dev` |
| **Frontend build** | `cd frontend && npm run build` |
| **Backend tests** | `cd backend && uv sync --extra test && uv run pytest` |
| **Backend tests + coverage** | `cd backend && uv run pytest --cov=src --cov-fail-under=80` |
| **Backend test runner** | `cd backend && uv run python scripts/run_tests.py` |
| **Docker up** | `docker compose up --build -d` |
| **Docker logs** | `docker compose logs -f` |
| **Deploy to Pi** | `./scripts/pi-deploy.sh [--prod] [--no-backup]` |

## Architecture

- **Backend routers** are domain-scoped: `sightings.py`, `ringings.py`, `birds.py`, `family.py`, `analytics.py`, `dashboard.py`, `reports.py`, `suggestions.py`, `health.py`, `auth.py`, `admin.py`, `places.py`, `species.py`
- **Frontend routes** are defined inline in `main.ts` (not in `router/index.ts` which is unused)
- **Frontend stores** use mixed patterns — some Composition API, some Options API
- **Auth** is handled by Cloudflare Zero Trust in prod; `DEVELOPMENT_MODE=true` bypasses auth locally
- **API layer** is a single file `frontend/src/api/index.ts` (~284 lines) with Axios

## Production Infrastructure

**Host:** Raspberry Pi (aarch64, Debian 12 Bookworm), SSH: `pi@pi-server.local`
**Storage:** 234GB NVMe SSD at `/mnt/ssd` (21% used)

### Containers (3 for Vogelring)

| Container | Port Binding | Notes |
|-----------|-------------|-------|
| `vogelring-postgres` | `127.0.0.1:5432` | PostgreSQL 15, data at `/mnt/ssd/data/vogelring/postgres`; from a laptop use `ssh -L 5432:127.0.0.1:5432 pi@pi-server` |
| `vogelring-api` | `127.0.0.1:8000` | FastAPI, logs at `/mnt/ssd/logs/vogelring` |
| `vogelring-nginx` | `127.0.0.1:80` | Serves frontend + proxies `/api/` to backend |

Pi also runs: Grafana (:3000), Prometheus (:9090), pgAdmin (:5050), LibreChat (:3080), n8n (:5678), neo4j, node-exporter, cadvisor.

### Cloudflare Tunnel (`pi-server`)

| Hostname | Service |
|----------|---------|
| `vogelring.com` | Vogelring app (`:80`) |
| `analytics.vogelring.com` | Streamlit analytics (`:8501`) |
| `monitoring.vogelring.com` | Grafana (`:3000`) |
| `db.vogelring.com` | pgAdmin (`:5050`) |
| `n8n.vogelring.com` | n8n (`:5678`) |
| `chat.vogelring.com` | LibreChat (`:3080`) |

### Data & Backups

```
/mnt/ssd/data/vogelring/
  postgres/          # PostgreSQL data volume
  backups/           # Daily SQL dumps (gzipped, 7-day retention)
  nginx_cache/       # Nginx proxy cache
/mnt/ssd/logs/vogelring/
  nginx/             # Nginx access/error logs
```

- **Cron:** Daily at 02:00 — `DATA_DIR=/mnt/ssd/data/vogelring /mnt/ssd/apps/vogelring/scripts/backup.sh`
- Backup creates SQL dump + compressed data archive, copies to `/mnt/ssd/data/shared/vogelring-backups/` for n8n access

### Deploy Workflow

```bash
# On local machine: push to GitHub
git push origin master

# On Pi (or via SSH):
cd /mnt/ssd/apps/vogelring
./scripts/pi-deploy.sh --prod
```

`pi-deploy.sh --prod` does: git pull → backup DB → stop containers → `npm ci && npm run build` → `docker compose build --no-cache` → `docker compose up -d` → health check → prune old images.

### Nginx (prod)

- Rate limiting: 10r/s for API, 1r/s for login
- Trusts Cloudflare IPs via `set_real_ip_from` + `CF-Connecting-IP` header
- Static assets cached 1 year (immutable), HTML cached 1 hour
- Security headers: HSTS, X-Frame-Options DENY, nosniff, XSS protection

## Conventions

- **Commits:** Conventional commit format (`feat:`, `fix:`, `chore:`, `refactor:`, `docs:`, `ci:`, `test:`). Never mention Claude Code in commit messages.
- **Branching:** Trunk-based on `master`. Use `feat/<name>` or `fix/<name>` branches for larger changes. No PRs — single developer workflow.
- **Releases:** release-please automates versioning and changelogs.
- **German UI:** User-facing text is in German (Einträge, Beringungen, etc.)
