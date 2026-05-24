#!/usr/bin/env python3
"""
Browser Manager - Módulo de Orquestração do Navegador
Telegram Collector Pro v9.0 - Navegador Seguro

Este módulo orquestra a criação e gerenciamento das instâncias do navegador
com configurações anti-fingerprint.

Versão compatível com Python 3.13+ (usa Selenium puro)
"""

import os
import json
import shutil
import time
import subprocess
import sys
import copy
import threading
import sqlite3
import tempfile
import urllib.parse
import zipfile
import hashlib
import socket
import unicodedata
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

from app.core.paths import BASE_DIR
from app.core.error_service import log_exception

try:
    from app.core.app_context import get_app_store
except Exception:
    get_app_store = None

# Tentar importar undetected-chromedriver (preferência) ou selenium (fallback)
UNDETECTED_AVAILABLE = False
SELENIUM_AVAILABLE = False
SELENIUM_ERROR = ""

# Primeiro tentar undetected-chromedriver (melhor anti-detecção)
try:
    import undetected_chromedriver as uc
    UNDETECTED_AVAILABLE = True
except ImportError:
    pass
except Exception as e:
    print(f"Aviso: undetected-chromedriver disponível mas com erro: {e}")

# Fallback para selenium padrão
try:
    from selenium import webdriver
    from selenium.webdriver.chrome.service import Service
    from selenium.webdriver.chrome.options import Options
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        NoSuchElementException, 
        ElementNotInteractableException, 
        StaleElementReferenceException,
        WebDriverException,
        InvalidSessionIdException
    )
    SELENIUM_AVAILABLE = True
except ImportError as e:
    SELENIUM_ERROR = f"selenium não encontrado: {e}"
except Exception as e:
    SELENIUM_ERROR = f"Erro ao importar selenium: {e}"

from fingerprint_generator import FingerprintGenerator
from proxy_manager import ProxyManager, ProxyConfig

# Importar gerenciador de configurações padrão
try:
    from profile_defaults_manager import ProfileDefaultsManager
    DEFAULTS_MANAGER_AVAILABLE = True
except ImportError:
    DEFAULTS_MANAGER_AVAILABLE = False


BUILTIN_DEFAULT_FAVORITES = [
    {
        "id": "builtin_anime",
        "name": "anime",
        "url": (
            "https://sso.crunchyroll.com/pt-br/register?return_url=%2Fauthorize%3Fclient_id%3Dkmj7imhjt_q90lcbzzsj%26redirect_uri%3D"
            "https%253A%252F%252Fcrunchyroll.com%252Fpremium%252Fredirects%26response_type%3Dcookie%26state%3Dis_skip_freetrial"
            "%253Dtrue%2526ref%253Dnewweb_organic_header%2526return_url%253Dhttps%25253A%25252F%25252Fwww.crunchyroll.com"
            "%25252Fpt-br%25252Fvideos%25252Fpopular%2526search%253D%2525253Freferrer%2525253Dnewweb_organic_header"
            "%25252526return_url%2525253Dhttps%252525253A%252525252F%252525252Fwww.crunchyroll.com%252525252Fpt-br"
            "%252525252Fvideos%252525252Fpopular%2526selected_sku%253Dcr_fan_pack.1_month"
        ),
        "folder": "Fixados",
        "icon": "anime",
    },
    {
        "id": "builtin_anime_history",
        "name": "anime hist.",
        "url": "https://www.crunchyroll.com/payments/history",
        "folder": "Fixados",
        "icon": "history",
    },
    {
        "id": "builtin_hbo",
        "name": "hbo",
        "url": "https://auth.hbomax.com/create-account?flow=purchase",
        "folder": "Fixados",
        "icon": "hbo",
    },
    {
        "id": "builtin_outlook",
        "name": "outlook",
        "url": (
            "https://login.microsoftonline.com/common/oauth2/v2.0/authorize?client_id=9199bf20-a13f-4107-85dc-02114787ef48&"
            "scope=https%3A%2F%2Foutlook.office.com%2F.default%20openid%20profile%20offline_access&redirect_uri=https%3A%2F%2F"
            "outlook.live.com%2Fmail%2F&client-request-id=2d48915a-88a1-fcac-abdf-f89ee6aff401&response_mode=fragment&"
            "client_info=1&prompt=select_account&nonce=019b58d7-9ee5-7a69-abb5-44958cc4b3f7&state=eyJpZCI6IjAxOWI1OGQ3LTllZTUt"
            "N2JmNy1hMzgxLTQ5OTg0YTVjZTYwNCIsIm1ldGEiOnsiaW50ZXJhY3Rpb25UeXBlIjoicmVkaXJlY3QifX0%3D%7CaHR0cHM6Ly9vdXRsb29r"
            "LmxpdmUuY29tL21haWwvMC8_ZGVlcGxpbms9bWFpbCUyRjAlMkY&claims=%7B%22access_token%22%3A%7B%22xms_cc%22%3A%7B%22values"
            "%22%3A%5B%22CP1%22%5D%7D%7D%7D&x-client-SKU=msal.js.browser&x-client-VER=4.26.0&response_type=code&code_challenge="
            "kayrA5bxYnQ2BtwV5SQTEOr7kGEqG3GvELq0RfQXLJ0&code_challenge_method=S256&cobrandid=ab0455a0-8d03-46b9-b18b-df2f57b9e44c&fl=dob,flname,wld"
        ),
        "folder": "Fixados",
        "icon": "email",
    },
    {"id": "builtin_amazon", "name": "amazon", "url": "https://www.amazon.com.br/", "folder": "Fixados", "icon": "amazon"},
    {"id": "builtin_paramount", "name": "paramunt", "url": "https://www.paramountplus.com/br/?ftag=PPM-02-10aeh6j", "folder": "Fixados", "icon": "paramount"},
    {"id": "builtin_paramount_login", "name": "paramunt login", "url": "https://www.paramountplus.com/br/account/signin/", "folder": "Fixados", "icon": "paramount"},
    {"id": "builtin_paramount_plan", "name": "paramunt plano", "url": "https://www.paramountplus.com/br/account/signup/plan/", "folder": "Fixados", "icon": "paramount"},
    {
        "id": "builtin_prime",
        "name": "prime",
        "url": "https://www.primevideo.com/-/pt/region/na/offers/nonprimehomepage/ref=dv_web_force_root?language=pt",
        "folder": "Fixados",
        "icon": "prime",
    },
    {
        "id": "builtin_wallet",
        "name": "wallet",
        "url": "https://www.amazon.com.br/cpe/yourpayments/wallet?ref_=ya_d_c_pmt_mpo#",
        "folder": "Fixados",
        "icon": "wallet",
    },
    {"id": "builtin_emailtm", "name": "emailtm", "url": "https://mail.tm/pt/", "folder": "Fixados", "icon": "mail"},
]

LEGACY_DEFAULT_FAVORITE_IDS = {
    "anime001",
    "hbo001",
    "amazon001",
    "prime001",
    "aniprime001",
    "wallet001",
    "disney001",
    "outlook001",
}


class BrowserProfile:
    """Representa um perfil de navegação."""
    
    def __init__(
        self,
        name: str,
        fingerprint: Dict = None,
        proxy: str = None,
        auto_login: Dict = None,
        persist_data: bool = True,
        tags: List[str] = None,
        notes: str = "",
        compatibility_mode: bool = False,
        save_logins: bool = True,
        browser_mode: str = "auto",
        fingerprint_level: str = "Leve",
        address_data: Dict = None,
        archived: bool = False,
        account_identity: Dict = None,
    ):
        """
        Inicializa um perfil de navegação.
        
        Args:
            name: Nome do perfil
            fingerprint: Configurações de fingerprint
            proxy: String do proxy (IP:Porta ou IP:Porta:User:Senha)
            auto_login: Configurações de auto-login {url: {user, password}}
            persist_data: Se True, mantém histórico, cookies e dados entre sessões
        """
        self.name = name
        self.fingerprint = fingerprint or {}
        self.proxy = proxy
        self.auto_login = auto_login or {}
        self.persist_data = persist_data  # Nova opção para persistência de dados
        self.tags = tags or []
        self.notes = notes or ""
        self.compatibility_mode = compatibility_mode
        self.save_logins = save_logins
        self.browser_mode = browser_mode or "auto"
        self.fingerprint_level = fingerprint_level or "Leve"
        self.address_data = address_data or {}
        self.archived = bool(archived)
        self.account_identity = account_identity or {}
        self.created_at = datetime.now().isoformat()
        self.last_used = None
        self.id = fingerprint.get("id") if fingerprint else self._generate_id()
    
    def _generate_id(self) -> str:
        """Gera um ID único para o perfil."""
        import hashlib
        raw = f"{self.name}{datetime.now().timestamp()}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]
    
    def to_dict(self) -> Dict:
        """Converte o perfil para dicionário."""
        return {
            "id": self.id,
            "name": self.name,
            "fingerprint": self.fingerprint,
            "proxy": self.proxy,
            "auto_login": self.auto_login,
            "persist_data": self.persist_data,
            "tags": self.tags,
            "notes": self.notes,
            "compatibility_mode": self.compatibility_mode,
            "save_logins": self.save_logins,
            "browser_mode": self.browser_mode,
            "fingerprint_level": self.fingerprint_level,
            "address_data": self.address_data,
            "archived": self.archived,
            "account_identity": self.account_identity,
            "created_at": self.created_at,
            "last_used": self.last_used,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "BrowserProfile":
        """Cria um perfil a partir de um dicionário."""
        profile = cls(
            name=data.get("name", "Sem Nome"),
            fingerprint=data.get("fingerprint", {}),
            proxy=data.get("proxy"),
            auto_login=data.get("auto_login", {}),
            persist_data=data.get("persist_data", True),
            tags=data.get("tags", []),
            notes=data.get("notes", ""),
            compatibility_mode=data.get("compatibility_mode", False),
            save_logins=data.get("save_logins", True),
            browser_mode=data.get("browser_mode", "auto"),
            fingerprint_level=data.get("fingerprint_level", "Leve"),
            address_data=data.get("address_data", {}),
            archived=data.get("archived", False),
            account_identity=data.get("account_identity", {}),
        )
        profile.id = data.get("id", profile.id)
        profile.created_at = data.get("created_at", profile.created_at)
        profile.last_used = data.get("last_used")
        return profile


class BrowserManager:
    """
    Gerenciador de navegadores com perfis anti-fingerprint.
    Versão compatível com Python 3.13+ usando Selenium puro.
    """
    
    def __init__(self, profiles_dir: str = None):
        """
        Inicializa o gerenciador de navegadores.
        
        Args:
            profiles_dir: Diretório para armazenar perfis
        """
        self.profiles_dir = Path(profiles_dir) if profiles_dir else BASE_DIR / "browser_profiles"
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        
        self.extensions_dir = BASE_DIR / "browser_extensions"
        self.extensions_dir.mkdir(parents=True, exist_ok=True)
        
        self.global_extensions_dir = self.extensions_dir / "global"
        self.global_extensions_dir.mkdir(parents=True, exist_ok=True)
        
        self.fingerprint_generator = FingerprintGenerator()
        self.proxy_manager = ProxyManager(str(self.extensions_dir / "proxy"))
        
        # Gerenciador de configurações padrão (favoritos, extensões, senhas)
        self.config_dir = BASE_DIR / "browser_config"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.logs_file = self.config_dir / "browser_logs.jsonl"
        
        if DEFAULTS_MANAGER_AVAILABLE:
            self.defaults_manager = ProfileDefaultsManager(str(self.config_dir), str(self.extensions_dir))
        else:
            self.defaults_manager = None
        
        # Perfis carregados
        self.profiles: Dict[str, BrowserProfile] = {}
        
        # Navegadores ativos
        self.active_browsers: Dict[str, any] = {}
        self.launching_profiles = set()
        self.browser_state_lock = threading.RLock()
        self.active_browser_modes: Dict[str, str] = {}
        self.active_debug_ports: Dict[str, int] = {}
        self.active_native_browser_names: Dict[str, str] = {}
        self.native_control_drivers: Dict[str, any] = {}
        
        # Carregar perfis existentes
        self._load_profiles()
        self._ensure_builtin_default_favorites()
    
    def _load_profiles(self):
        """Carrega perfis do disco."""
        profiles_file = self.profiles_dir / "profiles.json"
        
        if profiles_file.exists():
            try:
                with open(profiles_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                for profile_data in data.get("profiles", []):
                    profile = BrowserProfile.from_dict(profile_data)
                    self.profiles[profile.id] = profile
                    
            except Exception as e:
                print(f"Erro ao carregar perfis: {e}")

    def _ensure_builtin_default_favorites(self):
        """Garante que os favoritos fixados do projeto existam nos padrões."""
        if not self.defaults_manager:
            return

        favorites_manager = getattr(self.defaults_manager, "favorites", None)
        if not favorites_manager:
            return

        now = datetime.now().isoformat()
        favorites = favorites_manager.favorites
        original_count = len(favorites)
        favorites[:] = [fav for fav in favorites if fav.get("id") not in LEGACY_DEFAULT_FAVORITE_IDS]
        by_id = {fav.get("id"): fav for fav in favorites if fav.get("id")}
        by_name = {(fav.get("name") or "").strip().lower(): fav for fav in favorites if fav.get("name")}
        by_url = {fav.get("url"): fav for fav in favorites if fav.get("url")}
        changed = len(favorites) != original_count

        for builtin in BUILTIN_DEFAULT_FAVORITES:
            builtin = copy.deepcopy(builtin)
            # Deixa os favoritos principais visíveis direto na barra.
            # Pastas continuam existindo para favoritos customizados, mas os
            # atalhos padrão do projeto não ficam mais escondidos em "Fixados".
            builtin["folder"] = "Barra de Favoritos"
            favorite = (
                by_id.get(builtin["id"])
                or by_name.get(builtin["name"].lower())
                or by_url.get(builtin["url"])
            )
            if favorite:
                for key in ("id", "name", "url", "folder", "icon"):
                    if favorite.get(key) != builtin.get(key):
                        favorite[key] = builtin.get(key)
                        changed = True
                if changed:
                    favorite["updated_at"] = now
            else:
                payload = copy.deepcopy(builtin)
                payload["added_at"] = now
                favorites.append(payload)
                by_id[payload["id"]] = payload
                by_name[payload["name"].lower()] = payload
                by_url[payload["url"]] = payload
                changed = True

        if changed:
            favorites_manager._save_favorites()
    
    def _save_profiles(self):
        """Salva perfis no disco."""
        profiles_file = self.profiles_dir / "profiles.json"
        profiles_payload = [p.to_dict() for p in self.profiles.values()]
        
        data = {
            "version": "9.0",
            "profiles": profiles_payload
        }
        
        try:
            with open(profiles_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            if get_app_store:
                try:
                    get_app_store().set_state(
                        "browser.summary",
                        {
                            "profiles": len(profiles_payload),
                            "archived": sum(1 for p in profiles_payload if p.get("archived")),
                            "open": len(self.active_browsers) if hasattr(self, "active_browsers") else 0,
                            "updated_at": datetime.now().isoformat(),
                        },
                    )
                except Exception:
                    pass
        except Exception as e:
            print(f"Erro ao salvar perfis: {e}")

    def log_event(self, event: str, profile_id: str = None, message: str = "", level: str = "info"):
        """Registra eventos simples do navegador para o painel de logs."""
        try:
            payload = {
                "time": datetime.now().isoformat(),
                "level": level,
                "event": event,
                "profile_id": profile_id,
                "message": message,
            }
            with open(self.logs_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
            if get_app_store:
                try:
                    get_app_store().add_event(
                        "browser",
                        event,
                        message,
                        level=level,
                        entity_type="profile" if profile_id else "",
                        entity_id=profile_id or "",
                        payload=payload,
                    )
                except Exception:
                    pass
        except Exception:
            pass

    def get_recent_logs(self, limit: int = 80) -> List[Dict]:
        """Retorna os logs recentes do navegador."""
        if not self.logs_file.exists():
            return []
        try:
            lines = self.logs_file.read_text(encoding="utf-8").splitlines()[-limit:]
            logs = []
            for line in lines:
                try:
                    logs.append(json.loads(line))
                except Exception:
                    continue
            return logs
        except Exception:
            return []

    def get_profile_last_issue(self, profile_id: str, limit: int = 300) -> Optional[Dict]:
        """Retorna o último aviso/erro relevante de um perfil."""
        if not profile_id:
            return None
        noisy_events = {
            "browser_already_open",
            "profile_cache_clean_skip",
            "address_autofill_frame_skip",
            "address_autofill_frame_error",
            "address_state_frame_error",
        }
        for item in reversed(self.get_recent_logs(limit)):
            if item.get("profile_id") != profile_id:
                continue
            event = str(item.get("event") or "")
            level = str(item.get("level") or "info").lower()
            message = str(item.get("message") or "")
            if event in noisy_events:
                continue
            if level not in ("warning", "error"):
                continue
            code = message.split(":", 1)[0].strip() if ":" in message else event
            label = {
                "blocked_403": "403",
                "robot_check": "verificação",
                "captcha": "captcha",
                "network_error": "rede",
                "browser_error": "navegador",
                "native_control_error": "controle",
                "read_error": "diagnóstico",
            }.get(code, code.replace("_", " ")[:24] or "aviso")
            return {
                "time": item.get("time"),
                "level": level,
                "event": event,
                "code": code,
                "label": label,
                "message": message,
            }
        return None

    def _load_json_list(self, filename: str) -> List[Dict]:
        path = self.config_dir / filename
        if not path.exists():
            return []
        try:
            data = json.load(open(path, "r", encoding="utf-8"))
            return data if isinstance(data, list) else data.get("items", [])
        except Exception:
            return []

    def _save_json_list(self, filename: str, items: List[Dict]):
        path = self.config_dir / filename
        data = {"updated_at": datetime.now().isoformat(), "items": items}
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def list_accounts(self) -> List[Dict]:
        return self._load_json_list("browser_accounts.json")

    def save_account(self, account: Dict) -> Dict:
        accounts = self.list_accounts()
        if not account.get("id"):
            account["id"] = hashlib.md5(f"{account.get('name')}{datetime.now()}".encode()).hexdigest()[:12]
            account["created_at"] = datetime.now().isoformat()
        account["updated_at"] = datetime.now().isoformat()

        replaced = False
        for i, existing in enumerate(accounts):
            if existing.get("id") == account["id"]:
                accounts[i] = account
                replaced = True
                break
        if not replaced:
            accounts.append(account)
        self._save_json_list("browser_accounts.json", accounts)
        self.log_event("account_saved", account.get("profile_id"), f"Conta salva: {account.get('name', '')}")
        if get_app_store:
            try:
                get_app_store().set_state(f"browser.account.{account['id']}", account)
            except Exception:
                pass
        return account

    def delete_account(self, account_id: str) -> bool:
        accounts = self.list_accounts()
        filtered = [acc for acc in accounts if acc.get("id") != account_id]
        if len(filtered) == len(accounts):
            return False
        self._save_json_list("browser_accounts.json", filtered)
        self.log_event("account_deleted", None, f"Conta removida: {account_id}")
        return True

    def list_tasks(self) -> List[Dict]:
        return self._load_json_list("browser_tasks.json")

    def save_task(self, task: Dict) -> Dict:
        tasks = self.list_tasks()
        if not task.get("id"):
            task["id"] = hashlib.md5(f"{task.get('title')}{datetime.now()}".encode()).hexdigest()[:12]
            task["created_at"] = datetime.now().isoformat()
            task.setdefault("done", False)
        task["updated_at"] = datetime.now().isoformat()

        replaced = False
        for i, existing in enumerate(tasks):
            if existing.get("id") == task["id"]:
                tasks[i] = task
                replaced = True
                break
        if not replaced:
            tasks.append(task)
        self._save_json_list("browser_tasks.json", tasks)
        self.log_event("task_saved", task.get("profile_id"), f"Tarefa salva: {task.get('title', '')}")
        if get_app_store:
            try:
                get_app_store().upsert_task(
                    f"browser:{task['id']}",
                    "browser-task",
                    task.get("title") or "Tarefa do navegador",
                    source="browser",
                    status="success" if task.get("done") else "pending",
                    entity_type="profile" if task.get("profile_id") else "",
                    entity_id=task.get("profile_id") or "",
                    payload=task,
                )
            except Exception:
                pass
        return task

    def delete_task(self, task_id: str) -> bool:
        tasks = self.list_tasks()
        filtered = [task for task in tasks if task.get("id") != task_id]
        if len(filtered) == len(tasks):
            return False
        self._save_json_list("browser_tasks.json", filtered)
        self.log_event("task_deleted", None, f"Tarefa removida: {task_id}")
        if get_app_store:
            try:
                get_app_store().upsert_task(
                    f"browser:{task_id}",
                    "browser-task",
                    f"Tarefa removida: {task_id}",
                    source="browser",
                    status="cancelled",
                    payload={"id": task_id, "deleted": True},
                )
            except Exception:
                pass
        return True

    def set_task_done(self, task_id: str, done: bool) -> bool:
        tasks = self.list_tasks()
        changed = False
        for task in tasks:
            if task.get("id") == task_id:
                task["done"] = done
                task["updated_at"] = datetime.now().isoformat()
                changed = True
                break
        if changed:
            self._save_json_list("browser_tasks.json", tasks)
            self.log_event("task_done" if done else "task_open", None, task_id)
            if get_app_store:
                try:
                    get_app_store().upsert_task(
                        f"browser:{task_id}",
                        "browser-task",
                        task.get("title") or "Tarefa do navegador",
                        source="browser",
                        status="success" if done else "pending",
                        entity_type="profile" if task.get("profile_id") else "",
                        entity_id=task.get("profile_id") or "",
                        payload=task,
                    )
                except Exception:
                    pass
        return changed
    
    def create_profile(
        self,
        name: str,
        fingerprint: Dict = None,
        proxy: str = None,
        country: str = "BR",
        persist_data: bool = True
    ) -> BrowserProfile:
        """
        Cria um novo perfil de navegação.
        
        Args:
            name: Nome do perfil
            fingerprint: Fingerprint customizado (opcional)
            proxy: String do proxy (opcional)
            country: País para gerar fingerprint (padrão: BR)
            persist_data: Se True, mantém histórico, cookies e dados entre sessões
            
        Returns:
            BrowserProfile criado
        """
        # Gerar fingerprint se não fornecido
        if not fingerprint:
            if country == "BR":
                fingerprint = self.fingerprint_generator.generate_brazilian_fingerprint()
            else:
                fingerprint = self.fingerprint_generator.generate_random_fingerprint(country)
        
        profile = BrowserProfile(
            name=name,
            fingerprint=fingerprint,
            proxy=proxy,
            persist_data=persist_data,
        )
        
        self.profiles[profile.id] = profile
        self._save_profiles()
        
        # Aplicar configurações padrão ao novo perfil
        self._apply_defaults_to_profile(profile.id)
        self.log_event("profile_created", profile.id, f"Perfil criado: {profile.name}")
        
        return profile
    
    def _apply_defaults_to_profile(self, profile_id: str) -> bool:
        """
        Aplica configurações padrão (favoritos, extensões) a um perfil.
        
        Args:
            profile_id: ID do perfil
            
        Returns:
            True se aplicado com sucesso
        """
        if not self.defaults_manager:
            print("[Browser] Gerenciador de configurações padrão não disponível")
            return False
        
        try:
            # Diretório de dados do perfil
            user_data_dir = self.profiles_dir / f"data_{profile_id}"
            user_data_dir.mkdir(parents=True, exist_ok=True)
            
            print(f"[Browser] Aplicando configurações padrão ao perfil {profile_id}")
            print(f"[Browser] Diretório do perfil: {user_data_dir}")
            
            # Aplicar favoritos padrão
            results = self.defaults_manager.apply_defaults_to_profile(user_data_dir)
            
            if results.get("favorites", False):
                print(f"[Browser] Favoritos aplicados com sucesso")
            else:
                print(f"[Browser] Falha ao aplicar favoritos")
            
            return results.get("favorites", False)
        except Exception as e:
            print(f"Erro ao aplicar configurações padrão: {e}")
            log_exception(BASE_DIR, "browser_errors.log", "aplicar configuracoes padrao ao perfil", e)
            return False
    
    def _clear_profile_data(self, user_data_dir: Path):
        """
        Limpa dados do perfil (histórico, cookies, cache) mantendo favoritos e configurações.
        Usado quando persist_data é False.
        
        Args:
            user_data_dir: Diretório de dados do perfil
        """
        try:
            # Pastas a serem limpas (dados de navegação)
            folders_to_clear = [
                "Cache",
                "Code Cache",
                "GPUCache",
                "Service Worker",
                "Session Storage",
                "Local Storage",
                "IndexedDB",
                "File System",
                "blob_storage",
                "databases",
            ]
            
            # Arquivos a serem limpos
            files_to_clear = [
                "History",
                "History-journal",
                "Cookies",
                "Cookies-journal",
                "Web Data",
                "Web Data-journal",
                "Login Data",
                "Login Data-journal",
                "Visited Links",
            "Network Action Predictor",
            "Top Sites",
            "Top Sites-journal",
            "Current Session",
            "Current Tabs",
            "Last Session",
            "Last Tabs",
        ]
            
            default_dir = user_data_dir / "Default"
            if default_dir.exists():
                # Limpar pastas
                for folder in folders_to_clear:
                    folder_path = default_dir / folder
                    if folder_path.exists():
                        try:
                            shutil.rmtree(folder_path)
                        except Exception:
                            pass
                
                # Limpar arquivos
                for file in files_to_clear:
                    file_path = default_dir / file
                    if file_path.exists():
                        try:
                            file_path.unlink()
                        except Exception:
                            pass

                sessions_dir = default_dir / "Sessions"
                if sessions_dir.exists():
                    try:
                        shutil.rmtree(sessions_dir)
                    except Exception:
                        pass
            
            print(f"[Browser] Dados de navegação limpos para o perfil")
            
        except Exception as e:
            print(f"Erro ao limpar dados do perfil: {e}")

    @staticmethod
    def format_size(value: int) -> str:
        """Formata bytes em texto curto para a interface."""
        units = ("B", "KB", "MB", "GB")
        size = float(value or 0)
        for unit in units:
            if size < 1024 or unit == units[-1]:
                if unit == "B":
                    return f"{int(size)} {unit}"
                return f"{size:.1f} {unit}"
            size /= 1024
        return f"{value} B"

    def _folder_size(self, path: Path) -> int:
        """Calcula tamanho de arquivo/pasta tolerando arquivos bloqueados pelo Chrome."""
        if not path.exists():
            return 0
        if path.is_file():
            try:
                return path.stat().st_size
            except OSError:
                return 0

        total = 0
        stack = [path]
        while stack:
            current = stack.pop()
            try:
                entries = list(current.iterdir())
            except OSError:
                continue
            for entry in entries:
                try:
                    if entry.is_dir():
                        stack.append(entry)
                    elif entry.is_file():
                        total += entry.stat().st_size
                except OSError:
                    continue
        return total

    def get_profile_storage_report(self, profile_id: str) -> Dict:
        """Mostra quanto um perfil ocupa sem alterar nenhum dado."""
        profile = self.profiles.get(profile_id)
        if not profile:
            return {"ok": False, "message": "Perfil nao encontrado."}

        user_data_dir = self.get_profile_data_dir(profile_id)
        if not user_data_dir.exists():
            return {
                "ok": False,
                "message": "Este perfil ainda nao tem pasta de navegador.",
                "total_bytes": 0,
            }

        default_dir = user_data_dir / "Default"
        cache_paths = [
            default_dir / "Cache",
            default_dir / "Code Cache",
            default_dir / "GPUCache",
            default_dir / "DawnCache",
            default_dir / "DawnGraphiteCache",
            default_dir / "DawnWebGPUCache",
            user_data_dir / "ShaderCache",
            user_data_dir / "GrShaderCache",
            user_data_dir / "optimization_guide_model_store",
            user_data_dir / "component_crx_cache",
            user_data_dir / "BrowserMetrics",
        ]
        site_data_paths = [
            default_dir / "IndexedDB",
            default_dir / "Local Storage",
            default_dir / "Session Storage",
            default_dir / "File System",
            default_dir / "databases",
            default_dir / "blob_storage",
            default_dir / "Service Worker",
        ]
        identity_paths = [
            default_dir / "Network" / "Cookies",
            default_dir / "Cookies",
            default_dir / "Login Data",
            default_dir / "Web Data",
        ]

        total = self._folder_size(user_data_dir)
        cache = sum(self._folder_size(path) for path in cache_paths)
        site_data = sum(self._folder_size(path) for path in site_data_paths)
        identity = sum(self._folder_size(path) for path in identity_paths)
        known = cache + site_data + identity
        other = max(0, total - known)

        status = "leve"
        if total >= 400 * 1024 * 1024:
            status = "pesado"
        elif total >= 200 * 1024 * 1024:
            status = "medio"

        return {
            "ok": True,
            "profile_id": profile_id,
            "profile_name": profile.name,
            "total_bytes": total,
            "cache_bytes": cache,
            "site_data_bytes": site_data,
            "identity_bytes": identity,
            "other_bytes": other,
            "status": status,
            "message": f"Perfil {status}: {self.format_size(total)}",
        }

    def clear_profile_cache_only(self, profile_id: str) -> Dict:
        """Limpa apenas cache seguro, preservando cookies, logins e dados de sites."""
        profile = self.profiles.get(profile_id)
        if not profile:
            return {"ok": False, "message": "Perfil nao encontrado."}
        if self.is_browser_active(profile_id):
            return {"ok": False, "message": "Feche o navegador deste perfil antes de limpar cache."}

        user_data_dir = self.get_profile_data_dir(profile_id)
        if not user_data_dir.exists():
            return {"ok": False, "message": "Este perfil ainda nao tem pasta de navegador."}

        before = self.get_profile_storage_report(profile_id)
        default_dir = user_data_dir / "Default"
        cache_paths = [
            default_dir / "Cache",
            default_dir / "Code Cache",
            default_dir / "GPUCache",
            default_dir / "DawnCache",
            default_dir / "DawnGraphiteCache",
            default_dir / "DawnWebGPUCache",
            user_data_dir / "ShaderCache",
            user_data_dir / "GrShaderCache",
            user_data_dir / "optimization_guide_model_store",
            user_data_dir / "component_crx_cache",
            user_data_dir / "BrowserMetrics",
        ]

        removed = []
        for path in cache_paths:
            if not path.exists():
                continue
            try:
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
                removed.append(path.name)
            except Exception as e:
                self.log_event("profile_cache_clean_skip", profile_id, f"{path.name}: {e}", "warning")

        after = self.get_profile_storage_report(profile_id)
        freed = max(0, int(before.get("total_bytes", 0)) - int(after.get("total_bytes", 0)))
        self.log_event(
            "profile_cache_cleaned",
            profile_id,
            f"{self.format_size(freed)} liberados; cookies/logins preservados",
        )
        return {
            "ok": True,
            "removed": removed,
            "freed_bytes": freed,
            "before": before,
            "after": after,
            "message": f"Cache limpo: {self.format_size(freed)} liberados.",
        }
    
    def clear_profile_data(self, profile_id: str) -> bool:
        """
        Limpa dados de navegação de um perfil específico.
        
        Args:
            profile_id: ID do perfil
            
        Returns:
            True se limpou com sucesso
        """
        try:
            user_data_dir = self.profiles_dir / f"data_{profile_id}"
            if user_data_dir.exists():
                self._clear_profile_data(user_data_dir)
                return True
            return False
        except Exception as e:
            print(f"Erro ao limpar dados do perfil: {e}")
            return False
    
    def set_persist_data(self, profile_id: str, persist: bool) -> bool:
        """
        Define se o perfil deve manter dados entre sessões.
        
        Args:
            profile_id: ID do perfil
            persist: True para manter dados, False para limpar a cada sessão
            
        Returns:
            True se atualizado com sucesso
        """
        profile = self.profiles.get(profile_id)
        if not profile:
            return False
        
        profile.persist_data = persist
        self._save_profiles()
        return True
    
    def create_quick_profile(self, persist_data: bool = True) -> BrowserProfile:
        """
        Cria um perfil rápido com configurações aleatórias brasileiras.
        
        Returns:
            BrowserProfile criado
        """
        name = self._next_quick_profile_name()
        
        return self.create_profile(name=name, country="BR", persist_data=persist_data)

    def _next_quick_profile_name(self) -> str:
        """Gera nomes simples para perfil rapido: perfil 1, perfil 2..."""
        used_numbers = set()
        used_names = {profile.name.strip().lower() for profile in self.profiles.values()}
        for profile in self.profiles.values():
            name = profile.name.strip().lower()
            if not name.startswith("perfil "):
                continue
            number_text = name.replace("perfil ", "", 1).strip()
            if number_text.isdigit():
                used_numbers.add(int(number_text))

        number = 1
        while number in used_numbers or f"perfil {number}" in used_names:
            number += 1
        return f"perfil {number}"

    @staticmethod
    def normalize_navigation_target(target: str, default_url: str = "https://browserleaks.com/javascript") -> str:
        """Converte texto digitado em URL navegável ou busca do Google."""
        target = (target or "").strip()
        if not target:
            return default_url

        parsed = urllib.parse.urlparse(target)
        if parsed.scheme in ("http", "https", "chrome", "about", "file"):
            return target

        looks_like_domain = (
            " " not in target
            and (
                "." in target
                or target.startswith("localhost")
                or target.replace(":", "").replace("/", "").replace(".", "").isdigit()
            )
        )
        if looks_like_domain:
            if target.startswith("localhost") or target.replace(":", "").replace("/", "").replace(".", "").isdigit():
                return "http://" + target
            return "https://" + target

        return "https://www.google.com/search?q=" + urllib.parse.quote_plus(target)

    def clone_profile(self, profile_id: str, new_name: str = None, clone_data: bool = False) -> Optional[BrowserProfile]:
        """Clona configurações de um perfil para criar outro login isolado."""
        source = self.profiles.get(profile_id)
        if not source:
            return None

        profile = BrowserProfile(
            name=new_name or f"{source.name} Copy",
            fingerprint=copy.deepcopy(source.fingerprint),
            proxy=source.proxy,
            auto_login=copy.deepcopy(source.auto_login),
            persist_data=source.persist_data,
            tags=copy.deepcopy(getattr(source, "tags", [])),
            notes=getattr(source, "notes", ""),
            compatibility_mode=getattr(source, "compatibility_mode", False),
            save_logins=getattr(source, "save_logins", True),
            browser_mode=getattr(source, "browser_mode", "auto"),
            fingerprint_level=getattr(source, "fingerprint_level", "Leve"),
            address_data=copy.deepcopy(getattr(source, "address_data", {})),
        )
        profile.id = profile._generate_id()
        if isinstance(profile.fingerprint, dict):
            profile.fingerprint["id"] = profile.id

        self.profiles[profile.id] = profile
        self._save_profiles()
        self._apply_defaults_to_profile(profile.id)

        if clone_data:
            src_dir = self.profiles_dir / f"data_{profile_id}"
            dst_dir = self.profiles_dir / f"data_{profile.id}"
            if src_dir.exists() and not dst_dir.exists():
                try:
                    shutil.copytree(src_dir, dst_dir)
                except Exception as e:
                    print(f"Erro ao clonar dados do perfil: {e}")
        return profile

    def apply_defaults_to_all_profiles(self) -> Dict[str, bool]:
        """Aplica favoritos padrão aos dados de todos os perfis existentes."""
        results = {}
        for profile_id in list(self.profiles.keys()):
            results[profile_id] = self._apply_defaults_to_profile(profile_id)
        return results

    def get_default_extension_count(self) -> int:
        """Retorna quantas extensões padrão habilitadas serão carregadas no Chrome."""
        if not self.defaults_manager:
            return 0
        return len(self.defaults_manager.get_extension_paths_for_chrome())

    def get_default_favorite_count(self) -> int:
        """Retorna quantos favoritos padrão serão fixados nos perfis."""
        if not self.defaults_manager:
            return 0
        favorites = getattr(self.defaults_manager, "favorites", None)
        return len(favorites.get_favorites()) if favorites else 0

    def get_default_favorites(self) -> List[Dict]:
        """Retorna os favoritos padrão configurados."""
        if not self.defaults_manager:
            return []
        favorites = getattr(self.defaults_manager, "favorites", None)
        return favorites.get_favorites() if favorites else []

    def profile_has_default_favorites(self, profile_id: str) -> bool:
        """Confere se todos os favoritos padrão existem no perfil."""
        expected_urls = {fav.get("url") for fav in self.get_default_favorites() if fav.get("url")}
        if not expected_urls:
            return True

        bookmarks_file = self.profiles_dir / f"data_{profile_id}" / "Default" / "Bookmarks"
        if not bookmarks_file.exists():
            return False
        try:
            data = json.load(open(bookmarks_file, "r", encoding="utf-8"))
        except Exception:
            return False

        found_urls = set()
        stack = list(data.get("roots", {}).values())
        while stack:
            node = stack.pop()
            if isinstance(node, dict) and node.get("type") == "url" and node.get("url"):
                found_urls.add(node.get("url"))
            if isinstance(node, dict):
                stack.extend(node.get("children", []) or [])
        return expected_urls.issubset(found_urls)

    def is_profile_launching(self, profile_id: str) -> bool:
        """Retorna True enquanto o perfil ainda esta abrindo."""
        with self.browser_state_lock:
            return profile_id in self.launching_profiles

    def begin_profile_launch(self, profile_id: str) -> bool:
        """Reserva o perfil para evitar duas aberturas ao mesmo tempo."""
        with self.browser_state_lock:
            if profile_id in self.launching_profiles:
                return False
            if profile_id in self.active_browsers:
                # Nao chame is_browser_active aqui: em alguns drivers Selenium,
                # consultar window_handles pode bloquear a interface por muito tempo.
                active_ref = self.active_browsers.get(profile_id)
                if self.active_browser_modes.get(profile_id) == "native" and hasattr(active_ref, "poll"):
                    if active_ref.poll() is None:
                        return False
                    port = self.active_debug_ports.get(profile_id)
                    if port:
                        try:
                            with socket.create_connection(("127.0.0.1", int(port)), timeout=0.15):
                                return False
                        except Exception:
                            pass
                    self.active_browsers.pop(profile_id, None)
                    self.active_browser_modes.pop(profile_id, None)
                    self.active_debug_ports.pop(profile_id, None)
                    self.active_native_browser_names.pop(profile_id, None)
                    self.native_control_drivers.pop(profile_id, None)
                elif self.active_browser_modes.get(profile_id) == "selenium":
                    process = getattr(getattr(active_ref, "service", None), "process", None)
                    if process is not None and hasattr(process, "poll") and process.poll() is not None:
                        self.active_browsers.pop(profile_id, None)
                        self.active_browser_modes.pop(profile_id, None)
                        self.active_debug_ports.pop(profile_id, None)
                        self.active_native_browser_names.pop(profile_id, None)
                        self.native_control_drivers.pop(profile_id, None)
                    else:
                        return False
                else:
                    return False
            self.launching_profiles.add(profile_id)
            return True

    def end_profile_launch(self, profile_id: str):
        """Libera a reserva feita enquanto o perfil estava abrindo."""
        with self.browser_state_lock:
            self.launching_profiles.discard(profile_id)

    def get_profile_status(self, profile_id: str) -> Dict:
        """Retorna status resumido para a central de perfis."""
        profile = self.profiles.get(profile_id)
        if not profile:
            return {"label": "erro", "color": "#ef4444"}
        active = self.is_browser_active(profile_id)
        launching = self.is_profile_launching(profile_id)
        has_proxy = bool(profile.proxy)
        has_favorites = self.profile_has_default_favorites(profile_id)
        label = "aberto" if active else "abrindo" if launching else "fechado"
        return {
            "active": active,
            "launching": launching,
            "has_proxy": has_proxy,
            "has_favorites": has_favorites,
            "label": label,
            "proxy_label": "com proxy" if has_proxy else "sem proxy",
            "favorites_label": "favoritos OK" if has_favorites else "sem favoritos",
            "color": "#10b981" if active else "#38bdf8" if launching else "#94a3b8",
        }

    def _register_backup_entity(self, backup_file: Path, kind: str = "browser_backup"):
        if not get_app_store or not backup_file:
            return
        try:
            stat = backup_file.stat()
            entity_id = hashlib.md5(str(backup_file).lower().encode()).hexdigest()[:16]
            get_app_store().upsert_entity(
                f"backup:{entity_id}",
                "backup",
                backup_file.name,
                source="backups",
                status="available",
                summary=f"{round(stat.st_size / (1024 * 1024), 2)} MB",
                payload={
                    "path": str(backup_file),
                    "size": stat.st_size,
                    "kind": kind,
                    "created_at": datetime.now().isoformat(),
                },
            )
        except Exception:
            pass

    def create_browser_backup(self) -> Optional[Path]:
        """Cria backup zip dos perfis, favoritos, extensões e configurações do navegador."""
        try:
            backup_dir = BASE_DIR / "backups" / "browser"
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_file = backup_dir / f"browser_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            sources = [self.profiles_dir, self.config_dir, self.extensions_dir]

            with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as zf:
                for source in sources:
                    if not source.exists():
                        continue
                    for path in source.rglob("*"):
                        if path.is_file():
                            zf.write(path, path.relative_to(BASE_DIR))

            self.log_event("backup_created", None, str(backup_file))
            self._register_backup_entity(backup_file, "browser_backup")
            return backup_file
        except Exception as e:
            self.log_event("backup_error", None, str(e), "error")
            return None

    def create_format_backup(self) -> Dict:
        """Cria um backup pensado para restaurar depois de formatar o PC."""
        try:
            backup_dir = BASE_DIR / "backups" / "formatacao"
            backup_dir.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = backup_dir / f"backup_formatacao_navegador_{timestamp}.zip"

            profiles_report = []
            profiles = self.list_profiles(include_archived=True)
            for profile in profiles:
                identity = self.inspect_profile_identity(profile.id)
                if identity.get("ok"):
                    profile.account_identity = identity
                profiles_report.append({
                    "id": profile.id,
                    "name": profile.name,
                    "archived": getattr(profile, "archived", False),
                    "tags": getattr(profile, "tags", []) or [],
                    "browser_mode": getattr(profile, "browser_mode", "auto"),
                    "fingerprint_level": getattr(profile, "fingerprint_level", "Leve"),
                    "persist_data": getattr(profile, "persist_data", True),
                    "save_logins": getattr(profile, "save_logins", True),
                    "last_used": getattr(profile, "last_used", None),
                    "address_saved": bool((getattr(profile, "address_data", {}) or {}).get("cep")),
                    "identity": {
                        "ok": identity.get("ok", False),
                        "message": identity.get("message", ""),
                        "login_count": identity.get("login_count", 0),
                        "cookies_total": identity.get("cookies_total", 0),
                        "cookie_domains_count": identity.get("cookie_domains_count", 0),
                        "likely_sites": identity.get("likely_sites", [])[:12],
                    },
                })

            self._save_profiles()
            manifest = {
                "created_at": datetime.now().isoformat(),
                "base_dir": str(BASE_DIR),
                "profiles_total": len(profiles_report),
                "archived_total": len([p for p in profiles_report if p.get("archived")]),
                "active_browsers_at_backup": len(self.get_active_browsers()),
                "included_folders": [
                    "browser_profiles",
                    "browser_config",
                    "browser_extensions",
                ],
                "restore_hint": (
                    "Restaure este ZIP na pasta do projeto antes de abrir os perfis. "
                    "Cookies podem continuar, mas sites como Amazon/Google/Microsoft ainda podem pedir confirmação."
                ),
                "profiles": profiles_report,
            }

            sources = [self.profiles_dir, self.config_dir, self.extensions_dir]
            skipped_dirs = {"_trash"}
            skipped_names = {"SingletonCookie", "SingletonLock", "SingletonSocket"}

            with zipfile.ZipFile(backup_file, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.writestr(
                    "backup_manifest_formatacao.json",
                    json.dumps(manifest, indent=2, ensure_ascii=False),
                )
                for source in sources:
                    if not source.exists():
                        continue
                    for path in source.rglob("*"):
                        if any(part in skipped_dirs for part in path.parts):
                            continue
                        if path.name in skipped_names:
                            continue
                        if path.is_file():
                            try:
                                zf.write(path, path.relative_to(BASE_DIR))
                            except Exception as file_error:
                                self.log_event("format_backup_file_skip", None, f"{path}: {file_error}", "warning")

            size_mb = round(backup_file.stat().st_size / (1024 * 1024), 2)
            self.log_event("format_backup_created", None, f"{backup_file} ({size_mb} MB)")
            self._register_backup_entity(backup_file, "format_backup")
            return {
                "ok": True,
                "file": str(backup_file),
                "name": backup_file.name,
                "size_mb": size_mb,
                "profiles_total": manifest["profiles_total"],
                "archived_total": manifest["archived_total"],
                "profiles_with_logins": len([p for p in profiles_report if p["identity"].get("login_count", 0) > 0]),
                "profiles_with_cookies": len([p for p in profiles_report if p["identity"].get("cookie_domains_count", 0) > 0]),
                "manifest": manifest,
                "message": f"Backup para formatação criado: {backup_file.name}",
            }
        except Exception as e:
            self.log_event("format_backup_error", None, str(e), "error")
            return {"ok": False, "message": str(e)}
    
    def get_profile(self, profile_id: str) -> Optional[BrowserProfile]:
        """
        Obtém um perfil pelo ID.
        
        Args:
            profile_id: ID do perfil
            
        Returns:
            BrowserProfile ou None
        """
        return self.profiles.get(profile_id)
    
    def update_profile(
        self,
        profile_id: str,
        name: str = None,
        fingerprint: Dict = None,
        proxy: str = None,
        auto_login: Dict = None,
    ) -> Optional[BrowserProfile]:
        """
        Atualiza um perfil existente.
        
        Args:
            profile_id: ID do perfil
            name: Novo nome (opcional)
            fingerprint: Novo fingerprint (opcional)
            proxy: Novo proxy (opcional)
            auto_login: Novas configurações de auto-login (opcional)
            
        Returns:
            BrowserProfile atualizado ou None
        """
        profile = self.profiles.get(profile_id)
        if not profile:
            return None
        
        if name is not None:
            profile.name = name
        if fingerprint is not None:
            profile.fingerprint = fingerprint
        if proxy is not None:
            profile.proxy = proxy
        if auto_login is not None:
            profile.auto_login = auto_login
        
        self._save_profiles()
        return profile
    
    def delete_profile(self, profile_id: str) -> bool:
        """
        Remove um perfil.
        
        Args:
            profile_id: ID do perfil
            
        Returns:
            True se removido com sucesso
        """
        if profile_id not in self.profiles:
            return False
        
        # Fechar navegador se ativo
        if profile_id in self.active_browsers:
            self.close_browser(profile_id)
        
        # Remover dados do perfil sem travar a interface. Perfis do Chrome/Edge
        # costumam ter milhares de arquivos pequenos; apagar direto no clique
        # deixa o PyQt com cara de travado.
        user_data_dir = self.profiles_dir / f"data_{profile_id}"
        if user_data_dir.exists():
            trash_dir = self.profiles_dir / "_trash"
            trash_dir.mkdir(parents=True, exist_ok=True)
            trash_path = trash_dir / f"deleted_{profile_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            delete_target = user_data_dir
            try:
                user_data_dir.rename(trash_path)
                delete_target = trash_path
            except Exception as e:
                self.log_event("profile_data_trash_error", profile_id, f"Usando exclusão direta em segundo plano: {e}", "warning")
            self._delete_profile_path_background(delete_target, profile_id)
        
        del self.profiles[profile_id]
        self._save_profiles()
        self.log_event("profile_deleted", profile_id, "Perfil removido da lista; dados apagando em segundo plano")
        
        return True

    def _delete_profile_path_background(self, path: Path, profile_id: str):
        """Apaga pasta pesada do perfil sem bloquear a UI."""
        path = Path(path)

        def worker():
            if not path.exists():
                return
            try:
                shutil.rmtree(path)
                self.log_event("profile_data_deleted", profile_id, f"Dados removidos: {path.name}")
            except Exception as e:
                self.log_event("profile_data_delete_error", profile_id, f"{path}: {e}", "warning")

        threading.Thread(target=worker, name=f"delete-profile-{profile_id}", daemon=True).start()
    
    def list_profiles(self, include_archived: bool = False, only_archived: bool = False) -> List[BrowserProfile]:
        """
        Lista todos os perfis.
        
        Returns:
            Lista de BrowserProfile
        """
        profiles = list(self.profiles.values())
        if only_archived:
            return [profile for profile in profiles if getattr(profile, "archived", False)]
        if include_archived:
            return profiles
        return [profile for profile in profiles if not getattr(profile, "archived", False)]

    def archive_profile(self, profile_id: str, archived: bool = True) -> bool:
        """Arquiva/restaura um perfil sem apagar cookies, logins ou pasta de dados."""
        profile = self.profiles.get(profile_id)
        if not profile:
            return False
        if archived and self.is_browser_active(profile_id):
            self.close_browser(profile_id)
        profile.archived = bool(archived)
        self._save_profiles()
        event = "profile_archived" if archived else "profile_unarchived"
        message = "Perfil arquivado" if archived else "Perfil restaurado"
        self.log_event(event, profile_id, f"{message}: {profile.name}")
        return True

    def get_profile_data_dir(self, profile_id: str) -> Path:
        """Retorna a pasta de dados do navegador para um perfil."""
        return self.profiles_dir / f"data_{profile_id}"

    def update_profile_identity(self, profile_id: str) -> Dict:
        """Analisa cookies/logins locais e salva um resumo no perfil."""
        result = self.inspect_profile_identity(profile_id)
        profile = self.profiles.get(profile_id)
        if profile and result.get("ok"):
            profile.account_identity = result
            self._save_profiles()
            self.log_event(
                "profile_identity_scanned",
                profile_id,
                f"{result.get('login_count', 0)} login(s), {result.get('cookie_domains_count', 0)} domínio(s) com cookies"
            )
        return result

    def inspect_profile_identity(self, profile_id: str) -> Dict:
        """Lê metadados locais de Cookies/Login Data sem descriptografar senhas."""
        profile = self.profiles.get(profile_id)
        if not profile:
            return {"ok": False, "message": "Perfil não encontrado."}

        user_data_dir = self.get_profile_data_dir(profile_id)
        default_dir = user_data_dir / "Default"
        if not user_data_dir.exists():
            return {
                "ok": False,
                "message": "Este perfil ainda não tem pasta de navegador. Abra ele uma vez para gerar cookies/logins.",
            }

        cookie_rows = []
        login_rows = []
        cookie_db_candidates = [
            default_dir / "Network" / "Cookies",
            default_dir / "Cookies",
            user_data_dir / "Default" / "Network" / "Cookies",
        ]
        login_db_candidates = [
            default_dir / "Login Data",
            user_data_dir / "Default" / "Login Data",
        ]

        def read_db(db_path: Path, query: str):
            if not db_path.exists():
                return []
            tmp_file = None
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".sqlite") as tmp:
                    tmp_file = Path(tmp.name)
                shutil.copy2(db_path, tmp_file)
                conn = sqlite3.connect(str(tmp_file))
                try:
                    conn.row_factory = sqlite3.Row
                    rows = [dict(row) for row in conn.execute(query).fetchall()]
                    return rows
                finally:
                    conn.close()
            except Exception as e:
                self.log_event("profile_identity_db_error", profile_id, f"{db_path.name}: {e}", "warning")
                return []
            finally:
                if tmp_file:
                    try:
                        tmp_file.unlink(missing_ok=True)
                    except Exception:
                        pass

        for db_path in cookie_db_candidates:
            cookie_rows = read_db(
                db_path,
                "SELECT host_key, name, expires_utc, is_secure, is_httponly FROM cookies"
            )
            if cookie_rows:
                break

        for db_path in login_db_candidates:
            login_rows = read_db(
                db_path,
                "SELECT origin_url, action_url, username_value, date_created, blacklisted_by_user "
                "FROM logins WHERE COALESCE(blacklisted_by_user, 0) = 0"
            )
            if login_rows:
                break

        def domain_label(domain: str) -> str:
            clean = domain.lower().lstrip(".")
            labels = [
                ("amazon", "Amazon"),
                ("primevideo", "Prime Video"),
                ("paramountplus", "Paramount+"),
                ("crunchyroll", "Crunchyroll"),
                ("hbomax", "HBO Max"),
                ("max.com", "HBO Max"),
                ("outlook", "Outlook"),
                ("live.com", "Microsoft/Outlook"),
                ("microsoft", "Microsoft"),
                ("google", "Google"),
                ("mail.tm", "Mail.tm"),
            ]
            for token, label in labels:
                if token in clean:
                    return label
            parts = clean.split(".")
            if len(parts) >= 2:
                return ".".join(parts[-2:])
            return clean or "Desconhecido"

        domain_counts: Dict[str, int] = {}
        for row in cookie_rows:
            domain = str(row.get("host_key") or "").lstrip(".").lower()
            if not domain:
                continue
            domain_counts[domain] = domain_counts.get(domain, 0) + 1

        sorted_domains = sorted(domain_counts.items(), key=lambda item: item[1], reverse=True)
        cookie_domains = [
            {
                "domain": domain,
                "label": domain_label(domain),
                "count": count,
            }
            for domain, count in sorted_domains[:30]
        ]

        logins = []
        for row in login_rows:
            url = row.get("origin_url") or row.get("action_url") or ""
            parsed = urllib.parse.urlparse(url)
            domain = parsed.netloc or url
            username = (row.get("username_value") or "").strip()
            if not username:
                username = "(usuário salvo sem nome visível)"
            logins.append({
                "site": domain_label(domain),
                "domain": domain.lstrip("."),
                "username": username,
                "url": url,
            })

        seen_sites = []
        for item in logins:
            label = item.get("site") or item.get("domain")
            if label and label not in seen_sites:
                seen_sites.append(label)
        for item in cookie_domains:
            label = item.get("label") or item.get("domain")
            if label and label not in seen_sites:
                seen_sites.append(label)

        return {
            "ok": True,
            "profile_id": profile_id,
            "profile_name": profile.name,
            "scanned_at": datetime.now().isoformat(),
            "cookies_total": len(cookie_rows),
            "cookie_domains_count": len(domain_counts),
            "cookie_domains": cookie_domains,
            "login_count": len(logins),
            "logins": logins[:50],
            "likely_sites": seen_sites[:12],
            "message": f"{len(logins)} login(s) salvo(s), {len(cookie_rows)} cookie(s) em {len(domain_counts)} domínio(s).",
        }
    
    def _find_chrome_path(self) -> Optional[str]:
        """
        Encontra o caminho do Chrome instalado.
        
        Returns:
            Caminho do Chrome ou None
        """
        # Caminhos comuns do Chrome no Windows
        possible_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe"),
        ]
        
        # Adicionar caminhos do Linux/Mac
        if sys.platform != "win32":
            possible_paths.extend([
                "/usr/bin/google-chrome",
                "/usr/bin/google-chrome-stable",
                "/usr/bin/chromium",
                "/usr/bin/chromium-browser",
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
            ])
        
        for path in possible_paths:
            if os.path.exists(path):
                return path
        
        return None

    def _find_native_browser(self, preferred: str = None) -> Optional[Dict[str, str]]:
        """Encontra navegador instalado para modo nativo."""
        preferred = (preferred or "auto").lower()
        candidates = [
            ("chrome", r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
            ("chrome", r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
            ("chrome", os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")),
            ("edge", r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
            ("edge", r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
            ("edge", os.path.expanduser(r"~\AppData\Local\Microsoft\Edge\Application\msedge.exe")),
            ("firefox", r"C:\Program Files\Mozilla Firefox\firefox.exe"),
            ("firefox", r"C:\Program Files (x86)\Mozilla Firefox\firefox.exe"),
        ]
        if preferred and preferred != "auto":
            candidates = [item for item in candidates if item[0] == preferred] + [
                item for item in candidates if item[0] != preferred
            ]
        for name, path in candidates:
            if os.path.exists(path):
                if preferred in ("chrome", "edge", "firefox") and name != preferred:
                    continue
                return {"name": name, "path": path}
        commands = (("chrome", "chrome"), ("edge", "msedge"), ("firefox", "firefox"))
        if preferred and preferred != "auto":
            commands = tuple(item for item in commands if item[0] == preferred)
        for name, command in commands:
            found = shutil.which(command)
            if found:
                return {"name": name, "path": found}
        return None

    def _is_port_free(self, port: int) -> bool:
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(0.15)
                return sock.connect_ex(("127.0.0.1", port)) != 0
        except OSError:
            return False

    def _pick_debug_port(self, profile_id: str) -> int:
        seed = int(hashlib.md5(profile_id.encode("utf-8")).hexdigest()[:4], 16)
        start = 9300 + (seed % 700)
        used = set(self.active_debug_ports.values())
        for offset in range(250):
            port = start + offset
            if port > 65500:
                port = 9300 + (port % 700)
            if port not in used and self._is_port_free(port):
                return port
        return start

    def _launch_native_chrome(self, profile: BrowserProfile, user_data_dir: Path, start_url: str = None, preferred_browser: str = None):
        """Abre navegador direto, sem Selenium, para sites que bloqueiam automação."""
        preferred_browser = preferred_browser or getattr(profile, "browser_mode", "auto")
        browser = self._find_native_browser(preferred_browser)
        if not browser:
            raise Exception("Nenhum navegador nativo encontrado. Instale Chrome, Edge ou Firefox.")

        screen = profile.fingerprint.get("screen", {})
        launch_rect = getattr(profile, "launch_rect", None) or {}
        width = int(launch_rect.get("width") or screen.get("width", 1366))
        height = int(launch_rect.get("height") or screen.get("height", 768))
        locale = profile.fingerprint.get("locale", "pt-BR")
        target_url = self.normalize_navigation_target(start_url or "https://www.paramountplus.com/br/account/signin/")
        if "paramountplus.com" in target_url.lower():
            if "/account/user-flow" in target_url.lower() or "/f-upsell" in target_url.lower():
                target_url = "https://www.paramountplus.com/br/account/signin/"

        debug_port = None
        if browser["name"] == "firefox":
            firefox_profile_dir = user_data_dir / "FirefoxProfile"
            firefox_profile_dir.mkdir(parents=True, exist_ok=True)
            args = [
                browser["path"],
                "-profile",
                str(firefox_profile_dir),
                "-width",
                str(width),
                "-height",
                str(height),
                "-new-window",
                target_url,
            ]
        else:
            args = [
                browser["path"],
                f"--user-data-dir={user_data_dir}",
                f"--window-size={width},{height}",
                f"--lang={locale}",
                "--new-window",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-notifications",
                "--disable-session-crashed-bubble",
            ]
            if launch_rect:
                args.append(f"--window-position={int(launch_rect.get('x', 0))},{int(launch_rect.get('y', 0))}")
            debug_port = self._pick_debug_port(profile.id)
            args.append(f"--remote-debugging-port={debug_port}")
            args.append("--remote-allow-origins=*")
            if not getattr(profile, "save_logins", True):
                args.append("--disable-save-password-bubble")

        if profile.proxy and browser["name"] != "firefox":
            proxy_config = self.proxy_manager.parse_proxy_string(profile.proxy)
            if proxy_config and not proxy_config.requires_auth:
                args.append(f"--proxy-server=http://{proxy_config.host}:{proxy_config.port}")

        if browser["name"] != "firefox":
            args.append(target_url)
        process = subprocess.Popen(args, cwd=str(BASE_DIR))
        if hasattr(profile, "launch_rect"):
            profile.launch_rect = None
        if debug_port:
            self.active_debug_ports[profile.id] = debug_port
            self.active_native_browser_names[profile.id] = browser["name"]
        self.log_event("native_browser_opened", profile.id, f"{browser['name']} nativo aberto: {target_url}")
        return process
    
    def create_browser(self, profile_id: str, start_url: str = None) -> Optional[any]:
        """
        Cria uma instância do navegador com o perfil especificado.
        Versão compatível com Python 3.13+ usando Selenium puro.
        
        Args:
            profile_id: ID do perfil
            
        Returns:
            Instância do driver ou None
        """
        if not SELENIUM_AVAILABLE:
            error_msg = "Selenium não está instalado.\n"
            error_msg += "Execute: pip install selenium\n"
            if SELENIUM_ERROR:
                error_msg += f"\nDetalhes: {SELENIUM_ERROR}"
            raise ImportError(error_msg)
        
        profile = self.profiles.get(profile_id)
        if not profile:
            raise ValueError(f"Perfil não encontrado: {profile_id}")

        # Garante favoritos/preferências no diretório exato que o Chrome vai abrir.
        if self.is_browser_active(profile_id):
            self.log_event("browser_already_open", profile_id, "Abertura duplicada bloqueada; perfil ja esta aberto", "warning")
            return self.active_browsers.get(profile_id)

        self._apply_defaults_to_profile(profile_id)
        browser_mode = (getattr(profile, "browser_mode", "auto") or "auto").lower()
        fingerprint_level = (getattr(profile, "fingerprint_level", "Leve") or "Leve").lower()
        compatibility_mode = bool(getattr(profile, "compatibility_mode", False))
        if fingerprint_level == "streaming":
            compatibility_mode = True
        if start_url and any(domain in start_url.lower() for domain in ("paramountplus.com", "hbomax.com", "primevideo.com", "crunchyroll.com")):
            compatibility_mode = True
        
        # Atualizar último uso
        profile.last_used = datetime.now().isoformat()
        self._save_profiles()
        
        # Configurar opções do Chrome
        options = Options()
        
        # Diretório de dados do usuário (isolado por perfil)
        user_data_dir = self.profiles_dir / f"data_{profile_id}"
        user_data_dir.mkdir(parents=True, exist_ok=True)
        
        # Se persist_data for False, limpar dados anteriores (modo "incognito" persistente)
        if not profile.persist_data:
            self._clear_profile_data(user_data_dir)

        native_requested = browser_mode in ("chrome", "edge", "firefox")
        if native_requested or (
            compatibility_mode
            and start_url
            and any(domain in start_url.lower() for domain in ("paramountplus.com", "crunchyroll.com"))
        ):
            if self.is_browser_active(profile_id):
                self.log_event("browser_already_open", profile_id, "Abertura duplicada bloqueada no modo nativo", "warning")
                return self.active_browsers.get(profile_id)
            process = self._launch_native_chrome(
                profile,
                user_data_dir,
                start_url,
                preferred_browser=browser_mode if native_requested else None,
            )
            self.active_browsers[profile_id] = process
            self.active_browser_modes[profile_id] = "native"
            self.log_event("native_mode", profile_id, f"Navegador nativo aberto ({browser_mode})")
            return process
        
        options.add_argument(f"--user-data-dir={user_data_dir}")
        
        # Configurar User-Agent
        if profile.fingerprint.get("user_agent"):
            options.add_argument(f"--user-agent={profile.fingerprint['user_agent']}")
        
        # Configurar resolução
        screen = profile.fingerprint.get("screen", {})
        launch_rect = getattr(profile, "launch_rect", None) or {}
        width = int(launch_rect.get("width") or screen.get("width", 1920))
        height = int(launch_rect.get("height") or screen.get("height", 1080))
        options.add_argument(f"--window-size={width},{height}")
        if launch_rect:
            options.add_argument(f"--window-position={int(launch_rect.get('x', 0))},{int(launch_rect.get('y', 0))}")
        
        # === CONFIGURAÇÕES ANTI-DETECÇÃO ===
        
        light_spoof = fingerprint_level in ("leve", "forte")
        strong_spoof = fingerprint_level == "forte"
        if not compatibility_mode and light_spoof:
            # Desabilitar flag de automação
            options.add_argument("--disable-blink-features=AutomationControlled")

            # Excluir switches que indicam automação
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option("useAutomationExtension", False)

            # Desabilitar WebRTC para prevenir vazamento de IP
            options.add_argument("--disable-webrtc")
            options.add_argument("--disable-webrtc-hw-encoding")
            options.add_argument("--disable-webrtc-hw-decoding")
            options.add_argument("--disable-webrtc-multiple-routes")
            options.add_argument("--disable-webrtc-hw-vp8-encoding")
            options.add_argument("--enforce-webrtc-ip-permission-check")
            options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
        
        # Outras configurações
        options.add_argument("--disable-infobars")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-notifications")
        if not getattr(profile, "save_logins", True):
            options.add_argument("--disable-save-password-bubble")
        if not compatibility_mode and light_spoof:
            options.add_argument("--disable-popup-blocking")
        
        # Configurar idioma
        locale = profile.fingerprint.get("locale", "pt-BR")
        options.add_argument(f"--lang={locale}")
        
        # Configurar preferências
        prefs = {
            "intl.accept_languages": ",".join(profile.fingerprint.get("languages", ["pt-BR", "pt", "en"])),
            "profile.default_content_setting_values.notifications": 2,
            "credentials_enable_service": bool(getattr(profile, "save_logins", True)),
            "profile.password_manager_enabled": bool(getattr(profile, "save_logins", True)),
            "bookmark_bar.show_on_all_tabs": True,
            "browser.show_home_button": True,
        }
        if not compatibility_mode and light_spoof:
            prefs.update({
                "webrtc.ip_handling_policy": "disable_non_proxied_udp",
                "webrtc.multiple_routes_enabled": False,
                "webrtc.nonproxied_udp_enabled": False,
            })
        options.add_experimental_option("prefs", prefs)
        
        # Lista de extensões a carregar
        extensions_to_load = []
        
        # Configurar proxy
        if profile.proxy:
            proxy_config = self.proxy_manager.parse_proxy_string(profile.proxy)
            if proxy_config:
                if proxy_config.requires_auth:
                    # Criar extensão para proxy autenticado
                    ext_path = self.proxy_manager.create_proxy_extension_mv2(proxy_config)
                    if ext_path:
                        extensions_to_load.append(ext_path)
                else:
                    # Proxy sem autenticação
                    options.add_argument(f"--proxy-server=http://{proxy_config.host}:{proxy_config.port}")
        
        # Carregar extensões globais
        if not compatibility_mode and self.global_extensions_dir.exists():
            for ext_item in self.global_extensions_dir.iterdir():
                if ext_item.is_dir() or ext_item.suffix in [".crx", ".zip"]:
                    extensions_to_load.append(str(ext_item.absolute()))
        
        # Carregar extensões padrão do gerenciador de configurações
        if not compatibility_mode and self.defaults_manager:
            default_ext_paths = self.defaults_manager.get_extension_paths_for_chrome()
            extensions_to_load.extend(default_ext_paths)
        
        extension_dirs = []
        extension_files = []
        for ext_path in dict.fromkeys(extensions_to_load):
            path_obj = Path(ext_path)
            if path_obj.is_dir():
                extension_dirs.append(str(path_obj.absolute()))
            elif path_obj.suffix.lower() == ".crx":
                extension_files.append(str(path_obj.absolute()))

        # Pastas unpacked carregam via --load-extension. CRX carrega por add_extension.
        if extension_dirs:
            options.add_argument(f"--load-extension={','.join(extension_dirs)}")
        for ext_file in extension_files:
            try:
                options.add_extension(ext_file)
            except Exception as e:
                print(f"Aviso: não foi possível adicionar extensão {ext_file}: {e}")
        
        # Encontrar Chrome
        chrome_path = self._find_chrome_path()
        if chrome_path:
            options.binary_location = chrome_path
        
        # Criar driver - Tentar undetected-chromedriver primeiro (melhor anti-detecção)
        driver = None
        use_undetected = UNDETECTED_AVAILABLE
        
        if use_undetected:
            try:
                print("[Anti-Detect] Usando undetected-chromedriver...")
                
                # Configurar opções para undetected-chromedriver
                uc_options = uc.ChromeOptions()
                
                # Diretório de dados do usuário
                uc_options.add_argument(f"--user-data-dir={user_data_dir}")
                
                # User-Agent
                if profile.fingerprint.get("user_agent"):
                    uc_options.add_argument(f"--user-agent={profile.fingerprint['user_agent']}")
                
                # Resolução
                uc_options.add_argument(f"--window-size={width},{height}")
                if launch_rect:
                    uc_options.add_argument(f"--window-position={int(launch_rect.get('x', 0))},{int(launch_rect.get('y', 0))}")
                
                # Idioma
                uc_options.add_argument(f"--lang={locale}")
                
                if not compatibility_mode and light_spoof:
                    # Desabilitar WebRTC
                    uc_options.add_argument("--disable-webrtc")
                    uc_options.add_argument("--force-webrtc-ip-handling-policy=disable_non_proxied_udp")
                
                # Outras configurações
                uc_options.add_argument("--disable-infobars")
                uc_options.add_argument("--disable-notifications")
                if not compatibility_mode and light_spoof:
                    uc_options.add_argument("--disable-popup-blocking")
                
                # Proxy (se configurado e sem autenticação)
                if profile.proxy:
                    proxy_config = self.proxy_manager.parse_proxy_string(profile.proxy)
                    if proxy_config and not proxy_config.requires_auth:
                        uc_options.add_argument(f"--proxy-server=http://{proxy_config.host}:{proxy_config.port}")

                if extension_dirs:
                    uc_options.add_argument(f"--load-extension={','.join(extension_dirs)}")
                for ext_file in extension_files:
                    try:
                        uc_options.add_extension(ext_file)
                    except Exception as e:
                        print(f"Aviso: não foi possível adicionar extensão {ext_file}: {e}")
                
                # Criar driver undetected
                driver = uc.Chrome(
                    options=uc_options,
                    use_subprocess=True,
                    version_main=None  # Auto-detectar versão do Chrome
                )
                
                print("[Anti-Detect] undetected-chromedriver iniciado com sucesso!")
                
            except Exception as e:
                print(f"[Anti-Detect] Falha no undetected-chromedriver: {e}")
                print("[Anti-Detect] Tentando Selenium padrão...")
                use_undetected = False
                driver = None
        
        # Fallback para Selenium padrão
        if not use_undetected or driver is None:
            try:
                print("[Browser] Usando Selenium padrão...")
                driver = webdriver.Chrome(options=options)
                print("[Browser] Selenium iniciado com sucesso!")
            except Exception as e:
                error_msg = str(e)
                if "chromedriver" in error_msg.lower() or "chrome" in error_msg.lower():
                    raise Exception(
                        "Erro ao iniciar o Chrome.\n\n"
                        "Verifique se:\n"
                        "1. O Google Chrome está instalado\n"
                        "2. O Chrome está atualizado\n"
                        "3. Você tem o Selenium 4.6+: pip install --upgrade selenium\n"
                        "4. Ou instale: pip install undetected-chromedriver\n\n"
                        f"Erro: {error_msg}"
                    )
                raise
        
        if not compatibility_mode and light_spoof:
            # Injetar scripts de spoofing (especialmente importante para Selenium padrão)
            self._inject_spoofing_scripts(driver, profile)

            # Injetar scripts adicionais de anti-detecção
            if strong_spoof:
                self._inject_advanced_antidetect(driver, profile)
        else:
            self.log_event("compatibility_mode", profile_id, "Modo compatibilidade ativo para streaming")
        
        # Armazenar referência
        self.active_browsers[profile_id] = driver
        self.active_browser_modes[profile_id] = "selenium"
        if hasattr(profile, "launch_rect"):
            profile.launch_rect = None
        self.log_event("browser_opened", profile_id, f"Navegador aberto: {profile.name}")
        
        return driver
    
    def _inject_spoofing_scripts(self, driver, profile: BrowserProfile):
        """
        Injeta scripts de spoofing no navegador.
        
        Args:
            driver: Instância do driver
            profile: Perfil de navegação
        """
        fingerprint = profile.fingerprint
        
        # Obter script completo de spoofing
        spoof_script = self.fingerprint_generator.get_full_spoof_script(fingerprint)
        
        # Injetar script para ser executado em cada nova página
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": spoof_script}
            )
        except Exception as e:
            print(f"Aviso: Não foi possível injetar scripts via CDP: {e}")
            # Fallback: executar script diretamente
            try:
                driver.execute_script(spoof_script)
            except Exception as script_err:
                print(f"Aviso: Fallback de script também falhou: {script_err}")
        
        # Remover propriedade webdriver
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"}
            )
        except Exception as webdriver_err:
            print(f"Aviso: Não foi possível remover propriedade webdriver: {webdriver_err}")
    
    def _inject_advanced_antidetect(self, driver, profile: BrowserProfile):
        """
        Injeta scripts avançados de anti-detecção.
        Inclui spoofing de AudioContext, fontes e outras APIs.
        
        Args:
            driver: Instância do driver
            profile: Perfil de navegação
        """
        fingerprint = profile.fingerprint
        
        # Script avançado de anti-detecção
        advanced_script = '''
        // ===== ANTI-DETECÇÃO AVANÇADA =====
        
        // 1. Spoofing de AudioContext (evita fingerprint por áudio)
        (function() {
            const originalAudioContext = window.AudioContext || window.webkitAudioContext;
            if (originalAudioContext) {
                const originalCreateAnalyser = originalAudioContext.prototype.createAnalyser;
                const originalCreateOscillator = originalAudioContext.prototype.createOscillator;
                const originalCreateGain = originalAudioContext.prototype.createGain;
                const originalCreateDynamicsCompressor = originalAudioContext.prototype.createDynamicsCompressor;
                
                // Adicionar ruído aleatório aos dados de áudio
                const addNoise = (data) => {
                    for (let i = 0; i < data.length; i++) {
                        data[i] = data[i] + (Math.random() * 0.0001 - 0.00005);
                    }
                    return data;
                };
                
                // Override getFloatFrequencyData
                const originalGetFloatFrequencyData = AnalyserNode.prototype.getFloatFrequencyData;
                AnalyserNode.prototype.getFloatFrequencyData = function(array) {
                    originalGetFloatFrequencyData.call(this, array);
                    addNoise(array);
                };
                
                // Override getByteFrequencyData
                const originalGetByteFrequencyData = AnalyserNode.prototype.getByteFrequencyData;
                AnalyserNode.prototype.getByteFrequencyData = function(array) {
                    originalGetByteFrequencyData.call(this, array);
                    for (let i = 0; i < array.length; i++) {
                        array[i] = Math.max(0, Math.min(255, array[i] + Math.floor(Math.random() * 2 - 1)));
                    }
                };
            }
        })();
        
        // 2. Spoofing de Fontes do Sistema
        (function() {
            // Lista de fontes comuns brasileiras/portuguesas
            const fakeFonts = [
                'Arial', 'Arial Black', 'Calibri', 'Cambria', 'Comic Sans MS',
                'Courier New', 'Georgia', 'Impact', 'Lucida Console', 'Lucida Sans Unicode',
                'Microsoft Sans Serif', 'Palatino Linotype', 'Segoe UI', 'Tahoma',
                'Times New Roman', 'Trebuchet MS', 'Verdana'
            ];
            
            // Adicionar variação aleatória
            const randomFonts = fakeFonts.slice(0, Math.floor(Math.random() * 5) + 12);
            
            // Override para document.fonts
            if (document.fonts && document.fonts.check) {
                const originalCheck = document.fonts.check.bind(document.fonts);
                document.fonts.check = function(font) {
                    const fontName = font.split(' ').pop().replace(/["']/g, '');
                    if (randomFonts.includes(fontName)) {
                        return true;
                    }
                    return originalCheck(font);
                };
            }
        })();
        
        // 3. Spoofing de Hardware Concurrency
        (function() {
            const cores = ''' + str(fingerprint.get('hardware_concurrency', 8)) + ''';
            Object.defineProperty(navigator, 'hardwareConcurrency', {
                get: () => cores
            });
        })();
        
        // 4. Spoofing de Device Memory
        (function() {
            const memory = ''' + str(fingerprint.get('device_memory', 8)) + ''';
            Object.defineProperty(navigator, 'deviceMemory', {
                get: () => memory
            });
        })();
        
        // 5. Spoofing de Connection (Network Information API)
        (function() {
            if (navigator.connection) {
                Object.defineProperty(navigator.connection, 'effectiveType', {
                    get: () => '4g'
                });
                Object.defineProperty(navigator.connection, 'downlink', {
                    get: () => Math.random() * 5 + 5  // 5-10 Mbps
                });
                Object.defineProperty(navigator.connection, 'rtt', {
                    get: () => Math.floor(Math.random() * 50) + 50  // 50-100ms
                });
            }
        })();
        
        // 6. Spoofing de Battery API
        (function() {
            if (navigator.getBattery) {
                navigator.getBattery = () => Promise.resolve({
                    charging: Math.random() > 0.5,
                    chargingTime: Infinity,
                    dischargingTime: Math.floor(Math.random() * 10000) + 5000,
                    level: Math.random() * 0.5 + 0.5,  // 50-100%
                    addEventListener: () => {},
                    removeEventListener: () => {}
                });
            }
        })();
        
        // 7. Remover rastros de automação
        (function() {
            // Remover propriedades do Selenium/ChromeDriver
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            
            // Remover $cdc_ variables
            for (let prop in window) {
                if (prop.match(/[$]cdc_/)) {
                    delete window[prop];
                }
            }
            
            // Remover __webdriver_evaluate
            delete window.__webdriver_evaluate;
            delete window.__selenium_evaluate;
            delete window.__webdriver_script_function;
            delete window.__webdriver_script_func;
            delete window.__webdriver_script_fn;
            delete window.__fxdriver_evaluate;
            delete window.__driver_unwrapped;
            delete window.__webdriver_unwrapped;
            delete window.__driver_evaluate;
            delete window.__selenium_unwrapped;
            delete window.__fxdriver_unwrapped;
            
            // Remover document.$cdc_
            if (document) {
                for (let prop in document) {
                    if (prop.match(/[$]cdc_/)) {
                        delete document[prop];
                    }
                }
            }
        })();
        
        // 8. Spoofing de Permissions API
        (function() {
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = (parameters) => {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({ state: 'prompt', onchange: null });
                }
                return originalQuery(parameters);
            };
        })();
        
        // 9. Spoofing de WebGL Vendor/Renderer (mais robusto)
        (function() {
            const getParameterOriginal = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {  // UNMASKED_VENDOR_WEBGL
                    return 'Google Inc. (Intel)';
                }
                if (parameter === 37446) {  // UNMASKED_RENDERER_WEBGL
                    return 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                }
                return getParameterOriginal.call(this, parameter);
            };
            
            // Mesmo para WebGL2
            if (typeof WebGL2RenderingContext !== 'undefined') {
                const getParameter2Original = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Google Inc. (Intel)';
                    }
                    if (parameter === 37446) {
                        return 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)';
                    }
                    return getParameter2Original.call(this, parameter);
                };
            }
        })();
        
        console.log('[Anti-Detect] Scripts avançados injetados com sucesso!');
        ''';
        
        try:
            driver.execute_cdp_cmd(
                "Page.addScriptToEvaluateOnNewDocument",
                {"source": advanced_script}
            )
        except Exception as e:
            print(f"Aviso: Não foi possível injetar scripts avançados via CDP: {e}")
            try:
                driver.execute_script(advanced_script)
            except Exception as adv_err:
                print(f"Aviso: Fallback de script avançado também falhou: {adv_err}")
    
    def navigate_to(self, profile_id: str, url: str) -> bool:
        """
        Navega para uma URL com o navegador do perfil.
        
        Args:
            profile_id: ID do perfil
            url: URL para navegar
            
        Returns:
            True se navegou com sucesso
        """
        driver = self.active_browsers.get(profile_id)
        if not driver:
            return False
        
        try:
            url = self.normalize_navigation_target(url)
            driver.get(url)
            
            # Verificar auto-login
            profile = self.profiles.get(profile_id)
            if profile and profile.auto_login:
                self._try_auto_login(driver, url, profile.auto_login)
            
            return True
            
        except Exception as e:
            print(f"Erro ao navegar: {e}")
            return False
    
    def _try_auto_login(self, driver, current_url: str, auto_login: Dict):
        """
        Tenta fazer auto-login se a URL corresponder.
        
        Args:
            driver: Instância do driver
            current_url: URL atual
            auto_login: Configurações de auto-login
        """
        for url_pattern, credentials in auto_login.items():
            if url_pattern in current_url:
                try:
                    # Aguardar página carregar
                    time.sleep(2)
                    
                    # Tentar encontrar campos de login comuns
                    username_selectors = [
                        "input[type='email']",
                        "input[type='text'][name*='user']",
                        "input[type='text'][name*='login']",
                        "input[type='text'][name*='email']",
                        "input[id*='user']",
                        "input[id*='login']",
                        "input[id*='email']",
                        "#username",
                        "#email",
                        "#login",
                    ]
                    
                    password_selectors = [
                        "input[type='password']",
                        "input[name*='pass']",
                        "input[id*='pass']",
                        "#password",
                    ]
                    
                    # Tentar preencher username
                    username_filled = False
                    for selector in username_selectors:
                        try:
                            elem = driver.find_element(By.CSS_SELECTOR, selector)
                            if elem.is_displayed():
                                elem.clear()
                                elem.send_keys(credentials.get("username", ""))
                                username_filled = True
                                break
                        except (NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException):
                            continue
                    
                    # Tentar preencher password
                    password_filled = False
                    for selector in password_selectors:
                        try:
                            elem = driver.find_element(By.CSS_SELECTOR, selector)
                            if elem.is_displayed():
                                elem.clear()
                                elem.send_keys(credentials.get("password", ""))
                                password_filled = True
                                break
                        except (NoSuchElementException, ElementNotInteractableException, StaleElementReferenceException):
                            continue
                    
                    if username_filled and password_filled:
                        print(f"Auto-login preenchido para: {url_pattern}")
                        
                except Exception as e:
                    print(f"Erro no auto-login: {e}")

    def _attach_native_control_driver(self, profile_id: str):
        """Conecta o Selenium ao Chrome/Edge nativo aberto pelo app via porta local."""
        existing = self.native_control_drivers.get(profile_id)
        if existing:
            try:
                _ = existing.current_url
                return existing
            except Exception:
                self.native_control_drivers.pop(profile_id, None)

        port = self.active_debug_ports.get(profile_id)
        browser_name = self.active_native_browser_names.get(profile_id, "chrome")
        if not port or browser_name not in ("chrome", "edge"):
            return None

        last_error = None
        for _ in range(8):
            try:
                if browser_name == "edge":
                    options = webdriver.EdgeOptions()
                    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
                    driver = webdriver.Edge(options=options)
                else:
                    options = Options()
                    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{port}")
                    driver = webdriver.Chrome(options=options)
                self.native_control_drivers[profile_id] = driver
                return driver
            except Exception as e:
                last_error = e
                time.sleep(0.35)

        self.log_event("native_control_error", profile_id, str(last_error), "error")
        return None

    def detect_page_issue(self, profile_id: str) -> Dict:
        """Analisa a pagina aberta e traduz erros comuns para uma mensagem util."""
        active_ref = self.active_browsers.get(profile_id)
        if not active_ref or not self.is_browser_active(profile_id):
            return {
                "ok": False,
                "severity": "error",
                "code": "browser_closed",
                "title": "Navegador fechado",
                "message": "Abra o navegador deste perfil antes de diagnosticar a pagina.",
                "suggestions": ["Inicie o perfil e tente novamente."],
            }

        if self.is_native_browser(profile_id):
            driver = self._attach_native_control_driver(profile_id)
            if not driver:
                return {
                    "ok": False,
                    "severity": "error",
                    "code": "no_control",
                    "title": "Controle local indisponivel",
                    "message": "Feche este navegador e abra de novo pelo app para ativar o diagnostico.",
                    "suggestions": ["Use Chrome ou Edge aberto pelo Navegador Seguro."],
                }
        else:
            driver = active_ref

        if not hasattr(driver, "execute_script"):
            return {
                "ok": False,
                "severity": "error",
                "code": "unsupported",
                "title": "Diagnostico indisponivel",
                "message": "Este modo de navegador nao permite ler a pagina aberta.",
                "suggestions": ["Abra o perfil em Chrome ou Edge pelo app."],
            }

        script = """
function allElements(selector, root = document) {
  const found = [];
  function walk(node) {
    try { found.push(...Array.from(node.querySelectorAll(selector))); } catch (_) {}
    try {
      for (const el of Array.from(node.querySelectorAll("*"))) {
        if (el.shadowRoot) walk(el.shadowRoot);
      }
    } catch (_) {}
  }
  walk(root);
  return found;
}
const body = document.body ? document.body.innerText || "" : "";
const inputs = allElements("input, textarea, select")
  .filter(el => {
    const st = window.getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return !el.disabled && st.display !== "none" && st.visibility !== "hidden" && r.width > 2 && r.height > 2;
  })
  .map(el => ({
    tag: el.tagName,
    type: el.type || "",
    name: el.name || "",
    id: el.id || "",
    placeholder: el.placeholder || "",
    autocomplete: el.getAttribute("autocomplete") || "",
    aria: el.getAttribute("aria-label") || ""
  }))
  .slice(0, 80);
const buttons = allElements("button, [role='button'], input[type='submit']")
  .filter(el => {
    const st = window.getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return st.display !== "none" && st.visibility !== "hidden" && r.width > 2 && r.height > 2;
  })
  .map(el => (el.innerText || el.value || el.getAttribute("aria-label") || "").trim())
  .filter(Boolean)
  .slice(0, 40);
return {
  url: location.href,
  title: document.title || "",
  body: body.slice(0, 12000),
  bodyLength: body.length,
  inputCount: inputs.length,
  inputs,
  buttons
};
"""
        try:
            driver.switch_to.default_content()
        except Exception:
            pass

        try:
            info = driver.execute_script(script) or {}
        except Exception as e:
            self.log_event("page_detector_error", profile_id, str(e), "error")
            return {
                "ok": False,
                "severity": "error",
                "code": "read_error",
                "title": "Nao consegui ler a pagina",
                "message": f"Erro tecnico: {e}",
                "suggestions": ["Atualize a pagina e rode o diagnostico novamente."],
            }

        url = str(info.get("url") or "")
        title = str(info.get("title") or "")
        body = str(info.get("body") or "")
        haystack = f"{url}\n{title}\n{body}".lower()
        input_count = int(info.get("inputCount") or 0)
        body_length = int(info.get("bodyLength") or 0)
        site = "geral"
        if "crunchyroll.com" in url:
            site = "crunchyroll"
        elif "paramountplus.com" in url:
            site = "paramount"
        elif "hbomax.com" in url or "max.com" in url:
            site = "hbo"
        elif "primevideo.com" in url or "amazon." in url:
            site = "amazon"

        result = {
            "ok": True,
            "severity": "success",
            "code": "ok",
            "title": "Pagina parece normal",
            "message": "Nao encontrei bloqueio ou erro claro na pagina aberta.",
            "url": url,
            "site": site,
            "page_title": title,
            "input_count": input_count,
            "body_length": body_length,
            "suggestions": [
                "Se algum campo nao preencher, tente clicar nele uma vez e usar Preencher pagina aberta.",
                "Se o site ficar estranho, atualize a pagina antes de repetir a acao.",
            ],
        }

        def apply(code, severity, title_text, message, suggestions):
            result.update({
                "severity": severity,
                "code": code,
                "title": title_text,
                "message": message,
                "suggestions": suggestions,
            })

        if any(token in haystack for token in ["403", "forbidden", "access denied", "error 54113", "varnish", "cache-for"]):
            apply(
                "blocked_403",
                "warning",
                "Bloqueio 403 detectado",
                "O site recusou a pagina atual antes de carregar o fluxo normal.",
                [
                    "Na Paramount, abra pelo favorito 'paramount login' em vez da URL travada.",
                    "Use fingerprint Streaming ou Leve; fingerprint agressivo pode piorar streaming.",
                    "Limpe dados deste perfil se ele ficou preso em cache de erro.",
                    "Troque rede/proxy se o mesmo erro continuar em perfil limpo.",
                ],
            )
        elif any(token in haystack for token in [
            "captcha", "recaptcha", "hcaptcha", "verify you are human", "verifique que voce",
            "verifique se voce", "verificacao humana", "verificação humana",
        ]):
            apply(
                "captcha",
                "warning",
                "Verificacao humana detectada",
                "A pagina parece estar pedindo captcha ou verificacao manual.",
                [
                    "Resolva manualmente no navegador.",
                    "Evite abrir muitos perfis ao mesmo tempo nesse site.",
                    "Use rede estavel e fingerprint Normal/Leve.",
                ],
            )
        elif any(token in haystack for token in [
            "verify you're not a bot", "verify you are not a bot", "are you human",
            "are you a human", "prove you are human", "checking your browser",
            "checking if the site connection is secure", "just a moment",
            "security check", "unusual traffic", "automated traffic",
            "bot detection", "robot check", "verificacao de robo",
            "verificação de robô", "verifique que nao e um robo", "verifique que não é um robô",
            "executando verificacao de seguranca", "executando verificação de segurança",
            "confirme que e humano", "confirme que é humano", "ray id", "turnstile",
            "cloudflare", "access has been restricted",
        ]):
            suggestions = [
                "Resolva a verificação manualmente no navegador quando ela aparecer.",
                "Use modo Streaming ou Normal/Leve; evite fingerprint Forte nesse site.",
                "Evite proxy/VPN ruim e muitas tentativas seguidas no mesmo perfil.",
                "Mantenha cookies salvos para o site lembrar que o perfil ja foi verificado.",
            ]
            if site == "crunchyroll":
                suggestions.insert(0, "Para Crunchyroll, use o favorito fixado e um perfil com cookies persistentes.")
                suggestions.insert(1, "Se aparecer o tradutor/extensão por cima, feche o pop-up e tente marcar a verificação manualmente.")
                suggestions.append("Se marcar e voltar para a mesma tela em loop, use Reset limpo do site neste perfil.")
            loop_tokens = (
                "um momento", "just a moment", "ray id",
                "executando verificacao de seguranca", "executando verificação de segurança",
                "confirme que e humano", "confirme que é humano",
            )
            loop_detected = site == "crunchyroll" and any(token in haystack for token in loop_tokens)
            if loop_detected:
                suggestions.insert(0, "Loop de verificação detectado: não feche o navegador antes de tentar 'Tentar sem fechar'.")
                suggestions.append("Se continuar repetindo, aguarde alguns minutos antes de tentar no mesmo perfil/rede.")
            apply(
                "robot_loop" if loop_detected else "robot_check",
                "warning",
                "Verificacao em loop detectada" if loop_detected else "Verificacao de robo detectada",
                "O site esta repetindo a checagem de seguranca antes de liberar a pagina normal." if loop_detected else "O site esta pedindo uma checagem de seguranca antes de liberar a pagina normal.",
                suggestions,
            )
        elif any(token in haystack for token in ["err_timed_out", "err_connection", "dns_probe", "this site can't be reached", "nao e possivel acessar esse site", "não é possível acessar esse site"]):
            apply(
                "network_error",
                "error",
                "Erro de rede detectado",
                "A pagina nao conseguiu carregar por DNS, conexao ou proxy.",
                [
                    "Teste sem proxy neste perfil.",
                    "Limpe DNS pela ferramenta Desempenho.",
                    "Verifique se Chrome/Edge tem internet fora do app.",
                ],
            )
        elif any(token in haystack for token in ["payment declined", "pagamento recusado", "cartao recusado", "cartão recusado", "nao autorizado", "não autorizado"]):
            apply(
                "payment_error",
                "warning",
                "Erro de pagamento detectado",
                "A pagina carregou, mas retornou uma recusa ou falha no pagamento.",
                [
                    "Confira os campos obrigatorios antes de tentar de novo.",
                    "Rode o preenchimento de endereco e revise o estado/UF.",
                    "Salve uma observacao no perfil para lembrar o resultado.",
                ],
            )
        elif any(token in haystack for token in ["senha incorreta", "invalid password", "incorrect password", "email ou senha", "login failed"]):
            apply(
                "login_error",
                "warning",
                "Erro de login detectado",
                "O site parece ter recusado usuario, email ou senha.",
                [
                    "Confira a conta vinculada ao perfil.",
                    "Atualize o auto-login salvo se a senha mudou.",
                    "Tente login manual uma vez e salve os dados do Chrome.",
                ],
            )
        elif body_length < 80 and input_count == 0:
            apply(
                "blank_page",
                "warning",
                "Pagina vazia ou incompleta",
                "A pagina carregou pouco conteudo e nao exibiu campos visiveis.",
                [
                    "Atualize a pagina.",
                    "Aguarde alguns segundos e rode o diagnostico de novo.",
                    "Se continuar, tente outro navegador no perfil.",
                ],
            )

        self.log_event("page_detector", profile_id, f"{result['code']}: {result['title']}", result["severity"])
        return result

    def _driver_visible(self, driver, element) -> bool:
        try:
            return bool(driver.execute_script(
                """
                const el = arguments[0];
                if (!el || !el.getBoundingClientRect) return false;
                const st = window.getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return st.display !== "none" && st.visibility !== "hidden" &&
                       r.width > 2 && r.height > 2 && !el.disabled && !el.readOnly;
                """,
                element,
            ))
        except Exception:
            try:
                return element.is_displayed() and element.is_enabled()
            except Exception:
                return False

    def _driver_physical_click(self, driver, element) -> bool:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", element)
            time.sleep(0.03)
            ActionChains(driver).move_to_element(element).pause(0.03).click().perform()
            return True
        except Exception:
            try:
                element.click()
                return True
            except Exception:
                try:
                    driver.execute_script(
                        """
                        const el = arguments[0];
                        el.focus?.();
                        for (const type of ["pointerdown","mousedown","mouseup","pointerup","click"]) {
                          try { el.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true, view:window})); } catch (_) {}
                        }
                        try { el.click?.(); } catch (_) {}
                        """,
                        element,
                    )
                    return True
                except Exception:
                    return False

    def _driver_physical_type(self, driver, element, value: str) -> bool:
        value = str(value or "")
        if not value or not self._driver_visible(driver, element):
            return False
        if not self._driver_physical_click(driver, element):
            return False
        try:
            element.send_keys(Keys.CONTROL, "a")
            element.send_keys(Keys.BACKSPACE)
            element.send_keys(value)
        except Exception:
            try:
                element.clear()
                element.send_keys(value)
            except Exception:
                return False
        try:
            driver.execute_script(
                """
                const el = arguments[0];
                for (const type of ["input", "change", "keyup", "blur"]) {
                  try { el.dispatchEvent(new Event(type, {bubbles:true})); } catch (_) {}
                }
                """,
                element,
            )
        except Exception:
            pass
        return True

    @staticmethod
    def _driver_clean_text(value) -> str:
        text = unicodedata.normalize("NFD", str(value or ""))
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in text).split())

    def _field_text_for_element(self, element) -> str:
        attrs = []
        for attr in ("name", "id", "placeholder", "aria-label", "autocomplete", "data-testid", "data-test", "title"):
            try:
                attrs.append(element.get_attribute(attr) or "")
            except Exception:
                pass
        try:
            attrs.append(element.text or "")
        except Exception:
            pass
        return self._driver_clean_text(" ".join(attrs))

    def _fill_field_physical(self, driver, selectors: List[str], keywords: List[str], value: str, blocked: List[str] = None) -> Dict:
        blocked = blocked or []
        candidates = []
        for selector in selectors:
            try:
                candidates.extend(driver.find_elements(By.CSS_SELECTOR, selector))
            except Exception:
                continue
        if not candidates:
            try:
                all_fields = driver.find_elements(By.CSS_SELECTOR, "input, textarea")
            except Exception:
                all_fields = []
            clean_keywords = [self._driver_clean_text(word) for word in keywords]
            clean_blocked = [self._driver_clean_text(word) for word in blocked]
            for element in all_fields:
                text = self._field_text_for_element(element)
                if clean_blocked and any(word and word in text for word in clean_blocked):
                    continue
                if any(word and word in text for word in clean_keywords):
                    candidates.append(element)
        for element in candidates:
            if self._driver_physical_type(driver, element, value):
                return {"ok": True, "field": self._field_text_for_element(element)[:60]}
        return {"ok": False, "field": ""}

    def _fill_paramount_payment_physical(self, driver, address_data: Dict) -> Dict:
        try:
            current_url = driver.execute_script("return location.href") or ""
        except Exception:
            current_url = ""
        if "paramountplus.com" not in current_url.lower():
            return {"filled": 0, "fields": []}

        fields = []
        blocked = ["cartao", "card", "cvv", "cvc", "validade", "expir", "month", "year", "senha", "password", "email"]
        tasks = [
            (
                "primeiro_nome",
                ["#first_name", "input[name='first_name']", "input[data-ci='first_name']", ".qt-first_nametxtfield"],
                ["primeiro nome", "first name", "first_name", "given name"],
                address_data.get("firstName"),
            ),
            (
                "sobrenome",
                ["#last_name", "input[name='last_name']", "input[data-ci='last_name']", ".qt-last_nametxtfield"],
                ["sobrenome", "last name", "last_name", "family name"],
                address_data.get("lastName"),
            ),
            (
                "rua",
                ["#address1", "input[name='address1']", "input[data-ci='address1']", ".qt-addresstxtfield", "input[autocomplete='address-line1']", "input[name='addressLine1']", "input[id='addressLine1']"],
                ["endereco", "logradouro", "address line 1", "rua", "street"],
                address_data.get("logradouro") or address_data.get("rua"),
            ),
            (
                "cidade",
                ["#city", "input[name='city']", "input[data-ci='city']", ".qt-citytxtfield", "input[autocomplete='address-level2']"],
                ["cidade", "city", "locality"],
                address_data.get("cidade"),
            ),
            (
                "cep",
                ["#postal_code", "input[name='postal_code']", "input[data-ci='postal_code']", ".qt-ziptxtfield", "input[autocomplete='postal-code']", "input[name='postalCode']", "input[id='postalCode']"],
                ["cep", "postal", "zip"],
                address_data.get("cep"),
            ),
            (
                "cpf",
                [
                    "#tax_identifier",
                    "input[name='tax_identifier']",
                    "input[data-recurly='tax_identifier']",
                    "input[data-ci='tax_identifier']",
                    ".qt-tax_identifiertxtfield",
                    "input[name='cpf']",
                    "input[id='cpf']",
                    "input[placeholder='CPF']",
                ],
                ["cpf", "documento", "tax", "tax identifier", "tax_identifier"],
                address_data.get("cpf") or address_data.get("cpfDigits") or address_data.get("documento"),
            ),
        ]
        for name, selectors, keywords, value in tasks:
            if not value:
                continue
            result = self._fill_field_physical(driver, selectors, keywords, value, blocked)
            if result.get("ok"):
                fields.append(name)

        state_result = self._fill_paramount_state_dropdown(driver, address_data)
        if state_result.get("filled"):
            fields.extend(state_result.get("fields", []) or ["estado"])

        return {"filled": len(fields), "fields": fields}

    def _fill_paramount_state_dropdown_fast(self, driver, desired_state: str, desired_uf: str) -> Dict:
        """Seleciona Estado na Paramount sem varrer a pagina inteira."""
        script = r"""
const desiredState = (arguments[0] || "").toString();
const desiredUf = (arguments[1] || "").toString().toUpperCase();
const done = arguments[arguments.length - 1];
const UF_TO_STATE = {
  AC:"Acre", AL:"Alagoas", AP:"Amapa", AM:"Amazonas", BA:"Bahia", CE:"Ceara",
  DF:"Distrito Federal", ES:"Espirito Santo", GO:"Goias", MA:"Maranhao",
  MT:"Mato Grosso", MS:"Mato Grosso do Sul", MG:"Minas Gerais", PA:"Para",
  PB:"Paraiba", PR:"Parana", PE:"Pernambuco", PI:"Piaui", RJ:"Rio de Janeiro",
  RN:"Rio Grande do Norte", RS:"Rio Grande do Sul", RO:"Rondonia", RR:"Roraima",
  SC:"Santa Catarina", SP:"Sao Paulo", SE:"Sergipe", TO:"Tocantins"
};
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}
function compact(s) { return clean(s).replace(/[^a-z0-9]/g, ""); }
function visible(el) {
  if (!el || !el.getBoundingClientRect) return false;
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 2 && r.height > 2;
}
function textOf(el) {
  return clean([
    el.innerText, el.textContent, el.value, el.placeholder,
    el.getAttribute("aria-label"), el.getAttribute("data-value"),
    el.getAttribute("value"), el.getAttribute("title")
  ].filter(Boolean).join(" "));
}
function fire(el) {
  if (!el || !visible(el)) return false;
  try { el.scrollIntoView({block:"center", inline:"center"}); } catch (_) {}
  try { el.focus?.(); } catch (_) {}
  for (const type of ["pointerdown", "mousedown", "mouseup", "pointerup", "click"]) {
    try { el.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true, view:window})); } catch (_) {}
  }
  try { el.click?.(); } catch (_) {}
  return true;
}
function setNativeValue(el, value) {
  if (!el || !value) return false;
  const proto = el instanceof HTMLSelectElement ? HTMLSelectElement.prototype :
                el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype :
                HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set || Object.getOwnPropertyDescriptor(el.__proto__, "value")?.set;
  if (setter) setter.call(el, value);
  else el.value = value;
  for (const type of ["input", "change", "blur"]) el.dispatchEvent(new Event(type, {bubbles:true}));
  return true;
}
const stateName = desiredState || UF_TO_STATE[desiredUf] || "";
const stateClean = clean(stateName);
const ufClean = clean(desiredUf);
const mappedClean = clean(UF_TO_STATE[desiredUf]);
const stateCompact = compact(stateName);
const ufCompact = compact(desiredUf);
const mappedCompact = compact(UF_TO_STATE[desiredUf]);
const wanted = [stateClean, ufClean, mappedClean].filter(Boolean);
if (!wanted.length) {
  done({filled:0, fields:[]});
  return;
}
function matchesText(raw) {
  const tx = clean(raw);
  const cx = compact(raw);
  if (!tx || tx.length > 80) return false;
  if (/^(estado|state|selecione|select)$/.test(tx)) return false;
  if (stateClean && (tx === stateClean || cx === stateCompact || tx.includes(stateClean + " "))) return true;
  if (mappedClean && (tx === mappedClean || cx === mappedCompact || tx.includes(mappedClean + " "))) return true;
  if (ufClean && (tx === ufClean || cx === ufCompact || tx.endsWith(" " + ufClean) || cx.endsWith(ufCompact))) return true;
  return false;
}
function optionMatches(opt) {
  return matchesText([opt.innerText, opt.textContent, opt.value, opt.getAttribute("data-value"), opt.getAttribute("aria-label")].filter(Boolean).join(" "));
}
function dispatchValueEvents(el) {
  if (!el) return;
  for (const type of ["input", "change", "keyup", "blur"]) {
    try { el.dispatchEvent(new Event(type, {bubbles:true})); } catch (_) {}
  }
}
function clickEvenHidden(el) {
  if (!el) return false;
  for (const type of ["pointerdown", "mousedown", "mouseup", "pointerup", "click"]) {
    try { el.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true, view:window})); } catch (_) {}
  }
  try { el.click?.(); } catch (_) {}
  return true;
}
function forceParamountNativeSelect() {
  const wrapper = document.querySelector("#custom-selector-state");
  const sel = document.querySelector("#state, #custom-selector-state select, select[data-recurly='state']");
  if (!sel) return false;
  const option = Array.from(sel.options || []).find(optionMatches);
  if (!option) return false;
  const label = (option.textContent || option.getAttribute("aria-label") || stateName || desiredUf || "").trim();
  setNativeValue(sel, option.value);
  sel.value = option.value;
  option.selected = true;
  dispatchValueEvents(sel);

  const selected = document.querySelector("#custom-selector-state-selected, [id='custom-selector-state-selected']");
  if (selected) {
    selected.textContent = label;
    selected.setAttribute("aria-label", label);
    dispatchValueEvents(selected);
  }
  if (wrapper) {
    wrapper.classList.remove("error");
    wrapper.classList.add("initialized");
    const labelEl = wrapper.querySelector("label");
    if (labelEl) labelEl.classList.add("floated");
  }
  const targetValue = (option.value || "").toString();
  const targetLi = Array.from(document.querySelectorAll("#custom-selector-state .select-option, #custom-selector-state li"))
    .find(el => (el.getAttribute("value") || "").toUpperCase() === targetValue.toUpperCase() || optionMatches(el));
  clickEvenHidden(targetLi);
  setNativeValue(sel, option.value);
  sel.value = option.value;
  option.selected = true;
  dispatchValueEvents(sel);
  if (selected) selected.textContent = label;
  return true;
}

if (forceParamountNativeSelect()) {
  setTimeout(() => done({filled:1, fields:["paramount-estado-native-direto"]}), 80);
  return;
}

for (const sel of Array.from(document.querySelectorAll("select")).filter(visible)) {
  const stateLike = /estado|state|uf|province|address-level1/i.test([
    sel.name, sel.id, sel.getAttribute("aria-label"), sel.getAttribute("autocomplete")
  ].filter(Boolean).join(" "));
  for (const opt of Array.from(sel.options || [])) {
    if ((stateLike || optionMatches(opt)) && optionMatches(opt)) {
      sel.value = opt.value;
      opt.selected = true;
      for (const type of ["input", "change", "blur"]) sel.dispatchEvent(new Event(type, {bubbles:true}));
      done({filled:1, fields:["paramount-estado-select"]});
      return;
    }
  }
}

const hiddenState = document.querySelector("input[name*='state' i], input[id*='state' i], input[name*='province' i], input[id*='province' i]");
if (hiddenState && !visible(hiddenState)) {
  setNativeValue(hiddenState, desiredUf || stateName);
}

const selected = document.querySelector("#custom-selector-state-selected, [id='custom-selector-state-selected']");
if (selected && visible(selected) && matchesText(textOf(selected))) {
  done({filled:1, fields:["paramount-estado-ja-selecionado"]});
  return;
}

const trigger = selected ||
  document.querySelector("#custom-selector-state .select-selected, [id*='custom-selector-state'] .select-selected") ||
  document.querySelector("#custom-selector-state, [id*='custom-selector-state']");
if (!fire(trigger)) {
  done({filled:0, fields:[]});
  return;
}

setTimeout(() => {
  const optionSelectors = [
    "#custom-selector-state .select-items div",
    "[id*='custom-selector-state'] [role='option']",
    "[id*='custom-selector-state'] [role='menuitem']",
    "[id*='custom-selector-state'] li",
    ".select-items div",
    ".select-option",
    ".select-item",
    "[role='listbox'] [role='option']",
    "[role='option']",
    "[data-value]"
  ].join(",");
  const options = Array.from(document.querySelectorAll(optionSelectors)).filter(visible);
  for (const opt of options) {
    if (optionMatches(opt) && fire(opt)) {
      done({filled:1, fields:["paramount-estado-rapido"]});
      return;
    }
  }
  done({filled:0, fields:[]});
}, 320);
"""
        try:
            result = driver.execute_async_script(script, desired_state, desired_uf) or {}
            if result.get("filled"):
                return result
        except Exception as exc:
            self.log_event("paramount_state_fast_skip", "global", str(exc), "warning")

        def clean(value) -> str:
            text = unicodedata.normalize("NFD", str(value or ""))
            text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
            return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in text).split())

        wanted = clean(desired_state or desired_uf)
        try:
            triggers = driver.find_elements(
                By.CSS_SELECTOR,
                "#custom-selector-state-selected, #custom-selector-state .select-selected, [id*='custom-selector-state']",
            )
        except Exception:
            triggers = []
        for trigger in triggers[:3]:
            try:
                if not self._driver_visible(driver, trigger):
                    continue
                if not self._driver_physical_click(driver, trigger):
                    continue
                # Nao usa teclado/Enter aqui: o componente da Paramount pode
                # aceitar Enter como "primeira opcao" e selecionar Acre.
                continue
            except Exception:
                continue
        return {"filled": 0, "fields": []}

    def _fill_paramount_state_dropdown(self, driver, address_data: Dict) -> Dict:
        """Fallback específico para o dropdown Estado da Paramount."""
        try:
            current_url = driver.execute_script("return location.href") or ""
        except Exception:
            current_url = ""
        if "paramountplus.com" not in current_url.lower():
            return {"filled": 0, "fields": []}

        def clean(value) -> str:
            text = unicodedata.normalize("NFD", str(value or ""))
            text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
            return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in text).split())

        desired_state = str(address_data.get("estado") or "").strip()
        desired_uf = str(address_data.get("uf") or "").strip().upper()
        desired_state_clean = clean(desired_state)
        desired_uf_clean = clean(desired_uf)
        if not desired_state_clean and not desired_uf_clean:
            return {"filled": 0, "fields": []}

        return self._fill_paramount_state_dropdown_fast(driver, desired_state, desired_uf)

        def selenium_option_matches(element) -> bool:
            text = clean(element.text or element.get_attribute("textContent") or "")
            value = clean(
                element.get_attribute("value")
                or element.get_attribute("data-value")
                or element.get_attribute("aria-label")
                or element.get_attribute("id")
                or ""
            )
            hay = " ".join(part for part in [text, value] if part)
            if not hay or len(hay) > 120:
                return False
            if desired_state_clean and (hay == desired_state_clean or desired_state_clean in hay):
                return True
            if desired_uf_clean and (hay == desired_uf_clean or hay.endswith(f" {desired_uf_clean}") or f" {desired_uf_clean} " in f" {hay} "):
                return True
            return False

        physical_triggers = [
            "#custom-selector-state-selected",
            "[id='custom-selector-state-selected']",
            "#custom-selector-state",
            "[id*='custom-selector-state']",
            ".select-selected",
            "[aria-label*='Estado']",
            "[role='combobox']",
        ]
        physical_options = [
            "[role='option']",
            "[role='menuitem']",
            "[aria-selected]",
            ".select-items div",
            ".select-item",
            ".select-option",
            "li",
            "button",
            "div",
            "span",
        ]
        for trigger_selector in physical_triggers:
            try:
                triggers = driver.find_elements(By.CSS_SELECTOR, trigger_selector)
            except Exception:
                triggers = []
            for trigger in triggers:
                if not self._driver_visible(driver, trigger):
                    continue
                if not self._driver_physical_click(driver, trigger):
                    continue
                time.sleep(0.18)
                for opt_selector in physical_options:
                    try:
                        options = driver.find_elements(By.CSS_SELECTOR, opt_selector)
                    except Exception:
                        options = []
                    for option in options:
                        try:
                            if self._driver_visible(driver, option) and selenium_option_matches(option) and self._driver_physical_click(driver, option):
                                return {"filled": 1, "fields": ["paramount-estado-fisico"]}
                        except Exception:
                            continue
                # Nao usa teclado/Enter aqui: o componente da Paramount pode
                # aceitar Enter como "primeira opcao" e selecionar Acre.
                continue

        paramount_custom_script = r"""
const address = arguments[0] || {};
const done = arguments[arguments.length - 1];
const UF_TO_STATE = {
  AC:"Acre", AL:"Alagoas", AP:"Amapa", AM:"Amazonas", BA:"Bahia", CE:"Ceara",
  DF:"Distrito Federal", ES:"Espirito Santo", GO:"Goias", MA:"Maranhao",
  MT:"Mato Grosso", MS:"Mato Grosso do Sul", MG:"Minas Gerais", PA:"Para",
  PB:"Paraiba", PR:"Parana", PE:"Pernambuco", PI:"Piaui", RJ:"Rio de Janeiro",
  RN:"Rio Grande do Norte", RS:"Rio Grande do Sul", RO:"Rondonia", RR:"Roraima",
  SC:"Santa Catarina", SP:"Sao Paulo", SE:"Sergipe", TO:"Tocantins"
};
function clean(s) {
  return (s || "")
    .toString()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}
function compact(s) {
  return clean(s).replace(/[^a-z0-9]/g, "");
}
function visible(el) {
  if (!el || !el.getBoundingClientRect) return false;
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 2 && r.height > 2;
}
function all(selector) {
  const out = [];
  function walk(root) {
    try { out.push(...Array.from(root.querySelectorAll(selector))); } catch (_) {}
    try {
      for (const el of Array.from(root.querySelectorAll("*"))) {
        if (el.shadowRoot) walk(el.shadowRoot);
      }
    } catch (_) {}
  }
  walk(document);
  return out;
}
function textOf(el) {
  return clean([
    el.innerText, el.textContent, el.value, el.placeholder,
    el.getAttribute("aria-label"), el.getAttribute("data-value"),
    el.getAttribute("value"), el.getAttribute("title"), el.id, el.name
  ].filter(Boolean).join(" "));
}
function fire(el) {
  if (!el || !visible(el)) return false;
  try { el.scrollIntoView({block:"center", inline:"center"}); } catch (_) {}
  try { el.focus?.(); } catch (_) {}
  for (const type of ["pointerdown", "mousedown", "mouseup", "pointerup", "click"]) {
    try { el.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true, view:window})); } catch (_) {}
  }
  try { el.click?.(); } catch (_) {}
  return true;
}
const uf = (address.uf || "").toString().trim().toUpperCase();
const state = address.estado || address.state || UF_TO_STATE[uf] || "";
const wanted = [state, uf, UF_TO_STATE[uf]].map(clean).filter(Boolean);
const wantedCompact = [state, uf, UF_TO_STATE[uf]].map(compact).filter(Boolean);
if (!wanted.length) {
  done({filled:0, fields:[]});
  return;
}
function matches(el) {
  const tx = textOf(el);
  const cx = compact(tx);
  if (!tx || tx.length > 90) return false;
  if (/estado|state|selecione|select/.test(tx) && tx.split(" ").length <= 3) return false;
  return wanted.some(w => tx === w || tx.includes(w) || tx.endsWith(" " + w)) ||
         wantedCompact.some(w => cx === w || cx.includes(w) || cx.endsWith(w));
}
function selectedAlready() {
  const selected = all("#custom-selector-state-selected, [id*='custom-selector-state-selected'], .select-selected")
    .filter(visible);
  return selected.some(el => matches(el));
}
if (selectedAlready()) {
  done({filled:1, fields:["paramount-estado-ja-selecionado"]});
  return;
}
const triggerSelectors = [
  "#custom-selector-state-selected",
  "[id='custom-selector-state-selected']",
  "#custom-selector-state",
  "[id*='custom-selector-state']",
  ".select-selected",
  "[aria-label*='Estado' i]",
  "[role='combobox']"
];
let clicked = false;
for (const selector of triggerSelectors) {
  const elements = all(selector).filter(visible);
  for (const el of elements) {
    const candidates = [
      el,
      el.closest("[role='combobox']"),
      el.closest("[aria-haspopup]"),
      el.closest("button"),
      el.parentElement,
      el.parentElement?.parentElement,
    ].filter(Boolean);
    for (const candidate of candidates) {
      const tx = textOf(candidate);
      if (candidate !== el && tx.length > 120 && !/estado|state/.test(tx)) continue;
      if (fire(candidate)) {
        clicked = true;
        break;
      }
    }
    if (clicked) break;
  }
  if (clicked) break;
}
setTimeout(() => {
  const optionSelectors = [
    "[role='option']", "[role='menuitem']", "[aria-selected]",
    ".select-items div", ".select-item", ".select-option",
    "[class*='option']", "[class*='Option']", "li", "button", "div", "span"
  ].join(",");
  const options = all(optionSelectors).filter(visible).filter(matches);
  for (const opt of options) {
    if (fire(opt)) {
      setTimeout(() => {
        done({filled:1, fields:["paramount-estado-custom-exato"]});
      }, 40);
      return;
    }
  }
  done({filled:0, fields: clicked ? ["paramount-estado-aberto-sem-match"] : []});
}, clicked ? 320 : 80);
"""
        try:
            paramount_custom_result = driver.execute_async_script(
                paramount_custom_script,
                {
                    "estado": desired_state,
                    "state": desired_state,
                    "uf": desired_uf,
                },
            ) or {}
            if paramount_custom_result.get("filled"):
                return paramount_custom_result
        except Exception:
            pass

        def option_matches(element) -> bool:
            text = clean(element.text or element.get_attribute("textContent") or "")
            value = clean(element.get_attribute("value") or element.get_attribute("aria-label") or "")
            hay = " ".join(part for part in [text, value] if part)
            if not hay:
                return False
            if desired_state_clean and (hay == desired_state_clean or desired_state_clean in hay):
                return True
            if desired_uf_clean and (hay == desired_uf_clean or hay.endswith(f" {desired_uf_clean}")):
                return True
            return False

        dropdown_selectors = [
            "#custom-selector-state-selected",
            "#custom-selector-state",
            "[id='custom-selector-state-selected']",
            "[id*='custom-selector-state']",
            ".select-selected",
            "[data-testid*='state']",
            "[data-test*='state']",
            "[aria-label*='Estado']",
            "[aria-label*='State']",
            "[placeholder*='Estado']",
            "[role='combobox']",
        ]
        option_selectors = [
            "[role='option']",
            "ul[role='listbox'] li",
            "li",
            "button",
            "div[class*='option']",
            "div[class*='Option']",
            "span",
        ]

        def click_element(element) -> bool:
            try:
                if not element.is_displayed():
                    return False
                driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", element)
                time.sleep(0.05)
                try:
                    element.click()
                except Exception:
                    driver.execute_script("arguments[0].click();", element)
                return True
            except Exception:
                return False

        custom_script = r"""
const address = arguments[0] || {};
const done = arguments[arguments.length - 1];
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}
function visible(el) {
  if (!el || !el.getBoundingClientRect) return false;
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 2 && r.height > 2;
}
function all(selector) {
  const out = [];
  function walk(root) {
    try { out.push(...Array.from(root.querySelectorAll(selector))); } catch (_) {}
    try {
      for (const el of Array.from(root.querySelectorAll("*"))) {
        if (el.shadowRoot) walk(el.shadowRoot);
      }
    } catch (_) {}
  }
  walk(document);
  return out;
}
function textOf(el) {
  return clean([
    el.innerText, el.textContent, el.value,
    el.getAttribute("aria-label"), el.getAttribute("data-value"),
    el.getAttribute("value"), el.getAttribute("title")
  ].filter(Boolean).join(" "));
}
function fire(el) {
  if (!visible(el)) return false;
  el.scrollIntoView({block:"center", inline:"center"});
  el.focus?.();
  for (const type of ["pointerdown", "mousedown", "mouseup", "pointerup", "click"]) {
    try { el.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true, view:window})); } catch (_) {}
  }
  try { el.click?.(); } catch (_) {}
  return true;
}
const wantedState = clean(address.estado || address.state || "");
const wantedUf = clean(address.uf || "");
const wanted = [wantedState, wantedUf].filter(Boolean);
if (!wanted.length) {
  done({filled:0, fields:[]});
  return;
}
const triggers = [
  "#custom-selector-state-selected",
  "#custom-selector-state",
  "[id='custom-selector-state-selected']",
  "[id*='custom-selector-state']",
  ".select-selected",
  "[aria-label*='Estado' i]",
  "[role='combobox']"
];
let clickedTrigger = false;
for (const selector of triggers) {
  for (const el of all(selector).filter(visible)) {
    const target = el.closest("[role='combobox'], .custom-selector, .select, button, div") || el;
    if (fire(target) || fire(el)) {
      clickedTrigger = true;
      break;
    }
  }
  if (clickedTrigger) break;
}
setTimeout(() => {
  const optionSelectors = [
    "[role='option']", "[role='menuitem']", "[aria-selected]",
    ".select-items div", ".select-item", ".select-option",
    "li", "button", "div", "span"
  ].join(",");
  const options = all(optionSelectors).filter(visible);
  for (const opt of options) {
    const txt = textOf(opt);
    if (!txt || txt.length > 90 || /estado|selecione/.test(txt)) continue;
    const match = wanted.some(w => txt === w || txt.includes(w) || txt.endsWith(" " + w));
    if (match && fire(opt)) {
      done({filled:1, fields:["paramount-estado-custom"]});
      return;
    }
  }
  done({filled:0, fields: clickedTrigger ? ["paramount-estado-aberto-sem-opcao"] : []});
}, 280);
"""
        try:
            custom_result = driver.execute_async_script(
                custom_script,
                {
                    "estado": desired_state,
                    "state": desired_state,
                    "uf": desired_uf,
                },
            ) or {}
            if custom_result.get("filled"):
                return custom_result
        except Exception as exc:
            self.log_event("paramount_state_custom_skip", "global", str(exc), "warning")

        for selector in dropdown_selectors:
            try:
                candidates = driver.find_elements(By.CSS_SELECTOR, selector)
            except Exception:
                candidates = []
            for dropdown in candidates:
                if not click_element(dropdown):
                    continue
                time.sleep(0.18)
                for opt_selector in option_selectors:
                    try:
                        options = driver.find_elements(By.CSS_SELECTOR, opt_selector)
                    except Exception:
                        options = []
                    for option in options:
                        try:
                            if option.is_displayed() and option_matches(option) and click_element(option):
                                return {"filled": 1, "fields": ["paramount-estado-dropdown"]}
                        except Exception:
                            continue
                # Evita ENTER no dropdown da Paramount: em alguns casos ele
                # escolhe a primeira opcao (Acre) em vez do estado real.
                continue

        return {"filled": 0, "fields": []}

    def fill_address_fields(self, profile_id: str, address_data: Dict) -> Dict:
        """
        Preenche campos de endereço na página aberta do perfil.

        Funciona em Selenium e também em Chrome/Edge nativo quando o navegador
        foi aberto pelo app com porta local de controle.
        """
        if not address_data:
            return {"ok": False, "filled": 0, "message": "Nenhum endereço salvo no perfil."}

        active_ref = self.active_browsers.get(profile_id)
        if not active_ref or not self.is_browser_active(profile_id):
            return {"ok": False, "filled": 0, "message": "Abra o navegador deste perfil antes de preencher."}

        if self.is_native_browser(profile_id):
            driver = self._attach_native_control_driver(profile_id)
            if not driver:
                return {
                    "ok": False,
                    "filled": 0,
                    "message": "Feche este navegador e abra de novo pelo app. A versão nova precisa abrir o Chrome com controle local para preencher a Paramount.",
                }
        else:
            driver = active_ref

        if not hasattr(driver, "execute_script"):
            return {"ok": False, "filled": 0, "message": "Este navegador não permite preenchimento automático."}

        normalized = {
            "cep": str(address_data.get("cep", "")).strip(),
            "cep_sem_ponto": str(address_data.get("cep", "")).replace("-", "").replace(".", "").strip(),
            "logradouro": str(address_data.get("logradouro", "")).strip(),
            "rua": str(address_data.get("rua") or address_data.get("logradouro", "")).strip(),
            "numero": str(address_data.get("numero", "")).strip(),
            "bairro": str(address_data.get("bairro", "")).strip(),
            "cidade": str(address_data.get("cidade", "")).strip(),
            "estado": str(address_data.get("estado", "")).strip(),
            "uf": str(address_data.get("uf", "")).strip().upper(),
            "complemento": str(address_data.get("complemento", "")).strip(),
            "cpf": str(address_data.get("cpf") or address_data.get("cpfDigits") or address_data.get("documento") or "").strip(),
            "cpfDigits": str(address_data.get("cpfDigits") or address_data.get("cpf") or address_data.get("documento") or "").strip(),
            "firstName": str(address_data.get("firstName") or address_data.get("first_name") or "").strip(),
            "lastName": str(address_data.get("lastName") or address_data.get("last_name") or "").strip(),
            "fullName": str(address_data.get("fullName") or address_data.get("full_name") or "").strip(),
        }
        uf_to_state = {
            "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
            "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
            "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
            "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
            "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
            "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
            "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
        }
        if normalized["uf"]:
            expected_state = uf_to_state.get(normalized["uf"], normalized["uf"])
            state_text = normalized["estado"]
            if not state_text or state_text.upper() == normalized["uf"] or "Ã" in state_text:
                normalized["estado"] = expected_state
        street_compact = "".join(ch for ch in normalized["logradouro"].upper() if ch.isalnum())
        invalid_streets = {"BR", "BRA", "BRASIL"}
        if (
            len(street_compact) < 4
            or street_compact in invalid_streets
            or (normalized["uf"] and street_compact == normalized["uf"])
            or (normalized["cidade"] and street_compact == "".join(ch for ch in normalized["cidade"].upper() if ch.isalnum()))
            or (normalized["estado"] and street_compact == "".join(ch for ch in normalized["estado"].upper() if ch.isalnum()))
        ):
            normalized["logradouro"] = ""
            normalized["rua"] = ""
        normalized["endereco_completo"] = ", ".join(
            part for part in [
                normalized["logradouro"],
                normalized["numero"],
                normalized["bairro"],
                normalized["cidade"],
                normalized["uf"],
                normalized["cep"],
            ] if part
        )

        physical_results = []
        try:
            current_url_for_physical = driver.execute_script("return location.href") or ""
        except Exception:
            current_url_for_physical = ""
        is_paramount_page = "paramountplus.com" in current_url_for_physical.lower()
        if is_paramount_page:
            try:
                physical_results.append(self._fill_paramount_payment_physical(driver, normalized))
            except Exception as exc:
                self.log_event("paramount_physical_fill_skip", profile_id, str(exc), "warning")

            fast_fields = []
            for item in physical_results:
                fast_fields.extend(item.get("fields", []) or [])
            fast_fields = list(dict.fromkeys(str(field) for field in fast_fields if field))
            fast_lookup = [field.lower() for field in fast_fields]

            def fast_has(*needles: str) -> bool:
                return any(any(needle in field for needle in needles) for field in fast_lookup)

            has_address_core = (
                fast_has("rua", "logradouro", "endereco", "endereço")
                and fast_has("cidade")
                and fast_has("cep", "postal")
            )
            has_document = fast_has("cpf", "documento", "tax")
            has_state = fast_has("estado", "state", "uf")

            if has_address_core and has_document and has_state:
                filled = max(
                    sum(int(item.get("filled", 0) or 0) for item in physical_results),
                    len(fast_fields),
                )
                message = f"Preenchi {filled} campo(s) no modo rápido da Paramount."
                self.log_event("address_autofill", profile_id, message)
                return {
                    "ok": True,
                    "filled": filled,
                    "fields": fast_fields,
                    "message": message,
                }

        script = r"""
const address = arguments[0] || {};

function clean(s) {
  return (s || "")
    .toString()
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase();
}

function fieldText(el) {
  const bits = [
    el.name, el.id, el.placeholder, el.getAttribute("aria-label"),
    el.getAttribute("autocomplete"), el.getAttribute("data-testid"),
    el.getAttribute("data-test"), el.getAttribute("title")
  ];
  for (const attr of ["aria-labelledby", "aria-describedby"]) {
    const ids = (el.getAttribute(attr) || "").split(/\s+/).filter(Boolean);
    for (const id of ids) {
      const ref = document.getElementById(id);
      if (ref) bits.push(ref.innerText || ref.textContent || "");
    }
  }
  if (el.labels) {
    Array.from(el.labels).forEach(label => bits.push(label.innerText));
  }
  const previous = el.previousElementSibling;
  if (previous) bits.push(previous.innerText || previous.textContent || "");
  const labelParent = el.closest("label");
  if (labelParent) bits.push(labelParent.innerText || labelParent.textContent || "");
  const parent = el.parentElement;
  if (parent) {
    const txt = (parent.innerText || parent.textContent || "").trim();
    const lines = txt.split(/\n+/).filter(Boolean).length;
    if (txt.length <= 140 && lines <= 4) bits.push(txt);
  }
  return clean(bits.filter(Boolean).join(" "));
}

function pickValue(el, text) {
  const type = clean(el.type || "");
  const compact = text.replace(/[^a-z0-9]/g, "");
  if (type === "password" || type === "email") return null;
  if (/card|cartao|cvv|cvc|security|month|year|expir|cc-|credit|debito|credito|validade|numero do cartao/.test(text) || /(cardnumber|creditcard|securitycode|expiration|expiry|cvc|cvv)/.test(compact)) return null;
  if (/telefone|phone|mobile|celular/.test(text) || /phone(number)?/.test(compact)) return null;
  if (type === "tel" && !/cep|postal|zip|codigo postal/.test(text) && !/(postalcode|zipcode|postcode)/.test(compact)) return null;
  if (/cep|postal|zip|codigo postal|c[oó]digo postal/.test(text) || /(postalcode|postalzipcode|zipcode|zip|postcode|enteraddresspostalcode|addresspostalcode)/.test(compact)) return address.cep || address.cep_sem_ponto;
  if (
    /logradouro|endereco|endereço|address line 1|address1|rua|street|avenida|av\.|road/.test(text) ||
    /(addressline1|addresslineone|address1|streetaddress|street1|shippingaddressline1|billingaddressline1|enteraddressline1|enteraddressaddressline1)/.test(compact)
  ) return address.logradouro || address.rua || null;
  if (/numero|n[uú]mero|address number|house number|num /.test(text) || /(addressnumber|housenumber|streetnumber|numero|numberstreet|enternumber)/.test(compact)) return address.numero;
  if (/bairro|neighborhood|district|suburb/.test(text) || /(neighborhood|district|suburb|bairro)/.test(compact)) return address.bairro;
  if (/cidade|city|locality|municipio|munic[ií]pio/.test(text) || /(city|locality|municipality|town|addresslevel2|enteraddresscity|addresscity|shippingcity|billingcity)/.test(compact)) return address.cidade;
  if (/estado|state|province|provincia|prov[ií]ncia|regi[aã]o/.test(text) || /(stateorregion|stateprovince|regionstate|addresslevel1|administrativearealevel1|provincecode|statecode|enteraddressstateorregion|addressstate|shippingstate|billingstate)/.test(compact)) return address.estado || address.uf;
  if (/(^|\s)uf($|\s)|unidade federativa|region/.test(text) || /(^|[^a-z])uf([^a-z]|$)/.test(text)) return address.uf || address.estado;
  if (/cpf|documento|tax id|taxid/.test(text) || /(taxidentifier|taxid|cpf|document)/.test(compact)) return address.cpf || address.cpfDigits;
  if (/complemento|complement|address line 2|address2|apartamento|apto|suite/.test(text) || /(addressline2|addresslinetwo|address2|apartment|suite|complemento|enteraddressline2)/.test(compact)) return address.complemento || address.numero;
  if (/endereco completo|full address/.test(text)) return address.endereco_completo;
  return null;
}

function setNativeValue(el, value) {
  if (value === null || value === undefined || value === "") return false;
  el.focus();
  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set || Object.getOwnPropertyDescriptor(el.__proto__, "value")?.set;
  if (setter) setter.call(el, value);
  else el.value = value;
  el.dispatchEvent(new Event("input", { bubbles: true }));
  el.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, key: "Tab" }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
  el.dispatchEvent(new Event("blur", { bubbles: true }));
  return true;
}

function compactClean(s) {
  return clean(s).replace(/[^a-z0-9]/g, "");
}

function allElements(selector, root = document) {
  const found = [];
  function walk(node) {
    try { found.push(...Array.from(node.querySelectorAll(selector))); } catch (_) {}
    try {
      for (const el of Array.from(node.querySelectorAll("*"))) {
        if (el.shadowRoot) walk(el.shadowRoot);
      }
    } catch (_) {}
  }
  walk(root);
  return found;
}

function optionMatchesState(opt) {
  const value = clean(opt.value);
  const label = clean(opt.textContent);
  const valueCompact = compactClean(opt.value);
  const labelCompact = compactClean(opt.textContent);
  const wantedState = clean(address.estado);
  const wantedUf = clean(address.uf);
  const wantedUfCompact = compactClean(address.uf);
  const wantedStateCompact = compactClean(address.estado);
  return (
    value === wantedUf || label === wantedUf ||
    value === wantedState || label === wantedState ||
    valueCompact === wantedUfCompact || labelCompact === wantedUfCompact ||
    valueCompact.endsWith(wantedUfCompact) || labelCompact.endsWith(wantedUfCompact) ||
    (wantedState && (label.includes(wantedState) || value.includes(wantedState))) ||
    (wantedStateCompact && (labelCompact.includes(wantedStateCompact) || valueCompact.includes(wantedStateCompact)))
  );
}

function fillSelect(el, text) {
  const options = Array.from(el.options || []);
  const looksLikeState = /estado|state|province|provincia|uf|region/.test(text) || options.some(optionMatchesState);
  if (!looksLikeState) return false;
  for (const opt of options) {
    if (optionMatchesState(opt)) {
      el.value = opt.value;
      opt.selected = true;
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      el.dispatchEvent(new Event("blur", { bubbles: true }));
      return true;
    }
  }
  return false;
}

let filled = 0;
let names = [];
const fields = allElements("input, textarea, select");
for (const el of fields) {
  if (el.disabled || el.readOnly) continue;
  const style = window.getComputedStyle(el);
  if (style.display === "none" || style.visibility === "hidden") continue;
  const rect = el.getBoundingClientRect();
  if (rect.width <= 1 || rect.height <= 1) continue;
  const text = fieldText(el);
  let ok = false;
  if (el.tagName.toLowerCase() === "select") {
    ok = fillSelect(el, text);
  } else {
    const value = pickValue(el, text);
    ok = setNativeValue(el, value);
  }
  if (ok) {
    filled += 1;
    names.push((el.name || el.id || el.placeholder || el.tagName).toString().slice(0, 50));
  }
}
return { filled, fields: names };
"""

        state_script = r"""
const address = arguments[0] || {};
const done = arguments[arguments.length - 1];

const UF_TO_STATE = {
  AC:"Acre", AL:"Alagoas", AP:"Amapá", AM:"Amazonas", BA:"Bahia", CE:"Ceará",
  DF:"Distrito Federal", ES:"Espírito Santo", GO:"Goiás", MA:"Maranhão",
  MT:"Mato Grosso", MS:"Mato Grosso do Sul", MG:"Minas Gerais", PA:"Pará",
  PB:"Paraíba", PR:"Paraná", PE:"Pernambuco", PI:"Piauí", RJ:"Rio de Janeiro",
  RN:"Rio Grande do Norte", RS:"Rio Grande do Sul", RO:"Rondônia", RR:"Roraima",
  SC:"Santa Catarina", SP:"São Paulo", SE:"Sergipe", TO:"Tocantins"
};

function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}

function isVisible(el) {
  if (!el || !el.getBoundingClientRect) return false;
  const style = window.getComputedStyle(el);
  const rect = el.getBoundingClientRect();
  return style.display !== "none" && style.visibility !== "hidden" && rect.width > 2 && rect.height > 2;
}

function textOf(el) {
  const bits = [
    el.innerText, el.textContent, el.value, el.placeholder, el.name, el.id,
    el.getAttribute("aria-label"), el.getAttribute("aria-labelledby"),
    el.getAttribute("autocomplete"), el.getAttribute("data-testid"),
    el.getAttribute("data-test"), el.getAttribute("title")
  ];
  for (const attr of ["aria-labelledby", "aria-describedby"]) {
    const ids = (el.getAttribute(attr) || "").split(/\s+/).filter(Boolean);
    for (const id of ids) {
      const ref = document.getElementById(id);
      if (ref) bits.push(ref.innerText || ref.textContent || "");
    }
  }
  if (el.labels) Array.from(el.labels).forEach(label => bits.push(label.innerText));
  const previous = el.previousElementSibling;
  if (previous) bits.push(previous.innerText || previous.textContent || "");
  const labelParent = el.closest("label");
  if (labelParent) bits.push(labelParent.innerText || labelParent.textContent || "");
  const parent = el.parentElement;
  if (parent) {
    const txt = (parent.innerText || parent.textContent || "").trim();
    const lines = txt.split(/\n+/).filter(Boolean).length;
    if (txt.length <= 160 && lines <= 4) bits.push(txt);
  }
  return clean(bits.filter(Boolean).join(" "));
}

function fireClick(el) {
  if (!el || !isVisible(el)) return false;
  el.scrollIntoView({ block: "center", inline: "center" });
  el.focus?.();
  for (const type of ["pointerdown", "mousedown", "mouseup", "pointerup", "click"]) {
    try {
      el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
    } catch (_) {}
  }
  try { el.click?.(); } catch (_) {}
  return true;
}

function compactClean(s) {
  return clean(s).replace(/[^a-z0-9]/g, "");
}

function allElements(selector, root = document) {
  const found = [];
  function walk(node) {
    try { found.push(...Array.from(node.querySelectorAll(selector))); } catch (_) {}
    try {
      for (const el of Array.from(node.querySelectorAll("*"))) {
        if (el.shadowRoot) walk(el.shadowRoot);
      }
    } catch (_) {}
  }
  walk(root);
  return found;
}

function selectNative(el, desired) {
  const wanted = clean(desired);
  const wantedUf = clean(address.uf);
  const wantedState = clean(address.estado || UF_TO_STATE[address.uf] || "");
  const wantedUfCompact = compactClean(address.uf);
  const wantedStateCompact = compactClean(address.estado || UF_TO_STATE[address.uf] || "");
  for (const opt of Array.from(el.options || [])) {
    const label = clean(opt.textContent);
    const value = clean(opt.value);
  const labelCompact = compactClean(opt.textContent);
  const valueCompact = compactClean(opt.value);
    if (
      label === wanted || value === wanted ||
      label === wantedUf || value === wantedUf ||
      label === wantedState || value === wantedState ||
      (wantedState && (label.includes(wantedState) || value.includes(wantedState))) ||
      (wantedStateCompact && (labelCompact.includes(wantedStateCompact) || valueCompact.includes(wantedStateCompact))) ||
      (wantedUfCompact && (labelCompact === wantedUfCompact || valueCompact === wantedUfCompact || labelCompact.endsWith(wantedUfCompact) || valueCompact.endsWith(wantedUfCompact)))
    ) {
      el.value = opt.value;
      opt.selected = true;
      el.dispatchEvent(new Event("input", { bubbles: true }));
      el.dispatchEvent(new Event("change", { bubbles: true }));
      el.dispatchEvent(new Event("blur", { bubbles: true }));
      return true;
    }
  }
  return false;
}

function setTextValue(el, value) {
  if (!el || !value) return false;
  el.scrollIntoView({ block: "center", inline: "center" });
  el.focus?.();
  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set || Object.getOwnPropertyDescriptor(el.__proto__, "value")?.set;
  if (setter) setter.call(el, value);
  else el.value = value;
  for (const type of ["input", "change", "blur"]) {
    el.dispatchEvent(new Event(type, { bubbles: true }));
  }
  return true;
}

const desiredState = address.estado || UF_TO_STATE[address.uf] || "";
const desiredUf = address.uf || "";
const desiredValues = [desiredState, desiredUf].map(clean).filter(Boolean);
const stateFieldPattern = /estado|state|province|provincia|uf|region|addresslevel1|administrativearealevel1|stateorregion|stateprovince|statecode|provincecode|enteraddressstateorregion/;
if (!desiredValues.length) {
  done({ filled: 0, fields: [] });
  return;
}

// 1) select nativo.
for (const sel of allElements("select")) {
  if (!isVisible(sel)) continue;
  const tx = textOf(sel);
  if ((stateFieldPattern.test(tx) || selectNative(sel, desiredState || desiredUf)) && selectNative(sel, desiredState || desiredUf)) {
    done({ filled: 1, fields: ["estado-select"] });
    return;
  }
}

// 2) dropdown customizado: clica no campo "Estado" e depois na opção.
const clickableSelectors = [
  "[role='combobox']", "[aria-haspopup='listbox']", "[aria-haspopup='true']",
  "button", "input", "div", "span"
].join(",");

const candidates = allElements(clickableSelectors)
  .filter(isVisible)
  .filter(el => {
    const tx = textOf(el);
    if (!stateFieldPattern.test(tx)) return false;
    const shortText = clean(el.innerText || el.textContent || el.placeholder || el.value || "");
    return shortText.length < 80 || /estado|state|uf/.test(shortText);
  });

let target = null;
for (const el of candidates) {
  target = el.closest("[role='combobox'], [aria-haspopup], button") || el;
  if (fireClick(target)) break;
}

function optionMatches(el) {
  const tx = clean(el.innerText || el.textContent || el.value || el.getAttribute("aria-label") || "");
  if (!tx || tx.length > 90) return false;
  return desiredValues.some(v => tx === v || tx.includes(v));
}

setTimeout(() => {
  const optionSelectors = [
    "[role='option']", "[role='menuitem']", "li", "button", "div", "span"
  ].join(",");
  const options = allElements(optionSelectors)
    .filter(isVisible)
    .filter(optionMatches);
  for (const opt of options) {
    if (fireClick(opt)) {
      done({ filled: 1, fields: ["estado-dropdown"] });
      return;
    }
  }

  // Fallback para campos read-only/customizados: alguns sites aceitam valor
  // direto depois de CEP/cidade, mas nao expõem lista de opcoes no DOM.
  const stateInputs = allElements("input, textarea")
    .filter(isVisible)
    .filter(el => stateFieldPattern.test(textOf(el)));
  for (const input of stateInputs) {
    if (setTextValue(input, desiredState || desiredUf)) {
      done({ filled: 1, fields: ["estado-input"] });
      return;
    }
  }

  done({ filled: 0, fields: [] });
}, 360);
"""
        try:
            results = list(physical_results)

            def run_current_frame():
                try:
                    data = driver.execute_script(script, normalized) or {}
                    results.append(data)
                except Exception as frame_error:
                    self.log_event("address_autofill_frame_error", profile_id, str(frame_error), "warning")

            def run_state_frame():
                try:
                    data = driver.execute_async_script(state_script, normalized) or {}
                    results.append(data)
                except Exception as frame_error:
                    self.log_event("address_state_frame_error", profile_id, str(frame_error), "warning")

            driver.switch_to.default_content()
            run_current_frame()
            if not is_paramount_page:
                run_state_frame()
            try:
                frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
                for index in range(len(frames)):
                    try:
                        driver.switch_to.default_content()
                        frames = driver.find_elements(By.CSS_SELECTOR, "iframe, frame")
                        driver.switch_to.frame(frames[index])
                        run_current_frame()
                        if not is_paramount_page:
                            run_state_frame()
                    except Exception as frame_error:
                        self.log_event("address_autofill_frame_skip", profile_id, str(frame_error), "warning")
            finally:
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass

            filled = sum(int(item.get("filled", 0) or 0) for item in results)
            fields = []
            for item in results:
                fields.extend(item.get("fields", []) or [])
            try:
                current_url = driver.execute_script("return location.href") or ""
            except Exception:
                current_url = ""
            if "paramountplus.com" in current_url.lower():
                state_result = self._fill_paramount_state_dropdown(driver, normalized)
                if state_result.get("filled"):
                    filled += int(state_result.get("filled", 0) or 0)
                    fields.extend(state_result.get("fields", []) or [])
            self.log_event("address_autofill", profile_id, f"Endereço preenchido em {filled} campo(s)")
            return {
                "ok": filled > 0,
                "filled": filled,
                "fields": fields,
                "message": f"Preenchi {filled} campo(s) de endereço." if filled else "Não encontrei campos de endereço visíveis nesta página.",
            }
        except Exception as e:
            self.log_event("address_autofill_error", profile_id, str(e), "error")
            return {"ok": False, "filled": 0, "message": f"Erro ao preencher endereço: {e}"}

    def retry_site_without_closing(self, profile_id: str) -> Dict:
        """
        Tenta destravar a página atual sem fechar o navegador.

        Limpa dados do site aberto via DevTools/Selenium e recarrega a página.
        Isso não muda argumentos de inicialização do Chrome; ajustes de fingerprint
        completos continuam exigindo reabrir o perfil.
        """
        active_ref = self.active_browsers.get(profile_id)
        if not active_ref or not self.is_browser_active(profile_id):
            return {"ok": False, "message": "Abra o navegador deste perfil antes de tentar."}

        if self.is_native_browser(profile_id):
            driver = self._attach_native_control_driver(profile_id)
            if not driver:
                return {"ok": False, "message": "Não consegui controlar este Chrome aberto. Abra o perfil pelo app novamente."}
        else:
            driver = active_ref

        if not hasattr(driver, "execute_script"):
            return {"ok": False, "message": "Este modo de navegador não permite limpar a página aberta sem fechar."}

        try:
            current_url = driver.current_url
        except Exception:
            current_url = ""

        parsed = urllib.parse.urlparse(current_url or "")
        if not parsed.scheme or not parsed.netloc:
            return {"ok": False, "message": "A página atual ainda não tem um endereço válido."}

        origin = f"{parsed.scheme}://{parsed.netloc}"
        cleared = []
        try:
            driver.execute_cdp_cmd(
                "Storage.clearDataForOrigin",
                {
                    "origin": origin,
                    "storageTypes": "cookies,local_storage,session_storage,indexeddb,cache_storage,service_workers,websql,file_systems",
                },
            )
            cleared.append("dados do site")
        except Exception as exc:
            self.log_event("site_soft_reset_cdp_skip", profile_id, str(exc), "warning")

        try:
            driver.execute_cdp_cmd("Network.clearBrowserCache", {})
            cleared.append("cache do navegador")
        except Exception as exc:
            self.log_event("site_soft_reset_cache_skip", profile_id, str(exc), "warning")

        try:
            driver.execute_script(
                """
                try { window.localStorage && window.localStorage.clear(); } catch (_) {}
                try { window.sessionStorage && window.sessionStorage.clear(); } catch (_) {}
                try {
                  if (window.caches && caches.keys) {
                    caches.keys().then(keys => keys.forEach(key => caches.delete(key)));
                  }
                } catch (_) {}
                """
            )
            cleared.append("armazenamento da aba")
        except Exception as exc:
            self.log_event("site_soft_reset_js_skip", profile_id, str(exc), "warning")

        try:
            driver.refresh()
        except Exception:
            try:
                driver.get(current_url)
            except Exception as exc:
                self.log_event("site_soft_reset_reload_error", profile_id, str(exc), "warning")

        self.log_event("site_soft_reset", profile_id, f"Reset sem fechar aplicado em {origin}")
        return {
            "ok": True,
            "origin": origin,
            "cleared": cleared,
            "message": f"Tentei destravar {origin} sem fechar o navegador. Aguarde recarregar e marque a verificação novamente.",
        }
    
    def close_browser(self, profile_id: str) -> bool:
        """
        Fecha o navegador de um perfil.
        
        Args:
            profile_id: ID do perfil
            
        Returns:
            True se fechou com sucesso
        """
        driver = self.active_browsers.get(profile_id)
        if not driver:
            return False
        
        control_driver = self.native_control_drivers.pop(profile_id, None)
        if control_driver:
            try:
                control_driver.quit()
            except Exception:
                pass

        try:
            if self.active_browser_modes.get(profile_id) == "native":
                driver.terminate()
            else:
                driver.quit()
        except Exception as quit_err:
            print(f"Aviso: Erro ao fechar navegador: {quit_err}")
        
        self.active_browsers.pop(profile_id, None)
        self.active_browser_modes.pop(profile_id, None)
        self.active_debug_ports.pop(profile_id, None)
        self.active_native_browser_names.pop(profile_id, None)
        self.log_event("browser_closed", profile_id, "Navegador fechado")
        return True
    
    def is_browser_active(self, profile_id: str) -> bool:
        """
        Verifica se o navegador de um perfil está ativo.
        
        Args:
            profile_id: ID do perfil
            
        Returns:
            True se ativo
        """
        def native_port_alive() -> bool:
            port = self.active_debug_ports.get(profile_id)
            if not port:
                return False
            try:
                with socket.create_connection(("127.0.0.1", int(port)), timeout=0.25):
                    return True
            except Exception:
                return False

        if profile_id not in self.active_browsers:
            return native_port_alive()
        
        driver = self.active_browsers[profile_id]
        try:
            if self.active_browser_modes.get(profile_id) == "native":
                if hasattr(driver, "poll"):
                    alive = driver.poll() is None
                    if not alive:
                        if native_port_alive():
                            return True
                        self.active_browsers.pop(profile_id, None)
                        self.active_browser_modes.pop(profile_id, None)
                        self.active_debug_ports.pop(profile_id, None)
                        self.active_native_browser_names.pop(profile_id, None)
                        self.native_control_drivers.pop(profile_id, None)
                    return alive
                self.active_browser_modes.pop(profile_id, None)
            if self.active_browser_modes.get(profile_id) == "selenium":
                # Evita bool(driver.window_handles) aqui. Quando o Chrome/Selenium trava,
                # essa chamada pode bloquear a interface por minutos.
                process = getattr(getattr(driver, "service", None), "process", None)
                if process is not None and hasattr(process, "poll") and process.poll() is not None:
                    self.active_browsers.pop(profile_id, None)
                    self.active_browser_modes.pop(profile_id, None)
                    self.active_debug_ports.pop(profile_id, None)
                    self.active_native_browser_names.pop(profile_id, None)
                    self.native_control_drivers.pop(profile_id, None)
                    return False
                return True
            return bool(driver.window_handles)
        except (WebDriverException, InvalidSessionIdException, AttributeError) as e:
            # Se falhar, remover da lista
            print(f"Aviso: Navegador não responde, removendo da lista: {e}")
            self.active_browsers.pop(profile_id, None)
            self.active_browser_modes.pop(profile_id, None)
            self.active_debug_ports.pop(profile_id, None)
            self.active_native_browser_names.pop(profile_id, None)
            self.native_control_drivers.pop(profile_id, None)
            return False

    def is_native_browser(self, profile_id: str) -> bool:
        return self.active_browser_modes.get(profile_id) == "native"
    
    def get_active_browsers(self) -> List[str]:
        """
        Lista IDs dos perfis com navegadores ativos.
        
        Returns:
            Lista de IDs
        """
        # Verificar quais ainda estão ativos
        active = []
        for profile_id in list(self.active_browsers.keys()):
            if self.is_browser_active(profile_id):
                active.append(profile_id)
        return active
    
    def cleanup(self):
        """Fecha todos os navegadores ativos."""
        for profile_id in list(self.active_browsers.keys()):
            self.close_browser(profile_id)
    
    def add_auto_login(
        self,
        profile_id: str,
        url: str,
        username: str,
        password: str
    ) -> bool:
        """
        Adiciona configuração de auto-login a um perfil.
        
        Args:
            profile_id: ID do perfil
            url: URL do site
            username: Nome de usuário
            password: Senha
            
        Returns:
            True se adicionado com sucesso
        """
        profile = self.profiles.get(profile_id)
        if not profile:
            return False
        
        profile.auto_login[url] = {
            "username": username,
            "password": password
        }
        
        self._save_profiles()
        return True
    
    def remove_auto_login(self, profile_id: str, url: str) -> bool:
        """
        Remove configuração de auto-login de um perfil.
        
        Args:
            profile_id: ID do perfil
            url: URL do site
            
        Returns:
            True se removido com sucesso
        """
        profile = self.profiles.get(profile_id)
        if not profile or url not in profile.auto_login:
            return False
        
        del profile.auto_login[url]
        self._save_profiles()
        return True


# Teste do módulo
if __name__ == "__main__":
    print("=== Teste do Browser Manager ===\n")
    
    if not SELENIUM_AVAILABLE:
        print("AVISO: Selenium não está instalado.")
        print("Execute: pip install selenium webdriver-manager")
        print("\nTestando apenas funcionalidades de perfil...\n")
    
    manager = BrowserManager()
    
    # Criar perfil rápido
    print("Criando perfil rápido...")
    profile = manager.create_quick_profile()
    print(f"Perfil criado: {profile.name}")
    print(f"ID: {profile.id}")
    print(f"User-Agent: {profile.fingerprint.get('user_agent', 'N/A')[:50]}...")
    screen = profile.fingerprint.get("screen", {})
    print(f"Resolução: {screen.get('width', 'N/A')}x{screen.get('height', 'N/A')}")
    print("=" * 50)
    
    # Criar perfil customizado
    print("\nCriando perfil customizado...")
    profile2 = manager.create_profile(
        name="Meu Perfil Seguro",
        proxy="192.168.1.1:8080:user:pass"
    )
    print(f"Perfil criado: {profile2.name}")
    print(f"Proxy: {profile2.proxy}")
    print("=" * 50)
    
    # Listar perfis
    print("\nPerfis salvos:")
    for p in manager.list_profiles():
        print(f"  - {p.name} (ID: {p.id})")
    
    print("=" * 50)
    
    # Testar auto-login
    print("\nAdicionando auto-login...")
    manager.add_auto_login(
        profile2.id,
        "https://example.com/login",
        "usuario",
        "senha123"
    )
    print("Auto-login adicionado!")
    print(f"Auto-logins salvos: {list(profile2.auto_login.keys())}")
    
    print("\nTeste concluído!")


