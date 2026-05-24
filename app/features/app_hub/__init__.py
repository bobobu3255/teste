"""Dashboard, busca global, logs e configuracoes gerais."""
from .logs_panel import PrettyLogsWidget, friendly_error_text, read_recent_logs  # noqa: F401
from .settings_widget import (  # noqa: F401
    BackupWorker,
    GeneralSettingsWidget,
    load_app_settings,
    maybe_run_daily_backup,
    save_app_settings,
)
from .widget import AppDashboardWidget, GlobalSearchDialog  # noqa: F401
