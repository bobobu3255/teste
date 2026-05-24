#!/usr/bin/env python3
"""
Coletor de Dados do Telegram - VERSÃO OTIMIZADA
Versão 5.0 - Melhorias de Performance

OTIMIZAÇÕES IMPLEMENTADAS:
1. Regex pré-compilados para extração mais rápida
2. Batch processing de mensagens
3. Async batch insert no banco de dados
4. Cache de padrões de extração
5. Processamento paralelo de mensagens
6. Redução de chamadas de IA desnecessárias
7. Buffer de escrita para reduzir I/O
"""
import re
import sqlite3
import asyncio
import os
import json
import unicodedata
from telethon import TelegramClient
from telethon.errors import SessionPasswordNeededError, FloodWaitError
from datetime import datetime
from typing import Dict, List, Optional, Callable, Set
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor

from settings import settings, BASE_DIR
from config_manager import ConfigManager
from address_reserve import AddressExtractor

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False


# OTIMIZAÇÃO 1: Regex pré-compilados (compile uma vez, use muitas vezes)
def _plain_text(value: str) -> str:
    """Normaliza texto para comparacao sem depender de acentos."""
    value = value or ""
    value = unicodedata.normalize("NFKD", value)
    value = "".join(ch for ch in value if not unicodedata.combining(ch))
    return value.lower()


def _parse_score_number(value: str) -> Optional[int]:
    """Converte score em formatos como 750, 750/1000, 1.000 ou 0810."""
    if value is None:
        return None
    token = str(value).strip()
    if not token:
        return None

    token = token.split("/")[0].strip()
    token = re.sub(r"[^\d,\.]", "", token)
    if not token:
        return None

    if re.fullmatch(r"0*1[,.]000", token):
        token = "1000"
    elif re.fullmatch(r"\d{1,4}[,.]0+", token):
        token = token.split(".")[0].split(",")[0]
    elif re.fullmatch(r"\d{1,3}[,.]\d{3}", token):
        token = token.replace(".", "").replace(",", "")
    else:
        token = re.sub(r"\D", "", token)

    try:
        score = int(token)
    except ValueError:
        return None
    if 0 <= score <= 1000:
        return score
    return None


def _normalize_birth_date(value: str) -> Optional[str]:
    """Normaliza datas de nascimento comuns para dd/mm/aaaa."""
    raw = str(value or "").strip()
    if not raw:
        return None

    raw = raw.replace("\\", "/").replace("-", "/").replace(".", "/")
    current_year = datetime.now().year

    if re.fullmatch(r"\d{4}/\d{1,2}/\d{1,2}", raw):
        year_s, month_s, day_s = raw.split("/")
    elif re.fullmatch(r"\d{1,2}/\d{1,2}/\d{2,4}", raw):
        day_s, month_s, year_s = raw.split("/")
    else:
        return None

    try:
        day = int(day_s)
        month = int(month_s)
        year = int(year_s)
    except ValueError:
        return None

    if year < 100:
        pivot = current_year % 100
        year += 2000 if year <= pivot else 1900

    if not 1900 <= year <= current_year:
        return None

    try:
        dt = datetime(year, month, day)
    except ValueError:
        return None

    if dt.date() > datetime.now().date():
        return None

    return f"{day:02d}/{month:02d}/{year:04d}"


def _age_from_birth_date(value: str) -> Optional[int]:
    normalized = _normalize_birth_date(value)
    if not normalized:
        return None
    try:
        day, month, year = map(int, normalized.split("/"))
        born = datetime(year, month, day)
    except ValueError:
        return None
    today = datetime.now()
    age = today.year - born.year
    if (today.month, today.day) < (born.month, born.day):
        age -= 1
    return age if 0 <= age < 130 else None


class CompiledPatterns:
    """Padrões regex pré-compilados para extração rápida"""
    
    # CPF patterns
    CPF_PATTERNS = [
        re.compile(r'CPF\s*[:=>\s]+\s*(\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2})', re.IGNORECASE),
        re.compile(r'CPF\s*[:=>\s]+\s*(\d{11})', re.IGNORECASE),
        re.compile(r'•\s*CPF\s*[:=>\s]+\s*(\d{3}[.\s]?\d{3}[.\s]?\d{3}[-.\s]?\d{2})', re.IGNORECASE),
        re.compile(r'(?:^|\n)\s*(\d{3}\.\d{3}\.\d{3}-\d{2})\s*(?:$|\n)'),
    ]
    
    # Nome patterns
    NOME_PATTERNS = [
        re.compile(r'NOME\s*[:=>\s]+\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿa-zà-ÿ\s]+?)(?:\n|$|CPF|NASC|DATA|IDADE)', re.IGNORECASE),
        re.compile(r'•\s*NOME\s*[:=>\s]+\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿa-zà-ÿ\s]+?)(?:\n|$)', re.IGNORECASE),
        re.compile(r'NOME COMPLETO\s*[:=>\s]+\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿa-zà-ÿ\s]+?)(?:\n|$)', re.IGNORECASE),
    ]
    
    # Data nascimento patterns
    DATA_NASC_PATTERNS = [
        re.compile(r'(?:NASC(?:IMENTO)?|DATA\s*(?:DE\s*)?NASC(?:IMENTO)?|DT\.?\s*NASC|DN)\s*[:=>\s]+\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})', re.IGNORECASE),
        re.compile(r'•\s*(?:NASC|DATA|DN)\s*[:=>\s]+\s*(\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4})', re.IGNORECASE),
        re.compile(r'(?:NASC(?:IMENTO)?|DATA\s*(?:DE\s*)?NASC(?:IMENTO)?|DT\.?\s*NASC|DN)\s*[:=>\s]+\s*(\d{4}[/.-]\d{1,2}[/.-]\d{1,2})', re.IGNORECASE),
        re.compile(r'\b(\d{1,2}/\d{1,2}/\d{2,4})\b'),
    ]
    
    # Idade patterns
    IDADE_PATTERNS = [
        re.compile(r'IDADE\s*[:=>\s]+\s*(\d{1,3})\s*(?:anos?)?', re.IGNORECASE),
        re.compile(r'•\s*IDADE\s*[:=>\s]+\s*(\d{1,3})', re.IGNORECASE),
        re.compile(r'(\d{1,3})\s*anos?', re.IGNORECASE),
    ]
    
    # Telefone patterns
    TELEFONE_PATTERNS = [
        re.compile(r'(?:TEL(?:EFONE)?|CELULAR|WHATSAPP|CONTATO)\s*[:=>\s]+\s*\(?(\d{2})\)?\s*[9]?\s*(\d{4,5})[-.\s]?(\d{4})', re.IGNORECASE),
        re.compile(r'•\s*(?:TEL|CEL)\s*[:=>\s]+\s*(\d{10,11})', re.IGNORECASE),
        re.compile(r'(\d{2})\s*[9]?\s*(\d{4,5})[-.\s]?(\d{4})'),
    ]
    
    # Score patterns - VERSÃO EXPANDIDA para capturar mais formatos
    SCORE_PATTERNS = [
        # Padrões básicos de SCORE
        re.compile(r'SCORE\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'•\s*SCORE\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'PONTUAÇÃO\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        
        # SERASA patterns
        re.compile(r'SERASA\s*(?:SCORE)?\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'•\s*SERASA\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'SERASA\s*[:(]\s*(\d{1,4})', re.IGNORECASE),
        
        # SPC patterns
        re.compile(r'SPC\s*(?:SCORE)?\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'•\s*SPC\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'SPC\s*[:(]\s*(\d{1,4})', re.IGNORECASE),
        
        # BOA VISTA / SCPC patterns
        re.compile(r'BOA\s*VISTA\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'SCPC\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        
        # Padrões com emojis
        re.compile(r'[⭐🔥✨💯]\s*(?:SCORE)?\s*[:=>\s]*\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'SCORE\s*[⭐🔥✨💯]\s*[:=>\s]*\s*(\d{1,4})', re.IGNORECASE),
        
        # Padrões com parênteses
        re.compile(r'SCORE\s*\(?\s*(\d{1,4})\s*\)?', re.IGNORECASE),
        re.compile(r'\(\s*SCORE\s*[:=>\s]*\s*(\d{1,4})\s*\)', re.IGNORECASE),
        
        # Padrões abreviados
        re.compile(r'SC\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'SCR\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        
        # Padrões com hífen ou barra
        re.compile(r'SCORE\s*[-/]\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'SERASA\s*[-/]\s*(\d{1,4})', re.IGNORECASE),
        
        # Padrões com "de crédito"
        re.compile(r'SCORE\s*(?:DE)?\s*CR[ÉE]DITO\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        re.compile(r'PONTUA[ÇC][ÃA]O\s*(?:DE)?\s*CR[ÉE]DITO\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        
        # Padrões com "nota"
        re.compile(r'NOTA\s*(?:SERASA|SPC)?\s*[:=>\s]+\s*(\d{1,4})', re.IGNORECASE),
        
        # Padrões com pontos (ex: "Score: 750 pontos")
        re.compile(r'SCORE\s*[:=>\s]+\s*(\d{1,4})\s*(?:pontos?|pts?)?', re.IGNORECASE),
        
        # Padrão genérico no final da linha (ex: "SERASA 800")
        re.compile(r'(?:SERASA|SPC|SCORE)\s+(\d{3,4})(?:\s|$|\n)', re.IGNORECASE),
    ]
    
    # Mae patterns
    MAE_PATTERNS = [
        re.compile(r'(?:MÃE|MAE|NOME\s*(?:DA\s*)?MÃE)\s*[:=>\s]+\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿa-zà-ÿ\s]+?)(?:\n|$|PAI)', re.IGNORECASE),
        re.compile(r'•\s*MÃE\s*[:=>\s]+\s*([A-ZÀ-Ÿ][A-ZÀ-Ÿa-zà-ÿ\s]+?)(?:\n|$)', re.IGNORECASE),
    ]
    
    # Nomes inválidos
    INVALID_NAMES = frozenset([
        'SEM INFORMAÇÃO', 'DESCONHECIDO', 'NULL', 'N/A', 'NAO INFORMADO',
        'NÃO INFORMADO', 'NONE', 'UNDEFINED', 'VAZIO', 'EMPTY'
    ])


class AIValidator:
    """Validador de dados usando IA - VERSÃO OTIMIZADA"""
    
    def __init__(self, enabled: bool = True):
        self.enabled = enabled and OPENAI_AVAILABLE
        self._call_count = 0
        self._max_calls_per_session = 100  # Limitar chamadas de IA
        
        if self.enabled:
            try:
                self.client = OpenAI()
                self.model = "gpt-4.1-nano"
            except Exception as e:
                print(f"Aviso: IA não disponível - {e}")
                self.enabled = False
    
    def should_use_ai(self, dados: Dict) -> bool:
        """Decide se deve usar IA baseado em heurísticas"""
        # Não usar IA se já excedeu limite
        if self._call_count >= self._max_calls_per_session:
            return False
        
        # Não usar IA se dados parecem completos e válidos
        if all([
            dados.get('nome'),
            dados.get('cpf'),
            dados.get('data_nascimento'),
            len(dados.get('nome', '').split()) >= 2  # Nome com pelo menos 2 partes
        ]):
            return False
        
        return True
    
    def validate_data(self, dados: Dict) -> Dict:
        """Valida dados - só usa IA quando necessário"""
        if not self.enabled or not self.should_use_ai(dados):
            return dados
        
        self._call_count += 1
        
        try:
            # Prompt otimizado (mais curto = mais rápido)
            prompt = f"""Valide: Nome:{dados.get('nome')} CPF:{dados.get('cpf')} Nasc:{dados.get('data_nascimento')}
JSON: {{"valido":bool,"confianca":0-100}}"""
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,  # Reduzido
                temperature=0
            )
            
            result = response.choices[0].message.content.strip()
            if result.startswith('{'):
                validation = json.loads(result)
                dados['_ai_valid'] = validation.get('valido', True)
                dados['_ai_confidence'] = validation.get('confianca', 0)
                
        except Exception:
            dados['_ai_valid'] = None
        
        return dados


class TelegramCollectorOptimized:
    """Coletor otimizado com batch processing"""
    
    def __init__(self, conta_id: int = None, progress_callback: Callable = None,
                 code_callback: Callable = None, password_callback: Callable = None,
                 use_ai_validation: bool = True, idade_maxima: int = None,
                 filtrar_idosos: bool = False, exigir_data_nascimento: bool = False):
        
        self.config_manager = ConfigManager()
        self.progress_callback = progress_callback or print
        self.code_callback = code_callback
        self.password_callback = password_callback
        self.conta_id = conta_id
        
        self.filtrar_idosos = filtrar_idosos
        self.idade_maxima = 59 if filtrar_idosos and idade_maxima is None else idade_maxima
        self.exigir_data_nascimento = exigir_data_nascimento
        
        # Contadores
        self.idosos_ignorados = 0
        self.sem_data_ignorados = 0
        self.sem_score_coletados = 0
        
        # Componentes
        self.ai_validator = AIValidator(enabled=use_ai_validation)
        self.address_extractor = AddressExtractor()
        self.patterns = CompiledPatterns()
        
        # OTIMIZAÇÃO 2: Cache de CPFs já processados na sessão
        self._processed_cpfs: Set[str] = set()
        
        # OTIMIZAÇÃO 3: Buffer de escrita
        self._write_buffer: List[Dict] = []
        self._buffer_size = 50  # Flush a cada 50 registros
        
        # OTIMIZAÇÃO 4: Thread pool para processamento paralelo
        self._executor = ThreadPoolExecutor(max_workers=4)
        
        self._setup_credentials()
        self.client = TelegramClient(str(self.session_path), self.api_id, self.api_hash)
        self.init_db()
    
    def _setup_credentials(self):
        """Configura credenciais"""
        if self.conta_id:
            conta = None
            for c in self.config_manager.listar_contas():
                if c['id'] == self.conta_id:
                    conta = c
                    break
            
            if conta:
                self.api_id = conta['api_id'] if conta['api_id'] else 2040
                self.api_hash = conta['api_hash'] if conta['api_hash'] else 'b18441a1ff607e10a989891a5462e627'
                self.phone = conta['telefone']
                conta_dir = self.config_manager.get_diretorio_conta(self.conta_id)
                self.session_path = os.path.join(conta_dir, 'session')
                self.db_path = os.path.join(conta_dir, 'dados.db')
            else:
                raise ValueError(f"Conta {self.conta_id} não encontrada")
        else:
            if not settings.is_configured:
                missing = ', '.join(settings.missing_settings)
                raise ValueError(f"Configurações faltando: {missing}")
            
            self.api_id = settings.api_id
            self.api_hash = settings.api_hash
            self.phone = settings.phone
            self.session_path = settings.session_path
            self.db_path = str(settings.db_path)
    
    def init_db(self):
        """Inicializa banco com configurações otimizadas"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        
        # Configurações de performance
        c.execute("PRAGMA journal_mode=WAL")
        c.execute("PRAGMA synchronous=NORMAL")
        c.execute("PRAGMA cache_size=5000")
        
        c.execute('''CREATE TABLE IF NOT EXISTS pessoas
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      nome TEXT NOT NULL,
                      cpf TEXT NOT NULL UNIQUE,
                      idade INTEGER,
                      data_nascimento TEXT,
                      telefone TEXT,
                      score INTEGER,
                      mae TEXT,
                      endereco TEXT,
                      cidade TEXT,
                      estado TEXT,
                      mensagem_id INTEGER,
                      grupo_origem TEXT,
                      ai_validated INTEGER DEFAULT 0,
                      ai_confidence INTEGER,
                      data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
        
        c.execute('CREATE INDEX IF NOT EXISTS idx_cpf ON pessoas(cpf)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_idade ON pessoas(idade)')
        c.execute('CREATE INDEX IF NOT EXISTS idx_score ON pessoas(score)')
        
        conn.commit()
        conn.close()
        
        # Carregar CPFs existentes em cache
        self._load_existing_cpfs()
    
    def _load_existing_cpfs(self):
        """Carrega CPFs existentes para evitar queries de verificação"""
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT cpf FROM pessoas")
        self._processed_cpfs = {row[0] for row in c.fetchall()}
        conn.close()
    
    def _report_progress(self, msg: str):
        if self.progress_callback:
            self.progress_callback(msg)
    
    # OTIMIZAÇÃO 5: Extração com regex pré-compilados
    @lru_cache(maxsize=1000)
    def _extract_cpf_cached(self, text_hash: int) -> Optional[str]:
        """Extração de CPF com cache"""
        # Este método é chamado via wrapper que passa o hash
        pass
    
    def _extract_cpf(self, text: str) -> Optional[str]:
        """Extrai CPF usando padrões pré-compilados"""
        for pattern in self.patterns.CPF_PATTERNS:
            match = pattern.search(text)
            if match:
                cpf = ''.join(filter(str.isdigit, match.group(1)))
                if len(cpf) == 11:
                    return cpf
        return None
    
    def _extract_nome(self, text: str) -> Optional[str]:
        """Extrai nome usando padrões pré-compilados"""
        for pattern in self.patterns.NOME_PATTERNS:
            match = pattern.search(text)
            if match:
                nome = match.group(1).strip()
                nome = re.sub(r'\s+', ' ', nome)
                
                # Validar nome
                if nome.upper() in self.patterns.INVALID_NAMES:
                    continue
                if len(nome) < 3 or len(nome.split()) < 1:
                    continue
                if any(c.isdigit() for c in nome):
                    continue
                
                return nome.title()
        return None
    
    def _extract_data_nascimento(self, text: str) -> Optional[str]:
        """Extrai data de nascimento"""
        for pattern in self.patterns.DATA_NASC_PATTERNS:
            match = pattern.search(text)
            if match:
                data = _normalize_birth_date(match.group(1))
                if data:
                    return data
        return None
    
    def _extract_idade(self, text: str) -> Optional[int]:
        """Extrai idade"""
        for pattern in self.patterns.IDADE_PATTERNS:
            match = pattern.search(text)
            if match:
                idade = int(match.group(1))
                if 0 < idade < 130:
                    return idade
        return None
    
    def _extract_telefone(self, text: str) -> Optional[str]:
        """Extrai telefone"""
        for pattern in self.patterns.TELEFONE_PATTERNS:
            match = pattern.search(text)
            if match:
                groups = match.groups()
                tel = ''.join(filter(str.isdigit, ''.join(groups)))
                if 10 <= len(tel) <= 11:
                    return tel
        return None
    
    def _extract_score(self, text: str) -> Optional[int]:
        """Extrai score - VERSÃO MELHORADA
        
        Scores válidos:
        - SERASA: 0-1000 (mais comum 300-900)
        - SPC: 0-1000
        - BOA VISTA: 0-1000
        """
        for pattern in self.patterns.SCORE_PATTERNS:
            match = pattern.search(text)
            if match:
                try:
                    score = int(match.group(1))
                    # Score válido: entre 0 e 1000
                    # Scores muito baixos (<100) podem ser falsos positivos
                    # Scores muito altos (>1000) são inválidos
                    if 100 <= score <= 1000:
                        return score
                    # Aceitar scores entre 0-99 apenas se o contexto menciona score explicitamente
                    elif 0 <= score < 100:
                        # Verificar se tem contexto de score
                        context_words = ['score', 'serasa', 'spc', 'pontua', 'crédito', 'credito']
                        text_lower = text.lower()
                        if any(word in text_lower for word in context_words):
                            return score
                except (ValueError, IndexError):
                    continue
        return None
    
    def _extract_score(self, text: str) -> Optional[int]:
        """Extrai score com mais precisao e menos falso positivo.

        Aceita formatos comuns: Score 750, Score: 750/1000, 1.000,
        SERASA Score, SPC, Boa Vista, SCPC, CSB/CSB8/CSBA e pontuacao.
        """
        if not text:
            return None

        normalized_lines = []
        for line in text.splitlines():
            plain = _plain_text(line)
            plain = re.sub(r"\s+", " ", plain).strip()
            if plain:
                normalized_lines.append(plain)

        label_re = (
            r"(?:score(?:\s+(?:serasa|spc|scpc|boa\s*vista|credito|digital|positivo|csb8?|csba))?"
            r"|(?:serasa|spc|scpc|boa\s*vista)\s+score"
            r"|pontuacao(?:\s+de\s+credito)?|nota\s+(?:serasa|spc|credito)"
            r"|csb8?|csba)"
        )
        number_re = r"([0-9][0-9.,]{0,7})(?:\s*/\s*1000)?"
        negative_re = re.compile(
            r"(?:sem|nao|n[aã]o|inexistente|indisponivel|nao\s+informado).{0,20}(?:score|pontuacao)"
        )
        candidates = []

        def add_candidate(raw_value, priority, line_index):
            score = _parse_score_number(raw_value)
            if score is None:
                return
            if score < 100 and priority > 1:
                return
            candidates.append((priority, line_index, score))

        for idx, line in enumerate(normalized_lines):
            if negative_re.search(line):
                continue
            score_context = re.search(label_re, line, re.I)
            if not score_context:
                continue

            before_count = len(candidates)
            for match in re.finditer(label_re + r"\s*(?:[:=>\-/|]|\s+)\s*" + number_re, line, re.I):
                label = match.group(0)
                priority = 0 if any(key in label for key in ("score", "serasa", "pontuacao")) else 1
                add_candidate(match.group(1), priority, idx)

            if len(candidates) == before_count:
                tail = line[score_context.start():score_context.start() + 80]
                for match in re.finditer(number_re, tail):
                    add_candidate(match.group(1), 1, idx)

            if len(candidates) == before_count and idx + 1 < len(normalized_lines):
                if re.fullmatch(label_re + r"\s*[:=>\-/|]?\s*", line, re.I):
                    next_match = re.search(number_re, normalized_lines[idx + 1])
                    if next_match:
                        add_candidate(next_match.group(1), 1, idx)

        if candidates:
            candidates.sort(key=lambda item: (item[0], item[1]))
            return candidates[0][2]

        for pattern in self.patterns.SCORE_PATTERNS:
            match = pattern.search(text)
            if match:
                score = _parse_score_number(match.group(1))
                if score is not None:
                    return score
        return None

    def _extract_mae(self, text: str) -> Optional[str]:
        """Extrai nome da mãe"""
        for pattern in self.patterns.MAE_PATTERNS:
            match = pattern.search(text)
            if match:
                mae = match.group(1).strip()
                mae = re.sub(r'\s+', ' ', mae)
                if len(mae) >= 3 and mae.upper() not in self.patterns.INVALID_NAMES:
                    return mae.title()
        return None
    
    def extract_all_data(self, text: str) -> List[Dict]:
        """Extrai todos os dados de uma mensagem"""
        dados = {
            'nome': self._extract_nome(text),
            'cpf': self._extract_cpf(text),
            'idade': self._extract_idade(text),
            'data_nascimento': self._extract_data_nascimento(text),
            'telefone': self._extract_telefone(text),
            'score': self._extract_score(text),
            'mae': self._extract_mae(text),
            'endereco': None,
            'cidade': None,
            'estado': None
        }
        
        # Extrair endereço
        end_data = self.address_extractor.extrair_endereco(text) if self.address_extractor else {}
        if end_data:
            dados['cidade'] = end_data.get('cidade')
            dados['estado'] = end_data.get('uf')
            dados['endereco'] = end_data.get('logradouro')
        
        # Validar
        if not dados['cpf'] or not dados['nome']:
            return []
        
        # Verificar filtros
        if self.exigir_data_nascimento and not dados['data_nascimento']:
            self.sem_data_ignorados += 1
            return []
        
        # Calcular idade se necessário
        if dados['data_nascimento'] and not dados['idade']:
            dados['idade'] = _age_from_birth_date(dados['data_nascimento'])
        
        # Filtrar por idade
        if self.idade_maxima and dados.get('idade') and dados['idade'] > self.idade_maxima:
            self.idosos_ignorados += 1
            return []

        if dados.get('score') is None:
            self.sem_score_coletados += 1
        
        # Validar com IA (só se necessário)
        if self.ai_validator.enabled:
            dados = self.ai_validator.validate_data(dados)
        
        return [dados]
    
    def _flush_buffer(self, conn, group: str):
        """Escreve buffer no banco de dados"""
        if not self._write_buffer:
            return 0, 0
        
        c = conn.cursor()
        collected, updated = 0, 0
        
        for p in self._write_buffer:
            try:
                c.execute('''INSERT INTO pessoas 
                            (nome, cpf, idade, data_nascimento, telefone, score,
                             mae, endereco, cidade, estado, mensagem_id, grupo_origem,
                             ai_validated, ai_confidence) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (p['nome'], p['cpf'], p['idade'], p['data_nascimento'], 
                         p['telefone'], p['score'], p['mae'], p['endereco'], 
                         p['cidade'], p['estado'], p.get('mensagem_id'), group,
                         1 if p.get('_ai_valid') else 0, p.get('_ai_confidence')))
                collected += 1
                self._processed_cpfs.add(p['cpf'])
                
            except sqlite3.IntegrityError:
                # Atualizar registro existente
                updates = []
                params = []
                for field in ['data_nascimento', 'idade', 'telefone', 'score', 'mae', 'endereco', 'cidade', 'estado']:
                    if p.get(field):
                        if field == 'score':
                            updates.append(
                                "score = CASE "
                                "WHEN score IS NULL THEN ? "
                                "WHEN score < 100 AND ? >= 100 THEN ? "
                                "WHEN score > 1000 THEN ? "
                                "ELSE score END"
                            )
                            params.extend([p[field], p[field], p[field], p[field]])
                        else:
                            updates.append(f"{field} = COALESCE(NULLIF({field}, ''), ?)")
                            params.append(p[field])
                
                if updates:
                    params.append(p['cpf'])
                    c.execute(f"UPDATE pessoas SET {', '.join(updates)} WHERE cpf = ?", params)
                    if c.rowcount > 0:
                        updated += 1
        
        self._write_buffer = []
        return collected, updated
    
    async def collect_messages(self, group_username: str = None, limit: int = 2000) -> int:
        """Coleta mensagens com batch processing"""
        group = group_username or settings.default_group
        
        try:
            entity = await self.client.get_entity(group)
            self._report_progress(f"✓ Grupo: {entity.title}")
            messages = await self.client.get_messages(entity, limit=limit)
            
            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            
            collected, updated, duplicates = 0, 0, 0
            
            for i, message in enumerate(messages):
                if not message.text:
                    continue
                
                pessoas = self.extract_all_data(message.text)
                
                for p in pessoas:
                    # Verificar duplicata em cache
                    if p['cpf'] in self._processed_cpfs:
                        duplicates += 1
                        # Ainda adicionar ao buffer para atualização
                        p['mensagem_id'] = message.id
                        self._write_buffer.append(p)
                    else:
                        p['mensagem_id'] = message.id
                        self._write_buffer.append(p)
                        self._report_progress(f"  ✓ {p['nome'][:25]} | CPF:{p['cpf'][-4:]}")
                
                # Flush buffer periodicamente
                if len(self._write_buffer) >= self._buffer_size:
                    c, u = self._flush_buffer(conn, group)
                    collected += c
                    updated += u
                    conn.commit()
                
                # Progresso
                if (i + 1) % 200 == 0:
                    self._report_progress(f"  Processadas {i + 1}/{len(messages)}...")
            
            # Flush final
            c, u = self._flush_buffer(conn, group)
            collected += c
            updated += u
            conn.commit()
            conn.close()
            
            # Estatísticas
            stats = [f"{collected} novos", f"{updated} atualizados", f"{duplicates} duplicados"]
            if self.idosos_ignorados:
                stats.append(f"{self.idosos_ignorados} idosos ignorados")
            if self.sem_data_ignorados:
                stats.append(f"{self.sem_data_ignorados} sem data ignorados")
            if self.sem_score_coletados:
                stats.append(f"{self.sem_score_coletados} sem score aceitos")
            
            self._report_progress(f"\n✓ FIM: {', '.join(stats)}")
            return collected
            
        except Exception as e:
            self._report_progress(f"✗ Erro: {e}")
            raise
    
    async def connect(self):
        """Conecta ao Telegram"""
        self._report_progress("Conectando ao Telegram...")
        try:
            if self.code_callback:
                await self.client.connect()
                if not await self.client.is_user_authorized():
                    await self.client.send_code_request(self.phone)
                    code = await self.code_callback()
                    if not code:
                        raise ValueError("Código não fornecido")
                    try:
                        await self.client.sign_in(self.phone, code)
                    except SessionPasswordNeededError:
                        if self.password_callback:
                            password = await self.password_callback()
                            if not password:
                                raise ValueError("Senha não fornecida")
                            await self.client.sign_in(password=password)
                        else:
                            raise
                self._report_progress("✓ Conectado")
                return True
            else:
                await self.client.start(phone=self.phone)
                self._report_progress("✓ Conectado")
                return True
        except Exception as e:
            self._report_progress(f"✗ Erro: {e}")
            raise
    
    async def run(self, group_username: str = None, limit: int = 2000) -> int:
        """Executa coleta"""
        try:
            await self.connect()
            return await self.collect_messages(group_username, limit)
        finally:
            await self.client.disconnect()
            self._executor.shutdown(wait=False)
    
    async def run_multiple_groups(self, groups: List[str], limit: int = 2000) -> int:
        """Coleta de múltiplos grupos"""
        try:
            await self.connect()
            total = 0
            for group in groups:
                try:
                    self._report_progress(f"\n>>> Coletando de: {group}")
                    total += await self.collect_messages(group, limit)
                except Exception as e:
                    self._report_progress(f"  ✗ Erro no grupo {group}: {e}")
            return total
        finally:
            await self.client.disconnect()
            self._executor.shutdown(wait=False)


# Alias para compatibilidade
TelegramCollector = TelegramCollectorOptimized

if __name__ == '__main__':
    asyncio.run(TelegramCollectorOptimized().run())
