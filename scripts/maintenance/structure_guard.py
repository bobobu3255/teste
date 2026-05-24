#!/usr/bin/env python3
"""Guarda de organizacao do V12 Core.

Este script nao altera nada. Ele confere se a organizacao segura continua de pe
antes/depois de mexer no projeto.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs" / "PROJECT_ORGANIZATION.md"


@dataclass(frozen=True)
class SizeRule:
    path: str
    max_lines: int
    reason: str


REQUIRED_PATHS = (
    "main_app.py",
    "app/core/paths.py",
    "app/core/config_manager.py",
    "app/core/database.py",
    "app/core/worker_threads.py",
    "app/ui/app_bootstrap.py",
    "app/ui/app_state.py",
    "app/ui/main_layout.py",
    "app/ui/main_pages.py",
    "app/ui/simple_pages.py",
    "app/ui/generator_page.py",
    "app/ui/browser_page.py",
    "app/ui/crunchyroll_page.py",
    "app/ui/tools_page.py",
    "app/ui/tools_page_assets.py",
    "app/ui/main_actions.py",
    "app/ui/window_controls.py",
    "app/ui/components.py",
    "app/features/browser/widget.py",
    "app/features/browser/styles.py",
    "app/features/ai_assistant/widget.py",
    "app/features/ai_assistant/styles.py",
    "app/features/app_hub/maintenance_panel.py",
    "app/features/app_hub/logs_panel.py",
    "app/features/app_hub/settings_widget.py",
    "app/features/notepad/widget.py",
    "app/features/notepad/styles.py",
    "app/features/performance/widget.py",
    "app/features/performance/styles.py",
    "app/features/data_organizer/widget.py",
    "app/features/crunchyroll/widget.py",
    "app/features/crunchyroll/styles.py",
    "app/features/tools/styles.py",
    "app/services/address_generator.py",
    "app/services/address_reserve.py",
    "app/services/collector.py",
    "scripts/maintenance/health_check.py",
    "scripts/maintenance/bridge_check.py",
    "scripts/maintenance/widget_smoke_check.py",
    "scripts/maintenance/ui_style_audit.py",
    "scripts/maintenance/storage_report.py",
    "scripts/maintenance/safe_cleanup.py",
    "scripts/maintenance/structure_guard.py",
    "scripts/maintenance/verify_all.py",
)

DOC_REQUIRED = (
    "app/ui/main_pages.py",
    "app/ui/simple_pages.py",
    "app/ui/generator_page.py",
    "app/ui/browser_page.py",
    "app/ui/crunchyroll_page.py",
    "app/ui/tools_page.py",
    "app/ui/tools_page_assets.py",
    "app/ui/main_actions.py",
    "app/ui/window_controls.py",
    "app/ui/main_layout.py",
    "app/features/browser/",
    "app/features/ai_assistant/",
    "app/features/app_hub/maintenance_panel.py",
    "app/features/notepad/",
    "app/features/performance/",
    "scripts/maintenance/health_check.py",
    "scripts/maintenance/bridge_check.py",
    "scripts/maintenance/widget_smoke_check.py",
    "scripts/maintenance/ui_style_audit.py",
    "scripts/maintenance/storage_report.py",
    "scripts/maintenance/safe_cleanup.py",
    "scripts/maintenance/structure_guard.py",
    "scripts/maintenance/verify_all.py",
)

SIZE_RULES = (
    SizeRule("main_app.py", 90, "main_app.py deve continuar como entrada pequena."),
    SizeRule("app/ui/main_pages.py", 90, "main_pages.py deve apenas orquestrar abas."),
    SizeRule("app/ui/simple_pages.py", 120, "paginas simples devem ficar pequenas."),
    SizeRule("app/ui/browser_page.py", 90, "builder do navegador deve ficar enxuto."),
    SizeRule("app/ui/tools_page.py", 140, "pagina Ferramentas nao deve voltar a virar monolito."),
    SizeRule("app/ui/crunchyroll_page.py", 150, "pagina Crunchyroll deve conter so builder/acoes da tela."),
)

ROOT_BRIDGES = (
    "browser_widget.py",
    "browser_manager.py",
    "ai_assistant_widget.py",
    "notepad_widget.py",
    "performance_widget.py",
    "data_organizer.py",
    "crunchyroll_widget.py",
    "crunchyroll_login_widget.py",
    "app_hub.py",
    "database.py",
    "collector.py",
)


def line_count(path: Path) -> int:
    try:
        return len(path.read_text(encoding="utf-8", errors="replace").splitlines())
    except OSError:
        return -1


def check_required_paths() -> list[str]:
    errors: list[str] = []
    for rel in REQUIRED_PATHS:
        if not (ROOT / rel).exists():
            errors.append(f"arquivo/pasta essencial ausente: {rel}")
    return errors


def check_size_rules() -> list[str]:
    errors: list[str] = []
    for rule in SIZE_RULES:
        path = ROOT / rule.path
        count = line_count(path)
        if count < 0:
            errors.append(f"nao consegui ler {rule.path}")
        elif count > rule.max_lines:
            errors.append(f"{rule.path} tem {count} linhas; limite {rule.max_lines}. {rule.reason}")
        else:
            print(f"[guard] OK tamanho {rule.path}: {count}/{rule.max_lines}")
    return errors


def check_docs() -> list[str]:
    if not DOCS.exists():
        return ["docs/PROJECT_ORGANIZATION.md ausente"]
    text = DOCS.read_text(encoding="utf-8", errors="replace")
    missing = [item for item in DOC_REQUIRED if item not in text]
    return [f"documentacao nao cita: {item}" for item in missing]


def check_root_bridges() -> list[str]:
    errors: list[str] = []
    for rel in ROOT_BRIDGES:
        path = ROOT / rel
        if not path.exists():
            errors.append(f"ponte da raiz ausente: {rel}")
            continue
        count = line_count(path)
        if count > 80:
            errors.append(f"ponte {rel} tem {count} linhas; ela deveria ser so compatibilidade/import leve")
        else:
            print(f"[guard] OK ponte {rel}: {count} linhas")
    return errors


def main() -> int:
    print(f"[guard] Projeto: {ROOT}")
    errors: list[str] = []
    errors.extend(check_required_paths())
    errors.extend(check_size_rules())
    errors.extend(check_docs())
    errors.extend(check_root_bridges())

    if errors:
        print(f"[guard] Falhas encontradas: {len(errors)}")
        for error in errors:
            print(f"- {error}")
        return 1

    print("[guard] Organizacao OK. Estrutura principal do V12 Core continua protegida.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
