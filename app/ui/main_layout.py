#!/usr/bin/env python3
"""Montagem da interface e navegacao principal do SimpleApp."""

import importlib
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QMessageBox, QSizePolicy, QSplitter, QTabWidget, QVBoxLayout, QWidget, QShortcut

from app.ui.main_pages import CRUNCHYROLL_AVAILABLE
from app.ui.shell_widgets import AppStatusBar, HeaderBar, SidebarNav
from app_hub import GlobalSearchDialog


class MainLayoutMixin:
    def init_ui(self):
        root = QWidget()
        self._app_root = root
        self.setCentralWidget(root)
        root_lay = QVBoxLayout(root)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)
        root.setContentsMargins(0, 0, 0, 0)

        # ── Header
        self.header = HeaderBar()
        root_lay.addWidget(self.header)

        # ── Corpo: sidebar + stack (QSplitter para ser redimensionável)
        self.body_splitter = QSplitter(Qt.Horizontal)
        self.body_splitter.setStyleSheet(
            "QSplitter::handle{background:transparent;width:0px;}"
        )
        self.body_splitter.setChildrenCollapsible(False)
        self.body_splitter.setHandleWidth(0)

        self.sidebar = SidebarNav(show_crunchyroll=CRUNCHYROLL_AVAILABLE)
        self.sidebar.tab_changed.connect(self._on_nav)
        self.sidebar.tool_requested.connect(self.show_tools_tab)
        self.sidebar.pin_btn.clicked.connect(self.toggle_always_on_top)
        self.sidebar.fs_btn.clicked.connect(self.toggle_fullscreen)
        self.sidebar.compact_btn.clicked.connect(self.toggle_compact_mode)
        self.body_splitter.addWidget(self.sidebar)

        # Stack pages
        self.main_tabs = QTabWidget()
        self.main_tabs.setObjectName("MainTabs")
        self.main_tabs.setStyleSheet("QTabWidget#MainTabs::pane{border:none;background:transparent;}")
        self.main_tabs.tabBar().hide()
        self.main_tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.body_splitter.addWidget(self.main_tabs)

        # Sidebar não encolhe, conteúdo pega todo o resto
        self.body_splitter.setStretchFactor(0, 0)
        self.body_splitter.setStretchFactor(1, 1)

        root_lay.addWidget(self.body_splitter, 1)

        # ── Status bar customizada
        self.status_bar = AppStatusBar()
        root_lay.addWidget(self.status_bar)

        # ── Atalhos globais
        QShortcut(QKeySequence("F11"),    self, self.toggle_fullscreen)
        QShortcut(QKeySequence("Escape"), self, self._exit_fullscreen)
        QShortcut(QKeySequence("Return"), self, self._shortcut_generate)
        QShortcut(QKeySequence("Space"),  self, self._shortcut_generate)
        QShortcut(QKeySequence("Ctrl+G"), self, self.generate_pair)
        QShortcut(QKeySequence("Ctrl+C"), self, self._shortcut_copy)
        QShortcut(QKeySequence("Ctrl+Shift+R"), self, self.reload_current_page)
        QShortcut(QKeySequence("Ctrl+Alt+R"), self, self.restart_application)
        QShortcut(QKeySequence("Return"), self, self._shortcut_generate)
        QShortcut(QKeySequence("Ctrl+G"), self, self._shortcut_generate)
        QShortcut(QKeySequence("Ctrl+C"), self, self._shortcut_copy)

        # Constrói as páginas
        self._build_pages()
        self.open_page_by_name("Gerador")
        QTimer.singleShot(80, self._apply_responsive_shell)
        QTimer.singleShot(1200, self._run_startup_tasks)
        self.update_stats()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_responsive_shell()

    def _set_visual_density(self, density: str):
        """Aplica densidade visual sem reconstruir as telas."""
        if getattr(self, "_visual_density", None) == density:
            return
        self._visual_density = density
        targets = [self]
        root = getattr(self, "_app_root", None)
        if root is not None:
            targets.append(root)
            targets.extend(root.findChildren(QWidget))
        for widget in targets:
            try:
                widget.setProperty("density", density)
                widget.style().unpolish(widget)
                widget.style().polish(widget)
                widget.update()
            except Exception:
                pass

    def _apply_responsive_shell(self):
        """Adapta o casco principal para janelas estreitas ou ultra-wide redimensionadas."""
        if not hasattr(self, "sidebar") or not hasattr(self, "body_splitter"):
            return
        width = max(0, self.width())
        if width <= 0:
            return

        density = "compact" if width < 1180 else "wide" if width >= 1850 else "normal"
        self._set_visual_density(density)

        # O modo compacto deve depender da largura real da janela, nao de
        # fullscreen. Em monitor ultra-wide, fullscreen ainda tem espaco de sobra.
        force_slim = width < 1180
        current_slim = getattr(self.sidebar, "_slim", False)
        if force_slim != current_slim:
            self.sidebar.set_collapsed(force_slim)
            self.sidebar.set_current(self.main_tabs.currentIndex())

        side_attr = "SLIM_W" if force_slim else "FULL_W"
        side_w = int(getattr(self.sidebar, side_attr, self.sidebar.width()) or self.sidebar.width())
        content_w = max(480, width - side_w)
        if width > side_w + 420:
            self.body_splitter.setSizes([side_w, content_w])

    def reload_current_page(self):
        """Reconstrói a tela atual para puxar alterações visuais sem reiniciar tudo."""
        if not hasattr(self, "main_tabs") or self.main_tabs.count() == 0:
            return
        idx = self.main_tabs.currentIndex()
        title = self.main_tabs.tabText(idx)

        if self._page_has_active_browser(title):
            reply = QMessageBox.question(
                self,
                "Recarregar tela",
                "Existe navegador aberto nesta tela. Recarregar a interface pode perder o controle visual dessa sessão.\n\n"
                "Continuar mesmo assim?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return

        builder = self._page_builder_for_title(title)
        if not builder:
            self.status_bar.showMessage("Nao consegui recarregar esta tela.", 2500)
            return

        self._reload_modules_for_title(title)
        old_widget = self.main_tabs.widget(idx)
        try:
            new_widget = builder()
        except Exception as exc:
            QMessageBox.critical(self, "Recarregar tela", f"Nao foi possivel recriar a tela:\n{exc}")
            return

        self.main_tabs.removeTab(idx)
        self.main_tabs.insertTab(idx, new_widget, title)
        if old_widget:
            old_widget.deleteLater()
        self.main_tabs.setCurrentIndex(idx)
        self.sidebar.set_current(idx)
        self.header.set_title(self.tab_titles[idx] if idx < len(self.tab_titles) else title)
        self.status_bar.showMessage("Tela atual recarregada.", 2500)

    def _page_has_active_browser(self, title):
        if "naveg" not in (title or "").lower():
            return False
        manager = getattr(getattr(self, "browser_widget", None), "browser_manager", None)
        if not manager or not hasattr(manager, "get_active_browsers"):
            return False
        try:
            return bool(manager.get_active_browsers())
        except Exception:
            return False

    def _page_builder_for_title(self, title):
        lower = (title or "").lower()
        if "in" in lower and "cio" in lower:
            return self._build_inicio_page
        if "gerador" in lower:
            return self._build_gerador_page
        if "naveg" in lower:
            return self._build_navegador_page
        if "ia" in lower:
            return self._build_ai_page
        if "crunchy" in lower:
            return self._build_crunchyroll_page
        if "notas" in lower:
            return self._build_notas_page
        if "config" in lower:
            return self._build_config_page
        if "ferramentas" in lower:
            return self._build_ferramentas_page
        return None

    def _reload_modules_for_title(self, title):
        lower = (title or "").lower()
        modules = [
            "app.ui.components",
            "app.ui.shell_widgets",
            "app.ui.tools_page_assets",
        ]
        if "in" in lower and "cio" in lower:
            modules += ["app.features.app_hub.widget", "app.features.app_hub", "app_hub"]
        elif "gerador" in lower:
            modules += ["app.ui.generator_page"]
        elif "naveg" in lower:
            modules += [
                "app.features.browser.styles",
                "app.features.browser.widget",
                "profile_defaults_widget",
                "browser_widget",
            ]
        elif "ia" in lower:
            modules += ["app.features.ai_assistant.widget", "ai_assistant_widget"]
        elif "crunchy" in lower:
            modules += [
                "app.ui.crunchyroll_page",
                "app.features.crunchyroll.widget",
                "app.features.crunchyroll.login_widget",
                "crunchyroll_widget",
                "crunchyroll_login_widget",
            ]
        elif "notas" in lower:
            modules += ["app.features.notepad.widget", "notepad_widget"]
        elif "config" in lower:
            modules += [
                "app.features.app_hub.settings_widget",
                "app.features.app_hub.maintenance_panel",
                "app.features.app_hub.logs_panel",
                "app.features.app_hub",
                "app_hub",
            ]
        elif "ferramentas" in lower:
            modules += [
                "app.ui.tools_page",
                "app.features.tools.dialog",
                "app.features.performance.widget",
                "app.features.data_organizer.widget",
                "app.features.data_pro.widget",
                "app.features.text_corrector.widget",
                "app.features.paramount_assist.widget",
                "performance_widget",
                "data_organizer",
                "data_pro_widget",
                "text_corrector_widget",
                "paramount_assist_widget",
                "extra_tools",
            ]

        importlib.invalidate_caches()
        for name in modules:
            module = sys.modules.get(name)
            if not module:
                continue
            try:
                importlib.reload(module)
            except Exception:
                # Hot reload é conveniência; se um módulo não recarregar, a tela ainda tenta abrir.
                pass

    def _on_nav(self, idx):
        if idx < 0 or idx >= self.main_tabs.count():
            return
        self.main_tabs.setCurrentIndex(idx)
        self.header.set_title(self.tab_titles[idx] if idx < len(self.tab_titles) else "")

    def _page_index_by_name(self, name):
        target = name.lower()
        for i, title in enumerate(self.tab_titles):
            if target in title.lower():
                return i
        for i in range(self.main_tabs.count()):
            if target in self.main_tabs.tabText(i).lower():
                return i
        return -1

    def open_page_by_name(self, name):
        idx = self._page_index_by_name(name)
        if idx >= 0:
            self.main_tabs.setCurrentIndex(idx)
            self.sidebar.set_current(idx)
            self.header.set_title(self.tab_titles[idx] if idx < len(self.tab_titles) else name)

    def open_notes_page(self):
        self.open_page_by_name("Notas")

    def open_global_search(self):
        manager = getattr(getattr(self, "browser_widget", None), "browser_manager", None)
        GlobalSearchDialog(manager, self).exec_()

    def _run_startup_tasks(self):
        # Nao roda backup pesado na abertura: perfis de navegador podem ter muitos
        # arquivos e isso deixa o Windows marcar o app como "nao respondendo".
        self.status_bar.showMessage("✅ Pronto", 1500)
