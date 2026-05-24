import re

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.ui.components import (
    PALETTE,
    button_qss,
    field_qss,
    group_qss,
    label_qss,
    make_button,
    table_qss,
)


class DataOrganizer(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        self.setStyleSheet(field_qss() + group_qss() + table_qss())

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)

        header = QGroupBox("Organizador")
        header_layout = QVBoxLayout(header)
        header_layout.setContentsMargins(14, 14, 14, 14)
        title = QLabel("Organizador de Dados")
        title.setStyleSheet(label_qss("title"))
        subtitle = QLabel("Cole listas de contas, cartoes ou texto solto e gere uma saida limpa para uso rapido.")
        subtitle.setStyleSheet(label_qss("subtitle"))
        header_layout.addWidget(title)
        header_layout.addWidget(subtitle)
        layout.addWidget(header)

        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet("QSplitter::handle{background:transparent;width:8px;}")

        input_group = QGroupBox("Entrada")
        input_layout = QVBoxLayout(input_group)
        input_layout.setContentsMargins(14, 18, 14, 14)
        input_layout.setSpacing(8)

        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText(
            "Cole sua lista aqui...\n"
            "Exemplos:\n"
            "4066699928138769|01|2028|345\n"
            "email@exemplo.com:senha123"
        )
        self.input_text.setStyleSheet(field_qss())
        input_layout.addWidget(self.input_text, 1)

        splitter.addWidget(input_group)

        output_group = QGroupBox("Resultado")
        output_layout = QVBoxLayout(output_group)
        output_layout.setContentsMargins(14, 18, 14, 14)
        output_layout.setSpacing(8)

        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setPlaceholderText("O resultado aparece aqui.")
        self.output_text.setStyleSheet(
            field_qss()
            + f"""
            QTextEdit {{
                color: {PALETTE.success};
                font-family: Consolas, 'Cascadia Code', monospace;
                font-size: 12px;
            }}
            """
        )
        output_layout.addWidget(self.output_text, 1)

        splitter.addWidget(output_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, 1)

        controls = QGroupBox("Saida")
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(14, 18, 14, 14)
        controls_layout.setSpacing(10)

        fmt_label = QLabel("Formato")
        fmt_label.setStyleSheet(label_qss("section"))
        controls_layout.addWidget(fmt_label)

        self.format_combo = QComboBox()
        self.format_combo.addItems([
            "Original",
            "Simples (Pipe |)",
            "Agrupado por Tag",
            "Detalhado",
        ])
        self.format_combo.setStyleSheet(field_qss(compact=True))
        controls_layout.addWidget(self.format_combo, 1)

        self.status_label = QLabel("Pronto")
        self.status_label.setStyleSheet(label_qss("muted"))
        controls_layout.addWidget(self.status_label)

        process_btn = make_button("Processar", "success", "lg")
        process_btn.clicked.connect(self.process_data)
        controls_layout.addWidget(process_btn)

        copy_btn = make_button("Copiar", "primary", "lg")
        copy_btn.clicked.connect(self.copy_result)
        controls_layout.addWidget(copy_btn)

        clear_btn = make_button("Limpar", "danger", "lg")
        clear_btn.clicked.connect(self.clear_fields)
        controls_layout.addWidget(clear_btn)

        layout.addWidget(controls)

    def parse_line(self, line):
        line = line.strip()
        if not line:
            return None

        card_data = {}
        tag_match = re.match(r"^(anime|n foi|prime|sem cor|outros|vinculado|vinvulado|live)\s+", line, re.IGNORECASE)
        if tag_match:
            card_data["tag"] = tag_match.group(1).lower()
            line = line[tag_match.end():]
        else:
            card_data["tag"] = "sem tag"

        card_match = re.search(r"(\d{13,19})", line)
        if card_match:
            card_data["number"] = card_match.group(1)
            line_without_card = line.replace(card_data["number"], "")
            date_match = re.search(r"(\d{2})[\|/\s](\d{2,4})[\|/\s](\d{3,4})", line_without_card)
            if date_match:
                year = date_match.group(2)
                if len(year) == 2:
                    year = f"20{year}"
                card_data["month"] = date_match.group(1)
                card_data["year"] = year
                card_data["cvv"] = date_match.group(3)
                card_data["type"] = "card"
                return card_data

        return {"type": "text", "content": line}

    def process_data(self):
        raw_text = self.input_text.toPlainText()
        if not raw_text.strip():
            QMessageBox.warning(self, "Organizador", "Cole dados antes de processar.")
            return

        lines = [line for line in raw_text.splitlines() if line.strip()]
        parsed_data = [self.parse_line(line) for line in lines]
        parsed_data = [item for item in parsed_data if item]

        result = self._format_items(parsed_data, self.format_combo.currentText())
        self.output_text.setPlainText(result)
        cards = sum(1 for item in parsed_data if item["type"] == "card")
        texts = len(parsed_data) - cards
        self.status_label.setText(f"{len(parsed_data)} linhas | {cards} cartoes | {texts} textos")

    def _format_items(self, parsed_data, output_format):
        if output_format == "Simples (Pipe |)":
            return "".join(self._format_simple(item) for item in parsed_data)

        if output_format == "Agrupado por Tag":
            grouped = {}
            others = []
            for item in parsed_data:
                if item["type"] == "card":
                    grouped.setdefault(item.get("tag", "sem tag"), []).append(item)
                else:
                    others.append(item)

            result = []
            for tag in sorted(grouped.keys()):
                result.append(f"\ngrupo {tag}\n")
                result.extend(self._format_simple(item) for item in grouped[tag])
            if others:
                result.append("\nOutros\n")
                result.extend(f"{item['content']}\n" for item in others)
            return "".join(result).strip()

        if output_format == "Detalhado":
            blocks = []
            for index, item in enumerate(parsed_data, start=1):
                if item["type"] == "card":
                    blocks.append(
                        f"#{index:02d}\n"
                        f"Cartao: {item['number']}\n"
                        f"Validade: {item['month']}/{item['year']}\n"
                        f"CVV: {item['cvv']}\n"
                        f"Tag: {item.get('tag', 'sem tag')}\n"
                    )
                else:
                    blocks.append(f"#{index:02d}\nTexto: {item['content']}\n")
            return "\n".join(blocks).strip()

        return "".join(self._format_simple(item, include_tag=True) for item in parsed_data).strip()

    def _format_simple(self, item, include_tag=False):
        if item["type"] == "card":
            tag = f"{item.get('tag', 'sem tag')} " if include_tag and item.get("tag") != "sem tag" else ""
            return f"{tag}{item['number']}|{item['month']}|{item['year']}|{item['cvv']}\n"
        return f"{item['content']}\n"

    def clear_fields(self):
        self.input_text.clear()
        self.output_text.clear()
        self.status_label.setText("Pronto")

    def copy_result(self):
        text = self.output_text.toPlainText().strip()
        if not text:
            QMessageBox.information(self, "Organizador", "Nao ha resultado para copiar.")
            return
        QApplication.clipboard().setText(text)
        self.status_label.setText("Resultado copiado")
