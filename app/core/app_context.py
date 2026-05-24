#!/usr/bin/env python3
"""Acesso singleton ao estado central do app."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.core.app_metadata import version_payload
from app.core.app_store import AppStore


_store: AppStore | None = None
_context: "AppContext | None" = None


def get_app_store() -> AppStore:
    global _store
    if _store is None:
        _store = AppStore()
    return _store


@dataclass
class AppContext:
    store: AppStore

    def __post_init__(self) -> None:
        try:
            self.store.set_state("app.version", version_payload())
        except Exception:
            pass

    def remember(self, key: str, value: Any) -> None:
        self.store.set_state(key, value)

    def recall(self, key: str, default: Any = None) -> Any:
        return self.store.get_state(key, default)

    def emit(
        self,
        source: str,
        event: str,
        message: str = "",
        *,
        level: str = "info",
        entity_type: str = "",
        entity_id: str = "",
        payload: Any = None,
    ) -> int:
        return self.store.add_event(
            source,
            event,
            message,
            level=level,
            entity_type=entity_type,
            entity_id=entity_id,
            payload=payload,
        )


def get_app_context() -> AppContext:
    global _context
    if _context is None:
        _context = AppContext(store=get_app_store())
    return _context
