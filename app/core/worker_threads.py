#!/usr/bin/env python3
"""Threads de trabalho usadas pela interface principal."""

import asyncio

from PyQt5.QtCore import QThread, pyqtSignal

from settings import settings

class CollectorThread(QThread):
    """Thread para executar a coleta de dados do Telegram"""
    finished = pyqtSignal(int)
    error = pyqtSignal(str)
    progress = pyqtSignal(str)
    code_requested = pyqtSignal(str)
    password_requested = pyqtSignal()
    
    def __init__(self, groups: list = None, limit: int = 2000, 
                 filtrar_idosos: bool = False, idade_maxima: int = None,
                 exigir_data_nascimento: bool = False, conta_id: int = None):
        super().__init__()
        self.groups = groups or [settings.default_group]
        self.limit = limit
        self.filtrar_idosos = filtrar_idosos
        self.idade_maxima = idade_maxima
        self.exigir_data_nascimento = exigir_data_nascimento
        self.conta_id = conta_id
        self.verification_code = None
        self.password_2fa = None
        self._code_event = asyncio.Event()
        self._password_event = asyncio.Event()
    
    def set_verification_code(self, code: str):
        self.verification_code = code
        if hasattr(self, '_loop') and self._loop:
            self._loop.call_soon_threadsafe(self._code_event.set)
    
    def set_password(self, password: str):
        self.password_2fa = password
        if hasattr(self, '_loop') and self._loop:
            self._loop.call_soon_threadsafe(self._password_event.set)
    
    def run(self):
        try:
            self.progress.emit("Iniciando coletor...")
            
            def progress_callback(msg):
                self.progress.emit(msg)
            
            self._loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._loop)
            
            self._code_event = asyncio.Event()
            self._password_event = asyncio.Event()
            
            async def code_callback():
                self.progress.emit("📱 Aguardando código de verificação...")
                self.code_requested.emit(settings.telegram_phone)
                await self._code_event.wait()
                return self.verification_code
            
            async def password_callback():
                self.progress.emit("🔐 Aguardando senha 2FA...")
                self.password_requested.emit()
                await self._password_event.wait()
                return self.password_2fa
            
            from collector import TelegramCollector

            collector = TelegramCollector(
                progress_callback=progress_callback,
                code_callback=code_callback,
                password_callback=password_callback,
                filtrar_idosos=self.filtrar_idosos,
                idade_maxima=self.idade_maxima,
                exigir_data_nascimento=self.exigir_data_nascimento,
                conta_id=self.conta_id
            )
            
            if len(self.groups) == 1:
                collected = self._loop.run_until_complete(
                    collector.run(self.groups[0], self.limit)
                )
            else:
                collected = self._loop.run_until_complete(
                    collector.run_multiple_groups(self.groups, self.limit)
                )
            
            self.finished.emit(collected)
            
        except Exception as e:
            self.error.emit(str(e))
        finally:
            if hasattr(self, '_loop') and self._loop:
                self._loop.close()


class CardGeneratorThread(QThread):
    """Thread para geração de cartões sem travar a interface"""
    
    # Sinais para comunicação com a interface
    progress = pyqtSignal(int, int)  # (atual, total)
    finished_cards = pyqtSignal(list)  # lista de cartões gerados
    error = pyqtSignal(str)  # mensagem de erro
    
    def __init__(self, generator, pattern, quantity, month, year, cvv):
        super().__init__()
        self.generator = generator
        self.pattern = pattern
        self.quantity = quantity
        self.month = month
        self.year = year
        self.cvv = cvv
    
    def run(self):
        """Executa a geração em thread separada"""
        try:
            # Callback para reportar progresso
            def progress_callback(current, total):
                self.progress.emit(current, total)
            
            # Gerar cartões
            cards = self.generator.generate_cards(
                self.pattern, 
                self.quantity, 
                self.month, 
                self.year, 
                self.cvv,
                progress_callback
            )
            
            self.finished_cards.emit(cards)
            
        except Exception as e:
            self.error.emit(str(e))
    
    def stop(self):
        """Para a geração"""
        self.generator.cancel()


class AddressGeneratorThread(QThread):
    """Thread para geração de endereços sem travar a interface"""
    progress = pyqtSignal(int, int)  # (atual, total)
    finished_addresses = pyqtSignal(list)  # lista de endereços formatados
    error = pyqtSignal(str)  # mensagem de erro
    
    def __init__(self, generator, quantidade, uf=None, cidade=None, com_pontuacao=True):
        super().__init__()
        self.generator = generator
        self.quantidade = quantidade
        self.uf = uf
        self.cidade = cidade
        self.com_pontuacao = com_pontuacao
        self._stop_flag = False
    
    def stop(self):
        """Sinaliza para parar a geração"""
        self._stop_flag = True
        self.generator.cancel()
    
    def run(self):
        try:
            def progress_callback(current, total):
                if not self._stop_flag:
                    self.progress.emit(current, total)
            
            enderecos = self.generator.gerar_enderecos(
                quantidade=self.quantidade,
                uf=self.uf,
                cidade=self.cidade,
                com_pontuacao=self.com_pontuacao,
                progress_callback=progress_callback
            )
            
            # Formatar endereços para exibição
            formatted = []
            for end in enderecos:
                formatted.append(end.format_linha(self.com_pontuacao))
            
            self.finished_addresses.emit(formatted)
            
        except Exception as e:
            self.error.emit(str(e))
