#!/usr/bin/env python3
"""Caminhos centrais do projeto."""

from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[2]
CONFIG_DIR = BASE_DIR / "browser_config"
APP_DATA_DIR = BASE_DIR / "app_data"
TEMP_DIR = BASE_DIR / "_temp"
BACKUP_DIR = BASE_DIR / "backups"
AI_OUTPUT_DIR = BASE_DIR / "IA_Saidas"
ARCHIVE_DIR = BASE_DIR / "archive"
DEV_BACKUPS_DIR = ARCHIVE_DIR / "dev_backups"
DOCS_DIR = BASE_DIR / "docs"
SCRIPTS_DIR = BASE_DIR / "scripts"


def ensure_runtime_dirs() -> None:
    for path in (
        CONFIG_DIR,
        APP_DATA_DIR,
        TEMP_DIR,
        BACKUP_DIR,
        AI_OUTPUT_DIR,
        ARCHIVE_DIR,
        DEV_BACKUPS_DIR,
        DOCS_DIR,
        SCRIPTS_DIR,
    ):
        path.mkdir(parents=True, exist_ok=True)
