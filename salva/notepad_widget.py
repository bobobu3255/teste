import os
import sys
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTextEdit, QLabel, QFileDialog, QMessageBox, 
    QTabWidget, QMenuBar, QMenu, QAction, QFrame,
    QPlainTextEdit
)
from PyQt5.QtCore import Qt, QRect, QSize, pyqtSignal
from PyQt5.QtGui import (
    QFont, QColor, QTextFormat, QPainter, 
    QSyntaxHighlighter, QTextCharFormat
)

# --- DESTAQUE DE SINTAXE SIMPLIFICADO ---
class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []

        # Estilos para o modo programação
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff79c6")) # Rosa (Dracula Style)
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ["class", "def", "if", "else", "elif", "for", "while", "return", "import", "from", "as", "try", "except", "self"]
        for word in keywords:
            self.highlighting_rules.append((f"\\b{word}\\b", keyword_format))

        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#f1fa8c")) # Amarelo
        self.highlighting_rules.append(("(\".*\"|'.*')", string_format))

        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272a4")) # Azul acinzentado
        self.highlighting_rules.append(("#.*", comment_format))

    def highlightBlock(self, text):
        import re
        for pattern, format in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), format)

# --- ÁREA DE CÓDIGO COM NÚMEROS DE LINHA ---
class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)

class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self.set_programming_mode(True)
        
        # Estilo padrão
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #0f172a;
                color: #e2e8f0;
                border: none;
                font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
                font-size: 14px;
            }
        """)

    def set_programming_mode(self, enabled):
        if enabled:
            self.highlighter = PythonHighlighter(self.document())
        else:
            self.highlighter = None

    def line_number_area_width(self):
        digits = 1
        max_value = max(1, self.blockCount())
        while max_value >= 10:
            max_value /= 10
            digits += 1
        space = 15 + self.fontMetrics().horizontalAdvance('9') * digits
        return space

    def update_line_number_area_width(self, _):
        self.setViewportMargins(self.line_number_area_width(), 0, 0, 0)

    def update_line_number_area(self, rect, dy):
        if dy:
            self.line_number_area.scroll(0, dy)
        else:
            self.line_number_area.update(0, rect.y(), self.line_number_area.width(), rect.height())
        if rect.contains(self.viewport().rect()):
            self.update_line_number_area_width(0)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        cr = self.contentsRect()
        self.line_number_area.setGeometry(QRect(cr.left(), cr.top(), self.line_number_area_width(), cr.height()))

    def line_number_area_paint_event(self, event):
        painter = QPainter(self.line_number_area)
        painter.fillRect(event.rect(), QColor("#1e293b")) # Cor da barra lateral

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()

        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                number = str(block_number + 1)
                painter.setPen(QColor("#64748b"))
                painter.drawText(0, int(top), self.line_number_area.width() - 5, self.fontMetrics().height(),
                                 Qt.AlignRight, number)
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_number += 1

    def highlight_current_line(self):
        extra_selections = []
        if not self.isReadOnly():
            selection = QTextEdit.ExtraSelection()
            line_color = QColor("#1e293b")
            selection.format.setBackground(line_color)
            selection.format.setProperty(QTextFormat.FullWidthSelection, True)
            selection.cursor = self.textCursor()
            selection.cursor.clearSelection()
            extra_selections.append(selection)
        self.setExtraSelections(extra_selections)

# --- WIDGET PRINCIPAL DO BLOCO DE NOTAS ---
class NotepadWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)

        # Barra de Ferramentas Estilo Windows 11
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(50)
        self.toolbar.setStyleSheet("""
            QFrame {
                background-color: #0f172a;
                border-bottom: 1px solid #1e293b;
            }
            QPushButton {
                background: transparent;
                color: #94a3b8;
                padding: 8px 15px;
                border-radius: 6px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #1e293b;
                color: #f8fafc;
            }
        """)
        toolbar_layout = QHBoxLayout(self.toolbar)
        toolbar_layout.setContentsMargins(10, 0, 10, 0)

        self.btn_new = QPushButton("📄 Novo")
        self.btn_new.clicked.connect(self.add_new_tab)
        
        self.btn_open = QPushButton("📂 Abrir")
        self.btn_open.clicked.connect(self.open_file)

        self.btn_save = QPushButton("💾 Salvar")
        self.btn_save.clicked.connect(self.save_current_tab)

        self.btn_mode = QPushButton("💻 Modo: Programação")
        self.btn_mode.setCheckable(True)
        self.btn_mode.setChecked(True)
        self.btn_mode.toggled.connect(self.toggle_programming_mode)

        toolbar_layout.addWidget(self.btn_new)
        toolbar_layout.addWidget(self.btn_open)
        toolbar_layout.addWidget(self.btn_save)
        toolbar_layout.addStretch()
        toolbar_layout.addWidget(self.btn_mode)
        
        self.layout.addWidget(self.toolbar)

        # Sistema de Abas
        self.tabs = QTabWidget()
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: none;
                background-color: #0f172a;
            }
            QTabBar::tab {
                background-color: #1e293b;
                color: #94a3b8;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                min-width: 120px;
            }
            QTabBar::tab:selected {
                background-color: #0f172a;
                color: #06b6d4;
                border-bottom: 2px solid #06b6d4;
            }
            QTabBar::tab:hover {
                background-color: #334155;
            }
        """)
        self.layout.addWidget(self.tabs)

        # Barra de Status
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(25)
        self.status_bar.setStyleSheet("background-color: #1e293b; color: #64748b; font-size: 11px;")
        status_layout = QHBoxLayout(self.status_bar)
        status_layout.setContentsMargins(15, 0, 15, 0)
        self.status_label = QLabel("Linha 1, Coluna 1 | UTF-8")
        status_layout.addStretch()
        status_layout.addWidget(self.status_label)
        self.layout.addWidget(self.status_bar)

        # Iniciar com uma aba vazia
        self.add_new_tab()

    def add_new_tab(self, checked=False, name="Sem título", content="", file_path=None):
        # Se 'checked' vier como string (pelo nome), ajustamos os argumentos
        if isinstance(checked, str):
            file_path = content
            content = name
            name = checked
            
        # Garante que o nome seja uma string válida
        if not isinstance(name, str):
            name = "Sem título"

        editor = CodeEditor()
        editor.setPlainText(content)
        editor.file_path = file_path
        editor.cursorPositionChanged.connect(self.update_status)
        
        index = self.tabs.addTab(editor, name)
        self.tabs.setCurrentIndex(index)
        return editor

    def close_tab(self, index):
        if self.tabs.count() > 1:
            self.tabs.removeTab(index)
        else:
            self.tabs.widget(0).setPlainText("")
            self.tabs.setTabText(0, "Sem título")
            self.tabs.widget(0).file_path = None

    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(self, "Abrir Arquivo", "", "Todos os Arquivos (*)")
        if path:
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()
                self.add_new_tab(os.path.basename(path), content, path)
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao abrir: {str(e)}")

    def save_current_tab(self):
        editor = self.tabs.currentWidget()
        if not editor: return

        if not editor.file_path:
            path, _ = QFileDialog.getSaveFileName(self, "Salvar Arquivo", "novo.txt", "Todos os Arquivos (*)")
            if not path: return
            editor.file_path = path
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))

        try:
            with open(editor.file_path, 'w', encoding='utf-8') as f:
                f.write(editor.toPlainText())
            QMessageBox.information(self, "Salvo", "Arquivo salvo com sucesso!")
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao salvar: {str(e)}")

    def toggle_programming_mode(self, enabled):
        for i in range(self.tabs.count()):
            editor = self.tabs.widget(i)
            editor.set_programming_mode(enabled)
        
        self.btn_mode.setText("💻 Modo: Programação" if enabled else "📝 Modo: Texto")

    def update_status(self):
        editor = self.tabs.currentWidget()
        if editor:
            cursor = editor.textCursor()
            line = cursor.blockNumber() + 1
            col = cursor.columnNumber() + 1
            self.status_label.setText(f"Linha {line}, Coluna {col} | UTF-8")

if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    window = NotepadWidget()
    window.show()
    sys.exit(app.exec_())
