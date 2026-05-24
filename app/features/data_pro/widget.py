#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Dados Pro: qualidade, higiene, atualizacao inteligente e mini ferramentas."""

import html
import os
import re
import sqlite3
from datetime import datetime
from pathlib import Path

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from app.core.paths import BASE_DIR
from app.ui.app_theme import DARK_STYLE_PRO
from app.ui.components import PALETTE, tabs_qss
from address_generator import AddressGenerator


INVALID_EMPTY = {"", "none", "null", "n/a", "na", "nao informado", "não informado", "sem informacao", "sem informação"}


def _digits(value):
    return re.sub(r"\D", "", str(value or ""))


def _title_name(value):
    value = re.sub(r"\s+", " ", str(value or "").strip())
    if not value:
        return None
    return " ".join(part.capitalize() if len(part) > 2 else part.lower() for part in value.split())


def _parse_date(value):
    if not value:
        return None
    text = str(value).strip().replace("-", "/").replace(".", "/")
    current_year = datetime.now().year
    match_iso = re.search(r"\b(\d{4})/(\d{1,2})/(\d{1,2})\b", text)
    if match_iso:
        y, m, d = map(int, match_iso.groups())
    else:
        match = re.search(r"\b(\d{1,2})/(\d{1,2})/(\d{2,4})\b", text)
        if not match:
            return None
        d, m, y = map(int, match.groups())
        if y < 100:
            y += 2000 if y <= current_year % 100 else 1900
    try:
        dt = datetime(y, m, d)
    except ValueError:
        return None
    if not 1900 <= dt.year <= current_year or dt.date() > datetime.now().date():
        return None
    return dt


def _age_from_birth(value):
    dt = _parse_date(value)
    if not dt:
        return None
    today = datetime.now()
    age = today.year - dt.year
    if (today.month, today.day) < (dt.month, dt.day):
        age -= 1
    return age if 0 <= age <= 130 else None


def _score_value(value):
    if value is None:
        return None
    token = str(value).strip().split("/")[0]
    token = re.sub(r"[^\d,.]", "", token)
    if not token:
        return None
    if re.fullmatch(r"0*1[,.]000", token):
        token = "1000"
    elif re.fullmatch(r"\d{1,4}[,.]0+", token):
        token = token.split(".")[0].split(",")[0]
    elif re.fullmatch(r"\d{1,3}[,.]\d{3}", token):
        token = token.replace(".", "").replace(",", "")
    else:
        token = re.sub(r"\D", "", token)
    try:
        score = int(token)
    except ValueError:
        return None
    return score if 0 <= score <= 1000 else None


class DataProWidget(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self.db = db
        self.estados = AddressGenerator.ESTADOS
        self._build()
        self.refresh_quality()

    def update_db(self, db):
        self.db = db
        self.refresh_quality()

    def _build(self):
        self.setStyleSheet(
            DARK_STYLE_PRO
            + tabs_qss(compact=True)
            + f"""
            QTextEdit {{ font-family: Consolas, 'Cascadia Code', monospace; }}
            QFrame#DataProHeader, QFrame#DataProMetricCard {{
                background: {PALETTE.card};
                border: 1px solid {PALETTE.border};
                border-radius: 10px;
            }}
            QFrame#DataProMetricCard {{
                background: {PALETTE.card_alt};
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(16, 12, 16, 12)
        root.setSpacing(10)
        root.addWidget(self._header())

        self.tabs = QTabWidget()
        root.addWidget(self.tabs, 1)
        self.tabs.addTab(self._quality_tab(), "Qualidade")
        self.tabs.addTab(self._clean_tab(), "Higienizar")
        self.tabs.addTab(self._update_tab(), "Atualizador")
        self.tabs.addTab(self._builder_tab(), "Mini ferramentas")

    def _header(self):
        frame = QFrame()
        frame.setObjectName("DataProHeader")
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(16, 12, 16, 12)
        title = QLabel("Dados Pro")
        title.setStyleSheet("background:transparent;border:none;font-size:22px;font-weight:900;color:#f8fafc;")
        sub = QLabel("Qualidade da coleta, limpeza segura, melhoria de registros e criador de mini ferramentas.")
        sub.setStyleSheet("background:transparent;border:none;color:#94a3b8;")
        lay.addWidget(title)
        lay.addWidget(sub)
        return frame

    def _quality_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(10)

        self.quality_grid = QGridLayout()
        self.quality_grid.setSpacing(10)
        self.quality_cards = {}
        for i, key in enumerate(["total", "score", "idade", "telefone", "cidade", "duplicados"]):
            card = self._metric_card(key.title(), "0", "#22d3ee")
            self.quality_cards[key] = card
            self.quality_grid.addWidget(card["frame"], i // 3, i % 3)
        lay.addLayout(self.quality_grid)

        actions = QHBoxLayout()
        actions.addWidget(self._button("Atualizar qualidade", self.refresh_quality, "#22d3ee"))
        actions.addWidget(self._button("Copiar relatorio", self.copy_quality_report, "#34d399"))
        actions.addStretch(1)
        lay.addLayout(actions)

        self.quality_report = QTextEdit()
        self.quality_report.setReadOnly(True)
        lay.addWidget(self.quality_report, 1)
        return page

    def _clean_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        box = QGroupBox("LIMPEZA GUIADA")
        box_lay = QVBoxLayout(box)
        info = QLabel("Faz ajustes seguros: remove espacos, corrige telefone/CPF quando possivel, normaliza score e limpa campos vazios.")
        info.setWordWrap(True)
        info.setStyleSheet("color:#94a3b8;")
        box_lay.addWidget(info)
        buttons = QHBoxLayout()
        buttons.addWidget(self._button("Prever limpeza", self.preview_cleanup, "#22d3ee"))
        buttons.addWidget(self._button("Aplicar limpeza", self.apply_cleanup, "#fbbf24"))
        buttons.addStretch(1)
        box_lay.addLayout(buttons)
        lay.addWidget(box)
        self.clean_report = QTextEdit()
        self.clean_report.setReadOnly(True)
        lay.addWidget(self.clean_report, 1)
        return page

    def _update_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        box = QGroupBox("ATUALIZADOR INTELIGENTE")
        box_lay = QVBoxLayout(box)
        info = QLabel("Melhora registros sem sobrescrever dado bom: recalcula idade pela data, arruma nomes em caixa alta/baixa e melhora estado por extenso.")
        info.setWordWrap(True)
        info.setStyleSheet("color:#94a3b8;")
        box_lay.addWidget(info)
        buttons = QHBoxLayout()
        buttons.addWidget(self._button("Prever melhorias", self.preview_smart_update, "#22d3ee"))
        buttons.addWidget(self._button("Aplicar melhorias", self.apply_smart_update, "#34d399"))
        buttons.addStretch(1)
        box_lay.addLayout(buttons)
        lay.addWidget(box)
        self.update_report = QTextEdit()
        self.update_report.setReadOnly(True)
        lay.addWidget(self.update_report, 1)
        return page

    def _builder_tab(self):
        page = QWidget()
        lay = QVBoxLayout(page)
        lay.setContentsMargins(0, 0, 0, 0)
        form = QGroupBox("CONSTRUTOR DE MINI FERRAMENTAS")
        f_lay = QGridLayout(form)
        self.tool_name = QLineEdit()
        self.tool_name.setPlaceholderText("Ex: Organizador de pedidos")
        self.tool_desc = QLineEdit()
        self.tool_desc.setPlaceholderText("Ex: salvar pedidos com status e observacao")
        self.tool_kind = QComboBox()
        self.tool_kind.addItems(["Tabela simples", "Checklist", "Cadastro com status"])
        self.tool_fields = QTextEdit()
        self.tool_fields.setPlaceholderText("Um campo por linha. Ex:\nNome\nEmail\nStatus\nObservacao")
        self.tool_fields.setMinimumHeight(120)
        f_lay.addWidget(QLabel("Nome:"), 0, 0)
        f_lay.addWidget(self.tool_name, 0, 1)
        f_lay.addWidget(QLabel("Descricao:"), 1, 0)
        f_lay.addWidget(self.tool_desc, 1, 1)
        f_lay.addWidget(QLabel("Modelo:"), 2, 0)
        f_lay.addWidget(self.tool_kind, 2, 1)
        f_lay.addWidget(QLabel("Campos:"), 3, 0)
        f_lay.addWidget(self.tool_fields, 3, 1)
        buttons = QHBoxLayout()
        buttons.addWidget(self._button("Criar mini ferramenta HTML", self.create_mini_tool, "#22d3ee"))
        buttons.addWidget(self._button("Abrir pasta", self.open_mini_tools_folder, "#94a3b8"))
        buttons.addStretch(1)
        f_lay.addLayout(buttons, 4, 1)
        lay.addWidget(form)
        self.builder_report = QTextEdit()
        self.builder_report.setReadOnly(True)
        lay.addWidget(self.builder_report, 1)
        return page

    def _metric_card(self, title, value, color):
        frame = QFrame()
        frame.setObjectName("DataProMetricCard")
        frame.setMinimumHeight(95)
        frame.setStyleSheet(
            "QFrame#DataProMetricCard{"
            f"background:#0d1523;border:1px solid rgba(148,163,184,0.12);"
            f"border-left:4px solid {color};border-radius:14px;"
            "}"
        )
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(14, 10, 14, 10)
        label = QLabel(title)
        label.setStyleSheet(f"background:transparent;border:none;color:{color};font-weight:900;font-size:11px;")
        val = QLabel(value)
        val.setStyleSheet("background:transparent;border:none;color:#f8fafc;font-size:24px;font-weight:900;")
        detail = QLabel("Aguardando...")
        detail.setWordWrap(True)
        detail.setStyleSheet("background:transparent;border:none;color:#94a3b8;font-size:11px;")
        lay.addWidget(label)
        lay.addWidget(val)
        lay.addWidget(detail)
        return {"frame": frame, "value": val, "detail": detail}

    def _button(self, text, fn, color):
        btn = QPushButton(text)
        btn.setMinimumHeight(38)
        btn.setStyleSheet(
            f"QPushButton{{color:{color};background:#111827;border:1px solid rgba(148,163,184,0.18);border-radius:10px;font-weight:900;}}"
            f"QPushButton:hover{{background:{color}14;border-color:{color}88;}}"
        )
        btn.clicked.connect(fn)
        return btn

    def _connection(self):
        return self.db._get_connection()

    def _rows(self):
        with self._connection() as conn:
            conn.row_factory = sqlite3.Row
            return [dict(row) for row in conn.execute("SELECT * FROM pessoas").fetchall()]

    def refresh_quality(self):
        rows = self._rows()
        total = len(rows)
        if total == 0:
            self.quality_report.setText("Banco vazio.")
            return
        with_score = sum(1 for r in rows if r.get("score") is not None)
        valid_score = sum(1 for r in rows if _score_value(r.get("score")) is not None)
        with_age = sum(1 for r in rows if r.get("idade") is not None)
        birth_ages = [_age_from_birth(r.get("data_nascimento")) for r in rows]
        with_birth = sum(1 for age in birth_ages if age is not None)
        under_60 = sum(1 for age in birth_ages if age is not None and age <= 59)
        with_phone = sum(1 for r in rows if r.get("telefone"))
        with_city = sum(1 for r in rows if r.get("cidade") or r.get("estado"))
        cpf_counts = {}
        for r in rows:
            cpf = _digits(r.get("cpf"))
            if cpf:
                cpf_counts[cpf] = cpf_counts.get(cpf, 0) + 1
        duplicates = sum(count - 1 for count in cpf_counts.values() if count > 1)

        metrics = {
            "total": (total, "registros no banco"),
            "score": (with_score, f"{with_score * 100 / total:.1f}% com score | {valid_score} validos"),
            "idade": (with_age, f"{with_birth * 100 / total:.1f}% com nascimento | {under_60} ate 59"),
            "telefone": (with_phone, f"{with_phone * 100 / total:.1f}% com telefone"),
            "cidade": (with_city, f"{with_city * 100 / total:.1f}% com cidade/estado"),
            "duplicados": (duplicates, "CPFs repetidos apos normalizar"),
        }
        for key, (value, detail) in metrics.items():
            self.quality_cards[key]["value"].setText(str(value))
            self.quality_cards[key]["detail"].setText(detail)

        group_counts = {}
        for r in rows:
            group = r.get("grupo_origem") or "Sem grupo"
            group_counts[group] = group_counts.get(group, 0) + 1
        top_groups = sorted(group_counts.items(), key=lambda item: item[1], reverse=True)[:8]
        report = [
            "RELATORIO DE QUALIDADE",
            "",
            f"Total: {total}",
            f"Com score: {with_score} ({with_score * 100 / total:.1f}%)",
            f"Score valido: {valid_score}",
            f"Sem score: {total - with_score}",
            f"Com idade: {with_age}",
            f"Com nascimento valido: {with_birth}",
            f"Ate 59 anos pela data: {under_60}",
            f"Sem nascimento valido: {total - with_birth}",
            f"Com telefone: {with_phone}",
            f"Com cidade/estado: {with_city}",
            f"Possiveis duplicados por CPF normalizado: {duplicates}",
            "",
            "Grupos mais produtivos:",
        ]
        report += [f"- {name}: {count}" for name, count in top_groups]
        self.quality_report.setText("\n".join(report))

    def copy_quality_report(self):
        QApplication.clipboard().setText(self.quality_report.toPlainText())

    def _cleanup_changes(self):
        changes = []
        for r in self._rows():
            row_changes = {}
            cpf = _digits(r.get("cpf"))
            if cpf and len(cpf) == 11 and cpf != str(r.get("cpf") or ""):
                row_changes["cpf"] = cpf
            phone = _digits(r.get("telefone"))
            if phone.startswith("55") and len(phone) in (12, 13):
                phone = phone[2:]
            if phone and 10 <= len(phone) <= 11 and phone != str(r.get("telefone") or ""):
                row_changes["telefone"] = phone
            score = _score_value(r.get("score"))
            if score != r.get("score"):
                row_changes["score"] = score
            for field in ("cidade", "estado", "endereco", "mae"):
                raw = r.get(field)
                if raw is None:
                    continue
                clean = re.sub(r"\s+", " ", str(raw).strip())
                if clean.lower() in INVALID_EMPTY:
                    clean = None
                elif field in ("cidade", "estado"):
                    clean = _title_name(clean)
                    if field == "estado" and clean and len(clean) == 2:
                        clean = clean.upper()
                if clean != raw:
                    row_changes[field] = clean
            if row_changes:
                changes.append((r["id"], row_changes))
        return changes

    def preview_cleanup(self):
        changes = self._cleanup_changes()
        lines = [f"Previa: {len(changes)} registro(s) precisam de limpeza.", ""]
        for row_id, row_changes in changes[:80]:
            lines.append(f"ID {row_id}: " + ", ".join(f"{k} => {v}" for k, v in row_changes.items()))
        if len(changes) > 80:
            lines.append(f"... +{len(changes)-80} registros")
        self.clean_report.setText("\n".join(lines))

    def apply_cleanup(self):
        changes = self._cleanup_changes()
        if not changes:
            self.clean_report.setText("Nada para limpar.")
            return
        if QMessageBox.question(self, "Aplicar limpeza", f"Aplicar limpeza em {len(changes)} registro(s)?") != QMessageBox.Yes:
            return
        updated = self._apply_changes(changes)
        self.clean_report.setText(f"Limpeza aplicada em {updated} registro(s).")
        self.refresh_quality()

    def _smart_changes(self):
        changes = []
        for r in self._rows():
            row_changes = {}
            age = _age_from_birth(r.get("data_nascimento"))
            if age is not None and (r.get("idade") is None or abs(int(r.get("idade") or 0) - age) > 1):
                row_changes["idade"] = age
            nome = r.get("nome")
            if nome and nome.upper() == nome and len(nome.split()) >= 2:
                row_changes["nome"] = _title_name(nome)
            estado = r.get("estado")
            if estado and len(str(estado).strip()) == 2:
                uf = str(estado).strip().upper()
                if uf in self.estados:
                    row_changes["estado"] = self.estados[uf]
            if row_changes:
                changes.append((r["id"], row_changes))
        return changes

    def preview_smart_update(self):
        changes = self._smart_changes()
        lines = [f"Previa: {len(changes)} registro(s) podem ser melhorados.", ""]
        for row_id, row_changes in changes[:80]:
            lines.append(f"ID {row_id}: " + ", ".join(f"{k} => {v}" for k, v in row_changes.items()))
        if len(changes) > 80:
            lines.append(f"... +{len(changes)-80} registros")
        self.update_report.setText("\n".join(lines))

    def apply_smart_update(self):
        changes = self._smart_changes()
        if not changes:
            self.update_report.setText("Nada para melhorar.")
            return
        if QMessageBox.question(self, "Aplicar melhorias", f"Aplicar melhorias em {len(changes)} registro(s)?") != QMessageBox.Yes:
            return
        updated = self._apply_changes(changes)
        self.update_report.setText(f"Atualizacao inteligente aplicada em {updated} registro(s).")
        self.refresh_quality()

    def _apply_changes(self, changes):
        updated = 0
        with self._connection() as conn:
            cur = conn.cursor()
            for row_id, fields in changes:
                parts = []
                params = []
                for key, value in fields.items():
                    parts.append(f"{key} = ?")
                    params.append(value)
                if not parts:
                    continue
                params.append(row_id)
                try:
                    cur.execute(f"UPDATE pessoas SET {', '.join(parts)} WHERE id = ?", params)
                    updated += cur.rowcount
                except sqlite3.IntegrityError:
                    # Exemplo: CPF normalizado ja existe em outro registro. Mantem seguro e segue.
                    continue
            conn.commit()
        return updated

    def create_mini_tool(self):
        name = self.tool_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Mini ferramenta", "Digite um nome para a ferramenta.")
            return
        fields = [line.strip() for line in self.tool_fields.toPlainText().splitlines() if line.strip()]
        if not fields:
            fields = ["Nome", "Status", "Observacao"]
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "mini_ferramenta"
        out_dir = BASE_DIR / "mini_tools"
        out_dir.mkdir(exist_ok=True)
        path = out_dir / f"{slug}.html"
        path.write_text(self._mini_tool_html(name, self.tool_desc.text().strip(), fields), encoding="utf-8")
        self.builder_report.setText(f"Mini ferramenta criada:\n{path}\n\nEla salva dados no navegador usando localStorage.")
        try:
            os.startfile(str(path))
        except Exception:
            pass

    def open_mini_tools_folder(self):
        out_dir = BASE_DIR / "mini_tools"
        out_dir.mkdir(exist_ok=True)
        try:
            os.startfile(str(out_dir))
        except Exception as exc:
            self.builder_report.setText(f"Pasta: {out_dir}\nNao consegui abrir automaticamente: {exc}")

    def _mini_tool_html(self, name, desc, fields):
        safe_name = html.escape(name)
        safe_desc = html.escape(desc or "Mini ferramenta local gerada pelo Telegram Pro.")
        slug = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_") or "mini_ferramenta"
        fields_js = ", ".join(repr(f) for f in fields)
        inputs = "\n".join(
            f'<label>{html.escape(f)}<input id="f_{i}" placeholder="{html.escape(f)}"></label>'
            for i, f in enumerate(fields)
        )
        headers = "".join(f"<th>{html.escape(f)}</th>" for f in fields)
        return f"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{safe_name}</title>
<style>
body{{margin:0;background:#070b12;color:#e5e7eb;font-family:Segoe UI,Arial,sans-serif}}
main{{max-width:1100px;margin:0 auto;padding:28px}}
h1{{margin:0;font-size:28px}}p{{color:#94a3b8}}
.card{{background:#0a111d;border:1px solid rgba(148,163,184,.16);border-radius:14px;padding:16px;margin-top:14px}}
.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px}}
label{{display:flex;flex-direction:column;gap:6px;color:#93c5fd;font-weight:800;font-size:12px}}
input{{background:#0b1220;color:#e5e7eb;border:1px solid rgba(148,163,184,.22);border-radius:10px;padding:11px}}
button{{background:#0e7490;color:white;border:0;border-radius:10px;padding:11px 14px;font-weight:900;cursor:pointer}}
button.secondary{{background:#111827;color:#cbd5e1;border:1px solid rgba(148,163,184,.18)}}
table{{width:100%;border-collapse:collapse;margin-top:12px}}th,td{{border-bottom:1px solid rgba(148,163,184,.14);padding:9px;text-align:left}}th{{color:#67e8f9}}
</style>
</head>
<body>
<main>
<h1>{safe_name}</h1>
<p>{safe_desc}</p>
<section class="card">
<div class="grid">{inputs}</div>
<p><button onclick="addRow()">Adicionar</button> <button class="secondary" onclick="exportCsv()">Exportar CSV</button> <button class="secondary" onclick="clearAll()">Limpar</button></p>
</section>
<section class="card"><table><thead><tr>{headers}<th>Acoes</th></tr></thead><tbody id="rows"></tbody></table></section>
</main>
<script>
const fields=[{fields_js}];
const key='mini_tool_'+location.pathname;
let data=JSON.parse(localStorage.getItem(key)||'[]');
function save(){{localStorage.setItem(key,JSON.stringify(data));render();}}
function addRow(){{const row=fields.map((_,i)=>document.getElementById('f_'+i).value.trim());data.push(row);fields.forEach((_,i)=>document.getElementById('f_'+i).value='');save();}}
function delRow(i){{data.splice(i,1);save();}}
function clearAll(){{if(confirm('Limpar todos os dados desta mini ferramenta?')){{data=[];save();}}}}
function render(){{rows.innerHTML=data.map((r,i)=>'<tr>'+r.map(v=>'<td>'+escapeHtml(v)+'</td>').join('')+'<td><button class="secondary" onclick="delRow('+i+')">Excluir</button></td></tr>').join('');}}
function escapeHtml(s){{return String(s).replace(/[&<>"']/g,m=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[m]));}}
function exportCsv(){{const csv=[fields.join(';')].concat(data.map(r=>r.map(v=>'"'+String(v).replaceAll('"','""')+'"').join(';'))).join('\\n');const a=document.createElement('a');a.href=URL.createObjectURL(new Blob([csv],{{type:'text/csv'}}));a.download='{slug}.csv';a.click();}}
render();
</script>
</body>
</html>"""
