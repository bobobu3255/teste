#!/usr/bin/env python3
"""Estilos compartilhados do Bloco de Notas."""
from __future__ import annotations

BG = "#07111f"
BG_DARK = "#050d1a"
PANEL = "#08111f"
CARD = "#0f172a"
BORDER = "#1e293b"
BORDER_SOFT = "rgba(148,163,184,0.10)"
CYAN = "#06b6d4"
TEXT = "#e2e8f0"
MUTED = "#94a3b8"
FAINT = "#64748b"
SUCCESS = "#a8e6cf"


def notepad_editor_qss() -> str:
    return """
        QPlainTextEdit {
            background-color: #07111f;
            color: #dbeafe;
            border: none;
            padding: 10px 12px;
            selection-background-color: #0e7490;
            selection-color: #ffffff;
        }
    """


def notepad_menu_qss() -> str:
    return "QMenu { background-color: #1e293b; color: white; border: 1px solid #334155; } QMenu::item:selected { background-color: #06b6d4; }"


def toolbar_qss() -> str:
    return (
        "QFrame { background-color: #08111f; border-bottom: 1px solid #132238; }"
        "QPushButton { background: rgba(148,163,184,0.06); color: #cbd5e1; padding: 7px 11px; "
        "border: 1px solid rgba(148,163,184,0.10); border-radius: 7px; font-size: 12px; font-weight: 700; }"
        "QPushButton:hover { background-color: rgba(6,182,212,0.12); color: #f8fafc; border-color: rgba(6,182,212,0.35); }"
        "QPushButton:pressed { background-color: rgba(6,182,212,0.20); }"
    )


def toolbar_icon_qss() -> str:
    return "QPushButton { font-size: 16px; color: #06b6d4; } QPushButton:hover { background-color: #1e293b; }"


def toolbar_toggle_qss() -> str:
    return (
        "QPushButton { background: transparent; color: #94a3b8; padding: 5px 10px; "
        "border-radius: 6px; font-size: 12px; }"
        "QPushButton:hover { background-color: #1e293b; color: #f8fafc; }"
        "QPushButton:checked { color: #06b6d4; font-weight: bold; border-bottom: 2px solid #06b6d4; }"
    )


def toolbar_split_qss() -> str:
    return (
        "QPushButton { background: rgba(148,163,184,0.06); color: #94a3b8; "
        "border: 1px solid rgba(148,163,184,0.14); border-radius: 8px; "
        "padding: 6px 10px; min-width: 30px; font-size: 12px; font-weight: 800; }"
        "QPushButton:hover { background-color: rgba(6,182,212,0.12); color: #f8fafc; "
        "border-color: rgba(6,182,212,0.38); }"
        "QPushButton:checked { background-color: rgba(6,182,212,0.20); color: #22d3ee; "
        "border-color: #22d3ee; }"
    )


def search_bar_qss() -> str:
    return (
        "QFrame { background-color: #08111f; border-bottom: 1px solid #132238; }"
        "QLineEdit { background-color: #0f1d31; color: white; border: 1px solid #243449; border-radius: 6px; padding: 6px 8px; }"
        "QLineEdit:focus { border-color: #06b6d4; }"
        "QPushButton { background-color: #0f1d31; color: #cbd5e1; border: 1px solid #243449; border-radius: 6px; padding: 6px 10px; }"
        "QPushButton:hover { background-color: rgba(6,182,212,0.16); border-color: rgba(6,182,212,0.45); }"
        "QCheckBox { color: #94a3b8; font-size: 11px; }"
    )


def splitter_qss(width: int = 2) -> str:
    return f"QSplitter::handle {{ background-color: #1e293b; width: {width}px; }}"


def sidebar_qss() -> str:
    return "background-color: #0f172a; border-right: 1px solid #1e293b;"


def label_qss(kind: str = "muted") -> str:
    styles = {
        "section": "color: #64748b; font-size: 11px; font-weight: bold; margin-bottom: 10px;",
        "folder": "color: #7dd3fc; font-size: 10px; margin-bottom: 6px;",
        "tiny_cyan": "color: #06b6d4; font-weight: bold; font-size: 11px; margin-bottom: 6px;",
        "status_lang": "color: #06b6d4; font-weight: bold;",
        "search_count": "color: #64748b; font-size: 11px;",
        "terminal_prompt": "color: #06b6d4; font-family: Consolas; font-size: 13px; font-weight: bold;",
    }
    return styles.get(kind, "color: #64748b; font-size: 11px;")


def small_button_qss() -> str:
    return "font-size: 11px; color: #bae6fd; border: 1px solid #1e3a5f; padding: 6px; border-radius: 6px;"


def filter_input_qss() -> str:
    return (
        "QLineEdit { background-color: #08111f; color: #e2e8f0; border: 1px solid #1e293b; "
        "border-radius: 6px; padding: 6px; font-size: 11px; }"
        "QLineEdit:focus { border-color: #06b6d4; }"
    )


def file_list_qss() -> str:
    return (
        "QListWidget { background-color: transparent; border: none; color: #94a3b8; font-size: 12px; }"
        "QListWidget::item { padding: 8px; border-radius: 6px; }"
        "QListWidget::item:hover { background-color: #1e293b; color: #f8fafc; }"
        "QListWidget::item:selected { background-color: rgba(6,182,212,0.16); color: #e0f2fe; }"
    )


def tabs_qss() -> str:
    return (
        "QTabWidget::pane { border: 1px solid rgba(30,41,59,0.9); background-color: #0b1220; border-radius: 8px; }"
        "QTabBar::tab { background-color: #111827; color: #94a3b8; padding: 10px 18px; "
        "margin-right: 2px; border-top-left-radius: 8px; border-top-right-radius: 8px; "
        "min-width: 120px; font-size: 12px; }"
        "QTabBar::tab:selected { background-color: #0b1220; color: #22d3ee; border-bottom: 2px solid #22d3ee; font-weight: bold; }"
    )


def minimap_qss() -> str:
    return "background-color: #0a1020; border-left: 1px solid #1e293b;"


def status_bar_qss() -> str:
    return "background-color: #1e293b; color: #64748b; font-size: 11px; border-top: 1px solid #334155;"


def terminal_header_qss() -> str:
    return "background-color: #0f172a; border-top: 2px solid #06b6d4;"


def terminal_title_qss() -> str:
    return "color: #06b6d4; font-size: 11px; font-weight: bold;"


def terminal_clear_qss() -> str:
    return "QPushButton { background: transparent; color: #64748b; font-size: 10px; border: none; } QPushButton:hover { color: #f8fafc; }"


def terminal_output_qss() -> str:
    return "QPlainTextEdit { background-color: #050d1a; color: #a8e6cf; border: none; padding: 4px; }"


def terminal_input_frame_qss() -> str:
    return "background-color: #0a1122; border-top: 1px solid #1e293b;"


def terminal_input_qss() -> str:
    return "QLineEdit { background: transparent; color: #e2e8f0; border: none; font-family: Consolas; font-size: 12px; }"


def snippets_dialog_qss() -> str:
    return (
        "QDialog { background-color: #0f172a; color: #e2e8f0; }"
        "QLabel { color: #94a3b8; font-size: 12px; }"
        "QPushButton { background-color: #1e293b; color: #e2e8f0; border: 1px solid #334155; border-radius: 6px; padding: 6px 14px; font-size: 12px; }"
        "QPushButton:hover { background-color: #06b6d4; color: white; border-color: #06b6d4; }"
        "QListWidget { background-color: #1e293b; color: #e2e8f0; border: 1px solid #334155; border-radius: 6px; font-size: 12px; }"
        "QListWidget::item { padding: 8px; border-bottom: 1px solid #0f172a; }"
        "QListWidget::item:selected { background-color: #06b6d4; color: white; }"
        "QPlainTextEdit { background-color: #050d1a; color: #a8e6cf; border: 1px solid #334155; border-radius: 6px; font-family: Consolas; font-size: 12px; }"
    )


def primary_button_qss() -> str:
    return "QPushButton { background-color: #06b6d4; color: white; font-weight: bold; border: none; padding: 8px; border-radius: 6px; } QPushButton:hover { background-color: #0891b2; }"
