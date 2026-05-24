#!/usr/bin/env python3
"""Builder da pagina Navegador Seguro."""

from importlib.util import find_spec

from PyQt5.QtWidgets import QTabWidget, QVBoxLayout, QWidget

from app.ui.shell_widgets import TAB_TOP_QSS
from settings import BASE_DIR


PROFILE_DEFAULTS_AVAILABLE = find_spec("profile_defaults_widget") is not None


class BrowserPageMixin:
    def _build_navegador_page(self):
        page = QWidget()
        page.setStyleSheet("background: #07080f;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)

        self.browser_tabs = QTabWidget()
        self.browser_tabs.setStyleSheet(TAB_TOP_QSS)
        from browser_widget import BrowserWidget

        self.browser_widget = BrowserWidget()
        if hasattr(self, "dashboard_page"):
            self.dashboard_page.browser_widget = self.browser_widget
            self.dashboard_page.browser_manager = self.browser_widget.browser_manager
        self.browser_tabs.addTab(self.browser_widget, "🌐 Navegador")
        if PROFILE_DEFAULTS_AVAILABLE:
            from profile_defaults_widget import ProfileDefaultsWidget

            config_dir = str(BASE_DIR / "browser_config")
            self.profile_defaults_tab = ProfileDefaultsWidget(config_dir)
            self.browser_tabs.addTab(self.profile_defaults_tab, "⚙️ Configurações")
        lay.addWidget(self.browser_tabs)
        return page
