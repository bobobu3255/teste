# -*- coding: utf-8 -*-
"""
Novas Ferramentas - Telegram Collector Pro v8.0
Ferramentas adicionais: Validador, Gerador Fake, Busca Avançada, Backup
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGroupBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QTextEdit, QLineEdit, QSpinBox, QCheckBox, QComboBox,
    QFormLayout, QFileDialog, QMessageBox, QProgressBar,
    QListWidget, QListWidgetItem, QFrame, QGridLayout,
    QScrollArea, QApplication
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread, QTimer
from PyQt5.QtGui import QFont
import random
import string
import shutil
import os
from datetime import datetime, timedelta
from pathlib import Path


# ============================================================
# VALIDADOR DE CPF/CNPJ
# ============================================================

class CPFValidator:
    """Validador e gerador de CPF"""
    
    @staticmethod
    def validate(cpf: str) -> tuple:
        """Valida um CPF. Retorna (bool, mensagem)"""
        cpf = ''.join(filter(str.isdigit, cpf))
        
        if len(cpf) != 11:
            return False, "CPF deve ter 11 dígitos"
        
        if cpf == cpf[0] * 11:
            return False, "CPF inválido (dígitos repetidos)"
        
        # Validar primeiro dígito
        soma = sum(int(cpf[i]) * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[9]):
            return False, "CPF inválido (dígito verificador 1)"
        
        # Validar segundo dígito
        soma = sum(int(cpf[i]) * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        if resto == 10:
            resto = 0
        if resto != int(cpf[10]):
            return False, "CPF inválido (dígito verificador 2)"
        
        return True, "CPF válido"
    
    @staticmethod
    def generate() -> str:
        """Gera um CPF válido"""
        cpf = [random.randint(0, 9) for _ in range(9)]
        
        # Primeiro dígito verificador
        soma = sum(cpf[i] * (10 - i) for i in range(9))
        resto = (soma * 10) % 11
        cpf.append(0 if resto == 10 else resto)
        
        # Segundo dígito verificador
        soma = sum(cpf[i] * (11 - i) for i in range(10))
        resto = (soma * 10) % 11
        cpf.append(0 if resto == 10 else resto)
        
        return ''.join(map(str, cpf))
    
    @staticmethod
    def format(cpf: str) -> str:
        """Formata CPF: XXX.XXX.XXX-XX"""
        cpf = ''.join(filter(str.isdigit, cpf))
        if len(cpf) == 11:
            return f"{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}"
        return cpf


class CNPJValidator:
    """Validador e gerador de CNPJ"""
    
    @staticmethod
    def validate(cnpj: str) -> tuple:
        """Valida um CNPJ. Retorna (bool, mensagem)"""
        cnpj = ''.join(filter(str.isdigit, cnpj))
        
        if len(cnpj) != 14:
            return False, "CNPJ deve ter 14 dígitos"
        
        if cnpj == cnpj[0] * 14:
            return False, "CNPJ inválido (dígitos repetidos)"
        
        # Validar primeiro dígito
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos1[i] for i in range(12))
        resto = soma % 11
        digito1 = 0 if resto < 2 else 11 - resto
        if digito1 != int(cnpj[12]):
            return False, "CNPJ inválido (dígito verificador 1)"
        
        # Validar segundo dígito
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(int(cnpj[i]) * pesos2[i] for i in range(13))
        resto = soma % 11
        digito2 = 0 if resto < 2 else 11 - resto
        if digito2 != int(cnpj[13]):
            return False, "CNPJ inválido (dígito verificador 2)"
        
        return True, "CNPJ válido"
    
    @staticmethod
    def generate() -> str:
        """Gera um CNPJ válido"""
        cnpj = [random.randint(0, 9) for _ in range(8)]
        cnpj.extend([0, 0, 0, 1])  # Filial 0001
        
        # Primeiro dígito verificador
        pesos1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(cnpj[i] * pesos1[i] for i in range(12))
        resto = soma % 11
        cnpj.append(0 if resto < 2 else 11 - resto)
        
        # Segundo dígito verificador
        pesos2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
        soma = sum(cnpj[i] * pesos2[i] for i in range(13))
        resto = soma % 11
        cnpj.append(0 if resto < 2 else 11 - resto)
        
        return ''.join(map(str, cnpj))
    
    @staticmethod
    def format(cnpj: str) -> str:
        """Formata CNPJ: XX.XXX.XXX/XXXX-XX"""
        cnpj = ''.join(filter(str.isdigit, cnpj))
        if len(cnpj) == 14:
            return f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
        return cnpj


# ============================================================
# GERADOR DE DADOS FAKE
# ============================================================

class FakeDataGenerator:
    """Gerador de dados fictícios realistas"""
    
    NOMES_MASCULINOS = [
        "João", "Pedro", "Lucas", "Gabriel", "Rafael", "Matheus", "Bruno", 
        "Felipe", "Gustavo", "Leonardo", "André", "Carlos", "Eduardo", 
        "Fernando", "Ricardo", "Marcelo", "Paulo", "Rodrigo", "Thiago", "Diego"
    ]
    
    NOMES_FEMININOS = [
        "Maria", "Ana", "Juliana", "Fernanda", "Patricia", "Camila", "Amanda",
        "Bruna", "Carolina", "Beatriz", "Larissa", "Letícia", "Mariana",
        "Natália", "Gabriela", "Isabela", "Rafaela", "Vanessa", "Tatiana", "Renata"
    ]
    
    SOBRENOMES = [
        "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", 
        "Almeida", "Costa", "Gomes", "Martins", "Araújo", "Melo", "Barbosa",
        "Ribeiro", "Carvalho", "Cardoso", "Correia", "Pereira", "Lima", "Rocha"
    ]
    
    DOMINIOS = ["gmail.com", "hotmail.com", "outlook.com", "yahoo.com.br", "uol.com.br"]
    
    DDDS = ["11", "21", "31", "41", "51", "61", "71", "81", "85", "91", "27", "47", "48", "19", "13"]
    
    ESTADOS = {
        "AC": "Acre", "AL": "Alagoas", "AP": "Amapá", "AM": "Amazonas",
        "BA": "Bahia", "CE": "Ceará", "DF": "Distrito Federal", "ES": "Espírito Santo",
        "GO": "Goiás", "MA": "Maranhão", "MT": "Mato Grosso", "MS": "Mato Grosso do Sul",
        "MG": "Minas Gerais", "PA": "Pará", "PB": "Paraíba", "PR": "Paraná",
        "PE": "Pernambuco", "PI": "Piauí", "RJ": "Rio de Janeiro", "RN": "Rio Grande do Norte",
        "RS": "Rio Grande do Sul", "RO": "Rondônia", "RR": "Roraima", "SC": "Santa Catarina",
        "SP": "São Paulo", "SE": "Sergipe", "TO": "Tocantins"
    }
    
    CIDADES = {
        "SP": ["São Paulo", "Campinas", "Santos", "Guarulhos", "São Bernardo"],
        "RJ": ["Rio de Janeiro", "Niterói", "Petrópolis", "Nova Iguaçu", "Duque de Caxias"],
        "MG": ["Belo Horizonte", "Uberlândia", "Contagem", "Juiz de Fora", "Betim"],
        "RS": ["Porto Alegre", "Caxias do Sul", "Pelotas", "Canoas", "Santa Maria"],
        "PR": ["Curitiba", "Londrina", "Maringá", "Ponta Grossa", "Cascavel"],
        "BA": ["Salvador", "Feira de Santana", "Vitória da Conquista", "Camaçari", "Itabuna"],
        "SC": ["Florianópolis", "Joinville", "Blumenau", "São José", "Chapecó"],
        "PE": ["Recife", "Jaboatão", "Olinda", "Caruaru", "Petrolina"],
        "CE": ["Fortaleza", "Caucaia", "Juazeiro do Norte", "Maracanaú", "Sobral"],
        "GO": ["Goiânia", "Aparecida de Goiânia", "Anápolis", "Rio Verde", "Luziânia"]
    }
    
    LOGRADOUROS = ["Rua", "Avenida", "Travessa", "Alameda", "Praça"]
    
    BAIRROS = [
        "Centro", "Jardim América", "Vila Nova", "Boa Vista", "Santa Cruz",
        "São José", "Liberdade", "Consolação", "Pinheiros", "Moema"
    ]
    
    @classmethod
    def generate_name(cls, gender: str = None) -> tuple:
        """Gera nome completo. Retorna (nome, genero)"""
        if gender is None:
            gender = random.choice(["M", "F"])
        
        if gender == "M":
            primeiro_nome = random.choice(cls.NOMES_MASCULINOS)
        else:
            primeiro_nome = random.choice(cls.NOMES_FEMININOS)
        
        sobrenome1 = random.choice(cls.SOBRENOMES)
        sobrenome2 = random.choice(cls.SOBRENOMES)
        
        return f"{primeiro_nome} {sobrenome1} {sobrenome2}", gender
    
    @classmethod
    def generate_email(cls, nome: str) -> str:
        """Gera email baseado no nome"""
        partes = nome.lower().split()
        dominio = random.choice(cls.DOMINIOS)
        
        opcoes = [
            f"{partes[0]}.{partes[-1]}",
            f"{partes[0]}_{partes[-1]}",
            f"{partes[0]}{random.randint(1, 99)}",
            f"{partes[0]}.{partes[-1]}{random.randint(1, 99)}"
        ]
        
        email = random.choice(opcoes)
        # Remover acentos
        acentos = {'á': 'a', 'é': 'e', 'í': 'i', 'ó': 'o', 'ú': 'u', 
                   'ã': 'a', 'õ': 'o', 'ç': 'c', 'â': 'a', 'ê': 'e', 'ô': 'o'}
        for a, s in acentos.items():
            email = email.replace(a, s)
        
        return f"{email}@{dominio}"
    
    @classmethod
    def generate_phone(cls) -> str:
        """Gera telefone celular"""
        ddd = random.choice(cls.DDDS)
        numero = f"9{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
        return f"({ddd}) {numero}"
    
    @classmethod
    def generate_birth_date(cls, min_age: int = 18, max_age: int = 65) -> tuple:
        """Gera data de nascimento. Retorna (data_str, idade)"""
        hoje = datetime.now()
        idade = random.randint(min_age, max_age)
        ano_nasc = hoje.year - idade
        mes_nasc = random.randint(1, 12)
        dia_nasc = random.randint(1, 28)
        
        data = datetime(ano_nasc, mes_nasc, dia_nasc)
        return data.strftime("%d/%m/%Y"), idade
    
    @classmethod
    def generate_address(cls) -> dict:
        """Gera endereço completo"""
        uf = random.choice(list(cls.CIDADES.keys()))
        cidade = random.choice(cls.CIDADES.get(uf, ["Capital"]))
        
        return {
            "logradouro": f"{random.choice(cls.LOGRADOUROS)} {random.choice(cls.SOBRENOMES)}",
            "numero": str(random.randint(1, 9999)),
            "bairro": random.choice(cls.BAIRROS),
            "cidade": cidade,
            "estado": uf,
            "cep": f"{random.randint(10000, 99999)}-{random.randint(100, 999)}"
        }
    
    @classmethod
    def generate_complete_person(cls, gender: str = None) -> dict:
        """Gera pessoa completa com todos os dados"""
        nome, genero = cls.generate_name(gender)
        data_nasc, idade = cls.generate_birth_date()
        
        return {
            "nome": nome,
            "cpf": CPFValidator.format(CPFValidator.generate()),
            "email": cls.generate_email(nome),
            "telefone": cls.generate_phone(),
            "data_nascimento": data_nasc,
            "idade": idade,
            "genero": "Masculino" if genero == "M" else "Feminino",
            "score": random.randint(300, 900),
            "endereco": cls.generate_address()
        }


# ============================================================
# WIDGET: VALIDADOR DE CPF/CNPJ
# ============================================================

class ValidadorWidget(QWidget):
    """Widget para validação de CPF e CNPJ"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("✅ Validador de CPF/CNPJ")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(title)
        
        subtitle = QLabel("Valide e gere CPFs e CNPJs válidos em tempo real")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # === CPF ===
        cpf_group = QGroupBox("CPF")
        cpf_layout = QVBoxLayout(cpf_group)
        
        # Input CPF
        cpf_input_layout = QHBoxLayout()
        self.cpf_input = QLineEdit()
        self.cpf_input.setPlaceholderText("Digite o CPF (ex: 123.456.789-00)")
        self.cpf_input.setStyleSheet("""
            QLineEdit {
                background-color: #111827;
                border: 2px solid #1e293b;
                border-radius: 10px;
                padding: 14px;
                font-size: 16px;
                color: #f1f5f9;
            }
            QLineEdit:focus {
                border-color: #06b6d4;
            }
        """)
        self.cpf_input.textChanged.connect(self._validate_cpf)
        cpf_input_layout.addWidget(self.cpf_input)
        
        # Botão gerar CPF
        self.gen_cpf_btn = QPushButton("🎲 Gerar")
        self.gen_cpf_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #f1f5f9;
                border: none;
                border-radius: 10px;
                padding: 14px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #28b84c;
            }
        """)
        self.gen_cpf_btn.clicked.connect(self._generate_cpf)
        cpf_input_layout.addWidget(self.gen_cpf_btn)
        
        # Botão copiar
        self.copy_cpf_btn = QPushButton("📋")
        self.copy_cpf_btn.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                border: none;
                border-radius: 10px;
                padding: 14px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        self.copy_cpf_btn.clicked.connect(lambda: self._copy_to_clipboard(self.cpf_input.text()))
        cpf_input_layout.addWidget(self.copy_cpf_btn)
        
        cpf_layout.addLayout(cpf_input_layout)
        
        # Resultado CPF
        self.cpf_result = QLabel("")
        self.cpf_result.setAlignment(Qt.AlignCenter)
        self.cpf_result.setStyleSheet("padding: 15px; font-size: 14px;")
        cpf_layout.addWidget(self.cpf_result)
        
        layout.addWidget(cpf_group)
        
        # === CNPJ ===
        cnpj_group = QGroupBox("CNPJ")
        cnpj_layout = QVBoxLayout(cnpj_group)
        
        # Input CNPJ
        cnpj_input_layout = QHBoxLayout()
        self.cnpj_input = QLineEdit()
        self.cnpj_input.setPlaceholderText("Digite o CNPJ (ex: 12.345.678/0001-90)")
        self.cnpj_input.setStyleSheet("""
            QLineEdit {
                background-color: #111827;
                border: 2px solid #1e293b;
                border-radius: 10px;
                padding: 14px;
                font-size: 16px;
                color: #f1f5f9;
            }
            QLineEdit:focus {
                border-color: #06b6d4;
            }
        """)
        self.cnpj_input.textChanged.connect(self._validate_cnpj)
        cnpj_input_layout.addWidget(self.cnpj_input)
        
        # Botão gerar CNPJ
        self.gen_cnpj_btn = QPushButton("🎲 Gerar")
        self.gen_cnpj_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #f1f5f9;
                border: none;
                border-radius: 10px;
                padding: 14px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #28b84c;
            }
        """)
        self.gen_cnpj_btn.clicked.connect(self._generate_cnpj)
        cnpj_input_layout.addWidget(self.gen_cnpj_btn)
        
        # Botão copiar
        self.copy_cnpj_btn = QPushButton("📋")
        self.copy_cnpj_btn.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                border: none;
                border-radius: 10px;
                padding: 14px;
                font-size: 16px;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        self.copy_cnpj_btn.clicked.connect(lambda: self._copy_to_clipboard(self.cnpj_input.text()))
        cnpj_input_layout.addWidget(self.copy_cnpj_btn)
        
        cnpj_layout.addLayout(cnpj_input_layout)
        
        # Resultado CNPJ
        self.cnpj_result = QLabel("")
        self.cnpj_result.setAlignment(Qt.AlignCenter)
        self.cnpj_result.setStyleSheet("padding: 15px; font-size: 14px;")
        cnpj_layout.addWidget(self.cnpj_result)
        
        layout.addWidget(cnpj_group)
        layout.addStretch()
    
    def _validate_cpf(self):
        cpf = self.cpf_input.text().strip()
        if not cpf or len(cpf.replace('.', '').replace('-', '')) < 11:
            self.cpf_result.setText("")
            self.cpf_result.setStyleSheet("padding: 15px;")
            return
        
        is_valid, message = CPFValidator.validate(cpf)
        
        if is_valid:
            self.cpf_result.setText(f"✅ {message}")
            self.cpf_result.setStyleSheet("""
                background: rgba(48, 209, 88, 0.2);
                color: #10b981;
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
                font-weight: 600;
            """)
        else:
            self.cpf_result.setText(f"❌ {message}")
            self.cpf_result.setStyleSheet("""
                background: rgba(255, 69, 58, 0.2);
                color: #f43f5e;
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
                font-weight: 600;
            """)
    
    def _validate_cnpj(self):
        cnpj = self.cnpj_input.text().strip()
        if not cnpj or len(cnpj.replace('.', '').replace('/', '').replace('-', '')) < 14:
            self.cnpj_result.setText("")
            self.cnpj_result.setStyleSheet("padding: 15px;")
            return
        
        is_valid, message = CNPJValidator.validate(cnpj)
        
        if is_valid:
            self.cnpj_result.setText(f"✅ {message}")
            self.cnpj_result.setStyleSheet("""
                background: rgba(48, 209, 88, 0.2);
                color: #10b981;
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
                font-weight: 600;
            """)
        else:
            self.cnpj_result.setText(f"❌ {message}")
            self.cnpj_result.setStyleSheet("""
                background: rgba(255, 69, 58, 0.2);
                color: #f43f5e;
                border-radius: 10px;
                padding: 15px;
                font-size: 14px;
                font-weight: 600;
            """)
    
    def _generate_cpf(self):
        cpf = CPFValidator.generate()
        self.cpf_input.setText(CPFValidator.format(cpf))
    
    def _generate_cnpj(self):
        cnpj = CNPJValidator.generate()
        self.cnpj_input.setText(CNPJValidator.format(cnpj))
    
    def _copy_to_clipboard(self, text: str):
        if text.strip():
            QApplication.clipboard().setText(text.strip())
            QMessageBox.information(self, "Copiado!", "Texto copiado para a área de transferência!")


# ============================================================
# WIDGET: GERADOR DE DADOS FAKE
# ============================================================

class GeradorFakeWidget(QWidget):
    """Widget para geração de dados fictícios"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("🎭 Gerador de Dados Fake")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(title)
        
        subtitle = QLabel("Gere pessoas fictícias completas para testes")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Opções
        options_group = QGroupBox("OPÇÕES")
        options_layout = QHBoxLayout(options_group)
        
        # Gênero
        options_layout.addWidget(QLabel("Gênero:"))
        self.gender_combo = QComboBox()
        self.gender_combo.addItems(["Aleatório", "Masculino", "Feminino"])
        self.gender_combo.setStyleSheet("""
            QComboBox {
                background-color: #111827;
                border: none;
                border-radius: 8px;
                padding: 10px 15px;
                min-width: 120px;
                color: #f1f5f9;
            }
        """)
        options_layout.addWidget(self.gender_combo)
        
        options_layout.addSpacing(20)
        
        # Quantidade
        options_layout.addWidget(QLabel("Quantidade:"))
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setRange(1, 50)
        self.quantity_spin.setValue(1)
        self.quantity_spin.setStyleSheet("""
            QSpinBox {
                background-color: #111827;
                border: none;
                border-radius: 8px;
                padding: 10px 15px;
                min-width: 80px;
                color: #f1f5f9;
            }
        """)
        options_layout.addWidget(self.quantity_spin)
        
        options_layout.addStretch()
        
        # Botão gerar
        self.generate_btn = QPushButton("🎲 Gerar Dados")
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #06b6d4;
                color: #f1f5f9;
                border: none;
                border-radius: 10px;
                padding: 14px 28px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0070e0;
            }
        """)
        self.generate_btn.clicked.connect(self._generate_data)
        options_layout.addWidget(self.generate_btn)
        
        layout.addWidget(options_group)
        
        # Resultado
        result_group = QGroupBox("RESULTADO")
        result_layout = QVBoxLayout(result_group)
        
        self.result_text = QTextEdit()
        self.result_text.setReadOnly(True)
        self.result_text.setStyleSheet("""
            QTextEdit {
                background-color: #0a0e1a;
                border: none;
                border-radius: 12px;
                padding: 15px;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 13px;
                color: #f1f5f9;
                line-height: 1.6;
            }
        """)
        self.result_text.setMinimumHeight(350)
        result_layout.addWidget(self.result_text)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        self.copy_btn = QPushButton("📋 Copiar Tudo")
        self.copy_btn.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                color: #06b6d4;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        self.copy_btn.clicked.connect(self._copy_all)
        btn_layout.addWidget(self.copy_btn)
        
        self.clear_btn = QPushButton("🗑️ Limpar")
        self.clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                color: #f43f5e;
                border: none;
                border-radius: 10px;
                padding: 12px 24px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        self.clear_btn.clicked.connect(lambda: self.result_text.clear())
        btn_layout.addWidget(self.clear_btn)
        
        btn_layout.addStretch()
        result_layout.addLayout(btn_layout)
        
        layout.addWidget(result_group)
    
    def _generate_data(self):
        gender_map = {"Aleatório": None, "Masculino": "M", "Feminino": "F"}
        gender = gender_map[self.gender_combo.currentText()]
        quantity = self.quantity_spin.value()
        
        results = []
        for i in range(quantity):
            person = FakeDataGenerator.generate_complete_person(gender)
            
            text = f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
👤 Nome: {person['nome']}
🆔 CPF: {person['cpf']}
📧 Email: {person['email']}
📱 Telefone: {person['telefone']}
📅 Nascimento: {person['data_nascimento']} ({person['idade']} anos)
⚧️ Gênero: {person['genero']}
⭐ Score: {person['score']}

🏠 Endereço:
   {person['endereco']['logradouro']}, {person['endereco']['numero']}
   {person['endereco']['bairro']}
   {person['endereco']['cidade']} - {person['endereco']['estado']}
   CEP: {person['endereco']['cep']}
"""
            results.append(text)
        
        self.result_text.setText('\n'.join(results))
    
    def _copy_all(self):
        text = self.result_text.toPlainText().strip()
        if text:
            QApplication.clipboard().setText(text)
            QMessageBox.information(self, "Copiado!", f"Copiado {len(text)} caracteres!")


# ============================================================
# WIDGET: BACKUP
# ============================================================

class BackupWidget(QWidget):
    """Widget para backup e restauração do banco de dados"""
    
    def __init__(self, db_path: str = None, parent=None):
        super().__init__(parent)
        self.db_path = db_path or "dados.db"
        self._setup_ui()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("💾 Backup e Restauração")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(title)
        
        subtitle = QLabel("Proteja seus dados criando backups regulares")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Info do banco
        info_group = QGroupBox("INFORMAÇÕES DO BANCO")
        info_layout = QVBoxLayout(info_group)
        
        self.db_info = QLabel("Carregando informações...")
        self.db_info.setStyleSheet("color: #64748b; padding: 10px;")
        info_layout.addWidget(self.db_info)
        
        layout.addWidget(info_group)
        
        # Ações
        actions_group = QGroupBox("AÇÕES")
        actions_layout = QVBoxLayout(actions_group)
        
        # Botão criar backup
        self.backup_btn = QPushButton("📦 Criar Backup Agora")
        self.backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #f1f5f9;
                border: none;
                border-radius: 12px;
                padding: 18px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #28b84c;
            }
        """)
        self.backup_btn.clicked.connect(self._create_backup)
        actions_layout.addWidget(self.backup_btn)
        
        # Botão restaurar
        self.restore_btn = QPushButton("🔄 Restaurar Backup")
        self.restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #f59e0b;
                color: #f1f5f9;
                border: none;
                border-radius: 12px;
                padding: 18px;
                font-weight: 600;
                font-size: 15px;
            }
            QPushButton:hover {
                background-color: #e68f09;
            }
        """)
        self.restore_btn.clicked.connect(self._restore_backup)
        actions_layout.addWidget(self.restore_btn)
        
        layout.addWidget(actions_group)
        
        # Lista de backups
        backups_group = QGroupBox("BACKUPS DISPONÍVEIS")
        backups_layout = QVBoxLayout(backups_group)
        
        self.backups_list = QListWidget()
        self.backups_list.setStyleSheet("""
            QListWidget {
                background-color: #0a0e1a;
                border: none;
                border-radius: 12px;
                padding: 10px;
            }
            QListWidget::item {
                padding: 12px;
                border-radius: 8px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background-color: rgba(10, 132, 255, 0.3);
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.1);
            }
        """)
        self.backups_list.setMinimumHeight(200)
        backups_layout.addWidget(self.backups_list)
        
        layout.addWidget(backups_group)
        
        # Atualizar info
        self._update_info()
        self._list_backups()
    
    def _update_info(self):
        try:
            if os.path.exists(self.db_path):
                size = os.path.getsize(self.db_path)
                modified = datetime.fromtimestamp(os.path.getmtime(self.db_path))
                
                if size < 1024:
                    size_str = f"{size} bytes"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                
                self.db_info.setText(
                    f"📁 Arquivo: {self.db_path}\n"
                    f"📊 Tamanho: {size_str}\n"
                    f"🕐 Última modificação: {modified.strftime('%d/%m/%Y %H:%M:%S')}"
                )
            else:
                self.db_info.setText("⚠️ Banco de dados não encontrado")
        except Exception as e:
            self.db_info.setText(f"❌ Erro ao ler informações: {e}")
    
    def _list_backups(self):
        self.backups_list.clear()
        backup_dir = Path("backups")
        
        if backup_dir.exists():
            backups = sorted(backup_dir.glob("*.db"), key=os.path.getmtime, reverse=True)
            for backup in backups[:20]:  # Últimos 20 backups
                size = os.path.getsize(backup)
                modified = datetime.fromtimestamp(os.path.getmtime(backup))
                
                if size < 1024:
                    size_str = f"{size} bytes"
                elif size < 1024 * 1024:
                    size_str = f"{size / 1024:.1f} KB"
                else:
                    size_str = f"{size / (1024 * 1024):.1f} MB"
                
                item = QListWidgetItem(
                    f"📦 {backup.name}\n"
                    f"   {size_str} • {modified.strftime('%d/%m/%Y %H:%M')}"
                )
                item.setData(Qt.UserRole, str(backup))
                self.backups_list.addItem(item)
        
        if self.backups_list.count() == 0:
            self.backups_list.addItem("Nenhum backup encontrado")
    
    def _create_backup(self):
        try:
            if not os.path.exists(self.db_path):
                QMessageBox.warning(self, "Aviso", "Banco de dados não encontrado!")
                return
            
            backup_dir = Path("backups")
            backup_dir.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = backup_dir / f"backup_{timestamp}.db"
            
            shutil.copy2(self.db_path, backup_path)
            
            QMessageBox.information(
                self, "Sucesso", 
                f"Backup criado com sucesso!\n\n{backup_path}"
            )
            
            self._list_backups()
            
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao criar backup:\n{e}")
    
    def _restore_backup(self):
        current = self.backups_list.currentItem()
        
        if not current or "Nenhum backup" in current.text():
            # Abrir diálogo para selecionar arquivo
            filepath, _ = QFileDialog.getOpenFileName(
                self, "Selecionar Backup", "", "Database (*.db);;All Files (*)"
            )
            if not filepath:
                return
            backup_path = filepath
        else:
            backup_path = current.data(Qt.UserRole)
        
        reply = QMessageBox.question(
            self, "Confirmar Restauração",
            f"Tem certeza que deseja restaurar este backup?\n\n"
            f"O banco de dados atual será substituído!\n\n"
            f"Backup: {os.path.basename(backup_path)}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                # Criar backup do atual antes de restaurar
                if os.path.exists(self.db_path):
                    backup_dir = Path("backups")
                    backup_dir.mkdir(exist_ok=True)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    shutil.copy2(self.db_path, backup_dir / f"pre_restore_{timestamp}.db")
                
                # Restaurar
                shutil.copy2(backup_path, self.db_path)
                
                QMessageBox.information(
                    self, "Sucesso",
                    "Backup restaurado com sucesso!\n\n"
                    "Reinicie a aplicação para ver as alterações."
                )
                
                self._update_info()
                self._list_backups()
                
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao restaurar backup:\n{e}")


# Exportar classes
__all__ = [
    'CPFValidator', 'CNPJValidator', 'FakeDataGenerator',
    'ValidadorWidget', 'GeradorFakeWidget', 'BackupWidget'
]


# ============================================================
# WIDGET: BUSCA AVANÇADA
# ============================================================

class BuscaAvancadaWidget(QWidget):
    """Widget para busca avançada no banco de dados"""
    
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.db = db
        self._setup_ui()
    
    def set_database(self, db):
        """Define o banco de dados para busca"""
        self.db = db
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("🔍 Busca Avançada")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(title)
        
        subtitle = QLabel("Pesquise em múltiplos campos do banco de dados")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Campo de busca
        search_group = QGroupBox("PESQUISAR")
        search_layout = QVBoxLayout(search_group)
        
        # Input de busca
        input_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Digite o termo de busca...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #111827;
                border: 2px solid #1e293b;
                border-radius: 12px;
                padding: 16px;
                font-size: 15px;
                color: #f1f5f9;
            }
            QLineEdit:focus {
                border-color: #06b6d4;
            }
        """)
        self.search_input.returnPressed.connect(self._search)
        input_layout.addWidget(self.search_input)
        
        self.search_btn = QPushButton("🔍 Buscar")
        self.search_btn.setStyleSheet("""
            QPushButton {
                background-color: #06b6d4;
                color: #f1f5f9;
                border: none;
                border-radius: 12px;
                padding: 16px 28px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #0070e0;
            }
        """)
        self.search_btn.clicked.connect(self._search)
        input_layout.addWidget(self.search_btn)
        
        search_layout.addLayout(input_layout)
        
        # Campos para buscar
        fields_layout = QHBoxLayout()
        fields_layout.addWidget(QLabel("Buscar em:"))
        
        self.check_nome = QCheckBox("Nome")
        self.check_nome.setChecked(True)
        fields_layout.addWidget(self.check_nome)
        
        self.check_cpf = QCheckBox("CPF")
        self.check_cpf.setChecked(True)
        fields_layout.addWidget(self.check_cpf)
        
        self.check_telefone = QCheckBox("Telefone")
        self.check_telefone.setChecked(True)
        fields_layout.addWidget(self.check_telefone)
        
        self.check_email = QCheckBox("Email")
        self.check_email.setChecked(True)
        fields_layout.addWidget(self.check_email)
        
        fields_layout.addStretch()
        search_layout.addLayout(fields_layout)
        
        layout.addWidget(search_group)
        
        # Resultados
        results_group = QGroupBox("RESULTADOS")
        results_layout = QVBoxLayout(results_group)
        
        self.results_label = QLabel("Nenhuma busca realizada")
        self.results_label.setStyleSheet("color: #64748b; padding: 10px;")
        results_layout.addWidget(self.results_label)
        
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(6)
        self.results_table.setHorizontalHeaderLabels([
            "Nome", "CPF", "Telefone", "Email", "Idade", "Score"
        ])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.results_table.setStyleSheet("""
            QTableWidget {
                background-color: #0a0e1a;
                border: none;
                border-radius: 12px;
                gridline-color: #111827;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #111827;
            }
            QTableWidget::item:selected {
                background-color: rgba(10, 132, 255, 0.3);
            }
            QHeaderView::section {
                background-color: #111827;
                color: #64748b;
                padding: 12px;
                border: none;
                font-weight: 600;
            }
        """)
        self.results_table.setMinimumHeight(300)
        results_layout.addWidget(self.results_table)
        
        # Botões de ação
        btn_layout = QHBoxLayout()
        
        self.copy_selected_btn = QPushButton("📋 Copiar Selecionado")
        self.copy_selected_btn.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                color: #06b6d4;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        self.copy_selected_btn.clicked.connect(self._copy_selected)
        btn_layout.addWidget(self.copy_selected_btn)
        
        self.export_btn = QPushButton("💾 Exportar Resultados")
        self.export_btn.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                color: #10b981;
                border: none;
                border-radius: 10px;
                padding: 12px 20px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        self.export_btn.clicked.connect(self._export_results)
        btn_layout.addWidget(self.export_btn)
        
        btn_layout.addStretch()
        results_layout.addLayout(btn_layout)
        
        layout.addWidget(results_group)
    
    def _search(self):
        term = self.search_input.text().strip()
        if not term:
            QMessageBox.warning(self, "Aviso", "Digite um termo para buscar!")
            return
        
        if not self.db:
            QMessageBox.warning(self, "Aviso", "Banco de dados não conectado!")
            return
        
        # Limpar tabela
        self.results_table.setRowCount(0)
        
        # Buscar no banco
        try:
            results = self.db.search(term)
            
            if not results:
                self.results_label.setText(f"Nenhum resultado encontrado para: '{term}'")
                return
            
            self.results_label.setText(f"Encontrados {len(results)} resultados para: '{term}'")
            
            for record in results:
                row = self.results_table.rowCount()
                self.results_table.insertRow(row)
                
                self.results_table.setItem(row, 0, QTableWidgetItem(str(record.get('nome', ''))))
                self.results_table.setItem(row, 1, QTableWidgetItem(str(record.get('cpf', ''))))
                self.results_table.setItem(row, 2, QTableWidgetItem(str(record.get('telefone', ''))))
                self.results_table.setItem(row, 3, QTableWidgetItem(str(record.get('email', ''))))
                self.results_table.setItem(row, 4, QTableWidgetItem(str(record.get('idade', ''))))
                self.results_table.setItem(row, 5, QTableWidgetItem(str(record.get('score', ''))))
        
        except Exception as e:
            QMessageBox.critical(self, "Erro", f"Erro ao buscar: {e}")
    
    def _copy_selected(self):
        selected = self.results_table.selectedItems()
        if not selected:
            QMessageBox.warning(self, "Aviso", "Selecione um registro para copiar!")
            return
        
        row = selected[0].row()
        data = []
        for col in range(self.results_table.columnCount()):
            item = self.results_table.item(row, col)
            if item and item.text():
                header = self.results_table.horizontalHeaderItem(col).text()
                data.append(f"{header}: {item.text()}")
        
        text = '\n'.join(data)
        QApplication.clipboard().setText(text)
        QMessageBox.information(self, "Copiado!", "Registro copiado para a área de transferência!")
    
    def _export_results(self):
        if self.results_table.rowCount() == 0:
            QMessageBox.warning(self, "Aviso", "Nenhum resultado para exportar!")
            return
        
        filepath, _ = QFileDialog.getSaveFileName(
            self, "Salvar Resultados", "busca_resultados.csv", "CSV (*.csv)"
        )
        
        if filepath:
            try:
                with open(filepath, 'w', encoding='utf-8') as f:
                    # Header
                    headers = []
                    for col in range(self.results_table.columnCount()):
                        headers.append(self.results_table.horizontalHeaderItem(col).text())
                    f.write(','.join(headers) + '\n')
                    
                    # Data
                    for row in range(self.results_table.rowCount()):
                        row_data = []
                        for col in range(self.results_table.columnCount()):
                            item = self.results_table.item(row, col)
                            row_data.append(item.text() if item else '')
                        f.write(','.join(row_data) + '\n')
                
                QMessageBox.information(self, "Sucesso", f"Resultados exportados para:\n{filepath}")
            
            except Exception as e:
                QMessageBox.critical(self, "Erro", f"Erro ao exportar: {e}")


# ============================================================
# WIDGET: DASHBOARD
# ============================================================

class DashboardWidget(QWidget):
    """Widget de dashboard com estatísticas visuais"""
    
    def __init__(self, db=None, parent=None):
        super().__init__(parent)
        self.db = db
        self._setup_ui()
        self._update_stats()
    
    def set_database(self, db):
        """Define o banco de dados"""
        self.db = db
        self._update_stats()
    
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        # Título
        title = QLabel("📊 Dashboard")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #f1f5f9;")
        layout.addWidget(title)
        
        subtitle = QLabel("Visão geral das suas estatísticas")
        subtitle.setStyleSheet("font-size: 13px; color: #64748b; margin-bottom: 20px;")
        layout.addWidget(subtitle)
        
        # Cards de estatísticas
        cards_layout = QGridLayout()
        cards_layout.setSpacing(20)
        
        # Card 1 - Total de Registros
        self.card_total = self._create_stat_card("📊", "0", "TOTAL DE REGISTROS", "#06b6d4")
        cards_layout.addWidget(self.card_total, 0, 0)
        
        # Card 2 - Com CPF
        self.card_cpf = self._create_stat_card("🆔", "0", "COM CPF", "#10b981")
        cards_layout.addWidget(self.card_cpf, 0, 1)
        
        # Card 3 - Com Telefone
        self.card_telefone = self._create_stat_card("📱", "0", "COM TELEFONE", "#f59e0b")
        cards_layout.addWidget(self.card_telefone, 1, 0)
        
        # Card 4 - Com Email
        self.card_email = self._create_stat_card("📧", "0", "COM EMAIL", "#06b6d4")
        cards_layout.addWidget(self.card_email, 1, 1)
        
        layout.addLayout(cards_layout)
        
        # Médias
        averages_group = QGroupBox("MÉDIAS")
        averages_layout = QHBoxLayout(averages_group)
        
        # Média de Idade
        self.avg_idade = self._create_avg_card("🎂", "0.0", "MÉDIA DE IDADE")
        averages_layout.addWidget(self.avg_idade)
        
        # Média de Score
        self.avg_score = self._create_avg_card("⭐", "0", "MÉDIA DE SCORE")
        averages_layout.addWidget(self.avg_score)
        
        layout.addWidget(averages_group)
        
        # Botão atualizar
        refresh_btn = QPushButton("🔄 Atualizar Estatísticas")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #111827;
                color: #06b6d4;
                border: none;
                border-radius: 12px;
                padding: 16px;
                font-weight: 600;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #1e293b;
            }
        """)
        refresh_btn.clicked.connect(self._update_stats)
        layout.addWidget(refresh_btn)
        
        layout.addStretch()
    
    def _create_stat_card(self, icon: str, value: str, label: str, color: str) -> QFrame:
        """Cria um card de estatística"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 rgba({self._hex_to_rgb(color)}, 0.2),
                    stop:1 rgba({self._hex_to_rgb(color)}, 0.1));
                border: 1px solid rgba({self._hex_to_rgb(color)}, 0.3);
                border-radius: 16px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        layout.setSpacing(10)
        
        # Ícone
        icon_label = QLabel(icon)
        icon_label.setStyleSheet(f"font-size: 32px; color: {color};")
        layout.addWidget(icon_label)
        
        # Valor
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet(f"font-size: 36px; font-weight: bold; color: {color};")
        layout.addWidget(value_label)
        
        # Label
        text_label = QLabel(label)
        text_label.setStyleSheet("font-size: 11px; color: #64748b; font-weight: 600; letter-spacing: 1px;")
        layout.addWidget(text_label)
        
        return card
    
    def _create_avg_card(self, icon: str, value: str, label: str) -> QFrame:
        """Cria um card de média"""
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background-color: #0a0e1a;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignCenter)
        
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28px;")
        icon_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(icon_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #f1f5f9;")
        value_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(value_label)
        
        text_label = QLabel(label)
        text_label.setStyleSheet("font-size: 10px; color: #64748b; font-weight: 600;")
        text_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(text_label)
        
        return card
    
    def _hex_to_rgb(self, hex_color: str) -> str:
        """Converte cor hex para RGB"""
        hex_color = hex_color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        return f"{r}, {g}, {b}"
    
    def _update_stats(self):
        """Atualiza as estatísticas do dashboard"""
        if not self.db:
            return
        
        try:
            stats = self.db.get_stats()
            
            # Atualizar cards
            self._update_card_value(self.card_total, str(stats.get('total', 0)))
            self._update_card_value(self.card_cpf, str(stats.get('with_cpf', 0)))
            self._update_card_value(self.card_telefone, str(stats.get('with_phone', 0)))
            self._update_card_value(self.card_email, str(stats.get('with_email', 0)))
            
            # Atualizar médias
            self._update_card_value(self.avg_idade, f"{stats.get('avg_age', 0):.1f}")
            self._update_card_value(self.avg_score, str(int(stats.get('avg_score', 0))))
        
        except Exception as e:
            print(f"Erro ao atualizar estatísticas: {e}")
    
    def _update_card_value(self, card: QFrame, value: str):
        """Atualiza o valor de um card"""
        value_label = card.findChild(QLabel, "value")
        if value_label:
            value_label.setText(value)


# Atualizar exports
__all__ = [
    'CPFValidator', 'CNPJValidator', 'FakeDataGenerator',
    'ValidadorWidget', 'GeradorFakeWidget', 'BackupWidget',
    'BuscaAvancadaWidget', 'DashboardWidget'
]
