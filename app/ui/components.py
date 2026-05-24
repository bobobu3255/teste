"""Componentes visuais reutilizaveis para o app.

Camada de design system: paleta, tokens (espaco/raio/tipografia) e helpers de
QSS para botoes, cards, inputs, badges, pills e indicadores de status.

Mantem 100% de compatibilidade com a API publica anterior (`button_qss`,
`card_qss`, `panel_qss`, `group_qss`, `table_qss`, `tabs_qss`, `scroll_qss`,
`message_qss`, `field_qss`, `label_qss`, `make_button`, `make_card`,
`make_label`, `make_line_edit`, `make_text_area`, `make_combo`,
`make_section`).

Adicoes v12 design rework:
- TYPOGRAPHY com fontes tecnicas (JetBrains Mono / Cascadia Code)
- SPACING_* / RADIUS_* tokens consolidados
- BUTTON com glow simulado em hover/focus
- pill_qss / make_pill / status_dot_qss / make_status_dot
- accent_card_qss / divider_qss / kbd_qss
"""
from __future__ import annotations

from dataclasses import dataclass

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
)


# ---------------------------------------------------------------------------
# Paleta
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class UiPalette:
    bg: str = "#07080f"
    panel: str = "#0b1626"
    card: str = "#0f172a"
    card_alt: str = "#111c2f"
    border: str = "rgba(125,211,252,0.14)"
    border_strong: str = "rgba(34,211,238,0.34)"
    border_glow: str = "rgba(34,211,238,0.55)"
    text: str = "#f1f5f9"
    muted: str = "#94a3b8"
    faint: str = "#475569"
    primary: str = "#06b6d4"
    primary_dark: str = "#0891b2"
    primary_light: str = "#22d3ee"
    success: str = "#10b981"
    danger: str = "#ef4444"
    warning: str = "#f59e0b"
    purple: str = "#8b5cf6"


PALETTE = UiPalette()

# ---------------------------------------------------------------------------
# Tokens
# ---------------------------------------------------------------------------
# Espacos seguem grade de 4px para consistencia em toda a aplicacao.
SPACING_XS = 4
SPACING_SM = 8
SPACING_MD = 12
SPACING_LG = 16
SPACING_XL = 24
SPACING_XXL = 32

RADIUS_XS = 4
RADIUS_SM = 6
RADIUS_MD = 8
RADIUS_LG = 10
RADIUS_XL = 12
RADIUS_PILL = 999

# Tipografia
FONT_UI = "'Segoe UI', 'Inter', system-ui, sans-serif"
FONT_MONO = "'JetBrains Mono', 'Cascadia Code', 'Consolas', 'Menlo', monospace"
FONT_DISPLAY = "'Segoe UI', 'Inter', system-ui, sans-serif"


@dataclass(frozen=True)
class Typography:
    family_ui: str = FONT_UI
    family_mono: str = FONT_MONO
    family_display: str = FONT_DISPLAY
    size_xs: str = "10px"
    size_sm: str = "11px"
    size_md: str = "12px"
    size_lg: str = "13px"
    size_xl: str = "14px"
    size_2xl: str = "18px"
    size_3xl: str = "22px"
    size_display: str = "28px"


TYPOGRAPHY = Typography()


# ---------------------------------------------------------------------------
# Botoes
# ---------------------------------------------------------------------------
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
    "display": ("22px", "800", PALETTE.text),
    "eyebrow": ("10px", "700", PALETTE.primary_light),
}


def button_qss(role: str = "primary", size: str = "md") -> str:
    """QSS de botao — agora com glow simulado no hover/focus."""
    base, hover, text = BUTTON_COLORS.get(role, BUTTON_COLORS["primary"])
    height, font_size, padding = BUTTON_SIZES.get(size, BUTTON_SIZES["md"])
    border = "1px solid rgba(125,211,252,0.18)" if role in {"secondary", "ghost"} else "1px solid transparent"
    hover_text = PALETTE.text if role in {"secondary", "ghost"} else text
    return f"""
        QPushButton {{
            min-height: {height}px;
            background: {base};
            color: {text};
            border: {border};
            border-radius: 8px;
            padding: {padding};
            font-family: {FONT_UI};
            font-size: {font_size};
            font-weight: 700;
            letter-spacing: 0.2px;
        }}
        QPushButton:hover {{
            background: {hover};
            color: {hover_text};
            border: 1px solid {PALETTE.border_glow};
        }}
        QPushButton:focus {{
            outline: none;
            border: 1px solid {PALETTE.primary_light};
        }}
        QPushButton:pressed {{
            background: {base};
            padding-top: {int(padding.split(' ')[0].rstrip('px')) + 1}px;
        }}
        QPushButton:disabled {{
            background: rgba(71,85,105,0.22);
            color: {PALETTE.faint};
            border: 1px solid rgba(71,85,105,0.20);
        }}
    """


def make_button(text: str, role: str = "primary", size: str = "md", tooltip: str = "") -> QPushButton:
    button = QPushButton(text)
    button.setCursor(Qt.PointingHandCursor)
    button.setStyleSheet(button_qss(role, size))
    if tooltip:
        button.setToolTip(tooltip)
    return button


# ---------------------------------------------------------------------------
# Cards e superficies
# ---------------------------------------------------------------------------
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


def accent_card_qss(radius: int = RADIUS_LG) -> str:
    """Card com gradient sutil cyan e borda de glow — usado em destaque."""
    return f"""
        QFrame {{
            background: qlineargradient(
                x1:0, y1:0, x2:1, y2:1,
                stop:0 {PALETTE.card},
                stop:1 {PALETTE.card_alt}
            );
            border: 1px solid {PALETTE.border_strong};
            border-radius: {radius}px;
        }}
        QFrame:hover {{
            border: 1px solid {PALETTE.border_glow};
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
            font-family: {FONT_UI};
            font-weight: 700;
        }}
        QGroupBox::title {{
            subcontrol-origin: margin;
            left: 14px;
            top: 4px;
            padding: 1px 8px;
            color: {title_color};
            background: transparent;
            font-family: {FONT_MONO};
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1px;
        }}
    """


def divider_qss() -> str:
    return f"""
        QFrame {{
            background: {PALETTE.border};
            border: none;
            min-height: 1px;
            max-height: 1px;
        }}
    """


# ---------------------------------------------------------------------------
# Tabelas, abas e scroll
# ---------------------------------------------------------------------------
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
            font-family: {FONT_MONO};
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.6px;
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
            border-bottom: 2px solid transparent;
            border-radius: {RADIUS_MD}px;
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
            background: rgba(34,211,238,0.45);
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
        QScrollBar::handle:horizontal:hover {
            background: rgba(34,211,238,0.45);
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


# ---------------------------------------------------------------------------
# Mensagens e alertas
# ---------------------------------------------------------------------------
def message_qss(kind: str = "info") -> str:
    colors = {
        "info": (PALETTE.primary, "rgba(6,182,212,0.08)"),
        "success": (PALETTE.success, "rgba(16,185,129,0.10)"),
        "warning": (PALETTE.warning, "rgba(245,158,11,0.12)"),
        "danger": (PALETTE.danger, "rgba(239,68,68,0.12)"),
    }
    color, bg = colors.get(kind, colors["info"])
    return f"""
        QLabel {{
            background: {bg};
            border: 1px solid {color};
            border-left: 3px solid {color};
            border-radius: {RADIUS_MD}px;
            color: {color};
            padding: 10px 14px;
            font-family: {FONT_UI};
            font-size: 12px;
            font-weight: 700;
        }}
    """


# ---------------------------------------------------------------------------
# Pills, badges e indicadores
# ---------------------------------------------------------------------------
def pill_qss(tone: str = "default") -> str:
    """Pill compacta para tags, badges, status."""
    tones = {
        "default": (PALETTE.muted, "rgba(125,211,252,0.10)", "rgba(125,211,252,0.32)"),
        "primary": (PALETTE.primary_light, "rgba(34,211,238,0.10)", "rgba(34,211,238,0.55)"),
        "success": (PALETTE.success, "rgba(16,185,129,0.10)", "rgba(16,185,129,0.55)"),
        "warning": (PALETTE.warning, "rgba(245,158,11,0.10)", "rgba(245,158,11,0.55)"),
        "danger":  (PALETTE.danger,  "rgba(239,68,68,0.12)",  "rgba(239,68,68,0.55)"),
    }
    fg, bg, border = tones.get(tone, tones["default"])
    return f"""
        QLabel {{
            color: {fg};
            background: {bg};
            border: 1px solid {border};
            border-radius: {RADIUS_PILL}px;
            padding: 2px 10px;
            font-family: {FONT_MONO};
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
        }}
    """


def make_pill(text: str, tone: str = "default") -> QLabel:
    label = QLabel(text.upper())
    label.setStyleSheet(pill_qss(tone))
    label.setAlignment(Qt.AlignCenter)
    return label


def status_dot_qss(tone: str = "primary", size: int = 8) -> str:
    tones = {
        "primary": PALETTE.primary_light,
        "success": PALETTE.success,
        "warning": PALETTE.warning,
        "danger":  PALETTE.danger,
        "muted":   PALETTE.muted,
    }
    color = tones.get(tone, PALETTE.primary_light)
    return f"""
        QLabel {{
            background: {color};
            border: 1px solid {color};
            border-radius: {size // 2}px;
            min-width: {size}px;
            max-width: {size}px;
            min-height: {size}px;
            max-height: {size}px;
        }}
    """


def make_status_dot(tone: str = "primary", size: int = 8) -> QLabel:
    dot = QLabel()
    dot.setStyleSheet(status_dot_qss(tone, size))
    dot.setFixedSize(size, size)
    return dot


def kbd_qss() -> str:
    """Estilo para teclas / atalhos."""
    return f"""
        QLabel {{
            color: {PALETTE.text};
            background: {PALETTE.card_alt};
            border: 1px solid {PALETTE.border_strong};
            border-bottom: 2px solid {PALETTE.border_strong};
            border-radius: {RADIUS_SM}px;
            padding: 1px 6px;
            font-family: {FONT_MONO};
            font-size: 11px;
            font-weight: 700;
        }}
    """


# ---------------------------------------------------------------------------
# Helpers de construcao
# ---------------------------------------------------------------------------
def make_card(radius: int = 8, padding: int = 12, spacing: int = 8, tone: str = "default"):
    card = QFrame()
    card.setStyleSheet(card_qss(tone, radius))
    layout = QVBoxLayout(card)
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(spacing)
    return card, layout


def make_accent_card(padding: int = SPACING_LG, spacing: int = SPACING_SM, radius: int = RADIUS_LG):
    card = QFrame()
    card.setStyleSheet(accent_card_qss(radius))
    layout = QVBoxLayout(card)
    layout.setContentsMargins(padding, padding, padding, padding)
    layout.setSpacing(spacing)
    return card, layout


def label_qss(variant: str = "body") -> str:
    size, weight, color = LABEL_STYLES.get(variant, LABEL_STYLES["body"])
    if variant == "mono":
        family = FONT_MONO
    elif variant == "eyebrow":
        family = FONT_MONO
        return (
            f"color:{color}; font-size:{size}; font-weight:{weight}; "
            f"font-family:{family}; background:transparent; border:none; letter-spacing:3px;"
        )
    elif variant == "display":
        family = FONT_DISPLAY
        return (
            f"color:{color}; font-size:{size}; font-weight:{weight}; "
            f"font-family:{family}; background:transparent; border:none; letter-spacing:-0.5px;"
        )
    else:
        family = FONT_UI
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
            font-family: {FONT_UI};
            selection-background-color: #0e7490;
            selection-color: #ffffff;
        }}
        QLineEdit:hover, QTextEdit:hover, QComboBox:hover, QSpinBox:hover {{
            border-color: {PALETTE.border_strong};
        }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
            border: 2px solid {PALETTE.primary_light};
            padding: {('3px 7px' if compact else '6px 9px')};
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
    frame, layout = make_card(radius=RADIUS_MD, padding=SPACING_MD, spacing=SPACING_XS, tone="default")
    layout.addWidget(make_label(title, "section"))
    if subtitle:
        layout.addWidget(make_label(subtitle, "muted", word_wrap=True))
    return frame, layout


def make_status_row(text: str, tone: str = "primary"):
    """Linha com ponto colorido + label compacta."""
    container = QFrame()
    layout = QHBoxLayout(container)
    layout.setContentsMargins(0, 0, 0, 0)
    layout.setSpacing(SPACING_SM)
    layout.addWidget(make_status_dot(tone))
    layout.addWidget(make_label(text, "muted"))
    layout.addStretch(1)
    return container


__all__ = [
    "PALETTE",
    "UiPalette",
    "TYPOGRAPHY",
    "Typography",
    "FONT_UI",
    "FONT_MONO",
    "FONT_DISPLAY",
    "SPACING_XS",
    "SPACING_SM",
    "SPACING_MD",
    "SPACING_LG",
    "SPACING_XL",
    "SPACING_XXL",
    "RADIUS_XS",
    "RADIUS_SM",
    "RADIUS_MD",
    "RADIUS_LG",
    "RADIUS_XL",
    "RADIUS_PILL",
    "BUTTON_COLORS",
    "BUTTON_SIZES",
    "LABEL_STYLES",
    "button_qss",
    "make_button",
    "card_qss",
    "accent_card_qss",
    "panel_qss",
    "group_qss",
    "divider_qss",
    "table_qss",
    "tabs_qss",
    "scroll_qss",
    "message_qss",
    "pill_qss",
    "make_pill",
    "status_dot_qss",
    "make_status_dot",
    "kbd_qss",
    "make_card",
    "make_accent_card",
    "label_qss",
    "make_label",
    "field_qss",
    "make_line_edit",
    "make_text_area",
    "make_combo",
    "make_section",
    "make_status_row",
]
