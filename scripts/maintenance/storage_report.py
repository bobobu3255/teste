#!/usr/bin/env python3
"""Relatorio seguro de tamanho do projeto.

Nao apaga arquivos. A ideia e mostrar onde o projeto esta ficando pesado,
principalmente para uso em pendrive.
"""
from __future__ import annotations

import argparse
import heapq
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

WATCHED_DIRS = (
    "browser_profiles",
    "backups",
    "archive",
    "venv",
    "IA_Saidas",
    "browser_extensions",
    "crunchyroll_bot",
    "crunchyroll_login_bot",
    "config",
)

SKIP_NAMES = {".git", "__pycache__"}


@dataclass(frozen=True)
class FolderStat:
    path: Path
    bytes: int
    files: int
    dirs: int


def human_size(value: int) -> str:
    units = ("B", "KB", "MB", "GB", "TB")
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(size)} {unit}"
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def scan_folder(path: Path) -> FolderStat:
    total = 0
    file_count = 0
    dir_count = 0
    stack = [path]

    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue

        for entry in entries:
            if entry.name in SKIP_NAMES:
                continue
            try:
                if entry.is_dir():
                    dir_count += 1
                    stack.append(entry)
                elif entry.is_file():
                    file_count += 1
                    total += entry.stat().st_size
            except OSError:
                continue

    return FolderStat(path=path, bytes=total, files=file_count, dirs=dir_count)


def top_level_stats(root: Path) -> list[FolderStat]:
    stats: list[FolderStat] = []
    for entry in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        if entry.name in SKIP_NAMES or not entry.is_dir():
            continue
        stats.append(scan_folder(entry))
    return sorted(stats, key=lambda item: item.bytes, reverse=True)


def largest_files(root: Path, limit: int) -> list[tuple[int, Path]]:
    if limit <= 0:
        return []

    heap: list[tuple[int, str, Path]] = []
    stack = [root]
    while stack:
        current = stack.pop()
        try:
            entries = list(current.iterdir())
        except OSError:
            continue

        for entry in entries:
            if entry.name in SKIP_NAMES:
                continue
            try:
                if entry.is_dir():
                    stack.append(entry)
                elif entry.is_file():
                    size = entry.stat().st_size
                    item = (size, str(entry).lower(), entry)
                    if len(heap) < limit:
                        heapq.heappush(heap, item)
                    else:
                        heapq.heappushpop(heap, item)
            except OSError:
                continue

    return [(size, path) for size, _key, path in sorted(heap, reverse=True)]


def print_section(title: str) -> None:
    print()
    print(title)
    print("-" * len(title))


def print_advice(total_bytes: int, watched: dict[str, FolderStat]) -> None:
    print_section("Leitura rapida")
    print("- Codigo e interface quase nunca pesam muitos GB.")
    print("- Perfis do navegador, caches, cookies e backups sao os maiores vilões.")
    print("- Em pendrive, muitos arquivos pequenos podem deixar abrir/copiar mais lento.")
    print("- Este relatorio nao limpa nada; ele so aponta onde vale olhar.")

    browser_profiles = watched.get("browser_profiles")
    backups = watched.get("backups")

    print_section("Alertas")
    if total_bytes > 8 * 1024**3:
        print("! Projeto acima de 8 GB: no pendrive pode ficar pesado para backup e inicializacao.")
    elif total_bytes > 4 * 1024**3:
        print("! Projeto acima de 4 GB: ainda ok, mas vale vigiar perfis e backups.")
    else:
        print("OK Tamanho total controlado para o projeto com perfis de navegador.")

    if browser_profiles and browser_profiles.bytes > 1024**3:
        print("! browser_profiles passou de 1 GB: normal se ha muitos perfis, mas cache pode crescer rapido.")
    if backups and backups.bytes > 512 * 1024**2:
        print("! backups passou de 512 MB: bom mover backups antigos para HD/cloud quando estiver seguro.")
    if not browser_profiles and not backups:
        print("OK Nenhuma pasta pesada principal encontrada.")

    print_section("O que evitar")
    print("- Nao apague browser_profiles se quer manter login/cookies dos perfis.")
    print("- Nao apague backups sem ter outro backup testado.")
    print("- Nao mova venv/dependencias no susto; isso pode quebrar inicializacao.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Mostra o tamanho real do projeto sem apagar nada.")
    parser.add_argument("--root", type=Path, default=ROOT, help="Pasta do projeto.")
    parser.add_argument("--top-files", type=int, default=8, help="Quantidade de arquivos grandes para listar.")
    args = parser.parse_args()

    root = args.root.resolve()
    if not root.exists():
        print(f"Pasta nao encontrada: {root}")
        return 2

    print(f"Projeto: {root}")
    stats = top_level_stats(root)
    root_files_size = sum(entry.stat().st_size for entry in root.iterdir() if entry.is_file())
    total = root_files_size + sum(item.bytes for item in stats)
    print(f"Tamanho total estimado: {human_size(total)}")

    print_section("Pastas maiores")
    for item in stats[:18]:
        print(f"{human_size(item.bytes):>10}  {item.path.name:<28}  {item.files} arquivos")

    watched = {item.path.name: item for item in stats if item.path.name in WATCHED_DIRS}
    print_section("Pastas importantes")
    for name in WATCHED_DIRS:
        path = root / name
        item = watched.get(name)
        if item:
            print(f"{human_size(item.bytes):>10}  {name:<28}  {item.files} arquivos")
        elif path.exists():
            print(f"{human_size(0):>10}  {name:<28}  vazio ou inacessivel")

    files = largest_files(root, args.top_files)
    if files:
        print_section("Arquivos maiores")
        for size, path in files:
            try:
                rel = path.relative_to(root)
            except ValueError:
                rel = path
            print(f"{human_size(size):>10}  {rel}")

    print_advice(total, watched)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
