#!/usr/bin/env python3
"""Estilos compartilhados das ferramentas internas.

A ideia e tirar aos poucos o CSS solto do dialogo grande, sem alterar a logica
dos geradores. As proximas fases podem migrar uma aba por vez para estes helpers.
"""
from __future__ import annotations

from app.ui.components import PALETTE, button_qss, field_qss, scroll_qss, tabs_qss


TOOL_DIALOG_QSS = f"""
    QDialog {{
        background: {PALETTE.bg};
        color: {PALETTE.text};
        font-family: 'Segoe UI', Arial, sans-serif;
    }}
    QScrollArea {{
        border: none;
        background: transparent;
    }}
    {scroll_qss()}
"""

TOOL_TABS_QSS = tabs_qss(compact=False)


def tool_tab_qss() -> str:
    return f"QWidget{{background:{PALETTE.bg}; color:{PALETTE.text};}}"


def tool_group_qss(accent: str | None = None) -> str:
    color = accent or PALETTE.primary
    return f"""
        QGroupBox {{
            background-color: {PALETTE.card};
            border: 1px solid {PALETTE.border};
            border-radius: 8px;
            margin-top: 16px;
            padding: 16px;
            padding-top: 32px;
            color: {PALETTE.text};
        }}
        QGroupBox::title {{
            color: {color};
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 1px;
            subcontrol-origin: margin;
            left: 14px;
            top: 5px;
        }}
    """


def tool_field_qss(accent: str | None = None) -> str:
    focus = accent or PALETTE.border_strong
    return field_qss(compact=False) + f"""
        QComboBox::drop-down {{ border: 0; width: 24px; }}
        QSpinBox {{ min-width: 80px; }}
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {{
            border-color: {focus};
        }}
    """


def tool_output_qss(accent: str = "#34d399", dashed: bool = False) -> str:
    border_style = "dashed" if dashed else "solid"
    return f"""
        QTextEdit {{
            background-color: #030712;
            border: 1px {border_style} rgba(34, 211, 238, 0.20);
            border-radius: 8px;
            padding: 14px;
            font-family: Consolas, 'Cascadia Code', monospace;
            font-size: 12px;
            color: {accent};
            line-height: 1.5;
        }}
    """


def tool_result_field_qss() -> str:
    return """
        QLineEdit {
            background-color: #030712;
            border: 1px solid rgba(34, 211, 238, 0.18);
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 13px;
            color: #34d399;
            font-weight: 700;
        }
    """


def tool_button_qss(kind: str = "secondary", size: str = "md") -> str:
    role_map = {
        "primary": "primary",
        "success": "success",
        "danger": "danger",
        "warning": "warning",
        "secondary": "secondary",
        "ghost": "ghost",
        "purple": "purple",
    }
    return button_qss(role_map.get(kind, "secondary"), size)


def tool_copy_button_qss() -> str:
    return """
        QPushButton {
            min-width: 34px;
            min-height: 34px;
            background-color: rgba(148, 163, 184, 0.06);
            color: #67e8f9;
            border: 1px solid rgba(125, 211, 252, 0.12);
            border-radius: 8px;
            font-size: 14px;
            font-weight: 800;
        }
        QPushButton:hover {
            background-color: rgba(125, 211, 252, 0.14);
            border-color: rgba(34, 211, 238, 0.34);
        }
    """


def tool_radio_qss() -> str:
    return f"color:{PALETTE.text}; font-weight:700; background:transparent; border:none;"


def tool_status_qss(color: str | None = None) -> str:
    return f"color:{color or PALETTE.muted}; font-size:12px; font-weight:600; background:transparent; border:none;"


def tool_progress_qss() -> str:
    return """
        QProgressBar {
            background:#0f172a;
            border:0;
            border-radius:4px;
            height:8px;
        }
        QProgressBar::chunk {
            background:#22d3ee;
            border-radius:4px;
        }
    """


def tool_light_result_field_qss() -> str:
    return """
        QLineEdit {
            background-color: #ffffff;
            border: 1px solid #d2d2d7;
            border-radius: 8px;
            padding: 10px 12px;
            font-size: 13px;
            color: #1d1d1f;
        }
    """


def tool_light_copy_button_qss() -> str:
    return """
        QPushButton {
            min-width: 34px;
            min-height: 34px;
            background-color: #f3f4f6;
            color: #0f172a;
            border: 1px solid #d2d2d7;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 800;
        }
        QPushButton:hover {
            background-color: #e8e8ed;
        }
    """


def tool_inline_label_qss(color: str = "#64748b", size: int = 12, bold: bool = False, min_width: int | None = None) -> str:
    weight = "700" if bold else "500"
    width = f" min-width: {min_width}px;" if min_width else ""
    return f"font-weight: {weight}; color: {color}; font-size: {size}px;{width}"


def tool_analysis_qss(color: str = "#94a3b8", strong: bool = False) -> str:
    border = color if strong else "rgba(34,211,238,0.16)"
    weight = "font-weight: 700;" if strong else ""
    return (
        f"color: {color}; background: #0b1626; border: 1px solid {border}; "
        f"border-radius: 10px; padding: 10px 12px; font-size: 12px; {weight}"
    )


def tool_stat_tile_qss(color: str = "#c4b5fd") -> str:
    return f"""
        QLabel {{
            background: #07111f;
            border: 1px solid rgba(139, 92, 246, 0.22);
            border-radius: 8px;
            padding: 10px;
            color: {color};
            font-size: 12px;
            font-weight: 900;
        }}
    """


def tool_scroll_area_qss() -> str:
    return "QScrollArea { border: none; background: transparent; }"
