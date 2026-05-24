#!/usr/bin/env python3
"""
Configurações Centralizadas — v11.0

Gerencia credenciais e configurações via variáveis de ambiente.

Mudanças desta versão
─────────────────────
• Helpers tipados para parsing de envvars (`_env`, `_env_int`, `_env_bool`)
• Validação consolidada — `is_configured` reflete o estado atual sem cache
• Aliases (`api_id`, `api_hash`, `phone`) preservados via property
• Logger estruturado em vez de `print`
• Constantes para nomes de arquivos (sem strings mágicas)
• Suporte para sobrescrever o `BASE_DIR` em testes
"""
from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Final

from dotenv import load_dotenv

log = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════════
#  Constantes
# ════════════════════════════════════════════════════════════════
DEFAULT_GROUP: Final[str] = "PuxadasTr4in"
ENV_FILENAME: Final[str] = ".env"
DB_FILENAME: Final[str] = "dados.db"
SESSION_FILENAME: Final[str] = "session"
ACCOUNTS_FILENAME: Final[str] = "contas.json"

REQUIRED_KEYS: Final[tuple[str, ...]] = (
    "TELEGRAM_API_ID",
    "TELEGRAM_API_HASH",
)


# ════════════════════════════════════════════════════════════════
#  Helpers
# ════════════════════════════════════════════════════════════════
def _resolve_base_dir() -> Path:
    """Detecta o diretório base, suportando execução congelada (PyInstaller)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent


def _load_env_file(base: Path) -> Path | None:
    """Procura `.env` em `base` e em `base.parent`. Retorna o caminho carregado."""
    for candidate in (base / ENV_FILENAME, base.parent / ENV_FILENAME):
        if candidate.exists():
            load_dotenv(candidate, override=False)
            log.debug("Variáveis carregadas de %s", candidate)
            return candidate
    log.debug("Nenhum arquivo .env encontrado em %s", base)
    return None


def _env(key: str, default: str | None = None) -> str | None:
    """Lê variável de ambiente; trata string vazia como ausente."""
    value = os.getenv(key)
    if value is None or value == "":
        return default
    return value


def _env_int(key: str) -> int | None:
    """Lê variável de ambiente como int (ou None se inválido)."""
    raw = (os.getenv(key) or "").strip()
    if raw and raw.lstrip("-").isdigit():
        return int(raw)
    return None


def _env_bool(key: str, default: bool = False) -> bool:
    """Lê variável de ambiente como bool. Aceita 1/true/yes/y/on (case-insensitive)."""
    raw = (os.getenv(key) or "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "y", "on"}


# ════════════════════════════════════════════════════════════════
#  Inicialização do .env (executa uma vez na importação)
# ════════════════════════════════════════════════════════════════
BASE_DIR: Final[Path] = _resolve_base_dir()
_LOADED_ENV_PATH: Path | None = _load_env_file(BASE_DIR)


# ════════════════════════════════════════════════════════════════
#  Settings
# ════════════════════════════════════════════════════════════════
class Settings:
    """Configurações centrais da aplicação.

    Cada acesso reflete o valor atual da variável de ambiente — chame
    `reload()` após alterar o `.env` em runtime.
    """

    def __init__(self, base_dir: Path | None = None) -> None:
        self.base_dir: Path = base_dir or BASE_DIR

    # ── Telegram ─────────────────────────────────────────────────
    @property
    def telegram_api_id(self) -> int | None:
        return _env_int("TELEGRAM_API_ID")

    @property
    def telegram_api_hash(self) -> str | None:
        return _env("TELEGRAM_API_HASH")

    @property
    def telegram_phone(self) -> str | None:
        return _env("TELEGRAM_PHONE")

    @property
    def default_group(self) -> str:
        return _env("TELEGRAM_DEFAULT_GROUP", DEFAULT_GROUP) or DEFAULT_GROUP

    # ── Aliases para compatibilidade ─────────────────────────────
    @property
    def api_id(self) -> int | None:
        return self.telegram_api_id

    @property
    def api_hash(self) -> str | None:
        return self.telegram_api_hash

    @property
    def phone(self) -> str | None:
        return self.telegram_phone

    # ── Segurança ────────────────────────────────────────────────
    @property
    def encrypt_data(self) -> bool:
        return _env_bool("ENCRYPT_SENSITIVE_DATA", False)

    @property
    def encryption_key(self) -> str | None:
        return _env("ENCRYPTION_KEY")

    # ── Caminhos ─────────────────────────────────────────────────
    @property
    def db_path(self) -> Path:
        return self.base_dir / DB_FILENAME

    @property
    def session_path(self) -> Path:
        return self.base_dir / SESSION_FILENAME

    @property
    def config_path(self) -> Path:
        return self.base_dir / ACCOUNTS_FILENAME

    @property
    def env_path(self) -> Path:
        return self.base_dir / ENV_FILENAME

    # ── Validação ────────────────────────────────────────────────
    @property
    def missing_settings(self) -> list[str]:
        """Lista as chaves obrigatórias que ainda não foram configuradas."""
        return [k for k in REQUIRED_KEYS if not _env(k)]

    @property
    def is_configured(self) -> bool:
        """True se todas as chaves obrigatórias estiverem presentes."""
        return not self.missing_settings

    # ── Mutações ─────────────────────────────────────────────────
    def reload(self) -> None:
        """Recarrega as variáveis a partir do `.env`."""
        path = self.env_path
        if path.exists():
            load_dotenv(path, override=True)
            log.info("Configurações recarregadas de %s", path)
        else:
            log.warning("Tentativa de recarregar, mas %s não existe", path)

    def create_env_file(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        group: str | None = None,
    ) -> bool:
        """Grava o arquivo `.env` com as credenciais informadas."""
        try:
            content = self._build_env_content(api_id, api_hash, phone, group)
            self.env_path.write_text(content, encoding="utf-8")
            self.reload()
            log.info("Arquivo .env criado em %s", self.env_path)
            return True
        except OSError as exc:
            log.error("Falha ao criar arquivo .env: %s", exc)
            return False

    # ── Templates ────────────────────────────────────────────────
    @staticmethod
    def _build_env_content(
        api_id: int,
        api_hash: str,
        phone: str,
        group: str | None,
    ) -> str:
        return (
            "# Configurações do Telegram Collector\n"
            "# Gerado automaticamente — NÃO COMPARTILHE ESTE ARQUIVO!\n\n"
            f"TELEGRAM_API_ID={api_id}\n"
            f"TELEGRAM_API_HASH={api_hash}\n"
            f"TELEGRAM_PHONE={phone}\n"
            f"TELEGRAM_DEFAULT_GROUP={group or DEFAULT_GROUP}\n"
            "ENCRYPT_SENSITIVE_DATA=false\n"
        )

    def get_env_template(self) -> str:
        """Template para o usuário preencher manualmente."""
        return (
            "# Configurações do Telegram Collector\n"
            "# Obtenha suas credenciais em: https://my.telegram.org/apps\n\n"
            "TELEGRAM_API_ID=seu_api_id_aqui\n"
            "TELEGRAM_API_HASH=seu_api_hash_aqui\n"
            "TELEGRAM_PHONE=+5500000000000\n"
            f"TELEGRAM_DEFAULT_GROUP={DEFAULT_GROUP}\n"
        )

    # ── Debug ────────────────────────────────────────────────────
    def __repr__(self) -> str:
        return (
            f"Settings(configured={self.is_configured}, "
            f"base_dir={self.base_dir!r}, "
            f"missing={self.missing_settings})"
        )


# ════════════════════════════════════════════════════════════════
#  Instância global
# ════════════════════════════════════════════════════════════════
settings = Settings()
