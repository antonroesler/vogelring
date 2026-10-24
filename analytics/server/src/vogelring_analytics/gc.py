"""Retention: delete datasets, visuals and exports older than RETENTION_DAYS unless a report references them."""

from __future__ import annotations

import json
import logging
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path

from .settings import settings

log = logging.getLogger(__name__)


def _referenced_by_reports() -> tuple[set[str], set[str]]:
    visuals: set[str] = set()
    datasets: set[str] = set()
    for p in settings.reports_dir.glob("rp_*/meta.json"):
        try:
            m = json.loads(p.read_text())
            visuals.update(m.get("visual_ids", []))
            datasets.update(m.get("dataset_ids", []))
        except Exception:
            continue
    return visuals, datasets


def _referenced_by_visuals() -> set[str]:
    out: set[str] = set()
    for p in settings.visuals_dir.glob("vz_*/meta.json"):
        try:
            out.update(json.loads(p.read_text()).get("dataset_ids", []))
        except Exception:
            continue
    return out


def _older_than(path: Path, cutoff: datetime) -> bool:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc) < cutoff
    except OSError:
        return False


def collect_garbage(days: int | None = None) -> dict[str, int]:
    days = days or settings.retention_days
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    keep_v, keep_d = _referenced_by_reports()
    removed = {"visuals": 0, "datasets": 0, "exports": 0}
    for d in settings.visuals_dir.glob("vz_*"):
        if d.name not in keep_v and _older_than(d / "meta.json", cutoff):
            shutil.rmtree(d, ignore_errors=True)
            removed["visuals"] += 1
    keep_d |= _referenced_by_visuals()
    for d in settings.datasets_dir.glob("ds_*"):
        if d.name not in keep_d and _older_than(d / "meta.json", cutoff):
            shutil.rmtree(d, ignore_errors=True)
            removed["datasets"] += 1
    for f in settings.exports_dir.glob("*"):
        if f.is_file() and _older_than(f, cutoff):
            f.unlink(missing_ok=True)
            removed["exports"] += 1
    if any(removed.values()):
        log.info("GC removed %s", removed)
    return removed
