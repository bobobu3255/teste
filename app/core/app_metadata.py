"""Identidade central do aplicativo.

Este arquivo evita que nome e versao fiquem espalhados pela interface,
relatorios e empacotador.
"""
from __future__ import annotations

APP_NAME = "Telegram Collector Pro"
APP_MAJOR = 12
APP_MINOR = 0
APP_STAGE = "Preview"
APP_VERSION = f"{APP_MAJOR}.{APP_MINOR}"
APP_VERSION_LABEL = f"v{APP_VERSION} {APP_STAGE}"
APP_CODENAME = "V12 Core"
APP_WINDOW_TITLE = f"{APP_NAME}  {APP_VERSION_LABEL}"
APP_TRAY_TOOLTIP = f"{APP_NAME} {APP_VERSION_LABEL}"
APP_USER_MODEL_ID = "TelegramCollector.Pro.v12.preview"
APP_STORAGE_VERSION = "v12-core"


def version_payload() -> dict:
    """Retorna a identidade do app em formato facil de gravar no estado central."""
    return {
        "name": APP_NAME,
        "major": APP_MAJOR,
        "minor": APP_MINOR,
        "stage": APP_STAGE,
        "version": APP_VERSION,
        "label": APP_VERSION_LABEL,
        "codename": APP_CODENAME,
        "storage_version": APP_STORAGE_VERSION,
    }
