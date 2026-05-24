#!/usr/bin/env python3
"""Valida o estado central, eventos e fila SQLite."""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.app_store import AppStore, TASK_ERROR, TASK_PENDING, TASK_SUCCESS


def main() -> int:
    with tempfile.TemporaryDirectory(prefix="v12_app_store_") as tmp:
        store = AppStore(Path(tmp) / "app_state.sqlite3")

        store.set_state("check.value", {"ok": True, "count": 1})
        state = store.get_state("check.value")
        if not state or state.get("ok") is not True:
            print("[app-store] Falha ao gravar estado.")
            return 1

        event_id = store.add_event(
            "maintenance",
            "check_started",
            "Teste do estado central",
            payload={"source": "app_store_check"},
        )
        if event_id <= 0:
            print("[app-store] Falha ao registrar evento.")
            return 1

        task_id = store.create_task(
            "self-test",
            "Validar fila central",
            source="maintenance",
            status=TASK_PENDING,
        )
        store.update_task(task_id, status=TASK_SUCCESS)
        error_task_id = store.create_task(
            "self-test-error",
            "Validar contador de erro",
            source="maintenance",
            status=TASK_ERROR,
        )
        store.update_task(error_task_id, last_error="erro simulado")
        stable_id = store.upsert_task(
            "stable-task",
            "self-test",
            "Tarefa estavel",
            source="maintenance",
            status=TASK_PENDING,
            payload={"step": 1},
        )
        store.upsert_task(
            stable_id,
            "self-test",
            "Tarefa estavel atualizada",
            source="maintenance",
            status=TASK_SUCCESS,
            payload={"step": 2},
        )
        entity_id = store.upsert_entity(
            "entity-check",
            "maintenance_item",
            "Entidade de teste",
            source="maintenance",
            status="active",
            payload={"ok": True},
        )
        store.upsert_entity(
            entity_id,
            "maintenance_item",
            "Entidade de teste atualizada",
            source="maintenance",
            status="synced",
            payload={"ok": True, "updated": True},
        )

        counts = store.task_counts()
        if counts.get(TASK_SUCCESS) != 2 or counts.get(TASK_ERROR) != 1:
            print(f"[app-store] Contadores inesperados: {counts}")
            return 1
        entity_counts = store.entity_counts()
        if entity_counts.get("maintenance_item") != 1:
            print(f"[app-store] Entidades inesperadas: {entity_counts}")
            return 1

        if not store.list_events(source="maintenance", limit=5):
            print("[app-store] Lista de eventos vazia.")
            return 1

    print("[app-store] Estado central, eventos e fila OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
