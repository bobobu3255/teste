#!/usr/bin/env python3
"""Builder da pagina Ferramentas."""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QTabWidget, QVBoxLayout, QWidget

from app.ui.components import card_qss, label_qss
from app.ui.tools_page_assets import COUNTER_QSS, TOOLS_METADATA


class ToolsPageMixin:
    def _build_ferramentas_page(self):
        page = QWidget()
        page.setStyleSheet("background: #07080f;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(14, 10, 14, 12)
        lay.setSpacing(8)

        self.tools_tabs = QTabWidget()
        self.tools_tabs.setUsesScrollButtons(True)
        self.tools_tabs.setElideMode(Qt.ElideNone)
        self.tools_tabs.setDocumentMode(True)
        self._add_tool_tabs()
        self.tools_tabs.tabBar().hide()
        self.tools_tabs.setStyleSheet(
            "QTabWidget{background:#07080f;border:0;}"
            "QTabWidget::pane{border:0;background:#07080f;margin-top:0;}"
        )
        lay.addWidget(self.tools_tabs, 1)
        return page

    def _add_tool_tabs(self):
        from app.features.tools.dialog import ToolsDialog
        from data_organizer import DataOrganizer
        from data_pro_widget import DataProWidget
        from extra_tools import ValidadorWidget
        from performance_widget import PerformanceWidget
        from paramount_assist_widget import ParamountAssistWidget
        from text_corrector_widget import TextCorrectorWidget
        from email_codes_admin_widget import EmailCodesAdminWidget
        from site_leads_admin_widget import SiteLeadsAdminWidget
        from temp_mail_widget import TempMailWidget

        helper = ToolsDialog(self)
        browser_manager = getattr(getattr(self, "browser_widget", None), "browser_manager", None)
        widgets = [
            helper.create_card_generator_tab(),
            helper.create_cep_generator_tab(),
            helper.create_account_formatter_tab(),
            DataOrganizer(),
            ValidadorWidget(),
            PerformanceWidget(),
            DataProWidget(self.db),
            TextCorrectorWidget(),
            ParamountAssistWidget(browser_manager=browser_manager),
            EmailCodesAdminWidget(),
            SiteLeadsAdminWidget(),
            TempMailWidget(),
        ]
        self.data_pro_tab = widgets[6]
        self._tool_descriptions = [description for _, description in TOOLS_METADATA]
        for (name, _), widget in zip(TOOLS_METADATA, widgets):
            self.tools_tabs.addTab(widget, name)

    def _build_tools_header(self):
        frame = QFrame()
        frame.setStyleSheet(card_qss("default", radius=10))
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(12)

        title_box = QVBoxLayout()
        title = QLabel("Ferramentas")
        title.setStyleSheet(label_qss("title"))
        self.tools_context_label = QLabel("Escolha uma ferramenta para trabalhar com dados, texto, perfis e sistema.")
        self.tools_context_label.setWordWrap(True)
        self.tools_context_label.setStyleSheet(label_qss("subtitle"))
        title_box.addWidget(title)
        title_box.addWidget(self.tools_context_label)
        layout.addLayout(title_box, 1)

        self.tools_counter_label = QLabel("0 ferramentas")
        self.tools_counter_label.setAlignment(Qt.AlignCenter)
        self.tools_counter_label.setMinimumWidth(120)
        self.tools_counter_label.setStyleSheet(COUNTER_QSS)
        layout.addWidget(self.tools_counter_label)
        return frame

    def _update_tools_header(self, index):
        if not hasattr(self, "tools_counter_label"):
            return
        count = self.tools_tabs.count() if hasattr(self, "tools_tabs") else 0
        self.tools_counter_label.setText(f"{count} ferramentas")
        if 0 <= index < len(getattr(self, "_tool_descriptions", [])):
            name = self.tools_tabs.tabText(index)
            self.tools_context_label.setText(f"{name}: {self._tool_descriptions[index]}")
