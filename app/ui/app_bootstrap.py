# -*- coding: utf-8 -*-
"""Bootstrap visual do QApplication.

Configura paleta global Qt, fonte padrao, estilo Fusion e aplica o tema dark
unificado. Tambem expoe `create_splash` para integrar com a janela principal.
"""
from __future__ import annotations

from PyQt5.QtGui import QColor, QFont, QFontDatabase, QPalette
from PyQt5.QtWidgets import QApplication

from app.ui.app_theme import DARK_STYLE_PRO


def create_application(argv):
    """Cria QApplication com paleta e tema globais aplicados."""
    app = QApplication(argv)
    configure_application(app)
    return app


def configure_application(app: QApplication) -> None:
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    app.setPalette(build_dark_palette())
    _apply_default_font(app)
    app.setStyleSheet(DARK_STYLE_PRO)


def _apply_default_font(app: QApplication) -> None:
    """Define Segoe UI / Inter como familia padrao com fallback seguro."""
    families = QFontDatabase().families()
    preferred = ["Segoe UI", "Inter", "SF Pro Text", "DejaVu Sans"]
    chosen = next((f for f in preferred if f in families), None)
    font = QFont(chosen) if chosen else app.font()
    font.setPointSize(10)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)


def build_dark_palette() -> QPalette:
    """Paleta Qt sincronizada com a paleta do design system."""
    palette = QPalette()
    # superficies base
    palette.setColor(QPalette.Window, QColor(7, 8, 15))
    palette.setColor(QPalette.WindowText, QColor(241, 245, 249))
    palette.setColor(QPalette.Base, QColor(15, 23, 42))
    palette.setColor(QPalette.AlternateBase, QColor(17, 28, 47))
    # tooltips
    palette.setColor(QPalette.ToolTipBase, QColor(15, 23, 42))
    palette.setColor(QPalette.ToolTipText, QColor(241, 245, 249))
    # texto
    palette.setColor(QPalette.Text, QColor(241, 245, 249))
    palette.setColor(QPalette.PlaceholderText, QColor(71, 85, 105))
    # botoes
    palette.setColor(QPalette.Button, QColor(11, 22, 38))
    palette.setColor(QPalette.ButtonText, QColor(241, 245, 249))
    palette.setColor(QPalette.BrightText, QColor(34, 211, 238))
    # selecao / highlight
    palette.setColor(QPalette.Highlight, QColor(6, 182, 212))
    palette.setColor(QPalette.HighlightedText, QColor(7, 8, 15))
    # links
    palette.setColor(QPalette.Link, QColor(34, 211, 238))
    palette.setColor(QPalette.LinkVisited, QColor(8, 145, 178))
    return palette


def create_splash(app_name: str = "Telegram Collector Pro", version: str = "v12.0"):
    """Cria e retorna um LaunchSplash pronto para uso opcional pelo bootstrap.

    Import lazy para evitar penalizar quem nao usa splash.
    """
    from app.ui.splash import LaunchSplash
    return LaunchSplash(app_name=app_name, version=version)


__all__ = [
    "create_application",
    "configure_application",
    "build_dark_palette",
    "create_splash",
]
