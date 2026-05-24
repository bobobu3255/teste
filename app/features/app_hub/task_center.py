#!/usr/bin/env python3
"""Painel compacto para fila central e modo recuperacao."""
from __future__ import annotations

from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFrame,
    QGridLayout,
    QHeaderView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from app.core.app_store import TASK_ERROR, TASK_PENDING, TASK_REVIEW, TASK_RUNNING, TASK_SUCCESS
from app.ui.components import button_qss, card_qss, label_qss, table_qss

try:
    from app.core.app_context import get_app_store
except Exception:
    get_app_store = None


def _short_dt(value: str) -> str:
    try:
        dt = datetime.fromisoformat(str(value))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return str(value or "-")[:16]


class TaskCenterPanel(QFrame):
    """Mostra tarefas longas e oferece recuperacao sem fechar o app."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(card_qss("default", radius=10))
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(12, 10, 12, 12)
        root.setSpacing(8)

        top = QHBoxLayout()
        self.title = QLabel("Centro de tarefas")
        self.title.setStyleSheet(label_qss("section"))
        self.summary = QLabel("Carregando...")
        self.summary.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        self.summary.setStyleSheet(label_qss("muted"))
        top.addWidget(self.title)
        top.addStretch()
        top.addWidget(self.summary)
        root.addLayout(top)

        actions = QHBoxLayout()
        self.recover_btn = QPushButton("Recuperar travadas")
        self.recover_btn.setCursor(Qt.PointingHandCursor)
        self.recover_btn.setStyleSheet(button_qss("warning"))
        self.recover_btn.clicked.connect(self.recover_stale)
        self.clean_btn = QPushButton("Limpar concluidas")
        self.clean_btn.setCursor(Qt.PointingHandCursor)
        self.clean_btn.setStyleSheet(button_qss("secondary"))
        self.clean_btn.clicked.connect(self.clean_done)
        self.refresh_btn = QPushButton("Atualizar fila")
        self.refresh_btn.setCursor(Qt.PointingHandCursor)
        self.refresh_btn.setStyleSheet(button_qss("secondary"))
        self.refresh_btn.clicked.connect(self.refresh)
        actions.addWidget(self.recover_btn)
        actions.addWidget(self.clean_btn)
        actions.addWidget(self.refresh_btn)
        root.addLayout(actions)

        filter_row = QHBoxLayout()
        filter_row.setSpacing(8)
        filter_label = QLabel("Filtro")
        filter_label.setStyleSheet(label_qss("muted"))
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Tudo", "Rodando", "Revisar", "Erros", "Paramount"])
        self.filter_combo.currentTextChanged.connect(self.refresh)
        self.filter_combo.setMinimumHeight(30)
        filter_row.addWidget(filter_label)
        filter_row.addWidget(self.filter_combo)
        filter_row.addStretch()
        root.addLayout(filter_row)

        self.metrics = QGridLayout()
        self.metrics.setSpacing(6)
        root.addLayout(self.metrics)

        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(["Status", "Origem", "Tarefa", "Atualizado", "Erro"])
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.setStyleSheet(table_qss())
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.setMinimumHeight(170)
        root.addWidget(self.table, 1)

    def refresh(self):
        if not get_app_store:
            self.summary.setText("Estado central indisponivel")
            return
        try:
            store = get_app_store()
            counts = store.task_counts()
            stale = store.list_stale_tasks(max_age_minutes=8, limit=50)
            selected_filter = self.filter_combo.currentText() if hasattr(self, "filter_combo") else "Tudo"
            status_filter = [TASK_RUNNING, TASK_PENDING, TASK_REVIEW, TASK_ERROR]
            source_filter = None
            if selected_filter == "Rodando":
                status_filter = [TASK_RUNNING]
            elif selected_filter == "Revisar":
                status_filter = [TASK_REVIEW]
            elif selected_filter == "Erros":
                status_filter = [TASK_ERROR]
            elif selected_filter == "Paramount":
                source_filter = "paramount_assist"
            tasks = store.list_tasks(status=status_filter, source=source_filter, limit=80)
        except Exception as exc:
            self.summary.setText(f"Erro: {exc}")
            return

        running = int(counts.get(TASK_RUNNING, 0) or 0)
        review = int(counts.get(TASK_REVIEW, 0) or 0)
        error = int(counts.get(TASK_ERROR, 0) or 0)
        self.summary.setText(f"{running} rodando | {review} revisar | {error} erro | {len(stale)} travada(s)")
        self.recover_btn.setEnabled(bool(stale))

        while self.metrics.count():
            item = self.metrics.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        metric_data = [
            ("Rodando", running, "#38bdf8"),
            ("Revisar", review, "#fbbf24"),
            ("Erros", error, "#f87171"),
            ("Pendentes", int(counts.get(TASK_PENDING, 0) or 0), "#a78bfa"),
            ("OK", int(counts.get(TASK_SUCCESS, 0) or 0), "#34d399"),
        ]
        for index, (name, value, color) in enumerate(metric_data):
            box = QLabel(f"{name}\n{value}")
            box.setAlignment(Qt.AlignCenter)
            box.setMinimumHeight(42)
            box.setStyleSheet(
                f"background:#08111f;border:1px solid rgba(56,189,248,0.12);"
                f"border-radius:8px;padding:7px;color:{color};font-weight:900;"
            )
            self.metrics.addWidget(box, index // 3, index % 3)

        self.table.setRowCount(0)
        for task in tasks:
            row = self.table.rowCount()
            self.table.insertRow(row)
            values = [
                self._status_label(task.get("status", "")),
                task.get("source", ""),
                task.get("title", ""),
                _short_dt(task.get("updated_at", "")),
                task.get("last_error", ""),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, task.get("id", ""))
                self.table.setItem(row, col, item)
        self.table.resizeColumnsToContents()
        self.table.setColumnWidth(2, max(190, self.table.columnWidth(2)))

    def recover_stale(self):
        if not get_app_store:
            return
        try:
            total = get_app_store().recover_stale_tasks(max_age_minutes=8)
            self.summary.setText(f"Recuperadas {total} tarefa(s) para revisao.")
        except Exception as exc:
            self.summary.setText(f"Erro ao recuperar: {exc}")
        self.refresh()

    def clean_done(self):
        if not get_app_store:
            return
        try:
            removed = get_app_store().delete_tasks(status=["success", "cancelled"], older_than_days=1)
            self.summary.setText(f"Removidas {removed} tarefa(s) antigas.")
        except Exception as exc:
            self.summary.setText(f"Erro ao limpar: {exc}")
        self.refresh()

    @staticmethod
    def _status_label(status: str) -> str:
        return {
            "pending": "Pendente",
            "running": "Rodando",
            "success": "Sucesso",
            "error": "Erro",
            "review": "Revisar",
            "cancelled": "Cancelada",
        }.get(str(status), str(status))
