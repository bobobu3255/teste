#!/usr/bin/env python3
"""Estilos compartilhados da IA Local."""
from __future__ import annotations

from app.ui.app_theme import DARK_STYLE_PRO

BG = "#05070d"
PANEL = "#07111f"
PANEL_RAISED = "#0b1626"
CARD = "#0b1220"
TEXT = "#e5e7eb"
TITLE = "#f8fafc"
MUTED = "#94a3b8"
FAINT = "#64748b"
CYAN = "#22d3ee"
CYAN_SOFT = "rgba(34,211,238,0.22)"
BORDER = "rgba(148,163,184,0.18)"


def ai_widget_qss() -> str:
    return DARK_STYLE_PRO + """
        QWidget{background:#05070d;color:#e5e7eb;font-family:'Segoe UI',Arial,sans-serif;font-size:13px;}
        QPushButton{background:#0b1220;border:1px solid rgba(148,163,184,0.22);border-radius:10px;color:#e5e7eb;padding:8px 12px;font-weight:700;}
        QPushButton:hover{background:#111827;border-color:rgba(34,211,238,0.42);}
        QPushButton:pressed{background:#0f172a;}
        QLineEdit,QComboBox,QTextEdit,QListWidget{background:#07111f;border:1px solid rgba(148,163,184,0.18);border-radius:10px;color:#f8fafc;padding:7px;}
        QLineEdit:focus,QComboBox:focus,QTextEdit:focus{border-color:rgba(34,211,238,0.55);}
        QComboBox::drop-down{border:0;width:24px;}
        QScrollBar:vertical{background:#05070d;width:10px;border-radius:5px;}
        QScrollBar::handle:vertical{background:#155e75;border-radius:5px;min-height:32px;}
    """


def label_qss(kind: str = "body") -> str:
    styles = {
        "title": "color:#f8fafc;font-size:18px;font-weight:850;background:transparent;border:none;",
        "title_big": "color:#f8fafc;font-size:22px;font-weight:900;background:transparent;border:none;",
        "subtitle": "color:#64748b;font-size:11px;background:transparent;border:none;",
        "subtitle_big": "color:#94a3b8;font-size:12px;background:transparent;border:none;",
        "small": "color:#94a3b8;font-size:11px;font-weight:800;background:transparent;border:none;",
        "hint": "color:#7dd3fc;font-size:11px;background:rgba(34,211,238,0.06);border-radius:8px;padding:7px 9px;",
        "attachments": "color:#94a3b8;font-size:11px;background:transparent;border:none;",
        "dialog_title": "color:#f8fafc;font-size:18px;font-weight:850;background:transparent;border:none;",
        "dialog_desc": "color:#94a3b8;background:transparent;border:none;",
        "dialog_section": "color:#94a3b8;font-weight:800;background:transparent;border:none;",
    }
    return styles.get(kind, "color:#e5e7eb;background:transparent;border:none;")


def pill_qss(color: str) -> str:
    return (
        f"color:{color};background:rgba(15,23,42,0.85);"
        f"border:1px solid {color}55;border-radius:10px;padding:6px 10px;font-weight:800;"
    )


def frame_qss(kind: str = "settings") -> str:
    radius = "10px"
    bg = PANEL if kind == "input" else PANEL_RAISED
    border = "rgba(34,211,238,0.22)" if kind == "input" else "rgba(34,211,238,0.18)"
    return f"QFrame{{background:{bg};border:1px solid {border};border-radius:{radius};}}"


def chat_output_qss(minimal: bool = True) -> str:
    if minimal:
        return "QTextEdit{background:#05070d;border:0;color:#e5e7eb;padding:8px 4px;font-size:14px;}"
    return (
        "QTextEdit{background:#05070d;border:1px solid rgba(34,211,238,0.14);"
        "border-radius:10px;color:#e5e7eb;padding:12px;font-size:13px;}"
        "QScrollBar:vertical{background:#07111f;width:10px;border-radius:5px;}"
        "QScrollBar::handle:vertical{background:#164e63;border-radius:5px;}"
    )


def prompt_input_qss(minimal: bool = True) -> str:
    if minimal:
        return "QTextEdit{background:transparent;border:0;color:#f8fafc;padding:4px;font-size:14px;}QTextEdit:focus{border:0;}"
    return (
        "QTextEdit{background:#08111f;border:1px solid rgba(148,163,184,0.10);"
        "border-radius:12px;color:#f8fafc;padding:9px;font-size:13px;}"
        "QTextEdit:focus{border-color:rgba(34,211,238,0.45);}"
    )


def menu_qss() -> str:
    return (
        "QMenu{background:#07111f;color:#e5e7eb;border:1px solid rgba(34,211,238,0.22);border-radius:10px;padding:6px;}"
        "QMenu::item{padding:8px 18px;border-radius:8px;}"
        "QMenu::item:selected{background:#0f172a;color:#67e8f9;}"
    )


def chat_body_open() -> str:
    return "<html><body style='background:#05070d;color:#e5e7eb;font-family:Segoe UI,Arial,sans-serif;margin:0;'><div style='padding:8px 0 18px 0;'>"


def image_style() -> str:
    return "max-width:420px;max-height:420px;border-radius:10px;border:1px solid rgba(148,163,184,0.20);"


def message_style(role: str) -> tuple[str, str, str, str, str]:
    if role == "user":
        return "right", "#0e7490", "rgba(103,232,249,0.35)", "Voce", "70%"
    if role == "system":
        return "center", "#0b1220", "rgba(148,163,184,0.20)", "Sistema", "88%"
    return "left", "#05070d", "rgba(148,163,184,0.10)", "IA Local", "88%"
