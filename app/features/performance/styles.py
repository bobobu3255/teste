#!/usr/bin/env python3
"""Estilos compartilhados da ferramenta Desempenho Pro."""
from __future__ import annotations


BG = "#070a12"
PANEL = "#0d1524"
CARD = "#111b2d"
BORDER = "rgba(148,163,184,0.14)"
BORDER_STRONG = "rgba(34,211,238,0.42)"
TEXT = "#e2e8f0"
TITLE = "#f1f5f9"
MUTED = "#64748b"
FAINT = "#475569"
CYAN = "#22d3ee"
GREEN = "#34d399"
YELLOW = "#fbbf24"
RED = "#fb7185"


def performance_widget_qss() -> str:
    return f"""
        QWidget {{
            background: {BG};
            color: {TEXT};
            font-family: 'Segoe UI', Arial, sans-serif;
            font-size: 12px;
        }}
        QLabel {{ background: transparent; border: none; }}
        QPushButton {{
            background: #111827;
            border: 1px solid rgba(148,163,184,0.18);
            border-radius: 11px;
            color: #dbeafe;
            min-height: 42px;
            padding: 11px 18px;
            font-size: 13px;
            font-weight: 800;
        }}
        QPushButton:hover {{
            background: rgba(34,211,238,0.12);
            border-color: {BORDER_STRONG};
            color: {TEXT};
        }}
        QPushButton:pressed {{ background: rgba(6,182,212,0.06); }}
        QComboBox {{
            background: {PANEL};
            border: 1px solid rgba(6,182,212,0.18);
            border-radius: 8px;
            color: {TEXT};
            padding: 6px 10px;
            font-size: 12px;
        }}
        QComboBox::drop-down {{ border: none; width: 22px; }}
        QComboBox:hover {{ border-color: {BORDER_STRONG}; }}
        QTabWidget#perfTabs::pane {{
            border: none;
            background: transparent;
            margin-top: 4px;
        }}
        QTabWidget#perfTabs QTabBar {{ background: transparent; }}
        QTabWidget#perfTabs QTabBar::tab {{
            background: #0d1524;
            color: #94a3b8;
            border: 1px solid rgba(148,163,184,0.12);
            border-radius: 10px;
            min-height: 48px;
            min-width: 160px;
            padding: 0 22px;
            margin: 4px 4px 6px 0;
            font-size: 13px;
            font-weight: 800;
        }}
        QTabWidget#perfTabs QTabBar::tab:hover {{
            color: #e2e8f0;
            border-color: rgba(34,211,238,0.30);
            background: rgba(34,211,238,0.07);
        }}
        QTabWidget#perfTabs QTabBar::tab:selected {{
            color: {CYAN};
            border: 1px solid rgba(34,211,238,0.55);
            background: rgba(34,211,238,0.12);
        }}
        QScrollArea {{ border: none; background: transparent; }}
        QScrollBar:vertical {{
            background: {BG}; width: 6px; margin: 0; border-radius: 3px;
        }}
        QScrollBar::handle:vertical {{
            background: #1a2540; border-radius: 3px; min-height: 28px;
        }}
        QScrollBar::handle:vertical:hover {{ background: #06b6d4; }}
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
        QGroupBox {{
            background: #0b1220;
            border: 1px solid {BORDER};
            border-radius: 10px;
            margin-top: 16px;
            padding: 14px;
            padding-top: 32px;
        }}
        QGroupBox::title {{
            color: #cbd5e1;
            font-size: 11px;
            font-weight: 800;
            letter-spacing: 0.6px;
            subcontrol-origin: margin;
            left: 14px;
            top: 8px;
        }}
        QTextEdit {{
            background: #050810;
            border: 1px solid {BORDER};
            border-radius: 10px;
            color: #94a3b8;
            padding: 10px 12px;
            font-family: Consolas, monospace;
            font-size: 11px;
        }}
    """


def history_chart_qss() -> str:
    return "#historyChart{background:#0b1220;border:1px solid rgba(6,182,212,0.10);border-radius:8px;}"


def perf_header_qss() -> str:
    return "#perfHeader{background:#07080f;border-bottom:1px solid rgba(6,182,212,0.10);}"


def perf_label_qss(kind: str = "body", color: str | None = None) -> str:
    styles = {
        "icon": "font-size:20px; background:transparent; border:none;",
        "title": "color:#f1f5f9; font-size:18px; font-weight:800;",
        "subtitle": "color:#64748b; font-size:11px; border:none;",
        "metric_title": "font-size:10px; font-weight:900; letter-spacing:0.8px;",
        "metric_value": "color:#f8fafc; font-size:23px; font-weight:800; line-height:1.1;",
        "muted": "color:#94a3b8; font-size:11px;",
        "section": "color:#94a3b8; font-size:10px; font-weight:900; letter-spacing:0.8px;",
        "card_title": "color:#f1f5f9; font-size:13px; font-weight:800;",
        "guide_title": "color:#22d3ee; font-weight:700; font-size:12px;",
        "info_title": "color:#f1f5f9; font-size:16px; font-weight:700;",
    }
    base = styles.get(kind, "color:#e2e8f0; font-size:12px;")
    if color:
        base += f" color:{color};"
    return base


def status_badge_qss(level: str = "safe") -> str:
    data = {
        "safe": ("#34d399", "rgba(52,211,153,0.10)", "rgba(52,211,153,0.28)"),
        "warn": ("#fde68a", "rgba(120,53,15,0.22)", "rgba(251,191,36,0.32)"),
        "alert": ("#fecaca", "rgba(127,29,29,0.28)", "rgba(248,113,113,0.35)"),
    }.get(level, ("#34d399", "rgba(52,211,153,0.10)", "rgba(52,211,153,0.28)"))
    color, bg, border = data
    return f"color:{color};background:{bg};border:1px solid {border};border-radius:8px;padding:10px 16px;font-weight:900;"


def banner_qss(color: str, bg: str) -> str:
    return f"color:{color};background:{bg};border:1px solid {color}33;border-radius:10px;padding:10px 14px;font-size:12px;font-weight:700;"


def stat_card_qss(color: str, alert: bool = False, warn: bool = False) -> str:
    tone = "rgba(244,63,94,0.08)" if alert else "rgba(245,158,11,0.07)" if warn else CARD
    line = RED if alert else YELLOW if warn else color
    return f"#statCard{{background:{tone};border:1px solid {line}55;border-left:4px solid {line};border-radius:12px;}}"


def action_button_qss(color: str) -> str:
    return (
        f"QPushButton{{background:{color}14;color:{color};border:1px solid {color}45;"
        "border-radius:11px;min-height:46px;padding:12px 18px;font-size:13px;font-weight:900;}"
        f"QPushButton:hover{{background:{color}24;border-color:{color}90;}}"
        f"QPushButton:pressed{{background:{color}0a;}}"
    )


def panel_qss(name: str, transparent: bool = False, line: str | None = None) -> str:
    if transparent:
        border = line or "rgba(6,182,212,0.07)"
        return f"#{name}{{background:transparent;border:none;border-bottom:1px solid {border};border-radius:0;}}"
    return f"#{name}{{background:{CARD};border:1px solid rgba(148,163,184,0.12);border-radius:12px;}}"


def accent_card_qss(name: str, color: str) -> str:
    return f"#{name}{{background:{CARD};border:1px solid {color}45;border-left:4px solid {color};border-radius:12px;}}"


def pill_qss(color: str) -> str:
    return f"color:{color};background:{color}14;border:1px solid {color}45;border-radius:9px;padding:4px 10px;font-size:10px;font-weight:800;"
