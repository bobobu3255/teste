#!/usr/bin/env python3
"""Compatibilidade para ferramentas antigas.

As classes reais foram movidas para `app.features.extra_tools.widget`.
Manter este arquivo evita quebrar imports antigos como:
`from extra_tools import ValidadorWidget`.
"""
from app.features.extra_tools.widget import *  # noqa: F401,F403
