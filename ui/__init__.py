#!/usr/bin/env python3
"""
UI Package - Componentes de interface do usuário

Este pacote contém componentes de UI:
- ui_components: Componentes reutilizáveis de interface
- theme: Temas e estilos da aplicação
"""

from .theme import DARK_STYLE, get_theme
from .ui_components import *

__all__ = [
    'DARK_STYLE',
    'get_theme'
]
