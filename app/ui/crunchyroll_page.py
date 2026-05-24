#!/usr/bin/env python3
"""Builder e acoes da pagina Crunchyroll."""

from importlib.util import find_spec

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QTabWidget, QVBoxLayout, QWidget

from app.ui.shell_widgets import TAB_TOP_QSS


CRUNCHYROLL_AVAILABLE = find_spec("crunchyroll_widget") is not None
CRUNCHYROLL_LOGIN_AVAILABLE = find_spec("crunchyroll_login_widget") is not None


class CrunchyrollPageMixin:
    def _build_crunchyroll_page(self):
        page = QWidget()
        page.setStyleSheet("background: #07080f;")
        lay = QVBoxLayout(page)
        lay.setContentsMargins(10, 8, 10, 8)
        lay.setSpacing(8)

        quick = QFrame()
        quick.setStyleSheet(
            "QFrame{background:#0b1626;border:1px solid rgba(34,211,238,0.12);border-radius:8px;}"
        )
        quick_lay = QHBoxLayout(quick)
        quick_lay.setContentsMargins(10, 8, 10, 8)
        quick_lay.setSpacing(8)
        title = QLabel("Crunchyroll")
        title.setStyleSheet("color:#e2e8f0;font-weight:900;font-size:14px;background:transparent;border:none;")
        quick_lay.addWidget(title)
        quick_lay.addStretch()

        back_btn = QPushButton("← Voltar")
        back_btn.setFixedHeight(32)
        back_btn.setToolTip("Voltar para o início do Crunchyroll")
        back_btn.clicked.connect(self._crunchyroll_back)
        quick_lay.addWidget(back_btn)

        for text, tab_name in [
            ("Contas", "Contas"),
            ("Cartões", "Cartões"),
            ("Resultados", "Resultados"),
            ("Verificador", "Verificador"),
        ]:
            btn = QPushButton(text)
            btn.setFixedHeight(32)
            btn.clicked.connect(lambda _, name=tab_name: self._open_crunchyroll_bot_tab(name))
            quick_lay.addWidget(btn)

        if CRUNCHYROLL_LOGIN_AVAILABLE:
            login_btn = QPushButton("Login/Auth")
            login_btn.setFixedHeight(32)
            login_btn.clicked.connect(self._open_crunchyroll_login_tab)
            quick_lay.addWidget(login_btn)

        refresh_btn = QPushButton("Atualizar resultados")
        refresh_btn.setFixedHeight(32)
        refresh_btn.clicked.connect(self._refresh_crunchyroll_results)
        quick_lay.addWidget(refresh_btn)
        lay.addWidget(quick)

        self.crunchy_tabs = QTabWidget()
        self.crunchy_tabs.setStyleSheet(TAB_TOP_QSS)
        from crunchyroll_widget import CrunchyrollWidget

        self.crunchyroll_tab = CrunchyrollWidget()
        self.crunchy_tabs.addTab(self.crunchyroll_tab, "🍦 Bot Principal")
        if CRUNCHYROLL_LOGIN_AVAILABLE:
            from crunchyroll_login_widget import CrunchyrollLoginWidget

            self.crunchyroll_login_tab = CrunchyrollLoginWidget()
            self.crunchy_tabs.addTab(self.crunchyroll_login_tab, "🔐 Login/Auth")
        lay.addWidget(self.crunchy_tabs)
        return page

    def _open_crunchyroll_bot_tab(self, tab_name):
        if hasattr(self, "crunchy_tabs"):
            self.crunchy_tabs.setCurrentIndex(0)
        inner_tabs = getattr(getattr(self, "crunchyroll_tab", None), "tabs", None)
        if not inner_tabs:
            return
        target = tab_name.lower()
        for i in range(inner_tabs.count()):
            if target in inner_tabs.tabText(i).lower():
                inner_tabs.setCurrentIndex(i)
                break

    def _crunchyroll_back(self):
        if hasattr(self, "crunchy_tabs") and self.crunchy_tabs.currentIndex() != 0:
            self.crunchy_tabs.setCurrentIndex(0)
            self.status_bar.showMessage("✅ Voltou para o Bot Principal", 2000)
            return

        inner_tabs = getattr(getattr(self, "crunchyroll_tab", None), "tabs", None)
        if inner_tabs and inner_tabs.currentIndex() != 0:
            inner_tabs.setCurrentIndex(0)
            self.status_bar.showMessage("✅ Voltou para o Controle do Crunchyroll", 2000)
            return

        self.status_bar.showMessage("ℹ️ Você já está no início do Crunchyroll", 2000)

    def _open_crunchyroll_login_tab(self):
        if hasattr(self, "crunchy_tabs") and self.crunchy_tabs.count() > 1:
            self.crunchy_tabs.setCurrentIndex(1)

    def _refresh_crunchyroll_results(self):
        refreshed = False
        for widget_name in ("crunchyroll_tab", "crunchyroll_login_tab"):
            widget = getattr(self, widget_name, None)
            if widget and hasattr(widget, "load_results"):
                widget.load_results()
                refreshed = True
        if refreshed:
            self.status_bar.showMessage("✅ Resultados do Crunchyroll atualizados", 2500)

