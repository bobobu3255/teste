#!/usr/bin/env python3
"""
Exceções Customizadas
Versão 1.0 - Hierarquia de exceções específicas para melhor tratamento de erros
"""


class TelegramCollectorException(Exception):
    """Exceção base para toda a aplicação"""
    pass


# ===== EXCEÇÕES DE CONFIGURAÇÃO =====

class ConfigurationException(TelegramCollectorException):
    """Erro em configuração da aplicação"""
    pass


class MissingConfigurationError(ConfigurationException):
    """Configuração obrigatória não encontrada"""
    pass


class InvalidConfigurationError(ConfigurationException):
    """Configuração inválida ou malformada"""
    pass


# ===== EXCEÇÕES DE AUTENTICAÇÃO =====

class AuthenticationException(TelegramCollectorException):
    """Erro de autenticação no Telegram"""
    pass


class InvalidCredentialsError(AuthenticationException):
    """Credenciais inválidas"""
    pass


class SessionExpiredError(AuthenticationException):
    """Sessão expirou"""
    pass


class TwoFactorAuthenticationError(AuthenticationException):
    """Erro na autenticação de dois fatores"""
    pass


# ===== EXCEÇÕES DE BANCO DE DADOS =====

class DatabaseException(TelegramCollectorException):
    """Erro de banco de dados"""
    pass


class DatabaseConnectionError(DatabaseException):
    """Erro ao conectar ao banco de dados"""
    pass


class DatabaseQueryError(DatabaseException):
    """Erro ao executar query"""
    pass


class DatabaseIntegrityError(DatabaseException):
    """Violação de integridade de dados"""
    pass


# ===== EXCEÇÕES DE COLETA =====

class CollectionException(TelegramCollectorException):
    """Erro durante coleta de dados"""
    pass


class FloodWaitException(CollectionException):
    """Telegram está limitando requisições (flood wait)"""
    pass


class InvalidGroupException(CollectionException):
    """Grupo inválido ou inacessível"""
    pass


class MessageFetchException(CollectionException):
    """Erro ao buscar mensagens"""
    pass


class DataExtractionException(CollectionException):
    """Erro ao extrair dados de mensagem"""
    pass


# ===== EXCEÇÕES DE PROCESSAMENTO =====

class ProcessingException(TelegramCollectorException):
    """Erro durante processamento de dados"""
    pass


class ValidationException(ProcessingException):
    """Erro na validação de dados"""
    pass


class FormatException(ProcessingException):
    """Erro ao formatar dados"""
    pass


class AIValidationException(ProcessingException):
    """Erro na validação com IA"""
    pass


# ===== EXCEÇÕES DE ARQUIVO =====

class FileException(TelegramCollectorException):
    """Erro ao manipular arquivo"""
    pass


class FileNotFoundError(FileException):
    """Arquivo não encontrado"""
    pass


class FileWriteError(FileException):
    """Erro ao escrever arquivo"""
    pass


class FileReadError(FileException):
    """Erro ao ler arquivo"""
    pass


# ===== EXCEÇÕES DE REDE =====

class NetworkException(TelegramCollectorException):
    """Erro de rede"""
    pass


class ConnectionTimeoutError(NetworkException):
    """Timeout na conexão"""
    pass


class ConnectionRefusedError(NetworkException):
    """Conexão recusada"""
    pass


# ===== EXCEÇÕES DE UI =====

class UIException(TelegramCollectorException):
    """Erro na interface do usuário"""
    pass


class ThreadException(UIException):
    """Erro em thread de UI"""
    pass


class ProgressException(UIException):
    """Erro ao atualizar progresso"""
    pass


# Mapeamento de exceções do Telethon para nossas exceções
TELETHON_ERROR_MAP = {
    'SessionPasswordNeededError': TwoFactorAuthenticationError,
    'AuthKeyError': InvalidCredentialsError,
    'FloodWaitError': FloodWaitException,
    'ChannelPrivateError': InvalidGroupException,
    'ChatNotModifiedError': InvalidGroupException,
    'ConnectionError': ConnectionRefusedError,
}


def map_telethon_error(error: Exception) -> TelegramCollectorException:
    """
    Mapeia exceção do Telethon para nossa hierarquia
    
    Args:
        error: Exceção do Telethon
    
    Returns:
        Exceção mapeada ou CollectionException genérica
    """
    error_class_name = error.__class__.__name__
    
    if error_class_name in TELETHON_ERROR_MAP:
        mapped_exception = TELETHON_ERROR_MAP[error_class_name]
        return mapped_exception(str(error))
    
    return CollectionException(f"Erro do Telegram: {error_class_name} - {str(error)}")
