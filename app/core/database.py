#!/usr/bin/env python3
"""
Gerenciador de Banco de Dados - VERSÃO OTIMIZADA
Versão 4.0 - Melhorias de Performance

OTIMIZAÇÕES IMPLEMENTADAS:
1. Connection pooling com reutilização de conexões
2. Batch inserts para importação CSV (executemany)
3. Transações otimizadas com menos commits
4. Índices compostos para queries frequentes
5. Cache de CPFs existentes para evitar queries repetidas
6. Prepared statements para queries frequentes
7. WAL mode para melhor concorrência
8. Lazy loading de dados grandes
"""
import sqlite3
import random
from typing import Tuple, List, Optional, Dict, Any, Set
from datetime import datetime, timedelta
from contextlib import contextmanager
import hashlib
import csv
import os
import re
import unicodedata
from functools import lru_cache
from threading import Lock

from settings import settings, BASE_DIR
from app.core.error_service import log_exception


def _parse_score_value(value) -> Optional[int]:
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
    return score if 0 <= score <= 1000 else None


def _normalize_search_text(value: Any) -> str:
    text = unicodedata.normalize("NFD", str(value or ""))
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return re.sub(r"\s+", " ", text.lower()).strip()


class DatabaseManager:
    """Gerenciador de banco de dados SQLite otimizado"""
    
    SCHEMA_VERSION = 5  # Nova versão com otimizações
    
    # Cache de conexão (singleton por db_path)
    _connections: Dict[str, sqlite3.Connection] = {}
    _locks: Dict[str, Lock] = {}
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or str(settings.db_path)
        
        # Criar lock para este banco se não existir
        if self.db_path not in DatabaseManager._locks:
            DatabaseManager._locks[self.db_path] = Lock()
        
        self._lock = DatabaseManager._locks[self.db_path]
        
        # Cache de CPFs para evitar queries repetidas
        self._cpf_cache: Set[str] = set()
        self._cpf_cache_loaded = False
        
        self._init_db()
    
    def _get_persistent_connection(self) -> sqlite3.Connection:
        """Retorna conexão persistente (reutilizada)"""
        if self.db_path not in DatabaseManager._connections:
            conn = sqlite3.connect(self.db_path, check_same_thread=False)
            conn.row_factory = sqlite3.Row
            
            # OTIMIZAÇÃO 1: Configurações de performance do SQLite
            conn.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
            conn.execute("PRAGMA synchronous=NORMAL")  # Menos sync, mais rápido
            conn.execute("PRAGMA cache_size=10000")  # Cache maior (10MB)
            conn.execute("PRAGMA temp_store=MEMORY")  # Temp tables em memória
            conn.execute("PRAGMA mmap_size=268435456")  # Memory-mapped I/O (256MB)
            
            DatabaseManager._connections[self.db_path] = conn
        
        return DatabaseManager._connections[self.db_path]
    
    @contextmanager
    def _get_connection(self):
        """Context manager thread-safe para conexões"""
        with self._lock:
            conn = self._get_persistent_connection()
            try:
                yield conn
            except Exception:
                conn.rollback()
                raise
    
    def _load_cpf_cache(self):
        """Carrega todos os CPFs em cache para verificação rápida"""
        if self._cpf_cache_loaded:
            return
        
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute("SELECT cpf FROM pessoas")
            self._cpf_cache = {row[0] for row in c.fetchall()}
            self._cpf_cache_loaded = True
    
    def _init_db(self):
        """Inicializa o banco de dados com otimizações"""
        with self._get_connection() as conn:
            c = conn.cursor()
            
            c.execute('''CREATE TABLE IF NOT EXISTS schema_version
                         (version INTEGER PRIMARY KEY,
                          applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
            
            c.execute('SELECT MAX(version) FROM schema_version')
            result = c.fetchone()
            current_version = result[0] if result[0] else 0
            
            self._run_migrations(conn, current_version)
    
    def _run_migrations(self, conn, current_version: int):
        """Executa migrações com índices otimizados"""
        c = conn.cursor()
        
        # Migrações 1-4 (iguais ao original)
        if current_version < 1:
            c.execute('''CREATE TABLE IF NOT EXISTS pessoas
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          nome TEXT NOT NULL,
                          cpf TEXT NOT NULL UNIQUE,
                          idade INTEGER,
                          data_nascimento TEXT,
                          telefone TEXT,
                          data_coleta TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          mensagem_id INTEGER)''')
            
            c.execute('''CREATE TABLE IF NOT EXISTS historico_sorteios
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          pessoa_id INTEGER NOT NULL,
                          data_sorteio TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                          FOREIGN KEY(pessoa_id) REFERENCES pessoas(id))''')
            
            c.execute('CREATE INDEX IF NOT EXISTS idx_cpf ON pessoas(cpf)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_idade ON pessoas(idade)')
            c.execute('INSERT INTO schema_version (version) VALUES (1)')
            conn.commit()
        
        if current_version < 2:
            columns = self._get_table_columns(c, 'pessoas')
            if 'grupo_origem' not in columns:
                c.execute('ALTER TABLE pessoas ADD COLUMN grupo_origem TEXT')
            if 'cpf_hash' not in columns:
                c.execute('ALTER TABLE pessoas ADD COLUMN cpf_hash TEXT')
            
            c.execute('CREATE INDEX IF NOT EXISTS idx_data_nasc ON pessoas(data_nascimento)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_grupo ON pessoas(grupo_origem)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_data_coleta ON pessoas(data_coleta)')
            c.execute('INSERT INTO schema_version (version) VALUES (2)')
            conn.commit()
        
        if current_version < 3:
            columns = self._get_table_columns(c, 'pessoas')
            for col in ['score', 'mae', 'endereco', 'cidade', 'estado']:
                if col not in columns:
                    col_type = 'INTEGER' if col == 'score' else 'TEXT'
                    c.execute(f'ALTER TABLE pessoas ADD COLUMN {col} {col_type}')
            
            c.execute('CREATE INDEX IF NOT EXISTS idx_score ON pessoas(score)')
            c.execute('INSERT INTO schema_version (version) VALUES (3)')
            conn.commit()
        
        if current_version < 4:
            columns = self._get_table_columns(c, 'pessoas')
            if 'ai_validated' not in columns:
                c.execute('ALTER TABLE pessoas ADD COLUMN ai_validated INTEGER DEFAULT 0')
            if 'ai_confidence' not in columns:
                c.execute('ALTER TABLE pessoas ADD COLUMN ai_confidence INTEGER')
            c.execute('INSERT INTO schema_version (version) VALUES (4)')
            conn.commit()
        
        # MIGRAÇÃO 5: Índices compostos para queries frequentes
        if current_version < 5:
            # OTIMIZAÇÃO 2: Índices compostos para filtros combinados
            c.execute('CREATE INDEX IF NOT EXISTS idx_idade_score ON pessoas(idade, score)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_nome_cpf ON pessoas(nome, cpf)')
            c.execute('CREATE INDEX IF NOT EXISTS idx_historico_data ON historico_sorteios(pessoa_id, data_sorteio)')
            
            # Índice parcial para nomes "Desconhecido" (facilita correção)
            c.execute('CREATE INDEX IF NOT EXISTS idx_nome_desconhecido ON pessoas(nome) WHERE nome = "Desconhecido"')
            
            c.execute('INSERT INTO schema_version (version) VALUES (5)')
            conn.commit()
    
    def _get_table_columns(self, cursor, table_name: str) -> List[str]:
        cursor.execute(f'PRAGMA table_info({table_name})')
        return [row[1] for row in cursor.fetchall()]
    
    @lru_cache(maxsize=10000)
    def _hash_cpf(self, cpf: str) -> str:
        """Hash de CPF com cache LRU"""
        return hashlib.sha256(cpf.encode()).hexdigest()[:16]
    
    def cpf_exists(self, cpf: str) -> bool:
        """Verifica se CPF existe usando cache"""
        self._load_cpf_cache()
        return cpf in self._cpf_cache
    
    def add_pessoa(self, nome: str, cpf: str, idade: Optional[int] = None, 
                   data_nascimento: Optional[str] = None, telefone: Optional[str] = None,
                   mensagem_id: Optional[int] = None, grupo_origem: Optional[str] = None,
                   score: Optional[int] = None, mae: Optional[str] = None,
                   endereco: Optional[str] = None, cidade: Optional[str] = None,
                   estado: Optional[str] = None) -> bool:
        """Adiciona pessoa com verificação em cache"""
        
        # OTIMIZAÇÃO 3: Verificar cache antes de query
        if self.cpf_exists(cpf):
            self._update_missing_fields(cpf, nome, idade, data_nascimento, 
                                       telefone, score, mae, endereco, cidade, estado)
            return False
        
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                c.execute('''INSERT INTO pessoas 
                            (nome, cpf, idade, data_nascimento, telefone, mensagem_id, 
                             grupo_origem, cpf_hash, score, mae, endereco, cidade, estado) 
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (nome, cpf, idade, data_nascimento, telefone, mensagem_id, 
                         grupo_origem, self._hash_cpf(cpf), score, mae, endereco, cidade, estado))
                conn.commit()
                
                # Atualizar cache
                self._cpf_cache.add(cpf)
                return True
                
        except sqlite3.IntegrityError:
            self._update_missing_fields(cpf, nome, idade, data_nascimento, 
                                       telefone, score, mae, endereco, cidade, estado)
            self._cpf_cache.add(cpf)
            return False
        except Exception as e:
            print(f"Erro ao adicionar pessoa: {e}")
            return False
    
    def _update_missing_fields(self, cpf: str, nome: Optional[str], idade: Optional[int], 
                               data_nascimento: Optional[str], telefone: Optional[str], 
                               score: Optional[int], mae: Optional[str],
                               endereco: Optional[str], cidade: Optional[str], estado: Optional[str]):
        """Atualiza campos vazios - VERSÃO OTIMIZADA"""
        updates = []
        params = []
        
        # Atualizar nome se atual for "Desconhecido"
        if nome and nome.strip() and nome.strip().upper() != 'DESCONHECIDO':
            updates.append("nome = CASE WHEN nome IS NULL OR nome = '' OR UPPER(nome) = 'DESCONHECIDO' THEN ? ELSE nome END")
            params.append(nome)
        
        # Campos com COALESCE
        field_values = [
            ('idade', idade),
            ('data_nascimento', data_nascimento),
            ('telefone', telefone),
            ('mae', mae),
            ('endereco', endereco),
            ('cidade', cidade),
            ('estado', estado)
        ]
        
        for field, value in field_values:
            if value is not None:
                updates.append(f"{field} = COALESCE({field}, ?)")
                params.append(value)

        if score is not None:
            updates.append(
                "score = CASE "
                "WHEN score IS NULL THEN ? "
                "WHEN score < 100 AND ? >= 100 THEN ? "
                "WHEN score > 1000 THEN ? "
                "ELSE score END"
            )
            params.extend([score, score, score, score])
        
        if updates:
            with self._get_connection() as conn:
                c = conn.cursor()
                params.append(cpf)
                query = f"UPDATE pessoas SET {', '.join(updates)} WHERE cpf = ?"
                c.execute(query, params)
                conn.commit()
    
    # OTIMIZAÇÃO 4: Batch insert para importação CSV
    def import_csv_optimized(self, filepath: str, batch_size: int = 1000) -> Dict[str, int]:
        """
        Importação CSV otimizada com batch inserts
        
        Melhorias:
        - Processa em lotes de 1000 registros
        - Uma única transação por lote
        - Cache de CPFs pré-carregado
        - Menos queries de verificação
        """
        stats = {'added': 0, 'updated': 0, 'errors': 0}
        
        try:
            # Pré-carregar cache de CPFs
            self._load_cpf_cache()
            
            # Detectar encoding
            encoding = 'utf-8-sig'
            try:
                with open(filepath, 'r', encoding='utf-8-sig') as f:
                    f.read(1024)
            except UnicodeDecodeError:
                encoding = 'latin-1'
            
            with open(filepath, 'r', encoding=encoding) as f:
                sample = f.read(1024)
                f.seek(0)
                
                delimiter = ';' if ';' in sample else ','
                reader = csv.DictReader(f, delimiter=delimiter)
                
                # Mapear campos
                field_map = self._create_field_map(reader.fieldnames or [])
                
                # Processar em lotes
                batch_new = []
                batch_update = []
                
                for row in reader:
                    try:
                        data = self._extract_row_data(row, field_map)
                        if not data:
                            continue
                        
                        cpf = data['cpf']
                        
                        if cpf in self._cpf_cache:
                            batch_update.append(data)
                        else:
                            batch_new.append(data)
                            self._cpf_cache.add(cpf)
                        
                        # Processar lote quando atingir tamanho
                        if len(batch_new) >= batch_size:
                            stats['added'] += self._batch_insert(batch_new)
                            batch_new = []
                        
                        if len(batch_update) >= batch_size:
                            stats['updated'] += self._batch_update(batch_update)
                            batch_update = []
                            
                    except Exception as e:
                        stats['errors'] += 1
                
                # Processar registros restantes
                if batch_new:
                    stats['added'] += self._batch_insert(batch_new)
                if batch_update:
                    stats['updated'] += self._batch_update(batch_update)
                    
        except Exception as e:
            print(f"Erro ao importar CSV: {e}")
            log_exception(BASE_DIR, "database_errors.log", "importar CSV", e)
        
        return stats
    
    def _create_field_map(self, fieldnames: List[str]) -> Dict[str, str]:
        """Cria mapeamento de campos do CSV"""
        field_map = {}
        mappings = {
            'nome': ['nome', 'name', 'full_name', 'nome_completo'],
            'cpf': ['cpf', 'documento', 'doc'],
            'idade': ['idade', 'age'],
            'data_nascimento': ['nascimento', 'data_nascimento', 'birth_date', 'data_nasc', 
                               'dt_nascimento', 'dt_nasc', 'datanascimento', 'data_de_nascimento'],
            'telefone': ['telefone', 'phone', 'celular', 'whatsapp', 'tel'],
            'score': ['score', 'pontuacao'],
            'mae': ['mae', 'mother', 'nome_mae'],
            'endereco': ['endereco', 'address', 'logradouro'],
            'cidade': ['cidade', 'city'],
            'estado': ['estado', 'state', 'uf']
        }
        
        for field in fieldnames:
            clean = field.lstrip('\ufeff').strip().lower().replace(' ', '_').replace('.', '')
            for db_field, variants in mappings.items():
                if clean in variants:
                    field_map[field] = db_field
                    break
        
        return field_map
    
    def _extract_row_data(self, row: Dict, field_map: Dict) -> Optional[Dict]:
        """Extrai dados de uma linha do CSV"""
        data = {}
        for csv_field, db_field in field_map.items():
            if csv_field in row and row[csv_field]:
                value = row[csv_field].strip()
                if db_field == 'nome' and value.upper() == 'DESCONHECIDO':
                    continue
                data[db_field] = value
        
        if 'cpf' not in data or not data['cpf']:
            return None
        
        cpf_clean = ''.join(filter(str.isdigit, data['cpf']))
        if len(cpf_clean) != 11:
            return None
        
        data['cpf'] = cpf_clean
        
        # Converter tipos
        if 'idade' in data:
            try:
                data['idade'] = int(data['idade'])
            except (ValueError, TypeError):
                data['idade'] = None
        
        if 'score' in data:
            data['score'] = _parse_score_value(data['score'])
        
        return data
    
    def _batch_insert(self, records: List[Dict]) -> int:
        """Insere múltiplos registros em uma transação"""
        if not records:
            return 0
        
        with self._get_connection() as conn:
            c = conn.cursor()
            
            # Preparar dados para executemany
            values = []
            for r in records:
                values.append((
                    r.get('nome', 'Desconhecido'),
                    r['cpf'],
                    r.get('idade'),
                    r.get('data_nascimento'),
                    r.get('telefone'),
                    None,  # mensagem_id
                    'Importação CSV',
                    self._hash_cpf(r['cpf']),
                    r.get('score'),
                    r.get('mae'),
                    r.get('endereco'),
                    r.get('cidade'),
                    r.get('estado')
                ))
            
            try:
                c.executemany('''INSERT OR IGNORE INTO pessoas 
                                (nome, cpf, idade, data_nascimento, telefone, mensagem_id, 
                                 grupo_origem, cpf_hash, score, mae, endereco, cidade, estado) 
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', values)
                conn.commit()
                return c.rowcount
            except Exception as e:
                print(f"Erro no batch insert: {e}")
                conn.rollback()
                return 0
    
    def _batch_update(self, records: List[Dict]) -> int:
        """Atualiza múltiplos registros"""
        if not records:
            return 0
        
        count = 0
        with self._get_connection() as conn:
            c = conn.cursor()
            
            for r in records:
                try:
                    updates = []
                    params = []
                    
                    if r.get('nome') and r['nome'].upper() != 'DESCONHECIDO':
                        updates.append("nome = CASE WHEN UPPER(nome) = 'DESCONHECIDO' THEN ? ELSE nome END")
                        params.append(r['nome'])
                    
                    for field in ['idade', 'data_nascimento', 'telefone', 'score', 'mae', 'endereco', 'cidade', 'estado']:
                        if r.get(field) is not None:
                            updates.append(f"{field} = COALESCE({field}, ?)")
                            params.append(r[field])
                    
                    if updates:
                        params.append(r['cpf'])
                        c.execute(f"UPDATE pessoas SET {', '.join(updates)} WHERE cpf = ?", params)
                        if c.rowcount > 0:
                            count += 1
                except (sqlite3.Error, KeyError) as e:
                    print(f"Aviso: Erro ao atualizar registro: {e}")
            
            conn.commit()
        
        return count
    
    # OTIMIZAÇÃO 5: Query otimizada para sorteio
    def get_random_pair_optimized(self, filters: Dict = None) -> Optional[Dict]:
        """Retorna par aleatório com query otimizada"""
        with self._get_connection() as conn:
            c = conn.cursor()
            
            # Usar subquery com LIMIT para melhor performance
            # FILTRO: Excluir registros com nome "Desconhecido"
            query = '''
                SELECT id, nome, cpf, idade, data_nascimento, telefone, score 
                FROM pessoas 
                WHERE id IN (
                    SELECT id FROM pessoas WHERE 1=1
                    AND nome != 'Desconhecido' 
                    AND nome IS NOT NULL 
                    AND nome != ''
            '''
            params = []
            
            if filters:
                if filters.get('require_birth'):
                    query += " AND data_nascimento IS NOT NULL AND TRIM(data_nascimento) != ''"
                if filters.get('idade_min'):
                    query += ' AND idade >= ?'
                    params.append(filters['idade_min'])
                if filters.get('idade_max'):
                    query += ' AND idade <= ?'
                    params.append(filters['idade_max'])
                if filters.get('score_min'):
                    query += ' AND score >= ?'
                    params.append(filters['score_min'])
                if filters.get('score_max'):
                    query += ' AND score <= ?'
                    params.append(filters['score_max'])
            
            # Usar ABS(RANDOM()) % count para seleção aleatória mais eficiente
            query += '''
                    ORDER BY RANDOM() LIMIT 1
                )
            '''
            
            c.execute(query, params)
            row = c.fetchone()
            
            if row:
                return {
                    'id': row['id'],
                    'nome': row['nome'],
                    'cpf': row['cpf'],
                    'idade': row['idade'],
                    'nascimento': row['data_nascimento'],
                    'telefone': row['telefone'],
                    'score': row['score']
                }
            return None
    
    # OTIMIZAÇÃO 6: Paginação com cursor para grandes datasets
    def get_all_data_paginated(self, page: int = 1, per_page: int = 100) -> Tuple[List[Dict], int]:
        """Retorna dados paginados para melhor performance"""
        with self._get_connection() as conn:
            c = conn.cursor()
            
            # Contar total (com cache se possível)
            c.execute("SELECT COUNT(*) FROM pessoas")
            total = c.fetchone()[0]
            
            # Buscar página
            offset = (page - 1) * per_page
            c.execute('''SELECT id, nome, cpf, idade, data_nascimento, telefone,
                                score, cidade, estado, data_coleta
                        FROM pessoas ORDER BY id DESC LIMIT ? OFFSET ?''',
                     (per_page, offset))
            
            results = []
            for row in c.fetchall():
                results.append({
                    'id': row['id'],
                    'nome': row['nome'],
                    'cpf': row['cpf'],
                    'idade': row['idade'],
                    'nascimento': row['data_nascimento'],
                    'telefone': row['telefone'],
                    'score': row['score'],
                    'cidade': row['cidade'],
                    'estado': row['estado'],
                    'data_coleta': row['data_coleta'],
                })
            
            return results, total

    def record_draw(self, pessoa_id: int) -> None:
        """Registra que um dado foi usado no gerador, para consulta posterior."""
        if not pessoa_id:
            return
        try:
            with self._get_connection() as conn:
                conn.execute("INSERT INTO historico_sorteios (pessoa_id) VALUES (?)", (int(pessoa_id),))
                conn.commit()
        except Exception as exc:
            log_exception(exc, "record_draw")

    def search_data(
        self,
        query: str,
        limit: int = 800,
        *,
        idade_min: Optional[int] = None,
        idade_max: Optional[int] = None,
        cpf_query: str = "",
        order_by: str = "recent",
    ) -> List[Dict]:
        """Busca ampla e tolerante em nome, CPF, telefone, nascimento e localidade."""
        query = str(query or "").strip()
        limit = max(1, min(int(limit or 800), 2000))
        cpf_digits = re.sub(r"\D", "", cpf_query or "")
        if not query and not cpf_digits and idade_min is None and idade_max is None:
            data, _ = self.get_all_data_paginated(page=1, per_page=min(limit, 1000))
            return data

        normalized_query = _normalize_search_text(query)
        tokens = [token for token in re.split(r"\s+", normalized_query) if token]
        digits = re.sub(r"\D", "", query)

        order_sql = {
            "recent": "id DESC",
            "oldest": "id ASC",
            "name": "nome COLLATE NOCASE ASC",
            "age_asc": "idade ASC, id DESC",
            "age_desc": "idade DESC, id DESC",
            "score_desc": "score DESC, id DESC",
            "score_asc": "score ASC, id DESC",
        }.get(order_by, "id DESC")

        with self._get_connection() as conn:
            c = conn.cursor()
            where = []
            params: List[Any] = []
            if idade_min is not None:
                where.append("idade >= ?")
                params.append(idade_min)
            if idade_max is not None:
                where.append("idade <= ?")
                params.append(idade_max)
            if cpf_digits:
                where.append("REPLACE(REPLACE(REPLACE(cpf, '.', ''), '-', ''), ' ', '') LIKE ?")
                params.append(f"%{cpf_digits}%")
            where_sql = "WHERE " + " AND ".join(where) if where else ""
            c.execute(f'''SELECT id, nome, cpf, idade, data_nascimento, telefone,
                                 score, cidade, estado, data_coleta
                          FROM pessoas
                          {where_sql}
                          ORDER BY {order_sql}''', params)
            results: List[Dict] = []
            for row in c:
                haystack = _normalize_search_text(
                    " ".join(
                        str(row[key] or "")
                        for key in ("id", "nome", "cpf", "idade", "data_nascimento", "telefone", "score", "cidade", "estado")
                    )
                )
                row_digits = re.sub(
                    r"\D",
                    "",
                    " ".join(str(row[key] or "") for key in ("id", "cpf", "telefone", "data_nascimento")),
                )
                token_ok = all(token in haystack for token in tokens) if tokens else True
                digit_ok = digits in row_digits if digits else True
                if token_ok and digit_ok:
                    results.append({
                        'id': row['id'],
                        'nome': row['nome'],
                        'cpf': row['cpf'],
                        'idade': row['idade'],
                        'nascimento': row['data_nascimento'],
                        'telefone': row['telefone'],
                        'score': row['score'],
                        'cidade': row['cidade'],
                        'estado': row['estado'],
                        'data_coleta': row['data_coleta'],
                    })
                    if len(results) >= limit:
                        break
            return results

    def get_recent_draws(self, limit: int = 300) -> List[Dict]:
        """Retorna os dados usados recentemente no gerador."""
        with self._get_connection() as conn:
            c = conn.cursor()
            c.execute('''SELECT h.id AS historico_id, h.data_sorteio,
                                p.id, p.nome, p.cpf, p.idade, p.data_nascimento,
                                p.telefone, p.score, p.cidade, p.estado, p.data_coleta
                         FROM historico_sorteios h
                         JOIN pessoas p ON p.id = h.pessoa_id
                         ORDER BY h.data_sorteio DESC, h.id DESC
                         LIMIT ?''', (limit,))
            results: List[Dict] = []
            for row in c.fetchall():
                results.append({
                    'id': row['id'],
                    'nome': row['nome'],
                    'cpf': row['cpf'],
                    'idade': row['idade'],
                    'nascimento': row['data_nascimento'],
                    'telefone': row['telefone'],
                    'score': row['score'],
                    'cidade': row['cidade'],
                    'estado': row['estado'],
                    'data_coleta': row['data_coleta'],
                    'data_sorteio': row['data_sorteio'],
                    'historico_id': row['historico_id'],
                })
            return results
    
    def close(self):
        """Fecha conexão persistente"""
        if self.db_path in DatabaseManager._connections:
            DatabaseManager._connections[self.db_path].close()
            del DatabaseManager._connections[self.db_path]
    
    def vacuum(self):
        """Otimiza o banco de dados (executar periodicamente)"""
        with self._get_connection() as conn:
            conn.execute("VACUUM")
            conn.execute("ANALYZE")
    
    def get_stats(self) -> Dict[str, int]:
        """Retorna estatísticas do banco"""
        with self._get_connection() as conn:
            c = conn.cursor()
            
            stats = {}
            c.execute("SELECT COUNT(*) FROM pessoas")
            stats['total'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM pessoas WHERE nome != 'Desconhecido' AND data_nascimento IS NOT NULL AND telefone IS NOT NULL")
            stats['complete'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM pessoas WHERE telefone IS NOT NULL")
            stats['with_phone'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM pessoas WHERE score IS NOT NULL")
            stats['with_score'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM pessoas WHERE data_nascimento IS NOT NULL")
            stats['with_birth'] = c.fetchone()[0]
            
            c.execute("SELECT COUNT(*) FROM pessoas WHERE data_nascimento IS NULL")
            stats['without_birth'] = c.fetchone()[0]
            
            return stats
    
    # Manter compatibilidade com métodos antigos
    def import_csv(self, filepath: str) -> Dict[str, int]:
        """Wrapper para manter compatibilidade"""
        return self.import_csv_optimized(filepath)
    
    def get_random_pair(self, filters: Dict = None) -> Optional[Dict]:
        """Wrapper para manter compatibilidade"""
        return self.get_random_pair_optimized(filters)
    
    def get_all_data(self) -> List[Dict]:
        """Wrapper para manter compatibilidade (usa paginação internamente)"""
        results, _ = self.get_all_data_paginated(page=1, per_page=10000)
        return results
    
    def export_csv(self, filepath: str, export_type: str = 'completo', mode: str = 'w') -> bool:
        """
        Exporta dados para arquivo CSV
        
        Args:
            filepath: Caminho do arquivo de saída
            export_type: Tipo de exportação ('completo', 'basico', 'telefones')
            mode: Modo de escrita ('w' para sobrescrever, 'a' para anexar)
        
        Returns:
            bool: True se exportação foi bem sucedida, False caso contrário
        """
        try:
            with self._get_connection() as conn:
                c = conn.cursor()
                
                # Definir colunas baseado no tipo de exportação
                if export_type == 'basico':
                    columns = ['nome', 'cpf', 'data_nascimento', 'telefone']
                    query = '''SELECT nome, cpf, data_nascimento, telefone FROM pessoas ORDER BY id DESC'''
                elif export_type == 'telefones':
                    columns = ['nome', 'cpf', 'telefone']
                    query = '''SELECT nome, cpf, telefone FROM pessoas WHERE telefone IS NOT NULL AND telefone != '' ORDER BY id DESC'''
                else:  # completo
                    columns = ['id', 'nome', 'cpf', 'idade', 'data_nascimento', 'telefone', 
                              'score', 'mae', 'endereco', 'cidade', 'estado', 'grupo_origem', 'data_coleta']
                    query = '''SELECT id, nome, cpf, idade, data_nascimento, telefone, 
                              score, mae, endereco, cidade, estado, grupo_origem, data_coleta 
                              FROM pessoas ORDER BY id DESC'''
                
                c.execute(query)
                rows = c.fetchall()
                
                if not rows:
                    return False
                
                # Verificar se deve escrever cabeçalho (apenas se for novo arquivo ou modo 'w')
                write_header = True
                if mode == 'a' and os.path.exists(filepath):
                    # Verificar se arquivo já tem conteúdo
                    with open(filepath, 'r', encoding='utf-8-sig') as f:
                        write_header = len(f.read().strip()) == 0
                
                with open(filepath, mode, newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f, delimiter=';', quoting=csv.QUOTE_MINIMAL)
                    
                    if write_header:
                        # Escrever cabeçalho em português
                        header_map = {
                            'id': 'ID',
                            'nome': 'Nome',
                            'cpf': 'CPF',
                            'idade': 'Idade',
                            'data_nascimento': 'Data Nascimento',
                            'telefone': 'Telefone',
                            'score': 'Score',
                            'mae': 'Nome da Mãe',
                            'endereco': 'Endereço',
                            'cidade': 'Cidade',
                            'estado': 'Estado',
                            'grupo_origem': 'Grupo Origem',
                            'data_coleta': 'Data Coleta'
                        }
                        header = [header_map.get(col, col) for col in columns]
                        writer.writerow(header)
                    
                    # Escrever dados
                    for row in rows:
                        # Converter Row para lista, tratando valores None
                        row_data = []
                        for i, value in enumerate(row):
                            if value is None:
                                row_data.append('')
                            elif columns[i] == 'cpf':
                                # Formatar CPF com pontos e traço
                                cpf = str(value)
                                if len(cpf) == 11:
                                    row_data.append(f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}')
                                else:
                                    row_data.append(cpf)
                            else:
                                row_data.append(str(value))
                        writer.writerow(row_data)
                
                return True
                
        except Exception as e:
            print(f"Erro ao exportar CSV: {e}")
            log_exception(BASE_DIR, "database_errors.log", "exportar CSV", e)
            return False
