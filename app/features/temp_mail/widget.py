#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Gerador de contas temporarias Mail.tm em lote."""

from __future__ import annotations

import json
import random
import string
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.paths import APP_DATA_DIR
from app.ui.app_theme import DARK_STYLE_PRO
from app.ui.components import PALETTE, scroll_qss, table_qss

try:
    from app.core.app_context import get_app_store
except Exception:
    get_app_store = None


DATA_FILE = APP_DATA_DIR / "temp_mail_accounts.json"
API_BASE = "https://api.mail.tm"
API_ATTRIBUTION = "Mail.tm"


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _safe_read_json(path: Path, default):
    try:
        if path.exists():
            return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        pass
    return default


def _safe_write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def _rand_text(length: int = 10) -> str:
    alphabet = string.ascii_lowercase + string.digits
    return "".join(random.choice(alphabet) for _ in range(length))


def _make_password() -> str:
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(14))


class MailTmClient:
    def request(self, method: str, path: str, payload: Optional[dict] = None, token: str = ""):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "TelegramPro-TempMail/1.0",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"
        req = urllib.request.Request(f"{API_BASE}{path}", data=data, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=25) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            return json.loads(raw) if raw else {}

    def domains(self) -> List[str]:
        data = self.request("GET", "/domains")
        items = data.get("hydra:member") or data.get("domains") or []
        domains = []
        for item in items:
            if item.get("isActive", True) and item.get("domain"):
                domains.append(item["domain"])
        return domains

    def create_account(self, address: str, password: str) -> dict:
        return self.request("POST", "/accounts", {"address": address, "password": password})

    def token(self, address: str, password: str) -> str:
        data = self.request("POST", "/token", {"address": address, "password": password})
        return data.get("token", "")

    def me(self, token: str) -> dict:
        return self.request("GET", "/me", token=token)

    def messages(self, token: str) -> List[dict]:
        data = self.request("GET", "/messages", token=token)
        return data.get("hydra:member") or data.get("messages") or []


class TempMailBatchWorker(QThread):
    progress = pyqtSignal(dict)
    finished_batch = pyqtSignal(list, str)

    def __init__(self, count: int, fixed_password: str, prefix: str, existing: set[str], custom_email: str = "", parent=None):
        super().__init__(parent)
        self.count = max(1, min(50, int(count)))
        self.fixed_password = fixed_password.strip()
        self.prefix = "".join(ch for ch in prefix.strip().lower() if ch.isalnum())[:18]
        self.existing = set(existing)
        self.custom_email = (custom_email or "").strip().lower()
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        client = MailTmClient()
        created = []
        try:
            domains = self._with_retry("dominios", client.domains, max_attempts=5)
            if not domains:
                self.finished_batch.emit([], "Nenhum dominio ativo retornado pelo Mail.tm.")
                return
            domain = domains[0]
            wanted = 1 if self.custom_email else self.count
            attempts_without_success = 0
            while len(created) < wanted and not self._stop:
                if self._stop:
                    break
                address = self._custom_or_unique_address(domain)
                password = self.fixed_password or _make_password()
                account = {
                    "email": address,
                    "password": password,
                    "domain": domain,
                    "created_at": _now(),
                    "status": "criando",
                    "token": "",
                    "source": API_ATTRIBUTION,
                }
                try:
                    self._with_retry(f"criar {address}", lambda: client.create_account(address, password))
                    time.sleep(0.9)
                    token = self._with_retry(f"token {address}", lambda: client.token(address, password))
                    verified = self._with_retry(f"validar {address}", lambda: client.me(token), max_attempts=3)
                    account["token"] = token
                    account["mailtm_id"] = verified.get("id", "")
                    account["status"] = "ok verificado" if token and verified else "sem token"
                    created.append(account)
                    attempts_without_success = 0
                    self.progress.emit({"index": len(created), "total": wanted, "account": account, "save": True})
                except urllib.error.HTTPError as exc:
                    attempts_without_success += 1
                    status = "limite da API, aguardando..." if exc.code == 429 else f"erro HTTP {exc.code}"
                    self.progress.emit({
                        "index": len(created),
                        "total": wanted,
                        "account": {"email": address, "status": status},
                        "save": False,
                    })
                    if exc.code == 429:
                        time.sleep(min(18, 4 + attempts_without_success * 2))
                    else:
                        time.sleep(1.5)
                except Exception as exc:
                    attempts_without_success += 1
                    self.progress.emit({
                        "index": len(created),
                        "total": wanted,
                        "account": {"email": address, "status": f"erro: {str(exc)[:80]}"},
                        "save": False,
                    })
                    time.sleep(1.5)
                if attempts_without_success >= 8:
                    self.finished_batch.emit(created, "A API recusou varias tentativas seguidas. Aguarde alguns minutos e continue o lote.")
                    return
                time.sleep(0.9)
            self.finished_batch.emit(created, "" if created else "Nenhuma conta foi criada.")
        except Exception as exc:
            self.finished_batch.emit(created, str(exc))

    def _with_retry(self, label: str, fn, max_attempts: int = 4):
        delay = 3.0
        last_error = None
        for attempt in range(1, max_attempts + 1):
            if self._stop:
                raise RuntimeError("Lote parado pelo usuario.")
            try:
                return fn()
            except urllib.error.HTTPError as exc:
                last_error = exc
                if exc.code == 422:
                    raise RuntimeError("Email indisponivel ou dominio nao aceito pelo Mail.tm.")
                if exc.code != 429 or attempt >= max_attempts:
                    raise
                self.progress.emit({
                    "index": 0,
                    "total": self.count,
                    "account": {"email": label, "status": f"HTTP 429, nova tentativa em {int(delay)}s"},
                    "save": False,
                })
                time.sleep(delay)
                delay *= 1.8
        if last_error:
            raise last_error
        raise RuntimeError(f"Falha em {label}")

    def _unique_address(self, domain: str) -> str:
        for _ in range(1000):
            local = f"{self.prefix or 'tmp'}{_rand_text(10)}"
            address = f"{local}@{domain}"
            if address not in self.existing:
                self.existing.add(address)
                return address
        return f"{self.prefix or 'tmp'}{int(time.time())}{random.randint(1000,9999)}@{domain}"

    def _custom_or_unique_address(self, domain: str) -> str:
        if not self.custom_email:
            return self._unique_address(domain)
        if "@" in self.custom_email:
            local, custom_domain = self.custom_email.split("@", 1)
            local = "".join(ch for ch in local if ch.isalnum() or ch in "._-").strip("._-")
            custom_domain = custom_domain.strip()
            if custom_domain:
                domain = custom_domain
        else:
            local = "".join(ch for ch in self.custom_email if ch.isalnum() or ch in "._-").strip("._-")
        if not local:
            return self._unique_address(domain)
        address = f"{local}@{domain}"
        self.existing.add(address)
        return address


class TempMailInboxWorker(QThread):
    result = pyqtSignal(list, str)

    def __init__(self, email: str, password: str, token: str = "", parent=None):
        super().__init__(parent)
        self.email = email
        self.password = password
        self.token = token

    def run(self):
        try:
            client = MailTmClient()
            token = self.token or client.token(self.email, self.password)
            if not token:
                self.result.emit([], "Nao consegui autenticar essa conta.")
                return
            messages = client.messages(token)
            self.result.emit(messages, "")
        except Exception as exc:
            self.result.emit([], str(exc))


class TempMailAllInboxWorker(QThread):
    progress = pyqtSignal(str)
    result = pyqtSignal(list, str, dict)

    def __init__(self, accounts: List[Dict], parent=None):
        super().__init__(parent)
        self.accounts = [
            {
                "email": str(account.get("email", "")).strip(),
                "password": str(account.get("password", "")),
                "token": str(account.get("token", "")),
            }
            for account in accounts
            if account.get("email") and account.get("password")
        ]

    def run(self):
        client = MailTmClient()
        messages: List[dict] = []
        token_updates: Dict[str, str] = {}
        errors: List[str] = []
        total = len(self.accounts)
        for index, account in enumerate(self.accounts, 1):
            email = account["email"]
            try:
                self.progress.emit(f"Consultando {index}/{total}: {email}")
                token = account.get("token") or self._with_retry(lambda: client.token(email, account["password"]))
                if token and token != account.get("token"):
                    token_updates[email] = token
                inbox = self._with_retry(lambda: client.messages(token)) if token else []
                for message in inbox:
                    item = dict(message)
                    item["_account"] = email
                    messages.append(item)
            except Exception as exc:
                errors.append(f"{email}: {str(exc)[:90]}")
            time.sleep(0.3)
        messages.sort(key=lambda item: str(item.get("createdAt", "")), reverse=True)
        error_text = "" if messages else "\n".join(errors[:8])
        self.result.emit(messages, error_text, token_updates)

    def _with_retry(self, fn, max_attempts: int = 3):
        delay = 2.0
        for attempt in range(1, max_attempts + 1):
            try:
                return fn()
            except urllib.error.HTTPError as exc:
                if exc.code != 429 or attempt >= max_attempts:
                    raise
                time.sleep(delay)
                delay *= 1.8


class TempMailWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.accounts: List[Dict] = _safe_read_json(DATA_FILE, [])
        self.worker: Optional[TempMailBatchWorker] = None
        self.inbox_worker: Optional[TempMailInboxWorker] = None
        self.all_inbox_worker: Optional[TempMailAllInboxWorker] = None
        self.cached_inbox_messages: List[dict] = []
        self._last_inbox_account = ""
        self.inbox_mode = "all"
        self._build_ui()
        self.refresh_table()

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
        title = QLabel("Email Temp")
        title.setObjectName("Title")
        subtitle = QLabel("Gere, importe, filtre e veja varias caixas de entrada em um painel unico.")
        subtitle.setObjectName("Subtitle")
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        hero_lay.addLayout(title_box, 1)
        self.status_badge = QLabel("Pronto")
        self.status_badge.setObjectName("Badge")
        self.status_badge.setAlignment(Qt.AlignCenter)
        hero_lay.addWidget(self.status_badge)
        root.addWidget(hero)

        body = QHBoxLayout()
        body.setSpacing(12)
        root.addLayout(body, 1)

        controls = QFrame()
        controls.setObjectName("Card")
        controls.setFixedWidth(400)
        c = QVBoxLayout(controls)
        c.setContentsMargins(16, 14, 16, 14)
        c.setSpacing(8)
        h = QLabel("Gerar lote")
        h.setObjectName("Section")
        c.addWidget(h)

        c.addWidget(QLabel("Quantidade"))
        self.count_spin = QSpinBox()
        self.count_spin.setRange(1, 50)
        self.count_spin.setValue(50)
        c.addWidget(self.count_spin)

        c.addWidget(QLabel("Senha fixa opcional"))
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Vazio = senha aleatoria por conta")
        c.addWidget(self.password_input)

        c.addWidget(QLabel("Prefixo opcional"))
        self.prefix_input = QLineEdit()
        self.prefix_input.setPlaceholderText("Ex: teste, amazon, conta")
        c.addWidget(self.prefix_input)

        c.addWidget(QLabel("Email personalizado opcional"))
        self.custom_email_input = QLineEdit()
        self.custom_email_input.setPlaceholderText("Ex: meuemail ou meuemail@dominio Mail.tm")
        c.addWidget(self.custom_email_input)

        c.addWidget(QLabel("Lote rapido email:senha"))
        self.bulk_input = QTextEdit()
        self.bulk_input.setObjectName("BulkBox")
        self.bulk_input.setPlaceholderText("Cole aqui:\nemail@dominio.com:senha\noutro@dominio.com:senha")
        self.bulk_input.setFixedHeight(86)
        c.addWidget(self.bulk_input)

        bulk_actions = QHBoxLayout()
        import_paste_btn = QPushButton("Importar lista")
        import_paste_btn.setObjectName("Accent")
        import_paste_btn.clicked.connect(self.import_pasted_batch)
        import_fetch_btn = QPushButton("Importar + inbox")
        import_fetch_btn.setObjectName("Primary")
        import_fetch_btn.clicked.connect(self.import_pasted_and_fetch)
        bulk_actions.addWidget(import_paste_btn)
        bulk_actions.addWidget(import_fetch_btn)
        c.addLayout(bulk_actions)

        self.progress_label = QLabel("Nenhuma geracao em andamento.")
        self.progress_label.setObjectName("Hint")
        self.progress_label.setWordWrap(True)
        c.addWidget(self.progress_label)

        generate_btn = QPushButton("Gerar lote")
        generate_btn.setObjectName("Primary")
        generate_btn.clicked.connect(self.start_batch)
        c.addWidget(generate_btn)

        stop_btn = QPushButton("Parar")
        stop_btn.setObjectName("Warning")
        stop_btn.clicked.connect(self.stop_batch)
        c.addWidget(stop_btn)

        copy_btn = QPushButton("Copiar todos email:senha")
        copy_btn.setObjectName("Accent")
        copy_btn.clicked.connect(self.copy_all)
        c.addWidget(copy_btn)

        import_btn = QPushButton("Importar lote email:senha")
        import_btn.clicked.connect(self.import_batch_dialog)
        c.addWidget(import_btn)

        export_btn = QPushButton("Exportar TXT")
        export_btn.clicked.connect(self.export_txt)
        c.addWidget(export_btn)

        delete_btn = QPushButton("Apagar selecionados")
        delete_btn.setObjectName("Danger")
        delete_btn.clicked.connect(self.delete_selected)
        c.addWidget(delete_btn)

        delete_filtered_btn = QPushButton("Apagar filtrados")
        delete_filtered_btn.setObjectName("DangerSoft")
        delete_filtered_btn.clicked.connect(self.delete_filtered)
        c.addWidget(delete_filtered_btn)

        clean_errors_btn = QPushButton("Limpar erros da lista")
        clean_errors_btn.clicked.connect(self.clean_error_rows)
        c.addWidget(clean_errors_btn)
        c.addStretch(1)
        c.addWidget(QLabel("Uso permitido: testes, contas proprias e recebimento temporario. Respeite limites e regras do Mail.tm."))
        body.addWidget(controls)

        right = QVBoxLayout()
        right.setSpacing(10)
        body.addLayout(right, 1)

        summary = QFrame()
        summary.setObjectName("Card")
        s = QHBoxLayout(summary)
        s.setContentsMargins(14, 10, 14, 10)
        self.total_label = QLabel("0 contas")
        self.total_label.setObjectName("Metric")
        self.ok_label = QLabel("0 ok")
        self.ok_label.setObjectName("Metric")
        self.last_label = QLabel("ultimo: -")
        self.last_label.setObjectName("Metric")
        self.paramount_paid_label = QLabel("0 pagos Paramount")
        self.paramount_paid_label.setObjectName("Metric")
        for widget in (self.total_label, self.ok_label, self.paramount_paid_label, self.last_label):
            s.addWidget(widget)
        right.addWidget(summary)

        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("Filtrar contas por email, dominio, status ou data...")
        self.filter_input.textChanged.connect(self.refresh_table)
        right.addWidget(self.filter_input)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Email", "Senha", "Dominio", "Status", "Criado"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.cellDoubleClicked.connect(lambda *_: self.copy_selected())
        right.addWidget(self.table, 1)

        actions = QHBoxLayout()
        copy_selected_btn = QPushButton("Copiar selecionado")
        copy_selected_btn.clicked.connect(self.copy_selected)
        inbox_btn = QPushButton("Ver inbox")
        inbox_btn.clicked.connect(self.fetch_inbox)
        all_inbox_btn = QPushButton("Inbox de todos")
        all_inbox_btn.setObjectName("Primary")
        all_inbox_btn.clicked.connect(self.fetch_all_inboxes)
        paid_btn = QPushButton("Pagamentos Paramount")
        paid_btn.setObjectName("Success")
        paid_btn.clicked.connect(lambda: self.fetch_all_inboxes(paramount_only=True))
        save_btn = QPushButton("Salvar agora")
        save_btn.clicked.connect(self.save_accounts)
        actions.addWidget(copy_selected_btn)
        actions.addWidget(inbox_btn)
        actions.addWidget(all_inbox_btn)
        actions.addWidget(paid_btn)
        actions.addWidget(save_btn)
        right.addLayout(actions)

        self.inbox_filter_input = QLineEdit()
        self.inbox_filter_input.setPlaceholderText("Filtrar inbox por email, remetente, assunto ou Paramount...")
        self.inbox_filter_input.textChanged.connect(self.render_inbox_messages)
        right.addWidget(self.inbox_filter_input)

        self.inbox_view = QTextEdit()
        self.inbox_view.setReadOnly(True)
        self.inbox_view.setPlaceholderText("Selecione uma conta e clique em Ver inbox.")
        self.inbox_view.setFixedHeight(175)
        right.addWidget(self.inbox_view)

    def start_batch(self):
        if self.worker and self.worker.isRunning():
            self.set_status("Gerando...", pending=True)
            return
        existing = {acc.get("email", "") for acc in self.accounts}
        custom_email = self.custom_email_input.text().strip()
        self.worker = TempMailBatchWorker(
            1 if custom_email else self.count_spin.value(),
            self.password_input.text(),
            self.prefix_input.text(),
            existing,
            custom_email,
            self,
        )
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_batch.connect(self.on_finished)
        self.worker.start()
        self.set_status("Gerando...", pending=True)
        self.progress_label.setText("Iniciando lote...")
        self._task_running(
            "temp-mail:batch",
            "Gerar emails temporarios",
            {"count": 1 if custom_email else self.count_spin.value(), "custom": bool(custom_email)},
        )

    def stop_batch(self):
        if self.worker and self.worker.isRunning():
            self.worker.stop()
            self.progress_label.setText("Parando apos a conta atual...")
            self._task_done("temp-mail:batch", "review", "Parada solicitada pelo usuario.")

    def on_progress(self, payload: dict):
        account = payload.get("account") or {}
        self.progress_label.setText(f"{payload.get('index')}/{payload.get('total')} - {account.get('email', '')} - {account.get('status', '')}")
        if payload.get("save", True) and account.get("email"):
            self.accounts.append(account)
            self.save_accounts(silent=True)
            self.refresh_table()

    def on_finished(self, created: list, error: str):
        if error and not created:
            self.set_status("Erro", ok=False)
            self.progress_label.setText(error)
            self._task_done("temp-mail:batch", "error", error)
        else:
            self.set_status("Pronto", ok=True)
            self.progress_label.setText(f"Lote finalizado. Novas contas: {len(created)}")
            self._task_done("temp-mail:batch", "success", "")
        self.refresh_table()

    def refresh_table(self):
        self.table.setRowCount(0)
        query = self.filter_input.text().strip().lower() if hasattr(self, "filter_input") else ""
        for account in self.accounts:
            if query and not self._account_matches(account, query):
                continue
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                account.get("email", ""),
                account.get("password", ""),
                account.get("domain", ""),
                account.get("status", ""),
                account.get("created_at", ""),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, account.get("email", ""))
                self.table.setItem(row, col, item)
        ok_count = sum(1 for acc in self.accounts if str(acc.get("status", "")).lower().startswith("ok"))
        self.total_label.setText(f"{len(self.accounts)} contas")
        self.ok_label.setText(f"{ok_count} ok")
        self.last_label.setText(f"ultimo: {self.accounts[-1].get('email', '-') if self.accounts else '-'}")

    def _account_matches(self, account: Dict, query: str) -> bool:
        blob = " ".join(str(account.get(key, "")) for key in ("email", "password", "domain", "status", "created_at", "source")).lower()
        return query in blob

    def selected_account(self) -> Optional[Dict]:
        row = self.table.currentRow()
        if row < 0:
            return None
        email_item = self.table.item(row, 0)
        email = email_item.text() if email_item else ""
        for account in self.accounts:
            if account.get("email") == email:
                return account
        return None

    def copy_selected(self):
        account = self.selected_account()
        if not account:
            QMessageBox.information(self, "Email Temp", "Selecione uma conta.")
            return
        text = f"{account.get('email', '')}:{account.get('password', '')}"
        QApplication.clipboard().setText(text)
        self.set_status("Copiado", ok=True)

    def copy_all(self):
        lines = [f"{a.get('email', '')}:{a.get('password', '')}" for a in self.accounts if a.get("email")]
        QApplication.clipboard().setText("\n".join(lines))
        self.set_status(f"{len(lines)} copiadas", ok=True)

    def import_pasted_batch(self):
        raw = self.bulk_input.toPlainText().strip() or QApplication.clipboard().text().strip()
        added, ignored = self.import_batch_text(raw)
        self.progress_label.setText(f"Lista processada. Adicionadas: {added}. Ignoradas/duplicadas/sem senha: {ignored}.")

    def import_pasted_and_fetch(self):
        raw = self.bulk_input.toPlainText().strip() or QApplication.clipboard().text().strip()
        added, ignored = self.import_batch_text(raw)
        self.progress_label.setText(f"Lista processada. Adicionadas: {added}. Ignoradas: {ignored}. Consultando inbox...")
        self.fetch_all_inboxes(paramount_only=False)

    def import_batch_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Importar lote email:senha")
        dlg.resize(560, 420)
        layout = QVBoxLayout(dlg)
        info = QLabel("Cole uma conta por linha. Aceita email:senha, email|senha, email;senha ou email senha. Sem senha nao da para abrir inbox.")
        info.setWordWrap(True)
        layout.addWidget(info)
        text = QTextEdit()
        text.setPlaceholderText("email@dominio.com:senha\noutro@dominio.com senha")
        clip = QApplication.clipboard().text().strip()
        if "@" in clip and ":" in clip:
            text.setPlainText(clip)
        layout.addWidget(text, 1)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        layout.addWidget(buttons)
        if dlg.exec_() == QDialog.Accepted:
            self.import_batch_text(text.toPlainText())

    def import_batch_text(self, raw: str) -> tuple[int, int]:
        existing = {str(account.get("email", "")).lower() for account in self.accounts}
        added = 0
        ignored = 0
        for line in raw.splitlines():
            email, password = self._parse_account_line(line)
            if not email or not password:
                ignored += 1
                continue
            if "@" not in email or not password:
                ignored += 1
                continue
            if email in existing:
                ignored += 1
                continue
            domain = email.split("@", 1)[1]
            self.accounts.append({
                "email": email,
                "password": password,
                "domain": domain,
                "created_at": _now(),
                "status": "importado",
                "token": "",
                "source": "manual",
            })
            existing.add(email)
            added += 1
        self.save_accounts(silent=True)
        self.refresh_table()
        self.set_status(f"{added} importadas", ok=added > 0)
        self.progress_label.setText(f"Importacao finalizada. Adicionadas: {added}. Ignoradas/duplicadas: {ignored}.")
        return added, ignored

    def _parse_account_line(self, line: str) -> tuple[str, str]:
        item = line.strip()
        if not item:
            return "", ""
        for separator in (":", "|", ";", "\t"):
            if separator in item:
                email, password = item.split(separator, 1)
                return email.strip().lower(), password.strip()
        parts = item.split(None, 1)
        if len(parts) == 2:
            return parts[0].strip().lower(), parts[1].strip()
        return "", ""

    def export_txt(self):
        default = str(APP_DATA_DIR / "temp_mail_export.txt")
        path, _ = QFileDialog.getSaveFileName(self, "Exportar emails temporarios", default, "Texto (*.txt)")
        if not path:
            return
        lines = [f"{a.get('email', '')}:{a.get('password', '')}" for a in self.accounts if a.get("email")]
        Path(path).write_text("\n".join(lines), encoding="utf-8")
        self.set_status("Exportado", ok=True)

    def delete_selected(self):
        emails = self.selected_emails()
        if not emails:
            QMessageBox.information(self, "Email Temp", "Selecione uma conta.")
            return
        if len(emails) > 1:
            ok = QMessageBox.question(
                self,
                "Email Temp",
                f"Apagar {len(emails)} conta(s) selecionada(s) da lista?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if ok != QMessageBox.Yes:
                return
        self.accounts = [a for a in self.accounts if a.get("email") not in emails]
        self.save_accounts(silent=True)
        self.refresh_table()
        self.set_status(f"{len(emails)} apagadas", ok=True)

    def selected_emails(self) -> set[str]:
        rows = set()
        selection = self.table.selectionModel()
        if selection:
            rows.update(index.row() for index in selection.selectedRows())
        if self.table.currentRow() >= 0:
            rows.add(self.table.currentRow())
        emails = set()
        for row in rows:
            item = self.table.item(row, 0)
            if item and item.text():
                emails.add(item.text())
        return emails

    def delete_filtered(self):
        query = self.filter_input.text().strip().lower()
        if not query:
            QMessageBox.information(self, "Email Temp", "Digite um filtro antes de apagar em massa.")
            return
        filtered = [account for account in self.accounts if self._account_matches(account, query)]
        if not filtered:
            self.set_status("Nada filtrado", ok=True)
            return
        ok = QMessageBox.question(
            self,
            "Email Temp",
            f"Apagar {len(filtered)} conta(s) que batem com o filtro atual?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if ok != QMessageBox.Yes:
            return
        filtered_emails = {account.get("email") for account in filtered}
        self.accounts = [account for account in self.accounts if account.get("email") not in filtered_emails]
        self.save_accounts(silent=True)
        self.refresh_table()
        self.set_status(f"{len(filtered)} filtradas apagadas", ok=True)

    def clean_error_rows(self):
        before = len(self.accounts)
        self.accounts = [
            account for account in self.accounts
            if not str(account.get("status", "")).lower().startswith(("erro", "limite"))
        ]
        self.save_accounts(silent=True)
        self.refresh_table()
        self.set_status(f"{before - len(self.accounts)} erros removidos", ok=True)

    def fetch_inbox(self):
        account = self.selected_account()
        if not account:
            QMessageBox.information(self, "Email Temp", "Selecione uma conta.")
            return
        self.inbox_view.setPlainText("Buscando mensagens...")
        self._last_inbox_account = account.get("email", "")
        self.inbox_mode = "all"
        self.inbox_worker = TempMailInboxWorker(account.get("email", ""), account.get("password", ""), account.get("token", ""), self)
        self.inbox_worker.result.connect(self.on_inbox_result)
        self.inbox_worker.start()
        self._task_running("temp-mail:inbox", "Consultar inbox selecionado", {"email": account.get("email", "")})

    def fetch_all_inboxes(self, paramount_only: bool = False):
        accounts = [account for account in self.accounts if account.get("email") and account.get("password")]
        if not accounts:
            QMessageBox.information(self, "Email Temp", "Nenhuma conta com email e senha para consultar.")
            return
        if self.all_inbox_worker and self.all_inbox_worker.isRunning():
            self.set_status("Consultando...", pending=True)
            return
        self.inbox_mode = "paramount_payment" if paramount_only else "all"
        target = "pagamentos Paramount" if paramount_only else "inbox"
        self.inbox_view.setPlainText(f"Consultando {target} em {len(accounts)} conta(s)...")
        self.all_inbox_worker = TempMailAllInboxWorker(accounts, self)
        self.all_inbox_worker.progress.connect(lambda text: self.progress_label.setText(text))
        self.all_inbox_worker.result.connect(self.on_all_inbox_result)
        self.all_inbox_worker.start()
        self.set_status("Consultando...", pending=True)
        self._task_running("temp-mail:inbox-all", f"Consultar {target}", {"accounts": len(accounts)})

    def on_inbox_result(self, messages: list, error: str):
        if error:
            self.inbox_view.setPlainText(error)
            self._task_done("temp-mail:inbox", "error", error)
            return
        self._task_done("temp-mail:inbox", "success", "")
        self.inbox_mode = "all"
        enriched = []
        for msg in messages:
            item = dict(msg)
            item["_account"] = self._last_inbox_account
            enriched.append(item)
        self.cached_inbox_messages = enriched
        self.render_inbox_messages()

    def on_all_inbox_result(self, messages: list, error: str, token_updates: dict):
        if token_updates:
            for account in self.accounts:
                email = account.get("email", "")
                if email in token_updates:
                    account["token"] = token_updates[email]
                    if str(account.get("status", "")).lower() in {"importado", "sem token", ""}:
                        account["status"] = "ok verificado"
            self.save_accounts(silent=True)
            self.refresh_table()
        if error:
            self.inbox_view.setPlainText(error)
            self.set_status("Erro inbox", ok=False)
            self._task_done("temp-mail:inbox-all", "error", error)
            return
        if not messages:
            self.inbox_view.setPlainText("Nenhuma mensagem encontrada em nenhuma conta.")
            self.set_status("Sem mensagens", ok=True)
            self._task_done("temp-mail:inbox-all", "success", "")
            return
        self.cached_inbox_messages = messages
        self.render_inbox_messages()
        self._task_done("temp-mail:inbox-all", "success", "")

    def _task_running(self, task_id: str, title: str, payload: Optional[dict] = None):
        if not get_app_store:
            return
        try:
            get_app_store().upsert_task(
                task_id,
                "temp-mail",
                title,
                source="temp_mail",
                status="running",
                priority=40,
                payload=payload or {},
            )
        except Exception:
            pass

    def _task_done(self, task_id: str, status: str, error: str = ""):
        if not get_app_store:
            return
        try:
            get_app_store().update_task(task_id, status=status, last_error=error, attempts_delta=1 if status == "error" else 0)
        except Exception:
            pass

    def render_inbox_messages(self):
        messages = list(self.cached_inbox_messages)
        if not hasattr(self, "inbox_view"):
            return
        paid_count = sum(1 for msg in messages if self._message_is_paramount_payment(msg))
        if hasattr(self, "paramount_paid_label"):
            self.paramount_paid_label.setText(f"{paid_count} pagos Paramount")
        if not messages:
            self.inbox_view.setPlainText("Nenhuma mensagem encontrada.")
            return
        query = self.inbox_filter_input.text().strip().lower() if hasattr(self, "inbox_filter_input") else ""
        filtered = []
        for msg in messages:
            if self.inbox_mode == "paramount_payment" and not self._message_is_paramount_payment(msg):
                continue
            blob = self._message_blob(msg)
            if not query or query in blob:
                filtered.append(msg)
        if self.inbox_mode == "paramount_payment":
            title = f"Pagamentos Paramount: {len(filtered)} encontrado(s)."
        else:
            title = f"Inbox: {len(filtered)}/{len(messages)} mensagem(ns). Pagamentos Paramount: {paid_count}."
        lines = [title, ""]
        for msg in filtered[:100]:
            from_addr = msg.get("from", {}).get("address", "")
            subject = msg.get("subject", "")
            account = msg.get("_account", "")
            created = msg.get("createdAt", "")
            tag = "[PAGO PARAMOUNT]" if self._message_is_paramount_payment(msg) else "[EMAIL]"
            lines.append(f"{tag} {created} | {account} | {from_addr} | {subject}")
        if len(filtered) > 100:
            lines.append("")
            lines.append(f"...mais {len(filtered) - 100} mensagem(ns).")
        self.inbox_view.setPlainText("\n".join(lines))
        self.set_status(f"{len(filtered)} exibidas", ok=True)

    def _message_blob(self, msg: dict) -> str:
        from_info = msg.get("from", {})
        if isinstance(from_info, dict):
            from_text = " ".join(str(from_info.get(key, "")) for key in ("address", "name"))
        else:
            from_text = str(from_info)
        return " ".join([
            str(msg.get("_account", "")),
            from_text,
            str(msg.get("subject", "")),
            str(msg.get("intro", "")),
            str(msg.get("text", "")),
            str(msg.get("createdAt", "")),
        ]).lower()

    def _message_is_paramount_payment(self, msg: dict) -> bool:
        blob = self._message_blob(msg)
        is_paramount = "paramount" in blob or "transactions.paramountplus" in blob
        payment_hit = (
            "pagamento da sua assinatura" in blob
            or ("pagamento" in blob and "recebido" in blob)
            or ("payment" in blob and ("received" in blob or "receipt" in blob))
            or ("total pago" in blob and "paramount" in blob)
        )
        return is_paramount and payment_hit

    def save_accounts(self, silent: bool = False):
        _safe_write_json(DATA_FILE, self.accounts)
        if not silent:
            self.set_status("Salvo", ok=True)

    def set_status(self, text: str, ok: bool = False, pending: bool = False):
        self.status_badge.setText(text[:40])
        self.status_badge.setProperty("state", "pending" if pending else ("ok" if ok else "normal"))
        self.status_badge.style().unpolish(self.status_badge)
        self.status_badge.style().polish(self.status_badge)

    @staticmethod
    def _qss():
        p = PALETTE
        return DARK_STYLE_PRO + f"""
        QFrame#Hero {{
            background:{p.panel};
            border:1px solid {p.border};
            border-radius:10px;
        }}
        QFrame#Card {{
            background:{p.card};
            border:1px solid {p.border};
            border-radius:10px;
        }}
        QLabel#Title {{ font-size:22px; font-weight:900; color:{p.text}; }}
        QLabel#Subtitle, QLabel#Hint {{ color:{p.muted}; }}
        QLabel#Section {{
            color:{p.primary};
            font-size:14px;
            font-weight:900;
        }}
        QLabel#Metric {{
            background:{p.panel};
            border:1px solid {p.border};
            border-radius:8px;
            padding:12px;
            color:{p.success};
            font-weight:900;
        }}
        QLabel#Badge {{
            min-width:124px;
            min-height:42px;
            padding:8px 14px;
            border-radius:10px;
            font-weight:900;
            border:1px solid {p.border};
            background:{p.panel};
            color:{p.text};
        }}
        QLabel#Badge[state="ok"] {{ background:#052e25; color:{p.success}; border-color:#10b981; }}
        QLabel#Badge[state="pending"] {{ background:#082f49; color:{p.primary}; border-color:{p.border_strong}; }}
        QTextEdit#BulkBox {{
            background:{p.panel};
            border:1px solid {p.border_strong};
        }}
        QPushButton#Primary {{
            background:{p.primary};
            color:#021019;
            border-color:{p.primary};
        }}
        QPushButton#Accent {{
            background:#082f49;
            color:{p.primary};
            border-color:{p.border_strong};
        }}
        QPushButton#Success {{
            background:#052e25;
            color:{p.success};
            border-color:#10b981;
        }}
        QPushButton#Warning {{
            background:#3b2a09;
            color:{p.warning};
            border-color:#f59e0b;
        }}
        QPushButton#Danger {{
            background:#3f1111;
            color:{p.danger};
            border-color:#ef4444;
        }}
        QPushButton#DangerSoft {{
            background:#3f1111;
            color:{p.danger};
            border-color:#ef4444;
        }}
        {table_qss()}
        {scroll_qss()}
        """
