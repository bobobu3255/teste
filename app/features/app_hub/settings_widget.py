#!/usr/bin/env python3
"""Configuracoes gerais e manutencao visual do app."""
from __future__ import annotations

import json
import os
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QFileDialog, QFrame, QHBoxLayout, QLabel,
    QLineEdit, QMessageBox, QPushButton, QScrollArea, QSpinBox, QTabWidget,
    QVBoxLayout, QWidget,
)

from browser_manager import BrowserManager
from app.core.paths import BASE_DIR, CONFIG_DIR
from app.features.app_hub.logs_panel import PrettyLogsWidget
from app.features.app_hub.maintenance_panel import MaintenancePanel
from app.ui.components import button_qss, field_qss, label_qss

try:
    from app.core.app_context import get_app_store
except Exception:
    get_app_store = None


SETTINGS_FILE = CONFIG_DIR / "app_general_settings.json"
LAST_BACKUP_FILE = CONFIG_DIR / "last_auto_backup.txt"


class BackupWorker(QThread):
    finished_backup = pyqtSignal(bool, str)

    def run(self):
        try:
            manager = BrowserManager()
            path = manager.create_browser_backup()
            if path:
                self.finished_backup.emit(True, str(path))
            else:
                self.finished_backup.emit(False, "Nao foi possivel criar o backup.")
        except Exception as exc:
            self.finished_backup.emit(False, str(exc))


def _load_json(path, default):
    try:
        if Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _save_json(path, data):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def load_app_settings():
    data = _load_json(SETTINGS_FILE, {})
    defaults = {
        "theme": "Escuro profissional",
        "ui_scale": 100,
        "compact_mode": False,
        "data_folder": str(BASE_DIR),
        "auto_backup": True,
        "workspace": "Padrao",
    }
    defaults.update(data if isinstance(data, dict) else {})
    if get_app_store:
        try:
            central = get_app_store().get_state("app.settings", {})
            if isinstance(central, dict):
                defaults.update(central)
        except Exception:
            pass
    return defaults


def save_app_settings(data):
    _save_json(SETTINGS_FILE, data)
    if get_app_store:
        try:
            store = get_app_store()
            store.set_state("app.settings", data)
            store.add_event("settings", "settings_saved", "Configuracoes gerais salvas.", payload=data)
        except Exception:
            pass


def maybe_run_daily_backup(browser_manager=None):
    settings = load_app_settings()
    if not settings.get("auto_backup", True):
        return None
    today = datetime.now().strftime("%Y-%m-%d")
    if LAST_BACKUP_FILE.exists() and LAST_BACKUP_FILE.read_text(encoding="utf-8").strip() == today:
        return None
    manager = browser_manager or BrowserManager()
    backup_path = manager.create_browser_backup()
    LAST_BACKUP_FILE.parent.mkdir(parents=True, exist_ok=True)
    LAST_BACKUP_FILE.write_text(today, encoding="utf-8")
    if get_app_store:
        try:
            store = get_app_store()
            store.set_state("backup.last_daily", {"date": today, "path": str(backup_path) if backup_path else ""})
            store.add_event("backup", "daily_backup", f"Backup diario: {backup_path}")
        except Exception:
            pass
    return backup_path


class GeneralSettingsWidget(QWidget):
    def __init__(self, browser_manager=None, parent=None):
        super().__init__(parent)
        self.browser_manager = browser_manager or BrowserManager()
        self.settings = load_app_settings()
        self._build()

    def _button(self, text, role="secondary", size="md"):
        button = QPushButton(text)
        button.setCursor(Qt.PointingHandCursor)
        button.setStyleSheet(button_qss(role, size))
        return button

    def _style_field(self, widget):
        widget.setStyleSheet(field_qss())
        return widget

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        header = QHBoxLayout()
        title_box = QVBoxLayout()
        title = QLabel("Configuracoes Gerais")
        title.setStyleSheet(label_qss("title").replace("18px", "22px"))
        title_box.addWidget(title)
        subtitle = QLabel("Ajustes do app separados por area para ficar mais facil de entender.")
        subtitle.setStyleSheet(label_qss("subtitle"))
        title_box.addWidget(subtitle)
        header.addLayout(title_box, 1)

        reload_btn = self._button("Recarregar tela", "secondary", "lg")
        reload_btn.setToolTip("Puxa mudancas visuais da tela aberta sem fechar o projeto inteiro.")
        reload_btn.clicked.connect(self.reload_current_page)
        header.addWidget(reload_btn)

        restart_btn = self._button("Reiniciar app", "warning", "lg")
        restart_btn.setToolTip("Fecha e abre o projeto automaticamente quando a mudanca for mais profunda.")
        restart_btn.clicked.connect(self.restart_application)
        header.addWidget(restart_btn)

        save_btn = self._button("Salvar configuracoes", "primary", "lg")
        save_btn.clicked.connect(self.save)
        header.addWidget(save_btn)
        root.addLayout(header)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("GeneralSettingsTabs")
        self.tabs.setStyleSheet(self._tab_qss())
        self.tabs.addTab(self._build_general_tab(), "Geral")
        self.tabs.addTab(self._build_backup_tab(), "Backup")
        self.tabs.addTab(self._build_ai_tab(), "IA Local")
        self.tabs.addTab(self._build_maintenance_tab(), "Manutencao")
        root.addWidget(self.tabs, 1)

    def _tab_qss(self):
        return """
        QTabWidget#GeneralSettingsTabs::pane {
            border: 1px solid rgba(34,211,238,0.12);
            border-radius: 14px;
            background: #07080f;
            top: -1px;
        }
        QTabWidget#GeneralSettingsTabs QTabBar {
            background: transparent;
            max-height: 999px;
        }
        QTabWidget#GeneralSettingsTabs QTabBar::tab {
            background: #101827;
            color: #94a3b8;
            min-height: 36px;
            min-width: 132px;
            padding: 8px 18px;
            margin-right: 8px;
            border: 1px solid rgba(148,163,184,0.12);
            border-top-left-radius: 10px;
            border-top-right-radius: 10px;
            font-weight: 800;
        }
        QTabWidget#GeneralSettingsTabs QTabBar::tab:selected {
            background: #0b2c3a;
            color: #67e8f9;
            border-color: rgba(34,211,238,0.42);
        }
        QTabWidget#GeneralSettingsTabs QTabBar::tab:hover:!selected {
            color: #e2e8f0;
            background: #111c2f;
        }
        """

    def _tab_body(self):
        page = QWidget()
        page.setStyleSheet("background:#07080f;")
        outer = QVBoxLayout(page)
        outer.setContentsMargins(0, 0, 0, 0)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea{background:#07080f;border:none;}")
        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(12)
        scroll.setWidget(content)
        outer.addWidget(scroll)
        return page, layout

    def _build_general_tab(self):
        page, body_lay = self._tab_body()

        app_card = self._section_card("Aparencia e Workspace", "Como o projeto deve parecer e organizar campanhas.")
        self.workspace_input = self._style_field(QLineEdit(self.settings.get("workspace", "Padrao")))
        app_card.layout().addWidget(self._row("Workspace/campanha", self.workspace_input))

        self.theme_combo = self._style_field(QComboBox())
        self.theme_combo.addItems(["Escuro profissional", "Claro", "Compacto escuro"])
        self.theme_combo.setCurrentText(self.settings.get("theme", "Escuro profissional"))
        app_card.layout().addWidget(self._row("Tema", self.theme_combo))

        self.scale_spin = self._style_field(QSpinBox())
        self.scale_spin.setRange(80, 130)
        self.scale_spin.setSuffix("%")
        self.scale_spin.setValue(int(self.settings.get("ui_scale", 100)))
        app_card.layout().addWidget(self._row("Tamanho da interface", self.scale_spin))
        body_lay.addWidget(app_card)

        window_card = self._section_card("Janela e comportamento", "Controle como o app abre, fecha e usa o painel compacto.")
        self.compact_check = QCheckBox("Iniciar preferindo modo compacto")
        self.compact_check.setChecked(bool(self.settings.get("compact_mode", False)))
        window_card.layout().addWidget(self._check_row(self.compact_check, "Abre o painel flutuante como preferencia."))

        self.close_to_tray_check = QCheckBox("Fechar no X minimiza para bandeja")
        self.close_to_tray_check.setChecked(bool(self.settings.get("close_to_tray", False)))
        window_card.layout().addWidget(self._check_row(self.close_to_tray_check, "Desmarcado fecha o projeto de verdade."))
        body_lay.addWidget(window_card)
        body_lay.addStretch()
        return page

    def _build_backup_tab(self):
        page, body_lay = self._tab_body()

        data_card = self._section_card("Dados e Backup", "Pasta de dados, backup inteligente e restauracao.")
        data_row = QHBoxLayout()
        self.data_folder = self._style_field(QLineEdit(self.settings.get("data_folder", str(BASE_DIR))))
        browse_btn = self._button("Escolher pasta", "secondary")
        browse_btn.clicked.connect(self.choose_data_folder)
        data_row.addWidget(self.data_folder, 1)
        data_row.addWidget(browse_btn)
        data_card.layout().addWidget(self._row("Pasta de dados", data_row))

        self.backup_check = QCheckBox("Backup automatico diario local")
        self.backup_check.setChecked(bool(self.settings.get("auto_backup", True)))
        data_card.layout().addWidget(self._check_row(self.backup_check, "Mantido como preferencia; backup pesado nao roda na abertura."))

        backup_actions = QHBoxLayout()
        self.backup_btn = self._button("Criar backup agora", "success")
        self.backup_btn.clicked.connect(self.create_backup_now)
        backup_actions.addWidget(self.backup_btn)
        restore_btn = self._button("Restaurar backup", "secondary")
        restore_btn.clicked.connect(self.restore_backup)
        backup_actions.addWidget(restore_btn)
        data_card.layout().addLayout(backup_actions)
        body_lay.addWidget(data_card)
        body_lay.addStretch()
        return page

    def _build_ai_tab(self):
        page, body_lay = self._tab_body()

        ai_card = self._section_card("IA Local", "Atalhos para configurar Ollama, LM Studio, GPT4All ou LocalAI.")
        self.ai_provider_combo = self._style_field(QComboBox())
        self.ai_provider_combo.addItems(["Ollama", "OpenAI Compativel", "llama.cpp"])
        self.ai_provider_combo.setCurrentText(self.settings.get("ai_provider", "Ollama"))
        ai_card.layout().addWidget(self._row("Motor preferido", self.ai_provider_combo))
        self.ai_model_input = self._style_field(QLineEdit(self.settings.get("ai_model", "llama3.2:3b")))
        ai_card.layout().addWidget(self._row("Modelo preferido", self.ai_model_input))
        ai_actions = QHBoxLayout()
        open_ai_btn = self._button("Abrir aba IA Local", "primary")
        open_ai_btn.clicked.connect(self._open_ai_page)
        ai_actions.addWidget(open_ai_btn)
        ai_actions.addStretch()
        ai_card.layout().addLayout(ai_actions)
        body_lay.addWidget(ai_card)
        body_lay.addStretch()
        return page

    def _build_maintenance_tab(self):
        page, body_lay = self._tab_body()

        maintenance_card = self._section_card("Reparos rapidos", "Acoes simples quando algo parar de funcionar.")
        actions = QHBoxLayout()
        repair_btn = self._button("Reparar dependencias", "warning")
        repair_btn.clicked.connect(self.repair_dependencies)
        actions.addWidget(repair_btn)
        open_folder_btn = self._button("Abrir pasta do projeto", "secondary")
        open_folder_btn.clicked.connect(self.open_project_folder)
        actions.addWidget(open_folder_btn)
        reload_btn = self._button("Recarregar tela atual", "primary")
        reload_btn.setToolTip("Puxa mudancas visuais da tela aberta sem fechar o projeto inteiro.")
        reload_btn.clicked.connect(self.reload_current_page)
        actions.addWidget(reload_btn)
        restart_btn = self._button("Reiniciar app", "warning")
        restart_btn.setToolTip("Fecha e abre o projeto automaticamente quando a mudanca for mais profunda.")
        restart_btn.clicked.connect(self.restart_application)
        actions.addWidget(restart_btn)
        actions.addStretch()
        maintenance_card.layout().addLayout(actions)
        body_lay.addWidget(maintenance_card)

        self.maintenance_panel = MaintenancePanel(self)
        body_lay.addWidget(self.maintenance_panel)

        self.logs = PrettyLogsWidget()
        body_lay.addWidget(self.logs, 1)
        return page

    def _section_card(self, title, subtitle):
        frame = QFrame()
        frame.setStyleSheet(
            "QFrame{background:#0b1626;border:1px solid rgba(34,211,238,0.14);border-radius:16px;}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(9)
        title_lbl = QLabel(title)
        title_lbl.setStyleSheet(label_qss("title").replace("18px", "15px"))
        sub_lbl = QLabel(subtitle)
        sub_lbl.setWordWrap(True)
        sub_lbl.setStyleSheet(label_qss("muted"))
        lay.addWidget(title_lbl)
        lay.addWidget(sub_lbl)
        return frame

    def _row(self, label, widget_or_layout):
        frame = QFrame()
        frame.setStyleSheet("QFrame{background:#08111f;border:1px solid rgba(148,163,184,0.10);border-radius:12px;}")
        lay = QHBoxLayout(frame)
        lay.setContentsMargins(12, 9, 12, 9)
        lbl = QLabel(label)
        lbl.setMinimumWidth(160)
        lbl.setStyleSheet(label_qss("muted") + "font-weight:700;")
        lay.addWidget(lbl)
        if isinstance(widget_or_layout, QHBoxLayout):
            lay.addLayout(widget_or_layout, 1)
        else:
            lay.addWidget(widget_or_layout, 1)
        return frame

    def _check_row(self, checkbox, hint):
        frame = QFrame()
        frame.setStyleSheet("QFrame{background:#08111f;border:1px solid rgba(148,163,184,0.10);border-radius:12px;}")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 9, 12, 9)
        checkbox.setStyleSheet("QCheckBox{color:#e2e8f0;font-weight:700;background:transparent;border:none;} QCheckBox::indicator{width:16px;height:16px;}")
        lay.addWidget(checkbox)
        label = QLabel(hint)
        label.setWordWrap(True)
        label.setStyleSheet(label_qss("muted"))
        lay.addWidget(label)
        return frame

    def choose_data_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Pasta de dados", self.data_folder.text())
        if folder:
            self.data_folder.setText(folder)

    def save(self):
        data = {
            "workspace": self.workspace_input.text().strip() or "Padrao",
            "theme": self.theme_combo.currentText(),
            "ui_scale": self.scale_spin.value(),
            "compact_mode": self.compact_check.isChecked(),
            "close_to_tray": self.close_to_tray_check.isChecked(),
            "auto_backup": self.backup_check.isChecked(),
            "data_folder": self.data_folder.text().strip() or str(BASE_DIR),
            "ai_provider": self.ai_provider_combo.currentText(),
            "ai_model": self.ai_model_input.text().strip() or "llama3.2:3b",
        }
        save_app_settings(data)
        QMessageBox.information(self, "Configuracoes", "Configuracoes salvas.")

    def _open_ai_page(self):
        parent = self.window()
        if parent and hasattr(parent, "open_page_by_name"):
            parent.open_page_by_name("IA Local")

    def reload_current_page(self):
        parent = self.window()
        if parent and hasattr(parent, "reload_current_page"):
            parent.reload_current_page()

    def restart_application(self):
        parent = self.window()
        if parent and hasattr(parent, "restart_application"):
            parent.restart_application()

    def open_project_folder(self):
        try:
            if os.name == "nt":
                os.startfile(str(BASE_DIR))
            else:
                subprocess.Popen(["xdg-open", str(BASE_DIR)])
        except Exception as exc:
            QMessageBox.warning(self, "Pasta do projeto", f"Nao foi possivel abrir a pasta:\n{exc}")

    def create_backup_now(self):
        if hasattr(self, "_backup_worker") and self._backup_worker.isRunning():
            QMessageBox.information(self, "Backup", "Backup ja esta em andamento.")
            return
        self.backup_btn.setEnabled(False)
        self.backup_btn.setText("Criando backup...")
        if get_app_store:
            try:
                get_app_store().upsert_task(
                    "backup:manual",
                    "backup",
                    "Backup manual do projeto",
                    source="backup",
                    status="running",
                    priority=50,
                )
            except Exception:
                pass
        self._backup_worker = BackupWorker(self)
        self._backup_worker.finished_backup.connect(self._on_backup_finished)
        self._backup_worker.start()

    def _on_backup_finished(self, ok, message):
        self.backup_btn.setEnabled(True)
        self.backup_btn.setText("Criar backup agora")
        if ok:
            LAST_BACKUP_FILE.parent.mkdir(parents=True, exist_ok=True)
            LAST_BACKUP_FILE.write_text(datetime.now().strftime("%Y-%m-%d"), encoding="utf-8")
            if get_app_store:
                try:
                    get_app_store().update_task("backup:manual", status="success", last_error="")
                except Exception:
                    pass
            QMessageBox.information(self, "Backup", f"Backup criado:\n{message}")
        else:
            if get_app_store:
                try:
                    get_app_store().update_task("backup:manual", status="error", last_error=message, attempts_delta=1)
                except Exception:
                    pass
            QMessageBox.warning(self, "Backup", f"Nao foi possivel criar o backup:\n{message}")

    def restore_backup(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Restaurar backup", str(BASE_DIR), "Backups (*.zip)")
        if not file_path:
            return
        reply = QMessageBox.question(
            self,
            "Restaurar backup",
            "Isso vai restaurar arquivos do backup sobre a pasta do projeto. Continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                zf.extractall(BASE_DIR)
            QMessageBox.information(self, "Backup", "Backup restaurado. Reinicie o projeto para recarregar tudo.")
        except Exception as exc:
            QMessageBox.critical(self, "Backup", f"Erro ao restaurar backup:\n{exc}")

    def repair_dependencies(self):
        installer = BASE_DIR / "INSTALAR_TUDO.bat"
        if not installer.exists():
            QMessageBox.warning(self, "Reparo", "INSTALAR_TUDO.bat nao encontrado.")
            return
        try:
            subprocess.Popen(["cmd", "/c", "start", "/min", str(installer)], cwd=str(BASE_DIR))
            QMessageBox.information(self, "Reparo", "Reparo iniciado minimizado.")
        except Exception as exc:
            QMessageBox.critical(self, "Reparo", f"Nao foi possivel iniciar o reparo:\n{exc}")
