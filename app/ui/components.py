"""Componentes visuais reutilizaveis para o app.

Este modulo nao muda nenhuma tela por conta propria. Ele fornece pecas pequenas
para as proximas fases deixarem botoes, cards, inputs e titulos mais consistentes.
"""
from __future__ import annotations

from dataclasses import dataclass

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QComboBox, QFrame, QLabel, QLineEdit, QPushButton, QTextEdit, QVBoxLayout


@dataclass(frozen=True)
class UiPalette:
    bg: str = "#07080f"
    panel: str = "#0b1626"
    card: str = "#0f172a"
    card_alt: str = "#111c2f"
    border: str = "rgba(125,211,252,0.14)"
    border_strong: str = "rgba(34,211,238,0.34)"
    text: str = "#f1f5f9"
    muted: str = "#94a3b8"
    faint: str = "#475569"
    primary: str = "#06b6d4"
    primary_dark: str = "#0891b2"
    success: str = "#10b981"
    danger: str = "#ef4444"
    warning: str = "#f59e0b"
    purple: str = "#8b5cf6"


PALETTE = UiPalette()

RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 10
RADIUS_XL = 12

BUTTON_COLORS = {
    "primary": (PALETTE.primary_dark, PALETTE.primary, "#ffffff"),
    "secondary": ("rgba(148,163,184,0.06)", "rgba(125,211,252,0.16)", PALETTE.muted),
    "success": ("#059669", PALETTE.success, "#ffffff"),
    "danger": ("#dc2626", PALETTE.danger, "#ffffff"),
    "warning": ("#d97706", PALETTE.warning, "#ffffff"),
    "purple": ("#6d28d9", PALETTE.purple, "#ffffff"),
    "ghost": ("transparent", "rgba(125,211,252,0.10)", PALETTE.muted),
}

BUTTON_SIZES = {
    "sm": (28, "10px", "6px 10px"),
    "md": (34, "11px", "8px 14px"),
    "lg": (40, "12px", "10px 18px"),
}

LABEL_STYLES = {
    "title": ("18px", "800", PALETTE.text),
    "subtitle": ("12px", "500", PALETTE.muted),
    "section": ("11px", "800", PALETTE.primary),
    "body": ("12px", "400", PALETTE.text),
    "muted": ("11px", "400", PALETTE.muted),
    "mono": ("12px", "500", PALETTE.primary),
}


def button_qss(role: str = "primary", size: str = "md") -> str:
    base, hover, text = BUTTON_COLORS.get(role, BUTTON_COLORS["primary"])
    height, font_size, padding = BUTTON_SIZES.get(size, BUTTON_SIZES["md"])
    border = "1px solid rgba(125,211,252,0.18)" if role in {"secondary", "ghost"} else "none"
    hover_text = PALETTE.text if role in {"secondary", "ghost"} else text
    return f"""
        QPushButton {{
            min-height: {height}px;
            background: {base};
            color: {text};
            border: {border};
            border-radius: 8px;
            padding: {padding};
            font-size: {font_size};
            font-weight: 700;
        }}
        QPushButton:hover {{
            background: {hover};
            color: {hover_text};
            border-color: {PALETTE.border_strong};
        }}
        QPushButton:pressed {{
            background: {base};
        }}
        QPushButton:disabled {{
            background: rgba(71,85,105,0.22);
            color: {PALETTE.faint};
            border-color: rgba(71,85,105,0.20);
        }}
    """


def make_button(text: str, role: str = "primary", size: str = "md", tooltip: str = "") -> QPushButton:
    button = QPushButton(text)
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(button_qss(role, size))
    if tooltip:
        button.setToolTip(tooltip)
    return button


def card_qss(tone: str = "default", radius: int = 8) -> str:
    bg = PALETTE.card_alt if tone == "raised" else PALETTE.card
    border = PALETTE.border_strong if tone == "active" else PALETTE.border
    return f"""
        QFrame {{
            background: {bg};
            border: 1px solid {border};
            border-radius: {radius}px;
        }}
    """


def panel_qss(radius: int = RADIUS_LG) -> str:
    return f"""
        QWidget, QFrame {{
            background: {PALETTE.panel};
            border: 1px solid {PALETTE.border};
            border-radius: {radius}px;
        }}
    """


def group_qss(accent: str | None = None, radius: int = RADIUS_LG) -> str:
    title_color = accent or PALETTE.primary
    return f"""
        QGroupBox {{
            background: {PALETTE.card};
            border: 1px solid {PALETTE.border};
            border-radius: {radius}px;
            margin-top: 16px;
            padding: 14px;
            padding-top: 30px;
            color: {PALETTE.text};
            font-weight: 700;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            top: 4px;
            padding: 1px 8px;
            color: {title_color};
            background: transparent;
            font-size: 11px;
            font-weight: 800;
        }}
    """


def table_qss(compact: bool = False) -> str:
    row_pad = "6px 8px" if compact else "9px 10px"
    header_pad = "7px 8px" if compact else "10px 10px"
    return f"""
        QTableWidget, QTableView, QTreeWidget {{
            background: {PALETTE.panel};
            alternate-background-color: rgba(125,211,252,0.035);
            color: {PALETTE.text};
            border: 1px solid {PALETTE.border};
            border-radius: {RADIUS_MD}px;
            gridline-color: rgba(125,211,252,0.08);
            selection-background-color: rgba(6,182,212,0.34);
            selection-color: #ffffff;
            outline: none;
        }}
        QTableWidget::item, QTableView::item, QTreeWidget::item {{
            padding: {row_pad};
            border: none;
        }}
        QTableWidget::item:selected, QTableView::item:selected, QTreeWidget::item:selected {{
            background: rgba(6,182,212,0.34);
            color: #ffffff;
        }}
        QHeaderView::section {{
            background: #0b2235;
            color: #67e8f9;
            border: none;
            border-bottom: 1px solid rgba(125,211,252,0.18);
            padding: {header_pad};
            font-size: 11px;
            font-weight: 800;
        }}
        QTableCornerButton::section {{
            background: #0b2235;
            border: none;
        }}
    """


def tabs_qss(compact: bool = False) -> str:
    height = 32 if compact else 36
    width = 94 if compact else 116
    return f"""
        QTabWidget::pane {{
            border: 1px solid {PALETTE.border};
            border-radius: {RADIUS_MD}px;
            background: {PALETTE.bg};
            margin-top: 8px;
        }}
        QTabBar::tab {{
            min-height: {height}px;
            min-width: {width}px;
            background: rgba(15,23,42,0.78);
            color: {PALETTE.muted};
            border: 1px solid rgba(125,211,252,0.12);
            border-radius: {RADIUS_MD}px;
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
    """


def scroll_qss() -> str:
    return """
        QScrollBar:vertical {
            background: transparent;
            width: 10px;
            margin: 4px 2px;
        }
        QScrollBar::handle:vertical {
            background: rgba(125,211,252,0.22);
            border-radius: 5px;
            min-height: 34px;
        }
        QScrollBar::handle:vertical:hover {
            background: rgba(34,211,238,0.36);
        }
        QScrollBar::add-line:vertical,
        QScrollBar::sub-line:vertical,
        QScrollBar::add-page:vertical,
        QScrollBar::sub-page:vertical {
            border: none;
            background: transparent;
            height: 0;
        }
        QScrollBar:horizontal {
            background: transparent;
            height: 10px;
            margin: 2px 4px;
        }
        QScrollBar::handle:horizontal {
            background: rgba(125,211,252,0.22);
            border-radius: 5px;
            min-width: 34px;
        }
        QScrollBar::add-line:horizontal,
        QScrollBar::sub-line:horizontal,
        QScrollBar::add-page:horizontal,
        QScrollBar::sub-page:horizontal {
            border: none;
            background: transparent;
            width: 0;
        }
    """


def message_qss(kind: str = "info") -> str:
    colors = {
        "info": (PALETTE.primary, "rgba(6,182,212,0.08)"),
        "success": (PALETTE.success, "rgba(16,185,129,0.08)"),
        "warning": (PALETTE.warning, "rgba(245,158,11,0.10)"),
        "danger": (PALETTE.danger, "rgba(239,68,68,0.10)"),
    }
    color, bg = colors.get(kind, colors["info"])
    return f"""
        QLabel {{
            background: {bg};
            border: 1px solid {color};
            border-radius: {RADIUS_MD}px;
            color: {color};
            padding: 10px 12px;
            font-size: 12px;
            font-weight: 700;
        }}
    """


def make_card(radius: int = 8, padding: int = 12, spacing: int = 8, tone: str = "default"):
    card = QFrame()
    card.setStyleSheet(card_qss(tone, radius))
    layout = QVBoxLayout(card)
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(spacing)
    return card, layout


def label_qss(variant: str = "body") -> str:
    size, weight, color = LABEL_STYLES.get(variant, LABEL_STYLES["body"])
    family = "'Consolas', 'Cascadia Code', monospace" if variant == "mono" else "'Segoe UI', Arial, sans-serif"
    return (
        f"color:{color}; font-size:{size}; font-weight:{weight}; "
        f"font-family:{family}; background:transparent; border:none;"
    )


def make_label(text: str, variant: str = "body", word_wrap: bool = False) -> QLabel:
    label = QLabel(text)
    label.setStyleSheet(label_qss(variant))
    label.setWordWrap(word_wrap)
    return label


def field_qss(compact: bool = False) -> str:
    height = 28 if compact else 34
    pad = "4px 8px" if compact else "7px 10px"
    return f"""
        QLineEdit, QTextEdit, QComboBox, QSpinBox {{
            min-height: {height}px;
            background: {PALETTE.panel};
            color: #e2e8f0;
            border: 1px solid {PALETTE.border};
            border-radius: 8px;
            padding: {pad};
            selection-background-color: #0e7490;
            selection-color: #ffffff;
        }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
            border-color: {PALETTE.border_strong};
        }}
        QLineEdit:disabled, QTextEdit:disabled, QComboBox:disabled, QSpinBox:disabled {{
            color: {PALETTE.faint};
            background: rgba(15,23,42,0.45);
        }}
    """


def make_line_edit(placeholder: str = "", text: str = "", compact: bool = False, read_only: bool = False) -> QLineEdit:
    field = QLineEdit(text)
    field.setPlaceholderText(placeholder)
    field.setReadOnly(read_only)
    field.setStyleSheet(field_qss(compact))
    return field


def make_text_area(placeholder: str = "", compact: bool = False, read_only: bool = False) -> QTextEdit:
    field = QTextEdit()
    field.setPlaceholderText(placeholder)
    field.setReadOnly(read_only)
    field.setStyleSheet(field_qss(compact))
    return field


def make_combo(items: list[str] | tuple[str, ...] = (), compact: bool = False) -> QComboBox:
    combo = QComboBox()
    combo.addItems(list(items))
    combo.setStyleSheet(field_qss(compact))
    return combo


def make_section(title: str, subtitle: str = ""):
    frame, layout = make_card(radius=8, padding=12, spacing=4, tone="default")
    layout.addWidget(make_label(title, "section"))
    if subtitle:
        layout.addWidget(make_label(subtitle, "muted", word_wrap=True))
    return frame, layout
