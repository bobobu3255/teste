#!/usr/bin/env python3
"""Builders das paginas simples da janela principal."""

from PyQt5.QtWidgets import QVBoxLayout, QWidget


class SimplePagesMixin:
    def _blank_page_with_widget(self, widget):
        page = QWidget()
        page.setStyleSheet("background: #07080f;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(widget)
        return page

    def _build_inicio_page(self):
        from app_hub import AppDashboardWidget

        self.dashboard_page = AppDashboardWidget(
            db=self.db,
            browser_widget=getattr(self, "browser_widget", None),
            open_page=self.open_page_by_name,
            open_tool=self.show_tools_tab,
        )
        return self._blank_page_with_widget(self.dashboard_page)

    def _build_ai_page(self):
        from ai_assistant_widget import AIAssistantWidget

        self.ai_assistant_tab = AIAssistantWidget()
        return self._blank_page_with_widget(self.ai_assistant_tab)

    def _build_notas_page(self):
        from notepad_widget import NotepadWidget

        self.notepad_tab = NotepadWidget()
        return self._blank_page_with_widget(self.notepad_tab)

    def _build_config_page(self):
        from app_hub import GeneralSettingsWidget

        manager = getattr(getattr(self, "browser_widget", None), "browser_manager", None)
        self.general_settings_tab = GeneralSettingsWidget(manager)
        return self._blank_page_with_widget(self.general_settings_tab)
