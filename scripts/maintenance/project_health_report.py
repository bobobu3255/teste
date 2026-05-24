#!/usr/bin/env python3
"""Relatorio unico de saude do app baseado no estado central."""
from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.app_metadata import APP_CODENAME, APP_VERSION_LABEL
from app.core.app_store import AppStore
from app.core.paths import BASE_DIR, CONFIG_DIR


def load_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def count_items(path: Path, *keys: str) -> int:
    data = load_json(path, {})
    if isinstance(data, list):
        return len(data)
    if isinstance(data, dict):
        for key in keys or ("items",):
            value = data.get(key)
            if isinstance(value, list):
                return len(value)
    return 0


def main() -> int:
    store = AppStore()
    browser_summary = store.get_state("browser.summary", {})
    paramount_summary = store.get_state("paramount_assist.summary", {})
    app_settings = store.get_state("app.settings", {})
    task_counts = store.task_counts()
    entity_counts = store.entity_counts()
    errors = store.list_events(level="error", limit=8)

    print(f"Saude geral - {APP_CODENAME}")
    print("========================")
    print(f"Versao: {APP_VERSION_LABEL}")
    print(f"Projeto: {BASE_DIR}")
    print(f"SQLite central: {store.db_path}")
    print()
    print("Resumo")
    print("------")
    print(f"Perfis navegador: {browser_summary.get('profiles', count_items(BASE_DIR / 'browser_profiles' / 'profiles.json', 'profiles'))}")
    print(f"Perfis arquivados: {browser_summary.get('archived', 0)}")
    print(f"Contas Paramount: {paramount_summary.get('accounts', count_items(CONFIG_DIR / 'paramount_assist.json', 'accounts'))}")
    print(f"Assinaturas ativas marcadas: {paramount_summary.get('active', 0)}")
    print(f"Workspace: {app_settings.get('workspace', 'Padrao')}")
    print()
    print("Entidades centrais")
    print("------------------")
    for kind in ("browser_profile", "paramount_account", "favorite", "backup", "browser_account"):
        print(f"{kind}: {entity_counts.get(kind, 0)}")
    print()
    print("Fila")
    print("----")
    for status in ("pending", "running", "review", "error", "success", "cancelled"):
        print(f"{status}: {task_counts.get(status, 0)}")
    print()
    print("Erros recentes")
    print("--------------")
    if not errors:
        print("Nenhum erro central recente.")
    for event in errors:
        print(f"- {event.get('source')}/{event.get('event')}: {event.get('message')}")
    print()
    print("Checks recomendados")
    print("-------------------")
    print("python scripts\\maintenance\\verify_all.py --quick")
    print("python scripts\\maintenance\\app_store_maintenance.py --backup --snapshot")
    print("python scripts\\maintenance\\storage_report.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
