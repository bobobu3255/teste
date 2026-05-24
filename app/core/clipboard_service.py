#!/usr/bin/env python3
"""Servico unico de clipboard para evitar copias espalhadas pelo app."""

from PyQt5.QtCore import QMimeData
from PyQt5.QtWidgets import QApplication


def set_clipboard_text(text: str) -> bool:
    """Copia texto usando Qt puro, com verificacao curta para botoes pequenos."""
    text = text or ""
    clipboard = QApplication.clipboard()
    mime = QMimeData()
    mime.setText(text)
    clipboard.setMimeData(mime)
    if clipboard.text() != text:
        clipboard.setText(text)
    return clipboard.text() == text

