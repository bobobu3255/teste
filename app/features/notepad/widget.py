import os
import sys
import json
import re
import subprocess
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTextEdit, QLabel, QFileDialog, QMessageBox,
    QTabWidget, QFrame, QPlainTextEdit, QLineEdit,
    QShortcut, QListWidget, QSplitter, QMenu, QAction, QCheckBox, QSizePolicy,
    QInputDialog, QDialog, QApplication, QComboBox, QSpinBox, QListWidgetItem
)
from PyQt5.QtCore import Qt, QRect, QSize, QTimer, QEvent, QThread, pyqtSignal
from PyQt5.QtGui import (
    QFont, QColor, QTextFormat, QPainter,
    QSyntaxHighlighter, QTextCharFormat, QKeySequence, QTextCursor, QPen,
    QTextDocument
)

from app.core.paths import BASE_DIR
from app.features.notepad.styles import (
    file_list_qss, filter_input_qss, label_qss as note_label_qss, minimap_qss,
    notepad_editor_qss, notepad_menu_qss, primary_button_qss, search_bar_qss,
    sidebar_qss, small_button_qss, snippets_dialog_qss, splitter_qss,
    status_bar_qss, tabs_qss, terminal_clear_qss, terminal_header_qss,
    terminal_input_frame_qss, terminal_input_qss, terminal_output_qss,
    terminal_title_qss, toolbar_icon_qss, toolbar_qss, toolbar_toggle_qss,
)

SESSION_FILE = os.path.join(str(BASE_DIR), "notepad_session.json")
SNIPPETS_FILE = os.path.join(str(BASE_DIR), "notepad_snippets.json")
NOTES_DIR = os.path.join(str(BASE_DIR), "notas")
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0

# ─────────────────────────────────────────────
#  DESTAQUE DE SINTAXE – Python (original)
# ─────────────────────────────────────────────
class PythonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.highlighting_rules = []
        keyword_format = QTextCharFormat()
        keyword_format.setForeground(QColor("#ff79c6"))
        keyword_format.setFontWeight(QFont.Bold)
        keywords = ["class", "def", "if", "else", "elif", "for", "while", "return",
                    "import", "from", "as", "try", "except", "finally", "with", "self",
                    "True", "False", "None", "and", "or", "not", "in", "is", "lambda",
                    "pass", "break", "continue", "raise", "yield", "global", "nonlocal",
                    "del", "assert", "async", "await"]
        for word in keywords:
            self.highlighting_rules.append((fr"\b{word}\b", keyword_format))
        builtin_format = QTextCharFormat()
        builtin_format.setForeground(QColor("#8be9fd"))
        builtins = ["print", "len", "range", "type", "int", "str", "float", "list",
                    "dict", "set", "tuple", "open", "enumerate", "zip", "map", "filter",
                    "sorted", "sum", "min", "max", "abs", "round", "input", "super",
                    "isinstance", "hasattr"]
        for word in builtins:
            self.highlighting_rules.append((fr"\b{word}\b", builtin_format))
        string_format = QTextCharFormat()
        string_format.setForeground(QColor("#f1fa8c"))
        self.highlighting_rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', string_format))
        self.highlighting_rules.append((r"'[^'\\]*(\\.[^'\\]*)*'", string_format))
        number_format = QTextCharFormat()
        number_format.setForeground(QColor("#bd93f9"))
        self.highlighting_rules.append((r'\b\d+(\.\d+)?\b', number_format))
        decorator_format = QTextCharFormat()
        decorator_format.setForeground(QColor("#50fa7b"))
        self.highlighting_rules.append((r'@\w+', decorator_format))
        comment_format = QTextCharFormat()
        comment_format.setForeground(QColor("#6272a4"))
        comment_format.setFontItalic(True)
        self.highlighting_rules.append((r'#.*', comment_format))

    def highlightBlock(self, text):
        for pattern, fmt in self.highlighting_rules:
            for match in re.finditer(pattern, text):
                self.setFormat(match.start(), match.end() - match.start(), fmt)


# ─────────────────────────────────────────────
#  DESTAQUE DE SINTAXE – JSON
# ─────────────────────────────────────────────
class JsonHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []
        key_fmt = QTextCharFormat()
        key_fmt.setForeground(QColor("#8be9fd"))
        key_fmt.setFontWeight(QFont.Bold)
        self.rules.append((r'"[^"\\]*(\\.[^"\\]*)*"\s*:', key_fmt))
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#f1fa8c"))
        self.rules.append((r':\s*"[^"\\]*(\\.[^"\\]*)*"', str_fmt))
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#bd93f9"))
        self.rules.append((r'\b\d+(\.\d+)?\b', num_fmt))
        bool_fmt = QTextCharFormat()
        bool_fmt.setForeground(QColor("#ff79c6"))
        bool_fmt.setFontWeight(QFont.Bold)
        self.rules.append((r'\b(true|false|null)\b', bool_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for m in re.finditer(pattern, text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ─────────────────────────────────────────────
#  DESTAQUE DE SINTAXE – HTML
# ─────────────────────────────────────────────
class HtmlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []
        tag_fmt = QTextCharFormat()
        tag_fmt.setForeground(QColor("#ff79c6"))
        tag_fmt.setFontWeight(QFont.Bold)
        self.rules.append((r'<[^>]+>', tag_fmt))
        attr_fmt = QTextCharFormat()
        attr_fmt.setForeground(QColor("#50fa7b"))
        self.rules.append((r'\b\w+\s*=', attr_fmt))
        val_fmt = QTextCharFormat()
        val_fmt.setForeground(QColor("#f1fa8c"))
        self.rules.append((r'"[^"]*"', val_fmt))
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6272a4"))
        comment_fmt.setFontItalic(True)
        self.rules.append((r'<!--.*?-->', comment_fmt))
        entity_fmt = QTextCharFormat()
        entity_fmt.setForeground(QColor("#8be9fd"))
        self.rules.append((r'&[a-zA-Z]+;', entity_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for m in re.finditer(pattern, text, re.DOTALL):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ─────────────────────────────────────────────
#  DESTAQUE DE SINTAXE – SQL
# ─────────────────────────────────────────────
class SqlHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#ff79c6"))
        kw_fmt.setFontWeight(QFont.Bold)
        keywords = ["SELECT", "FROM", "WHERE", "INSERT", "INTO", "VALUES", "UPDATE",
                    "SET", "DELETE", "CREATE", "TABLE", "DROP", "ALTER", "ADD", "COLUMN",
                    "INDEX", "VIEW", "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON",
                    "GROUP", "BY", "ORDER", "HAVING", "LIMIT", "OFFSET", "AS", "AND",
                    "OR", "NOT", "NULL", "IS", "IN", "LIKE", "BETWEEN", "DISTINCT",
                    "COUNT", "SUM", "AVG", "MIN", "MAX", "CASE", "WHEN", "THEN", "ELSE",
                    "END", "UNION", "ALL", "EXISTS", "PRIMARY", "KEY", "FOREIGN",
                    "REFERENCES", "DEFAULT", "UNIQUE", "CHECK", "BEGIN", "COMMIT",
                    "ROLLBACK", "TRANSACTION", "DATABASE", "USE", "TRUNCATE", "WITH"]
        for kw in keywords:
            self.rules.append((fr'\b{kw}\b', kw_fmt))
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#f1fa8c"))
        self.rules.append((r"'[^']*'", str_fmt))
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#bd93f9"))
        self.rules.append((r'\b\d+(\.\d+)?\b', num_fmt))
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6272a4"))
        comment_fmt.setFontItalic(True)
        self.rules.append((r'--.*', comment_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for m in re.finditer(pattern, text, re.IGNORECASE):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


# ─────────────────────────────────────────────
#  ÁREA DE NÚMEROS DE LINHA (original)
# ─────────────────────────────────────────────
class MarkdownHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []
        heading_fmt = QTextCharFormat()
        heading_fmt.setForeground(QColor("#8be9fd"))
        heading_fmt.setFontWeight(QFont.Bold)
        self.rules.append((r"^#{1,6}\s.*", heading_fmt))
        bold_fmt = QTextCharFormat()
        bold_fmt.setForeground(QColor("#f1fa8c"))
        bold_fmt.setFontWeight(QFont.Bold)
        self.rules.append((r"\*\*[^*]+\*\*", bold_fmt))
        code_fmt = QTextCharFormat()
        code_fmt.setForeground(QColor("#50fa7b"))
        self.rules.append((r"`[^`]+`", code_fmt))
        link_fmt = QTextCharFormat()
        link_fmt.setForeground(QColor("#bd93f9"))
        self.rules.append((r"\[[^\]]+\]\([^)]+\)", link_fmt))
        quote_fmt = QTextCharFormat()
        quote_fmt.setForeground(QColor("#6272a4"))
        quote_fmt.setFontItalic(True)
        self.rules.append((r"^\s*>.*", quote_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for m in re.finditer(pattern, text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class CssHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []
        selector_fmt = QTextCharFormat()
        selector_fmt.setForeground(QColor("#8be9fd"))
        self.rules.append((r"^[^{]+(?=\{)", selector_fmt))
        prop_fmt = QTextCharFormat()
        prop_fmt.setForeground(QColor("#50fa7b"))
        self.rules.append((r"[-a-zA-Z]+\s*:", prop_fmt))
        value_fmt = QTextCharFormat()
        value_fmt.setForeground(QColor("#f1fa8c"))
        self.rules.append((r":\s*[^;]+", value_fmt))
        color_fmt = QTextCharFormat()
        color_fmt.setForeground(QColor("#bd93f9"))
        self.rules.append((r"#[0-9a-fA-F]{3,8}\b", color_fmt))
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6272a4"))
        comment_fmt.setFontItalic(True)
        self.rules.append((r"/\*.*?\*/", comment_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for m in re.finditer(pattern, text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class JsHighlighter(QSyntaxHighlighter):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []
        kw_fmt = QTextCharFormat()
        kw_fmt.setForeground(QColor("#ff79c6"))
        kw_fmt.setFontWeight(QFont.Bold)
        keywords = [
            "const", "let", "var", "function", "return", "if", "else", "for",
            "while", "class", "new", "this", "import", "from", "export",
            "async", "await", "try", "catch", "finally", "throw", "true",
            "false", "null", "undefined"
        ]
        for kw in keywords:
            self.rules.append((fr"\b{kw}\b", kw_fmt))
        str_fmt = QTextCharFormat()
        str_fmt.setForeground(QColor("#f1fa8c"))
        self.rules.append((r'"[^"\\]*(\\.[^"\\]*)*"', str_fmt))
        self.rules.append((r"'[^'\\]*(\\.[^'\\]*)*'", str_fmt))
        self.rules.append((r"`[^`]*`", str_fmt))
        num_fmt = QTextCharFormat()
        num_fmt.setForeground(QColor("#bd93f9"))
        self.rules.append((r"\b\d+(\.\d+)?\b", num_fmt))
        comment_fmt = QTextCharFormat()
        comment_fmt.setForeground(QColor("#6272a4"))
        comment_fmt.setFontItalic(True)
        self.rules.append((r"//.*", comment_fmt))

    def highlightBlock(self, text):
        for pattern, fmt in self.rules:
            for m in re.finditer(pattern, text):
                self.setFormat(m.start(), m.end() - m.start(), fmt)


class LineNumberArea(QWidget):
    def __init__(self, editor):
        super().__init__(editor)
        self.code_editor = editor

    def sizeHint(self):
        return QSize(self.code_editor.line_number_area_width(), 0)

    def paintEvent(self, event):
        self.code_editor.line_number_area_paint_event(event)


# ─────────────────────────────────────────────
#  MINI-MAPA
# ─────────────────────────────────────────────
class MiniMap(QWidget):
    def __init__(self, editor, parent=None):
        super().__init__(parent)
        self.editor = editor
        self.setFixedWidth(80)
        self.setStyleSheet("background-color: #0a1020;")
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip("Mini-Mapa: clique para navegar")
        self._dragging = False

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor("#0a1020"))
        try:
            doc = self.editor.document()
        except RuntimeError:
            return
        total_lines = max(doc.blockCount(), 1)
        w = self.width()
        h = max(self.height(), 1)
        line_h = max(1.0, h / total_lines)
        block = doc.begin()
        y = 0.0
        while block.isValid():
            text = block.text().strip()
            if text:
                color = self._line_color(text)
                rect = QRect(2, int(y), w - 4, max(1, int(line_h)))
                painter.fillRect(rect, color)
            y += line_h
            if y > h:
                break
            block = block.next()
        # Viewport indicator
        sb = self.editor.verticalScrollBar()
        total = sb.maximum() + sb.pageStep()
        if total > 0:
            ratio_start = sb.value() / total
            ratio_size = sb.pageStep() / total
        else:
            ratio_start, ratio_size = 0, 1
        vp_y = int(ratio_start * h)
        vp_h = max(10, int(ratio_size * h))
        painter.setBrush(QColor(6, 182, 212, 45))
        painter.setPen(QPen(QColor("#06b6d4"), 1))
        painter.drawRect(1, vp_y, w - 2, vp_h)

    def _line_color(self, text):
        ch = text[0] if text else ' '
        if ch in ('#', '-', '/'):
            return QColor("#6272a4")
        if ch in ('"', "'"):
            return QColor("#f1fa8c")
        if ch.isdigit():
            return QColor("#bd93f9")
        if ch.isupper():
            return QColor("#ff79c6")
        return QColor("#8be9fd")

    def mousePressEvent(self, event):
        self._dragging = True
        self._scroll_to(event.y())

    def mouseMoveEvent(self, event):
        if self._dragging:
            self._scroll_to(event.y())

    def mouseReleaseEvent(self, event):
        self._dragging = False

    def _scroll_to(self, y):
        ratio = max(0.0, min(1.0, y / max(self.height(), 1)))
        sb = self.editor.verticalScrollBar()
        sb.setValue(int(ratio * max(sb.maximum(), 0)))
        self.update()


# ─────────────────────────────────────────────
#  EDITOR DE CÓDIGO (original + multilanguage)
# ─────────────────────────────────────────────
class CodeEditor(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.line_number_area = LineNumberArea(self)
        self.blockCountChanged.connect(self.update_line_number_area_width)
        self.updateRequest.connect(self.update_line_number_area)
        self.cursorPositionChanged.connect(self.highlight_current_line)
        self.update_line_number_area_width(0)
        self._language = "python"
        self.set_language("python")
        self.file_path = None
        self.is_modified = False
        self.current_font_size = 14
        self.update_font()
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setPlaceholderText("Escreva notas, scripts, listas, logs ou rascunhos...")
        self.setStyleSheet(notepad_editor_qss())
        self.document().contentsChanged.connect(lambda: setattr(self, 'is_modified', True))

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #1e293b; color: white; border: 1px solid #334155; } QMenu::item:selected { background-color: #06b6d4; }")
        undo_action = menu.addAction("↩️ Desfazer")
        undo_action.setShortcut("Ctrl+Z")
        undo_action.triggered.connect(self.undo)
        undo_action.setEnabled(self.document().isUndoAvailable())
        redo_action = menu.addAction("↪️ Refazer")
        redo_action.setShortcut("Ctrl+Y")
        redo_action.triggered.connect(self.redo)
        redo_action.setEnabled(self.document().isRedoAvailable())
        menu.addSeparator()
        cut_action = menu.addAction("✂️ Recortar")
        cut_action.setShortcut("Ctrl+X")
        cut_action.triggered.connect(self.cut)
        copy_action = menu.addAction("📋 Copiar")
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self.copy)
        paste_action = menu.addAction("📥 Colar")
        paste_action.setShortcut("Ctrl+V")
        paste_action.triggered.connect(self.paste)
        delete_action = menu.addAction("🗑️ Excluir")
        delete_action.triggered.connect(lambda: self.textCursor().removeSelectedText())
        menu.addSeparator()
        select_all_action = menu.addAction("🔍 Selecionar Tudo")
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.selectAll)
        menu.exec_(event.globalPos())

    def update_font(self):
        font = QFont('Consolas', self.current_font_size)
        self.setFont(font)
        try:
            self.setTabStopDistance(self.fontMetrics().horizontalAdvance(' ') * 4)
        except AttributeError:
            pass

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            if event.angleDelta().y() > 0:
                self.current_font_size += 1
            else:
                self.current_font_size = max(6, self.current_font_size - 1)
            self.update_font()
        else:
            super().wheelEvent(event)

    def set_language(self, lang):
        self._language = lang
        doc = self.document()
        if lang == "python":
            self.highlighter = PythonHighlighter(doc)
        elif lang == "json":
            self.highlighter = JsonHighlighter(doc)
        elif lang == "html":
            self.highlighter = HtmlHighlighter(doc)
        elif lang == "sql":
            self.highlighter = SqlHighlighter(doc)
        elif lang == "markdown":
            self.highlighter = MarkdownHighlighter(doc)
        elif lang == "css":
            self.highlighter = CssHighlighter(doc)
        elif lang == "javascript":
            self.highlighter = JsHighlighter(doc)
        else:
            self.highlighter = None

    def set_programming_mode(self, enabled):
        if enabled:
            self.set_language(self._language)
        else:
            self.highlighter = None

    def set_word_wrap(self, enabled):
        self.setLineWrapMode(QPlainTextEdit.WidgetWidth if enabled else QPlainTextEdit.NoWrap)

    def line_number_area_width(self):
        digits, max_val = 1, max(1, self.blockCount())
        while max_val >= 10:
            max_val /= 10
            digits += 1
        return 15 + self.fontMetrics().horizontalAdvance('9') * digits

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
        painter.fillRect(event.rect(), QColor("#0a1627"))
        block = self.firstVisibleBlock()
        block_num = block.blockNumber()
        top = self.blockBoundingGeometry(block).translated(self.contentOffset()).top()
        bottom = top + self.blockBoundingRect(block).height()
        while block.isValid() and top <= event.rect().bottom():
            if block.isVisible() and bottom >= event.rect().top():
                painter.setPen(QColor("#52637a"))
                painter.drawText(0, int(top), self.line_number_area.width() - 5,
                                 self.fontMetrics().height(), Qt.AlignRight, str(block_num + 1))
            block = block.next()
            top = bottom
            bottom = top + self.blockBoundingRect(block).height()
            block_num += 1

    def highlight_current_line(self):
        selections = []
        if not self.isReadOnly():
            s = QTextEdit.ExtraSelection()
            s.format.setBackground(QColor("#0f2137"))
            s.format.setProperty(QTextFormat.FullWidthSelection, True)
            s.cursor = self.textCursor()
            s.cursor.clearSelection()
            selections.append(s)
        self.setExtraSelections(selections)


# ─────────────────────────────────────────────
#  TERMINAL INTEGRADO
# ─────────────────────────────────────────────
class TerminalCommandWorker(QThread):
    result_ready = pyqtSignal(str, str, int)

    def __init__(self, cmd, cwd, parent=None):
        super().__init__(parent)
        self.cmd = cmd
        self.cwd = cwd

    def run(self):
        try:
            result = subprocess.run(
                self.cmd,
                shell=True,
                cwd=self.cwd,
                capture_output=True,
                text=True,
                timeout=15,
                encoding="utf-8",
                errors="replace",
                creationflags=CREATE_NO_WINDOW,
            )
            self.result_ready.emit(result.stdout or "", result.stderr or "", result.returncode)
        except subprocess.TimeoutExpired:
            self.result_ready.emit("", "Tempo limite excedido (15s)\n", 124)
        except Exception as exc:
            self.result_ready.emit("", f"Erro: {exc}\n", 1)


class TerminalWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(175)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        header = QFrame()
        header.setFixedHeight(28)
        header.setStyleSheet(terminal_header_qss())
        hdr_layout = QHBoxLayout(header)
        hdr_layout.setContentsMargins(10, 0, 10, 0)
        lbl = QLabel("⚡ TERMINAL INTEGRADO")
        lbl.setStyleSheet(terminal_title_qss())
        self.btn_limpar = QPushButton("🗑 Limpar")
        self.btn_limpar.setFixedHeight(20)
        self.btn_limpar.setStyleSheet(terminal_clear_qss())
        self.btn_limpar.clicked.connect(self._clear)
        hdr_layout.addWidget(lbl)
        hdr_layout.addStretch()
        hdr_layout.addWidget(self.btn_limpar)
        layout.addWidget(header)

        self.output = QPlainTextEdit()
        self.output.setReadOnly(True)
        self.output.setFont(QFont("Consolas", 11))
        self.output.setStyleSheet(terminal_output_qss())
        self.output.setMaximumBlockCount(400)
        layout.addWidget(self.output)

        input_frame = QFrame()
        input_frame.setFixedHeight(30)
        input_frame.setStyleSheet(terminal_input_frame_qss())
        inp_layout = QHBoxLayout(input_frame)
        inp_layout.setContentsMargins(8, 2, 8, 2)
        prompt = QLabel("$")
        prompt.setStyleSheet(note_label_qss("terminal_prompt"))
        self.cmd_input = QLineEdit()
        self.cmd_input.setStyleSheet(terminal_input_qss())
        self.cmd_input.setPlaceholderText("Digite um comando e pressione Enter...")
        self.cmd_input.returnPressed.connect(self.run_command)
        inp_layout.addWidget(prompt)
        inp_layout.addWidget(self.cmd_input)
        layout.addWidget(input_frame)

        self._history = []
        self._history_idx = -1
        self._cwd = os.getcwd()
        self._worker = None
        self.cmd_input.installEventFilter(self)
        self._append("Terminal iniciado em: " + self._cwd + "\n")

    def eventFilter(self, obj, event):
        if obj == self.cmd_input and event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Up:
                if self._history and self._history_idx < len(self._history) - 1:
                    self._history_idx += 1
                    self.cmd_input.setText(self._history[-(self._history_idx + 1)])
                return True
            elif event.key() == Qt.Key_Down:
                if self._history_idx > 0:
                    self._history_idx -= 1
                    self.cmd_input.setText(self._history[-(self._history_idx + 1)])
                elif self._history_idx == 0:
                    self._history_idx = -1
                    self.cmd_input.clear()
                return True
        return super().eventFilter(obj, event)

    def run_command(self):
        cmd = self.cmd_input.text().strip()
        if not cmd:
            return
        if self._worker and self._worker.isRunning():
            self._append("Aguarde o comando atual terminar.\n", color="#ffb86c")
            return
        self._history.append(cmd)
        self._history_idx = -1
        self._append("$ " + cmd + "\n", color="#06b6d4")
        self.cmd_input.clear()
        if cmd.startswith("cd "):
            path = cmd[3:].strip()
            try:
                target = path if os.path.isabs(path) else os.path.join(self._cwd, path)
                target = os.path.abspath(target)
                if not os.path.isdir(target):
                    raise FileNotFoundError(target)
                self._cwd = target
                self._append("Diretório: " + self._cwd + "\n")
            except Exception as e:
                self._append("Erro: " + str(e) + "\n", color="#ff5555")
            return
        if cmd in ("clear", "cls"):
            self._clear()
            return
        self.cmd_input.setEnabled(False)
        self._worker = TerminalCommandWorker(cmd, self._cwd, self)
        self._worker.result_ready.connect(self._on_command_finished)
        self._worker.finished.connect(self._worker.deleteLater)
        self._worker.start()

    def _on_command_finished(self, stdout, stderr, returncode):
        if stdout:
            self._append(stdout)
        if stderr:
            self._append(stderr, color="#ff5555" if returncode != 124 else "#ffb86c")
        if not stdout and not stderr:
            self._append("(sem saída)\n", color="#64748b")
        self.cmd_input.setEnabled(True)
        self.cmd_input.setFocus()

    def _append(self, text, color="#a8e6cf"):
        cursor = self.output.textCursor()
        cursor.movePosition(QTextCursor.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        cursor.mergeCharFormat(fmt)
        cursor.insertText(text)
        self.output.setTextCursor(cursor)
        self.output.ensureCursorVisible()

    def _clear(self):
        self.output.clear()


# ─────────────────────────────────────────────
#  DIÁLOGO DE SNIPPETS
# ─────────────────────────────────────────────
class SnippetsDialog(QDialog):
    def __init__(self, snippets, parent=None):
        super().__init__(parent)
        self._result_code = None
        self.setWindowTitle("📌 Gerenciador de Snippets")
        self.setMinimumSize(600, 420)
        self.setStyleSheet(snippets_dialog_qss())
        self.snippets = snippets

        layout = QHBoxLayout(self)

        left = QVBoxLayout()
        lbl = QLabel("📌 SNIPPETS SALVOS")
        lbl.setStyleSheet(note_label_qss("tiny_cyan"))
        left.addWidget(lbl)
        self.list_widget = QListWidget()
        self.list_widget.currentRowChanged.connect(self._on_select)
        left.addWidget(self.list_widget)
        btn_row = QHBoxLayout()
        self.btn_novo = QPushButton("➕ Novo")
        self.btn_novo.clicked.connect(self._novo)
        self.btn_excluir = QPushButton("🗑 Excluir")
        self.btn_excluir.clicked.connect(self._excluir)
        btn_row.addWidget(self.btn_novo)
        btn_row.addWidget(self.btn_excluir)
        left.addLayout(btn_row)

        right = QVBoxLayout()
        lbl2 = QLabel("📝 CONTEÚDO (editável)")
        lbl2.setStyleSheet(note_label_qss("tiny_cyan"))
        right.addWidget(lbl2)
        self.preview = QPlainTextEdit()
        self.preview.setPlaceholderText("Selecione ou crie um snippet...")
        right.addWidget(self.preview)

        self.btn_inserir = QPushButton("📥  Inserir no Editor")
        self.btn_inserir.setStyleSheet(primary_button_qss())
        self.btn_inserir.clicked.connect(self._inserir)
        right.addWidget(self.btn_inserir)

        layout.addLayout(left, 1)
        layout.addLayout(right, 2)
        self._populate()

    def _populate(self):
        self.list_widget.clear()
        for name in self.snippets:
            self.list_widget.addItem(name)

    def _on_select(self, row):
        # Salva edições da seleção anterior antes de trocar
        curr_items = self.list_widget.selectedItems()
        # Nota: row já é o novo row. Para salvar o anterior seria necessário
        # rastrear o índice anterior. Salvamos via closeEvent e _inserir.
        if row < 0:
            self.preview.clear()
            return
        name = self.list_widget.item(row).text()
        self.preview.setPlainText(self.snippets.get(name, ""))

    def _novo(self):
        name, ok = QInputDialog.getText(self, "Novo Snippet", "Nome do snippet:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self.snippets:
            QMessageBox.warning(self, "Aviso", "Já existe um snippet com esse nome.")
            return
        self.snippets[name] = "# Escreva o código aqui\n"
        self._populate()
        items = self.list_widget.findItems(name, Qt.MatchExactly)
        if items:
            self.list_widget.setCurrentItem(items[0])

    def _excluir(self):
        row = self.list_widget.currentRow()
        if row < 0:
            return
        name = self.list_widget.item(row).text()
        reply = QMessageBox.question(self, "Excluir",
                                     f'Excluir snippet "{name}"?',
                                     QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.Yes:
            del self.snippets[name]
            self._populate()
            self.preview.clear()
            if self.list_widget.count() > 0:
                self.list_widget.setCurrentRow(0)

    def _inserir(self):
        row = self.list_widget.currentRow()
        if row < 0:
            QMessageBox.information(self, "Aviso", "Selecione um snippet primeiro.")
            return
        name = self.list_widget.item(row).text()
        self.snippets[name] = self.preview.toPlainText()
        self._result_code = self.snippets[name]
        self.accept()

    def closeEvent(self, event):
        row = self.list_widget.currentRow()
        if row >= 0:
            name = self.list_widget.item(row).text()
            self.snippets[name] = self.preview.toPlainText()
        super().closeEvent(event)

    def get_code(self):
        return self._result_code


# ─────────────────────────────────────────────
#  WIDGET PRINCIPAL
# ─────────────────────────────────────────────
class NotepadWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.snippets = self._load_snippets()
        os.makedirs(NOTES_DIR, exist_ok=True)
        self.current_folder = NOTES_DIR
        self.word_wrap_enabled = True
        self.programming_mode_enabled = True
        self.simple_mode_enabled = True
        self.editor_panes = []
        self.tabs = None
        self.init_ui()
        self.load_session()
        self.setup_autosave()
        self.refresh_file_list()

    # ── SNIPPETS ──────────────────────────────
    def _load_snippets(self):
        if os.path.exists(SNIPPETS_FILE):
            try:
                with open(SNIPPETS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {
            "Python – Classe básica": (
                "class MinhaClasse:\n"
                "    def __init__(self):\n"
                "        pass\n\n"
                "    def metodo(self):\n"
                "        pass\n"
            ),
            "SQL – SELECT com JOIN": (
                "SELECT a.id, a.nome, b.valor\n"
                "FROM tabela_a AS a\n"
                "INNER JOIN tabela_b AS b ON a.id = b.id_a\n"
                "WHERE a.ativo = 1\n"
                "ORDER BY a.nome;\n"
            ),
            "HTML – Estrutura básica": (
                '<!DOCTYPE html>\n'
                '<html lang="pt-BR">\n'
                '<head>\n'
                '    <meta charset="UTF-8">\n'
                '    <title>Título</title>\n'
                '</head>\n'
                '<body>\n'
                '    <h1>Olá Mundo</h1>\n'
                '</body>\n'
                '</html>\n'
            ),
            "JSON – Configuração": (
                '{\n'
                '    "nome": "projeto",\n'
                '    "versao": "1.0.0",\n'
                '    "configuracoes": {\n'
                '        "debug": false,\n'
                '        "porta": 8080\n'
                '    }\n'
                '}\n'
            ),
        }

    def _save_snippets(self):
        try:
            with open(SNIPPETS_FILE, "w", encoding="utf-8") as f:
                json.dump(self.snippets, f, ensure_ascii=False, indent=4)
        except:
            pass

    def _salvar_snippet_atual(self):
        editor = self.tabs.currentWidget()
        if not editor:
            return
        cursor = editor.textCursor()
        texto = cursor.selectedText() if cursor.hasSelection() else editor.toPlainText()
        if not texto.strip():
            QMessageBox.information(self, "Aviso", "Selecione ou escreva algum código primeiro.")
            return
        name, ok = QInputDialog.getText(self, "Salvar Snippet", "Nome do snippet:")
        if ok and name.strip():
            self.snippets[name.strip()] = texto
            self._save_snippets()
            self._show_status(f"Snippet '{name}' salvo!")

    def _abrir_gerenciador_snippets(self):
        dlg = SnippetsDialog(self.snippets, parent=self)
        if dlg.exec_() == QDialog.Accepted:
            code = dlg.get_code()
            if code:
                editor = self.tabs.currentWidget()
                if editor:
                    editor.textCursor().insertText(code)
        self._save_snippets()

    # ── INTERFACE ─────────────────────────────
    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # BARRA DE FERRAMENTAS
        self.toolbar = QFrame()
        self.toolbar.setFixedHeight(52)
        self.toolbar.setStyleSheet(toolbar_qss())
        toolbar_hbox = QHBoxLayout(self.toolbar)
        toolbar_hbox.setContentsMargins(12, 0, 12, 0)
        toolbar_hbox.setSpacing(7)

        self.btn_toggle_sidebar = QPushButton("📁")
        self.btn_toggle_sidebar.setToolTip("Mostrar/Esconder Explorador (Ctrl+B)")
        self.btn_toggle_sidebar.setFixedWidth(40)
        self.btn_toggle_sidebar.setStyleSheet(toolbar_icon_qss())
        self.btn_toggle_sidebar.clicked.connect(self.toggle_sidebar)

        self.btn_new = QPushButton("📄 Novo")
        self.btn_new.clicked.connect(lambda: self.add_new_tab())
        self.btn_open = QPushButton("📂 Abrir")
        self.btn_open.clicked.connect(self.open_file)

        self.btn_save = QPushButton("💾 Salvar ▼")
        save_menu = QMenu(self)
        save_menu.setStyleSheet(notepad_menu_qss())
        save_menu.addAction("💾 Salvar", self.save_current_tab)
        save_menu.addAction("💾 Salvar Como...", self.save_as_current_tab)
        save_menu.addAction("💾 Salvar Tudo", self.save_all_tabs)
        self.btn_save.setMenu(save_menu)

        self.btn_search = QPushButton("🔍 Buscar")
        self.btn_search.setToolTip("Localizar e substituir (Ctrl+F)")
        self.btn_search.clicked.connect(self.toggle_search)

        self.btn_data = QPushButton("🧹 Dados ▼")
        data_menu = QMenu(self)
        data_menu.setStyleSheet(notepad_menu_qss())
        data_menu.addAction("Remover Duplicados", self.remove_duplicates)
        data_menu.addAction("Ordenar A-Z", lambda: self.sort_lines(reverse=False))
        data_menu.addAction("Ordenar Z-A", lambda: self.sort_lines(reverse=True))
        data_menu.addAction("Remover Linhas Vazias", self.remove_empty_lines)
        data_menu.addAction("Aparar Espacos", self.trim_lines)
        data_menu.addAction("Normalizar Espacos", self.normalize_spaces)
        data_menu.addAction("Inverter Linhas", self.reverse_lines)
        data_menu.addSeparator()
        data_menu.addAction("MAIUSCULAS", lambda: self.transform_text("upper"))
        data_menu.addAction("minusculas", lambda: self.transform_text("lower"))
        data_menu.addAction("Titulo", lambda: self.transform_text("title"))
        data_menu.addSeparator()
        data_menu.addAction("Formatar JSON", self.format_json)
        data_menu.addAction("Minificar JSON", self.minify_json)
        data_menu.addSeparator()
        data_menu.addAction("Extrair E-mails", lambda: self.extract_pattern(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'))
        data_menu.addAction("Extrair CPFs", lambda: self.extract_pattern(r'\d{3}\.\d{3}\.\d{3}-\d{2}|\d{11}'))
        data_menu.addAction("Extrair Telefones", lambda: self.extract_pattern(r'\+?\d[\d\s().-]{7,}\d'))
        data_menu.addAction("Extrair URLs", lambda: self.extract_pattern(r'https?://[^\s]+'))
        self.btn_data.setMenu(data_menu)

        # SNIPPETS
        self.btn_snippets = QPushButton("📌 Snippets ▼")
        snippets_menu = QMenu(self)
        snippets_menu.setStyleSheet(notepad_menu_qss())
        snippets_menu.addAction("📋 Gerenciar Snippets", self._abrir_gerenciador_snippets)
        snippets_menu.addAction("💾 Salvar Seleção como Snippet", self._salvar_snippet_atual)
        self.btn_snippets.setMenu(snippets_menu)

        # LINGUAGEM
        self.btn_lang = QPushButton("🌐 Linguagem ▼")
        lang_menu = QMenu(self)
        lang_menu.setStyleSheet(notepad_menu_qss())
        lang_menu.addAction("🐍 Python", lambda: self._set_lang("python"))
        lang_menu.addAction("{ } JSON", lambda: self._set_lang("json"))
        lang_menu.addAction("🌐 HTML", lambda: self._set_lang("html"))
        lang_menu.addAction("🗄 SQL", lambda: self._set_lang("sql"))
        lang_menu.addAction("MD Markdown", lambda: self._set_lang("markdown"))
        lang_menu.addAction("# CSS", lambda: self._set_lang("css"))
        lang_menu.addAction("JS JavaScript", lambda: self._set_lang("javascript"))
        lang_menu.addSeparator()
        lang_menu.addAction("📄 Texto Simples", lambda: self._set_lang("text"))
        self.btn_lang.setMenu(lang_menu)

        # VISUAL / EDITOR
        self.btn_view = QPushButton("Visual v")
        view_menu = QMenu(self)
        view_menu.setStyleSheet(notepad_menu_qss())
        self.wrap_action = QAction("Quebra de linha", self)
        self.wrap_action.setCheckable(True)
        self.wrap_action.setChecked(True)
        self.wrap_action.toggled.connect(self.toggle_word_wrap)
        view_menu.addAction(self.wrap_action)
        self.programming_action = QAction("Realce de sintaxe", self)
        self.programming_action.setCheckable(True)
        self.programming_action.setChecked(True)
        self.programming_action.toggled.connect(self.toggle_programming_mode)
        view_menu.addAction(self.programming_action)
        view_menu.addSeparator()
        view_menu.addAction("Renomear aba", self.rename_current_tab)
        view_menu.addAction("Ir para linha", self.go_to_line)
        view_menu.addAction("Copiar caminho", self.copy_current_path)
        self.btn_view.setMenu(view_menu)

        # DIVISAO DE PAINEIS
        self.btn_layout = QPushButton("▥ Dividir ▼")
        layout_menu = QMenu(self)
        layout_menu.setStyleSheet(view_menu.styleSheet())
        layout_menu.addAction("1 painel", lambda: self.set_split_view(1))
        layout_menu.addAction("2 painéis lado a lado", lambda: self.set_split_view(2))
        layout_menu.addAction("3 painéis lado a lado", lambda: self.set_split_view(3))
        self.btn_layout.setMenu(layout_menu)

        self.btn_editor = QPushButton("Editor v")
        editor_menu = QMenu(self)
        editor_menu.setStyleSheet(view_menu.styleSheet())
        editor_menu.addAction("Duplicar linha/selecao", self.duplicate_line_or_selection)
        editor_menu.addAction("Comentar/descomentar", self.toggle_comment)
        editor_menu.addSeparator()
        editor_menu.addAction("Aumentar fonte", lambda: self.adjust_font_size(1))
        editor_menu.addAction("Diminuir fonte", lambda: self.adjust_font_size(-1))
        editor_menu.addAction("Fonte padrao", lambda: self.adjust_font_size(0, reset=True))
        self.btn_editor.setMenu(editor_menu)

        # TERMINAL toggle
        self.btn_terminal = QPushButton("⚡ Terminal")
        self.btn_terminal.setCheckable(True)
        self.btn_terminal.setChecked(False)
        self.btn_terminal.toggled.connect(self._toggle_terminal)
        self.btn_terminal.setStyleSheet(toolbar_toggle_qss())

        # MINI-MAPA toggle
        self.btn_minimap = QPushButton("🗺 Mini-Mapa")
        self.btn_minimap.setCheckable(True)
        self.btn_minimap.setChecked(False)
        self.btn_minimap.toggled.connect(self._toggle_minimap)
        self.btn_minimap.setStyleSheet(toolbar_toggle_qss())

        self.btn_tools = QPushButton("⚙ Ferramentas ▼")
        tools_menu = QMenu(self)
        tools_menu.setStyleSheet(view_menu.styleSheet())
        data_menu.setTitle("🧹 Dados")
        snippets_menu.setTitle("📌 Snippets")
        lang_menu.setTitle("🌐 Linguagem")
        editor_menu.setTitle("Editor")
        view_menu.setTitle("Visual")
        tools_menu.addMenu(data_menu)
        tools_menu.addMenu(snippets_menu)
        tools_menu.addMenu(lang_menu)
        tools_menu.addMenu(editor_menu)
        tools_menu.addMenu(view_menu)
        tools_menu.addSeparator()
        self.simple_mode_action = QAction("Modo simples", self)
        self.simple_mode_action.setCheckable(True)
        self.simple_mode_action.setChecked(True)
        self.simple_mode_action.toggled.connect(self.toggle_simple_mode)
        tools_menu.addAction(self.simple_mode_action)
        self.btn_tools.setMenu(tools_menu)

        toolbar_hbox.addWidget(self.btn_toggle_sidebar)
        toolbar_hbox.addWidget(self.btn_new)
        toolbar_hbox.addWidget(self.btn_open)
        toolbar_hbox.addWidget(self.btn_save)
        toolbar_hbox.addWidget(self.btn_search)
        toolbar_hbox.addWidget(self.btn_layout)
        toolbar_hbox.addWidget(self.btn_tools)
        toolbar_hbox.addSpacing(10)
        toolbar_hbox.addWidget(self.btn_data)
        toolbar_hbox.addWidget(self.btn_snippets)
        toolbar_hbox.addWidget(self.btn_lang)
        toolbar_hbox.addWidget(self.btn_editor)
        toolbar_hbox.addWidget(self.btn_view)
        toolbar_hbox.addStretch()
        toolbar_hbox.addWidget(self.btn_minimap)
        toolbar_hbox.addWidget(self.btn_terminal)
        self.main_layout.addWidget(self.toolbar)
        self.toggle_simple_mode(True)

        # BUSCA E SUBSTITUIÇÃO (original)
        self.search_frame = QFrame()
        self.search_frame.hide()
        self.search_frame.setStyleSheet(search_bar_qss())
        search_layout = QHBoxLayout(self.search_frame)
        search_layout.setContentsMargins(10, 6, 10, 6)
        search_layout.setSpacing(8)
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Localizar...")
        self.search_input.textChanged.connect(self.search_text)
        self.search_count_label = QLabel("")
        self.search_count_label.setStyleSheet(note_label_qss("search_count"))
        self.replace_input = QLineEdit()
        self.replace_input.setPlaceholderText("🔄 Substituir por...")
        self.search_case = QCheckBox("Aa")
        self.search_case.setToolTip("Diferenciar maiusculas/minusculas")
        self.search_case.toggled.connect(lambda: self.search_text(self.search_input.text()))
        self.search_regex = QCheckBox("Regex")
        self.search_regex.toggled.connect(lambda: self.search_text(self.search_input.text()))
        btn_prev = QPushButton("Anterior")
        btn_prev.clicked.connect(lambda: self.search_text(forward=False))
        btn_next = QPushButton("Proximo")
        btn_next.clicked.connect(lambda: self.search_text(forward=True))
        btn_rep = QPushButton("Substituir")
        btn_rep.clicked.connect(self.replace_text)
        btn_rep_all = QPushButton("Tudo")
        btn_rep_all.setToolTip("Substituir todas as ocorrencias")
        btn_rep_all.clicked.connect(self.replace_all_text)
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.search_count_label)
        search_layout.addWidget(self.search_case)
        search_layout.addWidget(self.search_regex)
        search_layout.addWidget(btn_prev)
        search_layout.addWidget(btn_next)
        search_layout.addWidget(self.replace_input)
        search_layout.addWidget(btn_rep)
        search_layout.addWidget(btn_rep_all)
        self.main_layout.addWidget(self.search_frame)

        # SPLITTER: sidebar | (tabs + minimap)
        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.setStyleSheet(splitter_qss(2))

        # Sidebar (original)
        self.sidebar = QFrame()
        self.sidebar.setFixedWidth(260)
        self.sidebar.setStyleSheet(sidebar_qss())
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(10, 15, 10, 10)
        lbl_explorer = QLabel("📂 EXPLORADOR")
        lbl_explorer.setStyleSheet(note_label_qss("section"))
        sidebar_layout.addWidget(lbl_explorer)

        self.folder_label = QLabel(self.current_folder)
        self.folder_label.setWordWrap(True)
        self.folder_label.setStyleSheet(note_label_qss("folder"))
        sidebar_layout.addWidget(self.folder_label)

        btn_open_folder = QPushButton("Pasta")
        btn_open_folder.setToolTip("Escolher pasta de trabalho")
        btn_open_folder.clicked.connect(self.open_folder)
        btn_open_folder.setStyleSheet(small_button_qss())
        sidebar_layout.addWidget(btn_open_folder)

        self.file_filter_input = QLineEdit()
        self.file_filter_input.setPlaceholderText("Filtrar arquivos...")
        self.file_filter_input.setStyleSheet(filter_input_qss())
        self.file_filter_input.textChanged.connect(self.refresh_file_list)
        sidebar_layout.addWidget(self.file_filter_input)

        self.file_list = QListWidget()
        self.file_list.setStyleSheet(file_list_qss())
        self.file_list.itemDoubleClicked.connect(self.open_sidebar_file)
        sidebar_layout.addWidget(self.file_list)
        btn_refresh = QPushButton("🔄 Atualizar Lista")
        btn_refresh.setStyleSheet(small_button_qss())
        btn_refresh.clicked.connect(self.refresh_file_list)
        sidebar_layout.addWidget(btn_refresh)
        self.splitter.addWidget(self.sidebar)

        # Centro: tabs + mini-mapa lado a lado
        self.center_widget = QWidget()
        self.center_layout = QHBoxLayout(self.center_widget)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(0)

        self.editor_splitter = QSplitter(Qt.Horizontal)
        self.editor_splitter.setStyleSheet(splitter_qss(3))
        self.tabs = self._create_tabs_pane()
        self.editor_panes = [self.tabs]
        self.editor_splitter.addWidget(self.tabs)
        self.center_layout.addWidget(self.editor_splitter)

        # Container do mini-mapa (slot fixo na direita)
        self.minimap_container = QFrame()
        self.minimap_container.setFixedWidth(82)
        self.minimap_container.setStyleSheet(minimap_qss())
        self.minimap_inner = QVBoxLayout(self.minimap_container)
        self.minimap_inner.setContentsMargins(0, 0, 0, 0)
        self.minimap_inner.setSpacing(0)
        self.minimap_container.setVisible(False)
        self.center_layout.addWidget(self.minimap_container)
        self.splitter.addWidget(self.center_widget)
        self.splitter.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        # Criar Splitter Vertical para separar Editor/Explorador do Terminal
        self.v_splitter = QSplitter(Qt.Vertical)
        self.v_splitter.addWidget(self.splitter)
        
        # TERMINAL
        self.terminal = TerminalWidget(self)
        self.v_splitter.addWidget(self.terminal)
        self.terminal.hide()
        
        # Adicionar o splitter vertical ao layout principal
        self.main_layout.addWidget(self.v_splitter, 1)

        # STATUS BAR (original + língua)
        self.status_bar = QFrame()
        self.status_bar.setFixedHeight(22) # Mais compacto
        self.status_bar.setStyleSheet(status_bar_qss())
        status_layout = QHBoxLayout(self.status_bar)
        self.status_pos_label = QLabel("Linha 1, Coluna 1")
        self.status_words_label = QLabel("0 palavras")
        self.status_lang_label = QLabel("🐍 Python")
        self.status_lang_label.setStyleSheet(note_label_qss("status_lang"))
        self.status_mode_label = QLabel("Ctrl+Scroll: Zoom")
        status_layout.addWidget(self.status_pos_label)
        status_layout.addSpacing(20)
        status_layout.addWidget(self.status_words_label)
        status_layout.addSpacing(20)
        status_layout.addWidget(self.status_lang_label)
        status_layout.addStretch()
        status_layout.addWidget(self.status_mode_label)
        self.main_layout.addWidget(self.status_bar)

        # Atalhos (originais + novos)
        QShortcut(QKeySequence("Ctrl+F"), self, self.toggle_search)
        QShortcut(QKeySequence("Ctrl+S"), self, self.save_current_tab)
        QShortcut(QKeySequence("Ctrl+N"), self, lambda: self.add_new_tab())
        QShortcut(QKeySequence("Ctrl+B"), self, self.toggle_sidebar)
        QShortcut(QKeySequence("Ctrl+T"), self, lambda: self.btn_terminal.toggle())
        QShortcut(QKeySequence("Ctrl+M"), self, lambda: self.btn_minimap.toggle())

    def _create_tabs_pane(self):
        tabs = QTabWidget()
        tabs.setTabsClosable(True)
        tabs.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        tabs.setMinimumHeight(100)
        tabs.setStyleSheet(tabs_qss())
        tabs.tabCloseRequested.connect(lambda index, pane=tabs: self.close_tab(index, pane))
        tabs.currentChanged.connect(lambda index, pane=tabs: self._on_tab_changed(index, pane))
        tabs.installEventFilter(self)
        return tabs

    def _all_panes(self):
        return [pane for pane in getattr(self, "editor_panes", []) if pane is not None]

    def _all_editors(self):
        for pane in self._all_panes():
            for index in range(pane.count()):
                editor = pane.widget(index)
                if editor:
                    yield pane, index, editor

    def _set_active_pane(self, pane):
        if pane in self._all_panes():
            self.tabs = pane

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.FocusIn, QEvent.MouseButtonPress):
            if isinstance(obj, QTabWidget):
                self._set_active_pane(obj)
            elif isinstance(obj, CodeEditor):
                for pane in self._all_panes():
                    if pane.indexOf(obj) >= 0:
                        self._set_active_pane(pane)
                        break
        return super().eventFilter(obj, event)

    def toggle_simple_mode(self, enabled):
        self.simple_mode_enabled = enabled
        advanced = [
            getattr(self, "btn_data", None),
            getattr(self, "btn_snippets", None),
            getattr(self, "btn_lang", None),
            getattr(self, "btn_editor", None),
            getattr(self, "btn_view", None),
            getattr(self, "btn_minimap", None),
            getattr(self, "btn_terminal", None),
        ]
        for button in advanced:
            if button:
                button.setVisible(not enabled)
        if enabled and hasattr(self, "btn_minimap") and self.btn_minimap.isChecked():
            self.btn_minimap.setChecked(False)
        if enabled and hasattr(self, "btn_terminal") and self.btn_terminal.isChecked():
            self.btn_terminal.setChecked(False)
        self._show_status("Modo simples ligado" if enabled else "Ferramentas visíveis")

    def set_split_view(self, count: int, create_blank: bool = True):
        count = max(1, min(3, int(count or 1)))
        while len(self.editor_panes) > count:
            pane = self.editor_panes.pop()
            while pane.count():
                widget = pane.widget(0)
                title = pane.tabText(0)
                pane.removeTab(0)
                self.editor_panes[0].addTab(widget, title)
            pane.setParent(None)
            pane.deleteLater()

        while len(self.editor_panes) < count:
            pane = self._create_tabs_pane()
            self.editor_panes.append(pane)
            self.editor_splitter.addWidget(pane)
            if create_blank:
                self.add_new_tab(name=f"Painel {len(self.editor_panes)}", content="", target_tabs=pane, lang="text")

        sizes = [1 for _ in self.editor_panes]
        self.editor_splitter.setSizes(sizes)
        self._set_active_pane(self.editor_panes[0])
        self._set_minimap_editor(self.tabs.currentWidget())
        self._show_status(f"Visual dividido em {count} painel(is)")

    # ── MINI-MAPA ────────────────────────────
    def _set_minimap_editor(self, editor):
        # Remove todos os widgets do container
        while self.minimap_inner.count():
            item = self.minimap_inner.takeAt(0)
            w = item.widget()
            if w and w.parent() == self.minimap_container:
                w.setParent(None)
        if editor and hasattr(editor, "_minimap"):
            mm = editor._minimap
            if mm is not None:
                mm.setParent(self.minimap_container)
                self.minimap_inner.addWidget(mm)
                mm.setVisible(self.btn_minimap.isChecked())
                mm.update()

    def _toggle_minimap(self, visible):
        self.minimap_container.setVisible(visible)
        # Atualiza minimap da aba atual
        editor = self.tabs.currentWidget()
        if editor and hasattr(editor, "_minimap") and editor._minimap is not None:
            editor._minimap.setVisible(visible)
            if visible:
                editor._minimap.update()

    def _on_tab_changed(self, index, pane=None):
        if pane is not None:
            self._set_active_pane(pane)
        pane = pane or self.tabs
        editor = pane.widget(index) if pane and index >= 0 else None
        self._set_minimap_editor(editor)
        self.update_status()
        self._update_lang_label()

    # ── TERMINAL ─────────────────────────────
    def _toggle_terminal(self, visible):
        self.terminal.setVisible(visible)
        if visible:
            self.terminal.cmd_input.setFocus()
            # Ajustar proporção para o terminal não ocupar a tela toda (ex: 70% editor, 30% terminal)
            self.v_splitter.setSizes([int(self.height() * 0.7), int(self.height() * 0.3)])
        else:
            # Ao esconder, dar todo o espaço para o editor
            self.v_splitter.setSizes([self.height(), 0])

    # ── LINGUAGEM ────────────────────────────
    def _set_lang(self, lang):
        editor = self.tabs.currentWidget()
        if editor:
            editor.set_language(lang)
            self._update_lang_label()
            labels = {
                "python": "Python", "json": "JSON", "html": "HTML", "sql": "SQL",
                "markdown": "Markdown", "css": "CSS", "javascript": "JavaScript",
                "text": "Texto"
            }
            self._show_status("Linguagem: " + labels.get(lang, lang))

    def _update_lang_label(self):
        editor = self.tabs.currentWidget()
        if editor:
            lang = getattr(editor, "_language", "python")
            labels = {"python": "🐍 Python", "json": "{ } JSON", "html": "🌐 HTML",
                      "sql": "🗄 SQL", "text": "📄 Texto"}
            labels.update({
                "markdown": "MD Markdown", "css": "# CSS",
                "javascript": "JS JavaScript"
            })
            self.status_lang_label.setText(labels.get(lang, lang))

    def _detect_lang(self, filename):
        ext = os.path.splitext(filename)[1].lower()
        return {
            ".py": "python", ".json": "json", ".html": "html", ".htm": "html",
            ".sql": "sql", ".md": "markdown", ".markdown": "markdown",
            ".css": "css", ".js": "javascript", ".mjs": "javascript",
            ".cjs": "javascript"
        }.get(ext, "text")

    # ── SIDEBAR ──────────────────────────────
    def toggle_sidebar(self):
        self.sidebar.setVisible(not self.sidebar.isVisible())
        self.btn_toggle_sidebar.setText("📁" if self.sidebar.isVisible() else "📂")

    # ── DADOS ────────────────────────────────
    def remove_duplicates(self):
        editor = self.tabs.currentWidget()
        if editor:
            lines = editor.toPlainText().split("\n")
            seen = set()
            unique = [x for x in lines if not (x in seen or seen.add(x))]
            editor.setPlainText("\n".join(unique))
            self._show_status("Duplicados removidos")

    def sort_lines(self, reverse=False):
        editor = self.tabs.currentWidget()
        if editor:
            lines = editor.toPlainText().split("\n")
            lines.sort(key=str.lower, reverse=reverse)
            editor.setPlainText("\n".join(lines))
            self._show_status("Linhas ordenadas")

    def remove_empty_lines(self):
        editor = self.tabs.currentWidget()
        if editor:
            lines = [l for l in editor.toPlainText().split("\n") if l.strip()]
            editor.setPlainText("\n".join(lines))
            self._show_status("Linhas vazias removidas")

    def _target_text(self):
        editor = self.tabs.currentWidget()
        if not editor:
            return None, None, False
        cursor = editor.textCursor()
        if cursor.hasSelection():
            return cursor.selectedText().replace("\u2029", "\n"), cursor, True
        return editor.toPlainText(), cursor, False

    def _replace_target_text(self, new_text, cursor=None, selected=False):
        editor = self.tabs.currentWidget()
        if not editor:
            return
        if selected and cursor:
            cursor.insertText(new_text)
        else:
            old_cursor = editor.textCursor()
            editor.setPlainText(new_text)
            editor.setTextCursor(old_cursor)

    def trim_lines(self):
        text, cursor, selected = self._target_text()
        if text is None:
            return
        self._replace_target_text("\n".join(line.strip() for line in text.splitlines()), cursor, selected)
        self._show_status("Espacos aparados")

    def normalize_spaces(self):
        text, cursor, selected = self._target_text()
        if text is None:
            return
        lines = [re.sub(r"[ \t]+", " ", line.strip()) for line in text.splitlines()]
        self._replace_target_text("\n".join(lines), cursor, selected)
        self._show_status("Espacos normalizados")

    def reverse_lines(self):
        text, cursor, selected = self._target_text()
        if text is None:
            return
        self._replace_target_text("\n".join(reversed(text.splitlines())), cursor, selected)
        self._show_status("Linhas invertidas")

    def transform_text(self, mode):
        text, cursor, selected = self._target_text()
        if text is None:
            return
        if mode == "upper":
            new_text = text.upper()
        elif mode == "lower":
            new_text = text.lower()
        else:
            new_text = text.title()
        self._replace_target_text(new_text, cursor, selected)
        self._show_status("Texto transformado")

    def format_json(self):
        text, cursor, selected = self._target_text()
        if text is None:
            return
        try:
            obj = json.loads(text)
            self._replace_target_text(json.dumps(obj, ensure_ascii=False, indent=4), cursor, selected)
            self._set_lang("json")
            self._show_status("JSON formatado")
        except Exception as e:
            QMessageBox.warning(self, "JSON", "Nao foi possivel formatar JSON:\n" + str(e))

    def minify_json(self):
        text, cursor, selected = self._target_text()
        if text is None:
            return
        try:
            obj = json.loads(text)
            self._replace_target_text(json.dumps(obj, ensure_ascii=False, separators=(",", ":")), cursor, selected)
            self._set_lang("json")
            self._show_status("JSON minificado")
        except Exception as e:
            QMessageBox.warning(self, "JSON", "Nao foi possivel minificar JSON:\n" + str(e))

    def extract_pattern(self, pattern):
        editor = self.tabs.currentWidget()
        if editor:
            matches = re.findall(pattern, editor.toPlainText())
            if matches:
                self.add_new_tab("Extração", "\n".join(matches))
            else:
                QMessageBox.information(self, "Aviso", "Nenhum padrão encontrado.")

    # ── EXPLORADOR ───────────────────────────
    def open_folder(self):
        path = QFileDialog.getExistingDirectory(self, "Escolher pasta", self.current_folder)
        if path:
            self.current_folder = path
            self.folder_label.setText(path)
            self.refresh_file_list()
            self._show_status("Pasta: " + path)

    def refresh_file_list(self):
        self.file_list.clear()
        try:
            exts = (".txt", ".py", ".json", ".log", ".md", ".csv", ".html", ".htm",
                    ".sql", ".css", ".js", ".xml", ".yml", ".yaml")
            query = ""
            if hasattr(self, "file_filter_input"):
                query = self.file_filter_input.text().strip().lower()
            found = 0
            for root, dirs, files in os.walk(self.current_folder):
                dirs[:] = [d for d in dirs if d not in ("__pycache__", ".git", "venv", ".venv", "node_modules")]
                for f in sorted(files):
                    if not f.lower().endswith(exts):
                        continue
                    full_path = os.path.join(root, f)
                    rel_path = os.path.relpath(full_path, self.current_folder)
                    if query and query not in rel_path.lower():
                        continue
                    item = QListWidgetItem(rel_path)
                    item.setToolTip(full_path)
                    item.setData(Qt.UserRole, full_path)
                    self.file_list.addItem(item)
                    found += 1
                    if found >= 600:
                        self._show_status("Mostrando os primeiros 600 arquivos")
                        return
        except Exception as e:
            self._show_status("Erro no explorador: " + str(e))

    def open_sidebar_file(self, item):
        filename = item.data(Qt.UserRole) or os.path.join(self.current_folder, item.text())
        try:
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            lang = self._detect_lang(filename)
            self.add_new_tab(os.path.basename(filename), content, os.path.abspath(filename), lang=lang)
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    # ── SESSÃO / AUTOSAVE (original + lang) ──
    def setup_autosave(self):
        self.autosave_timer = QTimer(self)
        self.autosave_timer.timeout.connect(self.save_session)
        self.autosave_timer.start(10000)

    def _is_project_internal_file(self, file_path):
        if not file_path:
            return False
        try:
            path = os.path.abspath(file_path)
            base = os.path.abspath(str(BASE_DIR))
            if os.path.commonpath([base, path]) != base:
                return False
            rel = os.path.relpath(path, base)
            first = rel.split(os.sep, 1)[0].lower()
            blocked_dirs = {
                "app", "archive", "backups", "browser_config", "browser_extensions",
                "browser_profiles", "crunchyroll_bot", "paramount_bot", "scripts",
                "venv", ".venv", "__pycache__",
            }
            if first in blocked_dirs:
                return True
            blocked_exts = {".py", ".pyc", ".js", ".json", ".css", ".html", ".htm", ".xml", ".yml", ".yaml"}
            return os.path.splitext(path)[1].lower() in blocked_exts
        except Exception:
            return False

    def _should_persist_session_tab(self, name, content, file_path):
        if file_path and self._is_project_internal_file(file_path):
            return False
        if not file_path and not str(content or "").strip():
            clean_name = str(name or "").lstrip("● ").strip().lower()
            return clean_name not in {"sem título", "sem titulo", "painel 2", "painel 3"}
        return True

    def _session_item_from_editor(self, pane, index):
        editor = pane.widget(index)
        tab_title = pane.tabText(index)
        if tab_title.startswith("● "):
            tab_title = tab_title[2:]
        tab_title = tab_title.strip()
        content = editor.toPlainText()
        file_path = editor.file_path
        if not self._should_persist_session_tab(tab_title, content, file_path):
            return None
        return {
            "name": tab_title,
            "content": content,
            "file_path": file_path,
            "language": getattr(editor, "_language", "python"),
        }

    def save_session(self):
        active_index = self.editor_panes.index(self.tabs) if self.tabs in self.editor_panes else 0
        session_data = {
            "version": 2,
            "pane_count": len(self.editor_panes),
            "active_pane_index": active_index,
            "panes": [],
            "current_index": self.tabs.currentIndex() if self.tabs else 0,
            "tabs": [],
        }
        for pane in self._all_panes():
            pane_data = {"current_index": pane.currentIndex(), "tabs": []}
            for i in range(pane.count()):
                item = self._session_item_from_editor(pane, i)
                if not item:
                    continue
                pane_data["tabs"].append(item)
                if pane is self.editor_panes[0]:
                    session_data["tabs"].append(item)
            session_data["panes"].append(pane_data)
        try:
            with open(SESSION_FILE, "w", encoding="utf-8") as f:
                json.dump(session_data, f, ensure_ascii=False, indent=4)
        except:
            pass

    def load_session(self):
        if os.path.exists(SESSION_FILE):
            try:
                with open(SESSION_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                filtered_session = False
                if data.get("panes"):
                    panes_data = data.get("panes", [])[:3]
                    self.set_split_view(max(1, len(panes_data)), create_blank=False)
                    for pane, pane_data in zip(self.editor_panes, panes_data):
                        for tab in pane_data.get("tabs", []):
                            if not self._should_persist_session_tab(
                                tab.get("name", "Sem título"),
                                tab.get("content", ""),
                                tab.get("file_path"),
                            ):
                                filtered_session = True
                                continue
                            self.add_new_tab(
                                name=tab.get("name", "Sem título"),
                                content=tab.get("content", ""),
                                file_path=tab.get("file_path"),
                                lang=tab.get("language", "python"),
                                target_tabs=pane,
                            )
                        if pane.count() == 0:
                            self.add_new_tab(target_tabs=pane)
                        pane.setCurrentIndex(min(pane_data.get("current_index", 0), max(0, pane.count() - 1)))
                    active = min(data.get("active_pane_index", 0), len(self.editor_panes) - 1)
                    self._set_active_pane(self.editor_panes[active])
                    self._set_minimap_editor(self.tabs.currentWidget())
                    if filtered_session:
                        QTimer.singleShot(0, self.save_session)
                    return
                if data.get("tabs"):
                    for tab in data["tabs"]:
                        if not self._should_persist_session_tab(
                            tab.get("name", "Sem título"),
                            tab.get("content", ""),
                            tab.get("file_path"),
                        ):
                            filtered_session = True
                            continue
                        self.add_new_tab(
                            name=tab["name"],
                            content=tab["content"],
                            file_path=tab["file_path"],
                            lang=tab.get("language", "python"),
                        )
                    if self.tabs.count() == 0:
                        self.add_new_tab()
                    self.tabs.setCurrentIndex(data.get("current_index", 0))
                    if filtered_session:
                        QTimer.singleShot(0, self.save_session)
                    return
            except:
                pass
        self.add_new_tab()

    # ── BUSCA ────────────────────────────────
    def toggle_search(self):
        if self.search_frame.isVisible():
            self.search_frame.hide()
        else:
            self.search_frame.show()
            self.search_input.setFocus()
            self.search_input.selectAll()

    def search_text(self, text=None, forward=True):
        if text is None:
            text = self.search_input.text()
        editor = self.tabs.currentWidget()
        if not editor or not text:
            self.search_count_label.setText("")
            return
        content = editor.toPlainText()
        count = len(re.findall(re.escape(text), content, re.IGNORECASE))
        self.search_count_label.setText(f"{count} resultado(s)" if count else "Não encontrado")
        # QPlainTextEdit.find() aceita QTextDocument.FindFlags (int)
        # FindBackward = 4 em Qt
        from PyQt5.QtGui import QTextDocument
        flag = QTextDocument.FindBackward if not forward else QTextDocument.FindFlags()
        if not editor.find(text, flag):
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start if forward else QTextCursor.End)
            editor.setTextCursor(cursor)
            editor.find(text, flag)

    def replace_text(self):
        editor = self.tabs.currentWidget()
        s_term, r_term = self.search_input.text(), self.replace_input.text()
        if editor and s_term:
            cursor = editor.textCursor()
            if cursor.hasSelection() and cursor.selectedText().lower() == s_term.lower():
                cursor.insertText(r_term)
            self.search_text(s_term, forward=True)

    # ── ABAS ─────────────────────────────────
    def replace_all_text(self):
        editor = self.tabs.currentWidget()
        if not editor:
            return
        s_term = self.search_input.text()
        r_term = self.replace_input.text()
        if not s_term:
            return
        flags = 0 if self.search_case.isChecked() else re.IGNORECASE
        pattern = s_term if self.search_regex.isChecked() else re.escape(s_term)
        try:
            new_text, count = re.subn(pattern, lambda _: r_term, editor.toPlainText(), flags=flags)
        except re.error as e:
            QMessageBox.warning(self, "Busca", "Regex invalido:\n" + str(e))
            return
        if count:
            editor.setPlainText(new_text)
        self._show_status(f"{count} ocorrencia(s) substituida(s)")

    def toggle_word_wrap(self, enabled):
        self.word_wrap_enabled = enabled
        for _, _, editor in self._all_editors():
            editor.set_word_wrap(enabled)
        self._show_status("Quebra de linha ligada" if enabled else "Quebra de linha desligada")

    def rename_current_tab(self):
        index = self.tabs.currentIndex()
        if index < 0:
            return
        current = self.tabs.tabText(index).lstrip("● ").strip()
        name, ok = QInputDialog.getText(self, "Renomear aba", "Nome:", text=current)
        if ok and name.strip():
            prefix = "● " if self.tabs.widget(index).is_modified else ""
            self.tabs.setTabText(index, prefix + name.strip())
            self.save_session()

    def go_to_line(self):
        editor = self.tabs.currentWidget()
        if not editor:
            return
        max_line = max(1, editor.blockCount())
        line, ok = QInputDialog.getInt(self, "Ir para linha", "Linha:", 1, 1, max_line, 1)
        if ok:
            cursor = editor.textCursor()
            cursor.movePosition(QTextCursor.Start)
            cursor.movePosition(QTextCursor.Down, QTextCursor.MoveAnchor, line - 1)
            editor.setTextCursor(cursor)
            editor.setFocus()

    def copy_current_path(self):
        editor = self.tabs.currentWidget()
        if editor and editor.file_path:
            QApplication.clipboard().setText(editor.file_path)
            self._show_status("Caminho copiado")
        else:
            self._show_status("A aba atual ainda nao tem arquivo")

    def duplicate_line_or_selection(self):
        editor = self.tabs.currentWidget()
        if not editor:
            return
        cursor = editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText().replace("\u2029", "\n")
            cursor.insertText(text + text)
        else:
            cursor.select(QTextCursor.LineUnderCursor)
            text = cursor.selectedText()
            cursor.movePosition(QTextCursor.EndOfLine)
            cursor.insertText("\n" + text)
        self._show_status("Linha/selecao duplicada")

    def toggle_comment(self):
        editor = self.tabs.currentWidget()
        if not editor:
            return
        lang = getattr(editor, "_language", "text")
        marker = "--" if lang == "sql" else ("//" if lang in ("javascript", "css") else "#")
        cursor = editor.textCursor()
        if cursor.hasSelection():
            text = cursor.selectedText().replace("\u2029", "\n")
            lines = text.splitlines()
            uncomment = all((not line.strip()) or line.lstrip().startswith(marker) for line in lines)
            new_lines = []
            for line in lines:
                if uncomment:
                    idx = line.find(marker)
                    new_lines.append(line[:idx] + line[idx + len(marker):].lstrip() if idx >= 0 else line)
                else:
                    new_lines.append(marker + " " + line)
            cursor.insertText("\n".join(new_lines))
        else:
            cursor.select(QTextCursor.LineUnderCursor)
            line = cursor.selectedText()
            stripped = line.lstrip()
            indent = line[:len(line) - len(stripped)]
            if stripped.startswith(marker):
                cursor.insertText(indent + stripped[len(marker):].lstrip())
            else:
                cursor.insertText(indent + marker + " " + stripped)
        self._show_status("Comentario alternado")

    def adjust_font_size(self, delta, reset=False):
        editor = self.tabs.currentWidget()
        if not editor:
            return
        editor.current_font_size = 14 if reset else max(6, min(32, editor.current_font_size + delta))
        editor.update_font()
        self._show_status(f"Fonte: {editor.current_font_size}px")
    def add_new_tab(self, checked=False, name="Sem título", content="", file_path=None, lang=None, target_tabs=None):
        if isinstance(checked, str):
            file_path, content, name = content, name, checked
        if not isinstance(name, str):
            name = "Sem título"

        pane = target_tabs if target_tabs is not None else (self.tabs if self.tabs is not None else (self.editor_panes[0] if self.editor_panes else None))
        if pane is None:
            return None
        self._set_active_pane(pane)
        editor = CodeEditor()
        editor.setPlainText(content)
        editor.file_path = file_path

        if lang is None:
            if file_path:
                lang = self._detect_lang(file_path)
            elif name != "Sem título":
                lang = self._detect_lang(name)
            else:
                lang = "python"
        editor.set_language(lang)
        editor.set_word_wrap(self.word_wrap_enabled)
        if not self.programming_mode_enabled:
            editor.set_programming_mode(False)
        editor.installEventFilter(self)

        # Mini-mapa vinculado
        mm = MiniMap(editor)
        editor._minimap = mm
        editor.document().contentsChanged.connect(mm.update)
        editor.verticalScrollBar().valueChanged.connect(lambda _, m=mm: m.update())

        editor.cursorPositionChanged.connect(self.update_status)
        editor.document().contentsChanged.connect(lambda e=editor: self._mark_tab_modified(e))

        index = pane.addTab(editor, name)
        pane.setCurrentIndex(index)
        editor.is_modified = False
        self._update_lang_label()
        return editor

    def _mark_tab_modified(self, editor=None):
        if editor is None:
            editor = self.tabs.currentWidget() if self.tabs else None
        for pane in self._all_panes():
            index = pane.indexOf(editor)
            if index >= 0:
                current_text = pane.tabText(index)
                if not current_text.startswith("●"):
                    pane.setTabText(index, "● " + current_text)
                return

    def close_tab(self, index, pane=None):
        pane = pane or self.tabs
        self._set_active_pane(pane)
        editor = pane.widget(index)
        if editor and editor.is_modified:
            name = pane.tabText(index).lstrip("● ").strip()
            reply = QMessageBox.question(
                self, "Salvar?",
                f'"{name}" tem alterações. Salvar?',
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )
            if reply == QMessageBox.Cancel:
                return
            if reply == QMessageBox.Save:
                pane.setCurrentIndex(index)
                self.save_current_tab()
        if hasattr(editor, "_minimap"):
            editor._minimap.setParent(None)
        if pane.count() > 1:
            pane.removeTab(index)
            # Força atualização do mini-mapa para a aba agora ativa
            curr = pane.currentWidget()
            if curr:
                self._set_minimap_editor(curr)
        else:
            pane.widget(0).setPlainText("")
            pane.setTabText(0, "Sem título")
            pane.widget(0).file_path = None
        self.save_session()

    # ── ARQUIVOS ─────────────────────────────
    def open_file(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Abrir Arquivo", "",
            "Arquivos de Código (*.txt *.py *.json *.log *.md *.csv *.html *.htm *.sql);;Todos (*)"
        )
        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    content = f.read()
                lang = self._detect_lang(path)
                self.add_new_tab(os.path.basename(path), content, path, lang=lang)
                self._fix_tab_title()
            except Exception as e:
                QMessageBox.critical(self, "Erro", str(e))

    def save_current_tab(self):
        editor = self.tabs.currentWidget()
        if not editor:
            return
        if not editor.file_path:
            self.save_as_current_tab()
            return
        self._do_save(editor)

    def save_as_current_tab(self):
        editor = self.tabs.currentWidget()
        if not editor:
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Salvar Como", "novo.txt",
            "Arquivos de Texto (*.txt *.py *.json *.log *.md *.html *.sql);;Todos (*)"
        )
        if path:
            editor.file_path = path
            self.tabs.setTabText(self.tabs.currentIndex(), os.path.basename(path))
            self._do_save(editor)

    def save_all_tabs(self):
        current_pane = self.tabs
        current_indexes = {pane: pane.currentIndex() for pane in self._all_panes()}
        for pane in self._all_panes():
            self._set_active_pane(pane)
            for i in range(pane.count()):
                pane.setCurrentIndex(i)
                self.save_current_tab()
        for pane, index in current_indexes.items():
            if pane.count():
                pane.setCurrentIndex(min(index, pane.count() - 1))
        self._set_active_pane(current_pane)

    def _do_save(self, editor):
        try:
            with open(editor.file_path, "w", encoding="utf-8") as f:
                f.write(editor.toPlainText())
            editor.is_modified = False
            # Remove o marcador "●" da aba correta
            for pane, i, pane_editor in self._all_editors():
                if pane_editor is editor:
                    title = pane.tabText(i)
                    if title.startswith("● "):
                        pane.setTabText(i, title[2:].strip())
                    break
            self.save_session()
            self.refresh_file_list()
            self._show_status("Salvo: " + os.path.basename(editor.file_path))
        except Exception as e:
            QMessageBox.critical(self, "Erro", str(e))

    def _fix_tab_title(self):
        idx = self.tabs.currentIndex()
        if idx >= 0:
            self.tabs.setTabText(idx, self.tabs.tabText(idx).lstrip("● ").strip())

    def toggle_programming_mode(self, enabled):
        self.programming_mode_enabled = enabled
        for _, _, editor in self._all_editors():
            editor.set_programming_mode(enabled)
        self._show_status("Realce de sintaxe ligado" if enabled else "Realce de sintaxe desligado")

    # ── STATUS ───────────────────────────────
    def update_status(self):
        editor = self.tabs.currentWidget()
        if editor:
            cursor = editor.textCursor()
            text = editor.toPlainText()
            self.status_pos_label.setText(
                f"Linha {cursor.blockNumber() + 1}, Coluna {cursor.columnNumber() + 1}"
            )
            self.status_words_label.setText(
                f"{len(text.split())} palavras | {len(text)} chars"
            )

    def _show_status(self, msg, duration=3000):
        if not hasattr(self, "status_mode_label"):
            return
        self.status_mode_label.setText(msg)
        QTimer.singleShot(duration, lambda: self.status_mode_label.setText("Ctrl+Scroll: Zoom"))


