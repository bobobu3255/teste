#!/usr/bin/env python3
"""Entrada principal do Telegram Collector Pro V12 Core."""
import sys

from PyQt5.QtWidgets import QMainWindow

from app.core.error_service import install_crash_logger as core_install_crash_logger
from app.ui.app_bootstrap import create_application
from app.ui.app_state import MainStateMixin
from app.ui.main_actions import MainActionsMixin
from app.ui.main_layout import MainLayoutMixin
from app.ui.main_pages import MainPagesMixin
from app.ui.window_controls import MainWindowControlsMixin
from settings import BASE_DIR


def install_crash_logger():
    """Guarda erros fatais em arquivo para diagnosticar fechamentos silenciosos."""
    core_install_crash_logger(BASE_DIR)


class SimpleApp(MainStateMixin, MainLayoutMixin, MainWindowControlsMixin, MainActionsMixin, MainPagesMixin, QMainWindow):
    """Janela principal do projeto."""

    NORMAL_SIZE = (1280, 860)
    COMPACT_SIZE = (400, 600)

    # Títulos das abas para o header
    TAB_TITLES = {
        "inicio": "🏠  Painel Inicial",
        "gerador": "🎲  Gerador de Pares",
        "ferramentas": "🛠️  Ferramentas",
        "navegador": "🌐  Navegador Seguro",
        "ia": "🤖  IA Local",
        "crunchyroll": "🍦  Crunchyroll",
        "notas": "📝  Bloco de Notas",
        "config": "⚙️  Configurações",
    }


    def __init__(self):
        super().__init__()
        self.initialize_runtime_state()
        self._setup_window()
        self.init_ui()
        self._setup_tray()
        self.check_configuration()
        self._load_state()


def main():
    install_crash_logger()
    app = create_application(sys.argv)
    window = SimpleApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
