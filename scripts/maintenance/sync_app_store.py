#!/usr/bin/env python3
"""Sincroniza JSONs importantes para o estado central SQLite."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.app_metadata import version_payload
from app.core.app_store import AppStore
from app.core.paths import BACKUP_DIR, BASE_DIR, CONFIG_DIR


def load_json(path: Path, default: Any) -> Any:
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default
    return default


def as_items(data: Any, *keys: str) -> List[Dict]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict):
        for key in keys or ("items", "accounts", "tasks"):
            value = data.get(key)
            if isinstance(value, list):
                return [item for item in value if isinstance(item, dict)]
    return []


def paramount_status(account: Dict) -> str:
    raw = str(account.get("status") or "").lower()
    notes = str(account.get("notes") or "").lower()
    combined = f"{raw} {notes}"
    if any(token in combined for token in ("erro", "falha", "403", "bloqueio", "negado", "reprov")):
        return "error"
    if "assinatura ativa" in combined or raw in {"ativa", "sucesso", "finalizado"}:
        return "success"
    if any(token in combined for token in ("rodando", "processando", "abrindo", "preenchendo")):
        return "running"
    if any(token in combined for token in ("login ok", "perfil pronto", "endereco ok", "endereço ok", "plano")):
        return "review"
    return "pending"


def sync_browser_tasks(store: AppStore) -> int:
    tasks = as_items(load_json(CONFIG_DIR / "browser_tasks.json", {}), "items", "tasks")
    for task in tasks:
        task_id = task.get("id") or hashlib.md5(json.dumps(task, sort_keys=True).encode()).hexdigest()[:12]
        store.upsert_task(
            f"browser:{task_id}",
            "browser-task",
            task.get("title") or "Tarefa do navegador",
            source="browser",
            status="success" if task.get("done") else "pending",
            entity_type="profile" if task.get("profile_id") else "",
            entity_id=task.get("profile_id") or "",
            payload=task,
        )
    return len(tasks)


def sync_browser_entities(store: AppStore) -> int:
    store.delete_entities_by_source("browser_profiles")
    data = load_json(BASE_DIR / "browser_profiles" / "profiles.json", {})
    profiles = as_items(data, "profiles")
    for profile in profiles:
        profile_id = profile.get("id") or hashlib.md5(json.dumps(profile, sort_keys=True).encode()).hexdigest()[:12]
        tags = ", ".join(profile.get("tags") or []) if isinstance(profile.get("tags"), list) else ""
        status = "archived" if profile.get("archived") else "active"
        store.upsert_entity(
            f"browser_profile:{profile_id}",
            "browser_profile",
            profile.get("name") or profile_id,
            source="browser_profiles",
            status=status,
            summary=tags,
            payload={
                "id": profile_id,
                "name": profile.get("name", ""),
                "tags": profile.get("tags", []),
                "browser_mode": profile.get("browser_mode", "auto"),
                "fingerprint_level": profile.get("fingerprint_level", ""),
                "last_used": profile.get("last_used", ""),
                "archived": bool(profile.get("archived")),
            },
        )
    return len(profiles)


def sync_paramount_accounts(store: AppStore) -> int:
    store.delete_entities_by_source("paramount_assist")
    data = load_json(CONFIG_DIR / "paramount_assist.json", {})
    accounts = as_items(data, "accounts")
    for account in accounts:
        email = str(account.get("email") or "").strip()
        if not email:
            continue
        account_id = account.get("id") or hashlib.md5(email.lower().encode()).hexdigest()[:12]
        store.upsert_task(
            f"paramount:{account_id}",
            "paramount-account-flow",
            email,
            source="paramount_assist",
            status=paramount_status(account),
            entity_type="account",
            entity_id=str(account_id),
            priority=20,
            payload={
                "email": email,
                "status": account.get("status", ""),
                "profile_id": account.get("profile_id", ""),
                "plan": account.get("plan", ""),
                "has_email_password": bool(account.get("email_password")),
                "updated_at": account.get("updated_at", ""),
            },
            last_error=str(account.get("last_error") or ""),
        )
        person = account.get("person") if isinstance(account.get("person"), dict) else {}
        store.upsert_entity(
            f"paramount_account:{account_id}",
            "paramount_account",
            email,
            source="paramount_assist",
            status=account.get("status") or "novo",
            summary=f"{person.get('name', '')} | {account.get('plan', '')}".strip(" |"),
            payload={
                "id": account_id,
                "email": email,
                "status": account.get("status", ""),
                "profile_id": account.get("profile_id", ""),
                "plan": account.get("plan", ""),
                "person_name": person.get("name", ""),
                "has_email_password": bool(account.get("email_password")),
                "updated_at": account.get("updated_at", ""),
            },
        )
    store.set_state(
        "paramount_assist.summary",
        {
            "accounts": len(accounts),
            "active": sum(1 for a in accounts if a.get("status") == "assinatura ativa"),
            "source": "sync_app_store",
        },
    )
    return len(accounts)


def sync_browser_summary(store: AppStore) -> int:
    data = load_json(BASE_DIR / "browser_profiles" / "profiles.json", {})
    profiles = as_items(data, "profiles")
    store.set_state(
        "browser.summary",
        {
            "profiles": len(profiles),
            "archived": sum(1 for item in profiles if item.get("archived")),
            "source": "sync_app_store",
        },
    )
    return len(profiles)


def sync_favorites(store: AppStore) -> int:
    store.delete_entities_by_source("profile_defaults", "favorite")
    data = load_json(CONFIG_DIR / "default_favorites.json", {})
    favorites = as_items(data, "favorites", "items")
    for favorite in favorites:
        fav_id = favorite.get("id") or hashlib.md5(str(favorite.get("url", "")).encode()).hexdigest()[:12]
        store.upsert_entity(
            f"favorite:{fav_id}",
            "favorite",
            favorite.get("name") or favorite.get("url") or fav_id,
            source="profile_defaults",
            status="active",
            summary=favorite.get("folder", ""),
            payload={
                "id": fav_id,
                "name": favorite.get("name", ""),
                "url": favorite.get("url", ""),
                "folder": favorite.get("folder", ""),
                "icon": favorite.get("icon", ""),
                "updated_at": favorite.get("updated_at", ""),
            },
        )
    return len(favorites)


def sync_backups(store: AppStore) -> int:
    store.delete_entities_by_source("backups")
    backup_dirs = [
        BACKUP_DIR,
        BACKUP_DIR / "browser",
        BACKUP_DIR / "formatacao",
        BACKUP_DIR / "app_state",
        BASE_DIR / "browser_backups",
    ]
    seen: set[Path] = set()
    count = 0
    for folder in backup_dirs:
        if not folder.exists():
            continue
        for path in folder.glob("*"):
            if not path.is_file() or path in seen:
                continue
            if path.suffix.lower() not in {".zip", ".db", ".sqlite", ".sqlite3", ".json"}:
                continue
            seen.add(path)
            try:
                stat = path.stat()
            except OSError:
                continue
            entity_id = hashlib.md5(str(path).lower().encode()).hexdigest()[:16]
            store.upsert_entity(
                f"backup:{entity_id}",
                "backup",
                path.name,
                source="backups",
                status="available",
                summary=f"{round(stat.st_size / (1024 * 1024), 2)} MB",
                payload={
                    "path": str(path),
                    "size": stat.st_size,
                    "modified_at": stat.st_mtime,
                    "suffix": path.suffix.lower(),
                },
            )
            count += 1
    return count


def main() -> int:
    store = AppStore()
    store.set_state("app.version", version_payload())
    browser_tasks = sync_browser_tasks(store)
    paramount_accounts = sync_paramount_accounts(store)
    browser_profiles = sync_browser_summary(store)
    browser_entities = sync_browser_entities(store)
    favorites = sync_favorites(store)
    backups = sync_backups(store)
    store.add_event(
        "maintenance",
        "sync_app_store",
        (
            f"Sincronizados: {browser_tasks} tarefas, {paramount_accounts} contas Paramount, "
            f"{browser_profiles} perfis, {favorites} favoritos, {backups} backups."
        ),
    )
    print(
        "[sync] OK:",
        f"{browser_tasks} tarefas,",
        f"{paramount_accounts} contas Paramount,",
        f"{browser_profiles} perfis ({browser_entities} entidades),",
        f"{favorites} favoritos,",
        f"{backups} backups.",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
