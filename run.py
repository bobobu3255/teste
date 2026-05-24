#!/usr/bin/env python3
"""
Telegram Collector Pro v12.0 Preview - Entry Point

Inicializa a aplicação com:
- Verificação da versão mínima do Python
- Bootstrap de logging estruturado
- Tratamento robusto de erros fatais (com fallback gráfico)
- Códigos de saída padronizados
"""
from __future__ import annotations

import logging
import os
import sys
import traceback
from pathlib import Path
from typing import NoReturn

# ────────────────────────────────────────────────────────────────
#  Constantes de bootstrap
# ────────────────────────────────────────────────────────────────
MIN_PYTHON: tuple[int, int] = (3, 9)
APP_NAME: str = "Telegram Collector Pro"
APP_VERSION: str = "12.0-preview"

EXIT_OK: int = 0
EXIT_ERROR: int = 1
EXIT_INTERRUPTED: int = 130  # padrão POSIX para SIGINT

log = logging.getLogger("telegram_collector")


# ────────────────────────────────────────────────────────────────
#  Helpers de inicialização
# ────────────────────────────────────────────────────────────────
def _setup_path() -> None:
    """Garante que o diretório do projeto está no `sys.path`."""
    base = Path(__file__).resolve().parent
    base_str = str(base)
    if base_str not in sys.path:
        sys.path.insert(0, base_str)


def _check_python_version() -> None:
    """Encerra se a versão do Python for inferior à mínima exigida."""
    if sys.version_info < MIN_PYTHON:
        required = ".".join(map(str, MIN_PYTHON))
        current = ".".join(map(str, sys.version_info[:3]))
        sys.stderr.write(
            f"\n[ERRO] Python {required}+ é necessário. "
            f"Versão atual: {current}\n\n"
        )
        sys.exit(EXIT_ERROR)


def _bootstrap_logging() -> None:
    """Configura logging mínimo antes de carregar o restante do sistema."""
    level_name = os.getenv("LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s │ %(levelname)-7s │ %(name)-22s │ %(message)s",
        datefmt="%H:%M:%S",
    )


def _show_fatal_error(exc: BaseException) -> None:
    """Mostra erro fatal no stderr e tenta exibir um diálogo gráfico."""
    tb = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    banner = "═" * 60
    sys.stderr.write(
        f"\n{banner}\n"
        f"  ERRO FATAL — {APP_NAME}\n"
        f"{banner}\n"
        f"  Tipo:     {type(exc).__name__}\n"
        f"  Mensagem: {exc}\n\n"
        f"{tb}"
        f"{banner}\n\n"
    )

    # Fallback gráfico — silencioso se PyQt não estiver disponível
    try:
        from PyQt5.QtWidgets import QApplication, QMessageBox

        app = QApplication.instance() or QApplication(sys.argv)
        QMessageBox.critical(
            None,
            f"Erro Fatal — {APP_NAME}",
            f"<b>{type(exc).__name__}</b><br><br>{exc}",
        )
    except Exception:  # noqa: BLE001
        pass


# ────────────────────────────────────────────────────────────────
#  Entry point
# ────────────────────────────────────────────────────────────────
def main() -> int:
    """Ponto de entrada principal. Retorna o código de saída."""
    _check_python_version()
    _setup_path()
    _bootstrap_logging()

    log.info("Iniciando %s v%s", APP_NAME, APP_VERSION)

    try:
        from main_app import main as app_main
        return app_main() or EXIT_OK

    except KeyboardInterrupt:
        log.info("Encerrado pelo usuário (Ctrl+C)")
        return EXIT_INTERRUPTED

    except ImportError as exc:
        log.error("Falha ao importar 'main_app': %s", exc)
        _show_fatal_error(exc)
        return EXIT_ERROR

    except SystemExit:
        raise  # respeita sys.exit() interno

    except BaseException as exc:  # noqa: BLE001
        log.exception("Erro fatal não tratado")
        _show_fatal_error(exc)
        return EXIT_ERROR


def _entry() -> NoReturn:
    sys.exit(main())


if __name__ == "__main__":
    _entry()
