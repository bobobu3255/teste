#!/usr/bin/env python3
"""Estado central leve para o app.

Este modulo nao substitui os JSONs atuais de uma vez. Ele cria uma camada
segura para registrar eventos, status e tarefas em fila, permitindo migracoes
graduais sem quebrar ferramentas que ja funcionam.
"""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from threading import RLock
from typing import Any, Dict, Iterable, List, Optional
from uuid import uuid4

from app.core.paths import APP_DATA_DIR


TASK_PENDING = "pending"
TASK_RUNNING = "running"
TASK_SUCCESS = "success"
TASK_ERROR = "error"
TASK_REVIEW = "review"
TASK_CANCELLED = "cancelled"

TASK_STATUSES = {
    TASK_PENDING,
    TASK_RUNNING,
    TASK_SUCCESS,
    TASK_ERROR,
    TASK_REVIEW,
    TASK_CANCELLED,
}


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _to_json(value: Any) -> str:
    return json.dumps(value if value is not None else {}, ensure_ascii=False, sort_keys=True)


def _from_json(raw: str | None, default: Any = None) -> Any:
    if not raw:
        return {} if default is None else default
    try:
        return json.loads(raw)
    except (TypeError, json.JSONDecodeError):
        return {} if default is None else default


class AppStore:
    """SQLite central para estado, eventos e fila de tarefas.

    O foco aqui e previsibilidade: uma conexao por operacao, WAL habilitado e
    metodos pequenos que ferramentas podem chamar sem depender umas das outras.
    """

    SCHEMA_VERSION = 1

    def __init__(self, db_path: str | Path | None = None):
        self.db_path = Path(db_path) if db_path else APP_DATA_DIR / "app_state.sqlite3"
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        self._init_db()

    @contextmanager
    def connect(self):
        conn = sqlite3.connect(str(self.db_path), timeout=15, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        try:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA foreign_keys=ON")
            conn.execute("PRAGMA temp_store=MEMORY")
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def _init_db(self) -> None:
        with self._lock, self.connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS app_schema (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS app_state (
                    key TEXT PRIMARY KEY,
                    value_json TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS app_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    level TEXT NOT NULL,
                    event TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id TEXT,
                    message TEXT,
                    payload_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS app_tasks (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    source TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    entity_type TEXT,
                    entity_id TEXT,
                    priority INTEGER NOT NULL DEFAULT 100,
                    attempts INTEGER NOT NULL DEFAULT 0,
                    last_error TEXT,
                    payload_json TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS app_entities (
                    id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    entity_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    title TEXT NOT NULL,
                    status TEXT NOT NULL,
                    summary TEXT,
                    payload_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_app_events_source_time
                    ON app_events(source, created_at);
                CREATE INDEX IF NOT EXISTS idx_app_events_level_time
                    ON app_events(level, created_at);
                CREATE INDEX IF NOT EXISTS idx_app_tasks_status_priority
                    ON app_tasks(status, priority, created_at);
                CREATE INDEX IF NOT EXISTS idx_app_tasks_entity
                    ON app_tasks(entity_type, entity_id);
                CREATE INDEX IF NOT EXISTS idx_app_entities_type_status
                    ON app_entities(entity_type, status);
                CREATE INDEX IF NOT EXISTS idx_app_entities_source_time
                    ON app_entities(source, updated_at);
                """
            )
            conn.execute(
                "INSERT OR IGNORE INTO app_schema (version, applied_at) VALUES (?, ?)",
                (self.SCHEMA_VERSION, _now()),
            )

    def set_state(self, key: str, value: Any) -> None:
        with self._lock, self.connect() as conn:
            conn.execute(
                """
                INSERT INTO app_state (key, value_json, updated_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value_json = excluded.value_json,
                    updated_at = excluded.updated_at
                """,
                (key, _to_json(value), _now()),
            )

    def get_state(self, key: str, default: Any = None) -> Any:
        with self._lock, self.connect() as conn:
            row = conn.execute("SELECT value_json FROM app_state WHERE key = ?", (key,)).fetchone()
        if not row:
            return default
        return _from_json(row["value_json"], default)

    def add_event(
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
        with self._lock, self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO app_events
                    (created_at, source, level, event, entity_type, entity_id, message, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    _now(),
                    source or "app",
                    level or "info",
                    event or "event",
                    entity_type,
                    entity_id,
                    message,
                    _to_json(payload),
                ),
            )
            return int(cursor.lastrowid)

    def list_events(
        self,
        *,
        limit: int = 100,
        source: str | None = None,
        level: str | None = None,
    ) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit or 100), 1000))
        where: list[str] = []
        params: list[Any] = []
        if source:
            where.append("source = ?")
            params.append(source)
        if level:
            where.append("level = ?")
            params.append(level)
        sql = "SELECT * FROM app_events"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        with self._lock, self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_event(row) for row in rows]

    def create_task(
        self,
        kind: str,
        title: str,
        *,
        source: str = "app",
        status: str = TASK_PENDING,
        entity_type: str = "",
        entity_id: str = "",
        priority: int = 100,
        payload: Any = None,
        task_id: str | None = None,
    ) -> str:
        if status not in TASK_STATUSES:
            status = TASK_PENDING
        task_id = task_id or uuid4().hex
        now = _now()
        with self._lock, self.connect() as conn:
            conn.execute(
                """
                INSERT INTO app_tasks
                    (id, created_at, updated_at, source, kind, title, status,
                     entity_type, entity_id, priority, attempts, last_error, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, '', ?)
                """,
                (
                    task_id,
                    now,
                    now,
                    source or "app",
                    kind or "task",
                    title or kind or "Tarefa",
                    status,
                    entity_type,
                    entity_id,
                    int(priority),
                    _to_json(payload),
                ),
            )
        return task_id

    def upsert_task(
        self,
        task_id: str,
        kind: str,
        title: str,
        *,
        source: str = "app",
        status: str = TASK_PENDING,
        entity_type: str = "",
        entity_id: str = "",
        priority: int = 100,
        payload: Any = None,
        last_error: str = "",
    ) -> str:
        """Cria ou atualiza uma tarefa mantendo um id estavel.

        Use este metodo quando uma ferramenta ja tem uma entidade propria, como
        conta, perfil ou card. Assim o painel central nao duplica tarefas a cada
        salvamento.
        """
        if status not in TASK_STATUSES:
            status = TASK_REVIEW
        task_id = task_id or uuid4().hex
        now = _now()
        with self._lock, self.connect() as conn:
            conn.execute(
                """
                INSERT INTO app_tasks
                    (id, created_at, updated_at, source, kind, title, status,
                     entity_type, entity_id, priority, attempts, last_error, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    source = excluded.source,
                    kind = excluded.kind,
                    title = excluded.title,
                    status = excluded.status,
                    entity_type = excluded.entity_type,
                    entity_id = excluded.entity_id,
                    priority = excluded.priority,
                    last_error = excluded.last_error,
                    payload_json = excluded.payload_json
                """,
                (
                    task_id,
                    now,
                    now,
                    source or "app",
                    kind or "task",
                    title or kind or "Tarefa",
                    status,
                    entity_type,
                    entity_id,
                    int(priority),
                    last_error or "",
                    _to_json(payload),
                ),
            )
        return task_id

    def update_task(
        self,
        task_id: str,
        *,
        status: str | None = None,
        last_error: str | None = None,
        payload: Any = None,
        attempts_delta: int = 0,
    ) -> None:
        fields = ["updated_at = ?"]
        params: list[Any] = [_now()]
        if status:
            fields.append("status = ?")
            params.append(status if status in TASK_STATUSES else TASK_REVIEW)
        if last_error is not None:
            fields.append("last_error = ?")
            params.append(last_error)
        if payload is not None:
            fields.append("payload_json = ?")
            params.append(_to_json(payload))
        if attempts_delta:
            fields.append("attempts = attempts + ?")
            params.append(int(attempts_delta))
        params.append(task_id)
        with self._lock, self.connect() as conn:
            conn.execute(f"UPDATE app_tasks SET {', '.join(fields)} WHERE id = ?", params)

    def upsert_entity(
        self,
        entity_id: str,
        entity_type: str,
        title: str,
        *,
        source: str = "app",
        status: str = "active",
        summary: str = "",
        payload: Any = None,
    ) -> str:
        """Cria ou atualiza uma entidade central.

        Entidade e qualquer coisa importante do app: perfil, conta, favorito,
        backup, configuracao, extensao ou arquivo. O id deve ser estavel para
        evitar duplicacao.
        """
        entity_id = entity_id or uuid4().hex
        now = _now()
        with self._lock, self.connect() as conn:
            conn.execute(
                """
                INSERT INTO app_entities
                    (id, created_at, updated_at, entity_type, source, title, status, summary, payload_json)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    updated_at = excluded.updated_at,
                    entity_type = excluded.entity_type,
                    source = excluded.source,
                    title = excluded.title,
                    status = excluded.status,
                    summary = excluded.summary,
                    payload_json = excluded.payload_json
                """,
                (
                    entity_id,
                    now,
                    now,
                    entity_type or "item",
                    source or "app",
                    title or entity_id,
                    status or "active",
                    summary or "",
                    _to_json(payload),
                ),
            )
        return entity_id

    def list_entities(
        self,
        *,
        entity_type: str | Iterable[str] | None = None,
        status: str | Iterable[str] | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit or 100), 2000))
        where: list[str] = []
        params: list[Any] = []
        if entity_type:
            types = [entity_type] if isinstance(entity_type, str) else list(entity_type)
            if types:
                where.append("entity_type IN (" + ",".join("?" for _ in types) + ")")
                params.extend(types)
        if status:
            statuses = [status] if isinstance(status, str) else list(status)
            if statuses:
                where.append("status IN (" + ",".join("?" for _ in statuses) + ")")
                params.extend(statuses)
        if source:
            where.append("source = ?")
            params.append(source)
        sql = "SELECT * FROM app_entities"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY updated_at DESC LIMIT ?"
        params.append(limit)
        with self._lock, self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_entity(row) for row in rows]

    def entity_counts(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        with self._lock, self.connect() as conn:
            rows = conn.execute("SELECT entity_type, COUNT(*) AS total FROM app_entities GROUP BY entity_type").fetchall()
        for row in rows:
            counts[str(row["entity_type"])] = int(row["total"])
        return counts

    def delete_entities_by_source(self, source: str, entity_type: str | None = None) -> int:
        if not source:
            return 0
        sql = "DELETE FROM app_entities WHERE source = ?"
        params: list[Any] = [source]
        if entity_type:
            sql += " AND entity_type = ?"
            params.append(entity_type)
        with self._lock, self.connect() as conn:
            cursor = conn.execute(sql, params)
            return int(cursor.rowcount if cursor.rowcount is not None else 0)

    def list_tasks(
        self,
        *,
        status: str | Iterable[str] | None = None,
        source: str | None = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        limit = max(1, min(int(limit or 100), 1000))
        where: list[str] = []
        params: list[Any] = []
        if status:
            statuses = [status] if isinstance(status, str) else list(status)
            statuses = [item for item in statuses if item in TASK_STATUSES]
            if statuses:
                where.append("status IN (" + ",".join("?" for _ in statuses) + ")")
                params.extend(statuses)
        if source:
            where.append("source = ?")
            params.append(source)
        sql = "SELECT * FROM app_tasks"
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY priority ASC, created_at DESC LIMIT ?"
        params.append(limit)
        with self._lock, self.connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_task(row) for row in rows]

    def task_counts(self) -> Dict[str, int]:
        counts = {status: 0 for status in TASK_STATUSES}
        with self._lock, self.connect() as conn:
            rows = conn.execute("SELECT status, COUNT(*) AS total FROM app_tasks GROUP BY status").fetchall()
        for row in rows:
            counts[str(row["status"])] = int(row["total"])
        return counts

    def list_stale_tasks(
        self,
        *,
        max_age_minutes: int = 10,
        source: str | None = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Lista tarefas rodando ha tempo demais.

        Usado pelo modo recuperacao: nada e apagado automaticamente; a UI pode
        avisar o usuario e oferecer mover para revisao.
        """
        cutoff = datetime.now() - timedelta(minutes=max(0, int(max_age_minutes if max_age_minutes is not None else 10)))
        candidates = self.list_tasks(status=TASK_RUNNING, source=source, limit=limit)
        stale = []
        for task in candidates:
            updated = _parse_dt(task.get("updated_at"))
            if updated and updated <= cutoff:
                stale.append(task)
        return stale

    def recover_stale_tasks(
        self,
        *,
        max_age_minutes: int = 10,
        source: str | None = None,
        reason: str = "Marcada para revisao pelo modo recuperacao.",
    ) -> int:
        """Move tarefas antigas de running para review e registra evento."""
        stale = self.list_stale_tasks(max_age_minutes=max_age_minutes, source=source, limit=500)
        for task in stale:
            self.update_task(
                task["id"],
                status=TASK_REVIEW,
                last_error=reason,
                attempts_delta=1,
            )
            self.add_event(
                task.get("source") or source or "app",
                "task_recovered",
                f"Tarefa recuperada: {task.get('title', task.get('id'))}",
                level="warning",
                entity_type=task.get("entity_type") or "",
                entity_id=task.get("entity_id") or "",
                payload={"task_id": task.get("id"), "reason": reason},
            )
        return len(stale)

    def delete_tasks(
        self,
        *,
        status: str | Iterable[str] | None = None,
        source: str | None = None,
        older_than_days: int | None = None,
    ) -> int:
        """Remove tarefas antigas/concluidas para manter a fila leve."""
        where: list[str] = []
        params: list[Any] = []
        if status:
            statuses = [status] if isinstance(status, str) else list(status)
            statuses = [item for item in statuses if item in TASK_STATUSES]
            if statuses:
                where.append("status IN (" + ",".join("?" for _ in statuses) + ")")
                params.extend(statuses)
        if source:
            where.append("source = ?")
            params.append(source)
        if older_than_days is not None:
            cutoff = (datetime.now() - timedelta(days=max(0, int(older_than_days)))).isoformat(timespec="seconds")
            where.append("updated_at <= ?")
            params.append(cutoff)
        if not where:
            return 0
        sql = "DELETE FROM app_tasks WHERE " + " AND ".join(where)
        with self._lock, self.connect() as conn:
            cursor = conn.execute(sql, params)
            return int(cursor.rowcount if cursor.rowcount is not None else 0)

    def health_summary(self) -> Dict[str, Any]:
        return {
            "db_path": str(self.db_path),
            "tasks": self.task_counts(),
            "stale_tasks": self.list_stale_tasks(max_age_minutes=10, limit=20),
            "entities": self.entity_counts(),
            "recent_errors": self.list_events(level="error", limit=10),
        }

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> Dict[str, Any]:
        item = dict(row)
        item["payload"] = _from_json(item.pop("payload_json", None), {})
        return item

    @staticmethod
    def _row_to_task(row: sqlite3.Row) -> Dict[str, Any]:
        item = dict(row)
        item["payload"] = _from_json(item.pop("payload_json", None), {})
        return item

    @staticmethod
    def _row_to_entity(row: sqlite3.Row) -> Dict[str, Any]:
        item = dict(row)
        item["payload"] = _from_json(item.pop("payload_json", None), {})
        return item
