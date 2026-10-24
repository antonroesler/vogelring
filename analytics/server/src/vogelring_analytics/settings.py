"""Runtime configuration from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    return int(raw) if raw else default


@dataclass(frozen=True)
class Settings:
    database_url: str = field(default_factory=lambda: os.environ.get("DATABASE_URL", ""))
    # Separate, restricted role for the gated write path (empty = writes disabled).
    write_database_url: str = field(default_factory=lambda: os.environ.get("WRITE_DATABASE_URL", ""))
    write_org_id: str = field(default_factory=lambda: os.environ.get("WRITE_ORG_ID", "").strip())
    write_max_rows: int = field(default_factory=lambda: _env_int("WRITE_MAX_ROWS", 2000))
    write_proposal_ttl_min: int = field(default_factory=lambda: _env_int("WRITE_PROPOSAL_TTL_MIN", 240))
    data_dir: Path = field(default_factory=lambda: Path(os.environ.get("DATA_DIR", "/data")))
    public_base_url: str = field(
        default_factory=lambda: os.environ.get("PUBLIC_BASE_URL", "https://charts.vogelring.com").rstrip("/")
    )
    carto_key: str = field(default_factory=lambda: os.environ.get("CARTO_BASEMAP_KEY", "").strip())
    tile_referer: str = field(default_factory=lambda: os.environ.get("TILE_REFERER", "https://vogelring.com/"))
    port: int = field(default_factory=lambda: _env_int("PORT", 8000))
    chat_url: str = field(default_factory=lambda: os.environ.get("CHAT_URL", "https://chat.vogelring.com").rstrip("/"))
    chat_agent_id: str = field(default_factory=lambda: os.environ.get("CHAT_AGENT_ID", "agent_jhKSvfDXizwVf0IHVWwjY"))
    web_dir: Path | None = field(default_factory=lambda: Path(os.environ["WEB_DIR"]) if os.environ.get("WEB_DIR") else None)
    max_rows: int = field(default_factory=lambda: _env_int("MAX_ROWS", 50_000))
    statement_timeout_ms: int = field(default_factory=lambda: _env_int("STATEMENT_TIMEOUT_MS", 30_000))
    render_timeout_s: int = field(default_factory=lambda: _env_int("RENDER_TIMEOUT_S", 60))
    retention_days: int = field(default_factory=lambda: _env_int("RETENTION_DAYS", 180))
    browser_cache_dir: Path = field(
        default_factory=lambda: Path(os.environ.get("BROWSER_CACHE_DIR", "/data/browser-cache"))
    )
    # Hostnames the MCP transport accepts (DNS-rebinding protection).
    allowed_hosts: tuple[str, ...] = field(
        default_factory=lambda: tuple(
            h.strip()
            for h in os.environ.get("MCP_ALLOWED_HOSTS", "analytics-mcp,analytics-mcp:*,localhost,localhost:*,127.0.0.1,127.0.0.1:*").split(",")
            if h.strip()
        )
    )

    @property
    def datasets_dir(self) -> Path:
        return self.data_dir / "datasets"

    @property
    def visuals_dir(self) -> Path:
        return self.data_dir / "viz"

    @property
    def exports_dir(self) -> Path:
        return self.data_dir / "exports"

    @property
    def reports_dir(self) -> Path:
        return self.data_dir / "reports"

    @property
    def decks_dir(self) -> Path:
        return self.data_dir / "decks"

    def ensure_dirs(self) -> None:
        for d in (self.datasets_dir, self.visuals_dir, self.exports_dir, self.reports_dir, self.decks_dir, self.browser_cache_dir):
            d.mkdir(parents=True, exist_ok=True)


settings = Settings()
