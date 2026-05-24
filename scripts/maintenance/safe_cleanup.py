#!/usr/bin/env python3
"""Limpeza segura do projeto.

Por padrao, este script so mostra o que poderia ser limpo. Use --apply apenas
quando quiser remover os itens seguros listados. Ele protege perfis do navegador,
cookies, backups, banco, IA, configuracoes e dependencias.
"""
from __future__ import annotations

import argparse
import shutil
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

PROTECTED_TOP_LEVEL = {
    "browser_profiles",
    "browser_config",
    "browser_extensions",
    "backups",
    "archive",
    "venv",
    ".venv",
    "config",
    "IA_Saidas",
    "conta_1",
    "crunchyroll_bot",
    "crunchyroll_login_bot",
    "dados.db",
    "notepad_session.json",
    "notepad_snippets.json",
    "enderecos_reserva.json",
}

SAFE_CACHE_DIRS = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
SAFE_FILE_SUFFIXES = {".pyc", ".pyo"}


@dataclass(frozen=True)
class Candidate:
    path: Path
    bytes: int
    kind: str
    reason: str


def human_size(value: int) -> str:
    units = ("B", "KB", "MB", "GB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def is_inside(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def top_level_name(path: Path, root: Path) -> str:
    try:
        rel = path.resolve().relative_to(root.resolve())
    except ValueError:
        return ""
    return rel.parts[0] if rel.parts else ""


def is_protected(path: Path, root: Path) -> bool:
    top = top_level_name(path, root)
    return top in PROTECTED_TOP_LEVEL


def folder_size(path: Path) -> int:
    total = 0
    stack = [path]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue
        for entry in entries:
            try:
                if entry.is_dir():
                    stack.append(entry)
                elif entry.is_file():
                    total += entry.stat().st_size
            except OSError:
                continue
    return total


def candidate_size(path: Path) -> int:
    try:
        if path.is_dir():
            return folder_size(path)
        if path.is_file():
            return path.stat().st_size
    except OSError:
        return 0
    return 0


def collect_candidates(root: Path) -> list[Candidate]:
    candidates: list[Candidate] = []
    stack = [root]

    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue

        for entry in entries:
            if is_protected(entry, root):
                continue

            try:
                if entry.is_dir():
                    if entry.name in SAFE_CACHE_DIRS:
                        candidates.append(
                            Candidate(
                                path=entry,
                                bytes=candidate_size(entry),
                                kind="cache python",
                                reason="cache recriado automaticamente pelo Python",
                            )
                        )
                    elif top_level_name(entry, root) == "_temp":
                        candidates.append(
                            Candidate(
                                path=entry,
                                bytes=candidate_size(entry),
                                kind="temporario",
                                reason="arquivo/pasta dentro de _temp",
                            )
                        )
                    else:
                        stack.append(entry)
                elif entry.is_file():
                    if entry.suffix.lower() in SAFE_FILE_SUFFIXES:
                        candidates.append(
                            Candidate(
                                path=entry,
                                bytes=candidate_size(entry),
                                kind="bytecode",
                                reason="arquivo compilado recriado automaticamente",
                            )
                        )
                    elif top_level_name(entry, root) == "_temp":
                        candidates.append(
                            Candidate(
                                path=entry,
                                bytes=candidate_size(entry),
                                kind="temporario",
                                reason="arquivo dentro de _temp",
                            )
                        )
            except OSError:
                continue

    return sorted(candidates, key=lambda item: item.bytes, reverse=True)


def can_remove(candidate: Candidate, root: Path) -> bool:
    path = candidate.path.resolve()
    if not is_inside(path, root):
        return False
    if is_protected(path, root):
        return False
    if path.name in SAFE_CACHE_DIRS:
        return True
    if path.suffix.lower() in SAFE_FILE_SUFFIXES:
        return True
    if top_level_name(path, root) == "_temp":
        return True
    return False


def remove_candidate(candidate: Candidate, root: Path) -> bool:
    path = candidate.path.resolve()
    if not can_remove(candidate, root):
        print(f"RECUSADO: {path}")
        return False
    try:
        if path.is_dir():
            shutil.rmtree(path)
        elif path.exists():
            path.unlink()
        return True
    except OSError as exc:
        print(f"ERRO ao limpar {path}: {exc}")
        return False


def print_report(root: Path, candidates: list[Candidate], limit: int) -> None:
    total = sum(item.bytes for item in candidates)
    print(f"Projeto: {root}")
    print(f"Itens seguros encontrados: {len(candidates)}")
    print(f"Espaco recuperavel estimado: {human_size(total)}")
    print()
    print("Protegido sempre:")
    print("- perfis do navegador, cookies, backups, banco, IA, extensoes, venv e bots externos")
    print()

    if not candidates:
        print("Nada seguro para limpar agora.")
        return

    print("Maiores itens seguros:")
    for item in candidates[:limit]:
        try:
            rel = item.path.relative_to(root)
        except ValueError:
            rel = item.path
        print(f"{human_size(item.bytes):>9}  {item.kind:<13}  {rel}  ({item.reason})")

    if len(candidates) > limit:
        print(f"... mais {len(candidates) - limit} item(ns) menores.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Mostra e aplica limpeza segura do projeto.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Pasta do projeto.")
    parser.add_argument("--apply", action="store_true", help="Remove apenas os itens seguros listados.")
    parser.add_argument("--limit", type=int, default=20, help="Quantidade de itens para mostrar.")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        print(f"Pasta nao encontrada: {root}")
        return 2

    candidates = collect_candidates(root)
    print_report(root, candidates, args.limit)

    if not args.apply:
        print()
        print("Modo simulacao. Para limpar estes itens seguros, rode novamente com --apply.")
        return 0

    print()
    print("Aplicando limpeza segura...")
    removed = 0
    freed = 0
    for candidate in candidates:
        size = candidate.bytes
        if remove_candidate(candidate, root):
            removed += 1
            freed += size

    print(f"Limpeza concluida: {removed} item(ns), {human_size(freed)} liberados.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
