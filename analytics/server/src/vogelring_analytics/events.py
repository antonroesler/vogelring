"""In-process event bus: every store change is published so the web app can mirror the agent live (SSE)."""

from __future__ import annotations

import asyncio
import json
import logging
import threading
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class Event:
    type: str  # e.g. "visual.created", "view.updated", "navigate", "log"
    title: str  # plain German one-liner for the activity log
    payload: dict[str, Any] = field(default_factory=dict)
    at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds"))
    seq: int = 0

    def sse(self) -> str:
        data = json.dumps({"seq": self.seq, "type": self.type, "title": self.title, "at": self.at, **self.payload}, ensure_ascii=False, default=str)
        return f"id: {self.seq}\nevent: {self.type}\ndata: {data}\n\n"


class EventBus:
    """Thread-safe publish from sync store code; async subscribers get an asyncio.Queue."""

    def __init__(self, history: int = 300) -> None:
        self._subs: set[asyncio.Queue[Event]] = set()
        self._history: deque[Event] = deque(maxlen=history)
        self._lock = threading.Lock()
        self._seq = 0
        self._loop: asyncio.AbstractEventLoop | None = None
        self._persist = None  # optional callable(Event) → persists to the catalog activity log

    def bind(self, loop: asyncio.AbstractEventLoop, persist=None) -> None:
        self._loop = loop
        self._persist = persist

    def publish(self, type: str, title: str, **payload: Any) -> Event:
        with self._lock:
            self._seq += 1
            ev = Event(type=type, title=title, payload=payload, seq=self._seq)
            self._history.append(ev)
            subs = list(self._subs)
        if self._persist:
            try:
                self._persist(ev)
            except Exception:
                log.exception("persisting event failed")
        loop = self._loop
        if loop is None:
            return ev
        for q in subs:
            try:
                if loop.is_running():
                    loop.call_soon_threadsafe(q.put_nowait, ev)
            except RuntimeError:
                pass
        return ev

    def subscribe(self) -> asyncio.Queue[Event]:
        q: asyncio.Queue[Event] = asyncio.Queue(maxsize=500)
        with self._lock:
            self._subs.add(q)
        return q

    def unsubscribe(self, q: asyncio.Queue[Event]) -> None:
        with self._lock:
            self._subs.discard(q)

    def since(self, seq: int) -> list[Event]:
        with self._lock:
            return [e for e in self._history if e.seq > seq]

    def recent(self, n: int = 50) -> list[Event]:
        with self._lock:
            return list(self._history)[-n:]


bus = EventBus()
