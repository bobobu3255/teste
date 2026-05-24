#!/usr/bin/env python3
"""Relatorio de pistas visuais e de manutencao da interface.

Este script nao altera arquivos e nao reprova o build. Ele serve como mapa para
as fases de polimento: mostra telas com muito CSS solto, widgets grandes e
pontos que merecem refatoracao visual gradual.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SCAN_DIRS = (ROOT / "app" / "ui", ROOT / "app" / "features")
SKIP_PARTS = {"__pycache__", "node_modules", "venv", ".venv"}
COLOR_RE = re.compile(r"#[0-9a-fA-F]{3,8}|rgba?\(")
STYLESHEET_RE = re.compile(r"setStyleSheet\s*\(")
RADIUS_RE = re.compile(r"border-radius\s*:\s*(\d+)px")
BUTTON_HEIGHT_RE = re.compile(r"min-height\s*:\s*(\d+)px")
BLOCKING_RE = re.compile(r"\b(time\.sleep|requests\.(get|post)|subprocess\.run|Popen\()")


@dataclass(frozen=True)
class FileFinding:
    path: Path
    lines: int
    stylesheets: int
    colors: int
    large_radius: int
    tiny_controls: int
    blocking_calls: int

    @property
    def rel(self) -> str:
        return str(self.path.relative_to(ROOT)).replace("\\", "/")


def iter_python_files() -> list[Path]:
    files: list[Path] = []
    for folder in SCAN_DIRS:
        if not folder.exists():
            continue
        for path in folder.rglob("*.py"):
            if any(part in SKIP_PARTS for part in path.parts) or path.name == "styles.py":
                continue
            files.append(path)
    return sorted(files)


def analyze(path: Path) -> FileFinding:
    text = path.read_text(encoding="utf-8", errors="replace")
    radii = [int(value) for value in RADIUS_RE.findall(text)]
    heights = [int(value) for value in BUTTON_HEIGHT_RE.findall(text)]
    return FileFinding(
        path=path,
        lines=len(text.splitlines()),
        stylesheets=len(STYLESHEET_RE.findall(text)),
        colors=len(COLOR_RE.findall(text)),
        large_radius=sum(1 for value in radii if value > 12),
        tiny_controls=sum(1 for value in heights if value < 28),
        blocking_calls=len(BLOCKING_RE.findall(text)),
    )


def print_top(title: str, rows: list[tuple[int, FileFinding]], label: str, limit: int = 8) -> None:
    rows = [(score, item) for score, item in rows if score > 0]
    if not rows:
        print(f"[ui-audit] {title}: nada relevante.")
        return
    print(f"[ui-audit] {title}:")
    for score, item in rows[:limit]:
        print(f"  {score:>4} {label:<14} {item.rel}")


def main() -> int:
    print(f"[ui-audit] Projeto: {ROOT}")
    findings = [analyze(path) for path in iter_python_files()]
    print(f"[ui-audit] Arquivos analisados: {len(findings)}")

    print_top(
        "Arquivos maiores da interface",
        sorted(((item.lines, item) for item in findings if item.lines >= 350), reverse=True, key=lambda row: row[0]),
        "linhas",
    )
    print_top(
        "Mais setStyleSheet diretos",
        sorted(((item.stylesheets, item) for item in findings), reverse=True, key=lambda row: row[0]),
        "styles",
    )
    print_top(
        "Mais cores hardcoded",
        sorted(((item.colors, item) for item in findings if item.rel != "app/ui/components.py"), reverse=True, key=lambda row: row[0]),
        "cores",
    )
    print_top(
        "Raio visual acima de 12px",
        sorted(((item.large_radius, item) for item in findings), reverse=True, key=lambda row: row[0]),
        "raios",
    )
    print_top(
        "Controles com altura pequena",
        sorted(((item.tiny_controls, item) for item in findings), reverse=True, key=lambda row: row[0]),
        "pequenos",
    )
    print_top(
        "Chamadas que podem travar UI se rodarem no thread principal",
        sorted(((item.blocking_calls, item) for item in findings), reverse=True, key=lambda row: row[0]),
        "chamadas",
    )

    print("[ui-audit] Proximas telas provaveis para polimento: arquivos com muitos styles/cores e widgets grandes.")
    print("[ui-audit] Relatorio informativo apenas; nao reprova o V12 Core.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
