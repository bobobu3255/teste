#!/usr/bin/env python3
"""
Services Package - Serviços centralizados da aplicação

Este pacote contém serviços profissionais e reutilizáveis:
- LoggerService: Sistema de logging estruturado
"""

from .logger_service import (
    LoggerService,
    LogLevel,
    LogContext,
    LogEntry,
    get_logger_service,
    get_logger,
    log_execution,
    timed_operation
)

__all__ = [
    'LoggerService',
    'LogLevel',
    'LogContext',
    'LogEntry',
    'get_logger_service',
    'get_logger',
    'log_execution',
    'timed_operation'
]
