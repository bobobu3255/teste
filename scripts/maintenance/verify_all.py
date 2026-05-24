#!/usr/bin/env python3
"""Roda os principais verificadores de manutencao do app."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts" / "maintenance"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.core.app_metadata import APP_CODENAME


@dataclass(frozen=True)
class Check:
    name: str
    args: tuple[str, ...]
    description: str
    quick: bool = True


CHECKS = (
    Check("estrutura", ("structure_guard.py",), "Confere organizacao, pontes leves e documentacao."),
    Check("health-ui", ("health_check.py", "--ui"), "Compila o projeto e abre a janela principal em modo invisivel."),
    Check("pontes", ("bridge_check.py",), "Confere imports antigos que apontam para modulos novos."),
    Check("coletador", ("collector_rules_check.py",), "Garante nascimento obrigatorio, sem score aceito e 60+ filtrado."),
    Check("estado-central", ("app_store_check.py",), "Valida SQLite central, eventos e fila de tarefas."),
    Check("ui-kit", ("ui_components_check.py",), "Valida componentes visuais compartilhados."),
    Check("visual-audit", ("ui_style_audit.py",), "Mapeia dividas visuais sem travar o build.", quick=False),
    Check("widgets", ("widget_smoke_check.py",), "Abre as ferramentas principais em modo seguro."),
    Check("imports", ("import_time_report.py",), "Mede gargalos de importacao.", quick=False),
)


def build_env() -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("PYTHONIOENCODING", "utf-8")
    env.setdefault("QT_QPA_PLATFORM", "offscreen")

    paths = [str(ROOT), str(ROOT / "venv" / "Lib" / "site-packages")]
    old = env.get("PYTHONPATH")
    env["PYTHONPATH"] = os.pathsep.join(paths + ([old] if old else []))
    return env


def run_check(check: Check, env: dict[str, str]) -> bool:
    command = [sys.executable, str(SCRIPTS / check.args[0]), *check.args[1:]]
    print()
    print(f"[verify] {check.name}: {check.description}")
    print(f"[verify] comando: {' '.join(command)}")
    started = time.perf_counter()
    proc = subprocess.run(
        command,
        cwd=str(ROOT),
        env=env,
        capture_output=True,
        text=True,
        timeout=180,
    )
    elapsed = time.perf_counter() - started

    output = (proc.stdout or "").strip()
    error = (proc.stderr or "").strip()
    if output:
        print(output)
    if error:
        print(error)

    if proc.returncode == 0:
        print(f"[verify] OK {check.name} em {elapsed:.1f}s")
        return True

    print(f"[verify] FALHOU {check.name} em {elapsed:.1f}s (codigo {proc.returncode})")
    return False


def main() -> int:
    parser = argparse.ArgumentParser(description=f"Roda a bateria de verificacao segura do {APP_CODENAME}.")
    parser.add_argument("--quick", action="store_true", help="Pula verificacoes mais lentas, como relatorio de imports.")
    args = parser.parse_args()

    print(f"[verify] Projeto: {ROOT}")
    print("[verify] Modo: rapido" if args.quick else "[verify] Modo: completo")
    env = build_env()

    selected = [check for check in CHECKS if check.quick or not args.quick]
    failures: list[str] = []
    started = time.perf_counter()
    for check in selected:
        if not run_check(check, env):
            failures.append(check.name)

    elapsed = time.perf_counter() - started
    if failures:
        print()
        print(f"[verify] Falhas: {', '.join(failures)}")
        print(f"[verify] Tempo total: {elapsed:.1f}s")
        return 1

    print()
    print(f"[verify] Tudo OK. O {APP_CODENAME} passou na bateria de manutencao.")
    print(f"[verify] Tempo total: {elapsed:.1f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
