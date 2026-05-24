#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Desempenho Pro - monitoramento e ajustes seguros.

Este modulo evita tweaks destrutivos: nada de apagar arquivos do Windows,
nada de .reg/.bat desconhecido e nada de BCDEDIT automatico.
"""
import ctypes
import tempfile
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from ctypes import wintypes

from PyQt5.QtCore import QThread, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.paths import BASE_DIR
from app.features.performance.styles import (
    action_button_qss, accent_card_qss, banner_qss, history_chart_qss, panel_qss,
    perf_header_qss, perf_label_qss, performance_widget_qss, pill_qss,
    stat_card_qss, status_badge_qss,
)


CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


class FILETIME(ctypes.Structure):
    _fields_ = [
        ("dwLowDateTime", wintypes.DWORD),
        ("dwHighDateTime", wintypes.DWORD),
    ]


class MEMORYSTATUSEX(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


def _filetime_to_int(value):
    return (value.dwHighDateTime << 32) + value.dwLowDateTime


def _gb(value):
    try:
        return f"{float(value) / (1024 ** 3):.1f} GB"
    except Exception:
        return "N/D"


def _run_command(args, timeout=8):
    try:
        proc = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=timeout,
            creationflags=CREATE_NO_WINDOW,
        )
        return proc.returncode, (proc.stdout or "").strip(), (proc.stderr or "").strip()
    except FileNotFoundError:
        return 127, "", f"{args[0]} nao encontrado"
    except subprocess.TimeoutExpired:
        return 124, "", "Tempo limite excedido"
    except Exception as exc:
        return 1, "", str(exc)


def _powershell_json_data(command, timeout=8):
    code, out, err = _run_command(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        timeout=timeout,
    )
    if code != 0 or not out:
        return None, err or out
    try:
        return json.loads(out), ""
    except Exception as exc:
        return None, str(exc)


def _query_cpu_clock_safe():
    command = "(Get-CimInstance Win32_Processor | Select-Object -First 1 -ExpandProperty CurrentClockSpeed)"
    code, out, _ = _run_command(["powershell", "-NoProfile", "-Command", command], timeout=5)
    try:
        return f"{float(out.strip()) / 1000:.2f} GHz" if code == 0 and out.strip() else "N/D"
    except Exception:
        return "N/D"


def _query_standby_memory_safe():
    command = (
        "$m=Get-CimInstance Win32_PerfRawData_PerfOS_Memory;"
        "[pscustomobject]@{"
        "Standby=($m.StandbyCacheCoreBytes+$m.StandbyCacheNormalPriorityBytes+$m.StandbyCacheReserveBytes)"
        "} | ConvertTo-Json -Compress"
    )
    data, _ = _powershell_json_data(command, timeout=6)
    if not data:
        return "N/D"
    return _gb(int(data.get("Standby") or 0))


def _query_storage_health_safe():
    command = (
        "$rows=@();"
        "Get-PhysicalDisk | ForEach-Object {"
        "$r=$_ | Get-StorageReliabilityCounter -ErrorAction SilentlyContinue;"
        "$rows += [pscustomobject]@{Name=$_.FriendlyName;Health=$_.HealthStatus;"
        "Media=$_.MediaType;Temp=if($r){$r.Temperature}else{$null};Wear=if($r){$r.Wear}else{$null}}"
        "}; $rows | ConvertTo-Json -Compress"
    )
    data, _ = _powershell_json_data(command, timeout=8)
    if not data:
        return "N/D"
    rows = data if isinstance(data, list) else [data]
    summary = []
    for row in rows[:2]:
        name = str(row.get("Name") or "Disco").strip()
        health = str(row.get("Health") or "N/D")
        temp = row.get("Temp")
        wear = row.get("Wear")
        extra = []
        if temp not in (None, ""):
            extra.append(f"{temp}C")
        if wear not in (None, ""):
            extra.append(f"wear {wear}%")
        suffix = " / ".join(extra)
        summary.append(f"{name}: {health}" + (f" ({suffix})" if suffix else ""))
    return " | ".join(summary) if summary else "N/D"


def _query_power_plan_safe():
    code, out, _ = _run_command(["powercfg", "/getactivescheme"], timeout=5)
    if code != 0 or not out:
        return "N/D"
    match = re.search(r"\((.*?)\)", out)
    return match.group(1).strip() if match else out.strip()


def _query_admin_safe():
    try:
        return "Administrador" if ctypes.windll.shell32.IsUserAnAdmin() else "Usuario normal"
    except Exception:
        return "N/D"


def _query_network_totals_safe():
    command = (
        "$s=Get-NetAdapterStatistics -ErrorAction SilentlyContinue | "
        "Measure-Object -Property ReceivedBytes,SentBytes -Sum;"
        "$rx=($s | Where-Object Property -eq 'ReceivedBytes').Sum;"
        "$tx=($s | Where-Object Property -eq 'SentBytes').Sum;"
        "[pscustomobject]@{Rx=[int64]$rx;Tx=[int64]$tx} | ConvertTo-Json -Compress"
    )
    data, _ = _powershell_json_data(command, timeout=6)
    if not data:
        return 0, 0
    return int(data.get("Rx") or 0), int(data.get("Tx") or 0)


def _query_top_processes_safe():
    command = (
        "Get-Process | Sort-Object WS -Descending | Select-Object -First 8 "
        "@{n='Name';e={$_.ProcessName}},Id,@{n='MB';e={[math]::Round($_.WS/1MB,1)}} "
        "| ConvertTo-Json -Compress"
    )
    data, _ = _powershell_json_data(command, timeout=8)
    if not data:
        return "N/D"
    rows = data if isinstance(data, list) else [data]
    lines = []
    for row in rows:
        lines.append(f"{row.get('Name', 'proc')}  PID {row.get('Id', '-')}  {row.get('MB', '-')} MB")
    return "\n".join(lines)


def _query_lhm_sensors_safe():
    command = (
        "$rows=Get-CimInstance -Namespace root\\LibreHardwareMonitor -ClassName Sensor "
        "-ErrorAction SilentlyContinue | "
        "Where-Object {$_.SensorType -in @('Temperature','Fan')} | "
        "Select-Object Name,SensorType,Value | ConvertTo-Json -Compress"
    )
    data, _ = _powershell_json_data(command, timeout=8)
    if not data:
        return {"summary": "N/D", "temps": {}}

    rows = data if isinstance(data, list) else [data]
    temps = {}
    fans = []
    for row in rows:
        name = str(row.get("Name") or "").strip()
        sensor_type = str(row.get("SensorType") or "").strip().lower()
        try:
            value = float(row.get("Value"))
        except Exception:
            continue
        low_name = name.lower()
        if sensor_type == "temperature":
            if "cpu package" in low_name or ("cpu" in low_name and "core" not in low_name):
                temps["CPU"] = max(value, temps.get("CPU", 0))
            elif "gpu" in low_name:
                temps["GPU"] = max(value, temps.get("GPU", 0))
            elif "ssd" in low_name or "nvme" in low_name or "drive" in low_name:
                temps["SSD"] = max(value, temps.get("SSD", 0))
        elif sensor_type == "fan":
            fans.append(f"{name}: {value:.0f} RPM")

    parts = [f"{key}: {val:.0f}C" for key, val in temps.items()]
    if fans:
        parts.append("Fans: " + " / ".join(fans[:2]))
    return {"summary": " | ".join(parts) if parts else "Sensores encontrados, sem temperatura principal.", "temps": temps}


class SlowMetricsWorker(QThread):
    metrics_ready = pyqtSignal(object)

    def run(self):
        self.metrics_ready.emit({
            "clock": _query_cpu_clock_safe(),
            "standby": _query_standby_memory_safe(),
            "storage": _query_storage_health_safe(),
            "power": _query_power_plan_safe(),
            "admin": _query_admin_safe(),
            "network": _query_network_totals_safe(),
            "processes": _query_top_processes_safe(),
            "lhm": _query_lhm_sensors_safe(),
        })


class CommandWorker(QThread):
    command_done = pyqtSignal(object)

    def __init__(self, title, commands, timeout=30, parent=None):
        super().__init__(parent)
        self.title = title
        self.commands = commands
        self.timeout = timeout

    def run(self):
        results = []
        final_code = 0
        for args in self.commands:
            code, out, err = _run_command(args, timeout=self.timeout)
            final_code = code if code != 0 else final_code
            results.append({
                "cmd": " ".join(args),
                "code": code,
                "out": out,
                "err": err,
            })
        self.command_done.emit({"title": self.title, "code": final_code, "results": results})


def _query_primary_network_config_safe():
    command = (
        "$cfg=Get-NetIPConfiguration -ErrorAction SilentlyContinue | "
        "Where-Object {$_.IPv4DefaultGateway -and $_.NetAdapter.Status -eq 'Up'} | "
        "Select-Object -First 1;"
        "if($cfg){[pscustomobject]@{"
        "Adapter=$cfg.InterfaceAlias;"
        "IPv4=($cfg.IPv4Address.IPAddress -join ', ');"
        "Gateway=$cfg.IPv4DefaultGateway.NextHop;"
        "DNS=($cfg.DNSServer.ServerAddresses -join ', ')"
        "} | ConvertTo-Json -Compress}"
    )
    data, err = _powershell_json_data(command, timeout=8)
    return data if isinstance(data, dict) else {"error": err or "Nenhum adaptador ativo com gateway."}


class NetworkDiagnosisWorker(QThread):
    diagnosis_ready = pyqtSignal(object)

    def _ping(self, host):
        code, out, err = _run_command(["ping", "-n", "1", "-w", "1200", host], timeout=5)
        return {"host": host, "ok": code == 0, "out": out, "err": err}

    def run(self):
        config = _query_primary_network_config_safe()
        gateway = str(config.get("Gateway") or "").strip() if isinstance(config, dict) else ""

        steps = []
        if gateway:
            steps.append(("Roteador/Gateway", self._ping(gateway)))
        else:
            steps.append(("Roteador/Gateway", {"host": "-", "ok": False, "err": "Gateway nao encontrado."}))

        steps.append(("Internet direta", self._ping("1.1.1.1")))
        code, out, err = _run_command(["nslookup", "google.com"], timeout=6)
        steps.append(("DNS", {"host": "google.com", "ok": code == 0 and "Address" in out, "out": out, "err": err}))
        steps.append(("Site por nome", self._ping("google.com")))

        gateway_ok = steps[0][1]["ok"]
        ip_ok = steps[1][1]["ok"]
        dns_ok = steps[2][1]["ok"]
        domain_ok = steps[3][1]["ok"]

        if not gateway:
            verdict = "Sem gateway: o Windows nao achou rota padrao. Verifique Wi-Fi/cabo/roteador."
            level = "error"
        elif not gateway_ok:
            verdict = "O PC nao conseguiu falar com o roteador. Problema provavel: Wi-Fi, cabo, adaptador ou roteador travado."
            level = "error"
        elif not ip_ok:
            verdict = "O roteador responde, mas a internet externa falhou. Problema provavel: modem/provedor/roteador."
            level = "error"
        elif not dns_ok or not domain_ok:
            verdict = "Internet por IP funciona, mas nomes de sites falham. Problema provavel: DNS."
            level = "warn"
        else:
            verdict = "Rede parece saudavel. Se um site/app falhar, o problema pode ser proxy, site bloqueado ou cache do app."
            level = "ok"

        self.diagnosis_ready.emit({
            "config": config,
            "steps": steps,
            "verdict": verdict,
            "level": level,
        })


class MiniHistoryChart(QFrame):
    """Grafico leve para historico de CPU/GPU/RAM sem depender de libs externas."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.series = {
            "CPU": [],
            "GPU": [],
            "RAM": [],
        }
        self.colors = {
            "CPU": QColor("#22d3ee"),
            "GPU": QColor("#a78bfa"),
            "RAM": QColor("#34d399"),
        }
        self.setObjectName("historyChart")
        self.setMinimumHeight(130)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setStyleSheet(history_chart_qss())

    def set_series(self, series):
        self.series = series
        self.update()

    def paintEvent(self, event):
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        rect = self.rect().adjusted(16, 16, -16, -24)
        if rect.width() <= 10 or rect.height() <= 10:
            return

        painter.setPen(QPen(QColor("#0f1a2e"), 1))
        for ratio in (0.25, 0.5, 0.75):
            y = rect.bottom() - rect.height() * ratio
            painter.drawLine(rect.left(), int(y), rect.right(), int(y))

        painter.setPen(QPen(QColor("#334155"), 1))
        painter.drawText(rect.left(), self.rect().bottom() - 7, "Historico dos ultimos minutos")

        for name, values in self.series.items():
            if len(values) < 2:
                continue
            clean_values = [max(0, min(100, float(v))) for v in values[-90:]]
            step = rect.width() / max(len(clean_values) - 1, 1)
            path = QPainterPath()
            for i, val in enumerate(clean_values):
                x = rect.left() + i * step
                y = rect.bottom() - (val / 100.0) * rect.height()
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)
            painter.setPen(QPen(self.colors.get(name, QColor("#e5e7eb")), 1.5))
            painter.drawPath(path)

        x = rect.right() - 210
        for name in ("CPU", "GPU", "RAM"):
            painter.setPen(QPen(self.colors[name], 6))
            painter.drawPoint(x, self.rect().bottom() - 13)
            painter.setPen(QPen(QColor("#475569"), 1))
            painter.drawText(x + 10, self.rect().bottom() - 8, name)
            x += 70


class PerformanceWidget(QWidget):
    """Painel seguro de desempenho em tempo real."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._last_cpu_times = None
        self._last_slow_poll = time.time()
        self._standby_text = "N/D"
        self._storage_text = "Carregando..."
        self._cpu_clock = "N/D"
        self._power_plan = "N/D"
        self._admin_text = "N/D"
        self._top_processes = "Carregando..."
        self._last_network = None
        self._network_speed = "Download: N/D | Upload: N/D"
        self._slow_worker = None
        self._history = {"CPU": [], "GPU": [], "RAM": []}
        self._lhm_summary = "N/D"
        self._lhm_temps = {}
        self._last_power_plan_guid = None
        self._network_worker = None
        self._net_diag_worker = None
        self._build()
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh_metrics)
        self.timer.start(1500)
        self.refresh_metrics()

    def _build(self):
        self.setStyleSheet(performance_widget_qss())

        root = QVBoxLayout(self)
        root.setContentsMargins(18, 14, 18, 14)
        root.setSpacing(12)

        header = QFrame()
        header.setObjectName("perfHeader")
        header.setStyleSheet(perf_header_qss())
        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(4, 10, 4, 10)
        h_lay.setSpacing(10)

        icon_lbl = QLabel("⚡")
        icon_lbl.setStyleSheet(perf_label_qss("icon"))
        h_lay.addWidget(icon_lbl)

        title_box = QVBoxLayout()
        title_box.setSpacing(2)
        title = QLabel("Desempenho Pro")
        title.setStyleSheet(perf_label_qss("title"))
        subtitle = QLabel("Monitoramento limpo, auditoria segura e perfis reversiveis para jogo, IA e uso normal.")
        subtitle.setStyleSheet(perf_label_qss("subtitle"))
        title_box.addWidget(title)
        title_box.addWidget(subtitle)
        h_lay.addLayout(title_box, 1)

        self.status_badge = QLabel("Seguro")
        self.status_badge.setAlignment(Qt.AlignCenter)
        self.status_badge.setStyleSheet(status_badge_qss("safe"))
        h_lay.addWidget(self.status_badge)
        root.addWidget(header)

        self.tabs = QTabWidget()
        self.tabs.setObjectName("perfTabs")
        self.tabs.tabBar().setExpanding(True)
        self.tabs.tabBar().setMinimumHeight(54)
        root.addWidget(self.tabs, 1)

        dashboard = QWidget()
        d_lay = QVBoxLayout(dashboard)
        d_lay.setContentsMargins(0, 8, 0, 0)
        d_lay.setSpacing(12)

        self.alert_banner = QLabel("● Tudo tranquilo agora. Historico e sensores continuam sendo atualizados.")
        self.alert_banner.setWordWrap(True)
        self.alert_banner.setStyleSheet(
            "color:#34d399;"
            "background: rgba(16,185,129,0.07);"
            "border: 1px solid rgba(16,185,129,0.20);"
            "border-radius: 8px;"
            "padding: 8px 12px;"
            "font-size: 12px;"
            "font-weight: 500;"
        )
        d_lay.addWidget(self.alert_banner)

        overview = QGroupBox("VISAO GERAL")
        overview_lay = QVBoxLayout(overview)
        overview_lay.setContentsMargins(12, 8, 12, 12)
        grid = QGridLayout()
        grid.setSpacing(10)
        self.cpu_card = self._stat_card("CPU", "#22d3ee")
        self.gpu_card = self._stat_card("GPU", "#a78bfa")
        self.ram_card = self._stat_card("RAM", "#34d399")
        self.ssd_card = self._stat_card("SSD", "#fbbf24")
        self.net_card = self._stat_card("REDE", "#38bdf8")
        self.system_card = self._stat_card("SISTEMA", "#fb7185")
        grid.addWidget(self.cpu_card["frame"], 0, 0)
        grid.addWidget(self.gpu_card["frame"], 0, 1)
        grid.addWidget(self.ram_card["frame"], 0, 2)
        grid.addWidget(self.ssd_card["frame"], 1, 0)
        grid.addWidget(self.net_card["frame"], 1, 1)
        grid.addWidget(self.system_card["frame"], 1, 2)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(2, 1)
        overview_lay.addLayout(grid)
        d_lay.addWidget(overview)

        self.chart = MiniHistoryChart()
        d_lay.addWidget(self.chart)

        actions = QGroupBox("ACOES ORGANIZADAS")
        a_lay = QGridLayout(actions)
        a_lay.setSpacing(10)
        action_groups = [
            ("Diagnostico", [
                ("Diagnostico rapido", self.quick_diagnosis, "#22d3ee"),
                ("Atualizar sensores", self.force_slow_refresh, "#94a3b8"),
            ]),
            ("Relatorio", [
                ("Resumo do sistema", self.copy_summary, "#34d399"),
                ("Auditar pacotes", self.audit_package_tweaks, "#60a5fa"),
            ]),
            ("Protecao", [
                ("Limpeza segura TEMP", self.safe_temp_cleanup, "#fbbf24"),
                ("Criar ponto de restauracao", self.create_restore_point, "#a78bfa"),
            ]),
        ]
        for col, (group_title, group_buttons) in enumerate(action_groups):
            a_lay.addWidget(self._action_panel(group_title, group_buttons), 0, col)
            a_lay.setColumnStretch(col, 1)
        d_lay.addWidget(actions)

        processes = QGroupBox("PROCESSOS PESADOS")
        p_lay = QVBoxLayout(processes)
        self.process_box = QTextEdit()
        self.process_box.setReadOnly(True)
        self.process_box.setMaximumHeight(135)
        self.process_box.setPlaceholderText("A lista aparece aqui depois do primeiro diagnostico.")
        p_lay.addWidget(self.process_box)
        d_lay.addWidget(processes)

        notice = QLabel(
            "Modo seguro: os RARs foram usados como referencia, mas .bat/.reg/.exe nao sao executados. "
            "BCD, HPET e registro ficam em auditoria para evitar quebrar o Windows."
        )
        notice.setWordWrap(True)
        notice.setStyleSheet(
            "color:#fbbf24;"
            "background: rgba(245,158,11,0.06);"
            "border: 1px solid rgba(245,158,11,0.16);"
            "border-radius: 8px;"
            "padding: 8px 12px;"
            "font-size: 11px;"
            "font-weight: 400;"
        )
        d_lay.addWidget(notice)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setMinimumHeight(145)
        d_lay.addWidget(self.log_box)
        self.tabs.addTab(self._scroll(dashboard), "Painel")

        audit = QWidget()
        au_lay = QVBoxLayout(audit)
        au_lay.setContentsMargins(0, 8, 0, 0)
        au_lay.setSpacing(12)
        au_lay.addWidget(self._info_header(
            "Auditoria segura dos pacotes",
            "O app le os ajustes parecidos com os packs, mas separa o que e seguro do que pode dar dor de cabeca."
        ))
        audit_grid = QGridLayout()
        audit_grid.setSpacing(10)
        audit_cards = [
            ("Limpeza dos RARs", "Perigoso automatico", "Nao apagamos Prefetch, logs do Windows, cookies globais nem spooler. Isso pode causar bugs e perda de historico.", "#fb7185"),
            ("BCD / HPET", "Somente diagnostico", "Mexer no boot/timer pode piorar desempenho ou quebrar inicializacao. Aqui a ferramenta so mostra o estado.", "#fbbf24"),
            ("Game DVR", "Com backup", "Pode reduzir captura em segundo plano. Ideal e auditar primeiro e mudar so se voce souber que nao usa gravacao do Xbox.", "#fbbf24"),
            ("Prioridade de jogos", "Seguro com controle", "Prioridade alta ajuda apps em foco, mas nao deve ser aplicada em processo do sistema.", "#34d399"),
            ("Mouse e teclado", "Atencao", "Ajustes de input sao pessoais. O painel mostra os valores atuais antes de qualquer mudanca.", "#fbbf24"),
            ("Executaveis do pack", "Bloqueado", "Ferramentas externas dos RARs nao sao abertas automaticamente dentro do projeto.", "#fb7185"),
        ]
        for i, data in enumerate(audit_cards):
            audit_grid.addWidget(self._audit_card(*data), i // 3, i % 3)
        au_lay.addLayout(audit_grid)
        audit_actions = QHBoxLayout()
        audit_actions.addWidget(self._action_button("Auditar agora", self.audit_package_tweaks, "#22d3ee"))
        audit_actions.addWidget(self._action_button("Diagnosticar BCD/HPET", self.diagnose_timer, "#a78bfa"))
        audit_actions.addWidget(self._action_button("Copiar resumo", self.copy_summary, "#34d399"))
        au_lay.addLayout(audit_actions)
        self.audit_result_box = QTextEdit()
        self.audit_result_box.setReadOnly(True)
        self.audit_result_box.setMinimumHeight(260)
        self.audit_result_box.setPlaceholderText("Clique em Auditar agora para ver o estado atual do Windows.")
        au_lay.addWidget(self.audit_result_box)
        self.tabs.addTab(self._scroll(audit), "Auditoria")

        profiles = QWidget()
        pr_lay = QVBoxLayout(profiles)
        pr_lay.setContentsMargins(0, 8, 0, 0)
        pr_lay.setSpacing(12)
        pr_lay.addWidget(self._info_header(
            "Perfis reversiveis",
            "Escolha um modo de uso. O app evita tweaks permanentes e registra o que fez para voce voltar ao normal."
        ))
        profile_box = QGroupBox("MODO DE USO")
        profile_lay = QGridLayout(profile_box)
        profile_lay.setSpacing(10)
        self.profile_combo = QComboBox()
        self.profile_combo.addItems(["Normal", "Jogo", "IA pesada"])
        self.profile_combo.currentTextChanged.connect(self._update_profile_hint)
        self.profile_hint_label = QLabel()
        self.profile_hint_label.setWordWrap(True)
        self.profile_hint_label.setStyleSheet(perf_label_qss("muted"))
        profile_lay.addWidget(QLabel("Perfil:"), 0, 0)
        profile_lay.addWidget(self.profile_combo, 0, 1)
        profile_lay.addWidget(self._action_button("Aplicar perfil", self.apply_performance_profile, "#22d3ee"), 0, 2)
        profile_lay.addWidget(self._action_button("Voltar ao normal", self.restore_normal_profile, "#94a3b8"), 0, 3)
        profile_lay.addWidget(self.profile_hint_label, 1, 0, 1, 4)
        profile_lay.addWidget(self._action_button("Prioridade alta no app em foco", lambda: self.set_foreground_priority(high=True), "#fbbf24"), 2, 0, 1, 2)
        profile_lay.addWidget(self._action_button("Prioridade normal no app em foco", lambda: self.set_foreground_priority(high=False), "#94a3b8"), 2, 2, 1, 2)
        self._update_profile_hint(self.profile_combo.currentText())
        pr_lay.addWidget(profile_box)

        optim_box = QGroupBox("OTIMIZACOES SEGURAS COM EXPLICACAO")
        optim_grid = QGridLayout(optim_box)
        optim_grid.setSpacing(12)
        optim_grid.addWidget(self._optimization_card(
            "Desempenho maximo",
            "Seguro, reversivel",
            "Ativa o plano Ultimate Performance do Windows. Bom para jogo, IA local e render. Gasta mais energia.",
            "Ativar agora",
            self.enable_ultimate_performance,
            "#22d3ee",
        ), 0, 0)
        optim_grid.addWidget(self._optimization_card(
            "Modo normal",
            "Recomendado no dia a dia",
            "Volta para o plano Equilibrado. Mantem o PC mais frio e evita consumo alto quando nao precisa.",
            "Voltar ao normal",
            self.enable_balanced_power,
            "#34d399",
        ), 0, 1)
        optim_grid.addWidget(self._optimization_card(
            "Prioridade do app em foco",
            "Use so no jogo/app aberto",
            "Da mais prioridade de CPU ao aplicativo que estiver em primeiro plano. Nao mexe em processos do sistema.",
            "Aplicar alta",
            lambda: self.set_foreground_priority(high=True),
            "#fbbf24",
        ), 1, 0)
        optim_grid.addWidget(self._optimization_card(
            "Memoria do Telegram Pro",
            "Limpeza leve",
            "Pede ao Windows para reduzir memoria usada pelo proprio projeto. Nao fecha programas e nao limpa RAM global.",
            "Liberar do app",
            self.trim_app_memory,
            "#a78bfa",
        ), 1, 1)
        optim_grid.setColumnStretch(0, 1)
        optim_grid.setColumnStretch(1, 1)
        pr_lay.addWidget(optim_box)

        lhm_box = QGroupBox("TEMPERATURA REAL COM LIBREHARDWAREMONITOR")
        lhm_lay = QVBoxLayout(lhm_box)
        self.lhm_status_label = QLabel(
            "Opcional: coloque LibreHardwareMonitor portatil em tools\\LibreHardwareMonitor e abra ele com WMI ativo para CPU, placa-mae, SSD e fans aparecerem aqui."
        )
        self.lhm_status_label.setWordWrap(True)
        self.lhm_status_label.setStyleSheet("color:#cbd5e1;")
        lhm_lay.addWidget(self.lhm_status_label)
        lhm_actions = QHBoxLayout()
        lhm_actions.addWidget(self._action_button("Detectar sensores", self.detect_lhm, "#22d3ee"))
        lhm_actions.addWidget(self._action_button("Abrir pasta esperada", self.open_lhm_folder, "#94a3b8"))
        lhm_lay.addLayout(lhm_actions)
        pr_lay.addWidget(lhm_box)
        pr_lay.addStretch(1)
        self.tabs.addTab(self._scroll(profiles), "Perfis")

        network = QWidget()
        n_lay = QVBoxLayout(network)
        n_lay.setContentsMargins(0, 8, 0, 0)
        n_lay.setSpacing(12)
        n_lay.addWidget(self._info_header(
            "Rede, DNS e IP",
            "Ferramentas seguras para resolver internet lenta, DNS travado e DHCP. Renovar IP pode desconectar por alguns segundos."
        ))
        self.net_status_label = QLabel(
            "Dica: limpar DNS e ver IP sao leves. Renovar IP DHCP pode ou nao mudar seu IP publico, isso depende do roteador/provedor."
        )
        self.net_status_label.setWordWrap(True)
        self.net_status_label.setStyleSheet(self._banner_style("#bae6fd", "rgba(14,116,144,0.12)"))
        n_lay.addWidget(self.net_status_label)

        smart_box = QGroupBox("DIAGNOSTICO INTELIGENTE")
        smart_lay = QGridLayout(smart_box)
        smart_lay.setSpacing(12)
        self.net_health_card = self._diagnosis_card(
            "Saude da rede",
            "Aguardando teste",
            "Clique em Diagnosticar para descobrir se o problema e Wi-Fi, roteador, internet do provedor ou DNS.",
            "#22d3ee",
        )
        smart_lay.addWidget(self.net_health_card["frame"], 0, 0)
        self.net_fix_card = self._diagnosis_card(
            "Reparo guiado",
            "Nao executado",
            "Roda uma sequencia util: limpar DNS, registrar DNS e renovar IP DHCP. Pede confirmacao antes.",
            "#34d399",
        )
        smart_lay.addWidget(self.net_fix_card["frame"], 0, 1)
        smart_actions = QHBoxLayout()
        smart_actions.addWidget(self._action_button("Diagnosticar internet", self.diagnose_network, "#22d3ee"))
        smart_actions.addWidget(self._action_button("Reparar internet", self.repair_internet_flow, "#34d399"))
        smart_actions.addWidget(self._action_button("Copiar diagnostico", self.copy_network_report, "#a78bfa"))
        smart_lay.addLayout(smart_actions, 1, 0, 1, 2)
        smart_lay.setColumnStretch(0, 1)
        smart_lay.setColumnStretch(1, 1)
        n_lay.addWidget(smart_box)

        network_grid = QGridLayout()
        network_grid.setSpacing(12)
        network_grid.addWidget(self._network_action_card(
            "Limpar DNS",
            "Seguro",
            "Limpa o cache de nomes do Windows. Ajuda quando site abre errado, fica preso em IP antigo ou DNS falha.",
            "Limpar DNS",
            self.flush_dns_cache,
            "#22d3ee",
        ), 0, 0)
        network_grid.addWidget(self._network_action_card(
            "Renovar IP DHCP",
            "Pode cair por segundos",
            "Libera e pede um IP novo ao roteador. Nao garante trocar IP publico, mas ajuda quando Wi-Fi/rede fica preso.",
            "Renovar IP",
            self.renew_dhcp_ip,
            "#fbbf24",
        ), 0, 1)
        network_grid.addWidget(self._network_action_card(
            "Registrar DNS",
            "Leve",
            "Forca o Windows a registrar novamente nomes e IPs configurados. Bom para falha de resolucao em rede local.",
            "Registrar DNS",
            self.register_dns,
            "#34d399",
        ), 1, 0)
        network_grid.addWidget(self._network_action_card(
            "Reset Winsock",
            "Avancado",
            "Repara catalogo de rede do Windows quando navegadores/apps nao conectam. Normalmente pede reiniciar o PC.",
            "Resetar Winsock",
            self.reset_winsock,
            "#fb7185",
        ), 1, 1)
        network_grid.addWidget(self._network_action_card(
            "Diagnostico IP",
            "Somente leitura",
            "Mostra IP, gateway e adaptadores atuais sem alterar nada.",
            "Ver IP",
            self.show_network_config,
            "#60a5fa",
        ), 2, 0)
        network_grid.addWidget(self._network_action_card(
            "Adaptadores do Windows",
            "Atalho",
            "Abre a tela classica de conexoes de rede para ativar, desativar ou conferir Wi-Fi/Ethernet manualmente.",
            "Abrir conexoes",
            self.open_network_adapters,
            "#a78bfa",
        ), 2, 1)
        network_grid.setColumnStretch(0, 1)
        network_grid.setColumnStretch(1, 1)
        n_lay.addLayout(network_grid)

        self.network_box = QTextEdit()
        self.network_box.setReadOnly(True)
        self.network_box.setMinimumHeight(220)
        self.network_box.setPlaceholderText("Clique em Ver IP, Limpar DNS ou outra acao para ver o resultado aqui.")
        n_lay.addWidget(self.network_box)
        self.tabs.addTab(self._scroll(network), "Rede")

        guide = QWidget()
        g_lay = QVBoxLayout(guide)
        g_lay.setContentsMargins(0, 8, 0, 0)
        g_lay.setSpacing(10)
        g_lay.addWidget(self._info_header(
            "Guia simples",
            "Uma explicacao direta do que cada botao faz, para qualquer pessoa usar sem medo."
        ))
        guide_items = [
            ("Diagnostico rapido", "Olha CPU, RAM, plano de energia e avisos basicos. Ele nao altera nada."),
            ("Atualizar sensores", "Busca dados mais lentos: plano de energia, SSD, memoria standby, rede e processos pesados."),
            ("Resumo do sistema", "Copia para a area de transferencia um texto com CPU, GPU, RAM, SSD, rede e processos."),
            ("Liberar memoria do app", "Pede ao Windows para reduzir a memoria usada pelo proprio Telegram Pro. Nao fecha programas."),
            ("Limpeza segura TEMP", "Remove apenas arquivos antigos da pasta temporaria do seu usuario. Nao mexe em arquivos do Windows."),
            ("Criar ponto de restauracao", "Tenta criar uma protecao antes de ajustes. Precisa abrir como administrador e ter Protecao do Sistema ativa."),
            ("Auditoria dos pacotes", "Le os valores atuais parecidos com os packs, mas nao executa scripts, registros ou programas externos."),
            ("Perfis Normal/Jogo/IA", "Troca plano de energia de forma controlada. Jogo e IA usam desempenho maximo; Normal volta ao equilibrado."),
            ("LibreHardwareMonitor", "Programa portatil opcional para temperatura real de CPU, placa-mae, SSD e fans. O projeto ja esta pronto para ler esses sensores."),
            ("Diagnosticar internet", "Testa roteador, internet externa, DNS e site por nome. No fim ele fala a causa provavel do problema."),
            ("Reparar internet", "Roda uma sequencia guiada para DNS e IP. Pode derrubar a rede por segundos, por isso sempre pede confirmacao."),
            ("Limpar DNS", "Apaga o cache de DNS do Windows. Ajuda quando sites ficam presos em endereco antigo ou falham do nada."),
            ("Renovar IP DHCP", "Pede um IP novo ao roteador. Pode derrubar a rede por alguns segundos e nao garante mudar IP publico."),
            ("Reset Winsock", "Repara a base de rede do Windows quando apps nao conectam. E avancado e normalmente precisa reiniciar o PC."),
        ]
        for title_text, body_text in guide_items:
            g_lay.addWidget(self._guide_card(title_text, body_text))
        g_lay.addStretch(1)
        self.tabs.addTab(self._scroll(guide), "Guia simples")

    def _stat_card(self, title, color):
        frame = QFrame()
        frame.setObjectName("statCard")
        frame.setMinimumHeight(88)
        frame.setStyleSheet(stat_card_qss(color))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(13, 10, 13, 10)
        lay.setSpacing(3)
        title_label = QLabel(title)
        title_label.setStyleSheet(perf_label_qss("metric_title", color))
        value = QLabel("N/D")
        value.setStyleSheet(perf_label_qss("metric_value"))
        detail = QLabel("Aguardando...")
        detail.setWordWrap(True)
        detail.setStyleSheet(perf_label_qss("muted"))
        lay.addWidget(title_label)
        lay.addWidget(value)
        lay.addWidget(detail)
        return {"frame": frame, "value": value, "detail": detail, "color": color}

    def _apply_card_style(self, card, alert=False, warn=False):
        card["frame"].setStyleSheet(stat_card_qss(card.get("color", "#22d3ee"), alert, warn))

    def _scroll(self, widget):
        area = QScrollArea()
        area.setWidgetResizable(True)
        area.setWidget(widget)
        return area

    def _action_button(self, text, fn, color):
        btn = QPushButton(text)
        btn.setMinimumHeight(46)
        btn.setStyleSheet(action_button_qss(color))
        btn.clicked.connect(fn)
        return btn

    def _action_panel(self, title, buttons):
        frame = QFrame()
        frame.setObjectName("actionPanel")
        frame.setStyleSheet(panel_qss("actionPanel"))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 12, 14, 14)
        lay.setSpacing(9)
        label = QLabel(title.upper())
        label.setStyleSheet(perf_label_qss("section"))
        lay.addWidget(label)
        for text, fn, color in buttons:
            lay.addWidget(self._action_button(text, fn, color))
        lay.addStretch(1)
        return frame

    def _optimization_card(self, title, badge, body, button_text, fn, color):
        frame = QFrame()
        frame.setObjectName("optimizationCard")
        frame.setMinimumHeight(164)
        frame.setStyleSheet(accent_card_qss("optimizationCard", color))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 13, 16, 14)
        lay.setSpacing(9)
        top = QHBoxLayout()
        top.setSpacing(8)
        title_label = QLabel(title)
        title_label.setStyleSheet(perf_label_qss("card_title"))
        badge_label = QLabel(badge)
        badge_label.setStyleSheet(pill_qss(color))
        top.addWidget(title_label, 1)
        top.addWidget(badge_label)
        lay.addLayout(top)
        body_label = QLabel(body)
        body_label.setWordWrap(True)
        body_label.setStyleSheet(perf_label_qss("muted"))
        lay.addWidget(body_label, 1)
        lay.addWidget(self._action_button(button_text, fn, color))
        return frame

    def _network_action_card(self, title, badge, body, button_text, fn, color):
        frame = self._optimization_card(title, badge, body, button_text, fn, color)
        frame.setMinimumHeight(186)
        return frame

    def _update_profile_hint(self, profile_name):
        if not hasattr(self, "profile_hint_label"):
            return
        hints = {
            "Normal": "Uso diario: volta ao plano Equilibrado e evita consumo alto quando voce nao esta jogando, renderizando ou usando IA pesada.",
            "Jogo": "Foco em FPS/latencia: usa energia maxima e deixa o app pronto para aplicar prioridade alta apenas no jogo aberto.",
            "IA pesada": "Foco em Ollama/Stable Diffusion/render: usa energia maxima e recomenda acompanhar temperatura, VRAM e RAM no painel.",
        }
        self.profile_hint_label.setText(hints.get(profile_name, "Escolha um perfil e aplique quando quiser mudar o modo de uso do PC."))

    def _diagnosis_card(self, title, status, body, color):
        frame = QFrame()
        frame.setObjectName("diagnosisCard")
        frame.setMinimumHeight(120)
        frame.setStyleSheet(accent_card_qss("diagnosisCard", color))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 11, 14, 11)
        lay.setSpacing(6)
        title_label = QLabel(title)
        title_label.setStyleSheet(perf_label_qss("card_title"))
        status_label = QLabel(status)
        status_label.setStyleSheet(pill_qss(color))
        body_label = QLabel(body)
        body_label.setWordWrap(True)
        body_label.setStyleSheet(perf_label_qss("muted"))
        lay.addWidget(title_label)
        lay.addWidget(status_label)
        lay.addWidget(body_label, 1)
        return {"frame": frame, "status": status_label, "body": body_label, "color": color}

    def _set_diagnosis_card(self, card, status, body, color):
        card["status"].setText(status)
        card["status"].setStyleSheet(pill_qss(color))
        card["body"].setText(body)
        card["frame"].setStyleSheet(accent_card_qss("diagnosisCard", color))

    def _banner_style(self, color, bg):
        return banner_qss(color, bg)

    def _info_header(self, title, body):
        frame = QFrame()
        frame.setObjectName("infoHeader")
        frame.setStyleSheet(panel_qss("infoHeader", transparent=True, line="rgba(6,182,212,0.08)"))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(0, 0, 0, 10)
        lay.setSpacing(3)
        title_label = QLabel(title)
        title_label.setStyleSheet(perf_label_qss("info_title"))
        body_label = QLabel(body)
        body_label.setWordWrap(True)
        body_label.setStyleSheet(perf_label_qss("muted"))
        lay.addWidget(title_label)
        lay.addWidget(body_label)
        return frame

    def _audit_card(self, title, status, body, color):
        frame = QFrame()
        frame.setObjectName("auditCard")
        frame.setMinimumHeight(130)
        frame.setStyleSheet(accent_card_qss("auditCard", color))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 11, 14, 11)
        lay.setSpacing(6)
        title_label = QLabel(title)
        title_label.setStyleSheet(perf_label_qss("card_title"))
        status_label = QLabel(status)
        status_label.setStyleSheet(pill_qss(color))
        body_label = QLabel(body)
        body_label.setWordWrap(True)
        body_label.setStyleSheet(perf_label_qss("muted"))
        lay.addWidget(title_label)
        lay.addWidget(status_label)
        lay.addWidget(body_label)
        return frame

    def _guide_card(self, title, body):
        frame = QFrame()
        frame.setObjectName("guideCard")
        frame.setStyleSheet(panel_qss("guideCard", transparent=True))
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(4, 8, 4, 8)
        lay.setSpacing(2)
        title_label = QLabel(title)
        title_label.setStyleSheet(perf_label_qss("guide_title"))
        body_label = QLabel(body)
        body_label.setWordWrap(True)
        body_label.setStyleSheet(perf_label_qss("muted"))
        lay.addWidget(title_label)
        lay.addWidget(body_label)
        return frame

    def _log(self, text):
        stamp = time.strftime("%H:%M:%S")
        self.log_box.append(f"[{stamp}] {text}")

    def _run(self, args, timeout=8):
        return _run_command(args, timeout=timeout)

    def _network_log(self, text):
        self._log(text)
        if hasattr(self, "network_box"):
            stamp = time.strftime("%H:%M:%S")
            self.network_box.append(f"[{stamp}] {text}")

    def _run_network_commands(self, title, commands, timeout=30):
        if self._network_worker and self._network_worker.isRunning():
            self._network_log("Aguarde: outra acao de rede ainda esta rodando.")
            return
        self._network_log(f"Iniciando: {title}")
        self._network_worker = CommandWorker(title, commands, timeout, self)
        self._network_worker.command_done.connect(self._network_command_done)
        self._network_worker.start()

    def _network_command_done(self, data):
        title = data.get("title", "Acao de rede")
        ok = data.get("code") == 0
        lines = [f"{title}: {'concluido' if ok else 'finalizado com aviso'}", ""]
        for item in data.get("results", []):
            lines.append(f"> {item.get('cmd')}")
            if item.get("out"):
                lines.append(item["out"])
            if item.get("err"):
                lines.append("ERRO/AVISO: " + item["err"])
            lines.append("")
        text = "\n".join(lines).strip()
        if hasattr(self, "network_box"):
            self.network_box.setText(text)
        self._network_log(lines[0])
        if hasattr(self, "net_status_label"):
            color = "#bbf7d0" if ok else "#fde68a"
            bg = "rgba(20,83,45,0.16)" if ok else "rgba(120,53,15,0.20)"
            self.net_status_label.setText(lines[0])
            self.net_status_label.setStyleSheet(self._banner_style(color, bg))
        if "Reparo guiado" in title and hasattr(self, "net_fix_card"):
            self._set_diagnosis_card(
                self.net_fix_card,
                "Reparo concluido" if ok else "Reparo com aviso",
                "Agora rode Diagnosticar internet para confirmar se gateway, DNS e site por nome responderam.",
                "#34d399" if ok else "#fbbf24",
            )

    def diagnose_network(self):
        if self._net_diag_worker and self._net_diag_worker.isRunning():
            self._network_log("Diagnostico de rede ja esta rodando.")
            return
        if hasattr(self, "network_box"):
            self.network_box.setText("Diagnosticando internet...\n\nTestando gateway, IP externo, DNS e site por nome.")
        self._set_diagnosis_card(
            self.net_health_card,
            "Testando...",
            "O app esta verificando roteador, internet externa e DNS.",
            "#fbbf24",
        )
        self._net_diag_worker = NetworkDiagnosisWorker(self)
        self._net_diag_worker.diagnosis_ready.connect(self._network_diagnosis_ready)
        self._net_diag_worker.start()

    def _network_diagnosis_ready(self, data):
        level = data.get("level", "warn")
        color = "#34d399" if level == "ok" else "#fbbf24" if level == "warn" else "#fb7185"
        status = "Saudavel" if level == "ok" else "Atencao" if level == "warn" else "Problema encontrado"
        verdict = data.get("verdict", "Diagnostico finalizado.")
        self._set_diagnosis_card(self.net_health_card, status, verdict, color)
        if hasattr(self, "net_status_label"):
            self.net_status_label.setText(verdict)
            self.net_status_label.setStyleSheet(self._banner_style("#bbf7d0" if level == "ok" else "#fde68a" if level == "warn" else "#fecaca", "rgba(20,83,45,0.16)" if level == "ok" else "rgba(120,53,15,0.20)" if level == "warn" else "rgba(127,29,29,0.26)"))

        lines = ["DIAGNOSTICO INTELIGENTE DA REDE", "", verdict, ""]
        config = data.get("config") or {}
        if isinstance(config, dict):
            lines.extend([
                "Adaptador:",
                f"- Nome: {config.get('Adapter') or 'N/D'}",
                f"- IPv4: {config.get('IPv4') or 'N/D'}",
                f"- Gateway: {config.get('Gateway') or 'N/D'}",
                f"- DNS: {config.get('DNS') or 'N/D'}",
                "",
            ])
        lines.append("Etapas:")
        for name, result in data.get("steps", []):
            mark = "OK" if result.get("ok") else "FALHOU"
            host = result.get("host") or ""
            lines.append(f"- {name}: {mark} ({host})")
        lines.extend(["", "Sugestao:"])
        if level == "ok":
            lines.append("- A rede parece boa. Se um app especifico falhar, limpe cache do app, proxy ou perfil.")
        elif "DNS" in verdict:
            lines.append("- Use Limpar DNS ou Reparar Internet. Se continuar, troque DNS no roteador/Windows.")
        elif "roteador" in verdict.lower():
            lines.append("- Reinicie roteador/modem e confira Wi-Fi/cabo.")
        else:
            lines.append("- Use Reparar Internet. Se continuar, o problema pode estar no provedor ou modem.")

        if hasattr(self, "network_box"):
            self.network_box.setText("\n".join(lines))
        self._network_log("Diagnostico de rede finalizado: " + status)

    def repair_internet_flow(self):
        if QMessageBox.question(
            self,
            "Reparar Internet",
            "Rodar reparo guiado agora?\n\nEtapas: limpar DNS, registrar DNS, liberar IP e renovar IP.\nA rede pode cair por alguns segundos durante a renovacao.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self._set_diagnosis_card(
            self.net_fix_card,
            "Rodando reparo",
            "Limpando DNS e renovando IP. A conexao pode piscar por alguns segundos.",
            "#fbbf24",
        )
        self._run_network_commands(
            "Reparo guiado de internet",
            [["ipconfig", "/flushdns"], ["ipconfig", "/registerdns"], ["ipconfig", "/release"], ["ipconfig", "/renew"], ["ipconfig"]],
            timeout=50,
        )

    def copy_network_report(self):
        if not hasattr(self, "network_box") or not self.network_box.toPlainText().strip():
            self._network_log("Nada de rede para copiar ainda. Rode o diagnostico primeiro.")
            return
        QApplication.clipboard().setText(self.network_box.toPlainText())
        self._network_log("Diagnostico de rede copiado.")

    def flush_dns_cache(self):
        self._run_network_commands("Cache DNS limpo", [["ipconfig", "/flushdns"]], timeout=15)

    def register_dns(self):
        self._run_network_commands("Registro DNS solicitado", [["ipconfig", "/registerdns"]], timeout=20)

    def renew_dhcp_ip(self):
        if QMessageBox.question(
            self,
            "Renovar IP DHCP",
            "Isso pode derrubar sua conexao por alguns segundos.\n\nTambem nao garante trocar o IP publico; depende do roteador/provedor.\n\nContinuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self._run_network_commands(
            "Renovacao de IP DHCP",
            [["ipconfig", "/release"], ["ipconfig", "/renew"], ["ipconfig"]],
            timeout=45,
        )

    def reset_winsock(self):
        if QMessageBox.question(
            self,
            "Reset Winsock",
            "Essa acao repara a base de rede do Windows e normalmente precisa reiniciar o PC depois.\n\nUse apenas se navegadores ou apps nao conectam mesmo com internet funcionando.\n\nContinuar?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        self._run_network_commands("Reset Winsock", [["netsh", "winsock", "reset"]], timeout=30)

    def show_network_config(self):
        self._run_network_commands("Diagnostico IP", [["ipconfig"]], timeout=15)

    def open_network_adapters(self):
        try:
            if os.name == "nt":
                os.startfile("ncpa.cpl")
                self._network_log("Tela de conexoes de rede aberta.")
            else:
                self._network_log("Atalho de adaptadores disponivel apenas no Windows.")
        except Exception as exc:
            self._network_log(f"Nao consegui abrir conexoes de rede: {exc}")

    def refresh_metrics(self):
        cpu = self._cpu_percent()
        mem = self._memory_status()
        gpu = self._gpu_status()
        disk_c = shutil.disk_usage("C:\\") if os.name == "nt" else shutil.disk_usage("/")

        now = time.time()
        if now - self._last_slow_poll > 15 and (
            self._slow_worker is None or not self._slow_worker.isRunning()
        ):
            self._last_slow_poll = now
            self._slow_worker = SlowMetricsWorker(self)
            self._slow_worker.metrics_ready.connect(self._slow_metrics_ready)
            self._slow_worker.start()

        self.cpu_card["value"].setText(f"{cpu:.0f}%" if cpu is not None else "Calculando")
        cpu_temp = self._lhm_temps.get("CPU")
        cpu_temp_text = f"{cpu_temp:.0f}C" if cpu_temp is not None else "N/D"
        self.cpu_card["detail"].setText(f"Clock: {self._cpu_clock} | Temp: {cpu_temp_text}")

        gpu_percent = None
        gpu_temp = self._lhm_temps.get("GPU")
        if gpu:
            try:
                gpu_percent = float(gpu["util"])
            except Exception:
                gpu_percent = None
            try:
                gpu_temp = float(gpu.get("temp") or gpu_temp)
            except Exception:
                pass
            self.gpu_card["value"].setText(f"{gpu['util']}%")
            self.gpu_card["detail"].setText(
                f"VRAM: {gpu['mem_used']} / {gpu['mem_total']} MB | Temp: {gpu['temp']}C | Fan: {gpu['fan']}"
            )
        else:
            self.gpu_card["value"].setText("N/D")
            temp_hint = f" | LHM: {gpu_temp:.0f}C" if gpu_temp is not None else ""
            self.gpu_card["detail"].setText("NVIDIA SMI nao encontrado ou GPU indisponivel." + temp_hint)

        used_ram = mem["total"] - mem["avail"]
        self.ram_card["value"].setText(f"{mem['load']}%")
        self.ram_card["detail"].setText(
            f"Uso: {_gb(used_ram)} / {_gb(mem['total'])} | Livre: {_gb(mem['avail'])} | Standby: {self._standby_text}"
        )

        disk_percent = (disk_c.used / disk_c.total * 100) if disk_c.total else 0
        self.ssd_card["value"].setText(f"{disk_percent:.0f}% C:")
        self.ssd_card["detail"].setText(
            f"Livre: {_gb(disk_c.free)} | SMART: {self._storage_text}"
        )

        self.net_card["value"].setText(self._network_speed.split("|")[0].replace("Download:", "").strip())
        self.net_card["detail"].setText(self._network_speed)

        self.system_card["value"].setText(self._admin_text)
        self.system_card["detail"].setText(f"Plano de energia: {self._power_plan}")

        self._append_history(cpu, gpu_percent, mem["load"])
        self._update_alerts(cpu, gpu_temp, mem["load"], self._extract_max_temp(self._storage_text), cpu_temp)

    def _slow_metrics_ready(self, data):
        self._cpu_clock = data.get("clock") or "N/D"
        self._standby_text = data.get("standby") or "N/D"
        self._storage_text = data.get("storage") or "N/D"
        self._power_plan = data.get("power") or "N/D"
        self._admin_text = data.get("admin") or "N/D"
        self._top_processes = data.get("processes") or "N/D"
        self.process_box.setText(self._top_processes)
        self._update_network_speed(data.get("network"))
        lhm = data.get("lhm") or {}
        self._lhm_summary = lhm.get("summary") or "N/D"
        self._lhm_temps = lhm.get("temps") or {}
        if hasattr(self, "lhm_status_label"):
            self.lhm_status_label.setText(
                "LibreHardwareMonitor: " + self._lhm_summary
                if self._lhm_summary != "N/D"
                else "LibreHardwareMonitor nao detectado. Coloque a versao portatil em tools\\LibreHardwareMonitor e execute com WMI ativo."
            )

    def _append_history(self, cpu, gpu, ram):
        values = {"CPU": cpu, "GPU": gpu, "RAM": ram}
        for key, value in values.items():
            if value is None:
                continue
            self._history[key].append(float(value))
            if len(self._history[key]) > 120:
                self._history[key] = self._history[key][-120:]
        if hasattr(self, "chart"):
            self.chart.set_series(self._history)

    def _extract_max_temp(self, text):
        temps = []
        for match in re.finditer(r"(\d+(?:\.\d+)?)\s*C", text or "", re.I):
            try:
                temps.append(float(match.group(1)))
            except Exception:
                pass
        return max(temps) if temps else self._lhm_temps.get("SSD")

    def _update_alerts(self, cpu_load, gpu_temp, ram_load, ssd_temp, cpu_temp):
        alerts = []
        warns = []
        self._apply_card_style(self.cpu_card)
        self._apply_card_style(self.gpu_card)
        self._apply_card_style(self.ram_card)
        self._apply_card_style(self.ssd_card)

        if cpu_temp is not None and cpu_temp >= 90:
            alerts.append(f"CPU muito quente ({cpu_temp:.0f}C)")
            self._apply_card_style(self.cpu_card, alert=True)
        elif cpu_load is not None and cpu_load >= 95:
            warns.append(f"CPU no limite ({cpu_load:.0f}%)")
            self._apply_card_style(self.cpu_card, warn=True)

        if gpu_temp is not None and gpu_temp >= 84:
            alerts.append(f"GPU muito quente ({gpu_temp:.0f}C)")
            self._apply_card_style(self.gpu_card, alert=True)
        elif gpu_temp is not None and gpu_temp >= 78:
            warns.append(f"GPU aquecendo ({gpu_temp:.0f}C)")
            self._apply_card_style(self.gpu_card, warn=True)

        if ram_load >= 92:
            warns.append(f"RAM muito cheia ({ram_load:.0f}%)")
            self._apply_card_style(self.ram_card, warn=True)

        if ssd_temp is not None and ssd_temp >= 70:
            alerts.append(f"SSD/NVMe muito quente ({ssd_temp:.0f}C)")
            self._apply_card_style(self.ssd_card, alert=True)
        elif ssd_temp is not None and ssd_temp >= 60:
            warns.append(f"SSD/NVMe aquecendo ({ssd_temp:.0f}C)")
            self._apply_card_style(self.ssd_card, warn=True)

        if alerts:
            text = "Alerta: " + " | ".join(alerts) + ". Reduza carga, confira fans e ventilacao."
            style = self._banner_style("#fecaca", "rgba(127,29,29,0.26)")
            self.status_badge.setText("Alerta")
            self.status_badge.setStyleSheet(status_badge_qss("alert"))
        elif warns:
            text = "Atencao: " + " | ".join(warns) + ". Ainda esta usavel, mas vale observar."
            style = self._banner_style("#fde68a", "rgba(120,53,15,0.20)")
            self.status_badge.setText("Atencao")
            self.status_badge.setStyleSheet(status_badge_qss("warn"))
        else:
            text = "Tudo tranquilo agora. Historico e sensores continuam sendo atualizados."
            style = self._banner_style("#bbf7d0", "rgba(20,83,45,0.16)")
            self.status_badge.setText("Seguro")
            self.status_badge.setStyleSheet(status_badge_qss("safe"))
        self.alert_banner.setText(text)
        self.alert_banner.setStyleSheet(style)

    def _update_network_speed(self, totals):
        if not totals:
            return
        now = time.time()
        rx, tx = totals
        if self._last_network:
            last_time, last_rx, last_tx = self._last_network
            elapsed = max(now - last_time, 0.1)
            down = max(rx - last_rx, 0) / elapsed
            up = max(tx - last_tx, 0) / elapsed
            self._network_speed = f"Download: {self._format_rate(down)} | Upload: {self._format_rate(up)}"
        self._last_network = (now, rx, tx)

    def _format_rate(self, value):
        if value >= 1024 * 1024:
            return f"{value / (1024 * 1024):.1f} MB/s"
        if value >= 1024:
            return f"{value / 1024:.0f} KB/s"
        return f"{value:.0f} B/s"

    def _cpu_percent(self):
        idle = FILETIME()
        kernel = FILETIME()
        user = FILETIME()
        if not ctypes.windll.kernel32.GetSystemTimes(ctypes.byref(idle), ctypes.byref(kernel), ctypes.byref(user)):
            return None
        current = (_filetime_to_int(idle), _filetime_to_int(kernel), _filetime_to_int(user))
        if self._last_cpu_times is None:
            self._last_cpu_times = current
            return None
        old_idle, old_kernel, old_user = self._last_cpu_times
        self._last_cpu_times = current
        idle_delta = current[0] - old_idle
        kernel_delta = current[1] - old_kernel
        user_delta = current[2] - old_user
        total = kernel_delta + user_delta
        if total <= 0:
            return 0
        busy = total - idle_delta
        return max(0.0, min(100.0, busy * 100.0 / total))

    def _memory_status(self):
        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        return {"load": stat.dwMemoryLoad, "total": stat.ullTotalPhys, "avail": stat.ullAvailPhys}

    def _gpu_status(self):
        args = [
            "nvidia-smi",
            "--query-gpu=utilization.gpu,memory.used,memory.total,temperature.gpu,fan.speed",
            "--format=csv,noheader,nounits",
        ]
        code, out, _ = self._run(args, timeout=4)
        if code != 0 or not out:
            return None
        line = out.splitlines()[0]
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 5:
            return None
        return {
            "util": parts[0],
            "mem_used": parts[1],
            "mem_total": parts[2],
            "temp": parts[3],
            "fan": parts[4] + "%",
        }

    def _powershell_json(self, command, timeout=8):
        return _powershell_json_data(command, timeout=timeout)

    def _query_cpu_clock(self):
        return _query_cpu_clock_safe()

    def _query_standby_memory(self):
        return _query_standby_memory_safe()

    def _query_storage_health(self):
        return _query_storage_health_safe()

    def enable_ultimate_performance(self):
        if QMessageBox.question(
            self,
            "Ultimate Performance",
            "Ativar o plano Ultimate Performance do Windows? Isso nao apaga nada, mas aumenta consumo de energia.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
        code, out, err = self._run(["powercfg", "-duplicatescheme", guid], timeout=8)
        new_guid = guid
        match = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F-]{27,})", out)
        if match:
            new_guid = match.group(1)
        code2, out2, err2 = self._run(["powercfg", "-setactive", new_guid], timeout=8)
        if code2 == 0:
            self._log("Ultimate Performance ativado.")
        else:
            self._log(f"Nao consegui ativar: {err2 or out2 or err}")

    def enable_balanced_power(self):
        code, out, err = self._run(["powercfg", "-setactive", "SCHEME_BALANCED"], timeout=8)
        self._log("Plano Equilibrado ativado." if code == 0 else f"Falha ao ativar Equilibrado: {err or out}")

    def trim_app_memory(self):
        try:
            handle = ctypes.windll.kernel32.GetCurrentProcess()
            ctypes.windll.psapi.EmptyWorkingSet(handle)
            import gc

            gc.collect()
            self._log("Memoria do proprio app aparada com seguranca. Standby do Windows nao foi forcado.")
        except Exception as exc:
            self._log(f"Nao consegui aparar memoria do app: {exc}")

    def set_foreground_priority(self, high=True):
        if QMessageBox.question(
            self,
            "Prioridade de processo",
            "Aplicar prioridade ao aplicativo que esta em foco agora? Use apenas em jogos/apps seus, nunca em processos do sistema.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return
        try:
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            pid = wintypes.DWORD()
            ctypes.windll.user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            if pid.value <= 4:
                self._log("Processo do sistema ignorado.")
                return
            PROCESS_SET_INFORMATION = 0x0200
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = ctypes.windll.kernel32.OpenProcess(
                PROCESS_SET_INFORMATION | PROCESS_QUERY_LIMITED_INFORMATION, False, pid.value
            )
            if not handle:
                self._log("Sem permissao para alterar esse processo.")
                return
            priority = 0x00000080 if high else 0x00000020
            ok = ctypes.windll.kernel32.SetPriorityClass(handle, priority)
            ctypes.windll.kernel32.CloseHandle(handle)
            self._log(f"Prioridade {'alta' if high else 'normal'} aplicada ao PID {pid.value}." if ok else "Falha ao alterar prioridade.")
        except Exception as exc:
            self._log(f"Erro ao alterar prioridade: {exc}")

    def diagnose_timer(self):
        code, out, err = self._run(["bcdedit", "/enum", "{current}"], timeout=8)
        if code == 0:
            useful = []
            for line in out.splitlines():
                low = line.lower()
                if "useplatformclock" in low or "disabledynamictick" in low or "tscsyncpolicy" in low:
                    useful.append(line.strip())
            self._log("Timer/BCD: " + (" | ".join(useful) if useful else "nenhum ajuste manual encontrado."))
            self._log("Por seguranca, este modulo nao altera HPET/BCD automaticamente.")
        else:
            self._log(f"Nao consegui ler BCD: {err or out}")

    def force_slow_refresh(self):
        if self._slow_worker and self._slow_worker.isRunning():
            self._log("Diagnostico ainda esta atualizando.")
            return
        self._last_slow_poll = time.time()
        self._slow_worker = SlowMetricsWorker(self)
        self._slow_worker.metrics_ready.connect(self._slow_metrics_ready)
        self._slow_worker.start()
        self._log("Atualizando diagnostico completo em segundo plano.")

    def quick_diagnosis(self):
        notes = []
        try:
            ram_load = int(self.ram_card["value"].text().replace("%", "").strip())
            if ram_load >= 85:
                notes.append("RAM alta: feche apps pesados ou reinicie antes de jogo/IA pesada.")
        except Exception:
            pass
        try:
            cpu_load = int(self.cpu_card["value"].text().replace("%", "").strip())
            if cpu_load >= 90:
                notes.append("CPU muito alta: verifique processos pesados na lista abaixo.")
        except Exception:
            pass
        if "Equilibrado" in self._power_plan:
            notes.append("Plano equilibrado ativo: para desempenho maximo, use Ultimate Performance quando estiver jogando.")
        if self._admin_text == "Usuario normal":
            notes.append("Sem admin: algumas leituras/acoes podem ficar limitadas.")
        if not notes:
            notes.append("Nenhum alerta grave agora. Temperaturas podem exigir LibreHardwareMonitor para leitura completa.")
        for note in notes:
            self._log(note)

    def _reg_value(self, key, value):
        code, out, err = self._run(["reg", "query", key, "/v", value], timeout=6)
        if code != 0:
            return "N/D"
        pattern = re.compile(r"^\s*" + re.escape(value) + r"\s+REG_\w+\s+(.+?)\s*$", re.I)
        for line in out.splitlines():
            match = pattern.match(line)
            if match:
                return match.group(1).strip()
        return "N/D"

    def audit_package_tweaks(self):
        self._log("Pacotes analisados: PACK e Extreme BOOST/CLEAR. Nada foi executado.")
        self._log("Aproveitavel com seguranca: energia, Game DVR, prioridade de jogos, mouse/teclado e diagnostico BCD.")
        self._log("Mantido como perigoso: apagar Prefetch, limpar logs do Windows, mexer em BCD/HPET no automatico e rodar .exe desconhecido.")

        checks = [
            ("GameDVR_Enabled", r"HKCU\System\GameConfigStore", "GameDVR_Enabled"),
            ("AppCaptureEnabled", r"HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\GameDVR", "AppCaptureEnabled"),
            ("NetworkThrottlingIndex", r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "NetworkThrottlingIndex"),
            ("SystemResponsiveness", r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile", "SystemResponsiveness"),
            ("Games GPU Priority", r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "GPU Priority"),
            ("Games CPU Priority", r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "Priority"),
            ("Games Scheduling", r"HKLM\SOFTWARE\Microsoft\Windows NT\CurrentVersion\Multimedia\SystemProfile\Tasks\Games", "Scheduling Category"),
            ("MouseSpeed", r"HKCU\Control Panel\Mouse", "MouseSpeed"),
            ("MouseThreshold1", r"HKCU\Control Panel\Mouse", "MouseThreshold1"),
            ("MouseThreshold2", r"HKCU\Control Panel\Mouse", "MouseThreshold2"),
            ("MouseSensitivity", r"HKCU\Control Panel\Mouse", "MouseSensitivity"),
            ("KeyboardDelay", r"HKCU\Control Panel\Keyboard", "KeyboardDelay"),
            ("KeyboardSpeed", r"HKCU\Control Panel\Keyboard", "KeyboardSpeed"),
        ]
        values = []
        for label, key, value in checks:
            values.append(f"{label}: {self._reg_value(key, value)}")
        self._log("Registro atual: " + " | ".join(values[:7]))
        self._log("Mouse/teclado atual: " + " | ".join(values[7:]))

        code, out, err = self._run(["powershell", "-NoProfile", "-Command", "(Get-MMAgent).MemoryCompression"], timeout=6)
        compression = ((out or err).strip() if code == 0 else "N/D")
        self._log("Compactacao de memoria: " + compression)
        result = [
            "AUDITORIA SEGURA DOS PACOTES",
            "",
            "O que foi aproveitado:",
            "- Energia e plano Ultimate Performance.",
            "- Leitura de Game DVR e prioridade de jogos.",
            "- Leitura de mouse/teclado para input lag.",
            "- Diagnostico de timer/BCD sem alterar boot.",
            "",
            "O que ficou bloqueado por seguranca:",
            "- Apagar Prefetch, logs do Windows e cookies globais.",
            "- Importar .reg grande sem backup.",
            "- Rodar .exe desconhecido dos packs.",
            "- Alterar BCD/HPET automaticamente.",
            "",
            "Valores atuais:",
            *values,
            f"MemoryCompression: {compression}",
            f"Plano de energia: {self._power_plan}",
        ]
        if hasattr(self, "audit_result_box"):
            self.audit_result_box.setText("\n".join(result))
        self.diagnose_timer()

    def create_restore_point(self):
        if not _query_admin_safe().startswith("Administrador"):
            self._log("Ponto de restauracao precisa do app aberto como administrador.")
            return
        if QMessageBox.question(
            self,
            "Ponto de restauracao",
            "Criar um ponto de restauracao antes de qualquer ajuste do Windows?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        ) != QMessageBox.Yes:
            return
        command = "Checkpoint-Computer -Description 'Antes Desempenho Pro' -RestorePointType 'MODIFY_SETTINGS'"
        code, out, err = self._run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
            timeout=60,
        )
        if code == 0:
            self._log("Ponto de restauracao solicitado com sucesso.")
        else:
            self._log("Nao consegui criar ponto de restauracao. Ative Protecao do Sistema no Windows. " + (err or out))

    def safe_temp_cleanup(self):
        temp_dir = Path(tempfile.gettempdir()).resolve()
        user_profile = Path(os.environ.get("USERPROFILE", "")).resolve()
        try:
            temp_dir.relative_to(user_profile)
        except Exception:
            self._log(f"Limpeza cancelada: TEMP fora da pasta do usuario ({temp_dir}).")
            return

        if QMessageBox.question(
            self,
            "Limpeza segura",
            f"Limpar somente arquivos antigos do TEMP do usuario?\n\nPasta: {temp_dir}\nIdade minima: 24 horas\nPrefetch, logs e Windows Temp nao serao tocados.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        ) != QMessageBox.Yes:
            return

        cutoff = time.time() - (24 * 60 * 60)
        removed = 0
        freed = 0
        failed = 0

        def inside_temp(path):
            try:
                path.resolve().relative_to(temp_dir)
                return True
            except Exception:
                return False

        for item in list(temp_dir.iterdir()):
            try:
                if item.is_symlink() or not inside_temp(item):
                    continue
                if item.stat().st_mtime > cutoff:
                    continue
                size = item.stat().st_size if item.is_file() else 0
                if item.is_dir():
                    for nested in item.rglob("*"):
                        if nested.is_file() and inside_temp(nested):
                            try:
                                size += nested.stat().st_size
                            except Exception:
                                pass
                    shutil.rmtree(item)
                else:
                    item.unlink()
                removed += 1
                freed += size
            except Exception:
                failed += 1

        self._log(f"Limpeza segura finalizada: {removed} item(ns), {_gb(freed)} liberados, {failed} falha(s).")

    def _active_power_guid(self):
        code, out, _ = self._run(["powercfg", "/getactivescheme"], timeout=5)
        if code != 0:
            return None
        match = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F-]{27,})", out)
        return match.group(1) if match else None

    def apply_performance_profile(self):
        profile = self.profile_combo.currentText() if hasattr(self, "profile_combo") else "Normal"
        if QMessageBox.question(
            self,
            "Aplicar perfil",
            f"Aplicar perfil '{profile}' agora? As mudancas sao reversiveis pelo botao Voltar ao normal.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        ) != QMessageBox.Yes:
            return

        self._last_power_plan_guid = self._active_power_guid()
        if profile == "Normal":
            self.enable_balanced_power()
            self._log("Perfil Normal aplicado: plano equilibrado e sem ajustes agressivos.")
            return

        guid = "e9a42b02-d5df-448d-aa00-03f14749eb61"
        code, out, err = self._run(["powercfg", "-duplicatescheme", guid], timeout=8)
        new_guid = guid
        match = re.search(r"([0-9a-fA-F]{8}-[0-9a-fA-F-]{27,})", out)
        if match:
            new_guid = match.group(1)
        code2, out2, err2 = self._run(["powercfg", "-setactive", new_guid], timeout=8)
        if code2 == 0:
            if profile == "Jogo":
                self._log("Perfil Jogo aplicado: energia maxima. Use prioridade alta apenas no jogo em foco.")
            else:
                self._log("Perfil IA pesada aplicado: energia maxima para Ollama/Stable Diffusion. Monitore GPU/RAM.")
        else:
            self._log(f"Nao consegui aplicar perfil {profile}: {err2 or out2 or err}")

    def restore_normal_profile(self):
        target = self._last_power_plan_guid or "SCHEME_BALANCED"
        code, out, err = self._run(["powercfg", "-setactive", target], timeout=8)
        if code == 0:
            self._log("Voltou ao modo normal/equilibrado.")
        else:
            self._log(f"Nao consegui voltar ao normal: {err or out}")

    def detect_lhm(self):
        sensors = _query_lhm_sensors_safe()
        self._lhm_summary = sensors.get("summary") or "N/D"
        self._lhm_temps = sensors.get("temps") or {}
        if self._lhm_summary == "N/D":
            msg = (
                "LibreHardwareMonitor ainda nao apareceu no WMI. Baixe a versao portatil, coloque em "
                "tools\\LibreHardwareMonitor, abra como administrador e ative a opcao WMI/Remote web se existir."
            )
        else:
            msg = "Sensores detectados: " + self._lhm_summary
        if hasattr(self, "lhm_status_label"):
            self.lhm_status_label.setText(msg)
        self._log(msg)

    def open_lhm_folder(self):
        folder = BASE_DIR / "tools" / "LibreHardwareMonitor"
        try:
            folder.mkdir(parents=True, exist_ok=True)
            if os.name == "nt":
                os.startfile(str(folder))
                self._log(f"Pasta aberta: {folder}")
            else:
                self._log(f"Pasta esperada: {folder}")
        except Exception as exc:
            self._log(f"Nao consegui abrir a pasta do LibreHardwareMonitor: {exc}")

    def copy_summary(self):
        summary = "\n".join([
            "Desempenho Pro - Resumo",
            f"CPU: {self.cpu_card['value'].text()} | {self.cpu_card['detail'].text()}",
            f"GPU: {self.gpu_card['value'].text()} | {self.gpu_card['detail'].text()}",
            f"RAM: {self.ram_card['value'].text()} | {self.ram_card['detail'].text()}",
            f"SSD: {self.ssd_card['value'].text()} | {self.ssd_card['detail'].text()}",
            f"Rede: {self.net_card['detail'].text()}",
            f"Sistema: {self.system_card['value'].text()} | {self.system_card['detail'].text()}",
            "",
            "Processos pesados:",
            self.process_box.toPlainText() or "N/D",
        ])
        QApplication.clipboard().setText(summary)
        self._log("Resumo copiado para a area de transferencia.")

    def closeEvent(self, event):
        if self._slow_worker and self._slow_worker.isRunning():
            self._slow_worker.wait(200)
        super().closeEvent(event)
