#!/usr/bin/env python3
"""Paramount Assist: fila segura para contas, perfis e preenchimento visivel.

Redesign V2 — UI premium dark com badges de status, hierarquia visual clara
e paleta coesa. Logica identica ao original.
"""

from __future__ import annotations

import hashlib
import json
import re
import socket
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor, QPalette, QFont, QIcon
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
)

from app.core.paths import BASE_DIR
from app.core.clipboard_service import set_clipboard_text

try:
    from app.core.app_context import get_app_store
except Exception:
    get_app_store = None

try:
    from address_generator import AddressGenerator
except Exception:
    AddressGenerator = None

try:
    from address_reserve import AddressExtractor
except Exception:
    AddressExtractor = None

try:
    from database import DatabaseManager
except Exception:
    DatabaseManager = None

from browser_manager import BrowserManager
from browser_widget import BrowserLaunchThread

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
except Exception:
    By = None
    Keys = None
    ActionChains = None


PARAMOUNT_URLS = {
    "login": "https://www.paramountplus.com/br/account/signin/",
    "cadastro": "https://www.paramountplus.com/br/account/signup/account",
    "plano": "https://www.paramountplus.com/br/account/signup/plan/",
    "inicio": "https://www.paramountplus.com/br/",
}

LEGACY_PARAMOUNT_DIR = Path(
    "F:/GGS/bots/TelegramCollectorPro_v10.2_FINAL/CrunchyrollBot_Melhorado/paramount_bot"
)

PLAN_OPTIONS = [
    "Premium Mensal",
    "Premium Anual",
    "Essencial Mensal",
    "Essencial Anual",
    "Mensal",
    "Anual",
]

UF_NAMES = {
    "AC": "Acre", "AL": "Alagoas", "AP": "Amapa", "AM": "Amazonas",
    "BA": "Bahia", "CE": "Ceara", "DF": "Distrito Federal", "ES": "Espirito Santo",
    "GO": "Goias", "MA": "Maranhao", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
    "MG": "Minas Gerais", "PA": "Para", "PB": "Paraiba", "PR": "Parana",
    "PE": "Pernambuco", "PI": "Piaui", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
    "RS": "Rio Grande do Sul", "RO": "Rondonia", "RR": "Roraima", "SC": "Santa Catarina",
    "SP": "Sao Paulo", "SE": "Sergipe", "TO": "Tocantins",
}

# ─── Paleta de cores ──────────────────────────────────────────────────────────
P = {
    "bg":          "#060a14",
    "surface":     "#0a1020",
    "surface2":    "#0d1526",
    "card":        "#0f1a2e",
    "border":      "rgba(56, 189, 248, 0.12)",
    "border_glow": "rgba(56, 189, 248, 0.35)",
    "text":        "#e2e8f0",
    "muted":       "#64748b",
    "subtle":      "#94a3b8",
    "cyan":        "#38bdf8",
    "cyan_dim":    "#0ea5e9",
    "green":       "#34d399",
    "green_dim":   "#10b981",
    "red":         "#f87171",
    "red_dim":     "#ef4444",
    "amber":       "#fbbf24",
    "purple":      "#a78bfa",
    "blue":        "#60a5fa",
}

# Cores por status (badge)
STATUS_COLORS = {
    "novo":                    ("#1e3a5f", "#60a5fa"),
    "perfil pronto":           ("#1a3d2e", "#34d399"),
    "login ok":                ("#1a3d2e", "#34d399"),
    "precisa verificar":       ("#3b2e0d", "#fbbf24"),
    "bloqueio/403":            ("#3b1212", "#f87171"),
    "assinatura ativa":        ("#0d3b2e", "#10f0a0"),
    "sem assinatura":          ("#332a12", "#fbbf24"),
    "cartao recusado manual":  ("#3b1212", "#f87171"),
    "pausado":                 ("#1e2433", "#64748b"),
}


def _status_badge_qss(status: str) -> str:
    bg, fg = STATUS_COLORS.get(status, ("#1e2433", "#94a3b8"))
    return (
        f"background:{bg}; color:{fg}; border:1px solid {fg}40;"
        "border-radius:6px; padding:2px 8px; font-size:10px; font-weight:800;"
        "letter-spacing:0.5px;"
    )


class _ParamountActionWorker(QThread):
    """Roda Selenium/BrowserManager fora da UI para evitar congelamento."""

    result = pyqtSignal(str, object)
    error = pyqtSignal(str, str)

    def __init__(self, key: str, fn, parent=None):
        super().__init__(parent)
        self.key = key
        self.fn = fn

    def run(self):
        try:
            self.result.emit(self.key, self.fn())
        except Exception as exc:
            self.error.emit(self.key, str(exc))


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _make_id(prefix: str, seed: str = "") -> str:
    raw = f"{prefix}:{seed}:{_now()}".encode("utf-8", errors="ignore")
    return hashlib.sha1(raw).hexdigest()[:12]


def _digits(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


# ─── Componentes visuais auxiliares ──────────────────────────────────────────

def _divider(vertical: bool = False) -> QFrame:
    line = QFrame()
    line.setFrameShape(QFrame.VLine if vertical else QFrame.HLine)
    line.setStyleSheet(f"color: {P['border']}; background: {P['border']};")
    line.setFixedHeight(1) if not vertical else line.setFixedWidth(1)
    return line


def _section_label(text: str) -> QLabel:
    lbl = QLabel(text.upper())
    lbl.setStyleSheet(
        f"color:{P['cyan']}; font-size:10px; font-weight:900;"
        "letter-spacing:2px; background:transparent; border:none; padding:0;"
    )
    return lbl


def _icon_button(text: str, obj_name: str = "", tooltip: str = "") -> QPushButton:
    btn = QPushButton(text)
    if obj_name:
        btn.setObjectName(obj_name)
    if tooltip:
        btn.setToolTip(tooltip)
    return btn


# ─── Folha de estilo principal ────────────────────────────────────────────────

MAIN_QSS = f"""
/* ── Base ── */
QWidget {{
    background: {P['bg']};
    color: {P['text']};
    font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
    font-size: 12px;
}}
QLabel {{
    background: transparent;
    border: none;
}}

/* ── Paineis e cards ── */
QFrame#Header {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0d1a30, stop:0.5 #0a1828, stop:1 #071220);
    border: 1px solid {P['border_glow']};
    border-radius: 16px;
}}
QFrame#Panel {{
    background: {P['surface']};
    border: 1px solid {P['border']};
    border-radius: 14px;
}}
QFrame#InfoCard {{
    background: {P['card']};
    border: 1px solid {P['border']};
    border-radius: 10px;
}}

/* ── GroupBox ── */
QGroupBox {{
    background: {P['surface']};
    border: 1px solid {P['border']};
    border-radius: 12px;
    margin-top: 16px;
    padding: 14px;
    padding-top: 30px;
    color: {P['text']};
    font-size: 12px;
}}
QGroupBox::title {{
    color: {P['cyan']};
    left: 14px;
    top: 6px;
    font-weight: 900;
    font-size: 10px;
    letter-spacing: 1.5px;
    subcontrol-origin: margin;
    text-transform: uppercase;
}}

/* ── Campos de entrada ── */
QLineEdit, QTextEdit, QComboBox {{
    background: {P['surface2']};
    color: {P['text']};
    border: 1px solid rgba(148,163,184,0.15);
    border-radius: 8px;
    padding: 8px 10px;
    selection-background-color: #0e7490;
    font-size: 12px;
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{
    border: 1px solid {P['border_glow']};
    background: #0c1828;
}}
QLineEdit:read-only {{
    background: #080e1a;
    color: {P['muted']};
    border-color: rgba(100,116,139,0.12);
}}
QLineEdit::placeholder, QTextEdit::placeholder {{
    color: {P['muted']};
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox QAbstractItemView {{
    background: {P['surface2']};
    border: 1px solid {P['border_glow']};
    border-radius: 8px;
    color: {P['text']};
    selection-background-color: #0e4a6e;
    outline: none;
    padding: 4px;
}}

/* ── Botoes base ── */
QPushButton {{
    background: {P['surface2']};
    color: {P['text']};
    border: 1px solid rgba(148,163,184,0.18);
    border-radius: 8px;
    padding: 8px 14px;
    font-weight: 700;
    font-size: 12px;
}}
QPushButton:hover {{
    background: #131f35;
    border-color: rgba(56,189,248,0.35);
    color: #f0f9ff;
}}
QPushButton:pressed {{
    background: #0c1828;
}}

/* ── Botoes especializados ── */
QPushButton#Primary {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0369a1, stop:1 #0891b2);
    color: #e0f7ff;
    border: 1px solid rgba(56,189,248,0.45);
    font-weight: 800;
}}
QPushButton#Primary:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #0284c7, stop:1 #06b6d4);
    border-color: rgba(56,189,248,0.70);
}}
QPushButton#Success {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #065f46, stop:1 #0f766e);
    color: #d1fae5;
    border: 1px solid rgba(52,211,153,0.40);
    font-weight: 800;
}}
QPushButton#Success:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #047857, stop:1 #0d9488);
    border-color: rgba(52,211,153,0.65);
}}
QPushButton#Danger {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #7f1d1d, stop:1 #991b1b);
    color: #fee2e2;
    border: 1px solid rgba(248,113,113,0.40);
    font-weight: 800;
}}
QPushButton#Danger:hover {{
    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
        stop:0 #991b1b, stop:1 #b91c1c);
    border-color: rgba(248,113,113,0.65);
}}
QPushButton#Soft {{
    background: rgba(15,28,48,0.80);
    color: {P['cyan']};
    border: 1px solid rgba(56,189,248,0.22);
    font-weight: 700;
}}
QPushButton#Soft:hover {{
    background: rgba(14,116,144,0.18);
    border-color: rgba(56,189,248,0.50);
    color: #bae6fd;
}}
QPushButton#Ghost {{
    background: transparent;
    color: {P['subtle']};
    border: 1px solid rgba(148,163,184,0.12);
    font-weight: 600;
}}
QPushButton#Ghost:hover {{
    background: rgba(148,163,184,0.06);
    color: {P['text']};
}}
QPushButton#IconBtn {{
    background: rgba(15,28,48,0.80);
    color: {P['cyan']};
    border: 1px solid rgba(56,189,248,0.18);
    border-radius: 8px;
    padding: 6px 10px;
    min-width: 32px;
    font-size: 14px;
    font-weight: 900;
}}
QPushButton#IconBtn:hover {{
    background: rgba(14,116,144,0.25);
    border-color: rgba(56,189,248,0.50);
}}

/* ── Tabelas ── */
QTableWidget {{
    background: {P['surface2']};
    color: {P['text']};
    gridline-color: rgba(30,50,80,0.80);
    border: 1px solid {P['border']};
    border-radius: 10px;
    selection-background-color: #0c2d4a;
    outline: none;
}}
QTableWidget::item {{
    padding: 7px 10px;
    border-bottom: 1px solid rgba(30,50,80,0.60);
}}
QTableWidget::item:selected {{
    background: #0e3d5c;
    color: #e0f7ff;
}}
QTableWidget::item:hover {{
    background: rgba(14,116,144,0.12);
}}
QHeaderView::section {{
    background: {P['card']};
    color: {P['cyan']};
    border: none;
    border-bottom: 1px solid rgba(56,189,248,0.18);
    padding: 8px 10px;
    font-weight: 900;
    font-size: 10px;
    letter-spacing: 1px;
    text-transform: uppercase;
}}
QHeaderView::section:first {{
    border-top-left-radius: 10px;
}}
QHeaderView::section:last {{
    border-top-right-radius: 10px;
}}

/* ── Tabs ── */
QTabWidget::pane {{
    border: 1px solid {P['border']};
    border-radius: 12px;
    background: {P['surface']};
    margin-top: 4px;
}}
QTabBar::tab {{
    background: {P['surface2']};
    color: {P['muted']};
    border: 1px solid rgba(56,189,248,0.10);
    padding: 9px 18px;
    margin-right: 5px;
    border-radius: 9px;
    font-weight: 800;
    font-size: 11px;
    letter-spacing: 0.5px;
    min-width: 80px;
}}
QTabBar::tab:selected {{
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1,
        stop:0 #0c2d4a, stop:1 #0a2038);
    color: {P['cyan']};
    border-color: rgba(56,189,248,0.45);
    border-bottom: 2px solid {P['cyan']};
}}
QTabBar::tab:hover:!selected {{
    background: #0d1e33;
    color: {P['subtle']};
    border-color: rgba(56,189,248,0.22);
}}

/* ── Scrollbars ── */
QScrollBar:vertical {{
    background: transparent;
    width: 6px;
    margin: 0;
}}
QScrollBar::handle:vertical {{
    background: rgba(56,189,248,0.20);
    border-radius: 3px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: rgba(56,189,248,0.40);
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QScrollBar:horizontal {{
    height: 6px;
}}
QScrollBar::handle:horizontal {{
    background: rgba(56,189,248,0.20);
    border-radius: 3px;
}}

/* ── Splitter ── */
QSplitter::handle {{
    background: {P['border']};
    width: 2px;
}}
QSplitter::handle:hover {{
    background: rgba(56,189,248,0.30);
}}
"""


class ParamountAssistWidget(QWidget):
    """Central focada em Paramount, sem automatizar compra ou teste de cartao."""

    _log_signal = pyqtSignal(str)

    DATA_FILE = BASE_DIR / "browser_config" / "paramount_assist.json"
    STATUSES = [
        "novo",
        "perfil pronto",
        "login ok",
        "sem assinatura",
        "precisa verificar",
        "bloqueio/403",
        "assinatura ativa",
        "cartao recusado manual",
        "pausado",
    ]

    def __init__(self, browser_manager: Optional[BrowserManager] = None, parent=None):
        super().__init__(parent)
        self._log_signal.connect(self._append_log)
        self.browser_manager = browser_manager or BrowserManager()
        self.address_generator = AddressGenerator() if AddressGenerator else None
        self.address_reserve = AddressExtractor() if AddressExtractor else None
        self.db = DatabaseManager() if DatabaseManager else None
        self.launch_threads: Dict[str, BrowserLaunchThread] = {}
        self._action_workers: Dict[str, _ParamountActionWorker] = {}
        self._action_started_at: Dict[str, float] = {}
        self._recovery_notice_shown = False
        self._auto_flow_attempts: Dict[str, int] = {}
        self._side_by_side_jobs: List = []
        self._side_by_side_total = 0
        self._side_by_side_opening = False
        self._side_by_side_started_at = 0.0
        self.current_account_id = ""
        self.data = {"accounts": [], "cards": [], "logs": [], "settings": {}}
        self._build()
        self._init_toast()
        self.load_data()
        self.refresh_all()
        self.subscription_scan_timer = QTimer(self)
        self.subscription_scan_timer.setInterval(15000)
        self.subscription_scan_timer.timeout.connect(self.auto_detect_open_subscriptions)
        self.subscription_scan_timer.start()
        self.recovery_watchdog_timer = QTimer(self)
        self.recovery_watchdog_timer.setInterval(5000)
        self.recovery_watchdog_timer.timeout.connect(self._recovery_watchdog_tick)
        self.recovery_watchdog_timer.start()

    # ─────────────────────────────────────────────────────────────────────────
    # Construcao principal
    # ─────────────────────────────────────────────────────────────────────────

    def _build(self):
        self.setStyleSheet(MAIN_QSS)

        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(6)

        self.main_splitter = QSplitter(Qt.Horizontal)
        self.main_splitter.setChildrenCollapsible(False)
        self.main_splitter.setHandleWidth(6)
        root.addWidget(self.main_splitter, 1)

        self.left_panel = self._left_panel()
        self.right_panel = self._right_panel()
        self.main_splitter.addWidget(self.left_panel)
        self.main_splitter.addWidget(self.right_panel)
        self.main_splitter.setStretchFactor(0, 0)
        self.main_splitter.setStretchFactor(1, 1)
        self.main_splitter.setSizes([360, 980])
        QTimer.singleShot(80, self._sync_responsive_state)

    def _init_toast(self):
        self.toast_label = QLabel(self)
        self.toast_label.setObjectName("ParamountToast")
        self.toast_label.setWordWrap(True)
        self.toast_label.setTextFormat(Qt.PlainText)
        self.toast_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        self.toast_label.hide()

        self.toast_timer = QTimer(self)
        self.toast_timer.setSingleShot(True)
        self.toast_timer.timeout.connect(self.toast_label.hide)

    def _position_toast(self):
        if not hasattr(self, "toast_label") or not self.toast_label.isVisible():
            return
        margin = 22
        x = max(margin, self.width() - self.toast_label.width() - margin)
        y = max(margin, self.height() - self.toast_label.height() - margin)
        self.toast_label.move(x, y)

    def _show_toast(self, title: str, message: str = "", kind: str = "info", duration: int = 3600):
        if not hasattr(self, "toast_label"):
            return
        colors = {
            "success": (P["green"], "rgba(16,185,129,0.14)", "rgba(16,185,129,0.42)"),
            "warning": (P["amber"], "rgba(251,191,36,0.14)", "rgba(251,191,36,0.42)"),
            "error":   (P["red"], "rgba(248,113,113,0.14)", "rgba(248,113,113,0.42)"),
            "info":    (P["cyan"], "rgba(56,189,248,0.14)", "rgba(56,189,248,0.42)"),
        }
        accent, bg, border = colors.get(kind, colors["info"])
        text = str(title or "").strip()
        detail = str(message or "").strip()
        if detail:
            text = f"{text}\n{detail}" if text else detail
        self.toast_label.setText(text)
        self.toast_label.setStyleSheet(
            f"""
            QLabel#ParamountToast {{
                color: {P['text']};
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 {bg}, stop:1 rgba(15,23,42,0.97));
                border: 1px solid {border};
                border-left: 4px solid {accent};
                border-radius: 14px;
                padding: 12px 16px;
                font-size: 12px;
                font-weight: 700;
            }}
            """
        )
        self.toast_label.setMinimumWidth(320)
        self.toast_label.setMaximumWidth(520)
        self.toast_label.adjustSize()
        self._position_toast()
        self.toast_label.raise_()
        self.toast_label.show()
        self.toast_timer.start(duration)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_responsive_state()
        self._position_toast()

    def _sync_responsive_state(self):
        """Mantem o layout legivel quando a janela esta estreita."""
        if not hasattr(self, "main_splitter"):
            return
        width = max(0, self.width())
        if width <= 0:
            return
        narrow = width < 900
        compact = width < 1220
        if narrow:
            left_w = 270
            min_left, max_left = 250, 315
        elif compact:
            left_w = 315
            min_left, max_left = 285, 370
        else:
            left_w = min(430, max(340, int(width * 0.28)))
            min_left, max_left = 320, 470
        right_w = max(480, width - left_w - 24)
        if hasattr(self, "left_panel"):
            self.left_panel.setMinimumWidth(min_left)
            self.left_panel.setMaximumWidth(max_left)
        self.main_splitter.setSizes([left_w, right_w])
        if hasattr(self, "tabs"):
            self.tabs.tabBar().setExpanding(not compact)
        if hasattr(self, "accounts_table"):
            self.accounts_table.setColumnHidden(1, width < 1080)
        if hasattr(self, "_paramount_quick_buttons"):
            compact_labels = ["Continuar", "Abrir perfil", "Colar emails", "Abrir 3 lado a lado"]
            for index, button in enumerate(self._paramount_quick_buttons):
                full_text = str(button.property("full_text") or button.text())
                if compact and index < len(compact_labels):
                    button.setText(compact_labels[index])
                    button.setToolTip(full_text)
                else:
                    button.setText(full_text)
                    button.setToolTip("")
        if hasattr(self, "paramount_info_card"):
            self.paramount_info_card.setVisible(not narrow)

    def _debug_port_alive_fast(self, port) -> bool:
        if not port:
            return False
        try:
            with socket.create_connection(("127.0.0.1", int(port)), timeout=0.12):
                return True
        except Exception:
            return False

    def _is_profile_probably_active_fast(self, profile_id: str) -> bool:
        """Checagem leve para a UI: evita chamar Selenium/window_handles na thread visual."""
        if not profile_id:
            return False
        manager = self.browser_manager
        try:
            if manager.is_profile_launching(profile_id):
                return True
        except Exception:
            pass

        try:
            active = getattr(manager, "active_browsers", {}) or {}
            modes = getattr(manager, "active_browser_modes", {}) or {}
            ports = getattr(manager, "active_debug_ports", {}) or {}
            if profile_id not in active:
                return self._debug_port_alive_fast(ports.get(profile_id))

            ref = active.get(profile_id)
            if modes.get(profile_id) == "native":
                if hasattr(ref, "poll"):
                    alive = ref.poll() is None
                    if alive:
                        return True
                    if self._debug_port_alive_fast(ports.get(profile_id)):
                        return True
                    for attr in (
                        "active_browsers",
                        "active_browser_modes",
                        "active_debug_ports",
                        "active_native_browser_names",
                        "native_control_drivers",
                    ):
                        try:
                            getattr(manager, attr, {}).pop(profile_id, None)
                        except Exception:
                            pass
                    return False
                return True

            # Selenium pode travar ao consultar window_handles. Na UI, se esta registrado,
            # tratamos como ativo e deixamos a thread de fundo validar de verdade.
            return True
        except Exception:
            return False

    def _reschedule_auto_flow_tick(self, account_id: str, profile_id: str, delay_ms: int = 2000):
        if not account_id or not profile_id:
            return
        QTimer.singleShot(delay_ms, lambda aid=account_id, pid=profile_id: self._auto_flow_tick(aid, pid))

    def _run_background_action(
        self,
        key: str,
        title: str,
        message: str,
        work_fn,
        on_result,
        on_error=None,
        quiet: bool = False,
    ) -> bool:
        """Executa Selenium/BrowserManager fora da thread visual."""
        if key in self._action_workers:
            if not quiet:
                self._show_toast(title, "Esta acao ainda esta em andamento.", "warning", 3000)
            return False

        worker = _ParamountActionWorker(key, work_fn, self)
        self._action_workers[key] = worker
        self._action_started_at[key] = time.time()
        task_id = f"paramount-action:{key}"
        if get_app_store:
            try:
                get_app_store().upsert_task(
                    task_id,
                    "paramount-action",
                    title or key,
                    source="paramount_assist",
                    status="running",
                    priority=10,
                    payload={"key": key, "message": message or ""},
                )
            except Exception:
                pass
        if not quiet:
            self._show_toast(title, message, "info", 3000)

        def cleanup(action_key: str):
            finished = self._action_workers.pop(action_key, None)
            self._action_started_at.pop(action_key, None)
            if finished:
                finished.deleteLater()

        def handle_result(action_key: str, payload):
            cleanup(action_key)
            if get_app_store:
                try:
                    get_app_store().update_task(f"paramount-action:{action_key}", status="success", last_error="")
                except Exception:
                    pass
            on_result(payload)

        def handle_error(action_key: str, error: str):
            cleanup(action_key)
            if get_app_store:
                try:
                    get_app_store().update_task(
                        f"paramount-action:{action_key}",
                        status="error",
                        last_error=error,
                        attempts_delta=1,
                    )
                except Exception:
                    pass
            if on_error:
                on_error(error)
            else:
                self.log(f"{title}: {error}")
                self._show_toast(title, error, "error", 5200)

        worker.result.connect(handle_result)
        worker.error.connect(handle_error)
        worker.start()
        return True

    def _recovery_watchdog_tick(self):
        """Detecta automacoes demoradas e mostra um aviso recuperavel."""
        now = time.time()
        stuck = [
            key for key, started in list(self._action_started_at.items())
            if now - started > 120
        ]
        launching = []
        try:
            launching = list(getattr(self.browser_manager, "launching_profiles", set()) or [])
        except Exception:
            launching = []

        side_opening_timed_out = bool(
            getattr(self, "_side_by_side_opening", False)
            and getattr(self, "_side_by_side_started_at", 0.0)
            and now - float(self._side_by_side_started_at) > 120
        )

        if stuck or side_opening_timed_out:
            if hasattr(self, "recovery_status_label"):
                waiting = len(stuck) + (1 if side_opening_timed_out else 0)
                self.recovery_status_label.setText(f"{waiting} tarefa(s) demorando. Use Recuperar travas se a tela parou.")
                self.recovery_status_label.setStyleSheet(f"color:{P['amber']}; font-weight:800;")
            if not self._recovery_notice_shown:
                self._recovery_notice_shown = True
                self._show_toast(
                    "Modo recuperacao",
                    "Detectei uma automacao demorando demais. Voce pode recuperar sem fechar o app inteiro.",
                    "warning",
                    6200,
                )
            if get_app_store:
                try:
                    get_app_store().recover_stale_tasks(
                        max_age_minutes=2,
                        source="paramount_assist",
                        reason="Acao demorou demais e foi enviada para revisao.",
                    )
                except Exception:
                    pass
            if side_opening_timed_out and get_app_store:
                try:
                    get_app_store().update_task(
                        "paramount-action:side_by_side",
                        status="review",
                        last_error="Abertura lado a lado demorou demais e foi enviada para revisao.",
                        attempts_delta=1,
                    )
                except Exception:
                    pass
        else:
            self._recovery_notice_shown = False
            if hasattr(self, "recovery_status_label"):
                running = len(self._action_workers)
                launch_count = len(launching)
                if running or launch_count or getattr(self, "_side_by_side_opening", False):
                    self.recovery_status_label.setText(f"Rodando: {running} acao(oes), {launch_count} perfil(is) abrindo.")
                    self.recovery_status_label.setStyleSheet(f"color:{P['cyan']}; font-weight:800;")
                else:
                    self.recovery_status_label.setText("Estavel. Nenhuma automacao presa.")
                    self.recovery_status_label.setStyleSheet(f"color:{P['green']}; font-weight:800;")

    def recover_paramount_state(self):
        """Cancela filas locais e libera reservas sem derrubar o app inteiro."""
        stopped = 0
        for key, worker in list(self._action_workers.items()):
            try:
                worker.requestInterruption()
                worker.quit()
                if not worker.wait(250):
                    worker.terminate()
                    worker.wait(500)
                stopped += 1
            except Exception:
                pass
            if get_app_store:
                try:
                    get_app_store().update_task(
                        f"paramount-action:{key}",
                        status="review",
                        last_error="Recuperacao manual: acao interrompida.",
                        attempts_delta=1,
                    )
                except Exception:
                    pass
            self._action_workers.pop(key, None)
            self._action_started_at.pop(key, None)

        for profile_id, thread in list(self.launch_threads.items()):
            try:
                thread.stop()
                if not thread.wait(250):
                    thread.terminate()
                    thread.wait(500)
            except Exception:
                pass
            try:
                self.browser_manager.end_profile_launch(profile_id)
            except Exception:
                pass
            self.launch_threads.pop(profile_id, None)

        try:
            for profile_id in list(getattr(self.browser_manager, "launching_profiles", set()) or []):
                self.browser_manager.end_profile_launch(profile_id)
        except Exception:
            pass

        self._side_by_side_jobs = []
        self._side_by_side_total = 0
        self._side_by_side_opening = False
        self._side_by_side_started_at = 0.0
        self._auto_flow_attempts.clear()
        if get_app_store:
            try:
                get_app_store().recover_stale_tasks(
                    max_age_minutes=0,
                    source="paramount_assist",
                    reason="Recuperacao manual: automacao cancelada pelo usuario.",
                )
                get_app_store().add_event(
                    "paramount_assist",
                    "manual_recovery",
                    f"Recuperacao manual executada. Acoes encerradas: {stopped}",
                    level="warning",
                )
                get_app_store().update_task(
                    "paramount-action:side_by_side",
                    status="review",
                    last_error="Recuperacao manual: abertura lado a lado cancelada.",
                    attempts_delta=1,
                )
            except Exception:
                pass
        self.log(f"Modo recuperacao executado. Acoes encerradas: {stopped}.")
        if hasattr(self, "recovery_status_label"):
            self.recovery_status_label.setText("Recuperacao concluida. Pode continuar por uma conta de cada vez.")
            self.recovery_status_label.setStyleSheet(f"color:{P['green']}; font-weight:900;")
        self._show_toast(
            "Recuperacao concluida",
            "Fila local limpa. Os navegadores que ja abriram continuam na tela.",
            "success",
            5200,
        )

    # ─────────────────────────────────────────────────────────────────────────
    # Header
    # ─────────────────────────────────────────────────────────────────────────

    def _header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("Header")
        frame.setFixedHeight(74)
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(20, 0, 20, 0)
        lay.setSpacing(16)

        # Icone decorativo
        icon_lbl = QLabel("▶")
        icon_lbl.setStyleSheet(
            f"font-size:22px; color:{P['cyan']}; background:rgba(56,189,248,0.10);"
            "border:1px solid rgba(56,189,248,0.25); border-radius:10px;"
            "padding:4px 12px; font-weight:900;"
        )
        lay.addWidget(icon_lbl)

        # Textos
        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Paramount Assist")
        title.setStyleSheet(
            f"font-size:20px; font-weight:900; color:#f8fafc;"
            "letter-spacing:-0.5px; background:transparent;"
        )
        sub = QLabel("Central segura para contas, perfis, enderecos e fluxo visivel")
        sub.setStyleSheet(f"color:{P['muted']}; font-size:11px; background:transparent;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        lay.addLayout(title_box, 1)

        # Stats no header
        for attr, label, color in [
            ("summary_total", "contas", P["cyan"]),
            ("summary_profiles", "perfis", P["green"]),
            ("summary_active", "ativas", P["purple"]),
        ]:
            tile = QFrame()
            tile.setObjectName("InfoCard")
            tile.setFixedSize(100, 50)
            tile_lay = QVBoxLayout(tile)
            tile_lay.setContentsMargins(10, 6, 10, 6)
            tile_lay.setSpacing(0)
            val_lbl = QLabel("0")
            val_lbl.setStyleSheet(
                f"font-size:20px; font-weight:900; color:{color};"
                "background:transparent; border:none;"
            )
            cap_lbl = QLabel(label)
            cap_lbl.setStyleSheet(
                f"font-size:10px; color:{P['muted']};"
                "background:transparent; border:none; letter-spacing:0.5px;"
            )
            tile_lay.addWidget(val_lbl, 0, Qt.AlignCenter)
            tile_lay.addWidget(cap_lbl, 0, Qt.AlignCenter)
            setattr(self, attr, val_lbl)
            lay.addWidget(tile)

        return frame

    # ─────────────────────────────────────────────────────────────────────────
    # Painel esquerdo — lista de contas
    # ─────────────────────────────────────────────────────────────────────────

    def _left_panel(self) -> QFrame:
        panel = QFrame()
        panel.setObjectName("Panel")
        panel.setMinimumWidth(300)
        panel.setMaximumWidth(430)
        panel.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        lay = QVBoxLayout(panel)
        lay.setContentsMargins(10, 12, 10, 12)
        lay.setSpacing(8)

        # Cabecalho do painel
        hdr = QHBoxLayout()
        lbl = _section_label("Contas")
        hdr.addWidget(lbl)
        hdr.addStretch()
        lay.addLayout(hdr)

        # Busca
        search_row = QHBoxLayout()
        search_row.setSpacing(6)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍  Buscar email ou senha...")
        self.search_input.setStyleSheet(
            f"background:{P['surface2']}; border:1px solid rgba(56,189,248,0.15);"
            "border-radius:8px; padding:8px 10px; color:#c7d2e0;"
        )
        self.search_input.textChanged.connect(self.refresh_accounts_table)
        search_row.addWidget(self.search_input, 1)
        lay.addLayout(search_row)

        # Tabela de contas — colunas: email, status
        self.accounts_table = QTableWidget(0, 3)
        self.accounts_table.setHorizontalHeaderLabels(["Email", "Senha email", "Status"])
        self.accounts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.accounts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.accounts_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.accounts_table.setTextElideMode(Qt.ElideMiddle)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.accounts_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.accounts_table.setShowGrid(False)
        self.accounts_table.verticalHeader().setVisible(False)
        self.accounts_table.itemSelectionChanged.connect(self.on_account_selected)
        self.accounts_table.cellDoubleClicked.connect(lambda *_: self.open_profile_only_for_current())
        lay.addWidget(self.accounts_table, 1)

        # Hint da conta selecionada
        self.selected_hint = QLabel("Selecione uma conta para ver detalhes.")
        self.selected_hint.setWordWrap(True)
        self.selected_hint.setStyleSheet(
            f"color:{P['subtle']}; background:{P['card']};"
            f"border:1px solid {P['border']}; border-radius:8px;"
            "padding:8px 10px; font-size:11px;"
        )
        lay.addWidget(self.selected_hint)

        lay.addWidget(_divider())

        # Botoes de acao principal
        self._build_left_buttons(lay)

        return panel

    def _build_left_buttons(self, lay: QVBoxLayout):
        grid = QGridLayout()
        grid.setHorizontalSpacing(6)
        grid.setVerticalSpacing(6)
        buttons = [
            ("Continuar", self.smart_continue_for_current, "Success", 0, 0),
            ("Abrir perfil", self.open_profile_only_for_current, "Soft", 0, 1),
            ("Colar emails", self.import_accounts_dialog, "Primary", 1, 0),
            ("Copiar", self.copy_selected_account_login, "Ghost", 1, 1),
            ("Proxima", self.select_next_account, "Ghost", 2, 0),
            ("Salvar", self.save_current_account, "Ghost", 2, 1),
            ("Remover", self.remove_selected_accounts, "Danger", 3, 0),
            ("Importar .txt", self.import_accounts_file, "Ghost", 3, 1),
            ("Ativas", self.copy_active_account_logins, "Success", 4, 0),
        ]
        for text, cb, obj, row, col in buttons:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.setMinimumHeight(34)
            btn.setMinimumWidth(0)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(cb)
            if text == "Ativas":
                btn.setToolTip("Copia todas as contas com assinatura ativa no formato email:senha do email.")
                grid.addWidget(btn, row, col, 1, 2)
            else:
                grid.addWidget(btn, row, col)
        lay.addLayout(grid)
        return

        # Linha de acao rapida (3 botoes principais)
        primary_row = QHBoxLayout()
        primary_row.setSpacing(6)
        for text, cb, obj in [
            ("▶  Continuar", self.smart_continue_for_current, "Success"),
            ("⬡  Abrir perfil", self.open_profile_only_for_current, "Soft"),
            ("⊕  Colar emails", self.import_accounts_dialog, "Primary"),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.setMinimumHeight(38)
            btn.clicked.connect(cb)
            primary_row.addWidget(btn)
        lay.addLayout(primary_row)

        # Linha secundaria
        secondary_row = QHBoxLayout()
        secondary_row.setSpacing(6)
        for text, cb, obj in [
            ("⎘  Copiar", self.copy_selected_account_login, "Ghost"),
            ("→  Proxima", self.select_next_account, "Ghost"),
            ("✓  Salvar", self.save_current_account, "Ghost"),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.setMinimumHeight(34)
            btn.clicked.connect(cb)
            secondary_row.addWidget(btn)
        lay.addLayout(secondary_row)

        # Linha terciaria
        tertiary_row = QHBoxLayout()
        tertiary_row.setSpacing(6)
        remove_btn = QPushButton("✕  Remover")
        remove_btn.setObjectName("Danger")
        remove_btn.setMinimumHeight(32)
        remove_btn.clicked.connect(self.remove_selected_accounts)
        import_btn = QPushButton("↑  Importar .txt")
        import_btn.setObjectName("Ghost")
        import_btn.setMinimumHeight(32)
        import_btn.clicked.connect(self.import_accounts_file)
        active_btn = QPushButton("Ativas")
        active_btn.setObjectName("Success")
        active_btn.setMinimumHeight(32)
        active_btn.setToolTip("Copia todas as contas com assinatura ativa no formato email:senha do email.")
        active_btn.clicked.connect(self.copy_active_account_logins)
        tertiary_row.addWidget(remove_btn)
        tertiary_row.addWidget(import_btn)
        tertiary_row.addWidget(active_btn)
        lay.addLayout(tertiary_row)

    # ─────────────────────────────────────────────────────────────────────────
    # Painel direito — tabs
    # ─────────────────────────────────────────────────────────────────────────

    def _right_panel(self) -> QWidget:
        container = QWidget()
        lay = QVBoxLayout(container)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(0)

        self.tabs = QTabWidget()
        self.tabs.tabBar().setUsesScrollButtons(True)
        self.tabs.tabBar().setExpanding(False)
        self.tabs.tabBar().setElideMode(Qt.ElideRight)
        self.tabs.addTab(self._flow_tab(), "⚡  Fluxo")
        self.tabs.addTab(self._address_tab(), "📍  Enderecos")
        self.tabs.addTab(self._cards_tab(), "💳  Cartoes")
        self.tabs.addTab(self._help_tab(), "📋  Logs")
        lay.addWidget(self.tabs)
        return container

    # ─────────────────────────────────────────────────────────────────────────
    # Tab Fluxo
    # ─────────────────────────────────────────────────────────────────────────

    def _flow_tab(self) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(14)

        # ── Quick start ────────────────────────────────────────────────────
        quick = QGroupBox("Início rápido")
        quick_lay = QVBoxLayout(quick)
        quick_lay.setSpacing(10)

        hint = QLabel("Use estes passos na ordem. A ferramenta para antes do pagamento final.")
        hint.setWordWrap(True)
        hint.setStyleSheet(
            f"color:{P['cyan']}; font-weight:700; font-size:11px;"
            "background:transparent; border:none; padding:0 0 4px 0;"
        )
        quick_lay.addWidget(hint)

        quick_grid = QGridLayout()
        quick_grid.setSpacing(8)
        self._paramount_quick_buttons = []
        for text, cb, row, col, obj in [
            ("▶  Continuar fluxo automatico", self.smart_continue_for_current, 0, 0, "Success"),
            ("⬡  Abrir perfil sem automacao",  self.open_profile_only_for_current, 0, 1, "Soft"),
            ("⊕  Colar emails/senhas",         self.import_accounts_dialog, 0, 2, "Primary"),
            ("▥  Abrir ate 3 lado a lado",     self.open_side_by_side_for_accounts, 1, 0, "Primary"),
        ]:
            btn = QPushButton(text)
            btn.setProperty("full_text", text)
            btn.setObjectName(obj)
            btn.setMinimumHeight(42)
            btn.setMinimumWidth(0)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(cb)
            self._paramount_quick_buttons.append(btn)
            if text.startswith("▥"):
                quick_grid.addWidget(btn, row, col, 1, 3)
            else:
                quick_grid.addWidget(btn, row, col)
        quick_lay.addLayout(quick_grid)

        recovery_row = QHBoxLayout()
        recovery_row.setSpacing(8)
        self.recovery_status_label = QLabel("Estavel. Nenhuma automacao presa.")
        self.recovery_status_label.setWordWrap(True)
        self.recovery_status_label.setStyleSheet(f"color:{P['green']}; font-weight:800;")
        recovery_btn = QPushButton("Recuperar travas")
        recovery_btn.setObjectName("Ghost")
        recovery_btn.setMinimumHeight(34)
        recovery_btn.setCursor(Qt.PointingHandCursor)
        recovery_btn.clicked.connect(self.recover_paramount_state)
        recovery_row.addWidget(self.recovery_status_label, 1)
        recovery_row.addWidget(recovery_btn)
        quick_lay.addLayout(recovery_row)
        lay.addWidget(quick)

        # ── Conta selecionada ──────────────────────────────────────────────
        account_group = QGroupBox("Conta selecionada")
        form = QGridLayout(account_group)
        form.setContentsMargins(12, 12, 12, 12)
        form.setHorizontalSpacing(8)
        form.setVerticalSpacing(6)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(3, 1)

        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@exemplo.com")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha fixa da Paramount")
        self.email_password_input = QLineEdit()
        self.email_password_input.setPlaceholderText("Senha original do email")

        self.status_combo = QComboBox()
        self.status_combo.addItems(self.STATUSES)

        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(0)

        self.plan_combo = QComboBox()
        self.plan_combo.setEditable(True)
        self.plan_combo.addItems(PLAN_OPTIONS)
        self.plan_combo.setToolTip("Texto do plano a procurar na pagina.")

        self.person_name_input = QLineEdit()
        self.person_name_input.setPlaceholderText("Gerado pelo banco do projeto")
        self.person_cpf_input = QLineEdit()
        self.person_cpf_input.setPlaceholderText("CPF")
        self.person_birth_input = QLineEdit()
        self.person_birth_input.setPlaceholderText("Nascimento")
        for w in [self.person_name_input, self.person_cpf_input, self.person_birth_input]:
            w.setReadOnly(True)
        for w in [
            self.email_input,
            self.password_input,
            self.email_password_input,
            self.status_combo,
            self.profile_combo,
            self.plan_combo,
            self.person_name_input,
            self.person_cpf_input,
            self.person_birth_input,
        ]:
            w.setMinimumWidth(0)
            w.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Observacoes, erro visto, etapa parada...")
        self.notes_input.setMinimumHeight(38)
        self.notes_input.setMaximumHeight(54)

        def _lbl(text):
            l = QLabel(text)
            l.setStyleSheet(f"color:{P['subtle']}; font-size:11px; font-weight:700;")
            return l

        form.addWidget(_lbl("Email"), 0, 0)
        form.addWidget(self.email_input, 0, 1)
        form.addWidget(_lbl("Senha Paramount"), 0, 2)
        form.addWidget(self.password_input, 0, 3)

        form.addWidget(_lbl("Senha email"), 1, 0)
        form.addWidget(self.email_password_input, 1, 1)
        form.addWidget(_lbl("Status"), 1, 2)
        form.addWidget(self.status_combo, 1, 3)

        form.addWidget(_lbl("Perfil"), 2, 0)
        form.addWidget(self.profile_combo, 2, 1)
        form.addWidget(_lbl("Plano"), 2, 2)
        form.addWidget(self.plan_combo, 2, 3)

        form.addWidget(_lbl("Nome"), 3, 0)
        form.addWidget(self.person_name_input, 3, 1)
        form.addWidget(_lbl("CPF / Nasc."), 3, 2)
        doc_row = QHBoxLayout()
        doc_row.setSpacing(6)
        doc_row.addWidget(self.person_cpf_input, 2)
        doc_row.addWidget(self.person_birth_input, 1)
        form.addLayout(doc_row, 3, 3)

        form.addWidget(_lbl("Notas"), 4, 0)
        form.addWidget(self.notes_input, 4, 1, 1, 3)

        lay.addWidget(account_group)

        # ── Ajustes manuais ────────────────────────────────────────────────
        actions = QGroupBox("Ajustes manuais")
        grid = QGridLayout(actions)
        grid.setSpacing(8)
        for text, cb, row, col, obj in [
            ("Abrir cadastro",     self.open_signup_for_current,    0, 0, "Primary"),
            ("Preencher cadastro", self.fill_signup_for_current_async, 0, 1, "Success"),
            ("Selecionar plano",   self.quick_select_plan_async,    0, 2, "Soft"),
            ("CPF + endereco",     self.fill_cpf_address_for_current, 0, 3, "Success"),
            ("Ver assinatura",     self.check_subscription_for_current, 1, 0, "Soft"),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.setMinimumHeight(38)
            btn.setMinimumWidth(0)
            btn.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            btn.clicked.connect(cb)
            if text == "Ver assinatura":
                grid.addWidget(btn, row, col, 1, 4)
            else:
                grid.addWidget(btn, row, col)
        for col in range(4):
            grid.setColumnStretch(col, 1)
        lay.addWidget(actions)

        # ── Como usar (card informativo) ───────────────────────────────────
        info_card = QFrame()
        self.paramount_info_card = info_card
        info_card.setObjectName("InfoCard")
        info_lay = QVBoxLayout(info_card)
        info_lay.setContentsMargins(14, 12, 14, 12)
        info_lay.setSpacing(6)
        steps_hdr = _section_label("Como usar")
        info_lay.addWidget(steps_hdr)
        for i, text in enumerate([
            "Cole email:senha, selecione a conta e use Continuar fluxo automatico.",
            "A ferramenta tenta abrir, preencher, clicar em continuar, selecionar plano e preencher CPF/endereco.",
            "Ela para antes de pagamento/compra final para voce conferir manualmente.",
        ], start=1):
            step_row = QHBoxLayout()
            num = QLabel(str(i))
            num.setFixedSize(20, 20)
            num.setAlignment(Qt.AlignCenter)
            num.setStyleSheet(
                f"color:{P['bg']}; background:{P['cyan']}; border-radius:10px;"
                "font-weight:900; font-size:10px; border:none;"
            )
            step_lbl = QLabel(text)
            step_lbl.setWordWrap(True)
            step_lbl.setStyleSheet(f"color:{P['subtle']}; font-size:11px;")
            step_row.addWidget(num, 0, Qt.AlignTop)
            step_row.addWidget(step_lbl, 1)
            info_lay.addLayout(step_row)
        lay.addWidget(info_card)

        lay.addStretch()
        scroll.setWidget(page)
        return scroll

    # ─────────────────────────────────────────────────────────────────────────
    # Tab Enderecos
    # ─────────────────────────────────────────────────────────────────────────

    def _address_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(12)

        group = QGroupBox("Endereco da conta / perfil")
        form = QGridLayout(group)
        form.setSpacing(8)
        form.setColumnStretch(1, 1)
        form.setColumnStretch(3, 1)

        self.addr_cep = QLineEdit()
        self.addr_street = QLineEdit()
        self.addr_number = QLineEdit()
        self.addr_neighborhood = QLineEdit()
        self.addr_city = QLineEdit()
        self.addr_state = QLineEdit()
        self.addr_uf = QLineEdit()

        for widget, ph in [
            (self.addr_cep,          "00000-000"),
            (self.addr_street,       "Rua / Avenida"),
            (self.addr_number,       "Numero"),
            (self.addr_neighborhood, "Bairro"),
            (self.addr_city,         "Cidade"),
            (self.addr_state,        "Estado"),
            (self.addr_uf,           "UF"),
        ]:
            widget.setPlaceholderText(ph)

        def _lbl(t):
            l = QLabel(t)
            l.setStyleSheet(f"color:{P['subtle']}; font-size:11px; font-weight:700;")
            return l

        form.addWidget(_lbl("CEP"),    0, 0);  form.addWidget(self.addr_cep,          0, 1)
        form.addWidget(_lbl("Rua"),    0, 2);  form.addWidget(self.addr_street,        0, 3)
        form.addWidget(_lbl("Numero"), 1, 0);  form.addWidget(self.addr_number,        1, 1)
        form.addWidget(_lbl("Bairro"), 1, 2);  form.addWidget(self.addr_neighborhood,  1, 3)
        form.addWidget(_lbl("Cidade"), 2, 0);  form.addWidget(self.addr_city,          2, 1)
        form.addWidget(_lbl("Estado"), 2, 2);  form.addWidget(self.addr_state,         2, 3)
        form.addWidget(_lbl("UF"),     3, 0);  form.addWidget(self.addr_uf,            3, 1)

        btns = QHBoxLayout()
        btns.setSpacing(8)
        for text, cb, obj in [
            ("⟳  Gerar do projeto",     self.generate_address_for_current, "Primary"),
            ("✓  Salvar endereco",       self.save_current_account,         "Success"),
            ("⎘  Copiar endereco",       self.copy_current_address,         "Soft"),
            ("↑  Preencher pagina",      self.fill_address_for_current,     "Soft"),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.setMinimumHeight(38)
            btn.clicked.connect(cb)
            btns.addWidget(btn)
        form.addLayout(btns, 4, 0, 1, 4)

        lay.addWidget(group)
        lay.addStretch()
        return page

    # ─────────────────────────────────────────────────────────────────────────
    # Tab Cartoes
    # ─────────────────────────────────────────────────────────────────────────

    def _cards_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(12)

        # Banner de aviso
        banner = QFrame()
        banner.setObjectName("InfoCard")
        banner.setStyleSheet(
            "background:#061a10; border:1px solid rgba(52,211,153,0.22); border-radius:10px;"
        )
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(14, 10, 14, 10)
        icon = QLabel("🔒")
        icon.setStyleSheet("font-size:18px; background:transparent; border:none;")
        msg = QLabel(
            "Apenas referencia de cartoes proprios. O app salva somente final, "
            "validade e titular — sem CVV e sem testar pagamento."
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(
            f"color:#86efac; font-weight:700; font-size:11px; background:transparent; border:none;"
        )
        banner_lay.addWidget(icon)
        banner_lay.addWidget(msg, 1)
        lay.addWidget(banner)

        # Tabela
        self.cards_table = QTableWidget(0, 5)
        self.cards_table.setHorizontalHeaderLabels(["Apelido", "Final", "Validade", "Titular", "Status"])
        self.cards_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        for col in [1, 2, 4]:
            self.cards_table.horizontalHeader().setSectionResizeMode(col, QHeaderView.ResizeToContents)
        self.cards_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.cards_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.cards_table.setShowGrid(False)
        self.cards_table.verticalHeader().setVisible(False)
        lay.addWidget(self.cards_table, 1)

        # Formulario de adicao
        form_group = QGroupBox("Adicionar referencia de cartao")
        grid = QGridLayout(form_group)
        grid.setSpacing(8)

        self.card_label  = QLineEdit(); self.card_label.setPlaceholderText("Apelido")
        self.card_input  = QLineEdit(); self.card_input.setPlaceholderText("Numero ou final 4")
        self.card_expiry = QLineEdit(); self.card_expiry.setPlaceholderText("MM/AA")
        self.card_holder = QLineEdit(); self.card_holder.setPlaceholderText("Titular")
        self.card_status = QComboBox()
        self.card_status.addItems(["novo", "usando", "aprovado manual", "recusado manual", "pausado"])

        grid.addWidget(self.card_label, 0, 0)
        grid.addWidget(self.card_input, 0, 1)
        grid.addWidget(self.card_expiry, 0, 2)
        grid.addWidget(self.card_holder, 0, 3)
        grid.addWidget(self.card_status, 0, 4)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        for text, cb, obj in [
            ("⊕  Adicionar referencia", self.add_card, "Primary"),
            ("✕  Remover selecionado",  self.remove_selected_card, "Danger"),
            ("⎘  Copiar resumo",        self.copy_selected_card, "Soft"),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.setMinimumHeight(38)
            btn.clicked.connect(cb)
            btn_row.addWidget(btn)
        grid.addLayout(btn_row, 1, 0, 1, 5)
        lay.addWidget(form_group)
        return page

    # ─────────────────────────────────────────────────────────────────────────
    # Tab Logs
    # ─────────────────────────────────────────────────────────────────────────

    def _help_tab(self) -> QWidget:
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(14, 14, 14, 14)
        lay.setSpacing(10)

        # Aviso
        banner = QFrame()
        banner.setObjectName("InfoCard")
        banner_lay = QHBoxLayout(banner)
        banner_lay.setContentsMargins(12, 8, 12, 8)
        msg = QLabel(
            "Esta ferramenta organiza e acelera o trabalho visivel. "
            "Nao faz compra invisivel, nao testa cartao e nao burla verificacao humana."
        )
        msg.setWordWrap(True)
        msg.setStyleSheet(f"color:{P['subtle']}; font-size:11px; background:transparent; border:none;")
        banner_lay.addWidget(msg)
        lay.addWidget(banner)

        # Log box
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Aguardando eventos...")
        self.log_box.setStyleSheet(
            f"background:#040810; color:#4ade80;"
            "border:1px solid rgba(52,211,153,0.15); border-radius:10px;"
            "padding:12px; font-family:Consolas,'Cascadia Code',monospace; font-size:11px;"
        )
        lay.addWidget(self.log_box, 1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(8)
        clear_btn = QPushButton("✕  Limpar logs")
        clear_btn.setObjectName("Ghost")
        clear_btn.clicked.connect(self.clear_logs)
        btn_row.addStretch()
        btn_row.addWidget(clear_btn)
        lay.addLayout(btn_row)

        return page

    # =========================================================================
    # Toda a logica abaixo e identica ao original — sem alteracoes funcionais
    # =========================================================================

    def summary_label(self):
        """Compat shim — nao mais um unico QLabel."""
        pass

    # helpers internos de atualizacao de stats
    def _update_summary(self, total: int, ready: int):
        if hasattr(self, "summary_total"):
            self.summary_total.setText(str(total))
        if hasattr(self, "summary_profiles"):
            self.summary_profiles.setText(str(ready))
        if hasattr(self, "summary_active"):
            active = sum(1 for account in self.data.get("accounts", []) if account.get("status") == "assinatura ativa")
            self.summary_active.setText(str(active))

    def load_data(self):
        self.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not self.DATA_FILE.exists():
            return
        try:
            raw = json.loads(self.DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self.data.update({
                    "accounts": raw.get("accounts", []) if isinstance(raw.get("accounts"), list) else [],
                    "cards":    raw.get("cards",    []) if isinstance(raw.get("cards"),    list) else [],
                    "logs":     raw.get("logs",     []) if isinstance(raw.get("logs"),     list) else [],
                    "settings": raw.get("settings", {}) if isinstance(raw.get("settings"), dict)  else {},
                })
                if self.repair_profile_links():
                    self.save_data()
        except Exception as exc:
            self.log(f"Erro ao carregar dados: {exc}")

    def repair_profile_links(self) -> bool:
        profiles = self.paramount_profiles(include_all=False)
        by_name = [(profile.id, (getattr(profile, "name", "") or "").lower()) for profile in profiles]
        changed = False
        used = {a.get("profile_id") for a in self.data.get("accounts", []) if a.get("profile_id")}
        for account in self.data.get("accounts", []):
            if account.get("profile_id"):
                continue
            email = (account.get("email") or "").strip().lower()
            if "@" not in email:
                continue
            prefix = email.split("@", 1)[0][:18]
            candidates = [pid for pid, name in by_name if pid not in used and prefix and prefix in name]
            if len(candidates) == 1:
                account["profile_id"] = candidates[0]
                account["updated_at"] = _now()
                used.add(candidates[0])
                changed = True
        if changed:
            self.log("Vinculos de perfil reparados automaticamente.")
        return changed

    def _central_status_for_account(self, account: Dict) -> str:
        raw = str(account.get("status") or "").strip().lower()
        notes = str(account.get("notes") or "").strip().lower()
        combined = f"{raw} {notes}"
        if any(token in combined for token in ("erro", "falha", "403", "bloqueio", "negado", "reprov")):
            return "error"
        if "assinatura ativa" in combined or raw in {"ativa", "sucesso", "finalizado"}:
            return "success"
        if any(token in combined for token in ("rodando", "processando", "abrindo", "preenchendo")):
            return "running"
        if any(token in combined for token in ("login ok", "perfil pronto", "endereco ok", "endereço ok", "plano")):
            return "review"
        return "pending"

    def _sync_accounts_to_central_store(self, store, accounts: List[Dict]) -> None:
        for account in accounts:
            email = str(account.get("email") or "").strip()
            if not email:
                continue
            account_id = account.get("id") or hashlib.md5(email.lower().encode()).hexdigest()[:12]
            store.upsert_task(
                f"paramount:{account_id}",
                "paramount-account-flow",
                email,
                source="paramount_assist",
                status=self._central_status_for_account(account),
                entity_type="account",
                entity_id=str(account_id),
                priority=20,
                payload={
                    "email": email,
                    "status": account.get("status", ""),
                    "profile_id": account.get("profile_id", ""),
                    "plan": account.get("plan", ""),
                    "has_email_password": bool(account.get("email_password")),
                    "updated_at": account.get("updated_at", ""),
                },
                last_error=str(account.get("last_error") or ""),
            )

    def save_data(self):
        self.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": _now(),
            "accounts":   self.data.get("accounts", []),
            "cards":      self.data.get("cards", []),
            "logs":       self.data.get("logs", [])[-300:],
            "settings":   self.data.get("settings", {}),
        }
        self.DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        if get_app_store:
            try:
                accounts = self.data.get("accounts", [])
                store = get_app_store()
                store.set_state(
                    "paramount_assist.summary",
                    {
                        "accounts": len(accounts),
                        "cards": len(self.data.get("cards", [])),
                        "active": sum(1 for a in accounts if a.get("status") == "assinatura ativa"),
                        "updated_at": payload["updated_at"],
                    },
                )
                self._sync_accounts_to_central_store(store, accounts)
            except Exception:
                pass

    def log(self, message: str):
        app = QApplication.instance()
        if app is not None and QThread.currentThread() != app.thread():
            self._log_signal.emit(str(message))
            return
        self._append_log(message)

    def _append_log(self, message: str):
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        self.data.setdefault("logs", []).append(entry)
        if hasattr(self, "log_box"):
            self.log_box.setPlainText("\n".join(self.data.get("logs", [])[-200:]))
            self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())
        if get_app_store:
            try:
                level = "error" if any(token in message.lower() for token in ("erro", "falha", "403")) else "info"
                get_app_store().add_event("paramount_assist", "log", message, level=level)
            except Exception:
                pass

    def refresh_all(self):
        self.refresh_profile_combo()
        self.refresh_accounts_table()
        self.refresh_cards_table()
        self.refresh_logs()
        total = len(self.data.get("accounts", []))
        ready = len(self.linked_profile_ids())
        self._update_summary(total, ready)

    def refresh_logs(self):
        if hasattr(self, "log_box"):
            self.log_box.setPlainText("\n".join(self.data.get("logs", [])[-200:]))

    def refresh_profile_combo(self):
        account = self.current_account()
        current = account.get("profile_id", "") if account else ""
        if not current and not account and hasattr(self, "profile_combo"):
            current = self.profile_combo.currentData()
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItem("Sem perfil vinculado", "")
        for profile in self.paramount_profiles(include_all=False):
            self.profile_combo.addItem(profile.name, profile.id)
        if current:
            idx = self.profile_combo.findData(current)
            if idx < 0:
                profile = self.browser_manager.get_profile(current)
                if profile and not getattr(profile, "archived", False):
                    self.profile_combo.addItem(profile.name, current)
                    idx = self.profile_combo.findData(current)
            if idx >= 0:
                self.profile_combo.setCurrentIndex(idx)
        self.profile_combo.blockSignals(False)

    def linked_profile_ids(self) -> set:
        ids = set()
        for account in self.data.get("accounts", []):
            profile_id = account.get("profile_id", "")
            if profile_id and self.profile_link_is_valid(profile_id):
                ids.add(profile_id)
        return ids

    def is_paramount_assist_profile(self, profile) -> bool:
        if not profile:
            return False
        tags = {str(t).lower() for t in getattr(profile, "tags", []) or []}
        name = (getattr(profile, "name", "") or "").lower()
        return ("paramount" in tags and "assist" in tags) or name.startswith("paramount ")

    def paramount_profiles(self, include_all: bool = False, only_linked: bool = True):
        linked_ids = self.linked_profile_ids() if only_linked and not include_all else set()
        if only_linked and not include_all and not linked_ids:
            return []
        profiles = []
        for profile in self.browser_manager.list_profiles(include_archived=False):
            tags = [str(t).lower() for t in getattr(profile, "tags", []) or []]
            name = (getattr(profile, "name", "") or "").lower()
            if linked_ids and profile.id not in linked_ids:
                continue
            if include_all or "paramount" in tags or "paramount" in name:
                profiles.append(profile)
        return profiles

    def refresh_accounts_table(self):
        query = self.search_input.text().strip().lower() if hasattr(self, "search_input") else ""
        if self.cleanup_invalid_profile_links():
            self.save_data()
        accounts = self.data.get("accounts", [])
        if query:
            accounts = [
                a for a in accounts
                if query in " ".join([
                    a.get("email", ""),
                    a.get("password", ""),
                    a.get("email_password", ""),
                    a.get("status", ""),
                    self.profile_name(a.get("profile_id")),
                ]).lower()
            ]

        self.accounts_table.blockSignals(True)
        self.accounts_table.setRowCount(0)
        current_row = -1
        for account in accounts:
            row = self.accounts_table.rowCount()
            self.accounts_table.insertRow(row)
            status = account.get("status", "novo")
            values = [account.get("email", ""), account.get("email_password", ""), status]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, account.get("id"))
                # Colorir linha por status
                if status in STATUS_COLORS:
                    _, fg = STATUS_COLORS[status]
                    if col == 2:
                        item.setForeground(QColor(fg))
                self.accounts_table.setItem(row, col, item)
            if account.get("id") == self.current_account_id:
                current_row = row
        if current_row >= 0:
            self.accounts_table.selectRow(current_row)
        self.accounts_table.blockSignals(False)

        total = len(self.data.get("accounts", []))
        ready = len(self.linked_profile_ids())
        self._update_summary(total, ready)
        self.update_selected_hint()

    def profile_link_is_valid(self, profile_id: str) -> bool:
        if not profile_id:
            return False
        profile = self.browser_manager.get_profile(profile_id)
        return bool(profile and not getattr(profile, "archived", False))

    def cleanup_invalid_profile_links(self) -> bool:
        changed = False
        for account in self.data.get("accounts", []):
            profile_id = account.get("profile_id", "")
            if profile_id and not self.profile_link_is_valid(profile_id):
                account["profile_id"] = ""
                if account.get("status") == "perfil pronto":
                    account["status"] = "novo"
                account["updated_at"] = _now()
                changed = True
        if changed:
            self.log("Removi vinculos de perfis apagados/arquivados da lista Paramount.")
        return changed

    def update_selected_hint(self):
        if not hasattr(self, "selected_hint"):
            return
        account = self.current_account()
        if not account:
            self.selected_hint.setText("Selecione uma conta para ver detalhes.")
            return
        profile_name = self.profile_name(account.get("profile_id")) or "sem perfil"
        address = self.normalize_address(account.get("address", {}) or {})
        address_ok = "✓ endereco OK" if self.address_is_complete(address) else "⚠ sem endereco"
        status = account.get("status", "novo")
        subscription = account.get("subscription_status", "")
        subscription_text = f"  ·  assinatura: {subscription}" if subscription else ""
        _, status_color = STATUS_COLORS.get(status, ("", P["subtle"]))
        self.selected_hint.setStyleSheet(
            f"color:{P['subtle']}; background:{P['card']};"
            f"border:1px solid {P['border']}; border-radius:8px;"
            "padding:8px 10px; font-size:11px;"
        )
        self.selected_hint.setText(
            f"{account.get('email', '')}  ·  {profile_name}  ·  {status}  ·  {address_ok}{subscription_text}"
        )

    def refresh_cards_table(self):
        self.cards_table.setRowCount(0)
        for card in self.data.get("cards", []):
            row = self.cards_table.rowCount()
            self.cards_table.insertRow(row)
            values = [
                card.get("label", ""),
                card.get("last4", ""),
                card.get("expiry", ""),
                card.get("holder", ""),
                card.get("status", ""),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, card.get("id"))
                self.cards_table.setItem(row, col, item)

    # ── Selecao de conta ──────────────────────────────────────────────────────

    def current_account(self) -> Optional[Dict]:
        if self.current_account_id:
            for account in self.data.get("accounts", []):
                if account.get("id") == self.current_account_id:
                    return account
        row = self.accounts_table.currentRow() if hasattr(self, "accounts_table") else -1
        if row < 0:
            return None
        item = self.accounts_table.item(row, 0)
        account_id = item.data(Qt.UserRole) if item else ""
        for account in self.data.get("accounts", []):
            if account.get("id") == account_id:
                return account
        return None

    def selected_account_rows(self) -> List[int]:
        if not hasattr(self, "accounts_table"):
            return []
        return sorted({idx.row() for idx in self.accounts_table.selectedIndexes()})

    def selected_accounts(self) -> List[Dict]:
        accounts = []
        seen = set()
        for row in self.selected_account_rows():
            item = self.accounts_table.item(row, 0)
            account_id = item.data(Qt.UserRole) if item else ""
            if not account_id or account_id in seen:
                continue
            seen.add(account_id)
            for account in self.data.get("accounts", []):
                if account.get("id") == account_id:
                    accounts.append(account)
                    break
        return accounts

    def accounts_for_parallel_open(self, limit: int = 3) -> List[Dict]:
        selected = [a for a in self.selected_accounts() if (a.get("email") or "").strip()]
        accounts = [a for a in self.data.get("accounts", []) if (a.get("email") or "").strip()]
        if not accounts:
            return []
        if selected:
            picked = []
            seen_selected = set()
            for account in selected:
                account_id = account.get("id") or account.get("email")
                if account_id and account_id not in seen_selected:
                    seen_selected.add(account_id)
                    picked.append(account)
                if len(picked) >= limit:
                    return picked[:limit]
            for account in accounts:
                account_id = account.get("id") or account.get("email")
                if not account_id or account_id in seen_selected:
                    continue
                seen_selected.add(account_id)
                picked.append(account)
                if len(picked) >= limit:
                    break
            return picked[:limit]
        current = selected[0] if selected else self.current_account()
        start = 0
        if current:
            for idx, account in enumerate(accounts):
                if account.get("id") == current.get("id"):
                    start = idx
                    break
        ordered = accounts[start:] + accounts[:start]
        picked = []
        seen = set()
        for account in ordered:
            account_id = account.get("id") or account.get("email")
            if not account_id or account_id in seen:
                continue
            seen.add(account_id)
            picked.append(account)
            if len(picked) >= limit:
                break
        return picked

    def on_account_selected(self):
        rows = self.selected_account_rows()
        account = None
        if rows:
            item = self.accounts_table.item(rows[0], 0)
            account_id = item.data(Qt.UserRole) if item else ""
            if account_id:
                for candidate in self.data.get("accounts", []):
                    if candidate.get("id") == account_id:
                        account = candidate
                        break
        if account is None:
            account = self.current_account()
        if account:
            self.current_account_id = account.get("id", "")
        self.populate_form()
        self.update_selected_hint()

    def populate_form(self):
        account = self.current_account()
        if not account:
            return
        for widget, key in [
            (self.email_input,    "email"),
            (self.password_input, "password"),
            (self.email_password_input, "email_password"),
        ]:
            widget.setText(account.get(key, ""))
        self.status_combo.setCurrentText(account.get("status", self.STATUSES[0]))
        profile_id = account.get("profile_id", "")
        idx = self.profile_combo.findData(profile_id)
        if idx >= 0:
            self.profile_combo.setCurrentIndex(idx)
        plan = account.get("plan", "")
        if plan:
            idx = self.plan_combo.findText(plan)
            if idx >= 0:
                self.plan_combo.setCurrentIndex(idx)
            else:
                self.plan_combo.setCurrentText(plan)
        self.notes_input.setPlainText(account.get("notes", ""))
        person = self.normalize_person(account.get("person", {}) or {})
        self.person_name_input.setText(person.get("name", ""))
        self.person_cpf_input.setText(person.get("cpf", ""))
        self.person_birth_input.setText(person.get("birth", ""))
        address = self.normalize_address(account.get("address", {}) or {})
        for widget, key in [
            (self.addr_cep,          "cep"),
            (self.addr_street,       "street"),
            (self.addr_number,       "number"),
            (self.addr_neighborhood, "neighborhood"),
            (self.addr_city,         "city"),
            (self.addr_state,        "state"),
            (self.addr_uf,           "uf"),
        ]:
            widget.setText(address.get(key, ""))

    def account_from_form(self) -> Dict:
        account = self.current_account() or {}
        account["email"]      = self.email_input.text().strip()
        account["password"]   = self.password_input.text().strip()
        account["email_password"] = self.email_password_input.text().strip()
        account["status"]     = self.status_combo.currentText()
        profile_choice = self.profile_combo.currentData()
        if profile_choice:
            account["profile_id"] = profile_choice
        else:
            account.setdefault("profile_id", "")
        account["plan"]       = self.plan_combo.currentText().strip()
        account["notes"]      = self.notes_input.toPlainText().strip()
        account["person"]     = self.person_from_form(account.get("person", {}) or {})
        account["updated_at"] = _now()
        return account

    @staticmethod
    def normalize_person(person: Dict) -> Dict:
        if not isinstance(person, dict):
            person = {}
        name = (person.get("name") or person.get("nome") or "").strip()
        cpf = (person.get("cpf") or "").strip()
        birth = (person.get("birth") or person.get("nascimento") or "").strip()
        return {
            "name": name,
            "nome": name,
            "cpf": cpf,
            "birth": birth,
            "nascimento": birth,
        }

    @staticmethod
    def person_name_is_valid(name: str) -> bool:
        text = " ".join(str(name or "").strip().split())
        if not text or "@" in text or ":" in text:
            return False
        parts = [p for p in text.split() if len(p) > 1]
        return len(parts) >= 2

    def person_from_form(self, fallback: Optional[Dict] = None) -> Dict:
        person = self.normalize_person(fallback or {})
        name = self.person_name_input.text().strip() if hasattr(self, "person_name_input") else ""
        cpf = self.person_cpf_input.text().strip() if hasattr(self, "person_cpf_input") else ""
        birth = self.person_birth_input.text().strip() if hasattr(self, "person_birth_input") else ""
        if name:
            person["name"] = person["nome"] = name
        if cpf:
            person["cpf"] = cpf
        if birth:
            person["birth"] = person["nascimento"] = birth
        return person

    def load_person_to_form(self, person: Dict):
        person = self.normalize_person(person)
        self.person_name_input.setText(person.get("name", ""))
        self.person_cpf_input.setText(person.get("cpf", ""))
        self.person_birth_input.setText(person.get("birth", ""))

    def project_person_payload(self, used_cpfs: Optional[set] = None) -> Dict:
        if not self.db or not hasattr(self.db, "get_random_pair"):
            return {}
        used_cpfs = used_cpfs or set()
        for _ in range(12):
            try:
                person = self.db.get_random_pair({"require_birth": True, "idade_max": 59})
            except TypeError:
                person = self.db.get_random_pair({})
            except Exception as exc:
                self.log(f"Nao consegui buscar pessoa no banco: {exc}")
                return {}
            if not person:
                return {}
            payload = self.normalize_person({
                "name": person.get("nome") or person.get("name") or "",
                "cpf": person.get("cpf") or "",
                "birth": person.get("nascimento") or person.get("birth") or "",
            })
            cpf = payload.get("cpf", "")
            if payload.get("name") and cpf and cpf not in used_cpfs:
                used_cpfs.add(cpf)
                return payload
        return {}

    def ensure_person_for_account(self, account: Dict, persist: bool = True) -> Dict:
        person = self.normalize_person(account.get("person", {}) or {})
        if self.person_name_is_valid(person.get("name", "")):
            account["person"] = person
            if persist:
                self.load_person_to_form(person)
            return person
        used_cpfs = {
            self.normalize_person(a.get("person", {}) or {}).get("cpf", "")
            for a in self.data.get("accounts", [])
            if self.normalize_person(a.get("person", {}) or {}).get("cpf", "")
        }
        generated = self.project_person_payload(used_cpfs)
        if generated:
            account["person"] = generated
            if persist:
                self.load_person_to_form(generated)
                account["updated_at"] = _now()
                self.save_data()
                self.refresh_accounts_table()
                self.log(f"Pessoa vinculada: {generated.get('name', '')} | CPF {generated.get('cpf', '')}")
            return generated
        return person

    def address_from_form(self) -> Dict:
        street = self.addr_street.text().strip()
        number = self.addr_number.text().strip()
        neighborhood = self.addr_neighborhood.text().strip()
        city = self.addr_city.text().strip()
        state = self.addr_state.text().strip()
        uf = self.addr_uf.text().strip().upper()
        return self.normalize_address({
            "cep": self.addr_cep.text().strip(),
            "street": street,
            "logradouro": street,
            "rua": street,
            "number": number,
            "numero": number,
            "neighborhood": neighborhood,
            "bairro": neighborhood,
            "city": city,
            "cidade": city,
            "state": state,
            "estado": state,
            "uf": uf,
        })

    def is_valid_street(self, street: str, address: Dict = None) -> bool:
        address = address or {}
        raw = str(street or "").strip()
        compact = re.sub(r"[^A-Za-zÀ-ÿ0-9]", "", raw).upper()
        uf = str(address.get("uf", "") or "").strip().upper()
        state = str(address.get("estado") or address.get("state") or "").strip().upper()
        city = str(address.get("cidade") or address.get("city") or "").strip().upper()
        if len(compact) < 4:
            return False
        if compact in {"BR", "BRA", "BRASIL"}:
            return False
        if uf and compact == uf:
            return False
        if state and compact == re.sub(r"[^A-ZÀ-Ý0-9]", "", state):
            return False
        if city and compact == re.sub(r"[^A-ZÀ-Ý0-9]", "", city):
            return False
        return True

    def normalize_address(self, addr: Dict) -> Dict:
        if not isinstance(addr, dict):
            return {}
        aliases = {
            "logradouro":  "street",
            "rua":         "street",
            "numero":      "number",
            "bairro":      "neighborhood",
            "cidade":      "city",
            "estado":      "state",
            "complemento": "complement",
        }
        out = dict(addr)
        for alias, canonical in aliases.items():
            if alias in out and canonical not in out:
                out[canonical] = out.get(alias)

        cep = str(out.get("cep", "") or "").strip()
        uf = str(out.get("uf") or "").strip().upper()
        state = str(out.get("state") or out.get("estado") or "").strip()
        if (len(uf) != 2 or uf not in UF_NAMES) and state:
            state_clean = re.sub(r"[^A-Z]", "", state.upper())
            for candidate_uf, candidate_name in UF_NAMES.items():
                if state_clean == re.sub(r"[^A-Z]", "", candidate_name.upper()):
                    uf = candidate_uf
                    break
        if (len(uf) != 2 or uf not in UF_NAMES) and self.address_reserve:
            try:
                inferred = self.address_reserve._infer_uf_from_cep(cep)
                if inferred:
                    uf = inferred
            except Exception:
                pass
        if uf in UF_NAMES:
            out["uf"] = uf
            generator_states = getattr(self.address_generator, "ESTADOS", {}) if self.address_generator else {}
            state_name = generator_states.get(uf) or UF_NAMES.get(uf, "")
            if not state or state.upper() == uf or "Ã" in state:
                state = state_name

        street = str(out.get("street") or "").strip()
        number = str(out.get("number") or "").strip()
        neighborhood = str(out.get("neighborhood") or "").strip()
        city = str(out.get("city") or "").strip()
        if not self.is_valid_street(street, {"uf": out.get("uf", ""), "estado": state, "cidade": city}):
            street = ""
            out["street"] = ""
        else:
            out["street"] = street
        out["number"] = number
        out["neighborhood"] = neighborhood
        out["city"] = city
        out["state"] = state
        out.setdefault("logradouro", street)
        out.setdefault("rua", street)
        out.setdefault("numero", number)
        out.setdefault("bairro", neighborhood)
        out.setdefault("cidade", city)
        out.setdefault("estado", state)
        out["logradouro"] = street
        out["rua"] = street
        out["numero"] = number
        out["bairro"] = neighborhood
        out["cidade"] = city
        out["estado"] = state
        if out.get("uf"):
            out["uf"] = str(out.get("uf", "")).strip().upper()
        return out

    @staticmethod
    def address_is_complete(address: Dict) -> bool:
        has_base = all(str(address.get(k, "") or "").strip() for k in ["cep", "street", "number", "city"])
        has_state = bool(str(address.get("uf") or address.get("state") or address.get("estado") or "").strip())
        return has_base and has_state

    def load_address_to_form(self, address: Dict):
        address = self.normalize_address(address or {})
        for widget, key in [
            (self.addr_cep,          "cep"),
            (self.addr_street,       "street"),
            (self.addr_number,       "number"),
            (self.addr_neighborhood, "neighborhood"),
            (self.addr_city,         "city"),
            (self.addr_state,        "state"),
            (self.addr_uf,           "uf"),
        ]:
            widget.setText(str(address.get(key, "") or ""))

    def _uf_hint_from_address(self, address: Dict = None, fallback: str = "") -> str:
        address = self.normalize_address(address or {})
        raw_values = [
            address.get("uf", ""),
            address.get("state", ""),
            address.get("estado", ""),
            fallback,
        ]
        for value in raw_values:
            text = str(value or "").strip()
            if len(text) == 2 and text.upper() in UF_NAMES:
                return text.upper()
            if text:
                text_clean = unicodedata.normalize("NFD", text)
                text_clean = "".join(ch for ch in text_clean if unicodedata.category(ch) != "Mn")
                text_clean = re.sub(r"[^A-Z]", "", text_clean.upper())
                for uf, name in UF_NAMES.items():
                    name_clean = unicodedata.normalize("NFD", name)
                    name_clean = "".join(ch for ch in name_clean if unicodedata.category(ch) != "Mn")
                    name_clean = re.sub(r"[^A-Z]", "", name_clean.upper())
                    if text_clean == name_clean:
                        return uf
        return ""

    def _generate_complete_address(self, uf_hint: str = "", base: Dict = None, silent: bool = False) -> Dict:
        base_address = self.normalize_address(base or {})
        hint = self._uf_hint_from_address(base_address, uf_hint)
        address = None

        def complete_candidate(candidate: Dict) -> Dict:
            candidate = self.normalize_address(candidate or {})
            if candidate and not str(candidate.get("number", "") or "").strip():
                seed = int(datetime.now().timestamp()) % 8900
                candidate["number"] = str(100 + seed)
                candidate["numero"] = candidate["number"]
            return self.normalize_address(candidate)

        if self.address_reserve:
            try:
                candidate = self.address_reserve.get_reserva(hint or None)
                candidate = complete_candidate(candidate or {})
                if self.address_is_complete(candidate):
                    address = candidate
            except Exception as exc:
                if not silent:
                    self.log(f"Reserva de endereco falhou: {exc}")

        if not address and self.address_generator:
            try:
                for _ in range(6):
                    generated = self.address_generator.gerar_endereco(uf=hint if hint in UF_NAMES else None)
                    candidate = generated.to_dict() if generated else None
                    candidate = complete_candidate(candidate or {})
                    if self.address_is_complete(candidate):
                        address = candidate
                        break
            except Exception as exc:
                if not silent:
                    self.log(f"Gerador de endereco falhou: {exc}")

        if not address:
            fallback = self._offline_address_fallback(hint)
            if self.address_is_complete(fallback):
                address = fallback

        return self.normalize_address(address or {})

    def _offline_address_fallback(self, uf_hint: str = "") -> Dict:
        """Endereco simples offline para a automacao nao parar quando API/reserva falhar."""
        uf = uf_hint if uf_hint in UF_NAMES else "SP"
        samples = {
            "AC": ("69900-000", "Rua Rio Branco", "Centro", "Rio Branco"),
            "AL": ("57020-000", "Rua do Sol", "Centro", "Maceio"),
            "AM": ("69010-000", "Avenida Eduardo Ribeiro", "Centro", "Manaus"),
            "AP": ("68900-000", "Rua Sao Jose", "Central", "Macapa"),
            "BA": ("40020-000", "Avenida Sete de Setembro", "Centro", "Salvador"),
            "CE": ("60025-000", "Rua Major Facundo", "Centro", "Fortaleza"),
            "DF": ("70040-010", "SCS Quadra 2", "Asa Sul", "Brasilia"),
            "ES": ("29010-000", "Rua Sete de Setembro", "Centro", "Vitoria"),
            "GO": ("74015-010", "Avenida Goias", "Centro", "Goiania"),
            "MA": ("65010-000", "Rua Grande", "Centro", "Sao Luis"),
            "MG": ("30130-010", "Avenida Afonso Pena", "Centro", "Belo Horizonte"),
            "MS": ("79002-000", "Rua 14 de Julho", "Centro", "Campo Grande"),
            "MT": ("78005-000", "Avenida Getulio Vargas", "Centro", "Cuiaba"),
            "PA": ("66010-000", "Avenida Presidente Vargas", "Campina", "Belem"),
            "PB": ("58010-000", "Rua Duque de Caxias", "Centro", "Joao Pessoa"),
            "PE": ("50010-000", "Rua do Imperador", "Santo Antonio", "Recife"),
            "PI": ("64000-010", "Rua Alvaro Mendes", "Centro", "Teresina"),
            "PR": ("80010-000", "Rua XV de Novembro", "Centro", "Curitiba"),
            "RJ": ("20040-020", "Avenida Rio Branco", "Centro", "Rio de Janeiro"),
            "RN": ("59020-000", "Avenida Rio Branco", "Cidade Alta", "Natal"),
            "RO": ("76801-000", "Avenida Sete de Setembro", "Centro", "Porto Velho"),
            "RR": ("69301-000", "Avenida Jaime Brasil", "Centro", "Boa Vista"),
            "RS": ("90010-000", "Rua dos Andradas", "Centro Historico", "Porto Alegre"),
            "SC": ("88010-000", "Rua Felipe Schmidt", "Centro", "Florianopolis"),
            "SE": ("49010-000", "Rua Joao Pessoa", "Centro", "Aracaju"),
            "SP": ("01001-000", "Praca da Se", "Se", "Sao Paulo"),
            "TO": ("77001-002", "Avenida JK", "Plano Diretor Sul", "Palmas"),
        }
        cep, street, neighborhood, city = samples.get(uf, samples["SP"])
        seed = int(datetime.now().timestamp()) % 8900
        return self.normalize_address({
            "cep": cep,
            "street": street,
            "logradouro": street,
            "number": str(100 + seed),
            "numero": str(100 + seed),
            "neighborhood": neighborhood,
            "bairro": neighborhood,
            "city": city,
            "cidade": city,
            "state": UF_NAMES.get(uf, uf),
            "estado": UF_NAMES.get(uf, uf),
            "uf": uf,
        })

    def profile_name(self, profile_id: str) -> str:
        if not profile_id:
            return ""
        profile = self.browser_manager.get_profile(profile_id)
        return getattr(profile, "name", "") if profile else ""

    def save_current_account(self):
        account = self.account_from_form()
        account["address"] = self.address_from_form()
        email = account.get("email", "").strip()
        if not email:
            return
        accounts = self.data.setdefault("accounts", [])
        existing_ids = {a.get("id") for a in accounts}
        if not account.get("id") or account["id"] not in existing_ids:
            account["id"]         = _make_id("account", email)
            account["created_at"] = _now()
            accounts.append(account)
        else:
            for i, a in enumerate(accounts):
                if a.get("id") == account.get("id"):
                    accounts[i] = account
                    break
        self.current_account_id = account["id"]
        self.save_data()
        self.refresh_accounts_table()
        self.log(f"Conta salva: {email}")

    def remove_selected_accounts(self):
        rows = set(idx.row() for idx in self.accounts_table.selectedIndexes())
        ids_to_remove = set()
        for row in rows:
            item = self.accounts_table.item(row, 0)
            if item:
                ids_to_remove.add(item.data(Qt.UserRole))
        if not ids_to_remove:
            QMessageBox.information(self, "Conta", "Selecione uma ou mais contas.")
            return

        selected_accounts = [a for a in self.data.get("accounts", []) if a.get("id") in ids_to_remove]
        remaining_accounts = [a for a in self.data.get("accounts", []) if a.get("id") not in ids_to_remove]
        remaining_profile_ids = {a.get("profile_id") for a in remaining_accounts if a.get("profile_id")}
        profile_ids = []
        for account in selected_accounts:
            profile_id = account.get("profile_id", "")
            profile = self.browser_manager.get_profile(profile_id) if profile_id else None
            if profile_id and profile_id not in remaining_profile_ids and self.is_paramount_assist_profile(profile):
                profile_ids.append(profile_id)

        note = f"\n\nTambem vou apagar {len(profile_ids)} perfil(is) Paramount criado(s)." if profile_ids else ""
        reply = QMessageBox.question(
            self,
            "Remover contas",
            f"Remover {len(ids_to_remove)} conta(s) da fila?{note}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        deleted_profiles = 0
        for profile_id in profile_ids:
            try:
                if self.browser_manager.delete_profile(profile_id):
                    deleted_profiles += 1
            except Exception as exc:
                self.log(f"Nao consegui apagar perfil {profile_id}: {exc}")
        self.data["accounts"] = remaining_accounts
        self.current_account_id = ""
        self.save_data()
        self.refresh_all()
        if deleted_profiles:
            self.log(f"Removidas {len(ids_to_remove)} conta(s) e {deleted_profiles} perfil(is).")
        else:
            self.log(f"Removidas {len(ids_to_remove)} conta(s).")

    def select_next_account(self):
        row = self.accounts_table.currentRow()
        count = self.accounts_table.rowCount()
        if count == 0:
            return
        next_row = (row + 1) % count
        self.accounts_table.selectRow(next_row)

    def copy_selected_account_login(self):
        account = self.current_account()
        if not account:
            return
        email_password = account.get("email_password") or account.get("password", "")
        text = f"{account.get('email', '')}:{email_password}"
        set_clipboard_text(text)
        self.log("Email/senha do email copiado.")

    def copy_active_account_logins(self):
        lines = []
        for account in self.data.get("accounts", []):
            if account.get("status") != "assinatura ativa":
                continue
            email = (account.get("email") or "").strip()
            password = (account.get("email_password") or account.get("password") or "").strip()
            if email:
                lines.append(f"{email}:{password}" if password else email)
        if not lines:
            QMessageBox.information(self, "Assinaturas", "Ainda nao tem conta marcada como assinatura ativa.")
            return
        set_clipboard_text("\n".join(lines))
        self.log(f"Copiadas {len(lines)} conta(s) com assinatura ativa.")

    def import_accounts_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Colar emails / senhas")
        dlg.setMinimumWidth(480)
        dlg.setStyleSheet(MAIN_QSS)
        lay = QVBoxLayout(dlg)
        lbl = QLabel(
            "Cole email:senha do email, um por linha.\n"
            "Se preencher senha fixa, a Paramount usa a senha fixa e a senha do email fica guardada para copiar."
        )
        lbl.setStyleSheet(f"color:{P['subtle']}; font-size:11px;")
        lbl.setWordWrap(True)
        lay.addWidget(lbl)
        fixed_password = QLineEdit()
        fixed_password.setPlaceholderText("Senha fixa da Paramount; opcional")
        lay.addWidget(fixed_password)
        text_edit = QTextEdit()
        text_edit.setPlaceholderText("email@exemplo.com:senha123\noutroemail@gmail.com senha456")
        text_edit.setMinimumHeight(200)
        lay.addWidget(text_edit)
        btns = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        btns.accepted.connect(dlg.accept)
        btns.rejected.connect(dlg.reject)
        lay.addWidget(btns)
        if dlg.exec_() != QDialog.Accepted:
            return
        lines = text_edit.toPlainText().splitlines()
        added = 0
        fixed = fixed_password.text().strip()
        existing = {a.get("email", "").lower(): a for a in self.data.get("accounts", []) if a.get("email")}
        used_cpfs = {
            self.normalize_person(a.get("person", {}) or {}).get("cpf", "")
            for a in self.data.get("accounts", [])
            if self.normalize_person(a.get("person", {}) or {}).get("cpf", "")
        }
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                parts = line.split(":", 1)
            elif " " in line:
                parts = line.split(" ", 1)
            else:
                parts = [line, ""]
            email = parts[0].strip().lower()
            email_password = parts[1].strip() if len(parts) > 1 else ""
            password = fixed or email_password
            if not email or "@" not in email:
                continue
            if email in existing:
                account = existing[email]
                changed = False
                if email_password and account.get("email_password") != email_password:
                    account["email_password"] = email_password
                    changed = True
                desired_password = fixed or (email_password if not account.get("password") else "")
                if desired_password and account.get("password") != desired_password:
                    account["password"] = desired_password
                    changed = True
                if not self.normalize_person(account.get("person", {}) or {}).get("name"):
                    person = self.project_person_payload(used_cpfs)
                    if person:
                        account["person"] = person
                        changed = True
                if changed:
                    account["updated_at"] = _now()
                    added += 1
                continue
            account = {
                "id":         _make_id("account", email),
                "email":      email,
                "password":   password,
                "email_password": email_password,
                "status":     "novo",
                "profile_id": "",
                "plan":       PLAN_OPTIONS[0],
                "person":     self.project_person_payload(used_cpfs),
                "address":    {},
                "created_at": _now(),
                "updated_at": _now(),
            }
            self.data.setdefault("accounts", []).append(account)
            existing[email] = account
            added += 1
        if added:
            self.save_data()
            self.refresh_accounts_table()
            self.log(f"Importadas {added} conta(s).")
        else:
            QMessageBox.information(self, "Importar", "Nenhuma conta nova encontrada.")

    def import_accounts_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Importar contas de arquivo", "", "Text files (*.txt);;All files (*)"
        )
        if not path:
            return
        try:
            content = Path(path).read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            QMessageBox.warning(self, "Importar", f"Erro ao ler arquivo: {exc}")
            return
        lines = content.splitlines()
        added = 0
        existing_emails = {a.get("email", "").lower() for a in self.data.get("accounts", [])}
        used_cpfs = {
            self.normalize_person(a.get("person", {}) or {}).get("cpf", "")
            for a in self.data.get("accounts", [])
            if self.normalize_person(a.get("person", {}) or {}).get("cpf", "")
        }
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if ":" in line:
                parts = line.split(":", 1)
            elif " " in line:
                parts = line.split(" ", 1)
            else:
                parts = [line, ""]
            email = parts[0].strip().lower()
            email_password = parts[1].strip() if len(parts) > 1 else ""
            password = email_password
            if not email or "@" not in email:
                continue
            if email in existing_emails:
                continue
            account = {
                "id":         _make_id("account", email),
                "email":      email,
                "password":   password,
                "email_password": email_password,
                "status":     "novo",
                "profile_id": "",
                "plan":       PLAN_OPTIONS[0],
                "person":     self.project_person_payload(used_cpfs),
                "address":    {},
                "created_at": _now(),
                "updated_at": _now(),
            }
            self.data.setdefault("accounts", []).append(account)
            existing_emails.add(email)
            added += 1
        if added:
            self.save_data()
            self.refresh_accounts_table()
            self.log(f"Importadas {added} conta(s) de {Path(path).name}.")
        else:
            QMessageBox.information(self, "Importar", "Nenhuma conta nova encontrada no arquivo.")

    # ── Navegacao de browser ──────────────────────────────────────────────────

    def _driver_for_current(self):
        account = self.current_account()
        profile_id = account.get("profile_id") if account else ""
        if not profile_id:
            return None, "Nenhum perfil vinculado. Crie ou vincule um perfil primeiro."
        return self._driver_for_profile(profile_id)

    def _driver_for_profile(self, profile_id: str):
        if not profile_id:
            return None, "Nenhum perfil vinculado. Crie ou vincule um perfil primeiro."
        if self.browser_manager.is_native_browser(profile_id) or getattr(self.browser_manager, "active_debug_ports", {}).get(profile_id):
            driver = self.browser_manager._attach_native_control_driver(profile_id)
        else:
            driver = self.browser_manager.active_browsers.get(profile_id)
        if not driver:
            return None, "Perfil nao tem driver ativo. Abra o perfil primeiro."
        return driver, ""

    def navigate_active_profile(self, profile_id: str, url: str):
        if self.browser_manager.is_native_browser(profile_id) or getattr(self.browser_manager, "active_debug_ports", {}).get(profile_id):
            driver = self.browser_manager._attach_native_control_driver(profile_id)
        else:
            driver = self.browser_manager.active_browsers.get(profile_id)
        if driver:
            try:
                driver.get(url)
            except Exception as exc:
                self.log(f"Erro ao navegar: {exc}")
        else:
            self.log(f"Sem driver ativo para perfil {profile_id}.")

    def _account_payload_for_page(self, account: Dict, persist: bool = True) -> Dict:
        if persist:
            person = self.ensure_person_for_account(account, persist=True)
        else:
            # Chamado em worker/background: nao gera dados nem toca em widgets.
            # A pessoa ja deve ter sido preparada na thread principal antes.
            person = self.normalize_person(account.get("person", {}) or {})
        name = " ".join((person.get("name") or person.get("nome") or "").strip().split())
        if not self.person_name_is_valid(name):
            return {}
        parts = name.split()
        return {
            "email": account.get("email", "").strip(),
            "password": account.get("password", "").strip(),
            "fullName": name,
            "firstName": parts[0] if parts else "",
            "lastName": " ".join(parts[1:]) if len(parts) > 1 else "",
            "cpf": person.get("cpf", ""),
            "cpfDigits": _digits(person.get("cpf", "")),
            "birth": person.get("birth") or person.get("nascimento") or "",
        }

    def _visible_element(self, driver, element) -> bool:
        try:
            return bool(driver.execute_script(
                """
                const el = arguments[0];
                if (!el) return false;
                const st = window.getComputedStyle(el);
                const r = el.getBoundingClientRect();
                return st.display !== "none" && st.visibility !== "hidden" &&
                       r.width > 2 && r.height > 2 && !el.disabled && !el.readOnly;
                """,
                element,
            ))
        except Exception:
            try:
                return element.is_displayed() and element.is_enabled()
            except Exception:
                return False

    def _physical_click(self, driver, element) -> bool:
        try:
            driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", element)
            time.sleep(0.03)
            if ActionChains:
                ActionChains(driver).move_to_element(element).pause(0.03).click().perform()
            else:
                element.click()
            return True
        except Exception:
            try:
                driver.execute_script(
                    """
                    const el = arguments[0];
                    el.focus?.();
                    for (const type of ["pointerdown","mousedown","mouseup","pointerup","click"]) {
                      try { el.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true, view:window})); } catch (_) {}
                    }
                    try { el.click?.(); } catch (_) {}
                    """,
                    element,
                )
                return True
            except Exception:
                return False

    def _physical_type(self, driver, element, value: str) -> bool:
        value = str(value or "")
        if not value or not self._visible_element(driver, element):
            return False
        if not self._physical_click(driver, element):
            return False
        try:
            if Keys:
                element.send_keys(Keys.CONTROL, "a")
                element.send_keys(Keys.BACKSPACE)
            else:
                element.clear()
            element.send_keys(value)
        except Exception:
            try:
                element.clear()
                element.send_keys(value)
            except Exception:
                return False
        try:
            driver.execute_script(
                """
                const el = arguments[0];
                for (const type of ["input", "change", "keyup", "blur"]) {
                  try { el.dispatchEvent(new Event(type, {bubbles:true})); } catch (_) {}
                }
                """,
                element,
            )
        except Exception:
            pass
        try:
            current = element.get_attribute("value") or ""
            return bool(current.strip())
        except Exception:
            return True

    def _fill_input_physical(self, driver, selectors: List[str], keywords: List[str], value: str, used=None) -> Dict:
        if not By:
            return {"ok": False, "field": ""}
        used = used if used is not None else set()
        candidates = []
        for selector in selectors:
            try:
                candidates.extend(driver.find_elements(By.CSS_SELECTOR, selector))
            except Exception:
                continue
        if not candidates:
            try:
                all_inputs = driver.find_elements(By.CSS_SELECTOR, "input, textarea")
            except Exception:
                all_inputs = []
            clean_keywords = [self._clean_ascii(word) for word in keywords if word]
            for element in all_inputs:
                try:
                    attrs = [
                        element.get_attribute("name"),
                        element.get_attribute("id"),
                        element.get_attribute("placeholder"),
                        element.get_attribute("aria-label"),
                        element.get_attribute("autocomplete"),
                        element.get_attribute("data-ci"),
                        element.get_attribute("data-testid"),
                        element.get_attribute("aria-describedby"),
                    ]
                    text = self._clean_ascii(" ".join(str(a or "") for a in attrs))
                    if any(word in text for word in clean_keywords):
                        candidates.append(element)
                except Exception:
                    continue
        for element in candidates:
            marker = None
            try:
                marker = element.id
            except Exception:
                marker = id(element)
            if marker in used:
                continue
            if self._physical_type(driver, element, value):
                used.add(marker)
                try:
                    field = element.get_attribute("name") or element.get_attribute("id") or element.get_attribute("placeholder") or ""
                except Exception:
                    field = ""
                return {"ok": True, "field": field}
        return {"ok": False, "field": ""}

    @staticmethod
    def _clean_ascii(value: str) -> str:
        text = unicodedata.normalize("NFD", str(value or ""))
        text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
        return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())

    def _fill_signup_fields_physical(self, driver, payload: Dict) -> Dict:
        used = set()
        results = {
            "fullName": self._fill_input_physical(
                driver,
                [
                    "#fullName",
                    "input[name='fullName']",
                    "input[data-ci='fullName']",
                    "input[aria-describedby='fullName_error-msg']",
                ],
                ["fullName", "full name", "nome completo", "nome e sobrenome"],
                payload.get("fullName", ""),
                used,
            ),
            "email": self._fill_input_physical(
                driver,
                [
                    "#email",
                    "input[name='email']",
                    "input[data-ci='email']",
                    "input[aria-describedby='email_error-msg']",
                    "input[type='email']",
                ],
                ["email", "e mail", "login"],
                payload.get("email", ""),
                used,
            ),
            "password": self._fill_input_physical(
                driver,
                [
                    "#password",
                    "input[name='password']",
                    "input[data-ci='password']",
                    "input[aria-describedby='password_error-msg']",
                    ".qt-pwdtxtfield",
                    "input[type='password']",
                ],
                ["password", "senha"],
                payload.get("password", ""),
                used,
            ),
        }
        return {
            "ok": True,
            "filled": sum(1 for item in results.values() if item.get("ok")),
            "results": results,
            "mode": "physical",
        }

    def _fill_signup_fields(self, account: Dict) -> Dict:
        driver, error = self._driver_for_current()
        if not driver:
            return {"ok": False, "message": error, "filled": 0}
        return self._fill_signup_fields_on_driver(driver, account, persist=True)

    def _fill_signup_fields_on_driver(self, driver, account: Dict, persist: bool = False) -> Dict:
        payload = self._account_payload_for_page(account, persist=persist)
        if not payload:
            return {"ok": False, "message": "Nao consegui gerar nome completo valido para esta conta.", "filled": 0}
        if not payload.get("email") or not payload.get("password"):
            return {"ok": False, "message": "Informe email e senha antes de preencher.", "filled": 0}
        physical = self._fill_signup_fields_physical(driver, payload)
        if physical.get("filled", 0) >= 3:
            return physical
        script = r"""
const data = arguments[0] || {};
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}
function visible(el) {
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 2 && r.height > 2 && !el.disabled && !el.readOnly;
}
function textFor(el) {
  const bits = [
    el.name, el.id, el.type, el.placeholder, el.autocomplete,
    el.getAttribute("aria-label"), el.getAttribute("data-testid"),
    el.getAttribute("data-test"), el.getAttribute("data-ci")
  ];
  if (el.labels) Array.from(el.labels).forEach(label => bits.push(label.innerText || label.textContent || ""));
  for (const attr of ["aria-labelledby", "aria-describedby"]) {
    const ids = (el.getAttribute(attr) || "").split(/\s+/).filter(Boolean);
    for (const id of ids) {
      const ref = document.getElementById(id);
      if (ref) bits.push(ref.innerText || ref.textContent || "");
    }
  }
  const previous = el.previousElementSibling;
  if (previous) bits.push(previous.innerText || previous.textContent || "");
  const labelParent = el.closest("label");
  if (labelParent) bits.push(labelParent.innerText || labelParent.textContent || "");
  return clean(bits.filter(Boolean).join(" "));
}
function setValue(el, value) {
  if (!el || !value || !visible(el)) return false;
  el.scrollIntoView({block:"center", inline:"center"});
  el.focus();
  const proto = el instanceof HTMLTextAreaElement ? HTMLTextAreaElement.prototype : HTMLInputElement.prototype;
  const setter = Object.getOwnPropertyDescriptor(proto, "value")?.set || Object.getOwnPropertyDescriptor(el.__proto__, "value")?.set;
  if (setter) setter.call(el, value);
  else el.value = value;
  el.dispatchEvent(new InputEvent("input", { bubbles: true, inputType: "insertText", data: value }));
  el.dispatchEvent(new Event("change", { bubbles: true }));
  el.dispatchEvent(new KeyboardEvent("keyup", { bubbles: true, key: "Tab" }));
  el.dispatchEvent(new Event("blur", { bubbles: true }));
  return true;
}
const bad = /card|cartao|cartão|cvv|cvc|security|month|year|expir|cc-|credit|debito|credito|validade|numero do cartao|número do cartão/;
const fields = Array.from(document.querySelectorAll("input, textarea"))
  .filter(visible)
  .filter(el => !/checkbox|radio|submit|button|hidden/i.test(el.type || ""))
  .map(el => ({el, text: textFor(el)}))
  .filter(item => !bad.test(item.text));
const used = new Set();
function bySelector(selectors) {
  for (const sel of selectors) {
    const el = document.querySelector(sel);
    if (el && visible(el) && !used.has(el)) return el;
  }
  return null;
}
function fillExact(kind, selectors, value) {
  const el = bySelector(selectors);
  if (!el) return {ok:false, field:""};
  if (!setValue(el, value)) return {ok:false, field:""};
  used.add(el);
  return {ok:true, field:(el.name || el.id || el.getAttribute("data-ci") || kind).toString(), exact:true};
}
function choose(kind) {
  let best = null;
  for (const item of fields) {
    const el = item.el;
    const txt = item.text;
    if (used.has(el)) continue;
    let score = 0;
    if (kind === "email") {
      if ((el.type || "").toLowerCase() === "email") score += 80;
      if (/e-?mail|email|mail/.test(txt)) score += 45;
      if (/username|login/.test(txt)) score += 10;
      if (/senha|password|pass|nome completo|full.?name|cpf|documento/.test(txt)) score -= 100;
    } else if (kind === "password") {
      if ((el.type || "").toLowerCase() === "password") score += 90;
      if (/senha|password|pass/.test(txt)) score += 45;
      if (/email|e-?mail|nome|full.?name|cpf|documento/.test(txt)) score -= 100;
    } else if (kind === "fullName") {
      if ((el.type || "").toLowerCase() === "email" || (el.type || "").toLowerCase() === "password") score -= 120;
      if (/nome completo|nome e sobrenome|full.?name|complete.?name|display.?name/.test(txt)) score += 90;
      if (/\bnome\b|name/.test(txt)) score += 25;
      if (/sobrenome|last.?name/.test(txt)) score -= 20;
      if (/email|e-?mail|mail|senha|password|pass|cpf|documento/.test(txt)) score -= 120;
    } else if (kind === "cpf") {
      if (/cpf|documento|tax|taxid|tax_identifier/.test(txt)) score += 70;
      if (/email|senha|password|nome|card|cartao|cartão/.test(txt)) score -= 100;
    }
    if (score > 0 && (!best || score > best.score)) best = {el, score, text: txt};
  }
  return best;
}
function fill(kind, value) {
  if (kind === "fullName") {
    const exact = fillExact(kind, [
      "#fullName", "input[name='fullName']", "input[data-ci='fullName']",
      "input[aria-describedby='fullName_error-msg']"
    ], value);
    if (exact.ok) return exact;
  }
  if (kind === "email") {
    const exact = fillExact(kind, [
      "#email", "input[name='email']", "input[data-ci='email']",
      "input[aria-describedby='email_error-msg']"
    ], value);
    if (exact.ok) return exact;
  }
  if (kind === "password") {
    const exact = fillExact(kind, [
      "#password", "input[name='password']", "input[data-ci='password']",
      "input[aria-describedby='password_error-msg']", ".qt-pwdtxtfield"
    ], value);
    if (exact.ok) return exact;
  }
  const picked = choose(kind);
  if (!picked) return {ok:false, field:""};
  if (!setValue(picked.el, value)) return {ok:false, field:""};
  used.add(picked.el);
  return {ok:true, field:(picked.el.name || picked.el.id || picked.el.placeholder || kind).toString()};
}
const results = {
  fullName: fill("fullName", data.fullName),
  email: fill("email", data.email),
  password: fill("password", data.password),
};
return {
  ok: true,
  filled: Object.values(results).filter(r => r && r.ok).length,
  results,
  url: location.href,
  title: document.title,
};
"""
        try:
            result = driver.execute_script(script, payload) or {}
            result["ok"] = True
            return result
        except Exception as exc:
            return {"ok": False, "message": f"Nao consegui preencher: {exc}", "filled": 0}

    def _page_state(self, driver) -> Dict:
        script = r"""
const text = (document.body && (document.body.innerText || document.body.textContent) || "").slice(0, 6000);
const inputCount = Array.from(document.querySelectorAll("input, textarea, select")).filter(el => {
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0 && !el.disabled;
}).length;
function exists(selectors) {
  return selectors.some(sel => {
    const el = document.querySelector(sel);
    if (!el) return false;
    const st = window.getComputedStyle(el);
    const r = el.getBoundingClientRect();
    return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0 && !el.disabled;
  });
}
const hasSignupFields =
  exists(["#fullName", "input[name='fullName']", "input[data-ci='fullName']"]) &&
  exists(["#email", "input[name='email']", "input[data-ci='email']", "input[type='email']"]) &&
  exists(["#password", "input[name='password']", "input[data-ci='password']", "input[type='password']"]);
const hasPaymentFields =
  exists(["input[autocomplete='postal-code']", "input[name='postalCode']", "input[id='postalCode']", "#postal_code", "input[name='postal_code']", "input[data-ci='postal_code']"]) ||
  exists(["input[name='cpf']", "input[id='cpf']", "input[placeholder='CPF']", "#tax_identifier", "input[name='tax_identifier']", "input[data-recurly='tax_identifier']", "input[data-ci='tax_identifier']"]) ||
  exists(["#first_name", "input[name='first_name']", "input[data-ci='first_name']"]) ||
  exists(["#state", "select[data-recurly='state']", "#custom-selector-state"]);
return {
  url: location.href,
  title: document.title,
  text,
  input_count: inputCount,
  has_signup_fields: hasSignupFields,
  has_payment_fields: hasPaymentFields,
};
"""
        try:
            return driver.execute_script(script) or {}
        except Exception as exc:
            self.log(f"Fluxo: nao consegui ler a pagina: {exc}")
            return {}

    def _subscription_status_from_state(self, state: Dict) -> Dict:
        """Detecta assinatura ativa/inativa lendo apenas a pagina aberta."""
        url = (state.get("url") or "").lower()
        raw_text = state.get("text") or ""

        def clean(value: str) -> str:
            text = unicodedata.normalize("NFD", str(value or ""))
            text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
            return " ".join("".join(ch.lower() if ch.isalnum() else " " for ch in text).split())

        text = clean(raw_text)
        if not text:
            return {"status": "", "label": "desconhecido", "reason": "pagina sem texto suficiente"}

        if "/user-profile/whos-watching" in url:
            return {
                "status": "assinatura ativa",
                "label": "ativa",
                "reason": "tela de perfis da Paramount",
            }

        if any(term in text for term in ["cloudflare", "confirme que e humano", "verificacao de seguranca"]):
            return {"status": "precisa verificar", "label": "verificacao", "reason": "pagina em verificacao"}

        checkout_terms = [
            "account signup",
            "adicione um metodo de pagamento",
            "concordar e assinar",
            "sua fatura",
            "numero do cartao de credito",
            "escolha o plano",
            "crie uma conta",
        ]
        if "/signup/" in url or any(term in text for term in checkout_terms):
            return {"status": "", "label": "cadastro", "reason": "tela de cadastro/pagamento, nao conta ativa"}

        active_terms = [
            "assinatura ativa",
            "sua assinatura",
            "gerenciar assinatura",
            "cancelar assinatura",
            "proximo pagamento",
            "proxima cobranca",
            "data de renovacao",
            "renovacao",
            "plano atual",
            "metodo de pagamento salvo",
            "quem esta assistindo",
            "selecione ou crie um perfil",
            "adicionar perfil",
        ]
        inactive_terms = [
            "sem assinatura",
            "nenhuma assinatura",
            "assinatura cancelada",
            "reativar assinatura",
            "assine agora",
            "assinar agora",
            "escolha um plano",
            "comece agora",
        ]

        active_hit = next((term for term in active_terms if term in text), "")
        if active_hit:
            return {"status": "assinatura ativa", "label": "ativa", "reason": active_hit}

        inactive_hit = next((term for term in inactive_terms if term in text), "")
        if inactive_hit:
            return {"status": "sem assinatura", "label": "sem assinatura", "reason": inactive_hit}

        return {"status": "", "label": "desconhecido", "reason": "nao encontrei sinal claro de assinatura"}

    def _apply_subscription_status(self, account: Dict, state: Dict, silent: bool = True) -> Dict:
        result = self._subscription_status_from_state(state)
        detected_status = result.get("status", "")
        if detected_status not in {"assinatura ativa", "sem assinatura", "precisa verificar"}:
            return result

        previous = account.get("status", "novo")
        if detected_status == "precisa verificar":
            if previous not in {"assinatura ativa", "sem assinatura"}:
                account["status"] = "precisa verificar"
        else:
            account["status"] = detected_status
            account["subscription_status"] = result.get("label", "")
            account["subscription_checked_at"] = _now()
            account["subscription_reason"] = result.get("reason", "")
        account["updated_at"] = _now()
        self.status_combo.setCurrentText(account.get("status", previous))
        self.save_data()
        self.refresh_accounts_table()

        if not silent:
            label = result.get("label", "desconhecido")
            reason = result.get("reason", "")
            self._show_toast("Assinatura", f"Status: {label}. {reason}", "success" if detected_status == "assinatura ativa" else "warning")
        return result

    def auto_detect_open_subscriptions(self):
        """Varre perfis Paramount abertos e marca assinatura ativa sem precisar clicar no botao."""
        key = "auto_subscription_scan"
        if key in self._action_workers:
            return
        if getattr(self, "_side_by_side_opening", False):
            return
        if any(str(k).startswith(("smart_continue:", "position_window:", "prepare_profile:")) for k in self._action_workers):
            return
        accounts = [
            {"id": a.get("id", ""), "profile_id": a.get("profile_id", "")}
            for a in self.data.get("accounts", [])
            if a.get("profile_id")
        ]
        if not accounts:
            return

        def work():
            results = []
            for item in accounts[:5]:
                profile_id = item.get("profile_id", "")
                if not self.browser_manager.is_browser_active(profile_id):
                    continue
                driver, error = self._driver_for_profile(profile_id)
                if not driver:
                    continue
                state = self._page_state(driver)
                detected = self._subscription_status_from_state(state)
                if detected.get("status") in {"assinatura ativa", "sem assinatura", "precisa verificar"}:
                    results.append({"account_id": item.get("id", ""), "state": state})
            return results

        worker = _ParamountActionWorker(key, work, self)
        self._action_workers[key] = worker
        self._action_started_at[key] = time.time()
        if get_app_store:
            try:
                get_app_store().upsert_task(
                    f"paramount-action:{key}",
                    "paramount-action",
                    "Varredura de assinaturas",
                    source="paramount_assist",
                    status="running",
                    priority=60,
                    payload={"key": key},
                )
            except Exception:
                pass

        def cleanup(action_key: str):
            finished = self._action_workers.pop(action_key, None)
            self._action_started_at.pop(action_key, None)
            if finished:
                finished.deleteLater()

        def handle_result(action_key: str, results):
            cleanup(action_key)
            if get_app_store:
                try:
                    get_app_store().update_task(f"paramount-action:{action_key}", status="success", last_error="")
                except Exception:
                    pass
            changed = 0
            for item in results or []:
                account = self._account_by_id(item.get("account_id", ""))
                if not account:
                    continue
                previous = account.get("status")
                self._apply_subscription_status(account, item.get("state", {}) or {}, silent=True)
                if account.get("status") != previous:
                    changed += 1
            if changed:
                self.log(f"Assinatura detectada automaticamente em {changed} conta(s).")

        def handle_error(action_key: str, _error: str):
            cleanup(action_key)
            if get_app_store:
                try:
                    get_app_store().update_task(f"paramount-action:{action_key}", status="error", last_error=_error)
                except Exception:
                    pass

        worker.result.connect(handle_result)
        worker.error.connect(handle_error)
        worker.start()

    def _accept_visible_terms(self, driver) -> Dict:
        script = r"""
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}
function visible(el) {
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0 && !el.disabled;
}
function textFor(el) {
  const bits = [
    el.name, el.id, el.getAttribute("aria-label"),
    el.getAttribute("data-testid"), el.getAttribute("data-ci")
  ];
  if (el.labels) Array.from(el.labels).forEach(label => bits.push(label.innerText || label.textContent || ""));
  const parent = el.closest("label, div");
  if (parent) bits.push((parent.innerText || parent.textContent || "").slice(0, 300));
  return clean(bits.filter(Boolean).join(" "));
}
let checked = 0;
for (const el of Array.from(document.querySelectorAll("input[type='checkbox']")).filter(visible)) {
  const txt = textFor(el);
  const required = el.required || /termos|terms|privacidade|privacy|concordo|concordar|uso/.test(txt);
  if (required && !el.checked) {
    el.scrollIntoView({block:"center", inline:"center"});
    el.click();
    checked++;
  }
}
for (const el of Array.from(document.querySelectorAll(".cbs-checkbox__checkbox, [role='checkbox'], [aria-label*='Concordar' i], [aria-label*='Termos' i], [aria-label*='Privacidade' i]")).filter(visible)) {
  const txt = textFor(el);
  const state = (el.getAttribute("aria-checked") || "").toLowerCase();
  const required = /termos|terms|privacidade|privacy|concordo|concordar|uso/.test(txt);
  if (required && state !== "true") {
    el.scrollIntoView({block:"center", inline:"center"});
    el.focus?.();
    for (const type of ["pointerdown", "mousedown", "mouseup", "pointerup", "click"]) {
      try { el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window })); } catch (_) {}
    }
    try { el.click?.(); } catch (_) {}
    checked++;
  }
}
return {checked};
"""
        try:
            return driver.execute_script(script) or {}
        except Exception as exc:
            self.log(f"Fluxo: nao consegui marcar aceite: {exc}")
            return {"checked": 0}

    def _dismiss_browser_overlays(self, driver):
        """Fecha popups nativos leves do Chrome, como 'Salvar senha?', antes de clicar."""
        if not driver:
            return
        try:
            if ActionChains and Keys:
                ActionChains(driver).send_keys(Keys.ESCAPE).pause(0.08).send_keys(Keys.ESCAPE).perform()
                time.sleep(0.12)
        except Exception:
            pass
        try:
            driver.execute_script("window.focus(); document.body && document.body.focus && document.body.focus();")
        except Exception:
            pass

    def _click_safe_continue(self, driver) -> Dict:
        self._dismiss_browser_overlays(driver)

        def clean_text(value: str) -> str:
            text = unicodedata.normalize("NFD", str(value or ""))
            text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
            return " ".join(text.lower().split())

        good_words = ("continuar", "continue", "proximo", "avancar", "seguir", "criar conta")
        blocked_words = (
            "pagar", "pagamento", "finalizar", "concluir compra", "confirmar pagamento",
            "concordar e assinar", "assinar agora", "comprar", "pay", "subscribe",
        )
        if By:
            selectors = [
                "button[aria-label='Continuar'].buttonWindows",
                "button[aria-label='Continuar']",
                "button.buttonWindows",
                "button.primary",
            ]
            for selector in selectors:
                try:
                    elements = driver.find_elements(By.CSS_SELECTOR, selector)
                except Exception:
                    elements = []
                for element in elements:
                    try:
                        label = clean_text(
                            element.get_attribute("aria-label")
                            or element.text
                            or element.get_attribute("innerText")
                            or element.get_attribute("textContent")
                        )
                        if not label:
                            continue
                        if any(word in label for word in blocked_words):
                            continue
                        if not any(word in label for word in good_words):
                            continue
                        driver.execute_script("arguments[0].scrollIntoView({block:'center', inline:'center'});", element)
                        if not self._physical_click(driver, element):
                            driver.execute_script(
                                """
                                const el = arguments[0];
                                el.focus?.();
                                for (const type of ["pointerdown","mousedown","mouseup","pointerup","click"]) {
                                  try { el.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true, view:window})); } catch (_) {}
                                }
                                try { el.click?.(); } catch (_) {}
                                """,
                                element,
                            )
                        return {"clicked": True, "button": label, "url": getattr(driver, "current_url", "")}
                    except Exception as exc:
                        self.log(f"Fluxo: clique nativo falhou em {selector}: {exc}")

        script = r"""
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}
function visible(el) {
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0 && !el.disabled;
}
const good = [
  "concordar & continuar", "concordar e continuar", "concordar continuar",
  "continuar", "continue", "proximo", "próximo", "avancar", "avançar", "seguir", "criar conta"
];
const blocked = [
  "pagar", "pagamento", "finalizar", "concluir compra", "confirmar pagamento",
  "concordar e assinar", "assinar agora", "comprar", "pay", "subscribe"
];
const candidates = Array.from(document.querySelectorAll("button, a, [role='button'], input[type='button'], input[type='submit'], .buttonWindows, .button__text"))
  .filter(visible)
  .map(el => {
    const button = el.closest("button, a, [role='button'], input[type='button'], input[type='submit']") || el;
    return {
      el: button,
      txt: clean(button.innerText || button.value || button.getAttribute("aria-label") || el.innerText || el.textContent || "")
    };
  })
  .filter(item => item.txt && good.some(word => item.txt.includes(clean(word))))
  .filter(item => !blocked.some(word => item.txt.includes(clean(word))));
const unique = [];
const seen = new Set();
for (const item of candidates) {
  if (seen.has(item.el)) continue;
  seen.add(item.el);
  unique.push(item);
}
if (!unique.length) {
  return {clicked:false, reason:"nenhum botao seguro de continuar encontrado", url:location.href};
}
const target = unique[0];
target.el.scrollIntoView({block:"center", inline:"center"});
target.el.focus?.();
for (const type of ["pointerdown", "mousedown", "mouseup", "pointerup", "click"]) {
  try { target.el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window })); } catch (_) {}
}
try { target.el.click?.(); } catch (_) {}
return {clicked:true, button:target.txt, url:location.href};
"""
        try:
            return driver.execute_script(script) or {}
        except Exception as exc:
            return {"clicked": False, "reason": str(exc)}

    def _show_flow_result(self, step: str, fill_result: Dict, click_result: Dict):
        filled = int((fill_result or {}).get("filled") or 0)
        clicked = bool((click_result or {}).get("clicked"))
        if not (fill_result or {}).get("ok", True):
            self._show_toast("Fluxo Paramount", (fill_result or {}).get("message", "Nao consegui preencher."), "warning", 5200)
            return
        msg = f"{step}: preenchi {filled} campo(s)."
        if clicked:
            msg += f" Cliquei em: {click_result.get('button', 'continuar')}."
        else:
            msg += f" Nao cliquei: {click_result.get('reason', 'botao nao encontrado')}."
        self.log(msg)
        self._show_toast("Fluxo Paramount", msg, "success" if clicked or filled else "warning")

    def open_profile_only_for_current(self):
        account = self.current_account()
        if not account:
            QMessageBox.warning(self, "Perfil", "Selecione uma conta primeiro.")
            return
        profile_id = account.get("profile_id")
        if not profile_id:
            reply = QMessageBox.question(
                self, "Perfil",
                "Essa conta nao tem perfil vinculado. Criar um novo perfil Paramount agora?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply == QMessageBox.Yes:
                self.create_profile_for_current()
            return
        self._launch_profile(profile_id, navigate_to=None)

    def create_paramount_profile_for_account(self, account: Dict) -> Optional[str]:
        if not account:
            return ""
        profile_id = account.get("profile_id", "")
        if profile_id and self.browser_manager.get_profile(profile_id):
            return profile_id
        email = account.get("email", "")
        prefix = email.split("@")[0][:18] if "@" in email else "paramount"
        number = len(self.paramount_profiles(include_all=False, only_linked=False)) + 1
        name = f"Paramount {number} - {prefix}"
        try:
            profile = self.browser_manager.create_profile(name=name, country="BR", persist_data=True)
            profile.tags = sorted(set((getattr(profile, "tags", []) or []) + ["paramount", "assist"]))
            profile.browser_mode = "auto"
            profile.fingerprint_level = "Streaming"
            profile.compatibility_mode = True
            profile.save_logins = True
            if account.get("address"):
                profile.address_data = dict(account.get("address") or {})
            self.browser_manager._save_profiles()
            account["profile_id"] = profile.id
            account["updated_at"] = _now()
            if account.get("status") == "novo":
                account["status"] = "perfil pronto"
            self.save_data()
            self.log(f"Perfil criado: {name} ({profile.id})")
            return profile.id
        except Exception as exc:
            QMessageBox.warning(self, "Perfil", f"Erro ao criar perfil: {exc}")
            return ""

    def create_profile_for_current(self):
        account = self.current_account()
        if not account:
            return
        profile_id = self.create_paramount_profile_for_account(account)
        if profile_id:
            self.refresh_all()
            self._launch_profile(profile_id, navigate_to=PARAMOUNT_URLS["login"])

    def ensure_profile_for_account(self, account: Dict) -> Optional[str]:
        if not account:
            return ""
        profile_id = account.get("profile_id", "")
        if profile_id and self.browser_manager.get_profile(profile_id):
            return profile_id
        profile_id = self.create_paramount_profile_for_account(account)
        if profile_id:
            self.save_data()
            self.refresh_all()
        return profile_id

    def _driver_for_profile(self, profile_id: str):
        if not profile_id:
            return None, "Nenhum perfil vinculado. Crie ou vincule um perfil primeiro."
        try:
            if self.browser_manager.is_native_browser(profile_id) or getattr(self.browser_manager, "active_debug_ports", {}).get(profile_id):
                driver = self.browser_manager._attach_native_control_driver(profile_id)
            else:
                driver = self.browser_manager.active_browsers.get(profile_id)
        except Exception as exc:
            message = f"Controle do perfil falhou: {exc}"
            self.log(message)
            return None, message
        if not driver:
            return None, "Perfil nao tem driver ativo. Abra o perfil primeiro."
        return driver, ""

    def _position_profile_window(self, profile_id: str, rect: Dict, quiet: bool = False) -> bool:
        driver, error = self._driver_for_profile(profile_id)
        if not driver:
            if error and not quiet:
                self.log(error)
            return False
        try:
            driver.set_window_rect(
                int(rect.get("x", 0)),
                int(rect.get("y", 0)),
                int(rect.get("width", 900)),
                int(rect.get("height", 700)),
            )
            return True
        except Exception:
            try:
                driver.set_window_position(int(rect.get("x", 0)), int(rect.get("y", 0)))
                driver.set_window_size(int(rect.get("width", 900)), int(rect.get("height", 700)))
                return True
            except Exception as exc:
                if not quiet:
                    self.log(f"Nao consegui posicionar janela: {exc}")
        return False

    def _parallel_window_rects(self, count: int) -> List[Dict]:
        screen = QApplication.primaryScreen()
        geo = screen.availableGeometry() if screen else self.window().geometry()
        count = max(1, min(3, count))
        margin = 8
        available_width = max(560, geo.width() - (margin * (count + 1)))
        width = max(520, available_width // count)
        height = max(620, geo.height() - (margin * 2))
        return [
            {
                "x": geo.x() + margin + ((width + margin) * i),
                "y": geo.y() + margin,
                "width": width if i < count - 1 else max(520, available_width - (width * i)),
                "height": height,
            }
            for i in range(count)
        ]

    def _schedule_profile_reposition(self, profile_id: str, rect: Dict, attempts: int = 5, delay_ms: int = 1400):
        if not profile_id or not rect or attempts <= 0:
            return
        rect_snapshot = dict(rect)

        def attempt():
            if not self._is_profile_probably_active_fast(profile_id):
                if attempts > 1:
                    self._schedule_profile_reposition(profile_id, rect_snapshot, attempts - 1, delay_ms)
                return

            def work():
                return {"positioned": self._position_profile_window(profile_id, rect_snapshot, quiet=True)}

            def done(payload):
                if not payload.get("positioned") and attempts > 1:
                    self._schedule_profile_reposition(profile_id, rect_snapshot, attempts - 1, delay_ms)

            def failed(_error):
                if attempts > 1:
                    self._schedule_profile_reposition(profile_id, rect_snapshot, attempts - 1, delay_ms)

            self._run_background_action(
                f"position_window:{profile_id}:{attempts}:{int(time.time() * 1000)}",
                "Janela",
                "Ajustando posicao do navegador...",
                work,
                done,
                on_error=failed,
                quiet=True,
            )

        QTimer.singleShot(delay_ms, attempt)

    def _on_launch_finished(self, profile_id: str, ok: bool, msg: str, rect: Optional[Dict] = None):
        self.log(msg if ok else msg)
        if ok and rect:
            self._schedule_profile_reposition(profile_id, rect, attempts=5, delay_ms=900)
        # A janela recebe tamanho/posição na criação pelo BrowserManager.
        # Evita reconectar no Chrome aqui, porque isso pode congelar a UI ao abrir 3 perfis.

    def _launch_profile(self, profile_id: str, navigate_to: Optional[str] = None, window_rect: Optional[Dict] = None):
        if profile_id in self.launch_threads:
            old = self.launch_threads.pop(profile_id)
            try:
                old.stop()
            except Exception:
                pass
        if self._is_profile_probably_active_fast(profile_id):
            if window_rect or navigate_to:
                rect_snapshot = dict(window_rect or {})
                navigate_snapshot = navigate_to

                def work():
                    if rect_snapshot:
                        self._position_profile_window(profile_id, rect_snapshot)
                    if navigate_snapshot:
                        self.navigate_active_profile(profile_id, navigate_snapshot)
                    return {"ok": True}

                self._run_background_action(
                    f"prepare_profile:{profile_id}",
                    "Perfil",
                    "Ajustando navegador ja aberto sem travar a interface...",
                    work,
                    lambda _payload: None,
                    on_error=lambda error: self.log(f"Perfil: {error}"),
                )
            self.log(f"Perfil ja aberto: {self.profile_name(profile_id) or profile_id}")
            return
        if self.browser_manager.is_profile_launching(profile_id):
            self.log("Este perfil ja esta abrindo.")
            return
        if not self.browser_manager.begin_profile_launch(profile_id):
            self.log("Este perfil ja esta aberto ou reservado para abrir.")
            return
        if window_rect:
            profile = self.browser_manager.get_profile(profile_id)
            if profile:
                profile.launch_rect = dict(window_rect)
        thread = BrowserLaunchThread(self.browser_manager, profile_id, navigate_to, monitor=True)
        thread.finished.connect(lambda ok, msg, pid=profile_id, rect=window_rect: self._on_launch_finished(pid, ok, msg, rect))
        thread.browser_closed.connect(lambda pid: self.browser_manager.end_profile_launch(pid))
        thread.thread_done.connect(lambda pid: (self.browser_manager.end_profile_launch(pid), self.launch_threads.pop(pid, None), self.refresh_profile_combo()))
        self.launch_threads[profile_id] = thread
        thread.start()
        self.log(f"Abrindo perfil {profile_id}...")

    def open_side_by_side_for_accounts(self):
        if getattr(self, "_side_by_side_opening", False):
            self._show_toast(
                "Perfis",
                "Ja existe uma abertura lado a lado em andamento. Aguarde os navegadores terminarem de abrir.",
                "warning",
                4200,
            )
            return
        accounts = self.accounts_for_parallel_open(3)
        if not accounts:
            self._show_toast("Perfis", "Cole ou selecione contas primeiro.", "warning", 4200)
            return
        rects = self._parallel_window_rects(len(accounts))
        jobs = []
        for account, rect in zip(accounts, rects):
            profile_id = self.ensure_profile_for_account(account)
            if not profile_id:
                continue
            account_id = account.get("id", "")
            self._auto_flow_attempts[account_id] = 0
            jobs.append((account_id, profile_id, rect))
        if not jobs:
            self._show_toast("Perfis", "Nao consegui preparar perfis para abrir.", "warning", 4200)
            return
        self._side_by_side_jobs = jobs
        self._side_by_side_total = len(jobs)
        self._side_by_side_opening = True
        self._side_by_side_started_at = time.time()
        if get_app_store:
            try:
                get_app_store().upsert_task(
                    "paramount-action:side_by_side",
                    "paramount-action",
                    "Abrir perfis lado a lado",
                    source="paramount_assist",
                    status="running",
                    priority=8,
                    payload={"total": len(jobs)},
                )
            except Exception:
                pass
        self.log(f"Preparando abertura lado a lado com fluxo automatico: {len(jobs)} perfil(is).")
        QTimer.singleShot(120, self._open_next_side_by_side_job)
        self.save_data()
        self.refresh_all()

    def _open_next_side_by_side_job(self):
        jobs = getattr(self, "_side_by_side_jobs", [])
        if not jobs:
            total = getattr(self, "_side_by_side_total", 0)
            self._side_by_side_opening = False
            self._side_by_side_started_at = 0.0
            if get_app_store:
                try:
                    get_app_store().update_task("paramount-action:side_by_side", status="success", last_error="")
                except Exception:
                    pass
            self.log(f"Abertura lado a lado solicitada para {total} perfil(is).")
            return
        account_id, profile_id, rect = jobs.pop(0)
        self._side_by_side_jobs = jobs
        total = getattr(self, "_side_by_side_total", len(jobs) + 1)
        current = total - len(jobs)
        self.log(f"Abrindo perfil {current}/{total} lado a lado e preparando fluxo...")
        self._launch_profile(profile_id, navigate_to=PARAMOUNT_URLS["cadastro"], window_rect=rect)
        self._schedule_profile_reposition(profile_id, rect, attempts=6, delay_ms=2200)
        self._schedule_auto_flow_next(account_id, profile_id, 7600 + (current * 900))
        QTimer.singleShot(2600, self._open_next_side_by_side_job)

    def _account_by_id(self, account_id: str) -> Optional[Dict]:
        for account in self.data.get("accounts", []):
            if account.get("id") == account_id:
                return account
        return None

    def _set_flow_task(
        self,
        account_id: str,
        account: Optional[Dict] = None,
        *,
        status: str = "running",
        last_error: str = "",
        attempts: int | None = None,
    ):
        """Registra o fluxo da conta no Centro de Tarefas."""
        if not get_app_store or not account_id:
            return
        try:
            account = account or self._account_by_id(account_id) or {}
            email = account.get("email", "") or account_id
            payload = {
                "email": email,
                "profile_id": account.get("profile_id", ""),
                "attempts": attempts if attempts is not None else self._auto_flow_attempts.get(account_id, 0),
            }
            get_app_store().upsert_task(
                f"paramount-flow:{account_id}",
                "paramount-flow",
                f"Fluxo Paramount - {email}",
                source="paramount_assist",
                status=status,
                priority=7,
                entity_type="paramount_account",
                entity_id=account_id,
                payload=payload,
                last_error=last_error,
            )
        except Exception:
            pass

    def _schedule_auto_flow_next(self, account_id: str, profile_id: str, delay_ms: int = 2800):
        if not account_id or not profile_id:
            return
        attempts = self._auto_flow_attempts.get(account_id, 0) + 1
        self._auto_flow_attempts[account_id] = attempts
        self._set_flow_task(account_id, self._account_by_id(account_id), status="running", attempts=attempts)
        if attempts > 10:
            self._set_flow_task(
                account_id,
                self._account_by_id(account_id),
                status="review",
                last_error="Fluxo automatico parou por excesso de etapas. Confira a tela aberta.",
                attempts=attempts,
            )
            self._show_toast(
                "Fluxo Paramount",
                "Parei o fluxo automatico depois de muitas etapas. Confira a tela aberta.",
                "warning",
                5200,
            )
            return
        QTimer.singleShot(delay_ms, lambda aid=account_id, pid=profile_id: self._auto_flow_tick(aid, pid))

    def _auto_flow_tick(self, account_id: str, profile_id: str):
        account = self._account_by_id(account_id)
        if not account:
            return
        if self.browser_manager.is_profile_launching(profile_id):
            self._reschedule_auto_flow_tick(account_id, profile_id, 2200)
            return
        if f"smart_continue:{profile_id}" in self._action_workers:
            self._reschedule_auto_flow_tick(account_id, profile_id, 2200)
            return
        if any(str(key).startswith("smart_continue:") for key in self._action_workers):
            self._reschedule_auto_flow_tick(account_id, profile_id, 1600)
            return
        if not self._is_profile_probably_active_fast(profile_id):
            self._launch_profile(profile_id, navigate_to=PARAMOUNT_URLS["cadastro"])
            self._schedule_auto_flow_next(account_id, profile_id, 6500)
            return
        self._smart_continue_active_async(account, profile_id, auto_chain=True)

    def _smart_continue_active_async(self, account: Dict, profile_id: str, auto_chain: bool = False):
        self.ensure_person_for_account(account, persist=True)
        self.save_data()
        account_id = account.get("id", "")
        profile_id_value = str(profile_id)
        account_snapshot = json.loads(json.dumps(account, ensure_ascii=False))

        def work():
            driver, error = self._driver_for_profile(profile_id_value)
            if not driver:
                return {"action": "error", "message": error}

            state = self._page_state(driver)
            url = (state.get("url") or "").lower()
            text = (state.get("text") or "").lower()
            subscription_result = self._subscription_status_from_state(state)
            if subscription_result.get("status") == "assinatura ativa":
                return {"action": "subscription_active", "state": state}

            if any(term in text for term in ["cloudflare", "confirme que e humano", "confirme que é humano", "verificacao de seguranca", "verificação de segurança"]):
                return {"action": "manual_check"}

            if "signup/account" in url and int(state.get("input_count", 0) or 0) == 0:
                clicked = self._click_safe_continue(driver)
                return {"action": "flow_result", "step": "Entrada", "fill": {"ok": True, "filled": 0}, "click": clicked}

            if any(term in text for term in ["voce esta a apenas alguns passos", "você está a apenas alguns passos"]):
                clicked = self._click_safe_continue(driver)
                return {"action": "flow_result", "step": "Entrada", "fill": {"ok": True, "filled": 0}, "click": clicked}

            has_signup_fields = bool(state.get("has_signup_fields"))
            has_payment_fields = bool(state.get("has_payment_fields"))

            if has_signup_fields or ("signup/account" in url and any(term in text for term in ["crie uma conta", "nome completo", "e-mail", "senha"])):
                fill_result = self._fill_signup_fields_on_driver(driver, account_snapshot, persist=False)
                if not fill_result.get("ok"):
                    return {"action": "error", "message": fill_result.get("message", "Nao consegui preencher.")}
                self._accept_visible_terms(driver)
                clicked = self._click_safe_continue(driver)
                return {"action": "signup_result", "fill": fill_result, "click": clicked}

            if "signup/plan" in url and any(term in text for term in ["em seguida", "selecione as opcoes", "selecione as opções", "renovacao automatica", "renovação automática", "voce pode cancelar", "você pode cancelar"]):
                clicked = self._click_safe_continue(driver)
                return {"action": "flow_result", "step": "Plano", "fill": {"ok": True, "filled": 0}, "click": clicked}

            if "signup/tier" in url or "signup/plan" in url or "escolha o plano" in text or "escolha seu plano" in text:
                return {"action": "plan"}

            if has_payment_fields or any(term in text for term in ["metodo de pagamento", "método de pagamento", "cep", "cpf", "endereco", "endereço"]):
                return {"action": "address"}

            clicked = self._click_safe_continue(driver)
            if clicked.get("clicked"):
                return {"action": "flow_result", "step": "Pagina", "fill": {"ok": True, "filled": 0}, "click": clicked}

            return {"action": "unknown", "url": state.get("url", "")}

        def done(payload: Dict):
            action = payload.get("action")
            target = self._account_by_id(account_id) or self.current_account() or account

            if action == "error":
                self._set_flow_task(account_id, target, status="error", last_error=payload.get("message", "Falha no fluxo."))
                self._show_toast("Fluxo Paramount", payload.get("message", "Falha no fluxo."), "warning", 5200)
                return

            if action == "subscription_active":
                self._apply_subscription_status(target, payload.get("state", {}), silent=True)
                self._set_flow_task(account_id, target, status="success", last_error="")
                self._show_toast(
                    "Assinatura ativa",
                    "Esta conta parece ter assinatura ativa. Parei o fluxo para voce conferir.",
                    "success",
                    5200,
                )
                return

            if action == "manual_check":
                self._set_flow_task(
                    account_id,
                    target,
                    status="review",
                    last_error="Verificacao manual ou bloqueio visual na pagina.",
                )
                self._show_toast(
                    "Verificacao manual",
                    "Resolva no navegador e clique em Continuar de novo.",
                    "warning",
                    5200,
                )
                return

            if action == "signup_result":
                fill_result = payload.get("fill", {}) or {}
                if fill_result.get("filled", 0) >= 2:
                    target["status"] = "login ok"
                    target["updated_at"] = _now()
                    self.status_combo.setCurrentText("login ok")
                    self.save_data()
                    self.refresh_accounts_table()
                self._set_flow_task(account_id, target, status="running", last_error="")
                self._show_flow_result("Cadastro", fill_result, payload.get("click", {}) or {})
                if auto_chain and (payload.get("click", {}) or {}).get("clicked"):
                    self._schedule_auto_flow_next(account_id, profile_id_value, 3300)
                return

            if action == "flow_result":
                self._set_flow_task(account_id, target, status="running", last_error="")
                self._show_flow_result(payload.get("step", "Pagina"), payload.get("fill", {}) or {}, payload.get("click", {}) or {})
                if auto_chain and (payload.get("click", {}) or {}).get("clicked"):
                    self._schedule_auto_flow_next(account_id, profile_id_value, 2800)
                return

            if action == "plan":
                if auto_chain:
                    self.quick_select_plan_async(
                        target,
                        profile_id_value,
                        after_done=lambda aid=account_id, pid=profile_id_value: self._schedule_auto_flow_next(aid, pid, 3300),
                    )
                else:
                    self.quick_select_plan_async(target, profile_id_value)
                return

            if action == "address":
                self.fill_cpf_address_for_current(target, profile_id_value)
                self._set_flow_task(
                    account_id,
                    target,
                    status="review",
                    last_error="Chegou em CPF/endereco. Confira antes de pagamento.",
                )
                if auto_chain:
                    self._auto_flow_attempts.pop(account_id, None)
                return

            self._set_flow_task(
                account_id,
                target,
                status="review",
                last_error=f"Proximo passo nao identificado: {payload.get('url', '')}",
            )
            self._show_toast(
                "Fluxo Paramount",
                f"Nao encontrei o proximo passo automatico nesta tela. URL: {payload.get('url', '')}",
                "warning",
                5200,
            )

        self._run_background_action(
            f"smart_continue:{profile_id_value}",
            "Fluxo Paramount",
            "Analisando a tela e clicando sem travar a interface...",
            work,
            done,
        )

    def smart_continue_for_current(self):
        account = self.current_account()
        if not account:
            self._show_toast("Continuar", "Selecione uma conta primeiro.", "warning", 4200)
            return
        self.save_current_account()
        account = self.current_account() or account
        profile_id = account.get("profile_id", "")

        if not profile_id:
            profile_id = self.ensure_profile_for_account(account)
            if profile_id:
                self._auto_flow_attempts[account.get("id", "")] = 0
                self._launch_profile(profile_id, navigate_to=PARAMOUNT_URLS["cadastro"])
                self._schedule_auto_flow_next(account.get("id", ""), profile_id, 6500)
            return

        if not self._is_profile_probably_active_fast(profile_id):
            self._auto_flow_attempts[account.get("id", "")] = 0
            self._launch_profile(profile_id, navigate_to=PARAMOUNT_URLS["cadastro"])
            self.log(f"Abrindo cadastro para {account.get('email', '')}...")
            self._schedule_auto_flow_next(account.get("id", ""), profile_id, 6500)
            return

        self._auto_flow_attempts[account.get("id", "")] = 0
        self._smart_continue_active_async(account, profile_id, auto_chain=True)
        return

        driver, error = self._driver_for_current()
        if not driver:
            QMessageBox.warning(self, "Fluxo Paramount", error)
            return

        state = self._page_state(driver)
        url = (state.get("url") or "").lower()
        text = (state.get("text") or "").lower()
        subscription_result = self._apply_subscription_status(account, state, silent=True)
        if subscription_result.get("status") == "assinatura ativa":
            self._show_toast(
                "Assinatura ativa",
                "Esta conta parece ter assinatura ativa. Parei o fluxo para voce conferir.",
                "success",
                5200,
            )
            return

        if any(term in text for term in ["cloudflare", "confirme que e humano", "confirme que é humano", "verificacao de seguranca", "verificação de segurança"]):
            self._show_toast(
                "Verificacao manual",
                "Resolva no navegador e clique em Continuar de novo.",
                "warning",
                5200,
            )
            return

        if "signup/account" in url and int(state.get("input_count", 0) or 0) == 0:
            clicked = self._click_safe_continue(driver)
            self._show_flow_result("Entrada", {"ok": True, "filled": 0}, clicked)
            return

        if any(term in text for term in ["voce esta a apenas alguns passos", "você está a apenas alguns passos"]):
            clicked = self._click_safe_continue(driver)
            self._show_flow_result("Entrada", {"ok": True, "filled": 0}, clicked)
            return

        if "signup/account" in url or "crie uma conta" in text or state.get("input_count", 0) >= 3:
            result = self._fill_signup_fields(account)
            if not result.get("ok"):
                QMessageBox.warning(self, "Fluxo Paramount", result.get("message", "Nao consegui preencher."))
                return
            self._accept_visible_terms(driver)
            clicked = self._click_safe_continue(driver)
            if result.get("filled", 0) >= 2:
                account["status"] = "login ok"
                account["updated_at"] = _now()
                self.save_data()
                self.status_combo.setCurrentText("login ok")
                self.refresh_accounts_table()
            self._show_flow_result("Cadastro", result, clicked)
            return

        if "signup/plan" in url or "escolha o plano" in text or "escolha seu plano" in text:
            self.quick_select_plan()
            return

        if any(term in text for term in ["metodo de pagamento", "método de pagamento", "cep", "cpf", "endereco", "endereço"]):
            self.fill_cpf_address_for_current()
            return

        clicked = self._click_safe_continue(driver)
        if clicked.get("clicked"):
            self._show_flow_result("Pagina", {"ok": True, "filled": 0}, clicked)
            return

        self._show_toast(
            "Fluxo Paramount",
            f"Nao encontrei o proximo passo automatico nesta tela. URL: {state.get('url', '')}",
            "warning",
            5200,
        )

    def open_signup_for_current(self):
        account = self.current_account()
        if not account:
            QMessageBox.warning(self, "Cadastro", "Selecione uma conta primeiro.")
            return
        profile_id = account.get("profile_id")
        if not profile_id:
            QMessageBox.warning(self, "Cadastro", "Crie ou vincule um perfil primeiro.")
            return
        self._launch_profile(profile_id, navigate_to=PARAMOUNT_URLS["cadastro"])

    def fill_signup_for_current(self):
        account = self.account_from_form()
        profile_id = account.get("profile_id")
        if not profile_id:
            QMessageBox.warning(self, "Preencher", "Crie ou vincule um perfil primeiro.")
            return
        if not self._is_profile_probably_active_fast(profile_id):
            self._launch_profile(profile_id, navigate_to=PARAMOUNT_URLS["cadastro"])
            self._show_toast(
                "Cadastro aberto",
                "Quando carregar, clique em Preencher cadastro de novo.",
                "info",
            )
            return
        driver, _ = self._driver_for_current()
        if driver:
            state = self._page_state(driver)
            if state.get("has_payment_fields") and not state.get("has_signup_fields"):
                self._show_toast(
                    "Tela de pagamento",
                    "Esta tela usa primeiro nome/sobrenome. Use CPF + endereco ou Continuar fluxo automatico.",
                    "warning",
                    5200,
                )
                return
        result = self._fill_signup_fields(account)
        if not result.get("ok"):
            QMessageBox.warning(self, "Preencher", result.get("message", "Nao consegui preencher."))
            return
        if driver:
            self._accept_visible_terms(driver)
        results = result.get("results", {}) or {}
        name_ok = bool((results.get("fullName") or {}).get("ok"))
        email_ok = bool((results.get("email") or {}).get("ok"))
        pass_ok = bool((results.get("password") or {}).get("ok"))
        if result.get("filled", 0):
            account["status"]     = "login ok"
            account["updated_at"] = _now()
            self.save_data()
            self.status_combo.setCurrentText("login ok")
            self.refresh_accounts_table()
            self.log(f"Cadastro preenchido: nome={name_ok}, email={email_ok}, senha={pass_ok}")
            self._show_toast(
                "Cadastro preenchido",
                f"Nome: {name_ok} | Email: {email_ok} | Senha: {pass_ok}. Aceite marcado quando encontrado.",
                "success",
            )
        else:
            QMessageBox.warning(
                self, "Preencher",
                "Nao encontrei os campos na pagina aberta.\n\nAbra o cadastro manualmente e tente de novo.",
            )

    def fill_signup_for_current_async(self):
        account = self.account_from_form()
        profile_id = account.get("profile_id")
        if not profile_id:
            QMessageBox.warning(self, "Preencher", "Crie ou vincule um perfil primeiro.")
            return
        if not self._is_profile_probably_active_fast(profile_id):
            self._launch_profile(profile_id, navigate_to=PARAMOUNT_URLS["cadastro"])
            self._show_toast(
                "Cadastro aberto",
                "Quando carregar, clique em Preencher cadastro de novo.",
                "info",
            )
            return

        self.ensure_person_for_account(account, persist=True)
        self.save_data()
        account_id = account.get("id", "")
        profile_id_value = str(profile_id)
        account_snapshot = json.loads(json.dumps(account, ensure_ascii=False))

        def work():
            driver, error = self._driver_for_profile(profile_id_value)
            if not driver:
                return {"ok": False, "message": error, "filled": 0}
            self._prepare_driver_for_short_action(driver)
            state = self._page_state(driver)
            if state.get("has_payment_fields") and not state.get("has_signup_fields"):
                return {
                    "ok": False,
                    "message": "Esta tela usa primeiro nome/sobrenome. Use CPF + endereco ou Continuar fluxo automatico.",
                    "filled": 0,
                }
            result = self._fill_signup_fields_on_driver(driver, account_snapshot, persist=False)
            if result.get("ok"):
                self._accept_visible_terms(driver)
            return result

        def done(result: Dict):
            target = self._account_by_id(account_id) or self.current_account() or account
            if not result.get("ok"):
                self._show_toast("Preencher", result.get("message", "Nao consegui preencher."), "warning", 5200)
                return
            results = result.get("results", {}) or {}
            name_ok = bool((results.get("fullName") or {}).get("ok"))
            email_ok = bool((results.get("email") or {}).get("ok"))
            pass_ok = bool((results.get("password") or {}).get("ok"))
            if result.get("filled", 0):
                target["status"] = "login ok"
                target["updated_at"] = _now()
                self.save_data()
                self.status_combo.setCurrentText("login ok")
                self.refresh_accounts_table()
                self.log(f"Cadastro preenchido: nome={name_ok}, email={email_ok}, senha={pass_ok}")
                self._show_toast(
                    "Cadastro preenchido",
                    f"Nome: {name_ok} | Email: {email_ok} | Senha: {pass_ok}. Aceite marcado quando encontrado.",
                    "success",
                )
            else:
                self._show_toast(
                    "Preencher",
                    "Nao encontrei os campos na pagina aberta. Abra o cadastro e tente de novo.",
                    "warning",
                    5200,
                )

        self._run_background_action(
            f"signup:{profile_id_value}",
            "Preencher",
            "Preenchendo cadastro sem travar a interface...",
            work,
            done,
            on_error=lambda error: self._show_toast("Preencher", error, "error", 5200),
        )

    def fill_cpf_address_for_current(self, account_override: Optional[Dict] = None, profile_id_override: Optional[str] = None):
        account = account_override or self.account_from_form()
        profile_id = profile_id_override or account.get("profile_id")
        raw_address = account.get("address", {}) or ({} if account_override else self.address_from_form())
        address = self.normalize_address(raw_address)
        if not profile_id:
            self._show_toast("CPF/Endereco", "Crie ou vincule um perfil primeiro.", "warning", 4200)
            return
        person = account.get("person", {}) or {}
        cpf = _digits(person.get("cpf", ""))
        if not cpf:
            self._show_toast("CPF/Endereco", "Nenhum CPF disponivel. Gere os dados da pessoa primeiro.", "warning", 4200)
            return
        if not self.address_is_complete(address):
            generated = self._generate_complete_address(base=address, silent=True)
            if generated and self.address_is_complete(generated):
                address = generated
                if not account_override:
                    self.load_address_to_form(address)
                account["address"] = address
                account["updated_at"] = _now()
                self.save_data()
                self.log(f"Endereco gerado automaticamente: {address.get('city', '')} / {address.get('uf', '')}")
            else:
                self._show_toast(
                    "CPF/Endereco",
                    "Nao consegui montar um endereco completo automaticamente. Tente gerar de novo ou confira a reserva de CEP.",
                    "warning",
                    5200,
                )
                return
        address["cpf"] = cpf
        address["cpfDigits"] = cpf
        address["documento"] = cpf
        name_payload = self._account_payload_for_page(account, persist=True)
        if name_payload:
            address["firstName"] = name_payload.get("firstName", "")
            address["lastName"] = name_payload.get("lastName", "")
            address["fullName"] = name_payload.get("fullName", "")
        account["address"] = address
        account["updated_at"] = _now()
        self.save_data()

        address_payload = dict(address)
        profile_id_value = str(profile_id)

        def work():
            return self.browser_manager.fill_address_fields(profile_id_value, dict(address_payload))

        def done(address_result: Dict):
            ok_count = int(address_result.get("filled", 0) or 0)
            self.log(f"CPF/Endereco: {ok_count} campo(s). {address_result.get('message', '')}")
            if ok_count >= 2:
                self._show_toast(
                    "CPF e endereco",
                    f"Preenchi {ok_count} campo(s). Confira antes de continuar.",
                    "success",
                )
            else:
                self._show_toast(
                    "CPF/Endereco",
                    address_result.get("message") or "Poucos campos encontrados. Verifique se a pagina de checkout/perfil esta aberta.",
                    "warning",
                    5200,
                )

        self._run_background_action(
            f"cpf_address:{profile_id_value}",
            "CPF e endereco",
            "Preenchendo sem travar a interface...",
            work,
            done,
        )

    def generate_address_for_current(self):
        account = self.current_account()
        if not account:
            QMessageBox.warning(self, "Gerar endereco", "Selecione uma conta primeiro.")
            return
        existing = self.normalize_address(account.get("address", {}) or {})
        address = self._generate_complete_address(base=existing)

        if not address or not self.address_is_complete(address):
            QMessageBox.warning(
                self,
                "Gerar endereco",
                "Nao consegui gerar um endereco completo agora. Tente novamente ou confira a reserva de CEP.",
            )
            return

        address = self.normalize_address(address if isinstance(address, dict) else vars(address))
        self.load_address_to_form(address)

        account["address"]    = address
        account["updated_at"] = _now()
        self.save_data()
        self.log(f"Endereco gerado: {address.get('city', '')} / {address.get('uf', '')}")

    def copy_current_address(self):
        address = self.normalize_address(self.address_from_form())
        parts = [
            address.get("street", ""),
            address.get("number", ""),
            address.get("neighborhood", ""),
            address.get("city", ""),
            address.get("uf", "") or address.get("state", ""),
            address.get("cep", ""),
        ]
        text = ", ".join(p for p in parts if p)
        if text:
            set_clipboard_text(text)
            self.log("Endereco copiado.")

    def _select_paramount_tier_plan(self, driver, plan: str) -> Dict:
        """Seleciona o card real de plano na tela /signup/tier."""
        script = r"""
const wanted = (arguments[0] || "").toString();
const done = arguments[arguments.length - 1];
let finished = false;
function finish(payload) {
  if (finished) return;
  finished = true;
  done(payload);
}
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
}
function visible(el) {
  if (!el || !el.getBoundingClientRect) return false;
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 2 && r.height > 2;
}
function disabled(el) {
  return !!(el.disabled || el.getAttribute("aria-disabled") === "true" || /\bdisabled\b/i.test(el.className || ""));
}
function click(el) {
  if (!el) return false;
  try { el.scrollIntoView({block:"center", inline:"center"}); } catch (_) {}
  try { el.focus?.(); } catch (_) {}
  for (const type of ["pointerdown", "mousedown", "mouseup", "pointerup", "click"]) {
    try { el.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true, view:window})); } catch (_) {}
  }
  try { el.click?.(); } catch (_) {}
  return true;
}
const wantedClean = clean(wanted);
const tokens = wantedClean.split(/\s+/).filter(t => t.length > 2);
const wantsPadrao = /padrao|standard/.test(wantedClean);
const wantsPremium = !wantsPadrao || /premium/.test(wantedClean);
function scoreCard(el) {
  const text = clean(el.innerText || el.textContent || "");
  if (!text || text.length < 20 || text.length > 2200) return -999;
  let score = 0;
  if (/selecionar plano|escolher plano|premium|padrao|r\$/.test(text)) score += 15;
  if (wantsPremium && /\bpremium\b/.test(text)) score += 120;
  if (wantsPremium && /\bpadrao\b|\bstandard\b/.test(text)) score -= 80;
  if (wantsPadrao && (/\bpadrao\b|\bstandard\b/.test(text))) score += 120;
  if (wantsPadrao && /\bpremium\b/.test(text)) score -= 80;
  for (const token of tokens) if (token !== "mensal" && text.includes(token)) score += 8;
  if (/44,90|44\.90|premium mensal/.test(text)) score += wantsPremium ? 25 : -20;
  if (/34,90|34\.90/.test(text)) score += wantsPadrao ? 25 : -20;
  return score;
}
const cards = Array.from(document.querySelectorAll("article, section, li, label, form, [class*='plan'], [class*='tier'], [class*='card'], div"))
  .filter(visible)
  .map(el => ({el, text: el.innerText || el.textContent || "", score: scoreCard(el)}))
  .filter(item => item.score > 0)
  .sort((a, b) => b.score - a.score);
if (!cards.length) {
  finish({clicked:false, reason:"Nao encontrei card Premium/Padrao.", url:location.href});
  return;
}
const card = cards[0].el;
const cardText = clean(cards[0].text);
const radio = Array.from(card.querySelectorAll("input[type='radio'], [role='radio'], [aria-label], button, [class*='radio'], [class*='circle']"))
  .filter(visible)
  .filter(el => !disabled(el))
  .find(el => {
    const tx = clean(el.innerText || el.value || el.getAttribute("aria-label") || el.textContent || "");
    return !/selecionar plano|continuar|assinar/.test(tx);
  });
click(radio || card);
function candidateButtons() {
  const local = Array.from(card.querySelectorAll("button, a, [role='button'], input[type='button'], input[type='submit']"));
  const global = Array.from(document.querySelectorAll("button, a, [role='button'], input[type='button'], input[type='submit']"));
  const seen = new Set();
  return local.concat(global)
    .filter(el => {
      if (!el || seen.has(el)) return false;
      seen.add(el);
      return true;
    })
    .filter(visible)
    .map(el => ({el, text: clean(el.innerText || el.value || el.getAttribute("aria-label") || el.textContent || ""), disabled: disabled(el)}))
    .filter(item => /selecionar plano|escolher plano|continuar|selecionar/.test(item.text))
    .filter(item => !/assinar|pagamento|pagar|comprar|finalizar/.test(item.text))
    .map(item => {
      const parent = item.el.closest("article, section, li, label, form, [class*='plan'], [class*='tier'], [class*='card'], div");
      const parentText = clean((parent && (parent.innerText || parent.textContent)) || "");
      let score = parent === card ? 50 : 0;
      if (wantsPremium && /\bpremium\b/.test(parentText)) score += 40;
      if (wantsPadrao && (/\bpadrao\b|\bstandard\b/.test(parentText))) score += 40;
      if (item.disabled) score -= 1000;
      return {...item, score};
    })
    .sort((a, b) => b.score - a.score);
}
function trySubmit() {
  const buttons = candidateButtons();
  const enabled = buttons.find(item => !item.disabled && item.score > -100) || null;
  if (enabled) {
    click(enabled.el);
    finish({clicked:true, matched:cardText.slice(0,220), button:enabled.text || "selecionar plano", url:location.href});
    return true;
  }
  return false;
}
let tries = 0;
const timer = setInterval(() => {
  tries += 1;
  if (trySubmit()) {
    clearInterval(timer);
    return;
  }
  if (tries === 3 || tries === 6) click(radio || card);
  if (tries >= 12) {
    clearInterval(timer);
    finish({clicked:true, matched:cardText.slice(0,220), button:"card/radio", url:location.href, selectedOnly:true});
  }
}, 250);
"""
        try:
            try:
                driver.set_script_timeout(7)
            except Exception:
                pass
            return driver.execute_async_script(script, plan) or {}
        except Exception as exc:
            return {"clicked": False, "reason": str(exc), "url": ""}

    def _click_paramount_plan_submit(self, driver, plan: str) -> Dict:
        """Tenta clicar no botao habilitado de plano depois do card estar marcado."""
        script = r"""
const wanted = (arguments[0] || "").toString();
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().replace(/\s+/g, " ").trim();
}
function visible(el) {
  if (!el || !el.getBoundingClientRect) return false;
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 2 && r.height > 2;
}
function disabled(el) {
  return !!(el.disabled || el.getAttribute("aria-disabled") === "true" || /\bdisabled\b/i.test(el.className || ""));
}
function click(el) {
  try { el.scrollIntoView({block:"center", inline:"center"}); } catch (_) {}
  try { el.focus?.(); } catch (_) {}
  for (const type of ["pointerdown", "mousedown", "mouseup", "pointerup", "click"]) {
    try { el.dispatchEvent(new MouseEvent(type, {bubbles:true, cancelable:true, view:window})); } catch (_) {}
  }
  try { el.click?.(); } catch (_) {}
}
const wantedClean = clean(wanted);
const wantsPadrao = /padrao|standard/.test(wantedClean);
const wantsPremium = !wantsPadrao || /premium/.test(wantedClean);
const buttons = Array.from(document.querySelectorAll("button, a, [role='button'], input[type='button'], input[type='submit']"))
  .filter(visible)
  .map(el => {
    const text = clean(el.innerText || el.value || el.getAttribute("aria-label") || el.textContent || "");
    const parent = el.closest("article, section, li, label, form, [class*='plan'], [class*='tier'], [class*='card'], div");
    const parentText = clean((parent && (parent.innerText || parent.textContent)) || "");
    let score = 0;
    if (/selecionar plano|escolher plano|continuar|selecionar/.test(text)) score += 50;
    if (/assinar|pagamento|pagar|comprar|finalizar/.test(text)) score -= 1000;
    if (disabled(el)) score -= 1000;
    if (wantsPremium && /\bpremium\b/.test(parentText)) score += 40;
    if (wantsPremium && /\bpadrao\b|\bstandard\b/.test(parentText)) score -= 40;
    if (wantsPadrao && (/\bpadrao\b|\bstandard\b/.test(parentText))) score += 40;
    if (wantsPadrao && /\bpremium\b/.test(parentText)) score -= 40;
    return {el, text, score};
  })
  .filter(item => item.score > 0)
  .sort((a, b) => b.score - a.score);
if (!buttons.length) return {clicked:false, reason:"botao de plano ainda nao habilitado", url:location.href};
click(buttons[0].el);
return {clicked:true, button:buttons[0].text || "selecionar plano", url:location.href};
"""
        try:
            return driver.execute_script(script, plan) or {}
        except Exception as exc:
            return {"clicked": False, "reason": str(exc), "url": ""}

    def _prepare_driver_for_short_action(self, driver):
        """Evita que um script/site segure a automacao por tempo demais."""
        if not driver:
            return
        try:
            driver.set_page_load_timeout(18)
        except Exception:
            pass
        try:
            driver.set_script_timeout(8)
        except Exception:
            pass

    def _quick_select_plan_worker(self, profile_id_value: str, plan: str) -> Dict:
        driver, error = self._driver_for_profile(profile_id_value)
        if not driver:
            return {"action": "error", "message": error}

        self._prepare_driver_for_short_action(driver)
        self._dismiss_browser_overlays(driver)
        try:
            state = self._page_state(driver)
            current_url = state.get("url") or driver.execute_script("return location.href") or ""
        except Exception:
            state = {}
            current_url = getattr(driver, "current_url", "") or ""

        plan_url = current_url.lower()
        if "paramountplus.com" not in plan_url:
            try:
                driver.get(PARAMOUNT_URLS["plano"])
                return {"action": "navigated", "message": "Levei o perfil para a pagina de planos."}
            except Exception as exc:
                return {"action": "error", "message": f"Nao consegui abrir a pagina de planos: {exc}"}

        if "/signup/plan" in plan_url and "/signup/tier" not in plan_url:
            clicked = self._click_safe_continue(driver)
            if clicked.get("clicked"):
                return {"action": "advanced", "message": "Avancei da tela inicial de planos.", "click": clicked}
            return {"action": "error", "message": clicked.get("reason", "Nao encontrei o botao Continuar da tela de planos.")}

        if "/signup/tier" in plan_url:
            result = self._select_paramount_tier_plan(driver, plan)
            if result.get("selectedOnly"):
                time.sleep(0.45)
                submit = self._click_paramount_plan_submit(driver, plan)
                if submit.get("clicked"):
                    result = submit
            if result.get("clicked"):
                return {"action": "selected", "message": "Plano selecionado.", "result": result}
            return {"action": "error", "message": result.get("reason", "Nao consegui selecionar o plano.")}

        submit = self._click_paramount_plan_submit(driver, plan)
        if submit.get("clicked"):
            return {"action": "selected", "message": "Plano selecionado.", "result": submit}
        fallback = self._click_safe_continue(driver)
        if fallback.get("clicked"):
            return {"action": "advanced", "message": "Avancei para a proxima etapa do plano.", "click": fallback}
        return {
            "action": "error",
            "message": submit.get("reason") or fallback.get("reason") or "Nao encontrei o plano nesta tela.",
        }

    def quick_select_plan_async(
        self,
        account_override: Optional[Dict] = None,
        profile_id_override: Optional[str] = None,
        after_done=None,
    ):
        account = account_override or self.account_from_form()
        plan = account.get("plan", "").strip()
        profile_id = profile_id_override or account.get("profile_id")
        if not plan:
            QMessageBox.warning(self, "Plano", "Selecione ou escreva um plano no campo Plano.")
            return
        if not profile_id:
            self._launch_profile_and_navigate(PARAMOUNT_URLS["plano"])
            self._show_toast("Plano", "Abri a pagina de planos. Quando carregar, clique em Selecionar plano.", "info")
            return

        account_id = account.get("id", "")
        profile_id_value = str(profile_id)

        def work():
            return self._quick_select_plan_worker(profile_id_value, plan)

        def done(payload: Dict):
            action = (payload or {}).get("action", "")
            target = self._account_by_id(account_id) or self.current_account() or account
            if action in {"selected", "advanced", "navigated"}:
                target["plan"] = plan
                target["updated_at"] = _now()
                self.save_data()
                self.refresh_accounts_table()
                detail = (payload or {}).get("message", "Plano processado.")
                result = (payload or {}).get("result") or (payload or {}).get("click") or {}
                button = result.get("button", "")
                self.log(f"Plano: {detail} {button}".strip())
                self._show_toast("Plano", detail, "success" if action != "navigated" else "info")
                if after_done:
                    QTimer.singleShot(2800 if action != "navigated" else 4200, after_done)
                return
            message = (payload or {}).get("message", "Nao consegui selecionar o plano.")
            self.log(f"Plano: {message}")
            self._show_toast("Plano", message, "warning", 5200)

        self._run_background_action(
            f"plan:{profile_id_value}",
            "Plano",
            "Selecionando plano sem travar a interface...",
            work,
            done,
            on_error=lambda error: self._show_toast("Plano", error, "error", 5200),
        )

    def quick_select_plan(self, account_override: Optional[Dict] = None, profile_id_override: Optional[str] = None):
        account = account_override or self.account_from_form()
        plan = account.get("plan", "").strip()
        profile_id = profile_id_override or account.get("profile_id")
        if not plan:
            QMessageBox.warning(self, "Plano", "Selecione ou escreva um plano no campo Plano.")
            return
        if not profile_id:
            self._launch_profile_and_navigate(PARAMOUNT_URLS["plano"])
            self._show_toast("Plano", "Abri a pagina de planos. Quando carregar, clique em Selecionar plano.", "info")
            return
        driver, error = self._driver_for_profile(str(profile_id))
        if not driver:
            QMessageBox.warning(self, "Plano", error)
            return
        self._dismiss_browser_overlays(driver)
        try:
            current_url = driver.execute_script("return location.href") or ""
        except Exception:
            current_url = ""
        plan_url = current_url.lower()
        if "paramountplus.com" not in plan_url or ("/signup/plan" not in plan_url and "/signup/tier" not in plan_url):
            self.navigate_active_profile(profile_id, PARAMOUNT_URLS["plano"])
            self._show_toast("Plano", "Levei o perfil para a pagina de planos. Quando carregar, clique em Selecionar plano de novo.", "info")
            return
        if "/signup/tier" in plan_url:
            result = self._select_paramount_tier_plan(driver, plan)
            if result.get("selectedOnly"):
                time.sleep(0.6)
                submit = self._click_paramount_plan_submit(driver, plan)
                if submit.get("clicked"):
                    result = submit
            if result.get("clicked"):
                account["plan"] = plan
                account["updated_at"] = _now()
                self.save_data()
                self.log(f"Plano selecionado no tier: {plan} | {result.get('button', '')}")
                self._show_toast(
                    "Plano selecionado",
                    "Cliquei no card do plano e avancei quando o botao ficou disponivel.",
                    "success",
                )
            else:
                self.log(f"Plano nao encontrado no tier: {plan} | {result.get('reason', '')}")
                QMessageBox.warning(self, "Plano", result.get("reason", "Nao consegui selecionar o plano."))
            return
        script = r"""
const wanted = (arguments[0] || "").toString();
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}
function visible(el) {
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0;
}
const wantedClean = clean(wanted);
const tokens = wantedClean.split(/\s+/).filter(t => t.length > 2);
const positive = ["selecionar", "escolher", "continuar", "assinar", "comecar", "começar"];
const blocked  = ["pagar", "pagamento", "finalizar", "concluir compra", "confirmar pagamento", "confirmar assinatura"];
function scoreText(text) {
  const hay = clean(text);
  let score = 0;
  for (const token of tokens) if (hay.includes(token)) score += 3;
  if (wantedClean && hay.includes(wantedClean)) score += 8;
  if (/mensal|mes|mês|anual|premium|essencial|standard|r\$/.test(hay)) score += 1;
  return score;
}
const blocks = Array.from(document.querySelectorAll("article, section, li, div, form"))
  .filter(visible)
  .map(el => ({el, text: el.innerText || el.textContent || ""}))
  .filter(item => item.text && item.text.length < 1800)
  .map(item => ({...item, score: scoreText(item.text)}))
  .filter(item => item.score > 0)
  .sort((a, b) => b.score - a.score);
for (const item of blocks) {
  const buttons = Array.from(item.el.querySelectorAll("button, a, [role='button'], input[type='button'], input[type='submit']"))
    .filter(visible);
  const ranked = buttons.map(btn => {
    const txt = clean(btn.innerText || btn.value || btn.getAttribute("aria-label") || btn.textContent || "");
    let score = 0;
    if (positive.some(word => txt.includes(clean(word)))) score += 5;
    if (tokens.some(token => txt.includes(token))) score += 2;
    if (blocked.some(word => txt.includes(clean(word)))) score -= 30;
    return {btn, txt, score};
  }).filter(x => x.score >= 0).sort((a, b) => b.score - a.score);
  if (ranked.length) {
    ranked[0].btn.scrollIntoView({block:"center", inline:"center"});
    ranked[0].btn.click();
    return {clicked:true, matched:item.text.slice(0,220), button:ranked[0].txt, url:location.href};
  }
  item.el.scrollIntoView({block:"center", inline:"center"});
  item.el.click();
  return {clicked:true, matched:item.text.slice(0,220), button:"card", url:location.href};
}
return {clicked:false, reason:"Nao encontrei card/botao com esse texto.", url:location.href};
"""
        try:
            result = driver.execute_script(script, plan) or {}
        except Exception as exc:
            QMessageBox.warning(self, "Plano", f"Nao consegui selecionar o plano: {exc}")
            return
        if result.get("clicked"):
            account["plan"]       = plan
            account["updated_at"] = _now()
            self.save_data()
            self.log(f"Plano selecionado visualmente: {plan} | botao: {result.get('button', '')}")
            self._show_toast(
                "Plano selecionado",
                "Confira a tela antes de continuar. O app nao confirma pagamento.",
                "success",
            )
        else:
            fallback = self._click_safe_continue(driver)
            if fallback.get("clicked"):
                self.log(f"Plano: clique seguro em continuar usado como fallback | {fallback.get('button', '')}")
                self._show_toast(
                    "Plano",
                    "Avancei pela tela de plano. O app ainda para antes de confirmar pagamento.",
                    "success",
                )
                return
            self.log(f"Plano nao encontrado: {plan} | {result.get('reason', '')}")
            QMessageBox.warning(
                self, "Plano",
                f"Nao encontrei o plano '{plan}'.\n\nDigite no campo Plano um texto igual ao que aparece no site e tente de novo.",
            )

    def fill_address_for_current(self):
        account  = self.account_from_form()
        profile_id = account.get("profile_id")
        address  = self.normalize_address(self.address_from_form())
        if not profile_id:
            QMessageBox.warning(self, "Endereco", "Crie ou vincule um perfil primeiro.")
            return
        if not self.address_is_complete(address):
            generated = self._generate_complete_address(base=address, silent=True)
            if generated and self.address_is_complete(generated):
                address = generated
                self.load_address_to_form(address)
                account["address"] = address
                account["updated_at"] = _now()
                self.save_data()
                self.log(f"Endereco gerado automaticamente: {address.get('city', '')} / {address.get('uf', '')}")
            else:
                QMessageBox.warning(self, "Endereco", "Nao consegui gerar um endereco completo agora.")
                return
        address_payload = dict(address)
        name_payload = self._account_payload_for_page(account, persist=True)
        if name_payload:
            address_payload.update({
                "firstName": name_payload.get("firstName", ""),
                "lastName": name_payload.get("lastName", ""),
                "fullName": name_payload.get("fullName", ""),
            })
        profile_id_value = str(profile_id)

        def work():
            return self.browser_manager.fill_address_fields(profile_id_value, dict(address_payload))

        def done(result: Dict):
            self.log(result.get("message", f"Endereco: {result.get('filled', 0)} campo(s)."))
            if not result.get("ok"):
                QMessageBox.warning(self, "Endereco", result.get("message", "Nao consegui preencher."))
            else:
                self._show_toast("Endereco", result.get("message", "Endereco preenchido."), "success")

        self._run_background_action(
            f"address:{profile_id_value}",
            "Endereco",
            "Preenchendo endereco sem travar a interface...",
            work,
            done,
        )

    def diagnose_current_page(self):
        account = self.account_from_form()
        profile_id = account.get("profile_id")
        if not profile_id:
            QMessageBox.warning(self, "Diagnostico", "Crie ou vincule um perfil primeiro.")
            return
        result = self.browser_manager.detect_page_issue(profile_id)
        lines = [
            result.get("title", "Diagnostico"),
            result.get("message", ""),
            "",
            "Sugestoes:",
            *[f"- {s}" for s in result.get("suggestions", [])],
        ]
        self.log(" | ".join(line for line in lines if line))
        QMessageBox.information(self, "Diagnostico", "\n".join(lines))

    def check_subscription_for_current(self):
        account = self.account_from_form()
        profile_id = account.get("profile_id")
        if not profile_id:
            QMessageBox.warning(self, "Assinatura", "Crie ou vincule um perfil primeiro.")
            return
        account_id = account.get("id", "")
        profile_id_value = str(profile_id)

        def work():
            driver, error = self._driver_for_profile(profile_id_value)
            if not driver:
                return {"ok": False, "message": error, "state": {}}
            return {"ok": True, "state": self._page_state(driver)}

        def done(payload: Dict):
            if not payload.get("ok"):
                QMessageBox.warning(self, "Assinatura", payload.get("message", "Nao consegui ler a pagina."))
                return
            target = None
            for item in self.data.get("accounts", []):
                if item.get("id") == account_id:
                    target = item
                    break
            target = target or self.current_account() or account
            result = self._apply_subscription_status(target, payload.get("state", {}), silent=False)
            if not result.get("status"):
                self.log(f"Assinatura nao detectada: {result.get('reason', '')}")
                self._show_toast(
                    "Assinatura",
                    "Nao encontrei sinal claro. Abra a area da conta/assinatura e tente de novo.",
                    "warning",
                    5200,
                )

        self._run_background_action(
            f"subscription:{profile_id_value}",
            "Assinatura",
            "Lendo a pagina aberta sem travar a interface...",
            work,
            done,
        )

    def mark_status(self, status: str):
        account = self.current_account()
        if not account:
            return
        account["status"]     = status
        account["updated_at"] = _now()
        self.status_combo.setCurrentText(status)
        self.save_data()
        self.refresh_accounts_table()
        self.log(f"Status atualizado: {account.get('email', '')} -> {status}")

    def add_card(self):
        number = _digits(self.card_input.text())
        last4  = number[-4:] if number else self.card_input.text().strip()[-4:]
        if len(last4) < 4:
            QMessageBox.warning(self, "Cartao", "Informe pelo menos o final 4.")
            return
        card = {
            "id":         _make_id("card", last4),
            "label":      self.card_label.text().strip() or f"Cartao final {last4}",
            "last4":      last4,
            "expiry":     self.card_expiry.text().strip(),
            "holder":     self.card_holder.text().strip(),
            "status":     self.card_status.currentText(),
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.data.setdefault("cards", []).append(card)
        self.card_input.clear()
        self.save_data()
        self.refresh_cards_table()
        self.log(f"Referencia de cartao salva: final {last4}")

    def selected_card(self) -> Optional[Dict]:
        row = self.cards_table.currentRow()
        if row < 0:
            return None
        item = self.cards_table.item(row, 0)
        card_id = item.data(Qt.UserRole) if item else ""
        for card in self.data.get("cards", []):
            if card.get("id") == card_id:
                return card
        return None

    def remove_selected_card(self):
        card = self.selected_card()
        if not card:
            return
        self.data["cards"] = [c for c in self.data.get("cards", []) if c.get("id") != card.get("id")]
        self.save_data()
        self.refresh_cards_table()
        self.log(f"Referencia removida: final {card.get('last4', '')}")

    def copy_selected_card(self):
        card = self.selected_card()
        if not card:
            return
        text = f"{card.get('label', '')} | final {card.get('last4', '')} | {card.get('expiry', '')} | {card.get('holder', '')}"
        set_clipboard_text(text)
        self.log("Resumo do cartao copiado.")

    def clear_logs(self):
        self.data["logs"] = []
        self.save_data()
        self.refresh_logs()

    def closeEvent(self, event):
        for thread in list(self.launch_threads.values()):
            try:
                thread.stop()
            except Exception:
                pass
        for worker in list(getattr(self, "_action_workers", {}).values()):
            try:
                worker.requestInterruption()
                worker.wait(250)
            except Exception:
                pass
        super().closeEvent(event)

    def _launch_profile_and_navigate(self, url: str):
        account = self.current_account()
        if account and account.get("profile_id"):
            self._launch_profile(account["profile_id"], navigate_to=url)
