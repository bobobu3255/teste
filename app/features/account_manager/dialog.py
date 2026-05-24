#!/usr/bin/env python3
"""
Gerenciador de Contas e Grupos
Interface para adicionar múltiplas contas e grupos do Telegram
"""
import sys
import os
import shutil
from PyQt5.QtWidgets import (QApplication, QDialog, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QLineEdit, QSpinBox, QListWidget,
                             QListWidgetItem, QMessageBox, QTabWidget, QWidget,
                             QFileDialog, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from config_manager import ConfigManager

class GerenciadorContas(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.init_ui()
        self.carregar_dados()
    
    def init_ui(self):
        """Inicializa a interface"""
        self.setWindowTitle("Gerenciador de Contas e Grupos")
        self.setGeometry(100, 100, 700, 500)
        
        layout = QVBoxLayout()
        
        # Abas
        tabs = QTabWidget()
        
        # Aba 1: Contas
        tab_contas = self.criar_aba_contas()
        tabs.addTab(tab_contas, "📱 Contas")
        
        # Aba 2: Grupos
        tab_grupos = self.criar_aba_grupos()
        tabs.addTab(tab_grupos, "👥 Grupos")
        
        layout.addWidget(tabs)
        
        # Botão fechar
        btn_fechar = QPushButton("Fechar")
        btn_fechar.clicked.connect(self.accept)
        layout.addWidget(btn_fechar)
        
        self.setLayout(layout)
    
    def criar_aba_contas(self):
        """Cria a aba de contas"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("Gerenciar Contas do Telegram")
        titulo_font = QFont()
        titulo_font.setPointSize(12)
        titulo_font.setBold(True)
        titulo.setFont(titulo_font)
        layout.addWidget(titulo)
        
        # Formulário para adicionar conta
        form_layout = QVBoxLayout()
        
        form_layout.addWidget(QLabel("Telefone:"))
        self.telefone_input = QLineEdit()
        self.telefone_input.setPlaceholderText("+5579991427786")
        form_layout.addWidget(self.telefone_input)
        
        form_layout.addWidget(QLabel("API ID:"))
        self.api_id_input = QSpinBox()
        self.api_id_input.setMaximum(999999999)
        form_layout.addWidget(self.api_id_input)
        
        form_layout.addWidget(QLabel("API Hash:"))
        self.api_hash_input = QLineEdit()
        self.api_hash_input.setPlaceholderText("Copie do my.telegram.org")
        form_layout.addWidget(self.api_hash_input)
        
        form_layout.addWidget(QLabel("Nome da Conta:"))
        self.nome_conta_input = QLineEdit()
        self.nome_conta_input.setPlaceholderText("Ex: Minha Conta")
        form_layout.addWidget(self.nome_conta_input)
        
        btn_adicionar = QPushButton("➕ Adicionar Conta")
        btn_adicionar.clicked.connect(self.adicionar_conta)
        form_layout.addWidget(btn_adicionar)
        
        layout.addLayout(form_layout)
        
        layout.addWidget(QLabel("Contas Cadastradas:"))
        
        # Lista de contas
        self.lista_contas = QListWidget()
        layout.addWidget(self.lista_contas)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        btn_ativar = QPushButton("✓ Ativar")
        btn_ativar.clicked.connect(self.ativar_conta)
        btn_layout.addWidget(btn_ativar)
        
        btn_deletar = QPushButton("🗑️ Deletar")
        btn_deletar.clicked.connect(self.deletar_conta)
        btn_layout.addWidget(btn_deletar)
        
        layout.addLayout(btn_layout)
        
        # Grupo de Gerenciamento de Sessão
        session_group = QGroupBox("📁 Gerenciar Sessão")
        session_layout = QHBoxLayout()
        
        btn_importar = QPushButton("📥 Importar Sessão")
        btn_importar.clicked.connect(self.importar_sessao)
        btn_importar.setToolTip("Importar arquivo .session existente")
        session_layout.addWidget(btn_importar)
        
        btn_exportar = QPushButton("📤 Exportar Sessão")
        btn_exportar.clicked.connect(self.exportar_sessao)
        btn_exportar.setToolTip("Fazer backup da sessão atual")
        session_layout.addWidget(btn_exportar)
        
        btn_verificar = QPushButton("🔍 Verificar")
        btn_verificar.clicked.connect(self.verificar_sessao)
        btn_verificar.setToolTip("Verificar se a conta tem sessão válida")
        session_layout.addWidget(btn_verificar)
        
        session_group.setLayout(session_layout)
        layout.addWidget(session_group)
        
        widget.setLayout(layout)
        return widget
    
    def criar_aba_grupos(self):
        """Cria a aba de grupos"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Título
        titulo = QLabel("Gerenciar Grupos para Coleta")
        titulo_font = QFont()
        titulo_font.setPointSize(12)
        titulo_font.setBold(True)
        titulo.setFont(titulo_font)
        layout.addWidget(titulo)
        
        # Formulário para adicionar grupo
        form_layout = QVBoxLayout()
        
        form_layout.addWidget(QLabel("Nome do Grupo:"))
        self.nome_grupo_input = QLineEdit()
        self.nome_grupo_input.setPlaceholderText("Ex: Puxadas Train")
        form_layout.addWidget(self.nome_grupo_input)
        
        form_layout.addWidget(QLabel("Username do Grupo:"))
        self.username_grupo_input = QLineEdit()
        self.username_grupo_input.setPlaceholderText("Ex: PuxadasTr4in")
        form_layout.addWidget(self.username_grupo_input)
        
        form_layout.addWidget(QLabel("Conta a Usar:"))
        self.combo_contas = QListWidget()
        form_layout.addWidget(self.combo_contas)
        
        btn_adicionar_grupo = QPushButton("➕ Adicionar Grupo")
        btn_adicionar_grupo.clicked.connect(self.adicionar_grupo)
        form_layout.addWidget(btn_adicionar_grupo)
        
        layout.addLayout(form_layout)
        
        layout.addWidget(QLabel("Grupos Cadastrados:"))
        
        # Lista de grupos
        self.lista_grupos = QListWidget()
        layout.addWidget(self.lista_grupos)
        
        # Botão deletar grupo
        btn_deletar_grupo = QPushButton("🗑️ Deletar Grupo")
        btn_deletar_grupo.clicked.connect(self.deletar_grupo)
        layout.addWidget(btn_deletar_grupo)
        
        widget.setLayout(layout)
        return widget
    
    def carregar_dados(self):
        """Carrega dados das contas e grupos"""
        self.atualizar_lista_contas()
        self.atualizar_lista_grupos()
    
    def atualizar_lista_contas(self):
        """Atualiza a lista de contas"""
        self.lista_contas.clear()
        self.combo_contas.clear()
        
        contas = self.config.listar_contas()
        conta_ativa = self.config.get_conta_ativa()
        
        for conta in contas:
            ativo = "✓" if conta_ativa and conta['id'] == conta_ativa['id'] else " "
            texto = f"[{ativo}] {conta['nome']} - {conta['telefone']}"
            
            item = QListWidgetItem(texto)
            item.setData(Qt.UserRole, conta['id'])
            self.lista_contas.addItem(item)
            
            # Adicionar também ao combo de contas
            item_combo = QListWidgetItem(conta['nome'])
            item_combo.setData(Qt.UserRole, conta['id'])
            self.combo_contas.addItem(item_combo)
        
        # Selecionar automaticamente a primeira conta se houver
        if self.lista_contas.count() > 0:
            self.lista_contas.setCurrentRow(0)
            self.combo_contas.setCurrentRow(0)
    
    def atualizar_lista_grupos(self):
        """Atualiza a lista de grupos"""
        self.lista_grupos.clear()
        
        grupos = self.config.listar_grupos()
        
        for grupo in grupos:
            # Encontrar nome da conta
            conta = None
            for c in self.config.listar_contas():
                if c['id'] == grupo['conta_id']:
                    conta = c
                    break
            
            conta_nome = conta['nome'] if conta else "Desconhecida"
            texto = f"{grupo['nome']} (@{grupo['username']}) - {conta_nome}"
            
            item = QListWidgetItem(texto)
            item.setData(Qt.UserRole, grupo['id'])
            self.lista_grupos.addItem(item)
    
    def adicionar_conta(self):
        """Adiciona uma nova conta"""
        telefone = self.telefone_input.text().strip()
        api_id = self.api_id_input.value()
        api_hash = self.api_hash_input.text().strip()
        nome = self.nome_conta_input.text().strip()
        
        if not telefone or not api_id or not api_hash:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return
        
        if self.config.adicionar_conta(telefone, api_id, api_hash, nome):
            QMessageBox.information(self, "Sucesso", "Conta adicionada!")
            self.telefone_input.clear()
            self.api_id_input.setValue(0)
            self.api_hash_input.clear()
            self.nome_conta_input.clear()
            self.atualizar_lista_contas()
        else:
            QMessageBox.warning(self, "Erro", "Conta já existe!")
    
    def ativar_conta(self):
        """Ativa uma conta"""
        item = self.lista_contas.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta!")
            return
        
        conta_id = item.data(Qt.UserRole)
        if self.config.set_conta_ativa(conta_id):
            QMessageBox.information(self, "Sucesso", "Conta ativada!")
            self.atualizar_lista_contas()
        else:
            QMessageBox.error(self, "Erro", "Erro ao ativar conta!")
    
    def deletar_conta(self):
        """Deleta uma conta"""
        item = self.lista_contas.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta!")
            return
        
        reply = QMessageBox.question(self, "Confirmação", 
                                     "Tem certeza que deseja deletar esta conta?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            conta_id = item.data(Qt.UserRole)
            if self.config.deletar_conta(conta_id):
                QMessageBox.information(self, "Sucesso", "Conta deletada!")
                self.atualizar_lista_contas()
                self.atualizar_lista_grupos()
            else:
                QMessageBox.error(self, "Erro", "Erro ao deletar conta!")
    
    def adicionar_grupo(self):
        """Adiciona um novo grupo"""
        nome_grupo = self.nome_grupo_input.text().strip()
        username = self.username_grupo_input.text().strip()
        
        item_conta = self.combo_contas.currentItem()
        if not item_conta:
            QMessageBox.warning(self, "Erro", "Selecione uma conta!")
            return
        
        if not nome_grupo or not username:
            QMessageBox.warning(self, "Erro", "Preencha todos os campos!")
            return
        
        conta_id = item_conta.data(Qt.UserRole)
        
        if self.config.adicionar_grupo(nome_grupo, username, conta_id):
            QMessageBox.information(self, "Sucesso", "Grupo adicionado!")
            self.nome_grupo_input.clear()
            self.username_grupo_input.clear()
            self.atualizar_lista_grupos()
        else:
            QMessageBox.warning(self, "Erro", "Grupo já existe!")
    
    def deletar_grupo(self):
        """Deleta um grupo"""
        item = self.lista_grupos.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione um grupo!")
            return
        
        reply = QMessageBox.question(self, "Confirmação", 
                                     "Tem certeza que deseja deletar este grupo?",
                                     QMessageBox.Yes | QMessageBox.No)
        
        if reply == QMessageBox.Yes:
            grupo_id = item.data(Qt.UserRole)
            if self.config.deletar_grupo(grupo_id):
                QMessageBox.information(self, "Sucesso", "Grupo deletado!")
                self.atualizar_lista_grupos()
            else:
                QMessageBox.error(self, "Erro", "Erro ao deletar grupo!")


    def importar_sessao(self):
        """Importa um arquivo de sessão existente"""
        item = self.lista_contas.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta primeiro!")
            return
        
        conta_id = item.data(Qt.UserRole)
        
        # Abrir diálogo para selecionar arquivo
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Selecionar Arquivo de Sessão",
            "",
            "Arquivos de Sessão (*.session);;Todos os arquivos (*.*)"
        )
        
        if not file_path:
            return
        
        try:
            # Obter diretório da conta
            conta_dir = self.config.get_diretorio_conta(conta_id)
            destino = os.path.join(conta_dir, 'session.session')
            
            # Copiar arquivo
            shutil.copy2(file_path, destino)
            
            QMessageBox.information(
                self, "Sucesso", 
                f"Sessão importada com sucesso!\n\nArquivo salvo em:\n{destino}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao importar sessão:\n{e}")
    
    def exportar_sessao(self):
        """Exporta o arquivo de sessão da conta selecionada"""
        item = self.lista_contas.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta primeiro!")
            return
        
        conta_id = item.data(Qt.UserRole)
        conta_dir = self.config.get_diretorio_conta(conta_id)
        
        # Verificar se existe sessão
        session_file = os.path.join(conta_dir, 'session.session')
        if not os.path.exists(session_file):
            QMessageBox.warning(
                self, "Aviso", 
                "Esta conta não possui arquivo de sessão.\n"
                "Faça uma coleta primeiro para criar a sessão."
            )
            return
        
        # Abrir diálogo para salvar
        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Salvar Arquivo de Sessão",
            f"conta_{conta_id}_backup.session",
            "Arquivos de Sessão (*.session)"
        )
        
        if not save_path:
            return
        
        try:
            shutil.copy2(session_file, save_path)
            QMessageBox.information(
                self, "Sucesso", 
                f"Sessão exportada com sucesso!\n\nSalvo em:\n{save_path}"
            )
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao exportar sessão:\n{e}")
    
    def verificar_sessao(self):
        """Verifica se a conta selecionada tem sessão válida"""
        item = self.lista_contas.currentItem()
        if not item:
            QMessageBox.warning(self, "Aviso", "Selecione uma conta primeiro!")
            return
        
        conta_id = item.data(Qt.UserRole)
        conta_dir = self.config.get_diretorio_conta(conta_id)
        session_file = os.path.join(conta_dir, 'session.session')
        
        if os.path.exists(session_file):
            size = os.path.getsize(session_file)
            modified = os.path.getmtime(session_file)
            from datetime import datetime
            mod_date = datetime.fromtimestamp(modified).strftime('%d/%m/%Y %H:%M')
            
            QMessageBox.information(
                self, "Sessão Encontrada",
                f"✅ Sessão válida encontrada!\n\n"
                f"📁 Arquivo: {session_file}\n"
                f"📊 Tamanho: {size} bytes\n"
                f"📅 Modificado: {mod_date}"
            )
        else:
            QMessageBox.warning(
                self, "Sem Sessão",
                "❌ Esta conta não possui sessão.\n\n"
                "Você pode:\n"
                "• Importar uma sessão existente\n"
                "• Fazer uma coleta para criar nova sessão"
            )


def main():
    app = QApplication(sys.argv)
    window = GerenciadorContas()
    window.exec_()

if __name__ == '__main__':
    main()
