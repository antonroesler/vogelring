"""On-disk dataset store: query results as parquet + metadata, addressable by id."""

from __future__ import annotations

import json
import secrets
import threading
from collections import OrderedDict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

from .settings import settings


def new_id(prefix: str = "") -> str:
    return prefix + secrets.token_urlsafe(9)[:12]


@dataclass
class DatasetMeta:
    id: str
    name: str
    sql: str
    created_at: str
    row_count: int
    columns: list[dict[str, str]]
    truncated: bool = False
    extra: dict[str, Any] = field(default_factory=dict)
    description: str = ""
    source: str = "sql"


def _dtype_label(s: pd.Series) -> str:
    if pd.api.types.is_datetime64_any_dtype(s):
        return "date"
    if pd.api.types.is_bool_dtype(s):
        return "bool"
    if pd.api.types.is_integer_dtype(s):
        return "int"
    if pd.api.types.is_numeric_dtype(s):
        return "number"
    return "text"


def column_specs(df: pd.DataFrame) -> list[dict[str, str]]:
    return [{"name": str(c), "type": _dtype_label(df[c])} for c in df.columns]


class DatasetStore:
    def __init__(self, root: Path | None = None, cache_size: int = 32) -> None:
        self.root = root or settings.datasets_dir
        self.root.mkdir(parents=True, exist_ok=True)
        self._cache: OrderedDict[str, pd.DataFrame] = OrderedDict()
        self._cache_size = cache_size
        self._lock = threading.Lock()

    def _dir(self, dataset_id: str) -> Path:
        if not dataset_id or any(ch in dataset_id for ch in "/\\.."):
            raise KeyError(f"Invalid dataset id: {dataset_id!r}")
        return self.root / dataset_id

    def save(self, df: pd.DataFrame, *, name: str, sql: str, truncated: bool = False, extra: dict | None = None, description: str = "", source: str = "sql") -> DatasetMeta:
        dataset_id = new_id("ds_")
        d = self._dir(dataset_id)
        d.mkdir(parents=True, exist_ok=False)
        df = normalize_frame(df.reset_index(drop=True))
        df.to_parquet(d / "data.parquet", index=False)
        meta = DatasetMeta(
            id=dataset_id,
            name=name,
            sql=sql,
            created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
            row_count=int(len(df)),
            columns=column_specs(df),
            truncated=truncated,
            extra=extra or {},
            description=description,
            source=source,
        )
        (d / "meta.json").write_text(json.dumps(asdict(meta), ensure_ascii=False, indent=1))
        with self._lock:
            self._cache[dataset_id] = df
            self._trim()
        return meta

    def _trim(self) -> None:
        while len(self._cache) > self._cache_size:
            self._cache.popitem(last=False)

    def meta(self, dataset_id: str) -> DatasetMeta:
        p = self._dir(dataset_id) / "meta.json"
        if not p.exists():
            raise KeyError(f"Unknown dataset id: {dataset_id}")
        return DatasetMeta(**json.loads(p.read_text()))

    def load(self, dataset_id: str) -> pd.DataFrame:
        with self._lock:
            if dataset_id in self._cache:
                self._cache.move_to_end(dataset_id)
                return self._cache[dataset_id]
        p = self._dir(dataset_id) / "data.parquet"
        if not p.exists():
            raise KeyError(f"Unknown dataset id: {dataset_id}")
        df = normalize_frame(pd.read_parquet(p))
        with self._lock:
            self._cache[dataset_id] = df
            self._trim()
        return df

    def exists(self, dataset_id: str) -> bool:
        try:
            return (self._dir(dataset_id) / "meta.json").exists()
        except KeyError:
            return False

    def list(self, limit: int = 20) -> list[DatasetMeta]:
        metas: list[DatasetMeta] = []
        for p in self.root.glob("ds_*/meta.json"):
            try:
                metas.append(DatasetMeta(**json.loads(p.read_text())))
            except Exception:
                continue
        metas.sort(key=lambda m: m.created_at, reverse=True)
        return metas[:limit]


# ---------- presentation helpers ----------


def _fmt_cell(v: Any, max_len: int = 40) -> str:
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    if isinstance(v, pd.Timestamp):
        return v.strftime("%Y-%m-%d") if v == v.normalize() else v.strftime("%Y-%m-%d %H:%M")
    if isinstance(v, float):
        return f"{v:.6g}"
    s = str(v).replace("\n", " ")
    return s if len(s) <= max_len else s[: max_len - 1] + "…"


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Make object columns JSON/parquet friendly: UUIDs and bytes become strings.

    psycopg returns UUID objects; parquet stores them as raw 16-byte blobs, and pandas' JSON writer then fails with a
    UnicodeDecodeError. Normalising on save (new datasets) and load (old datasets) fixes both directions.
    """
    import uuid

    def conv(v: Any) -> Any:
        if isinstance(v, uuid.UUID):
            return str(v)
        if isinstance(v, (bytes, bytearray, memoryview)):
            b = bytes(v)
            if len(b) == 16:
                try:
                    return str(uuid.UUID(bytes=b))
                except ValueError:
                    pass
            try:
                return b.decode("utf-8")
            except UnicodeDecodeError:
                return b.hex()
        return v

    for c in df.columns:
        s = df[c]
        if s.dtype == object:
            sample = s.dropna().head(50)
            if any(isinstance(v, (uuid.UUID, bytes, bytearray, memoryview)) for v in sample):
                df[c] = s.map(lambda v: conv(v) if v is not None else v)
    return df


def preview_table(df: pd.DataFrame, n: int = 25) -> str:
    """Compact pipe-separated preview; header line + rows. Cheap on tokens, easy to read."""
    if df.empty:
        return "(keine Zeilen)"
    cols = [str(c) for c in df.columns]
    lines = [" | ".join(cols)]
    for _, row in df.head(n).iterrows():
        lines.append(" | ".join(_fmt_cell(row[c]) for c in df.columns))
    if len(df) > n:
        lines.append(f"… {len(df) - n} weitere Zeilen")
    return "\n".join(lines)


def column_summary(df: pd.DataFrame, max_values: int = 8) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for c in df.columns:
        s = df[c]
        info: dict[str, Any] = {"column": str(c), "type": _dtype_label(s), "non_null": int(s.notna().sum())}
        if info["type"] in ("int", "number", "date"):
            non_null = s.dropna()
            if not non_null.empty:
                info["min"] = _fmt_cell(non_null.min())
                info["max"] = _fmt_cell(non_null.max())
        else:
            nun = int(s.nunique(dropna=True))
            info["distinct"] = nun
            if 0 < nun <= max_values:
                info["values"] = [_fmt_cell(v) for v in s.dropna().unique()[:max_values]]
            elif nun > max_values:
                top = s.value_counts().head(max_values)
                info["top_values"] = {_fmt_cell(k): int(v) for k, v in top.items()}
        out.append(info)
    return out
