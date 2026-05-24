#!/usr/bin/env python3
"""Widgets e constantes visuais do casco principal da aplicacao."""

from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QIcon, QLinearGradient, QPainter, QPen, QPixmap
from PyQt5.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QVBoxLayout, QWidget,
)

from app.core.app_metadata import APP_VERSION_LABEL
from app.core.clipboard_service import set_clipboard_text
from app.core.error_service import log_exception
from app.ui.app_theme import DARK_STYLE_PRO
from settings import BASE_DIR

def create_app_icon():
    """Cria um ícone para a aplicação programaticamente"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    gradient = QLinearGradient(0, 0, 64, 64)
    gradient.setColorAt(0, QColor("#06b6d4"))
    gradient.setColorAt(1, QColor("#6d28d9"))
    
    painter.setBrush(QBrush(gradient))
    painter.setPen(QPen(Qt.transparent))
    painter.drawEllipse(4, 4, 56, 56)
    
    painter.setPen(QPen(QColor("#ffffff")))
    font = QFont("Arial", 20, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "TC")
    
    painter.end()
    
    return QIcon(pixmap)


def _btn(text, color="#06b6d4", text_color="#07080f", icon=""):
    """Helper para criar QPushButton estilizado."""
    b = QPushButton(f"{icon} {text}".strip() if icon else text)
    b.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            color: {text_color};
            border: none;
            border-radius: 10px;
            padding: 9px 18px;
            font-size: 12px;
            font-weight: 600;
        }}
        QPushButton:hover {{ background-color: {color}cc; }}
        QPushButton:pressed {{ background-color: {color}99; }}
        QPushButton:disabled {{ background-color: #1a2540; color: #475569; }}
    """)
    return b


def _ghost_btn(text, icon=""):
    """Botão fantasma (sem fundo)."""
    b = QPushButton(f"{icon} {text}".strip() if icon else text)
    b.setStyleSheet("""
        QPushButton {
            background: rgba(255,255,255,0.04);
            color: #94a3b8;
            border: 1px solid rgba(6,182,212,0.15);
            border-radius: 9px;
            padding: 8px 14px;
            font-size: 11px;
            font-weight: 500;
        }
        QPushButton:hover {
            background: rgba(6,182,212,0.1);
            border-color: rgba(6,182,212,0.4);
            color: #22d3ee;
        }
        QPushButton:checked {
            background: rgba(6,182,212,0.15);
            border-color: #06b6d4;
            color: #06b6d4;
        }
    """)
    return b


def _card(radius=14):
    """Cria um QFrame estilo cartão."""
    f = QFrame()
    f.setStyleSheet(f"""
        QFrame {{
            background-color: #131d2e;
            border: 1px solid rgba(6,182,212,0.1);
            border-radius: {radius}px;
        }}
    """)
    return f


def _separator(horizontal=True):
    f = QFrame()
    f.setFrameShape(QFrame.HLine if horizontal else QFrame.VLine)
    f.setStyleSheet("QFrame { background: rgba(6,182,212,0.08); border: none; max-height: 1px; }")
    return f


def _log_compact_error(context, exc):
    """Registra falhas do painel compacto sem derrubar o app."""
    log_exception(BASE_DIR, "compact_panel_errors.log", context, exc)


def _set_clipboard_text_safe(text):
    """Copia texto usando Qt puro e fallback direto do QApplication."""
    text = text or ""
    try:
        return set_clipboard_text(text)
    except Exception:
        QApplication.clipboard().setText(text)
        return True


def _label(text, size=12, color="#94a3b8", bold=False, mono=False):
    l = QLabel(text)
    weight = "600" if bold else "400"
    family = "'Consolas', 'SF Mono', monospace" if mono else "inherit"
    l.setStyleSheet(f"color:{color}; font-size:{size}px; font-weight:{weight}; font-family:{family}; background:transparent; border:none;")
    return l


def _field_row(icon_text, field_widget, copy_cb):
    """Linha de campo com label + widget + botao copiar."""
    row = QHBoxLayout()
    row.setSpacing(7)
    row.setContentsMargins(0, 1, 0, 1)
    lbl = QLabel(icon_text)
    lbl.setFixedWidth(62)
    lbl.setCursor(Qt.PointingHandCursor)
    lbl.setToolTip(f"Copiar {icon_text}")
    lbl.setStyleSheet("color:#94a3b8; font-size:11px; background:transparent; border:none;")
    cp = QPushButton("Copiar")
    cp.setFixedSize(64, 30)
    cp.setToolTip(f"Copiar {icon_text}")
    cp.setStyleSheet("""
        QPushButton {
            background: rgba(6,182,212,0.07);
            border: 1px solid rgba(6,182,212,0.15);
            border-radius: 5px;
            font-size: 11px;
            font-weight: 700;
            color: #06b6d4;
        }
        QPushButton:hover { background: rgba(6,182,212,0.2); }
    """)

    def run_copy(event=None):
        try:
            if event is not None:
                event.accept()
            copy_cb()
        except Exception as exc:
            _log_compact_error(f"copiar campo {icon_text}", exc)

    field_widget.setCursorPosition(0)
    field_widget.setCursor(Qt.PointingHandCursor)
    field_widget.setToolTip(f"Clique para copiar {icon_text}")
    field_widget.mousePressEvent = run_copy
    lbl.mousePressEvent = run_copy
    cp.clicked.connect(lambda checked=False: run_copy())
    row.addWidget(lbl)
    row.addWidget(field_widget, 1)
    row.addWidget(cp)
    return row


APP_COLORS = {
    "bg_deep":    "#07080f",
    "bg_base":    "#0a0e1a",
    "bg_panel":   "#0f1626",
    "bg_card":    "#131d2e",
    "bg_hover":   "#1a2540",
    "border":     "rgba(6,182,212,0.12)",
    "border_hi":  "rgba(6,182,212,0.35)",
    "accent":     "#06b6d4",
    "accent_dim": "#0891b2",
    "accent_glow":"rgba(6,182,212,0.08)",
    "text_hi":    "#f1f5f9",
    "text_mid":   "#94a3b8",
    "text_lo":    "#475569",
    "green":      "#10b981",
    "red":        "#f43f5e",
    "amber":      "#f59e0b",
    "purple":     "#8b5cf6",
}


GLOBAL_QSS = DARK_STYLE_PRO + """
QStatusBar {
    background-color: #07080f;
    color: #475569;
    font-size: 11px;
    border-top: 1px solid rgba(6,182,212,0.08);
}
QStatusBar::item { border: none; }
"""


TAB_SIDEBAR_QSS = """
QTabWidget::pane {
    border: none;
    background: transparent;
}
QTabBar {
    background: transparent;
}
QTabBar::tab {
    background: transparent;
    color: #475569;
    padding: 14px 0px;
    margin: 2px 0;
    border: none;
    border-left: 3px solid transparent;
    font-size: 12px;
    font-weight: 500;
    text-align: left;
}
QTabBar::tab:selected {
    color: #06b6d4;
    border-left: 3px solid #06b6d4;
    background: rgba(6,182,212,0.06);
    font-weight: 600;
}
QTabBar::tab:hover:!selected {
    color: #94a3b8;
    background: rgba(255,255,255,0.03);
}
"""


TAB_TOP_QSS = """
QTabWidget::pane {
    border: none;
    background: transparent;
    margin-top: 0;
}
QTabBar {
    background: transparent;
}
QTabBar::tab {
    background: transparent;
    color: #475569;
    padding: 10px 18px;
    margin-right: 2px;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 12px;
    font-weight: 500;
}
QTabBar::tab:selected {
    color: #06b6d4;
    border-bottom: 2px solid #06b6d4;
    font-weight: 600;
}
QTabBar::tab:hover:!selected { color: #94a3b8; }
"""


class SidebarNav(QFrame):
    tab_changed = pyqtSignal(int)
    tool_requested = pyqtSignal(int)

    PRIMARY_ITEMS = [
        ("🏠", "Início", "inicio"),
        ("🎲", "Gerador", "gerador"),
        ("⚙️", "Config", "config"),
    ]
    FEATURE_ITEMS = [
        ("🌐", "Navegador", "navegador"),
        ("🤖", "IA Local", "ia"),
        ("🍦", "Crunchyroll", "crunchyroll"),
        ("📝", "Notas", "notas"),
    ]
    TOOL_ITEMS = [
        ("💳", "Cartões", 0),
        ("🏠", "CEP", 1),
        ("📧", "Organizador", 2),
        ("🗂️", "Formatar", 3),
        ("✅", "CPF/CNPJ", 4),
        ("⚡", "Desempenho", 5),
        ("🧹", "Dados Pro", 6),
        ("✍️", "Português", 7),
        ("P+", "Paramount", 8),
        ("@", "Codigos", 9),
        ("BO", "Leads Site", 10),
        ("TM", "Email Temp", 11),
    ]
    SLIM_W = 56
    FULL_W = 156

    def __init__(self, parent=None, show_crunchyroll=True):
        super().__init__(parent)
        self.page_indices = self._build_page_indices(show_crunchyroll)
        self.nav_items = [
            (icon, label, self.page_indices[key])
            for icon, label, key in self.PRIMARY_ITEMS
            if key in self.page_indices
        ]
        self.feature_items = [
            (icon, label, self.page_indices[key])
            for icon, label, key in self.FEATURE_ITEMS
            if key in self.page_indices and (show_crunchyroll or key != "crunchyroll")
        ]
        self._slim = False
        self._current = 0
        self._buttons = []
        self._button_tabs = []
        self._apply_width()
        self.setStyleSheet(
            "QFrame{background-color:#08111f;"
            "border-right:1px solid rgba(125,211,252,0.10);}"
        )
        self._build()

    @staticmethod
    def _build_page_indices(show_crunchyroll):
        indices = {
            "inicio": 0,
            "gerador": 1,
            "navegador": 2,
            "ia": 3,
        }
        next_idx = 4
        if show_crunchyroll:
            indices["crunchyroll"] = next_idx
            next_idx += 1
        indices["notas"] = next_idx
        indices["config"] = next_idx + 1
        indices["ferramentas"] = next_idx + 2
        return indices

    def _apply_width(self):
        self.setFixedWidth(self.SLIM_W if self._slim else self.FULL_W)

    def _build(self):
        # Clear old layout
        old = self.layout()
        if old:
            while old.count():
                item = old.takeAt(0)
                w = item.widget()
                if w:
                    w.setParent(None)
            QWidget().setLayout(old)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(8, 10, 8, 10)
        lay.setSpacing(4)

        logo = QLabel("TC" if self._slim else "Telegram Pro")
        logo.setAlignment(Qt.AlignCenter)
        logo.setFixedHeight(38)
        logo.setStyleSheet(
            "color:#e0f2fe;font-size:13px;font-weight:800;"
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0e7490,stop:1 #155e75);"
            "border-radius:10px;border:1px solid rgba(125,211,252,0.22);"
        )
        lay.addWidget(logo)
        lay.addSpacing(4)

        self._buttons = []
        self._button_tabs = []
        for icon, label, tab_idx in self.nav_items:
            btn = self._make_nav_btn(icon, label, tab_idx)
            self._buttons.append(btn)
            self._button_tabs.append(tab_idx)
            lay.addWidget(btn)

        lay.addSpacing(8)
        if not self._slim:
            tools_lbl = QLabel("FERRAMENTAS")
            tools_lbl.setStyleSheet(
                "color:#475569;font-size:10px;font-weight:800;"
                "letter-spacing:1px;background:transparent;border:none;"
                "padding:2px 4px;"
            )
            lay.addWidget(tools_lbl)
        for icon, label, tab_idx in self.feature_items:
            btn = self._make_nav_btn(icon, label, tab_idx, small=True)
            self._buttons.append(btn)
            self._button_tabs.append(tab_idx)
            lay.addWidget(btn)
        if self.feature_items:
            lay.addSpacing(4)
        for icon, label, tab_idx in self.TOOL_ITEMS:
            lay.addWidget(self._make_tool_btn(icon, label, tab_idx))

        lay.addStretch()

        self._pin_btn     = self._make_ctrl_btn("📌", "Fixar no topo (sempre visível)")
        self._fs_btn      = self._make_ctrl_btn("⛶", "Tela cheia  —  F11")
        self._compact_btn = self._make_ctrl_btn("▣", "Modo compacto flutuante")
        for b in (self._pin_btn, self._fs_btn, self._compact_btn):
            lay.addWidget(b)

        self._set_active(self._current)

    def _make_nav_btn(self, icon, label, idx, small=False):
        w = self.SLIM_W - 16 if self._slim else self.FULL_W - 16
        h = 28 if small else 38
        if self._slim:
            btn = QPushButton(icon)
            btn.setFixedSize(w, h)
        else:
            btn = QPushButton(f"{icon}  {label}")
            btn.setFixedSize(w, h)
        btn.setToolTip(label)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _, i=idx: self._on_click(i))
        btn.setStyleSheet(self._inactive_qss())
        return btn

    def _make_ctrl_btn(self, icon, tip):
        w = self.SLIM_W - 16 if self._slim else self.FULL_W - 16
        btn = QPushButton(icon)
        btn.setFixedSize(w, 28)
        btn.setToolTip(tip)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(
            "QPushButton{background:rgba(148,163,184,0.04);color:#64748b;"
            "border:1px solid rgba(148,163,184,0.08);"
            "border-radius:8px;font-size:14px;}"
            "QPushButton:hover{background:rgba(6,182,212,0.12);color:#7dd3fc;"
            "border-color:rgba(125,211,252,0.24);}"
            "QPushButton:checked{color:#f43f5e;}"
        )
        return btn

    def _make_tool_btn(self, icon, label, tab_idx):
        w = self.SLIM_W - 16 if self._slim else self.FULL_W - 16
        text = icon if self._slim else f"{icon}  {label}"
        btn = QPushButton(text)
        btn.setFixedSize(w, 28)
        btn.setToolTip(label)
        btn.setCursor(Qt.PointingHandCursor)
        btn.clicked.connect(lambda _, i=tab_idx: self.tool_requested.emit(i))
        if self._slim:
            btn.setStyleSheet(
                "QPushButton{background:rgba(148,163,184,0.035);color:#64748b;"
                "border:1px solid rgba(148,163,184,0.07);border-radius:8px;"
                "font-size:14px;}"
                "QPushButton:hover{background:rgba(6,182,212,0.12);"
                "color:#7dd3fc;border-color:rgba(125,211,252,0.22);}"
            )
        else:
            btn.setStyleSheet(
                "QPushButton{background:rgba(148,163,184,0.035);color:#7c8da3;"
                "border:1px solid rgba(148,163,184,0.07);border-radius:8px;"
                "font-size:11px;font-weight:600;text-align:left;padding:2px 9px;}"
                "QPushButton:hover{background:rgba(6,182,212,0.12);"
                "color:#e0f2fe;border-color:rgba(125,211,252,0.22);}"
            )
        return btn

    def _inactive_qss(self):
        if self._slim:
            return ("QPushButton{background:transparent;color:#475569;border:none;"
                    "border-radius:9px;font-size:17px;padding:2px 0;}"
                    "QPushButton:hover{background:rgba(6,182,212,0.07);color:#94a3b8;}")
        return ("QPushButton{background:transparent;color:#94a3b8;"
                "border:1px solid transparent;border-radius:9px;font-size:12px;"
                "padding:2px 10px;"
                "text-align:left;}"
                "QPushButton:hover{background:rgba(6,182,212,0.08);"
                "color:#e0f2fe;border-color:rgba(125,211,252,0.14);}")

    def _active_qss(self):
        if self._slim:
            return ("QPushButton{background:rgba(6,182,212,0.13);color:#06b6d4;"
                    "border:1px solid rgba(6,182,212,0.26);border-radius:9px;"
                    "font-size:17px;font-weight:700;padding:2px 0;}")
        return ("QPushButton{background:rgba(6,182,212,0.15);color:#67e8f9;"
                "border:1px solid rgba(125,211,252,0.30);border-radius:9px;"
                "font-size:12px;font-weight:700;padding:2px 10px;"
                "text-align:left;}")

    def _on_click(self, idx):
        self._set_active(idx)
        self.tab_changed.emit(idx)

    def _set_active(self, idx):
        for tab_idx, btn in zip(self._button_tabs, self._buttons):
            btn.setStyleSheet(self._active_qss() if tab_idx == idx else self._inactive_qss())
        self._current = idx

    def set_current(self, idx):
        self._set_active(idx)

    def set_collapsed(self, slim: bool):
        if slim == self._slim:
            return
        self._slim = slim
        self._apply_width()
        self._build()

    @property
    def pin_btn(self): return self._pin_btn
    @property
    def fs_btn(self): return self._fs_btn
    @property
    def compact_btn(self): return self._compact_btn


class HeaderBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setStyleSheet("""
            QFrame {
                background-color: #08111f;
                border-bottom: 1px solid rgba(125,211,252,0.10);
            }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(18, 0, 16, 0)
        lay.setSpacing(10)

        self.title_lbl = QLabel("🏠  Painel Inicial")
        self.title_lbl.setStyleSheet(
            "color:#f8fafc; font-size:15px; font-weight:700;"
            " background:transparent; border:none; min-width:180px;"
        )
        lay.addWidget(self.title_lbl)
        lay.addStretch()

        # Stats individuais como mini-badges (se escondem se pequeno)
        self._stat_widgets = []
        stat_defs = [
            ("📋", "#94a3b8"), ("✅", "#10b981"), ("📅", "#8b5cf6"),
            ("📞", "#f43f5e"), ("⭐", "#f59e0b"),
        ]
        for icon, color in stat_defs:
            lbl = QLabel(f"{icon} —")
            lbl.setStyleSheet(
                f"color:{color}; font-size:11px; font-weight:700;"
                " background:rgba(148,163,184,0.055);"
                " border:1px solid rgba(148,163,184,0.10);"
                " border-radius:8px; padding:5px 8px;"
            )
            lbl.setMinimumWidth(48)
            lay.addWidget(lbl)
            self._stat_widgets.append(lbl)

    def set_title(self, text):
        self.title_lbl.setText(text)

    def set_stats(self, text):
        # Extrai números do texto de stats para badges individuais
        import re
        nums = re.findall(r"\d+", text)
        for i, w in enumerate(self._stat_widgets):
            parts = w.text().split()
            icon = parts[0] if parts else ""
            val = nums[i] if i < len(nums) else "—"
            w.setText(f"{icon} {val}")

    def resizeEvent(self, event):
        """Esconde badges de stats progressivamente conforme janela encolhe."""
        super().resizeEvent(event)
        w = event.size().width()
        for i, lbl in enumerate(self._stat_widgets):
            # Esconde os últimos badges primeiro
            threshold = 400 + i * 60
            lbl.setVisible(w > threshold)


class AppStatusBar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(28)
        self.setStyleSheet("""
            QFrame {
                background-color: #08111f;
                border-top: 1px solid rgba(125,211,252,0.10);
            }
        """)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(16, 0, 16, 0)
        lay.setSpacing(16)

        self._msg = QLabel("✅ Pronto")
        self._msg.setStyleSheet("color:#94a3b8; font-size:11px; background:transparent; border:none;")
        lay.addWidget(self._msg)

        lay.addStretch()

        self._version = QLabel(APP_VERSION_LABEL)
        self._version.setStyleSheet("color:#38bdf8; font-size:10px; font-weight:700; background:transparent; border:none;")
        lay.addWidget(self._version)

    def showMessage(self, text, timeout=0):
        self._msg.setText(text)
        if timeout > 0:
            QTimer.singleShot(timeout, lambda: self._msg.setText("✅ Pronto"))


class CompactWidget(QFrame):
    """Painel compacto lateral focado em nome, idade, score e cidade."""

    UF_NAMES = {
        "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
        "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
        "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
        "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
        "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
        "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
        "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins",
    }

    def __init__(self, db, address_gen, parent=None):
        super().__init__(None)
        self._main_window = parent
        self.db = db
        self.address_gen = address_gen
        self._current_pair = None
        self._drag_pos = None

        QApplication.setQuitOnLastWindowClosed(False)
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setAttribute(Qt.WA_QuitOnClose, False)
        self.setAttribute(Qt.WA_DeleteOnClose, False)
        self.setFixedSize(360, 590)
        self._build()

    def _build(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(8, 8, 8, 8)
        outer.setSpacing(0)

        # Container com sombra simulada via borda
        container = QFrame()
        container.setObjectName("compact_container")
        container.setStyleSheet("""
            QFrame#compact_container {
                background-color: #08111f;
                border: 1px solid rgba(125,211,252,0.28);
                border-radius: 18px;
            }
        """)
        c_lay = QVBoxLayout(container)
        c_lay.setContentsMargins(0, 0, 0, 0)
        c_lay.setSpacing(0)

        # ── Header arrastável
        hdr = QFrame()
        hdr.setFixedHeight(46)
        hdr.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #0e7490,stop:1 #155e75);
                border-radius: 18px 18px 0 0;
                border-bottom: 1px solid rgba(125,211,252,0.20);
            }
        """)
        hdr_lay = QHBoxLayout(hdr)
        hdr_lay.setContentsMargins(12, 0, 8, 0)
        title = QLabel("Painel Compacto")
        title.setStyleSheet("color:#e0f2fe; font-size:13px; font-weight:900; background:transparent; border:none;")
        hdr_lay.addWidget(title)
        hdr_lay.addStretch()
        restore_btn = QPushButton("↗")
        restore_btn.setFixedSize(30, 30)
        restore_btn.setToolTip("Mostrar janela principal")
        restore_btn.setStyleSheet("""
            QPushButton {
                background: rgba(224,242,254,0.14);
                color: #e0f2fe;
                border: 1px solid rgba(224,242,254,0.20);
                border-radius: 9px;
                font-size: 13px;
                font-weight: 800;
            }
            QPushButton:hover { background: rgba(224,242,254,0.24); }
        """)
        restore_btn.clicked.connect(self._restore_main)
        hdr_lay.addWidget(restore_btn)
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                background: rgba(244,63,94,0.15);
                color: #f43f5e;
                border: none;
                border-radius: 9px;
                font-size: 12px;
                font-weight: 700;
            }
            QPushButton:hover { background: #f43f5e; color: white; }
        """)
        close_btn.setToolTip("Fechar painel compacto e voltar ao app")
        close_btn.clicked.connect(self._close_compact)
        hdr_lay.addWidget(close_btn)
        hdr.mousePressEvent = self._drag_start
        hdr.mouseMoveEvent = self._drag_move
        c_lay.addWidget(hdr)

        # Conteudo fixo: sem scroll, tudo visivel no painel.
        body = QWidget()
        body.setStyleSheet("background: transparent;")
        b_lay = QVBoxLayout(body)
        b_lay.setContentsMargins(10, 8, 10, 10)
        b_lay.setSpacing(6)

        self._status = QLabel("Pronto")
        self._status.setStyleSheet(
            "color:#94a3b8;font-size:11px;background:rgba(148,163,184,0.06);"
            "border:1px solid rgba(148,163,184,0.10);border-radius:8px;padding:7px 9px;"
        )
        b_lay.addWidget(self._status)

        # ── Seção Pares
        b_lay.addWidget(self._section_header("Gerador de Pares"))
        self._fields = {}
        for key, icon_txt in [("nome","Nome"), ("cpf","CPF"), ("idade","Idade"), ("score","Score")]:
            f = QLineEdit()
            f.setReadOnly(True)
            f.setPlaceholderText("—")
            f.setFixedHeight(30 if key != "nome" else 34)
            f.setStyleSheet("""
                QLineEdit {
                    background: #0f1626;
                    border: 1px solid rgba(6,182,212,0.12);
                    border-radius: 6px;
                    color: #22d3ee;
                    font-size: 11px;
                    padding: 3px 8px;
                    font-family: 'Consolas', monospace;
                }
            """)
            self._fields[key] = f
            row = _field_row(icon_txt, f, lambda v=f, label=icon_txt: self._copy_field(label, v))
            b_lay.addLayout(row)

        # Botões pares
        pair_btns = QHBoxLayout()
        pair_btns.setSpacing(6)
        gen_btn = QPushButton("Gerar")
        gen_btn.setFixedHeight(32)
        gen_btn.setStyleSheet("QPushButton{background:#059669;color:white;border:none;"
                              "border-radius:7px;font-size:12px;font-weight:700;}"
                              "QPushButton:hover{background:#047857;}")
        gen_btn.clicked.connect(self._gen_pair)
        copy_all = QPushButton("Copiar")
        copy_all.setFixedHeight(32)
        copy_all.setStyleSheet("QPushButton{background:#0891b2;color:white;border:none;"
                               "border-radius:7px;font-size:12px;font-weight:700;}"
                               "QPushButton:hover{background:#0e7490;}")
        copy_all.clicked.connect(self._copy_pair)
        pair_btns.addWidget(gen_btn)
        pair_btns.addWidget(copy_all)
        b_lay.addLayout(pair_btns)

        b_lay.addWidget(_separator())

        # ── Seção CEP
        b_lay.addWidget(self._section_header("Cidade / Estado"))

        self._cep_estado = QComboBox()
        self._cep_estado.addItem("Todos os Estados", None)
        for uf, nome in self.UF_NAMES.items():
            self._cep_estado.addItem(f"{uf} — {nome}", uf)
        self._cep_estado.setFixedHeight(30)
        self._cep_estado.setStyleSheet("""
            QComboBox {
                background: #0f1626;
                border: 1px solid rgba(6,182,212,0.12);
                border-radius: 6px;
                color: #f1f5f9;
                font-size: 11px;
                padding: 3px 8px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #131d2e;
                border: 1px solid rgba(6,182,212,0.2);
                color: #f1f5f9;
                selection-background-color: rgba(6,182,212,0.2);
            }
        """)
        b_lay.addWidget(self._cep_estado)

        self._cep_fields = {}
        for key, icon_txt in [("endereco","Endereço"),("cidade","Cidade"),("estado","Estado"),("cep","CEP")]:
            f = QLineEdit()
            f.setReadOnly(True)
            f.setPlaceholderText("—")
            f.setFixedHeight(30)
            f.setStyleSheet("""
                QLineEdit {
                    background: #0f1626;
                    border: 1px solid rgba(6,182,212,0.12);
                    border-radius: 6px;
                    color: #10b981;
                    font-size: 11px;
                    padding: 3px 8px;
                    font-family: 'Consolas', monospace;
                }
            """)
            self._cep_fields[key] = f
            row = _field_row(icon_txt, f, lambda v=f, label=icon_txt: self._copy_field(label, v))
            b_lay.addLayout(row)

        cep_btns = QHBoxLayout()
        cep_btns.setSpacing(6)
        cep_gen = QPushButton("Gerar cidade")
        cep_gen.setFixedHeight(32)
        cep_gen.setStyleSheet("QPushButton{background:#0891b2;color:white;border:none;"
                              "border-radius:7px;font-size:12px;font-weight:700;}"
                              "QPushButton:hover{background:#0e7490;}")
        cep_gen.clicked.connect(self._gen_cep)
        cep_copy = QPushButton("Copiar")
        cep_copy.setFixedHeight(32)
        cep_copy.setStyleSheet("QPushButton{background:#7c3aed;color:white;border:none;"
                               "border-radius:7px;font-size:12px;font-weight:700;}"
                               "QPushButton:hover{background:#6d28d9;}")
        cep_copy.clicked.connect(self._copy_cep)
        cep_btns.addWidget(cep_gen)
        cep_btns.addWidget(cep_copy)
        b_lay.addLayout(cep_btns)

        b_lay.addStretch()
        c_lay.addWidget(body, 1)

        outer.addWidget(container)

    def _section_header(self, text):
        l = QLabel(text)
        l.setStyleSheet("color:#06b6d4; font-size:11px; font-weight:900; background:transparent; border:none; padding:1px 0;")
        return l

    def _state_name(self, uf, fallback=""):
        uf = (uf or "").strip().upper()
        return self.UF_NAMES.get(uf) or fallback or uf

    def _set_status(self, text, color="#94a3b8"):
        self._status.setText(text)
        self._status.setStyleSheet(
            f"color:{color};font-size:11px;background:rgba(148,163,184,0.06);"
            "border:1px solid rgba(148,163,184,0.10);border-radius:8px;padding:7px 9px;"
        )

    def _keep_app_alive(self):
        QApplication.setQuitOnLastWindowClosed(False)

    def _copy_text(self, text, status="Copiado"):
        try:
            self._keep_app_alive()
            text = text or ""
            if not text.strip():
                self._set_status("Nada para copiar", "#f59e0b")
                return
            _set_clipboard_text_safe(text)
            self._set_status(status, "#10b981")
            if not self.isVisible():
                self.show()
            self.raise_()
        except Exception as exc:
            _log_compact_error("copiar texto do painel compacto", exc)
            self._set_status("Erro ao copiar; veja _temp/compact_panel_errors.log", "#f43f5e")

    def _copy_field(self, label, field):
        self._copy_text(field.text(), f"{label} copiado")

    def _main(self):
        return self._main_window or self.parent()

    def _restore_main(self):
        parent = self._main()
        if parent:
            self.hide()
            if hasattr(parent, "is_compact_mode"):
                parent.is_compact_mode = False
            QApplication.setQuitOnLastWindowClosed(True)
            parent.showNormal()
            parent.activateWindow()
            parent.raise_()
        self._set_status("Janela principal aberta", "#7dd3fc")

    def _close_compact(self):
        parent = self._main()
        self.hide()
        if parent:
            if hasattr(parent, "is_compact_mode"):
                parent.is_compact_mode = False
            QApplication.setQuitOnLastWindowClosed(True)
            parent.showNormal()
            parent.activateWindow()
            parent.raise_()

    def closeEvent(self, event):
        """Nunca deixa o painel compacto encerrar o QApplication sozinho."""
        try:
            self._keep_app_alive()
            event.ignore()
            self._close_compact()
        except Exception as exc:
            _log_compact_error("fechar painel compacto", exc)
            event.ignore()

    def _open_tool(self, tab_idx):
        parent = self._main()
        if parent and hasattr(parent, "show_tools_tab"):
            parent.showNormal()
            parent.show_tools_tab(tab_idx)
            parent.activateWindow()
            parent.raise_()
            self._set_status("Ferramenta aberta na janela principal", "#7dd3fc")

    def _open_notes(self):
        parent = self._main()
        if parent and hasattr(parent, "open_notes_page"):
            parent.showNormal()
            parent.open_notes_page()
            parent.activateWindow()
            parent.raise_()
            self._set_status("Notas abertas", "#7dd3fc")

    def _open_config(self):
        parent = self._main()
        if parent and hasattr(parent, "open_page_by_name"):
            parent.showNormal()
            parent.open_page_by_name("Config")
            parent.activateWindow()
            parent.raise_()
            self._set_status("Config/Backup aberto", "#7dd3fc")
        elif parent and hasattr(parent, "main_tabs"):
            notes_idx = parent.main_tabs.count() - 1
            parent.showNormal()
            parent.main_tabs.setCurrentIndex(notes_idx)
            parent.sidebar.set_current(notes_idx)
            parent.header.set_title(parent.tab_titles[notes_idx] if notes_idx < len(parent.tab_titles) else "📝  Bloco de Notas")
            parent.activateWindow()
            parent.raise_()
            self._set_status("Notas abertas", "#7dd3fc")

    def _gen_pair(self):
        pair = self.db.get_random_pair({"require_birth": True, "idade_max": 59})
        if pair:
            self._current_pair = pair
            self._fields["nome"].setText(pair.get("nome", ""))
            self._fields["cpf"].setText(pair.get("cpf", ""))
            self._fields["idade"].setText(str(pair.get("idade", "")) + " anos" if pair.get("idade") else "")
            self._fields["score"].setText(str(pair.get("score", "")))
            self._set_status("Par gerado com sucesso", "#10b981")
        else:
            self._set_status("Nenhum registro encontrado", "#f59e0b")

    def _copy_pair(self):
        if not self._current_pair:
            return
        p = self._current_pair
        lines = []
        if p.get("nome"): lines.append(f"👤 {p['nome']}")
        if p.get("cpf"):  lines.append(f"🆔 {p['cpf']}")
        if p.get("idade"): lines.append(f"🎂 {p['idade']} anos")
        if p.get("nascimento"): lines.append(f"📅 {p['nascimento']}")
        if p.get("telefone"): lines.append(f"📞 {p['telefone']}")
        if p.get("score"): lines.append(f"⭐ {p['score']}")
        self._copy_text("\n".join(lines), "Par copiado")

    def _gen_cep(self):
        try:
            uf = self._cep_estado.currentData()
            end = self.address_gen.gerar_endereco(uf, None, True)
            if end:
                estado_nome = self._state_name(end.uf, getattr(end, "estado", ""))
                endereco_linha = end.logradouro
                if getattr(end, "bairro", ""):
                    endereco_linha = f"{endereco_linha} - {end.bairro}" if endereco_linha else end.bairro
                self._cep_fields["endereco"].setText(endereco_linha)
                self._cep_fields["cep"].setText(end.cep)
                self._cep_fields["cidade"].setText(end.cidade)
                self._cep_fields["estado"].setText(estado_nome)
                if getattr(self.address_gen, "last_source", "") == "reserva":
                    self._set_status("Cidade reserva usada", "#fbbf24")
                else:
                    self._set_status("Cidade gerada", "#10b981")
        except Exception as e:
            _log_compact_error("gerar CEP no painel compacto", e)
            self._set_status(f"Erro ao gerar CEP: {e}", "#f43f5e")

    def _copy_cep(self):
        try:
            parts = [
                self._cep_fields["endereco"].text(),
                self._cep_fields["cidade"].text(),
                self._cep_fields["estado"].text(),
                f"CEP: {self._cep_fields['cep'].text()}",
            ]
            self._copy_text("\n".join(p for p in parts if p), "Endereço copiado")
        except Exception as e:
            _log_compact_error("copiar CEP no painel compacto", e)
            self._set_status("Erro ao copiar CEP", "#f43f5e")

    # Drag para mover janela
    def _drag_start(self, ev):
        if ev.button() == Qt.LeftButton:
            self._drag_pos = ev.globalPos() - self.frameGeometry().topLeft()

    def _drag_move(self, ev):
        if ev.buttons() == Qt.LeftButton and self._drag_pos:
            self.move(ev.globalPos() - self._drag_pos)

    def update_db(self, db):
        self.db = db
