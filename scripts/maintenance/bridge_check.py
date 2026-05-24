#!/usr/bin/env python3
"""Confere se os arquivos ponte da raiz continuam apontando para os modulos reais."""
from __future__ import annotations

import importlib
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]

BRIDGES = (
    ("extra_tools", "app.features.extra_tools.widget", ("ValidadorWidget", "GeradorFakeWidget")),
    ("data_pro_widget", "app.features.data_pro.widget", ("DataProWidget",)),
    ("text_corrector_widget", "app.features.text_corrector.widget", ("TextCorrectorWidget",)),
    ("profile_defaults_widget", "app.features.profile_defaults.widget", ("ProfileDefaultsWidget",)),
    ("profile_defaults_manager", "app.services.profile_defaults_manager", ("ProfileDefaultsManager", "PasswordManager")),
    ("app_hub", "app.features.app_hub", ("AppDashboardWidget", "GeneralSettingsWidget")),
    ("performance_widget", "app.features.performance.widget", ("PerformanceWidget",)),
    ("data_organizer", "app.features.data_organizer.widget", ("DataOrganizer",)),
    ("account_manager", "app.features.account_manager.dialog", ("GerenciadorContas",)),
    ("account_formatter", "app.services.account_formatter", ("AccountFormatter",)),
    ("address_generator", "app.services.address_generator", ("AddressGenerator", "Endereco")),
    ("address_reserve", "app.services.address_reserve", ("AddressExtractor",)),
    ("config_manager", "app.core.config_manager", ("ConfigManager",)),
    ("exceptions", "app.core.exceptions", ("TelegramCollectorException",)),
    ("logger_manager", "app.core.logger_manager", ("LoggerManager", "get_logger")),
    ("workers", "app.core.workers", ("BaseWorker", "AsyncWorker")),
    ("cloud_service", "app.services.cloud_service", ("CloudService", "load_cloud_settings")),
    ("proxy_manager", "app.services.proxy_manager", ("ProxyManager", "ProxyConfig")),
    ("card_generator", "generators.card_generator", ("CardGenerator",)),
    ("fingerprint_generator", "generators.fingerprint_generator", ("FingerprintGenerator",)),
    ("theme", "app.ui.app_theme", ("DARK_STYLE_PRO", "LIGHT_STYLE_PRO")),
    ("database", "app.core.database", ("DatabaseManager",)),
    ("collector", "app.services.collector", ("TelegramCollector", "TelegramCollectorOptimized")),
    ("browser_manager", "app.features.browser.manager", ("BrowserManager", "BrowserProfile")),
    ("browser_widget", "app.features.browser.widget", ("BrowserWidget",)),
    ("ai_assistant_widget", "app.features.ai_assistant.widget", ("AIAssistantWidget", "AIWorker")),
    ("notepad_widget", "app.features.notepad.widget", ("NotepadWidget",)),
    ("crunchyroll_widget", "app.features.crunchyroll.widget", ("CrunchyrollWidget",)),
    ("crunchyroll_login_widget", "app.features.crunchyroll.login_widget", ("CrunchyrollLoginWidget",)),
)


def configure_path() -> None:
    for path in (
        ROOT / "venv" / "Lib" / "site-packages",
        ROOT,
    ):
        text = str(path)
        if path.exists() and text not in sys.path:
            sys.path.insert(0, text)


def check_bridges() -> list[str]:
    configure_path()
    errors: list[str] = []
    for legacy_name, target_name, attrs in BRIDGES:
        try:
            legacy = importlib.import_module(legacy_name)
            target = importlib.import_module(target_name)
        except Exception as exc:
            errors.append(f"{legacy_name} -> {target_name}: erro ao importar: {exc}")
            continue

        for attr in attrs:
            legacy_attr = getattr(legacy, attr, None)
            target_attr = getattr(target, attr, None)
            if legacy_attr is None or target_attr is None:
                errors.append(f"{legacy_name}.{attr}: atributo ausente")
            elif legacy_attr is not target_attr:
                errors.append(f"{legacy_name}.{attr}: nao aponta para {target_name}.{attr}")
            else:
                print(f"[bridge] OK {legacy_name}.{attr}")
    return errors


def main() -> int:
    print(f"[bridge] Projeto: {ROOT}")
    errors = check_bridges()
    if errors:
        print(f"[bridge] Falhas: {len(errors)}")
        for error in errors:
            print(error)
        return 1
    print("[bridge] Todas as pontes OK.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())






