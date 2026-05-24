"""
Hub geral do app: dashboard, busca global, logs bonitos, configuracoes e backup.
"""
import json
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QFrame, QGridLayout, QHBoxLayout, QLabel, QLineEdit, QListWidget,
    QPushButton, QVBoxLayout, QWidget,
)

from browser_manager import BrowserManager
from app.core.paths import BASE_DIR, CONFIG_DIR
from app.features.app_hub.logs_panel import read_recent_logs
from app.features.app_hub.task_center import TaskCenterPanel
from app.ui.components import button_qss, card_qss, field_qss, label_qss
from app.features.app_hub.settings_widget import (
    BackupWorker,
    GeneralSettingsWidget,
    load_app_settings,
    maybe_run_daily_backup,
    save_app_settings,
)

try:
    from app.core.app_context import get_app_store
except Exception:
    get_app_store = None


def _load_json(path, default):
    try:
        if Path(path).exists():
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return default


def _list_qss():
    return """
        QListWidget {
            background: #08111f;
            color: #e2e8f0;
            border: 1px solid rgba(148,163,184,0.10);
            border-radius: 12px;
            padding: 8px;
        }
        QListWidget::item {
            padding: 7px 8px;
            border-radius: 6px;
        }
        QListWidget::item:selected {
            background: #0b2c3a;
            color: #67e8f9;
        }
        QListWidget::item:hover:!selected {
            background: rgba(148,163,184,0.08);
        }
    """


def _card(title, value, subtitle="", color="#22d3ee"):
    frame = QFrame()
    frame.setMinimumHeight(86)
    frame.setStyleSheet(card_qss("default", radius=10))
    lay = QVBoxLayout(frame)
    lay.setContentsMargins(14, 12, 14, 12)
    lay.setSpacing(4)
    t = QLabel(title)
    t.setStyleSheet(label_qss("muted") + "font-weight:800;")
    v = QLabel(str(value))
    v.setStyleSheet(f"color:{color};font-size:24px;font-weight:900;background:transparent;border:none;")
    s = QLabel(subtitle)
    s.setWordWrap(True)
    s.setStyleSheet(label_qss("muted").replace("11px", "10px"))
    lay.addWidget(t)
    lay.addWidget(v)
    lay.addWidget(s)
    return frame


class AppDashboardWidget(QWidget):
    """Dashboard inicial real, com numeros e atalhos."""

    def __init__(self, db=None, browser_widget=None, open_page=None, open_tool=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.browser_widget = browser_widget
        self.open_page = open_page
        self.open_tool = open_tool
        self.browser_manager = getattr(browser_widget, "browser_manager", None) or BrowserManager()
        self._build()
        self.refresh()

    def _build(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(14, 12, 14, 12)
        root.setSpacing(10)

        top = QHBoxLayout()
        title = QLabel("Painel Inicial")
        title.setStyleSheet(label_qss("title"))
        top.addWidget(title)
        top.addStretch()
        refresh_btn = QPushButton("Atualizar")
        refresh_btn.setCursor(Qt.PointingHandCursor)
        refresh_btn.setStyleSheet(button_qss("secondary"))
        refresh_btn.clicked.connect(self.refresh)
        top.addWidget(refresh_btn)
        root.addLayout(top)

        self.cards_grid = QGridLayout()
        self.cards_grid.setSpacing(8)
        root.addLayout(self.cards_grid)

        shortcut_row = QHBoxLayout()
        shortcuts = [
            ("Notas", lambda: self._open("Notas")),
            ("Navegador", lambda: self._open("Navegador")),
            ("IA Local", lambda: self._open("IA Local")),
            ("Ferramentas", lambda: self._open("Ferramentas")),
            ("Backup", lambda: self._open("Config")),
            ("Busca global", self.open_global_search),
        ]
        for text, fn in shortcuts:
            btn = QPushButton(text)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet(button_qss("primary" if text == "Busca global" else "secondary"))
            btn.clicked.connect(fn)
            shortcut_row.addWidget(btn)
        root.addLayout(shortcut_row)

        lists = QHBoxLayout()
        self.recent_profiles = QListWidget()
        self.recent_profiles.setMinimumHeight(170)
        self.recent_profiles.setStyleSheet(_list_qss())
        self.recent_errors = QListWidget()
        self.recent_errors.setMinimumHeight(170)
        self.recent_errors.setStyleSheet(_list_qss())
        lists.addWidget(self._panel("Ultimos perfis usados", self.recent_profiles), 1)
        self.task_center = TaskCenterPanel(self)
        lists.addWidget(self.task_center, 2)
        lists.addWidget(self._panel("Erros recentes", self.recent_errors), 1)
        root.addLayout(lists, 1)

    def _panel(self, title, widget):
        frame = QFrame()
        frame.setStyleSheet(card_qss("default", radius=10))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 10, 12, 12)
        lay.setSpacing(8)
        lbl = QLabel(title)
        lbl.setStyleSheet(label_qss("section"))
        lay.addWidget(lbl)
        lay.addWidget(widget)
        return frame

    def _clear_cards(self):
        while self.cards_grid.count():
            item = self.cards_grid.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)

    def refresh(self):
        profiles = list(getattr(self.browser_manager, "profiles", {}).values())
        open_count = len(self.browser_manager.get_active_browsers()) if hasattr(self.browser_manager, "get_active_browsers") else 0
        tasks = _load_json(CONFIG_DIR / "browser_tasks.json", [])
        if isinstance(tasks, dict):
            tasks = tasks.get("tasks") or tasks.get("items") or []
        tasks = [t for t in tasks if isinstance(t, dict)] if isinstance(tasks, list) else []
        pending_tasks = len([t for t in tasks if not t.get("done")])
        central_tasks = {}
        central_queue = []
        paramount_summary = {}
        if get_app_store:
            try:
                store = get_app_store()
                central_tasks = store.task_counts()
                central_queue = store.list_tasks(status=["running", "pending", "review", "error"], limit=10)
                paramount_summary = store.get_state("paramount_assist.summary", {})
            except Exception:
                central_tasks = {}
                central_queue = []
                paramount_summary = {}
        pending_tasks += int(central_tasks.get("pending", 0)) + int(central_tasks.get("running", 0)) + int(central_tasks.get("review", 0))
        accounts = _load_json(CONFIG_DIR / "browser_accounts.json", [])
        if isinstance(accounts, dict):
            accounts = accounts.get("accounts") or accounts.get("items") or []
        accounts = [a for a in accounts if isinstance(a, dict)] if isinstance(accounts, list) else []
        backup_count = 0
        for backups_dir in (BASE_DIR / "browser_backups", BASE_DIR / "backups" / "browser", BASE_DIR / "backups" / "app_state"):
            if backups_dir.exists():
                backup_count += len(list(backups_dir.glob("*.zip"))) + len(list(backups_dir.glob("*.sqlite3"))) + len(list(backups_dir.glob("*.json")))
        total_accounts = len(accounts) + int(paramount_summary.get("accounts", 0) or 0)
        stats_total = 0
        try:
            stats_total = self.db.get_stats().get("total", 0) if self.db else 0
        except Exception:
            stats_total = 0

        self._clear_cards()
        cards = [
            ("Perfis", len(profiles), "total no navegador", "#22d3ee"),
            ("Abertos", open_count, "navegadores ativos", "#10b981"),
            ("Tarefas", pending_tasks, "pendentes", "#f59e0b"),
            ("Contas", total_accounts, "navegador + paramount", "#a78bfa"),
            ("Backups", backup_count, "arquivos seguros", "#38bdf8"),
            ("Base", stats_total, "registros do gerador", "#34d399"),
        ]
        for i, data in enumerate(cards):
            self.cards_grid.addWidget(_card(*data), i // 3, i % 3)

        self.recent_profiles.clear()
        profiles.sort(key=lambda p: getattr(p, "last_used", "") or "", reverse=True)
        for p in profiles[:8]:
            tags = ", ".join(getattr(p, "tags", []) or []) or "sem tags"
            self.recent_profiles.addItem(f"{p.name}  |  {tags}")

        if hasattr(self, "task_center"):
            self.task_center.refresh()

        self.recent_errors.clear()
        for item in read_recent_logs(limit=8, only_errors=True):
            self.recent_errors.addItem(item)

    def _format_task(self, task):
        status = str(task.get("status") or "pending")
        label = {
            "pending": "Pendente",
            "running": "Rodando",
            "success": "OK",
            "error": "Erro",
            "review": "Revisar",
            "cancelled": "Cancelada",
        }.get(status, status)
        title = str(task.get("title") or task.get("kind") or "Tarefa")
        source = str(task.get("source") or "app")
        return f"{label} | {source} | {title}"

    def _open(self, name):
        if self.open_page:
            self.open_page(name)

    def _tool(self, index):
        if self.open_tool:
            self.open_tool(index)

    def open_global_search(self):
        dialog = GlobalSearchDialog(self.browser_manager, self)
        dialog.exec_()


class GlobalSearchDialog(QDialog):
    """Busca em perfis, contas, tarefas, favoritos, logs e notas."""

    def __init__(self, browser_manager=None, parent=None):
        super().__init__(parent)
        self.browser_manager = browser_manager or BrowserManager()
        self.setWindowTitle("Busca global")
        self.resize(760, 520)
        self.setStyleSheet("QDialog{background:#07080f;}")
        self._records = self._collect_records()
        self._build()
        self.search_input.setFocus()

    def _build(self):
        lay = QVBoxLayout(self)
        self.search_input = QLineEdit()
        self.search_input.setStyleSheet(field_qss())
        self.search_input.setPlaceholderText("Pesquisar perfil, nota, conta, email, senha, ferramenta, log ou favorito...")
        self.search_input.textChanged.connect(self._filter)
        lay.addWidget(self.search_input)
        self.results = QListWidget()
        self.results.setStyleSheet(_list_qss())
        lay.addWidget(self.results, 1)
        close_btn = QPushButton("Fechar")
        close_btn.setCursor(Qt.PointingHandCursor)
        close_btn.setStyleSheet(button_qss("secondary"))
        close_btn.clicked.connect(self.accept)
        lay.addWidget(close_btn)
        self._filter("")

    def _collect_records(self):
        records = []
        if get_app_store:
            try:
                for entity in get_app_store().list_entities(limit=600):
                    text = " ".join(
                        str(part or "")
                        for part in (
                            entity.get("title"),
                            entity.get("summary"),
                            entity.get("entity_type"),
                            entity.get("source"),
                            entity.get("status"),
                            json.dumps(entity.get("payload", {}), ensure_ascii=False),
                        )
                    )
                    label = str(entity.get("entity_type") or "Item").replace("_", " ").title()
                    display = f"{entity.get('title', '')} | {entity.get('status', '')}"
                    records.append((label, text, display[:140]))
            except Exception:
                pass
        for p in getattr(self.browser_manager, "profiles", {}).values():
            text = " ".join([
                getattr(p, "name", ""), getattr(p, "id", ""), getattr(p, "notes", ""),
                ", ".join(getattr(p, "tags", []) or []), getattr(p, "proxy", "") or "",
            ])
            records.append(("Perfil", text, f"{p.name} | {p.id}"))
        for file_name, label, keys in [
            ("browser_accounts.json", "Conta", ["name", "email", "site", "status", "notes"]),
            ("browser_tasks.json", "Tarefa", ["title", "profile_name", "account_name", "notes"]),
            ("default_favorites.json", "Favorito", ["name", "url", "folder"]),
        ]:
            data = _load_json(CONFIG_DIR / file_name, [])
            if isinstance(data, dict):
                data = data.get("items") or data.get("favorites") or []
            for row in data if isinstance(data, list) else []:
                text = " ".join(str(row.get(k, "")) for k in keys if isinstance(row, dict))
                records.append((label, text, text[:120]))
        notes_data = _load_json(BASE_DIR / "notepad_session.json", {})
        records.append(("Notas", json.dumps(notes_data, ensure_ascii=False), "Sessao do bloco de notas"))
        for line in read_recent_logs(limit=80, only_errors=False):
            records.append(("Log", line, line[:140]))
        return records

    def _filter(self, text):
        q = text.strip().lower()
        self.results.clear()
        for kind, haystack, display in self._records:
            if not q or q in haystack.lower():
                self.results.addItem(f"{kind}: {display}")


