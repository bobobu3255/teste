#!/usr/bin/env python3
"""
Workers Assíncronos — v2.0

QThread workers especializados para coleta, processamento, banco de dados
e operações assíncronas em geral.

Mudanças desta versão
─────────────────────
🐛 BUG CRÍTICO CORRIGIDO
   `signals = WorkerSignals()` era atributo de CLASSE em `BaseWorker`
   — ou seja, TODOS os workers compartilhavam o MESMO objeto de sinais.
   Agora `self.signals` é instanciado por worker, no `__init__`.

✨ Cancelamento cooperativo via `threading.Event` (mais seguro que flag bool).
✨ `sleep_interruptible()` para esperas que respeitam cancelamento.
✨ Tratamento centralizado de exceções (`_emit_error`).
✨ `AsyncWorker` com cleanup correto do event loop mesmo em erro.
✨ Type hints modernos (PEP 604, PEP 585).
✨ Fallbacks para `logger_manager`/`exceptions` ausentes em dev.
"""
from __future__ import annotations

import asyncio
import logging
import threading
from typing import Any, Callable, Sequence

from PyQt5.QtCore import QObject, QThread, pyqtSignal

# ────────────────────────────────────────────────────────────────
#  Imports opcionais com fallback
# ────────────────────────────────────────────────────────────────
try:
    from logger_manager import LogContext, get_logger  # type: ignore[import-not-found]
except ImportError:
    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

    class LogContext:
        """Fallback no-op para LogContext."""

        def __init__(self, _logger: Any, _msg: str) -> None: ...
        def __enter__(self) -> "LogContext": return self
        def __exit__(self, *_exc: Any) -> bool: return False

try:
    from exceptions import (  # type: ignore[import-not-found]
        CollectionException,
        DatabaseException,
        FloodWaitException,
        ProcessingException,
    )
except ImportError:
    class FloodWaitException(Exception):  # type: ignore[no-redef]
        """Limite de requisições do Telegram."""

    class CollectionException(Exception):  # type: ignore[no-redef]
        """Erro na coleta de dados."""

    class DatabaseException(Exception):  # type: ignore[no-redef]
        """Erro no banco de dados."""

    class ProcessingException(Exception):  # type: ignore[no-redef]
        """Erro no processamento de dados."""


log = get_logger(__name__)


# ════════════════════════════════════════════════════════════════
#  Sinais
# ════════════════════════════════════════════════════════════════
class WorkerSignals(QObject):
    """Sinais emitidos por workers.

    ⚠️  Cada worker DEVE ter sua própria instância — não usar como atributo
       de classe (todos compartilhariam o mesmo objeto Qt).
    """

    progress = pyqtSignal(int)              # 0..100
    status = pyqtSignal(str)                # mensagem de status
    finished = pyqtSignal()                 # concluído (sucesso ou cancelado)
    result = pyqtSignal(object)             # resultado final
    error = pyqtSignal(str)                 # mensagem de erro
    error_detailed = pyqtSignal(str, str)   # (tipo_erro, mensagem)
    log = pyqtSignal(str, str)              # (mensagem, nível)


# ════════════════════════════════════════════════════════════════
#  Base Worker
# ════════════════════════════════════════════════════════════════
class BaseWorker(QThread):
    """Worker base com cancelamento cooperativo e tratamento de erros."""

    DEFAULT_STOP_TIMEOUT_MS: int = 5_000

    _LOG_LEVELS: dict[str, int] = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    def __init__(self, name: str = "Worker", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self.name = name
        # CRÍTICO: instância própria de sinais por worker
        self.signals = WorkerSignals()
        self._cancel = threading.Event()

    # ── Estado ──────────────────────────────────────────────────
    @property
    def is_running(self) -> bool:
        """True enquanto o cancelamento não foi requisitado."""
        return not self._cancel.is_set()

    @property
    def was_cancelled(self) -> bool:
        return self._cancel.is_set()

    # ── Ciclo de vida ───────────────────────────────────────────
    def stop(self, timeout_ms: int | None = None) -> bool:
        """Sinaliza cancelamento e aguarda o término. Retorna True se parou."""
        self._cancel.set()
        timeout = timeout_ms if timeout_ms is not None else self.DEFAULT_STOP_TIMEOUT_MS
        return self.wait(timeout)

    def run(self) -> None:
        """Loop principal — não chame diretamente; use `start()`."""
        try:
            with LogContext(log, f"Worker '{self.name}' iniciado"):
                self._execute()
                self.signals.finished.emit()

        except FloodWaitException as exc:
            self._emit_error(exc, "FloodWait", level="warning")

        except (CollectionException, DatabaseException, ProcessingException) as exc:
            self._emit_error(exc, type(exc).__name__, level="error")

        except Exception as exc:  # noqa: BLE001
            log.exception("Erro inesperado em %s", self.name)
            self._emit_error(exc, "UnexpectedError", level="error")

    def _execute(self) -> None:
        """Sobrescreva nas subclasses."""
        raise NotImplementedError("Subclasses devem implementar _execute()")

    # ── Helpers de emissão ──────────────────────────────────────
    def emit_progress(self, progress: int, status: str = "") -> None:
        """Emite progresso (clamped em 0..100) e opcionalmente um status."""
        clamped = max(0, min(100, int(progress)))
        self.signals.progress.emit(clamped)
        if status:
            self.signals.status.emit(status)
            log.debug("%s: %s (%d%%)", self.name, status, clamped)

    def emit_log(self, message: str, level: str = "INFO") -> None:
        """Emite log com nível textual."""
        self.signals.log.emit(message, level)
        log.log(self._LOG_LEVELS.get(level.upper(), logging.INFO), message)

    def _emit_error(self, exc: BaseException, kind: str, *, level: str) -> None:
        msg = f"{kind}: {exc}"
        getattr(log, level, log.error)(msg)
        self.signals.error.emit(msg)
        self.signals.error_detailed.emit(kind, str(exc))

    # ── Utilidades ──────────────────────────────────────────────
    def sleep_interruptible(self, seconds: float, step_ms: int = 100) -> bool:
        """Sleep que respeita o cancelamento.

        Retorna True se completou, False se foi cancelado.
        """
        total_ms = int(seconds * 1000)
        elapsed = 0
        while elapsed < total_ms:
            if not self.is_running:
                return False
            chunk = min(step_ms, total_ms - elapsed)
            self.msleep(chunk)
            elapsed += chunk
        return True


# ════════════════════════════════════════════════════════════════
#  Worker: Coleta de dados do Telegram
# ════════════════════════════════════════════════════════════════
class CollectorWorker(BaseWorker):
    """Worker para coleta de dados do Telegram a partir de uma lista de grupos."""

    def __init__(
        self,
        collector: Any,
        grupos: Sequence[str],
        callback_progress: Callable[[int], None] | None = None,
    ) -> None:
        super().__init__("CollectorWorker")
        self.collector = collector
        self.grupos: list[str] = list(grupos)
        self.callback_progress = callback_progress
        self.dados_coletados: list[Any] = []

    def _execute(self) -> None:
        total = len(self.grupos)
        if total == 0:
            self.emit_log("Nenhum grupo para coletar", "WARNING")
            self.signals.result.emit(self.dados_coletados)
            return

        self.emit_log(f"Iniciando coleta de {total} grupo(s)", "INFO")

        for idx, grupo in enumerate(self.grupos):
            if not self.is_running:
                self.emit_log("Coleta cancelada pelo usuário", "WARNING")
                break

            self.emit_progress(int(idx * 100 / total), f"Coletando de {grupo}")
            self._coletar_grupo(grupo)

        self.emit_progress(100, "Coleta concluída")
        self.signals.result.emit(self.dados_coletados)

    def _coletar_grupo(self, grupo: str) -> None:
        """Coleta um grupo isoladamente, tratando erros não-fatais."""
        try:
            self.emit_log(f"Processando grupo: {grupo}", "INFO")
            # ─── lógica real de coleta entra aqui ───
            # dados = self.collector.coletar_grupo(grupo)
            # self.dados_coletados.extend(dados)
            self.sleep_interruptible(0.5)

        except FloodWaitException as exc:
            self.emit_log(f"Flood wait em {grupo}: {exc}", "WARNING")
            self.sleep_interruptible(5.0)

        except CollectionException as exc:
            self.emit_log(f"Erro ao coletar {grupo}: {exc}", "ERROR")


# ════════════════════════════════════════════════════════════════
#  Worker: Processamento item-a-item
# ════════════════════════════════════════════════════════════════
class ProcessingWorker(BaseWorker):
    """Aplica `processor_func` a cada item de `data`."""

    def __init__(
        self,
        data: Sequence[Any],
        processor_func: Callable[[Any], Any],
    ) -> None:
        super().__init__("ProcessingWorker")
        self.data = list(data)
        self.processor_func = processor_func
        self.processed_data: list[Any] = []

    def _execute(self) -> None:
        total = len(self.data)
        if total == 0:
            self.emit_log("Nenhum item para processar", "WARNING")
            self.signals.result.emit(self.processed_data)
            return

        self.emit_log(f"Iniciando processamento de {total} registro(s)", "INFO")

        for idx, item in enumerate(self.data):
            if not self.is_running:
                self.emit_log("Processamento cancelado", "WARNING")
                break

            try:
                self.processed_data.append(self.processor_func(item))
                self.emit_progress(
                    int((idx + 1) * 100 / total),
                    f"Processado {idx + 1}/{total}",
                )
            except ProcessingException as exc:
                self.emit_log(f"Erro ao processar item {idx}: {exc}", "ERROR")

        self.emit_progress(100, "Processamento concluído")
        self.signals.result.emit(self.processed_data)


# ════════════════════════════════════════════════════════════════
#  Worker: Operações de banco de dados
# ════════════════════════════════════════════════════════════════
class DatabaseWorker(BaseWorker):
    """Executa operações nomeadas (`insert`/`update`/`delete`/`export`)."""

    OPERATIONS = ("insert", "update", "delete", "export")

    def __init__(self, db_manager: Any, operation: str, data: Any) -> None:
        super().__init__("DatabaseWorker")
        if operation not in self.OPERATIONS:
            raise ValueError(
                f"Operação desconhecida: {operation!r}. "
                f"Use uma de: {', '.join(self.OPERATIONS)}"
            )
        self.db_manager = db_manager
        self.operation = operation
        self.data = data

    def _execute(self) -> None:
        self.emit_log(f"Executando operação: {self.operation}", "INFO")

        handler = getattr(self, f"_{self.operation}_data")
        result = handler()

        self.emit_log(f"Operação '{self.operation}' concluída", "INFO")
        self.signals.result.emit(result)

    # ── Implementações ──────────────────────────────────────────
    def _insert_data(self) -> int:
        self.emit_progress(50, "Inserindo dados...")
        # implementar inserção
        self.emit_progress(100, "Dados inseridos")
        return len(self.data) if isinstance(self.data, (list, tuple)) else 1

    def _update_data(self) -> bool:
        self.emit_progress(50, "Atualizando dados...")
        # implementar atualização
        self.emit_progress(100, "Dados atualizados")
        return True

    def _delete_data(self) -> bool:
        self.emit_progress(50, "Deletando dados...")
        # implementar deleção
        self.emit_progress(100, "Dados deletados")
        return True

    def _export_data(self) -> Any:
        self.emit_progress(50, "Exportando dados...")
        # implementar exportação
        self.emit_progress(100, "Dados exportados")
        return self.data


# ════════════════════════════════════════════════════════════════
#  Worker: Operação assíncrona genérica
# ════════════════════════════════════════════════════════════════
class AsyncWorker(BaseWorker):
    """Executa uma corotina (`async def`) em um event loop dedicado."""

    def __init__(
        self,
        async_func: Callable[..., Any],
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().__init__("AsyncWorker")
        self.async_func = async_func
        self.args = args
        self.kwargs = kwargs

    def _execute(self) -> None:
        loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(loop)
            self.emit_log("Executando operação assíncrona", "INFO")
            result = loop.run_until_complete(
                self.async_func(*self.args, **self.kwargs)
            )
            self.signals.result.emit(result)
        finally:
            try:
                # cancela tasks pendentes antes de fechar
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                if pending:
                    loop.run_until_complete(
                        asyncio.gather(*pending, return_exceptions=True)
                    )
            except Exception:  # noqa: BLE001
                pass
            finally:
                loop.close()
                asyncio.set_event_loop(None)


# ════════════════════════════════════════════════════════════════
#  Worker: Processamento em lotes
# ════════════════════════════════════════════════════════════════
class BatchWorker(BaseWorker):
    """Processa `items` em lotes de tamanho `batch_size`."""

    def __init__(
        self,
        items: Sequence[Any],
        batch_size: int,
        process_func: Callable[[list[Any]], Any],
    ) -> None:
        super().__init__("BatchWorker")
        if batch_size <= 0:
            raise ValueError(f"batch_size deve ser > 0 (recebido: {batch_size})")
        self.items = list(items)
        self.batch_size = batch_size
        self.process_func = process_func
        self.results: list[Any] = []

    def _execute(self) -> None:
        total_items = len(self.items)
        if total_items == 0:
            self.emit_log("Nenhum item para processar em lote", "WARNING")
            self.signals.result.emit(self.results)
            return

        total_batches = (total_items + self.batch_size - 1) // self.batch_size
        self.emit_log(
            f"Processando {total_items} itens em {total_batches} lote(s)",
            "INFO",
        )

        for batch_idx in range(total_batches):
            if not self.is_running:
                self.emit_log("Processamento em lotes cancelado", "WARNING")
                break

            start = batch_idx * self.batch_size
            batch = self.items[start : start + self.batch_size]

            try:
                batch_result = self.process_func(batch)
                if isinstance(batch_result, list):
                    self.results.extend(batch_result)
                else:
                    self.results.append(batch_result)

                self.emit_progress(
                    int((batch_idx + 1) * 100 / total_batches),
                    f"Lote {batch_idx + 1}/{total_batches}",
                )
            except Exception as exc:  # noqa: BLE001
                self.emit_log(f"Erro no lote {batch_idx}: {exc}", "ERROR")

        self.emit_progress(100, "Processamento em lotes concluído")
        self.signals.result.emit(self.results)


# ════════════════════════════════════════════════════════════════
#  Exports
# ════════════════════════════════════════════════════════════════
__all__ = [
    "WorkerSignals",
    "BaseWorker",
    "CollectorWorker",
    "ProcessingWorker",
    "DatabaseWorker",
    "AsyncWorker",
    "BatchWorker",
]
