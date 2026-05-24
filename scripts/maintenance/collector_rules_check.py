#!/usr/bin/env python3
"""Confere regras centrais da coleta automatica."""
from __future__ import annotations

import os
import sys
from types import SimpleNamespace
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def configure_environment() -> None:
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    paths = [ROOT / "venv" / "Lib" / "site-packages", ROOT]
    for path in paths:
        text = str(path)
        if path.exists() and text not in sys.path:
            sys.path.insert(0, text)


def main() -> int:
    configure_environment()
    from collector import CompiledPatterns, TelegramCollector

    collector = TelegramCollector.__new__(TelegramCollector)
    collector.filtrar_idosos = True
    collector.idade_maxima = 59
    collector.exigir_data_nascimento = True
    collector.idosos_ignorados = 0
    collector.sem_data_ignorados = 0
    collector.sem_score_coletados = 0
    collector.ai_validator = SimpleNamespace(enabled=False)
    collector.address_extractor = None
    collector.patterns = CompiledPatterns()

    valid = """
NOME: MARIA TESTE SILVA
CPF: 123.456.789-09
NASCIMENTO: 10/05/1990
SCORE: 810
"""
    no_score = """
NOME: JOAO TESTE SILVA
CPF: 987.654.321-00
NASCIMENTO: 12/03/1995
"""
    old = """
NOME: PAULO TESTE SILVA
CPF: 111.222.333-44
NASCIMENTO: 01/01/1960
SCORE: 700
"""
    no_birth = """
NOME: ANA TESTE SILVA
CPF: 555.666.777-88
SCORE: 720
"""

    failures: list[str] = []
    if len(collector.extract_all_data(valid)) != 1:
        failures.append("registro valido com nascimento e score foi rejeitado")
    if len(collector.extract_all_data(no_score)) != 1:
        failures.append("registro sem score deveria ser aceito")
    if collector.sem_score_coletados < 1:
        failures.append("contador de sem score nao atualizou")
    if collector.extract_all_data(old):
        failures.append("registro 60+ deveria ser ignorado")
    if collector.extract_all_data(no_birth):
        failures.append("registro sem nascimento deveria ser ignorado")

    if failures:
        print("[collector-rules] Falhas:")
        for failure in failures:
            print(f"- {failure}")
        return 1

    print("[collector-rules] Regras OK: exige nascimento, aceita sem score e barra 60+.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
