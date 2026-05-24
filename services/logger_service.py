#!/usr/bin/env python3
"""
LoggerService - Sistema de Logging Estruturado Profissional
Versão 2.0 - Logging avançado com suporte a JSON, rotação, contexto e métricas

Características:
- Logging estruturado em JSON para análise
- Rotação automática de arquivos por tamanho e data
- Contexto de execução (request_id, user_id, etc)
- Métricas de performance integradas
- Suporte a múltiplos outputs (console, arquivo, UI)
- Níveis de log configuráveis por módulo
- Sanitização de dados sensíveis
- Exportação de logs em múltiplos formatos
"""
import logging
import logging.handlers
import json
import os
import sys
import traceback
import threading
import time
import gzip
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Callable, Dict, Any, List, Union
from enum import Enum
from dataclasses import dataclass, field, asdict
from contextlib import contextmanager
from functools import wraps
import uuid


class LogLevel(Enum):
    """Níveis de log disponíveis"""
    TRACE = 5
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


@dataclass
class LogContext:
    """Contexto de execução para logs"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4())[:8])
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    module: Optional[str] = None
    operation: Optional[str] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte contexto para dicionário"""
        result = {
            'request_id': self.request_id,
        }
        if self.user_id:
            result['user_id'] = self.user_id
        if self.session_id:
            result['session_id'] = self.session_id
        if self.module:
            result['module'] = self.module
        if self.operation:
            result['operation'] = self.operation
        if self.extra:
            result.update(self.extra)
        return result


@dataclass
class LogEntry:
    """Entrada de log estruturada"""
    timestamp: str
    level: str
    message: str
    logger_name: str
    context: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[str] = None
    duration_ms: Optional[float] = None
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Converte entrada para dicionário"""
        result = {
            'timestamp': self.timestamp,
            'level': self.level,
            'message': self.message,
            'logger': self.logger_name,
        }
        if self.context:
            result['context'] = self.context
        if self.exception:
            result['exception'] = self.exception
        if self.duration_ms is not None:
            result['duration_ms'] = self.duration_ms
        if self.extra:
            result['extra'] = self.extra
        return result
    
    def to_json(self) -> str:
        """Converte entrada para JSON"""
        return json.dumps(self.to_dict(), ensure_ascii=False)


class SensitiveDataFilter(logging.Filter):
    """Filtro para sanitizar dados sensíveis nos logs"""
    
    SENSITIVE_PATTERNS = [
        'password', 'senha', 'token', 'api_key', 'secret',
        'credit_card', 'cartao', 'cpf', 'cnpj', 'cvv'
    ]
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Sanitiza dados sensíveis na mensagem"""
        if hasattr(record, 'msg') and isinstance(record.msg, str):
            for pattern in self.SENSITIVE_PATTERNS:
                if pattern.lower() in record.msg.lower():
                    record.msg = self._sanitize_message(record.msg, pattern)
        return True
    
    def _sanitize_message(self, msg: str, pattern: str) -> str:
        """Substitui valores sensíveis por asteriscos"""
        import re
        # Padrão para encontrar key=value ou key:value
        regex = rf'({pattern}["\']?\s*[:=]\s*["\']?)([^"\'\s,}}]+)'
        return re.sub(regex, r'\1****', msg, flags=re.IGNORECASE)


class JSONFormatter(logging.Formatter):
    """Formatador JSON para logs estruturados"""
    
    def __init__(self, include_context: bool = True):
        super().__init__()
        self.include_context = include_context
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata o registro como JSON"""
        entry = LogEntry(
            timestamp=datetime.fromtimestamp(record.created).isoformat(),
            level=record.levelname,
            message=record.getMessage(),
            logger_name=record.name,
        )
        
        # Adicionar contexto se disponível
        if self.include_context and hasattr(record, 'context'):
            entry.context = record.context
        
        # Adicionar exceção se houver
        if record.exc_info:
            entry.exception = self.formatException(record.exc_info)
        
        # Adicionar duração se disponível
        if hasattr(record, 'duration_ms'):
            entry.duration_ms = record.duration_ms
        
        # Adicionar extras
        if hasattr(record, 'extra_data'):
            entry.extra = record.extra_data
        
        return entry.to_json()


class ColoredFormatter(logging.Formatter):
    """Formatador com cores para console"""
    
    COLORS = {
        'TRACE': '\033[90m',      # Cinza
        'DEBUG': '\033[36m',      # Ciano
        'INFO': '\033[32m',       # Verde
        'WARNING': '\033[33m',    # Amarelo
        'ERROR': '\033[31m',      # Vermelho
        'CRITICAL': '\033[35m',   # Magenta
    }
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Formata com cores"""
        color = self.COLORS.get(record.levelname, '')
        
        # Timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%H:%M:%S')
        
        # Nível com cor
        level = f"{color}{self.BOLD}[{record.levelname:^8}]{self.RESET}"
        
        # Nome do logger simplificado
        logger_name = record.name.split('.')[-1] if '.' in record.name else record.name
        
        # Mensagem
        message = record.getMessage()
        
        # Contexto se disponível
        context_str = ""
        if hasattr(record, 'context') and record.context:
            ctx = record.context
            if 'request_id' in ctx:
                context_str = f" [{ctx['request_id']}]"
        
        # Duração se disponível
        duration_str = ""
        if hasattr(record, 'duration_ms') and record.duration_ms is not None:
            duration_str = f" ({record.duration_ms:.2f}ms)"
        
        formatted = f"{color}[{timestamp}]{self.RESET} {level} {logger_name}{context_str}: {message}{duration_str}"
        
        # Adicionar exceção se houver
        if record.exc_info:
            formatted += f"\n{self.formatException(record.exc_info)}"
        
        return formatted


class CompressedRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """Handler com rotação e compressão de arquivos antigos"""
    
    def doRollover(self):
        """Executa rotação com compressão"""
        if self.stream:
            self.stream.close()
            self.stream = None
        
        if self.backupCount > 0:
            # Comprimir arquivo atual antes de rotacionar
            for i in range(self.backupCount - 1, 0, -1):
                sfn = self.rotation_filename(f"{self.baseFilename}.{i}.gz")
                dfn = self.rotation_filename(f"{self.baseFilename}.{i + 1}.gz")
                if os.path.exists(sfn):
                    if os.path.exists(dfn):
                        os.remove(dfn)
                    os.rename(sfn, dfn)
            
            dfn = self.rotation_filename(f"{self.baseFilename}.1.gz")
            if os.path.exists(dfn):
                os.remove(dfn)
            
            # Comprimir arquivo atual
            if os.path.exists(self.baseFilename):
                with open(self.baseFilename, 'rb') as f_in:
                    with gzip.open(dfn, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(self.baseFilename)
        
        if not self.delay:
            self.stream = self._open()


class UIHandler(logging.Handler):
    """Handler para enviar logs para interface gráfica"""
    
    def __init__(self, callback: Callable[[str, str, Dict], None]):
        super().__init__()
        self.callback = callback
        self._lock = threading.Lock()
    
    def emit(self, record: logging.LogRecord):
        """Envia log para UI"""
        try:
            with self._lock:
                msg = self.format(record)
                context = getattr(record, 'context', {})
                self.callback(msg, record.levelname, context)
        except Exception:
            self.handleError(record)


class LoggerService:
    """Serviço de logging centralizado e profissional"""
    
    _instance = None
    _lock = threading.Lock()
    _context_var = threading.local()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(LoggerService, cls).__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa o serviço de logging"""
        if self._initialized:
            return
        
        self._initialized = True
        self._loggers: Dict[str, logging.Logger] = {}
        self._ui_handlers: List[UIHandler] = []
        self._metrics: Dict[str, Any] = {
            'total_logs': 0,
            'logs_by_level': {},
            'errors_count': 0,
            'start_time': datetime.now().isoformat()
        }
        
        # Configurar diretórios
        self.base_dir = Path(os.path.expanduser("~/.telegram_collector"))
        self.log_dir = self.base_dir / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Adicionar nível TRACE
        logging.addLevelName(LogLevel.TRACE.value, 'TRACE')
        
        # Configurar logger raiz
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Configura o logger raiz com handlers profissionais"""
        root_logger = logging.getLogger()
        root_logger.setLevel(LogLevel.DEBUG.value)
        
        # Remover handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Handler para arquivo JSON (logs estruturados)
        json_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.json"
        json_handler = CompressedRotatingFileHandler(
            json_file,
            maxBytes=50 * 1024 * 1024,  # 50MB
            backupCount=10,
            encoding='utf-8'
        )
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JSONFormatter(include_context=True))
        json_handler.addFilter(SensitiveDataFilter())
        
        # Handler para arquivo texto (logs legíveis)
        text_file = self.log_dir / f"app_{datetime.now().strftime('%Y%m%d')}.log"
        text_handler = CompressedRotatingFileHandler(
            text_file,
            maxBytes=20 * 1024 * 1024,  # 20MB
            backupCount=5,
            encoding='utf-8'
        )
        text_handler.setLevel(logging.INFO)
        text_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        text_handler.setFormatter(text_formatter)
        text_handler.addFilter(SensitiveDataFilter())
        
        # Handler para console com cores
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(ColoredFormatter())
        console_handler.addFilter(SensitiveDataFilter())
        
        root_logger.addHandler(json_handler)
        root_logger.addHandler(text_handler)
        root_logger.addHandler(console_handler)
    
    def get_logger(self, name: str) -> logging.Logger:
        """
        Obtém ou cria um logger com o nome especificado
        
        Args:
            name: Nome do logger (geralmente __name__)
        
        Returns:
            Logger configurado
        """
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        
        return self._loggers[name]
    
    def set_context(self, context: LogContext):
        """Define o contexto de execução para a thread atual"""
        self._context_var.context = context
    
    def get_context(self) -> Optional[LogContext]:
        """Obtém o contexto de execução da thread atual"""
        return getattr(self._context_var, 'context', None)
    
    def clear_context(self):
        """Limpa o contexto de execução da thread atual"""
        if hasattr(self._context_var, 'context'):
            delattr(self._context_var, 'context')
    
    @contextmanager
    def context(self, **kwargs):
        """Context manager para definir contexto temporário"""
        old_context = self.get_context()
        new_context = LogContext(**kwargs)
        self.set_context(new_context)
        try:
            yield new_context
        finally:
            if old_context:
                self.set_context(old_context)
            else:
                self.clear_context()
    
    def add_ui_handler(self, callback: Callable[[str, str, Dict], None]):
        """
        Adiciona handler para enviar logs para UI
        
        Args:
            callback: Função que recebe (mensagem, nível, contexto)
        """
        handler = UIHandler(callback)
        handler.setLevel(logging.INFO)
        handler.setFormatter(ColoredFormatter())
        
        root_logger = logging.getLogger()
        root_logger.addHandler(handler)
        self._ui_handlers.append(handler)
    
    def remove_ui_handlers(self):
        """Remove todos os handlers de UI"""
        root_logger = logging.getLogger()
        for handler in self._ui_handlers:
            root_logger.removeHandler(handler)
        self._ui_handlers.clear()
    
    def set_level(self, level: Union[LogLevel, str], logger_name: Optional[str] = None):
        """
        Define o nível de logging
        
        Args:
            level: Nível de log (LogLevel ou string)
            logger_name: Nome do logger específico (None para root)
        """
        if isinstance(level, str):
            level = LogLevel[level.upper()]
        
        if logger_name:
            logger = logging.getLogger(logger_name)
        else:
            logger = logging.getLogger()
        
        logger.setLevel(level.value)
    
    def log(self, level: LogLevel, message: str, logger_name: str = 'root',
            exc_info: bool = False, extra: Dict[str, Any] = None,
            duration_ms: float = None):
        """
        Registra uma mensagem de log
        
        Args:
            level: Nível do log
            message: Mensagem
            logger_name: Nome do logger
            exc_info: Incluir informação de exceção
            extra: Dados extras
            duration_ms: Duração da operação em ms
        """
        logger = self.get_logger(logger_name)
        
        # Preparar record extras
        record_extra = {}
        
        # Adicionar contexto
        context = self.get_context()
        if context:
            record_extra['context'] = context.to_dict()
        
        # Adicionar extras
        if extra:
            record_extra['extra_data'] = extra
        
        # Adicionar duração
        if duration_ms is not None:
            record_extra['duration_ms'] = duration_ms
        
        # Atualizar métricas
        self._update_metrics(level)
        
        # Registrar log
        logger.log(level.value, message, exc_info=exc_info, extra=record_extra)
    
    def _update_metrics(self, level: LogLevel):
        """Atualiza métricas de logging"""
        self._metrics['total_logs'] += 1
        level_name = level.name
        self._metrics['logs_by_level'][level_name] = \
            self._metrics['logs_by_level'].get(level_name, 0) + 1
        
        if level in (LogLevel.ERROR, LogLevel.CRITICAL):
            self._metrics['errors_count'] += 1
    
    def get_metrics(self) -> Dict[str, Any]:
        """Retorna métricas de logging"""
        return self._metrics.copy()
    
    def trace(self, message: str, **kwargs):
        """Log nível TRACE"""
        self.log(LogLevel.TRACE, message, **kwargs)
    
    def debug(self, message: str, **kwargs):
        """Log nível DEBUG"""
        self.log(LogLevel.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log nível INFO"""
        self.log(LogLevel.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log nível WARNING"""
        self.log(LogLevel.WARNING, message, **kwargs)
    
    def error(self, message: str, exc_info: bool = True, **kwargs):
        """Log nível ERROR"""
        self.log(LogLevel.ERROR, message, exc_info=exc_info, **kwargs)
    
    def critical(self, message: str, exc_info: bool = True, **kwargs):
        """Log nível CRITICAL"""
        self.log(LogLevel.CRITICAL, message, exc_info=exc_info, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log de exceção com traceback"""
        self.error(message, exc_info=True, **kwargs)
    
    def get_log_files(self) -> List[Path]:
        """Retorna lista de arquivos de log"""
        return sorted(self.log_dir.glob("*.log")) + sorted(self.log_dir.glob("*.json"))
    
    def export_logs(self, output_path: Path, format: str = 'json',
                    start_date: datetime = None, end_date: datetime = None,
                    levels: List[LogLevel] = None) -> bool:
        """
        Exporta logs para arquivo
        
        Args:
            output_path: Caminho do arquivo de saída
            format: Formato de saída ('json', 'csv', 'txt')
            start_date: Data inicial para filtro
            end_date: Data final para filtro
            levels: Lista de níveis para filtrar
        
        Returns:
            True se exportação foi bem sucedida
        """
        try:
            logs = self._read_logs(start_date, end_date, levels)
            
            if format == 'json':
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(logs, f, indent=2, ensure_ascii=False)
            
            elif format == 'csv':
                import csv
                with open(output_path, 'w', encoding='utf-8', newline='') as f:
                    if logs:
                        writer = csv.DictWriter(f, fieldnames=logs[0].keys())
                        writer.writeheader()
                        writer.writerows(logs)
            
            elif format == 'txt':
                with open(output_path, 'w', encoding='utf-8') as f:
                    for log in logs:
                        f.write(f"{log.get('timestamp', '')} | {log.get('level', '')} | {log.get('message', '')}\n")
            
            return True
        
        except Exception as e:
            self.error(f"Erro ao exportar logs: {e}")
            return False
    
    def _read_logs(self, start_date: datetime = None, end_date: datetime = None,
                   levels: List[LogLevel] = None) -> List[Dict]:
        """Lê logs dos arquivos JSON"""
        logs = []
        
        for log_file in self.log_dir.glob("*.json"):
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                            
                            # Filtrar por data
                            if start_date or end_date:
                                entry_date = datetime.fromisoformat(entry.get('timestamp', ''))
                                if start_date and entry_date < start_date:
                                    continue
                                if end_date and entry_date > end_date:
                                    continue
                            
                            # Filtrar por nível
                            if levels:
                                level_names = [l.name for l in levels]
                                if entry.get('level') not in level_names:
                                    continue
                            
                            logs.append(entry)
                        
                        except json.JSONDecodeError:
                            continue
            
            except Exception:
                continue
        
        return logs
    
    def cleanup_old_logs(self, days: int = 30):
        """
        Remove logs mais antigos que o número de dias especificado
        
        Args:
            days: Número de dias para manter logs
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        for log_file in self.log_dir.glob("*"):
            try:
                file_date = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_date < cutoff_date:
                    log_file.unlink()
                    self.info(f"Arquivo de log removido: {log_file.name}")
            except Exception as e:
                self.error(f"Erro ao remover arquivo de log {log_file}: {e}")


# Decorador para logging automático de funções
def log_execution(logger_name: str = None, level: LogLevel = LogLevel.DEBUG,
                  include_args: bool = True, include_result: bool = False):
    """
    Decorador que registra execução de funções com timing
    
    Args:
        logger_name: Nome do logger (None usa nome do módulo)
        level: Nível de log
        include_args: Incluir argumentos no log
        include_result: Incluir resultado no log
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            service = LoggerService()
            name = logger_name or func.__module__
            
            # Log de início
            args_str = ""
            if include_args:
                args_str = f" args={args}, kwargs={kwargs}"
            
            service.log(level, f"Iniciando {func.__name__}{args_str}", logger_name=name)
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                result_str = ""
                if include_result:
                    result_str = f" -> {result}"
                
                service.log(level, f"Concluído {func.__name__}{result_str}",
                           logger_name=name, duration_ms=duration_ms)
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                service.log(LogLevel.ERROR, f"Erro em {func.__name__}: {e}",
                           logger_name=name, exc_info=True, duration_ms=duration_ms)
                raise
        
        return wrapper
    return decorator


# Decorador para timing de operações
def timed_operation(operation_name: str = None):
    """
    Decorador para medir tempo de operações
    
    Args:
        operation_name: Nome da operação (None usa nome da função)
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            service = LoggerService()
            name = operation_name or func.__name__
            
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration_ms = (time.time() - start_time) * 1000
                
                service.info(f"Operação '{name}' concluída",
                            duration_ms=duration_ms,
                            extra={'operation': name, 'status': 'success'})
                
                return result
            
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                service.error(f"Operação '{name}' falhou: {e}",
                             duration_ms=duration_ms,
                             extra={'operation': name, 'status': 'error'})
                raise
        
        return wrapper
    return decorator


# Instância global para uso simplificado
_logger_service = None


def get_logger_service() -> LoggerService:
    """Obtém instância do serviço de logging"""
    global _logger_service
    if _logger_service is None:
        _logger_service = LoggerService()
    return _logger_service


def get_logger(name: str) -> logging.Logger:
    """Atalho para obter logger"""
    return get_logger_service().get_logger(name)
