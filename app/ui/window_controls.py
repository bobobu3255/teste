#!/usr/bin/env python3
"""Controles de janela, bandeja e persistencia da janela principal."""

import ctypes
import subprocess
import sys

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import QApplication, QMenu, QSystemTrayIcon

from app.core.app_metadata import APP_NAME, APP_TRAY_TOOLTIP, APP_USER_MODEL_ID, APP_WINDOW_TITLE
from app.ui.shell_widgets import CompactWidget, GLOBAL_QSS, create_app_icon
from app_hub import load_app_settings
from settings import BASE_DIR


class MainWindowControlsMixin:
    def _setup_window(self):
        self.setWindowTitle(APP_WINDOW_TITLE)
        self.setGeometry(80, 80, *self.NORMAL_SIZE)
        self.setMinimumSize(900, 600)
        self.setStyleSheet(GLOBAL_QSS)

        # Ícone
        self.app_icon = create_app_icon()
        self.setWindowIcon(self.app_icon)
        if sys.platform == "win32":
            try:
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(APP_USER_MODEL_ID)
            except Exception:
                pass

    def _setup_tray(self):
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray_icon = QSystemTrayIcon(self.app_icon, self)
        menu = QMenu()
        menu.addAction("Mostrar", self._show_normal)
        if hasattr(self, "reload_current_page"):
            menu.addAction("Recarregar tela atual", self.reload_current_page)
        menu.addAction("Reiniciar app", self.restart_application)
        menu.addAction("Modo Compacto", self.toggle_compact_mode)
        menu.addSeparator()
        menu.addAction("Fixar no Topo", self.toggle_always_on_top)
        menu.addSeparator()
        menu.addAction("Sair", self.quit_application)
        self.tray_icon.setContextMenu(menu)
        self.tray_icon.activated.connect(lambda r: self._show_normal() if r == QSystemTrayIcon.DoubleClick else None)
        self.tray_icon.show()
        self.tray_icon.setToolTip(APP_TRAY_TOOLTIP)

    def _show_normal(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()

    def quit_application(self):
        self._force_quit = True
        QApplication.setQuitOnLastWindowClosed(True)
        self._save_state()
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        QApplication.quit()

    def restart_application(self):
        """Fecha esta instancia e abre outra automaticamente."""
        self._force_quit = True
        QApplication.setQuitOnLastWindowClosed(True)
        self._save_state()
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        args = [sys.executable, str(BASE_DIR / "main_app.py")]
        kwargs = {"cwd": str(BASE_DIR)}
        if sys.platform == "win32":
            flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
            flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            kwargs["creationflags"] = flags
        try:
            subprocess.Popen(args, **kwargs)
        finally:
            QApplication.quit()

    def toggle_always_on_top(self):
        self.is_always_on_top = not self.is_always_on_top
        if self.is_always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.sidebar.pin_btn.setStyleSheet(self.sidebar.pin_btn.styleSheet().replace("#475569", "#f43f5e"))
            self.status_bar.showMessage("📌 Janela fixada no topo", 2500)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.status_bar.showMessage("📌 Janela desfixada", 2500)
        self.show()

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
            self.is_fullscreen = False
            self.sidebar.set_collapsed(False)
            self.sidebar.fs_btn.setToolTip("  Tela cheia  [F11]  ")
            self.status_bar.showMessage("⛶ Modo janela", 2000)
        else:
            self._pre_fs_geometry = self.geometry()
            self.showFullScreen()
            self.is_fullscreen = True
            self.sidebar.set_collapsed(True)
            self.sidebar.fs_btn.setToolTip("  Sair da tela cheia  [F11 / Esc]  ")
            self.status_bar.showMessage("⛶ Tela cheia — F11 ou Esc para sair", 3000)

    def _exit_fullscreen(self):
        if self.isFullScreen():
            self.toggle_fullscreen()

    def toggle_compact_mode(self):
        if not hasattr(self, "_compact_widget"):
            self._compact_widget = CompactWidget(self.db, self._address_gen, self)

        if self.is_compact_mode:
            self._compact_widget.hide()
            self.is_compact_mode = False
            QApplication.setQuitOnLastWindowClosed(True)
            self._show_normal()
            self.status_bar.showMessage("🖥️ Modo normal", 2000)
        else:
            QApplication.setQuitOnLastWindowClosed(False)
            self.is_compact_mode = True
            self._restore_compact_pos(self._compact_widget)
            self._compact_widget.show()
            self._compact_widget.raise_()
            self.showMinimized()
            self.status_bar.showMessage("📱 Painel compacto ativo  •  arraste pelo cabeçalho", 3000)

    def _save_state(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("alwaysOnTop", self.is_always_on_top)
        if hasattr(self, "_compact_widget") and self._compact_widget.isVisible():
            pos = self._compact_widget.pos()
            self.settings.setValue("compactX", pos.x())
            self.settings.setValue("compactY", pos.y())

    def _load_state(self):
        geo = self.settings.value("geometry")
        if geo:
            self.restoreGeometry(geo)
        if self.settings.value("alwaysOnTop", False, type=bool):
            self.toggle_always_on_top()

    def _restore_compact_pos(self, widget):
        """Restaura posição salva do painel compacto."""
        x = self.settings.value("compactX", type=int)
        y = self.settings.value("compactY", type=int)
        if x is not None and y is not None:
            screen = QApplication.primaryScreen().availableGeometry()
            # Garante que está dentro da tela
            x = max(0, min(x, screen.right() - widget.width()))
            y = max(0, min(y, screen.bottom() - widget.height()))
            widget.move(x, y)
        else:
            screen = QApplication.primaryScreen().availableGeometry()
            widget.move(screen.right() - widget.width() - 20, screen.top() + 60)

    def closeEvent(self, event):
        self._save_state()
        if (
            not getattr(self, "_force_quit", False)
            and hasattr(self, "_compact_widget")
            and self._compact_widget.isVisible()
        ):
            self.hide()
            event.ignore()
            return
        try:
            close_to_tray = bool(load_app_settings().get("close_to_tray", False))
        except Exception:
            close_to_tray = False
        if close_to_tray and hasattr(self, "tray_icon") and self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                APP_NAME,
                "Minimizado para a bandeja. Use Sair no menu da bandeja para encerrar.",
                QSystemTrayIcon.Information,
                2000,
            )
            event.ignore()
            return
        if hasattr(self, "_compact_widget"):
            self._compact_widget.hide()
        if hasattr(self, "tray_icon"):
            self.tray_icon.hide()
        event.accept()
        self._force_quit = True
        QTimer.singleShot(0, QApplication.quit)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_F11:
            self.toggle_fullscreen()
        else:
            super().keyPressEvent(event)
