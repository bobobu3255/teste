#!/usr/bin/env python3
"""Verificador leve de saude do projeto."""
from __future__ import annotations

import argparse
import os
import py_compile
import sys
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "archive",
    "backups",
    "node_modules",
    "salva",
    "venv",
}
SKIP_NAME_PARTS = (".before_",)


def iter_python_files():
    for path in ROOT.rglob("*.py"):
        try:
            rel = path.relative_to(ROOT)
        except ValueError:
            continue
        if any(part in SKIP_DIRS for part in rel.parts):
            continue
        if any(token in path.name for token in SKIP_NAME_PARTS):
            continue
        yield path


def compile_project() -> list[str]:
    errors: list[str] = []
    for path in iter_python_files():
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception:
            rel = path.relative_to(ROOT)
            errors.append(f"{rel}\n{traceback.format_exc()}")
    return errors


def run_ui_smoke() -> tuple[bool, str]:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    root_text = str(ROOT)
    if root_text not in sys.path:
        sys.path.insert(0, root_text)

    venv_site = ROOT / "venv" / "Lib" / "site-packages"
    if venv_site.exists() and str(venv_site) not in sys.path:
        sys.path.insert(0, str(venv_site))

    try:
        from PyQt5.QtWidgets import QApplication
        import main_app

        app = QApplication.instance() or QApplication([])
        window = main_app.SimpleApp()
        tab_count = getattr(window, "main_tabs", None).count() if getattr(window, "main_tabs", None) else 0
        window.close()
        app.quit()
        return True, f"SimpleApp abriu em modo teste com {tab_count} abas."
    except Exception:
        return False, traceback.format_exc()


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica compilacao e abertura basica do projeto.")
    parser.add_argument("--ui", action="store_true", help="Tambem tenta criar a janela principal em modo offscreen.")
    args = parser.parse_args()

    print(f"[health] Projeto: {ROOT}")
    errors = compile_project()
    if errors:
        print(f"[health] Erros de compilacao: {len(errors)}")
        for error in errors:
            print(error)
        return 1

    print("[health] Compilacao OK.")

    if args.ui:
        ok, message = run_ui_smoke()
        if not ok:
            print("[health] UI falhou:")
            print(message)
            return 1
        print(f"[health] UI OK. {message}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
