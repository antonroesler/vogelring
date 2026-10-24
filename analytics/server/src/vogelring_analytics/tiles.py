"""Basemap tile proxy with a disk cache.

CARTO keys are referrer-restricted to the app domain, and the headless renderer has no referrer, so tiles
are fetched server-side with the app's referrer and cached. This also keeps the key out of the pages and
makes repeated renders of the same area fast on the Pi.
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from pathlib import Path

import httpx
from starlette.requests import Request
from starlette.responses import FileResponse, PlainTextResponse, Response

from .settings import settings

log = logging.getLogger(__name__)

STYLES = {
    "light": ("https://{s}.basemaps.cartocdn.com/rastertiles/light_all/{z}/{x}/{y}{r}.png", "abcd", True),
    "dark": ("https://{s}.basemaps.cartocdn.com/rastertiles/dark_all/{z}/{x}/{y}{r}.png", "abcd", True),
    "voyager": ("https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png", "abcd", True),
    "osm": ("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", "abc", False),
}
_TTL_S = 30 * 24 * 3600
_UA = "VogelringAnalytics/0.1 (+https://vogelring.com; charts renderer)"
_NAME = re.compile(r"^(\d+)(@2x)?$")

_client: httpx.AsyncClient | None = None
_locks: dict[str, asyncio.Lock] = {}


def _get_client() -> httpx.AsyncClient:
    global _client
    if _client is None:
        _client = httpx.AsyncClient(timeout=httpx.Timeout(15.0), follow_redirects=True, headers={"User-Agent": _UA})
    return _client


async def close_client() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


def _upstream(style: str, z: int, x: int, y: int, retina: bool) -> str:
    template, subdomains, supports_retina = STYLES[style]
    s = subdomains[(x + y) % len(subdomains)]
    url = template.format(s=s, z=z, x=x, y=y, r="@2x" if (retina and supports_retina) else "")
    if style != "osm" and settings.carto_key:
        url += f"?key={settings.carto_key}"
    return url


async def tile(request: Request) -> Response:
    style = request.path_params["style"]
    if style not in STYLES:
        return PlainTextResponse("unknown style", status_code=404)
    try:
        z, x = int(request.path_params["z"]), int(request.path_params["x"])
    except ValueError:
        return PlainTextResponse("bad tile", status_code=400)
    m = _NAME.match(request.path_params["y"])
    if not m or not (0 <= z <= 19):
        return PlainTextResponse("bad tile", status_code=400)
    y, retina = int(m.group(1)), bool(m.group(2))
    if not (0 <= x < 2**z and 0 <= y < 2**z):
        return PlainTextResponse("bad tile", status_code=400)

    cache_dir = settings.data_dir / "tiles" / style / str(z) / str(x)
    path = cache_dir / f"{y}{'@2x' if retina else ''}.png"
    headers = {"Cache-Control": "public, max-age=86400"}
    if path.exists() and (time.time() - path.stat().st_mtime) < _TTL_S:
        return FileResponse(path, media_type="image/png", headers=headers)

    lock = _locks.setdefault(str(path), asyncio.Lock())
    async with lock:
        if path.exists() and (time.time() - path.stat().st_mtime) < _TTL_S:
            return FileResponse(path, media_type="image/png", headers=headers)
        client = _get_client()
        url = _upstream(style, z, x, y, retina)
        req_headers = {"Referer": settings.tile_referer} if (style != "osm" and settings.tile_referer) else {}
        try:
            resp = await client.get(url, headers=req_headers)
            if resp.status_code == 403 and style != "osm" and "?key=" in url:
                # key rejected (e.g. referrer policy): fall back to the public endpoint
                resp = await client.get(url.split("?key=")[0], headers=req_headers)
        except httpx.HTTPError as exc:
            log.warning("tile fetch failed %s: %s", url.split("?")[0], exc)
            if path.exists():
                return FileResponse(path, media_type="image/png", headers=headers)
            return PlainTextResponse("upstream error", status_code=502)
        if resp.status_code != 200 or not resp.headers.get("content-type", "").startswith("image"):
            log.warning("tile upstream %s -> %s", url.split("?")[0], resp.status_code)
            return PlainTextResponse("upstream error", status_code=502)
        cache_dir.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_bytes(resp.content)
        tmp.replace(path)
    return FileResponse(path, media_type="image/png", headers=headers)


def cache_size(root: Path | None = None) -> tuple[int, int]:
    root = root or settings.data_dir / "tiles"
    n = total = 0
    for p in root.rglob("*.png"):
        n += 1
        total += p.stat().st_size
    return n, total
