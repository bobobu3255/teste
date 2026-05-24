#!/usr/bin/env python3
"""
Aplicação Principal - Coletor de Dados Telegram
Versão 11.0 - Interface Reorganizada + Acesso Rápido às Ferramentas
"""
import sys
import os
import asyncio
import json
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QMessageBox, QDialog, QFormLayout, QLineEdit,
    QSpinBox, QCheckBox, QScrollArea, QTableWidget, QTableWidgetItem,
    QHeaderView, QProgressBar, QTabWidget, QGroupBox, QComboBox,
    QFileDialog, QStatusBar, QFrame, QInputDialog, QListWidget,
    QListWidgetItem, QTextEdit, QSplitter, QRadioButton, QButtonGroup,
    QSystemTrayIcon, QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer, QSettings
from PyQt5.QtGui import QFont, QIcon, QPalette, QColor, QPixmap, QPainter, QBrush, QLinearGradient, QPen
import ctypes

from database import DatabaseManager
from collector import TelegramCollector
from config_manager import ConfigManager
from settings import settings, BASE_DIR
from account_manager import GerenciadorContas
from card_generator import CardGenerator
from address_generator import AddressGenerator
from account_formatter import AccountFormatter
from data_organizer import DataOrganizer
from extra_tools import ValidadorWidget, GeradorFakeWidget, BackupWidget, BuscaAvancadaWidget, DashboardWidget
from browser_widget import BrowserWidget
from notepad_widget import NotepadWidget

# Importar widget de configurações padrão de perfis
try:
    from profile_defaults_widget import ProfileDefaultsWidget
    PROFILE_DEFAULTS_AVAILABLE = True
except ImportError:
    PROFILE_DEFAULTS_AVAILABLE = False

# Importar widget do Bot Crunchyroll
try:
    from crunchyroll_widget import CrunchyrollWidget
    CRUNCHYROLL_AVAILABLE = True
except ImportError:
    CRUNCHYROLL_AVAILABLE = False


# Importar widget do Bot Crunchyroll LOGIN
try:
    from crunchyroll_login_widget import CrunchyrollLoginWidget
    CRUNCHYROLL_LOGIN_AVAILABLE = True
except ImportError:
    CRUNCHYROLL_LOGIN_AVAILABLE = False


# Importar temas do módulo centralizado
from theme import DARK_STYLE_PRO as DARK_STYLE, LIGHT_STYLE_PRO as LIGHT_STYLE



class CodeInputDialog(QDialog):
    """Diálogo para entrada do código SMS do Telegram"""
    
    def __init__(self, phone: str, parent=None):
        super().__init__(parent)
        self.phone = phone
        self.code = None
        self.setWindowTitle("Código de Verificação")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet(DARK_STYLE)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("📱 Código de Verificação do Telegram")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #06b6d4;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        info = QLabel(f"Um código foi enviado para:\n{self.phone}\n\nDigite o código recebido:")
        info.setStyleSheet("color: #aaa; margin: 15px 0;")
        info.setWordWrap(True)
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Ex: 12345")
        self.code_input.setMaxLength(10)
        self.code_input.setStyleSheet("""
            QLineEdit {
                font-size: 28px;
                font-weight: bold;
                text-align: center;
                padding: 15px;
                letter-spacing: 10px;
                background-color: #0f172a;
                border: 3px solid #06b6d4;
                border-radius: 12px;
                color: #06b6d4;
            }
        """)
        self.code_input.setAlignment(Qt.AlignCenter)
        self.code_input.returnPressed.connect(self.submit_code)
        layout.addWidget(self.code_input)
        
        layout.addSpacing(15)
        
        btn_layout = QHBoxLayout()
        
        submit_btn = QPushButton("✓ Confirmar")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #06b6d4;
                color: #0f172a;
                font-size: 14px;
                padding: 12px 30px;
            }
            QPushButton:hover { background-color: #0891b2; }
        """)
        submit_btn.clicked.connect(self.submit_code)
        btn_layout.addWidget(submit_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.setStyleSheet("""
            QPushButton {
                background-color: #f43f5e;
                padding: 12px 30px;
            }
            QPushButton:hover { background-color: #e11d48; }
        """)
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.code_input.setFocus()
    
    def submit_code(self):
        code = self.code_input.text().strip()
        if code:
            self.code = code
            self.accept()
        else:
            QMessageBox.warning(self, "Aviso", "Digite o código de verificação!")


class PasswordInputDialog(QDialog):
    """Diálogo para entrada da senha 2FA"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.password = None
        self.setWindowTitle("Autenticação 2FA")
        self.setModal(True)
        self.setMinimumWidth(400)
        self.setStyleSheet(DARK_STYLE)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("🔐 Autenticação de Dois Fatores")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #ff9800;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        info = QLabel("Sua conta possui 2FA.\nDigite sua senha do Telegram:")
        info.setStyleSheet("color: #aaa; margin: 15px 0;")
        info.setAlignment(Qt.AlignCenter)
        layout.addWidget(info)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha 2FA")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setStyleSheet("""
            QLineEdit {
                font-size: 16px;
                padding: 12px;
                border: 3px solid #ff9800;
            }
        """)
        self.password_input.returnPressed.connect(self.submit_password)
        layout.addWidget(self.password_input)
        
        layout.addSpacing(15)
        
        btn_layout = QHBoxLayout()
        
        submit_btn = QPushButton("✓ Confirmar")
        submit_btn.setStyleSheet("""
            QPushButton {
                background-color: #ff9800;
                color: #0f172a;
                padding: 12px 30px;
            }
        """)
        submit_btn.clicked.connect(self.submit_password)
        btn_layout.addWidget(submit_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
        self.password_input.setFocus()
    
    def submit_password(self):
        password = self.password_input.text()
        if password:
            self.password = password
            self.accept()


class GroupManagerDialog(QDialog):
    """Diálogo para gerenciar múltiplos grupos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Gerenciar Grupos")
        self.setModal(True)
        self.setMinimumSize(500, 400)
        self.setStyleSheet(DARK_STYLE)
        self.groups = self.load_groups()
        self.init_ui()
    
    def load_groups(self):
        """Carrega grupos salvos"""
        groups_file = BASE_DIR / 'grupos.json'
        if groups_file.exists():
            try:
                with open(groups_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, PermissionError) as e:
                print(f"Aviso: Erro ao carregar grupos: {e}")
        return [settings.default_group]
    
    def save_groups(self):
        """Salva grupos"""
        groups_file = BASE_DIR / 'grupos.json'
        with open(groups_file, 'w') as f:
            json.dump(self.groups, f)
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("📋 Gerenciar Grupos do Telegram")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #06b6d4;")
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Lista de grupos
        self.group_list = QListWidget()
        for group in self.groups:
            self.group_list.addItem(group)
        layout.addWidget(self.group_list)
        
        # Campo para adicionar
        add_layout = QHBoxLayout()
        self.new_group_input = QLineEdit()
        self.new_group_input.setPlaceholderText("Nome do grupo (ex: PuxadasTr4in)")
        add_layout.addWidget(self.new_group_input)
        
        add_btn = QPushButton("➕ Adicionar")
        add_btn.setStyleSheet("background-color: #4CAF50;")
        add_btn.clicked.connect(self.add_group)
        add_layout.addWidget(add_btn)
        
        layout.addLayout(add_layout)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        remove_btn = QPushButton("🗑️ Remover Selecionado")
        remove_btn.setStyleSheet("background-color: #f43f5e;")
        remove_btn.clicked.connect(self.remove_group)
        btn_layout.addWidget(remove_btn)
        
        close_btn = QPushButton("✓ Salvar e Fechar")
        close_btn.setStyleSheet("background-color: #06b6d4; color: #0f172a;")
        close_btn.clicked.connect(self.save_and_close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def add_group(self):
        group = self.new_group_input.text().strip()
        if group and group not in self.groups:
            self.groups.append(group)
            self.group_list.addItem(group)
            self.new_group_input.clear()
    
    def remove_group(self):
        current = self.group_list.currentItem()
        if current:
            group = current.text()
            self.groups.remove(group)
            self.group_list.takeItem(self.group_list.row(current))
    
    def save_and_close(self):
        self.save_groups()
        self.accept()


class CollectorThread(QThread):
    """Thread para executar a coleta de dados do Telegram"""
    finished = pyqtSignal(int)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    code_requested = pyqtSignal(str)
    password_requested = pyqtSignal()
    
    def __init__(self, groups: list = None, limit: int = 2000, 
                 filtrar_idosos: bool = False, idade_maxima: int = None,
                 exigir_data_nascimento: bool = False, conta_id: int = None):
        super().__init__()
        self.groups = groups or [settings.default_group]
        self.limit = limit
        self.filtrar_idosos = filtrar_idosos
        self.idade_maxima = idade_maxima
        self.exigir_data_nascimento = exigir_data_nascimento
        self.conta_id = conta_id
        self.verification_code = None
        self.password_2fa = None
        self._code_event = asyncio.Event()
        self._password_event = asyncio.Event()
    
    def set_verification_code(self, code: str):
        self.verification_code = code
        if hasattr(self, '_loop') and self._loop:
            self._loop.call_soon_threadsafe(self._code_event.set)
    
    def set_password(self, password: str):
        self.password_2fa = password
        if hasattr(self, '_loop') and self._loop:
            self._loop.call_soon_threadsafe(self._password_event.set)
    
    def run(self):
        try:
            self.progress.emit("Iniciando coletor...")
            
            def progress_callback(msg):
                self.progress.emit(msg)
            
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            self._code_event = asyncio.Event()
            self._password_event = asyncio.Event()
            
            async def code_callback():
                self.progress.emit("📱 Aguardando código de verificação...")
                self.code_requested.emit(settings.telegram_phone)
                await self._code_event.wait()
                return self.verification_code
            
            async def password_callback():
                self.progress.emit("🔐 Aguardando senha 2FA...")
                self.password_requested.emit()
                await self._password_event.wait()
                return self.password_2fa
            
            collector = TelegramCollector(
                progress_callback=progress_callback,
                code_callback=code_callback,
                password_callback=password_callback,
                filtrar_idosos=self.filtrar_idosos,
                idade_maxima=self.idade_maxima,
                exigir_data_nascimento=self.exigir_data_nascimento,
                conta_id=self.conta_id
            )
            
            if len(self.groups) == 1:
                collected = self._loop.run_until_complete(
                    collector.run(self.groups[0], self.limit)
                )
            else:
                collected = self._loop.run_until_complete(
                    collector.run_multiple_groups(self.groups, self.limit)
                )
            
            self.finished.emit(collected)
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if hasattr(self, '_loop') and self._loop:
                self._loop.close()


class ConfigDialog(QDialog):
    """Diálogo para configuração inicial"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Configuração")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.setStyleSheet(DARK_STYLE)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        title = QLabel("⚙️ Configuração do Telegram")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #06b6d4;")
        layout.addWidget(title)
        
        info = QLabel("Obtenha suas credenciais em: https://my.telegram.org/apps")
        info.setStyleSheet("color: #888; margin-bottom: 15px;")
        layout.addWidget(info)
        
        form = QFormLayout()
        
        self.api_id_input = QLineEdit()
        self.api_id_input.setText(str(settings.telegram_api_id) if settings.telegram_api_id else "")
        self.api_id_input.setPlaceholderText("Ex: 12345678")
        form.addRow("API ID:", self.api_id_input)
        
        self.api_hash_input = QLineEdit()
        self.api_hash_input.setText(settings.telegram_api_hash or "")
        self.api_hash_input.setPlaceholderText("Ex: a1b2c3d4e5f6...")
        form.addRow("API Hash:", self.api_hash_input)
        
        self.phone_input = QLineEdit()
        self.phone_input.setText(settings.telegram_phone or "")
        self.phone_input.setPlaceholderText("Ex: +5511999999999")
        form.addRow("Telefone:", self.phone_input)
        
        self.group_input = QLineEdit()
        self.group_input.setText(settings.default_group or "")
        self.group_input.setPlaceholderText("Ex: PuxadasTr4in")
        form.addRow("Grupo padrão:", self.group_input)
        
        layout.addLayout(form)
        
        btn_layout = QHBoxLayout()
        
        save_btn = QPushButton("💾 Salvar")
        save_btn.setStyleSheet("background-color: #06b6d4; color: #0f172a;")
        save_btn.clicked.connect(self.save_config)
        btn_layout.addWidget(save_btn)
        
        cancel_btn = QPushButton("Cancelar")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)
        
        layout.addLayout(btn_layout)
        self.setLayout(layout)
    
    def save_config(self):
        try:
            api_id = int(self.api_id_input.text().strip())
            api_hash = self.api_hash_input.text().strip()
            phone = self.phone_input.text().strip()
            group = self.group_input.text().strip()
            
            if not all([api_id, api_hash, phone, group]):
                QMessageBox.warning(self, "Aviso", "Preencha todos os campos!")
                return
            
            # Usar o método create_env_file para salvar as configurações
            if settings.create_env_file(api_id, api_hash, phone, group):
                QMessageBox.information(self, "Sucesso", "Configurações salvas com sucesso!\nO arquivo .env foi criado.")
            else:
                QMessageBox.critical(self, "Erro", "Falha ao salvar configurações.\nVerifique as permissões de escrita.")
            self.accept()
            
        except ValueError:
            QMessageBox.warning(self, "Erro", "API ID deve ser um número!")


class DataViewDialog(QDialog):
    """Diálogo para visualizar dados coletados"""
    
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("Dados Coletados")
        self.setModal(True)
        self.setMinimumSize(800, 600)
        self.setStyleSheet(DARK_STYLE)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Filtros
        filter_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nome ou CPF...")
        self.search_input.textChanged.connect(self.filter_data)
        filter_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("🔄 Atualizar")
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)
        
        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "CPF", "Nascimento", "Telefone", "Score"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)
        
        # Botões
        btn_layout = QHBoxLayout()
        
        import_btn = QPushButton("📤 Importar CSV")
        import_btn.clicked.connect(self.import_csv)
        btn_layout.addWidget(import_btn)

        export_btn = QPushButton("📥 Exportar CSV")
        export_btn.clicked.connect(self.export_csv)
        btn_layout.addWidget(export_btn)
        
        close_btn = QPushButton("Fechar")
        close_btn.clicked.connect(self.close)
        btn_layout.addWidget(close_btn)
        
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_data()
    
    def load_data(self):
        data = self.db.get_all_data()
        self.table.setRowCount(len(data))
        
        for row, record in enumerate(data):
            self.table.setItem(row, 0, QTableWidgetItem(str(record.get('id', ''))))
            self.table.setItem(row, 1, QTableWidgetItem(record.get('nome', '')))
            self.table.setItem(row, 2, QTableWidgetItem(record.get('cpf', '')))
            self.table.setItem(row, 3, QTableWidgetItem(record.get('nascimento', '')))
            self.table.setItem(row, 4, QTableWidgetItem(record.get('telefone', '')))
            self.table.setItem(row, 5, QTableWidgetItem(str(record.get('score', ''))))
    
    def filter_data(self):
        search = self.search_input.text().lower()
        for row in range(self.table.rowCount()):
            show = False
            for col in range(self.table.columnCount()):
                item = self.table.item(row, col)
                if item and search in item.text().lower():
                    show = True
                    break
            self.table.setRowHidden(row, not show)
    
    def import_csv(self):
        """Importa dados de um arquivo CSV"""
        filepath, _ = QFileDialog.getOpenFileName(
            self, "Importar CSV", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if filepath:
            # Mostrar progresso indeterminado
            progress = QDialog(self)
            progress.setWindowTitle("Importando...")
            progress.setFixedSize(300, 100)
            layout = QVBoxLayout()
            layout.addWidget(QLabel("Lendo arquivo e importando dados...\nIsso pode levar alguns instantes."))
            bar = QProgressBar()
            bar.setRange(0, 0)  # Indeterminado
            layout.addWidget(bar)
            progress.setLayout(layout)
            progress.show()
            QApplication.processEvents()
            
            # Executar importação
            stats = self.db.import_csv(filepath)
            
            progress.close()
            
            # Mostrar resultado
            msg = (f"Importação concluída!\n\n"
                   f"✅ Adicionados: {stats['added']}\n"
                   f"🔄 Atualizados: {stats['updated']}\n"
                   f"⚠️ Erros/Ignorados: {stats['errors']}")
            
            QMessageBox.information(self, "Resultado da Importação", msg)
            
            # Atualizar tabela
            self.load_data()

    def export_csv(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar como CSV", "dados.csv", "CSV Files (*.csv)"
        )
        if filepath:
            mode = 'w'
            if os.path.exists(filepath):
                reply = QMessageBox.question(
                    self, "Arquivo Existente",
                    "O arquivo já existe. Deseja anexar os dados ao final do arquivo?",
                    QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                    QMessageBox.No
                )
                
                if reply == QMessageBox.Cancel:
                    return
                elif reply == QMessageBox.Yes:
                    mode = 'a'
            
            if self.db.export_csv(filepath, 'completo', mode):
                msg = "Dados anexados com sucesso!" if mode == 'a' else "Arquivo exportado com sucesso!"
                QMessageBox.information(self, "Sucesso", f"{msg}\n{filepath}")
            else:
                QMessageBox.critical(self, "Erro", "Erro ao exportar")


class CardGeneratorThread(QThread):
    """Thread para geração de cartões sem travar a interface"""
    
    # Sinais para comunicação com a interface
    progress = pyqtSignal(int, int)  # (atual, total)
    finished_cards = pyqtSignal(list)  # lista de cartões gerados
    error = pyqtSignal(str)  # mensagem de erro
    
    def __init__(self, generator, pattern, quantity, month, year, cvv):
        super().__init__()
        self.generator = generator
        self.pattern = pattern
        self.quantity = quantity
        self.month = month
        self.year = year
        self.cvv = cvv
    
    def run(self):
        """Executa a geração em thread separada"""
        try:
            # Callback para reportar progresso
            def progress_callback(current, total):
                self.progress.emit(current, total)
            
            # Gerar cartões
            cards = self.generator.generate_cards(
                self.pattern, 
                self.quantity, 
                self.month, 
                self.year, 
                self.cvv,
                progress_callback
            )
            
            self.finished_cards.emit(cards)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """Para a geração"""
        self.generator.cancel()


class AddressGeneratorThread(QThread):
    """Thread para geração de endereços sem travar a interface"""
    progress = pyqtSignal(int, int)  # (atual, total)
    finished_addresses = pyqtSignal(list)  # lista de endereços formatados
    error = pyqtSignal(str)  # mensagem de erro
    
    def __init__(self, generator, quantidade, uf=None, cidade=None, com_pontuacao=True):
        super().__init__()
        self.generator = generator
        self.quantidade = quantidade
        self.uf = uf
        self.cidade = cidade
        self.com_pontuacao = com_pontuacao
        self._stop_flag = False
    
    def stop(self):
        """Sinaliza para parar a geração"""
        self._stop_flag = True
        self.generator.cancel()
    
    def run(self):
        try:
            def progress_callback(current, total):
                if not self._stop_flag:
                    self.progress.emit(current, total)
            
            enderecos = self.generator.gerar_enderecos(
                quantidade=self.quantidade,
                uf=self.uf,
                cidade=self.cidade,
                com_pontuacao=self.com_pontuacao,
                progress_callback=progress_callback
            )
            
            # Formatar endereços para exibição
            formatted = []
            for end in enderecos:
                formatted.append(end.format_linha(self.com_pontuacao))
            
            self.finished_addresses.emit(formatted)
            
        except Exception as e:
            self.error.emit(str(e))


class ToolsDialog(QDialog):
    """Diálogo de Ferramentas com Gerador de Cartões e CEP - v4.2 com Modo Claro/Escuro"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🛠️ Ferramentas")
        self.setModal(False)  # Não bloqueia a janela principal
        self.setMinimumSize(750, 800)
        
        # Estado do tema
        self.is_dark_mode = True
        self.setStyleSheet(DARK_STYLE)
        
        self.card_generator = CardGenerator()
        self.address_generator = AddressGenerator()
        self.account_formatter = AccountFormatter()
        self.generated_cards = []
        self.generated_addresses = []
        self.formatted_accounts = ""
        self.generator_thread = None
        self.address_thread = None
        self.is_generating = False
        self.is_generating_addresses = False
        self.is_formatting = False
        
        # Dados do endereço atual
        self.current_address = None
        
        self.init_ui()
    
    def toggle_theme(self):
        """Alterna entre modo claro e escuro"""
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.setStyleSheet(DARK_STYLE)
            self.theme_btn.setText("☀️ Modo Claro")
        else:
            self.setStyleSheet(LIGHT_STYLE)
            self.theme_btn.setText("🌙 Modo Escuro")
        
        # Atualizar estilos dos campos de resultado do CEP
        self.update_cep_field_styles()
    
    def update_cep_field_styles(self):
        """Atualiza os estilos dos campos de resultado do CEP"""
        if self.is_dark_mode:
            field_style = """
                QLineEdit {
                    background-color: #1c1c1e;
                    border: 1px solid #3a3a3c;
                    border-radius: 12px;
                    padding: 12px 16px;
                    font-size: 14px;
                    color: #10b981;
                }
            """
            copy_btn_style = """
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 8px;
                    font-size: 16px;
                    min-width: 40px;
                }
                QPushButton:hover {
                    background-color: #2c2c2e;
                    border-radius: 12px;
                }
            """
        else:
            field_style = """
                QLineEdit {
                    background-color: #ffffff;
                    border: 1px solid #d2d2d7;
                    border-radius: 12px;
                    padding: 12px 16px;
                    font-size: 14px;
                    color: #1d1d1f;
                }
            """
            copy_btn_style = """
                QPushButton {
                    background-color: transparent;
                    border: none;
                    padding: 8px;
                    font-size: 16px;
                    min-width: 40px;
                }
                QPushButton:hover {
                    background-color: #e8e8ed;
                    border-radius: 12px;
                }
            """
        
        # Aplicar estilos
        self.cep_field.setStyleSheet(field_style)
        self.endereco_field.setStyleSheet(field_style)
        self.bairro_field.setStyleSheet(field_style)
        self.cidade_field.setStyleSheet(field_style)
        self.estado_field.setStyleSheet(field_style)
        
        self.copy_cep_btn.setStyleSheet(copy_btn_style)
        self.copy_endereco_btn.setStyleSheet(copy_btn_style)
        self.copy_bairro_btn.setStyleSheet(copy_btn_style)
        self.copy_cidade_btn.setStyleSheet(copy_btn_style)
        self.copy_estado_btn.setStyleSheet(copy_btn_style)
    
    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(24)
        main_layout.setContentsMargins(32, 32, 32, 32)
        
        # Header com título e botão de tema
        header_layout = QHBoxLayout()
        
        # Título - Estilo Apple
        title = QLabel("Ferramentas")
        title.setFont(QFont('-apple-system', 28, QFont.Bold))
        title.setStyleSheet("color: #ffffff; letter-spacing: -0.5px;")
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botão de alternar tema
        self.theme_btn = QPushButton("☀️ Modo Claro")
        self.theme_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2e;
                color: #ffffff;
                border: none;
                border-radius: 12px;
                padding: 10px 16px;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #3a3a3c;
            }
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)
        
        main_layout.addLayout(header_layout)
        
        # Tabs de ferramentas - Estilo Apple
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
                margin-top: 8px;
            }
            QTabBar::tab {
                background: transparent;
                color: #64748b;
                padding: 12px 28px;
                margin-right: 8px;
                border: none;
                border-bottom: 2px solid transparent;
                font-weight: 500;
                font-size: 14px;
            }
            QTabBar::tab:selected {
                color: #06b6d4;
                border-bottom: 2px solid #06b6d4;
            }
            QTabBar::tab:hover {
                color: #ffffff;
            }
        """)
        
        # Aba do Gerador de Cartões
        card_tab = self.create_card_generator_tab()
        self.tabs.addTab(card_tab, "💳 Gerador de Cartões")
        
        # Aba do Gerador de CEP (novo layout)
        address_tab = self.create_cep_generator_tab()
        self.tabs.addTab(address_tab, "🏠 Gerador de CEP")
        
        # Aba do Formatador de Contas Premium
        accounts_tab = self.create_account_formatter_tab()
        self.tabs.addTab(accounts_tab, "📧 Formatador de Contas")

        # Aba do Organizador de Dados (NOVA)
        organizer_tab = DataOrganizer()
        self.tabs.addTab(organizer_tab, "🗂️ Organizador")
        
        # === NOVAS FERRAMENTAS v8.0 ===
        
        # Aba do Validador de CPF/CNPJ
        validador_tab = ValidadorWidget()
        self.tabs.addTab(validador_tab, "✅ Validador")
        
        # Aba do Gerador de Dados Fake
        gerador_fake_tab = GeradorFakeWidget()
        self.tabs.addTab(gerador_fake_tab, "🎭 Dados Fake")
        
        # Aba de Backup
        backup_tab = BackupWidget()
        self.tabs.addTab(backup_tab, "💾 Backup")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)
    
    def create_card_generator_tab(self):
        """Cria a aba do gerador de cartões"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Grupo de configuração - Estilo Apple
        config_group = QGroupBox("CONFIGURAÇÃO")
        config_group.setStyleSheet("""
            QGroupBox {
                background-color: #1c1c1e;
                border: none;
                border-radius: 16px;
                margin-top: 24px;
                padding: 24px;
                padding-top: 40px;
            }
            QGroupBox::title {
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 1px;
            }
        """)
        config_layout = QVBoxLayout()
        config_layout.setSpacing(16)
        
        # Padrão do cartão
        pattern_layout = QHBoxLayout()
        pattern_label = QLabel("Padrão")
        pattern_label.setStyleSheet("font-weight: 500; min-width: 80px; color: #64748b;")
        pattern_layout.addWidget(pattern_label)
        
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Ex: 406669994713XXXX (X = dígitos aleatórios)")
        self.pattern_input.setStyleSheet("""
            QLineEdit {
                background-color: #2c2c2e;
                border: none;
                border-radius: 12px;
                padding: 14px 16px;
                font-size: 14px;
                font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
                color: #ffffff;
            }
            QLineEdit:focus {
                background-color: #3a3a3c;
            }
            QLineEdit::placeholder {
                color: #48484a;
            }
        """)
        pattern_layout.addWidget(self.pattern_input)
        config_layout.addLayout(pattern_layout)
        
        # Linha de expiração e CVV
        exp_layout = QHBoxLayout()
        exp_layout.setSpacing(16)
        
        # Estilo comum para labels
        label_style = "font-weight: 500; color: #64748b;"
        
        # Estilo comum para combos e inputs pequenos
        small_input_style = """
            min-width: 70px;
            background-color: #2c2c2e;
            border: none;
            border-radius: 12px;
            padding: 10px 12px;
        """
        
        # Mês
        mes_label = QLabel("Mês")
        mes_label.setStyleSheet(label_style)
        exp_layout.addWidget(mes_label)
        self.month_combo = QComboBox()
        self.month_combo.addItems([f"{i:02d}" for i in range(1, 13)])
        self.month_combo.setCurrentIndex(9)  # Outubro
        self.month_combo.setStyleSheet(small_input_style)
        exp_layout.addWidget(self.month_combo)
        
        # Ano
        ano_label = QLabel("Ano")
        ano_label.setStyleSheet(label_style)
        exp_layout.addWidget(ano_label)
        self.year_combo = QComboBox()
        current_year = 2025
        self.year_combo.addItems([str(y) for y in range(current_year, current_year + 10)])
        self.year_combo.setStyleSheet(small_input_style)
        exp_layout.addWidget(self.year_combo)
        
        # CVV
        cvv_label = QLabel("CVV")
        cvv_label.setStyleSheet(label_style)
        exp_layout.addWidget(cvv_label)
        self.cvv_combo = QComboBox()
        self.cvv_combo.addItem("Aleatório", "random")
        self.cvv_combo.addItems([f"{i:03d}" for i in range(0, 1000, 111)])
        self.cvv_combo.setStyleSheet(small_input_style)
        exp_layout.addWidget(self.cvv_combo)
        
        # Quantidade
        qtd_label = QLabel("Qtd")
        qtd_label.setStyleSheet(label_style)
        exp_layout.addWidget(qtd_label)
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 10000)
        self.quantity_spin.setValue(10)
        self.quantity_spin.setStyleSheet(small_input_style + "min-width: 90px;")
        exp_layout.addWidget(self.quantity_spin)
        
        exp_layout.addStretch()
        config_layout.addLayout(exp_layout)
        
        config_group.setLayout(config_layout)
        layout.addWidget(config_group)
        
        # Barra de progresso - Estilo Apple
        progress_layout = QVBoxLayout()
        progress_layout.setSpacing(8)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                background-color: #2c2c2e;
                border: none;
                border-radius: 4px;
                height: 6px;
            }
            QProgressBar::chunk {
                background-color: #06b6d4;
                border-radius: 4px;
            }
        """)
        self.progress_bar.hide()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet("color: #06b6d4; font-size: 13px; font-weight: 500;")
        self.progress_label.hide()
        progress_layout.addWidget(self.progress_label)
        
        layout.addLayout(progress_layout)
        
        # Botões de ação - Estilo Apple
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        # Estilos dos botões
        primary_btn_style = """
            QPushButton {
                background-color: #06b6d4;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 14px 28px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #409cff; }
            QPushButton:pressed { background-color: #0071e3; }
            QPushButton:disabled { background-color: #1c1c1e; color: #48484a; }
        """
        
        secondary_btn_style = """
            QPushButton {
                background-color: #2c2c2e;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
                padding: 12px 20px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #3a3a3c; }
        """
        
        destructive_btn_style = """
            QPushButton {
                background-color: #ff453a;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
                padding: 12px 20px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #ff6961; }
        """
        
        self.generate_btn = QPushButton("Gerar Cartões")
        self.generate_btn.setStyleSheet(primary_btn_style)
        self.generate_btn.clicked.connect(self.generate_cards)
        btn_layout.addWidget(self.generate_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setStyleSheet(destructive_btn_style)
        self.cancel_btn.clicked.connect(self.cancel_generation)
        self.cancel_btn.hide()
        btn_layout.addWidget(self.cancel_btn)
        
        copy_btn = QPushButton("Copiar Tudo")
        copy_btn.setStyleSheet(secondary_btn_style)
        copy_btn.clicked.connect(self.copy_cards)
        btn_layout.addWidget(copy_btn)
        
        clear_btn = QPushButton("Limpar")
        clear_btn.setStyleSheet(secondary_btn_style)
        clear_btn.clicked.connect(self.clear_cards)
        btn_layout.addWidget(clear_btn)
        
        layout.addLayout(btn_layout)
        
        # Botões de cópia individual - Estilo Apple
        copy_individual_layout = QHBoxLayout()
        copy_individual_layout.setSpacing(8)
        
        copy_btn_style = """
            QPushButton {
                background-color: #1c1c1e;
                color: #06b6d4;
                font-size: 12px;
                font-weight: 500;
                padding: 10px 14px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #2c2c2e; }
        """
        
        copy_numbers_btn = QPushButton("Números")
        copy_numbers_btn.setStyleSheet(copy_btn_style)
        copy_numbers_btn.clicked.connect(lambda: self.copy_card_field(0, "Número"))
        copy_individual_layout.addWidget(copy_numbers_btn)
        
        copy_months_btn = QPushButton("Meses")
        copy_months_btn.setStyleSheet(copy_btn_style)
        copy_months_btn.clicked.connect(lambda: self.copy_card_field(1, "Mês"))
        copy_individual_layout.addWidget(copy_months_btn)
        
        copy_years_btn = QPushButton("Anos")
        copy_years_btn.setStyleSheet(copy_btn_style)
        copy_years_btn.clicked.connect(lambda: self.copy_card_field(2, "Ano"))
        copy_individual_layout.addWidget(copy_years_btn)
        
        copy_cvvs_btn = QPushButton("CVVs")
        copy_cvvs_btn.setStyleSheet(copy_btn_style)
        copy_cvvs_btn.clicked.connect(lambda: self.copy_card_field(3, "CVV"))
        copy_individual_layout.addWidget(copy_cvvs_btn)
        
        layout.addLayout(copy_individual_layout)
        
        # Área de resultado - Estilo Apple
        result_group = QGroupBox("RESULTADO")
        result_group.setStyleSheet("""
            QGroupBox {
                background-color: #1c1c1e;
                border: none;
                border-radius: 16px;
                margin-top: 20px;
                padding: 20px;
                padding-top: 36px;
            }
            QGroupBox::title {
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 1px;
            }
        """)
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                border: 1px solid #2c2c2e;
                border-radius: 12px;
                padding: 16px;
                font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
                font-size: 13px;
                color: #10b981;
                line-height: 1.6;
            }
        """)
        self.result_text.setPlaceholderText("Os cartões gerados aparecerão aqui...\n\nFormato: NUMERO|MES|ANO|CVV")
        result_layout.addWidget(self.result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # Status - Estilo Apple
        self.status_label = QLabel("Histórico: 0 cartões · Gerados: 0")
        self.status_label.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 400;")
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        tab.setLayout(layout)
        return tab
    
    def create_cep_generator_tab(self):
        """Cria a aba do gerador de CEP com layout similar à imagem de referência"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        
        # Grupo de Opções
        options_group = QGroupBox("OPÇÕES")
        options_group.setStyleSheet("""
            QGroupBox {
                background-color: #1c1c1e;
                border: none;
                border-radius: 16px;
                margin-top: 24px;
                padding: 24px;
                padding-top: 40px;
            }
            QGroupBox::title {
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 1px;
            }
        """)
        options_layout = QVBoxLayout()
        options_layout.setSpacing(16)
        
        # Estilo comum para labels
        label_style = "font-weight: 500; color: #64748b; font-size: 13px;"
        
        # Estilo comum para combos
        combo_style = """
            QComboBox {
                min-width: 200px;
                background-color: #2c2c2e;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                color: #ffffff;
            }
        """
        
        # 1. Estado (opcional)
        estado_layout = QHBoxLayout()
        estado_label = QLabel("1. Estado (opcional):")
        estado_label.setStyleSheet(label_style)
        estado_layout.addWidget(estado_label)
        estado_layout.addStretch()
        options_layout.addLayout(estado_layout)
        
        self.estado_combo = QComboBox()
        self.estado_combo.addItem("Todos", "")
        for uf, nome in self.address_generator.get_estados():
            self.estado_combo.addItem(f"{uf} - {nome}", uf)
        self.estado_combo.setStyleSheet(combo_style)
        self.estado_combo.currentIndexChanged.connect(self.on_estado_changed)
        options_layout.addWidget(self.estado_combo)
        
        # 2. Cidade (opcional)
        cidade_layout = QHBoxLayout()
        cidade_label = QLabel("2. Cidade (opcional):")
        cidade_label.setStyleSheet(label_style)
        cidade_layout.addWidget(cidade_label)
        cidade_layout.addStretch()
        options_layout.addLayout(cidade_layout)
        
        self.cidade_combo = QComboBox()
        self.cidade_combo.addItem("Todas", "")
        self.cidade_combo.setStyleSheet(combo_style)
        options_layout.addWidget(self.cidade_combo)
        
        # 3. Gerar com pontuação?
        pontuacao_layout = QHBoxLayout()
        pontuacao_label = QLabel("3. Gerar com pontuação?")
        pontuacao_label.setStyleSheet(label_style)
        pontuacao_layout.addWidget(pontuacao_label)
        pontuacao_layout.addStretch()
        options_layout.addLayout(pontuacao_layout)
        
        # Radio buttons para pontuação
        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(20)
        
        self.pontuacao_group = QButtonGroup()
        
        self.radio_sim = QRadioButton("Sim")
        self.radio_sim.setChecked(True)
        self.radio_sim.setStyleSheet("color: #ffffff;")
        self.pontuacao_group.addButton(self.radio_sim)
        radio_layout.addWidget(self.radio_sim)
        
        self.radio_nao = QRadioButton("Não")
        self.radio_nao.setStyleSheet("color: #ffffff;")
        self.pontuacao_group.addButton(self.radio_nao)
        radio_layout.addWidget(self.radio_nao)
        
        radio_layout.addStretch()
        options_layout.addLayout(radio_layout)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        # Botão Gerar CEP
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.gerar_cep_btn = QPushButton("↻ GERAR CEP")
        self.gerar_cep_btn.setStyleSheet("""
            QPushButton {
                background-color: #4a7c7e;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 14px 40px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #5a8c8e;
            }
            QPushButton:pressed {
                background-color: #3a6c6e;
            }
        """)
        self.gerar_cep_btn.clicked.connect(self.generate_single_cep)
        btn_layout.addWidget(self.gerar_cep_btn)
        
        btn_layout.addStretch()
        layout.addLayout(btn_layout)
        
        # Grupo de Resultado com campos individuais
        result_group = QGroupBox("")
        result_group.setStyleSheet("""
            QGroupBox {
                background-color: #1c1c1e;
                border: none;
                border-radius: 16px;
                padding: 24px;
            }
        """)
        result_layout = QVBoxLayout()
        result_layout.setSpacing(16)
        
        # Estilo dos campos de resultado
        field_style = """
            QLineEdit {
                background-color: #1c1c1e;
                border: 1px solid #3a3a3c;
                border-radius: 12px;
                padding: 12px 16px;
                font-size: 14px;
                color: #10b981;
            }
        """
        
        copy_btn_style = """
            QPushButton {
                background-color: transparent;
                border: none;
                padding: 8px;
                font-size: 16px;
                min-width: 40px;
            }
            QPushButton:hover {
                background-color: #2c2c2e;
                border-radius: 12px;
            }
        """
        
        field_label_style = "font-weight: 500; color: #64748b; font-size: 12px;"
        
        # CEP
        cep_label = QLabel("CEP")
        cep_label.setStyleSheet(field_label_style)
        result_layout.addWidget(cep_label)
        
        cep_row = QHBoxLayout()
        self.cep_field = QLineEdit()
        self.cep_field.setReadOnly(True)
        self.cep_field.setPlaceholderText("00000-000")
        self.cep_field.setStyleSheet(field_style)
        cep_row.addWidget(self.cep_field)
        
        self.copy_cep_btn = QPushButton("📋")
        self.copy_cep_btn.setStyleSheet(copy_btn_style)
        self.copy_cep_btn.setToolTip("Copiar CEP")
        self.copy_cep_btn.clicked.connect(lambda: self.copy_single_field(self.cep_field, "CEP"))
        cep_row.addWidget(self.copy_cep_btn)
        result_layout.addLayout(cep_row)
        
        # Endereço
        endereco_label = QLabel("Endereço")
        endereco_label.setStyleSheet(field_label_style)
        result_layout.addWidget(endereco_label)
        
        endereco_row = QHBoxLayout()
        self.endereco_field = QLineEdit()
        self.endereco_field.setReadOnly(True)
        self.endereco_field.setPlaceholderText("Rua/Avenida")
        self.endereco_field.setStyleSheet(field_style)
        endereco_row.addWidget(self.endereco_field)
        
        self.copy_endereco_btn = QPushButton("📋")
        self.copy_endereco_btn.setStyleSheet(copy_btn_style)
        self.copy_endereco_btn.setToolTip("Copiar Endereço")
        self.copy_endereco_btn.clicked.connect(lambda: self.copy_single_field(self.endereco_field, "Endereço"))
        endereco_row.addWidget(self.copy_endereco_btn)
        result_layout.addLayout(endereco_row)
        
        # Bairro
        bairro_label = QLabel("Bairro")
        bairro_label.setStyleSheet(field_label_style)
        result_layout.addWidget(bairro_label)
        
        bairro_row = QHBoxLayout()
        self.bairro_field = QLineEdit()
        self.bairro_field.setReadOnly(True)
        self.bairro_field.setPlaceholderText("Bairro")
        self.bairro_field.setStyleSheet(field_style)
        bairro_row.addWidget(self.bairro_field)
        
        self.copy_bairro_btn = QPushButton("📋")
        self.copy_bairro_btn.setStyleSheet(copy_btn_style)
        self.copy_bairro_btn.setToolTip("Copiar Bairro")
        self.copy_bairro_btn.clicked.connect(lambda: self.copy_single_field(self.bairro_field, "Bairro"))
        bairro_row.addWidget(self.copy_bairro_btn)
        result_layout.addLayout(bairro_row)
        
        # Cidade
        cidade_label_result = QLabel("Cidade")
        cidade_label_result.setStyleSheet(field_label_style)
        result_layout.addWidget(cidade_label_result)
        
        cidade_row = QHBoxLayout()
        self.cidade_field = QLineEdit()
        self.cidade_field.setReadOnly(True)
        self.cidade_field.setPlaceholderText("Cidade")
        self.cidade_field.setStyleSheet(field_style)
        cidade_row.addWidget(self.cidade_field)
        
        self.copy_cidade_btn = QPushButton("📋")
        self.copy_cidade_btn.setStyleSheet(copy_btn_style)
        self.copy_cidade_btn.setToolTip("Copiar Cidade")
        self.copy_cidade_btn.clicked.connect(lambda: self.copy_single_field(self.cidade_field, "Cidade"))
        cidade_row.addWidget(self.copy_cidade_btn)
        result_layout.addLayout(cidade_row)
        
        # Estado
        estado_label_result = QLabel("Estado")
        estado_label_result.setStyleSheet(field_label_style)
        result_layout.addWidget(estado_label_result)
        
        estado_row = QHBoxLayout()
        self.estado_field = QLineEdit()
        self.estado_field.setReadOnly(True)
        self.estado_field.setPlaceholderText("UF")
        self.estado_field.setStyleSheet(field_style)
        estado_row.addWidget(self.estado_field)
        
        self.copy_estado_btn = QPushButton("📋")
        self.copy_estado_btn.setStyleSheet(copy_btn_style)
        self.copy_estado_btn.setToolTip("Copiar Estado")
        self.copy_estado_btn.clicked.connect(lambda: self.copy_single_field(self.estado_field, "Estado"))
        estado_row.addWidget(self.copy_estado_btn)
        result_layout.addLayout(estado_row)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # Status
        self.cep_status_label = QLabel("")
        self.cep_status_label.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 400;")
        self.cep_status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.cep_status_label)
        
        layout.addStretch()
        
        tab.setLayout(layout)
        return tab
    
    def on_estado_changed(self, index):
        """Atualiza as cidades quando o estado muda"""
        self.cidade_combo.clear()
        self.cidade_combo.addItem("Todas", "")
        
        uf = self.estado_combo.currentData()
        if uf:
            cidades = self.address_generator.get_cidades(uf)
            for id_cidade, nome_cidade in cidades:
                # Exibe o NOME, mas armazena o ID como dado
                self.cidade_combo.addItem(nome_cidade, id_cidade)
    
    def generate_single_cep(self):
        """Gera um único CEP e exibe nos campos"""
        uf = self.estado_combo.currentData() or None
        cidade = self.cidade_combo.currentData() or None
        com_pontuacao = self.radio_sim.isChecked()
        
        # Gerar um endereço
        endereco = self.address_generator.gerar_endereco(uf, cidade, com_pontuacao)
        
        if endereco:
            self.current_address = endereco
            
            # Preencher os campos
            self.cep_field.setText(endereco.cep)
            self.endereco_field.setText(endereco.logradouro)
            self.bairro_field.setText(endereco.bairro)
            self.cidade_field.setText(endereco.cidade)
            self.estado_field.setText(endereco.uf)
            
            self.cep_status_label.setText("CEP gerado com sucesso!")
            self.cep_status_label.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 400;")
        else:
            self.cep_status_label.setText("Erro ao gerar CEP")
            self.cep_status_label.setStyleSheet("color: #ff453a; font-size: 12px; font-weight: 400;")
    
    def copy_single_field(self, field, field_name):
        """Copia o valor de um campo específico"""
        text = field.text()
        if text:
            QApplication.clipboard().setText(text)
            self.cep_status_label.setText(f"{field_name} copiado!")
            self.cep_status_label.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 400;")
        else:
            self.cep_status_label.setText(f"Nenhum {field_name} para copiar")
            self.cep_status_label.setStyleSheet("color: #ff9f0a; font-size: 12px; font-weight: 400;")
    
    # ===== MÉTODOS DO GERADOR DE CARTÕES =====
    
    def generate_cards(self):
        """Inicia a geração de cartões em thread separada"""
        if self.is_generating:
            return
        
        pattern = self.pattern_input.text().strip()
        if not pattern:
            QMessageBox.warning(self, "Aviso", "Digite um padrão de cartão!")
            return
        
        quantity = self.quantity_spin.value()
        month = self.month_combo.currentText()
        year = self.year_combo.currentText()
        cvv = self.cvv_combo.currentData() if self.cvv_combo.currentIndex() == 0 else self.cvv_combo.currentText()
        
        # Preparar interface para geração
        self.is_generating = True
        self.generate_btn.setEnabled(False)
        self.cancel_btn.show()
        self.progress_bar.show()
        self.progress_label.show()
        self.progress_bar.setRange(0, quantity)
        self.progress_bar.setValue(0)
        self.progress_label.setText("Iniciando geração...")
        self.result_text.clear()
        
        # Resetar flag de cancelamento
        self.card_generator.reset_cancel()
        
        # Criar e iniciar thread
        self.generator_thread = CardGeneratorThread(
            self.card_generator, pattern, quantity, month, year, cvv
        )
        self.generator_thread.progress.connect(self.on_progress)
        self.generator_thread.finished_cards.connect(self.on_generation_finished)
        self.generator_thread.error.connect(self.on_generation_error)
        self.generator_thread.start()
    
    def on_progress(self, current, total):
        """Atualiza a barra de progresso"""
        self.progress_bar.setValue(current)
        percent = (current / total) * 100 if total > 0 else 0
        self.progress_label.setText(f"⚡ Gerando: {current}/{total} cartões ({percent:.1f}%)")
    
    def on_generation_finished(self, cards):
        """Chamado quando a geração termina"""
        self.is_generating = False
        self.generate_btn.setEnabled(True)
        self.cancel_btn.hide()
        
        if cards:
            self.generated_cards = cards
            self.result_text.setText('\n'.join(cards))
            self.update_status()
            
            self.progress_bar.setValue(len(cards))
            self.progress_label.setText(f"Concluído · {len(cards)} cartões gerados")
            self.progress_label.setStyleSheet("color: #10b981; font-size: 13px; font-weight: 500;")
        else:
            self.progress_label.setText("Nenhum cartão gerado")
            self.progress_label.setStyleSheet("color: #ff453a; font-size: 13px; font-weight: 500;")
        
        # Esconder barra após 3 segundos
        QTimer.singleShot(3000, self.hide_progress)
    
    def on_generation_error(self, error_msg):
        """Chamado quando ocorre erro na geração"""
        self.is_generating = False
        self.generate_btn.setEnabled(True)
        self.cancel_btn.hide()
        self.progress_label.setText(f"Erro: {error_msg}")
        self.progress_label.setStyleSheet("color: #ff453a; font-size: 13px; font-weight: 500;")
        QMessageBox.critical(self, "Erro", f"Erro durante a geração:\n\n{error_msg}")
        QTimer.singleShot(3000, self.hide_progress)
    
    def cancel_generation(self):
        """Cancela a geração em andamento"""
        if self.generator_thread and self.is_generating:
            self.generator_thread.stop()
            self.progress_label.setText("Cancelando...")
            self.progress_label.setStyleSheet("color: #ff9f0a; font-size: 13px; font-weight: 500;")
    
    def hide_progress(self):
        """Esconde a barra de progresso"""
        if not self.is_generating:
            self.progress_bar.hide()
            self.progress_label.hide()
            self.progress_label.setStyleSheet("color: #06b6d4; font-size: 13px; font-weight: 500;")
    
    def copy_cards(self):
        """Copia os cartões para a área de transferência"""
        text = self.result_text.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Sucesso", f"{len(self.generated_cards)} cartões copiados!")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum cartão para copiar!")
    
    def clear_cards(self):
        """Limpa a lista de cartões gerados"""
        self.result_text.clear()
        self.generated_cards = []
        self.update_status()
    
    def update_status(self):
        """Atualiza o status"""
        history_count = self.card_generator.get_history_count()
        generated_count = len(self.generated_cards)
        self.status_label.setText(f"Histórico: {history_count} cartões · Gerados: {generated_count}")
    
    def copy_card_field(self, field_index: int, field_name: str):
        """Copia um campo específico dos cartões para a área de transferência"""
        if not self.generated_cards:
            QMessageBox.warning(self, "Aviso", "Nenhum cartão para copiar!")
            return
        
        try:
            # Extrair o campo específico de cada cartão
            # Formato: NUMERO|MES|ANO|CVV
            fields = []
            for card in self.generated_cards:
                parts = card.split('|')
                if len(parts) > field_index:
                    fields.append(parts[field_index])
            
            if fields:
                text = '\n'.join(fields)
                QApplication.clipboard().setText(text)
                QMessageBox.information(self, "Sucesso", f"{len(fields)} {field_name}(s) copiado(s)!")
            else:
                QMessageBox.warning(self, "Aviso", f"Não foi possível extrair {field_name}!")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao copiar: {str(e)}")
    
    # ===== MÉTODOS DO FORMATADOR DE CONTAS =====
    
    def create_account_formatter_tab(self):
        """Cria a aba do formatador de contas premium"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        
        # Scroll area para caber tudo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        
        # Grupo de Entrada
        input_group = QGroupBox("ENTRADA")
        input_group.setStyleSheet("""
            QGroupBox {
                background-color: #1c1c1e;
                border: none;
                border-radius: 16px;
                margin-top: 24px;
                padding: 24px;
                padding-top: 40px;
            }
            QGroupBox::title {
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 1px;
            }
        """)
        input_layout = QVBoxLayout()
        input_layout.setSpacing(12)
        
        # Área de texto para colar credenciais
        input_label = QLabel("Cole as credenciais (email:senha, email|senha, email-senha):")
        input_label.setStyleSheet("font-weight: 500; color: #64748b; font-size: 12px;")
        input_layout.addWidget(input_label)
        
        self.accounts_input = QTextEdit()
        self.accounts_input.setPlaceholderText("usuario@gmail.com:senha123\noutro@hotmail.com|minhasenha\nemail@yahoo.com-pass456")
        self.accounts_input.setMinimumHeight(120)
        self.accounts_input.setMaximumHeight(150)
        self.accounts_input.setStyleSheet("""
            QTextEdit {
                background-color: #2c2c2e;
                border: none;
                border-radius: 12px;
                padding: 12px;
                font-family: 'SF Mono', 'Menlo', 'Consolas', monospace;
                font-size: 12px;
                color: #ffffff;
            }
        """)
        input_layout.addWidget(self.accounts_input)
        
        input_group.setLayout(input_layout)
        scroll_layout.addWidget(input_group)
        
        # Grupo de Configurações
        config_group = QGroupBox("CONFIGURAÇÕES")
        config_group.setStyleSheet("""
            QGroupBox {
                background-color: #1c1c1e;
                border: none;
                border-radius: 16px;
                margin-top: 20px;
                padding: 24px;
                padding-top: 40px;
            }
            QGroupBox::title {
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 1px;
            }
        """)
        config_layout = QVBoxLayout()
        config_layout.setSpacing(16)
        
        # Estilo comum
        label_style = "font-weight: 500; color: #64748b; font-size: 12px;"
        combo_style = """
            QComboBox {
                background-color: #2c2c2e;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                color: #ffffff;
                min-width: 200px;
            }
        """
        
        # Serviço
        service_layout = QHBoxLayout()
        service_label = QLabel("Serviço:")
        service_label.setStyleSheet(label_style)
        service_layout.addWidget(service_label)
        
        self.service_combo = QComboBox()
        services = self.account_formatter.get_services()
        for name, emoji in services.items():
            self.service_combo.addItem(f"{emoji} {name}", name)
        self.service_combo.setStyleSheet(combo_style)
        self.service_combo.currentIndexChanged.connect(self.on_service_changed)
        service_layout.addWidget(self.service_combo)
        service_layout.addStretch()
        config_layout.addLayout(service_layout)
        
        # Campo de serviço personalizado (oculto por padrão)
        self.custom_service_layout = QHBoxLayout()
        custom_label = QLabel("Nome do serviço:")
        custom_label.setStyleSheet(label_style)
        self.custom_service_layout.addWidget(custom_label)
        
        self.custom_service_input = QLineEdit()
        self.custom_service_input.setPlaceholderText("Digite o nome do serviço")
        self.custom_service_input.setStyleSheet("""
            QLineEdit {
                background-color: #2c2c2e;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                color: #ffffff;
            }
        """)
        self.custom_service_layout.addWidget(self.custom_service_input)
        self.custom_service_layout.addStretch()
        
        # Widget container para o layout personalizado
        self.custom_service_widget = QWidget()
        self.custom_service_widget.setLayout(self.custom_service_layout)
        self.custom_service_widget.hide()
        config_layout.addWidget(self.custom_service_widget)
        
        # Senha do serviço (opcional)
        pwd_layout = QHBoxLayout()
        pwd_label = QLabel("Senha do serviço (opcional):")
        pwd_label.setStyleSheet(label_style)
        pwd_layout.addWidget(pwd_label)
        
        self.service_password_input = QLineEdit()
        self.service_password_input.setPlaceholderText("Deixe vazio para usar a senha original")
        self.service_password_input.setStyleSheet("""
            QLineEdit {
                background-color: #2c2c2e;
                border: none;
                border-radius: 12px;
                padding: 12px 16px;
                color: #ffffff;
                min-width: 250px;
            }
        """)
        pwd_layout.addWidget(self.service_password_input)
        pwd_layout.addStretch()
        config_layout.addLayout(pwd_layout)
        
        # Modelo de formatação
        model_layout = QHBoxLayout()
        model_label = QLabel("Modelo:")
        model_label.setStyleSheet(label_style)
        model_layout.addWidget(model_label)
        
        self.model_combo = QComboBox()
        self.model_combo.addItem("📝 Clássico (Completo)", 1)
        self.model_combo.addItem("✨ Minimalista (Limpo)", 2)
        self.model_combo.addItem("📦 Detalhado (Box)", 3)
        self.model_combo.addItem("⚡ Compacto (One-liner)", 4)
        self.model_combo.setStyleSheet(combo_style)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        config_layout.addLayout(model_layout)
        
        config_group.setLayout(config_layout)
        scroll_layout.addWidget(config_group)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.format_btn = QPushButton("✨ FORMATAR CONTAS")
        self.format_btn.setStyleSheet("""
            QPushButton {
                background-color: #5856d6;
                color: #ffffff;
                font-size: 14px;
                font-weight: 600;
                padding: 14px 28px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #6e6cd8; }
            QPushButton:pressed { background-color: #4a48c4; }
        """)
        self.format_btn.clicked.connect(self.format_accounts)
        btn_layout.addWidget(self.format_btn)
        
        copy_formatted_btn = QPushButton("📋 Copiar Resultado")
        copy_formatted_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2e;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
                padding: 12px 20px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #3a3a3c; }
        """)
        copy_formatted_btn.clicked.connect(self.copy_formatted_accounts)
        btn_layout.addWidget(copy_formatted_btn)
        
        clear_formatted_btn = QPushButton("🗑️ Limpar")
        clear_formatted_btn.setStyleSheet("""
            QPushButton {
                background-color: #2c2c2e;
                color: #ffffff;
                font-size: 13px;
                font-weight: 500;
                padding: 12px 20px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #3a3a3c; }
        """)
        clear_formatted_btn.clicked.connect(self.clear_formatted_accounts)
        btn_layout.addWidget(clear_formatted_btn)
        
        scroll_layout.addLayout(btn_layout)
        
        # Grupo de Resultado
        result_group = QGroupBox("RESULTADO")
        result_group.setStyleSheet("""
            QGroupBox {
                background-color: #1c1c1e;
                border: none;
                border-radius: 16px;
                margin-top: 20px;
                padding: 20px;
                padding-top: 36px;
            }
            QGroupBox::title {
                color: #64748b;
                font-size: 11px;
                font-weight: 600;
                letter-spacing: 1px;
            }
        """)
        result_layout = QVBoxLayout()
        
        self.accounts_result = QTextEdit()
        self.accounts_result.setReadOnly(True)
        self.accounts_result.setMinimumHeight(200)
        self.accounts_result.setStyleSheet("""
            QTextEdit {
                background-color: #000000;
                border: 1px solid #2c2c2e;
                border-radius: 12px;
                padding: 16px;
                font-family: 'SF Mono', 'Menlo', 'Monaco', 'Consolas', monospace;
                font-size: 12px;
                color: #10b981;
                line-height: 1.6;
            }
        """)
        self.accounts_result.setPlaceholderText("As contas formatadas aparecerão aqui...")
        result_layout.addWidget(self.accounts_result)
        
        result_group.setLayout(result_layout)
        scroll_layout.addWidget(result_group)
        
        # Status
        self.accounts_status_label = QLabel("")
        self.accounts_status_label.setStyleSheet("color: #64748b; font-size: 12px; font-weight: 400;")
        self.accounts_status_label.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(self.accounts_status_label)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        tab.setLayout(layout)
        return tab
    
    def on_service_changed(self, index):
        """Mostra/oculta o campo de serviço personalizado"""
        service = self.service_combo.currentData()
        if service == "Personalizado":
            self.custom_service_widget.show()
        else:
            self.custom_service_widget.hide()
    
    def format_accounts(self):
        """Formata as contas de acordo com as configurações"""
        input_text = self.accounts_input.toPlainText().strip()
        
        if not input_text:
            QMessageBox.warning(self, "Aviso", "Cole as credenciais na área de entrada!")
            return
        
        # Obter configurações
        service = self.service_combo.currentData()
        if service == "Personalizado":
            service = self.custom_service_input.text().strip()
            if not service:
                QMessageBox.warning(self, "Aviso", "Digite o nome do serviço personalizado!")
                return
        
        model = self.model_combo.currentData()
        service_password = self.service_password_input.text().strip() or None
        
        # Formatar
        try:
            result, count = self.account_formatter.process_and_format(
                input_text, model, service, service_password
            )
            
            if result:
                self.formatted_accounts = result
                self.accounts_result.setText(result)
                self.accounts_status_label.setText(f"✅ {count} conta(s) formatada(s) com sucesso!")
                self.accounts_status_label.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 400;")
            else:
                self.accounts_status_label.setText("⚠️ Nenhuma credencial válida encontrada")
                self.accounts_status_label.setStyleSheet("color: #ff9f0a; font-size: 12px; font-weight: 400;")
        
        except Exception as e:
            self.accounts_status_label.setText(f"❌ Erro: {str(e)}")
            self.accounts_status_label.setStyleSheet("color: #ff453a; font-size: 12px; font-weight: 400;")
    
    def copy_formatted_accounts(self):
        """Copia as contas formatadas para a área de transferência"""
        text = self.accounts_result.toPlainText()
        if text:
            QApplication.clipboard().setText(text)
            self.accounts_status_label.setText("📋 Resultado copiado!")
            self.accounts_status_label.setStyleSheet("color: #10b981; font-size: 12px; font-weight: 400;")
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum resultado para copiar!")
    
    def clear_formatted_accounts(self):
        """Limpa os campos do formatador"""
        self.accounts_input.clear()
        self.accounts_result.clear()
        self.service_password_input.clear()
        self.custom_service_input.clear()
        self.formatted_accounts = ""
        self.accounts_status_label.setText("")
    
    def closeEvent(self, event):
        """Garante que a thread seja parada ao fechar"""
        if self.generator_thread and self.is_generating:
            self.generator_thread.stop()
            self.generator_thread.wait(2000)  # Espera até 2 segundos
        if self.address_thread and self.is_generating_addresses:
            self.address_thread.stop()
            self.address_thread.wait(2000)
        event.accept()


def create_app_icon():
    """Cria um ícone para a aplicação programaticamente"""
    pixmap = QPixmap(64, 64)
    pixmap.fill(Qt.transparent)
    
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    
    gradient = QLinearGradient(0, 0, 64, 64)
    gradient.setColorAt(0, QColor("#06b6d4"))
    gradient.setColorAt(1, QColor("#6d28d9"))
    
    painter.setBrush(QBrush(gradient))
    painter.setPen(QPen(Qt.transparent))
    painter.drawEllipse(4, 4, 56, 56)
    
    painter.setPen(QPen(QColor("#ffffff")))
    font = QFont("Arial", 20, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "TC")
    
    painter.end()
    
    return QIcon(pixmap)


class SimpleApp(QMainWindow):
    """Janela principal da aplicação - Tema Escuro com Modos Compacto e Fixar"""
    
    # Tamanhos padrão
    NORMAL_SIZE = (1200, 850)
    COMPACT_SIZE = (400, 600)
    MINI_SIZE = (350, 450)
    
    def __init__(self):
        super().__init__()
        self.config_manager = ConfigManager()
        self.db = self._get_database()
        self.collector_thread = None
        self.current_pair = None
        
        # Estados dos modos
        self.is_always_on_top = False
        self.is_compact_mode = False
        self.is_mini_mode = False
        self.settings = QSettings("TelegramCollector", "Pro")
        
        # Opções de exibição
        self.mostrar_nome = True
        self.mostrar_cpf = True
        self.mostrar_idade = True
        self.mostrar_data = True
        self.mostrar_telefone = True
        self.mostrar_score = True
        
        # Configurar ícone e propriedades da janela
        self.setup_window_properties()
        
        self.init_ui()
        self.setup_system_tray()
        self.check_configuration()
        self.load_window_state()
    
    def setup_window_properties(self):
        """Configura propriedades da janela para funcionar na barra de tarefas"""
        self.app_icon = create_app_icon()
        self.setWindowIcon(self.app_icon)
        
        if sys.platform == 'win32':
            try:
                app_id = 'TelegramCollector.Pro.v11.0'
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
            except Exception as e:
                print(f"Aviso: Não foi possível definir AppUserModelID: {e}")
    
    def setup_system_tray(self):
        """Configura o ícone na bandeja do sistema"""
        if QSystemTrayIcon.isSystemTrayAvailable():
            self.tray_icon = QSystemTrayIcon(self.app_icon, self)
            
            tray_menu = QMenu()
            
            show_action = QAction("Mostrar", self)
            show_action.triggered.connect(self.show_normal_window)
            tray_menu.addAction(show_action)
            
            compact_action = QAction("Modo Compacto", self)
            compact_action.triggered.connect(self.toggle_compact_mode)
            tray_menu.addAction(compact_action)
            
            tray_menu.addSeparator()
            
            pin_action = QAction("Fixar no Topo", self)
            pin_action.triggered.connect(self.toggle_always_on_top)
            tray_menu.addAction(pin_action)
            
            tray_menu.addSeparator()
            
            quit_action = QAction("Sair", self)
            quit_action.triggered.connect(self.quit_application)
            tray_menu.addAction(quit_action)
            
            self.tray_icon.setContextMenu(tray_menu)
            self.tray_icon.activated.connect(self.tray_icon_activated)
            self.tray_icon.show()
            self.tray_icon.setToolTip("Telegram Collector Pro v11.0")
    
    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.DoubleClick:
            self.show_normal_window()
    
    def show_normal_window(self):
        self.showNormal()
        self.activateWindow()
        self.raise_()
    
    def quit_application(self):
        self.save_window_state()
        if hasattr(self, 'tray_icon'):
            self.tray_icon.hide()
        QApplication.quit()
    
    def toggle_always_on_top(self):
        """Alterna o modo sempre no topo"""
        self.is_always_on_top = not self.is_always_on_top
        
        if self.is_always_on_top:
            self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
            self.pin_btn.setText("📍 Fixado")
            self.pin_btn.setStyleSheet("""
                QPushButton {
                    background-color: #ef4444;
                    color: white;
                    font-size: 11px;
                    padding: 8px 12px;
                    border-radius: 12px;
                    border: none;
                }
                QPushButton:hover { background-color: #dc2626; }
            """)
            self.statusBar().showMessage("✅ Janela fixada no topo", 2000)
        else:
            self.setWindowFlags(self.windowFlags() & ~Qt.WindowStaysOnTopHint)
            self.pin_btn.setText("📌 Fixar")
            self.pin_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    color: #f1f5f9;
                    font-size: 11px;
                    padding: 8px 12px;
                    border-radius: 12px;
                    border: 1px solid rgba(6,182,212,0.15);
                }
                QPushButton:hover { background-color: rgba(6,182,212,0.15); }
            """)
            self.statusBar().showMessage("📌 Janela desfixada", 2000)
        
        self.show()
    
    def toggle_compact_mode(self):
        """Alterna entre modo normal e compacto com interface dedicada"""
        self.is_compact_mode = not self.is_compact_mode
        
        if self.is_compact_mode:
            self.normal_geometry = self.geometry()
            
            # Ocultar a interface normal
            self.main_tabs.hide()
            
            # Criar widget compacto se não existir
            if not hasattr(self, 'compact_widget'):
                self.create_compact_widget()
            
            self.compact_widget.show()
            self.centralWidget().layout().addWidget(self.compact_widget)
            
            self.setMinimumSize(420, 700)
            self.setMaximumSize(500, 900)
            self.resize(450, 750)
            
            self.compact_btn.setText("📐 Normal")
            self.statusBar().showMessage("📱 Modo compacto ativado", 2000)
        else:
            # Ocultar widget compacto e mostrar interface normal
            if hasattr(self, 'compact_widget'):
                self.compact_widget.hide()
            
            self.main_tabs.show()
            
            self.setMinimumSize(0, 0)
            self.setMaximumSize(16777215, 16777215)
            
            if hasattr(self, 'normal_geometry'):
                self.setGeometry(self.normal_geometry)
            else:
                self.resize(*self.NORMAL_SIZE)
            
            self.compact_btn.setText("📱 Compacto")
            self.statusBar().showMessage("🖥️ Modo normal ativado", 2000)
    
    def create_compact_widget(self):
        """Cria o widget compacto com Gerador de Pares e CEP"""
        self.compact_widget = QWidget()
        layout = QVBoxLayout(self.compact_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Estilo compacto
        group_style = """
            QGroupBox {
                background-color: #111827;
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 12px;
                margin-top: 12px;
                padding: 10px;
                padding-top: 25px;
                font-size: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                top: 3px;
                padding: 0 8px;
                color: #22d3ee;
                font-size: 11px;
                font-weight: 600;
            }
        """
        
        field_style = """
            QLineEdit {
                background-color: #0a0e1a;
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 12px;
                padding: 8px 10px;
                font-size: 12px;
                color: #22d3ee;
                font-family: 'Consolas', monospace;
            }
        """
        
        btn_style = """
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 8px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover { background-color: #10b981; }
        """
        
        copy_btn_style = """
            QPushButton {
                background-color: #1e293b;
                color: #f1f5f9;
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 10px;
            }
            QPushButton:hover { background-color: rgba(6,182,212,0.15); }
        """
        
        # === GRUPO 1: GERADOR DE PARES ===
        pares_group = QGroupBox("🎲 Gerador de Pares")
        pares_group.setStyleSheet(group_style)
        pares_layout = QVBoxLayout(pares_group)
        pares_layout.setSpacing(8)
        
        # Campo Nome
        nome_row = QHBoxLayout()
        nome_lbl = QLabel("👤 Nome:")
        nome_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        nome_row.addWidget(nome_lbl)
        self.compact_nome = QLineEdit()
        self.compact_nome.setReadOnly(True)
        self.compact_nome.setPlaceholderText("Clique em Gerar")
        self.compact_nome.setStyleSheet(field_style)
        nome_row.addWidget(self.compact_nome, 1)
        copy_nome = QPushButton("📋")
        copy_nome.setStyleSheet(copy_btn_style)
        copy_nome.setFixedWidth(30)
        copy_nome.clicked.connect(lambda: self.copy_compact_field(self.compact_nome))
        nome_row.addWidget(copy_nome)
        pares_layout.addLayout(nome_row)
        
        # Campo CPF
        cpf_row = QHBoxLayout()
        cpf_lbl = QLabel("🆔 CPF:")
        cpf_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        cpf_row.addWidget(cpf_lbl)
        self.compact_cpf = QLineEdit()
        self.compact_cpf.setReadOnly(True)
        self.compact_cpf.setPlaceholderText("000.000.000-00")
        self.compact_cpf.setStyleSheet(field_style)
        cpf_row.addWidget(self.compact_cpf, 1)
        copy_cpf = QPushButton("📋")
        copy_cpf.setStyleSheet(copy_btn_style)
        copy_cpf.setFixedWidth(30)
        copy_cpf.clicked.connect(lambda: self.copy_compact_field(self.compact_cpf))
        cpf_row.addWidget(copy_cpf)
        pares_layout.addLayout(cpf_row)
        
        # Botão Gerar Par
        btn_row = QHBoxLayout()
        gerar_par_btn = QPushButton("🎲 Gerar Par")
        gerar_par_btn.setStyleSheet(btn_style)
        gerar_par_btn.clicked.connect(self.generate_compact_pair)
        btn_row.addWidget(gerar_par_btn)
        
        copiar_tudo_btn = QPushButton("📋 Copiar Tudo")
        copiar_tudo_btn.setStyleSheet(btn_style.replace("#059669", "#1f6feb").replace("#10b981", "#388bfd"))
        copiar_tudo_btn.clicked.connect(self.copy_compact_pair)
        btn_row.addWidget(copiar_tudo_btn)
        pares_layout.addLayout(btn_row)
        
        layout.addWidget(pares_group)
        
        # === GRUPO 2: GERADOR DE CEP ===
        cep_group = QGroupBox("🏠 Gerador de CEP")
        cep_group.setStyleSheet(group_style)
        cep_layout = QVBoxLayout(cep_group)
        cep_layout.setSpacing(8)
        
        # Seletor de Estado
        estado_row = QHBoxLayout()
        estado_lbl = QLabel("Estado:")
        estado_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        estado_row.addWidget(estado_lbl)
        self.compact_estado_combo = QComboBox()
        self.compact_estado_combo.setStyleSheet("""
            QComboBox {
                background-color: #0a0e1a;
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 12px;
                padding: 6px;
                color: #f1f5f9;
                font-size: 11px;
            }
        """)
        self.compact_estado_combo.addItem("Todos os Estados", None)
        # Adicionar estados
        estados = [
            ("AC", "Acre"), ("AL", "Alagoas"), ("AP", "Amapá"), ("AM", "Amazonas"),
            ("BA", "Bahia"), ("CE", "Ceará"), ("DF", "Distrito Federal"), ("ES", "Espírito Santo"),
            ("GO", "Goiás"), ("MA", "Maranhão"), ("MT", "Mato Grosso"), ("MS", "Mato Grosso do Sul"),
            ("MG", "Minas Gerais"), ("PA", "Pará"), ("PB", "Paraíba"), ("PR", "Paraná"),
            ("PE", "Pernambuco"), ("PI", "Piauí"), ("RJ", "Rio de Janeiro"), ("RN", "Rio Grande do Norte"),
            ("RS", "Rio Grande do Sul"), ("RO", "Rondônia"), ("RR", "Roraima"), ("SC", "Santa Catarina"),
            ("SP", "São Paulo"), ("SE", "Sergipe"), ("TO", "Tocantins")
        ]
        for uf, nome in estados:
            self.compact_estado_combo.addItem(f"{uf} - {nome}", uf)
        estado_row.addWidget(self.compact_estado_combo, 1)
        cep_layout.addLayout(estado_row)
        
        # Campos de resultado CEP
        # CEP
        cep_row = QHBoxLayout()
        cep_lbl = QLabel("📮 CEP:")
        cep_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        cep_row.addWidget(cep_lbl)
        self.compact_cep = QLineEdit()
        self.compact_cep.setReadOnly(True)
        self.compact_cep.setPlaceholderText("00000-000")
        self.compact_cep.setStyleSheet(field_style)
        cep_row.addWidget(self.compact_cep, 1)
        copy_cep = QPushButton("📋")
        copy_cep.setStyleSheet(copy_btn_style)
        copy_cep.setFixedWidth(30)
        copy_cep.clicked.connect(lambda: self.copy_compact_field(self.compact_cep))
        cep_row.addWidget(copy_cep)
        cep_layout.addLayout(cep_row)
        
        # Endereço
        end_row = QHBoxLayout()
        end_lbl = QLabel("🚩 Rua:")
        end_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        end_row.addWidget(end_lbl)
        self.compact_endereco = QLineEdit()
        self.compact_endereco.setReadOnly(True)
        self.compact_endereco.setPlaceholderText("Rua/Avenida")
        self.compact_endereco.setStyleSheet(field_style)
        end_row.addWidget(self.compact_endereco, 1)
        copy_end = QPushButton("📋")
        copy_end.setStyleSheet(copy_btn_style)
        copy_end.setFixedWidth(30)
        copy_end.clicked.connect(lambda: self.copy_compact_field(self.compact_endereco))
        end_row.addWidget(copy_end)
        cep_layout.addLayout(end_row)
        
        # Bairro
        bairro_row = QHBoxLayout()
        bairro_lbl = QLabel("🏘️ Bairro:")
        bairro_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        bairro_row.addWidget(bairro_lbl)
        self.compact_bairro = QLineEdit()
        self.compact_bairro.setReadOnly(True)
        self.compact_bairro.setPlaceholderText("Bairro")
        self.compact_bairro.setStyleSheet(field_style)
        bairro_row.addWidget(self.compact_bairro, 1)
        copy_bairro = QPushButton("📋")
        copy_bairro.setStyleSheet(copy_btn_style)
        copy_bairro.setFixedWidth(30)
        copy_bairro.clicked.connect(lambda: self.copy_compact_field(self.compact_bairro))
        bairro_row.addWidget(copy_bairro)
        cep_layout.addLayout(bairro_row)
        
        # Cidade/Estado
        cidade_row = QHBoxLayout()
        cidade_lbl = QLabel("🏙️ Cidade:")
        cidade_lbl.setStyleSheet("color: #94a3b8; font-size: 11px;")
        cidade_row.addWidget(cidade_lbl)
        self.compact_cidade = QLineEdit()
        self.compact_cidade.setReadOnly(True)
        self.compact_cidade.setPlaceholderText("Cidade - UF")
        self.compact_cidade.setStyleSheet(field_style)
        cidade_row.addWidget(self.compact_cidade, 1)
        copy_cidade = QPushButton("📋")
        copy_cidade.setStyleSheet(copy_btn_style)
        copy_cidade.setFixedWidth(30)
        copy_cidade.clicked.connect(lambda: self.copy_compact_field(self.compact_cidade))
        cidade_row.addWidget(copy_cidade)
        cep_layout.addLayout(cidade_row)
        
        # Botões CEP
        cep_btn_row = QHBoxLayout()
        gerar_cep_btn = QPushButton("🏠 Gerar CEP")
        gerar_cep_btn.setStyleSheet(btn_style.replace("#059669", "#06b6d4").replace("#10b981", "#22d3ee"))
        gerar_cep_btn.clicked.connect(self.generate_compact_cep)
        cep_btn_row.addWidget(gerar_cep_btn)
        
        copiar_end_btn = QPushButton("📋 Copiar Endereço")
        copiar_end_btn.setStyleSheet(btn_style.replace("#059669", "#1f6feb").replace("#10b981", "#388bfd"))
        copiar_end_btn.clicked.connect(self.copy_compact_address)
        cep_btn_row.addWidget(copiar_end_btn)
        cep_layout.addLayout(cep_btn_row)
        
        layout.addWidget(cep_group)
        
        # Status
        self.compact_status = QLabel("Pronto para usar")
        self.compact_status.setStyleSheet("color: #94a3b8; font-size: 10px; padding: 5px;")
        self.compact_status.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.compact_status)
        
        layout.addStretch()
    
    def generate_compact_pair(self):
        """Gera par no modo compacto"""
        pair = self.db.get_random_pair({})
        if pair:
            self.current_pair = pair
            nome = pair.get('nome', '-')
            cpf = pair.get('cpf', '-')
            self.compact_nome.setText(nome)
            self.compact_cpf.setText(cpf)
            # Atualizar também os campos normais
            if hasattr(self, 'nome_label'):
                self.nome_label.setText(f"👤 Nome: {nome}")
                self.cpf_label.setText(f"🆔 CPF: {cpf}")
            self.compact_status.setText("✅ Par gerado com sucesso!")
            self.compact_status.setStyleSheet("color: #059669; font-size: 10px; padding: 5px;")
        else:
            self.compact_status.setText("❌ Nenhum registro encontrado")
            self.compact_status.setStyleSheet("color: #f43f5e; font-size: 10px; padding: 5px;")
    
    def copy_compact_pair(self):
        """Copia nome e CPF do modo compacto"""
        nome = self.compact_nome.text()
        cpf = self.compact_cpf.text()
        if nome and cpf and nome != "Clique em Gerar":
            texto = f"{nome}\n{cpf}"
            QApplication.clipboard().setText(texto)
            self.compact_status.setText("✅ Nome e CPF copiados!")
            self.compact_status.setStyleSheet("color: #059669; font-size: 10px; padding: 5px;")
    
    def generate_compact_cep(self):
        """Gera CEP no modo compacto"""
        try:
            from address_generator import AddressGenerator
            if not hasattr(self, 'compact_address_gen'):
                self.compact_address_gen = AddressGenerator()
            
            uf = self.compact_estado_combo.currentData()
            endereco = self.compact_address_gen.gerar_endereco(uf, None, True)
            
            if endereco:
                self.compact_cep.setText(endereco.cep)
                self.compact_endereco.setText(endereco.logradouro)
                self.compact_bairro.setText(endereco.bairro)
                self.compact_cidade.setText(f"{endereco.cidade} - {endereco.uf}")
                self.compact_status.setText("✅ CEP gerado com sucesso!")
                self.compact_status.setStyleSheet("color: #06b6d4; font-size: 10px; padding: 5px;")
            else:
                self.compact_status.setText("❌ Erro ao gerar CEP")
                self.compact_status.setStyleSheet("color: #f43f5e; font-size: 10px; padding: 5px;")
        except Exception as e:
            self.compact_status.setText(f"❌ Erro: {str(e)[:30]}")
            self.compact_status.setStyleSheet("color: #f43f5e; font-size: 10px; padding: 5px;")
    
    def copy_compact_address(self):
        """Copia endereço completo do modo compacto"""
        cep = self.compact_cep.text()
        rua = self.compact_endereco.text()
        bairro = self.compact_bairro.text()
        cidade = self.compact_cidade.text()
        
        if cep and cep != "00000-000":
            texto = f"{rua}\n{bairro}\n{cidade}\nCEP: {cep}"
            QApplication.clipboard().setText(texto)
            self.compact_status.setText("✅ Endereço copiado!")
            self.compact_status.setStyleSheet("color: #06b6d4; font-size: 10px; padding: 5px;")
    
    def copy_compact_field(self, field):
        """Copia um campo específico no modo compacto"""
        text = field.text()
        if text and text not in ["Clique em Gerar", "00000-000", "Rua/Avenida", "Bairro", "Cidade - UF", "000.000.000-00"]:
            QApplication.clipboard().setText(text)
            self.compact_status.setText("✅ Copiado!")
            self.compact_status.setStyleSheet("color: #059669; font-size: 10px; padding: 5px;")
    
    def save_window_state(self):
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("isAlwaysOnTop", self.is_always_on_top)
        self.settings.setValue("isCompactMode", self.is_compact_mode)
    
    def load_window_state(self):
        geometry = self.settings.value("geometry")
        if geometry:
            self.restoreGeometry(geometry)
        
        if self.settings.value("isAlwaysOnTop", False, type=bool):
            self.toggle_always_on_top()
        
        if self.settings.value("isCompactMode", False, type=bool):
            self.toggle_compact_mode()
    
    def closeEvent(self, event):
        self.save_window_state()
        if hasattr(self, 'tray_icon') and self.tray_icon.isVisible():
            self.hide()
            self.tray_icon.showMessage(
                "Telegram Collector Pro",
                "Minimizado para a bandeja. Clique duplo para restaurar.",
                QSystemTrayIcon.Information,
                2000
            )
            event.ignore()
        else:
            event.accept()
    
    def _get_database(self):
        """Retorna o DatabaseManager correto baseado na conta ativa"""
        conta_ativa = self.config_manager.get_conta_ativa()
        if conta_ativa:
            db_path = self.config_manager.get_caminho_banco(conta_ativa['id'])
            return DatabaseManager(db_path)
        else:
            return DatabaseManager()
    
    def refresh_database(self):
        """Atualiza a conexão com o banco de dados da conta ativa"""
        self.db = self._get_database()
        self.update_stats()
    
    def check_configuration(self):
        if not settings.is_configured:
            QTimer.singleShot(500, self.show_config_dialog)
    
    def show_contas_dialog(self):
        """Abre o gerenciador de contas e sessões"""
        dialog = GerenciadorContas(self)
        dialog.exec_()
        # Atualizar banco de dados após possível mudança de conta
        self.config_manager.load_config()  # Recarregar configurações
        self.refresh_database()
    
    def show_config_dialog(self):
        dialog = ConfigDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_stats()
    
    def init_ui(self):
        self.setWindowTitle('🎲 Telegram Collector Pro v11.0')
        self.setGeometry(100, 100, 1200, 850)
        self.setStyleSheet(DARK_STYLE)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(15, 15, 15, 15)
        
        # Título Principal com Botões de Modo
        header_layout = QHBoxLayout()
        title = QLabel("🎲 Telegram Collector Pro v11.0")
        title.setFont(QFont('Arial', 18, QFont.Bold))
        title.setStyleSheet("color: #22d3ee; letter-spacing: 0.5px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # === BOTÕES DE CONTROLE DA JANELA ===
        control_layout = QHBoxLayout()
        control_layout.setSpacing(8)
        
        # Botão Fixar no Topo
        self.pin_btn = QPushButton("📌 Fixar")
        self.pin_btn.setToolTip("Manter janela sempre visível")
        self.pin_btn.setStyleSheet("""
            QPushButton {
                background: rgba(15,23,42,0.7);
                color: #94a3b8;
                font-size: 11px;
                padding: 8px 14px;
                border-radius: 12px;
                border: 1px solid rgba(6,182,212,0.2);
            }
            QPushButton:hover {
                background: rgba(6,182,212,0.1);
                border-color: rgba(6,182,212,0.4);
                color: #22d3ee;
            }
        """)
        self.pin_btn.clicked.connect(self.toggle_always_on_top)
        control_layout.addWidget(self.pin_btn)
        
        # Botão Modo Compacto
        self.compact_btn = QPushButton("📱 Compacto")
        self.compact_btn.setToolTip("Alternar modo compacto")
        self.compact_btn.setStyleSheet("""
            QPushButton {
                background: rgba(15,23,42,0.7);
                color: #94a3b8;
                font-size: 11px;
                padding: 8px 14px;
                border-radius: 12px;
                border: 1px solid rgba(6,182,212,0.2);
            }
            QPushButton:hover {
                background: rgba(6,182,212,0.1);
                border-color: rgba(6,182,212,0.4);
                color: #22d3ee;
            }
        """)
        self.compact_btn.clicked.connect(self.toggle_compact_mode)
        control_layout.addWidget(self.compact_btn)
        
        header_layout.addLayout(control_layout)
        main_layout.addLayout(header_layout)
        
        # === ABAS PRINCIPAIS INTEGRADAS ===
        self.main_tabs = QTabWidget()
        self.main_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(6,182,212,0.12);
                border-radius: 16px;
                background-color: rgba(10,14,26,0.8);
                margin-top: -1px;
                padding: 8px;
            }
            QTabBar::tab {
                background-color: rgba(15,23,42,0.6);
                color: #64748b;
                padding: 14px 28px;
                margin-right: 4px;
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                font-weight: 500;
                font-size: 13px;
                border: 1px solid transparent;
            }
            QTabBar::tab:selected {
                background-color: rgba(6,182,212,0.1);
                color: #22d3ee;
                border: 1px solid rgba(6,182,212,0.2);
                border-bottom: 3px solid #06b6d4;
                font-weight: 600;
            }
            QTabBar::tab:hover:!selected {
                background-color: rgba(6,182,212,0.06);
                color: #94a3b8;
            }
        """)
        
        # Aba 1: Gerador de Pares
        gerador_tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Grupo de Filtros
        filter_group = QGroupBox("🔍 Filtros")
        filter_group.setStyleSheet("""
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(15,23,42,0.9), stop:1 rgba(15,23,42,0.7));
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 18px;
                margin-top: 18px;
                padding: 18px;
                padding-top: 36px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 22px;
                top: 8px;
                padding: 4px 14px;
                color: #22d3ee;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                background: rgba(6,182,212,0.06);
                border-radius: 12px;
            }
        """)
        filter_layout = QVBoxLayout()
        filter_layout.setSpacing(10)
        
        # Filtro de idade
        idade_layout = QHBoxLayout()
        self.filtro_checkbox = QCheckBox("Filtrar por idade:")
        self.filtro_checkbox.stateChanged.connect(self.toggle_filtro)
        idade_layout.addWidget(self.filtro_checkbox)
        
        idade_layout.addWidget(QLabel("De"))
        self.idade_min_spin = QSpinBox()
        self.idade_min_spin.setRange(0, 120)
        self.idade_min_spin.setValue(18)
        self.idade_min_spin.setEnabled(False)
        idade_layout.addWidget(self.idade_min_spin)
        
        idade_layout.addWidget(QLabel("até"))
        self.idade_max_spin = QSpinBox()
        self.idade_max_spin.setRange(0, 120)
        self.idade_max_spin.setValue(65)
        self.idade_max_spin.setEnabled(False)
        idade_layout.addWidget(self.idade_max_spin)
        idade_layout.addWidget(QLabel("anos"))
        idade_layout.addStretch()
        filter_layout.addLayout(idade_layout)
        
        # Filtro de score
        score_layout = QHBoxLayout()
        self.filtro_score_checkbox = QCheckBox("Filtrar por score:")
        self.filtro_score_checkbox.stateChanged.connect(self.toggle_filtro_score)
        score_layout.addWidget(self.filtro_score_checkbox)
        
        score_layout.addWidget(QLabel("De"))
        self.score_min_spin = QSpinBox()
        self.score_min_spin.setRange(0, 1000)
        self.score_min_spin.setValue(500)
        self.score_min_spin.setEnabled(False)
        score_layout.addWidget(self.score_min_spin)
        
        score_layout.addWidget(QLabel("até"))
        self.score_max_spin = QSpinBox()
        self.score_max_spin.setRange(0, 1000)
        self.score_max_spin.setValue(1000)
        self.score_max_spin.setEnabled(False)
        score_layout.addWidget(self.score_max_spin)
        score_layout.addStretch()
        filter_layout.addLayout(score_layout)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # Grupo de Exibição
        display_group = QGroupBox("👁️ Exibição")
        display_group.setStyleSheet("""
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(15,23,42,0.9), stop:1 rgba(15,23,42,0.7));
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 18px;
                margin-top: 12px;
                padding: 18px;
                padding-top: 36px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 22px;
                top: 8px;
                padding: 4px 14px;
                color: #22d3ee;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                background: rgba(6,182,212,0.06);
                border-radius: 12px;
            }
        """)
        display_layout = QHBoxLayout()
        display_layout.setSpacing(15)
        
        self.check_nome = QCheckBox("Nome")
        self.check_nome.setChecked(True)
        self.check_nome.stateChanged.connect(lambda: self.toggle_display('nome'))
        display_layout.addWidget(self.check_nome)
        
        self.check_cpf = QCheckBox("CPF")
        self.check_cpf.setChecked(True)
        self.check_cpf.stateChanged.connect(lambda: self.toggle_display('cpf'))
        display_layout.addWidget(self.check_cpf)
        
        self.check_idade = QCheckBox("Idade")
        self.check_idade.setChecked(True)
        self.check_idade.stateChanged.connect(lambda: self.toggle_display('idade'))
        display_layout.addWidget(self.check_idade)
        
        self.check_data = QCheckBox("Data Nasc.")
        self.check_data.setChecked(True)
        self.check_data.stateChanged.connect(lambda: self.toggle_display('data'))
        display_layout.addWidget(self.check_data)
        
        self.check_telefone = QCheckBox("Telefone")
        self.check_telefone.setChecked(True)
        self.check_telefone.stateChanged.connect(lambda: self.toggle_display('telefone'))
        display_layout.addWidget(self.check_telefone)
        
        self.check_score = QCheckBox("Score")
        self.check_score.setChecked(True)
        self.check_score.stateChanged.connect(lambda: self.toggle_display('score'))
        display_layout.addWidget(self.check_score)
        
        display_group.setLayout(display_layout)
        layout.addWidget(display_group)
        
        # Área de resultado com botões de cópia individual
        result_container = QGroupBox("📋 Resultado")
        result_container.setStyleSheet("""
            QGroupBox {
                background-color: #0a0e1a;
                border: 2px solid rgba(6,182,212,0.15);
                border-radius: 12px;
                margin-top: 20px;
                padding: 20px;
                padding-top: 35px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                top: 8px;
                padding: 0 10px;
                color: #22d3ee;
                font-size: 14px;
                font-weight: 600;
            }
        """)
        result_layout = QVBoxLayout()
        result_layout.setSpacing(8)
        
        # Estilo para os campos de resultado
        field_style = """
            QFrame {
                background-color: #111827;
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 12px;
                padding: 8px;
            }
        """
        
        label_style = """
            QLabel {
                color: #22d3ee;
                font-family: 'Consolas', 'SF Mono', monospace;
                font-size: 13px;
                font-weight: 500;
                background-color: transparent;
                border: none;
                padding: 0;
            }
        """
        
        copy_btn_style = """
            QPushButton {
                background-color: #059669;
                color: white;
                border: none;
                border-radius: 12px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
                min-width: 60px;
            }
            QPushButton:hover {
                background-color: #10b981;
            }
            QPushButton:pressed {
                background-color: #047857;
            }
        """
        
        # Campo Nome
        self.nome_frame = QFrame()
        self.nome_frame.setStyleSheet(field_style)
        nome_layout = QHBoxLayout(self.nome_frame)
        nome_layout.setContentsMargins(12, 8, 12, 8)
        self.nome_label = QLabel("👤 Nome: -")
        self.nome_label.setStyleSheet(label_style)
        nome_layout.addWidget(self.nome_label, 1)
        self.copy_nome_btn = QPushButton("📋 Copiar")
        self.copy_nome_btn.setStyleSheet(copy_btn_style)
        self.copy_nome_btn.clicked.connect(lambda: self.copy_field('nome'))
        nome_layout.addWidget(self.copy_nome_btn)
        result_layout.addWidget(self.nome_frame)
        
        # Campo CPF
        self.cpf_frame = QFrame()
        self.cpf_frame.setStyleSheet(field_style)
        cpf_layout = QHBoxLayout(self.cpf_frame)
        cpf_layout.setContentsMargins(12, 8, 12, 8)
        self.cpf_label = QLabel("🆔 CPF: -")
        self.cpf_label.setStyleSheet(label_style)
        cpf_layout.addWidget(self.cpf_label, 1)
        self.copy_cpf_btn = QPushButton("📋 Copiar")
        self.copy_cpf_btn.setStyleSheet(copy_btn_style)
        self.copy_cpf_btn.clicked.connect(lambda: self.copy_field('cpf'))
        cpf_layout.addWidget(self.copy_cpf_btn)
        result_layout.addWidget(self.cpf_frame)
        
        # Campo Idade
        self.idade_frame = QFrame()
        self.idade_frame.setStyleSheet(field_style)
        idade_layout = QHBoxLayout(self.idade_frame)
        idade_layout.setContentsMargins(12, 8, 12, 8)
        self.idade_label = QLabel("🎂 Idade: -")
        self.idade_label.setStyleSheet(label_style)
        idade_layout.addWidget(self.idade_label, 1)
        self.copy_idade_btn = QPushButton("📋 Copiar")
        self.copy_idade_btn.setStyleSheet(copy_btn_style)
        self.copy_idade_btn.clicked.connect(lambda: self.copy_field('idade'))
        idade_layout.addWidget(self.copy_idade_btn)
        result_layout.addWidget(self.idade_frame)
        
        # Campo Data Nascimento
        self.nasc_frame = QFrame()
        self.nasc_frame.setStyleSheet(field_style)
        nasc_layout = QHBoxLayout(self.nasc_frame)
        nasc_layout.setContentsMargins(12, 8, 12, 8)
        self.nasc_label = QLabel("📅 Nascimento: -")
        self.nasc_label.setStyleSheet(label_style)
        nasc_layout.addWidget(self.nasc_label, 1)
        self.copy_nasc_btn = QPushButton("📋 Copiar")
        self.copy_nasc_btn.setStyleSheet(copy_btn_style)
        self.copy_nasc_btn.clicked.connect(lambda: self.copy_field('nascimento'))
        nasc_layout.addWidget(self.copy_nasc_btn)
        result_layout.addWidget(self.nasc_frame)
        
        # Campo Telefone
        self.telefone_frame = QFrame()
        self.telefone_frame.setStyleSheet(field_style)
        telefone_layout = QHBoxLayout(self.telefone_frame)
        telefone_layout.setContentsMargins(12, 8, 12, 8)
        self.telefone_label = QLabel("📞 Telefone: -")
        self.telefone_label.setStyleSheet(label_style)
        telefone_layout.addWidget(self.telefone_label, 1)
        self.copy_telefone_btn = QPushButton("📋 Copiar")
        self.copy_telefone_btn.setStyleSheet(copy_btn_style)
        self.copy_telefone_btn.clicked.connect(lambda: self.copy_field('telefone'))
        telefone_layout.addWidget(self.copy_telefone_btn)
        result_layout.addWidget(self.telefone_frame)
        
        # Campo Score
        self.score_frame = QFrame()
        self.score_frame.setStyleSheet(field_style)
        score_layout = QHBoxLayout(self.score_frame)
        score_layout.setContentsMargins(12, 8, 12, 8)
        self.score_label = QLabel("⭐ Score: -")
        self.score_label.setStyleSheet(label_style)
        score_layout.addWidget(self.score_label, 1)
        self.copy_score_btn = QPushButton("📋 Copiar")
        self.copy_score_btn.setStyleSheet(copy_btn_style)
        self.copy_score_btn.clicked.connect(lambda: self.copy_field('score'))
        score_layout.addWidget(self.copy_score_btn)
        result_layout.addWidget(self.score_frame)
        
        result_container.setLayout(result_layout)
        layout.addWidget(result_container)
        
        # Atualizar visibilidade inicial dos campos
        self.update_field_visibility()
        
        # Grupo de Ações Principais
        actions_group = QGroupBox("🎮 Ações")
        actions_group.setStyleSheet("""
            QGroupBox {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(15,23,42,0.9), stop:1 rgba(15,23,42,0.7));
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 18px;
                margin-top: 18px;
                padding: 18px;
                padding-top: 36px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 22px;
                top: 8px;
                padding: 4px 14px;
                color: #22d3ee;
                font-size: 11px;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 1.5px;
                background: rgba(6,182,212,0.06);
                border-radius: 12px;
            }
        """)
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)
        
        # Botões principais (Gerar e Copiar Tudo)
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)
        
        self.generate_btn = QPushButton("🎲 GERAR PAR")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #059669, stop:1 #10b981);
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 14px 30px;
                border-radius: 14px;
                border: none;
                letter-spacing: 0.5px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #10b981, stop:1 #34d399); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #047857, stop:1 #059669); }
        """)
        self.generate_btn.clicked.connect(self.generate_pair)
        btn_layout.addWidget(self.generate_btn, 2)
        
        copy_btn = QPushButton("📋 COPIAR TUDO")
        copy_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891b2, stop:1 #06b6d4);
                color: white;
                font-size: 15px;
                font-weight: bold;
                padding: 14px 25px;
                border-radius: 14px;
                border: none;
                letter-spacing: 0.5px;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #22d3ee); }
            QPushButton:pressed { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #155e75, stop:1 #0891b2); }
        """)
        copy_btn.clicked.connect(self.copy_result)
        btn_layout.addWidget(copy_btn, 1)
        
        actions_layout.addLayout(btn_layout)
        
        # Botões secundários (Coletar, Ver, Exportar, Ferramentas)
        btn_layout2 = QHBoxLayout()
        btn_layout2.setSpacing(8)
        
        secondary_btn_style = """
            QPushButton {
                background: rgba(15,23,42,0.7);
                color: #f1f5f9;
                font-size: 12px;
                font-weight: 500;
                padding: 10px 15px;
                border-radius: 12px;
                border: 1px solid rgba(6,182,212,0.2);
            }
            QPushButton:hover {
                background: rgba(6,182,212,0.12);
                border-color: rgba(6,182,212,0.4);
                color: #22d3ee;
            }
        """
        
        collect_btn = QPushButton("📥 Coletar")
        collect_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0891b2, stop:1 #06b6d4);
                color: white;
                font-size: 12px;
                font-weight: 500;
                padding: 10px 15px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #06b6d4, stop:1 #22d3ee); }
        """)
        collect_btn.clicked.connect(self.start_collection)
        btn_layout2.addWidget(collect_btn)
        
        view_btn = QPushButton("📊 Ver Dados")
        view_btn.setStyleSheet(secondary_btn_style)
        view_btn.clicked.connect(self.show_data)
        btn_layout2.addWidget(view_btn)
        
        export_btn = QPushButton("💾 Exportar")
        export_btn.setStyleSheet(secondary_btn_style)
        export_btn.clicked.connect(self.export_data)
        btn_layout2.addWidget(export_btn)
        
        tools_btn = QPushButton("🛠️ Ferramentas")
        tools_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: white;
                font-size: 12px;
                font-weight: 500;
                padding: 10px 15px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover { background-color: #d97706; }
        """)
        tools_btn.clicked.connect(self.show_tools)
        btn_layout2.addWidget(tools_btn)
        
        actions_layout.addLayout(btn_layout2)
        
        # Botões de configuração
        btn_layout3 = QHBoxLayout()
        btn_layout3.setSpacing(8)
        
        config_btn = QPushButton("⚙️ Configurar")
        config_btn.setStyleSheet(secondary_btn_style)
        config_btn.clicked.connect(self.show_config_dialog)
        btn_layout3.addWidget(config_btn)
        
        contas_btn = QPushButton("📱 Contas/Sessões")
        contas_btn.setStyleSheet(secondary_btn_style)
        contas_btn.clicked.connect(self.show_contas_dialog)
        contas_btn.setToolTip("Gerenciar contas do Telegram e importar/exportar sessões")
        btn_layout3.addWidget(contas_btn)
        
        groups_btn = QPushButton("📋 Grupos")
        groups_btn.setStyleSheet(secondary_btn_style)
        groups_btn.clicked.connect(self.show_groups_dialog)
        btn_layout3.addWidget(groups_btn)
        
        actions_layout.addLayout(btn_layout3)
        
        # === ATALHOS RÁPIDOS PARA GERADORES ===
        quick_tools_group = QGroupBox("🚀 Acesso Rápido - Geradores")
        quick_tools_group.setStyleSheet("""
            QGroupBox {
                background-color: #111827;
                border: 1px solid rgba(6,182,212,0.15);
                border-radius: 12px;
                margin-top: 10px;
                padding: 15px;
                padding-top: 30px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 20px;
                top: 5px;
                padding: 0 10px;
                color: #22d3ee;
                font-size: 12px;
                font-weight: 600;
            }
        """)
        quick_tools_layout = QHBoxLayout()
        quick_tools_layout.setSpacing(8)
        
        quick_btn_style = """
            QPushButton {
                background-color: #059669;
                color: white;
                font-size: 11px;
                font-weight: 500;
                padding: 8px 12px;
                border-radius: 12px;
                border: none;
            }
            QPushButton:hover {
                background-color: #10b981;
            }
        """
        
        # Botão Gerar Cartão
        card_btn = QPushButton("💳 Cartões")
        card_btn.setStyleSheet(quick_btn_style)
        card_btn.setToolTip("Gerar números de cartão de crédito")
        card_btn.clicked.connect(lambda: self.show_tools_tab(0))
        quick_tools_layout.addWidget(card_btn)
        
        # Botão Gerar CEP
        cep_btn = QPushButton("🏠 CEP")
        cep_btn.setStyleSheet(quick_btn_style)
        cep_btn.setToolTip("Gerar endereços com CEP válido")
        cep_btn.clicked.connect(lambda: self.show_tools_tab(1))
        quick_tools_layout.addWidget(cep_btn)
        
        # Botão Validador CPF/CNPJ
        cpf_btn = QPushButton("✅ CPF/CNPJ")
        cpf_btn.setStyleSheet(quick_btn_style.replace("#059669", "#0891b2").replace("#10b981", "#0e7490"))
        cpf_btn.setToolTip("Validar e gerar CPF/CNPJ")
        cpf_btn.clicked.connect(lambda: self.show_tools_tab(4))
        quick_tools_layout.addWidget(cpf_btn)
        
        # Botão Dados Fake
        fake_btn = QPushButton("🎭 Dados Fake")
        fake_btn.setStyleSheet(quick_btn_style.replace("#059669", "#0891b2").replace("#10b981", "#06b6d4"))
        fake_btn.setToolTip("Gerar dados fictícios completos")
        fake_btn.clicked.connect(lambda: self.show_tools_tab(5))
        quick_tools_layout.addWidget(fake_btn)
        
        # Botão Formatador
        format_btn = QPushButton("📧 Formatador")
        format_btn.setStyleSheet(quick_btn_style.replace("#059669", "#f59e0b").replace("#10b981", "#d97706"))
        format_btn.setToolTip("Formatar contas e dados")
        format_btn.clicked.connect(lambda: self.show_tools_tab(2))
        quick_tools_layout.addWidget(format_btn)
        
        quick_tools_group.setLayout(quick_tools_layout)
        actions_layout.addWidget(quick_tools_group)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Status
        self.stats_label = QLabel()
        self.stats_label.setAlignment(Qt.AlignCenter)
        self.stats_label.setStyleSheet("color: #94a3b8; font-size: 12px;")
        layout.addWidget(self.stats_label)
        
        # Finalizar aba do Gerador de Pares
        gerador_tab.setLayout(layout)
        self.main_tabs.addTab(gerador_tab, "🎲 Gerador de Pares")
        
        # === ABA 2: FERRAMENTAS ===
        ferramentas_tab = QWidget()
        ferramentas_layout = QVBoxLayout()
        ferramentas_layout.setContentsMargins(10, 10, 10, 10)
        
        # Sub-abas de ferramentas
        self.tools_tabs = QTabWidget()
        self.tools_tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background: transparent;
            }
            QTabBar::tab {
                background: transparent;
                color: #64748b;
                padding: 10px 20px;
                margin-right: 4px;
                border: none;
                border-bottom: 2px solid transparent;
                font-weight: 500;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                color: #06b6d4;
                border-bottom: 2px solid #06b6d4;
            }
            QTabBar::tab:hover {
                color: #ffffff;
            }
        """)
        
        # Criar instância do ToolsDialog para reutilizar seus métodos
        tools_helper = ToolsDialog(self)
        
        # Adicionar as abas de ferramentas
        self.tools_tabs.addTab(tools_helper.create_card_generator_tab(), "💳 Cartões")
        self.tools_tabs.addTab(tools_helper.create_cep_generator_tab(), "🏠 CEP")
        self.tools_tabs.addTab(tools_helper.create_account_formatter_tab(), "📧 Formatador")
        self.tools_tabs.addTab(DataOrganizer(), "🗂️ Organizador")
        self.tools_tabs.addTab(ValidadorWidget(), "✅ CPF/CNPJ")
        self.tools_tabs.addTab(GeradorFakeWidget(), "🎭 Dados Fake")
        self.tools_tabs.addTab(BackupWidget(), "💾 Backup")
        
        ferramentas_layout.addWidget(self.tools_tabs)
        ferramentas_tab.setLayout(ferramentas_layout)
        self.main_tabs.addTab(ferramentas_tab, "🛠️ Ferramentas")
        
        # === ABA 3: NAVEGADOR SEGURO ===
        navegador_tab = BrowserWidget()
        self.main_tabs.addTab(navegador_tab, "🌐 Navegador Seguro")
        
        # === ABA 4: CONFIGURAÇÕES DE PERFIS ===
        if PROFILE_DEFAULTS_AVAILABLE:
            config_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "browser_config")
            profile_defaults_tab = ProfileDefaultsWidget(config_dir)
            self.main_tabs.addTab(profile_defaults_tab, "⚙️ Config. Perfis")
        
        # === ABA 5: CRUNCHYROLL BOT ===
        if CRUNCHYROLL_AVAILABLE:
            crunchyroll_tab = CrunchyrollWidget()
            self.main_tabs.addTab(crunchyroll_tab, "🍦 Crunchyroll Bot")
        
        # === ABA 7: CRUNCHYROLL LOGIN BOT ===
        if CRUNCHYROLL_LOGIN_AVAILABLE:
            crunchyroll_login_tab = CrunchyrollLoginWidget()
            self.main_tabs.addTab(crunchyroll_login_tab, "🔐 Crunchyroll Login")

        # === ABA 8: BLOCO DE NOTAS ===
        self.notepad_tab = NotepadWidget()
        self.main_tabs.addTab(self.notepad_tab, "📝 Bloco de Notas")
        
        # Adicionar as abas principais ao layout
        main_layout.addWidget(self.main_tabs)
        
        central_widget.setLayout(main_layout)
        
        # Status bar
        self.statusBar().showMessage("Pronto")
        
        self.update_stats()
    
    def toggle_filtro(self, state):
        enabled = state == Qt.Checked
        self.idade_min_spin.setEnabled(enabled)
        self.idade_max_spin.setEnabled(enabled)
    
    def toggle_filtro_score(self, state):
        enabled = state == Qt.Checked
        self.score_min_spin.setEnabled(enabled)
        self.score_max_spin.setEnabled(enabled)
    
    def toggle_display(self, field):
        if field == 'nome':
            self.mostrar_nome = self.check_nome.isChecked()
        elif field == 'cpf':
            self.mostrar_cpf = self.check_cpf.isChecked()
        elif field == 'idade':
            self.mostrar_idade = self.check_idade.isChecked()
        elif field == 'data':
            self.mostrar_data = self.check_data.isChecked()
        elif field == 'telefone':
            self.mostrar_telefone = self.check_telefone.isChecked()
        elif field == 'score':
            self.mostrar_score = self.check_score.isChecked()
        
        # Atualizar visibilidade dos campos
        self.update_field_visibility()
        
        if self.current_pair:
            self.display_pair(self.current_pair)
    
    def update_stats(self):
        stats = self.db.get_stats()
        self.stats_label.setText(
            f"📊 Total: {stats['total']} | "
            f"✅ Completos: {stats['complete']} | "
            f"📅 Com nascimento: {stats.get('with_birth', 0)} | "
            f"📞 Com telefone: {stats['with_phone']} | "
            f"⭐ Com score: {stats['with_score']}"
        )
    
    def generate_pair(self):
        filters = {}
        
        if self.filtro_checkbox.isChecked():
            filters['idade_min'] = self.idade_min_spin.value()
            filters['idade_max'] = self.idade_max_spin.value()
        
        if self.filtro_score_checkbox.isChecked():
            filters['score_min'] = self.score_min_spin.value()
            filters['score_max'] = self.score_max_spin.value()
        
        pair = self.db.get_random_pair(filters)
        
        if pair:
            self.current_pair = pair
            self.display_pair(pair)
        else:
            # Limpar os campos quando não houver resultado
            self.nome_label.setText("👤 Nome: -")
            self.cpf_label.setText("🆔 CPF: -")
            self.idade_label.setText("🎂 Idade: -")
            self.nasc_label.setText("📅 Nascimento: -")
            self.telefone_label.setText("📞 Telefone: -")
            self.score_label.setText("⭐ Score: -")
            self.current_pair = None
            self.statusBar().showMessage("❌ Nenhum registro encontrado com os filtros aplicados", 3000)
    
    def display_pair(self, pair):
        """Exibe os dados do par nos campos individuais"""
        # Atualizar labels com os valores
        if pair.get('nome'):
            self.nome_label.setText(f"👤 Nome: {pair['nome']}")
        else:
            self.nome_label.setText("👤 Nome: -")
        
        if pair.get('cpf'):
            self.cpf_label.setText(f"🆔 CPF: {pair['cpf']}")
        else:
            self.cpf_label.setText("🆔 CPF: -")
        
        if pair.get('idade'):
            self.idade_label.setText(f"🎂 Idade: {pair['idade']} anos")
        else:
            self.idade_label.setText("🎂 Idade: -")
        
        if pair.get('nascimento'):
            self.nasc_label.setText(f"📅 Nascimento: {pair['nascimento']}")
        else:
            self.nasc_label.setText("📅 Nascimento: -")
        
        if pair.get('telefone'):
            self.telefone_label.setText(f"📞 Telefone: {pair['telefone']}")
        else:
            self.telefone_label.setText("📞 Telefone: -")
        
        if pair.get('score'):
            self.score_label.setText(f"⭐ Score: {pair['score']}")
        else:
            self.score_label.setText("⭐ Score: -")
        
        # Atualizar visibilidade dos campos
        self.update_field_visibility()
    
    def update_field_visibility(self):
        """Atualiza a visibilidade dos campos baseado nas opções de exibição"""
        self.nome_frame.setVisible(self.mostrar_nome)
        self.cpf_frame.setVisible(self.mostrar_cpf)
        self.idade_frame.setVisible(self.mostrar_idade)
        self.nasc_frame.setVisible(self.mostrar_data)
        self.telefone_frame.setVisible(self.mostrar_telefone)
        self.score_frame.setVisible(self.mostrar_score)
    
    def copy_field(self, field):
        """Copia o valor de um campo específico para a área de transferência"""
        if not self.current_pair:
            self.statusBar().showMessage("⚠️ Nenhum dado para copiar", 2000)
            return
        
        value = None
        field_name = ""
        
        if field == 'nome' and self.current_pair.get('nome'):
            value = self.current_pair['nome']
            field_name = "Nome"
        elif field == 'cpf' and self.current_pair.get('cpf'):
            value = self.current_pair['cpf']
            field_name = "CPF"
        elif field == 'idade' and self.current_pair.get('idade'):
            value = str(self.current_pair['idade'])
            field_name = "Idade"
        elif field == 'nascimento' and self.current_pair.get('nascimento'):
            value = self.current_pair['nascimento']
            field_name = "Nascimento"
        elif field == 'telefone' and self.current_pair.get('telefone'):
            value = self.current_pair['telefone']
            field_name = "Telefone"
        elif field == 'score' and self.current_pair.get('score'):
            value = str(self.current_pair['score'])
            field_name = "Score"
        
        if value:
            QApplication.clipboard().setText(value)
            self.statusBar().showMessage(f"✅ {field_name} copiado!", 2000)
        else:
            self.statusBar().showMessage(f"⚠️ {field_name} não disponível", 2000)
    
    def copy_result(self):
        """Copia todos os campos visíveis para a área de transferência"""
        if not self.current_pair:
            self.statusBar().showMessage("⚠️ Nenhum dado para copiar", 2000)
            return
        
        lines = []
        pair = self.current_pair
        
        if self.mostrar_nome and pair.get('nome'):
            lines.append(f"👤 Nome: {pair['nome']}")
        
        if self.mostrar_cpf and pair.get('cpf'):
            lines.append(f"🆔 CPF: {pair['cpf']}")
        
        if self.mostrar_idade and pair.get('idade'):
            lines.append(f"🎂 Idade: {pair['idade']} anos")
        
        if self.mostrar_data and pair.get('nascimento'):
            lines.append(f"📅 Nascimento: {pair['nascimento']}")
        
        if self.mostrar_telefone and pair.get('telefone'):
            lines.append(f"📞 Telefone: {pair['telefone']}")
        
        if self.mostrar_score and pair.get('score'):
            lines.append(f"⭐ Score: {pair['score']}")
        
        if lines:
            text = '\n'.join(lines)
            QApplication.clipboard().setText(text)
            self.statusBar().showMessage("✅ Todos os dados copiados!", 2000)
        else:
            self.statusBar().showMessage("⚠️ Nenhum dado para copiar", 2000)
    
    def show_tools(self):
        """Muda para a aba de ferramentas integrada"""
        self.main_tabs.setCurrentIndex(1)  # Índice da aba Ferramentas
    
    def show_tools_tab(self, tab_index):
        """Muda para a aba de ferramentas e seleciona uma sub-aba específica"""
        self.main_tabs.setCurrentIndex(1)  # Vai para aba Ferramentas
        self.tools_tabs.setCurrentIndex(tab_index)  # Seleciona a sub-aba
    
    def show_groups_dialog(self):
        dialog = GroupManagerDialog(self)
        dialog.exec_()
    
    def start_collection(self):
        # Verificar se existe conta ativa no gerenciador
        config_manager = ConfigManager()
        conta_ativa = config_manager.get_conta_ativa()
        
        if not settings.is_configured and not conta_ativa:
            QMessageBox.warning(self, "Configuração", "Configure as credenciais primeiro!")
            self.show_config_dialog()
            return
        
        # Carregar grupos
        groups_file = BASE_DIR / 'grupos.json'
        groups = [settings.default_group]
        if groups_file.exists():
            try:
                with open(groups_file, 'r') as f:
                    groups = json.load(f)
            except (json.JSONDecodeError, IOError, PermissionError) as e:
                print(f"Aviso: Erro ao carregar grupos: {e}")
        
        # Perguntar quais grupos coletar
        if len(groups) > 1:
            reply = QMessageBox.question(
                self, "Coletar Dados",
                f"Você tem {len(groups)} grupos configurados.\n\n"
                f"Grupos: {', '.join(groups)}\n\n"
                "Deseja coletar de TODOS os grupos?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            
            if reply == QMessageBox.Cancel:
                return
            elif reply == QMessageBox.No:
                groups = [groups[0]]  # Só o primeiro
        else:
            reply = QMessageBox.question(
                self, "Coletar Dados",
                "Você receberá um código SMS no Telegram.\n\nDeseja continuar?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
        
        # Perguntar sobre exigir data de nascimento
        exigir_data = QMessageBox.question(
            self, "Campos Obrigatórios",
            "📅 Deseja EXIGIR DATA DE NASCIMENTO?\n\n"
            "Se SIM, registros SEM data de nascimento serão IGNORADOS.\n"
            "Isso garante que você só colete dados completos.",
            QMessageBox.Yes | QMessageBox.No
        )
        exigir_data_nascimento = (exigir_data == QMessageBox.Yes)
        
        # Perguntar sobre filtro de idosos
        filtrar_idosos = False
        idade_maxima = None
        
        filtro_reply = QMessageBox.question(
            self, "Filtro de Idade",
            "🧓 Deseja FILTRAR IDOSOS da coleta?\n\n"
            "Se SIM, pessoas com 60+ anos serão IGNORADAS.\n"
            "Isso ajuda a evitar coletar dados de idosos.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if filtro_reply == QMessageBox.Yes:
            filtrar_idosos = True
            # Perguntar idade máxima personalizada
            idade_input, ok = QInputDialog.getInt(
                self, "Idade Máxima",
                "Digite a idade MÁXIMA permitida:\n(Pessoas acima dessa idade serão ignoradas)",
                59, 18, 100, 1
            )
            if ok:
                idade_maxima = idade_input
            else:
                idade_maxima = 59  # Padrão
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        self.generate_btn.setEnabled(False)
        
        # Obter ID da conta ativa
        conta_id = conta_ativa['id'] if conta_ativa else None
        
        self.collector_thread = CollectorThread(
            groups=groups,
            filtrar_idosos=filtrar_idosos,
            idade_maxima=idade_maxima,
            exigir_data_nascimento=exigir_data_nascimento,
            conta_id=conta_id
        )
        self.collector_thread.progress.connect(self.show_progress)
        self.collector_thread.error.connect(self.show_error)
        self.collector_thread.finished.connect(self.collection_finished)
        self.collector_thread.code_requested.connect(self.show_code_dialog)
        self.collector_thread.password_requested.connect(self.show_password_dialog)
        self.collector_thread.start()
    
    def show_code_dialog(self, phone: str):
        dialog = CodeInputDialog(phone, self)
        if dialog.exec_() == QDialog.Accepted and dialog.code:
            self.collector_thread.set_verification_code(dialog.code)
        else:
            self.show_error("Autenticação cancelada.")
    
    def show_password_dialog(self):
        dialog = PasswordInputDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.password:
            self.collector_thread.set_password(dialog.password)
        else:
            self.show_error("Autenticação 2FA cancelada.")
    
    def show_progress(self, message):
        self.statusBar().showMessage(message)
    
    def show_error(self, error):
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        QMessageBox.critical(self, "Erro", f"Erro na coleta:\n{error}")
    
    def collection_finished(self, collected):
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        # Atualizar conexão com banco de dados após coleta
        self.refresh_database()
        QMessageBox.information(self, "Sucesso", f"Coleta concluída!\n\n{collected} novos registros.")
    
    def show_data(self):
        # Usar o banco de dados atual (já configurado corretamente)
        dialog = DataViewDialog(self.db, self)
        dialog.exec_()
    
    def export_data(self):
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar como CSV", "dados_completo.csv", "CSV Files (*.csv)"
        )
        if filepath:
            if self.db.export_csv(filepath, 'completo'):
                QMessageBox.information(self, "Sucesso", f"Exportado para:\n{filepath}")
            else:
                QMessageBox.critical(self, "Erro", "Erro ao exportar")


def main():
    app = QApplication(sys.argv)
    app.setStyle('Fusion')
    
    # Aplicar paleta escura
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(10, 14, 26))
    palette.setColor(QPalette.WindowText, QColor(241, 245, 249))
    palette.setColor(QPalette.Base, QColor(17, 24, 39))
    palette.setColor(QPalette.AlternateBase, QColor(15, 23, 42))
    palette.setColor(QPalette.ToolTipBase, QColor(30, 41, 59))
    palette.setColor(QPalette.ToolTipText, QColor(241, 245, 249))
    palette.setColor(QPalette.Text, QColor(241, 245, 249))
    palette.setColor(QPalette.Button, QColor(8, 145, 178))
    palette.setColor(QPalette.ButtonText, QColor(241, 245, 249))
    palette.setColor(QPalette.BrightText, QColor(34, 211, 238))
    palette.setColor(QPalette.Highlight, QColor(6, 182, 212))
    palette.setColor(QPalette.HighlightedText, QColor(10, 14, 26))
    app.setPalette(palette)
    
    window = SimpleApp()
    window.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
