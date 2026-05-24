#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Painel admin para mensagens recebidas pelo site BOBOBU."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from PyQt5.QtCore import Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.app_theme import DARK_STYLE_PRO
from app.ui.components import PALETTE, table_qss

from app.core.paths import CONFIG_DIR


SETTINGS_FILE = CONFIG_DIR / "site_leads_admin.json"


def _load_settings() -> dict:
    try:
        if SETTINGS_FILE.exists():
            return json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except Exception:
        pass
    return {"base_url": "https://bobobu.com.br", "token": ""}


def _save_settings(data: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    SETTINGS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _api_url(base_url: str) -> str:
    base = (base_url or "").strip().rstrip("/")
    if not base:
        raise ValueError("Informe a URL do site.")
    return f"{base}/api/leads.php"


class SiteLeadsApiWorker(QThread):
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
                    "User-Agent": "TelegramPro-SiteLeads/1.0",
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
            self.result.emit(self.action, {}, f"HTTP {exc.code}: {text[:360]}")
        except Exception as exc:
            self.result.emit(self.action, {}, str(exc))


class SiteLeadsAdminWidget(QWidget):
    """Lista mensagens enviadas pelo formulario da pagina inicial."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.settings = _load_settings()
        self.worker = None
        self.leads = []
        self.logs = []
        self._pending_actions = []
        self._build_ui()
        self._load_fields()
        self.refresh_timer = QTimer(self)
        self.refresh_timer.setInterval(60000)
        self.refresh_timer.timeout.connect(self.refresh_light)
        self.refresh_timer.start()
        if self.settings.get("token"):
            QTimer.singleShot(600, self.refresh_all)

    def _build_ui(self):
        self.setStyleSheet(self._qss())
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 16, 18, 16)
        root.setSpacing(12)

        hero = QFrame()
        hero.setObjectName("Hero")
        hero_lay = QHBoxLayout(hero)
        hero_lay.setContentsMargins(18, 14, 18, 14)
        title_box = QVBoxLayout()
        title = QLabel("Leads Site")
        title.setObjectName("Title")
        subtitle = QLabel("Receba WhatsApp, Telegram, Discord, pedido e descricao enviados pela pagina BOBOBU.")
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
        grid.setContentsMargins(14, 12, 14, 12)
        grid.setHorizontalSpacing(10)
        grid.setVerticalSpacing(8)
        grid.addWidget(QLabel("URL do site"), 0, 0)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://bobobu.com.br")
        grid.addWidget(self.url_input, 0, 1, 1, 3)
        grid.addWidget(QLabel("Token"), 1, 0)
        self.token_input = QLineEdit()
        self.token_input.setEchoMode(QLineEdit.Password)
        self.token_input.setPlaceholderText("Mesmo site_admin_token do config.php")
        grid.addWidget(self.token_input, 1, 1, 1, 3)
        save_btn = QPushButton("Salvar")
        save_btn.clicked.connect(self.save_settings)
        refresh_btn = QPushButton("Atualizar")
        refresh_btn.clicked.connect(self.refresh_all)
        grid.addWidget(save_btn, 2, 2)
        grid.addWidget(refresh_btn, 2, 3)
        root.addWidget(config)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(["Data", "Status", "WhatsApp", "Telegram", "Discord", "Pedido", "Descricao", "ID"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellClicked.connect(self.copy_cell)
        root.addWidget(self.table, 1)

        actions = QHBoxLayout()
        copy_btn = QPushButton("Copiar contato")
        copy_btn.clicked.connect(self.copy_selected_contact)
        done_btn = QPushButton("Marcar contatado")
        done_btn.clicked.connect(self.mark_contacted)
        delete_btn = QPushButton("Excluir selecionado")
        delete_btn.setObjectName("Danger")
        delete_btn.clicked.connect(self.delete_selected)
        logs_btn = QPushButton("Ver logs")
        logs_btn.clicked.connect(lambda: self.call_api("logs"))
        actions.addWidget(copy_btn)
        actions.addWidget(done_btn)
        actions.addWidget(delete_btn)
        actions.addWidget(logs_btn)
        root.addLayout(actions)

        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setMaximumHeight(130)
        self.logs_text.setPlaceholderText("Logs aparecem aqui quando voce clicar em Ver logs.")
        root.addWidget(self.logs_text)

    def _load_fields(self):
        self.url_input.setText(self.settings.get("base_url", ""))
        self.token_input.setText(self.settings.get("token", ""))

    def save_settings(self):
        self.settings = {"base_url": self.url_input.text().strip(), "token": self.token_input.text().strip()}
        _save_settings(self.settings)
        self.set_status("Configuracao salva", ok=True)

    def refresh_all(self):
        self.queue_api([("ping", {}), ("list_leads", {}), ("logs", {})])

    def refresh_light(self):
        if not self.settings.get("token"):
            return
        if self.worker and self.worker.isRunning():
            return
        self.queue_api([("list_leads", {})])

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
            QMessageBox.warning(self, "Leads Site", "Preencha o token admin primeiro.")
            return
        if self.worker and self.worker.isRunning():
            if queued:
                self._pending_actions.insert(0, (action, payload or {}))
            else:
                self.set_status("Aguarde a requisicao atual terminar", ok=False)
            return
        self.set_status(f"Executando {action}...", pending=True)
        self.worker = SiteLeadsApiWorker(action, self.settings["base_url"], self.settings["token"], payload, self)
        self.worker.result.connect(self.on_api_result)
        self.worker.finished.connect(self._clear_worker)
        self.worker.finished.connect(lambda: QTimer.singleShot(120, self._start_next_api))
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.start()

    def _clear_worker(self):
        self.worker = None

    def on_api_result(self, action: str, data, error: str):
        if error:
            self.set_status(error, ok=False)
            return
        self.set_status("Online", ok=True)
        if action == "list_leads":
            self.leads = data.get("leads", [])
            self.render_leads()
        elif action in {"mark_contacted", "delete_lead"}:
            self._pending_actions.append(("list_leads", {}))
        elif action == "logs":
            self.logs = data.get("logs", [])
            self.render_logs()
        elif action == "ping":
            self.set_status("Conexao OK", ok=True)

    def render_leads(self):
        self.table.setRowCount(len(self.leads))
        for row, item in enumerate(self.leads):
            values = [
                item.get("created_at", ""),
                item.get("status", ""),
                item.get("whatsapp", ""),
                item.get("telegram", ""),
                item.get("discord", ""),
                item.get("order_number", ""),
                item.get("description", ""),
                item.get("id", ""),
            ]
            for col, value in enumerate(values):
                table_item = QTableWidgetItem(str(value))
                if col == 7:
                    table_item.setData(Qt.UserRole, item.get("id", ""))
                self.table.setItem(row, col, table_item)

    def render_logs(self):
        lines = []
        for item in self.logs[:120]:
            lines.append(f"{item.get('time', '')} | {item.get('type', '')} | {item.get('ip', '')} | {json.dumps(item.get('meta', {}), ensure_ascii=False)}")
        self.logs_text.setPlainText("\n".join(lines))

    def selected_lead(self) -> dict | None:
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return None
        row = rows[0].row()
        if 0 <= row < len(self.leads):
            return self.leads[row]
        return None

    def selected_id(self) -> str:
        lead = self.selected_lead()
        return str((lead or {}).get("id", ""))

    def copy_cell(self, row, col):
        item = self.table.item(row, col)
        if item:
            QApplication.clipboard().setText(item.text())
            self.set_status("Campo copiado", ok=True)

    def copy_selected_contact(self):
        lead = self.selected_lead()
        if not lead:
            QMessageBox.information(self, "Leads Site", "Selecione uma mensagem.")
            return
        text = (
            f"WhatsApp: {lead.get('whatsapp', '')}\n"
            f"Telegram: {lead.get('telegram', '')}\n"
            f"Discord: {lead.get('discord', '')}\n"
            f"Pedido: {lead.get('order_number', '')}\n"
            f"Descricao: {lead.get('description', '')}"
        )
        QApplication.clipboard().setText(text)
        self.set_status("Contato copiado", ok=True)

    def mark_contacted(self):
        lead_id = self.selected_id()
        if not lead_id:
            QMessageBox.information(self, "Leads Site", "Selecione uma mensagem.")
            return
        self.call_api("mark_contacted", {"id": lead_id})

    def delete_selected(self):
        lead_id = self.selected_id()
        if not lead_id:
            QMessageBox.information(self, "Leads Site", "Selecione uma mensagem.")
            return
        self.call_api("delete_lead", {"id": lead_id})

    def set_status(self, text: str, ok: bool = False, pending: bool = False):
        self.status_badge.setText(text[:90])
        self.status_badge.setProperty("state", "pending" if pending else ("ok" if ok else "error"))
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    @staticmethod
    def _qss():
        return (
            DARK_STYLE_PRO
            + table_qss(compact=True)
            + f"""
            QFrame#Hero, QFrame#Card {{
                background: {PALETTE.card};
                border: 1px solid {PALETTE.border};
                border-radius: 10px;
            }}
            QLabel#Title {{
                font-size: 22px;
                font-weight: 900;
                color: {PALETTE.text};
            }}
            QLabel#Subtitle {{
                color: {PALETTE.muted};
            }}
            QLabel#Badge {{
                min-width: 130px;
                min-height: 38px;
                padding: 7px 11px;
                border-radius: 8px;
                font-weight: 900;
                border: 1px solid rgba(148,163,184,.20);
                background: #111827;
                color: #cbd5e1;
            }}
            QLabel#Badge[state="ok"] {{ background:#052e25; color:#34d399; border-color:#10b981; }}
            QLabel#Badge[state="error"] {{ background:#3f1111; color:#fecaca; border-color:#ef4444; }}
            QLabel#Badge[state="pending"] {{ background:#172554; color:#93c5fd; border-color:#3b82f6; }}
            """
        )
