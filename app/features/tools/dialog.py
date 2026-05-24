#!/usr/bin/env python3
"""Dialogo auxiliar que constroi as abas de ferramentas."""

import re
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QButtonGroup, QComboBox, QDialog, QFileDialog, QFrame, QGridLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QProgressBar, QPushButton,
    QRadioButton, QScrollArea, QSizePolicy, QSpinBox, QTabWidget, QTextEdit, QVBoxLayout, QWidget,
)

from account_formatter import AccountFormatter
from address_generator import AddressGenerator
from card_generator import CardGenerator
from data_organizer import DataOrganizer
from extra_tools import ValidadorWidget
from app.core.worker_threads import AddressGeneratorThread, CardGeneratorThread
from app.ui.components import card_qss, label_qss
from app.features.tools.styles import (
    TOOL_DIALOG_QSS, TOOL_TABS_QSS, tool_analysis_qss, tool_button_qss, tool_field_qss,
    tool_group_qss, tool_inline_label_qss, tool_light_copy_button_qss,
    tool_light_result_field_qss, tool_output_qss, tool_progress_qss, tool_radio_qss,
    tool_result_field_qss, tool_scroll_area_qss, tool_stat_tile_qss, tool_status_qss,
    tool_tab_qss,
)
from app.ui.shell_widgets import _set_clipboard_text_safe
from theme import DARK_STYLE_PRO as DARK_STYLE, LIGHT_STYLE_PRO as LIGHT_STYLE

class ToolsDialog(QDialog):
    """Diálogo de Ferramentas com Gerador de Cartões e CEP - v4.2 com Modo Claro/Escuro"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Ferramentas")
        self.setModal(False)  # Não bloqueia a janela principal
        self.setMinimumSize(980, 720)
        
        # Estado do tema
        self.is_dark_mode = True
        self.setStyleSheet(TOOL_DIALOG_QSS)
        
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
        """Alterna entre modo claro e escuro."""
        self.is_dark_mode = not self.is_dark_mode
        if self.is_dark_mode:
            self.setStyleSheet(TOOL_DIALOG_QSS)
            self.theme_btn.setText("Modo claro")
        else:
            self.setStyleSheet(LIGHT_STYLE)
            self.theme_btn.setText("Modo escuro")

        self.update_cep_field_styles()

    def update_cep_field_styles(self):
        """Atualiza os estilos dos campos de resultado do CEP."""
        if self.is_dark_mode:
            field_style = tool_result_field_qss()
            copy_btn_style = self._tool_button_style("ghost")
        else:
            field_style = tool_light_result_field_qss()
            copy_btn_style = tool_light_copy_button_qss()

        for field_name in (
            "full_address_field", "cep_field", "endereco_field", "numero_field",
            "bairro_field", "cidade_field", "estado_field", "uf_field",
        ):
            field = getattr(self, field_name, None)
            if field:
                field.setStyleSheet(field_style)
        for button_name in (
            "copy_cep_btn", "copy_endereco_btn", "copy_numero_btn", "copy_bairro_btn",
            "copy_cidade_btn", "copy_estado_btn", "copy_uf_btn",
        ):
            button = getattr(self, button_name, None)
            if button:
                button.setStyleSheet(copy_btn_style)

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setSpacing(14)
        main_layout.setContentsMargins(18, 18, 18, 18)
        
        # Header com título e botão de tema
        header_layout = QHBoxLayout()
        
        # Título - Estilo Apple
        title = QLabel("Ferramentas")
        title.setFont(QFont('Segoe UI', 20, QFont.Bold))
        title.setStyleSheet(label_qss('title'))
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Botão de alternar tema
        self.theme_btn = QPushButton("Modo claro")
        self.theme_btn.setStyleSheet(tool_button_qss("secondary", "sm"))
        self.theme_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.theme_btn)
        
        main_layout.addLayout(header_layout)
        
        # Tabs de ferramentas - Estilo Apple
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(TOOL_TABS_QSS)
        
        # Aba do Gerador de Cartões
        card_tab = self.create_card_generator_tab()
        self.tabs.addTab(card_tab, "💳 Gerador de Cartões")
        
        # Aba do Gerador de CEP (novo layout)
        address_tab = self.create_cep_generator_tab()
        self.tabs.addTab(address_tab, "🏠 Gerador de CEP")
        
        # Aba do Organizador de Contas Premium
        accounts_tab = self.create_account_formatter_tab()
        self.tabs.addTab(accounts_tab, "📧 Organizador de Contas")

        # Aba do Formatador de Dados
        organizer_tab = DataOrganizer()
        self.tabs.addTab(organizer_tab, "🗂️ Formatar Dados")
        
        # === NOVAS FERRAMENTAS v8.0 ===
        
        # Aba do Validador de CPF/CNPJ
        validador_tab = ValidadorWidget()
        self.tabs.addTab(validador_tab, "✅ Validador")
        
        main_layout.addWidget(self.tabs)
        self.setLayout(main_layout)

    def _tool_header(self, title: str, subtitle: str, accent: str = "#22d3ee"):
        frame = QFrame()
        frame.setStyleSheet(card_qss("active", radius=8))
        layout = QVBoxLayout(frame)
        layout.setContentsMargins(18, 14, 18, 14)
        layout.setSpacing(4)
        title_label = QLabel(title)
        title_label.setStyleSheet(label_qss("title") + f" color:{accent}; font-size:19px;")
        subtitle_label = QLabel(subtitle)
        subtitle_label.setStyleSheet(label_qss("subtitle"))
        subtitle_label.setWordWrap(True)
        layout.addWidget(title_label)
        layout.addWidget(subtitle_label)
        return frame

    def _tool_group_style(self):
        return tool_group_qss()

    def _tool_input_style(self):
        return tool_field_qss()

    def _tool_button_style(self, kind="secondary"):
        return tool_button_qss(kind, "md")

    def _polish_card_tool(self, tab):
        tab.setStyleSheet(tool_tab_qss())
        if tab.layout():
            tab.layout().setContentsMargins(12, 10, 12, 12)
            tab.layout().setSpacing(14)
        for group in tab.findChildren(QGroupBox):
            group.setStyleSheet(self._tool_group_style())
        for cls in (QLineEdit, QComboBox, QSpinBox):
            for widget in tab.findChildren(cls):
                widget.setStyleSheet(self._tool_input_style())
        for button in tab.findChildren(QPushButton):
            button.setStyleSheet(self._tool_button_style("secondary"))
        self.generate_btn.setText("Gerar cartoes")
        self.generate_btn.setStyleSheet(self._tool_button_style("success"))
        self.cancel_btn.setStyleSheet(self._tool_button_style("danger"))
        self.result_text.setStyleSheet(tool_output_qss("#34d399"))
        self.progress_bar.setStyleSheet(tool_progress_qss())
        self.status_label.setStyleSheet(tool_status_qss())

    def _polish_cep_tool(self, tab):
        tab.setStyleSheet(tool_tab_qss())
        if tab.layout():
            tab.layout().setContentsMargins(12, 10, 12, 12)
            tab.layout().setSpacing(14)
        for group in tab.findChildren(QGroupBox):
            group.setStyleSheet(self._tool_group_style())
        for cls in (QLineEdit, QComboBox):
            for widget in tab.findChildren(cls):
                widget.setStyleSheet(self._tool_input_style())
        for radio in tab.findChildren(QRadioButton):
            radio.setStyleSheet(tool_radio_qss())
        for button in tab.findChildren(QPushButton):
            button.setStyleSheet(self._tool_button_style("secondary"))
        for button_name in (
            "copy_cep_btn", "copy_endereco_btn", "copy_numero_btn", "copy_bairro_btn",
            "copy_cidade_btn", "copy_estado_btn", "copy_uf_btn",
        ):
            button = getattr(self, button_name, None)
            if button:
                button.setText("Copiar")
                button.setMinimumWidth(92)
                button.setFixedHeight(34)
                button.setStyleSheet(self._tool_button_style("ghost"))
        self.gerar_cep_btn.setText("Gerar endereço")
        self.gerar_cep_btn.setStyleSheet(self._tool_button_style("primary"))
        if hasattr(self, "copy_full_cep_btn"):
            self.copy_full_cep_btn.setStyleSheet(self._tool_button_style("secondary"))
        for field_name in (
            "full_address_field", "cep_field", "endereco_field", "numero_field",
            "bairro_field", "cidade_field", "estado_field", "uf_field",
        ):
            field = getattr(self, field_name, None)
            if field:
                field.setStyleSheet(tool_result_field_qss())
        self.cep_status_label.setStyleSheet(tool_status_qss())

    def _polish_account_formatter_tool(self, tab):
        tab.setStyleSheet(tool_tab_qss())
        for group in tab.findChildren(QGroupBox):
            group.setStyleSheet(self._tool_group_style())
        for cls in (QLineEdit, QComboBox, QTextEdit):
            for widget in tab.findChildren(cls):
                if widget is getattr(self, "accounts_result", None):
                    continue
                if widget is getattr(self, "accounts_preview", None):
                    continue
                widget.setStyleSheet(tool_field_qss("rgba(139, 92, 246, 0.60)"))
        for button in tab.findChildren(QPushButton):
            button.setStyleSheet(self._tool_button_style("secondary"))
        self.format_btn.setText("Gerar contas")
        self.format_btn.setStyleSheet(self._tool_button_style("primary"))
        self.accounts_result.setStyleSheet(tool_output_qss("#34d399"))
        self.accounts_status_label.setStyleSheet(tool_status_qss())

    def _current_account_service(self):
        service = self.service_combo.currentData()
        if service == "Personalizado":
            return self.custom_service_input.text().strip() or "Personalizado"
        return service or "Crunchyroll"

    def _update_accounts_preview(self):
        if not hasattr(self, "accounts_preview"):
            return
        service = self._current_account_service()
        model = self.model_combo.currentData() or 1
        service_password = self.service_password_input.text().strip() or None
        preview, _ = self.account_formatter.process_and_format(
            "exemplo@outlook.com:senha123",
            model,
            service,
            service_password,
        )
        self.accounts_preview.setText(preview.strip())

    def _update_accounts_stats(self):
        if not hasattr(self, "accounts_total_stat"):
            return
        credentials = self.account_formatter.parse_credentials(self.accounts_input.toPlainText())
        domains = {cred.domain for cred in credentials}
        visible = len(getattr(self, "_account_result_blocks", []) or [])
        if hasattr(self, "accounts_search_input") and self.accounts_search_input.text().strip():
            visible = len([b for b in self._account_result_blocks if self.accounts_search_input.text().lower() in b.lower()])
        output_count = len(getattr(self, "_account_result_blocks", []) or [])
        self.accounts_total_stat.setText(f"{len(credentials)}\nCONTAS")
        self.accounts_domains_stat.setText(f"{len(domains)}\nDOMINIOS")
        self.accounts_visible_stat.setText(f"{visible}\nVISIVEIS")
        self.accounts_output_stat.setText(f"{output_count}\nSAIDAS")

    def _make_account_blocks(self, result, model):
        text = (result or "").strip()
        if not text:
            return []
        if model in (4, 7, 8, 9):
            return [line for line in text.splitlines() if line.strip()]
        return [block.strip() for block in re.split(r"\n\s*\n", text) if block.strip()]

    def filter_formatted_accounts(self):
        if not hasattr(self, "accounts_result"):
            return
        blocks = getattr(self, "_account_result_blocks", []) or []
        query = self.accounts_search_input.text().strip().lower()
        if not blocks:
            self._update_accounts_stats()
            return
        filtered = [block for block in blocks if not query or query in block.lower()]
        model = self.model_combo.currentData() or 1
        sep = "\n" if model in (4, 7, 8, 9) else "\n\n"
        self.accounts_result.setText(sep.join(filtered))
        self._update_accounts_stats()

    def export_formatted_accounts(self):
        text = self.accounts_result.toPlainText().strip()
        if not text:
            QMessageBox.warning(self, "Aviso", "Nenhum resultado para exportar!")
            return
        service = re.sub(r'[^a-zA-Z0-9_-]+', '_', self._current_account_service()).strip("_") or "contas"
        default_name = f"contas_{service}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path, _ = QFileDialog.getSaveFileName(self, "Exportar contas", str(Path.home() / "Downloads" / default_name), "Texto (*.txt);;Todos os arquivos (*)")
        if not path:
            return
        try:
            Path(path).write_text(text, encoding="utf-8")
            self.accounts_status_label.setText(f"Exportado em: {path}")
            self.accounts_status_label.setStyleSheet(tool_status_qss("#10b981"))
        except Exception as exc:
            QMessageBox.warning(self, "Erro", f"Nao consegui exportar:\n{exc}")
    
    def create_card_generator_tab(self):
        """Cria a aba do gerador de cartões"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(20)
        layout.addWidget(self._tool_header("Cartoes", "Gere listas no formato NUMERO|MES|ANO|CVV com uma interface mais limpa.", "#34d399"))
        
        # Grupo de configuração - Estilo Apple
        config_group = QGroupBox("CONFIGURAÇÃO")
        config_group.setStyleSheet(self._tool_group_style())
        config_layout = QVBoxLayout()
        config_layout.setSpacing(16)
        
        # Padrão do cartão
        pattern_layout = QHBoxLayout()
        pattern_label = QLabel("Padrão")
        pattern_label.setStyleSheet(tool_inline_label_qss(min_width=80))
        pattern_layout.addWidget(pattern_label)
        
        self.pattern_input = QLineEdit()
        self.pattern_input.setPlaceholderText("Ex: 406669994713XXXX (X = dígitos aleatórios)")
        self.pattern_input.textChanged.connect(self.update_card_pattern_hint)
        self.pattern_input.setStyleSheet(self._tool_input_style())
        pattern_layout.addWidget(self.pattern_input)
        config_layout.addLayout(pattern_layout)

        self.card_analysis_label = QLabel("Digite um padrão para ver bandeira, tamanho, campos X e validade local.")
        self.card_analysis_label.setWordWrap(True)
        self.card_analysis_label.setStyleSheet(tool_analysis_qss())
        config_layout.addWidget(self.card_analysis_label)
        
        # Linha de expiração e CVV
        exp_layout = QHBoxLayout()
        exp_layout.setSpacing(16)
        
        # Estilo comum para labels
        label_style = tool_inline_label_qss(size=12)
        
        # Estilo comum para combos e inputs pequenos
        small_input_style = self._tool_input_style()
        
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
        current_year = datetime.now().year
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
        self.progress_bar.setStyleSheet(tool_progress_qss())
        self.progress_bar.hide()
        progress_layout.addWidget(self.progress_bar)
        
        self.progress_label = QLabel("")
        self.progress_label.setAlignment(Qt.AlignCenter)
        self.progress_label.setStyleSheet(tool_status_qss("#06b6d4"))
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

        validate_btn = QPushButton("Validar lista")
        validate_btn.setStyleSheet(secondary_btn_style)
        validate_btn.clicked.connect(self.validate_generated_cards)
        btn_layout.addWidget(validate_btn)

        masked_btn = QPushButton("Copiar mascarado")
        masked_btn.setStyleSheet(secondary_btn_style)
        masked_btn.clicked.connect(self.copy_masked_cards)
        btn_layout.addWidget(masked_btn)
        
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
        result_group.setStyleSheet(self._tool_group_style())
        result_layout = QVBoxLayout()
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet(tool_output_qss("#34d399"))
        self.result_text.setPlaceholderText("Os cartões gerados aparecerão aqui...\n\nFormato: NUMERO|MES|ANO|CVV")
        result_layout.addWidget(self.result_text)
        
        result_group.setLayout(result_layout)
        layout.addWidget(result_group)
        
        # Status - Estilo Apple
        self.status_label = QLabel("Histórico: 0 cartões · Gerados: 0")
        self.status_label.setStyleSheet(tool_status_qss())
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        tab.setLayout(layout)
        self._polish_card_tool(tab)
        return tab
    
    def create_cep_generator_tab(self):
        """Cria a aba do gerador de CEP em layout compacto e copiavel."""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(14)

        card_style = """
            QFrame {
                background-color: #0b1626;
                border: 1px solid rgba(34, 211, 238, 0.20);
                border-radius: 10px;
            }
        """
        result_row_label_style = (
            "color:#93c5fd; font-size:12px; font-weight:800; "
            "background:transparent; border:none;"
        )
        label_style = tool_inline_label_qss(size=13)
        combo_style = self._tool_input_style()

        options_card = QFrame()
        options_card.setStyleSheet(card_style)
        options_layout = QGridLayout(options_card)
        options_layout.setContentsMargins(18, 16, 18, 16)
        options_layout.setHorizontalSpacing(14)
        options_layout.setVerticalSpacing(10)

        title = QLabel("Filtros")
        title.setStyleSheet("color:#22d3ee; font-size:14px; font-weight:900; background:transparent; border:none;")
        hint = QLabel("Deixe em Todos para gerar qualquer endereco, ou escolha estado/cidade quando precisar.")
        hint.setStyleSheet(label_qss("subtitle") + " background:transparent; border:none;")
        hint.setWordWrap(True)
        options_layout.addWidget(title, 0, 0, 1, 1)
        options_layout.addWidget(hint, 0, 1, 1, 2)

        estado_label = QLabel("Estado")
        estado_label.setStyleSheet(label_style)
        self.estado_combo = QComboBox()
        self.estado_combo.addItem("Todos", "")
        for uf, nome in self.address_generator.get_estados():
            self.estado_combo.addItem(f"{uf} - {nome}", uf)
        self.estado_combo.setStyleSheet(combo_style)
        self.estado_combo.currentIndexChanged.connect(self.on_estado_changed)

        cidade_label = QLabel("Cidade")
        cidade_label.setStyleSheet(label_style)
        self.cidade_combo = QComboBox()
        self.cidade_combo.addItem("Todas", "")
        self.cidade_combo.setStyleSheet(combo_style)

        pontuacao_label = QLabel("Formato")
        pontuacao_label.setStyleSheet(label_style)
        radio_layout = QHBoxLayout()
        radio_layout.setSpacing(18)
        self.pontuacao_group = QButtonGroup()

        self.radio_sim = QRadioButton("Com pontuacao")
        self.radio_sim.setChecked(True)
        self.radio_sim.setStyleSheet(tool_radio_qss())
        self.pontuacao_group.addButton(self.radio_sim)
        radio_layout.addWidget(self.radio_sim)

        self.radio_nao = QRadioButton("Sem pontuacao")
        self.radio_nao.setStyleSheet(tool_radio_qss())
        self.pontuacao_group.addButton(self.radio_nao)
        radio_layout.addWidget(self.radio_nao)
        radio_layout.addStretch()

        options_layout.addWidget(estado_label, 1, 0)
        options_layout.addWidget(cidade_label, 1, 1)
        options_layout.addWidget(pontuacao_label, 1, 2)
        options_layout.addWidget(self.estado_combo, 2, 0)
        options_layout.addWidget(self.cidade_combo, 2, 1)
        options_layout.addLayout(radio_layout, 2, 2)
        options_layout.setColumnStretch(0, 1)
        options_layout.setColumnStretch(1, 1)
        options_layout.setColumnStretch(2, 1)

        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(10)
        self.gerar_cep_btn = QPushButton("Gerar endereco")
        self.gerar_cep_btn.setMinimumHeight(42)
        self.gerar_cep_btn.setStyleSheet(self._tool_button_style("primary"))
        self.gerar_cep_btn.clicked.connect(self.generate_single_cep)
        actions_layout.addWidget(self.gerar_cep_btn, 2)

        self.copy_full_cep_btn = QPushButton("Copiar tudo")
        self.copy_full_cep_btn.setMinimumHeight(42)
        self.copy_full_cep_btn.setStyleSheet(self._tool_button_style("secondary"))
        self.copy_full_cep_btn.clicked.connect(self.copy_full_cep)
        actions_layout.addWidget(self.copy_full_cep_btn, 1)
        options_layout.addLayout(actions_layout, 3, 0, 1, 3)
        layout.addWidget(options_card)

        result_card = QFrame()
        result_card.setStyleSheet(card_style)
        result_layout = QVBoxLayout(result_card)
        result_layout.setContentsMargins(18, 16, 18, 16)
        result_layout.setSpacing(12)

        result_header = QHBoxLayout()
        result_title = QLabel("Resultado")
        result_title.setStyleSheet("color:#22d3ee; font-size:14px; font-weight:900; background:transparent; border:none;")
        self.cep_status_label = QLabel("")
        self.cep_status_label.setStyleSheet(tool_status_qss())
        self.cep_status_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        result_header.addWidget(result_title)
        result_header.addStretch()
        result_header.addWidget(self.cep_status_label)
        result_layout.addLayout(result_header)

        field_style = """
            QLineEdit {
                background-color: #030712;
                border: 1px solid rgba(34, 211, 238, 0.18);
                border-radius: 8px;
                padding: 9px 12px;
                font-size: 13px;
                color: #34d399;
                font-weight: 800;
            }
        """
        copy_btn_style = tool_button_qss("ghost", "sm")

        def make_result_field(attr_name, placeholder):
            field = QLineEdit()
            field.setReadOnly(True)
            field.setPlaceholderText(placeholder)
            field.setMinimumHeight(38)
            field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            field.setStyleSheet(field_style)
            setattr(self, attr_name, field)
            return field

        full_row = QHBoxLayout()
        full_row.setSpacing(10)
        full_label = QLabel("Completo")
        full_label.setStyleSheet(result_row_label_style)
        full_label.setFixedWidth(82)
        self.full_address_field = make_result_field("full_address_field", "Endereco completo aparece aqui depois de gerar.")
        full_row.addWidget(full_label)
        full_row.addWidget(self.full_address_field, 1)
        result_layout.addLayout(full_row)

        rows_grid = QGridLayout()
        rows_grid.setHorizontalSpacing(10)
        rows_grid.setVerticalSpacing(9)

        def add_result_row(row, title_text, attr_name, placeholder, copy_label):
            label = QLabel(title_text)
            label.setStyleSheet(result_row_label_style)
            label.setFixedWidth(82)
            label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
            field = make_result_field(attr_name, placeholder)
            button = QPushButton("Copiar")
            button.setStyleSheet(copy_btn_style)
            button.setToolTip(f"Copiar {copy_label}")
            button.setFixedWidth(92)
            button.setFixedHeight(36)
            button_attr = {
                "cep_field": "copy_cep_btn",
                "endereco_field": "copy_endereco_btn",
                "numero_field": "copy_numero_btn",
                "bairro_field": "copy_bairro_btn",
                "cidade_field": "copy_cidade_btn",
                "estado_field": "copy_estado_btn",
                "uf_field": "copy_uf_btn",
            }.get(attr_name)
            if button_attr:
                setattr(self, button_attr, button)
            button.clicked.connect(lambda _checked=False, f=field, n=copy_label: self.copy_single_field(f, n))
            rows_grid.addWidget(label, row, 0)
            rows_grid.addWidget(field, row, 1)
            rows_grid.addWidget(button, row, 2)

        add_result_row(0, "CEP", "cep_field", "00000-000", "CEP")
        add_result_row(1, "Rua", "endereco_field", "Rua / Avenida", "Endereco")
        add_result_row(2, "Numero", "numero_field", "Numero", "Numero")
        add_result_row(3, "Bairro", "bairro_field", "Bairro", "Bairro")
        add_result_row(4, "Cidade", "cidade_field", "Cidade", "Cidade")
        add_result_row(5, "Estado", "estado_field", "Estado completo", "Estado")
        add_result_row(6, "UF", "uf_field", "UF", "UF")
        rows_grid.setColumnStretch(1, 1)
        result_layout.addLayout(rows_grid)

        layout.addWidget(result_card)
        layout.addStretch()

        tab.setLayout(layout)
        self._polish_cep_tool(tab)
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
            if hasattr(self, "numero_field"):
                self.numero_field.setText(getattr(endereco, "numero", "") or "")
            self.bairro_field.setText(endereco.bairro)
            self.cidade_field.setText(endereco.cidade)
            estado_nome = self.address_generator.ESTADOS.get(endereco.uf, endereco.estado or endereco.uf)
            self.estado_field.setText(estado_nome)
            if hasattr(self, "uf_field"):
                self.uf_field.setText(endereco.uf or "")
            if hasattr(self, "full_address_field"):
                self.full_address_field.setText(endereco.format_completo(com_pontuacao))

            source = getattr(self.address_generator, "last_source", "")
            if source == "reserva":
                self.cep_status_label.setText("Reserva local usada porque a API nao respondeu.")
                self.cep_status_label.setStyleSheet(tool_status_qss("#fbbf24"))
            else:
                self.cep_status_label.setText("CEP gerado pela API.")
                self.cep_status_label.setStyleSheet(tool_status_qss("#10b981"))
        else:
            self.cep_status_label.setText("Erro ao gerar CEP")
            self.cep_status_label.setStyleSheet(tool_status_qss("#ef4444"))
    
    def copy_single_field(self, field, field_name):
        """Copia o valor de um campo específico"""
        text = field.text()
        if text:
            _set_clipboard_text_safe(text)
            self.cep_status_label.setText(f"{field_name} copiado!")
            self.cep_status_label.setStyleSheet(tool_status_qss("#10b981"))
        else:
            self.cep_status_label.setText(f"Nenhum {field_name} para copiar")
            self.cep_status_label.setStyleSheet(tool_status_qss("#f59e0b"))

    def copy_full_cep(self):
        """Copia o endereco completo em linhas nomeadas."""
        values = [
            ("CEP", self.cep_field.text()),
            ("Endereco", self.endereco_field.text()),
            ("Numero", getattr(self, "numero_field", self.cep_field).text() if hasattr(self, "numero_field") else ""),
            ("Bairro", self.bairro_field.text()),
            ("Cidade", self.cidade_field.text()),
            ("Estado", self.estado_field.text()),
            ("UF", getattr(self, "uf_field", self.cep_field).text() if hasattr(self, "uf_field") else ""),
        ]
        lines = [f"{label}: {value}" for label, value in values if value]
        if not lines:
            self.cep_status_label.setText("Nenhum endereco para copiar")
            self.cep_status_label.setStyleSheet(tool_status_qss("#f59e0b"))
            return
        _set_clipboard_text_safe("\n".join(lines))
        self.cep_status_label.setText("Endereco completo copiado!")
        self.cep_status_label.setStyleSheet(tool_status_qss("#10b981"))
    
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
        if str(cvv).lower() == "random":
            cvv = "RANDOM"
        
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
            self.progress_label.setStyleSheet(tool_status_qss("#10b981"))
        else:
            self.progress_label.setText("Nenhum cartão gerado")
            self.progress_label.setStyleSheet(tool_status_qss("#ef4444"))
        
        # Esconder barra após 3 segundos
        QTimer.singleShot(3000, self.hide_progress)
    
    def on_generation_error(self, error_msg):
        """Chamado quando ocorre erro na geração"""
        self.is_generating = False
        self.generate_btn.setEnabled(True)
        self.cancel_btn.hide()
        self.progress_label.setText(f"Erro: {error_msg}")
        self.progress_label.setStyleSheet(tool_status_qss("#ef4444"))
        QMessageBox.critical(self, "Erro", f"Erro durante a geração:\n\n{error_msg}")
        QTimer.singleShot(3000, self.hide_progress)
    
    def cancel_generation(self):
        """Cancela a geração em andamento"""
        if self.generator_thread and self.is_generating:
            self.generator_thread.stop()
            self.progress_label.setText("Cancelando...")
            self.progress_label.setStyleSheet(tool_status_qss("#f59e0b"))
    
    def hide_progress(self):
        """Esconde a barra de progresso"""
        if not self.is_generating:
            self.progress_bar.hide()
            self.progress_label.hide()
            self.progress_label.setStyleSheet(tool_status_qss("#06b6d4"))
    
    def copy_cards(self):
        """Copia os cartões para a área de transferência"""
        text = self.result_text.toPlainText()
        if text:
            _set_clipboard_text_safe(text)
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
                _set_clipboard_text_safe(text)
                QMessageBox.information(self, "Sucesso", f"{len(fields)} {field_name}(s) copiado(s)!")
            else:
                QMessageBox.warning(self, "Aviso", f"Não foi possível extrair {field_name}!")
        except Exception as e:
            QMessageBox.warning(self, "Erro", f"Erro ao copiar: {str(e)}")

    def _card_digits(self, value: str) -> str:
        """Extrai apenas os digitos do numero do cartao."""
        return re.sub(r"\D", "", value or "")

    def _detect_card_brand(self, digits: str) -> str:
        """Detecta a bandeira por prefixo, apenas localmente."""
        if not digits:
            return "Indefinida"
        prefix2 = int(digits[:2]) if len(digits) >= 2 else -1
        prefix3 = int(digits[:3]) if len(digits) >= 3 else -1
        prefix4 = int(digits[:4]) if len(digits) >= 4 else -1
        prefix6 = int(digits[:6]) if len(digits) >= 6 else -1
        if (
            digits.startswith(("401178", "401179", "431274", "438935", "451416", "457393", "457631"))
            or digits.startswith(("504175", "5067", "5090", "627780", "636297", "636368"))
        ):
            return "Elo"
        if digits.startswith("4"):
            return "Visa"
        if 51 <= prefix2 <= 55 or 2221 <= prefix4 <= 2720:
            return "Mastercard"
        if prefix2 in (34, 37):
            return "American Express"
        if digits.startswith("6011") or digits.startswith("65") or 644 <= prefix3 <= 649:
            return "Discover"
        if digits.startswith("35"):
            return "JCB"
        if prefix2 in (36, 38, 39):
            return "Diners"
        return "Indefinida"

    def update_card_pattern_hint(self):
        """Mostra uma leitura rapida do padrao antes de gerar."""
        if not hasattr(self, "card_analysis_label"):
            return
        pattern = self.pattern_input.text().strip()
        if not pattern:
            self.card_analysis_label.setText("Digite um padrão para ver bandeira, tamanho, campos X e validade local.")
            self.card_analysis_label.setStyleSheet(tool_analysis_qss())
            return

        clean_pattern = pattern.upper().replace(" ", "").replace("-", "")
        invalid_chars = [char for char in clean_pattern if not char.isdigit() and char != "X"]
        digits = self._card_digits(clean_pattern)
        x_count = clean_pattern.count("X")
        variable_digits = max(0, x_count - (1 if clean_pattern.endswith("X") else 0))
        combinations = 10 ** variable_digits if variable_digits <= 6 else None
        brand = self._detect_card_brand(digits)
        length = len(clean_pattern)

        if invalid_chars:
            status = "Revise: use apenas números e X."
            color = "#f43f5e"
        elif length < 13 or length > 19:
            status = "Tamanho incomum. O normal fica entre 13 e 19 dígitos."
            color = "#fbbf24"
        elif x_count == 0:
            valid = self.card_generator.validate_luhn(digits)
            status = "Luhn OK." if valid else "Luhn inválido para número completo."
            color = "#10b981" if valid else "#f43f5e"
        else:
            auto = "último X vira dígito Luhn automático" if clean_pattern.endswith("X") else "Luhn será validado por tentativa"
            status = f"{x_count} campo(s) X; {auto}."
            color = "#22d3ee"

        combo_text = f"{combinations:,}".replace(",", ".") if combinations is not None else "muitas"
        self.card_analysis_label.setText(
            f"Bandeira provável: {brand} | Tamanho: {length} | X: {x_count} | Combinações: {combo_text} | {status}"
        )
        self.card_analysis_label.setStyleSheet(tool_analysis_qss(color, strong=True))

    def _analyze_card_line(self, line: str) -> dict:
        parts = [part.strip() for part in re.split(r"[|;:]", line.strip()) if part.strip()]
        if len(parts) < 4:
            return {"ok": False, "reason": "formato", "brand": "Indefinida", "number": ""}

        number = self._card_digits(parts[0])
        month = self._card_digits(parts[1])
        year = self._card_digits(parts[2])
        cvv = self._card_digits(parts[3])
        brand = self._detect_card_brand(number)

        if not (13 <= len(number) <= 19):
            return {"ok": False, "reason": "numero", "brand": brand, "number": number}
        if not self.card_generator.validate_luhn(number):
            return {"ok": False, "reason": "luhn", "brand": brand, "number": number}
        if not month or not (1 <= int(month) <= 12):
            return {"ok": False, "reason": "mes", "brand": brand, "number": number}
        if len(year) == 2:
            full_year = 2000 + int(year)
        elif len(year) == 4:
            full_year = int(year)
        else:
            return {"ok": False, "reason": "ano", "brand": brand, "number": number}
        now = datetime.now()
        if full_year < now.year or (full_year == now.year and int(month) < now.month):
            return {"ok": False, "reason": "vencido", "brand": brand, "number": number}
        if len(cvv) not in (3, 4):
            return {"ok": False, "reason": "cvv", "brand": brand, "number": number}
        return {"ok": True, "reason": "ok", "brand": brand, "number": number}

    def validate_generated_cards(self):
        """Valida formato/Luhn da lista exibida, sem consulta externa."""
        lines = [line.strip() for line in self.result_text.toPlainText().splitlines() if line.strip()]
        if not lines:
            QMessageBox.warning(self, "Aviso", "Nenhum cartão na lista para validar.")
            return

        seen = set()
        stats = {"ok": 0, "duplicado": 0}
        brands = {}
        invalid_reasons = {}
        for line in lines:
            data = self._analyze_card_line(line)
            number = data.get("number", "")
            if number and number in seen:
                stats["duplicado"] += 1
            elif number:
                seen.add(number)
            if data["ok"]:
                stats["ok"] += 1
                brands[data["brand"]] = brands.get(data["brand"], 0) + 1
            else:
                reason = data.get("reason", "invalido")
                invalid_reasons[reason] = invalid_reasons.get(reason, 0) + 1

        invalid = len(lines) - stats["ok"]
        brand_text = ", ".join(f"{brand}: {count}" for brand, count in sorted(brands.items())) or "-"
        reason_text = ", ".join(f"{reason}: {count}" for reason, count in sorted(invalid_reasons.items())) or "-"
        self.status_label.setText(
            f"Validação local: {stats['ok']} OK · {invalid} revisar · {stats['duplicado']} duplicados"
        )
        QMessageBox.information(
            self,
            "Validação local",
            "Nada foi enviado para site externo.\n\n"
            f"Total: {len(lines)}\n"
            f"Formato/Luhn OK: {stats['ok']}\n"
            f"Para revisar: {invalid}\n"
            f"Duplicados por número: {stats['duplicado']}\n"
            f"Bandeiras: {brand_text}\n"
            f"Motivos de revisão: {reason_text}"
        )

    def copy_masked_cards(self):
        """Copia a lista com os numeros mascarados."""
        lines = [line.strip() for line in self.result_text.toPlainText().splitlines() if line.strip()]
        if not lines:
            QMessageBox.warning(self, "Aviso", "Nenhum cartão para copiar.")
            return

        masked = []
        for line in lines:
            parts = [part.strip() for part in re.split(r"[|;:]", line) if part.strip()]
            if len(parts) >= 4:
                number = self._card_digits(parts[0])
                safe_number = number[:6] + ("*" * max(0, len(number) - 10)) + number[-4:] if len(number) >= 10 else "****"
                masked.append(f"{safe_number}|{parts[1]}|{parts[2]}|***")
            else:
                masked.append(line)
        _set_clipboard_text_safe("\n".join(masked))
        QMessageBox.information(self, "Copiado", f"{len(masked)} linha(s) copiadas com número mascarado.")
    
    # ===== MÉTODOS DO FORMATADOR DE CONTAS =====
    
    def create_account_formatter_tab(self):
        """Cria a aba do formatador de contas premium"""
        tab = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.addWidget(self._tool_header(
            "Organizador de Contas",
            "Cole contas email:senha, escolha serviço/modelo e gere saídas prontas.",
            "#8b5cf6",
        ))
        
        # Scroll area para caber tudo
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet(tool_scroll_area_qss())
        
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setSpacing(16)
        
        # Grupo de Entrada
        input_group = QGroupBox("ENTRADA")
        input_group.setStyleSheet(self._tool_group_style())
        input_layout = QVBoxLayout()
        input_layout.setSpacing(12)
        
        # Área de texto para colar credenciais
        input_label = QLabel("Cole as credenciais (email:senha, email|senha, email-senha):")
        input_label.setStyleSheet(tool_inline_label_qss(size=12))
        input_layout.addWidget(input_label)
        
        self.accounts_input = QTextEdit()
        self.accounts_input.setPlaceholderText("usuario@gmail.com:senha123\noutro@hotmail.com|minhasenha\nemail@yahoo.com-pass456")
        self.accounts_input.setMinimumHeight(120)
        self.accounts_input.setMaximumHeight(150)
        self.accounts_input.setStyleSheet(self._tool_input_style())
        self.accounts_input.textChanged.connect(self._update_accounts_stats)
        input_layout.addWidget(self.accounts_input)
        
        input_group.setLayout(input_layout)
        scroll_layout.addWidget(input_group)

        stats_layout = QGridLayout()
        stats_layout.setSpacing(8)
        self.accounts_total_stat = QLabel("0\nCONTAS")
        self.accounts_domains_stat = QLabel("0\nDOMINIOS")
        self.accounts_visible_stat = QLabel("0\nVISIVEIS")
        self.accounts_output_stat = QLabel("0\nSAIDAS")
        for i, label in enumerate((
            self.accounts_total_stat,
            self.accounts_domains_stat,
            self.accounts_visible_stat,
            self.accounts_output_stat,
        )):
            label.setAlignment(Qt.AlignCenter)
            label.setStyleSheet(tool_stat_tile_qss())
            stats_layout.addWidget(label, 0, i)
        scroll_layout.addLayout(stats_layout)
        
        # Grupo de Configurações
        config_group = QGroupBox("CONFIGURAÇÕES")
        config_group.setStyleSheet(self._tool_group_style())
        config_layout = QVBoxLayout()
        config_layout.setSpacing(16)
        
        # Estilo comum
        label_style = tool_inline_label_qss(size=12)
        combo_style = self._tool_input_style()
        
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
        self.custom_service_input.setStyleSheet(self._tool_input_style())
        self.custom_service_input.textChanged.connect(self._update_accounts_preview)
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
        self.service_password_input.setStyleSheet(self._tool_input_style())
        self.service_password_input.textChanged.connect(self._update_accounts_preview)
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
        self.model_combo.addItem("💎 PRO Completo", 5)
        self.model_combo.addItem("🚀 PRO Simples", 6)
        self.model_combo.addItem("🔹 PRO Minimal", 7)
        self.model_combo.addItem("📊 Tabela Pipe", 8)
        self.model_combo.addItem("🧩 JSON Lines", 9)
        self.model_combo.setStyleSheet(combo_style)
        self.model_combo.currentIndexChanged.connect(self._update_accounts_preview)
        model_layout.addWidget(self.model_combo)
        model_layout.addStretch()
        config_layout.addLayout(model_layout)
        
        config_group.setLayout(config_layout)
        scroll_layout.addWidget(config_group)

        preview_group = QGroupBox("PREVIEW DO MODELO")
        preview_group.setStyleSheet(self._tool_group_style())
        preview_layout = QVBoxLayout()
        self.accounts_preview = QTextEdit()
        self.accounts_preview.setReadOnly(True)
        self.accounts_preview.setMaximumHeight(135)
        self.accounts_preview.setStyleSheet(tool_output_qss("#c4b5fd", dashed=True))
        preview_layout.addWidget(self.accounts_preview)
        preview_group.setLayout(preview_layout)
        scroll_layout.addWidget(preview_group)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(12)
        
        self.format_btn = QPushButton("✨ FORMATAR CONTAS")
        self.format_btn.setStyleSheet(self._tool_button_style("primary"))
        self.format_btn.clicked.connect(self.format_accounts)
        btn_layout.addWidget(self.format_btn)
        
        copy_formatted_btn = QPushButton("📋 Copiar Resultado")
        copy_formatted_btn.setStyleSheet(self._tool_button_style("secondary"))
        copy_formatted_btn.clicked.connect(self.copy_formatted_accounts)
        btn_layout.addWidget(copy_formatted_btn)

        export_formatted_btn = QPushButton("💾 Exportar TXT")
        export_formatted_btn.setStyleSheet(self._tool_button_style("secondary"))
        export_formatted_btn.clicked.connect(self.export_formatted_accounts)
        btn_layout.addWidget(export_formatted_btn)
        
        clear_formatted_btn = QPushButton("🗑️ Limpar")
        clear_formatted_btn.setStyleSheet(self._tool_button_style("secondary"))
        clear_formatted_btn.clicked.connect(self.clear_formatted_accounts)
        btn_layout.addWidget(clear_formatted_btn)
        
        scroll_layout.addLayout(btn_layout)

        search_layout = QHBoxLayout()
        search_label = QLabel("Buscar no resultado:")
        search_label.setStyleSheet(tool_inline_label_qss("#94a3b8", size=12, bold=True))
        search_layout.addWidget(search_label)
        self.accounts_search_input = QLineEdit()
        self.accounts_search_input.setPlaceholderText("email, dominio, serviço ou provedor...")
        self.accounts_search_input.textChanged.connect(self.filter_formatted_accounts)
        search_layout.addWidget(self.accounts_search_input, 1)
        scroll_layout.addLayout(search_layout)
        
        # Grupo de Resultado
        result_group = QGroupBox("RESULTADO")
        result_group.setStyleSheet(self._tool_group_style())
        result_layout = QVBoxLayout()
        
        self.accounts_result = QTextEdit()
        self.accounts_result.setReadOnly(True)
        self.accounts_result.setMinimumHeight(200)
        self.accounts_result.setStyleSheet(tool_output_qss("#34d399"))
        self.accounts_result.setPlaceholderText("As contas formatadas aparecerão aqui...")
        result_layout.addWidget(self.accounts_result)
        
        result_group.setLayout(result_layout)
        scroll_layout.addWidget(result_group)
        
        # Status
        self.accounts_status_label = QLabel("")
        self.accounts_status_label.setStyleSheet(tool_status_qss())
        self.accounts_status_label.setAlignment(Qt.AlignCenter)
        scroll_layout.addWidget(self.accounts_status_label)
        
        scroll.setWidget(scroll_content)
        layout.addWidget(scroll)
        
        tab.setLayout(layout)
        self._account_result_blocks = []
        self._polish_account_formatter_tool(tab)
        self._update_accounts_preview()
        self._update_accounts_stats()
        return tab
    
    def on_service_changed(self, index):
        """Mostra/oculta o campo de serviço personalizado"""
        service = self.service_combo.currentData()
        if service == "Personalizado":
            self.custom_service_widget.show()
        else:
            self.custom_service_widget.hide()
        self._update_accounts_preview()
    
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
                self._account_result_blocks = self._make_account_blocks(result, model)
                self.accounts_search_input.clear()
                self.accounts_result.setText(result)
                self.accounts_status_label.setText(f"✅ {count} conta(s) formatada(s) com sucesso!")
                self.accounts_status_label.setStyleSheet(tool_status_qss("#10b981"))
                self._update_accounts_stats()
            else:
                self._account_result_blocks = []
                self.accounts_result.clear()
                self.accounts_status_label.setText("⚠️ Nenhuma credencial válida encontrada")
                self.accounts_status_label.setStyleSheet(tool_status_qss("#f59e0b"))
                self._update_accounts_stats()
        
        except Exception as e:
            self.accounts_status_label.setText(f"❌ Erro: {str(e)}")
            self.accounts_status_label.setStyleSheet(tool_status_qss("#ef4444"))
    
    def copy_formatted_accounts(self):
        """Copia as contas formatadas para a área de transferência"""
        text = self.accounts_result.toPlainText()
        if text:
            _set_clipboard_text_safe(text)
            self.accounts_status_label.setText("📋 Resultado copiado!")
            self.accounts_status_label.setStyleSheet(tool_status_qss("#10b981"))
        else:
            QMessageBox.warning(self, "Aviso", "Nenhum resultado para copiar!")
    
    def clear_formatted_accounts(self):
        """Limpa os campos do formatador"""
        self.accounts_input.clear()
        self.accounts_result.clear()
        self.service_password_input.clear()
        self.custom_service_input.clear()
        self.formatted_accounts = ""
        self._account_result_blocks = []
        if hasattr(self, "accounts_search_input"):
            self.accounts_search_input.clear()
        self.accounts_status_label.setText("")
        self._update_accounts_stats()
        self._update_accounts_preview()
    
    def closeEvent(self, event):
        """Garante que a thread seja parada ao fechar"""
        if self.generator_thread and self.is_generating:
            self.generator_thread.stop()
            self.generator_thread.wait(2000)  # Espera até 2 segundos
        if self.address_thread and self.is_generating_addresses:
            self.address_thread.stop()
            self.address_thread.wait(2000)
        event.accept()
