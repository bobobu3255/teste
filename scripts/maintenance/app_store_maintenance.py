#!/usr/bin/env python3
"""Manutencao segura do SQLite central do app.

Nao apaga dados por padrao. Mostra resumo e pode criar backup do banco central.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sqlite3
import sys
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.app_metadata import APP_CODENAME, APP_VERSION_LABEL
from app.core.app_store import AppStore
from app.core.paths import APP_DATA_DIR, BACKUP_DIR


def human_size(value: int) -> str:
    units = ("B", "KB", "MB", "GB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{int(size)} {unit}" if unit == "B" else f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def table_count(db_path: Path, table: str) -> int:
    try:
        with sqlite3.connect(str(db_path)) as conn:
            row = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            return int(row[0] if row else 0)
    except Exception:
        return 0


def create_backup(db_path: Path) -> Path:
    backup_dir = BACKUP_DIR / "app_state"
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = backup_dir / f"app_state_{stamp}.sqlite3"
    shutil.copy2(db_path, target)
    return target


def create_snapshot(store: AppStore) -> Path:
    snapshot_dir = BACKUP_DIR / "app_state"
    snapshot_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    target = snapshot_dir / f"app_state_snapshot_{stamp}.json"
    payload = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "db_path": str(store.db_path),
        "task_counts": store.task_counts(),
        "entity_counts": store.entity_counts(),
        "recent_tasks": store.list_tasks(limit=80),
        "recent_entities": store.list_entities(limit=120),
        "recent_events": store.list_events(limit=120),
        "health": store.health_summary(),
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description=f"Resumo e backup do SQLite central do {APP_CODENAME}.")
    parser.add_argument("--backup", action="store_true", help="Cria backup seguro do app_state.sqlite3.")
    parser.add_argument("--snapshot", action="store_true", help="Exporta resumo legivel em JSON.")
    args = parser.parse_args()

    store = AppStore()
    db_path = store.db_path
    size = db_path.stat().st_size if db_path.exists() else 0

    print(f"{APP_CODENAME} ({APP_VERSION_LABEL})")
    print(f"Banco central: {db_path}")
    print(f"Tamanho: {human_size(size)}")
    print(f"Estado: {table_count(db_path, 'app_state')} itens")
    print(f"Eventos: {table_count(db_path, 'app_events')} registros")
    print(f"Tarefas: {table_count(db_path, 'app_tasks')} registros")
    print(f"Entidades: {table_count(db_path, 'app_entities')} registros")
    print(f"Contadores de fila: {store.task_counts()}")
    print(f"Contadores de entidades: {store.entity_counts()}")

    recent_errors = store.list_events(level="error", limit=5)
    if recent_errors:
        print()
        print("Erros recentes:")
        for event in recent_errors:
            print(f"- {event.get('source')}/{event.get('event')}: {event.get('message')}")

    if args.backup:
        target = create_backup(db_path)
        print()
        print(f"Backup criado: {target}")

    if args.snapshot:
        target = create_snapshot(store)
        print()
        print(f"Snapshot criado: {target}")

    APP_DATA_DIR.mkdir(parents=True, exist_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
