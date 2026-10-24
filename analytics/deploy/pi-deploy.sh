#!/usr/bin/env bash
# Deploy Vogelring analytics (MCP server + web app) to the Pi. Run from the Mac:
#   analytics/deploy/pi-deploy.sh [pi-host]
# Syncs analytics/ to /mnt/ssd/apps/librechat/analytics, migrates the LibreChat compose file from the
# old analytics-mcp layout if needed, builds the image on the Pi, restarts the container and LibreChat
# (MCP servers are initialised at LibreChat startup).
set -euo pipefail
HOST="${1:-pi@100.94.198.32}"
SRC="$(cd "$(dirname "$0")/.." && pwd)"   # analytics/
LC=/mnt/ssd/apps/librechat
DEST=$LC/analytics

rsync -a --delete \
  --exclude /server/.venv --exclude /server/golden/out --exclude /server/data \
  --exclude /web/node_modules --exclude /web/dist \
  --exclude __pycache__ --exclude .pytest_cache --exclude .DS_Store \
  "$SRC/" "$HOST:$DEST/"
# Deployment skills for LibreChat agents (mounted read-only at /app/skill) and the agent prompt.
rsync -a --delete "$SRC/agent/skills/" "$HOST:$LC/skills/"
rsync -a "$SRC/agent/prompt/vogelring-analyst.md" "$HOST:$LC/vogelring-analyst-prompt.md"

ssh "$HOST" "LC='$LC' bash -s" <<'REMOTE'
set -euo pipefail
cd "$LC"
grep -q "analytics-mcp:" docker-compose.yml || { echo "docker-compose.yml has no analytics-mcp service; merge deploy/librechat-compose.snippet.yml first"; exit 1; }
[ -f .env.analytics ] || { echo "missing $LC/.env.analytics (DATABASE_URL, CARTO_BASEMAP_KEY)"; exit 1; }

# --- Migrate docker-compose.yml (hand-maintained): new build context + port 8501 -----------------
mkdir -p backups
BAK="backups/docker-compose.yml.$(date +%Y%m%d-%H%M%S)"
cp -p docker-compose.yml "$BAK"

# (a) build context ./analytics-mcp -> ./analytics
sed -i -E -e 's#(context:[[:space:]]*)\./analytics-mcp([[:space:]]|$)#\1./analytics\2#' \
  -e 's#analytics-mcp/deploy/pi-deploy\.sh#analytics/deploy/pi-deploy.sh#' docker-compose.yml

# (c) the analytics-mcp service must publish 127.0.0.1:8001:8000 (charts.vogelring.com) and
#     127.0.0.1:8501:8000 (analytics.vogelring.com, formerly the Streamlit container).
python3 - docker-compose.yml <<'PY'
import re, sys

path = sys.argv[1]
lines = open(path, encoding="utf-8").read().split("\n")
indent = lambda s: len(s) - len(s.lstrip(" "))
significant = lambda s: s.strip() and not s.lstrip().startswith("#")

svc = next((i for i, l in enumerate(lines) if re.match(r"^\s+analytics-mcp:\s*(#.*)?$", l)), None)
if svc is None:
    sys.exit("compose edit: analytics-mcp service not found")
svc_ind = indent(lines[svc])
end = next((j for j in range(svc + 1, len(lines)) if significant(lines[j]) and indent(lines[j]) <= svc_ind), len(lines))
key_ind = next((indent(lines[j]) for j in range(svc + 1, end) if significant(lines[j])), svc_ind + 2)

wanted = [
    ("8001:8000", '"127.0.0.1:8001:8000"   # charts.vogelring.com (cloudflared -> localhost:8001)'),
    ("8501:8000", '"127.0.0.1:8501:8000"     # analytics.vogelring.com (cloudflared -> localhost:8501)'),
]

ports = next((k for k in range(svc + 1, end) if indent(lines[k]) == key_ind and re.match(r"^\s+ports:", lines[k])), None)
if ports is None:
    lines[svc + 1:svc + 1] = [" " * key_ind + "ports:"]
    ports, end = svc + 1, end + 1
elif not re.match(r"^\s+ports:\s*(#.*)?$", lines[ports]):
    sys.exit("compose edit: inline/flow-style ports list not supported, edit docker-compose.yml by hand")

# list items: following lines that are blank/comments or '- ...' entries at indent >= key_ind
last, item_ind = ports, None
for k in range(ports + 1, end):
    s = lines[k]
    if not significant(s):
        continue
    if s.lstrip().startswith("- ") and indent(s) >= key_ind:
        item_ind = item_ind if item_ind is not None else indent(s)
        last = k
        continue
    break
item_ind = item_ind if item_ind is not None else key_ind + 2
items = [l for l in lines[ports + 1:last + 1] if significant(l)]

missing = [entry for needle, entry in wanted if not any(needle in l.split("#")[0] for l in items)]
if not missing:
    print("compose edit: ports already ok")
    sys.exit(0)
lines[last + 1:last + 1] = [" " * item_ind + "- " + entry for entry in missing]
open(path, "w", encoding="utf-8").write("\n".join(lines))
print("compose edit: added ports", ", ".join(e.split()[0] for e in missing))
PY

if cmp -s docker-compose.yml "$BAK"; then
  rm -f "$BAK"
else
  echo "docker-compose.yml migrated (backup: $LC/$BAK):"
  diff -u "$BAK" docker-compose.yml || true
  docker compose config -q || { echo "edited docker-compose.yml is invalid, restoring backup"; cp -p "$BAK" docker-compose.yml; exit 1; }
fi

# --- (d) build first, so a failed build leaves the old Streamlit app on 8501 running ------------------
docker compose build analytics-mcp

# --- (b) retire the old Streamlit container (own compose project in /mnt/ssd/apps/streamlit-app) ---
# Port 8501 now belongs to this service. The streamlit-app directory is left untouched.
if docker ps -a --format '{{.Names}}' | grep -qx vogelring-analytics; then
  echo "removing old Streamlit container vogelring-analytics"
  docker rm -f vogelring-analytics
fi

docker compose up -d --remove-orphans analytics-mcp
healthy=0
for i in $(seq 1 40); do
  if curl -sf http://127.0.0.1:8001/health >/dev/null; then healthy=1; echo "analytics-mcp healthy"; break; fi
  sleep 3
done
if [ "$healthy" != 1 ]; then
  echo "analytics-mcp did not become healthy; last logs:"
  docker compose logs --tail 50 analytics-mcp
  exit 1
fi
curl -sf -o /dev/null http://127.0.0.1:8501/health && echo "port 8501 ok" || echo "WARNING: port 8501 not answering"

[ -d "$LC/analytics-mcp" ] && echo "note: old sync dir $LC/analytics-mcp is no longer used and can be removed"

# --- (e) LibreChat re-initialises MCP servers at startup ------------------------------------------
docker compose restart librechat
sleep 8
docker logs librechat --since 2m 2>&1 | sed -E 's/\x1b\[[0-9;]*m//g' | grep -E "\[MCP\]\[vogelring-analytics\]" | tail -5 || true
REMOTE
