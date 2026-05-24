"""Servicos centrais compartilhados do V12 Core."""

from app.core.app_context import AppContext, get_app_context, get_app_store
from app.core.app_metadata import APP_NAME, APP_VERSION_LABEL, version_payload
from app.core.app_store import AppStore

__all__ = [
    "APP_NAME",
    "APP_VERSION_LABEL",
    "AppContext",
    "AppStore",
    "get_app_context",
    "get_app_store",
    "version_payload",
]
