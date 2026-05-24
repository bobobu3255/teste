"""
Widget do Bot Crunchyroll para integração com Telegram Collector
Permite iniciar e controlar o bot Crunchyroll diretamente da interface

Versão 9.2 - Melhorias:
- Console avançado com filtros e cores
- Configuração de Proxy PyProxy rotativa
- IP único por conta criada
- Limite de 3 cartões por conta
- Remoção automática de contas/cartões após teste
- Tratamento robusto de erros (bot não para mais)
- Verificador de Assinatura corrigido
- Botão "Copiar email:senha" nos resultados
"""
import os
import sys
import subprocess
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from app.core.paths import BASE_DIR

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QTextEdit, QGroupBox, QFileDialog, QMessageBox, QLineEdit,
    QSpinBox, QCheckBox, QProgressBar, QTabWidget, QScrollArea,
    QFrame, QSplitter, QGridLayout, QComboBox, QPlainTextEdit, QApplication
)

from PyQt5.QtCore import Qt, QThread, pyqtSignal, QProcess, QTimer

from PyQt5.QtGui import QFont, QTextCursor, QColor, QTextCharFormat

from app.features.crunchyroll.styles import (
    cr_button_qss, cr_checkbox_qss, cr_combo_qss, cr_compact_label_qss,
    cr_console_qss, cr_dependency_status_qss, cr_description_qss,
    cr_darken_color, cr_group_qss, cr_header_qss, cr_info_box_qss,
    cr_label_qss, cr_lighten_color, cr_line_edit_qss, cr_mono_value_qss,
    cr_scroll_area_qss, cr_small_button_qss, cr_spinbox_qss, cr_stat_qss,
    cr_status_qss, cr_subtle_group_qss, cr_tabs_qss, cr_text_edit_qss,
)


def _resolve_command(*names):
    for name in names:
        path = shutil.which(name)
        if path:
            return path
    return names[0] if names else ""


def _hidden_subprocess_kwargs():
    if sys.platform != 'win32':
        return {}

    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return {
        'startupinfo': startupinfo,
        'creationflags': getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    }


def _find_chrome_executable():
    candidates = []
    if sys.platform == 'win32':
        local = os.environ.get('LOCALAPPDATA', '')
        program_files = os.environ.get('ProgramFiles', r'C:\Program Files')
        program_files_x86 = os.environ.get('ProgramFiles(x86)', r'C:\Program Files (x86)')
        user_profile = os.environ.get('USERPROFILE', '')
        candidates.extend([
            os.path.join(program_files, 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(program_files_x86, 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(local, 'Google', 'Chrome', 'Application', 'chrome.exe'),
            os.path.join(program_files, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
            os.path.join(program_files_x86, 'Microsoft', 'Edge', 'Application', 'msedge.exe'),
        ])
        if user_profile:
            cache_dir = os.path.join(user_profile, '.cache', 'puppeteer', 'chrome')
            if os.path.isdir(cache_dir):
                for root, _, files in os.walk(cache_dir):
                    if 'chrome.exe' in files:
                        candidates.append(os.path.join(root, 'chrome.exe'))
    else:
        for name in ('google-chrome', 'chromium', 'chromium-browser'):
            path = shutil.which(name)
            if path:
                candidates.append(path)

    for path in candidates:
        if path and os.path.exists(path):
            return path
    return ''


def _node_env():
    env = os.environ.copy()
    if sys.platform == 'win32':
        env['PYTHONIOENCODING'] = 'utf-8'
        env['PYTHONUTF8'] = '1'

    chrome_path = env.get('PUPPETEER_EXECUTABLE_PATH') or _find_chrome_executable()
    if chrome_path:
        env['PUPPETEER_EXECUTABLE_PATH'] = chrome_path
    return env


class InstallDependenciesThread(QThread):
    """Thread para instalar dependências do Node.js"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str)
    
    def __init__(self, bot_path, parent=None):
        super().__init__(parent)
        self.bot_path = bot_path
    
    def run(self):
        try:
            self.output_signal.emit("[INSTALAÇÃO] Iniciando instalação das dependências...")
            self.output_signal.emit("[INSTALAÇÃO] Executando: npm install")
            
            env = _node_env()
            
            npm_cmd = _resolve_command('npm.cmd', 'npm') if sys.platform == 'win32' else _resolve_command('npm')
            
            process = subprocess.Popen(
                [npm_cmd, 'install'],
                cwd=self.bot_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                **_hidden_subprocess_kwargs()
            )
            
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                
                try:
                    decoded_line = line.decode('utf-8', errors='replace').rstrip()
                except AttributeError:
                    decoded_line = line.rstrip() if isinstance(line, str) else str(line).rstrip()
                
                if decoded_line:
                    self.output_signal.emit(f"[NPM] {decoded_line}")
            
            process.stdout.close()
            return_code = process.wait()
            
            if return_code == 0:
                self.output_signal.emit("[INSTALAÇÃO] ✅ Dependências instaladas com sucesso!")
                self.finished_signal.emit(True, "Dependências instaladas com sucesso!")
            else:
                self.output_signal.emit(f"[INSTALAÇÃO] ❌ Erro na instalação (código: {return_code})")
                self.finished_signal.emit(False, f"Erro na instalação (código: {return_code})")
                
        except FileNotFoundError:
            self.output_signal.emit("[ERRO] npm não encontrado! Instale o Node.js primeiro.")
            self.finished_signal.emit(False, "npm não encontrado! Instale o Node.js primeiro.")
        except Exception as e:
            self.output_signal.emit(f"[ERRO] {str(e)}")
            self.finished_signal.emit(False, str(e))


class CrunchyrollBotThread(QThread):
    """Thread para executar o bot Crunchyroll"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)
    dependencies_missing = pyqtSignal()
    
    def __init__(self, bot_path, num_workers=3, proxy_config=None, parent=None):
        super().__init__(parent)
        self.bot_path = bot_path
        self.num_workers = num_workers
        self.proxy_config = proxy_config or {}
        self.process = None
        self._stop_requested = False
    
    def run(self):
        try:
            env = _node_env()
            
            # Configurar número de workers
            env['NUM_WORKERS'] = str(self.num_workers)
            
            # Configurar proxy se habilitado
            if self.proxy_config.get('enabled'):
                env['PROXY_ENABLED'] = 'true'
                env['PROXY_HOST'] = self.proxy_config.get('host', '')
                env['PROXY_PORT'] = str(self.proxy_config.get('port', 0))
                env['PROXY_USERNAME'] = self.proxy_config.get('username', '')
                env['PROXY_PASSWORD'] = self.proxy_config.get('password', '')
                env['PROXY_TYPE'] = self.proxy_config.get('type', 'http')
                env['PROXY_COUNTRY'] = self.proxy_config.get('country', 'BR')
                env['PROXY_UNIQUE_IP'] = 'true'
                env['PROXY_FULL_STRING'] = self.proxy_config.get('full_string', '')
                self.output_signal.emit(f"[PROXY] Proxy configurado: {self.proxy_config.get('host')}:{self.proxy_config.get('port')}")
                self.output_signal.emit(f"[PROXY] País: {self.proxy_config.get('country')} | IP único por conta: Ativado")
            
            # Verificar Node.js
            node_cmd = _resolve_command('node.exe', 'node') if sys.platform == 'win32' else _resolve_command('node')
            node_check = subprocess.run(
                [node_cmd, '--version'], 
                capture_output=True, 
                text=True, 
                encoding='utf-8',
                errors='replace',
                **_hidden_subprocess_kwargs()
            )
            if node_check.returncode != 0:
                self.error_signal.emit("Node.js não encontrado! Instale o Node.js primeiro.")
                return
            
            self.output_signal.emit(f"[INFO] Node.js {node_check.stdout.strip()} encontrado")
            self.output_signal.emit(f"[INFO] Usando {self.num_workers} navegador(es) simultâneo(s)")
            if env.get('PUPPETEER_EXECUTABLE_PATH'):
                self.output_signal.emit(f"[INFO] Navegador: {env['PUPPETEER_EXECUTABLE_PATH']}")
            
            # Verificar node_modules
            node_modules_path = os.path.join(self.bot_path, 'node_modules')
            if not os.path.exists(node_modules_path):
                self.output_signal.emit("[AVISO] Dependências não instaladas!")
                self.output_signal.emit("[AVISO] Clique em 'Instalar Dependências' primeiro.")
                self.dependencies_missing.emit()
                return

            puppeteer_check = subprocess.run(
                [node_cmd, '-e', "import puppeteer from 'puppeteer'; console.log(puppeteer.executablePath());"],
                cwd=self.bot_path,
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                env=env,
                **_hidden_subprocess_kwargs()
            )
            if puppeteer_check.returncode != 0:
                self.output_signal.emit("[AVISO] Puppeteer quebrado ou incompleto.")
                self.output_signal.emit(puppeteer_check.stderr.strip() or puppeteer_check.stdout.strip())
                self.dependencies_missing.emit()
                return
            
            self.output_signal.emit(f"[INFO] Iniciando bot em: {self.bot_path}")
            
            self.process = subprocess.Popen(
                [node_cmd, 'index.js'],
                cwd=self.bot_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                **_hidden_subprocess_kwargs()
            )
            
            while True:
                if self._stop_requested:
                    break
                
                line = self.process.stdout.readline()
                if not line:
                    break
                
                try:
                    decoded_line = line.decode('utf-8', errors='replace').rstrip()
                except AttributeError:
                    decoded_line = line.rstrip() if isinstance(line, str) else str(line).rstrip()
                
                if decoded_line:
                    self.output_signal.emit(decoded_line)
            
            self.process.stdout.close()
            return_code = self.process.wait()
            self.finished_signal.emit(return_code)
            
        except FileNotFoundError:
            self.error_signal.emit("Node.js não encontrado! Instale o Node.js primeiro.")
        except Exception as e:
            self.error_signal.emit(f"Erro ao executar bot: {str(e)}")
    
    def stop(self):
        self._stop_requested = True
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


class VerificadorThread(QThread):
    """Thread para executar o verificador de assinatura"""
    output_signal = pyqtSignal(str)
    finished_signal = pyqtSignal(int)
    error_signal = pyqtSignal(str)
    result_signal = pyqtSignal(dict)
    
    def __init__(self, bot_path, accounts, proxy_config=None, parent=None):
        super().__init__(parent)
        self.bot_path = bot_path
        self.accounts = accounts
        self.proxy_config = proxy_config or {}
        self.process = None
        self._stop_requested = False
    
    def run(self):
        try:
            env = _node_env()
            
            # Configurar proxy se habilitado
            if self.proxy_config.get('enabled'):
                env['PROXY_ENABLED'] = 'true'
                env['PROXY_HOST'] = self.proxy_config.get('host', '')
                env['PROXY_PORT'] = str(self.proxy_config.get('port', 0))
                env['PROXY_USERNAME'] = self.proxy_config.get('username', '')
                env['PROXY_PASSWORD'] = self.proxy_config.get('password', '')
                env['PROXY_FULL_STRING'] = self.proxy_config.get('full_string', '')
                self.output_signal.emit(f"[PROXY] Usando proxy: {self.proxy_config.get('host')}:{self.proxy_config.get('port')}")
            
            # Salvar contas para verificar
            verificar_path = os.path.join(self.bot_path, 'data', 'verificar.txt')
            os.makedirs(os.path.dirname(verificar_path), exist_ok=True)
            with open(verificar_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(self.accounts))
            
            self.output_signal.emit(f"[VERIFICADOR] Iniciando verificação de {len(self.accounts)} conta(s)...")
            
            # Verificar Node.js
            node_cmd = _resolve_command('node.exe', 'node') if sys.platform == 'win32' else _resolve_command('node')
            node_check = subprocess.run(
                [node_cmd, '--version'],
                capture_output=True,
                text=True,
                encoding='utf-8',
                errors='replace',
                **_hidden_subprocess_kwargs()
            )
            if node_check.returncode != 0:
                self.error_signal.emit("Node.js não encontrado! Instale o Node.js primeiro.")
                return

            node_modules_path = os.path.join(self.bot_path, 'node_modules')
            if not os.path.exists(node_modules_path):
                self.error_signal.emit("Dependências do bot não encontradas. Clique em 'Instalar Dependências' no Crunchyroll.")
                return
            
            self.process = subprocess.Popen(
                [node_cmd, 'verificador.js'],
                cwd=self.bot_path,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                env=env,
                **_hidden_subprocess_kwargs()
            )
            
            while True:
                if self._stop_requested:
                    break
                
                line = self.process.stdout.readline()
                if not line:
                    break
                
                try:
                    decoded_line = line.decode('utf-8', errors='replace').rstrip()
                except AttributeError:
                    decoded_line = line.rstrip() if isinstance(line, str) else str(line).rstrip()
                
                if decoded_line:
                    self.output_signal.emit(decoded_line)
            
            self.process.stdout.close()
            return_code = self.process.wait()
            
            # Ler resultados
            results = self.read_results()
            self.result_signal.emit(results)
            self.finished_signal.emit(return_code)
            
        except FileNotFoundError:
            self.error_signal.emit("Node.js não encontrado! Instale o Node.js primeiro.")
        except Exception as e:
            self.error_signal.emit(f"Erro ao executar verificador: {str(e)}")
    
    def read_results(self):
        """Lê os resultados do verificador"""
        results = {
            'completed': [],
            'failed': [],
            'login_failed': [],
            'no_payment': [],
            'invalid_email': [],
            'rate_limited': []
        }
        
        data_path = os.path.join(self.bot_path, 'data')
        
        # Completed
        completed_path = os.path.join(data_path, 'verificador_completed.txt')
        if os.path.exists(completed_path):
            with open(completed_path, 'r', encoding='utf-8') as f:
                results['completed'] = [l.strip() for l in f.readlines() if l.strip()]
        
        # Failed
        failed_path = os.path.join(data_path, 'verificador_failed.txt')
        if os.path.exists(failed_path):
            with open(failed_path, 'r', encoding='utf-8') as f:
                results['failed'] = [l.strip() for l in f.readlines() if l.strip()]
        
        # Login Failed
        login_failed_path = os.path.join(data_path, 'verificador_login_failed.txt')
        if os.path.exists(login_failed_path):
            with open(login_failed_path, 'r', encoding='utf-8') as f:
                results['login_failed'] = [l.strip() for l in f.readlines() if l.strip()]
        
        # No Payment
        no_payment_path = os.path.join(data_path, 'verificador_no_payment.txt')
        if os.path.exists(no_payment_path):
            with open(no_payment_path, 'r', encoding='utf-8') as f:
                results['no_payment'] = [l.strip() for l in f.readlines() if l.strip()]

        invalid_email_path = os.path.join(data_path, 'verificador_invalid_email.txt')
        if os.path.exists(invalid_email_path):
            with open(invalid_email_path, 'r', encoding='utf-8') as f:
                results['invalid_email'] = [l.strip() for l in f.readlines() if l.strip()]

        rate_limited_path = os.path.join(data_path, 'verificador_rate_limited.txt')
        if os.path.exists(rate_limited_path):
            with open(rate_limited_path, 'r', encoding='utf-8') as f:
                results['rate_limited'] = [l.strip() for l in f.readlines() if l.strip()]
        
        return results
    
    def stop(self):
        self._stop_requested = True
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()


class AdvancedConsole(QWidget):
    """Console avançado com filtros, cores e funcionalidades extras
    
    OTIMIZAÇÕES v9.1:
    - Limite máximo de linhas para evitar acumulação de memória
    - Batch update para evitar travamentos
    - Limpeza automática quando atinge o limite
    """
    
    # Limite máximo de linhas no console (evita travamentos)
    MAX_LOG_ENTRIES = 1000
    # Quantidade de linhas a remover quando atinge o limite
    CLEANUP_BATCH_SIZE = 300
    # Intervalo mínimo entre atualizações de UI (ms)
    MIN_UPDATE_INTERVAL = 50
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.log_entries = []
        self.filter_level = "ALL"
        self._pending_logs = []  # Buffer para batch updates
        self._last_update_time = 0
        self._update_timer = None
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de ferramentas do console
        toolbar = QHBoxLayout()
        
        # Filtro de nível
        filter_label = QLabel("Filtro:")
        filter_label.setStyleSheet(cr_label_qss())
        toolbar.addWidget(filter_label)
        
        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["Todos", "Info", "Sucesso", "Aviso", "Erro", "Conta", "Cartão", "Proxy", "Verificador"])
        self.filter_combo.setStyleSheet(cr_combo_qss())
        self.filter_combo.currentTextChanged.connect(self.apply_filter)
        toolbar.addWidget(self.filter_combo)
        
        # Checkbox auto-scroll
        self.auto_scroll_check = QCheckBox("Auto-scroll")
        self.auto_scroll_check.setChecked(True)
        self.auto_scroll_check.setStyleSheet(cr_checkbox_qss(size=12, color="#94a3b8", indicator=14))
        toolbar.addWidget(self.auto_scroll_check)
        
        # Contador de linhas
        self.line_count_label = QLabel("Linhas: 0")
        self.line_count_label.setStyleSheet(cr_label_qss("#6e7681", size=11, padding=0))
        toolbar.addWidget(self.line_count_label)
        
        toolbar.addStretch()
        
        # Botão exportar
        export_btn = QPushButton("📥 Exportar")
        export_btn.setStyleSheet(cr_small_button_qss(False))
        export_btn.clicked.connect(self.export_log)
        toolbar.addWidget(export_btn)
        
        # Botão limpar
        clear_btn = QPushButton("🗑️ Limpar")
        clear_btn.setStyleSheet(cr_small_button_qss(True))
        clear_btn.clicked.connect(self.clear_console)
        toolbar.addWidget(clear_btn)
        
        layout.addLayout(toolbar)
        
        # Console de texto
        self.console_text = QTextEdit()
        self.console_text.setReadOnly(True)
        self.console_text.setStyleSheet(cr_console_qss())
        self.console_text.setMinimumHeight(300)
        layout.addWidget(self.console_text)
        
        # Estatísticas rápidas
        stats_layout = QHBoxLayout()
        
        self.stats_info = QLabel("📊 Info: 0")
        self.stats_success = QLabel("✅ Sucesso: 0")
        self.stats_warning = QLabel("⚠️ Avisos: 0")
        self.stats_error = QLabel("❌ Erros: 0")
        
        for label in [self.stats_info, self.stats_success, self.stats_warning, self.stats_error]:
            label.setStyleSheet(cr_label_qss("#6e7681", size=11, padding=2))
            stats_layout.addWidget(label)
        
        stats_layout.addStretch()
        layout.addLayout(stats_layout)
        
        self.setLayout(layout)
        
        # Contadores
        self.counts = {'info': 0, 'success': 0, 'warning': 0, 'error': 0}
    
    def append(self, text):
        """Adiciona texto ao console com formatação - OTIMIZADO v9.1
        
        Otimizações:
        - Batch updates para evitar travamentos
        - Limite máximo de linhas com limpeza automática
        - Throttling de atualizações de UI
        """
        import time
        
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Determinar tipo e cor
        log_type, color = self.get_log_type_and_color(text)
        
        # Armazenar entrada
        entry = {
            'timestamp': timestamp,
            'text': text,
            'type': log_type,
            'color': color
        }
        self.log_entries.append(entry)
        
        # OTIMIZAÇÃO: Limpar entradas antigas se exceder o limite
        if len(self.log_entries) > self.MAX_LOG_ENTRIES:
            # Remover as entradas mais antigas
            entries_to_remove = self.CLEANUP_BATCH_SIZE
            self.log_entries = self.log_entries[entries_to_remove:]
            
            # Reconstruir o console (mais eficiente que remover linha por linha)
            self._rebuild_console()
        
        # Atualizar contadores
        if log_type == 'error':
            self.counts['error'] += 1
        elif log_type == 'success':
            self.counts['success'] += 1
        elif log_type == 'warning':
            self.counts['warning'] += 1
        else:
            self.counts['info'] += 1
        
        # OTIMIZAÇÃO: Throttle updates - não atualizar UI muito frequentemente
        current_time = time.time() * 1000  # em ms
        time_since_last_update = current_time - self._last_update_time
        
        if time_since_last_update < self.MIN_UPDATE_INTERVAL:
            # Adicionar ao buffer e agendar atualização
            self._pending_logs.append(entry)
            if self._update_timer is None:
                self._update_timer = QTimer.singleShot(
                    self.MIN_UPDATE_INTERVAL, 
                    self._flush_pending_logs
                )
            return
        
        # Atualizar imediatamente
        self._last_update_time = current_time
        self._add_entry_to_console(entry)
        self.update_stats()
        self.line_count_label.setText(f"Linhas: {len(self.log_entries)}")
    
    def _add_entry_to_console(self, entry):
        """Adiciona uma entrada ao console de texto"""
        if self.should_show(entry['type']):
            formatted = f'<span style="color: #6e7681;">[{entry["timestamp"]}]</span> <span style="color: {entry["color"]};">{entry["text"]}</span><br>'
            self.console_text.insertHtml(formatted)
            
            if self.auto_scroll_check.isChecked():
                cursor = self.console_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.console_text.setTextCursor(cursor)
    
    def _flush_pending_logs(self):
        """Processa logs pendentes em batch"""
        import time
        
        self._update_timer = None
        
        if not self._pending_logs:
            return
        
        # Processar todos os logs pendentes de uma vez
        # Desabilitar atualizações visuais temporárias para performance
        self.console_text.setUpdatesEnabled(False)
        
        try:
            for entry in self._pending_logs:
                self._add_entry_to_console(entry)
        finally:
            self.console_text.setUpdatesEnabled(True)
            self._pending_logs.clear()
        
        self._last_update_time = time.time() * 1000
        self.update_stats()
        self.line_count_label.setText(f"Linhas: {len(self.log_entries)}")
    
    def _rebuild_console(self):
        """Reconstrói o console após limpeza de memória - OTIMIZADO"""
        # Desabilitar atualizações visuais para performance
        self.console_text.setUpdatesEnabled(False)
        
        try:
            self.console_text.clear()
            
            # Reconstruir apenas as entradas visíveis (baseado no filtro)
            html_parts = []
            for entry in self.log_entries:
                if self.should_show(entry['type']):
                    html_parts.append(
                        f'<span style="color: #6e7681;">[{entry["timestamp"]}]</span> '
                        f'<span style="color: {entry["color"]};">{entry["text"]}</span><br>'
                    )
            
            # Inserir todo o HTML de uma vez (muito mais rápido)
            if html_parts:
                self.console_text.insertHtml(''.join(html_parts))
            
            if self.auto_scroll_check.isChecked():
                cursor = self.console_text.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.console_text.setTextCursor(cursor)
        finally:
            self.console_text.setUpdatesEnabled(True)
    
    def get_log_type_and_color(self, text):
        """Determina o tipo e cor do log"""
        text_lower = text.lower()
        
        if '[erro]' in text_lower or '[error]' in text_lower or 'error' in text_lower or 'falhou' in text_lower or 'falha' in text_lower or '[failed]' in text_lower:
            return 'error', '#f43f5e'
        elif '[ok]' in text_lower or '[sucesso]' in text_lower or 'success' in text_lower or 'aprovado' in text_lower or 'premium' in text_lower or '[completed]' in text_lower:
            return 'success', '#3fb950'
        elif '[aviso]' in text_lower or '[warn]' in text_lower or 'warning' in text_lower:
            return 'warning', '#d29922'
        elif '[proxy]' in text_lower or 'ip:' in text_lower:
            return 'proxy', '#a371f7'
        elif '[conta]' in text_lower or 'conta' in text_lower:
            return 'conta', '#79c0ff'
        elif '[cartao]' in text_lower or '[cartão]' in text_lower or 'cartao' in text_lower or 'cartão' in text_lower:
            return 'cartao', '#f0883e'
        elif '[verificador]' in text_lower or 'verificando' in text_lower or 'assinatura' in text_lower:
            return 'verificador', '#ff79c6'
        elif '[info]' in text_lower:
            return 'info', '#22d3ee'
        elif '[etapa]' in text_lower or '[step]' in text_lower:
            return 'step', '#a371f7'
        elif '[sistema]' in text_lower:
            return 'system', '#06b6d4'
        elif '[instalação]' in text_lower or '[npm]' in text_lower:
            return 'install', '#0891b2'
        else:
            return 'default', '#f1f5f9'
    
    def should_show(self, log_type):
        """Verifica se o log deve ser exibido baseado no filtro"""
        filter_text = self.filter_combo.currentText()
        
        if filter_text == "Todos":
            return True
        elif filter_text == "Info":
            return log_type in ['info', 'default', 'system', 'install', 'step']
        elif filter_text == "Sucesso":
            return log_type == 'success'
        elif filter_text == "Aviso":
            return log_type == 'warning'
        elif filter_text == "Erro":
            return log_type == 'error'
        elif filter_text == "Conta":
            return log_type == 'conta'
        elif filter_text == "Cartão":
            return log_type == 'cartao'
        elif filter_text == "Proxy":
            return log_type == 'proxy'
        elif filter_text == "Verificador":
            return log_type == 'verificador'
        
        return True
    
    def apply_filter(self):
        """Aplica o filtro atual ao console"""
        self.console_text.clear()
        
        for entry in self.log_entries:
            if self.should_show(entry['type']):
                formatted = f'<span style="color: #6e7681;">[{entry["timestamp"]}]</span> <span style="color: {entry["color"]};">{entry["text"]}</span><br>'
                self.console_text.insertHtml(formatted)
        
        if self.auto_scroll_check.isChecked():
            cursor = self.console_text.textCursor()
            cursor.movePosition(QTextCursor.End)
            self.console_text.setTextCursor(cursor)
    
    def update_stats(self):
        """Atualiza as estatísticas"""
        self.stats_info.setText(f"📊 Info: {self.counts['info']}")
        self.stats_success.setText(f"✅ Sucesso: {self.counts['success']}")
        self.stats_warning.setText(f"⚠️ Avisos: {self.counts['warning']}")
        self.stats_error.setText(f"❌ Erros: {self.counts['error']}")
    
    def clear_console(self):
        """Limpa o console"""
        self.console_text.clear()
        self.log_entries.clear()
        self.counts = {'info': 0, 'success': 0, 'warning': 0, 'error': 0}
        self.update_stats()
        self.line_count_label.setText("Linhas: 0")
    
    def export_log(self):
        """Exporta o log para arquivo"""
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Exportar Log", 
            f"crunchyroll_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
            "Text Files (*.txt);;All Files (*)"
        )
        
        if filepath:
            with open(filepath, 'w', encoding='utf-8') as f:
                for entry in self.log_entries:
                    f.write(f"[{entry['timestamp']}] {entry['text']}\n")
            
            QMessageBox.information(self, "Sucesso", f"Log exportado para:\n{filepath}")


class CrunchyrollWidget(QWidget):
    """Widget principal do Bot Crunchyroll v9.2 - MELHORADO
    
    MELHORIAS v9.2:
    - Atualização automática de cartões e contas a cada 1 minuto
    - Throttling de load_results para evitar chamadas excessivas
    - Limite de atualizações de UI por segundo
    - Processamento em batch de logs
    - Correções no sistema de fila
    """
    
    # Intervalo mínimo entre atualizações de resultados (ms)
    RESULTS_UPDATE_INTERVAL = 2000
    
    # Intervalo de atualização automática (ms) - 1 minuto
    AUTO_REFRESH_INTERVAL = 60000
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.bot_thread = None
        self.install_thread = None
        self.verificador_thread = None
        self.bot_path = os.path.join(str(BASE_DIR), 'crunchyroll_bot')
        self.is_dark_theme = True
        self.dependencies_installed = False
        self.proxy_config = {
            'enabled': False,
            'host': '',
            'port': 0,
            'username': '',
            'password': '',
            'type': 'http',
            'country': 'BR',
            'full_string': ''
        }
        
        # OTIMIZAÇÃO: Controle de throttling para load_results
        self._last_results_update = 0
        self._results_update_pending = False
        self._results_update_timer = None
        
        # NOVO v9.2: Timer para atualização automática
        self._auto_refresh_timer = None
        self._auto_refresh_enabled = True
        
        self.init_ui()
        self.load_files()
        self.check_dependencies()
        self.load_proxy_config()
        
        # NOVO v9.2: Iniciar timer de atualização automática
        self._setup_auto_refresh_timer()
    
    def check_dependencies(self):
        """Verifica se as dependências estão instaladas"""
        self.dependencies_issue = ""
        required_files = [
            os.path.join(self.bot_path, "index.js"),
            os.path.join(self.bot_path, "lib", "worker.js"),
            os.path.join(self.bot_path, "lib", "helpers", "charles-proxy-helper.js"),
        ]
        missing_files = [os.path.relpath(path, self.bot_path) for path in required_files if not os.path.exists(path)]
        if missing_files:
            self.dependencies_installed = False
            self.dependencies_issue = "Bot incompleto: " + ", ".join(missing_files)
            if hasattr(self, "console_output"):
                self.append_console(f"[ERRO] {self.dependencies_issue}")
            self.update_dependency_status()
            return

        node_modules_path = os.path.join(self.bot_path, 'node_modules')
        self.dependencies_installed = False
        if os.path.exists(node_modules_path):
            node_cmd = _resolve_command('node.exe', 'node') if sys.platform == 'win32' else _resolve_command('node')
            try:
                check = subprocess.run(
                    [node_cmd, '-e', "import puppeteer from 'puppeteer'; console.log(puppeteer.executablePath());"],
                    cwd=self.bot_path,
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace',
                    env=_node_env(),
                    timeout=12,
                    **_hidden_subprocess_kwargs()
                )
                self.dependencies_installed = check.returncode == 0
            except subprocess.TimeoutExpired:
                self.dependencies_installed = False
                if hasattr(self, "console_output"):
                    self.append_console("[AVISO] Verificacao do Puppeteer demorou demais. Tente reinstalar dependencias.")
            except Exception:
                self.dependencies_installed = False
        self.update_dependency_status()
    
    def update_dependency_status(self):
        """Atualiza o status das dependências na interface"""
        if self.dependencies_installed:
            self.deps_status_label.setText("✅ Dependências instaladas")
            self.deps_status_label.setStyleSheet(cr_dependency_status_qss(True))
            self.install_deps_btn.setEnabled(False)
            self.install_deps_btn.setText("✅ Dependências OK")
        else:
            issue = getattr(self, "dependencies_issue", "") or "Dependências NÃO instaladas"
            self.deps_status_label.setText(f"⚠️ {issue}")
            self.deps_status_label.setStyleSheet(cr_dependency_status_qss(False))
            self.install_deps_btn.setEnabled(True)
            self.install_deps_btn.setText("📦 Instalar Dependências")
    
    def get_group_style(self):
        return cr_group_qss()
    
    def lighten_color(self, hex_color, factor=0.2):
        return cr_lighten_color(hex_color, factor)
    
    def darken_color(self, hex_color, factor=0.2):
        return cr_darken_color(hex_color, factor)
    
    def get_button_style(self, color="#059669"):
        return cr_button_qss(color)
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # === HEADER ===
        header = QLabel("🎬 Crunchyroll Bot v9.2")
        header.setStyleSheet(cr_header_qss())
        header.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(header)
        
        # === TABS ===
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(cr_tabs_qss("solid"))
        
        # Tab 1: Controle do Bot
        control_tab = self.create_control_tab()
        self.tabs.addTab(control_tab, "🎮 Controle")
        
        # Tab 2: Contas
        accounts_tab = self.create_accounts_tab()
        self.tabs.addTab(accounts_tab, "📧 Contas")
        
        # Tab 3: Cartões
        cards_tab = self.create_cards_tab()
        self.tabs.addTab(cards_tab, "💳 Cartões")
        
        # Tab 4: Proxy
        proxy_tab = self.create_proxy_tab()
        self.tabs.addTab(proxy_tab, "🌐 Proxy")
        
        # Tab 5: Verificador de Assinatura
        verificador_tab = self.create_verificador_tab()
        self.tabs.addTab(verificador_tab, "🔍 Verificador")
        
        # Tab 6: Resultados
        results_tab = self.create_results_tab()
        self.tabs.addTab(results_tab, "📊 Resultados")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
    
    def create_control_tab(self):
        """Cria a aba de controle do bot"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Status
        status_group = QGroupBox("📊 Status")
        status_group.setStyleSheet(self.get_group_style())
        status_layout = QVBoxLayout()
        
        self.status_label = QLabel("⏸️ Bot parado")
        self.status_label.setStyleSheet(cr_status_qss("#94a3b8", 16))
        status_layout.addWidget(self.status_label)
        
        # Estatísticas
        stats_layout = QHBoxLayout()
        self.contas_label = QLabel("📧 Contas: 0")
        self.cartoes_label = QLabel("💳 Cartões: 0")
        self.premium_label = QLabel("✅ Premium: 0")
        
        for label in [self.contas_label, self.cartoes_label, self.premium_label]:
            label.setStyleSheet(cr_label_qss("#94a3b8", size=13))
            stats_layout.addWidget(label)
        
        status_layout.addLayout(stats_layout)
        
        # Status das dependências
        self.deps_status_label = QLabel("⏳ Verificando dependências...")
        self.deps_status_label.setStyleSheet(cr_dependency_status_qss())
        status_layout.addWidget(self.deps_status_label)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # === CONFIGURAÇÃO DE NAVEGADORES ===
        browsers_group = QGroupBox("🌐 Configuração de Navegadores")
        browsers_group.setStyleSheet(self.get_group_style())
        browsers_layout = QVBoxLayout()
        
        # Checkbox para ativar múltiplos navegadores
        self.multi_browser_checkbox = QCheckBox("Usar múltiplos navegadores simultâneos")
        self.multi_browser_checkbox.setStyleSheet(cr_checkbox_qss())
        self.multi_browser_checkbox.setChecked(True)
        self.multi_browser_checkbox.stateChanged.connect(self.on_multi_browser_changed)
        browsers_layout.addWidget(self.multi_browser_checkbox)
        
        # Layout para quantidade de navegadores
        qty_layout = QHBoxLayout()
        
        qty_label = QLabel("Quantidade de navegadores:")
        qty_label.setStyleSheet(cr_label_qss("#94a3b8", size=13))
        qty_layout.addWidget(qty_label)
        
        self.num_browsers_spin = QSpinBox()
        self.num_browsers_spin.setMinimum(1)
        self.num_browsers_spin.setMaximum(5)
        self.num_browsers_spin.setValue(3)
        self.num_browsers_spin.setStyleSheet(cr_spinbox_qss())
        qty_layout.addWidget(self.num_browsers_spin)
        
        self.browsers_info_label = QLabel("(3 navegadores = 3x mais rápido)")
        self.browsers_info_label.setStyleSheet(cr_label_qss("#6e7681", size=11))
        qty_layout.addWidget(self.browsers_info_label)
        qty_layout.addStretch()
        
        browsers_layout.addLayout(qty_layout)
        
        # Aviso
        warning_label = QLabel("⚠️ Dica: Se muitas contas falharem, tente usar menos navegadores (1-2)")
        warning_label.setStyleSheet(cr_label_qss("#d29922", size=11))
        browsers_layout.addWidget(warning_label)
        
        browsers_group.setLayout(browsers_layout)
        layout.addWidget(browsers_group)
        
        # Botão de instalação de dependências
        deps_group = QGroupBox("📦 Dependências (Node.js)")
        deps_group.setStyleSheet(self.get_group_style())
        deps_layout = QHBoxLayout()
        
        self.install_deps_btn = QPushButton("📦 Instalar Dependências")
        self.install_deps_btn.setStyleSheet(self.get_button_style("#0891b2"))
        self.install_deps_btn.clicked.connect(self.install_dependencies)
        deps_layout.addWidget(self.install_deps_btn)
        
        deps_info = QLabel("Necessário executar apenas uma vez")
        deps_info.setStyleSheet(cr_label_qss("#6e7681", size=11))
        deps_layout.addWidget(deps_info)
        deps_layout.addStretch()
        
        deps_group.setLayout(deps_layout)
        layout.addWidget(deps_group)
        
        # Botões de controle
        control_group = QGroupBox("🎮 Controles")
        control_group.setStyleSheet(self.get_group_style())
        control_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("▶️ INICIAR BOT")
        self.start_btn.setStyleSheet(self.get_button_style("#059669"))
        self.start_btn.clicked.connect(self.start_bot)
        control_layout.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("⏹️ PARAR BOT")
        self.stop_btn.setStyleSheet(self.get_button_style("#da3633"))
        self.stop_btn.clicked.connect(self.stop_bot)
        self.stop_btn.setEnabled(False)
        control_layout.addWidget(self.stop_btn)
        
        self.skip_btn = QPushButton("⏭️ PULAR CONTA")
        self.skip_btn.setStyleSheet(self.get_button_style("#d29922"))
        self.skip_btn.clicked.connect(self.skip_account)
        self.skip_btn.setEnabled(False)
        control_layout.addWidget(self.skip_btn)
        
        control_group.setLayout(control_layout)
        layout.addWidget(control_group)
        
        # Console avançado
        console_group = QGroupBox("📜 Console Avançado")
        console_group.setStyleSheet(self.get_group_style())
        console_layout = QVBoxLayout()
        
        self.advanced_console = AdvancedConsole()
        console_layout.addWidget(self.advanced_console)
        
        console_group.setLayout(console_layout)
        layout.addWidget(console_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_verificador_tab(self):
        """Cria a aba do verificador de assinatura"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Grupo de entrada de contas
        input_group = QGroupBox("📧 Contas para Verificar (email:senha)")
        input_group.setStyleSheet(self.get_group_style())
        input_layout = QVBoxLayout()
        
        self.verificador_input = QTextEdit()
        self.verificador_input.setStyleSheet(cr_text_edit_qss("#f1f5f9"))
        self.verificador_input.setPlaceholderText("Cole as contas aqui para verificar...\nFormato: email:senha ou email|senha\n\nExemplo:\nuser@email.com:senha123\noutro@email.com|minhasenha")
        self.verificador_input.setMaximumHeight(150)
        input_layout.addWidget(self.verificador_input)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        self.verificar_btn = QPushButton("🔍 VERIFICAR ASSINATURAS")
        self.verificar_btn.setStyleSheet(self.get_button_style("#0891b2"))
        self.verificar_btn.clicked.connect(self.start_verificador)
        btn_layout.addWidget(self.verificar_btn)
        
        self.parar_verificador_btn = QPushButton("⏹️ PARAR")
        self.parar_verificador_btn.setStyleSheet(self.get_button_style("#da3633"))
        self.parar_verificador_btn.clicked.connect(self.stop_verificador)
        self.parar_verificador_btn.setEnabled(False)
        btn_layout.addWidget(self.parar_verificador_btn)
        
        load_verificar_btn = QPushButton("📂 Carregar Arquivo")
        load_verificar_btn.setStyleSheet(self.get_button_style("#0891b2"))
        load_verificar_btn.clicked.connect(self.load_verificar_file)
        btn_layout.addWidget(load_verificar_btn)
        
        input_layout.addLayout(btn_layout)
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # Status do verificador
        status_group = QGroupBox("📊 Status da Verificação")
        status_group.setStyleSheet(self.get_group_style())
        status_layout = QHBoxLayout()
        
        self.verificador_status = QLabel("⏸️ Aguardando...")
        self.verificador_status.setStyleSheet(cr_status_qss("#94a3b8", 14))
        status_layout.addWidget(self.verificador_status)
        
        status_layout.addStretch()
        
        self.verificador_progress = QLabel("0/0")
        self.verificador_progress.setStyleSheet(cr_label_qss("#94a3b8", size=14, padding=0))
        status_layout.addWidget(self.verificador_progress)
        
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        # Resultados - Completed (Assinatura Ativa)
        completed_group = QGroupBox("✅ Assinaturas ATIVAS (Completed)")
        completed_group.setStyleSheet(self.get_group_style())
        completed_layout = QVBoxLayout()
        
        self.verificador_completed = QTextEdit()
        self.verificador_completed.setReadOnly(True)
        self.verificador_completed.setStyleSheet(cr_text_edit_qss("#3fb950", "#059669"))
        self.verificador_completed.setMaximumHeight(120)
        completed_layout.addWidget(self.verificador_completed)
        
        completed_btn_layout = QHBoxLayout()
        
        copy_completed_btn = QPushButton("📋 Copiar")
        copy_completed_btn.setStyleSheet(self.get_button_style("#059669"))
        copy_completed_btn.clicked.connect(self.copy_verificador_completed)
        completed_btn_layout.addWidget(copy_completed_btn)
        
        copy_completed_simple_btn = QPushButton("📋 Copiar email:senha")
        copy_completed_simple_btn.setStyleSheet(self.get_button_style("#0891b2"))
        copy_completed_simple_btn.clicked.connect(self.copy_verificador_completed_simple)
        completed_btn_layout.addWidget(copy_completed_simple_btn)
        
        clear_completed_btn = QPushButton("🗑️ Limpar")
        clear_completed_btn.setStyleSheet(cr_small_button_qss(True))
        clear_completed_btn.clicked.connect(self.clear_verificador_completed)
        completed_btn_layout.addWidget(clear_completed_btn)
        
        completed_btn_layout.addStretch()
        completed_layout.addLayout(completed_btn_layout)
        completed_group.setLayout(completed_layout)
        layout.addWidget(completed_group)
        
        # Resultados - Failed (Assinatura Falhou)
        failed_group = QGroupBox("❌ Assinaturas FALHAS (Failed)")
        failed_group.setStyleSheet(self.get_group_style())
        failed_layout = QVBoxLayout()
        
        self.verificador_failed = QTextEdit()
        self.verificador_failed.setReadOnly(True)
        self.verificador_failed.setStyleSheet(cr_text_edit_qss("#f43f5e", "#da3633"))
        self.verificador_failed.setMaximumHeight(100)
        failed_layout.addWidget(self.verificador_failed)
        
        failed_btn_layout = QHBoxLayout()
        
        copy_failed_btn = QPushButton("📋 Copiar")
        copy_failed_btn.setStyleSheet(self.get_button_style("#da3633"))
        copy_failed_btn.clicked.connect(self.copy_verificador_failed)
        failed_btn_layout.addWidget(copy_failed_btn)
        
        clear_failed_btn = QPushButton("🗑️ Limpar")
        clear_failed_btn.setStyleSheet(cr_small_button_qss(True))
        clear_failed_btn.clicked.connect(self.clear_verificador_failed)
        failed_btn_layout.addWidget(clear_failed_btn)
        
        failed_btn_layout.addStretch()
        failed_layout.addLayout(failed_btn_layout)
        failed_group.setLayout(failed_layout)
        layout.addWidget(failed_group)
        
        # Informações
        info_group = QGroupBox("ℹ️ Como Funciona")
        info_group.setStyleSheet(self.get_group_style())
        info_layout = QVBoxLayout()
        
        info_text = QLabel("""
<p style="color: #94a3b8; line-height: 1.6;">
<b style="color: #06b6d4;">O Verificador de Assinatura:</b><br><br>

1. Faz login em cada conta usando: <code style="background: #1e293b; padding: 2px 6px; border-radius: 4px;">https://sso.crunchyroll.com/pt-br/login</code><br><br>

2. Acessa o histórico de pagamentos: <code style="background: #1e293b; padding: 2px 6px; border-radius: 4px;">https://www.crunchyroll.com/payments/history</code><br><br>

3. Verifica o status da assinatura:<br>
   • <span style="color: #3fb950;"><b>Completed</b></span> = Assinatura ATIVA ✅<br>
   • <span style="color: #f43f5e;"><b>Failed</b></span> = Assinatura FALHOU ❌<br><br>

<b style="color: #d29922;">⚠️ Dica:</b> Use o proxy para evitar bloqueios!
</p>
        """)
        info_text.setWordWrap(True)
        info_layout.addWidget(info_text)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def create_proxy_tab(self):
        """Cria a aba de configuração de proxy"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        # Grupo de configuração de proxy
        proxy_group = QGroupBox("🌐 Configuração de Proxy PyProxy Rotativa")
        proxy_group.setStyleSheet(self.get_group_style())
        proxy_layout = QVBoxLayout()
        
        # Checkbox para habilitar proxy
        self.proxy_enabled_check = QCheckBox("Habilitar Proxy")
        self.proxy_enabled_check.setStyleSheet(cr_checkbox_qss(size=14, color="#f1f5f9", indicator=20))
        self.proxy_enabled_check.stateChanged.connect(self.on_proxy_enabled_changed)
        proxy_layout.addWidget(self.proxy_enabled_check)
        
        # Campo para proxy string completa
        proxy_string_layout = QVBoxLayout()
        
        proxy_string_label = QLabel("Cole sua proxy PyProxy completa (formato: host:porta:usuario:senha):")
        proxy_string_label.setStyleSheet(cr_label_qss("#94a3b8", size=13, padding=0))
        proxy_string_layout.addWidget(proxy_string_label)
        
        self.proxy_string_edit = QLineEdit()
        self.proxy_string_edit.setPlaceholderText("Ex: cfd0a9406cc7e8bc.shg.na.pyproxy.io:16666:admin121-zone-resi-region-br:pass1212")
        self.proxy_string_edit.setStyleSheet(cr_line_edit_qss(220))
        self.proxy_string_edit.textChanged.connect(self.parse_proxy_string)
        proxy_string_layout.addWidget(self.proxy_string_edit)
        
        proxy_layout.addLayout(proxy_string_layout)
        
        # Campos parseados (somente leitura)
        parsed_group = QGroupBox("📋 Dados Parseados")
        parsed_group.setStyleSheet(cr_subtle_group_qss())
        parsed_layout = QGridLayout()
        parsed_layout.setSpacing(8)
        
        # Host
        host_label = QLabel("Host:")
        host_label.setStyleSheet(cr_label_qss("#6e7681", padding=0))
        parsed_layout.addWidget(host_label, 0, 0)
        
        self.proxy_host_display = QLabel("-")
        self.proxy_host_display.setStyleSheet(cr_mono_value_qss())
        parsed_layout.addWidget(self.proxy_host_display, 0, 1)
        
        # Porta
        port_label = QLabel("Porta:")
        port_label.setStyleSheet(cr_label_qss("#6e7681", padding=0))
        parsed_layout.addWidget(port_label, 0, 2)
        
        self.proxy_port_display = QLabel("-")
        self.proxy_port_display.setStyleSheet(cr_mono_value_qss())
        parsed_layout.addWidget(self.proxy_port_display, 0, 3)
        
        # Usuário
        user_label = QLabel("Usuário:")
        user_label.setStyleSheet(cr_label_qss("#6e7681", padding=0))
        parsed_layout.addWidget(user_label, 1, 0)
        
        self.proxy_user_display = QLabel("-")
        self.proxy_user_display.setStyleSheet(cr_mono_value_qss())
        parsed_layout.addWidget(self.proxy_user_display, 1, 1)
        
        # Senha
        pass_label = QLabel("Senha:")
        pass_label.setStyleSheet(cr_label_qss("#6e7681", padding=0))
        parsed_layout.addWidget(pass_label, 1, 2)
        
        self.proxy_pass_display = QLabel("-")
        self.proxy_pass_display.setStyleSheet(cr_mono_value_qss())
        parsed_layout.addWidget(self.proxy_pass_display, 1, 3)
        
        parsed_group.setLayout(parsed_layout)
        proxy_layout.addWidget(parsed_group)
        
        # Checkbox IP único por conta
        self.unique_ip_check = QCheckBox("🔄 IP único por conta (rotaciona IP a cada conta criada)")
        self.unique_ip_check.setChecked(True)
        self.unique_ip_check.setStyleSheet(cr_checkbox_qss(size=13, color="#3fb950", indicator=18))
        proxy_layout.addWidget(self.unique_ip_check)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        save_proxy_btn = QPushButton("💾 Salvar Configuração")
        save_proxy_btn.setStyleSheet(self.get_button_style("#059669"))
        save_proxy_btn.clicked.connect(self.save_proxy_config)
        btn_layout.addWidget(save_proxy_btn)
        
        test_proxy_btn = QPushButton("🔍 Testar Proxy")
        test_proxy_btn.setStyleSheet(self.get_button_style("#0891b2"))
        test_proxy_btn.clicked.connect(self.test_proxy)
        btn_layout.addWidget(test_proxy_btn)
        
        btn_layout.addStretch()
        proxy_layout.addLayout(btn_layout)
        
        proxy_group.setLayout(proxy_layout)
        layout.addWidget(proxy_group)
        
        layout.addStretch()
        tab.setLayout(layout)
        return tab
    
    def parse_proxy_string(self, text):
        """Parseia a string de proxy e atualiza os campos"""
        text = text.strip()
        if not text:
            self.proxy_host_display.setText("-")
            self.proxy_port_display.setText("-")
            self.proxy_user_display.setText("-")
            self.proxy_pass_display.setText("-")
            return
        
        parts = text.split(':')
        if len(parts) >= 4:
            self.proxy_host_display.setText(parts[0])
            self.proxy_port_display.setText(parts[1])
            self.proxy_user_display.setText(parts[2])
            self.proxy_pass_display.setText(parts[3] if len(parts[3]) <= 20 else parts[3][:17] + "...")
        elif len(parts) == 2:
            self.proxy_host_display.setText(parts[0])
            self.proxy_port_display.setText(parts[1])
            self.proxy_user_display.setText("-")
            self.proxy_pass_display.setText("-")
        else:
            self.proxy_host_display.setText("Formato inválido")
            self.proxy_port_display.setText("-")
            self.proxy_user_display.setText("-")
            self.proxy_pass_display.setText("-")
    
    def create_accounts_tab(self):
        """Cria a aba de gerenciamento de contas"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        accounts_group = QGroupBox("📧 Contas (email|senha ou email:senha)")
        accounts_group.setStyleSheet(self.get_group_style())
        accounts_layout = QVBoxLayout()
        
        self.accounts_edit = QTextEdit()
        self.accounts_edit.setStyleSheet(cr_text_edit_qss("#f1f5f9"))
        self.accounts_edit.setPlaceholderText("Cole as contas aqui...\nFormato: email|senha ou email:senha")
        accounts_layout.addWidget(self.accounts_edit)
        
        btn_layout = QHBoxLayout()
        
        save_accounts_btn = QPushButton("💾 Salvar Contas")
        save_accounts_btn.setStyleSheet(self.get_button_style("#059669"))
        save_accounts_btn.clicked.connect(self.save_accounts)
        btn_layout.addWidget(save_accounts_btn)
        
        load_accounts_btn = QPushButton("📂 Carregar Arquivo")
        load_accounts_btn.setStyleSheet(self.get_button_style("#0891b2"))
        load_accounts_btn.clicked.connect(self.load_accounts_file)
        btn_layout.addWidget(load_accounts_btn)
        
        # BOTÃO DE ATUALIZAR - Remove contas já utilizadas
        refresh_accounts_btn = QPushButton("🔄 Atualizar (Remover Utilizadas)")
        refresh_accounts_btn.setStyleSheet(self.get_button_style("#06b6d4"))
        refresh_accounts_btn.clicked.connect(self.refresh_accounts_remove_used)
        refresh_accounts_btn.setToolTip("Remove contas que já foram processadas (premium, falhas, login OK, etc.)")
        btn_layout.addWidget(refresh_accounts_btn)
        
        accounts_layout.addLayout(btn_layout)
        accounts_group.setLayout(accounts_layout)
        layout.addWidget(accounts_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_cards_tab(self):
        """Cria a aba de gerenciamento de cartões"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        cards_group = QGroupBox("💳 Cartões (numero|mes|ano|cvv)")
        cards_group.setStyleSheet(self.get_group_style())
        cards_layout = QVBoxLayout()
        
        self.cards_edit = QTextEdit()
        self.cards_edit.setStyleSheet(cr_text_edit_qss("#f1f5f9"))
        self.cards_edit.setPlaceholderText("Cole os cartões aqui...\nFormato: numero|mes|ano|cvv")
        cards_layout.addWidget(self.cards_edit)
        
        btn_layout = QHBoxLayout()
        
        save_cards_btn = QPushButton("💾 Salvar Cartões")
        save_cards_btn.setStyleSheet(self.get_button_style("#059669"))
        save_cards_btn.clicked.connect(self.save_cards)
        btn_layout.addWidget(save_cards_btn)
        
        load_cards_btn = QPushButton("📂 Carregar Arquivo")
        load_cards_btn.setStyleSheet(self.get_button_style("#0891b2"))
        load_cards_btn.clicked.connect(self.load_cards_file)
        btn_layout.addWidget(load_cards_btn)
        
        # BOTÃO DE ATUALIZAR - Remove cartões já utilizados
        refresh_cards_btn = QPushButton("🔄 Atualizar (Remover Utilizados)")
        refresh_cards_btn.setStyleSheet(self.get_button_style("#06b6d4"))
        refresh_cards_btn.clicked.connect(self.refresh_cards_remove_used)
        refresh_cards_btn.setToolTip("Remove cartões que já foram aprovados ou reprovados")
        btn_layout.addWidget(refresh_cards_btn)
        
        cards_layout.addLayout(btn_layout)
        cards_group.setLayout(cards_layout)
        layout.addWidget(cards_group)
        
        tab.setLayout(layout)
        return tab
    
    def create_results_tab(self):
        """Cria a aba de resultados com botões de limpar"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(12)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(cr_scroll_area_qss())
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(12)
        
        # Resumo
        summary_group = QGroupBox("📈 Resumo")
        summary_group.setStyleSheet(self.get_group_style())
        summary_layout = QGridLayout()
        
        self.stat_premium = QLabel("✅ Premium: 0")
        self.stat_premium.setStyleSheet(cr_stat_qss("#10b981"))
        summary_layout.addWidget(self.stat_premium, 0, 0)
        
        self.stat_falhas = QLabel("❌ Falhas: 0")
        self.stat_falhas.setStyleSheet(cr_stat_qss("#f43f5e"))
        summary_layout.addWidget(self.stat_falhas, 0, 1)
        
        self.stat_cartoes_ok = QLabel("💳 Cartões Aprovados: 0")
        self.stat_cartoes_ok.setStyleSheet(cr_stat_qss("#10b981"))
        summary_layout.addWidget(self.stat_cartoes_ok, 1, 0)
        
        self.stat_cartoes_fail = QLabel("💳 Cartões Reprovados: 0")
        self.stat_cartoes_fail.setStyleSheet(cr_stat_qss("#f43f5e"))
        summary_layout.addWidget(self.stat_cartoes_fail, 1, 1)
        
        summary_group.setLayout(summary_layout)
        scroll_layout.addWidget(summary_group)
        
        # Contas Premium Criadas
        premium_group = QGroupBox("✅ Contas Premium Criadas")
        premium_group.setStyleSheet(self.get_group_style())
        premium_layout = QVBoxLayout()
        
        self.premium_edit = QTextEdit()
        self.premium_edit.setReadOnly(True)
        self.premium_edit.setStyleSheet(cr_text_edit_qss("#10b981", "#059669"))
        self.premium_edit.setMaximumHeight(150)
        premium_layout.addWidget(self.premium_edit)
        
        premium_btn_layout = QHBoxLayout()
        
        copy_premium_btn = QPushButton("📋 Copiar Tudo")
        copy_premium_btn.setStyleSheet(self.get_button_style("#0891b2"))
        copy_premium_btn.clicked.connect(self.copy_premium)
        premium_btn_layout.addWidget(copy_premium_btn)
        
        copy_simple_btn = QPushButton("📋 Copiar email:senha")
        copy_simple_btn.setStyleSheet(self.get_button_style("#0891b2"))
        copy_simple_btn.clicked.connect(self.copy_premium_simple)
        premium_btn_layout.addWidget(copy_simple_btn)
        
        clear_premium_btn = QPushButton("🗑️ Limpar")
        clear_premium_btn.setStyleSheet(cr_small_button_qss(True))
        clear_premium_btn.clicked.connect(self.clear_premium)
        premium_btn_layout.addWidget(clear_premium_btn)
        
        premium_btn_layout.addStretch()
        premium_layout.addLayout(premium_btn_layout)
        premium_group.setLayout(premium_layout)
        scroll_layout.addWidget(premium_group)
        
        # Cartões Aprovados
        cards_approved_group = QGroupBox("💳 Cartões Aprovados")
        cards_approved_group.setStyleSheet(self.get_group_style())
        cards_approved_layout = QVBoxLayout()
        
        self.cards_approved_edit = QTextEdit()
        self.cards_approved_edit.setReadOnly(True)
        self.cards_approved_edit.setStyleSheet(cr_text_edit_qss("#10b981", "#059669"))
        self.cards_approved_edit.setMaximumHeight(120)
        cards_approved_layout.addWidget(self.cards_approved_edit)
        
        cards_approved_btn_layout = QHBoxLayout()
        
        copy_cards_btn = QPushButton("📋 Copiar Cartões Aprovados")
        copy_cards_btn.setStyleSheet(self.get_button_style("#059669"))
        copy_cards_btn.clicked.connect(self.copy_cards_approved)
        cards_approved_btn_layout.addWidget(copy_cards_btn)
        
        clear_cards_approved_btn = QPushButton("🗑️ Limpar")
        clear_cards_approved_btn.setStyleSheet(cr_small_button_qss(True))
        clear_cards_approved_btn.clicked.connect(self.clear_cards_approved)
        cards_approved_btn_layout.addWidget(clear_cards_approved_btn)
        
        cards_approved_btn_layout.addStretch()
        cards_approved_layout.addLayout(cards_approved_btn_layout)
        cards_approved_group.setLayout(cards_approved_layout)
        scroll_layout.addWidget(cards_approved_group)
        
        # Cartões Reprovados
        cards_rejected_group = QGroupBox("❌ Cartões Reprovados")
        cards_rejected_group.setStyleSheet(self.get_group_style())
        cards_rejected_layout = QVBoxLayout()
        
        self.cards_rejected_edit = QTextEdit()
        self.cards_rejected_edit.setReadOnly(True)
        self.cards_rejected_edit.setStyleSheet(cr_text_edit_qss("#f43f5e", "#da3633"))
        self.cards_rejected_edit.setMaximumHeight(100)
        cards_rejected_layout.addWidget(self.cards_rejected_edit)
        
        cards_rejected_btn_layout = QHBoxLayout()
        
        clear_cards_rejected_btn = QPushButton("🗑️ Limpar Reprovados")
        clear_cards_rejected_btn.setStyleSheet(cr_small_button_qss(True))
        clear_cards_rejected_btn.clicked.connect(self.clear_cards_rejected)
        cards_rejected_btn_layout.addWidget(clear_cards_rejected_btn)
        
        cards_rejected_btn_layout.addStretch()
        cards_rejected_layout.addLayout(cards_rejected_btn_layout)
        cards_rejected_group.setLayout(cards_rejected_layout)
        scroll_layout.addWidget(cards_rejected_group)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        tab.setLayout(layout)
        return tab
    
    # ========== FUNÇÕES DO VERIFICADOR ==========
    
    def start_verificador(self):
        """Inicia o verificador de assinatura"""
        accounts_text = self.verificador_input.toPlainText().strip()
        if not accounts_text:
            QMessageBox.warning(self, "Aviso", "Cole as contas para verificar!")
            return
        
        accounts = [l.strip() for l in accounts_text.split('\n') if l.strip() and not l.startswith('#')]
        
        if not accounts:
            QMessageBox.warning(self, "Aviso", "Nenhuma conta válida encontrada!")
            return
        
        if not self.dependencies_installed:
            reply = QMessageBox.question(
                self, "Dependências não instaladas",
                "As dependências do Node.js não estão instaladas.\n\n"
                "Deseja instalar agora?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.install_dependencies()
            return
        
        # Iniciar thread do verificador
        self.verificador_thread = VerificadorThread(self.bot_path, accounts, self.proxy_config)
        self.verificador_thread.output_signal.connect(self.append_console)
        self.verificador_thread.finished_signal.connect(self.verificador_finished)
        self.verificador_thread.error_signal.connect(self.verificador_error)
        self.verificador_thread.result_signal.connect(self.verificador_results)
        self.verificador_thread.start()
        
        # Atualizar UI
        self.verificar_btn.setEnabled(False)
        self.parar_verificador_btn.setEnabled(True)
        self.verificador_status.setText(f"🔍 Verificando {len(accounts)} conta(s)...")
        self.verificador_status.setStyleSheet(cr_status_qss("#0891b2", 14))
        self.verificador_progress.setText(f"0/{len(accounts)}")
        
        self.append_console(f"[VERIFICADOR] Iniciando verificação de {len(accounts)} conta(s)...")
    
    def stop_verificador(self):
        """Para o verificador"""
        if self.verificador_thread:
            self.verificador_thread.stop()
            self.append_console("[VERIFICADOR] Parando verificação...")
    
    def verificador_finished(self, return_code):
        """Chamado quando o verificador termina"""
        self.verificar_btn.setEnabled(True)
        self.parar_verificador_btn.setEnabled(False)
        self.verificador_status.setText("✅ Verificação concluída!")
        self.verificador_status.setStyleSheet(cr_status_qss("#3fb950", 14))
        
        self.append_console(f"[VERIFICADOR] Verificação concluída (código: {return_code})")
    
    def verificador_error(self, error):
        """Chamado quando ocorre erro no verificador"""
        self.verificar_btn.setEnabled(True)
        self.parar_verificador_btn.setEnabled(False)
        self.verificador_status.setText("❌ Erro na verificação")
        self.verificador_status.setStyleSheet(cr_status_qss("#f43f5e", 14))
        
        self.append_console(f"[VERIFICADOR] Erro: {error}")
        QMessageBox.critical(self, "Erro", error)
    
    def verificador_results(self, results):
        """Atualiza os resultados do verificador"""
        completed = results.get('completed', [])
        failed_groups = [
            ("Falha", results.get('failed', [])),
            ("Login falhou", results.get('login_failed', [])),
            ("Sem pagamento", results.get('no_payment', [])),
            ("Email invalido", results.get('invalid_email', [])),
            ("Rate limit", results.get('rate_limited', [])),
        ]

        self.verificador_completed.setText('\n'.join(completed))

        failed_text = []
        for label, lines in failed_groups:
            if not lines:
                continue
            if failed_text:
                failed_text.append("")
            failed_text.append(f"[{label}]")
            failed_text.extend(lines)
        self.verificador_failed.setText('\n'.join(failed_text))

        # Atualizar contagem
        completed_count = len(completed)
        failed_count = sum(len(lines) for _, lines in failed_groups)
        
        self.verificador_progress.setText(f"✅ {completed_count} | ❌ {failed_count}")
    
    def load_verificar_file(self):
        """Carrega contas de um arquivo para verificar"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Carregar Contas", "", "Text Files (*.txt);;All Files (*)")
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
                current = self.verificador_input.toPlainText()
                if current.strip():
                    self.verificador_input.setText(current + '\n' + '\n'.join(lines))
                else:
                    self.verificador_input.setText('\n'.join(lines))
    
    def copy_verificador_completed(self):
        """Copia as contas com assinatura ativa"""

        text = self.verificador_completed.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Sucesso", "Contas com assinatura ATIVA copiadas!")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhuma conta para copiar!")
    
    def copy_verificador_completed_simple(self):
        """Copia as contas com assinatura ativa no formato email:senha"""

        
        # Primeiro tentar ler do arquivo simples
        simple_path = os.path.join(self.bot_path, 'data', 'verificador_completed_simples.txt')
        if os.path.exists(simple_path):
            with open(simple_path, 'r', encoding='utf-8') as f:
                text = f.read().strip()
            if text:
                QApplication.clipboard().setText(text)
                QMessageBox.information(self, "Sucesso", "Contas copiadas no formato email:senha!")
                return
        
        # Se não existir, converter do texto atual
        text = self.verificador_completed.toPlainText()
        if text:
            lines = []
            for line in text.strip().split('\n'):
                line = line.strip()
                if line:
                    # Converter para formato simples email:senha
                    if '|' in line:
                        parts = line.split('|')
                        if len(parts) >= 2:
                            lines.append(f"{parts[0].strip()}:{parts[1].strip()}")
                    elif ':' in line:
                        lines.append(line)
            
            if lines:
                simple_text = '\n'.join(lines)
                QApplication.clipboard().setText(simple_text)
                QMessageBox.information(self, "Sucesso", "Contas copiadas no formato email:senha!")
                return
        
        QMessageBox.warning(self, "Aviso", "Nenhuma conta para copiar!")
    
    def copy_verificador_failed(self):
        """Copia as contas com assinatura falha"""

        text = self.verificador_failed.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Sucesso", "Contas com assinatura FALHA copiadas!")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhuma conta para copiar!")
    
    def clear_verificador_completed(self):
        """Limpa as contas com assinatura ativa"""
        self.verificador_completed.clear()
        for filename in ('verificador_completed.txt', 'verificador_completed_simples.txt'):
            filepath = os.path.join(self.bot_path, 'data', filename)
            if os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('')
        self.append_console("[VERIFICADOR] Contas COMPLETED limpas")
    
    def clear_verificador_failed(self):
        """Limpa as contas com assinatura falha"""
        self.verificador_failed.clear()
        for filename in (
            'verificador_failed.txt',
            'verificador_login_failed.txt',
            'verificador_no_payment.txt',
            'verificador_invalid_email.txt',
            'verificador_rate_limited.txt',
        ):
            filepath = os.path.join(self.bot_path, 'data', filename)
            if os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('')
        self.append_console("[VERIFICADOR] Contas FAILED limpas")
    
    # ========== OUTRAS FUNÇÕES ==========
    
    def on_multi_browser_changed(self, state):
        """Callback quando o checkbox de múltiplos navegadores muda"""
        if state == Qt.Checked:
            self.num_browsers_spin.setEnabled(True)
            self.browsers_info_label.setText(f"({self.num_browsers_spin.value()} navegadores = {self.num_browsers_spin.value()}x mais rápido)")
        else:
            self.num_browsers_spin.setEnabled(False)
            self.num_browsers_spin.setValue(1)
            self.browsers_info_label.setText("(1 navegador - modo seguro)")
    
    def on_proxy_enabled_changed(self, state):
        """Callback quando o checkbox de proxy muda"""
        enabled = state == Qt.Checked
        self.proxy_string_edit.setEnabled(enabled)
        self.unique_ip_check.setEnabled(enabled)
    
    def load_proxy_config(self):
        """Carrega configuração de proxy salva"""
        config_path = os.path.join(self.bot_path, 'data', 'proxy_config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.proxy_enabled_check.setChecked(config.get('enabled', False))
                    self.proxy_string_edit.setText(config.get('full_string', ''))
                    self.unique_ip_check.setChecked(config.get('unique_ip', True))
                    self.proxy_config = config
            except Exception as e:
                print(f"Erro ao carregar config de proxy: {e}")
    
    def save_proxy_config(self):
        """Salva configuração de proxy"""
        proxy_string = self.proxy_string_edit.text().strip()
        
        # Parsear a string
        parts = proxy_string.split(':') if proxy_string else []
        
        self.proxy_config = {
            'enabled': self.proxy_enabled_check.isChecked(),
            'full_string': proxy_string,
            'host': parts[0] if len(parts) >= 1 else '',
            'port': int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else 0,
            'username': parts[2] if len(parts) >= 3 else '',
            'password': parts[3] if len(parts) >= 4 else '',
            'type': 'http',
            'country': 'BR',
            'unique_ip': self.unique_ip_check.isChecked()
        }
        
        config_path = os.path.join(self.bot_path, 'data', 'proxy_config.json')
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(self.proxy_config, f, indent=2)
        
        QMessageBox.information(self, "Sucesso", "Configuração de proxy salva!")
        self.append_console("[PROXY] Configuração de proxy salva")
        if self.proxy_config['enabled']:
            self.append_console(f"[PROXY] Host: {self.proxy_config['host']}:{self.proxy_config['port']}")
            self.append_console(f"[PROXY] IP único por conta: {'Ativado' if self.proxy_config['unique_ip'] else 'Desativado'}")
    
    def test_proxy(self):
        """Testa a conexão com o proxy"""
        if not self.proxy_enabled_check.isChecked():
            QMessageBox.warning(self, "Aviso", "Habilite o proxy primeiro!")
            return
        
        proxy_string = self.proxy_string_edit.text().strip()
        if not proxy_string:
            QMessageBox.warning(self, "Aviso", "Informe a string do proxy!")
            return
        
        parts = proxy_string.split(':')
        if len(parts) < 2:
            QMessageBox.warning(self, "Aviso", "Formato de proxy inválido!")
            return
        
        host = parts[0]
        try:
            port = int(parts[1])
        except ValueError:
            QMessageBox.warning(self, "Aviso", "Porta inválida!")
            return
        
        self.append_console(f"[PROXY] Testando conexão com {host}:{port}...")
        
        # Teste simples de conexão
        import socket
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10)
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result == 0:
                self.append_console(f"[PROXY] ✅ Conexão com {host}:{port} bem sucedida!")
                QMessageBox.information(self, "Sucesso", f"Proxy {host}:{port} está acessível!")
            else:
                self.append_console(f"[PROXY] ❌ Não foi possível conectar a {host}:{port}")
                QMessageBox.warning(self, "Erro", f"Não foi possível conectar ao proxy {host}:{port}")
        except Exception as e:
            self.append_console(f"[PROXY] ❌ Erro ao testar proxy: {str(e)}")
            QMessageBox.critical(self, "Erro", f"Erro ao testar proxy:\n{str(e)}")
    
    def load_files(self):
        """Carrega os arquivos de contas e cartões"""
        # Carregar contas
        contas_path = os.path.join(self.bot_path, 'data', 'contas.txt')
        if os.path.exists(contas_path):
            with open(contas_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
                self.accounts_edit.setText('\n'.join(lines))
        
        # Carregar cartões
        cartoes_path = os.path.join(self.bot_path, 'data', 'cartoes.txt')
        if os.path.exists(cartoes_path):
            with open(cartoes_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
                self.cards_edit.setText('\n'.join(lines))
        
        self.update_stats()
        self.load_results()
        self.load_verificador_results()
    
    def load_verificador_results(self):
        """Carrega os resultados do verificador"""
        if hasattr(self, "verificador_completed") and hasattr(self, "verificador_failed"):
            self.verificador_results(VerificadorThread(self.bot_path, []).read_results())
    
    def load_results(self):
        """Carrega os resultados - OTIMIZADO v9.1
        
        Otimizações:
        - Limita quantidade de linhas exibidas para evitar travamentos
        - Leitura otimizada de arquivos grandes
        - Atualização de UI desabilitada durante processamento
        """
        # Limite máximo de linhas a exibir nos campos de texto
        MAX_DISPLAY_LINES = 500
        
        data_path = os.path.join(self.bot_path, 'data')
        
        def read_file_optimized(filepath, max_lines=MAX_DISPLAY_LINES):
            """Lê arquivo de forma otimizada, limitando linhas"""
            if not os.path.exists(filepath):
                return '', 0
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    lines = [l.strip() for l in f if l.strip()]
                    total_count = len(lines)
                    
                    if total_count > max_lines:
                        # Mostrar apenas as últimas linhas + aviso
                        display_lines = lines[-max_lines:]
                        header = f"# ... ({total_count - max_lines} linhas anteriores ocultas)\n"
                        return header + '\n'.join(display_lines), total_count
                    else:
                        return '\n'.join(lines), total_count
            except Exception:
                return '', 0
        
        # Desabilitar atualizações visuais para performance
        self.premium_edit.setUpdatesEnabled(False)
        self.cards_approved_edit.setUpdatesEnabled(False)
        self.cards_rejected_edit.setUpdatesEnabled(False)
        
        try:
            # Premium
            premium_path = os.path.join(data_path, 'contas_premium.txt')
            content, premium_count = read_file_optimized(premium_path)
            self.premium_edit.setText(content)
            
            # Falhas (apenas contar, não exibir)
            failed_count = 0
            for filename in ['contas_sem_pagamento.txt', 'contas_login_falhou.txt', 'contas_sem_cartao.txt']:
                filepath = os.path.join(data_path, filename)
                if os.path.exists(filepath):
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            failed_count += sum(1 for l in f if l.strip())
                    except Exception:
                        pass
            
            # Cartões Aprovados
            cartoes_aprovados_path = os.path.join(data_path, 'cartoes_aprovados.txt')
            content, cards_approved_count = read_file_optimized(cartoes_aprovados_path)
            self.cards_approved_edit.setText(content)
            
            # Cartões Reprovados
            cartoes_falhos_path = os.path.join(data_path, 'cartoes_falhos.txt')
            content, cards_rejected_count = read_file_optimized(cartoes_falhos_path)
            self.cards_rejected_edit.setText(content)
            
            # Atualizar labels
            self.stat_premium.setText(f"✅ Premium: {premium_count}")
            self.stat_falhas.setText(f"❌ Falhas: {failed_count}")
            self.stat_cartoes_ok.setText(f"💳 Cartões Aprovados: {cards_approved_count}")
            self.stat_cartoes_fail.setText(f"💳 Cartões Reprovados: {cards_rejected_count}")
        finally:
            # Reabilitar atualizações visuais
            self.premium_edit.setUpdatesEnabled(True)
            self.cards_approved_edit.setUpdatesEnabled(True)
            self.cards_rejected_edit.setUpdatesEnabled(True)
        
        self.update_stats()
    
    def update_stats(self):
        """Atualiza as estatísticas"""
        contas_count = len([l for l in self.accounts_edit.toPlainText().split('\n') if l.strip()])
        self.contas_label.setText(f"📧 Contas: {contas_count}")
        
        cartoes_count = len([l for l in self.cards_edit.toPlainText().split('\n') if l.strip()])
        self.cartoes_label.setText(f"💳 Cartões: {cartoes_count}")
        
        premium_count = len([l for l in self.premium_edit.toPlainText().split('\n') if l.strip()])
        self.premium_label.setText(f"✅ Premium: {premium_count}")
    
    def save_accounts(self):
        """Salva as contas no arquivo"""
        contas_path = os.path.join(self.bot_path, 'data', 'contas.txt')
        os.makedirs(os.path.dirname(contas_path), exist_ok=True)
        
        with open(contas_path, 'w', encoding='utf-8') as f:
            f.write(self.accounts_edit.toPlainText())
        
        self.update_stats()
        QMessageBox.information(self, "Sucesso", "Contas salvas com sucesso!")
    
    def save_cards(self):
        """Salva os cartões no arquivo"""
        cartoes_path = os.path.join(self.bot_path, 'data', 'cartoes.txt')
        os.makedirs(os.path.dirname(cartoes_path), exist_ok=True)
        
        with open(cartoes_path, 'w', encoding='utf-8') as f:
            f.write(self.cards_edit.toPlainText())
        
        self.update_stats()
        QMessageBox.information(self, "Sucesso", "Cartões salvos com sucesso!")
    
    def load_accounts_file(self):
        """Carrega contas de um arquivo externo"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Carregar Contas", "", "Text Files (*.txt);;All Files (*)")
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
                current = self.accounts_edit.toPlainText()
                if current.strip():
                    self.accounts_edit.setText(current + '\n' + '\n'.join(lines))
                else:
                    self.accounts_edit.setText('\n'.join(lines))
            self.update_stats()
    
    def load_cards_file(self):
        """Carrega cartões de um arquivo externo"""
        filepath, _ = QFileDialog.getOpenFileName(self, "Carregar Cartões", "", "Text Files (*.txt);;All Files (*)")
        if filepath:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = [l for l in content.split('\n') if l.strip() and not l.strip().startswith('#')]
                current = self.cards_edit.toPlainText()
                if current.strip():
                    self.cards_edit.setText(current + '\n' + '\n'.join(lines))
                else:
                    self.cards_edit.setText('\n'.join(lines))
            self.update_stats()
    
    def copy_premium(self):
        """Copia as contas premium"""

        text = self.premium_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Sucesso", "Contas premium copiadas!")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhuma conta premium para copiar!")
    
    def copy_premium_simple(self):
        """Copia as contas premium no formato email:senha"""

        
        simple_path = os.path.join(self.bot_path, 'data', 'contas_premium_simples.txt')
        if os.path.exists(simple_path):
            with open(simple_path, 'r', encoding='utf-8') as f:
                text = f.read()
            if text.strip():
                QApplication.clipboard().setText(text)
                QMessageBox.information(self, "Sucesso", "Contas copiadas no formato email:senha!")
                return
        
        QMessageBox.warning(self, "Aviso", "Nenhuma conta para copiar!")
    
    def clear_premium(self):
        """Limpa as contas premium"""
        reply = QMessageBox.question(
            self, "Confirmar",
            "Tem certeza que deseja limpar todas as contas premium?\n\nEsta ação não pode ser desfeita!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.premium_edit.clear()
            
            # Limpar arquivos
            data_path = os.path.join(self.bot_path, 'data')
            for filename in ['contas_premium.txt', 'contas_premium_simples.txt']:
                filepath = os.path.join(data_path, filename)
                if os.path.exists(filepath):
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write('')
            
            self.load_results()
            self.append_console("[SISTEMA] Contas premium limpas")
    
    def copy_cards_approved(self):
        """Copia os cartões aprovados"""

        text = self.cards_approved_edit.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Sucesso", "Cartões aprovados copiados!")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum cartão aprovado para copiar!")
    
    def clear_cards_approved(self):
        """Limpa os cartões aprovados"""
        reply = QMessageBox.question(
            self, "Confirmar",
            "Tem certeza que deseja limpar todos os cartões aprovados?\n\nEsta ação não pode ser desfeita!",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.cards_approved_edit.clear()
            
            filepath = os.path.join(self.bot_path, 'data', 'cartoes_aprovados.txt')
            if os.path.exists(filepath):
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('')
            
            self.load_results()
            self.append_console("[SISTEMA] Cartões aprovados limpos")
    
    def clear_cards_rejected(self):
        """Limpa os cartões reprovados"""
        self.cards_rejected_edit.clear()
        
        filepath = os.path.join(self.bot_path, 'data', 'cartoes_falhos.txt')
        if os.path.exists(filepath):
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write('')
        
        self.load_results()
        self.append_console("[SISTEMA] Cartões reprovados limpos")
    
    def install_dependencies(self):
        """Instala as dependências do Node.js"""
        reply = QMessageBox.question(
            self, "Instalar Dependências",
            "Isso irá executar 'npm install' para instalar as dependências do bot.\n\n"
            "Certifique-se de que o Node.js está instalado.\n\n"
            "Deseja continuar?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.install_deps_btn.setEnabled(False)
            self.install_deps_btn.setText("⏳ Instalando...")
            self.start_btn.setEnabled(False)
            
            self.install_thread = InstallDependenciesThread(self.bot_path)
            self.install_thread.output_signal.connect(self.append_console)
            self.install_thread.finished_signal.connect(self.install_finished)
            self.install_thread.start()
    
    def install_finished(self, success, message):
        """Chamado quando a instalação termina"""
        self.start_btn.setEnabled(True)
        
        if success:
            self.dependencies_installed = True
            self.update_dependency_status()
            QMessageBox.information(self, "Sucesso", message)
        else:
            self.install_deps_btn.setEnabled(True)
            self.install_deps_btn.setText("📦 Instalar Dependências")
            QMessageBox.critical(self, "Erro", message)
    
    def start_bot(self):
        """Inicia o bot Crunchyroll"""
        if not self.accounts_edit.toPlainText().strip():
            QMessageBox.warning(self, "Aviso", "Adicione contas antes de iniciar!")
            return
        
        if not self.cards_edit.toPlainText().strip():
            QMessageBox.warning(self, "Aviso", "Adicione cartões antes de iniciar!")
            return
        
        if not self.dependencies_installed:
            reply = QMessageBox.question(
                self, "Dependências não instaladas",
                "As dependências do Node.js não estão instaladas.\n\n"
                "Deseja instalar agora?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                self.install_dependencies()
            return
        
        # Salvar arquivos
        self.save_accounts()
        self.save_cards()
        
        # Número de workers
        num_workers = self.num_browsers_spin.value() if self.multi_browser_checkbox.isChecked() else 1
        
        # Iniciar thread
        self.bot_thread = CrunchyrollBotThread(self.bot_path, num_workers, self.proxy_config)
        self.bot_thread.output_signal.connect(self.append_console)
        self.bot_thread.finished_signal.connect(self.bot_finished)
        self.bot_thread.error_signal.connect(self.bot_error)
        self.bot_thread.dependencies_missing.connect(self.on_dependencies_missing)
        self.bot_thread.start()
        
        # Atualizar UI
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.skip_btn.setEnabled(True)
        self.multi_browser_checkbox.setEnabled(False)
        self.num_browsers_spin.setEnabled(False)
        self.status_label.setText(f"🟢 Bot em execução ({num_workers} navegador(es))...")
        self.status_label.setStyleSheet(cr_status_qss("#10b981", 16))
        
        self.append_console("[SISTEMA] Bot iniciado!")
        self.append_console(f"[SISTEMA] Usando {num_workers} navegador(es) simultâneo(s)")
        
        if self.proxy_config.get('enabled'):
            self.append_console(f"[PROXY] Proxy habilitado: {self.proxy_config.get('host')}:{self.proxy_config.get('port')}")
            self.append_console(f"[PROXY] IP único por conta: {'Ativado' if self.proxy_config.get('unique_ip', True) else 'Desativado'}")
    
    def on_dependencies_missing(self):
        """Chamado quando as dependências estão faltando"""
        self.dependencies_installed = False
        self.update_dependency_status()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.multi_browser_checkbox.setEnabled(True)
        self.num_browsers_spin.setEnabled(self.multi_browser_checkbox.isChecked())
        self.status_label.setText("⚠️ Dependências faltando")
        self.status_label.setStyleSheet(cr_status_qss("#f43f5e", 16))
    
    def stop_bot(self):
        """Para o bot Crunchyroll"""
        if self.bot_thread:
            self.bot_thread.stop()
            self.append_console("[SISTEMA] Parando bot...")
    
    def bot_finished(self, return_code):
        """Chamado quando o bot termina"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.multi_browser_checkbox.setEnabled(True)
        self.num_browsers_spin.setEnabled(self.multi_browser_checkbox.isChecked())
        self.status_label.setText("⏸️ Bot parado")
        self.status_label.setStyleSheet(cr_status_qss("#94a3b8", 16))
        
        self.append_console(f"[SISTEMA] Bot finalizado (código: {return_code})")
        self.load_results()
    
    def bot_error(self, error):
        """Chamado quando ocorre erro no bot"""
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)
        self.multi_browser_checkbox.setEnabled(True)
        self.num_browsers_spin.setEnabled(self.multi_browser_checkbox.isChecked())
        self.status_label.setText("❌ Erro no bot")
        self.status_label.setStyleSheet(cr_status_qss("#da3633", 16))
        
        self.append_console(f"[ERRO] {error}")
        QMessageBox.critical(self, "Erro", error)
    
    def skip_account(self):
        """Envia comando para pular a conta atual"""
        if self.bot_thread and self.bot_thread.process:
            try:
                if sys.platform == 'win32':
                    self.bot_thread.process.stdin.write(b's')
                    self.bot_thread.process.stdin.flush()
                else:
                    import signal
                    self.bot_thread.process.send_signal(signal.SIGUSR1)
                
                self.append_console("[SISTEMA] Comando para pular conta enviado!")
            except Exception as e:
                self.append_console(f"[AVISO] Não foi possível enviar comando: {str(e)}")
        else:
            self.append_console("[AVISO] Bot não está em execução")
    
    def append_console(self, text):
        """Adiciona texto ao console avançado - OTIMIZADO v9.1
        
        Otimizações:
        - Throttling de load_results para evitar chamadas excessivas
        - Evita travamentos quando muitos logs chegam rapidamente
        """
        import time
        
        self.advanced_console.append(text)
        
        # Recarregar dados se necessário (com throttling)
        text_lower = text.lower()
        if any(keyword in text_lower for keyword in [
            'cartao removido', 'cartão removido',
            'conta processada', 'sucesso', 'aprovado', 'premium',
            'completed', 'failed', 'verificador'
        ]):
            self._schedule_results_update()
    
    def _schedule_results_update(self):
        """Agenda atualização de resultados com throttling - OTIMIZADO v9.1"""
        import time
        
        current_time = time.time() * 1000  # em ms
        time_since_last = current_time - self._last_results_update
        
        if time_since_last >= self.RESULTS_UPDATE_INTERVAL:
            # Pode atualizar imediatamente
            self._last_results_update = current_time
            self._do_results_update()
        elif not self._results_update_pending:
            # Agendar atualização futura
            self._results_update_pending = True
            wait_time = int(self.RESULTS_UPDATE_INTERVAL - time_since_last)
            QTimer.singleShot(wait_time, self._do_results_update)
    
    def _do_results_update(self):
        """Executa a atualização de resultados"""
        import time
        
        self._results_update_pending = False
        self._last_results_update = time.time() * 1000
        
        # Executar atualizações
        self.load_results()
        self.load_verificador_results()

    # ========== FUNÇÕES DE ATUALIZAÇÃO (REMOVER UTILIZADOS) ==========
    
    def refresh_accounts_remove_used(self):
        """
        Remove contas já utilizadas da lista.
        Verifica nos arquivos de resultados quais contas já foram processadas:
        - contas_premium.txt (aprovadas)
        - contas_premium_simples.txt (aprovadas simples)
        - contas_criadas.txt (criadas)
        - contas_login_sucesso.txt (login OK)
        - contas_login_falhou.txt (login falhou)
        - contas_sem_cartao.txt (sem cartão)
        - contas_sem_pagamento.txt (sem pagamento)
        """
        data_path = os.path.join(self.bot_path, 'data')
        
        # Coletar todos os emails já utilizados
        emails_utilizados = set()
        
        arquivos_resultados = [
            'contas_premium.txt',
            'contas_premium_simples.txt',
            'contas_criadas.txt',
            'contas_login_sucesso.txt',
            'contas_login_falhou.txt',
            'contas_sem_cartao.txt',
            'contas_sem_pagamento.txt'
        ]
        
        for arquivo in arquivos_resultados:
            filepath = os.path.join(data_path, arquivo)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for linha in f:
                            linha = linha.strip()
                            if linha and not linha.startswith('#'):
                                # Extrair email da linha (pode estar em vários formatos)
                                # Formatos: email:senha, email|senha, email:senha|cartao|..., etc.
                                email = None
                                if '@' in linha:
                                    # Encontrar o email na linha
                                    partes = re.split(r'[:|,\s]+', linha)
                                    for parte in partes:
                                        if '@' in parte:
                                            email = parte.lower().strip()
                                            break
                                
                                if email:
                                    emails_utilizados.add(email)
                except Exception as e:
                    self.append_console(f"[AVISO] Erro ao ler {arquivo}: {str(e)}")
        
        if not emails_utilizados:
            QMessageBox.information(self, "Informação", "Nenhuma conta utilizada encontrada nos arquivos de resultados.")
            return
        
        # Filtrar contas atuais
        contas_atuais = self.accounts_edit.toPlainText().strip().split('\n')
        contas_filtradas = []
        contas_removidas = 0
        
        for conta in contas_atuais:
            conta = conta.strip()
            if not conta or conta.startswith('#'):
                continue
            
            # Extrair email da conta
            email = None
            partes = re.split(r'[:|]+', conta)
            if len(partes) >= 1 and '@' in partes[0]:
                email = partes[0].lower().strip()
            
            if email and email in emails_utilizados:
                contas_removidas += 1
                self.append_console(f"[ATUALIZAR] Conta removida: {email}")
            else:
                contas_filtradas.append(conta)
        
        # Atualizar o campo de texto
        self.accounts_edit.setText('\n'.join(contas_filtradas))
        self.update_stats()
        
        # Mostrar resultado
        msg = f"Atualização concluída!\n\n"
        msg += f"• Contas removidas: {contas_removidas}\n"
        msg += f"• Contas restantes: {len(contas_filtradas)}\n\n"
        msg += f"Emails únicos encontrados nos resultados: {len(emails_utilizados)}"
        
        QMessageBox.information(self, "Atualização de Contas", msg)
        self.append_console(f"[ATUALIZAR] {contas_removidas} contas removidas, {len(contas_filtradas)} restantes")
    
    def refresh_cards_remove_used(self):
        """
        Remove cartões já utilizados da lista.
        Verifica nos arquivos de resultados quais cartões já foram processados:
        - cartoes_aprovados.txt (aprovados)
        - cartoes_falhos.txt (reprovados)
        """
        data_path = os.path.join(self.bot_path, 'data')
        
        # Coletar todos os números de cartão já utilizados
        cartoes_utilizados = set()
        
        arquivos_resultados = [
            'cartoes_aprovados.txt',
            'cartoes_falhos.txt'
        ]
        
        for arquivo in arquivos_resultados:
            filepath = os.path.join(data_path, arquivo)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for linha in f:
                            linha = linha.strip()
                            if linha and not linha.startswith('#'):
                                # Extrair número do cartão (primeiros 16 dígitos ou até o primeiro separador)
                                partes = re.split(r'[|:,\s]+', linha)
                                if partes:
                                    # O número do cartão é geralmente o primeiro campo
                                    numero = partes[0].strip()
                                    # Remover caracteres não numéricos
                                    numero_limpo = re.sub(r'\D', '', numero)
                                    if len(numero_limpo) >= 13:  # Cartões têm pelo menos 13 dígitos
                                        cartoes_utilizados.add(numero_limpo)
                except Exception as e:
                    self.append_console(f"[AVISO] Erro ao ler {arquivo}: {str(e)}")
        
        if not cartoes_utilizados:
            QMessageBox.information(self, "Informação", "Nenhum cartão utilizado encontrado nos arquivos de resultados.")
            return
        
        # Filtrar cartões atuais
        cartoes_atuais = self.cards_edit.toPlainText().strip().split('\n')
        cartoes_filtrados = []
        cartoes_removidos = 0
        
        for cartao in cartoes_atuais:
            cartao = cartao.strip()
            if not cartao or cartao.startswith('#'):
                continue
            
            # Extrair número do cartão
            partes = re.split(r'[|:]+', cartao)
            if partes:
                numero = partes[0].strip()
                numero_limpo = re.sub(r'\D', '', numero)
                
                if numero_limpo in cartoes_utilizados:
                    cartoes_removidos += 1
                    # Mostrar apenas os últimos 4 dígitos por segurança
                    self.append_console(f"[ATUALIZAR] Cartão removido: ****{numero_limpo[-4:]}")
                else:
                    cartoes_filtrados.append(cartao)
            else:
                cartoes_filtrados.append(cartao)
        
        # Atualizar o campo de texto
        self.cards_edit.setText('\n'.join(cartoes_filtrados))
        self.update_stats()
        
        # Mostrar resultado
        msg = f"Atualização concluída!\n\n"
        msg += f"• Cartões removidos: {cartoes_removidos}\n"
        msg += f"• Cartões restantes: {len(cartoes_filtrados)}\n\n"
        msg += f"Cartões únicos encontrados nos resultados: {len(cartoes_utilizados)}"
        
        QMessageBox.information(self, "Atualização de Cartões", msg)
        self.append_console(f"[ATUALIZAR] {cartoes_removidos} cartões removidos, {len(cartoes_filtrados)} restantes")

    # ========== FUNÇÕES DE ATUALIZAÇÃO AUTOMÁTICA v9.2 ==========
    
    def _setup_auto_refresh_timer(self):
        """Configura o timer de atualização automática"""
        self._auto_refresh_timer = QTimer(self)
        self._auto_refresh_timer.timeout.connect(self._auto_refresh_callback)
        self._auto_refresh_timer.start(self.AUTO_REFRESH_INTERVAL)
        self.append_console(f"[SISTEMA] Atualização automática configurada: a cada {self.AUTO_REFRESH_INTERVAL // 1000} segundos")
    
    def _auto_refresh_callback(self):
        """Callback do timer de atualização automática"""
        if not self._auto_refresh_enabled:
            return
        
        # Só atualizar se o bot estiver rodando
        if self.bot_thread and self.bot_thread.isRunning():
            self._perform_auto_refresh()
    
    def _perform_auto_refresh(self):
        """Executa a atualização automática de cartões e contas"""
        try:
            # Atualizar silenciosamente (sem mensagens de popup)
            self._auto_refresh_cards_silent()
            self._auto_refresh_accounts_silent()
            
            # Recarregar resultados
            self.load_results()
            
            # Log discreto
            timestamp = datetime.now().strftime('%H:%M:%S')
            self.append_console(f"[AUTO-REFRESH] {timestamp} - Listas atualizadas automaticamente")
        except Exception as e:
            self.append_console(f"[AUTO-REFRESH] Erro na atualização automática: {str(e)}")
    
    def _auto_refresh_cards_silent(self):
        """Remove cartões já utilizados silenciosamente (sem popup)"""
        data_path = os.path.join(self.bot_path, 'data')
        
        # Coletar todos os números de cartão já utilizados
        cartoes_utilizados = set()
        
        arquivos_resultados = ['cartoes_aprovados.txt', 'cartoes_falhos.txt']
        
        for arquivo in arquivos_resultados:
            filepath = os.path.join(data_path, arquivo)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for linha in f:
                            linha = linha.strip()
                            if linha and not linha.startswith('#'):
                                partes = re.split(r'[|:,\s]+', linha)
                                if partes:
                                    numero = partes[0].strip()
                                    numero_limpo = re.sub(r'\D', '', numero)
                                    if len(numero_limpo) >= 13:
                                        cartoes_utilizados.add(numero_limpo)
                except Exception:
                    pass
        
        if not cartoes_utilizados:
            return
        
        # Filtrar cartões atuais
        cartoes_atuais = self.cards_edit.toPlainText().strip().split('\n')
        cartoes_filtrados = []
        cartoes_removidos = 0
        
        for cartao in cartoes_atuais:
            cartao = cartao.strip()
            if not cartao or cartao.startswith('#'):
                continue
            
            partes = re.split(r'[|:]+', cartao)
            if partes:
                numero = partes[0].strip()
                numero_limpo = re.sub(r'\D', '', numero)
                
                if numero_limpo in cartoes_utilizados:
                    cartoes_removidos += 1
                else:
                    cartoes_filtrados.append(cartao)
            else:
                cartoes_filtrados.append(cartao)
        
        if cartoes_removidos > 0:
            self.cards_edit.setText('\n'.join(cartoes_filtrados))
            self.update_stats()
            self.append_console(f"[AUTO-REFRESH] {cartoes_removidos} cartões removidos automaticamente")
    
    def _auto_refresh_accounts_silent(self):
        """Remove contas já utilizadas silenciosamente (sem popup)"""
        data_path = os.path.join(self.bot_path, 'data')
        
        # Coletar todos os emails já utilizados
        emails_utilizados = set()
        
        arquivos_resultados = [
            'contas_premium.txt', 'contas_premium_simples.txt', 'contas_criadas.txt',
            'contas_login_sucesso.txt', 'contas_login_falhou.txt',
            'contas_sem_cartao.txt', 'contas_sem_pagamento.txt'
        ]
        
        for arquivo in arquivos_resultados:
            filepath = os.path.join(data_path, arquivo)
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        for linha in f:
                            linha = linha.strip()
                            if linha and not linha.startswith('#'):
                                if '@' in linha:
                                    partes = re.split(r'[:|,\s]+', linha)
                                    for parte in partes:
                                        if '@' in parte:
                                            emails_utilizados.add(parte.lower().strip())
                                            break
                except Exception:
                    pass
        
        if not emails_utilizados:
            return
        
        # Filtrar contas atuais
        contas_atuais = self.accounts_edit.toPlainText().strip().split('\n')
        contas_filtradas = []
        contas_removidas = 0
        
        for conta in contas_atuais:
            conta = conta.strip()
            if not conta or conta.startswith('#'):
                continue
            
            partes = re.split(r'[:|]+', conta)
            if len(partes) >= 1 and '@' in partes[0]:
                email = partes[0].lower().strip()
                if email in emails_utilizados:
                    contas_removidas += 1
                else:
                    contas_filtradas.append(conta)
            else:
                contas_filtradas.append(conta)
        
        if contas_removidas > 0:
            self.accounts_edit.setText('\n'.join(contas_filtradas))
            self.update_stats()
            self.append_console(f"[AUTO-REFRESH] {contas_removidas} contas removidas automaticamente")
    
    def toggle_auto_refresh(self, enabled):
        """Habilita/desabilita a atualização automática"""
        self._auto_refresh_enabled = enabled
        status = "habilitada" if enabled else "desabilitada"
        self.append_console(f"[SISTEMA] Atualização automática {status}")
    
    def set_auto_refresh_interval(self, interval_seconds):
        """Define o intervalo de atualização automática em segundos"""
        if interval_seconds < 30:
            interval_seconds = 30  # Mínimo de 30 segundos
        
        self.AUTO_REFRESH_INTERVAL = interval_seconds * 1000
        
        if self._auto_refresh_timer:
            self._auto_refresh_timer.stop()
            self._auto_refresh_timer.start(self.AUTO_REFRESH_INTERVAL)
        
        self.append_console(f"[SISTEMA] Intervalo de atualização automática: {interval_seconds} segundos")
