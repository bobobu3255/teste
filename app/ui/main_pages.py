#!/usr/bin/env python3
"""Orquestrador das paginas da janela principal."""

from app.ui.browser_page import BrowserPageMixin
from app.ui.crunchyroll_page import CRUNCHYROLL_AVAILABLE, CrunchyrollPageMixin
from app.ui.simple_pages import SimplePagesMixin
from app.ui.tools_page import ToolsPageMixin


class MainPagesMixin(SimplePagesMixin, CrunchyrollPageMixin, ToolsPageMixin, BrowserPageMixin):
    def _build_pages(self):
        self.main_tabs.addTab(self._build_inicio_page(), "In?cio")
        self.main_tabs.addTab(self._build_gerador_page(), "Gerador")
        self.main_tabs.addTab(self._build_navegador_page(), "Navegador")
        self.main_tabs.addTab(self._build_ai_page(), "IA Local")
        if CRUNCHYROLL_AVAILABLE:
            self.main_tabs.addTab(self._build_crunchyroll_page(), "Crunchyroll")
        self.main_tabs.addTab(self._build_notas_page(), "Notas")
        self.main_tabs.addTab(self._build_config_page(), "Config")
        self.main_tabs.addTab(self._build_ferramentas_page(), "Ferramentas")
        self.tab_titles.append(self.TAB_TITLES["ferramentas"])

    def _build_gerador_page(self):
        from app.ui.generator_page import build_generator_page

        return build_generator_page(self)

    def _build_ferramentas_page(self):
        return super()._build_ferramentas_page()
