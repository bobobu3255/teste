#!/usr/bin/env python3
"""Painel visual para rodar verificacoes de manutencao do app."""
from __future__ import annotations

import os
import subprocess
import sys
import time

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import QApplication, QFrame, QHBoxLayout, QLabel, QMessageBox, QPushButton, QTextEdit, QVBoxLayout

from app.core.app_metadata import APP_CODENAME
from app.core.paths import BASE_DIR
from app.ui.components import button_qss, label_qss


class MaintenanceCheckWorker(QThread):
    finished_check = pyqtSignal(bool, str)

    def __init__(self, mode: str = "quick", parent=None):
        super().__init__(parent)
        self.mode = mode

    def run(self):
        if self.mode == "storage":
            script = BASE_DIR / "scripts" / "maintenance" / "storage_report.py"
            command_args = []
        elif self.mode == "cleanup":
            script = BASE_DIR / "scripts" / "maintenance" / "safe_cleanup.py"
            command_args = ["--limit", "30"]
        elif self.mode == "appstore":
            script = BASE_DIR / "scripts" / "maintenance" / "app_store_maintenance.py"
            command_args = ["--snapshot"]
        elif self.mode == "appstore_backup":
            script = BASE_DIR / "scripts" / "maintenance" / "app_store_maintenance.py"
            command_args = ["--backup", "--snapshot"]
        elif self.mode == "health_report":
            script = BASE_DIR / "scripts" / "maintenance" / "project_health_report.py"
            command_args = []
        elif self.mode == "sync_state":
            script = BASE_DIR / "scripts" / "maintenance" / "sync_app_store.py"
            command_args = []
        else:
            script = BASE_DIR / "scripts" / "maintenance" / "verify_all.py"
            command_args = ["--quick"] if self.mode == "quick" else []
        if not script.exists():
            self.finished_check.emit(False, f"Script de manutencao nao encontrado em:\n{script}")
            return

        command = [sys.executable, str(script), *command_args]

        env = os.environ.copy()
        env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
        env.setdefault("PYTHONUTF8", "1")
        env.setdefault("PYTHONIOENCODING", "utf-8")
        env.setdefault("QT_QPA_PLATFORM", "offscreen")
        paths = [str(BASE_DIR), str(BASE_DIR / "venv" / "Lib" / "site-packages")]
        old_path = env.get("PYTHONPATH")
        env["PYTHONPATH"] = os.pathsep.join(paths + ([old_path] if old_path else []))

        startupinfo = None
        creationflags = 0
        if os.name == "nt":
            startupinfo = subprocess.STARTUPINFO()
            startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)

        started = time.perf_counter()
        try:
            proc = subprocess.run(
                command,
                cwd=str(BASE_DIR),
                env=env,
                capture_output=True,
                text=True,
                timeout=300,
                startupinfo=startupinfo,
                creationflags=creationflags,
            )
        except subprocess.TimeoutExpired:
            self.finished_check.emit(False, "Verificacao demorou demais e foi interrompida apos 5 minutos.")
            return
        except Exception as exc:
            self.finished_check.emit(False, f"Nao consegui iniciar a verificacao:\n{exc}")
            return

        elapsed = time.perf_counter() - started
        output = (proc.stdout or "").strip()
        error = (proc.stderr or "").strip()
        text = output
        if error:
            text = f"{text}\n\n[stderr]\n{error}" if text else error
        text = text or "Verificacao terminou sem saida."
        text = f"{text}\n\nTempo total visto pela interface: {elapsed:.1f}s"
        self.finished_check.emit(proc.returncode == 0, text)


class MaintenancePanel(QFrame):
    """Card de manutencao para a aba Config."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.worker = None
        self._build()

    def _build(self):
        self.setStyleSheet(
            "QFrame{background:#0b1626;border:1px solid rgba(34,211,238,0.14);border-radius:16px;}"
        )
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 14)
        root.setSpacing(9)

        title = QLabel(f"Verificacao e espaco do {APP_CODENAME}")
        title.setStyleSheet(label_qss("title").replace("18px", "15px"))
        root.addWidget(title)
        subtitle = QLabel("Rode checks, veja o peso do projeto e simule limpeza segura sem abrir terminal.")
        subtitle.setWordWrap(True)
        subtitle.setStyleSheet(label_qss("muted"))
        root.addWidget(subtitle)

        actions = QHBoxLayout()
        self.quick_btn = QPushButton("Verificar rapido")
        self.quick_btn.setMinimumHeight(34)
        self.quick_btn.setCursor(Qt.PointingHandCursor)
        self.quick_btn.setStyleSheet(button_qss("primary"))
        self.quick_btn.clicked.connect(lambda: self.run_check("quick"))
        actions.addWidget(self.quick_btn)

        self.full_btn = QPushButton("Verificar completo")
        self.full_btn.setMinimumHeight(34)
        self.full_btn.setCursor(Qt.PointingHandCursor)
        self.full_btn.setStyleSheet(button_qss("secondary"))
        self.full_btn.clicked.connect(lambda: self.run_check("full"))
        actions.addWidget(self.full_btn)

        self.copy_btn = QPushButton("Copiar resultado")
        self.copy_btn.setMinimumHeight(34)
        self.copy_btn.setCursor(Qt.PointingHandCursor)
        self.copy_btn.setStyleSheet(button_qss("secondary"))
        self.copy_btn.clicked.connect(self.copy_result)
        actions.addWidget(self.copy_btn)
        root.addLayout(actions)

        storage_actions = QHBoxLayout()
        self.storage_btn = QPushButton("Relatorio de espaco")
        self.storage_btn.setMinimumHeight(34)
        self.storage_btn.setCursor(Qt.PointingHandCursor)
        self.storage_btn.setStyleSheet(button_qss("secondary"))
        self.storage_btn.clicked.connect(lambda: self.run_check("storage"))
        storage_actions.addWidget(self.storage_btn)

        self.cleanup_btn = QPushButton("Limpeza segura (simular)")
        self.cleanup_btn.setMinimumHeight(34)
        self.cleanup_btn.setCursor(Qt.PointingHandCursor)
        self.cleanup_btn.setStyleSheet(button_qss("secondary"))
        self.cleanup_btn.clicked.connect(lambda: self.run_check("cleanup"))
        storage_actions.addWidget(self.cleanup_btn)
        root.addLayout(storage_actions)

        state_actions = QHBoxLayout()
        self.state_btn = QPushButton("Estado central")
        self.state_btn.setMinimumHeight(34)
        self.state_btn.setCursor(Qt.PointingHandCursor)
        self.state_btn.setStyleSheet(button_qss("secondary"))
        self.state_btn.clicked.connect(lambda: self.run_check("appstore"))
        state_actions.addWidget(self.state_btn)

        self.sync_state_btn = QPushButton("Sincronizar estado")
        self.sync_state_btn.setMinimumHeight(34)
        self.sync_state_btn.setCursor(Qt.PointingHandCursor)
        self.sync_state_btn.setStyleSheet(button_qss("primary"))
        self.sync_state_btn.clicked.connect(lambda: self.run_check("sync_state"))
        state_actions.addWidget(self.sync_state_btn)

        self.state_backup_btn = QPushButton("Backup estado central")
        self.state_backup_btn.setMinimumHeight(34)
        self.state_backup_btn.setCursor(Qt.PointingHandCursor)
        self.state_backup_btn.setStyleSheet(button_qss("secondary"))
        self.state_backup_btn.clicked.connect(lambda: self.run_check("appstore_backup"))
        state_actions.addWidget(self.state_backup_btn)
        self.health_report_btn = QPushButton("Relatorio geral")
        self.health_report_btn.setMinimumHeight(34)
        self.health_report_btn.setCursor(Qt.PointingHandCursor)
        self.health_report_btn.setStyleSheet(button_qss("secondary"))
        self.health_report_btn.clicked.connect(lambda: self.run_check("health_report"))
        state_actions.addWidget(self.health_report_btn)
        root.addLayout(state_actions)

        self.status_label = QLabel("Pronto para verificar.")
        self.status_label.setStyleSheet("color:#94a3b8;font-size:11px;background:transparent;border:none;")
        root.addWidget(self.status_label)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setMinimumHeight(170)
        self.output.setPlaceholderText("O resultado dos checks aparece aqui...")
        self.output.setStyleSheet(
            "QTextEdit{background:#08111f;color:#e2e8f0;border:1px solid rgba(148,163,184,0.10);"
            "border-radius:12px;padding:10px;font-family:'Consolas','Cascadia Code',monospace;font-size:11px;}"
        )
        root.addWidget(self.output)

    def run_check(self, mode: str):
        if self.worker and self.worker.isRunning():
            QMessageBox.information(self, "Verificacao", "Ja existe uma verificacao em andamento.")
            return
        self.set_running(True)
        labels = {
            "quick": "rapida",
            "full": "completa",
            "storage": "de espaco",
            "cleanup": "de limpeza segura",
            "appstore": "do estado central",
            "appstore_backup": "com backup do estado central",
            "health_report": "de saude geral",
            "sync_state": "de sincronizacao do estado central",
        }
        label = labels.get(mode, mode)
        self.status_label.setText(f"Rodando manutencao {label}...")
        self.output.setPlainText(f"Iniciando manutencao {label}. Aguarde...")
        self.worker = MaintenanceCheckWorker(mode, self)
        self.worker.finished_check.connect(self.on_finished)
        self.worker.start()

    def on_finished(self, ok: bool, text: str):
        self.set_running(False)
        self.output.setPlainText(text)
        self.status_label.setText("Tudo OK." if ok else "Falha encontrada. Copie o resultado para corrigir.")
        self.status_label.setStyleSheet(
            "color:#10b981;font-size:11px;background:transparent;border:none;" if ok
            else "color:#ef4444;font-size:11px;background:transparent;border:none;"
        )

    def set_running(self, running: bool):
        self.quick_btn.setEnabled(not running)
        self.full_btn.setEnabled(not running)
        self.copy_btn.setEnabled(not running)
        if hasattr(self, "storage_btn"):
            self.storage_btn.setEnabled(not running)
        if hasattr(self, "cleanup_btn"):
            self.cleanup_btn.setEnabled(not running)
        if hasattr(self, "state_btn"):
            self.state_btn.setEnabled(not running)
        if hasattr(self, "sync_state_btn"):
            self.sync_state_btn.setEnabled(not running)
        if hasattr(self, "state_backup_btn"):
            self.state_backup_btn.setEnabled(not running)
        if hasattr(self, "health_report_btn"):
            self.health_report_btn.setEnabled(not running)

    def copy_result(self):
        text = self.output.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Verificacao", "Ainda nao tem resultado para copiar.")
            return
        QApplication.clipboard().setText(text)
        self.status_label.setText("Resultado copiado.")
        self.status_label.setStyleSheet("color:#38bdf8;font-size:11px;background:transparent;border:none;")
