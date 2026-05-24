#!/usr/bin/env python3
"""Infraestrutura simples para integrar o app com um cPanel/domino proprio."""

from __future__ import annotations

import json
import platform
import socket
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from app.core.app_metadata import APP_NAME, APP_VERSION
from app.core.paths import BASE_DIR, CONFIG_DIR


CLOUD_SETTINGS_FILE = CONFIG_DIR / "cloud_settings.json"
USER_AGENT = "TelegramCollectorPro-V12"

DEFAULT_CLOUD_SETTINGS = {
    "enabled": False,
    "base_url": "https://bobobu.com.br/v11",
    "api_key": "",
    "send_logs": False,
    "check_updates": True,
    "sync_ai_catalog": True,
}


def load_cloud_settings() -> dict[str, Any]:
    data = DEFAULT_CLOUD_SETTINGS.copy()
    try:
        if CLOUD_SETTINGS_FILE.exists():
            loaded = json.loads(CLOUD_SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
    except Exception:
        pass
    return data


def save_cloud_settings(data: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    merged = DEFAULT_CLOUD_SETTINGS.copy()
    merged.update(data or {})
    CLOUD_SETTINGS_FILE.write_text(json.dumps(merged, indent=2, ensure_ascii=False), encoding="utf-8")


class CloudService:
    """Cliente pequeno para endpoints estaticos/PHP hospedados em cPanel."""

    def __init__(self, settings: dict[str, Any] | None = None):
        self.settings = settings or load_cloud_settings()
        self.base_url = str(self.settings.get("base_url") or "").rstrip("/")
        self.api_key = str(self.settings.get("api_key") or "")

    @property
    def enabled(self) -> bool:
        return bool(self.settings.get("enabled")) and bool(self.base_url)

    def _url(self, path: str) -> str:
        return f"{self.base_url}/{path.lstrip('/')}"

    def fetch_json(self, path: str, timeout: int = 12) -> dict[str, Any] | list[Any]:
        if not self.base_url:
            raise RuntimeError("URL da nuvem nao configurada.")
        req = urllib.request.Request(
            self._url(path),
            headers={
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
            },
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
        return json.loads(raw)

    def get_version(self) -> dict[str, Any]:
        data = self.fetch_json("version.json")
        return data if isinstance(data, dict) else {}

    def get_ai_models(self) -> list[dict[str, Any]]:
        data = self.fetch_json("ai_models.json")
        return data if isinstance(data, list) else []

    def get_prompts(self) -> dict[str, Any]:
        data = self.fetch_json("prompts.json")
        return data if isinstance(data, dict) else {}

    def send_log(self, tool: str, level: str, message: str, details: dict[str, Any] | None = None) -> bool:
        if not self.enabled or not self.settings.get("send_logs"):
            return False
        payload = {
            "app": APP_NAME,
            "version": APP_VERSION,
            "tool": str(tool)[:80],
            "level": str(level)[:20],
            "message": str(message)[:2000],
            "details": details or {},
            "machine": socket.gethostname(),
            "system": platform.platform(),
            "created_at": datetime.now().isoformat(timespec="seconds"),
        }
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self._url("api/log.php"),
            data=body,
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
                "User-Agent": USER_AGENT,
                "X-App-Key": self.api_key,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            response = json.loads(resp.read().decode("utf-8", errors="replace") or "{}")
        return bool(response.get("ok"))

    def diagnose(self) -> dict[str, Any]:
        result: dict[str, Any] = {
            "enabled": self.enabled,
            "base_url": self.base_url,
            "version_ok": False,
            "models_ok": False,
            "prompts_ok": False,
            "errors": [],
        }
        checks = [
            ("version_ok", self.get_version),
            ("models_ok", self.get_ai_models),
            ("prompts_ok", self.get_prompts),
        ]
        for key, fn in checks:
            try:
                fn()
                result[key] = True
            except (urllib.error.URLError, TimeoutError, OSError, ValueError, RuntimeError) as exc:
                result["errors"].append(f"{key}: {exc}")
        return result
