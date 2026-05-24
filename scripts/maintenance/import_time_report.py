#!/usr/bin/env python3
"""Mede tempos de import para achar gargalos de inicializacao."""
from __future__ import annotations

import importlib
import os
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

MODULES = (
    "settings",
    "database",
    "collector",
    "main_app",
    "browser_widget",
    "browser_manager",
    "ai_assistant_widget",
    "crunchyroll_widget",
    "notepad_widget",
    "app_hub",
    "performance_widget",
    "data_pro_widget",
    "text_corrector_widget",
    "profile_defaults_widget",
    "cloud_service",
)


def configure_path() -> None:
    for path in (
        ROOT / "venv" / "Lib" / "site-packages",
        ROOT,
    ):
        text = str(path)
        if path.exists() and text not in sys.path:
            sys.path.insert(0, text)


def main() -> int:
    configure_path()
    print(f"[imports] Projeto: {ROOT}")
    results: list[tuple[float, str, str]] = []
    for module_name in MODULES:
        elapsed, status = measure_module(module_name)
        results.append((elapsed, module_name, status))

    for elapsed, module_name, status in sorted(results, reverse=True):
        print(f"{elapsed:7.3f}s  {module_name:<28} {status}")

    failed = [item for item in results if item[2].startswith("ERRO")]
    return 1 if failed else 0


def measure_module(module_name: str) -> tuple[float, str]:
    code = (
        "import importlib, time\n"
        f"m={module_name!r}\n"
        "t=time.perf_counter()\n"
        "importlib.import_module(m)\n"
        "print(f'{time.perf_counter()-t:.6f}')\n"
    )
    env = os.environ.copy()
    paths = [str(ROOT), str(ROOT / "venv" / "Lib" / "site-packages")]
    env["PYTHONPATH"] = os.pathsep.join(paths + ([env["PYTHONPATH"]] if env.get("PYTHONPATH") else []))
    started = time.perf_counter()
    try:
        proc = subprocess.run(
            [sys.executable, "-c", code],
            cwd=str(ROOT),
            env=env,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except subprocess.TimeoutExpired:
        return 30.0, "ERRO: timeout"
    elapsed = time.perf_counter() - started
    if proc.returncode != 0:
        detail = (proc.stderr or proc.stdout or "").strip().splitlines()
        return elapsed, f"ERRO: {detail[-1] if detail else 'falha desconhecida'}"
    try:
        measured = float((proc.stdout or "").strip().splitlines()[-1])
    except Exception:
        measured = elapsed
    return measured, "OK"


if __name__ == "__main__":
    raise SystemExit(main())
