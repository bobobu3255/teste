#!/usr/bin/env python3
"""
Profile Defaults Widget - Interface Gráfica para Gerenciamento de Configurações Padrão
Telegram Collector Pro v10.0

Este módulo contém a interface gráfica PyQt5 para gerenciar:
- Abas favoritas padrão para novos perfis
- Extensões padrão para novos perfis
- Gerenciador de senhas portátil

Autor: Telegram Collector Team
Versão: 1.0
"""

import os
import json
from pathlib import Path
from typing import Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox,
    QGroupBox, QFormLayout, QMessageBox, QSpinBox,
    QCheckBox, QTextEdit, QSplitter, QFrame, QScrollArea,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QDialogButtonBox, QTabWidget, QInputDialog, QFileDialog,
    QMenu, QAction
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QColor

from app.services.profile_defaults_manager import (
    FavoritesManager, ExtensionsManager, PasswordManager, ProfileDefaultsManager
)


class AddFavoriteDialog(QDialog):
    """Diálogo para adicionar/editar favorito."""
    
    def __init__(self, parent=None, favorite: dict = None):
        super().__init__(parent)
        self.favorite = favorite
        self.result_data = None
        self.setWindowTitle("Adicionar Favorito" if not favorite else "Editar Favorito")
        self.setMinimumWidth(450)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("⭐ Configurar Favorito")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #fbbf24;")
        layout.addWidget(title)
        
        # Formulário
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ex: Netflix, YouTube, Gmail...")
        if self.favorite:
            self.name_input.setText(self.favorite.get("name", ""))
        form.addRow("Nome:", self.name_input)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://exemplo.com")
        if self.favorite:
            self.url_input.setText(self.favorite.get("url", ""))
        form.addRow("URL:", self.url_input)
        
        self.folder_combo = QComboBox()
        self.folder_combo.setEditable(True)
        self.folder_combo.addItems([
            "Barra de Favoritos",
            "Streaming",
            "Redes Sociais",
            "Trabalho",
            "Compras",
            "Finanças",
            "Outros"
        ])
        if self.favorite:
            folder = self.favorite.get("folder", "Barra de Favoritos")
            index = self.folder_combo.findText(folder)
            if index >= 0:
                self.folder_combo.setCurrentIndex(index)
            else:
                self.folder_combo.setCurrentText(folder)
        form.addRow("Pasta:", self.folder_combo)
        
        self.icon_input = QLineEdit()
        self.icon_input.setPlaceholderText("Emoji opcional (ex: 🎬, 📧, 💼)")
        if self.favorite:
            self.icon_input.setText(self.favorite.get("icon", ""))
        form.addRow("Ícone:", self.icon_input)
        
        layout.addLayout(form)
        
        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def accept(self):
        name = self.name_input.text().strip()
        url = self.url_input.text().strip()
        
        if not name or not url:
            QMessageBox.warning(self, "Aviso", "Nome e URL são obrigatórios!")
            return
        
        if not url.startswith(("http://", "https://")):
            url = "https://" + url
        
        self.result_data = {
            "name": name,
            "url": url,
            "folder": self.folder_combo.currentText(),
            "icon": self.icon_input.text().strip()
        }
        
        super().accept()


class AddExtensionDialog(QDialog):
    """Diálogo para adicionar extensão."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.result_data = None
        self.setWindowTitle("Adicionar Extensão")
        self.setMinimumWidth(500)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("🧩 Adicionar Extensão")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #06b6d4;")
        layout.addWidget(title)
        
        info = QLabel(
            "Você pode adicionar extensões de duas formas:\n"
            "1. Selecionar uma pasta de extensão descompactada\n"
            "2. Selecionar um arquivo .crx ou .zip"
        )
        info.setStyleSheet("color: #9ca3af; margin-bottom: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Formulário
        form = QFormLayout()
        
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Nome da extensão")
        form.addRow("Nome:", self.name_input)
        
        self.desc_input = QLineEdit()
        self.desc_input.setPlaceholderText("Descrição opcional")
        form.addRow("Descrição:", self.desc_input)
        
        # Seleção de arquivo/pasta
        source_layout = QHBoxLayout()
        self.source_input = QLineEdit()
        self.source_input.setPlaceholderText("Caminho da extensão")
        self.source_input.setReadOnly(True)
        source_layout.addWidget(self.source_input)
        
        folder_btn = QPushButton("📁 Pasta")
        folder_btn.clicked.connect(self.select_folder)
        source_layout.addWidget(folder_btn)
        
        file_btn = QPushButton("📄 Arquivo")
        file_btn.clicked.connect(self.select_file)
        source_layout.addWidget(file_btn)
        
        form.addRow("Fonte:", source_layout)
        
        self.enabled_check = QCheckBox("Habilitar extensão")
        self.enabled_check.setChecked(True)
        form.addRow("", self.enabled_check)
        
        layout.addLayout(form)
        
        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self, "Selecionar Pasta da Extensão"
        )
        if folder:
            self.source_input.setText(folder)
            self.source_type = "file"
    
    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Selecionar Arquivo de Extensão",
            "", "Extensões (*.crx *.zip)"
        )
        if file_path:
            self.source_input.setText(file_path)
            self.source_type = "crx"
    
    def accept(self):
        name = self.name_input.text().strip()
        source = self.source_input.text().strip()
        
        if not name:
            QMessageBox.warning(self, "Aviso", "Nome é obrigatório!")
            return
        
        if not source:
            QMessageBox.warning(self, "Aviso", "Selecione uma pasta ou arquivo!")
            return
        
        self.result_data = {
            "name": name,
            "source": source,
            "source_type": getattr(self, "source_type", "file"),
            "description": self.desc_input.text().strip(),
            "enabled": self.enabled_check.isChecked()
        }
        
        super().accept()


class AddPasswordDialog(QDialog):
    """Diálogo para adicionar/editar senha."""
    
    def __init__(self, parent=None, password: dict = None, categories: list = None):
        super().__init__(parent)
        self.password = password
        self.categories = categories or ["Geral", "Streaming", "Redes Sociais", "Trabalho", "Compras", "Finanças"]
        self.result_data = None
        self.setWindowTitle("Adicionar Senha" if not password else "Editar Senha")
        self.setMinimumWidth(450)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("🔐 Configurar Senha")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #10b981;")
        layout.addWidget(title)
        
        # Formulário
        form = QFormLayout()
        
        self.site_input = QLineEdit()
        self.site_input.setPlaceholderText("Nome do site (ex: Netflix)")
        if self.password:
            self.site_input.setText(self.password.get("site", ""))
        form.addRow("Site:", self.site_input)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("https://exemplo.com/login")
        if self.password:
            self.url_input.setText(self.password.get("url", ""))
        form.addRow("URL:", self.url_input)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Email ou nome de usuário")
        if self.password:
            self.username_input.setText(self.password.get("username", ""))
        form.addRow("Usuário:", self.username_input)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Senha")
        self.password_input.setEchoMode(QLineEdit.Password)
        if self.password:
            self.password_input.setText(self.password.get("password", ""))
        
        pwd_layout = QHBoxLayout()
        pwd_layout.addWidget(self.password_input)
        
        show_pwd_btn = QPushButton("👁")
        show_pwd_btn.setFixedWidth(40)
        show_pwd_btn.setCheckable(True)
        show_pwd_btn.toggled.connect(self.toggle_password_visibility)
        pwd_layout.addWidget(show_pwd_btn)
        
        form.addRow("Senha:", pwd_layout)
        
        self.category_combo = QComboBox()
        self.category_combo.setEditable(True)
        self.category_combo.addItems(self.categories)
        if self.password:
            category = self.password.get("category", "Geral")
            index = self.category_combo.findText(category)
            if index >= 0:
                self.category_combo.setCurrentIndex(index)
            else:
                self.category_combo.setCurrentText(category)
        form.addRow("Categoria:", self.category_combo)
        
        self.notes_input = QTextEdit()
        self.notes_input.setPlaceholderText("Notas adicionais (opcional)")
        self.notes_input.setMaximumHeight(80)
        if self.password:
            self.notes_input.setText(self.password.get("notes", ""))
        form.addRow("Notas:", self.notes_input)
        
        self.autofill_check = QCheckBox("Preencher automaticamente")
        self.autofill_check.setChecked(self.password.get("auto_fill", True) if self.password else True)
        form.addRow("", self.autofill_check)
        
        layout.addLayout(form)
        
        # Botões
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def toggle_password_visibility(self, checked):
        if checked:
            self.password_input.setEchoMode(QLineEdit.Normal)
        else:
            self.password_input.setEchoMode(QLineEdit.Password)
    
    def accept(self):
        site = self.site_input.text().strip()
        url = self.url_input.text().strip()
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not site and not url:
            QMessageBox.warning(self, "Aviso", "Site ou URL é obrigatório!")
            return
        
        self.result_data = {
            "site": site,
            "url": url,
            "username": username,
            "password": password,
            "category": self.category_combo.currentText(),
            "notes": self.notes_input.toPlainText().strip(),
            "auto_fill": self.autofill_check.isChecked()
        }
        
        super().accept()


class FavoritesWidget(QWidget):
    """Widget para gerenciar favoritos padrão."""
    
    def __init__(self, favorites_manager: FavoritesManager, parent=None):
        super().__init__(parent)
        self.favorites_manager = favorites_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Cabeçalho
        header = QHBoxLayout()
        
        title = QLabel("⭐ Favoritos Padrão")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #fbbf24;")
        header.addWidget(title)
        
        header.addStretch()
        
        add_btn = QPushButton("➕ Adicionar")
        add_btn.clicked.connect(self.add_favorite)
        header.addWidget(add_btn)
        
        import_btn = QPushButton("📥 Importar")
        import_btn.clicked.connect(self.import_favorites)
        header.addWidget(import_btn)
        
        export_btn = QPushButton("📤 Exportar")
        export_btn.clicked.connect(self.export_favorites)
        header.addWidget(export_btn)
        
        layout.addLayout(header)
        
        # Info
        info = QLabel(
            "Estes favoritos serão adicionados automaticamente a todos os novos perfis do navegador."
        )
        info.setStyleSheet("color: #9ca3af; margin-bottom: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Tabela de favoritos
        self.favorites_table = QTableWidget()
        self.favorites_table.setColumnCount(4)
        self.favorites_table.setHorizontalHeaderLabels(["Ícone", "Nome", "URL", "Pasta"])
        self.favorites_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.favorites_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.favorites_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.favorites_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.favorites_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.favorites_table.customContextMenuRequested.connect(self.show_context_menu)
        self.favorites_table.doubleClicked.connect(self.edit_favorite)
        
        layout.addWidget(self.favorites_table)
        
        self.setLayout(layout)
        self.refresh_table()
    
    def refresh_table(self):
        """Atualiza a tabela de favoritos."""
        self.favorites_table.setRowCount(0)
        
        for fav in self.favorites_manager.get_favorites():
            row = self.favorites_table.rowCount()
            self.favorites_table.insertRow(row)
            
            icon_item = QTableWidgetItem(fav.get("icon", "⭐"))
            icon_item.setData(Qt.UserRole, fav.get("id"))
            self.favorites_table.setItem(row, 0, icon_item)
            
            self.favorites_table.setItem(row, 1, QTableWidgetItem(fav.get("name", "")))
            self.favorites_table.setItem(row, 2, QTableWidgetItem(fav.get("url", "")))
            self.favorites_table.setItem(row, 3, QTableWidgetItem(fav.get("folder", "Padrão")))
    
    def add_favorite(self):
        """Adiciona um novo favorito."""
        dialog = AddFavoriteDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.result_data:
            data = dialog.result_data
            self.favorites_manager.add_favorite(
                name=data["name"],
                url=data["url"],
                folder=data["folder"],
                icon=data["icon"]
            )
            self.refresh_table()
    
    def edit_favorite(self):
        """Edita o favorito selecionado."""
        row = self.favorites_table.currentRow()
        if row < 0:
            return
        
        fav_id = self.favorites_table.item(row, 0).data(Qt.UserRole)
        favorites = self.favorites_manager.get_favorites()
        favorite = next((f for f in favorites if f.get("id") == fav_id), None)
        
        if favorite:
            dialog = AddFavoriteDialog(self, favorite)
            if dialog.exec_() == QDialog.Accepted and dialog.result_data:
                data = dialog.result_data
                self.favorites_manager.update_favorite(
                    fav_id,
                    name=data["name"],
                    url=data["url"],
                    folder=data["folder"],
                    icon=data["icon"]
                )
                self.refresh_table()
    
    def delete_favorite(self):
        """Remove o favorito selecionado."""
        row = self.favorites_table.currentRow()
        if row < 0:
            return
        
        fav_id = self.favorites_table.item(row, 0).data(Qt.UserRole)
        name = self.favorites_table.item(row, 1).text()
        
        reply = QMessageBox.question(
            self, "Confirmar",
            f"Deseja remover o favorito '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.favorites_manager.remove_favorite(fav_id)
            self.refresh_table()
    
    def show_context_menu(self, pos):
        """Mostra menu de contexto."""
        menu = QMenu(self)
        
        edit_action = QAction("✏️ Editar", self)
        edit_action.triggered.connect(self.edit_favorite)
        menu.addAction(edit_action)
        
        delete_action = QAction("🗑️ Remover", self)
        delete_action.triggered.connect(self.delete_favorite)
        menu.addAction(delete_action)
        
        menu.exec_(self.favorites_table.mapToGlobal(pos))
    
    def import_favorites(self):
        """Importa favoritos de arquivo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Favoritos",
            "", "JSON (*.json);;HTML (*.html)"
        )
        
        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                favorites_list = data.get("favorites", data) if isinstance(data, dict) else data
                count = self.favorites_manager.import_favorites(favorites_list)
                
                QMessageBox.information(
                    self, "Sucesso",
                    f"{count} favoritos importados com sucesso!"
                )
                self.refresh_table()
            except Exception as e:
                QMessageBox.critical(
                    self, "Erro",
                    f"Erro ao importar favoritos: {str(e)}"
                )
    
    def export_favorites(self):
        """Exporta favoritos para arquivo."""
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Exportar Favoritos",
            "favoritos.json", "JSON (*.json)"
        )
        
        if file_path:
            try:
                favorites = self.favorites_manager.export_favorites()
                data = {
                    "favorites": favorites
                }
                
                with open(file_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                QMessageBox.information(
                    self, "Sucesso",
                    f"Favoritos exportados para:\n{file_path}"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erro",
                    f"Erro ao exportar favoritos: {str(e)}"
                )


class ExtensionsWidget(QWidget):
    """Widget para gerenciar extensões padrão."""
    
    def __init__(self, extensions_manager: ExtensionsManager, parent=None):
        super().__init__(parent)
        self.extensions_manager = extensions_manager
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Cabeçalho
        header = QHBoxLayout()
        
        title = QLabel("🧩 Extensões Padrão")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #06b6d4;")
        header.addWidget(title)
        
        header.addStretch()
        
        add_btn = QPushButton("➕ Adicionar")
        add_btn.clicked.connect(self.add_extension)
        header.addWidget(add_btn)
        
        layout.addLayout(header)
        
        # Info
        info = QLabel(
            "Estas extensões serão carregadas automaticamente em todos os novos perfis do navegador.\n"
            "Você pode adicionar extensões descompactadas (pasta) ou arquivos .crx/.zip"
        )
        info.setStyleSheet("color: #9ca3af; margin-bottom: 10px;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Lista de extensões
        self.extensions_list = QListWidget()
        self.extensions_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.extensions_list.customContextMenuRequested.connect(self.show_context_menu)
        
        layout.addWidget(self.extensions_list)
        
        self.setLayout(layout)
        self.refresh_list()
    
    def refresh_list(self):
        """Atualiza a lista de extensões."""
        self.extensions_list.clear()
        
        for ext in self.extensions_manager.get_extensions():
            status = "✅" if ext.get("enabled", True) else "❌"
            item = QListWidgetItem(f"{status} {ext.get('name', 'Sem Nome')}")
            item.setData(Qt.UserRole, ext.get("id"))
            
            tooltip = f"Descrição: {ext.get('description', 'N/A')}\n"
            tooltip += f"Fonte: {ext.get('source', 'N/A')}\n"
            tooltip += f"Tipo: {ext.get('source_type', 'N/A')}"
            item.setToolTip(tooltip)
            
            self.extensions_list.addItem(item)
    
    def add_extension(self):
        """Adiciona uma nova extensão."""
        dialog = AddExtensionDialog(self)
        if dialog.exec_() == QDialog.Accepted and dialog.result_data:
            data = dialog.result_data
            success, message = self.extensions_manager.add_extension(
                name=data["name"],
                source=data["source"],
                source_type=data["source_type"],
                enabled=data["enabled"],
                description=data["description"]
            )
            
            if success:
                QMessageBox.information(self, "Sucesso", message)
                self.refresh_list()
            else:
                QMessageBox.critical(self, "Erro", message)
    
    def toggle_extension(self):
        """Alterna o estado da extensão selecionada."""
        item = self.extensions_list.currentItem()
        if item:
            ext_id = item.data(Qt.UserRole)
            self.extensions_manager.toggle_extension(ext_id)
            self.refresh_list()
    
    def delete_extension(self):
        """Remove a extensão selecionada."""
        item = self.extensions_list.currentItem()
        if not item:
            return
        
        ext_id = item.data(Qt.UserRole)
        name = item.text().split(" ", 1)[1] if " " in item.text() else item.text()
        
        reply = QMessageBox.question(
            self, "Confirmar",
            f"Deseja remover a extensão '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.extensions_manager.remove_extension(ext_id)
            self.refresh_list()
    
    def show_context_menu(self, pos):
        """Mostra menu de contexto."""
        menu = QMenu(self)
        
        toggle_action = QAction("🔄 Habilitar/Desabilitar", self)
        toggle_action.triggered.connect(self.toggle_extension)
        menu.addAction(toggle_action)
        
        delete_action = QAction("🗑️ Remover", self)
        delete_action.triggered.connect(self.delete_extension)
        menu.addAction(delete_action)
        
        menu.exec_(self.extensions_list.mapToGlobal(pos))


class MasterPasswordDialog(QDialog):
    """Diálogo para criar ou desbloquear com senha mestra."""
    
    def __init__(self, parent=None, is_new: bool = True):
        super().__init__(parent)
        self.is_new = is_new
        self.password = None
        self.setWindowTitle("Criar Senha Mestra" if is_new else "Desbloquear Senhas")
        self.setMinimumWidth(400)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Ícone e título
        if self.is_new:
            title = QLabel("🔐 Criar Senha Mestra")
            info = QLabel(
                "Crie uma senha mestra para proteger suas senhas salvas.\n"
                "Esta senha será necessária para acessar suas senhas.\n\n"
                "⚠️ IMPORTANTE: Se você esquecer esta senha, não será possível\n"
                "recuperar suas senhas salvas!"
            )
        else:
            title = QLabel("🔓 Desbloquear Gerenciador")
            info = QLabel(
                "Digite sua senha mestra para acessar suas senhas.\n"
                "Suas senhas estão criptografadas para sua segurança."
            )
        
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #10b981;")
        layout.addWidget(title)
        
        info.setStyleSheet("color: #9ca3af; margin: 10px 0;")
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # Campo de senha
        form = QFormLayout()
        
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Digite sua senha mestra...")
        form.addRow("Senha:", self.password_input)
        
        if self.is_new:
            self.confirm_input = QLineEdit()
            self.confirm_input.setEchoMode(QLineEdit.Password)
            self.confirm_input.setPlaceholderText("Confirme a senha...")
            form.addRow("Confirmar:", self.confirm_input)
        
        layout.addLayout(form)
        
        # Requisitos de senha (apenas para nova senha)
        if self.is_new:
            req_label = QLabel(
                "\nℹ️ Requisitos:\n"
                "• Mínimo de 8 caracteres\n"
                "• Recomendado: letras, números e símbolos"
            )
            req_label.setStyleSheet("color: #6b7280; font-size: 11px;")
            layout.addWidget(req_label)
        
        # Botões
        buttons = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
        
        self.setLayout(layout)
    
    def validate_and_accept(self):
        password = self.password_input.text()
        
        if len(password) < 8:
            QMessageBox.warning(
                self, "Senha Inválida",
                "A senha deve ter pelo menos 8 caracteres."
            )
            return
        
        if self.is_new:
            confirm = self.confirm_input.text()
            if password != confirm:
                QMessageBox.warning(
                    self, "Senhas Não Coincidem",
                    "As senhas digitadas não são iguais."
                )
                return
        
        self.password = password
        self.accept()


class PasswordsWidget(QWidget):
    """Widget para gerenciar senhas com suporte a senha mestra."""
    
    def __init__(self, password_manager: PasswordManager, parent=None):
        super().__init__(parent)
        self.password_manager = password_manager
        self.is_locked = True
        self.init_ui()
        self.check_lock_status()
    
    def check_lock_status(self):
        """Verifica se precisa desbloquear ou criar senha mestra."""
        if self.password_manager.is_master_password_set():
            if not self.password_manager.is_unlocked():
                self.show_locked_ui()
            else:
                self.is_locked = False
                self.show_unlocked_ui()
        else:
            # Primeira vez - perguntar se quer criar senha mestra
            self.show_setup_ui()
    
    def show_setup_ui(self):
        """Mostra interface para configurar senha mestra."""
        self.is_locked = True
        self.lock_widget.show()
        self.main_widget.hide()
        
        self.lock_title.setText("🔐 Configurar Proteção")
        self.lock_info.setText(
            "Suas senhas podem ser protegidas com uma senha mestra.\n"
            "Isso adiciona uma camada extra de segurança.\n\n"
            "Deseja configurar uma senha mestra agora?"
        )
        self.unlock_btn.setText("🔒 Criar Senha Mestra")
        self.unlock_btn.clicked.disconnect()
        self.unlock_btn.clicked.connect(self.create_master_password)
        
        # Botão para pular
        self.skip_btn.show()
    
    def show_locked_ui(self):
        """Mostra interface bloqueada."""
        self.is_locked = True
        self.lock_widget.show()
        self.main_widget.hide()
        
        self.lock_title.setText("🔒 Gerenciador Bloqueado")
        self.lock_info.setText(
            "Suas senhas estão protegidas com criptografia.\n"
            "Digite sua senha mestra para desbloquear."
        )
        self.unlock_btn.setText("🔓 Desbloquear")
        try:
            self.unlock_btn.clicked.disconnect()
        except TypeError:
            pass  # Nenhum slot conectado ainda
        self.unlock_btn.clicked.connect(self.unlock_passwords)
        self.skip_btn.hide()
    
    def show_unlocked_ui(self):
        """Mostra interface desbloqueada."""
        self.is_locked = False
        self.lock_widget.hide()
        self.main_widget.show()
        self.refresh_table()
        self.update_category_filter()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Widget de bloqueio
        self.lock_widget = QWidget()
        lock_layout = QVBoxLayout()
        lock_layout.setAlignment(Qt.AlignCenter)
        
        self.lock_title = QLabel("🔒 Gerenciador Bloqueado")
        self.lock_title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f59e0b;")
        self.lock_title.setAlignment(Qt.AlignCenter)
        lock_layout.addWidget(self.lock_title)
        
        self.lock_info = QLabel("Digite sua senha mestra para acessar suas senhas.")
        self.lock_info.setStyleSheet("color: #9ca3af; margin: 20px 0; font-size: 14px;")
        self.lock_info.setAlignment(Qt.AlignCenter)
        self.lock_info.setWordWrap(True)
        lock_layout.addWidget(self.lock_info)
        
        self.unlock_btn = QPushButton("🔓 Desbloquear")
        self.unlock_btn.setStyleSheet(
            "QPushButton { background-color: #10b981; color: white; padding: 15px 40px; "
            "font-size: 16px; border-radius: 8px; } "
            "QPushButton:hover { background-color: #059669; }"
        )
        self.unlock_btn.clicked.connect(self.unlock_passwords)
        lock_layout.addWidget(self.unlock_btn, alignment=Qt.AlignCenter)
        
        self.skip_btn = QPushButton("Pular por agora")
        self.skip_btn.setStyleSheet("color: #6b7280; border: none; margin-top: 10px;")
        self.skip_btn.clicked.connect(self.skip_master_password)
        self.skip_btn.hide()
        lock_layout.addWidget(self.skip_btn, alignment=Qt.AlignCenter)
        
        self.lock_widget.setLayout(lock_layout)
        layout.addWidget(self.lock_widget)
        
        # Widget principal (desbloqueado)
        self.main_widget = QWidget()
        main_layout = QVBoxLayout()
        
        # Cabeçalho
        header = QHBoxLayout()
        
        title = QLabel("🔐 Gerenciador de Senhas")
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #10b981;")
        header.addWidget(title)
        
        # Status de proteção
        self.protection_label = QLabel("🔒 Protegido")
        self.protection_label.setStyleSheet("color: #10b981; font-size: 12px;")
        header.addWidget(self.protection_label)
        
        header.addStretch()
        
        # Botão de configurações de segurança
        security_btn = QPushButton("⚙️")
        security_btn.setToolTip("Configurações de Segurança")
        security_btn.setFixedWidth(40)
        security_btn.clicked.connect(self.show_security_menu)
        header.addWidget(security_btn)
        
        add_btn = QPushButton("➕ Adicionar")
        add_btn.clicked.connect(self.add_password)
        header.addWidget(add_btn)
        
        import_btn = QPushButton("📥 Importar")
        import_btn.clicked.connect(self.import_passwords)
        header.addWidget(import_btn)
        
        export_btn = QPushButton("📤 Exportar")
        export_btn.clicked.connect(self.export_passwords)
        header.addWidget(export_btn)
        
        main_layout.addLayout(header)
        
        # Info
        info = QLabel(
            "Suas senhas são salvas de forma segura e podem ser exportadas para uso em outros navegadores.\n"
            "Formato de exportação compatível com Chrome, Firefox e outros gerenciadores."
        )
        info.setStyleSheet("color: #9ca3af; margin-bottom: 10px;")
        info.setWordWrap(True)
        main_layout.addWidget(info)
        
        # Barra de pesquisa
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Pesquisar senhas...")
        self.search_input.textChanged.connect(self.search_passwords)
        search_layout.addWidget(self.search_input)
        
        self.category_filter = QComboBox()
        self.category_filter.addItem("Todas as categorias", None)
        self.category_filter.currentIndexChanged.connect(self.filter_by_category)
        search_layout.addWidget(self.category_filter)
        
        main_layout.addLayout(search_layout)
        
        # Tabela de senhas
        self.passwords_table = QTableWidget()
        self.passwords_table.setColumnCount(5)
        self.passwords_table.setHorizontalHeaderLabels(["Site", "URL", "Usuário", "Categoria", "Auto"])
        self.passwords_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.passwords_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.passwords_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.passwords_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.passwords_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.passwords_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.passwords_table.customContextMenuRequested.connect(self.show_context_menu)
        self.passwords_table.doubleClicked.connect(self.edit_password)
        
        main_layout.addWidget(self.passwords_table)
        
        self.main_widget.setLayout(main_layout)
        layout.addWidget(self.main_widget)
        
        self.setLayout(layout)
    
    def create_master_password(self):
        """Cria uma nova senha mestra."""
        dialog = MasterPasswordDialog(self, is_new=True)
        if dialog.exec_() == QDialog.Accepted and dialog.password:
            success, message = self.password_manager.create_master_password(dialog.password)
            if success:
                QMessageBox.information(self, "Sucesso", message)
                self.show_unlocked_ui()
            else:
                QMessageBox.warning(self, "Erro", message)
    
    def unlock_passwords(self):
        """Desbloqueia o gerenciador com a senha mestra."""
        dialog = MasterPasswordDialog(self, is_new=False)
        if dialog.exec_() == QDialog.Accepted and dialog.password:
            success, message = self.password_manager.unlock(dialog.password)
            if success:
                self.show_unlocked_ui()
            else:
                QMessageBox.warning(self, "Erro", message)
    
    def skip_master_password(self):
        """Pula a configuração de senha mestra."""
        reply = QMessageBox.question(
            self, "Pular Proteção",
            "Suas senhas ficarão salvas sem criptografia.\n"
            "Você pode configurar uma senha mestra depois.\n\n"
            "Deseja continuar sem proteção?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.is_locked = False
            self.protection_label.setText("⚠️ Sem Proteção")
            self.protection_label.setStyleSheet("color: #f59e0b; font-size: 12px;")
            self.show_unlocked_ui()
    
    def show_security_menu(self):
        """Mostra menu de configurações de segurança."""
        menu = QMenu(self)
        
        if self.password_manager.is_master_password_set():
            change_action = QAction("🔑 Alterar Senha Mestra", self)
            change_action.triggered.connect(self.change_master_password)
            menu.addAction(change_action)
            
            lock_action = QAction("🔒 Bloquear Agora", self)
            lock_action.triggered.connect(self.lock_passwords)
            menu.addAction(lock_action)
        else:
            create_action = QAction("🔐 Criar Senha Mestra", self)
            create_action.triggered.connect(self.create_master_password)
            menu.addAction(create_action)
        
        menu.exec_(self.sender().mapToGlobal(self.sender().rect().bottomLeft()))
    
    def change_master_password(self):
        """Altera a senha mestra."""
        # Primeiro pedir senha atual
        old_dialog = MasterPasswordDialog(self, is_new=False)
        old_dialog.setWindowTitle("Senha Atual")
        if old_dialog.exec_() != QDialog.Accepted:
            return
        
        # Depois pedir nova senha
        new_dialog = MasterPasswordDialog(self, is_new=True)
        new_dialog.setWindowTitle("Nova Senha Mestra")
        if new_dialog.exec_() == QDialog.Accepted and new_dialog.password:
            success, message = self.password_manager.change_master_password(
                old_dialog.password, new_dialog.password
            )
            if success:
                QMessageBox.information(self, "Sucesso", message)
            else:
                QMessageBox.warning(self, "Erro", message)
    
    def lock_passwords(self):
        """Bloqueia o gerenciador."""
        self.password_manager._cipher = None
        self.password_manager.passwords = []
        self.show_locked_ui()
    
    def refresh_table(self, passwords: list = None):
        """Atualiza a tabela de senhas."""
        self.passwords_table.setRowCount(0)
        
        if passwords is None:
            passwords = self.password_manager.get_passwords()
        
        for pwd in passwords:
            row = self.passwords_table.rowCount()
            self.passwords_table.insertRow(row)
            
            site_item = QTableWidgetItem(pwd.get("site", ""))
            site_item.setData(Qt.UserRole, pwd.get("id"))
            self.passwords_table.setItem(row, 0, site_item)
            
            self.passwords_table.setItem(row, 1, QTableWidgetItem(pwd.get("url", "")))
            self.passwords_table.setItem(row, 2, QTableWidgetItem(pwd.get("username", "")))
            self.passwords_table.setItem(row, 3, QTableWidgetItem(pwd.get("category", "Geral")))
            
            auto_item = QTableWidgetItem("✅" if pwd.get("auto_fill", True) else "❌")
            auto_item.setTextAlignment(Qt.AlignCenter)
            self.passwords_table.setItem(row, 4, auto_item)
    
    def update_category_filter(self):
        """Atualiza o filtro de categorias."""
        current = self.category_filter.currentData()
        self.category_filter.clear()
        self.category_filter.addItem("Todas as categorias", None)
        
        for category in self.password_manager.get_categories():
            self.category_filter.addItem(category, category)
        
        if current:
            index = self.category_filter.findData(current)
            if index >= 0:
                self.category_filter.setCurrentIndex(index)
    
    def add_password(self):
        """Adiciona uma nova senha."""
        categories = self.password_manager.get_categories()
        dialog = AddPasswordDialog(self, categories=categories)
        if dialog.exec_() == QDialog.Accepted and dialog.result_data:
            data = dialog.result_data
            self.password_manager.add_password(
                site=data["site"],
                url=data["url"],
                username=data["username"],
                password=data["password"],
                notes=data["notes"],
                category=data["category"],
                auto_fill=data["auto_fill"]
            )
            self.refresh_table()
            self.update_category_filter()
    
    def edit_password(self):
        """Edita a senha selecionada."""
        row = self.passwords_table.currentRow()
        if row < 0:
            return
        
        pwd_id = self.passwords_table.item(row, 0).data(Qt.UserRole)
        passwords = self.password_manager.get_passwords()
        password = next((p for p in passwords if p.get("id") == pwd_id), None)
        
        if password:
            categories = self.password_manager.get_categories()
            dialog = AddPasswordDialog(self, password, categories)
            if dialog.exec_() == QDialog.Accepted and dialog.result_data:
                data = dialog.result_data
                self.password_manager.update_password(
                    pwd_id,
                    site=data["site"],
                    url=data["url"],
                    username=data["username"],
                    password=data["password"],
                    notes=data["notes"],
                    category=data["category"],
                    auto_fill=data["auto_fill"]
                )
                self.refresh_table()
                self.update_category_filter()
    
    def delete_password(self):
        """Remove a senha selecionada."""
        row = self.passwords_table.currentRow()
        if row < 0:
            return
        
        pwd_id = self.passwords_table.item(row, 0).data(Qt.UserRole)
        site = self.passwords_table.item(row, 0).text()
        
        reply = QMessageBox.question(
            self, "Confirmar",
            f"Deseja remover a senha de '{site}'?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.password_manager.remove_password(pwd_id)
            self.refresh_table()
            self.update_category_filter()
    
    def copy_password(self):
        """Copia a senha para a área de transferência."""
        row = self.passwords_table.currentRow()
        if row < 0:
            return
        
        pwd_id = self.passwords_table.item(row, 0).data(Qt.UserRole)
        passwords = self.password_manager.get_passwords()
        password = next((p for p in passwords if p.get("id") == pwd_id), None)
        
        if password:
            from PyQt5.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(password.get("password", ""))
            
            QMessageBox.information(
                self, "Copiado",
                "Senha copiada para a área de transferência!"
            )
    
    def search_passwords(self, query: str):
        """Pesquisa senhas."""
        if query:
            results = self.password_manager.search_passwords(query)
            self.refresh_table(results)
        else:
            self.refresh_table()
    
    def filter_by_category(self, index):
        """Filtra senhas por categoria."""
        category = self.category_filter.currentData()
        if category:
            passwords = self.password_manager.get_passwords(category)
            self.refresh_table(passwords)
        else:
            self.refresh_table()
    
    def show_context_menu(self, pos):
        """Mostra menu de contexto."""
        menu = QMenu(self)
        
        edit_action = QAction("✏️ Editar", self)
        edit_action.triggered.connect(self.edit_password)
        menu.addAction(edit_action)
        
        copy_action = QAction("📋 Copiar Senha", self)
        copy_action.triggered.connect(self.copy_password)
        menu.addAction(copy_action)
        
        menu.addSeparator()
        
        delete_action = QAction("🗑️ Remover", self)
        delete_action.triggered.connect(self.delete_password)
        menu.addAction(delete_action)
        
        menu.exec_(self.passwords_table.mapToGlobal(pos))
    
    def import_passwords(self):
        """Importa senhas de arquivo."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Importar Senhas",
            "", "CSV (*.csv);;JSON (*.json)"
        )
        
        if file_path:
            try:
                if file_path.endswith(".csv"):
                    count = self.password_manager.import_from_csv(file_path)
                else:
                    count = self.password_manager.import_from_json(file_path)
                
                QMessageBox.information(
                    self, "Sucesso",
                    f"{count} senhas importadas com sucesso!"
                )
                self.refresh_table()
                self.update_category_filter()
            except Exception as e:
                QMessageBox.critical(
                    self, "Erro",
                    f"Erro ao importar senhas: {str(e)}"
                )
    
    def export_passwords(self):
        """Exporta senhas para arquivo."""
        # Perguntar se deve incluir senhas
        reply = QMessageBox.question(
            self, "Exportar Senhas",
            "Deseja incluir as senhas no arquivo exportado?\n\n"
            "⚠️ ATENÇÃO: Isso criará um arquivo com todas as suas senhas em texto!\n"
            "Guarde este arquivo em local seguro.",
            QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
        )
        
        if reply == QMessageBox.Cancel:
            return
        
        include_passwords = reply == QMessageBox.Yes
        
        file_path, selected_filter = QFileDialog.getSaveFileName(
            self, "Exportar Senhas",
            "senhas.csv", "CSV (*.csv);;JSON (*.json)"
        )
        
        if file_path:
            try:
                if file_path.endswith(".csv") or "CSV" in selected_filter:
                    success = self.password_manager.export_to_csv(file_path, include_passwords)
                else:
                    success = self.password_manager.export_to_json(file_path, include_passwords)
                
                if success:
                    QMessageBox.information(
                        self, "Sucesso",
                        f"Senhas exportadas para:\n{file_path}"
                    )
                else:
                    QMessageBox.critical(
                        self, "Erro",
                        "Erro ao exportar senhas!"
                    )
            except Exception as e:
                QMessageBox.critical(
                    self, "Erro",
                    f"Erro ao exportar senhas: {str(e)}"
                )


class ProfileDefaultsWidget(QWidget):
    """
    Widget principal para gerenciamento de configurações padrão de perfis.
    Combina favoritos, extensões e senhas em uma interface com abas.
    """
    
    def __init__(self, config_dir: str = None, parent=None):
        super().__init__(parent)
        
        self.defaults_manager = ProfileDefaultsManager(config_dir)
        self.init_ui()
    
    def init_ui(self):
        layout = QVBoxLayout()
        
        # Título principal
        title = QLabel("⚙️ Configurações Padrão de Perfis")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(title)
        
        subtitle = QLabel(
            "Configure favoritos, extensões e senhas que serão aplicados automaticamente a todos os novos perfis."
        )
        subtitle.setStyleSheet("color: #9ca3af; margin-bottom: 15px;")
        subtitle.setWordWrap(True)
        layout.addWidget(subtitle)
        
        # Abas
        tabs = QTabWidget()
        
        # Aba de Favoritos
        favorites_widget = FavoritesWidget(self.defaults_manager.favorites)
        tabs.addTab(favorites_widget, "⭐ Favoritos")
        
        # Aba de Extensões
        extensions_widget = ExtensionsWidget(self.defaults_manager.extensions)
        tabs.addTab(extensions_widget, "🧩 Extensões")
        
        # Aba de Senhas
        passwords_widget = PasswordsWidget(self.defaults_manager.passwords)
        tabs.addTab(passwords_widget, "🔐 Senhas")
        
        layout.addWidget(tabs)
        
        self.setLayout(layout)
    
    def get_defaults_manager(self) -> ProfileDefaultsManager:
        """Retorna o gerenciador de configurações padrão."""
        return self.defaults_manager
