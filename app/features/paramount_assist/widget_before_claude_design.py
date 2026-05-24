#!/usr/bin/env python3
"""Paramount Assist: fila segura para contas, perfis e preenchimento visivel."""

from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt
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
)

from app.core.paths import BASE_DIR
from app.core.clipboard_service import set_clipboard_text

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


def _now() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _make_id(prefix: str, seed: str = "") -> str:
    raw = f"{prefix}:{seed}:{_now()}".encode("utf-8", errors="ignore")
    return hashlib.sha1(raw).hexdigest()[:12]


def _digits(value: str) -> str:
    return re.sub(r"\D", "", str(value or ""))


class ParamountAssistWidget(QWidget):
    """Central focada em Paramount, sem automatizar compra ou teste de cartao."""

    DATA_FILE = BASE_DIR / "browser_config" / "paramount_assist.json"
    STATUSES = [
        "novo",
        "perfil pronto",
        "login ok",
        "precisa verificar",
        "bloqueio/403",
        "assinatura ativa",
        "cartao recusado manual",
        "pausado",
    ]

    def __init__(self, browser_manager: Optional[BrowserManager] = None, parent=None):
        super().__init__(parent)
        self.browser_manager = browser_manager or BrowserManager()
        self.address_generator = AddressGenerator() if AddressGenerator else None
        self.address_reserve = AddressExtractor() if AddressExtractor else None
        self.db = DatabaseManager() if DatabaseManager else None
        self.launch_threads: Dict[str, BrowserLaunchThread] = {}
        self.current_account_id = ""
        self.data = {"accounts": [], "cards": [], "logs": [], "settings": {}}
        self._build()
        self.load_data()
        self.refresh_all()

    def _build(self):
        self.setStyleSheet("""
            QWidget { background:#07080f; color:#e5e7eb; font-family:'Segoe UI', Arial, sans-serif; font-size:12px; }
            QLabel { background:transparent; border:none; }
            QFrame#Header, QFrame#Panel, QGroupBox {
                background:#0b1220; border:1px solid rgba(34,211,238,0.14); border-radius:14px;
            }
            QGroupBox { margin-top:14px; padding:12px; padding-top:28px; }
            QGroupBox::title { color:#67e8f9; left:12px; top:4px; font-weight:900; }
            QLineEdit, QTextEdit, QComboBox {
                background:#08111f; color:#e5e7eb; border:1px solid rgba(148,163,184,0.18);
                border-radius:9px; padding:8px; selection-background-color:#0e7490;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus { border-color:rgba(34,211,238,0.55); }
            QPushButton {
                background:#111827; color:#e5e7eb; border:1px solid rgba(148,163,184,0.20);
                border-radius:9px; padding:8px 12px; font-weight:800;
            }
            QPushButton:hover { background:#172033; border-color:rgba(34,211,238,0.40); }
            QPushButton#Primary { background:#0891b2; color:#ecfeff; border-color:rgba(103,232,249,0.55); }
            QPushButton#Success { background:#0f9f74; color:#ecfdf5; border-color:rgba(16,185,129,0.55); }
            QPushButton#Danger { background:#7f1d1d; color:#fee2e2; border-color:rgba(248,113,113,0.45); }
            QPushButton#Soft { background:#0b1220; color:#bae6fd; border-color:rgba(125,211,252,0.22); }
            QTableWidget {
                background:#08111f; color:#e5e7eb; gridline-color:rgba(148,163,184,0.08);
                border:1px solid rgba(148,163,184,0.12); border-radius:10px;
            }
            QTableWidget::item { padding:6px; }
            QTableWidget::item:selected { background:#0e7490; color:white; }
            QHeaderView::section {
                background:#0f172a; color:#93c5fd; border:none; padding:7px; font-weight:900;
            }
            QTabWidget::pane { border:0; margin-top:8px; }
            QTabBar::tab {
                background:#0b1220; color:#cbd5e1; border:1px solid rgba(148,163,184,0.16);
                padding:9px 16px; margin-right:6px; border-radius:10px; font-weight:900;
            }
            QTabBar::tab:selected { background:#0e7490; color:#ecfeff; border-color:rgba(103,232,249,0.60); }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(12)
        root.addWidget(self._header())

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        root.addWidget(splitter, 1)

        left = QFrame()
        left.setObjectName("Panel")
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(12, 12, 12, 12)
        left_lay.setSpacing(8)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Buscar email ou senha...")
        self.search_input.textChanged.connect(self.refresh_accounts_table)
        left_lay.addWidget(self.search_input)

        self.accounts_table = QTableWidget(0, 2)
        self.accounts_table.setHorizontalHeaderLabels(["Email", "Senha"])
        self.accounts_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.accounts_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.accounts_table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.accounts_table.itemSelectionChanged.connect(self.on_account_selected)
        self.accounts_table.cellDoubleClicked.connect(lambda *_: self.open_profile_only_for_current())
        left_lay.addWidget(self.accounts_table, 1)

        self.selected_hint = QLabel("Selecione uma conta para abrir ou continuar.")
        self.selected_hint.setWordWrap(True)
        self.selected_hint.setStyleSheet(
            "color:#93c5fd;background:#08111f;border:1px solid rgba(34,211,238,0.12);"
            "border-radius:8px;padding:7px;"
        )
        left_lay.addWidget(self.selected_hint)

        left_buttons = QGridLayout()
        for text, cb, row, col, obj in [
            ("Colar emails", self.import_accounts_dialog, 0, 0, "Primary"),
            ("Abrir perfil", self.open_profile_only_for_current, 0, 1, "Soft"),
            ("Continuar", self.smart_continue_for_current, 0, 2, "Success"),
            ("Copiar", self.copy_selected_account_login, 1, 0, "Soft"),
            ("Proxima", self.select_next_account, 1, 1, "Soft"),
            ("Salvar", self.save_current_account, 1, 2, "Primary"),
            ("Remover", self.remove_selected_accounts, 2, 0, "Danger"),
            ("Importar .txt", self.import_accounts_file, 2, 1, "Soft"),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.clicked.connect(cb)
            left_buttons.addWidget(btn, row, col, 1, 2 if text == "Importar .txt" else 1)
        left_lay.addLayout(left_buttons)
        splitter.addWidget(left)

        self.tabs = QTabWidget()
        self.tabs.addTab(self._flow_tab(), "Fluxo")
        self.tabs.addTab(self._address_tab(), "Enderecos")
        self.tabs.addTab(self._cards_tab(), "Cartoes")
        self.tabs.addTab(self._help_tab(), "Ajuda e logs")
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([420, 980])

    def _header(self):
        frame = QFrame()
        frame.setObjectName("Header")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(16, 12, 16, 12)
        title_box = QVBoxLayout()
        title = QLabel("Paramount Assist")
        title.setStyleSheet("font-size:22px;font-weight:900;color:#f8fafc;")
        sub = QLabel("Central segura para contas, perfis, enderecos e fluxo visivel da Paramount.")
        sub.setStyleSheet("color:#94a3b8;")
        title_box.addWidget(title)
        title_box.addWidget(sub)
        lay.addLayout(title_box, 1)

        self.summary_label = QLabel("0 contas")
        self.summary_label.setAlignment(Qt.AlignCenter)
        self.summary_label.setMinimumWidth(180)
        self.summary_label.setStyleSheet(
            "background:#08111f;color:#67e8f9;border:1px solid rgba(34,211,238,0.22);"
            "border-radius:12px;padding:12px;font-weight:900;"
        )
        lay.addWidget(self.summary_label)
        return frame

    def _flow_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        quick = QGroupBox("Comece aqui")
        quick_lay = QVBoxLayout(quick)
        quick_hint = QLabel(
            "Use estes passos na ordem. O resto da tela fica para ajuste fino, histórico e correções."
        )
        quick_hint.setWordWrap(True)
        quick_hint.setStyleSheet("color:#bae6fd;font-weight:800;padding:2px 0 8px 0;")
        quick_lay.addWidget(quick_hint)

        quick_grid = QGridLayout()
        quick_defs = [
            ("Continuar fluxo automatico", self.smart_continue_for_current, 0, 0, "Success"),
            ("Abrir perfil sem automacao", self.open_profile_only_for_current, 0, 1, "Soft"),
            ("Colar emails/senhas", self.import_accounts_dialog, 0, 2, "Primary"),
        ]
        for text, cb, row, col, obj in quick_defs:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.setMinimumHeight(42)
            btn.clicked.connect(cb)
            quick_grid.addWidget(btn, row, col)
        quick_lay.addLayout(quick_grid)
        lay.addWidget(quick)

        account_group = QGroupBox("Conta selecionada")
        form = QGridLayout(account_group)
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("email@exemplo.com")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha da conta ou senha a usar no cadastro")
        self.status_combo = QComboBox()
        self.status_combo.addItems(self.STATUSES)
        self.profile_combo = QComboBox()
        self.profile_combo.setMinimumWidth(240)
        self.plan_combo = QComboBox()
        self.plan_combo.setEditable(True)
        self.plan_combo.addItems(PLAN_OPTIONS)
        self.plan_combo.setToolTip("Texto do plano a procurar na pagina. Pode escrever outro nome se o site mudar.")
        self.person_name_input = QLineEdit()
        self.person_name_input.setPlaceholderText("Gerado pelo banco do projeto")
        self.person_cpf_input = QLineEdit()
        self.person_cpf_input.setPlaceholderText("CPF do projeto")
        self.person_birth_input = QLineEdit()
        self.person_birth_input.setPlaceholderText("Nascimento")
        for person_input in [self.person_name_input, self.person_cpf_input, self.person_birth_input]:
            person_input.setReadOnly(True)
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Observacoes, erro visto, etapa parada, etc.")
        self.notes_input.setMinimumHeight(90)
        form.addWidget(QLabel("Email:"), 0, 0)
        form.addWidget(self.email_input, 0, 1)
        form.addWidget(QLabel("Senha:"), 0, 2)
        form.addWidget(self.password_input, 0, 3)
        form.addWidget(QLabel("Status:"), 1, 0)
        form.addWidget(self.status_combo, 1, 1)
        form.addWidget(QLabel("Perfil:"), 1, 2)
        form.addWidget(self.profile_combo, 1, 3)
        form.addWidget(QLabel("Plano:"), 2, 0)
        form.addWidget(self.plan_combo, 2, 1, 1, 3)
        form.addWidget(QLabel("Nome:"), 3, 0)
        form.addWidget(self.person_name_input, 3, 1)
        form.addWidget(QLabel("CPF/Nasc.:"), 3, 2)
        person_doc_row = QHBoxLayout()
        person_doc_row.addWidget(self.person_cpf_input, 2)
        person_doc_row.addWidget(self.person_birth_input, 1)
        form.addLayout(person_doc_row, 3, 3)
        form.addWidget(QLabel("Notas:"), 4, 0)
        form.addWidget(self.notes_input, 4, 1, 1, 3)
        lay.addWidget(account_group)

        actions = QGroupBox("Ajustes manuais")
        grid = QGridLayout(actions)
        action_defs = [
            ("Abrir cadastro", self.open_signup_for_current, 0, 0, "Primary"),
            ("Preencher cadastro", self.fill_signup_for_current, 0, 1, "Success"),
            ("Selecionar plano", self.quick_select_plan, 0, 2, "Soft"),
            ("CPF + endereco", self.fill_cpf_address_for_current, 0, 3, "Success"),
        ]
        for text, cb, row, col, obj in action_defs:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.clicked.connect(cb)
            grid.addWidget(btn, row, col)
        lay.addWidget(actions)

        steps = QGroupBox("Como usar")
        steps_lay = QVBoxLayout(steps)
        for text in [
            "Cole email:senha, selecione a conta e use Continuar fluxo automatico.",
            "A ferramenta tenta abrir, preencher, clicar em continuar, selecionar plano e preencher CPF/endereco.",
            "Ela para antes de pagamento/compra final para voce conferir manualmente.",
        ]:
            label = QLabel(text)
            label.setStyleSheet("color:#cbd5e1;padding:4px 0;")
            steps_lay.addWidget(label)
        lay.addWidget(steps)
        lay.addStretch()
        return page

    def _address_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        group = QGroupBox("Endereco da conta/perfil")
        form = QGridLayout(group)
        self.addr_cep = QLineEdit()
        self.addr_street = QLineEdit()
        self.addr_number = QLineEdit()
        self.addr_neighborhood = QLineEdit()
        self.addr_city = QLineEdit()
        self.addr_state = QLineEdit()
        self.addr_uf = QLineEdit()
        for widget, ph in [
            (self.addr_cep, "00000-000"),
            (self.addr_street, "Rua / Avenida"),
            (self.addr_number, "Numero"),
            (self.addr_neighborhood, "Bairro"),
            (self.addr_city, "Cidade"),
            (self.addr_state, "Estado"),
            (self.addr_uf, "UF"),
        ]:
            widget.setPlaceholderText(ph)
        form.addWidget(QLabel("CEP:"), 0, 0)
        form.addWidget(self.addr_cep, 0, 1)
        form.addWidget(QLabel("Rua:"), 0, 2)
        form.addWidget(self.addr_street, 0, 3)
        form.addWidget(QLabel("Numero:"), 1, 0)
        form.addWidget(self.addr_number, 1, 1)
        form.addWidget(QLabel("Bairro:"), 1, 2)
        form.addWidget(self.addr_neighborhood, 1, 3)
        form.addWidget(QLabel("Cidade:"), 2, 0)
        form.addWidget(self.addr_city, 2, 1)
        form.addWidget(QLabel("Estado:"), 2, 2)
        form.addWidget(self.addr_state, 2, 3)
        form.addWidget(QLabel("UF:"), 3, 0)
        form.addWidget(self.addr_uf, 3, 1)
        btns = QHBoxLayout()
        for text, cb, obj in [
            ("Gerar do projeto", self.generate_address_for_current, "Primary"),
            ("Salvar endereco", self.save_current_account, "Success"),
            ("Copiar endereco", self.copy_current_address, "Soft"),
            ("Preencher pagina aberta", self.fill_address_for_current, "Soft"),
        ]:
            btn = QPushButton(text)
            btn.setObjectName(obj)
            btn.clicked.connect(cb)
            btns.addWidget(btn)
        form.addLayout(btns, 4, 0, 1, 4)
        lay.addWidget(group)
        lay.addStretch()
        return page

    def _cards_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        info = QLabel(
            "Guarde aqui apenas referencia de cartoes proprios. O app salva final, validade e titular; nao salva CVV e nao testa pagamento."
        )
        info.setWordWrap(True)
        info.setStyleSheet(
            "background:#071a10;color:#bbf7d0;border:1px solid rgba(16,185,129,0.25);"
            "border-radius:10px;padding:10px;font-weight:700;"
        )
        lay.addWidget(info)

        self.cards_table = QTableWidget(0, 5)
        self.cards_table.setHorizontalHeaderLabels(["Apelido", "Final", "Validade", "Titular", "Status"])
        self.cards_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cards_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.cards_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.cards_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.cards_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.cards_table.setSelectionBehavior(QTableWidget.SelectRows)
        lay.addWidget(self.cards_table, 1)

        form = QGroupBox("Adicionar cartao de referencia")
        grid = QGridLayout(form)
        self.card_label = QLineEdit()
        self.card_input = QLineEdit()
        self.card_expiry = QLineEdit()
        self.card_holder = QLineEdit()
        self.card_status = QComboBox()
        self.card_status.addItems(["novo", "usando", "aprovado manual", "recusado manual", "pausado"])
        self.card_label.setPlaceholderText("Apelido")
        self.card_input.setPlaceholderText("Numero ou final 4 (so o final sera salvo)")
        self.card_expiry.setPlaceholderText("MM/AA")
        self.card_holder.setPlaceholderText("Titular")
        grid.addWidget(self.card_label, 0, 0)
        grid.addWidget(self.card_input, 0, 1)
        grid.addWidget(self.card_expiry, 0, 2)
        grid.addWidget(self.card_holder, 0, 3)
        grid.addWidget(self.card_status, 0, 4)
        add_btn = QPushButton("Adicionar referencia")
        add_btn.setObjectName("Primary")
        add_btn.clicked.connect(self.add_card)
        remove_btn = QPushButton("Remover selecionado")
        remove_btn.setObjectName("Danger")
        remove_btn.clicked.connect(self.remove_selected_card)
        copy_btn = QPushButton("Copiar resumo")
        copy_btn.setObjectName("Soft")
        copy_btn.clicked.connect(self.copy_selected_card)
        grid.addWidget(add_btn, 1, 0, 1, 2)
        grid.addWidget(remove_btn, 1, 2)
        grid.addWidget(copy_btn, 1, 3, 1, 2)
        lay.addWidget(form)
        return page

    def _help_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        help_label = QLabel(
            "Esta ferramenta organiza e acelera o trabalho visivel. Ela nao faz compra invisivel, nao testa cartao e nao burla verificacao humana."
        )
        help_label.setWordWrap(True)
        help_label.setStyleSheet(
            "background:#0b1220;color:#cbd5e1;border:1px solid rgba(148,163,184,0.16);"
            "border-radius:10px;padding:10px;font-weight:700;"
        )
        lay.addWidget(help_label)
        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setPlaceholderText("Logs da ferramenta...")
        lay.addWidget(self.log_box, 1)
        clear_btn = QPushButton("Limpar logs")
        clear_btn.setObjectName("Soft")
        clear_btn.clicked.connect(self.clear_logs)
        lay.addWidget(clear_btn)
        return page

    def load_data(self):
        self.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        if not self.DATA_FILE.exists():
            return
        try:
            raw = json.loads(self.DATA_FILE.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                self.data.update({
                    "accounts": raw.get("accounts", []) if isinstance(raw.get("accounts"), list) else [],
                    "cards": raw.get("cards", []) if isinstance(raw.get("cards"), list) else [],
                    "logs": raw.get("logs", []) if isinstance(raw.get("logs"), list) else [],
                    "settings": raw.get("settings", {}) if isinstance(raw.get("settings"), dict) else {},
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

    def save_data(self):
        self.DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "updated_at": _now(),
            "accounts": self.data.get("accounts", []),
            "cards": self.data.get("cards", []),
            "logs": self.data.get("logs", [])[-300:],
            "settings": self.data.get("settings", {}),
        }
        self.DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def log(self, message: str):
        entry = f"[{datetime.now().strftime('%H:%M:%S')}] {message}"
        self.data.setdefault("logs", []).append(entry)
        if hasattr(self, "log_box"):
            self.log_box.setPlainText("\n".join(self.data.get("logs", [])[-200:]))
            self.log_box.verticalScrollBar().setValue(self.log_box.verticalScrollBar().maximum())

    def refresh_all(self):
        self.refresh_profile_combo()
        self.refresh_accounts_table()
        self.refresh_cards_table()
        self.refresh_logs()
        total = len(self.data.get("accounts", []))
        ready = len(self.linked_profile_ids())
        self.summary_label.setText(f"{total} contas | {ready} perfis")

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
                    a.get("email", ""), a.get("password", ""),
                ]).lower()
            ]

        self.accounts_table.blockSignals(True)
        self.accounts_table.setRowCount(0)
        current_row = -1
        for account in accounts:
            row = self.accounts_table.rowCount()
            self.accounts_table.insertRow(row)
            values = [account.get("email", ""), account.get("password", "")]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, account.get("id"))
                self.accounts_table.setItem(row, col, item)
            if account.get("id") == self.current_account_id:
                current_row = row
        if current_row >= 0:
            self.accounts_table.selectRow(current_row)
        self.accounts_table.blockSignals(False)
        self.summary_label.setText(f"{len(self.data.get('accounts', []))} contas | {len(self.linked_profile_ids())} perfis")
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
            self.selected_hint.setText("Selecione uma conta para abrir ou continuar.")
            return
        profile_name = self.profile_name(account.get("profile_id")) or "sem perfil"
        address = self.normalize_address(account.get("address", {}) or {})
        address_ok = "endereco OK" if self.address_is_complete(address) else "sem endereco completo"
        self.selected_hint.setText(
            f"{account.get('email', '')} | {profile_name} | {account.get('status', 'novo')} | {address_ok}"
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

    def on_account_selected(self):
        rows = self.selected_account_rows()
        if not rows:
            self.update_selected_hint()
            return
        account_id = self.accounts_table.item(rows[0], 0).data(Qt.UserRole)
        account = self.get_account(account_id)
        if account:
            self.load_account_to_form(account)

    def selected_account_rows(self) -> List[int]:
        return sorted({idx.row() for idx in self.accounts_table.selectedIndexes()})

    def selected_accounts(self) -> List[Dict]:
        accounts = []
        for row in self.selected_account_rows():
            item = self.accounts_table.item(row, 0)
            if item:
                account = self.get_account(item.data(Qt.UserRole))
                if account:
                    accounts.append(account)
        return accounts

    def copy_selected_account_login(self):
        account = self.current_account()
        if not account:
            QMessageBox.information(self, "Copiar", "Selecione uma conta primeiro.")
            return
        text = f"{account.get('email', '')}:{account.get('password', '')}"
        set_clipboard_text(text)
        self.log(f"Login copiado: {account.get('email', '')}")

    def select_next_account(self):
        accounts = self.data.get("accounts", [])
        if not accounts:
            return
        skip_status = {"assinatura ativa", "pausado"}
        current_index = -1
        for idx, account in enumerate(accounts):
            if account.get("id") == self.current_account_id:
                current_index = idx
                break
        ordered = accounts[current_index + 1:] + accounts[:current_index + 1]
        target = None
        for account in ordered:
            if account.get("status", "novo") not in skip_status:
                target = account
                break
        target = target or accounts[0]
        self.current_account_id = target.get("id", "")
        self.load_account_to_form(target)
        self.refresh_accounts_table()
        self.log(f"Conta selecionada: {target.get('email', '')}")

    def get_account(self, account_id: str) -> Optional[Dict]:
        for account in self.data.get("accounts", []):
            if account.get("id") == account_id:
                return account
        return None

    def current_account(self) -> Optional[Dict]:
        account = self.get_account(self.current_account_id)
        if account:
            return account
        selected = self.selected_accounts()
        return selected[0] if selected else None

    def load_account_to_form(self, account: Dict):
        self.current_account_id = account.get("id", "")
        self.email_input.setText(account.get("email", ""))
        self.password_input.setText(account.get("password", ""))
        status = account.get("status", "novo")
        self.status_combo.setCurrentText(status if status in self.STATUSES else "novo")
        plan = account.get("plan", PLAN_OPTIONS[0])
        if self.plan_combo.findText(plan) < 0:
            self.plan_combo.addItem(plan)
        self.plan_combo.setCurrentText(plan)
        person = account.get("person", {}) or {}
        self.person_name_input.setText(person.get("nome", "") or "")
        self.person_cpf_input.setText(person.get("cpf", "") or "")
        self.person_birth_input.setText(person.get("nascimento", "") or "")
        self.notes_input.setPlainText(account.get("notes", ""))
        profile_id = account.get("profile_id", "")
        idx = self.profile_combo.findData(profile_id)
        if profile_id and idx < 0:
            profile = self.browser_manager.get_profile(profile_id)
            if profile and not getattr(profile, "archived", False):
                self.profile_combo.addItem(profile.name, profile_id)
                idx = self.profile_combo.findData(profile_id)
            else:
                account["profile_id"] = ""
                profile_id = ""
        self.profile_combo.setCurrentIndex(idx if idx >= 0 else 0)
        self.load_address_to_form(account.get("address", {}) or {})
        self.update_selected_hint()

    def account_from_form(self) -> Dict:
        account = self.current_account() or {"id": _make_id("acc", self.email_input.text()), "created_at": _now()}
        person = self.person_from_form()
        if not person.get("cpf") and self.email_input.text().strip():
            person = self.project_person_payload()
            if person:
                self.load_person_to_form(person)
        selected_profile_id = self.profile_combo.currentData()
        if selected_profile_id is None:
            selected_profile_id = ""
        profile_id = str(selected_profile_id or account.get("profile_id", "") or "")
        account.update({
            "email": self.email_input.text().strip(),
            "password": self.password_input.text().strip(),
            "status": self.status_combo.currentText(),
            "profile_id": profile_id,
            "plan": self.plan_combo.currentText().strip(),
            "person": person,
            "notes": self.notes_input.toPlainText().strip(),
            "address": self.address_from_form(),
            "updated_at": _now(),
        })
        return account

    def add_account(self):
        account = {
            "id": _make_id("acc"),
            "email": "",
            "password": "",
            "status": "novo",
            "profile_id": "",
            "plan": PLAN_OPTIONS[0],
            "person": {},
            "address": {},
            "notes": "",
            "created_at": _now(),
            "updated_at": _now(),
        }
        self.data.setdefault("accounts", []).append(account)
        self.current_account_id = account["id"]
        self.save_data()
        self.refresh_accounts_table()
        self.load_account_to_form(account)
        self.log("Conta vazia criada para preenchimento manual.")

    def save_current_account(self):
        account = self.account_from_form()
        if account.get("email") and "@" not in account["email"]:
            QMessageBox.warning(self, "Conta", "O email parece incompleto.")
            return
        replaced = False
        for idx, existing in enumerate(self.data.get("accounts", [])):
            if existing.get("id") == account.get("id"):
                self.data["accounts"][idx] = account
                replaced = True
                break
        if not replaced:
            self.data.setdefault("accounts", []).append(account)
        self.current_account_id = account["id"]
        self.save_data()
        self.refresh_all()
        self.log(f"Conta salva: {account.get('email') or account.get('id')}")
        self.update_selected_hint()

    def remove_selected_accounts(self):
        selected_accounts = self.selected_accounts()
        ids = [a.get("id") for a in selected_accounts]
        if not ids:
            QMessageBox.information(self, "Conta", "Selecione uma ou mais contas.")
            return
        removable_profile_ids = []
        remaining_accounts = [a for a in self.data.get("accounts", []) if a.get("id") not in ids]
        remaining_profile_ids = {a.get("profile_id") for a in remaining_accounts if a.get("profile_id")}
        for account in selected_accounts:
            profile_id = account.get("profile_id", "")
            profile = self.browser_manager.get_profile(profile_id) if profile_id else None
            if profile_id and profile_id not in remaining_profile_ids and self.is_paramount_assist_profile(profile):
                removable_profile_ids.append(profile_id)
        profile_note = ""
        if removable_profile_ids:
            profile_note = f"\n\nTambem vou apagar {len(removable_profile_ids)} perfil(is) Paramount criado(s) pela ferramenta."
        reply = QMessageBox.question(
            self,
            "Remover contas",
            f"Remover {len(ids)} conta(s) da fila?{profile_note}",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        deleted_profiles = 0
        for profile_id in removable_profile_ids:
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
            self.log(f"{len(ids)} conta(s) removida(s) e {deleted_profiles} perfil(is) Paramount apagado(s).")
        else:
            self.log(f"{len(ids)} conta(s) removida(s) da fila.")

    def import_accounts_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("Colar emails em lote")
        dialog.resize(720, 500)
        lay = QVBoxLayout(dialog)
        hint = QLabel(
            "Cole um email por linha. Pode ser email:senha, email|senha, email senha, "
            "ou apenas email. Se vier apenas email, a senha fixa abaixo sera usada."
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color:#bae6fd;font-weight:800;")
        lay.addWidget(hint)

        fixed_password = QLineEdit()
        fixed_password.setPlaceholderText("Senha fixa opcional; se preencher, substitui a senha do lote")
        lay.addWidget(fixed_password)

        text_box = QTextEdit()
        text_box.setPlaceholderText(
            "exemplo1@email.com:minhaSenha123\n"
            "exemplo2@email.com|outraSenha\n"
            "exemplo3@email.com\n\n"
            "Lote Amazon\n"
            "cliente@email.com senha123"
        )
        lay.addWidget(text_box, 1)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Importar")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancelar")
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        lay.addWidget(buttons)

        if dialog.exec_() != QDialog.Accepted:
            return
        text = text_box.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Importar", "Cole pelo menos um email.")
            return
        imported = self.import_accounts_text(
            text,
            "lote colado",
            fixed_password=fixed_password.text().strip(),
            auto_person=True,
        )
        self.save_data()
        self.refresh_all()
        QMessageBox.information(
            self,
            "Importar",
            f"{imported} conta(s) importada(s).\n\n"
            "Nome, CPF e nascimento foram buscados automaticamente no banco do projeto quando disponivel.",
        )

    def import_accounts_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar contas Paramount",
            str(BASE_DIR),
            "Textos (*.txt *.csv);;Todos (*.*)",
        )
        if not path:
            return
        try:
            text = Path(path).read_text(encoding="utf-8", errors="ignore")
        except Exception as exc:
            QMessageBox.warning(self, "Importar", f"Nao consegui ler o arquivo: {exc}")
            return
        imported = self.import_accounts_text(text, Path(path).stem, auto_person=True)
        self.save_data()
        self.refresh_all()
        QMessageBox.information(self, "Importar", f"{imported} conta(s) importada(s).")

    def import_legacy_folder(self):
        folder = LEGACY_PARAMOUNT_DIR if LEGACY_PARAMOUNT_DIR.exists() else None
        if not folder:
            selected = QFileDialog.getExistingDirectory(
                self,
                "Selecione a pasta paramount_bot antiga",
                str(BASE_DIR),
            )
            if not selected:
                return
            folder = Path(selected)

        data_dir = folder / "data"
        contas_path = data_dir / "contas.txt"
        cartoes_path = data_dir / "cartoes.txt"
        config_path = data_dir / "config.json"

        imported_accounts = 0
        imported_cards = 0
        plan_hint = ""

        if config_path.exists():
            try:
                config = json.loads(config_path.read_text(encoding="utf-8", errors="ignore"))
                raw_plan = str(config.get("planoAlvo") or config.get("plano") or "").strip()
                cadence = str(config.get("cadencia") or "").strip()
                plan_hint = " ".join(part for part in [raw_plan, cadence] if part).strip()
            except Exception as exc:
                self.log(f"Nao consegui ler config antiga: {exc}")

        if contas_path.exists():
            text = contas_path.read_text(encoding="utf-8", errors="ignore")
            imported_accounts = self.import_accounts_text(text, "paramount_bot antigo")
            if plan_hint:
                for account in self.data.get("accounts", []):
                    if not account.get("plan") or account.get("batch") == "paramount_bot antigo":
                        account["plan"] = plan_hint

        if cartoes_path.exists():
            text = cartoes_path.read_text(encoding="utf-8", errors="ignore")
            imported_cards = self.import_card_references_text(text, "paramount_bot antigo")

        self.save_data()
        self.refresh_all()
        QMessageBox.information(
            self,
            "Importacao antiga",
            f"Importei {imported_accounts} conta(s) e {imported_cards} referencia(s) de cartao.\n\n"
            "Por seguranca, CVV e numero completo nao sao salvos.",
        )

    def project_person_payload(self, used_cpfs: Optional[set] = None) -> Dict:
        if not self.db:
            return {}
        used_cpfs = used_cpfs or set()
        for _ in range(8):
            try:
                person = self.db.get_random_pair({"require_birth": True, "idade_max": 59})
            except Exception as exc:
                self.log(f"Nao consegui buscar pessoa no banco: {exc}")
                return {}
            if not person:
                return {}
            cpf = person.get("cpf", "")
            if cpf and cpf not in used_cpfs:
                used_cpfs.add(cpf)
                return {
                    "nome": person.get("nome", ""),
                    "cpf": cpf,
                    "nascimento": person.get("nascimento", ""),
                }
        return {}

    def parse_account_line(self, line: str, fixed_password: str = "") -> Optional[Dict[str, str]]:
        match = re.search(r"([\w.+-]+@[\w.-]+\.[A-Za-z]{2,})", line)
        if not match:
            return None
        email = match.group(1).strip()
        tail = (line[:match.start()] + line[match.end():]).strip()
        tail = re.sub(r"^[\s:;|,\-]+", "", tail).strip()
        fixed = fixed_password.strip()
        password = fixed
        if not password and tail:
            password = tail.split()[0].strip(" \t:;|,\"'")
        return {"email": email, "password": password}

    def import_accounts_text(
        self,
        text: str,
        batch: str = "",
        fixed_password: str = "",
        auto_person: bool = True,
    ) -> int:
        existing = {a.get("email", "").lower(): a for a in self.data.get("accounts", []) if a.get("email")}
        fixed_override = bool((fixed_password or "").strip())
        used_cpfs = {
            (a.get("person", {}) or {}).get("cpf", "")
            for a in self.data.get("accounts", [])
            if (a.get("person", {}) or {}).get("cpf")
        }
        imported = 0
        updated = 0
        first_imported_id = ""
        current_batch = batch or "importado"
        for raw_line in (text or "").splitlines():
            line = raw_line.strip().lstrip("\ufeff")
            if not line or line.startswith("#"):
                continue
            if "@" not in line:
                if len(line) <= 60:
                    current_batch = line.strip(": ")
                continue
            parsed = self.parse_account_line(line, fixed_password=fixed_password)
            if not parsed:
                continue
            email = parsed["email"]
            password = parsed["password"]
            existing_account = existing.get(email.lower())
            if existing_account:
                changed = False
                current_password = existing_account.get("password", "")
                if password and (not current_password or (fixed_override and current_password != password)):
                    existing_account["password"] = password
                    changed = True
                if auto_person and not (existing_account.get("person") or {}).get("cpf"):
                    person = self.project_person_payload(used_cpfs)
                    if person:
                        existing_account["person"] = person
                        changed = True
                if changed:
                    existing_account["updated_at"] = _now()
                    updated += 1
                continue
            person = self.project_person_payload(used_cpfs) if auto_person else {}
            new_account = {
                "id": _make_id("acc", email),
                "email": email,
                "password": password,
                "status": "novo",
                "profile_id": "",
                "plan": PLAN_OPTIONS[0],
                "person": person,
                "address": {},
                "notes": f"Importado de {current_batch}".strip(),
                "batch": current_batch,
                "created_at": _now(),
                "updated_at": _now(),
            }
            self.data.setdefault("accounts", []).append(new_account)
            if not first_imported_id:
                first_imported_id = new_account["id"]
            existing[email.lower()] = new_account
            imported += 1
        if first_imported_id and not self.current_account_id:
            self.current_account_id = first_imported_id
        if updated:
            self.log(f"Importacao concluida: {imported} nova(s), {updated} atualizada(s).")
        else:
            self.log(f"Importacao concluida: {imported} conta(s).")
        return imported

    def import_card_references_text(self, text: str, source: str = "") -> int:
        existing = {
            (card.get("last4", ""), card.get("expiry", ""))
            for card in self.data.get("cards", [])
        }
        imported = 0
        for raw_line in (text or "").splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [part.strip() for part in re.split(r"[|:;,\s]+", line) if part.strip()]
            if not parts:
                continue
            number = _digits(parts[0])
            if len(number) < 4:
                continue
            last4 = number[-4:]
            month = ""
            year = ""
            if len(parts) >= 3:
                month = _digits(parts[1])[:2]
                year = _digits(parts[2])[-2:]
            elif len(parts) >= 2:
                compact = _digits(parts[1])
                if len(compact) >= 4:
                    month = compact[:2]
                    year = compact[-2:]
            expiry = "/".join(part for part in [month, year] if part)
            key = (last4, expiry)
            if key in existing:
                continue
            self.data.setdefault("cards", []).append({
                "id": _make_id("card", f"{last4}:{expiry}"),
                "label": f"Importado {source}".strip() or f"Cartao final {last4}",
                "last4": last4,
                "expiry": expiry,
                "holder": "",
                "status": "novo",
                "source": source,
                "created_at": _now(),
                "updated_at": _now(),
            })
            existing.add(key)
            imported += 1
        self.log(f"Referencias de cartao importadas: {imported}. Numero completo e CVV foram descartados.")
        return imported

    def person_from_form(self) -> Dict:
        return {
            "nome": self.person_name_input.text().strip(),
            "cpf": self.person_cpf_input.text().strip(),
            "nascimento": self.person_birth_input.text().strip(),
        }

    def load_person_to_form(self, person: Dict):
        person = person or {}
        self.person_name_input.setText(person.get("nome", "") or "")
        self.person_cpf_input.setText(person.get("cpf", "") or "")
        self.person_birth_input.setText(person.get("nascimento", "") or "")

    def generate_person_for_current(self):
        account = self.current_account()
        if not account:
            self.save_current_account()
            account = self.current_account()
        person = self.project_person_payload()
        if not person:
            QMessageBox.warning(self, "Dados pessoais", "Nao encontrei dados com nascimento no gerador.")
            return
        payload = dict(person)
        self.load_person_to_form(payload)
        if account:
            account["person"] = payload
            account["updated_at"] = _now()
            self.save_data()
            self.refresh_accounts_table()
        self.log(f"Pessoa vinculada: {payload.get('nome', '')} | CPF {payload.get('cpf', '')}")

    def address_from_form(self) -> Dict:
        return self.normalize_address({
            "cep": self.addr_cep.text().strip(),
            "logradouro": self.addr_street.text().strip(),
            "rua": self.addr_street.text().strip(),
            "numero": self.addr_number.text().strip(),
            "bairro": self.addr_neighborhood.text().strip(),
            "cidade": self.addr_city.text().strip(),
            "estado": self.addr_state.text().strip(),
            "uf": self.addr_uf.text().strip().upper(),
        })

    def is_valid_street(self, street: str, address: Dict = None) -> bool:
        address = address or {}
        raw = str(street or "").strip()
        compact = re.sub(r"[^A-Za-zÀ-ÿ0-9]", "", raw).upper()
        uf = str(address.get("uf", "") or "").strip().upper()
        estado = str(address.get("estado", "") or "").strip().upper()
        cidade = str(address.get("cidade", "") or "").strip().upper()
        if len(compact) < 4:
            return False
        if compact in {"BR", "BRA", "BRASIL"}:
            return False
        if uf and compact == uf:
            return False
        if estado and compact == re.sub(r"[^A-ZÀ-Ý0-9]", "", estado):
            return False
        if cidade and compact == re.sub(r"[^A-ZÀ-Ý0-9]", "", cidade):
            return False
        return True

    def normalize_address(self, address: Dict) -> Dict:
        address = dict(address or {})
        uf = str(address.get("uf") or address.get("estado") or "").strip().upper()
        cep = str(address.get("cep") or "").strip()
        if len(uf) != 2 or uf not in UF_NAMES:
            state_clean = re.sub(r"[^A-Z]", "", str(address.get("estado", "")).upper())
            for candidate_uf, candidate_name in UF_NAMES.items():
                if state_clean and state_clean == re.sub(r"[^A-Z]", "", candidate_name.upper()):
                    uf = candidate_uf
                    break
        if (len(uf) != 2 or uf not in UF_NAMES) and self.address_reserve:
            try:
                inferred = self.address_reserve._infer_uf_from_cep(cep)
                if inferred:
                    uf = inferred
            except Exception:
                pass
        if len(uf) != 2 or uf not in UF_NAMES:
            uf = str(address.get("uf") or "").strip().upper()
        if uf in UF_NAMES:
            address["uf"] = uf
            generator_states = getattr(self.address_generator, "ESTADOS", {}) if self.address_generator else {}
            state_name = generator_states.get(uf) or UF_NAMES[uf]
            if not address.get("estado") or str(address.get("estado", "")).strip().upper() == uf:
                address["estado"] = state_name
        street = str(address.get("logradouro") or address.get("rua") or "").strip()
        if not self.is_valid_street(street, address):
            address["logradouro"] = ""
            address["rua"] = ""
        else:
            address["logradouro"] = street
            address["rua"] = street
        return address

    def address_is_complete(self, address: Dict) -> bool:
        address = self.normalize_address(address)
        return bool(address.get("cep") and address.get("logradouro") and address.get("cidade") and address.get("uf"))

    def load_address_to_form(self, address: Dict):
        address = self.normalize_address(address or {})
        self.addr_cep.setText(address.get("cep", ""))
        self.addr_street.setText(address.get("logradouro") or address.get("rua", ""))
        self.addr_number.setText(str(address.get("numero", "") or ""))
        self.addr_neighborhood.setText(address.get("bairro", ""))
        self.addr_city.setText(address.get("cidade", ""))
        self.addr_state.setText(address.get("estado", ""))
        self.addr_uf.setText(address.get("uf", ""))

    def generate_address_for_current(self):
        account = self.current_account()
        if not account:
            self.add_account()
            account = self.current_account()
        uf = self.addr_uf.text().strip().upper() or None
        address = None
        if self.address_reserve:
            candidate = self.address_reserve.get_reserva(uf)
            if candidate and self.address_is_complete(candidate):
                address = self.normalize_address(candidate)
        if (not address or not self.address_is_complete(address)) and self.address_generator:
            try:
                for _ in range(4):
                    generated = self.address_generator.gerar_endereco(uf=uf)
                    candidate = generated.to_dict() if generated else None
                    if candidate and self.address_is_complete(candidate):
                        address = self.normalize_address(candidate)
                        break
            except Exception as exc:
                self.log(f"API de endereco falhou: {exc}")
        if not address or not self.address_is_complete(address):
            QMessageBox.warning(self, "Endereco", "Nao consegui gerar endereco completo agora. Tente novamente ou confira as reservas de CEP.")
            return
        self.load_address_to_form(address)
        account["address"] = self.address_from_form()
        account["updated_at"] = _now()
        self.save_data()
        self.refresh_accounts_table()
        self.log(f"Endereco salvo para {account.get('email') or account.get('id')}: {address.get('cep', '')}")

    def copy_current_address(self):
        address = self.address_from_form()
        text = "\n".join(
            part for part in [
                f"CEP: {address.get('cep', '')}",
                f"Rua: {address.get('logradouro', '')}",
                f"Numero: {address.get('numero', '')}",
                f"Bairro: {address.get('bairro', '')}",
                f"Cidade: {address.get('cidade', '')}",
                f"Estado: {address.get('estado', '')}",
                f"UF: {address.get('uf', '')}",
            ] if part.split(": ", 1)[-1]
        )
        if text:
            set_clipboard_text(text)
            self.log("Endereco copiado.")

    def profile_name(self, profile_id: str) -> str:
        if not profile_id:
            return ""
        profile = self.browser_manager.get_profile(profile_id)
        return getattr(profile, "name", "") if profile else ""

    def ensure_profile_for_current(self):
        account = self.current_account()
        if not account:
            self.save_current_account()
            account = self.current_account()
        if not account:
            return ""
        if account.get("profile_id") and self.browser_manager.get_profile(account["profile_id"]):
            QMessageBox.information(self, "Perfil", "Esta conta ja tem perfil vinculado.")
            return account["profile_id"]
        profile_id = self.create_paramount_profile_for_account(account)
        self.save_data()
        self.refresh_all()
        return profile_id

    def create_paramount_profile_for_account(self, account: Dict) -> str:
        number = len(self.paramount_profiles(include_all=False)) + 1
        email = account.get("email", "")
        label = email.split("@", 1)[0][:18] if email else str(number)
        profile = self.browser_manager.create_profile(
            name=f"Paramount {number} - {label}",
            country="BR",
            persist_data=True,
        )
        profile.tags = sorted(set((getattr(profile, "tags", []) or []) + ["paramount", "assist"]))
        profile.browser_mode = "auto"
        profile.fingerprint_level = "Streaming"
        profile.compatibility_mode = True
        profile.save_logins = True
        if account.get("address"):
            profile.address_data = dict(account.get("address") or {})
        self.browser_manager._save_profiles()
        account["profile_id"] = profile.id
        account["status"] = "perfil pronto"
        account["updated_at"] = _now()
        self.log(f"Perfil criado: {profile.name}")
        return profile.id

    def selected_or_first_accounts(self, limit: int = 3) -> List[Dict]:
        selected = self.selected_accounts()
        if selected:
            return selected[:limit]
        accounts = self.data.get("accounts", [])
        return accounts[:limit]

    def open_three_profiles(self):
        accounts = self.selected_or_first_accounts(3)
        if not accounts:
            QMessageBox.information(self, "Perfis", "Importe ou crie contas primeiro.")
            return
        opened = 0
        for account in accounts[:3]:
            if not account.get("profile_id") or not self.browser_manager.get_profile(account.get("profile_id")):
                self.create_paramount_profile_for_account(account)
            if self.open_profile(account["profile_id"], PARAMOUNT_URLS["login"]):
                opened += 1
        self.save_data()
        self.refresh_all()
        self.log(f"Abertura solicitada para {opened} perfil(is).")

    def open_url_for_current(self, key: str):
        account = self.account_from_form()
        if account.get("id"):
            self.current_account_id = account["id"]
            self.save_current_account()
        profile_id = account.get("profile_id") or self.ensure_profile_for_current()
        url = PARAMOUNT_URLS.get(key, PARAMOUNT_URLS["login"])
        self.open_profile(profile_id, url)

    def quick_open_login(self):
        account = self.current_account() or self.account_from_form()
        if not account.get("email"):
            QMessageBox.information(
                self,
                "Comece pela conta",
                "Primeiro importe as contas antigas ou preencha o email/senha em Conta selecionada.\n\n"
                "Depois clique de novo em Criar perfil e abrir login.",
            )
            self.email_input.setFocus()
            return
        self.save_current_account()
        profile_id = account.get("profile_id") or self.ensure_profile_for_current()
        if profile_id:
            self.open_profile(profile_id, PARAMOUNT_URLS["login"])

    def open_signup_for_current(self):
        account = self.current_account()
        if not account and self.data.get("accounts"):
            account = self.data["accounts"][0]
            self.current_account_id = account.get("id", "")
            self.load_account_to_form(account)
        if not account:
            account = self.account_from_form()
        if not account.get("email"):
            QMessageBox.information(
                self,
                "Cadastro",
                "Cole emails em lote primeiro. Depois selecione uma conta e clique em Abrir cadastro.",
            )
            self.import_accounts_dialog()
            return
        self.save_current_account()
        profile_id = account.get("profile_id") or self.ensure_profile_for_current()
        if profile_id:
            self.open_profile(profile_id, PARAMOUNT_URLS["cadastro"])

    def open_profile_only_for_current(self):
        account = self.current_account()
        if not account and self.data.get("accounts"):
            account = self.data["accounts"][0]
            self.current_account_id = account.get("id", "")
            self.load_account_to_form(account)
        if not account:
            account = self.account_from_form()
        if not account.get("email"):
            QMessageBox.information(self, "Abrir perfil", "Cole ou importe pelo menos um email primeiro.")
            return
        self.save_current_account()
        account = self.current_account() or account
        profile_id = account.get("profile_id") or self.ensure_profile_for_current()
        if profile_id:
            self.open_profile(profile_id, PARAMOUNT_URLS["cadastro"])
            self.log("Perfil aberto sem executar preenchimento automatico.")

    def smart_continue_for_current(self):
        account = self.current_account()
        if not account and self.data.get("accounts"):
            account = self.data["accounts"][0]
            self.current_account_id = account.get("id", "")
            self.load_account_to_form(account)
        if not account:
            account = self.account_from_form()
        if not account.get("email"):
            self.import_accounts_dialog()
            return
        self.save_current_account()
        account = self.current_account() or account
        profile_id = account.get("profile_id") or self.ensure_profile_for_current()
        if not profile_id:
            return
        if not self.browser_manager.is_browser_active(profile_id):
            self.open_profile(profile_id, PARAMOUNT_URLS["cadastro"])
            self.log("Fluxo: abri o cadastro. Quando carregar, clique em Continuar de novo.")
            return

        driver, error = self._driver_for_current()
        if not driver:
            QMessageBox.warning(self, "Fluxo Paramount", error)
            return

        state = self._page_state(driver)
        url = state.get("url", "")
        text = state.get("text", "").lower()
        if any(term in text for term in ["cloudflare", "confirme que e humano", "confirme que é humano", "verificacao de seguranca", "verificação de segurança"]):
            QMessageBox.information(
                self,
                "Fluxo Paramount",
                "A pagina esta pedindo verificacao humana. Resolva no navegador e clique em Continuar de novo.",
            )
            return

        if "signin" in url:
            result = self._fill_signup_fields(account)
            clicked = self._click_safe_continue(driver)
            self._show_flow_result("Login", result, clicked)
            return

        if "signup/plan" in url or "escolha o plano" in text or "escolha seu plano" in text:
            self.select_plan_for_current()
            return

        if any(term in text for term in ["voce esta a apenas alguns passos", "você está a apenas alguns passos", "crie uma conta", "escolha o plano"]):
            clicked = self._click_safe_continue(driver)
            if clicked.get("clicked"):
                self.log(f"Fluxo: avancei na tela inicial da Paramount pelo botao {clicked.get('button', '')}.")
                return

        if any(term in text for term in ["metodo de pagamento", "método de pagamento", "cep", "cpf", "endereco", "endereço"]):
            self.fill_cpf_address_for_current()
            clicked = self._click_safe_continue(driver)
            self._show_flow_result("Dados/endereco", {"ok": True, "filled": 0}, clicked)
            return

        if "signup" in url or state.get("input_count", 0) > 0:
            result = self._fill_signup_fields(account)
            self._accept_visible_terms(driver)
            clicked = self._click_safe_continue(driver)
            self._show_flow_result("Cadastro", result, clicked)
            return

        clicked = self._click_safe_continue(driver)
        if clicked.get("clicked"):
            self.log(f"Fluxo: cliquei em {clicked.get('button', 'continuar')}.")
            QMessageBox.information(self, "Fluxo Paramount", "Cliquei no proximo botao seguro da pagina.")
            return

        QMessageBox.information(
            self,
            "Fluxo Paramount",
            "Nao encontrei o proximo passo automatico nesta tela. Use Diagnosticar pagina ou avance manualmente no navegador.",
        )

    def _page_state(self, driver) -> Dict:
        script = r"""
const text = (document.body && (document.body.innerText || document.body.textContent) || "").slice(0, 6000);
const inputCount = Array.from(document.querySelectorAll("input, textarea, select")).filter(el => {
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0 && !el.disabled;
}).length;
return {url: location.href, title: document.title, text, input_count: inputCount};
"""
        try:
            return driver.execute_script(script) or {}
        except Exception as exc:
            self.log(f"Fluxo: nao consegui ler a pagina: {exc}")
            return {}

    def _accept_visible_terms(self, driver) -> Dict:
        script = r"""
function visible(el) {
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0 && !el.disabled;
}
let checked = 0;
for (const el of Array.from(document.querySelectorAll("input[type='checkbox']")).filter(visible)) {
  if (!el.checked) {
    el.click();
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

    def _click_safe_continue(self, driver) -> Dict:
        script = r"""
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase().trim();
}
function visible(el) {
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0 && !el.disabled;
}
const good = ["continuar", "continue", "proximo", "próximo", "avancar", "avançar", "seguir"];
const blocked = ["pagar", "pagamento", "finalizar", "concluir compra", "confirmar pagamento", "assinar agora", "comprar", "pay"];
const candidates = Array.from(document.querySelectorAll("button, a, [role='button'], input[type='button'], input[type='submit']"))
  .filter(visible)
  .map(el => {
    const txt = clean(el.innerText || el.value || el.getAttribute("aria-label") || el.textContent || "");
    return {el, txt};
  })
  .filter(item => item.txt && good.some(word => item.txt.includes(clean(word))))
  .filter(item => !blocked.some(word => item.txt.includes(clean(word))));
if (!candidates.length) {
  return {clicked:false, reason:"nenhum botao seguro de continuar encontrado", url:location.href};
}
const target = candidates[0];
target.el.scrollIntoView({block:"center", inline:"center"});
target.el.click();
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
            QMessageBox.warning(self, "Fluxo Paramount", (fill_result or {}).get("message", "Nao consegui preencher."))
            return
        msg = f"{step}: preenchi {filled} campo(s)."
        if clicked:
            msg += f"\nCliquei em: {click_result.get('button', 'continuar')}."
        else:
            msg += "\nNao encontrei botao seguro para clicar nesta etapa."
        self.log(msg.replace("\n", " | "))
        if not clicked and filled == 0:
            QMessageBox.information(self, "Fluxo Paramount", msg)

    def quick_select_plan(self):
        account = self.current_account() or self.account_from_form()
        if not account.get("email"):
            QMessageBox.information(
                self,
                "Plano",
                "Selecione ou preencha uma conta primeiro. O plano fica salvo por conta.",
            )
            self.email_input.setFocus()
            return
        self.save_current_account()
        profile_id = account.get("profile_id") or self.ensure_profile_for_current()
        if profile_id and not self.browser_manager.is_browser_active(profile_id):
            self.open_profile(profile_id, PARAMOUNT_URLS["plano"])
            return
        self.select_plan_for_current()

    def open_profile(self, profile_id: str, url: str) -> bool:
        if not profile_id:
            return False
        if self.browser_manager.is_browser_active(profile_id):
            if self.navigate_active_profile(profile_id, url):
                self.log(f"Perfil ja estava aberto; naveguei para {url}")
                return True
            QMessageBox.warning(self, "Navegador", "Perfil ja aberto, mas nao consegui navegar a aba.")
            return False
        if self.browser_manager.is_profile_launching(profile_id):
            self.log("Este perfil ja esta abrindo.")
            return False
        if not self.browser_manager.begin_profile_launch(profile_id):
            self.log("Abertura duplicada bloqueada.")
            return False
        thread = BrowserLaunchThread(self.browser_manager, profile_id, url, monitor=True)
        thread.finished.connect(self.on_launch_finished)
        thread.browser_closed.connect(self.on_browser_closed)
        thread.thread_done.connect(self.on_thread_done)
        self.launch_threads[profile_id] = thread
        thread.start()
        self.log(f"Abrindo perfil em {url}")
        return True

    def navigate_active_profile(self, profile_id: str, url: str) -> bool:
        url = self.browser_manager.normalize_navigation_target(url)
        try:
            if self.browser_manager.is_native_browser(profile_id) or getattr(self.browser_manager, "active_debug_ports", {}).get(profile_id):
                driver = self.browser_manager._attach_native_control_driver(profile_id)
            else:
                driver = self.browser_manager.active_browsers.get(profile_id)
            if driver and hasattr(driver, "get"):
                driver.get(url)
                return True
        except Exception as exc:
            self.log(f"Falha ao navegar perfil ativo: {exc}")
        return False

    def on_launch_finished(self, success: bool, message: str):
        thread = self.sender()
        profile_id = getattr(thread, "profile_id", "")
        self.browser_manager.end_profile_launch(profile_id)
        self.log(message if success else f"Erro ao abrir: {message}")
        if not success:
            QMessageBox.warning(self, "Navegador", message)

    def on_browser_closed(self, profile_id: str):
        self.browser_manager.end_profile_launch(profile_id)
        self.browser_manager.active_browsers.pop(profile_id, None)
        self.log(f"Perfil fechado: {self.profile_name(profile_id) or profile_id}")

    def on_thread_done(self, profile_id: str):
        self.browser_manager.end_profile_launch(profile_id)
        thread = self.launch_threads.pop(profile_id, None)
        if thread:
            thread.deleteLater()

    def _driver_for_current(self):
        account = self.account_from_form()
        profile_id = account.get("profile_id")
        if not profile_id:
            return None, "Crie ou vincule um perfil primeiro."
        if not self.browser_manager.is_browser_active(profile_id):
            return None, "Abra o perfil antes de preencher."
        try:
            if self.browser_manager.is_native_browser(profile_id) or getattr(self.browser_manager, "active_debug_ports", {}).get(profile_id):
                driver = self.browser_manager._attach_native_control_driver(profile_id)
            else:
                driver = self.browser_manager.active_browsers.get(profile_id)
            if not driver or not hasattr(driver, "execute_script"):
                return None, "Este perfil nao permite preenchimento automatico."
            return driver, ""
        except Exception as exc:
            return None, f"Nao consegui conectar ao navegador: {exc}"

    def _account_payload_for_page(self, account: Dict) -> Dict:
        person = account.get("person", {}) or {}
        if not person.get("cpf"):
            person = self.project_person_payload()
            if person:
                account["person"] = person
                self.load_person_to_form(person)
                self.save_data()
        name = (person.get("nome") or "").strip()
        parts = name.split()
        return {
            "email": account.get("email", ""),
            "password": account.get("password", ""),
            "fullName": name,
            "firstName": parts[0] if parts else "",
            "lastName": " ".join(parts[1:]) if len(parts) > 1 else "",
            "cpf": person.get("cpf", ""),
            "cpfDigits": _digits(person.get("cpf", "")),
            "birth": person.get("nascimento", ""),
        }

    def _fill_signup_fields(self, account: Dict) -> Dict:
        driver, error = self._driver_for_current()
        if not driver:
            return {"ok": False, "message": error, "filled": 0}
        payload = self._account_payload_for_page(account)
        script = r"""
const data = arguments[0] || {};
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}
function visible(el) {
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0 && !el.disabled && !el.readOnly;
}
function fieldText(el) {
  const bits = [el.name, el.id, el.placeholder, el.type, el.autocomplete, el.getAttribute("aria-label"), el.getAttribute("data-testid"), el.getAttribute("data-recurly")];
  if (el.labels) Array.from(el.labels).forEach(label => bits.push(label.innerText || ""));
  for (const attr of ["aria-labelledby", "aria-describedby"]) {
    const ids = (el.getAttribute(attr) || "").split(/\s+/).filter(Boolean);
    for (const id of ids) {
      const ref = document.getElementById(id);
      if (ref) bits.push(ref.innerText || ref.textContent || "");
    }
  }
  const parent = el.closest("label, div, section, form");
  if (parent) bits.push((parent.innerText || parent.textContent || "").slice(0, 180));
  return clean(bits.filter(Boolean).join(" "));
}
function setValue(el, value) {
  if (!value) return false;
  el.focus();
  el.value = value;
  el.dispatchEvent(new Event("input", {bubbles:true}));
  el.dispatchEvent(new Event("change", {bubbles:true}));
  el.blur();
  return true;
}
const skip = /card|cartao|cvv|cvc|security|month|year|expir|cc-|credit|debito|credito|validade|numero do cartao/;
const fields = Array.from(document.querySelectorAll("input, textarea")).filter(visible);
let filled = 0;
let used = new Set();
function fillOne(test, value) {
  if (!value) return false;
  for (const el of fields) {
    if (used.has(el)) continue;
    const txt = fieldText(el);
    if (skip.test(txt)) continue;
    if (test(el, txt)) {
      if (setValue(el, value)) {
        used.add(el);
        filled++;
        return true;
      }
    }
  }
  return false;
}
fillOne((el, txt) => el.type === "email" || /email|e-mail/.test(txt), data.email);
fillOne((el, txt) => el.type === "password" || /senha|password|pass/.test(txt), data.password);
fillOne((el, txt) => /cpf|documento|tax|tax_identifier/.test(txt), data.cpf || data.cpfDigits);
fillOne((el, txt) => /birth|birthday|nascimento|data de nascimento|dob/.test(txt), data.birth);
fillOne((el, txt) => /full.?name|nome completo|nome do titular|titular/.test(txt), data.fullName);
fillOne((el, txt) => /first.?name|primeiro nome|\bnome\b/.test(txt) && !/sobrenome|last/.test(txt), data.firstName || data.fullName);
fillOne((el, txt) => /last.?name|sobrenome/.test(txt), data.lastName);
return {ok:true, filled, url:location.href, title:document.title};
"""
        try:
            result = driver.execute_script(script, payload) or {}
            result["ok"] = True
            return result
        except Exception as exc:
            return {"ok": False, "message": f"Nao consegui preencher: {exc}", "filled": 0}

    def fill_signup_for_current(self):
        account = self.account_from_form()
        if not account.get("email"):
            QMessageBox.warning(self, "Cadastro", "Selecione ou importe uma conta com email.")
            return
        if not account.get("password"):
            QMessageBox.warning(self, "Cadastro", "Esta conta esta sem senha. Use email:senha ou senha fixa no lote.")
            return
        result = self._fill_signup_fields(account)
        if not result.get("ok"):
            QMessageBox.warning(self, "Cadastro", result.get("message", "Nao consegui preencher."))
            return
        filled = int(result.get("filled") or 0)
        account["updated_at"] = _now()
        self.save_data()
        self.refresh_accounts_table()
        self.log(f"Cadastro: preenchi {filled} campo(s) em {result.get('url', '')}")
        QMessageBox.information(
            self,
            "Cadastro",
            f"Preenchi {filled} campo(s).\n\nConfira no site e clique em Continuar manualmente.",
        )

    def fill_cpf_address_for_current(self):
        account = self.account_from_form()
        if not account.get("profile_id"):
            QMessageBox.warning(self, "CPF/endereco", "Abra/crie o perfil desta conta primeiro.")
            return
        if not (account.get("person", {}) or {}).get("cpf"):
            person = self.project_person_payload()
            if person:
                account["person"] = person
                self.load_person_to_form(person)
        if not self.address_is_complete(self.address_from_form()):
            self.generate_address_for_current()
            account = self.account_from_form()
        personal = self._fill_signup_fields(account)
        address = self.address_from_form()
        address_result = {"ok": False, "message": "Endereco nao preenchido.", "filled": 0}
        if address.get("cep"):
            address_result = self.browser_manager.fill_address_fields(account.get("profile_id"), address)
        filled = int(personal.get("filled") or 0) + int(address_result.get("filled") or 0)
        self.log(f"CPF/endereco: {filled} campo(s) preenchido(s).")
        if not personal.get("ok"):
            QMessageBox.warning(self, "CPF/endereco", personal.get("message", "Nao consegui preencher CPF/dados."))
            return
        if not address_result.get("ok"):
            QMessageBox.warning(self, "CPF/endereco", address_result.get("message", "CPF preenchido, mas endereco falhou."))
            return
        QMessageBox.information(self, "CPF/endereco", f"Preenchi {filled} campo(s). Confira antes de continuar.")

    def fill_login_for_current(self):
        account = self.account_from_form()
        if not account.get("email"):
            QMessageBox.warning(self, "Login", "Informe o email da conta.")
            return
        driver, error = self._driver_for_current()
        if not driver:
            QMessageBox.warning(self, "Login", error)
            return
        script = r"""
const data = arguments[0] || {};
function visible(el) {
  const style = window.getComputedStyle(el);
  const rect = el.getBoundingClientRect();
  return style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0 && !el.disabled && !el.readOnly;
}
function textOf(el) {
  const bits = [el.name, el.id, el.placeholder, el.type, el.autocomplete, el.getAttribute("aria-label"), el.getAttribute("data-testid")];
  if (el.labels) Array.from(el.labels).forEach(label => bits.push(label.innerText));
  const parent = el.closest("label, div, section");
  if (parent) bits.push((parent.innerText || "").slice(0, 120));
  return bits.filter(Boolean).join(" ").toLowerCase();
}
function setValue(el, value) {
  el.focus();
  el.value = value;
  el.dispatchEvent(new Event("input", {bubbles:true}));
  el.dispatchEvent(new Event("change", {bubbles:true}));
  el.blur();
}
const fields = Array.from(document.querySelectorAll("input")).filter(visible);
let filled = 0;
let emailField = fields.find(el => /email|e-mail|usuario|login|user/.test(textOf(el)) || el.type === "email");
let passField = fields.find(el => el.type === "password" || /senha|password|pass/.test(textOf(el)));
if (emailField && data.email) { setValue(emailField, data.email); filled++; }
if (passField && data.password) { setValue(passField, data.password); filled++; }
return {filled, url: location.href, title: document.title};
"""
        try:
            result = driver.execute_script(script, {"email": account.get("email"), "password": account.get("password")}) or {}
        except Exception as exc:
            QMessageBox.warning(self, "Login", f"Nao consegui preencher: {exc}")
            return
        filled = int(result.get("filled") or 0)
        self.log(f"Preenchi {filled} campo(s) de login em {result.get('url', '')}")
        QMessageBox.information(self, "Login", f"Preenchi {filled} campo(s). Confira antes de continuar.")

    def fill_personal_for_current(self):
        account = self.account_from_form()
        person = account.get("person", {}) or {}
        name = person.get("nome", "").strip()
        cpf = person.get("cpf", "").strip()
        birth = person.get("nascimento", "").strip()
        if not any([name, cpf, birth]):
            QMessageBox.information(
                self,
                "Dados pessoais",
                "Clique em Gerar pessoa do projeto ou preencha Nome/CPF/Nascimento antes.",
            )
            return
        driver, error = self._driver_for_current()
        if not driver:
            QMessageBox.warning(self, "Dados pessoais", error)
            return
        parts = name.split()
        payload = {
            "fullName": name,
            "firstName": parts[0] if parts else "",
            "lastName": " ".join(parts[1:]) if len(parts) > 1 else "",
            "cpf": cpf,
            "cpfDigits": _digits(cpf),
            "birth": birth,
        }
        script = r"""
const data = arguments[0] || {};
function clean(s) {
  return (s || "").toString().normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
}
function visible(el) {
  const st = window.getComputedStyle(el);
  const r = el.getBoundingClientRect();
  return st.display !== "none" && st.visibility !== "hidden" && r.width > 0 && r.height > 0 && !el.disabled && !el.readOnly;
}
function fieldText(el) {
  const bits = [el.name, el.id, el.placeholder, el.type, el.autocomplete, el.getAttribute("aria-label"), el.getAttribute("data-testid"), el.getAttribute("data-recurly")];
  if (el.labels) Array.from(el.labels).forEach(label => bits.push(label.innerText || ""));
  for (const attr of ["aria-labelledby", "aria-describedby"]) {
    const ids = (el.getAttribute(attr) || "").split(/\s+/).filter(Boolean);
    for (const id of ids) {
      const ref = document.getElementById(id);
      if (ref) bits.push(ref.innerText || ref.textContent || "");
    }
  }
  const parent = el.closest("label, div, section");
  if (parent) bits.push((parent.innerText || parent.textContent || "").slice(0, 160));
  return clean(bits.filter(Boolean).join(" "));
}
function setValue(el, value) {
  if (!value) return false;
  el.focus();
  el.value = value;
  el.dispatchEvent(new Event("input", {bubbles:true}));
  el.dispatchEvent(new Event("change", {bubbles:true}));
  el.blur();
  return true;
}
const fields = Array.from(document.querySelectorAll("input")).filter(visible);
let filled = 0;
for (const el of fields) {
  const txt = fieldText(el);
  if (/card|cartao|cartao|cvv|cvc|security|month|year|expir|cc-/.test(txt)) continue;
  if (/full.?name|nome completo|nameoncard/.test(txt)) {
    if (setValue(el, data.fullName)) filled++;
  } else if (/first.?name|primeiro nome|nome\b/.test(txt) && !/sobrenome|last/.test(txt)) {
    if (setValue(el, data.firstName || data.fullName)) filled++;
  } else if (/last.?name|sobrenome|apelido/.test(txt)) {
    if (setValue(el, data.lastName)) filled++;
  } else if (/cpf|tax|documento|tax_identifier/.test(txt)) {
    if (setValue(el, data.cpf || data.cpfDigits)) filled++;
  } else if (/birth|birthday|nascimento|data de nascimento|dob/.test(txt)) {
    if (setValue(el, data.birth)) filled++;
  }
}
return {filled, url: location.href};
"""
        try:
            result = driver.execute_script(script, payload) or {}
        except Exception as exc:
            QMessageBox.warning(self, "Dados pessoais", f"Nao consegui preencher: {exc}")
            return
        filled = int(result.get("filled") or 0)
        self.log(f"Preenchi {filled} campo(s) pessoais em {result.get('url', '')}")
        QMessageBox.information(self, "Dados pessoais", f"Preenchi {filled} campo(s). Confira antes de continuar.")

    def select_plan_for_current(self):
        account = self.account_from_form()
        plan = (account.get("plan") or self.plan_combo.currentText() or "").strip()
        profile_id = account.get("profile_id")
        if not profile_id:
            QMessageBox.warning(self, "Plano", "Crie ou vincule um perfil primeiro.")
            return
        if not plan:
            QMessageBox.warning(self, "Plano", "Escolha ou digite o nome do plano.")
            return
        if not self.browser_manager.is_browser_active(profile_id):
            self.open_profile(profile_id, PARAMOUNT_URLS["plano"])
            QMessageBox.information(self, "Plano", "Abri a pagina de planos. Quando carregar, clique em Selecionar plano.")
            return

        driver, error = self._driver_for_current()
        if not driver:
            QMessageBox.warning(self, "Plano", error)
            return

        try:
            current_url = driver.execute_script("return location.href") or ""
        except Exception:
            current_url = ""
        if "paramountplus.com" not in current_url or "/signup/plan" not in current_url:
            self.navigate_active_profile(profile_id, PARAMOUNT_URLS["plano"])
            QMessageBox.information(self, "Plano", "Levei o perfil para a pagina de planos. Quando carregar, clique em Selecionar plano de novo.")
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
const blocked = ["pagar", "pagamento", "finalizar", "concluir compra", "confirmar pagamento", "confirmar assinatura"];
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
    return {clicked:true, matched:item.text.slice(0, 220), button:ranked[0].txt, url:location.href};
  }
  item.el.scrollIntoView({block:"center", inline:"center"});
  item.el.click();
  return {clicked:true, matched:item.text.slice(0, 220), button:"card", url:location.href};
}
return {clicked:false, reason:"Nao encontrei card/botao com esse texto.", url:location.href};
"""
        try:
            result = driver.execute_script(script, plan) or {}
        except Exception as exc:
            QMessageBox.warning(self, "Plano", f"Nao consegui selecionar o plano: {exc}")
            return
        if result.get("clicked"):
            account["plan"] = plan
            account["updated_at"] = _now()
            self.save_data()
            self.log(f"Plano selecionado visualmente: {plan} | botao: {result.get('button', '')}")
            QMessageBox.information(
                self,
                "Plano",
                "Tentei selecionar o plano na pagina aberta.\n\nConfira a tela antes de continuar. O app nao confirma pagamento.",
            )
        else:
            self.log(f"Plano nao encontrado: {plan} | {result.get('reason', '')}")
            QMessageBox.warning(
                self,
                "Plano",
                f"Nao encontrei o plano '{plan}'.\n\nDigite no campo Plano um texto igual ao que aparece no site e tente de novo.",
            )

    def fill_address_for_current(self):
        account = self.account_from_form()
        profile_id = account.get("profile_id")
        address = self.address_from_form()
        if not profile_id:
            QMessageBox.warning(self, "Endereco", "Crie ou vincule um perfil primeiro.")
            return
        if not address.get("cep"):
            QMessageBox.warning(self, "Endereco", "Gere ou informe um endereco primeiro.")
            return
        result = self.browser_manager.fill_address_fields(profile_id, address)
        self.log(result.get("message", f"Endereco: {result.get('filled', 0)} campo(s)."))
        if not result.get("ok"):
            QMessageBox.warning(self, "Endereco", result.get("message", "Nao consegui preencher."))
        else:
            QMessageBox.information(self, "Endereco", result.get("message", "Endereco preenchido."))

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

    def mark_status(self, status: str):
        account = self.current_account()
        if not account:
            return
        account["status"] = status
        account["updated_at"] = _now()
        self.status_combo.setCurrentText(status)
        self.save_data()
        self.refresh_accounts_table()
        self.log(f"Status atualizado: {account.get('email', '')} -> {status}")

    def add_card(self):
        number = _digits(self.card_input.text())
        last4 = number[-4:] if number else self.card_input.text().strip()[-4:]
        if len(last4) < 4:
            QMessageBox.warning(self, "Cartao", "Informe pelo menos o final 4.")
            return
        card = {
            "id": _make_id("card", last4),
            "label": self.card_label.text().strip() or f"Cartao final {last4}",
            "last4": last4,
            "expiry": self.card_expiry.text().strip(),
            "holder": self.card_holder.text().strip(),
            "status": self.card_status.currentText(),
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
        super().closeEvent(event)
