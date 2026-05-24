#!/usr/bin/env python3
"""
Componentes UI Reutilizáveis
Versão 1.0 - Widgets customizados para melhor UX e feedback visual
"""
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QProgressBar, QLabel, 
    QTextEdit, QGroupBox, QPushButton, QFrame, QScrollArea
)
from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QColor, QTextCursor
from datetime import datetime
from typing import Optional, Callable


class ProgressPanel(QGroupBox):
    """Painel de progresso com barra e informações"""
    
    def __init__(self, title: str = "Progresso"):
        super().__init__(title)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa componentes"""
        layout = QVBoxLayout()
        
        # Barra de progresso
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Informações
        info_layout = QHBoxLayout()
        
        self.status_label = QLabel("Aguardando...")
        self.status_label.setStyleSheet("color: #0a84ff; font-weight: 500;")
        info_layout.addWidget(self.status_label)
        
        info_layout.addStretch()
        
        self.time_label = QLabel("00:00")
        self.time_label.setStyleSheet("color: #8e8e93;")
        info_layout.addWidget(self.time_label)
        
        layout.addLayout(info_layout)
        
        self.setLayout(layout)
        
        # Timer para atualizar tempo
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_time)
        self.elapsed_seconds = 0
    
    def set_progress(self, value: int, status: str = ""):
        """Define progresso"""
        self.progress_bar.setValue(min(100, max(0, value)))
        if status:
            self.status_label.setText(status)
    
    def start(self):
        """Inicia contagem de tempo"""
        self.elapsed_seconds = 0
        self.timer.start(1000)
    
    def stop(self):
        """Para contagem de tempo"""
        self.timer.stop()
    
    def _update_time(self):
        """Atualiza tempo decorrido"""
        self.elapsed_seconds += 1
        minutes = self.elapsed_seconds // 60
        seconds = self.elapsed_seconds % 60
        self.time_label.setText(f"{minutes:02d}:{seconds:02d}")
    
    def reset(self):
        """Reseta o painel"""
        self.progress_bar.setValue(0)
        self.status_label.setText("Aguardando...")
        self.time_label.setText("00:00")
        self.elapsed_seconds = 0


class LogPanel(QGroupBox):
    """Painel de log com histórico de mensagens"""
    
    def __init__(self, title: str = "Log", max_lines: int = 1000):
        super().__init__(title)
        self.max_lines = max_lines
        self.init_ui()
    
    def init_ui(self):
        """Inicializa componentes"""
        layout = QVBoxLayout()
        
        # Text edit para logs
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.log_text.setMaximumHeight(200)
        
        # Fonte monoespacial para melhor legibilidade
        font = QFont("Courier")
        font.setPointSize(9)
        self.log_text.setFont(font)
        
        layout.addWidget(self.log_text)
        
        # Botões de controle
        button_layout = QHBoxLayout()
        
        clear_btn = QPushButton("Limpar")
        clear_btn.clicked.connect(self.clear)
        clear_btn.setMaximumWidth(100)
        button_layout.addWidget(clear_btn)
        
        button_layout.addStretch()
        
        self.auto_scroll_label = QLabel("Auto-scroll: ON")
        self.auto_scroll_label.setStyleSheet("color: #0a84ff;")
        button_layout.addWidget(self.auto_scroll_label)
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
        self.auto_scroll = True
    
    def add_log(self, message: str, level: str = "INFO"):
        """Adiciona mensagem ao log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Cores por nível
        colors = {
            "DEBUG": "#8e8e93",
            "INFO": "#ffffff",
            "WARNING": "#ff9500",
            "ERROR": "#ff3b30",
            "CRITICAL": "#ff3b30"
        }
        
        color = colors.get(level, "#ffffff")
        formatted_msg = f"<span style='color: {color}'>[{timestamp}] {level}: {message}</span>"
        
        self.log_text.append(formatted_msg)
        
        # Limitar número de linhas
        doc = self.log_text.document()
        if doc.blockCount() > self.max_lines:
            cursor = QTextCursor(doc)
            cursor.movePosition(QTextCursor.Start)
            cursor.select(QTextCursor.BlockUnderCursor)
            cursor.removeSelectedText()
        
        # Auto-scroll
        if self.auto_scroll:
            self.log_text.verticalScrollBar().setValue(
                self.log_text.verticalScrollBar().maximum()
            )
    
    def clear(self):
        """Limpa o log"""
        self.log_text.clear()
    
    def toggle_auto_scroll(self):
        """Alterna auto-scroll"""
        self.auto_scroll = not self.auto_scroll
        status = "ON" if self.auto_scroll else "OFF"
        self.auto_scroll_label.setText(f"Auto-scroll: {status}")


class StatusBar(QFrame):
    """Barra de status customizada"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Inicializa componentes"""
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("background-color: #1c1c1e; border-top: 1px solid #3a3a3c;")
        
        layout = QHBoxLayout()
        layout.setContentsMargins(16, 8, 16, 8)
        
        # Status principal
        self.status_label = QLabel("Pronto")
        self.status_label.setStyleSheet("color: #0a84ff; font-weight: 500;")
        layout.addWidget(self.status_label)
        
        layout.addSpacing(20)
        
        # Contadores
        self.counter_label = QLabel("0 registros")
        self.counter_label.setStyleSheet("color: #8e8e93;")
        layout.addWidget(self.counter_label)
        
        layout.addStretch()
        
        # Indicador de conexão
        self.connection_indicator = QLabel("●")
        self.connection_indicator.setStyleSheet("color: #34c759; font-size: 14px;")
        layout.addWidget(self.connection_indicator)
        
        self.connection_label = QLabel("Conectado")
        self.connection_label.setStyleSheet("color: #8e8e93;")
        layout.addWidget(self.connection_label)
        
        self.setLayout(layout)
    
    def set_status(self, message: str, color: str = "#0a84ff"):
        """Define mensagem de status"""
        self.status_label.setText(message)
        self.status_label.setStyleSheet(f"color: {color}; font-weight: 500;")
    
    def set_counter(self, count: int, label: str = "registros"):
        """Define contador"""
        self.counter_label.setText(f"{count} {label}")
    
    def set_connected(self, connected: bool):
        """Define estado de conexão"""
        if connected:
            self.connection_indicator.setStyleSheet("color: #34c759; font-size: 14px;")
            self.connection_label.setText("Conectado")
        else:
            self.connection_indicator.setStyleSheet("color: #ff3b30; font-size: 14px;")
            self.connection_label.setText("Desconectado")


class OperationPanel(QGroupBox):
    """Painel para operações com progresso e log integrados"""
    
    operation_started = pyqtSignal()
    operation_finished = pyqtSignal()
    operation_cancelled = pyqtSignal()
    
    def __init__(self, title: str = "Operação"):
        super().__init__(title)
        self.is_running = False
        self.init_ui()
    
    def init_ui(self):
        """Inicializa componentes"""
        layout = QVBoxLayout()
        
        # Painel de progresso
        self.progress_panel = ProgressPanel("Progresso da Operação")
        layout.addWidget(self.progress_panel)
        
        # Painel de log
        self.log_panel = LogPanel("Detalhes da Operação")
        layout.addWidget(self.log_panel)
        
        # Botões de controle
        button_layout = QHBoxLayout()
        
        self.start_btn = QPushButton("Iniciar")
        self.start_btn.clicked.connect(self._on_start)
        button_layout.addWidget(self.start_btn)
        
        self.pause_btn = QPushButton("Pausar")
        self.pause_btn.setEnabled(False)
        button_layout.addWidget(self.pause_btn)
        
        self.cancel_btn = QPushButton("Cancelar")
        self.cancel_btn.setEnabled(False)
        self.cancel_btn.clicked.connect(self._on_cancel)
        button_layout.addWidget(self.cancel_btn)
        
        button_layout.addStretch()
        
        layout.addLayout(button_layout)
        
        self.setLayout(layout)
    
    def start_operation(self):
        """Inicia operação"""
        self.is_running = True
        self.start_btn.setEnabled(False)
        self.cancel_btn.setEnabled(True)
        self.progress_panel.reset()
        self.progress_panel.start()
        self.operation_started.emit()
    
    def finish_operation(self, success: bool = True):
        """Finaliza operação"""
        self.is_running = False
        self.start_btn.setEnabled(True)
        self.cancel_btn.setEnabled(False)
        self.progress_panel.stop()
        
        if success:
            self.log_panel.add_log("Operação concluída com sucesso", "INFO")
        else:
            self.log_panel.add_log("Operação concluída com erros", "WARNING")
        
        self.operation_finished.emit()
    
    def _on_start(self):
        """Callback do botão iniciar"""
        self.start_operation()
    
    def _on_cancel(self):
        """Callback do botão cancelar"""
        self.is_running = False
        self.cancel_btn.setEnabled(False)
        self.log_panel.add_log("Operação cancelada pelo usuário", "WARNING")
        self.operation_cancelled.emit()
    
    def add_log(self, message: str, level: str = "INFO"):
        """Adiciona mensagem ao log"""
        self.log_panel.add_log(message, level)
    
    def set_progress(self, value: int, status: str = ""):
        """Define progresso"""
        self.progress_panel.set_progress(value, status)


class DetailedProgressDialog(QWidget):
    """Dialog com progresso detalhado e informações em tempo real"""
    
    def __init__(self, title: str = "Processando..."):
        super().__init__()
        self.setWindowTitle(title)
        self.setGeometry(100, 100, 600, 400)
        self.init_ui()
    
    def init_ui(self):
        """Inicializa componentes"""
        layout = QVBoxLayout()
        
        # Título
        title = QLabel("Processando dados...")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title.setFont(title_font)
        layout.addWidget(title)
        
        # Painel de operação
        self.operation_panel = OperationPanel()
        layout.addWidget(self.operation_panel)
        
        self.setLayout(layout)
    
    def update_progress(self, value: int, status: str = ""):
        """Atualiza progresso"""
        self.operation_panel.set_progress(value, status)
    
    def add_log(self, message: str, level: str = "INFO"):
        """Adiciona log"""
        self.operation_panel.add_log(message, level)
