#!/usr/bin/env python3
"""Estilos compartilhados do Navegador Seguro."""

from app.ui.app_theme import DARK_STYLE_PRO


def browser_widget_qss():
    return DARK_STYLE_PRO + """
        BrowserWidget, QWidget {
            background: #060a14;
            color: #e6edf7;
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
        }
        QFrame#BrowserHeader {
            background: #0b1626;
            border: 1px solid rgba(56,189,248,0.15);
            border-radius: 10px;
        }
        QFrame#BrowserPanel, QFrame#BrowserRightPanel {
            background: #0a1020;
            border: 1px solid rgba(56,189,248,0.13);
            border-radius: 10px;
        }
        QFrame#BrowserSectionTabs {
            background: transparent;
            border: none;
        }
        QFrame#browserGuide {
            background: transparent;
            border: none;
        }
        QFrame#BrowserBottomBar {
            background: #0a1020;
            border: 1px solid rgba(56,189,248,0.12);
            border-radius: 10px;
        }
        QListWidget, QTextEdit, QLineEdit, QComboBox, QSpinBox, QTableWidget {
            background: #07111f;
            color: #e6edf7;
            border: 1px solid rgba(56,189,248,0.15);
            border-radius: 10px;
            padding: 8px;
            selection-background-color: rgba(8,145,178,0.34);
        }
        QTextEdit {
            padding: 10px;
        }
        QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus {
            border: 1px solid rgba(34,211,238,0.55);
            background: #091827;
        }
        QComboBox::drop-down {
            border: none;
            width: 26px;
        }
        QComboBox::down-arrow {
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 6px solid #94a3b8;
            margin-right: 8px;
        }
        QComboBox QAbstractItemView {
            background: #07111f;
            color: #e6edf7;
            border: 1px solid rgba(56,189,248,0.18);
            border-radius: 10px;
            selection-background-color: rgba(8,145,178,0.34);
            outline: 0;
        }
        QListWidget::item {
            padding: 0;
            border-radius: 12px;
            margin: 4px 0;
        }
        QListWidget::item:selected {
            background: rgba(6,182,212,0.16);
            color: #f8fafc;
        }
        QTableWidget::item:selected {
            background: rgba(6,182,212,0.22);
            color: #f8fafc;
        }
        QHeaderView::section {
            background: #111827;
            color: #bae6fd;
            border: 1px solid rgba(56,189,248,0.10);
            padding: 8px;
            font-weight: 700;
        }
        QGroupBox {
            background: #0a1324;
            border: 1px solid rgba(56,189,248,0.13);
            border-radius: 10px;
            margin-top: 14px;
            padding: 18px 10px 10px 10px;
            font-weight: 700;
        }
        QGroupBox::title {
            color: #22d3ee;
            subcontrol-origin: margin;
            left: 14px;
            padding: 0 8px;
        }
        QPushButton {
            background: #101827;
            color: #e6edf7;
            border: 1px solid rgba(148,163,184,0.14);
            border-radius: 10px;
            padding: 9px 12px;
            font-weight: 700;
        }
        QPushButton:hover {
            background: #142033;
            border-color: rgba(34,211,238,0.36);
            color: #ffffff;
        }
        QPushButton:pressed {
            background: #0b1323;
        }
        QPushButton:checked {
            background: rgba(6,182,212,0.20);
            border-color: rgba(34,211,238,0.62);
            color: #ecfeff;
        }
        QPushButton:disabled {
            color: #64748b;
            background: rgba(148,163,184,0.05);
            border-color: rgba(148,163,184,0.08);
        }
        QPushButton#BrowserPrimaryButton {
            background: #22d3ee;
            color: #06111f;
            border: 1px solid rgba(125,211,252,0.55);
        }
        QPushButton#BrowserSuccessButton {
            background: #059669;
            color: #f8fafc;
            border: 1px solid rgba(52,211,153,0.38);
        }
        QPushButton#BrowserDangerButton {
            background: #7f1d1d;
            color: #fee2e2;
            border: 1px solid rgba(248,113,113,0.28);
        }
        QPushButton#BrowserDangerButton:hover {
            background: #991b1b;
        }
        QLabel#BrowserTitle {
            color: #f8fafc;
            font-size: 20px;
            font-weight: 900;
            background: transparent;
            border: none;
        }
        QLabel#BrowserSubtitle {
            color: #93a4b8;
            font-size: 12px;
            background: transparent;
            border: none;
        }
        QLabel#BrowserChip {
            color: #67e8f9;
            background: rgba(6,182,212,0.10);
            border: 1px solid rgba(34,211,238,0.18);
            border-radius: 10px;
            padding: 8px 12px;
            font-weight: 800;
        }
        QScrollBar:vertical {
            background: #060a14;
            width: 10px;
            margin: 0;
        }
        QScrollBar::handle:vertical {
            background: rgba(34,211,238,0.38);
            border-radius: 5px;
            min-height: 40px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
    """


def browser_label_qss(kind="muted"):
    styles = {
        "section": "font-size: 14px; font-weight: bold; color: #22d3ee;",
        "hint": "color:#94a3b8;font-size:11px;",
        "muted": "color:#9ca3af;font-size:11px;",
        "muted_plain": "color:#9ca3af;",
        "faded": "color:#6b7280;",
        "faded_small": "color:#6b7280;font-size:11px;",
        "soft": "color:#cbd5e1;font-size:12px;",
        "tiny": "font-size:11px;",
        "success": "color:#22c55e;font-size:11px;",
        "warning": "color:#f59e0b;font-size:11px;",
    }
    return styles.get(kind, styles["muted"])


def browser_status_qss(color="#94a3b8"):
    return (
        f"color:{color};font-size:11px;background:#07111f;"
        "border:1px solid rgba(56,189,248,0.14);border-radius:10px;padding:8px 10px;"
    )


def browser_checkbox_qss(color="#e5e7eb"):
    return f"color:{color};font-size:12px;padding:2px;"


def browser_dashboard_card_qss():
    return (
        "background:#07111f;border:1px solid rgba(56,189,248,0.14);"
        "border-radius:8px;padding:12px;color:#dbeafe;font-weight:800;"
    )


def browser_guide_item_qss():
    return (
        "background:#0d1526;border:1px solid rgba(56,189,248,0.12);"
        "border-radius:8px;padding:12px;color:#dbeafe;"
    )


def browser_panel_qss():
    return (
        "background:#07111f;border:1px solid rgba(56,189,248,0.13);border-radius:8px;"
        "padding:10px;color:#dbeafe;font-weight:650;"
    )


def browser_success_button_qss():
    return """
        QPushButton {
            background: #059669;
            color: white;
            font-weight: bold;
            padding: 11px;
            border-radius: 8px;
            border: 1px solid rgba(52,211,153,0.35);
        }
        QPushButton:hover {
            background: #10b981;
        }
    """


def browser_primary_button_qss():
    return """
        QPushButton {
            background: #2563eb;
            color: white;
            font-weight: bold;
            padding: 12px;
            border-radius: 8px;
            border: 1px solid rgba(96,165,250,0.35);
        }
        QPushButton:hover {
            background: #3b82f6;
        }
    """


def browser_danger_button_qss():
    return """
        QPushButton {
            background-color: #7f1d1d;
            color: #fee2e2;
            padding: 9px;
            border-radius: 10px;
            border: 1px solid rgba(248,113,113,0.30);
        }
        QPushButton:hover {
            background-color: #991b1b;
        }
    """


def browser_start_button_qss():
    return """
        QPushButton {
            background: #06b6d4;
            color: white;
            font-size: 16px;
            font-weight: bold;
            padding: 16px;
            border-radius: 10px;
        }
        QPushButton:hover {
            background: #0891b2;
        }
    """


def browser_profile_row_qss():
    return """
        QWidget#BrowserProfileRow {
            background: #0c1628;
            border: 1px solid rgba(56,189,248,0.10);
            border-radius: 8px;
        }
        QWidget#BrowserProfileRow:hover {
            background: #102033;
            border-color: rgba(34,211,238,0.28);
        }
        QLabel {
            background: transparent;
            border: none;
        }
    """


def browser_profile_title_qss():
    return "background:transparent;border:none;"


def browser_row_start_qss():
    return """
        QPushButton {
            background:#e6edf7;
            color:#06111f;
            border:1px solid rgba(255,255,255,0.24);
            border-radius:10px;
            font-weight:900;
        }
        QPushButton:hover { background:#ffffff; }
    """


def browser_row_close_qss():
    return """
        QPushButton {
            background:#ef4444;
            color:#ffffff;
            border:1px solid rgba(255,255,255,0.12);
            border-radius:10px;
            font-weight:900;
        }
        QPushButton:hover { background:#f87171; }
        QPushButton:disabled {
            background:#1f2937;
            color:#64748b;
            border-color:rgba(148,163,184,0.10);
        }
    """


def browser_section_tab_qss(active=False):
    if not active:
        return ""
    return "background:rgba(6,182,212,0.22);border-color:rgba(34,211,238,0.55);"


def browser_vault_status_qss(unlocked=False):
    return "color:#10b981;font-weight:600;" if unlocked else "color:#f59e0b;font-weight:600;"


def browser_proxy_status_qss(valid=False):
    return "color: #10b981; font-size: 11px;" if valid else "color: #ef4444; font-size: 11px;"
