#!/usr/bin/env python3
"""Tratamento central de erros e logs fatais."""

from __future__ import annotations

import faulthandler
import sys
import traceback
from datetime import datetime
from pathlib import Path


_CRASH_LOG_HANDLE = None


def log_exception(base_dir: Path, filename: str, context: str, exc: BaseException) -> None:
    """Registra excecao em arquivo sem interromper a interface."""
    try:
        log_dir = Path(base_dir) / "_temp"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / filename
        with open(log_file, "a", encoding="utf-8") as fh:
            fh.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {context}\n")
            fh.write("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)))
    except Exception:
        pass


def install_crash_logger(base_dir: Path) -> None:
    """Guarda excecoes e falhas fatais em `_temp/app_crash.log`."""
    global _CRASH_LOG_HANDLE
    try:
        log_dir = Path(base_dir) / "_temp"
        log_dir.mkdir(parents=True, exist_ok=True)
        if _CRASH_LOG_HANDLE is None or _CRASH_LOG_HANDLE.closed:
            _CRASH_LOG_HANDLE = open(log_dir / "app_crash.log", "a", encoding="utf-8")
        _CRASH_LOG_HANDLE.write(f"\n\n=== App iniciado {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
        _CRASH_LOG_HANDLE.flush()
        faulthandler.enable(file=_CRASH_LOG_HANDLE, all_threads=True)

        def _hook(exc_type, exc, tb):
            try:
                _CRASH_LOG_HANDLE.write(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Excecao nao tratada\n")
                _CRASH_LOG_HANDLE.write("".join(traceback.format_exception(exc_type, exc, tb)))
                _CRASH_LOG_HANDLE.flush()
            except Exception:
                pass
            sys.__excepthook__(exc_type, exc, tb)

        sys.excepthook = _hook
    except Exception:
        pass
