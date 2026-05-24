# -*- coding: utf-8 -*-
"""Tema visual unificado do Telegram Collector Pro.

Camada global do design system. As ferramentas continuam podendo ter QSS
proprio, mas todos os widgets padrao agora compartilham:

- paleta cyberpunk neon (cyan/teal sobre superficies escuras)
- tipografia tecnica (mono em badges, headers, status)
- estados consistentes (hover/focus/pressed/disabled)
- "glow" simulado em foco e itens ativos via bordas brilhantes
- gradientes sutis em superficies elevadas

Todos os seletores anteriores foram preservados — esta versao apenas estende.
"""
from __future__ import annotations

from app.ui.components import (
    FONT_MONO,
    FONT_UI,
    PALETTE,
    scroll_qss,
)


DARK_STYLE_PRO = f"""
/* ============================== BASE ============================== */
QMainWindow, QDialog {{
    background: {PALETTE.bg};
    color: {PALETTE.text};
}}

QWidget {{
    background: transparent;
    color: {PALETTE.text};
    font-family: {FONT_UI};
    font-size: 12px;
}}

QToolTip {{
    background: #0f172a;
    color: {PALETTE.text};
    border: 1px solid {PALETTE.border_strong};
    border-radius: 6px;
    padding: 7px 10px;
    font-family: {FONT_UI};
}}

/* ============================ TEXTOS ============================== */
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
    font-family: {FONT_MONO};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
}}

QLabel[variant="eyebrow"] {{
    color: {PALETTE.primary_light};
    font-family: {FONT_MONO};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 3px;
}}

QLabel[variant="display"] {{
    color: {PALETTE.text};
    font-family: {FONT_UI};
    font-size: 22px;
    font-weight: 800;
    letter-spacing: -0.5px;
}}

QLabel[role="kbd"] {{
    background: {PALETTE.card_alt};
    color: {PALETTE.text};
    border: 1px solid {PALETTE.border_strong};
    border-bottom: 2px solid {PALETTE.border_strong};
    border-radius: 6px;
    padding: 1px 6px;
    font-family: {FONT_MONO};
    font-size: 11px;
    font-weight: 700;
}}

/* ========================= SUPERFICIES ============================ */
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
    border: 1px solid {PALETTE.border_glow};
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {PALETTE.card},
        stop:1 {PALETTE.card_alt}
    );
}}

QFrame#GlowCard {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:1,
        stop:0 {PALETTE.card},
        stop:1 {PALETTE.card_alt}
    );
    border: 1px solid {PALETTE.border_strong};
    border-radius: 12px;
}}

QFrame#GlowCard:hover {{
    border: 1px solid {PALETTE.border_glow};
}}

QFrame#NavSidebar, QFrame#Sidebar {{
    background: {PALETTE.panel};
    border: none;
    border-right: 1px solid {PALETTE.border};
}}

QFrame#HeaderBar, QFrame#TopBar {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {PALETTE.card_alt},
        stop:1 {PALETTE.panel}
    );
    border: none;
    border-bottom: 1px solid {PALETTE.border};
}}

QFrame#FooterBar, QFrame#StatusBar {{
    background: {PALETTE.panel};
    border: none;
    border-top: 1px solid {PALETTE.border};
}}

QFrame#Divider {{
    background: {PALETTE.border};
    border: none;
    max-height: 1px;
    min-height: 1px;
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
    font-family: {FONT_MONO};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 1px;
}}

QScrollArea {{
    border: none;
    background: transparent;
}}

/* ============================= CAMPOS ============================= */
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox, QDateEdit, QTimeEdit {{
    min-height: 34px;
    background: {PALETTE.panel};
    color: #e2e8f0;
    border: 1px solid {PALETTE.border};
    border-radius: 8px;
    padding: 7px 10px;
    font-family: {FONT_UI};
    selection-background-color: #0e7490;
    selection-color: #ffffff;
}}

QLineEdit:hover, QPlainTextEdit:hover, QTextEdit:hover,
QComboBox:hover, QSpinBox:hover, QDoubleSpinBox:hover {{
    border-color: {PALETTE.border_strong};
}}

QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus,
QComboBox:focus, QSpinBox:focus, QDoubleSpinBox:focus {{
    border: 2px solid {PALETTE.primary_light};
    background: #0b1b2d;
    padding: 6px 9px;
}}

QLineEdit:disabled, QPlainTextEdit:disabled, QTextEdit:disabled,
QComboBox:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {{
    color: {PALETTE.faint};
    background: rgba(15,23,42,0.45);
    border-color: rgba(71,85,105,0.20);
}}

QLineEdit::placeholder, QTextEdit::placeholder {{
    color: {PALETTE.faint};
}}

/* Variante mono — para logs, tokens, codigo */
QLineEdit[variant="mono"], QPlainTextEdit[variant="mono"], QTextEdit[variant="mono"] {{
    font-family: {FONT_MONO};
    font-size: 12px;
    color: {PALETTE.primary_light};
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

QComboBox:hover::down-arrow {{
    border-top-color: {PALETTE.primary_light};
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

QSpinBox::up-button, QSpinBox::down-button,
QDoubleSpinBox::up-button, QDoubleSpinBox::down-button {{
    background: transparent;
    border: none;
    width: 22px;
}}

/* ============================ BOTOES ============================== */
QPushButton {{
    min-height: 34px;
    background: rgba(148,163,184,0.06);
    color: {PALETTE.text};
    border: 1px solid rgba(125,211,252,0.16);
    border-radius: 8px;
    padding: 8px 14px;
    font-family: {FONT_UI};
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 0.2px;
}}

QPushButton:hover {{
    background: rgba(125,211,252,0.14);
    border: 1px solid {PALETTE.border_glow};
    color: #ffffff;
}}

QPushButton:focus {{
    outline: none;
    border: 1px solid {PALETTE.primary_light};
}}

QPushButton:pressed {{
    background: rgba(8,145,178,0.32);
    padding-top: 9px;
}}

QPushButton:disabled {{
    background: rgba(71,85,105,0.22);
    color: {PALETTE.faint};
    border-color: rgba(71,85,105,0.20);
}}

QPushButton#Primary, QPushButton[action="primary"], QPushButton[role="primary"] {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {PALETTE.primary},
        stop:1 {PALETTE.primary_dark}
    );
    color: #ffffff;
    border: 1px solid {PALETTE.border_glow};
}}

QPushButton#Primary:hover, QPushButton[action="primary"]:hover, QPushButton[role="primary"]:hover {{
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 {PALETTE.primary_light},
        stop:1 {PALETTE.primary}
    );
    border: 1px solid {PALETTE.primary_light};
}}

QPushButton#Primary:pressed, QPushButton[action="primary"]:pressed, QPushButton[role="primary"]:pressed {{
    background: {PALETTE.primary_dark};
}}

QPushButton#Success, QPushButton[action="success"], QPushButton[role="success"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PALETTE.success}, stop:1 #047857);
    color: #ffffff;
    border: 1px solid rgba(16,185,129,0.55);
}}

QPushButton#Success:hover, QPushButton[action="success"]:hover, QPushButton[role="success"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #34d399, stop:1 {PALETTE.success});
    border-color: #34d399;
}}

QPushButton#Danger, QPushButton[action="danger"], QPushButton[role="danger"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PALETTE.danger}, stop:1 #b91c1c);
    color: #ffffff;
    border: 1px solid rgba(239,68,68,0.55);
}}

QPushButton#Danger:hover, QPushButton[action="danger"]:hover, QPushButton[role="danger"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #f87171, stop:1 {PALETTE.danger});
    border-color: #f87171;
}}

QPushButton#Warning, QPushButton[action="warning"], QPushButton[role="warning"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PALETTE.warning}, stop:1 #b45309);
    color: #ffffff;
    border: 1px solid rgba(245,158,11,0.55);
}}

QPushButton#Warning:hover, QPushButton[action="warning"]:hover, QPushButton[role="warning"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #fbbf24, stop:1 {PALETTE.warning});
    border-color: #fbbf24;
}}

QPushButton[secondary="true"], QPushButton[role="secondary"] {{
    background: rgba(148,163,184,0.06);
    border: 1px solid rgba(125,211,252,0.16);
    color: {PALETTE.muted};
}}

QPushButton[role="ghost"] {{
    background: transparent;
    border: 1px solid {PALETTE.border};
    color: {PALETTE.muted};
}}

QPushButton[role="ghost"]:hover {{
    color: {PALETTE.primary_light};
    border-color: {PALETTE.border_glow};
    background: rgba(34,211,238,0.06);
}}

QPushButton[role="icon"] {{
    min-height: 30px;
    min-width: 30px;
    padding: 0px;
    background: transparent;
    border: 1px solid transparent;
    border-radius: 8px;
}}

QPushButton[role="icon"]:hover {{
    background: rgba(34,211,238,0.10);
    border-color: {PALETTE.border_strong};
}}

/* =========================== NAV ITENS ============================ */
QPushButton[role="nav"] {{
    text-align: left;
    min-height: 38px;
    background: transparent;
    color: {PALETTE.muted};
    border: none;
    border-left: 3px solid transparent;
    border-radius: 0px;
    padding: 6px 14px;
    font-family: {FONT_UI};
    font-size: 12px;
    font-weight: 600;
}}

QPushButton[role="nav"]:hover {{
    color: {PALETTE.text};
    background: rgba(34,211,238,0.06);
    border-left: 3px solid {PALETTE.border_strong};
}}

QPushButton[role="nav"]:checked,
QPushButton[role="nav"][active="true"] {{
    color: #ffffff;
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 rgba(34,211,238,0.22),
        stop:1 rgba(34,211,238,0)
    );
    border-left: 3px solid {PALETTE.primary_light};
    font-weight: 800;
}}

/* ===================== TABELAS, LISTAS, ARVORE ==================== */
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

QTableWidget::item:hover, QTableView::item:hover,
QTreeWidget::item:hover, QListWidget::item:hover {{
    background: rgba(34,211,238,0.08);
}}

QTableWidget::item:selected, QTableView::item:selected,
QTreeWidget::item:selected, QListWidget::item:selected {{
    background: rgba(6,182,212,0.34);
    color: #ffffff;
}}

QHeaderView::section {{
    background: #0b2235;
    color: #67e8f9;
    border: none;
    border-bottom: 1px solid rgba(125,211,252,0.18);
    padding: 9px 10px;
    font-family: {FONT_MONO};
    font-size: 11px;
    font-weight: 800;
    letter-spacing: 0.6px;
}}

QTableCornerButton::section {{
    background: #0b2235;
    border: none;
}}

/* ============================= ABAS =============================== */
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
    border-bottom: 2px solid transparent;
    border-radius: 8px;
    padding: 6px 12px;
    margin-right: 7px;
    font-family: {FONT_UI};
    font-size: 12px;
    font-weight: 800;
    letter-spacing: 0.3px;
}}

QTabBar::tab:selected {{
    color: #ffffff;
    background: rgba(8,145,178,0.42);
    border-color: {PALETTE.border_strong};
    border-bottom: 2px solid {PALETTE.primary_light};
}}

QTabBar::tab:hover {{
    color: #ffffff;
    background: rgba(125,211,252,0.10);
    border-color: rgba(125,211,252,0.30);
}}

/* ========================== CHECK / RADIO ========================== */
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

QCheckBox::indicator:hover {{
    border-color: {PALETTE.primary_light};
}}

QCheckBox::indicator:checked {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {PALETTE.primary_light}, stop:1 {PALETTE.primary});
    border: 1px solid {PALETTE.primary_light};
}}

QRadioButton {{
    color: {PALETTE.text};
    spacing: 8px;
    background: transparent;
}}

QRadioButton::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 8px;
    border: 1px solid rgba(125,211,252,0.28);
    background: {PALETTE.panel};
}}

QRadioButton::indicator:checked {{
    background: qradialgradient(cx:0.5, cy:0.5, radius:0.5, fx:0.5, fy:0.5,
                                stop:0 {PALETTE.primary_light},
                                stop:0.45 {PALETTE.primary_light},
                                stop:0.5 {PALETTE.panel},
                                stop:1 {PALETTE.panel});
    border: 1px solid {PALETTE.primary_light};
}}

/* ========================== PROGRESS BAR =========================== */
QProgressBar {{
    background: {PALETTE.panel};
    border: 1px solid {PALETTE.border};
    border-radius: 6px;
    height: 12px;
    text-align: center;
    color: {PALETTE.muted};
    font-family: {FONT_MONO};
    font-size: 10px;
    font-weight: 700;
}}

QProgressBar::chunk {{
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 {PALETTE.primary},
        stop:1 {PALETTE.primary_light}
    );
    border-radius: 5px;
}}

/* ============================= SLIDER =============================== */
QSlider::groove:horizontal {{
    height: 4px;
    background: {PALETTE.panel};
    border-radius: 2px;
}}

QSlider::sub-page:horizontal {{
    background: {PALETTE.primary};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    width: 16px;
    height: 16px;
    margin: -6px 0;
    background: {PALETTE.primary_light};
    border: 2px solid {PALETTE.bg};
    border-radius: 8px;
}}

QSlider::handle:horizontal:hover {{
    background: #67e8f9;
}}

/* ============================== MENU ============================== */
QMenu {{
    background: #0b1626;
    border: 1px solid {PALETTE.border_strong};
    border-radius: 8px;
    color: {PALETTE.text};
    padding: 6px;
    font-family: {FONT_UI};
}}

QMenu::item {{
    padding: 7px 22px;
    border-radius: 6px;
}}

QMenu::item:selected {{
    background: rgba(6,182,212,0.20);
    color: #ffffff;
}}

QMenu::separator {{
    height: 1px;
    background: {PALETTE.border};
    margin: 4px 6px;
}}

QMessageBox {{
    background: {PALETTE.bg};
}}

/* ========================== STATUS BAR ============================ */
QStatusBar {{
    background: {PALETTE.panel};
    color: {PALETTE.muted};
    border-top: 1px solid {PALETTE.border};
    font-family: {FONT_MONO};
    font-size: 11px;
}}

QStatusBar::item {{
    border: none;
}}

/* =========================== TOOL BAR ============================= */
QToolBar {{
    background: {PALETTE.panel};
    border: none;
    spacing: 4px;
    padding: 4px;
}}

QToolButton {{
    background: transparent;
    color: {PALETTE.muted};
    border: 1px solid transparent;
    border-radius: 6px;
    padding: 5px 8px;
}}

QToolButton:hover {{
    background: rgba(34,211,238,0.10);
    color: {PALETTE.primary_light};
    border-color: {PALETTE.border_strong};
}}

QToolButton:checked {{
    background: rgba(34,211,238,0.18);
    color: {PALETTE.primary_light};
    border-color: {PALETTE.border_glow};
}}

/* ====================== DENSIDADE COMPACTA ======================== */
/* Aplicada pela janela principal para telas menores. */
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


LIGHT_STYLE_PRO = f"""
QMainWindow, QDialog {{ background:#f7fafc; color:#0f172a; }}
QWidget {{ background:transparent; color:#0f172a; font-family:{FONT_UI}; font-size:12px; }}
QGroupBox {{ background:#ffffff; border:1px solid #dbe7f3; border-radius:10px; }}
QFrame#Panel, QFrame#Card, QFrame#Header, QFrame#InfoCard, QFrame#ToolCard {{
    background:#ffffff; border:1px solid #dbe7f3; border-radius:10px;
}}
QGroupBox {{ margin-top:16px; padding:14px; padding-top:30px; }}
QGroupBox::title {{
    subcontrol-origin:margin; left:14px; top:4px;
    color:#0e7490; font-family:{FONT_MONO}; font-weight:800; letter-spacing:1px;
}}
QLineEdit, QPlainTextEdit, QTextEdit, QComboBox, QSpinBox, QDoubleSpinBox {{
    min-height:34px; background:#ffffff; color:#0f172a; border:1px solid #cbd5e1;
    border-radius:8px; padding:7px 10px;
}}
QLineEdit:focus, QPlainTextEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border:2px solid #0891b2; padding:6px 9px;
}}
QPushButton {{
    min-height:34px; background:#eef6fb; color:#0f172a; border:1px solid #cbd5e1;
    border-radius:8px; padding:8px 14px; font-weight:700;
}}
QPushButton:hover {{ background:#dff3fb; border-color:#0891b2; }}
QPushButton#Primary, QPushButton[action="primary"], QPushButton[role="primary"] {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #06b6d4, stop:1 #0891b2);
    color:white; border:1px solid #22d3ee;
}}
QPushButton#Primary:hover, QPushButton[action="primary"]:hover, QPushButton[role="primary"]:hover {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #22d3ee, stop:1 #06b6d4);
}}
QPushButton#Success, QPushButton[action="success"], QPushButton[role="success"] {{
    background:#059669; color:white; border:none;
}}
QPushButton#Danger, QPushButton[action="danger"], QPushButton[role="danger"] {{
    background:#dc2626; color:white; border:none;
}}
QTableWidget, QTableView, QTreeWidget, QListWidget {{
    background:#ffffff; color:#0f172a; border:1px solid #dbe7f3; border-radius:8px;
    gridline-color:#e2e8f0; selection-background-color:#bae6fd; selection-color:#0f172a;
}}
QHeaderView::section {{
    background:#e0f2fe; color:#0f172a; border:none; padding:9px 10px;
    font-family:{FONT_MONO}; font-weight:800;
}}
QTabWidget::pane {{ border:1px solid #dbe7f3; border-radius:8px; background:#f7fafc; margin-top:8px; }}
QTabBar::tab {{
    min-height:34px; min-width:104px; background:#ffffff; color:#475569;
    border:1px solid #dbe7f3; border-radius:8px; padding:6px 12px; margin-right:7px; font-weight:800;
}}
QTabBar::tab:selected {{ color:#0f172a; background:#e0f2fe; border-color:#0891b2; border-bottom:2px solid #0891b2; }}
QProgressBar::chunk {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #22d3ee);
}}
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
