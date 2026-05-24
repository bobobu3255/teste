#!/usr/bin/env python3
"""Central de logs bonitos do hub do app."""
from __future__ import annotations

import json

from PyQt5.QtWidgets import QApplication, QHBoxLayout, QLabel, QListWidget, QMessageBox, QPushButton, QVBoxLayout, QWidget

from app.core.paths import CONFIG_DIR
from app.ui.components import button_qss, label_qss

try:
    from app.core.app_context import get_app_store
except Exception:
    get_app_store = None


def read_central_logs(limit=30, only_errors=False):
    if not get_app_store:
        return []
    try:
        events = get_app_store().list_events(limit=max(limit * 3, 30))
    except Exception:
        return []

    lines = []
    for event in events:
        level = str(event.get("level") or "info").lower()
        typ = event.get("event") or "log"
        msg = event.get("message") or typ
        if only_errors and level not in {"error", "warning"} and "erro" not in str(msg).lower():
            continue
        source = event.get("source") or "app"
        lines.append(f"{source}/{typ}: {friendly_error_text(msg)}")
        if len(lines) >= limit:
            break
    return lines


def read_recent_logs(limit=30, only_errors=False):
    merged = read_central_logs(limit=limit, only_errors=only_errors)
    log_file = CONFIG_DIR / "browser_logs.jsonl"
    if not log_file.exists():
        return merged[:limit]
    lines = []
    try:
        raw = log_file.read_text(encoding="utf-8", errors="ignore").splitlines()[-200:]
        for line in reversed(raw):
            try:
                event = json.loads(line)
                msg = event.get("message") or event.get("details") or str(event)
                typ = event.get("event") or event.get("type") or "log"
                if only_errors and "erro" not in msg.lower() and "error" not in typ.lower() and "failed" not in msg.lower():
                    continue
                lines.append(f"{typ}: {friendly_error_text(msg)}")
                if len(lines) >= limit:
                    break
            except Exception:
                if not only_errors:
                    lines.append(line[:180])
    except Exception:
        return merged[:limit]
    return (merged + lines)[:limit]


def friendly_error_text(message):
    text = str(message)
    low = text.lower()
    if "403" in low or "forbidden" in low:
        return "Bloqueio 403: tente limpar o perfil, trocar proxy/rede, usar modo Streaming ou abrir em outro navegador."
    if "chrome nao encontrado" in low or "chrome não encontrado" in low:
        return "Chrome nao encontrado: instale Chrome/Edge/Firefox ou use o reparo do launcher."
    if "webdriver" in low or "selenium" in low:
        return "Erro do navegador automatizado: tente modo nativo ou reparar dependencias."
    return text[:220]


class PrettyLogsWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build()
        self.refresh()

    def _build(self):
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        top = QHBoxLayout()
        title = QLabel("Central de Logs")
        title.setStyleSheet(label_qss("title").replace("18px", "16px"))
        top.addWidget(title)
        top.addStretch()
        refresh_btn = QPushButton("Atualizar")
        refresh_btn.setStyleSheet(button_qss("secondary"))
        refresh_btn.clicked.connect(self.refresh)
        top.addWidget(refresh_btn)
        copy_btn = QPushButton("Copiar selecionado")
        copy_btn.setStyleSheet(button_qss("secondary"))
        copy_btn.clicked.connect(self.copy_selected)
        top.addWidget(copy_btn)
        fix_btn = QPushButton("Corrigir provavel")
        fix_btn.setStyleSheet(button_qss("warning"))
        fix_btn.clicked.connect(self.show_fix_hint)
        top.addWidget(fix_btn)
        lay.addLayout(top)
        self.list = QListWidget()
        self.list.setStyleSheet("QListWidget{background:#08111f;color:#e2e8f0;border:1px solid rgba(148,163,184,0.10);border-radius:12px;padding:8px;} QListWidget::item{padding:7px;border-radius:6px;} QListWidget::item:selected{background:#0b2c3a;color:#67e8f9;}")
        lay.addWidget(self.list, 1)

    def refresh(self):
        self.list.clear()
        for line in read_recent_logs(limit=80, only_errors=False):
            self.list.addItem(line)

    def copy_selected(self):
        item = self.list.currentItem()
        if item:
            QApplication.clipboard().setText(item.text())

    def show_fix_hint(self):
        item = self.list.currentItem()
        text = item.text() if item else ""
        QMessageBox.information(self, "Correcao provavel", friendly_error_text(text) or "Selecione um log para ver a sugestao.")


