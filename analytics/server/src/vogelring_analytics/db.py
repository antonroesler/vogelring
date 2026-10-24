"""Read-only database access with a SQL guard, statement timeout and row cap."""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any

import pandas as pd
from psycopg import sql as _sql
from psycopg_pool import AsyncConnectionPool

from .settings import settings

_FORBIDDEN = re.compile(
    r"\b(insert|update|delete|drop|alter|create|truncate|grant|revoke|copy|vacuum|analyze|"
    r"lock|listen|notify|refresh|reindex|cluster|call|do|set|reset|show|begin|commit|rollback|"
    r"savepoint|prepare|execute|deallocate|pg_sleep|pg_read_file|pg_ls_dir|lo_import|lo_export|dblink)\b",
    re.IGNORECASE,
)
_FORBIDDEN_TABLES = re.compile(r"\b(users|organizations|sighting_exports|sighting_export_items|pg_catalog\.\w+|information_schema\.\w+)\b", re.IGNORECASE)


class SqlRejected(ValueError):
    """Raised when a statement is not a plain read-only SELECT."""


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.DOTALL)
    sql = re.sub(r"--[^\n]*", " ", sql)
    return sql


def _strip_literals(sql: str) -> str:
    """Remove string literals so keywords inside quotes don't trigger the guard."""
    return re.sub(r"'(?:[^']|'')*'", "''", sql)


def guard_sql(sql: str) -> str:
    """Validate that `sql` is a single SELECT/WITH statement and return it normalised."""
    if not sql or not sql.strip():
        raise SqlRejected("Empty SQL.")
    cleaned = _strip_comments(sql).strip().rstrip(";").strip()
    bare = _strip_literals(cleaned)
    if ";" in bare:
        raise SqlRejected("Only a single statement is allowed (no ';').")
    head = cleaned.lstrip("(").split(None, 1)[0].lower() if cleaned else ""
    if head not in {"select", "with", "values", "table"}:
        raise SqlRejected("Only read-only SELECT / WITH queries are allowed.")
    if m := _FORBIDDEN.search(bare):
        raise SqlRejected(f"Keyword '{m.group(0)}' is not allowed in read-only queries.")
    if m := _FORBIDDEN_TABLES.search(bare):
        raise SqlRejected(f"Access to '{m.group(0)}' is not permitted. Use v_sightings, ringings, color_rings or the bird_* views.")
    return cleaned


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[tuple[Any, ...]]
    truncated: bool

    def to_frame(self) -> pd.DataFrame:
        df = pd.DataFrame.from_records(self.rows, columns=self.columns)
        return coerce_frame(df)


def coerce_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise DB types into pandas-friendly ones (Decimal -> float, date -> datetime64)."""
    for col in df.columns:
        s = df[col]
        if s.dtype != object:
            continue
        sample = s.dropna()
        if sample.empty:
            continue
        first = sample.iloc[0]
        if isinstance(first, Decimal):
            df[col] = pd.to_numeric(s.map(lambda v: float(v) if isinstance(v, Decimal) else v), errors="coerce")
        elif isinstance(first, (datetime, date)):
            df[col] = pd.to_datetime(s, errors="coerce")
    return df


class Database:
    def __init__(self, dsn: str) -> None:
        if not dsn:
            raise RuntimeError("DATABASE_URL is not configured")
        self._pool = AsyncConnectionPool(
            dsn, min_size=1, max_size=4, open=False, kwargs={"autocommit": False},
            check=AsyncConnectionPool.check_connection,  # drop connections killed by a Postgres restart instead of failing one request
            max_idle=300,
        )

    async def open(self) -> None:
        await self._pool.open()

    async def close(self) -> None:
        await self._pool.close()

    async def query(self, raw_sql: str, *, max_rows: int | None = None, params: tuple | list | None = None) -> QueryResult:
        statement = guard_sql(raw_sql)
        limit = max_rows or settings.max_rows
        async with self._pool.connection() as conn:
            await conn.set_read_only(True)
            async with conn.transaction():
                await conn.execute(
                    _sql.SQL("SET LOCAL statement_timeout = {}").format(_sql.Literal(settings.statement_timeout_ms))
                )
                async with conn.cursor() as cur:
                    await cur.execute(statement, params)  # type: ignore[arg-type]
                    if cur.description is None:
                        return QueryResult(columns=[], rows=[], truncated=False)
                    columns = [d.name for d in cur.description]
                    rows = await cur.fetchmany(limit + 1)
        truncated = len(rows) > limit
        return QueryResult(columns=columns, rows=rows[:limit], truncated=truncated)

    async def ping(self) -> bool:
        async with self._pool.connection() as conn:
            await conn.execute("SELECT 1")
        return True
