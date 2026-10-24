"""Visual store: spec + prepared model + rendered files per visual id."""

from __future__ import annotations

import json
import threading
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .datasets import new_id
from .settings import settings


@dataclass
class VisualMeta:
    id: str
    kind: str  # "chart" | "map"
    title: str | None
    created_at: str
    updated_at: str
    dataset_ids: list[str]
    width: int
    height: int
    summary: dict[str, Any] = field(default_factory=dict)
    history: list[dict[str, Any]] = field(default_factory=list)


class VisualStore:
    def __init__(self, root: Path | None = None) -> None:
        self.root = root or settings.visuals_dir
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def dir(self, visual_id: str) -> Path:
        if not visual_id or any(ch in visual_id for ch in "/\\.."):
            raise KeyError(f"Invalid visual id: {visual_id!r}")
        return self.root / visual_id

    def create(self, kind: str, spec: dict[str, Any], model: dict[str, Any], *, title: str | None, dataset_ids: list[str], width: int, height: int, summary: dict[str, Any]) -> VisualMeta:
        visual_id = new_id("vz_")
        d = self.dir(visual_id)
        d.mkdir(parents=True, exist_ok=False)
        now = datetime.now(timezone.utc).isoformat(timespec="seconds")
        meta = VisualMeta(id=visual_id, kind=kind, title=title, created_at=now, updated_at=now, dataset_ids=dataset_ids, width=width, height=height, summary=summary)
        self._write(d, spec, model, meta)
        return meta

    def update(self, visual_id: str, spec: dict[str, Any], model: dict[str, Any], *, title: str | None, dataset_ids: list[str], width: int, height: int, summary: dict[str, Any], patch: dict[str, Any]) -> VisualMeta:
        meta = self.meta(visual_id)
        meta.title = title
        meta.updated_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
        meta.dataset_ids = dataset_ids
        meta.width, meta.height, meta.summary = width, height, summary
        meta.history.append({"at": meta.updated_at, "patch": patch})
        self._write(self.dir(visual_id), spec, model, meta)
        return meta

    def _write(self, d: Path, spec: dict[str, Any], model: dict[str, Any], meta: VisualMeta) -> None:
        with self._lock:
            (d / "spec.json").write_text(json.dumps(spec, ensure_ascii=False, indent=1, default=str))
            (d / "model.json").write_text(json.dumps(model, ensure_ascii=False, default=str))
            (d / "meta.json").write_text(json.dumps(asdict(meta), ensure_ascii=False, indent=1))

    def meta(self, visual_id: str) -> VisualMeta:
        p = self.dir(visual_id) / "meta.json"
        if not p.exists():
            raise KeyError(f"Unknown visual id: {visual_id}")
        return VisualMeta(**json.loads(p.read_text()))

    def spec(self, visual_id: str) -> dict[str, Any]:
        return json.loads((self.dir(visual_id) / "spec.json").read_text())

    def model(self, visual_id: str) -> dict[str, Any]:
        return json.loads((self.dir(visual_id) / "model.json").read_text())

    def exists(self, visual_id: str) -> bool:
        try:
            return (self.dir(visual_id) / "meta.json").exists()
        except KeyError:
            return False

    def list(self, limit: int = 20) -> list[VisualMeta]:
        metas: list[VisualMeta] = []
        for p in self.root.glob("vz_*/meta.json"):
            try:
                metas.append(VisualMeta(**json.loads(p.read_text())))
            except Exception:
                continue
        metas.sort(key=lambda m: m.updated_at, reverse=True)
        return metas[:limit]

    def write_bytes(self, visual_id: str, name: str, data: bytes) -> Path:
        p = self.dir(visual_id) / name
        p.write_bytes(data)
        return p

    def file(self, visual_id: str, name: str) -> Path | None:
        p = self.dir(visual_id) / name
        return p if p.exists() else None


def merge_patch(target: Any, patch: Any) -> Any:
    """RFC 7396 JSON merge patch."""
    if not isinstance(patch, dict):
        return patch
    result = dict(target) if isinstance(target, dict) else {}
    for k, v in patch.items():
        if v is None:
            result.pop(k, None)
        else:
            result[k] = merge_patch(result.get(k), v)
    return result
