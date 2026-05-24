# -*- coding: utf-8 -*-
"""Tema visual unificado do Telegram Collector Pro.

Este arquivo e a camada global do design system. As ferramentas podem continuar
usando estilos proprios, mas os widgets padrao agora partem da mesma paleta,
raio, espaco e comportamento visual.
"""
from __future__ import annotations

from app.ui.components import PALETTE, scroll_qss


DARK_STYLE_PRO = f"""
/* Base */
QMainWindow, QDialog {{
    background: {PALETTE.bg};
    color: {PALETTE.text};
}}

QWidget {{
    background: transparent;
    color: {PALETTE.text};
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 12px;
}}

QToolTip {{
    background: #0f172a;
    color: {PALETTE.text};
    border: 1px solid {PALETTE.border_strong};
    border-radius: 6px;
    padding: 7px 9px;
}}

/* Textos */
QLabel {{
    color: {PALETTE.text};
    background: transparent;
    border: none;
}}

QLabel[variant="muted"] {{
    color: {PALETTE.muted};
}}

QLabel[variant="section"] {{
    color: {PALETTE.primary};
    font-size: 11px;
    font-weight: 800;
}}

/* Superficies */
QGroupBox {{
    background: {PALETTE.card};
    border: 1px solid {PALETTE.border};
    border-radius: 10px;
}}

QFrame#Panel, QFrame#Card, QFrame#Header, QFrame#InfoCard, QFrame#ToolCard {{
    background: {PALETTE.card};
    border: 1px solid {PALETTE.border};
    border-radius: 10px;
}}

QFrame[active="true"], QFrame#ActiveCard {{
    border-color: {PALETTE.border_strong};
    background: {PALETTE.card_alt};
}}

QGroupBox {{
    margin-top: 16px;
    padding: 14px;
    padding-top: 30px;
    font-weight: 700;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    top: 4px;
    padding: 1px 8px;
    color: {PALETTE.primary};
    background: transparent;
    font-size: 11px;
    font-weight: 800;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

/* Campos */
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
    min-height: 34px;
    background: {PALETTE.panel};
    color: #e2e8f0;
    border: 1px solid {PALETTE.border};
    border-radius: 8px;
    padding: 7px 10px;
    selection-background-color: #0e7490;
    selection-color: #ffffff;
}}

QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover, QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: rgba(125,211,252,0.28);
}}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {PALETTE.border_strong};
    background: #0b1b2d;
}}

QLineEdit:disabled, QPlainTextEdit:disabled, QTextEdit:disabled, QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    color: {PALETTE.faint};
    background: rgba(15,23,42,0.45);
    border-color: rgba(71,85,105,0.20);
}}

QLineEdit::placeholder, QTextEdit::placeholder {{
    color: {PALETTE.faint};
}}

QComboBox {{
    padding-right: 30px;
}}

QComboBox::drop-down {{
    border: none;
    width: 28px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid {PALETTE.muted};
    margin-right: 10px;
}}

QComboBox QAbstractItemView {{
    background: #0b1626;
    color: {PALETTE.text};
    border: 1px solid {PALETTE.border_strong};
    border-radius: 8px;
    padding: 6px;
    outline: none;
    selection-background-color: rgba(6,182,212,0.34);
}}

QComboBox QAbstractItemView::item {{
    min-height: 26px;
    padding: 6px 10px;
    border-radius: 6px;
}}

QSpinBox::up-button, QSpinBox::down-button, QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: transparent;
    border: none;
    width: 22px;
}}

/* Botoes */
QPushButton {{
    min-height: 34px;
    background: rgba(148,163,184,0.06);
    color: {PALETTE.text};
    border: 1px solid rgba(125,211,252,0.16);
    border-radius: 8px;
    padding: 8px 14px;
    font-size: 12px;
    font-weight: 700;
}}

QPushButton:hover {{
    background: rgba(125,211,252,0.12);
    border-color: {PALETTE.border_strong};
}}

QPushButton:pressed {{
    background: rgba(8,145,178,0.28);
}}

QPushButton:disabled {{
    background: rgba(71,85,105,0.22);
    color: {PALETTE.faint};
    border-color: rgba(71,85,105,0.20);
}}

QPushButton#Primary, QPushButton[action="primary"], QPushButton[role="primary"] {{
    background: {PALETTE.primary_dark};
    color: #ffffff;
    border: none;
}}

QPushButton#Primary:hover, QPushButton[action="primary"]:hover, QPushButton[role="primary"]:hover {{
    background: {PALETTE.primary};
}}

QPushButton#Success, QPushButton[action="success"], QPushButton[role="success"] {{
    background: #059669;
    color: #ffffff;
    border: none;
}}

QPushButton#Success:hover, QPushButton[action="success"]:hover, QPushButton[role="success"]:hover {{
    background: {PALETTE.success};
}}

QPushButton#Danger, QPushButton[action="danger"], QPushButton[role="danger"] {{
    background: #b91c1c;
    color: #ffffff;
    border: none;
}}

QPushButton#Danger:hover, QPushButton[action="danger"]:hover, QPushButton[role="danger"]:hover {{
    background: {PALETTE.danger};
}}

QPushButton#Warning, QPushButton[action="warning"], QPushButton[role="warning"] {{
    background: #b45309;
    color: #ffffff;
    border: none;
}}

QPushButton#Warning:hover, QPushButton[action="warning"]:hover, QPushButton[role="warning"]:hover {{
    background: {PALETTE.warning};
}}

QPushButton[secondary="true"], QPushButton[role="secondary"] {{
    background: rgba(148,163,184,0.06);
    border: 1px solid rgba(125,211,252,0.16);
    color: {PALETTE.muted};
}}

/* Tabelas e listas */
QTableWidget, QTableView, QTreeWidget, QListWidget {{
    background: {PALETTE.panel};
    alternate-background-color: rgba(125,211,252,0.035);
    color: {PALETTE.text};
    border: 1px solid {PALETTE.border};
    border-radius: 8px;
    gridline-color: rgba(125,211,252,0.08);
    selection-background-color: rgba(6,182,212,0.34);
    selection-color: #ffffff;
    outline: none;
}}

QTableWidget::item, QTableView::item, QTreeWidget::item, QListWidget::item {{
    padding: 8px 9px;
    border: none;
}}

QTableWidget::item:selected, QTableView::item:selected, QTreeWidget::item:selected, QListWidget::item:selected {{
    background: rgba(6,182,212,0.34);
    color: #ffffff;
}}

QHeaderView::section {{
    background: #0b2235;
    color: #67e8f9;
    border: none;
    border-bottom: 1px solid rgba(125,211,252,0.18);
    padding: 9px 10px;
    font-size: 11px;
    font-weight: 800;
}}

QTableCornerButton::section {{
    background: #0b2235;
    border: none;
}}

/* Abas */
QTabWidget::pane {{
    border: 1px solid {PALETTE.border};
    border-radius: 8px;
    background: {PALETTE.bg};
    margin-top: 8px;
}}

QTabBar::tab {{
    min-height: 34px;
    min-width: 104px;
    background: rgba(15,23,42,0.78);
    color: {PALETTE.muted};
    border: 1px solid rgba(125,211,252,0.12);
    border-radius: 8px;
    padding: 6px 12px;
    margin-right: 7px;
    font-size: 12px;
    font-weight: 800;
}}

QTabBar::tab:selected {{
    color: #ffffff;
    background: rgba(8,145,178,0.42);
    border-color: {PALETTE.border_strong};
}}

QTabBar::tab:hover {{
    color: #ffffff;
    background: rgba(125,211,252,0.10);
    border-color: rgba(125,211,252,0.30);
}}

/* Checks e barras */
QCheckBox {{
    color: {PALETTE.text};
    spacing: 8px;
    background: transparent;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid rgba(125,211,252,0.28);
    background: {PALETTE.panel};
}}

QCheckBox::indicator:checked {{
    background: {PALETTE.success};
    border-color: {PALETTE.success};
}}

QRadioButton {{
    color: {PALETTE.text};
    spacing: 8px;
    background: transparent;
}}

QProgressBar {{
    background: {PALETTE.panel};
    border: 1px solid {PALETTE.border};
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: {PALETTE.muted};
}}

QProgressBar::chunk {{
    background: {PALETTE.primary};
    border-radius: 4px;
}}

QMenu {{
    background: #0b1626;
    border: 1px solid {PALETTE.border};
    border-radius: 8px;
    color: {PALETTE.text};
    padding: 6px;
}}

QMenu::item {{
    padding: 7px 20px;
    border-radius: 6px;
}}

QMenu::item:selected {{
    background: rgba(6,182,212,0.18);
    color: #ffffff;
}}

QMessageBox {{
    background: {PALETTE.bg};
}}

/* Densidade responsiva aplicada pela janela principal.
   Compacta telas menores sem depender de cada ferramenta implementar tudo. */
QMainWindow[density="compact"] QPushButton,
QWidget[density="compact"] QPushButton {{
    min-height: 30px;
    padding: 6px 10px;
    font-size: 11px;
    border-radius: 7px;
}}

QMainWindow[density="compact"] QLineEdit,
QMainWindow[density="compact"] QPlainTextEdit,
QMainWindow[density="compact"] QTextEdit,
QMainWindow[density="compact"] QComboBox,
QMainWindow[density="compact"] QSpinBox,
QMainWindow[density="compact"] QDoubleSpinBox,
QWidget[density="compact"] QLineEdit,
QWidget[density="compact"] QPlainTextEdit,
QWidget[density="compact"] QTextEdit,
QWidget[density="compact"] QComboBox,
QWidget[density="compact"] QSpinBox,
QWidget[density="compact"] QDoubleSpinBox {{
    min-height: 30px;
    padding: 5px 8px;
    font-size: 11px;
    border-radius: 7px;
}}

QMainWindow[density="compact"] QTabBar::tab,
QWidget[density="compact"] QTabBar::tab {{
    min-height: 29px;
    min-width: 76px;
    padding: 5px 8px;
    margin-right: 5px;
    font-size: 11px;
}}

QMainWindow[density="compact"] QGroupBox,
QWidget[density="compact"] QGroupBox {{
    margin-top: 12px;
    padding: 10px;
    padding-top: 25px;
}}

QMainWindow[density="compact"] QGroupBox::title,
QWidget[density="compact"] QGroupBox::title {{
    left: 10px;
    top: 3px;
}}

QMainWindow[density="compact"] QHeaderView::section,
QWidget[density="compact"] QHeaderView::section {{
    padding: 7px 8px;
    font-size: 10px;
}}

QMainWindow[density="compact"] QTableWidget::item,
QMainWindow[density="compact"] QTableView::item,
QWidget[density="compact"] QTableWidget::item,
QWidget[density="compact"] QTableView::item {{
    padding: 6px 7px;
}}

{scroll_qss()}
"""


LIGHT_STYLE_PRO = """
QMainWindow, QDialog { background:#f7fafc; color:#0f172a; }
QWidget { background:transparent; color:#0f172a; font-family:'Segoe UI', Arial, sans-serif; font-size:12px; }
QGroupBox { background:#ffffff; border:1px solid #dbe7f3; border-radius:10px; }
QFrame#Panel, QFrame#Card, QFrame#Header, QFrame#InfoCard, QFrame#ToolCard { background:#ffffff; border:1px solid #dbe7f3; border-radius:10px; }
QGroupBox { margin-top:16px; padding:14px; padding-top:30px; }
QGroupBox::title { subcontrol-origin:margin; left:14px; top:4px; color:#0e7490; font-weight:800; }
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {
    min-height:34px; background:#ffffff; color:#0f172a; border:1px solid #cbd5e1;
    border-radius:8px; padding:7px 10px;
}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus { border-color:#0891b2; }
QPushButton {
    min-height:34px; background:#eef6fb; color:#0f172a; border:1px solid #cbd5e1;
    border-radius:8px; padding:8px 14px; font-weight:700;
}
QPushButton:hover { background:#dff3fb; border-color:#0891b2; }
QPushButton#Primary, QPushButton[action="primary"], QPushButton[role="primary"] { background:#0891b2; color:white; border:none; }
QPushButton#Success, QPushButton[action="success"], QPushButton[role="success"] { background:#059669; color:white; border:none; }
QPushButton#Danger, QPushButton[action="danger"], QPushButton[role="danger"] { background:#dc2626; color:white; border:none; }
QTableWidget, QTableView, QTreeWidget, QListWidget {
    background:#ffffff; color:#0f172a; border:1px solid #dbe7f3; border-radius:8px;
    gridline-color:#e2e8f0; selection-background-color:#bae6fd; selection-color:#0f172a;
}
QHeaderView::section { background:#e0f2fe; color:#0f172a; border:none; padding:9px 10px; font-weight:800; }
QTabWidget::pane { border:1px solid #dbe7f3; border-radius:8px; background:#f7fafc; margin-top:8px; }
QTabBar::tab { min-height:34px; min-width:104px; background:#ffffff; color:#475569; border:1px solid #dbe7f3; border-radius:8px; padding:6px 12px; margin-right:7px; font-weight:800; }
QTabBar::tab:selected { color:#0f172a; background:#e0f2fe; border-color:#0891b2; }
"""


DARK_STYLE = DARK_STYLE_PRO
LIGHT_STYLE = LIGHT_STYLE_PRO


def get_theme(theme_name: str = "dark") -> str:
    themes = {
        "dark": DARK_STYLE_PRO,
        "light": LIGHT_STYLE_PRO,
        "dark_pro": DARK_STYLE_PRO,
        "light_pro": LIGHT_STYLE_PRO,
    }
    return themes.get((theme_name or "dark").lower(), DARK_STYLE_PRO)


__all__ = ["DARK_STYLE_PRO", "LIGHT_STYLE_PRO", "DARK_STYLE", "LIGHT_STYLE", "get_theme"]
