from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication

from app.ui.app_theme import DARK_STYLE_PRO


def create_application(argv):
    app = QApplication(argv)
    configure_application(app)
    return app


def configure_application(app):
    app.setQuitOnLastWindowClosed(False)
    app.setStyle("Fusion")
    app.setPalette(build_dark_palette())
    app.setStyleSheet(DARK_STYLE_PRO)


def build_dark_palette():
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(10, 14, 26))
    palette.setColor(QPalette.WindowText, QColor(241, 245, 249))
    palette.setColor(QPalette.Base, QColor(17, 24, 39))
    palette.setColor(QPalette.AlternateBase, QColor(15, 23, 42))
    palette.setColor(QPalette.ToolTipBase, QColor(30, 41, 59))
    palette.setColor(QPalette.ToolTipText, QColor(241, 245, 249))
    palette.setColor(QPalette.Text, QColor(241, 245, 249))
    palette.setColor(QPalette.Button, QColor(8, 145, 178))
    palette.setColor(QPalette.ButtonText, QColor(241, 245, 249))
    palette.setColor(QPalette.BrightText, QColor(34, 211, 238))
    palette.setColor(QPalette.Highlight, QColor(6, 182, 212))
    palette.setColor(QPalette.HighlightedText, QColor(10, 14, 26))
    return palette
