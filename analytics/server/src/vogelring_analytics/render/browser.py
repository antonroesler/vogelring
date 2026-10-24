"""Headless Chromium renderer (Playwright). Screenshots the served visual page at 2x and prints a PDF."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from playwright.async_api import BrowserContext, Playwright, async_playwright

from ..settings import settings

log = logging.getLogger(__name__)


@dataclass
class RenderOutput:
    png_hi: bytes  # device pixels (2x), for download
    inline: bytes  # css pixels (1x), compact, for the chat
    inline_mime: str
    pdf: bytes


class Renderer:
    def __init__(self, base_url: str | None = None, concurrency: int = 2) -> None:
        self.base_url = base_url or f"http://127.0.0.1:{settings.port}"
        self._pw: Playwright | None = None
        self._ctx: BrowserContext | None = None
        self._sem = asyncio.Semaphore(concurrency)
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        async with self._lock:
            if self._ctx is not None:
                return
            self._pw = await async_playwright().start()
            settings.browser_cache_dir.mkdir(parents=True, exist_ok=True)
            self._ctx = await self._pw.chromium.launch_persistent_context(
                str(settings.browser_cache_dir),
                headless=True,
                device_scale_factor=2,
                viewport={"width": 1400, "height": 900},
                locale="de-DE",
                args=["--disable-gpu", "--no-sandbox", "--disable-dev-shm-usage", "--font-render-hinting=none"],
            )
            log.info("Chromium started (cache %s)", settings.browser_cache_dir)

    async def stop(self) -> None:
        async with self._lock:
            if self._ctx is not None:
                await self._ctx.close()
                self._ctx = None
            if self._pw is not None:
                await self._pw.stop()
                self._pw = None

    async def _ensure(self) -> BrowserContext:
        if self._ctx is None:
            await self.start()
        assert self._ctx is not None
        return self._ctx

    async def render_visual(self, visual_id: str, width: int, height: int, *, photographic: bool = False) -> RenderOutput:
        ctx = await self._ensure()
        url = f"{self.base_url}/viz/{visual_id}?render=1"
        timeout_ms = settings.render_timeout_s * 1000
        async with self._sem:
            page = await ctx.new_page()
            try:
                await page.set_viewport_size({"width": width, "height": height})
                await page.goto(url, wait_until="load", timeout=timeout_ms)
                try:
                    await page.wait_for_function("window.__READY__ === true", timeout=timeout_ms)
                except Exception as exc:  # tiles may hang; render what we have
                    log.warning("render %s: ready signal timed out (%s), capturing anyway", visual_id, exc)
                err = await page.evaluate("window.__ERROR__ || null")
                if err:
                    raise RuntimeError(f"Page reported error: {err}")
                stage = page.locator("#stage")
                png_hi = await stage.screenshot(type="png", scale="device", animations="disabled")
                if photographic:  # basemap tiles compress far better as JPEG; keeps the tool result well under 1 MB
                    inline = await stage.screenshot(type="jpeg", quality=82, scale="css", animations="disabled")
                    mime = "image/jpeg"
                else:
                    inline = await stage.screenshot(type="png", scale="css", animations="disabled")
                    mime = "image/png"
                if len(inline) > 600_000:
                    inline = await stage.screenshot(type="jpeg", quality=65, scale="css", animations="disabled")
                    mime = "image/jpeg"
                pdf = await page.pdf(width=f"{width}px", height=f"{height}px", print_background=True, margin={"top": "0", "right": "0", "bottom": "0", "left": "0"})
                return RenderOutput(png_hi=png_hi, inline=inline, inline_mime=mime, pdf=pdf)
            finally:
                await page.close()

    async def render_pdf(self, path: str, *, title: str = "") -> bytes:
        """Print a served page (e.g. a report) as an A4 PDF with page numbers."""
        ctx = await self._ensure()
        url = f"{self.base_url}{path}"
        timeout_ms = settings.render_timeout_s * 1000
        async with self._sem:
            page = await ctx.new_page()
            try:
                await page.set_viewport_size({"width": 900, "height": 1200})
                await page.goto(url, wait_until="load", timeout=timeout_ms)
                try:
                    await page.wait_for_function("window.__READY__ === true", timeout=timeout_ms)
                except Exception as exc:
                    log.warning("pdf %s: ready signal timed out (%s)", path, exc)
                await page.emulate_media(media="print")
                safe_title = (title or "").replace("<", "").replace(">", "")[:90]
                footer = (
                    '<div style="font-family:Inter,Arial,sans-serif;font-size:8.5px;color:#777;width:100%;padding:0 14mm;display:flex;justify-content:space-between">'
                    f'<span>{safe_title}</span><span>Seite <span class="pageNumber"></span> von <span class="totalPages"></span></span></div>'
                )
                return await page.pdf(
                    format="A4", print_background=True, prefer_css_page_size=False,
                    margin={"top": "16mm", "right": "16mm", "bottom": "18mm", "left": "16mm"},
                    display_header_footer=True, header_template="<span></span>", footer_template=footer,
                )
            finally:
                await page.close()
