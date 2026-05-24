#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Painel admin para codigos de email via cPanel."""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from datetime import datetime, timezone

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QSizePolicy,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from app.ui.app_theme import DARK_STYLE_PRO
from app.ui.components import PALETTE, table_qss, tabs_qss

from app.core.paths import CONFIG_DIR

try:
    from app.core.app_context import get_app_store
except Exception:
    get_app_store = None


SETTINGS_FILE = CONFIG_DIR / "email_codes_admin.json"


def _load_settings() -> dict:
    try:
        if SETTINGS_FILE.exists():
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"base_url": "https://bobobu.com.br/codigos", "token": ""}


def _save_settings(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _api_url(base_url: str) -> str:
    base = (base_url or "").strip().rstrip("/")
    if not base:
        raise ValueError("Informe a URL do painel hospedado.")
    return f"{base}/api/admin.php"


class EmailCodesApiWorker(QThread):
    result = pyqtSignal(str, object, str)

    def __init__(self, action: str, base_url: str, token: str, payload: dict | None = None, parent=None):
        super().__init__(parent)
        self.action = action
        self.base_url = base_url
        self.token = token
        self.payload = payload or {}

    def run(self):
        try:
            payload = dict(self.payload)
            payload["action"] = self.action
            req = urllib.request.Request(
                _api_url(self.base_url),
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "X-Admin-Token": self.token,
                    "User-Agent": "TelegramPro-EmailCodesAdmin/1.0",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8", errors="replace"))
            if not data.get("ok"):
                self.result.emit(self.action, data, str(data.get("error") or "Erro desconhecido"))
                return
            self.result.emit(self.action, data, "")
        except urllib.error.HTTPError as exc:
            text = exc.read().decode("utf-8", errors="replace") if exc.fp else ""
            self.result.emit(self.action, {}, f"HTTP {exc.code}: {text[:400]}")
        except Exception as exc:
            self.result.emit(self.action, {}, str(exc))


class EmailCodesAdminWidget(QWidget):
    """Admin visual para criar acessos temporarios e ler codigos."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = _load_settings()
        self.worker = None
        self.accesses = []
        self.codes = []
        self.logs = []
        self.last_created_code = ""
        self._pending_actions = []
        self.summary_values = {}
        self._loaded_access_id = ""
        self._build_ui()
        self._load_fields()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(60000)
        self.refresh_timer.timeout.connect(self.refresh_light)
        self.refresh_timer.start()
        if self.settings.get("token"):
            QTimer.singleShot(500, self.refresh_all)

    def _build_ui(self):
        self.setStyleSheet(self._qss())
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 10)
        root.setSpacing(8)

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_lay = QHBoxLayout(hero)
        hero_lay.setContentsMargins(16, 12, 16, 12)
        title_box = QVBoxLayout()
        title = QLabel("Codigos Email")
        title.setObjectName("Title")
        subtitle = QLabel("Crie acessos temporarios, veja codigos recebidos e acompanhe logs.")
        subtitle.setObjectName("Subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        hero_lay.addLayout(title_box, 1)
        self.status_badge = QLabel("Nao conectado")
        self.status_badge.setObjectName("Badge")
        self.status_badge.setAlignment(Qt.AlignCenter)
        hero_lay.addWidget(self.status_badge)
        root.addWidget(hero)

        config = QFrame()
        config.setObjectName("Card")
        grid = QGridLayout(config)
        grid.setContentsMargins(12, 10, 12, 10)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.addWidget(QLabel("URL"), 0, 0)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://bobobu.com.br/codigos")
        grid.addWidget(self.url_input, 0, 1, 1, 3)
        grid.addWidget(QLabel("Token admin"), 1, 0)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Mesmo admin_api_token do config.php")
        grid.addWidget(self.token_input, 1, 1, 1, 3)
        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(self.save_settings)
        test_btn = QPushButton("Atualizar painel")
        test_btn.clicked.connect(self.refresh_all)
        grid.addWidget(save_btn, 2, 2)
        grid.addWidget(test_btn, 2, 3)
        root.addWidget(config)

        root.addWidget(self._summary_panel())

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self.tabs.addTab(self._access_tab(), "Acessos")
        self.tabs.addTab(self._codes_tab(), "Codigos")
        self.tabs.addTab(self._logs_tab(), "Logs")

    def _summary_panel(self):
        panel = QFrame()
        panel.setObjectName("Summary")
        grid = QGridLayout(panel)
        grid.setContentsMargins(12, 10, 12, 10)
        grid.setHorizontalSpacing(10)
        items = [
            ("codes", "Codigos recentes", "0"),
            ("active", "Acessos ativos", "0"),
            ("errors", "Erros email/API", "0"),
            ("last", "Ultimo criado", "-"),
        ]
        for col, (key, label, value) in enumerate(items):
            card = QFrame()
            card.setObjectName("StatCard")
            box = QVBoxLayout(card)
            box.setContentsMargins(12, 8, 12, 8)
            title = QLabel(label)
            title.setObjectName("StatLabel")
            number = QLabel(value)
            number.setObjectName("StatValue")
            number.setTextInteractionFlags(Qt.TextSelectableByMouse)
            box.addWidget(title)
            box.addWidget(number)
            grid.addWidget(card, 0, col)
            self.summary_values[key] = number
        return panel

    def _access_tab(self):
        page = QWidget()
        lay = QHBoxLayout(page)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(10)

        form = QFrame()
        form.setObjectName("CreateCard")
        form.setMinimumWidth(310)
        form.setMaximumWidth(390)
        form_lay = QVBoxLayout(form)
        form_lay.setContentsMargins(14, 12, 14, 12)
        form_lay.setSpacing(9)

        title = QLabel("Criar acesso")
        title.setObjectName("SectionTitle")
        subtitle = QLabel("Gere um codigo temporario. O tempo comeca quando a pessoa usa pela primeira vez.")
        subtitle.setObjectName("Muted")
        subtitle.setWordWrap(True)
        form_lay.addWidget(title)
        form_lay.addWidget(subtitle)

        self.label_input = QLineEdit()
        self.label_input.setPlaceholderText("Nome/motivo")
        form_lay.addWidget(self.label_input)

        self.manual_code_input = QLineEdit()
        self.manual_code_input.setPlaceholderText("Codigo manual opcional, ex: GXPNRXMXLD")
        form_lay.addWidget(self.manual_code_input)

        spin_row = QHBoxLayout()
        spin_row.setSpacing(8)

        expire_box = QVBoxLayout()
        expire_label = QLabel("Min.")
        expire_label.setObjectName("Muted")
        self.expire_spin = QSpinBox()
        self.expire_spin.setRange(5, 10080)
        self.expire_spin.setValue(20)
        self.expire_spin.setToolTip("O tempo comeca quando a pessoa usa o codigo pela primeira vez.")
        expire_box.addWidget(expire_label)
        expire_box.addWidget(self.expire_spin)
        spin_row.addLayout(expire_box)

        views_box = QVBoxLayout()
        views_label = QLabel("Views")
        views_label.setObjectName("Muted")
        self.views_spin = QSpinBox()
        self.views_spin.setRange(1, 500)
        self.views_spin.setValue(10)
        views_box.addWidget(views_label)
        views_box.addWidget(self.views_spin)
        spin_row.addLayout(views_box)

        ips_box = QVBoxLayout()
        ips_label = QLabel("IPs")
        ips_label.setObjectName("Muted")
        self.max_ips_spin = QSpinBox()
        self.max_ips_spin.setRange(1, 50)
        self.max_ips_spin.setValue(1)
        self.max_ips_spin.setToolTip("1 e mais seguro. Use 2 ou 3 se a pessoa puder trocar de internet.")
        ips_box.addWidget(ips_label)
        ips_box.addWidget(self.max_ips_spin)
        spin_row.addLayout(ips_box)
        form_lay.addLayout(spin_row)

        self.ip_input = QLineEdit()
        self.ip_input.setPlaceholderText("IP fixo opcional. Vazio = qualquer IP")
        form_lay.addWidget(self.ip_input)

        self.last_code_output = QLineEdit()
        self.last_code_output.setReadOnly(True)
        self.last_code_output.setPlaceholderText("Ultimo codigo criado")
        form_lay.addWidget(self.last_code_output)

        copy_btn = QPushButton("Copiar ultimo codigo")
        copy_btn.clicked.connect(self.copy_last_code)
        form_lay.addWidget(copy_btn)

        create_btn = QPushButton("Criar codigo")
        create_btn.setObjectName("Primary")
        create_btn.clicked.connect(self.create_access)
        refresh_btn = QPushButton("Atualizar acessos")
        refresh_btn.clicked.connect(lambda: self.call_api("list_accesses"))
        form_lay.addWidget(create_btn)
        form_lay.addWidget(refresh_btn)

        self.created_label = QLabel("Nenhum codigo criado nesta sessao.")
        self.created_label.setObjectName("Info")
        self.created_label.setWordWrap(True)
        form_lay.addWidget(self.created_label)
        form_lay.addStretch(1)

        form_scroll = QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_scroll.setFrameShape(QFrame.NoFrame)
        form_scroll.setMinimumWidth(320)
        form_scroll.setMaximumWidth(410)
        form_scroll.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        form_scroll.setWidget(form)
        lay.addWidget(form_scroll)

        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(10)

        table_head = QHBoxLayout()
        list_title = QLabel("Acessos temporarios")
        list_title.setObjectName("SectionTitle")
        table_head.addWidget(list_title)
        table_head.addStretch()
        right_lay.addLayout(table_head)

        self.access_table = QTableWidget(0, 8)
        self.access_table.setHorizontalHeaderLabels(["Nome", "Final", "Uso", "IPs", "Expira", "Status", "IPs usados", "ID"])
        self.access_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.access_table.setColumnHidden(7, True)
        self.access_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.access_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.access_table.cellClicked.connect(self.copy_access_cell)
        self.access_table.itemSelectionChanged.connect(self.on_access_selection_changed)
        right_lay.addWidget(self.access_table, 1)

        edit_card = QFrame()
        edit_card.setObjectName("EditCard")
        edit_grid = QGridLayout(edit_card)
        edit_grid.setContentsMargins(12, 10, 12, 10)
        edit_grid.setHorizontalSpacing(10)
        edit_grid.setVerticalSpacing(6)
        edit_title = QLabel("Editar acesso selecionado")
        edit_title.setObjectName("SectionTitle")
        edit_grid.addWidget(edit_title, 0, 0, 1, 6)
        edit_hint = QLabel("Selecione uma linha para alterar tempo, limite, IP, reativar ou apagar.")
        edit_hint.setObjectName("Muted")
        edit_grid.addWidget(edit_hint, 1, 0, 1, 6)

        edit_grid.addWidget(QLabel("Nome/motivo"), 2, 0)
        self.edit_label_input = QLineEdit()
        self.edit_label_input.setPlaceholderText("Selecione um acesso na tabela")
        edit_grid.addWidget(self.edit_label_input, 3, 0, 1, 2)
        edit_grid.addWidget(QLabel("Min."), 2, 2)
        self.edit_expire_spin = QSpinBox()
        self.edit_expire_spin.setRange(5, 10080)
        self.edit_expire_spin.setValue(20)
        edit_grid.addWidget(self.edit_expire_spin, 3, 2)
        edit_grid.addWidget(QLabel("Views"), 2, 3)
        self.edit_views_spin = QSpinBox()
        self.edit_views_spin.setRange(1, 500)
        self.edit_views_spin.setValue(10)
        edit_grid.addWidget(self.edit_views_spin, 3, 3)
        edit_grid.addWidget(QLabel("IPs"), 2, 4)
        self.edit_max_ips_spin = QSpinBox()
        self.edit_max_ips_spin.setRange(1, 50)
        self.edit_max_ips_spin.setValue(1)
        edit_grid.addWidget(self.edit_max_ips_spin, 3, 4)
        edit_grid.addWidget(QLabel("IP fixo"), 2, 5)
        self.edit_ip_input = QLineEdit()
        self.edit_ip_input.setPlaceholderText("Vazio = qualquer IP")
        edit_grid.addWidget(self.edit_ip_input, 3, 5)

        load_edit_btn = QPushButton("Carregar")
        load_edit_btn.clicked.connect(lambda: self.load_selected_for_edit(silent=False))
        save_edit_btn = QPushButton("Salvar ajustes")
        save_edit_btn.setObjectName("Primary")
        save_edit_btn.clicked.connect(self.save_selected_edit)
        revoke_edit_btn = QPushButton("Revogar")
        revoke_edit_btn.setObjectName("Danger")
        revoke_edit_btn.clicked.connect(self.revoke_selected)
        reactivate_edit_btn = QPushButton("Reativar")
        reactivate_edit_btn.clicked.connect(self.reactivate_selected)
        delete_edit_btn = QPushButton("Apagar")
        delete_edit_btn.setObjectName("Danger")
        delete_edit_btn.clicked.connect(self.delete_selected)
        edit_grid.addWidget(load_edit_btn, 4, 0)
        edit_grid.addWidget(save_edit_btn, 4, 1)
        edit_grid.addWidget(revoke_edit_btn, 4, 2)
        edit_grid.addWidget(reactivate_edit_btn, 4, 3)
        edit_grid.addWidget(delete_edit_btn, 4, 4, 1, 2)
        right_lay.addWidget(edit_card)

        self.access_history_label = QLabel("Historico do acesso selecionado")
        self.access_history_label.setObjectName("Info")
        right_lay.addWidget(self.access_history_label)
        self.access_history_table = QTableWidget(0, 4)
        self.access_history_table.setHorizontalHeaderLabels(["Horario", "Acao", "Detalhes", "IP"])
        self.access_history_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.access_history_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.access_history_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.access_history_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.access_history_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.access_history_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.access_history_table.setMaximumHeight(120)
        self.access_history_table.cellClicked.connect(self.copy_history_cell)
        right_lay.addWidget(self.access_history_table)
        lay.addWidget(right, 1)
        return page

    def _codes_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 10, 0, 0)
        top = QHBoxLayout()
        fetch_btn = QPushButton("Buscar codigos agora")
        fetch_btn.clicked.connect(lambda: self.call_api("codes", {"force_refresh": True}))
        top.addWidget(fetch_btn)
        top.addStretch()
        lay.addLayout(top)
        self.codes_table = QTableWidget(0, 4)
        self.codes_table.setHorizontalHeaderLabels(["Codigo", "Data/Hora", "Expira", "Email"])
        self.codes_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.codes_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.codes_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.codes_table.cellClicked.connect(self.copy_code_cell)
        lay.addWidget(self.codes_table, 1)
        return page

    def _logs_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 10, 0, 0)
        lay.setSpacing(10)

        top = QHBoxLayout()
        self.logs_summary = QLabel("Nenhum log carregado.")
        self.logs_summary.setObjectName("Info")
        top.addWidget(self.logs_summary, 1)
        self.log_filter = QComboBox()
        self.log_filter.addItems(["Todos", "Erros", "Acessos", "Codigos copiados", "Consultas"])
        self.log_filter.currentIndexChanged.connect(lambda _index: self.render_logs())
        top.addWidget(self.log_filter)
        btn = QPushButton("Atualizar logs")
        btn.clicked.connect(lambda: self.call_api("logs"))
        top.addWidget(btn)
        lay.addLayout(top)

        self.logs_table = QTableWidget(0, 4)
        self.logs_table.setHorizontalHeaderLabels(["Horario", "Acao", "IP", "Detalhes"])
        self.logs_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.logs_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.logs_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.logs_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.Stretch)
        self.logs_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.logs_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.logs_table.cellClicked.connect(self.copy_log_cell)
        lay.addWidget(self.logs_table, 1)
        return page

    def _load_fields(self):
        self.url_input.setText(self.settings.get("base_url", ""))
        self.token_input.setText(self.settings.get("token", ""))

    def save_settings(self):
        self.settings = {"base_url": self.url_input.text().strip(), "token": self.token_input.text().strip()}
        _save_settings(self.settings)
        self.set_status("Configuracao salva", ok=True)

    def refresh_all(self):
        self.queue_api([
            ("cleanup", {}),
            ("ping", {}),
            ("list_accesses", {}),
            ("codes", {"force_refresh": True}),
            ("logs", {}),
        ])

    def refresh_light(self):
        if not self.settings.get("token"):
            return
        if self.worker and self.worker.isRunning():
            return
        self.queue_api([
            ("list_accesses", {}),
            ("codes", {}),
            ("logs", {}),
        ])

    def queue_api(self, actions):
        self._pending_actions.extend(actions)
        if not (self.worker and self.worker.isRunning()):
            self._start_next_api()

    def _start_next_api(self):
        if not self._pending_actions:
            return
        action, payload = self._pending_actions.pop(0)
        self.call_api(action, payload, queued=True)

    def call_api(self, action: str, payload: dict | None = None, queued: bool = False):
        self.save_settings()
        if not self.settings.get("token"):
            self._pending_actions.clear()
            QMessageBox.warning(self, "Codigos Email", "Preencha o token admin primeiro.")
            return
        if self.worker and self.worker.isRunning():
            if queued:
                self._pending_actions.insert(0, (action, payload or {}))
            else:
                self.set_status("Aguarde a requisicao atual terminar", ok=False)
            return
        self.set_status(f"Executando {action}...", pending=True)
        self._task_running(action, payload or {})
        self.worker = EmailCodesApiWorker(action, self.settings["base_url"], self.settings["token"], payload, self)
        self.worker.result.connect(self.on_api_result)
        self.worker.finished.connect(self._clear_worker)
        self.worker.finished.connect(lambda: QTimer.singleShot(120, self._start_next_api))
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _clear_worker(self):
        self.worker = None

    def _task_running(self, action: str, payload: dict):
        if not get_app_store:
            return
        try:
            get_app_store().upsert_task(
                f"email-codes:{action}",
                "email-codes-api",
                f"Codigos Email: {action}",
                source="email_codes",
                status="running",
                priority=45,
                payload=payload,
            )
        except Exception:
            pass

    def _task_done(self, action: str, status: str, error: str = ""):
        if not get_app_store:
            return
        try:
            get_app_store().update_task(
                f"email-codes:{action}",
                status=status,
                last_error=error,
                attempts_delta=1 if status == "error" else 0,
            )
        except Exception:
            pass

    def on_api_result(self, action: str, data, error: str):
        if error:
            self.set_status(error, ok=False)
            self._task_done(action, "error", error)
            return
        self._task_done(action, "success", "")
        self.set_status("Online", ok=True)
        if action == "ping":
            self.set_status("Conexao OK", ok=True)
        elif action == "cleanup":
            self._update_cleanup_summary(data.get("cleanup", {}))
        elif action == "list_accesses":
            self.accesses = data.get("accesses", [])
            self._update_cleanup_summary(data.get("cleanup", {}))
            self.render_accesses()
        elif action == "create_access":
            self.last_created_code = data.get("access_code", "")
            self.last_code_output.setText(self.last_created_code)
            self.summary_values.get("last", QLabel()).setText(self.last_created_code)
            self.created_label.setText("Codigo criado e copiado. A tabela mostra apenas o final por seguranca.")
            QApplication.clipboard().setText(self.last_created_code)
            self._pending_actions.append(("list_accesses", {}))
        elif action in {"revoke_access", "update_access", "reactivate_access", "delete_access"}:
            if action == "delete_access":
                self._loaded_access_id = ""
                self.edit_label_input.clear()
                self.edit_ip_input.clear()
            self._pending_actions.append(("list_accesses", {}))
            self._pending_actions.append(("logs", {}))
        elif action == "codes":
            self.codes = data.get("codes", [])
            self.render_codes()
        elif action == "logs":
            self.logs = data.get("logs", [])
            self._update_cleanup_summary(data.get("cleanup", {}))
            self.render_logs()
            self.render_access_history()
        self.update_summary_cards()

    def create_access(self):
        self.call_api("create_access", {
            "label": self.label_input.text().strip() or "Visitante",
            "access_code": self.manual_code_input.text().strip().upper(),
            "expires_minutes": self.expire_spin.value(),
            "max_views": self.views_spin.value(),
            "max_ips": self.max_ips_spin.value(),
            "allowed_ip": self.ip_input.text().strip(),
        })

    def selected_access_id(self):
        rows = self.access_table.selectionModel().selectedRows() if self.access_table.selectionModel() else []
        if not rows:
            return ""
        item = self.access_table.item(rows[0].row(), 7)
        return item.text() if item else ""

    def revoke_selected(self):
        access_id = self.selected_access_id()
        if not access_id:
            QMessageBox.warning(self, "Codigos Email", "Selecione um acesso para revogar.")
            return
        self.call_api("revoke_access", {"id": access_id})

    def on_access_selection_changed(self):
        self.load_selected_for_edit(silent=True)
        self.render_access_history()

    def load_selected_for_edit(self, silent: bool = False):
        access = self._selected_access()
        if not access:
            if not silent:
                QMessageBox.information(self, "Codigos Email", "Selecione um acesso na tabela.")
            return
        self._loaded_access_id = str(access.get("id", ""))
        self.edit_label_input.setText(str(access.get("label", "")))
        try:
            self.edit_expire_spin.setValue(max(5, int(access.get("expires_minutes", 20) or 20)))
        except Exception:
            self.edit_expire_spin.setValue(20)
        try:
            self.edit_views_spin.setValue(max(1, int(access.get("max_views", 10) or 10)))
        except Exception:
            self.edit_views_spin.setValue(10)
        try:
            self.edit_max_ips_spin.setValue(max(1, int(access.get("max_ips", 1) or 1)))
        except Exception:
            self.edit_max_ips_spin.setValue(1)
        self.edit_ip_input.setText(str(access.get("allowed_ip", "")))

    def save_selected_edit(self):
        access_id = self._loaded_access_id or self.selected_access_id()
        if not access_id:
            QMessageBox.warning(self, "Codigos Email", "Selecione um acesso para editar.")
            return
        self.call_api("update_access", {
            "id": access_id,
            "label": self.edit_label_input.text().strip() or "Visitante",
            "expires_minutes": self.edit_expire_spin.value(),
            "max_views": self.edit_views_spin.value(),
            "max_ips": self.edit_max_ips_spin.value(),
            "allowed_ip": self.edit_ip_input.text().strip(),
        })

    def reactivate_selected(self):
        access_id = self.selected_access_id() or self._loaded_access_id
        if not access_id:
            QMessageBox.warning(self, "Codigos Email", "Selecione um acesso para reativar.")
            return
        self.call_api("reactivate_access", {"id": access_id})

    def delete_selected(self):
        access_id = self.selected_access_id() or self._loaded_access_id
        if not access_id:
            QMessageBox.warning(self, "Codigos Email", "Selecione um acesso para apagar.")
            return
        reply = QMessageBox.question(
            self,
            "Apagar acesso",
            "Apagar este acesso da lista? Isso remove o registro do painel, mas mantem logs antigos.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        self.call_api("delete_access", {"id": access_id})

    def copy_last_code(self):
        code = self.last_created_code or self.last_code_output.text().strip()
        if not code:
            QMessageBox.information(self, "Codigos Email", "Nenhum codigo criado nesta sessao.")
            return
        QApplication.clipboard().setText(code)
        self.set_status("Codigo copiado", ok=True)

    @staticmethod
    def _used_ips(item: dict) -> list:
        seen = []
        raw_ips = item.get("used_ips", [])
        if not isinstance(raw_ips, list):
            raw_ips = []
        for value in list(raw_ips) + [item.get("first_ip", ""), item.get("last_ip", "")]:
            text = str(value or "").strip()
            if text and text not in seen:
                seen.append(text)
        return seen

    def _used_ip_count(self, item: dict) -> int:
        count = item.get("used_ip_count", None)
        try:
            return max(0, int(count))
        except Exception:
            return len(self._used_ips(item))

    def _ip_summary(self, item: dict) -> str:
        fixed_ip = str(item.get("allowed_ip", "") or "").strip()
        used = self._used_ips(item)
        parts = []
        if used:
            parts.append("usados: " + ", ".join(used))
        if fixed_ip:
            parts.append("fixo: " + fixed_ip)
        return " | ".join(parts) if parts else "qualquer IP"

    def render_accesses(self):
        self.access_table.setRowCount(len(self.accesses))
        for row, item in enumerate(self.accesses):
            status = self._access_status(item)
            expires_at = item.get("expires_at") or "ao primeiro uso"
            values = [
                item.get("label", ""),
                "****" + str(item.get("code_preview", "")),
                f"{item.get('view_count', 0)}/{item.get('max_views', 0)}",
                f"{self._used_ip_count(item)}/{max(1, int(item.get('max_ips', 1) or 1))}",
                expires_at,
                status,
                self._ip_summary(item),
                item.get("id", ""),
            ]
            for col, value in enumerate(values):
                self.access_table.setItem(row, col, QTableWidgetItem(str(value)))
        self.update_summary_cards()
        self.render_access_history()

    def _access_status(self, item: dict) -> str:
        if bool(item.get("revoked")):
            return "revogado"
        if int(item.get("view_count", 0) or 0) >= int(item.get("max_views", 0) or 0):
            return "limite"
        expires_at = str(item.get("expires_at") or "").strip()
        if not expires_at:
            return "aguardando uso"
        try:
            exp = datetime.fromisoformat(expires_at.replace("Z", "+00:00"))
            if exp.tzinfo is None:
                exp = exp.replace(tzinfo=timezone.utc)
            if exp < datetime.now(exp.tzinfo):
                return "expirado"
        except Exception:
            pass
        return "ativo"

    def render_codes(self):
        self.codes_table.setRowCount(len(self.codes))
        for row, item in enumerate(self.codes):
            values = [
                item.get("code", ""),
                item.get("date", ""),
                self._format_seconds(item.get("remaining_seconds", "")),
                item.get("to_masked", "") or self._mask_email(item.get("to", "")),
            ]
            for col, value in enumerate(values):
                self.codes_table.setItem(row, col, QTableWidgetItem(str(value)))
        self.update_summary_cards()

    @staticmethod
    def _format_seconds(value) -> str:
        try:
            seconds = max(0, int(value))
        except Exception:
            return ""
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    @staticmethod
    def _mask_email(value: str) -> str:
        text = str(value or "")
        if "@" not in text:
            return ""
        email = text.replace("<", " ").replace(">", " ").split()
        email = next((part for part in email if "@" in part), "")
        if not email:
            return ""
        local, _, domain = email.lower().partition("@")
        if len(local) < 5:
            return "***@" + domain
        return local[: min(3, len(local) - 2)] + "*****" + local[-2:] + "@" + domain

    def render_logs(self):
        visible_logs = self._filtered_logs(self.logs[:300])
        errors = sum(1 for item in visible_logs if self._log_kind(item.get("type", "")) == "error")
        self.logs_summary.setText(f"{len(visible_logs)} evento(s) carregado(s). Erros/alertas: {errors}. Clique em uma linha para copiar.")
        self.logs_table.setRowCount(len(visible_logs))
        for row, item in enumerate(visible_logs):
            raw_type = str(item.get("type", ""))
            values = [
                self._format_log_time(item.get("time", "")),
                self._human_log_type(raw_type),
                str(item.get("ip", "")),
                self._human_log_details(raw_type, item.get("meta", {})),
            ]
            raw = json.dumps(item, ensure_ascii=False)
            for col, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                table_item.setToolTip(raw)
                if self._log_kind(raw_type) == "error":
                    table_item.setData(Qt.ForegroundRole, QColor("#fb7185"))
                elif self._log_kind(raw_type) == "success":
                    table_item.setData(Qt.ForegroundRole, QColor("#34d399"))
                self.logs_table.setItem(row, col, table_item)
        self.update_summary_cards()

    def _filtered_logs(self, logs):
        selected = self.log_filter.currentText() if getattr(self, "log_filter", None) else "Todos"
        if selected == "Todos":
            return logs
        return [item for item in logs if self._log_category(str(item.get("type", ""))) == selected]

    @staticmethod
    def _log_category(raw_type: str) -> str:
        text = str(raw_type or "")
        if "failed" in text or "error" in text or "blocked" in text:
            return "Erros"
        if "access" in text or "viewer_" in text or "login" in text or "logout" in text:
            return "Acessos"
        if "copied" in text or text == "code_copied":
            return "Codigos copiados"
        if "codes_fetched" in text or "refreshed_codes" in text or "opened_codes" in text:
            return "Consultas"
        return "Todos"

    @staticmethod
    def _format_log_time(value) -> str:
        text = str(value or "").strip()
        if not text:
            return ""
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return dt.strftime("%d/%m %H:%M:%S")
        except Exception:
            return text.replace("T", " ")

    @staticmethod
    def _human_log_type(value: str) -> str:
        labels = {
            "api_codes_fetched": "Projeto buscou codigos",
            "viewer_refreshed_codes": "Pessoa atualizou codigos",
            "viewer_opened_codes": "Pessoa abriu painel",
            "viewer_login_ok": "Login com codigo",
            "viewer_login_failed": "Codigo temporario errado",
            "viewer_ip_blocked": "IP bloqueado",
            "viewer_browser_blocked": "Navegador bloqueado",
            "viewer_copied_code": "Codigo copiado",
            "code_copied": "Codigo copiado",
            "api_access_created": "Codigo de acesso criado",
            "access_code_created": "Codigo de acesso criado",
            "api_access_revoked": "Acesso revogado",
            "access_code_revoked": "Acesso revogado",
            "api_access_updated": "Acesso editado",
            "api_access_reactivated": "Acesso reativado",
            "api_access_deleted": "Acesso apagado",
            "api_auth_failed": "Falha de token/admin",
            "api_error": "Erro da API",
            "admin_login_ok": "Admin entrou",
            "admin_login_failed": "Tentativa admin falhou",
            "admin_opened_codes": "Admin abriu codigos",
            "logout": "Saiu do painel",
            "imap_error": "Erro ao ler email",
        }
        return labels.get(str(value or ""), str(value or "Evento"))

    @staticmethod
    def _log_kind(value: str) -> str:
        text = str(value or "")
        if "failed" in text or "error" in text or "blocked" in text:
            return "error"
        if text.endswith("_ok") or any(word in text for word in ("created", "copied", "updated", "reactivated", "deleted", "revoked")):
            return "success"
        return "normal"

    def _human_log_details(self, raw_type: str, meta) -> str:
        if not isinstance(meta, dict):
            return str(meta or "")
        parts = []
        label = str(meta.get("label") or "").strip()
        if label:
            parts.append(f"Acesso: {label}")
        if "codes_count" in meta:
            parts.append(f"Codigos vistos: {meta.get('codes_count')}")
        if "code_preview" in meta:
            parts.append(f"Final do codigo: ****{meta.get('code_preview')}")
        if "view_count" in meta:
            parts.append(f"Uso: {meta.get('view_count')}")
        if "max_views" in meta:
            parts.append(f"Limite: {meta.get('max_views')}")
        if "max_ips" in meta:
            parts.append(f"IPs permitidos: {meta.get('max_ips')}")
        if "used_ips" in meta and isinstance(meta.get("used_ips"), list):
            ips = [str(ip) for ip in meta.get("used_ips") if str(ip).strip()]
            if ips:
                parts.append("IPs usados: " + ", ".join(ips))
        if "minutes" in meta:
            parts.append(f"Tempo: {meta.get('minutes')} min")
        if "expires_at" in meta:
            parts.append(f"Expira: {self._format_log_time(meta.get('expires_at'))}")
        if "message" in meta:
            parts.append(str(meta.get("message"))[:180])
        if not parts and meta:
            parts.append(json.dumps(meta, ensure_ascii=False)[:220])
        if not parts:
            if raw_type == "api_codes_fetched":
                return "Consulta feita pelo projeto principal."
            if raw_type == "api_auth_failed":
                return "Token invalido ou configuracao diferente."
            return ""
        return " | ".join(parts)

    def update_summary_cards(self):
        active = sum(1 for item in self.accesses if self._access_status(item) in {"ativo", "aguardando uso"})
        errors = sum(1 for item in self.logs[:300] if self._log_kind(item.get("type", "")) == "error")
        if "codes" in self.summary_values:
            self.summary_values["codes"].setText(str(len(self.codes)))
        if "active" in self.summary_values:
            self.summary_values["active"].setText(str(active))
        if "errors" in self.summary_values:
            self.summary_values["errors"].setText(str(errors))
        if "last" in self.summary_values:
            self.summary_values["last"].setText(self.last_created_code or "-")

    def _update_cleanup_summary(self, cleanup):
        if not isinstance(cleanup, dict):
            return
        removed = int(cleanup.get("accesses_removed", 0) or 0) + int(cleanup.get("logs_removed", 0) or 0)
        if removed:
            self.set_status(f"Limpeza automatica removeu {removed} registro(s)", ok=True)

    def _selected_access(self):
        access_id = self.selected_access_id()
        if not access_id:
            return None
        for item in self.accesses:
            if str(item.get("id", "")) == access_id:
                return item
        return None

    def render_access_history(self):
        if not getattr(self, "access_history_table", None):
            return
        access = self._selected_access()
        if not access:
            self.access_history_label.setText("Historico do acesso selecionado")
            self.access_history_table.setRowCount(0)
            return
        access_id = str(access.get("id", ""))
        label = str(access.get("label", ""))
        related = []
        for item in self.logs[:300]:
            meta = item.get("meta", {})
            if not isinstance(meta, dict):
                continue
            if access_id and str(meta.get("access_id", "")) == access_id:
                related.append(item)
            elif label and str(meta.get("label", "")) == label:
                related.append(item)
        self.access_history_label.setText(f"Historico de {label or 'acesso'}: {len(related)} evento(s)")
        self.access_history_table.setRowCount(len(related[:30]))
        for row, item in enumerate(related[:30]):
            raw_type = str(item.get("type", ""))
            values = [
                self._format_log_time(item.get("time", "")),
                self._human_log_type(raw_type),
                self._human_log_details(raw_type, item.get("meta", {})),
                str(item.get("ip", "")),
            ]
            for col, value in enumerate(values):
                table_item = QTableWidgetItem(value)
                if self._log_kind(raw_type) == "error":
                    table_item.setData(Qt.ForegroundRole, QColor("#fb7185"))
                elif self._log_kind(raw_type) == "success":
                    table_item.setData(Qt.ForegroundRole, QColor("#34d399"))
                self.access_history_table.setItem(row, col, table_item)

    def copy_access_cell(self, row, col):
        item = self.access_table.item(row, col)
        if item:
            QApplication.clipboard().setText(item.text())

    def copy_code_cell(self, row, col):
        item = self.codes_table.item(row, col)
        if item:
            QApplication.clipboard().setText(item.text())

    def copy_log_cell(self, row, col):
        values = []
        for idx in range(self.logs_table.columnCount()):
            item = self.logs_table.item(row, idx)
            values.append(item.text() if item else "")
        QApplication.clipboard().setText(" | ".join(values).strip())
        self.set_status("Log copiado", ok=True)

    def copy_history_cell(self, row, col):
        values = []
        for idx in range(self.access_history_table.columnCount()):
            item = self.access_history_table.item(row, idx)
            values.append(item.text() if item else "")
        QApplication.clipboard().setText(" | ".join(values).strip())
        self.set_status("Historico copiado", ok=True)

    def set_status(self, text: str, ok: bool = False, pending: bool = False):
        self.status_badge.setText(text[:80])
        self.status_badge.setProperty("state", "pending" if pending else ("ok" if ok else "error"))
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    @staticmethod
    def _qss():
        return (
            DARK_STYLE_PRO
            + tabs_qss(compact=True)
            + table_qss(compact=True)
            + f"""
            QFrame#Hero, QFrame#Card, QFrame#CreateCard, QFrame#EditCard {{
                background: {PALETTE.card};
                border: 1px solid {PALETTE.border};
                border-radius: 10px;
            }}
            QFrame#Summary {{
                background: transparent;
                border: 0;
            }}
            QFrame#StatCard {{
                background: {PALETTE.card};
                border: 1px solid {PALETTE.border};
                border-radius: 8px;
            }}
            QLabel#Title {{
                font-size: 22px;
                font-weight: 900;
                color: {PALETTE.text};
            }}
            QLabel#Subtitle, QLabel#Info, QLabel#Muted {{
                color: {PALETTE.muted};
            }}
            QLabel#SectionTitle {{
                color: {PALETTE.text};
                font-size: 14px;
                font-weight: 900;
            }}
            QLabel#StatLabel {{
                color: {PALETTE.muted};
                font-size: 11px;
                font-weight: 800;
            }}
            QLabel#StatValue {{
                color: #67e8f9;
                font-size: 20px;
                font-weight: 900;
            }}
            QLabel#Badge {{
                min-width: 126px;
                min-height: 38px;
                padding: 7px 11px;
                border-radius: 8px;
                font-weight: 900;
                border: 1px solid rgba(148,163,184,.20);
                background: #111827;
                color: #cbd5e1;
            }}
            QLabel#Badge[state="ok"] {{
                background: #052e25;
                color: #34d399;
                border-color: #10b981;
            }}
            QLabel#Badge[state="error"] {{
                background: #3f1111;
                color: #fecaca;
                border-color: #ef4444;
            }}
            QLabel#Badge[state="pending"] {{
                background: #172554;
                color: #93c5fd;
                border-color: #3b82f6;
            }}
            QScrollArea {{
                background: transparent;
                border: 0;
            }}
            QScrollArea > QWidget > QWidget {{
                background: transparent;
            }}
            QFrame#CreateCard QLineEdit,
            QFrame#CreateCard QSpinBox,
            QFrame#EditCard QLineEdit,
            QFrame#EditCard QSpinBox {{
                min-height: 28px;
                padding: 4px 8px;
            }}
            QFrame#CreateCard QPushButton,
            QFrame#EditCard QPushButton {{
                min-height: 30px;
                padding: 5px 10px;
            }}
            """
        )
