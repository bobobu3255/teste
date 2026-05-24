#!/usr/bin/env python3
"""Dialogos reutilizaveis do aplicativo principal."""

import json
import os

from PyQt5.QtCore import QObject, Qt, QThread, QTimer, pyqtSignal
from PyQt5.QtWidgets import (
    QAbstractItemView, QApplication, QComboBox, QDialog, QFileDialog, QFormLayout,
    QHBoxLayout, QHeaderView, QLabel, QLineEdit, QListWidget, QMessageBox,
    QProgressBar, QPushButton, QSpinBox, QTableWidget, QTableWidgetItem, QVBoxLayout,
)

from settings import BASE_DIR, settings
from theme import DARK_STYLE_PRO as DARK_STYLE


class DataSearchWorker(QObject):
    finished = pyqtSignal(int, object, int)
    error = pyqtSignal(int, str)

    def __init__(
        self,
        db,
        request_id,
        mode,
        search,
        cpf_filter,
        idade_min,
        idade_max,
        order_by,
        page,
        per_page,
    ):
        super().__init__()
        self.db = db
        self.request_id = request_id
        self.mode = mode
        self.search = search
        self.cpf_filter = cpf_filter
        self.idade_min = idade_min
        self.idade_max = idade_max
        self.order_by = order_by
        self.page = page
        self.per_page = per_page

    def run(self):
        try:
            if self.mode == "Sorteados anteriores":
                data = self.db.get_recent_draws(limit=700) if hasattr(self.db, "get_recent_draws") else []
                if self.search or self.cpf_filter or self.idade_min is not None or self.idade_max is not None:
                    terms = [t for t in self.search.lower().split() if t]
                    cpf_digits = "".join(ch for ch in self.cpf_filter if ch.isdigit())
                    data = [
                        row for row in data
                        if all(t in " ".join(str(v or "").lower() for v in row.values()) for t in terms)
                        and (not cpf_digits or cpf_digits in "".join(ch for ch in str(row.get("cpf", "")) if ch.isdigit()))
                        and (self.idade_min is None or int(row.get("idade") or -1) >= self.idade_min)
                        and (self.idade_max is None or int(row.get("idade") or 999) <= self.idade_max)
                    ]
                self.finished.emit(self.request_id, data, len(data))
                return

            if (self.search or self.cpf_filter or self.idade_min is not None or self.idade_max is not None) and hasattr(self.db, "search_data"):
                data = self.db.search_data(
                    self.search,
                    limit=900,
                    idade_min=self.idade_min,
                    idade_max=self.idade_max,
                    cpf_query=self.cpf_filter,
                    order_by=self.order_by,
                )
                self.finished.emit(self.request_id, data, len(data))
                return

            data, total = self.db.get_all_data_paginated(page=self.page, per_page=self.per_page)
            self.finished.emit(self.request_id, data, total)
        except Exception as exc:
            self.error.emit(self.request_id, str(exc))

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

        newer_btn = QPushButton("Mais novos")
        newer_btn.clicked.connect(self.previous_page)
        btn_layout.addWidget(newer_btn)

        older_btn = QPushButton("Mais antigos")
        older_btn.clicked.connect(self.next_page)
        btn_layout.addWidget(older_btn)

        copy_btn = QPushButton("Copiar selecionado")
        copy_btn.clicked.connect(self.copy_selected_record)
        btn_layout.addWidget(copy_btn)
        
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
        self.page = 1
        self.per_page = 350
        self.total = 0
        self.current_records = []
        self._search_request_id = 0
        self._search_thread = None
        self._search_worker = None
        self._pending_search_params = None
        self.setWindowTitle("Dados Coletados")
        self.setModal(True)
        self.setMinimumSize(1040, 680)
        self.setStyleSheet(DARK_STYLE)
        self.search_timer = QTimer(self)
        self.search_timer.setSingleShot(True)
        self.search_timer.timeout.connect(lambda: self.load_data(reset_page=True))
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Filtros
        filter_layout = QHBoxLayout()

        self.mode_combo = QComboBox()
        self.mode_combo.addItems(["Ultimos coletados", "Sorteados anteriores"])
        self.mode_combo.currentIndexChanged.connect(lambda: self.load_data(reset_page=True))
        filter_layout.addWidget(self.mode_combo)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Buscar por nome ou CPF...")
        self.search_input.textChanged.connect(self.filter_data)
        self.search_input.returnPressed.connect(lambda: self.load_data(reset_page=True))
        self.search_input.setPlaceholderText("Buscar em tudo: nome, CPF, telefone, nascimento, cidade, estado ou score...")
        filter_layout.addWidget(self.search_input)
        
        refresh_btn = QPushButton("🔄 Atualizar")
        refresh_btn.clicked.connect(self.load_data)
        filter_layout.addWidget(refresh_btn)
        
        layout.addLayout(filter_layout)

        advanced_layout = QHBoxLayout()

        self.cpf_filter_input = QLineEdit()
        self.cpf_filter_input.setPlaceholderText("CPF contem...")
        self.cpf_filter_input.textChanged.connect(self.filter_data)
        advanced_layout.addWidget(self.cpf_filter_input)

        self.age_min_spin = QSpinBox()
        self.age_min_spin.setRange(0, 120)
        self.age_min_spin.setSpecialValueText("Idade min.")
        self.age_min_spin.valueChanged.connect(lambda: self.load_data(reset_page=True))
        advanced_layout.addWidget(self.age_min_spin)

        self.age_max_spin = QSpinBox()
        self.age_max_spin.setRange(0, 120)
        self.age_max_spin.setSpecialValueText("Idade max.")
        self.age_max_spin.valueChanged.connect(lambda: self.load_data(reset_page=True))
        advanced_layout.addWidget(self.age_max_spin)

        self.order_combo = QComboBox()
        self.order_combo.addItems([
            "Mais recentes",
            "Mais antigos",
            "Nome A-Z",
            "Idade menor",
            "Idade maior",
            "Score maior",
            "Score menor",
        ])
        self.order_combo.currentIndexChanged.connect(lambda: self.load_data(reset_page=True))
        advanced_layout.addWidget(self.order_combo)

        clear_btn = QPushButton("Limpar filtros")
        clear_btn.clicked.connect(self.clear_filters)
        advanced_layout.addWidget(clear_btn)

        layout.addLayout(advanced_layout)

        self.summary_label = QLabel("Carregando dados...")
        self.summary_label.setStyleSheet("color:#94a3b8; padding:4px 2px;")
        layout.addWidget(self.summary_label)
        
        # Tabela
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(["ID", "Nome", "CPF", "Nasc.", "Idade", "Telefone", "Score", "Cidade/UF", "Coleta/Uso"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.cellClicked.connect(self.copy_cell_value)
        self.table.doubleClicked.connect(self.copy_selected_record)
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
    
    def _collect_search_params(self):
        """Coleta filtros atuais sem tocar no banco, para a busca assíncrona."""
        order_map = {
            "Mais recentes": "recent",
            "Mais antigos": "oldest",
            "Nome A-Z": "name",
            "Idade menor": "age_asc",
            "Idade maior": "age_desc",
            "Score maior": "score_desc",
            "Score menor": "score_asc",
        }
        return {
            "mode": self.mode_combo.currentText(),
            "search": self.search_input.text().strip(),
            "cpf_filter": self.cpf_filter_input.text().strip(),
            "idade_min": self.age_min_spin.value() or None,
            "idade_max": self.age_max_spin.value() or None,
            "order_by": order_map.get(self.order_combo.currentText(), "recent"),
            "page": self.page,
            "per_page": self.per_page,
        }

    def load_data(self, reset_page=False):
        if reset_page:
            self.page = 1
        params = self._collect_search_params()
        self._search_request_id += 1
        params["request_id"] = self._search_request_id
        if self._search_thread and self._search_thread.isRunning():
            self._pending_search_params = params
            self.summary_label.setText("Atualizando busca em segundo plano...")
            return
        self._start_search_worker(params)

    def _start_search_worker(self, params):
        self.summary_label.setText("Buscando sem travar a interface...")
        thread = QThread(self)
        worker = DataSearchWorker(
            self.db,
            params["request_id"],
            params["mode"],
            params["search"],
            params["cpf_filter"],
            params["idade_min"],
            params["idade_max"],
            params["order_by"],
            params["page"],
            params["per_page"],
        )
        worker.moveToThread(thread)
        thread.started.connect(worker.run)
        worker.finished.connect(self._apply_loaded_data)
        worker.error.connect(self._search_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(lambda t=thread: self._finish_search_thread(t))
        self._search_thread = thread
        self._search_worker = worker
        thread.start()

    def _finish_search_thread(self, thread):
        if self._search_thread is thread:
            self._search_thread = None
            self._search_worker = None
        if self._pending_search_params:
            params = self._pending_search_params
            self._pending_search_params = None
            QTimer.singleShot(0, lambda: self._start_search_worker(params))

    def _apply_loaded_data(self, request_id, data, total):
        if request_id != self._search_request_id:
            return
        search = self.search_input.text().strip()
        mode = self.mode_combo.currentText()
        cpf_filter = self.cpf_filter_input.text().strip()
        idade_min = self.age_min_spin.value() or None
        idade_max = self.age_max_spin.value() or None
        self.total = total
        self.current_records = data
        self.table.setUpdatesEnabled(False)
        try:
            self.table.setRowCount(len(data))
            for row, record in enumerate(data):
                self.table.setItem(row, 0, QTableWidgetItem(str(record.get('id', ''))))
                self.table.setItem(row, 1, QTableWidgetItem(record.get('nome', '')))
                self.table.setItem(row, 2, QTableWidgetItem(record.get('cpf', '')))
                self.table.setItem(row, 3, QTableWidgetItem(record.get('nascimento', '')))
                self.table.setItem(row, 4, QTableWidgetItem(str(record.get('idade', '') or '')))
                self.table.setItem(row, 5, QTableWidgetItem(record.get('telefone', '')))
                self.table.setItem(row, 6, QTableWidgetItem(str(record.get('score', '') if record.get('score') is not None else '')))
                cidade_uf = " / ".join(v for v in [record.get('cidade', ''), record.get('estado', '')] if v)
                self.table.setItem(row, 7, QTableWidgetItem(cidade_uf))
                date_value = record.get('data_sorteio') or record.get('data_coleta') or ''
                self.table.setItem(row, 8, QTableWidgetItem(str(date_value)))
        finally:
            self.table.setUpdatesEnabled(True)

        active_filters = []
        if search:
            active_filters.append(search)
        if cpf_filter:
            active_filters.append(f"CPF {cpf_filter}")
        if idade_min is not None:
            active_filters.append(f"idade >= {idade_min}")
        if idade_max is not None:
            active_filters.append(f"idade <= {idade_max}")

        if active_filters:
            self.summary_label.setText(f"{len(data)} resultado(s) encontrados para: {' | '.join(active_filters)}")
        elif mode == "Sorteados anteriores":
            self.summary_label.setText(f"{len(data)} dado(s) usados anteriormente no gerador.")
        else:
            start = ((self.page - 1) * self.per_page) + 1 if data else 0
            end = min(self.page * self.per_page, self.total)
            self.summary_label.setText(f"Mostrando {start}-{end} de {self.total} registro(s). Pagina {self.page}.")

    def _search_error(self, request_id, message):
        if request_id != self._search_request_id:
            return
        self.summary_label.setText(f"Erro na busca: {message}")
    
    def filter_data(self):
        self.search_timer.start(350)

    def clear_filters(self):
        self.search_input.clear()
        self.cpf_filter_input.clear()
        self.age_min_spin.setValue(0)
        self.age_max_spin.setValue(0)
        self.order_combo.setCurrentIndex(0)
        self.mode_combo.setCurrentIndex(0)
        self.load_data(reset_page=True)

    def previous_page(self):
        if self.search_input.text().strip() or self.mode_combo.currentText() == "Sorteados anteriores":
            return
        if self.page > 1:
            self.page -= 1
            self.load_data()

    def next_page(self):
        if self.search_input.text().strip() or self.mode_combo.currentText() == "Sorteados anteriores":
            return
        if self.page * self.per_page < self.total:
            self.page += 1
            self.load_data()

    def selected_record(self):
        rows = self.table.selectionModel().selectedRows() if self.table.selectionModel() else []
        if not rows:
            return None
        index = rows[0].row()
        if 0 <= index < len(self.current_records):
            return self.current_records[index]
        return None

    def copy_cell_value(self, row, column):
        item = self.table.item(row, column)
        if not item:
            return
        value = item.text().strip()
        if not value:
            return
        QApplication.clipboard().setText(value)
        header = self.table.horizontalHeaderItem(column)
        label = header.text() if header else "Campo"
        self.summary_label.setText(f"{label} copiado: {value}")

    def copy_selected_record(self, *_):
        record = self.selected_record()
        if not record:
            return
        parts = [
            f"Nome: {record.get('nome', '')}",
            f"CPF: {record.get('cpf', '')}",
            f"Nascimento: {record.get('nascimento', '')}",
            f"Idade: {record.get('idade', '')}",
            f"Telefone: {record.get('telefone', '')}",
            f"Score: {record.get('score', '')}",
        ]
        cidade_uf = " / ".join(v for v in [record.get('cidade', ''), record.get('estado', '')] if v)
        if cidade_uf:
            parts.append(f"Cidade/UF: {cidade_uf}")
        QApplication.clipboard().setText("\n".join(parts))
    
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
