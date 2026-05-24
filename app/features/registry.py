#!/usr/bin/env python3
"""Registro leve das ferramentas do Telegram Collector Pro.

Este modulo nao importa widgets reais e nao muda a interface atual.
Ele existe para documentar o projeto e facilitar uma migracao segura
para ferramentas mais modulares no futuro.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class FeatureDefinition:
    key: str
    label: str
    module: str
    widget_class: str
    category: str
    status: str = "active"
    notes: str = ""


PRIMARY_FEATURES: Tuple[FeatureDefinition, ...] = (
    FeatureDefinition("home", "Inicio", "main_app", "SimpleApp._build_home_page", "principal"),
    FeatureDefinition("app_hub", "Hub Geral", "app.features.app_hub.widget", "AppDashboardWidget", "principal"),
    FeatureDefinition("generator", "Gerador", "main_app", "SimpleApp._build_generator_page", "principal"),
    FeatureDefinition("browser", "Navegador", "browser_widget", "BrowserWidget", "ferramentas"),
    FeatureDefinition("profile_defaults", "Padroes de Perfil", "app.features.profile_defaults.widget", "ProfileDefaultsWidget", "principal"),
    FeatureDefinition("ai", "IA Local", "ai_assistant_widget", "AIAssistantWidget", "ferramentas"),
    FeatureDefinition("crunchyroll", "Crunchyroll", "crunchyroll_widget", "CrunchyrollWidget", "ferramentas"),
    FeatureDefinition("notes", "Notas", "notepad_widget", "NotepadWidget", "ferramentas"),
    FeatureDefinition("config", "Config", "config_dialog", "ConfigDialog", "principal"),
    FeatureDefinition("telegram_accounts", "Contas Telegram", "app.features.account_manager.dialog", "GerenciadorContas", "principal"),
)

TOOL_FEATURES: Tuple[FeatureDefinition, ...] = (
    FeatureDefinition("cards", "Cartoes", "main_app", "ToolsDialog.create_card_generator_tab", "ferramentas"),
    FeatureDefinition("cep", "CEP", "main_app", "ToolsDialog.create_cep_generator_tab", "ferramentas"),
    FeatureDefinition("organizer", "Organizador", "main_app", "ToolsDialog.create_account_formatter_tab", "ferramentas"),
    FeatureDefinition("formatter", "Formatar", "app.features.data_organizer.widget", "DataOrganizer", "ferramentas"),
    FeatureDefinition("cpf_cnpj", "CPF/CNPJ", "app.features.extra_tools.widget", "ValidadorWidget", "ferramentas"),
    FeatureDefinition("performance", "Desempenho", "app.features.performance.widget", "PerformanceWidget", "ferramentas"),
    FeatureDefinition("data_pro", "Dados Pro", "app.features.data_pro.widget", "DataProWidget", "ferramentas"),
    FeatureDefinition("portuguese", "Portugues", "app.features.text_corrector.widget", "TextCorrectorWidget", "ferramentas"),
    FeatureDefinition("paramount_assist", "Paramount", "app.features.paramount_assist.widget", "ParamountAssistWidget", "ferramentas"),
    FeatureDefinition("email_codes", "Codigos", "app.features.email_codes_admin.widget", "EmailCodesAdminWidget", "ferramentas"),
    FeatureDefinition("site_leads", "Leads Site", "app.features.site_leads_admin.widget", "SiteLeadsAdminWidget", "ferramentas"),
    FeatureDefinition("temp_mail", "Email Temp", "app.features.temp_mail.widget", "TempMailWidget", "ferramentas"),
)

ALL_FEATURES: Tuple[FeatureDefinition, ...] = PRIMARY_FEATURES + TOOL_FEATURES


def feature_keys() -> Tuple[str, ...]:
    return tuple(feature.key for feature in ALL_FEATURES)


def features_by_category(category: str) -> Tuple[FeatureDefinition, ...]:
    wanted = category.strip().lower()
    return tuple(feature for feature in ALL_FEATURES if feature.category == wanted)
