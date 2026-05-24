"""
Widget do Bot Crunchyroll LOGIN para integração com Telegram Collector
Faz login em contas existentes e organiza resultados locais.

Versão 1.0 - Características:
- Login em contas existentes (email:senha)
- Cartoes como lista local/manual
- Suporte a 3 navegadores simultâneos
- Atualização automática de listas
"""

import os
import sys
import re
import subprocess
import threading
from datetime import datetime

from app.core.paths import BASE_DIR

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTextEdit, QGroupBox, QTabWidget, QSpinBox, QCheckBox,
    QMessageBox, QFileDialog, QGridLayout, QScrollArea,
    QFrame, QSplitter, QLineEdit, QApplication
)

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer

from PyQt5.QtGui import QFont, QColor

from app.features.crunchyroll.styles import (
    cr_button_qss, cr_checkbox_qss, cr_combo_qss, cr_compact_label_qss,
    cr_console_qss, cr_dependency_status_qss, cr_description_qss,
    cr_darken_color, cr_group_qss, cr_header_qss, cr_info_box_qss,
    cr_label_qss, cr_lighten_color, cr_line_edit_qss, cr_mono_value_qss,
    cr_scroll_area_qss, cr_small_button_qss, cr_spinbox_qss, cr_stat_qss,
    cr_status_qss, cr_subtle_group_qss, cr_tabs_qss, cr_text_edit_qss,
)


class BotLoginThread(QThread):
    """Thread para executar o bot de login"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)
    
    def __init__(self, bot_path, num_workers=3, proxy_config=None):
        super().__init__()
        self.bot_path = bot_path
        self.num_workers = num_workers
        self.proxy_config = proxy_config  # {'enabled': bool, 'host': str, 'port': str}
        self.process = None
        self._stop_requested = False
    
    def run(self):
        try:
            env = os.environ.copy()
            env['NUM_WORKERS'] = str(self.num_workers)
            
            # Configurar proxy via variáveis de ambiente
            if self.proxy_config and self.proxy_config.get('enabled'):
                env['PROXY_ENABLED'] = 'true'
                env['PROXY_HOST'] = self.proxy_config.get('host', '127.0.0.1')
                env['PROXY_PORT'] = self.proxy_config.get('port', '8888')
                env['PROXY_IGNORE_SSL'] = 'true'  # Necessário para Charles Proxy
                self.output_signal.emit(f"[PROXY] Configurado: {env['PROXY_HOST']}:{env['PROXY_PORT']}")

            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            
            self.process = subprocess.Popen(
                ['node', 'index.js'],
                cwd=self.bot_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.PIPE,
                env=env,
                bufsize=1,
                universal_newlines=True,
                creationflags=creationflags
            )
            
            for line in iter(self.process.stdout.readline, ''):
                if self._stop_requested:
                    break
                self.output_signal.emit(line.strip())
            
            self.process.wait()
            self.finished_signal.emit(self.process.returncode or 0)
            
        except Exception as e:
            self.error_signal.emit(str(e))
    
    def stop(self):
        self._stop_requested = True
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except Exception:
                try:
                    self.process.kill()
                except Exception:
                    pass


class InstallDependenciesThread(QThread):
    """Thread para instalar dependências"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, bot_path):
        super().__init__()
        self.bot_path = bot_path
    
    def run(self):
        try:
            self.output_signal.emit("[SISTEMA] Instalando dependências...")
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            
            # Detectar sistema operacional
            if sys.platform == 'win32':
                # No Windows, usar shell=True para encontrar npm
                npm_cmd = 'npm install'
                process = subprocess.Popen(
                    npm_cmd,
                    cwd=self.bot_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    shell=True,
                    creationflags=creationflags
                )
            else:
                # Linux/Mac
                process = subprocess.Popen(
                    ['npm', 'install'],
                    cwd=self.bot_path,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    universal_newlines=True,
                    creationflags=creationflags
                )
            
            for line in iter(process.stdout.readline, ''):
                self.output_signal.emit(line.strip())
            
            process.wait()
            
            if process.returncode == 0:
                self.finished_signal.emit(True, "Dependências instaladas com sucesso!")
            else:
                self.finished_signal.emit(False, "Erro ao instalar dependências. Verifique se o Node.js está instalado.")
                
        except FileNotFoundError:
            self.finished_signal.emit(False, "Node.js/npm não encontrado! Instale o Node.js em https://nodejs.org/")
        except Exception as e:
            self.finished_signal.emit(False, f"Erro: {str(e)}")


class CrunchyrollLoginWidget(QWidget):
    """Widget principal do Bot Crunchyroll LOGIN v1.0"""
    
    AUTO_REFRESH_INTERVAL = 60000  # 1 minuto
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bot_thread = None
        self.install_thread = None
        self.bot_path = os.path.join(str(BASE_DIR), 'crunchyroll_login_bot')
        self.dependencies_installed = False
        
        # Timer para atualização automática
        self._auto_refresh_timer = None
        self._auto_refresh_enabled = True
        
        self.init_ui()
        self.load_files()
        self.check_dependencies()
        
        # Iniciar timer de atualização automática
        self._setup_auto_refresh_timer()
    
    def check_dependencies(self):
        """Verifica se as dependências estão instaladas"""
        node_modules_path = os.path.join(self.bot_path, 'node_modules')
        self.dependencies_installed = os.path.exists(node_modules_path)
        self.update_dependency_status()
    
    def update_dependency_status(self):
        """Atualiza o status das dependências na interface"""
        if self.dependencies_installed:
            self.deps_status_label.setText("✅ Dependências instaladas")
            self.deps_status_label.setStyleSheet(cr_dependency_status_qss(True))
            self.install_deps_btn.setEnabled(False)
            self.install_deps_btn.setText("✅ Dependências OK")
        else:
            self.deps_status_label.setText("⚠️ Dependências NÃO instaladas")
            self.deps_status_label.setStyleSheet(cr_dependency_status_qss(False))
            self.install_deps_btn.setEnabled(True)
            self.install_deps_btn.setText("📦 Instalar Dependências")
    
    def get_group_style(self):
        return cr_group_qss()
    
    def get_button_style(self, color="#059669"):
        return cr_button_qss(color)
    
    def lighten_color(self, hex_color, factor=0.2):
        return cr_lighten_color(hex_color, factor)
    
    def init_ui(self):
        """Inicializa a interface"""
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # === HEADER ===
        header = QLabel("🔐 Crunchyroll Login")
        header.setStyleSheet(cr_header_qss())
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # Descrição
        desc = QLabel("Entra em contas existentes, registra o resultado e mantém cartões como controle local/manual.")
        desc.setStyleSheet(cr_description_qss())
        desc.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(desc)
        
        # === STATUS E CONTROLES ===
        control_group = QGroupBox("⚙️ Controles")
        control_group.setStyleSheet(self.get_group_style())
        control_layout = QVBoxLayout()
        
        # Status das dependências
        self.deps_status_label = QLabel("⏳ Verificando dependências...")
        control_layout.addWidget(self.deps_status_label)
        
        # Botões de controle
        btn_row = QHBoxLayout()
        
        self.install_deps_btn = QPushButton("📦 Instalar Dependências")
        self.install_deps_btn.setStyleSheet(self.get_button_style("#0891b2"))
        self.install_deps_btn.clicked.connect(self.install_dependencies)
        btn_row.addWidget(self.install_deps_btn)
        
        # Número de navegadores
        nav_label = QLabel("Navegadores:")
        nav_label.setStyleSheet(cr_label_qss("#f1f5f9", padding=0))
        btn_row.addWidget(nav_label)
        
        self.num_browsers_spin = QSpinBox()
        self.num_browsers_spin.setRange(1, 5)
        self.num_browsers_spin.setValue(3)
        self.num_browsers_spin.setStyleSheet(cr_spinbox_qss())
        btn_row.addWidget(self.num_browsers_spin)
        
        btn_row.addStretch()
        control_layout.addLayout(btn_row)
        
        # === CONFIGURAÇÃO DE PROXY (Charles Proxy) ===
        proxy_row = QHBoxLayout()
        
        self.proxy_checkbox = QCheckBox("Usar Proxy")
        self.proxy_checkbox.setStyleSheet(cr_checkbox_qss(size=12, color="#f1f5f9", indicator=14))
        self.proxy_checkbox.stateChanged.connect(self.toggle_proxy_fields)
        proxy_row.addWidget(self.proxy_checkbox)
        
        proxy_host_label = QLabel("Host:")
        proxy_host_label.setStyleSheet(cr_label_qss("#f1f5f9", padding=0))
        proxy_row.addWidget(proxy_host_label)
        
        self.proxy_host_input = QLineEdit()
        self.proxy_host_input.setText("127.0.0.1")
        self.proxy_host_input.setPlaceholderText("127.0.0.1")
        self.proxy_host_input.setEnabled(False)
        self.proxy_host_input.setStyleSheet(cr_line_edit_qss(100))
        proxy_row.addWidget(self.proxy_host_input)
        
        proxy_port_label = QLabel("Porta:")
        proxy_port_label.setStyleSheet(cr_label_qss("#f1f5f9", padding=0))
        proxy_row.addWidget(proxy_port_label)
        
        self.proxy_port_input = QLineEdit()
        self.proxy_port_input.setText("8888")
        self.proxy_port_input.setPlaceholderText("8888")
        self.proxy_port_input.setEnabled(False)
        self.proxy_port_input.setStyleSheet(cr_line_edit_qss(60))
        proxy_row.addWidget(self.proxy_port_input)
        
        # Botão de ajuda do Charles Proxy
        proxy_help_btn = QPushButton("❓")
        proxy_help_btn.setToolTip("Ajuda sobre Charles Proxy")
        proxy_help_btn.setStyleSheet(cr_button_qss("#0891b2"))
        proxy_help_btn.clicked.connect(self.show_proxy_help)
        proxy_row.addWidget(proxy_help_btn)
        
        proxy_row.addStretch()
        control_layout.addLayout(proxy_row)
        
        # Botões de ação
        action_row = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ Iniciar Bot")
        self.start_btn.setStyleSheet(self.get_button_style("#059669"))
        self.start_btn.clicked.connect(self.start_bot)
        action_row.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ Parar Bot")
        self.stop_btn.setStyleSheet(self.get_button_style("#da3633"))
        self.stop_btn.clicked.connect(self.stop_bot)
        self.stop_btn.setEnabled(False)
        action_row.addWidget(self.stop_btn)
        
        action_row.addStretch()
        
        # Status
        self.status_label = QLabel("⏸️ Bot parado")
        self.status_label.setStyleSheet(cr_status_qss("#94a3b8", 14))
        action_row.addWidget(self.status_label)
        
        control_layout.addLayout(action_row)
        control_group.setLayout(control_layout)
        main_layout.addWidget(control_group)
        
        # === TABS ===
        tabs = QTabWidget()
        tabs.setStyleSheet(cr_tabs_qss("quiet"))
        
        tabs.addTab(self.create_accounts_tab(), "📧 Contas")
        tabs.addTab(self.create_cards_tab(), "💳 Cartões")
        tabs.addTab(self.create_results_tab(), "📊 Resultados")
        tabs.addTab(self.create_console_tab(), "📝 Console")
        
        main_layout.addWidget(tabs)
        
        # === ESTATÍSTICAS ===
        stats_layout = QHBoxLayout()
        
        self.contas_label = QLabel("📧 Contas: 0")
        self.contas_label.setStyleSheet(cr_label_qss("#22d3ee"))
        stats_layout.addWidget(self.contas_label)
        
        self.cartoes_label = QLabel("💳 Cartões: 0")
        self.cartoes_label.setStyleSheet(cr_label_qss("#06b6d4"))
        stats_layout.addWidget(self.cartoes_label)
        
        self.premium_label = QLabel("✅ Premium: 0")
        self.premium_label.setStyleSheet(cr_label_qss("#10b981"))
        stats_layout.addWidget(self.premium_label)
        
        stats_layout.addStretch()
        main_layout.addLayout(stats_layout)
    
    def create_accounts_tab(self):
        """Cria a aba de contas para login"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        accounts_group = QGroupBox("📧 Contas para LOGIN (email:senha ou email|senha)")
        accounts_group.setStyleSheet(self.get_group_style())
        accounts_layout = QVBoxLayout()
        
        self.accounts_edit = QTextEdit()
        self.accounts_edit.setStyleSheet(cr_text_edit_qss("#f1f5f9"))
        self.accounts_edit.setPlaceholderText("Cole as contas aqui...\\nFormato: email:senha ou email|senha")
        accounts_layout.addWidget(self.accounts_edit)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Salvar Contas")
        save_btn.setStyleSheet(self.get_button_style("#059669"))
        save_btn.clicked.connect(self.save_accounts)
        btn_layout.addWidget(save_btn)
        
        load_btn = QPushButton("📂 Carregar Arquivo")
        load_btn.setStyleSheet(self.get_button_style("#0891b2"))
        load_btn.clicked.connect(self.load_accounts_file)
        btn_layout.addWidget(load_btn)
        
        refresh_btn = QPushButton("🔄 Atualizar (Remover Processadas)")
        refresh_btn.setStyleSheet(self.get_button_style("#06b6d4"))
        refresh_btn.clicked.connect(self.refresh_accounts_remove_used)
        btn_layout.addWidget(refresh_btn)
        
        accounts_layout.addLayout(btn_layout)
        accounts_group.setLayout(accounts_layout)
        layout.addWidget(accounts_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_cards_tab(self):
        """Cria a aba de cartões"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        info_label = QLabel(
            "Cartões aqui ficam salvos no projeto para controle manual e conferência de resultados. "
            "O verificador de login não depende deles."
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(cr_info_box_qss())
        layout.addWidget(info_label)

        cards_group = QGroupBox("💳 Cartões locais (numero|mes|ano|cvv)")
        cards_group.setStyleSheet(self.get_group_style())
        cards_layout = QVBoxLayout()

        self.cards_status_label = QLabel("Nenhum cartão carregado.")
        self.cards_status_label.setStyleSheet(cr_compact_label_qss())
        cards_layout.addWidget(self.cards_status_label)
        
        self.cards_edit = QTextEdit()
        self.cards_edit.setStyleSheet(cr_text_edit_qss("#f1f5f9"))
        self.cards_edit.setPlaceholderText("Cole cartões aqui para controle local...\\nFormato: numero|mes|ano|cvv")
        self.cards_edit.textChanged.connect(self.update_card_quality)
        cards_layout.addWidget(self.cards_edit)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Salvar cartões")
        save_btn.setStyleSheet(self.get_button_style("#059669"))
        save_btn.clicked.connect(self.save_cards)
        btn_layout.addWidget(save_btn)
        
        load_btn = QPushButton("📂 Carregar arquivo")
        load_btn.setStyleSheet(self.get_button_style("#0891b2"))
        load_btn.clicked.connect(self.load_cards_file)
        btn_layout.addWidget(load_btn)
        
        validate_btn = QPushButton("🧾 Conferir formato")
        validate_btn.setStyleSheet(self.get_button_style("#7c3aed"))
        validate_btn.clicked.connect(self.validate_cards_local)
        btn_layout.addWidget(validate_btn)
        
        refresh_btn = QPushButton("🔄 Remover usados dos resultados")
        refresh_btn.setStyleSheet(self.get_button_style("#06b6d4"))
        refresh_btn.clicked.connect(self.refresh_cards_remove_used)
        btn_layout.addWidget(refresh_btn)
        
        cards_layout.addLayout(btn_layout)
        cards_group.setLayout(cards_layout)
        layout.addWidget(cards_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_results_tab(self):
        """Cria a aba de resultados"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Resumo
        summary_group = QGroupBox("📈 Resumo")
        summary_group.setStyleSheet(self.get_group_style())
        summary_layout = QGridLayout()
        
        self.stat_login_ok = QLabel("✅ Login OK: 0")
        self.stat_login_ok.setStyleSheet(cr_stat_qss("#10b981"))
        summary_layout.addWidget(self.stat_login_ok, 0, 0)
        
        self.stat_login_fail = QLabel("❌ Login Falha: 0")
        self.stat_login_fail.setStyleSheet(cr_stat_qss("#f43f5e"))
        summary_layout.addWidget(self.stat_login_fail, 0, 1)
        
        self.stat_premium = QLabel("💎 Premium: 0")
        self.stat_premium.setStyleSheet(cr_stat_qss("#06b6d4"))
        summary_layout.addWidget(self.stat_premium, 1, 0)
        
        self.stat_cartoes_ok = QLabel("💳 Cartões Aprovados: 0")
        self.stat_cartoes_ok.setStyleSheet(cr_stat_qss("#10b981"))
        summary_layout.addWidget(self.stat_cartoes_ok, 1, 1)

        self.stat_review = QLabel("🟡 Revisar: 0")
        self.stat_review.setStyleSheet(cr_stat_qss("#f59e0b"))
        summary_layout.addWidget(self.stat_review, 2, 0)

        self.stat_no_card = QLabel("💳 Sem cartão: 0")
        self.stat_no_card.setStyleSheet(cr_stat_qss("#94a3b8"))
        summary_layout.addWidget(self.stat_no_card, 2, 1)
        
        summary_group.setLayout(summary_layout)
        layout.addWidget(summary_group)
        
        # Contas Premium
        premium_group = QGroupBox("💎 Contas Premium / aprovadas manualmente")
        premium_group.setStyleSheet(self.get_group_style())
        premium_layout = QVBoxLayout()
        
        self.premium_edit = QTextEdit()
        self.premium_edit.setReadOnly(True)
        self.premium_edit.setStyleSheet(cr_text_edit_qss("#10b981", "#059669"))
        self.premium_edit.setMaximumHeight(150)
        premium_layout.addWidget(self.premium_edit)
        
        premium_btn_layout = QHBoxLayout()
        
        copy_btn = QPushButton("📋 Copiar Tudo")
        copy_btn.setStyleSheet(self.get_button_style("#0891b2"))
        copy_btn.clicked.connect(self.copy_premium)
        premium_btn_layout.addWidget(copy_btn)
        
        copy_simple_btn = QPushButton("📋 Copiar email:senha")
        copy_simple_btn.setStyleSheet(self.get_button_style("#0891b2"))
        copy_simple_btn.clicked.connect(self.copy_premium_simple)
        premium_btn_layout.addWidget(copy_simple_btn)
        
        premium_btn_layout.addStretch()
        premium_layout.addLayout(premium_btn_layout)
        premium_group.setLayout(premium_layout)
        layout.addWidget(premium_group)

        details_group = QGroupBox("📋 Resultados detalhados")
        details_group.setStyleSheet(self.get_group_style())
        details_layout = QVBoxLayout()

        self.result_edits = {}
        detail_tabs = QTabWidget()
        detail_tabs.setStyleSheet(cr_tabs_qss("compact"))

        for key, title, color in [
            ("login_sucesso.txt", "Login OK", "#10b981"),
            ("login_revisar.txt", "Revisar", "#f59e0b"),
            ("login_falha.txt", "Login falha", "#f43f5e"),
            ("sem_cartao.txt", "Sem cartão", "#94a3b8"),
            ("sem_pagamento.txt", "Sem pagamento", "#94a3b8"),
            ("cartoes_aprovados.txt", "Cartões OK", "#10b981"),
            ("cartoes_falhos.txt", "Cartões falhos", "#f43f5e"),
        ]:
            edit = self._create_result_text(color)
            self.result_edits[key] = edit
            detail_tabs.addTab(edit, title)

        details_layout.addWidget(detail_tabs)
        details_group.setLayout(details_layout)
        layout.addWidget(details_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_console_tab(self):
        """Cria a aba de console"""
        tab = QWidget()
        layout = QVBoxLayout()
        
        console_group = QGroupBox("📝 Console de Saída")
        console_group.setStyleSheet(self.get_group_style())
        console_layout = QVBoxLayout()
        
        self.console_edit = QTextEdit()
        self.console_edit.setReadOnly(True)
        self.console_edit.setStyleSheet(cr_text_edit_qss("#f1f5f9", size=11))
        console_layout.addWidget(self.console_edit)
        
        btn_layout = QHBoxLayout()
        
        clear_btn = QPushButton("🗑️ Limpar Console")
        clear_btn.setStyleSheet(self.get_button_style("#1e293b"))
        clear_btn.clicked.connect(lambda: self.console_edit.clear())
        btn_layout.addWidget(clear_btn)
        
        btn_layout.addStretch()
        console_layout.addLayout(btn_layout)
        
        console_group.setLayout(console_layout)
        layout.addWidget(console_group)
        
        tab.setLayout(layout)
        return tab

    def _create_result_text(self, color="#f1f5f9"):
        """Cria uma caixa de resultado padronizada."""
        edit = QTextEdit()
        edit.setReadOnly(True)
        edit.setStyleSheet(f"""
            QTextEdit {{
                background-color: #0a0e1a;
                color: {color};
                font-family: 'Consolas', monospace;
                font-size: 12px;
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 8px;
                padding: 10px;
            }}
        """)
        edit.setMinimumHeight(170)
        return edit
    
    def load_files(self):
        """Carrega os arquivos de dados"""
        data_path = os.path.join(self.bot_path, 'data')
        
        # Contas
        contas_path = os.path.join(data_path, 'contas.txt')
        if os.path.exists(contas_path):
            with open(contas_path, 'r', encoding='utf-8') as f:
                self.accounts_edit.setText(f.read())
        
        # Cartões
        cartoes_path = os.path.join(data_path, 'cartoes.txt')
        if os.path.exists(cartoes_path):
            with open(cartoes_path, 'r', encoding='utf-8') as f:
                self.cards_edit.setText(f.read())
        
        self.load_results()
        self.update_stats()
    
    def load_results(self):
        """Carrega os resultados"""
        data_path = os.path.join(self.bot_path, 'data')

        def read_file(filename):
            filepath = os.path.join(data_path, filename)
            if not os.path.exists(filepath):
                return ""
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()

        def count_lines(text):
            return len([l for l in text.splitlines() if l.strip()])
        
        # Premium
        premium_content = read_file('contas_premium.txt')
        self.premium_edit.setText(premium_content)
        self.stat_premium.setText(f"💎 Premium: {count_lines(premium_content)}")
        
        # Login sucesso
        login_ok_count = count_lines(read_file('login_sucesso.txt'))
        self.stat_login_ok.setText(f"✅ Login OK: {login_ok_count}")
        
        # Login falha
        login_fail_count = count_lines(read_file('login_falha.txt'))
        self.stat_login_fail.setText(f"❌ Login Falha: {login_fail_count}")

        review_count = count_lines(read_file('login_revisar.txt'))
        self.stat_review.setText(f"🟡 Revisar: {review_count}")

        no_card_count = count_lines(read_file('sem_cartao.txt'))
        self.stat_no_card.setText(f"💳 Sem cartão: {no_card_count}")
        
        # Cartões aprovados
        cartoes_ok_count = count_lines(read_file('cartoes_aprovados.txt'))
        self.stat_cartoes_ok.setText(f"💳 Cartões Aprovados: {cartoes_ok_count}")

        for filename, edit in getattr(self, 'result_edits', {}).items():
            edit.setText(read_file(filename))
    
    def update_stats(self):
        """Atualiza as estatísticas"""
        contas_count = len([l for l in self.accounts_edit.toPlainText().split('\\n') if l.strip()])
        self.contas_label.setText(f"📧 Contas: {contas_count}")
        
        cartoes_count = len([l for l in self.cards_edit.toPlainText().split('\\n') if l.strip()])
        self.cartoes_label.setText(f"💳 Cartões: {cartoes_count}")
        self.update_card_quality()
        
        premium_count = len([l for l in self.premium_edit.toPlainText().split('\\n') if l.strip()])
        self.premium_label.setText(f"✅ Premium: {premium_count}")
    
    def _card_quality_counts(self):
        lines = [l.strip() for l in self.cards_edit.toPlainText().splitlines() if l.strip() and not l.strip().startswith('#')]
        valid = 0
        invalid = 0
        for line in lines:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                number = re.sub(r'\D', '', parts[0])
                month = re.sub(r'\D', '', parts[1])
                year = re.sub(r'\D', '', parts[2])
                cvv = re.sub(r'\D', '', parts[3])
                if 13 <= len(number) <= 19 and 1 <= len(month) <= 2 and len(year) in (2, 4) and 3 <= len(cvv) <= 4:
                    valid += 1
                else:
                    invalid += 1
            else:
                invalid += 1
        return len(lines), valid, invalid

    def update_card_quality(self):
        """Atualiza resumo visual dos cartões locais."""
        if not hasattr(self, 'cards_status_label'):
            return
        total, valid, invalid = self._card_quality_counts()
        if total == 0:
            self.cards_status_label.setText("Nenhum cartão carregado.")
            self.cards_status_label.setStyleSheet(cr_compact_label_qss())
            return
        color = "#10b981" if invalid == 0 else "#f59e0b"
        self.cards_status_label.setText(f"{total} cartões locais | {valid} com formato OK | {invalid} para revisar")
        self.cards_status_label.setStyleSheet(cr_compact_label_qss(color, bold=True))

    def validate_cards_local(self):
        """Confere apenas o formato local dos cartões."""
        total, valid, invalid = self._card_quality_counts()
        QMessageBox.information(
            self,
            "Conferência local",
            f"Cartões na lista: {total}\nFormato OK: {valid}\nPara revisar: {invalid}\n\nNada foi enviado para site externo."
        )
    
    def save_accounts(self, silent=False):
        """Salva as contas"""
        contas_path = os.path.join(self.bot_path, 'data', 'contas.txt')
        os.makedirs(os.path.dirname(contas_path), exist_ok=True)
        
        with open(contas_path, 'w', encoding='utf-8') as f:
            f.write(self.accounts_edit.toPlainText())
        
        self.update_stats()
        if not silent:
            QMessageBox.information(self, "Sucesso", "Contas salvas com sucesso!")
    
    def save_cards(self, silent=False):
        """Salva os cartões"""
        cartoes_path = os.path.join(self.bot_path, 'data', 'cartoes.txt')
        os.makedirs(os.path.dirname(cartoes_path), exist_ok=True)
        
        with open(cartoes_path, 'w', encoding='utf-8') as f:
            f.write(self.cards_edit.toPlainText())
        
        self.update_stats()
        if not silent:
            QMessageBox.information(self, "Sucesso", "Cartões salvos localmente!")
    
    def load_accounts_file(self):
        """Carrega contas de arquivo"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Carregar Contas", "", "Text Files (*.txt);;All Files (*)")
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [l for l in content.split('\\n') if l.strip() and not l.strip().startswith('#')]
                current = self.accounts_edit.toPlainText()
                if current.strip():
                    self.accounts_edit.setText(current + '\\n' + '\\n'.join(lines))
                else:
                    self.accounts_edit.setText('\\n'.join(lines))
            self.update_stats()
    
    def load_cards_file(self):
        """Carrega cartões de arquivo"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Carregar Cartões", "", "Text Files (*.txt);;All Files (*)")
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [l for l in content.split('\\n') if l.strip() and not l.strip().startswith('#')]
                current = self.cards_edit.toPlainText()
                if current.strip():
                    self.cards_edit.setText(current + '\\n' + '\\n'.join(lines))
                else:
                    self.cards_edit.setText('\\n'.join(lines))
            self.update_stats()
    
    def copy_premium(self):
        """Copia contas premium"""

        text = self.premium_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Sucesso", "Contas premium copiadas!")
    
    def copy_premium_simple(self):
        """Copia contas premium no formato simples"""

        
        simple_path = os.path.join(self.bot_path, 'data', 'contas_premium_simples.txt')
        if os.path.exists(simple_path):
            with open(simple_path, 'r', encoding='utf-8') as f:
                text = f.read()
            if text.strip():
                QApplication.clipboard().setText(text)
                QMessageBox.information(self, "Sucesso", "Contas copiadas!")
                return
        
        QMessageBox.warning(self, "Aviso", "Nenhuma conta para copiar!")
    
    def install_dependencies(self):
        """Instala dependências"""
        reply = QMessageBox.question(
            self, "Instalar Dependências",
            "Isso irá executar 'npm install'.\\n\\nDeseja continuar?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.install_deps_btn.setEnabled(False)
            self.install_deps_btn.setText("⏳ Instalando...")
            
            self.install_thread = InstallDependenciesThread(self.bot_path)
            self.install_thread.output_signal.connect(self.append_console)
            self.install_thread.finished_signal.connect(self.install_finished)
            self.install_thread.start()
    
    def install_finished(self, success, message):
        """Callback de instalação"""
        if success:
            self.dependencies_installed = True
            self.update_dependency_status()
            QMessageBox.information(self, "Sucesso", message)
        else:
            self.install_deps_btn.setEnabled(True)
            self.install_deps_btn.setText("📦 Instalar Dependências")
            QMessageBox.critical(self, "Erro", message)
    
    def start_bot(self):
        """Inicia o bot"""
        if not self.accounts_edit.toPlainText().strip():
            QMessageBox.warning(self, "Aviso", "Adicione contas antes de iniciar!")
            return
        
        if not self.dependencies_installed:
            reply = QMessageBox.question(
                self, "Dependências",
                "Dependências não instaladas. Instalar agora?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.install_dependencies()
            return
        
        # Salvar arquivos
        self.save_accounts(silent=True)
        self.save_cards(silent=True)
        
        # Iniciar bot
        num_workers = self.num_browsers_spin.value()
        
        # Configurar proxy
        proxy_config = None
        if self.proxy_checkbox.isChecked():
            proxy_config = {
                'enabled': True,
                'host': self.proxy_host_input.text().strip() or '127.0.0.1',
                'port': self.proxy_port_input.text().strip() or '8888'
            }
        
        self.bot_thread = BotLoginThread(self.bot_path, num_workers, proxy_config)
        self.bot_thread.output_signal.connect(self.append_console)
        self.bot_thread.finished_signal.connect(self.bot_finished)
        self.bot_thread.error_signal.connect(self.bot_error)
        self.bot_thread.start()
        
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.num_browsers_spin.setEnabled(False)
        self.status_label.setText(f"▶️ Bot rodando ({num_workers} navegadores)")
        self.status_label.setStyleSheet(cr_status_qss("#10b981", 14))
        
        self.append_console(f"[SISTEMA] Bot iniciado com {num_workers} navegadores")
    
    def stop_bot(self):
        """Para o bot"""
        if self.bot_thread:
            self.bot_thread.stop()
            self.append_console("[SISTEMA] Parando bot...")
    
    def bot_finished(self, return_code):
        """Callback de finalização"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.num_browsers_spin.setEnabled(True)
        self.status_label.setText("⏸️ Bot parado")
        self.status_label.setStyleSheet(cr_status_qss("#94a3b8", 14))
        
        self.append_console(f"[SISTEMA] Bot finalizado (código: {return_code})")
        self.load_results()
    
    def bot_error(self, error):
        """Callback de erro"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.num_browsers_spin.setEnabled(True)
        self.status_label.setText("❌ Erro no bot")
        self.status_label.setStyleSheet(cr_status_qss("#da3633", 14))
        
        self.append_console(f"[ERRO] {error}")
        QMessageBox.critical(self, "Erro", error)
    
    def append_console(self, text):
        """Adiciona texto ao console"""
        self.console_edit.append(text)
        
        # Atualizar resultados se necessário
        text_lower = text.lower()
        if any(k in text_lower for k in ['premium', 'aprovado', 'sucesso', 'login ok', 'revisao', 'revisar', 'falhou']):
            self.load_results()
    
    def refresh_accounts_remove_used(self):
        """Remove contas já processadas"""
        data_path = os.path.join(self.bot_path, 'data')
        
        emails_usados = set()
        
        arquivos = ['login_sucesso.txt', 'login_falha.txt', 'login_revisar.txt', 'contas_premium.txt', 'sem_pagamento.txt', 'ja_assinante.txt']
        
        for arquivo in arquivos:
            filepath = os.path.join(data_path, arquivo)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha = linha.strip()
                        if linha and '@' in linha:
                            partes = re.split(r'[:|,\\s]+', linha)
                            for parte in partes:
                                if '@' in parte:
                                    emails_usados.add(parte.lower().strip())
                                    break
        
        if not emails_usados:
            QMessageBox.information(self, "Info", "Nenhuma conta processada encontrada.")
            return
        
        contas_atuais = self.accounts_edit.toPlainText().strip().split('\\n')
        contas_filtradas = []
        removidas = 0
        
        for conta in contas_atuais:
            conta = conta.strip()
            if not conta:
                continue
            
            partes = re.split(r'[:|]+', conta)
            if len(partes) >= 1 and '@' in partes[0]:
                email = partes[0].lower().strip()
                if email in emails_usados:
                    removidas += 1
                else:
                    contas_filtradas.append(conta)
            else:
                contas_filtradas.append(conta)
        
        self.accounts_edit.setText('\\n'.join(contas_filtradas))
        self.update_stats()
        
        QMessageBox.information(self, "Atualização", f"Removidas {removidas} contas processadas.\\nRestantes: {len(contas_filtradas)}")
    
    def refresh_cards_remove_used(self):
        """Remove cartões já utilizados"""
        data_path = os.path.join(self.bot_path, 'data')
        
        cartoes_usados = set()
        
        arquivos = ['cartoes_aprovados.txt', 'cartoes_falhos.txt']
        
        for arquivo in arquivos:
            filepath = os.path.join(data_path, arquivo)
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    for linha in f:
                        linha = linha.strip()
                        if linha:
                            partes = re.split(r'[|:,\\s]+', linha)
                            if partes:
                                numero = re.sub(r'\\D', '', partes[0])
                                if len(numero) >= 13:
                                    cartoes_usados.add(numero)
        
        if not cartoes_usados:
            QMessageBox.information(self, "Info", "Nenhum cartão utilizado encontrado.")
            return
        
        cartoes_atuais = self.cards_edit.toPlainText().strip().split('\\n')
        cartoes_filtrados = []
        removidos = 0
        
        for cartao in cartoes_atuais:
            cartao = cartao.strip()
            if not cartao:
                continue
            
            partes = re.split(r'[|:]+', cartao)
            if partes:
                numero = re.sub(r'\\D', '', partes[0])
                if numero in cartoes_usados:
                    removidos += 1
                else:
                    cartoes_filtrados.append(cartao)
            else:
                cartoes_filtrados.append(cartao)
        
        self.cards_edit.setText('\\n'.join(cartoes_filtrados))
        self.update_stats()
        
        QMessageBox.information(self, "Atualização", f"Removidos {removidos} cartões utilizados.\\nRestantes: {len(cartoes_filtrados)}")
    
    def _setup_auto_refresh_timer(self):
        """Configura timer de atualização automática"""
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(self._auto_refresh_callback)
        self._auto_refresh_timer.start(self.AUTO_REFRESH_INTERVAL)
    
    def _auto_refresh_callback(self):
        """Callback de atualização automática"""
        if not self._auto_refresh_enabled:
            return
        
        if self.bot_thread and self.bot_thread.isRunning():
            self._perform_auto_refresh()
    
    def _perform_auto_refresh(self):
        """Executa atualização automática"""
        try:
            self.load_results()
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.append_console(f"[AUTO-REFRESH] {timestamp} - Resultados atualizados")
        except Exception as e:
            pass

    def toggle_proxy_fields(self, state):
        """Habilita/desabilita campos de proxy"""
        enabled = state == Qt.Checked
        self.proxy_host_input.setEnabled(enabled)
        self.proxy_port_input.setEnabled(enabled)
    
    def show_proxy_help(self):
        """Mostra ajuda sobre configuração de proxy"""
        help_text = """
<h2>🔐 Configuração de Proxy (Charles Proxy)</h2>

<h3>O que é o Charles Proxy?</h3>
<p>Charles Proxy é uma ferramenta de depuração HTTP que permite interceptar, 
visualizar e modificar o tráfego de rede entre seu computador e a internet.</p>

<h3>Como usar com o Bot:</h3>
<ol>
<li><b>Instale o Charles Proxy</b> - Baixe em <a href="https://www.charlesproxy.com/">charlesproxy.com</a></li>
<li><b>Inicie o Charles Proxy</b> - Ele escuta por padrão na porta 8888</li>
<li><b>Marque "Usar Proxy"</b> no bot</li>
<li><b>Configure Host e Porta</b>:
   <ul>
   <li>Host: 127.0.0.1 (localhost)</li>
   <li>Porta: 8888 (padrão do Charles)</li>
   </ul>
</li>
<li><b>Inicie o Bot</b> - O tráfego será capturado pelo Charles</li>
</ol>

<h3>Configuração SSL no Charles:</h3>
<p>Para capturar tráfego HTTPS:</p>
<ol>
<li>Vá em <b>Proxy → SSL Proxying Settings</b></li>
<li>Marque <b>Enable SSL Proxying</b></li>
<li>Adicione <b>*.crunchyroll.com</b> na lista de hosts</li>
<li>Instale o certificado do Charles no sistema</li>
</ol>

<h3>Usando outros proxies:</h3>
<p>Você pode usar qualquer proxy HTTP/HTTPS:</p>
<ul>
<li><b>Burp Suite</b>: porta padrão 8080</li>
<li><b>Fiddler</b>: porta padrão 8888</li>
<li><b>mitmproxy</b>: porta padrão 8080</li>
<li><b>Proxy externo</b>: configure host e porta do servidor</li>
</ul>

<h3>⚠️ Importante:</h3>
<ul>
<li>O proxy deve estar rodando ANTES de iniciar o bot</li>
<li>Erros de SSL são ignorados automaticamente</li>
<li>Use apenas para fins de depuração e desenvolvimento</li>
</ul>
"""
        
        msg = QMessageBox(self)
        msg.setWindowTitle("Ajuda - Configuração de Proxy")
        msg.setTextFormat(Qt.RichText)
        msg.setText(help_text)
        msg.setIcon(QMessageBox.Information)
        msg.setStyleSheet("""
            QMessageBox {
                background-color: #0a0e1a;
            }
            QMessageBox QLabel {
                color: #f1f5f9;
                font-size: 12px;
            }
        """)
        msg.exec_()

