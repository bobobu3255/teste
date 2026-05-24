#!/usr/bin/env python3
"""
Gerenciador de Logging Centralizado
Versão 1.0 - Sistema profissional de logging com suporte a múltiplos handlers
"""
import logging
import logging.handlers
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, Callable
from enum import Enum


class LogLevel(Enum):
    """Níveis de log disponíveis"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


class LoggerManager:
    """Gerenciador centralizado de logging para toda a aplicação"""
    
    _instance = None
    _loggers = {}
    _ui_callback = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LoggerManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Inicializa o gerenciador de logging"""
        if self._initialized:
            return
        
        self._initialized = True
        self.log_dir = Path(os.path.expanduser("~/.telegram_collector/logs"))
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Configurar logger raiz
        self._setup_root_logger()
    
    def _setup_root_logger(self):
        """Configura o logger raiz com handlers"""
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)
        
        # Remover handlers existentes
        for handler in root_logger.handlers[:]:
            root_logger.removeHandler(handler)
        
        # Handler para arquivo com rotação
        log_file = self.log_dir / f"telegram_collector_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Handler para console
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        # Formato detalhado para arquivo, simples para console
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(file_formatter)
        console_handler.setFormatter(console_formatter)
        
        root_logger.addHandler(file_handler)
        root_logger.addHandler(console_handler)
    
    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Obtém ou cria um logger com o nome especificado
        
        Args:
            name: Nome do logger (geralmente __name__)
        
        Returns:
            Logger configurado
        """
        if name not in cls._loggers:
            logger = logging.getLogger(name)
            cls._loggers[name] = logger
        
        return cls._loggers[name]
    
    @classmethod
    def set_ui_callback(cls, callback: Callable[[str, str], None]):
        """
        Define callback para enviar logs para UI
        
        Args:
            callback: Função que recebe (mensagem, nível) para exibir na UI
        """
        cls._ui_callback = callback
    
    @classmethod
    def log_to_ui(cls, message: str, level: str = "INFO"):
        """
        Envia mensagem de log para UI se callback foi definido
        
        Args:
            message: Mensagem a exibir
            level: Nível do log (INFO, WARNING, ERROR, etc)
        """
        if cls._ui_callback:
            try:
                cls._ui_callback(message, level)
            except Exception as e:
                logging.error(f"Erro ao enviar log para UI: {e}")
    
    @classmethod
    def set_level(cls, level: LogLevel):
        """Define o nível de logging global"""
        logging.getLogger().setLevel(level.value)
    
    @classmethod
    def get_log_file_path(cls) -> Path:
        """Retorna o caminho do arquivo de log atual"""
        log_file = cls().log_dir / f"telegram_collector_{datetime.now().strftime('%Y%m%d')}.log"
        return log_file


# Função auxiliar para uso simplificado
def get_logger(name: str) -> logging.Logger:
    """Atalho para obter logger"""
    return LoggerManager.get_logger(name)


# Decorador para logging automático de funções
def log_function_call(logger: Optional[logging.Logger] = None):
    """
    Decorador que registra chamadas e retorno de funções
    
    Args:
        logger: Logger a usar (se None, usa logger padrão)
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            func_logger = logger or LoggerManager.get_logger(func.__module__)
            
            try:
                func_logger.debug(f"Chamando {func.__name__} com args={args}, kwargs={kwargs}")
                result = func(*args, **kwargs)
                func_logger.debug(f"{func.__name__} retornou: {result}")
                return result
            except Exception as e:
                func_logger.error(f"Erro em {func.__name__}: {e}", exc_info=True)
                raise
        
        return wrapper
    return decorator


# Contexto para logging de blocos de código
class LogContext:
    """Context manager para logging de blocos de código"""
    
    def __init__(self, logger: logging.Logger, message: str, level: LogLevel = LogLevel.INFO):
        self.logger = logger
        self.message = message
        self.level = level
    
    def __enter__(self):
        self.logger.log(self.level.value, f"Iniciando: {self.message}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.logger.log(self.level.value, f"Concluído: {self.message}")
        else:
            self.logger.error(f"Erro em '{self.message}': {exc_val}", exc_info=True)
        return False
