#!/usr/bin/env python3
"""
Browser Widget - Interface Gráfica do Navegador Seguro
Telegram Collector Pro v9.0 - Navegador Anti-Fingerprint

Este módulo contém a interface gráfica PyQt5 para gerenciar
perfis de navegação e configurações anti-fingerprint.
"""

import json
from html import escape as html_escape
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox,
    QGroupBox, QFormLayout, QMessageBox, QSpinBox,
    QCheckBox, QTextEdit, QSplitter, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QDialogButtonBox, QTabWidget, QInputDialog, QMenu, QApplication,
    QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QSize
from PyQt5.QtGui import QFont, QColor

from browser_manager import BrowserManager, BrowserProfile
from fingerprint_generator import FingerprintGenerator
from proxy_manager import ProxyManager

try:
    from address_generator import AddressGenerator
except Exception:
    AddressGenerator = None

try:
    from address_reserve import AddressExtractor
except Exception:
    AddressExtractor = None

try:
    from profile_defaults_manager import PasswordManager
except Exception:
    PasswordManager = None

from app.features.browser.styles import (
    browser_checkbox_qss, browser_dashboard_card_qss, browser_danger_button_qss,
    browser_guide_item_qss, browser_label_qss, browser_panel_qss,
    browser_primary_button_qss, browser_profile_row_qss, browser_profile_title_qss,
    browser_proxy_status_qss, browser_row_close_qss, browser_row_start_qss,
    browser_section_tab_qss, browser_start_button_qss, browser_status_qss,
    browser_success_button_qss, browser_vault_status_qss, browser_widget_qss,
)


class BrowserLaunchThread(QThread):
    """Thread para iniciar o navegador sem bloquear a UI."""
    
    finished = pyqtSignal(bool, str)
    browser_closed = pyqtSignal(str)  # Sinal quando o navegador é fechado
    thread_done = pyqtSignal(str)  # Sinal real de encerramento da thread
    
    def __init__(self, manager: BrowserManager, profile_id: str, url: str = None, monitor: bool = True):
        super().__init__()
        self.manager = manager
        self.profile_id = profile_id
        self.url = url
        self.monitor = monitor
        self._running = True
    
    def run(self):
        try:
            driver = self.manager.create_browser(self.profile_id, self.url)
            if driver and self.url and not self.manager.is_native_browser(self.profile_id):
                self.manager.navigate_to(self.profile_id, self.url)
            self.finished.emit(True, "Navegador iniciado com sucesso!")
            
            # Monitorar o navegador até ser fechado
            if self.monitor and driver and not self.manager.is_native_browser(self.profile_id):
                self._monitor_browser(driver)
                
        except ImportError as e:
            self.finished.emit(False, str(e))
        except Exception as e:
            error_msg = str(e)
            # Verificar se é erro de fechamento do navegador
            if self._is_browser_closed_error(error_msg):
                self.browser_closed.emit(self.profile_id)
            else:
                self.finished.emit(False, f"Erro ao iniciar navegador: {error_msg}")
        finally:
            self.thread_done.emit(self.profile_id)
    
    def _monitor_browser(self, driver):
        """Monitora o navegador e detecta quando é fechado."""
        import time
        while self._running:
            try:
                handles = driver.window_handles
                if not handles:
                    self.browser_closed.emit(self.profile_id)
                    break
                time.sleep(1)
            except Exception as e:
                # Navegador foi fechado
                if self._is_browser_closed_error(str(e)):
                    self.browser_closed.emit(self.profile_id)
                break
    
    def _is_browser_closed_error(self, error_msg: str) -> bool:
        """Verifica se o erro indica que o navegador foi fechado."""
        closed_indicators = [
            "session not created",
            "chrome not reachable",
            "no such window",
            "target window already closed",
            "unable to connect",
            "connection refused",
            "chrome instance exited",
            "invalid session id",
            "session deleted",
        ]
        error_lower = error_msg.lower()
        return any(indicator in error_lower for indicator in closed_indicators)
    
    def stop(self):
        """Para o monitoramento do navegador."""
        self._running = False


class BrowserFormatBackupThread(QThread):
    """Cria backup de formatação sem travar a interface."""

    finished_backup = pyqtSignal(dict)

    def __init__(self, manager: BrowserManager):
        super().__init__()
        self.manager = manager

    def run(self):
        result = self.manager.create_format_backup()
        self.finished_backup.emit(result)


class AutoLoginDialog(QDialog):
    """Diálogo para configurar auto-login."""
    
    def __init__(self, parent=None, existing_logins: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Auto-Login")
        self.setMinimumWidth(500)
        self.existing_logins = existing_logins or {}
        self.result_logins = {}
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("🔐 Configurações de Auto-Login")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #06b6d4;")
        layout.addWidget(title)
        
        info = QLabel("Configure credenciais para login automático em sites específicos.")
        info.setStyleSheet("color: #9ca3af; margin-bottom: 15px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Tabela de logins
        self.login_table = QTableWidget()
        self.login_table.setColumnCount(3)
        self.login_table.setHorizontalHeaderLabels(["URL", "Usuário", "Senha"])
        self.login_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.login_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.login_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        
        # Preencher com logins existentes
        for url, creds in self.existing_logins.items():
            row = self.login_table.rowCount()
            self.login_table.insertRow(row)
            self.login_table.setItem(row, 0, QTableWidgetItem(url))
            self.login_table.setItem(row, 1, QTableWidgetItem(creds.get("username", "")))
            self.login_table.setItem(row, 2, QTableWidgetItem(creds.get("password", "")))
        
        layout.addWidget(self.login_table)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        add_btn = QPushButton("➕ Adicionar")
        add_btn.clicked.connect(self.add_login)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QPushButton("🗑️ Remover")
        remove_btn.clicked.connect(self.remove_login)
        btn_layout.addWidget(remove_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Botões de diálogo
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def add_login(self):
        row = self.login_table.rowCount()
        self.login_table.insertRow(row)
        self.login_table.setItem(row, 0, QTableWidgetItem("https://"))
        self.login_table.setItem(row, 1, QTableWidgetItem(""))
        self.login_table.setItem(row, 2, QTableWidgetItem(""))
    
    def remove_login(self):
        current_row = self.login_table.currentRow()
        if current_row >= 0:
            self.login_table.removeRow(current_row)
    
    def accept(self):
        self.result_logins = {}
        for row in range(self.login_table.rowCount()):
            url_item = self.login_table.item(row, 0)
            user_item = self.login_table.item(row, 1)
            pass_item = self.login_table.item(row, 2)
            
            if url_item and user_item and pass_item:
                url = url_item.text().strip()
                username = user_item.text().strip()
                password = pass_item.text().strip()
                
                if url and username:
                    self.result_logins[url] = {
                        "username": username,
                        "password": password
                    }
        
        super().accept()


class FingerprintConfigDialog(QDialog):
    """Diálogo para configuração avançada de fingerprint."""
    
    def __init__(self, parent=None, current_fingerprint: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Configurar Fingerprint")
        self.setMinimumSize(600, 500)
        self.fingerprint_generator = FingerprintGenerator()
        self.current_fingerprint = current_fingerprint or {}
        self.result_fingerprint = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("🎭 Configuração de Fingerprint")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #06b6d4;")
        layout.addWidget(title)
        
        # Scroll area para o formulário
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll_widget = QWidget()
        form_layout = QFormLayout()
        
        # User-Agent
        self.ua_combo = QComboBox()
        self.ua_combo.setEditable(True)
        for ua in self.fingerprint_generator.get_available_user_agents()[:20]:
            self.ua_combo.addItem(ua[:80] + "..." if len(ua) > 80 else ua, ua)
        if self.current_fingerprint.get("user_agent"):
            self.ua_combo.setCurrentText(self.current_fingerprint["user_agent"][:80])
        form_layout.addRow("User-Agent:", self.ua_combo)
        
        # Resolução
        res_layout = QHBoxLayout()
        self.width_spin = QSpinBox()
        self.width_spin.setRange(800, 3840)
        self.width_spin.setValue(self.current_fingerprint.get("screen", {}).get("width", 1920))
        res_layout.addWidget(self.width_spin)
        res_layout.addWidget(QLabel("x"))
        self.height_spin = QSpinBox()
        self.height_spin.setRange(600, 2160)
        self.height_spin.setValue(self.current_fingerprint.get("screen", {}).get("height", 1080))
        res_layout.addWidget(self.height_spin)
        
        res_widget = QWidget()
        res_widget.setLayout(res_layout)
        form_layout.addRow("Resolução:", res_widget)
        
        # País/Timezone
        self.country_combo = QComboBox()
        countries = {
            "BR": "🇧🇷 Brasil",
            "US": "🇺🇸 Estados Unidos",
            "UK": "🇬🇧 Reino Unido",
            "DE": "🇩🇪 Alemanha",
            "FR": "🇫🇷 França",
            "ES": "🇪🇸 Espanha",
            "PT": "🇵🇹 Portugal",
            "JP": "🇯🇵 Japão",
            "CN": "🇨🇳 China",
            "AU": "🇦🇺 Austrália",
        }
        for code, name in countries.items():
            self.country_combo.addItem(name, code)
        current_country = self.current_fingerprint.get("country", "BR")
        index = self.country_combo.findData(current_country)
        if index >= 0:
            self.country_combo.setCurrentIndex(index)
        form_layout.addRow("País/Timezone:", self.country_combo)
        
        # WebGL Vendor
        self.webgl_vendor_combo = QComboBox()
        for vendor in self.fingerprint_generator.get_available_webgl_vendors():
            self.webgl_vendor_combo.addItem(vendor)
        current_vendor = self.current_fingerprint.get("webgl", {}).get("vendor", "")
        if current_vendor:
            index = self.webgl_vendor_combo.findText(current_vendor)
            if index >= 0:
                self.webgl_vendor_combo.setCurrentIndex(index)
        form_layout.addRow("WebGL Vendor:", self.webgl_vendor_combo)
        
        # WebGL Renderer
        self.webgl_renderer_combo = QComboBox()
        for renderer in self.fingerprint_generator.get_available_webgl_renderers():
            self.webgl_renderer_combo.addItem(renderer[:60] + "..." if len(renderer) > 60 else renderer, renderer)
        current_renderer = self.current_fingerprint.get("webgl", {}).get("renderer", "")
        if current_renderer:
            index = self.webgl_renderer_combo.findData(current_renderer)
            if index >= 0:
                self.webgl_renderer_combo.setCurrentIndex(index)
        form_layout.addRow("WebGL Renderer:", self.webgl_renderer_combo)
        
        # CPU Cores
        self.cpu_spin = QSpinBox()
        self.cpu_spin.setRange(1, 32)
        self.cpu_spin.setValue(self.current_fingerprint.get("hardware", {}).get("cpu_cores", 4))
        form_layout.addRow("CPU Cores:", self.cpu_spin)
        
        # Device Memory
        self.memory_combo = QComboBox()
        for mem in [2, 4, 8, 16, 32]:
            self.memory_combo.addItem(f"{mem} GB", mem)
        current_mem = self.current_fingerprint.get("hardware", {}).get("device_memory", 8)
        index = self.memory_combo.findData(current_mem)
        if index >= 0:
            self.memory_combo.setCurrentIndex(index)
        form_layout.addRow("Memória:", self.memory_combo)
        
        scroll_widget.setLayout(form_layout)
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)
        
        # Botão para randomizar
        random_btn = QPushButton("🎲 Randomizar Tudo")
        random_btn.clicked.connect(self.randomize_all)
        layout.addWidget(random_btn)
        
        # Botões de diálogo
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def randomize_all(self):
        """Randomiza todas as configurações."""
        country = self.country_combo.currentData()
        fp = self.fingerprint_generator.generate_random_fingerprint(country)
        
        # Atualizar campos
        ua = fp.get("user_agent", "")
        self.ua_combo.setCurrentText(ua[:80])
        
        self.width_spin.setValue(fp.get("screen", {}).get("width", 1920))
        self.height_spin.setValue(fp.get("screen", {}).get("height", 1080))
        
        vendor = fp.get("webgl", {}).get("vendor", "")
        index = self.webgl_vendor_combo.findText(vendor)
        if index >= 0:
            self.webgl_vendor_combo.setCurrentIndex(index)
        
        renderer = fp.get("webgl", {}).get("renderer", "")
        index = self.webgl_renderer_combo.findData(renderer)
        if index >= 0:
            self.webgl_renderer_combo.setCurrentIndex(index)
        
        self.cpu_spin.setValue(fp.get("hardware", {}).get("cpu_cores", 4))
        
        mem = fp.get("hardware", {}).get("device_memory", 8)
        index = self.memory_combo.findData(mem)
        if index >= 0:
            self.memory_combo.setCurrentIndex(index)
    
    def accept(self):
        """Gera o fingerprint com as configurações selecionadas."""
        country = self.country_combo.currentData()
        
        # Obter User-Agent (pode ser texto editado ou item selecionado)
        ua_index = self.ua_combo.currentIndex()
        if ua_index >= 0:
            user_agent = self.ua_combo.itemData(ua_index) or self.ua_combo.currentText()
        else:
            user_agent = self.ua_combo.currentText()
        
        # Obter WebGL Renderer
        renderer_index = self.webgl_renderer_combo.currentIndex()
        if renderer_index >= 0:
            webgl_renderer = self.webgl_renderer_combo.itemData(renderer_index) or self.webgl_renderer_combo.currentText()
        else:
            webgl_renderer = self.webgl_renderer_combo.currentText()
        
        self.result_fingerprint = self.fingerprint_generator.generate_custom_fingerprint(
            user_agent=user_agent,
            resolution=(self.width_spin.value(), self.height_spin.value()),
            country=country,
            webgl_vendor=self.webgl_vendor_combo.currentText(),
            webgl_renderer=webgl_renderer,
        )
        
        # Adicionar configurações de hardware
        self.result_fingerprint["hardware"] = {
            "cpu_cores": self.cpu_spin.value(),
            "device_memory": self.memory_combo.currentData(),
        }
        
        super().accept()


class BrowserAccountDialog(QDialog):
    """Dialogo simples para cadastrar conta vinculada a perfil."""

    def __init__(self, profiles, parent=None, account: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciador de Contas")
        self.setMinimumWidth(520)
        self.account = account.copy() if account else {}
        self.result_account = None
        self.profiles = profiles
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.name_input = QLineEdit(self.account.get("name", ""))
        self.email_input = QLineEdit(self.account.get("email", ""))
        self.password_input = QLineEdit(self.account.get("password", ""))
        self.site_input = QLineEdit(self.account.get("site", ""))
        self.status_combo = QComboBox()
        for status in ["novo", "em uso", "pausado", "problema", "finalizado"]:
            self.status_combo.addItem(status)
        status_index = self.status_combo.findText(self.account.get("status", "novo"))
        if status_index >= 0:
            self.status_combo.setCurrentIndex(status_index)

        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Sem perfil vinculado", "")
        for profile in self.profiles:
            self.profile_combo.addItem(profile.name, profile.id)
        profile_index = self.profile_combo.findData(self.account.get("profile_id", ""))
        if profile_index >= 0:
            self.profile_combo.setCurrentIndex(profile_index)

        self.notes_input = QTextEdit(self.account.get("notes", ""))
        self.notes_input.setMaximumHeight(90)

        form.addRow("Nome:", self.name_input)
        form.addRow("Email/Usuário:", self.email_input)
        form.addRow("Senha:", self.password_input)
        form.addRow("Site:", self.site_input)
        form.addRow("Status:", self.status_combo)
        form.addRow("Perfil:", self.profile_combo)
        form.addRow("Anotação:", self.notes_input)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def accept(self):
        self.result_account = self.account.copy()
        self.result_account.update({
            "name": self.name_input.text().strip(),
            "email": self.email_input.text().strip(),
            "password": self.password_input.text(),
            "site": self.site_input.text().strip(),
            "status": self.status_combo.currentText(),
            "profile_id": self.profile_combo.currentData(),
            "notes": self.notes_input.toPlainText().strip(),
        })
        super().accept()


class BrowserTaskDialog(QDialog):
    """Dialogo simples para criar tarefa/checklist."""

    def __init__(self, profiles, accounts, parent=None, task: dict = None):
        super().__init__(parent)
        self.setWindowTitle("Gerador de Tarefas")
        self.setMinimumWidth(500)
        self.task = task.copy() if task else {}
        self.result_task = None
        self.profiles = profiles
        self.accounts = accounts
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()
        self.title_input = QLineEdit(self.task.get("title", ""))
        self.title_input.setPlaceholderText("Ex: abrir outlook, validar email, salvar observação")

        self.profile_combo = QComboBox()
        self.profile_combo.addItem("Sem perfil", "")
        for profile in self.profiles:
            self.profile_combo.addItem(profile.name, profile.id)
        profile_index = self.profile_combo.findData(self.task.get("profile_id", ""))
        if profile_index >= 0:
            self.profile_combo.setCurrentIndex(profile_index)

        self.account_combo = QComboBox()
        self.account_combo.addItem("Sem conta", "")
        for account in self.accounts:
            label = account.get("name") or account.get("email") or "Conta"
            self.account_combo.addItem(label, account.get("id", ""))
        account_index = self.account_combo.findData(self.task.get("account_id", ""))
        if account_index >= 0:
            self.account_combo.setCurrentIndex(account_index)

        self.notes_input = QTextEdit(self.task.get("notes", ""))
        self.notes_input.setMaximumHeight(90)
        self.done_checkbox = QCheckBox("Concluída")
        self.done_checkbox.setChecked(bool(self.task.get("done", False)))

        form.addRow("Tarefa:", self.title_input)
        form.addRow("Perfil:", self.profile_combo)
        form.addRow("Conta:", self.account_combo)
        form.addRow("Notas:", self.notes_input)
        form.addRow("", self.done_checkbox)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        self.setLayout(layout)

    def accept(self):
        self.result_task = self.task.copy()
        self.result_task.update({
            "title": self.title_input.text().strip(),
            "profile_id": self.profile_combo.currentData(),
            "account_id": self.account_combo.currentData(),
            "notes": self.notes_input.toPlainText().strip(),
            "done": self.done_checkbox.isChecked(),
        })
        super().accept()


class BrowserWidget(QWidget):
    """
    Widget principal do navegador seguro.
    Gerencia perfis de navegação e configurações anti-fingerprint.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.browser_manager = BrowserManager()
        self.proxy_manager = ProxyManager()
        self.fingerprint_generator = FingerprintGenerator()
        self.address_generator = AddressGenerator() if AddressGenerator else None
        self.address_reserve = AddressExtractor() if AddressExtractor else None
        self.selected_profile_id = None
        self.launch_thread = None
        self.launch_threads = {}
        self.launching_profile_ids = set()
        self.format_backup_thread = None
        self.password_manager = None
        self.init_ui()
    
    def _short_display(self, value, limit=42):
        """Encurta textos longos so para a lista visual, sem alterar dados reais."""
        text = str(value or "").strip()
        if len(text) <= limit:
            return text
        return text[: max(1, limit - 3)].rstrip() + "..."

    def init_ui(self):
        """Inicializa a interface do usuário."""
        self.setStyleSheet(browser_widget_qss())
        root_layout = QVBoxLayout()
        root_layout.setContentsMargins(16, 14, 16, 14)
        root_layout.setSpacing(12)

        header = QFrame()
        header.setObjectName("BrowserHeader")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(18, 14, 18, 14)
        header_layout.setSpacing(14)

        header_text = QVBoxLayout()
        header_text.setSpacing(2)
        title = QLabel("Navegador Seguro")
        title.setObjectName("BrowserTitle")
        self.browser_header_subtitle = QLabel("Perfis isolados, favoritos fixos, endereço inteligente e diagnóstico de páginas em um lugar só.")
        self.browser_header_subtitle.setObjectName("BrowserSubtitle")
        header_text.addWidget(title)
        header_text.addWidget(self.browser_header_subtitle)
        header_layout.addLayout(header_text, 1)

        self.browser_header_chip = QLabel("Modo visual novo")
        self.browser_header_chip.setObjectName("BrowserChip")
        self.browser_header_chip.setAlignment(Qt.AlignCenter)
        header_layout.addWidget(self.browser_header_chip)
        root_layout.addWidget(header)

        main_layout = QHBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(14)
        root_layout.addLayout(main_layout, 1)
        
        # === Coluna Esquerda - Lista de Perfis ===
        left_panel = QFrame()
        left_panel.setObjectName("BrowserPanel")
        left_layout = QVBoxLayout()
        left_layout.setContentsMargins(12, 12, 12, 12)
        left_layout.setSpacing(9)
        
        # Título da lista
        profiles_title = QLabel("Perfis de Navegação")
        profiles_title.setStyleSheet(browser_label_qss("section"))
        left_layout.addWidget(profiles_title)

        self.status_label = QLabel("Pronto")
        self.status_label.setWordWrap(True)
        self.status_label.setStyleSheet(browser_status_qss())
        left_layout.addWidget(self.status_label)

        self.profile_search = QLineEdit()
        self.profile_search.setPlaceholderText("Filtrar perfis...")
        self.profile_search.textChanged.connect(self.refresh_profile_list)
        left_layout.addWidget(self.profile_search)

        self.show_archived_checkbox = QCheckBox("Mostrar arquivados")
        self.show_archived_checkbox.setToolTip("Perfis arquivados ficam escondidos da lista normal, mas mantêm cookies, logins e dados salvos.")
        self.show_archived_checkbox.setStyleSheet(browser_checkbox_qss("#94a3b8"))
        self.show_archived_checkbox.toggled.connect(self.refresh_profile_list)
        left_layout.addWidget(self.show_archived_checkbox)
        
        # Lista de perfis
        self.profile_list = QListWidget()
        self.profile_list.setMinimumWidth(250)
        self.profile_list.setSpacing(6)
        self.profile_list.setWordWrap(False)
        self.profile_list.setSelectionMode(QListWidget.ExtendedSelection)
        self.profile_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.profile_list.itemClicked.connect(self.on_profile_selected)
        self.profile_list.itemDoubleClicked.connect(self.start_browser)
        self.profile_list.customContextMenuRequested.connect(self.show_profile_menu)
        left_layout.addWidget(self.profile_list)
        
        # Botões de gerenciamento de perfis
        profile_btn_top = QHBoxLayout()
        profile_btn_top.setSpacing(8)
        profile_btn_bottom = QHBoxLayout()
        profile_btn_bottom.setSpacing(8)
        
        add_btn = QPushButton("Novo")
        add_btn.setObjectName("BrowserPrimaryButton")
        add_btn.setToolTip("Criar novo perfil")
        add_btn.setMinimumHeight(36)
        add_btn.clicked.connect(self.create_profile)
        profile_btn_top.addWidget(add_btn)
        
        edit_btn = QPushButton("Editar")
        edit_btn.setToolTip("Editar perfil")
        edit_btn.setMinimumHeight(36)
        edit_btn.clicked.connect(self.edit_profile)
        profile_btn_top.addWidget(edit_btn)

        clone_btn = QPushButton("Clonar")
        clone_btn.setToolTip("Clonar perfil")
        clone_btn.setMinimumHeight(36)
        clone_btn.clicked.connect(self.clone_profile)
        profile_btn_top.addWidget(clone_btn)
        
        delete_btn = QPushButton("Excluir")
        delete_btn.setObjectName("BrowserDangerButton")
        delete_btn.setToolTip("Remover perfil selecionado ou vários perfis marcados")
        delete_btn.setMinimumHeight(36)
        delete_btn.clicked.connect(self.delete_profile)
        profile_btn_bottom.addWidget(delete_btn)

        archive_btn = QPushButton("Arquivar")
        archive_btn.setToolTip("Esconder perfil da lista sem apagar cookies, logins ou dados.")
        archive_btn.setMinimumHeight(36)
        archive_btn.clicked.connect(self.archive_selected_profiles)
        profile_btn_bottom.addWidget(archive_btn)

        select_all_btn = QPushButton("Todos")
        select_all_btn.setToolTip("Selecionar todos os perfis visíveis")
        select_all_btn.setMinimumHeight(36)
        select_all_btn.clicked.connect(self.select_all_profiles)
        profile_btn_bottom.addWidget(select_all_btn)
        
        left_layout.addLayout(profile_btn_top)
        left_layout.addLayout(profile_btn_bottom)
        
        # Botão de Perfil Rápido
        quick_btn = QPushButton("🚀 Perfil Rápido")
        quick_btn.setObjectName("BrowserSuccessButton")
        quick_btn.setStyleSheet(browser_success_button_qss())
        quick_btn.setToolTip("Criar perfil aleatório e iniciar navegador")
        quick_btn.clicked.connect(self.create_quick_profile)
        left_layout.addWidget(quick_btn)

        batch_btn = QPushButton("➕ Criar Lote de Perfis")
        batch_btn.setToolTip("Criar vários perfis isolados de uma vez")
        batch_btn.clicked.connect(self.create_profile_batch)
        left_layout.addWidget(batch_btn)

        utility_row = QHBoxLayout()
        close_active_btn = QPushButton("Fechar")
        close_active_btn.setToolTip("Fechar navegador do perfil selecionado")
        close_active_btn.clicked.connect(self.close_selected_browser)
        utility_row.addWidget(close_active_btn)
        close_all_btn = QPushButton("Fechar Todos")
        close_all_btn.clicked.connect(self.close_all_browsers)
        utility_row.addWidget(close_all_btn)
        left_layout.addLayout(utility_row)

        apply_defaults_btn = QPushButton("Aplicar padrões aos perfis")
        apply_defaults_btn.setToolTip("Favoritos são gravados nos perfis. Extensões padrão carregam em todos ao abrir.")
        apply_defaults_btn.clicked.connect(self.apply_defaults_to_all_profiles)
        apply_defaults_btn.setVisible(False)
        left_layout.addWidget(apply_defaults_btn)

        batch_row = QHBoxLayout()
        batch_favs_btn = QPushButton("⭐ Padrões selecionados")
        batch_favs_btn.setToolTip("Aplicar favoritos/extensões padrão apenas nos perfis selecionados.")
        batch_favs_btn.clicked.connect(self.apply_defaults_to_selected_profiles)
        batch_favs_btn.setVisible(False)
        batch_row.addWidget(batch_favs_btn)
        batch_clear_btn = QPushButton("🧹 Limpar selecionados")
        batch_clear_btn.setToolTip("Limpar dados dos perfis selecionados que estiverem fechados.")
        batch_clear_btn.clicked.connect(self.clear_selected_profile_data)
        batch_clear_btn.setVisible(False)
        batch_row.addWidget(batch_clear_btn)
        left_layout.addLayout(batch_row)

        batch_tags_btn = QPushButton("🏷️ Mudar tags dos selecionados")
        batch_tags_btn.clicked.connect(self.change_tags_selected_profiles)
        batch_tags_btn.setVisible(False)
        left_layout.addWidget(batch_tags_btn)
        
        left_panel.setLayout(left_layout)
        left_panel.setMinimumWidth(280)
        left_panel.setMaximumWidth(460)
        self.browser_left_panel = left_panel
        
        # === Coluna Direita - Configurações ===
        right_panel = QFrame()
        right_panel.setObjectName("BrowserRightPanel")
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(12, 12, 12, 12)
        right_layout.setSpacing(10)
        
        # Scroll area para configurações
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        
        config_widget = QWidget()
        config_layout = QVBoxLayout()
        config_layout.setContentsMargins(0, 0, 0, 0)
        config_layout.setSpacing(10)

        dashboard_group = QGroupBox("Visão Geral")
        dashboard_layout = QHBoxLayout()
        self.total_profiles_label = QLabel("Perfis: 0")
        self.open_profiles_label = QLabel("Abertos: 0")
        self.last_used_label = QLabel("Último uso: -")
        for label in (self.total_profiles_label, self.open_profiles_label, self.last_used_label):
            label.setWordWrap(True)
            label.setStyleSheet(browser_dashboard_card_qss())
            dashboard_layout.addWidget(label)
        dashboard_group.setLayout(dashboard_layout)
        config_layout.addWidget(dashboard_group)

        guide_frame = QFrame()
        guide_frame.setObjectName("browserGuide")
        guide_layout = QHBoxLayout()
        guide_layout.setContentsMargins(14, 12, 14, 12)
        guide_layout.setSpacing(12)
        guide_items = [
            ("Perfil isolado", "Cookie, login e dados separados por perfil."),
            ("Padrões prontos", "Favoritos e extensões ficam sempre disponíveis."),
            ("Abrir rápido", "Use URL, busca ou favorito direto no perfil."),
        ]
        for title, text in guide_items:
            item = QLabel(f"<b>{title}</b><br><span>{text}</span>")
            item.setWordWrap(True)
            item.setStyleSheet(browser_guide_item_qss())
            guide_layout.addWidget(item)
        guide_frame.setLayout(guide_layout)
        config_layout.addWidget(guide_frame)
        
        # Grupo: Informações do Perfil
        info_group = QGroupBox("📝 Informações do Perfil")
        info_layout = QFormLayout()

        info_hint = QLabel("Use o nome para identificar a conta. O ID é gerado sozinho para manter os dados separados.")
        info_hint.setWordWrap(True)
        info_hint.setStyleSheet(browser_label_qss("hint"))
        info_layout.addRow(info_hint)
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome do perfil")
        info_layout.addRow("Nome:", self.name_input)
        
        self.profile_id_label = QLabel("-")
        self.profile_id_label.setStyleSheet(browser_label_qss("faded"))
        info_layout.addRow("ID:", self.profile_id_label)

        self.browser_mode_combo = QComboBox()
        self.browser_mode_combo.addItems(["Auto", "Chrome", "Edge", "Firefox"])
        self.browser_mode_combo.setToolTip("Auto usa o fluxo atual. Chrome/Edge/Firefox abrem no navegador nativo escolhido.")
        info_layout.addRow("Navegador:", self.browser_mode_combo)

        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("anime, email, amazon, teste")
        info_layout.addRow("Tags:", self.tags_input)

        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Observações deste perfil...")
        self.notes_input.setMaximumHeight(90)
        info_layout.addRow("Notas:", self.notes_input)
        
        info_group.setLayout(info_layout)
        config_layout.addWidget(info_group)

        # Grupo: Endereço do perfil
        address_group = QGroupBox("📍 Endereço do Perfil")
        address_layout = QVBoxLayout()
        address_hint = QLabel(
            "Salve um endereço neste perfil e use o botão para preencher CEP, rua, número, bairro, cidade e estado na página aberta."
        )
        address_hint.setWordWrap(True)
        address_hint.setStyleSheet(browser_label_qss("hint"))
        address_layout.addWidget(address_hint)

        address_form = QFormLayout()
        self.address_cep_input = QLineEdit()
        self.address_cep_input.setPlaceholderText("00000-000")
        address_form.addRow("CEP:", self.address_cep_input)

        self.address_street_input = QLineEdit()
        self.address_street_input.setPlaceholderText("Rua / Avenida")
        address_form.addRow("Rua:", self.address_street_input)

        address_number_row = QHBoxLayout()
        self.address_number_input = QLineEdit()
        self.address_number_input.setPlaceholderText("Número")
        address_number_row.addWidget(self.address_number_input)
        self.address_complement_input = QLineEdit()
        self.address_complement_input.setPlaceholderText("Complemento")
        address_number_row.addWidget(self.address_complement_input)
        address_form.addRow("Número:", address_number_row)

        self.address_bairro_input = QLineEdit()
        self.address_bairro_input.setPlaceholderText("Bairro")
        address_form.addRow("Bairro:", self.address_bairro_input)

        city_state_row = QHBoxLayout()
        self.address_city_input = QLineEdit()
        self.address_city_input.setPlaceholderText("Cidade")
        city_state_row.addWidget(self.address_city_input, 2)
        self.address_state_input = QLineEdit()
        self.address_state_input.setPlaceholderText("Estado")
        city_state_row.addWidget(self.address_state_input, 2)
        self.address_uf_input = QLineEdit()
        self.address_uf_input.setPlaceholderText("UF")
        self.address_uf_input.setMaximumWidth(70)
        city_state_row.addWidget(self.address_uf_input)
        address_form.addRow("Cidade/UF:", city_state_row)
        address_layout.addLayout(address_form)

        address_btns = QHBoxLayout()
        generate_address_btn = QPushButton("🎲 Gerar endereço")
        generate_address_btn.setToolTip("Gera pelo módulo CEP. Se a API falhar, usa o banco de reserva local.")
        generate_address_btn.clicked.connect(self.generate_profile_address)
        address_btns.addWidget(generate_address_btn)

        fill_address_btn = QPushButton("⚡ Preencher página aberta")
        fill_address_btn.setToolTip("Preenche campos de endereço na aba aberta do navegador deste perfil.")
        fill_address_btn.clicked.connect(self.fill_address_on_current_page)
        address_btns.addWidget(fill_address_btn)

        copy_address_btn = QPushButton("📋 Copiar")
        copy_address_btn.clicked.connect(self.copy_profile_address)
        address_btns.addWidget(copy_address_btn)
        address_layout.addLayout(address_btns)

        self.address_status_label = QLabel("Endereço ainda não salvo neste perfil.")
        self.address_status_label.setWordWrap(True)
        self.address_status_label.setStyleSheet(browser_label_qss("muted"))
        address_layout.addWidget(self.address_status_label)
        address_group.setLayout(address_layout)
        config_layout.addWidget(address_group)
        
        # Grupo: Configuração de Proxy
        proxy_group = QGroupBox("🌐 Proxy")
        proxy_layout = QVBoxLayout()
        
        proxy_info = QLabel("Opcional. Use quando quiser que este perfil navegue com outro IP. Formato: IP:Porta ou IP:Porta:Usuário:Senha")
        proxy_info.setStyleSheet(browser_label_qss("muted"))
        proxy_info.setWordWrap(True)
        proxy_layout.addWidget(proxy_info)
        
        self.proxy_input = QLineEdit()
        self.proxy_input.setPlaceholderText("Ex: 192.168.1.1:8080 ou 192.168.1.1:8080:user:pass")
        proxy_layout.addWidget(self.proxy_input)
        
        self.proxy_status = QLabel("")
        self.proxy_status.setStyleSheet(browser_label_qss("tiny"))
        proxy_layout.addWidget(self.proxy_status)
        
        validate_proxy_btn = QPushButton("✓ Validar Proxy")
        validate_proxy_btn.clicked.connect(self.validate_proxy)
        proxy_layout.addWidget(validate_proxy_btn)
        
        proxy_group.setLayout(proxy_layout)
        config_layout.addWidget(proxy_group)
        
        # Grupo: Fingerprint
        fp_group = QGroupBox("🎭 Fingerprint")
        fp_layout = QVBoxLayout()

        fp_info = QLabel("Controla a aparência técnica do navegador: user-agent, resolução, timezone e WebGL.")
        fp_info.setStyleSheet(browser_label_qss("muted"))
        fp_info.setWordWrap(True)
        fp_layout.addWidget(fp_info)

        fp_mode_row = QHBoxLayout()
        fp_mode_row.addWidget(QLabel("Nível:"))
        self.fingerprint_level_combo = QComboBox()
        self.fingerprint_level_combo.addItems(["Normal", "Leve", "Forte", "Streaming"])
        self.fingerprint_level_combo.setToolTip(
            "Normal mexe menos. Leve é equilibrado. Forte aplica scripts extras. Streaming reduz ajustes para sites de vídeo."
        )
        fp_mode_row.addWidget(self.fingerprint_level_combo, 1)
        fp_layout.addLayout(fp_mode_row)
        
        # Resumo do fingerprint
        self.fp_summary = QTextEdit()
        self.fp_summary.setReadOnly(True)
        self.fp_summary.setMaximumHeight(120)
        self.fp_summary.setPlaceholderText("Selecione um perfil para ver o fingerprint")
        fp_layout.addWidget(self.fp_summary)
        
        fp_btn_layout = QHBoxLayout()
        
        randomize_btn = QPushButton("🎲 Randomizar")
        randomize_btn.clicked.connect(self.randomize_fingerprint)
        fp_btn_layout.addWidget(randomize_btn)
        
        customize_btn = QPushButton("⚙️ Customizar")
        customize_btn.clicked.connect(self.customize_fingerprint)
        fp_btn_layout.addWidget(customize_btn)
        
        fp_layout.addLayout(fp_btn_layout)
        fp_group.setLayout(fp_layout)
        config_layout.addWidget(fp_group)
        
        # Grupo: Persistência de Dados
        persist_group = QGroupBox("💾 Dados do Navegador")
        persist_layout = QVBoxLayout()
        
        self.persist_checkbox = QCheckBox("Manter histórico, cookies e dados entre sessões")
        self.persist_checkbox.setChecked(True)
        self.persist_checkbox.setStyleSheet(browser_checkbox_qss())
        self.persist_checkbox.setToolTip(
            "Se marcado, o navegador mantém histórico, cookies e logins salvos.\n"
            "Se desmarcado, os dados são limpos a cada nova sessão (modo privado)."
        )
        persist_layout.addWidget(self.persist_checkbox)

        self.compatibility_checkbox = QCheckBox("Modo compatibilidade para streaming")
        self.compatibility_checkbox.setToolTip(
            "Use para Paramount/Crunchyroll/HBO/Prime quando aparecer 403, verificação ou tela bloqueada. "
            "Abre com menos extensões e menos ajustes agressivos."
        )
        self.compatibility_checkbox.setStyleSheet(browser_checkbox_qss())
        persist_layout.addWidget(self.compatibility_checkbox)

        self.save_logins_checkbox = QCheckBox("Salvar logins no Chrome")
        self.save_logins_checkbox.setChecked(True)
        self.save_logins_checkbox.setToolTip(
            "Ativa o gerenciador de senhas do Chrome dentro deste perfil. "
            "Quando o Chrome salvar, o login fica preso neste perfil."
        )
        self.save_logins_checkbox.setStyleSheet(browser_checkbox_qss())
        persist_layout.addWidget(self.save_logins_checkbox)
        
        persist_info = QLabel("Desmarque para limpar dados automaticamente ao fechar")
        persist_info.setStyleSheet(browser_label_qss("faded_small"))
        persist_info.setWordWrap(True)
        persist_layout.addWidget(persist_info)
        
        clear_data_btn = QPushButton("🗑️ Limpar Dados Agora")
        clear_data_btn.setStyleSheet(browser_danger_button_qss())
        clear_data_btn.clicked.connect(self.clear_profile_data)
        persist_layout.addWidget(clear_data_btn)
        
        persist_group.setLayout(persist_layout)
        config_layout.addWidget(persist_group)

        storage_group = QGroupBox("📦 Espaço do Perfil")
        storage_layout = QVBoxLayout()
        storage_hint = QLabel(
            "Veja quanto o perfil ocupa. A limpeza segura remove cache do Chrome, mas preserva cookies, logins, favoritos e dados dos sites."
        )
        storage_hint.setWordWrap(True)
        storage_hint.setStyleSheet(browser_label_qss("muted"))
        storage_layout.addWidget(storage_hint)

        self.profile_storage_label = QLabel("Selecione um perfil e clique em Atualizar tamanho.")
        self.profile_storage_label.setWordWrap(True)
        self.profile_storage_label.setStyleSheet(browser_panel_qss())
        storage_layout.addWidget(self.profile_storage_label)

        storage_btns = QHBoxLayout()
        refresh_storage_btn = QPushButton("Atualizar tamanho")
        refresh_storage_btn.clicked.connect(self.refresh_profile_storage)
        storage_btns.addWidget(refresh_storage_btn)

        clean_cache_btn = QPushButton("Limpar cache seguro")
        clean_cache_btn.setToolTip("Remove apenas caches recriáveis do navegador. Não apaga cookies, logins nem favoritos.")
        clean_cache_btn.clicked.connect(self.clear_profile_cache_safe)
        storage_btns.addWidget(clean_cache_btn)
        storage_layout.addLayout(storage_btns)

        storage_group.setLayout(storage_layout)
        config_layout.addWidget(storage_group)

        format_backup_group = QGroupBox("🧳 Backup para Formatação")
        format_backup_layout = QVBoxLayout()
        format_backup_hint = QLabel(
            "Prepara um ZIP com perfis, cookies, favoritos, extensões e configurações do Navegador Seguro. "
            "Use antes de formatar o PC ou trocar de Windows."
        )
        format_backup_hint.setWordWrap(True)
        format_backup_hint.setStyleSheet(browser_label_qss("muted"))
        format_backup_layout.addWidget(format_backup_hint)

        self.format_backup_status_label = QLabel(
            "Dica: feche os navegadores antes do backup para copiar sessões com mais segurança."
        )
        self.format_backup_status_label.setWordWrap(True)
        self.format_backup_status_label.setStyleSheet(browser_panel_qss())
        format_backup_layout.addWidget(self.format_backup_status_label)

        self.format_backup_btn = QPushButton("🧳 Preparar backup para formatação")
        self.format_backup_btn.setToolTip("Cria um backup completo dos perfis e um relatório do que tem cookies/logins.")
        self.format_backup_btn.clicked.connect(self.prepare_format_backup)
        format_backup_layout.addWidget(self.format_backup_btn)

        format_backup_group.setLayout(format_backup_layout)
        config_layout.addWidget(format_backup_group)
        
        # Grupo: Auto-Login
        login_group = QGroupBox("🔐 Auto-Login")
        login_layout = QVBoxLayout()

        login_info = QLabel("Opcional. Salve credenciais por site para tentar preencher login automaticamente.")
        login_info.setStyleSheet(browser_label_qss("muted"))
        login_info.setWordWrap(True)
        login_layout.addWidget(login_info)
        
        self.login_count_label = QLabel("Nenhum site configurado")
        self.login_count_label.setStyleSheet(browser_label_qss("muted_plain"))
        login_layout.addWidget(self.login_count_label)
        
        config_login_btn = QPushButton("⚙️ Configurar Auto-Login")
        config_login_btn.clicked.connect(self.configure_auto_login)
        login_layout.addWidget(config_login_btn)
        
        login_group.setLayout(login_layout)
        config_layout.addWidget(login_group)

        accounts_group = QGroupBox("👤 Gerenciador de Contas")
        accounts_layout = QVBoxLayout()
        self.accounts_table = QTableWidget()
        self.accounts_table.setColumnCount(5)
        self.accounts_table.setHorizontalHeaderLabels(["Nome", "Email", "Site", "Status", "Perfil"])
        self.accounts_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.accounts_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.accounts_table.setMaximumHeight(170)
        accounts_layout.addWidget(self.accounts_table)
        account_btns = QHBoxLayout()
        add_account_btn = QPushButton("Adicionar conta")
        add_account_btn.clicked.connect(self.add_account)
        account_btns.addWidget(add_account_btn)
        edit_account_btn = QPushButton("Editar")
        edit_account_btn.clicked.connect(self.edit_account)
        account_btns.addWidget(edit_account_btn)
        open_account_btn = QPushButton("Abrir perfil da conta")
        open_account_btn.clicked.connect(self.open_account_profile)
        account_btns.addWidget(open_account_btn)
        remove_account_btn = QPushButton("Remover")
        remove_account_btn.clicked.connect(self.delete_account)
        account_btns.addWidget(remove_account_btn)
        accounts_layout.addLayout(account_btns)
        accounts_group.setLayout(accounts_layout)
        config_layout.addWidget(accounts_group)

        identity_group = QGroupBox("🧭 Identificação do Perfil")
        identity_layout = QVBoxLayout()
        identity_hint = QLabel(
            "Mostra o que existe salvo neste perfil: sites com cookies e logins gravados pelo navegador. "
            "Não descriptografa senha, só identifica domínio e usuário visível."
        )
        identity_hint.setWordWrap(True)
        identity_hint.setStyleSheet(browser_label_qss("muted"))
        identity_layout.addWidget(identity_hint)
        self.identity_summary_label = QLabel("Selecione um perfil e clique em Analisar.")
        self.identity_summary_label.setWordWrap(True)
        self.identity_summary_label.setStyleSheet(browser_panel_qss())
        identity_layout.addWidget(self.identity_summary_label)
        self.identity_table = QTableWidget()
        self.identity_table.setColumnCount(4)
        self.identity_table.setHorizontalHeaderLabels(["Site", "Tipo", "Usuário/Detalhe", "Evidência"])
        self.identity_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.identity_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.identity_table.setMaximumHeight(190)
        identity_layout.addWidget(self.identity_table)
        identity_btns = QHBoxLayout()
        scan_identity_btn = QPushButton("🔎 Analisar perfil")
        scan_identity_btn.setToolTip("Lê cookies e Login Data deste perfil localmente.")
        scan_identity_btn.clicked.connect(self.scan_selected_profile_identity)
        identity_btns.addWidget(scan_identity_btn)
        copy_identity_btn = QPushButton("Copiar resumo")
        copy_identity_btn.clicked.connect(self.copy_profile_identity_summary)
        identity_btns.addWidget(copy_identity_btn)
        identity_layout.addLayout(identity_btns)
        identity_group.setLayout(identity_layout)
        config_layout.addWidget(identity_group)

        tasks_group = QGroupBox("✅ Gerador de Tarefas")
        tasks_layout = QVBoxLayout()
        self.tasks_table = QTableWidget()
        self.tasks_table.setColumnCount(4)
        self.tasks_table.setHorizontalHeaderLabels(["OK", "Tarefa", "Perfil", "Conta"])
        self.tasks_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tasks_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.tasks_table.setMaximumHeight(170)
        tasks_layout.addWidget(self.tasks_table)
        task_btns = QHBoxLayout()
        add_task_btn = QPushButton("Nova tarefa")
        add_task_btn.clicked.connect(self.add_task)
        task_btns.addWidget(add_task_btn)
        done_task_btn = QPushButton("Alternar OK")
        done_task_btn.clicked.connect(self.toggle_task_done)
        task_btns.addWidget(done_task_btn)
        remove_task_btn = QPushButton("Remover")
        remove_task_btn.clicked.connect(self.delete_task)
        task_btns.addWidget(remove_task_btn)
        tasks_layout.addLayout(task_btns)
        tasks_group.setLayout(tasks_layout)
        config_layout.addWidget(tasks_group)

        vault_group = QGroupBox("🔐 Cofre Seguro")
        vault_layout = QVBoxLayout()
        vault_hint = QLabel("Guarde senhas, 2FA e backup codes com senha mestra. Desbloqueie para ver ou editar.")
        vault_hint.setWordWrap(True)
        vault_hint.setStyleSheet(browser_label_qss("muted"))
        vault_layout.addWidget(vault_hint)
        self.vault_status_label = QLabel("Cofre bloqueado")
        self.vault_status_label.setStyleSheet(browser_vault_status_qss(False))
        vault_layout.addWidget(self.vault_status_label)
        self.vault_table = QTableWidget()
        self.vault_table.setColumnCount(4)
        self.vault_table.setHorizontalHeaderLabels(["Site", "Usuário", "Categoria", "Notas/2FA"])
        self.vault_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.vault_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.vault_table.setMaximumHeight(150)
        vault_layout.addWidget(self.vault_table)
        vault_btns = QHBoxLayout()
        unlock_vault_btn = QPushButton("Desbloquear/Criar senha")
        unlock_vault_btn.clicked.connect(self.unlock_vault)
        vault_btns.addWidget(unlock_vault_btn)
        add_vault_btn = QPushButton("Adicionar segredo")
        add_vault_btn.clicked.connect(self.add_vault_secret)
        vault_btns.addWidget(add_vault_btn)
        remove_vault_btn = QPushButton("Remover")
        remove_vault_btn.clicked.connect(self.remove_vault_secret)
        vault_btns.addWidget(remove_vault_btn)
        vault_layout.addLayout(vault_btns)
        vault_group.setLayout(vault_layout)
        config_layout.addWidget(vault_group)

        defaults_group = QGroupBox("⭐ Favoritos e Extensões Padrão")
        defaults_layout = QVBoxLayout()
        self.defaults_summary_label = QLabel("")
        self.defaults_summary_label.setWordWrap(True)
        self.defaults_summary_label.setStyleSheet(browser_label_qss("soft"))
        defaults_layout.addWidget(self.defaults_summary_label)

        self.favorites_table = QTableWidget()
        self.favorites_table.setColumnCount(3)
        self.favorites_table.setHorizontalHeaderLabels(["Nome", "Pasta", "URL"])
        self.favorites_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.favorites_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.favorites_table.setMaximumHeight(150)
        defaults_layout.addWidget(self.favorites_table)

        fav_manage_row = QHBoxLayout()
        add_fav_btn = QPushButton("Adicionar favorito")
        add_fav_btn.clicked.connect(self.add_default_favorite)
        fav_manage_row.addWidget(add_fav_btn)
        edit_fav_btn = QPushButton("Editar")
        edit_fav_btn.clicked.connect(self.edit_default_favorite)
        fav_manage_row.addWidget(edit_fav_btn)
        test_fav_btn = QPushButton("Testar link")
        test_fav_btn.clicked.connect(self.test_default_favorite)
        fav_manage_row.addWidget(test_fav_btn)
        remove_fav_btn = QPushButton("Remover")
        remove_fav_btn.clicked.connect(self.remove_default_favorite)
        fav_manage_row.addWidget(remove_fav_btn)
        defaults_layout.addLayout(fav_manage_row)

        apply_favorites_btn = QPushButton("⭐ Fixar favoritos em todos os perfis")
        apply_favorites_btn.setToolTip("Grava os favoritos padrão na barra de favoritos dos perfis sem apagar os existentes.")
        apply_favorites_btn.clicked.connect(self.apply_defaults_to_all_profiles)
        defaults_layout.addWidget(apply_favorites_btn)

        self.extensions_table = QTableWidget()
        self.extensions_table.setColumnCount(4)
        self.extensions_table.setHorizontalHeaderLabels(["Extensão", "Status", "Tipo", "Caminho"])
        self.extensions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.extensions_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.extensions_table.setMaximumHeight(140)
        defaults_layout.addWidget(self.extensions_table)

        ext_btns = QHBoxLayout()
        import_ext_btn = QPushButton("Importar .crx/.zip")
        import_ext_btn.clicked.connect(self.import_extension_file)
        ext_btns.addWidget(import_ext_btn)
        import_ext_folder_btn = QPushButton("Importar pasta")
        import_ext_folder_btn.clicked.connect(self.import_extension_folder)
        ext_btns.addWidget(import_ext_folder_btn)
        toggle_ext_btn = QPushButton("Ativar/Desativar")
        toggle_ext_btn.clicked.connect(self.toggle_extension)
        ext_btns.addWidget(toggle_ext_btn)
        remove_ext_btn = QPushButton("Remover extensão")
        remove_ext_btn.clicked.connect(self.remove_extension)
        ext_btns.addWidget(remove_ext_btn)
        defaults_layout.addLayout(ext_btns)

        backup_btn = QPushButton("💾 Backup inteligente do navegador")
        backup_btn.setToolTip("Salva perfis, favoritos, extensões e configurações em um ZIP.")
        backup_btn.clicked.connect(self.create_browser_backup)
        defaults_layout.addWidget(backup_btn)

        defaults_group.setLayout(defaults_layout)
        config_layout.addWidget(defaults_group)

        logs_group = QGroupBox("🧾 Logs do Navegador")
        logs_layout = QVBoxLayout()
        self.logs_view = QTextEdit()
        self.logs_view.setReadOnly(True)
        self.logs_view.setMaximumHeight(150)
        logs_layout.addWidget(self.logs_view)
        logs_btn_layout = QHBoxLayout()
        refresh_logs_btn = QPushButton("Atualizar logs")
        refresh_logs_btn.clicked.connect(self.refresh_logs)
        logs_btn_layout.addWidget(refresh_logs_btn)
        copy_logs_btn = QPushButton("Copiar erro/log")
        copy_logs_btn.clicked.connect(self.copy_logs)
        logs_btn_layout.addWidget(copy_logs_btn)
        logs_layout.addLayout(logs_btn_layout)
        logs_group.setLayout(logs_layout)
        config_layout.addWidget(logs_group)
        
        # Botão Salvar
        save_btn = QPushButton("💾 Salvar Perfil")
        save_btn.setStyleSheet(browser_primary_button_qss())
        save_btn.clicked.connect(self.save_profile)
        self.save_profile_btn = save_btn
        config_layout.addWidget(save_btn)

        section_frame = QFrame()
        section_frame.setObjectName("BrowserSectionTabs")
        section_layout = QHBoxLayout()
        section_layout.setContentsMargins(0, 0, 0, 8)
        section_layout.setSpacing(8)
        self.config_section_buttons = {}
        sections = [
            ("Resumo", "resumo"),
            ("Perfil", "perfil"),
            ("Avançado", "avancado"),
            ("Contas", "contas"),
            ("Cofre", "cofre"),
            ("Padrões", "padroes"),
            ("Logs", "logs"),
        ]
        for label, key in sections:
            btn = QPushButton(label)
            btn.setCheckable(True)
            btn.setMinimumHeight(34)
            btn.clicked.connect(lambda checked=False, k=key: self.show_config_section(k))
            self.config_section_buttons[key] = btn
            section_layout.addWidget(btn)
        section_frame.setLayout(section_layout)
        config_layout.insertWidget(0, section_frame)

        self.config_sections = {
            "resumo": [dashboard_group, guide_frame],
            "perfil": [info_group, address_group],
            "avancado": [proxy_group, fp_group, persist_group, storage_group, format_backup_group, login_group],
            "contas": [accounts_group, identity_group, tasks_group],
            "cofre": [vault_group],
            "padroes": [defaults_group],
            "logs": [logs_group],
        }
        
        config_layout.addStretch()
        
        config_widget.setLayout(config_layout)
        scroll.setWidget(config_widget)
        right_layout.addWidget(scroll)
        
        # Botão Iniciar Navegador
        self.start_btn = QPushButton("🚀 Iniciar Navegador Seguro")
        self.start_btn.setStyleSheet(browser_start_button_qss())
        self.start_btn.clicked.connect(self.start_browser)
        self.start_btn.hide()
        
        bottom_bar = QFrame()
        bottom_bar.setObjectName("BrowserBottomBar")
        bottom_bar_layout = QVBoxLayout(bottom_bar)
        bottom_bar_layout.setContentsMargins(12, 10, 12, 10)
        bottom_bar_layout.setSpacing(8)

        # URL inicial
        url_layout = QHBoxLayout()
        url_layout.setSpacing(8)
        url_label = QLabel("URL ou pesquisa:")
        url_label.setToolTip("Aceita link completo, domínio ou texto para buscar no Google.")
        url_layout.addWidget(url_label)
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Digite URL ou pesquisa. Ex: gmail.com, browserleaks, consultar cpf")
        self.url_input.returnPressed.connect(self.start_browser)
        url_layout.addWidget(self.url_input)
        self.open_url_btn = QPushButton("Abrir URL")
        self.open_url_btn.setObjectName("BrowserPrimaryButton")
        self.open_url_btn.setToolTip("Abre a URL ou pesquisa no perfil selecionado.")
        self.open_url_btn.clicked.connect(self.start_browser)
        url_layout.addWidget(self.open_url_btn)
        bottom_bar_layout.addLayout(url_layout)

        favorite_layout = QHBoxLayout()
        favorite_layout.setSpacing(8)
        favorite_layout.addWidget(QLabel("Abrir favorito:"))
        self.favorite_combo = QComboBox()
        favorite_layout.addWidget(self.favorite_combo)
        open_favorite_btn = QPushButton("Abrir favorito no perfil")
        open_favorite_btn.clicked.connect(self.open_selected_favorite)
        favorite_layout.addWidget(open_favorite_btn)
        diagnose_btn = QPushButton("🔎 Diagnosticar página")
        diagnose_btn.setToolTip("Lê a página aberta e explica bloqueios, captcha, erro de rede ou formulário incompleto.")
        diagnose_btn.clicked.connect(self.detect_current_page_issue)
        favorite_layout.addWidget(diagnose_btn)
        paramount_btn = QPushButton("Detector 403 / Paramount")
        paramount_btn.setToolTip("Aplica modo Streaming, limpa o perfil fechado e abre uma URL alternativa da Paramount.")
        paramount_btn.clicked.connect(self.open_paramount_repair)
        favorite_layout.addWidget(paramount_btn)
        bottom_bar_layout.addLayout(favorite_layout)
        right_layout.addWidget(bottom_bar)
        
        right_panel.setLayout(right_layout)
        
        # Adicionar painéis ao layout principal
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([340, 900])
        self.browser_main_splitter = splitter
        
        main_layout.addWidget(splitter)
        self.setLayout(root_layout)
        
        # Carregar perfis
        self.refresh_favorites_combo()
        self.refresh_favorites_table()
        self.refresh_accounts()
        self.refresh_tasks()
        self.refresh_vault()
        self.refresh_extensions()
        self.refresh_logs()
        self.refresh_profile_list()
        self.show_config_section("perfil")
        self._sync_responsive_state()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._sync_responsive_state()

    def _sync_responsive_state(self):
        """Mantem o Navegador Seguro usavel em janela pequena, normal e ultra-wide."""
        if not hasattr(self, "browser_main_splitter"):
            return
        width = max(0, self.width())
        if width <= 0:
            return
        narrow = width < 980
        compact = width < 1260
        if narrow:
            left_w = 270
            min_left, max_left = 240, 315
        elif compact:
            left_w = 315
            min_left, max_left = 270, 370
        else:
            left_w = min(430, max(340, int(width * 0.27)))
            min_left, max_left = 300, 470
        if hasattr(self, "browser_left_panel"):
            self.browser_left_panel.setMinimumWidth(min_left)
            self.browser_left_panel.setMaximumWidth(max_left)
        if hasattr(self, "browser_header_subtitle"):
            self.browser_header_subtitle.setVisible(not narrow)
        if hasattr(self, "browser_header_chip"):
            self.browser_header_chip.setVisible(width >= 760)
        self.browser_main_splitter.setSizes([left_w, max(460, width - left_w - 24)])
    
    def refresh_profile_list(self):
        """Atualiza a lista de perfis."""
        self.profile_list.clear()
        
        query = ""
        if hasattr(self, "profile_search"):
            query = self.profile_search.text().strip().lower()

        include_archived = bool(getattr(self, "show_archived_checkbox", None) and self.show_archived_checkbox.isChecked())
        profiles = self.browser_manager.list_profiles(include_archived=include_archived)
        all_profiles = self.browser_manager.list_profiles(include_archived=True)
        active_count = len(self.browser_manager.get_active_browsers())
        last_used_profiles = sorted(
            [p for p in all_profiles if p.last_used and not getattr(p, "archived", False)],
            key=lambda p: p.last_used or "",
            reverse=True
        )
        if hasattr(self, "total_profiles_label"):
            archived_count = len([p for p in all_profiles if getattr(p, "archived", False)])
            self.total_profiles_label.setText(f"Perfis: {len(all_profiles) - archived_count} | Arquivados: {archived_count}")
            self.open_profiles_label.setText(f"Abertos: {active_count}")
            last_name = last_used_profiles[0].name if last_used_profiles else "-"
            self.last_used_label.setText(f"Último uso: {last_name}")
            if hasattr(self, "browser_header_chip"):
                self.browser_header_chip.setText(f"{len(all_profiles) - archived_count} perfis | {active_count} aberto(s)")

        for profile in profiles:
            tags_text = ", ".join(getattr(profile, "tags", []) or [])
            haystack = f"{profile.name} {profile.id} {tags_text} {getattr(profile, 'notes', '')}".lower()
            if query and query not in haystack:
                continue
            item = QListWidgetItem()

            status = self.browser_manager.get_profile_status(profile.id)
            icon = "🟢" if status.get("active") else "⚪"
            archived = getattr(profile, "archived", False)
            archive_badge = " 📦" if archived else ""
            tags_suffix = f"  [{tags_text}]" if tags_text else ""
            browser_label = (getattr(profile, "browser_mode", "auto") or "auto").title()
            fp_label = getattr(profile, "fingerprint_level", "Leve") or "Leve"
            address = getattr(profile, "address_data", {}) or {}
            address_badge = " • endereço OK" if address.get("cep") and address.get("cidade") else ""
            identity = getattr(profile, "account_identity", {}) or {}
            identity_badge = ""
            if identity.get("ok"):
                identity_badge = (
                    f" • {identity.get('login_count', 0)} login(s)"
                    f" • {identity.get('cookie_domains_count', 0)} site(s)"
                )
            last_issue = self.browser_manager.get_profile_last_issue(profile.id)
            issue_badge = f" • aviso: {last_issue.get('label')}" if last_issue else ""
            tags_suffix = f" [{tags_text}]" if tags_text else ""
            item.setText(
                f"{icon} {profile.name}{archive_badge}{tags_suffix}\n"
                f"   {status['label']} • {browser_label} • FP {fp_label}{address_badge}{identity_badge}{issue_badge}"
            )
            item.setData(Qt.UserRole + 1, item.text())
            item.setText("")
            item.setData(Qt.UserRole, profile.id)
            
            # Tooltip com informações
            tooltip = f"ID: {profile.id}\n"
            tooltip += f"Status: {status['label']} | {status['proxy_label']} | {status['favorites_label']}\n"
            tooltip += f"Navegador: {browser_label} | Fingerprint: {fp_label}\n"
            tooltip += f"Arquivado: {'Sim' if archived else 'Não'}\n"
            if identity.get("ok"):
                sites = ", ".join(identity.get("likely_sites", [])[:8])
                tooltip += f"Identificação: {identity.get('login_count', 0)} login(s), {identity.get('cookie_domains_count', 0)} site(s)\n"
                tooltip += f"Sites: {sites or '-'}\n"
            if last_issue:
                tooltip += f"Último aviso: {last_issue.get('message') or last_issue.get('label')}\n"
            tooltip += f"Tags: {tags_text or 'Nenhuma'}\n"
            tooltip += f"Proxy: {profile.proxy or 'Nenhum'}\n"
            tooltip += f"Criado: {profile.created_at[:10] if profile.created_at else 'N/A'}"
            item.setToolTip(tooltip)
            
            self.profile_list.addItem(item)
            row = self._create_profile_row_widget(
                profile,
                status,
                browser_label,
                fp_label,
                address_badge + identity_badge + issue_badge,
                tags_suffix,
                bool(last_issue),
            )
            item.setSizeHint(QSize(0, 80))
            self.profile_list.setItemWidget(item, row)

        fav_count = self.browser_manager.get_default_favorite_count()
        ext_count = self.browser_manager.get_default_extension_count()
        self._update_defaults_summary(fav_count, ext_count)
        self._set_status(
            f"{self.profile_list.count()} perfil(is) | {fav_count} favorito(s) fixados | {ext_count} extensão(ões) padrão"
        )

    def _create_profile_row_widget(self, profile, status: dict, browser_label: str, fp_label: str, address_badge: str, tags_suffix: str, has_issue: bool = False):
        row = QWidget()
        row.setObjectName("BrowserProfileRow")
        row.setFixedHeight(74)
        row.setStyleSheet(browser_profile_row_qss())
        layout = QHBoxLayout(row)
        layout.setContentsMargins(12, 8, 8, 8)
        layout.setSpacing(10)

        active = bool(status.get("active"))
        launching = bool(status.get("launching"))
        archived = getattr(profile, "archived", False)
        dot_color = "#22c55e" if active else "#38bdf8" if launching else "#f59e0b" if archived else "#e5e7eb"
        archived_text = " [arquivado]" if archived else ""
        full_title = f"{profile.name}{archived_text}"
        full_status = f"{status['label']} - {browser_label} - FP {fp_label}"
        full_badges = " ".join(part.strip(" •") for part in [tags_suffix.strip(), address_badge.strip()] if part.strip())
        compact_status = full_status
        if has_issue:
            compact_status += " - aviso"
        elif "endereco OK" in address_badge or "endereço OK" in address_badge:
            compact_status += " - endereco OK"

        dot = QLabel("")
        dot.setFixedSize(9, 9)
        dot.setStyleSheet(f"background:{dot_color};border-radius:4px;border:none;")
        layout.addWidget(dot, 0, Qt.AlignVCenter)

        title_text = self._short_display(full_title, 30)
        subtitle_text = self._short_display(compact_status, 42)
        subtitle_color = "#fbbf24" if has_issue else "#94a3b8"
        summary = QLabel(
            "<div style='font-size:12px;font-weight:850;color:#f8fafc;line-height:18px;'>"
            f"{html_escape(title_text)}</div>"
            f"<div style='font-size:10px;color:{subtitle_color};line-height:15px;'>"
            f"{html_escape(subtitle_text)}</div>"
        )
        summary.setToolTip(
            f"{full_title}{tags_suffix}\n{full_status}\n{full_badges}" if full_badges else f"{full_title}{tags_suffix}\n{full_status}"
        )
        summary.setTextFormat(Qt.RichText)
        summary.setWordWrap(False)
        summary.setMinimumWidth(0)
        summary.setFixedHeight(42)
        summary.setStyleSheet("background:transparent;border:none;padding:0;margin:0;")
        summary.mousePressEvent = lambda event, pid=profile.id: self._select_profile_by_id(pid)

        row.mousePressEvent = lambda event, pid=profile.id: self._select_profile_by_id(pid)
        layout.addWidget(summary, 1)

        start_btn = QPushButton("▶")
        start_btn.setToolTip("Iniciar navegador deste perfil")
        start_btn.setFixedSize(40, 30)
        start_btn.setEnabled(not active and not launching)
        if launching:
            start_btn.setToolTip("Este perfil ja esta abrindo")
        elif active:
            start_btn.setToolTip("Este perfil ja esta aberto")
        start_btn.setStyleSheet(browser_row_start_qss())
        start_btn.clicked.connect(lambda checked=False, pid=profile.id: self.start_profile_browser(pid))
        layout.addWidget(start_btn)

        close_btn = QPushButton("X")
        close_btn.setToolTip("Fechar navegador deste perfil")
        close_btn.setFixedSize(38, 30)
        close_btn.setEnabled(active)
        close_btn.setStyleSheet(browser_row_close_qss())
        close_btn.clicked.connect(lambda checked=False, pid=profile.id: self.close_profile_browser(pid))
        layout.addWidget(close_btn)
        return row

    def show_config_section(self, section: str):
        if not hasattr(self, "config_sections"):
            return
        for groups in self.config_sections.values():
            for group in groups:
                group.setVisible(False)
        for group in self.config_sections.get(section, []):
            group.setVisible(True)
        for key, btn in getattr(self, "config_section_buttons", {}).items():
            btn.setChecked(key == section)
            btn.setStyleSheet(browser_section_tab_qss(key == section))
        if hasattr(self, "save_profile_btn"):
            self.save_profile_btn.setVisible(section in ("perfil", "avancado"))

    def _update_defaults_summary(self, fav_count: int = None, ext_count: int = None):
        if fav_count is None:
            fav_count = self.browser_manager.get_default_favorite_count()
        if ext_count is None:
            ext_count = self.browser_manager.get_default_extension_count()
        if hasattr(self, "defaults_summary_label"):
            self.defaults_summary_label.setText(
                f"{fav_count} favorito(s) padrão ficam na barra de favoritos. "
                f"{ext_count} extensão(ões) padrão carregam quando o Chrome abre. "
                "Use o botão abaixo para atualizar perfis antigos também."
            )

    def refresh_extensions(self):
        if not hasattr(self, "extensions_table") or not self.browser_manager.defaults_manager:
            return
        extensions = self.browser_manager.defaults_manager.extensions.get_extensions()
        self.extensions_table.setRowCount(0)
        for ext in extensions:
            row = self.extensions_table.rowCount()
            self.extensions_table.insertRow(row)
            values = [
                ext.get("name", ""),
                "Ativa" if ext.get("enabled", True) else "Desativada",
                ext.get("source_type", ""),
                ext.get("local_path") or ext.get("source", ""),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(str(value))
                item.setData(Qt.UserRole, ext.get("id"))
                self.extensions_table.setItem(row, col, item)

    def _selected_extension_id(self):
        if not hasattr(self, "extensions_table"):
            return None
        row = self.extensions_table.currentRow()
        if row < 0:
            return None
        item = self.extensions_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def _add_extension_from_path(self, path: str, source_type: str):
        if not self.browser_manager.defaults_manager:
            QMessageBox.warning(self, "Extensões", "Gerenciador de padrões indisponível.")
            return
        name_default = Path(path).stem or "Extensão"
        name, ok = QInputDialog.getText(self, "Nome da extensão", "Nome:", text=name_default)
        if not ok or not name.strip():
            return
        ok_add, message = self.browser_manager.defaults_manager.extensions.add_extension(
            name.strip(),
            path,
            source_type=source_type,
            enabled=True,
            description="Importada pelo Navegador Seguro",
        )
        self.browser_manager.log_event("extension_imported" if ok_add else "extension_error", None, message, "info" if ok_add else "error")
        self.refresh_extensions()
        self.refresh_profile_list()
        self.refresh_logs()
        QMessageBox.information(self, "Extensões", message)

    def import_extension_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Importar extensão",
            "",
            "Extensões Chrome (*.crx *.zip);;Todos os arquivos (*.*)",
        )
        if path:
            source_type = "crx" if path.lower().endswith(".crx") else "file"
            self._add_extension_from_path(path, source_type)

    def import_extension_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Importar pasta de extensão")
        if path:
            self._add_extension_from_path(path, "file")

    def toggle_extension(self):
        ext_id = self._selected_extension_id()
        if not ext_id:
            QMessageBox.warning(self, "Extensões", "Selecione uma extensão primeiro.")
            return
        self.browser_manager.defaults_manager.extensions.toggle_extension(ext_id)
        self.browser_manager.log_event("extension_toggled", None, ext_id)
        self.refresh_extensions()
        self.refresh_profile_list()
        self.refresh_logs()

    def remove_extension(self):
        ext_id = self._selected_extension_id()
        if not ext_id:
            QMessageBox.warning(self, "Extensões", "Selecione uma extensão primeiro.")
            return
        self.browser_manager.defaults_manager.extensions.remove_extension(ext_id)
        self.browser_manager.log_event("extension_removed", None, ext_id)
        self.refresh_extensions()
        self.refresh_profile_list()
        self.refresh_logs()

    def _set_status(self, message: str, color: str = "#94a3b8"):
        if hasattr(self, "status_label"):
            self.status_label.setText(message)
            self.status_label.setStyleSheet(browser_status_qss(color))

    def _select_profile_by_id(self, profile_id: str, clear_selection: bool = True):
        for i in range(self.profile_list.count()):
            item = self.profile_list.item(i)
            if item.data(Qt.UserRole) == profile_id:
                if clear_selection:
                    self.profile_list.clearSelection()
                item.setSelected(True)
                self.profile_list.setCurrentItem(item)
                self.on_profile_selected(item)
                return True
        return False

    def start_profile_browser(self, profile_id: str):
        if self._select_profile_by_id(profile_id):
            self.start_browser()

    def close_profile_browser(self, profile_id: str):
        self._select_profile_by_id(profile_id)
        if self.browser_manager.close_browser(profile_id):
            self._set_status("Navegador fechado", "#10b981")
        else:
            self._set_status("Este perfil já estava fechado", "#94a3b8")
        self.refresh_profile_list()
        self.refresh_logs()

    def archive_selected_profiles(self):
        profile_ids = self.selected_profile_ids()
        if not profile_ids:
            QMessageBox.warning(self, "Arquivar", "Selecione um ou mais perfis primeiro.")
            return
        archived = 0
        for profile_id in profile_ids:
            if self.browser_manager.archive_profile(profile_id, True):
                archived += 1
        self.selected_profile_id = None
        self.clear_form()
        self.refresh_profile_list()
        self.refresh_logs()
        self._set_status(f"{archived} perfil(is) arquivado(s). Dados continuam salvos.", "#f59e0b")

    def restore_selected_profiles(self):
        profile_ids = self.selected_profile_ids()
        if not profile_ids:
            QMessageBox.warning(self, "Arquivados", "Marque 'Mostrar arquivados' e selecione um perfil.")
            return
        restored = 0
        for profile_id in profile_ids:
            if self.browser_manager.archive_profile(profile_id, False):
                restored += 1
        if hasattr(self, "show_archived_checkbox"):
            self.show_archived_checkbox.setChecked(True)
        self.refresh_profile_list()
        self.refresh_logs()
        self._set_status(f"{restored} perfil(is) restaurado(s).", "#10b981")

    def selected_profile_ids(self):
        ids = []
        for item in self.profile_list.selectedItems():
            profile_id = item.data(Qt.UserRole)
            if profile_id and profile_id not in ids:
                ids.append(profile_id)
        if not ids and self.selected_profile_id:
            ids.append(self.selected_profile_id)
        return ids

    def select_all_profiles(self):
        for i in range(self.profile_list.count()):
            self.profile_list.item(i).setSelected(True)
        self._set_status(f"{self.profile_list.count()} perfil(is) selecionado(s)", "#7dd3fc")

    def refresh_favorites_combo(self):
        if not hasattr(self, "favorite_combo"):
            return
        current_url = self.favorite_combo.currentData()
        self.favorite_combo.clear()
        for fav in self.browser_manager.get_default_favorites():
            name = fav.get("name", "Favorito")
            folder = fav.get("folder", "Fixados")
            self.favorite_combo.addItem(f"{name} ({folder})", fav.get("url", ""))
        if current_url:
            index = self.favorite_combo.findData(current_url)
            if index >= 0:
                self.favorite_combo.setCurrentIndex(index)

    def refresh_favorites_table(self):
        if not hasattr(self, "favorites_table"):
            return
        favorites = self.browser_manager.get_default_favorites()
        self.favorites_table.setRowCount(0)
        for row, fav in enumerate(favorites):
            self.favorites_table.insertRow(row)
            self.favorites_table.setItem(row, 0, QTableWidgetItem(fav.get("name", "Favorito")))
            self.favorites_table.setItem(row, 1, QTableWidgetItem(fav.get("folder", "Fixados")))
            self.favorites_table.setItem(row, 2, QTableWidgetItem(fav.get("url", "")))
            self.favorites_table.item(row, 0).setData(Qt.UserRole, fav.get("id"))

    def _selected_default_favorite(self):
        if not hasattr(self, "favorites_table"):
            return None
        row = self.favorites_table.currentRow()
        if row < 0:
            return None
        item = self.favorites_table.item(row, 0)
        fav_id = item.data(Qt.UserRole) if item else None
        for fav in self.browser_manager.get_default_favorites():
            if fav.get("id") == fav_id:
                return fav
        return None

    def add_default_favorite(self):
        if not self.browser_manager.defaults_manager:
            QMessageBox.warning(self, "Favoritos", "Gerenciador de favoritos indisponível.")
            return
        name, ok = QInputDialog.getText(self, "Adicionar favorito", "Nome:")
        if not ok or not name.strip():
            return
        url, ok = QInputDialog.getText(self, "Adicionar favorito", "URL:")
        if not ok or not url.strip():
            return
        folder, ok = QInputDialog.getText(self, "Adicionar favorito", "Pasta:", text="Fixados")
        if not ok:
            return
        self.browser_manager.defaults_manager.favorites.add_favorite(name.strip(), url.strip(), folder.strip() or "Fixados")
        self.refresh_favorites_combo()
        self.refresh_favorites_table()
        self.refresh_profile_list()

    def edit_default_favorite(self):
        fav = self._selected_default_favorite()
        if not fav:
            QMessageBox.warning(self, "Favoritos", "Selecione um favorito primeiro.")
            return
        name, ok = QInputDialog.getText(self, "Editar favorito", "Nome:", text=fav.get("name", ""))
        if not ok:
            return
        url, ok = QInputDialog.getText(self, "Editar favorito", "URL:", text=fav.get("url", ""))
        if not ok:
            return
        folder, ok = QInputDialog.getText(self, "Editar favorito", "Pasta:", text=fav.get("folder", "Fixados"))
        if not ok:
            return
        self.browser_manager.defaults_manager.favorites.update_favorite(
            fav.get("id"), name=name.strip(), url=url.strip(), folder=folder.strip() or "Fixados"
        )
        self.refresh_favorites_combo()
        self.refresh_favorites_table()
        self.refresh_profile_list()

    def remove_default_favorite(self):
        fav = self._selected_default_favorite()
        if not fav:
            QMessageBox.warning(self, "Favoritos", "Selecione um favorito primeiro.")
            return
        self.browser_manager.defaults_manager.favorites.remove_favorite(fav.get("id"))
        self.refresh_favorites_combo()
        self.refresh_favorites_table()
        self.refresh_profile_list()

    def test_default_favorite(self):
        fav = self._selected_default_favorite()
        if not fav:
            QMessageBox.warning(self, "Favoritos", "Selecione um favorito primeiro.")
            return
        self.url_input.setText(fav.get("url", ""))
        self.start_browser()

    def refresh_logs(self):
        if not hasattr(self, "logs_view"):
            return
        lines = []
        for log in self.browser_manager.get_recent_logs(60):
            when = (log.get("time") or "")[11:19]
            level = log.get("level", "info")
            event = log.get("event", "")
            message = log.get("message", "")
            profile_id = log.get("profile_id") or "-"
            lines.append(f"{when} [{level}] {event} {profile_id} - {message}")
        self.logs_view.setText("\n".join(lines[-40:]))

    def _profile_name(self, profile_id: str) -> str:
        profile = self.browser_manager.get_profile(profile_id)
        return profile.name if profile else "-"

    def _account_name(self, account_id: str) -> str:
        for account in self.browser_manager.list_accounts():
            if account.get("id") == account_id:
                return account.get("name") or account.get("email") or "-"
        return "-"

    def refresh_accounts(self):
        if not hasattr(self, "accounts_table"):
            return
        accounts = self.browser_manager.list_accounts()
        self.accounts_table.setRowCount(0)
        for account in accounts:
            row = self.accounts_table.rowCount()
            self.accounts_table.insertRow(row)
            values = [
                account.get("name", ""),
                account.get("email", ""),
                account.get("site", ""),
                account.get("status", ""),
                self._profile_name(account.get("profile_id", "")),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, account.get("id"))
                self.accounts_table.setItem(row, col, item)

    def refresh_profile_identity(self, profile: BrowserProfile = None):
        if not hasattr(self, "identity_table"):
            return
        if profile is None and self.selected_profile_id:
            profile = self.browser_manager.get_profile(self.selected_profile_id)

        self.identity_table.setRowCount(0)
        if not profile:
            self.identity_summary_label.setText("Selecione um perfil para ver contas e cookies identificados.")
            return

        identity = getattr(profile, "account_identity", {}) or {}
        if not identity.get("ok"):
            self.identity_summary_label.setText(
                "Ainda não analisado. Clique em 'Analisar perfil' para ler cookies e logins locais."
            )
            return

        sites = ", ".join(identity.get("likely_sites", [])[:8]) or "-"
        scanned = (identity.get("scanned_at") or "")[:19].replace("T", " ")
        self.identity_summary_label.setText(
            f"{identity.get('login_count', 0)} login(s) salvo(s) | "
            f"{identity.get('cookies_total', 0)} cookie(s) | "
            f"{identity.get('cookie_domains_count', 0)} site(s) com cookies | "
            f"Última análise: {scanned or '-'}\n"
            f"Sites prováveis: {sites}"
        )

        for login in identity.get("logins", [])[:50]:
            self._add_identity_row(
                login.get("site") or login.get("domain", ""),
                "Login salvo",
                login.get("username", ""),
                login.get("domain") or login.get("url", ""),
            )

        for cookie in identity.get("cookie_domains", [])[:30]:
            self._add_identity_row(
                cookie.get("label") or cookie.get("domain", ""),
                "Cookies",
                cookie.get("domain", ""),
                f"{cookie.get('count', 0)} cookie(s)",
            )

    def _add_identity_row(self, site: str, kind: str, detail: str, evidence: str):
        row = self.identity_table.rowCount()
        self.identity_table.insertRow(row)
        for col, value in enumerate([site, kind, detail, evidence]):
            self.identity_table.setItem(row, col, QTableWidgetItem(str(value or "")))

    def refresh_profile_storage(self, profile: BrowserProfile = None, quiet: bool = False):
        if isinstance(profile, bool):
            profile = None
        if not hasattr(self, "profile_storage_label"):
            return
        if profile is None and self.selected_profile_id:
            profile = self.browser_manager.get_profile(self.selected_profile_id)

        if not profile:
            self.profile_storage_label.setText("Selecione um perfil para ver o tamanho.")
            return

        report = self.browser_manager.get_profile_storage_report(profile.id)
        if not report.get("ok"):
            self.profile_storage_label.setText(report.get("message", "Nao consegui medir este perfil."))
            if not quiet:
                self._set_status(report.get("message", "Nao consegui medir este perfil."), "#f59e0b")
            return

        fmt = self.browser_manager.format_size
        status = report.get("status", "leve")
        status_text = {
            "leve": "Leve",
            "medio": "Medio",
            "pesado": "Pesado",
        }.get(status, status.title())
        self.profile_storage_label.setText(
            f"Tamanho total: {fmt(report.get('total_bytes', 0))} | Status: {status_text}\n"
            f"Cache seguro: {fmt(report.get('cache_bytes', 0))}\n"
            f"Dados de sites: {fmt(report.get('site_data_bytes', 0))} | Cookies/logins/Web Data: {fmt(report.get('identity_bytes', 0))}\n"
            f"Outros arquivos do Chrome: {fmt(report.get('other_bytes', 0))}"
        )
        if not quiet:
            self._set_status(report.get("message", "Tamanho atualizado."), "#7dd3fc")

    def clear_profile_cache_safe(self):
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Cache seguro", "Selecione um perfil primeiro.")
            return
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return
        if self.browser_manager.is_browser_active(self.selected_profile_id):
            QMessageBox.warning(self, "Cache seguro", "Feche o navegador deste perfil antes de limpar cache.")
            return

        report = self.browser_manager.get_profile_storage_report(self.selected_profile_id)
        cache_text = self.browser_manager.format_size(report.get("cache_bytes", 0)) if report.get("ok") else "N/D"
        reply = QMessageBox.question(
            self,
            "Limpar cache seguro",
            f"Limpar apenas o cache seguro do perfil '{profile.name}'?\n\n"
            f"Cache estimado: {cache_text}\n\n"
            "Isto preserva cookies, logins, favoritos, Local Storage e IndexedDB.",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        result = self.browser_manager.clear_profile_cache_only(self.selected_profile_id)
        self.refresh_logs()
        self.refresh_profile_storage(profile)
        if result.get("ok"):
            self.refresh_profile_list()
            QMessageBox.information(self, "Cache seguro", result.get("message", "Cache limpo."))
            self._set_status(result.get("message", "Cache limpo."), "#10b981")
        else:
            QMessageBox.warning(self, "Cache seguro", result.get("message", "Nao consegui limpar cache."))
            self._set_status(result.get("message", "Falha ao limpar cache."), "#f59e0b")

    def scan_selected_profile_identity(self):
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Identificação", "Selecione um perfil primeiro.")
            return
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return
        self._set_status("Analisando cookies e logins locais do perfil...", "#7dd3fc")
        result = self.browser_manager.update_profile_identity(self.selected_profile_id)
        self.refresh_logs()
        self.refresh_profile_list()
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        self.refresh_profile_identity(profile)
        if result.get("ok"):
            QMessageBox.information(
                self,
                "Identificação concluída",
                result.get("message", "Perfil analisado.") + "\n\n"
                "Nenhuma senha foi descriptografada. A leitura mostra apenas domínio, cookies e usuário salvo visível."
            )
            self._set_status(result.get("message", "Identificação atualizada."), "#10b981")
        else:
            QMessageBox.warning(self, "Identificação", result.get("message", "Não consegui analisar este perfil."))
            self._set_status(result.get("message", "Falha ao analisar perfil."), "#f59e0b")

    def copy_profile_identity_summary(self):
        profile = self.browser_manager.get_profile(self.selected_profile_id) if self.selected_profile_id else None
        if not profile:
            QMessageBox.warning(self, "Identificação", "Selecione um perfil primeiro.")
            return
        identity = getattr(profile, "account_identity", {}) or {}
        if not identity.get("ok"):
            QMessageBox.warning(self, "Identificação", "Analise o perfil antes de copiar o resumo.")
            return
        lines = [
            f"Perfil: {profile.name}",
            f"ID: {profile.id}",
            f"Analisado em: {(identity.get('scanned_at') or '').replace('T', ' ')}",
            f"Logins salvos: {identity.get('login_count', 0)}",
            f"Cookies: {identity.get('cookies_total', 0)}",
            f"Sites com cookies: {identity.get('cookie_domains_count', 0)}",
            "",
            "Logins:",
        ]
        for login in identity.get("logins", [])[:50]:
            lines.append(f"- {login.get('site', '-')}: {login.get('username', '-')} ({login.get('domain', '-')})")
        lines.append("")
        lines.append("Domínios com cookies:")
        for cookie in identity.get("cookie_domains", [])[:30]:
            lines.append(f"- {cookie.get('domain', '-')}: {cookie.get('count', 0)} cookie(s)")
        QApplication.clipboard().setText("\n".join(lines))
        self._set_status("Resumo de contas/cookies copiado.", "#10b981")

    def _selected_account(self):
        row = self.accounts_table.currentRow() if hasattr(self, "accounts_table") else -1
        if row < 0:
            return None
        item = self.accounts_table.item(row, 0)
        account_id = item.data(Qt.UserRole) if item else None
        for account in self.browser_manager.list_accounts():
            if account.get("id") == account_id:
                return account
        return None

    def add_account(self):
        dialog = BrowserAccountDialog(self.browser_manager.list_profiles(), self)
        if dialog.exec_() == QDialog.Accepted and dialog.result_account:
            self.browser_manager.save_account(dialog.result_account)
            self.refresh_accounts()
            self.refresh_logs()
            site = dialog.result_account.get("site") or dialog.result_account.get("name") or "site"
            self._set_status(f"Login salvo para: {site}", "#10b981")

    def edit_account(self):
        account = self._selected_account()
        if not account:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta primeiro.")
            return
        dialog = BrowserAccountDialog(self.browser_manager.list_profiles(), self, account)
        if dialog.exec_() == QDialog.Accepted and dialog.result_account:
            self.browser_manager.save_account(dialog.result_account)
            self.refresh_accounts()
            self.refresh_logs()
            site = dialog.result_account.get("site") or dialog.result_account.get("name") or "site"
            self._set_status(f"Login salvo para: {site}", "#10b981")

    def delete_account(self):
        account = self._selected_account()
        if not account:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta primeiro.")
            return
        if self.browser_manager.delete_account(account.get("id")):
            self.refresh_accounts()
            self.refresh_tasks()
            self.refresh_logs()

    def open_account_profile(self):
        account = self._selected_account()
        if not account or not account.get("profile_id"):
            QMessageBox.warning(self, "Aviso", "Essa conta não tem perfil vinculado.")
            return
        self.selected_profile_id = account.get("profile_id")
        if account.get("site"):
            self.url_input.setText(account.get("site"))
        self.start_browser()

    def refresh_tasks(self):
        if not hasattr(self, "tasks_table"):
            return
        tasks = self.browser_manager.list_tasks()
        self.tasks_table.setRowCount(0)
        for task in tasks:
            row = self.tasks_table.rowCount()
            self.tasks_table.insertRow(row)
            values = [
                "Sim" if task.get("done") else "Não",
                task.get("title", ""),
                self._profile_name(task.get("profile_id", "")),
                self._account_name(task.get("account_id", "")),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, task.get("id"))
                self.tasks_table.setItem(row, col, item)

    def _selected_task(self):
        row = self.tasks_table.currentRow() if hasattr(self, "tasks_table") else -1
        if row < 0:
            return None
        item = self.tasks_table.item(row, 0)
        task_id = item.data(Qt.UserRole) if item else None
        for task in self.browser_manager.list_tasks():
            if task.get("id") == task_id:
                return task
        return None

    def add_task(self):
        dialog = BrowserTaskDialog(
            self.browser_manager.list_profiles(),
            self.browser_manager.list_accounts(),
            self,
        )
        if dialog.exec_() == QDialog.Accepted and dialog.result_task:
            self.browser_manager.save_task(dialog.result_task)
            self.refresh_tasks()
            self.refresh_logs()

    def toggle_task_done(self):
        task = self._selected_task()
        if not task:
            QMessageBox.warning(self, "Aviso", "Selecione uma tarefa primeiro.")
            return
        self.browser_manager.set_task_done(task.get("id"), not task.get("done"))
        self.refresh_tasks()
        self.refresh_logs()

    def delete_task(self):
        task = self._selected_task()
        if not task:
            QMessageBox.warning(self, "Aviso", "Selecione uma tarefa primeiro.")
            return
        self.browser_manager.delete_task(task.get("id"))
        self.refresh_tasks()
        self.refresh_logs()

    def refresh_vault(self):
        if not hasattr(self, "vault_table"):
            return
        self.vault_table.setRowCount(0)
        unlocked = self.password_manager is not None and self.password_manager.is_unlocked()
        if hasattr(self, "vault_status_label"):
            self.vault_status_label.setText("Cofre desbloqueado" if unlocked else "Cofre bloqueado")
            self.vault_status_label.setStyleSheet(browser_vault_status_qss(unlocked))
        if not unlocked:
            return
        for secret in self.password_manager.get_passwords():
            row = self.vault_table.rowCount()
            self.vault_table.insertRow(row)
            values = [
                secret.get("site", ""),
                secret.get("username", ""),
                secret.get("category", ""),
                secret.get("notes", ""),
            ]
            for col, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setData(Qt.UserRole, secret.get("id"))
                self.vault_table.setItem(row, col, item)

    def unlock_vault(self):
        if PasswordManager is None:
            QMessageBox.warning(self, "Cofre", "Gerenciador de senhas indisponível neste ambiente.")
            return
        password, ok = QInputDialog.getText(
            self,
            "Senha mestra",
            "Digite a senha mestra do cofre:",
            QLineEdit.Password,
        )
        if not ok or not password:
            return
        manager = PasswordManager(str(self.browser_manager.config_dir))
        if manager.is_master_password_set():
            success, message = manager.unlock(password)
        else:
            success, message = manager.create_master_password(password)
        if success:
            self.password_manager = manager
            self.browser_manager.log_event("vault_unlocked", None, "Cofre desbloqueado")
        else:
            self.browser_manager.log_event("vault_error", None, message, "error")
        self.refresh_vault()
        self.refresh_logs()
        QMessageBox.information(self, "Cofre", message)

    def _selected_vault_secret_id(self):
        row = self.vault_table.currentRow() if hasattr(self, "vault_table") else -1
        if row < 0:
            return None
        item = self.vault_table.item(row, 0)
        return item.data(Qt.UserRole) if item else None

    def add_vault_secret(self):
        if not self.password_manager or not self.password_manager.is_unlocked():
            QMessageBox.warning(self, "Cofre", "Desbloqueie o cofre primeiro.")
            return
        site, ok = QInputDialog.getText(self, "Cofre", "Site/nome:")
        if not ok or not site.strip():
            return
        username, ok = QInputDialog.getText(self, "Cofre", "Usuário/email:")
        if not ok:
            return
        password, ok = QInputDialog.getText(self, "Cofre", "Senha/token:", QLineEdit.Password)
        if not ok:
            return
        notes, ok = QInputDialog.getMultiLineText(self, "Cofre", "Notas, 2FA ou backup codes:")
        if not ok:
            return
        self.password_manager.add_password(
            site=site.strip(),
            url="",
            username=username.strip(),
            password=password,
            notes=notes.strip(),
            category="Cofre",
            auto_fill=False,
        )
        self.browser_manager.log_event("vault_secret_added", None, site.strip())
        self.refresh_vault()
        self.refresh_logs()

    def remove_vault_secret(self):
        if not self.password_manager or not self.password_manager.is_unlocked():
            QMessageBox.warning(self, "Cofre", "Desbloqueie o cofre primeiro.")
            return
        secret_id = self._selected_vault_secret_id()
        if not secret_id:
            QMessageBox.warning(self, "Cofre", "Selecione um item do cofre.")
            return
        self.password_manager.remove_password(secret_id)
        self.browser_manager.log_event("vault_secret_removed", None, secret_id)
        self.refresh_vault()
        self.refresh_logs()

    def copy_logs(self):
        if hasattr(self, "logs_view"):
            QApplication.clipboard().setText(self.logs_view.toPlainText())
            self._set_status("Logs copiados", "#10b981")

    def create_browser_backup(self):
        backup_file = self.browser_manager.create_browser_backup()
        self.refresh_logs()
        if backup_file:
            self._set_status(f"Backup criado: {backup_file.name}", "#10b981")
            QMessageBox.information(self, "Backup criado", f"Backup salvo em:\n{backup_file}")
        else:
            self._set_status("Não foi possível criar o backup", "#f43f5e")
            QMessageBox.warning(self, "Backup", "Não foi possível criar o backup agora.")

    def prepare_format_backup(self):
        """Cria um backup próprio para antes de formatar o PC."""
        if self.format_backup_thread and self.format_backup_thread.isRunning():
            QMessageBox.information(self, "Backup", "Já existe um backup sendo preparado.")
            return

        active = self.browser_manager.get_active_browsers()
        if active:
            reply = QMessageBox.question(
                self,
                "Fechar navegadores?",
                "Existem navegadores abertos. Para o backup de sessão ficar mais confiável, feche todos antes.\n\n"
                "Fechar navegadores agora e continuar?",
                QMessageBox.Yes | QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
            self.browser_manager.cleanup()
            self.refresh_profile_list()

        reply = QMessageBox.question(
            self,
            "Backup para formatação",
            "Vou criar um ZIP com perfis, cookies, favoritos, extensões e configurações do Navegador Seguro.\n\n"
            "Isso ajuda a restaurar depois de formatar, mas Amazon/Google/Microsoft ainda podem pedir senha ou confirmação.\n\n"
            "Continuar?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        self.format_backup_btn.setEnabled(False)
        self.format_backup_status_label.setText("Preparando backup... isso pode demorar se os perfis tiverem muitos dados.")
        self._set_status("Preparando backup para formatação em segundo plano...", "#7dd3fc")

        self.format_backup_thread = BrowserFormatBackupThread(self.browser_manager)
        self.format_backup_thread.finished_backup.connect(self.on_format_backup_finished)
        self.format_backup_thread.start()

    def on_format_backup_finished(self, result: dict):
        self.refresh_logs()
        self.refresh_profile_list()
        if hasattr(self, "format_backup_btn"):
            self.format_backup_btn.setEnabled(True)

        if result.get("ok"):
            text = (
                f"Backup criado: {result.get('name')}\n"
                f"Tamanho: {result.get('size_mb')} MB\n"
                f"Perfis: {result.get('profiles_total')} | Arquivados: {result.get('archived_total')}\n"
                f"Com logins salvos: {result.get('profiles_with_logins')}\n"
                f"Com cookies: {result.get('profiles_with_cookies')}\n"
                f"Local: {result.get('file')}"
            )
            self.format_backup_status_label.setText(text)
            self._set_status("Backup para formatação criado com sucesso.", "#10b981")
            QMessageBox.information(
                self,
                "Backup para formatação criado",
                text + "\n\nDepois de formatar, restaure o ZIP na pasta do projeto antes de abrir os perfis."
            )
        else:
            message = result.get("message", "Não foi possível criar o backup.")
            self.format_backup_status_label.setText(f"Falha no backup: {message}")
            self._set_status("Falha ao criar backup para formatação.", "#f43f5e")
            QMessageBox.warning(self, "Backup", message)

    def open_selected_favorite(self):
        url = self.favorite_combo.currentData() if hasattr(self, "favorite_combo") else ""
        if not url:
            QMessageBox.warning(self, "Aviso", "Nenhum favorito selecionado.")
            return
        self.url_input.setText(url)
        self.start_browser()

    def detect_current_page_issue(self):
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro.")
            return
        result = self.browser_manager.detect_page_issue(self.selected_profile_id)
        self.refresh_logs()

        severity = result.get("severity", "info")
        icon = QMessageBox.Information
        if severity == "warning":
            icon = QMessageBox.Warning
        elif severity == "error":
            icon = QMessageBox.Critical

        suggestions = result.get("suggestions") or []
        details = [
            f"URL: {result.get('url', '-')}",
            f"Site: {result.get('site', '-')}",
            f"Título: {result.get('page_title', '-')}",
            f"Código: {result.get('code', '-')}",
            f"Campos visíveis: {result.get('input_count', '-')}",
            f"Tamanho do texto: {result.get('body_length', '-')}",
        ]

        box = QMessageBox(self)
        box.setIcon(icon)
        box.setWindowTitle("Detector de erro da página")
        box.setText(result.get("title", "Diagnóstico da página"))
        info_text = result.get("message", "")
        if suggestions:
            info_text += "\n\nSugestões:\n" + "\n".join(f"- {item}" for item in suggestions)
        box.setInformativeText(info_text)
        box.setDetailedText("\n".join(details))

        copy_btn = box.addButton("Copiar diagnóstico", QMessageBox.ActionRole)
        repair_btn = None
        streaming_btn = None
        retry_open_btn = None
        clean_site_btn = None
        if result.get("code") == "blocked_403" and result.get("site") == "paramount":
            repair_btn = box.addButton("Corrigir 403 Paramount", QMessageBox.ActionRole)
        if result.get("code") in ("blocked_403", "captcha", "robot_check", "robot_loop", "blank_page"):
            streaming_btn = box.addButton("Preparar modo Streaming", QMessageBox.ActionRole)
        if result.get("code") in ("robot_check", "robot_loop"):
            retry_open_btn = box.addButton("Tentar sem fechar", QMessageBox.ActionRole)
            clean_site_btn = box.addButton("Reset limpo (fecha)", QMessageBox.ActionRole)
        box.addButton(QMessageBox.Ok)
        box.exec_()

        clicked = box.clickedButton()
        if clicked == copy_btn:
            QApplication.clipboard().setText(
                f"{result.get('title', '')}\n{result.get('message', '')}\n\n" + "\n".join(details)
            )
            self._set_status("Diagnóstico copiado", "#10b981")
        elif repair_btn is not None and clicked == repair_btn:
            self.open_paramount_repair()
        elif streaming_btn is not None and clicked == streaming_btn:
            self.prepare_streaming_profile()
        elif retry_open_btn is not None and clicked == retry_open_btn:
            self.retry_site_without_closing()
        elif clean_site_btn is not None and clicked == clean_site_btn:
            self.reset_cloudflare_profile(result.get("site"), result.get("url"))

    def open_paramount_repair(self):
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro.")
            return
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return
        if self.browser_manager.is_browser_active(self.selected_profile_id):
            self.browser_manager.close_browser(self.selected_profile_id)
        profile.compatibility_mode = True
        profile.persist_data = True
        profile.save_logins = True
        profile.fingerprint_level = "Streaming"
        if getattr(profile, "browser_mode", "auto") == "auto":
            profile.browser_mode = "chrome"
        self.compatibility_checkbox.setChecked(True)
        self.persist_checkbox.setChecked(True)
        self.save_logins_checkbox.setChecked(True)
        if hasattr(self, "fingerprint_level_combo"):
            self.fingerprint_level_combo.setCurrentText("Streaming")
        if hasattr(self, "browser_mode_combo"):
            self.browser_mode_combo.setCurrentText(profile.browser_mode.title())
        self.browser_manager._save_profiles()
        self.browser_manager.clear_profile_data(self.selected_profile_id)
        self.url_input.setText("https://www.paramountplus.com/br/account/signin/")
        self._set_status("403 detectado: perfil limpo, modo Streaming e URL alternativa prontos.", "#7dd3fc")
        self.start_browser()

    def prepare_streaming_profile(self):
        """Ajusta o perfil para sites de streaming sem apagar cookies automaticamente."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro.")
            return
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return
        profile.compatibility_mode = True
        profile.persist_data = True
        profile.save_logins = True
        profile.fingerprint_level = "Streaming"
        if getattr(profile, "browser_mode", "auto") == "auto":
            profile.browser_mode = "chrome"
        self.compatibility_checkbox.setChecked(True)
        self.persist_checkbox.setChecked(True)
        self.save_logins_checkbox.setChecked(True)
        if hasattr(self, "fingerprint_level_combo"):
            self.fingerprint_level_combo.setCurrentText("Streaming")
        if hasattr(self, "browser_mode_combo"):
            self.browser_mode_combo.setCurrentText(profile.browser_mode.title())
        self.browser_manager._save_profiles()
        if self.browser_manager.is_browser_active(self.selected_profile_id):
            self._set_status("Modo Streaming salvo. Feche e abra o perfil de novo para aplicar tudo.", "#f59e0b")
            QMessageBox.information(
                self,
                "Modo Streaming",
                "Preparei este perfil para streaming.\n\n"
                "Como ele ja esta aberto, feche e abra novamente para aplicar todos os ajustes."
            )
        else:
            self._set_status("Modo Streaming preparado para este perfil.", "#10b981")
            QMessageBox.information(self, "Modo Streaming", "Perfil preparado. Agora abra pelo favorito do site.")

    def retry_site_without_closing(self):
        """Limpa dados do site atual e recarrega sem fechar a janela do navegador."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro.")
            return
        result = self.browser_manager.retry_site_without_closing(self.selected_profile_id)
        self.refresh_logs()
        if result.get("ok"):
            self._set_status(result.get("message", "Tentei sem fechar."), "#7dd3fc")
            QMessageBox.information(
                self,
                "Tentar sem fechar",
                result.get("message", "Tentei limpar o site aberto sem fechar o navegador.")
            )
        else:
            self._set_status(result.get("message", "Não consegui tentar sem fechar."), "#f59e0b")
            QMessageBox.warning(self, "Tentar sem fechar", result.get("message", "Não consegui tentar sem fechar."))

    def reset_cloudflare_profile(self, site: str = None, url: str = None):
        """Prepara um perfil limpo e normal para verificacoes Cloudflare travadas em loop."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro.")
            return
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return

        reply = QMessageBox.question(
            self,
            "Reset limpo do site",
            "Isso vai fechar este perfil e limpar cookies/cache/login salvos dele.\n\n"
            "Use quando a verificacao humana fica em loop mesmo depois de marcar.\n\n"
            "Continuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return

        if self.browser_manager.is_browser_active(self.selected_profile_id):
            self.browser_manager.close_browser(self.selected_profile_id)

        profile.compatibility_mode = True
        profile.persist_data = True
        profile.save_logins = True
        profile.fingerprint_level = "Normal"
        if getattr(profile, "browser_mode", "auto") == "auto":
            profile.browser_mode = "chrome"

        self.compatibility_checkbox.setChecked(True)
        self.persist_checkbox.setChecked(True)
        self.save_logins_checkbox.setChecked(True)
        if hasattr(self, "fingerprint_level_combo"):
            self.fingerprint_level_combo.setCurrentText("Normal")
        if hasattr(self, "browser_mode_combo"):
            self.browser_mode_combo.setCurrentText(profile.browser_mode.title())

        self.browser_manager._save_profiles()
        self.browser_manager.clear_profile_data(self.selected_profile_id)

        target = url or ""
        if site == "crunchyroll":
            target = "https://www.crunchyroll.com/discover"
        elif site == "paramount":
            target = "https://www.paramountplus.com/br/account/signin/"
        elif not target:
            target = "https://www.google.com/"
        self.url_input.setText(target)
        self._set_status("Perfil limpo e normal preparado. Abrindo novamente...", "#7dd3fc")
        self.start_browser()

    def show_profile_menu(self, pos):
        item = self.profile_list.itemAt(pos)
        if item:
            self.profile_list.setCurrentItem(item)
            self.on_profile_selected(item)

        menu = QMenu(self)
        menu.addAction("Abrir navegador", self.start_browser)
        menu.addAction("Clonar perfil", self.clone_profile)
        menu.addAction("Fechar navegador", self.close_selected_browser)
        menu.addAction("Selecionar todos", self.select_all_profiles)
        menu.addAction("Analisar contas/cookies", self.scan_selected_profile_identity)
        menu.addAction("Ver tamanho do perfil", self.refresh_profile_storage)
        menu.addAction("Arquivar selecionados", self.archive_selected_profiles)
        menu.addAction("Restaurar selecionados", self.restore_selected_profiles)
        menu.addAction("Excluir selecionados", self.delete_profile)
        menu.addSeparator()
        menu.addAction("Randomizar fingerprint", self.randomize_fingerprint)
        menu.addAction("Limpar cache seguro", self.clear_profile_cache_safe)
        menu.addAction("Limpar dados", self.clear_profile_data)
        menu.addSeparator()
        menu.addAction("Aplicar padrões nos selecionados", self.apply_defaults_to_selected_profiles)
        menu.addAction("Limpar dados dos selecionados", self.clear_selected_profile_data)
        menu.addAction("Mudar tags dos selecionados", self.change_tags_selected_profiles)
        menu.addSeparator()
        menu.addAction("Aplicar padrões aos perfis", self.apply_defaults_to_all_profiles)
        menu.exec_(self.profile_list.mapToGlobal(pos))

    def clone_profile(self):
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro!")
            return

        source = self.browser_manager.get_profile(self.selected_profile_id)
        if not source:
            return

        name, ok = QInputDialog.getText(
            self, "Clonar Perfil",
            "Nome do novo perfil:",
            text=f"{source.name} Copy"
        )
        if not ok or not name.strip():
            return

        clone = self.browser_manager.clone_profile(self.selected_profile_id, name.strip(), clone_data=False)
        if clone:
            self.refresh_profile_list()
            self.selected_profile_id = clone.id
            for i in range(self.profile_list.count()):
                item = self.profile_list.item(i)
                if item.data(Qt.UserRole) == clone.id:
                    self.profile_list.setCurrentItem(item)
                    self.on_profile_selected(item)
                    break
            self._set_status(f"Perfil clonado: {clone.name}", "#10b981")

    def close_selected_browser(self):
        profile_ids = self.selected_profile_ids()
        if not profile_ids:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro!")
            return
        closed = 0
        for profile_id in profile_ids:
            if self.browser_manager.close_browser(profile_id):
                closed += 1
        if closed:
            self._set_status(f"{closed} navegador(es) fechado(s)", "#10b981")
        else:
            self._set_status("Perfil selecionado sem navegador ativo", "#f59e0b")
        self.refresh_profile_list()

    def close_all_browsers(self):
        active = self.browser_manager.get_active_browsers()
        self.browser_manager.cleanup()
        self.refresh_profile_list()
        self._set_status(f"{len(active)} navegador(es) fechado(s)", "#10b981")

    def apply_defaults_to_all_profiles(self):
        results = self.browser_manager.apply_defaults_to_all_profiles()
        ok_count = sum(1 for ok in results.values() if ok)
        fav_count = self.browser_manager.get_default_favorite_count()
        ext_count = self.browser_manager.get_default_extension_count()
        self.refresh_favorites_combo()
        self._update_defaults_summary(fav_count, ext_count)
        self._set_status(
            f"Padrões aplicados em {ok_count}/{len(results)} perfil(is). {fav_count} favorito(s) e {ext_count} extensão(ões) prontos.",
            "#10b981"
        )
        self.refresh_profile_list()
        self.refresh_logs()

    def apply_defaults_to_selected_profiles(self):
        profile_ids = self.selected_profile_ids()
        if not profile_ids:
            QMessageBox.warning(self, "Padrões", "Selecione um ou mais perfis primeiro.")
            return
        ok_count = 0
        for profile_id in profile_ids:
            if self.browser_manager._apply_defaults_to_profile(profile_id):
                ok_count += 1
        self.browser_manager.log_event("defaults_applied_selected", None, f"{ok_count}/{len(profile_ids)} perfis")
        self.refresh_profile_list()
        self.refresh_logs()
        self._set_status(f"Padrões aplicados em {ok_count}/{len(profile_ids)} perfil(is).", "#10b981")

    def clear_selected_profile_data(self):
        profile_ids = self.selected_profile_ids()
        if not profile_ids:
            QMessageBox.warning(self, "Limpar dados", "Selecione um ou mais perfis primeiro.")
            return
        active = [pid for pid in profile_ids if self.browser_manager.is_browser_active(pid)]
        if active:
            QMessageBox.warning(self, "Limpar dados", "Feche os navegadores selecionados antes de limpar os dados.")
            return
        reply = QMessageBox.question(
            self,
            "Limpar selecionados",
            f"Limpar cookies, cache e sessões de {len(profile_ids)} perfil(is) selecionado(s)?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        ok_count = 0
        for profile_id in profile_ids:
            if self.browser_manager.clear_profile_data(profile_id):
                ok_count += 1
        self.browser_manager.log_event("profile_data_cleared_batch", None, f"{ok_count}/{len(profile_ids)} perfis")
        self.refresh_profile_list()
        self.refresh_logs()
        self._set_status(f"Dados limpos em {ok_count}/{len(profile_ids)} perfil(is).", "#10b981")

    def change_tags_selected_profiles(self):
        profile_ids = self.selected_profile_ids()
        if not profile_ids:
            QMessageBox.warning(self, "Tags", "Selecione um ou mais perfis primeiro.")
            return
        text, ok = QInputDialog.getText(
            self,
            "Mudar tags",
            "Tags para aplicar nos perfis selecionados:",
            text=self.tags_input.text(),
        )
        if not ok:
            return
        tags = [tag.strip() for tag in text.replace(";", ",").split(",") if tag.strip()]
        for profile_id in profile_ids:
            profile = self.browser_manager.get_profile(profile_id)
            if profile:
                profile.tags = tags
        self.browser_manager._save_profiles()
        self.browser_manager.log_event("profile_tags_batch", None, f"{len(profile_ids)} perfis")
        self.refresh_profile_list()
        self._set_status(f"Tags aplicadas em {len(profile_ids)} perfil(is).", "#10b981")
    
    def on_profile_selected(self, item):
        """Callback quando um perfil é selecionado."""
        profile_id = item.data(Qt.UserRole)
        self.selected_profile_id = profile_id
        
        profile = self.browser_manager.get_profile(profile_id)
        if profile:
            self.load_profile_to_form(profile)
            self.refresh_profile_identity(profile)
    
    def load_profile_to_form(self, profile: BrowserProfile):
        """Carrega os dados do perfil no formulário."""
        self.name_input.setText(profile.name)
        self.profile_id_label.setText(profile.id)
        self.proxy_input.setText(profile.proxy or "")
        if hasattr(self, "browser_mode_combo"):
            mode_map = {"auto": "Auto", "chrome": "Chrome", "edge": "Edge", "firefox": "Firefox"}
            self.browser_mode_combo.setCurrentText(mode_map.get(getattr(profile, "browser_mode", "auto"), "Auto"))
        self.tags_input.setText(", ".join(getattr(profile, "tags", []) or []))
        self.notes_input.setText(getattr(profile, "notes", "") or "")
        self.load_address_to_form(getattr(profile, "address_data", {}) or {})
        
        # Carregar configuração de persistência
        self.persist_checkbox.setChecked(getattr(profile, 'persist_data', True))
        self.compatibility_checkbox.setChecked(getattr(profile, "compatibility_mode", False))
        self.save_logins_checkbox.setChecked(getattr(profile, "save_logins", True))
        if hasattr(self, "fingerprint_level_combo"):
            level = getattr(profile, "fingerprint_level", "Leve") or "Leve"
            if self.fingerprint_level_combo.findText(level) >= 0:
                self.fingerprint_level_combo.setCurrentText(level)
        
        # Atualizar resumo do fingerprint
        fp = profile.fingerprint
        if fp:
            summary = f"User-Agent: {fp.get('user_agent', 'N/A')[:50]}...\n"
            summary += f"Resolução: {fp.get('screen', {}).get('width', 'N/A')}x{fp.get('screen', {}).get('height', 'N/A')}\n"
            summary += f"Timezone: {fp.get('timezone', {}).get('name', 'N/A')}\n"
            summary += f"WebGL: {fp.get('webgl', {}).get('vendor', 'N/A')[:30]}..."
            self.fp_summary.setText(summary)
        else:
            self.fp_summary.setText("Fingerprint não configurado")
        
        # Atualizar contagem de auto-login
        login_count = len(profile.auto_login)
        if login_count > 0:
            self.login_count_label.setText(f"{login_count} site(s) configurado(s)")
        else:
            self.login_count_label.setText("Nenhum site configurado")
        
        # Validar proxy se existir
        if profile.proxy:
            self.validate_proxy()
        self.refresh_profile_identity(profile)
        self.refresh_profile_storage(profile, quiet=True)

    def address_from_form(self) -> dict:
        """Lê os campos de endereço do formulário do perfil."""
        return {
            "cep": self.address_cep_input.text().strip(),
            "logradouro": self.address_street_input.text().strip(),
            "rua": self.address_street_input.text().strip(),
            "numero": self.address_number_input.text().strip(),
            "complemento": self.address_complement_input.text().strip(),
            "bairro": self.address_bairro_input.text().strip(),
            "cidade": self.address_city_input.text().strip(),
            "estado": self.address_state_input.text().strip(),
            "uf": self.address_uf_input.text().strip().upper(),
        }

    def load_address_to_form(self, address: dict):
        """Carrega endereço salvo no perfil para a UI."""
        address = address or {}
        self.address_cep_input.setText(address.get("cep", "") or "")
        self.address_street_input.setText(address.get("logradouro") or address.get("rua", "") or "")
        self.address_number_input.setText(str(address.get("numero", "") or ""))
        self.address_complement_input.setText(address.get("complemento", "") or "")
        self.address_bairro_input.setText(address.get("bairro", "") or "")
        self.address_city_input.setText(address.get("cidade", "") or "")
        self.address_state_input.setText(address.get("estado", "") or "")
        self.address_uf_input.setText(address.get("uf", "") or "")
        if address.get("cep") and (address.get("logradouro") or address.get("cidade")):
            self.address_status_label.setText(
                f"Salvo: {address.get('cep', '')} • {address.get('cidade', '')}/{address.get('uf', '')}"
            )
            self.address_status_label.setStyleSheet(browser_label_qss("success"))
        else:
            self.address_status_label.setText("Endereço ainda não salvo neste perfil.")
            self.address_status_label.setStyleSheet(browser_label_qss("muted"))

    def address_to_text(self, address: dict) -> str:
        parts = [
            address.get("cep", ""),
            address.get("logradouro") or address.get("rua", ""),
            address.get("numero", ""),
            address.get("complemento", ""),
            address.get("bairro", ""),
            address.get("cidade", ""),
            address.get("estado", ""),
            address.get("uf", ""),
        ]
        labels = ["CEP", "Rua", "Número", "Complemento", "Bairro", "Cidade", "Estado", "UF"]
        return "\n".join(f"{label}: {value}" for label, value in zip(labels, parts) if value)

    def set_profile_address(self, address: dict, save: bool = True):
        """Atualiza a UI e, se possível, salva no perfil selecionado."""
        self.load_address_to_form(address)
        if save and self.selected_profile_id:
            profile = self.browser_manager.get_profile(self.selected_profile_id)
            if profile:
                profile.address_data = self.address_from_form()
                self.browser_manager._save_profiles()
                self.browser_manager.log_event("address_saved", self.selected_profile_id, "Endereço salvo no perfil")

    def generate_profile_address(self):
        """Gera um endereço rápido usando a reserva local, com fallback para o gerador completo."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro.")
            return

        address = None
        uf = self.address_uf_input.text().strip().upper() or None
        if self.address_reserve:
            address = self.address_reserve.get_reserva(uf)

        if not address and self.address_generator:
            try:
                endereco = self.address_generator.gerar_endereco(uf=uf)
                address = endereco.to_dict() if endereco else None
            except Exception as e:
                self._set_status(f"Não consegui gerar endereço: {e}", "#f59e0b")

        if not address:
            QMessageBox.warning(self, "Endereço", "Não encontrei endereço na reserva local.")
            return

        self.set_profile_address(address, save=True)
        self._set_status("Endereço gerado e salvo no perfil.", "#10b981")

    def copy_profile_address(self):
        address = self.address_from_form()
        text = self.address_to_text(address)
        if not text:
            QMessageBox.warning(self, "Endereço", "Nenhum endereço preenchido para copiar.")
            return
        QApplication.clipboard().setText(text)
        self._set_status("Endereço copiado.", "#22c55e")

    def fill_address_on_current_page(self):
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro.")
            return

        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return

        profile.address_data = self.address_from_form()
        self.browser_manager._save_profiles()
        result = self.browser_manager.fill_address_fields(self.selected_profile_id, profile.address_data)
        if result.get("ok"):
            self._set_status(result.get("message", "Endereço preenchido."), "#10b981")
            QMessageBox.information(self, "Endereço", result.get("message", "Endereço preenchido."))
        else:
            self._set_status(result.get("message", "Não consegui preencher endereço."), "#f59e0b")
            QMessageBox.warning(self, "Endereço", result.get("message", "Não consegui preencher endereço."))
    
    def create_profile(self):
        """Cria um novo perfil."""
        name, ok = QInputDialog.getText(
            self, "Novo Perfil", "Nome do perfil:"
        )
        
        if ok and name:
            profile = self.browser_manager.create_profile(name=name)
            self.refresh_profile_list()
            
            # Selecionar o novo perfil
            for i in range(self.profile_list.count()):
                item = self.profile_list.item(i)
                if item.data(Qt.UserRole) == profile.id:
                    self.profile_list.setCurrentItem(item)
                    self.on_profile_selected(item)
                    break
            
            QMessageBox.information(
                self, "Sucesso",
                f"Perfil '{name}' criado com sucesso!"
            )
    
    def create_quick_profile(self):
        """Cria um perfil rápido e inicia o navegador."""
        try:
            profile = self.browser_manager.create_quick_profile()
            self.refresh_profile_list()
            
            # Selecionar o novo perfil
            for i in range(self.profile_list.count()):
                item = self.profile_list.item(i)
                if item.data(Qt.UserRole) == profile.id:
                    self.profile_list.setCurrentItem(item)
                    self.on_profile_selected(item)
                    break
            
            # Iniciar navegador
            self.selected_profile_id = profile.id
            self.start_browser()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Erro",
                f"Erro ao criar perfil rápido: {str(e)}"
            )

    def create_profile_batch(self):
        count, ok = QInputDialog.getInt(
            self, "Criar Lote",
            "Quantidade de perfis:",
            5, 1, 100, 1
        )
        if not ok:
            return

        created = []
        for _ in range(count):
            created.append(self.browser_manager.create_quick_profile())

        self.refresh_profile_list()
        if created:
            self.selected_profile_id = created[-1].id
            for i in range(self.profile_list.count()):
                item = self.profile_list.item(i)
                if item.data(Qt.UserRole) == self.selected_profile_id:
                    self.profile_list.setCurrentItem(item)
                    self.on_profile_selected(item)
                    break
        self._set_status(f"{len(created)} perfis criados com extensões padrão prontas", "#10b981")
    
    def edit_profile(self):
        """Edita o perfil selecionado."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro!")
            return
        
        # O formulário já está preenchido, apenas focar no nome
        self.name_input.setFocus()
        self.name_input.selectAll()
    
    def delete_profile(self):
        """Remove um ou vários perfis selecionados."""
        profile_ids = self.selected_profile_ids()
        if not profile_ids:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro!")
            return
        
        profiles = [self.browser_manager.get_profile(profile_id) for profile_id in profile_ids]
        profiles = [profile for profile in profiles if profile]
        if not profiles:
            return
        blocked = [
            profile.name for profile in profiles
            if self.browser_manager.is_browser_active(profile.id) or self.browser_manager.is_profile_launching(profile.id)
        ]
        if blocked:
            shown = "\n".join(f"- {name}" for name in blocked[:10])
            if len(blocked) > 10:
                shown += f"\n... e mais {len(blocked) - 10}"
            QMessageBox.warning(
                self,
                "Perfil aberto",
                "Feche estes perfis antes de excluir para evitar travamento e arquivo preso:\n\n"
                f"{shown}"
            )
            self._set_status("Feche o navegador do perfil antes de excluir.", "#f59e0b")
            return

        names = "\n".join(f"- {profile.name}" for profile in profiles[:12])
        if len(profiles) > 12:
            names += f"\n... e mais {len(profiles) - 12}"
        
        reply = QMessageBox.question(
            self, "Confirmar",
            f"Deseja realmente remover {len(profiles)} perfil(is)?\n\n{names}\n\n"
            "Todos os dados de navegação serão perdidos.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            removed = 0
            for profile in profiles:
                if self.browser_manager.delete_profile(profile.id):
                    removed += 1
            self.selected_profile_id = None
            self.clear_form()
            self.refresh_profile_list()
            self.refresh_logs()
            self._set_status(f"{removed} perfil(is) removido(s). Dados pesados apagando em segundo plano.", "#10b981")
            QMessageBox.information(
                self,
                "Sucesso",
                f"{removed} perfil(is) removido(s) da lista.\n\n"
                "A pasta pesada do navegador continua sendo apagada em segundo plano para não travar o projeto."
            )
    
    def clear_form(self):
        """Limpa o formulário."""
        self.name_input.clear()
        self.profile_id_label.setText("-")
        self.proxy_input.clear()
        self.tags_input.clear()
        self.notes_input.clear()
        self.proxy_status.clear()
        self.fp_summary.clear()
        self.login_count_label.setText("Nenhum site configurado")
        self.persist_checkbox.setChecked(True)
        self.compatibility_checkbox.setChecked(False)
        self.save_logins_checkbox.setChecked(True)
        if hasattr(self, "browser_mode_combo"):
            self.browser_mode_combo.setCurrentText("Auto")
        if hasattr(self, "fingerprint_level_combo"):
            self.fingerprint_level_combo.setCurrentText("Leve")
        self.load_address_to_form({})
        self.refresh_profile_identity(None)
        self.refresh_profile_storage(None)
    
    def clear_profile_data(self):
        """Limpa os dados de navegação do perfil selecionado."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro!")
            return
        
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return
        
        # Verificar se o navegador está ativo
        if self.browser_manager.is_browser_active(self.selected_profile_id):
            QMessageBox.warning(
                self, "Aviso",
                "Feche o navegador antes de limpar os dados!"
            )
            return
        
        reply = QMessageBox.question(
            self, "Confirmar",
            f"Deseja limpar todos os dados de navegação do perfil '{profile.name}'?\n\n"
            "Isso irá remover:\n"
            "• Histórico de navegação\n"
            "• Cookies e sessões\n"
            "• Cache e arquivos temporários\n"
            "• Dados de formulários\n\n"
            "Os favoritos serão mantidos.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            if self.browser_manager.clear_profile_data(self.selected_profile_id):
                QMessageBox.information(
                    self, "Sucesso",
                    "Dados de navegação limpos com sucesso!"
                )
            else:
                QMessageBox.warning(
                    self, "Aviso",
                    "Não foi possível limpar os dados do perfil."
                )
    
    def validate_proxy(self):
        """Valida o proxy informado."""
        proxy_str = self.proxy_input.text().strip()
        
        if not proxy_str:
            self.proxy_status.setText("")
            return
        
        valid, message = self.proxy_manager.validate_proxy(proxy_str)
        
        if valid:
            proxy = self.proxy_manager.parse_proxy_string(proxy_str)
            if proxy.requires_auth:
                self.proxy_status.setText("✅ Proxy válido (com autenticação)")
                self.proxy_status.setStyleSheet(browser_proxy_status_qss(True))
            else:
                self.proxy_status.setText("✅ Proxy válido")
                self.proxy_status.setStyleSheet(browser_proxy_status_qss(True))
        else:
            self.proxy_status.setText(f"❌ {message}")
            self.proxy_status.setStyleSheet(browser_proxy_status_qss(False))
    
    def randomize_fingerprint(self):
        """Randomiza o fingerprint do perfil selecionado."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro!")
            return
        
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return
        
        # Gerar novo fingerprint brasileiro
        new_fp = self.fingerprint_generator.generate_brazilian_fingerprint()
        profile.fingerprint = new_fp
        
        # Atualizar interface
        self.load_profile_to_form(profile)
        
        QMessageBox.information(
            self, "Sucesso",
            "Fingerprint randomizado! Clique em 'Salvar Perfil' para confirmar."
        )
    
    def customize_fingerprint(self):
        """Abre o diálogo de customização de fingerprint."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro!")
            return
        
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return
        
        dialog = FingerprintConfigDialog(self, profile.fingerprint)
        if dialog.exec_() == QDialog.Accepted and dialog.result_fingerprint:
            profile.fingerprint = dialog.result_fingerprint
            self.load_profile_to_form(profile)
            QMessageBox.information(
                self, "Sucesso",
                "Fingerprint customizado! Clique em 'Salvar Perfil' para confirmar."
            )
    
    def configure_auto_login(self):
        """Abre o diálogo de configuração de auto-login."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro!")
            return
        
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return
        
        dialog = AutoLoginDialog(self, profile.auto_login)
        if dialog.exec_() == QDialog.Accepted:
            profile.auto_login = dialog.result_logins
            
            # Atualizar label
            login_count = len(profile.auto_login)
            if login_count > 0:
                self.login_count_label.setText(f"{login_count} site(s) configurado(s)")
            else:
                self.login_count_label.setText("Nenhum site configurado")
            
            QMessageBox.information(
                self, "Sucesso",
                "Auto-login configurado! Clique em 'Salvar Perfil' para confirmar."
            )
    
    def save_profile(self):
        """Salva as alterações do perfil."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro!")
            return
        
        profile = self.browser_manager.get_profile(self.selected_profile_id)
        if not profile:
            return
        
        # Atualizar dados
        profile.name = self.name_input.text().strip() or profile.name
        profile.proxy = self.proxy_input.text().strip() or None
        profile.persist_data = self.persist_checkbox.isChecked()
        profile.compatibility_mode = self.compatibility_checkbox.isChecked()
        profile.save_logins = self.save_logins_checkbox.isChecked()
        if hasattr(self, "browser_mode_combo"):
            profile.browser_mode = self.browser_mode_combo.currentText().lower()
        if hasattr(self, "fingerprint_level_combo"):
            profile.fingerprint_level = self.fingerprint_level_combo.currentText()
        profile.tags = [
            tag.strip()
            for tag in self.tags_input.text().replace(";", ",").split(",")
            if tag.strip()
        ]
        profile.notes = self.notes_input.toPlainText().strip()
        profile.address_data = self.address_from_form()
        
        # Salvar
        self.browser_manager._save_profiles()
        self.browser_manager.log_event("profile_saved", self.selected_profile_id, f"Perfil salvo: {profile.name}")
        self.refresh_profile_list()
        
        QMessageBox.information(self, "Sucesso", "Perfil salvo com sucesso!")
    
    def start_browser(self, *_):
        """Inicia o navegador com o perfil selecionado."""
        if not self.selected_profile_id:
            QMessageBox.warning(self, "Aviso", "Selecione um perfil primeiro!")
            return
        
        profile_id = self.selected_profile_id

        thread = getattr(self, "launch_threads", {}).get(profile_id)
        if thread and thread.isRunning():
            self._set_status("Este perfil ja tem uma abertura em andamento.", "#38bdf8")
            return

        if profile_id in self.launching_profile_ids or self.browser_manager.is_profile_launching(profile_id):
            self._set_status("Este perfil ja esta abrindo. Aguarde terminar antes de clicar de novo.", "#38bdf8")
            return

        # Verificar se ja esta ativo
        if self.browser_manager.is_browser_active(profile_id):
            self._set_status("Este perfil ja esta aberto. Use Fechar se quiser reiniciar.", "#f59e0b")
            return

        if not self.browser_manager.begin_profile_launch(profile_id):
            self._set_status("Este perfil ja esta aberto ou abrindo.", "#38bdf8")
            return
        self.launching_profile_ids.add(profile_id)
        self.refresh_profile_list()
        
        # URL inicial ou pesquisa
        url = self.browser_manager.normalize_navigation_target(self.url_input.text().strip())
        if "paramountplus.com" in url.lower() and "/account/user-flow" in url.lower():
            url = "https://www.paramountplus.com/br/account/signin/"
        self.url_input.setText(url)
        
        # Iniciar em thread separada
        self.launch_thread = BrowserLaunchThread(
            self.browser_manager,
            profile_id,
            url,
            monitor=True  # Monitorar fechamento do navegador
        )
        self.launch_thread.finished.connect(self.on_browser_launch_finished)
        self.launch_thread.browser_closed.connect(self.on_browser_closed)
        self.launch_thread.thread_done.connect(self.on_browser_thread_done)
        self.launch_threads[profile_id] = self.launch_thread
        self.launch_thread.start()
        for btn_name in ("start_btn", "open_url_btn"):
            btn = getattr(self, btn_name, None)
            if btn:
                btn.setEnabled(False)
        profile = self.browser_manager.get_profile(profile_id)
        mode = getattr(profile, "browser_mode", "auto") if profile else "auto"
        self._set_status(f"Iniciando navegador isolado ({mode})...", "#7dd3fc")
    
    def on_browser_launch_finished(self, success: bool, message: str):
        """Callback quando o navegador termina de iniciar."""
        thread = self.sender()
        profile_id = getattr(thread, "profile_id", self.selected_profile_id)
        if profile_id:
            self.launching_profile_ids.discard(profile_id)
            self.browser_manager.end_profile_launch(profile_id)
        self.refresh_profile_list()
        self.refresh_logs()
        for btn_name in ("start_btn", "open_url_btn"):
            btn = getattr(self, btn_name, None)
            if btn:
                btn.setEnabled(True)
        
        if success:
            self._set_status(message, "#10b981")
        else:
            for btn_name in ("start_btn", "open_url_btn"):
                btn = getattr(self, btn_name, None)
                if btn:
                    btn.setEnabled(True)
            self.browser_manager.log_event("browser_error", profile_id, message, "error")
            self._set_status(message, "#f43f5e")
            QMessageBox.critical(self, "Erro", message)

    def on_browser_thread_done(self, profile_id: str):
        """Remove a thread finalizada sem perder o monitor de outros perfis."""
        thread = getattr(self, "launch_threads", {}).pop(profile_id, None)
        if thread:
            thread.deleteLater()

    def on_browser_closed(self, profile_id: str):
        """Callback quando o navegador é fechado pelo usuário."""
        # Limpar referência do navegador
        self.launching_profile_ids.discard(profile_id)
        self.browser_manager.end_profile_launch(profile_id)
        if profile_id in self.browser_manager.active_browsers:
            try:
                del self.browser_manager.active_browsers[profile_id]
            except Exception:
                pass
        
        # Atualizar lista de perfis
        self.refresh_profile_list()
        self.browser_manager.log_event("browser_closed", profile_id, "Chrome foi fechado")
        self.refresh_logs()
        for btn_name in ("start_btn", "open_url_btn"):
            btn = getattr(self, btn_name, None)
            if btn:
                btn.setEnabled(True)
        self._set_status("Navegador fechado", "#94a3b8")
        
        # Mostrar mensagem amigável (opcional - pode comentar se preferir sem notificação)
        # QMessageBox.information(self, "Navegador Fechado", "O navegador foi fechado.")
    
    def closeEvent(self, event):
        """Limpa recursos ao fechar."""
        # Parar monitores de navegador sem depender apenas da ultima thread criada.
        for thread in list(getattr(self, "launch_threads", {}).values()):
            try:
                if thread and thread.isRunning():
                    thread.stop()
                    thread.wait(1000)
            except Exception:
                pass
        self.launch_threads.clear()
        if self.format_backup_thread and self.format_backup_thread.isRunning():
            self.format_backup_thread.wait(1000)
        
        # Perguntar se deseja fechar navegadores
        if self.browser_manager.active_browsers:
            reply = QMessageBox.question(
                self, "Fechar Navegadores",
                "Existem navegadores ativos. Deseja fechá-los?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.browser_manager.cleanup()
        
        event.accept()


# Teste do módulo
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # Aplicar estilo escuro básico
    app.setStyleSheet("""
        QWidget {
            background-color: #0f172a;
            color: #f1f5f9;
            font-family: 'Segoe UI', sans-serif;
        }
        QGroupBox {
            border: 1px solid rgba(6,182,212,0.15);
            border-radius: 8px;
            margin-top: 15px;
            padding-top: 20px;
        }
        QGroupBox::title {
            color: #22d3ee;
        }
        QLineEdit, QTextEdit, QListWidget, QComboBox, QSpinBox {
            background-color: #1e293b;
            border: 1px solid rgba(6,182,212,0.15);
            border-radius: 6px;
            padding: 8px;
        }
        QPushButton {
            background-color: #06b6d4;
            border: none;
            border-radius: 6px;
            padding: 10px 16px;
            color: white;
        }
        QPushButton:hover {
            background-color: #0891b2;
        }
    """)
    
    widget = BrowserWidget()
    widget.setWindowTitle("🌐 Navegador Seguro - Teste")
    widget.resize(900, 700)
    widget.show()
    
    sys.exit(app.exec_())

