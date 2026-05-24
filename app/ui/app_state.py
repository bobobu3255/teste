from PyQt5.QtCore import QSettings

from address_generator import AddressGenerator
from app.ui.main_pages import CRUNCHYROLL_AVAILABLE
from config_manager import ConfigManager
from database import DatabaseManager
from settings import settings


class MainStateMixin:
    """Estado inicial e banco ativo da janela principal."""

    def initialize_runtime_state(self):
        self.config_manager = ConfigManager()
        self.db = self._get_database()
        self.collector_thread = None
        self.current_pair = None
        self._address_gen = AddressGenerator()

        self.is_always_on_top = False
        self.is_fullscreen = False
        self.is_compact_mode = False
        self._force_quit = False
        self.settings = QSettings("TelegramCollector", "Pro")

        self.mostrar_nome = True
        self.mostrar_cpf = True
        self.mostrar_idade = True
        self.mostrar_data = True
        self.mostrar_telefone = True
        self.mostrar_score = True

        self.tab_titles = [
            self.TAB_TITLES["inicio"],
            self.TAB_TITLES["gerador"],
            self.TAB_TITLES["navegador"],
            self.TAB_TITLES["ia"],
        ]
        if CRUNCHYROLL_AVAILABLE:
            self.tab_titles.append(self.TAB_TITLES["crunchyroll"])
        self.tab_titles.append(self.TAB_TITLES["notas"])
        self.tab_titles.append(self.TAB_TITLES["config"])

    def _get_database(self):
        conta = self.config_manager.get_conta_ativa()
        if conta:
            return DatabaseManager(self.config_manager.get_caminho_banco(conta["id"]))
        return DatabaseManager()

    def refresh_database(self):
        self.db = self._get_database()
        if hasattr(self, "_compact_widget"):
            self._compact_widget.update_db(self.db)
        if hasattr(self, "data_pro_tab"):
            self.data_pro_tab.update_db(self.db)
        self.update_stats()

    def check_configuration(self):
        if not settings.is_configured:
            self.status_bar.showMessage(
                "Telegram ainda nao configurado. Use Config. quando for coletar.",
                5000,
            )
