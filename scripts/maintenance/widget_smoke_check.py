#!/usr/bin/env python3
"""Teste rapido para detectar widgets quebrados sem abrir a janela inteira."""
from __future__ import annotations

import argparse
import os
import sys
import traceback
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def configure_environment() -> None:
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    for path in (
        ROOT / "venv" / "Lib" / "site-packages",
        ROOT,
    ):
        text = str(path)
        if path.exists() and text not in sys.path:
            sys.path.insert(0, text)


def build_checks(include_heavy: bool):
    from database import DatabaseManager

    db = DatabaseManager()
    checks = [
        ("Cartoes", lambda: __import__("app.features.tools.dialog", fromlist=["ToolsDialog"]).ToolsDialog().create_card_generator_tab()),
        ("CEP", lambda: __import__("app.features.tools.dialog", fromlist=["ToolsDialog"]).ToolsDialog().create_cep_generator_tab()),
        ("Organizador", lambda: __import__("app.features.tools.dialog", fromlist=["ToolsDialog"]).ToolsDialog().create_account_formatter_tab()),
        ("Formatar", lambda: __import__("data_organizer", fromlist=["DataOrganizer"]).DataOrganizer()),
        ("CPF/CNPJ", lambda: __import__("extra_tools", fromlist=["ValidadorWidget"]).ValidadorWidget()),
        ("Fake", lambda: __import__("extra_tools", fromlist=["GeradorFakeWidget"]).GeradorFakeWidget()),
        ("Desempenho", lambda: __import__("performance_widget", fromlist=["PerformanceWidget"]).PerformanceWidget()),
        ("Dados Pro", lambda: __import__("data_pro_widget", fromlist=["DataProWidget"]).DataProWidget(db)),
        ("Portugues", lambda: __import__("text_corrector_widget", fromlist=["TextCorrectorWidget"]).TextCorrectorWidget()),
        ("Paramount", lambda: __import__("paramount_assist_widget", fromlist=["ParamountAssistWidget"]).ParamountAssistWidget()),
        ("Codigos", lambda: __import__("email_codes_admin_widget", fromlist=["EmailCodesAdminWidget"]).EmailCodesAdminWidget()),
        ("Leads Site", lambda: __import__("site_leads_admin_widget", fromlist=["SiteLeadsAdminWidget"]).SiteLeadsAdminWidget()),
        ("Email Temp", lambda: __import__("temp_mail_widget", fromlist=["TempMailWidget"]).TempMailWidget()),
        ("Dashboard", lambda: __import__("app_hub", fromlist=["AppDashboardWidget"]).AppDashboardWidget(db=db, open_page=lambda *_: None, open_tool=lambda *_: None)),
        ("Config Geral", lambda: __import__("app_hub", fromlist=["GeneralSettingsWidget"]).GeneralSettingsWidget(None)),
    ]
    if include_heavy:
        checks.extend([
            ("Navegador", lambda: __import__("browser_widget", fromlist=["BrowserWidget"]).BrowserWidget()),
            ("IA Local", lambda: __import__("ai_assistant_widget", fromlist=["AIAssistantWidget"]).AIAssistantWidget()),
            ("Notas", lambda: __import__("notepad_widget", fromlist=["NotepadWidget"]).NotepadWidget()),
            ("Crunchyroll", lambda: __import__("crunchyroll_widget", fromlist=["CrunchyrollWidget"]).CrunchyrollWidget()),
            ("Crunchyroll Login", lambda: __import__("crunchyroll_login_widget", fromlist=["CrunchyrollLoginWidget"]).CrunchyrollLoginWidget()),
        ])
    return checks


def run_check(name: str, factory):
    try:
        widget = factory()
        if hasattr(widget, "deleteLater"):
            widget.deleteLater()
        return True, "OK"
    except Exception as exc:
        last = traceback.format_exc().strip().splitlines()[-1]
        return False, f"ERRO: {last or exc}"


def run_compact_panel_check():
    """Valida copias separadas do painel compacto sem depender da janela principal."""
    try:
        from PyQt5.QtWidgets import QApplication
        from app.ui.shell_widgets import CompactWidget

        widget = CompactWidget(None, None, None)
        widget._fields["cpf"].setText("123.456.789-00")
        widget._copy_field("CPF", widget._fields["cpf"])
        if QApplication.clipboard().text() != "123.456.789-00":
            return False, "ERRO: CPF nao copiado separadamente"

        widget._cep_fields["cidade"].setText("Rio Branco")
        widget._copy_field("Cidade", widget._cep_fields["cidade"])
        if QApplication.clipboard().text() != "Rio Branco":
            return False, "ERRO: cidade nao copiada separadamente"

        widget._cep_fields["estado"].setText("Acre")
        widget._copy_field("Estado", widget._cep_fields["estado"])
        if QApplication.clipboard().text() != "Acre":
            return False, "ERRO: estado nao copiado separadamente"

        widget.hide()
        widget.deleteLater()
        return True, "OK"
    except Exception as exc:
        last = traceback.format_exc().strip().splitlines()[-1]
        return False, f"ERRO: {last or exc}"


def run_browser_launch_guard_check():
    """Confere a trava que impede duas aberturas simultaneas do mesmo perfil."""
    try:
        from browser_manager import BrowserManager

        manager = BrowserManager()
        profile_id = "__smoke_launch_guard__"
        first = manager.begin_profile_launch(profile_id)
        second = manager.begin_profile_launch(profile_id)
        launching = manager.is_profile_launching(profile_id)
        manager.end_profile_launch(profile_id)
        released = not manager.is_profile_launching(profile_id)
        if not first or second or not launching or not released:
            return False, "ERRO: trava de abertura duplicada falhou"
        return True, "OK"
    except Exception as exc:
        last = traceback.format_exc().strip().splitlines()[-1]
        return False, f"ERRO: {last or exc}"


def main() -> int:
    parser = argparse.ArgumentParser(description="Verifica widgets principais em modo offscreen.")
    parser.add_argument("--heavy", action="store_true", help="inclui widgets mais pesados como navegador, IA, notas e Crunchyroll")
    args = parser.parse_args()

    configure_environment()
    from PyQt5.QtWidgets import QApplication

    app = QApplication.instance() or QApplication([])
    print(f"[widgets] Projeto: {ROOT}")
    failures = []
    for name, factory in build_checks(args.heavy):
        ok, status = run_check(name, factory)
        print(f"[widgets] {name:<18} {status}")
        if not ok:
            failures.append(name)

    ok, status = run_compact_panel_check()
    print(f"[widgets] {'Painel Compacto':<18} {status}")
    if not ok:
        failures.append("Painel Compacto")

    ok, status = run_browser_launch_guard_check()
    print(f"[widgets] {'Trava Navegador':<18} {status}")
    if not ok:
        failures.append("Trava Navegador")

    app.processEvents()
    if not failures:
        print("[widgets] Todas as ferramentas testadas abriram em modo seguro.")
        return 0
    print("[widgets] Falhas:", ", ".join(failures))
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
