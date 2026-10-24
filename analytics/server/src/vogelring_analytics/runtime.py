"""Process-wide singletons shared by the MCP tools and the HTTP routes."""

from __future__ import annotations

from functools import lru_cache

from .catalog import Catalog
from .datasets import DatasetStore
from .decks import DeckStore
from .definitions import DefinitionStore
from .db import Database
from .render.browser import Renderer
from .reports import ReportStore
from .settings import settings
from .visuals import VisualStore


@lru_cache(maxsize=1)
def datasets() -> DatasetStore:
    settings.ensure_dirs()
    return DatasetStore()


@lru_cache(maxsize=1)
def visuals() -> VisualStore:
    settings.ensure_dirs()
    return VisualStore()


@lru_cache(maxsize=1)
def renderer() -> Renderer:
    return Renderer()


@lru_cache(maxsize=1)
def database() -> Database:
    return Database(settings.database_url)


@lru_cache(maxsize=1)
def definitions() -> DefinitionStore:
    settings.ensure_dirs()
    return DefinitionStore()


@lru_cache(maxsize=1)
def reports() -> ReportStore:
    settings.ensure_dirs()
    return ReportStore()


@lru_cache(maxsize=1)
def catalog() -> Catalog:
    settings.ensure_dirs()
    return Catalog()


@lru_cache(maxsize=1)
def decks() -> DeckStore:
    settings.ensure_dirs()
    return DeckStore()
