#!/usr/bin/env python3
"""Acoes de negocio da janela principal.

Este mixin separa geracao, copia, coleta e exportacao do orquestrador main_app.py.
"""

import json

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication, QDialog, QFileDialog, QLineEdit, QMessageBox,
    QPlainTextEdit, QTextEdit,
)

from account_manager import GerenciadorContas
from app.core.worker_threads import CollectorThread
from app.ui.dialogs import (
    CodeInputDialog, ConfigDialog, DataViewDialog, GroupManagerDialog, PasswordInputDialog,
)
from app.ui.shell_widgets import _set_clipboard_text_safe
from config_manager import ConfigManager
from settings import BASE_DIR, settings


class MainActionsMixin:


    def statusBar(self):
        return self.status_bar

    def _shortcut_generate(self):
        """Enter/Space gera par apenas quando na aba Gerador."""
        if self.main_tabs.currentIndex() == self._page_index_by_name("Gerador"):
            self.generate_pair()

    def _shortcut_copy(self):
        """Ctrl+C copia resultado apenas quando na aba Gerador e sem seleção."""
        if self.main_tabs.currentIndex() == self._page_index_by_name("Gerador"):
            focused = QApplication.focusWidget()
            # Só age se não houver widget de texto com foco
            if not isinstance(focused, (QLineEdit, QTextEdit, QPlainTextEdit)):
                self.copy_result()

    def toggle_filtro(self, state):
        enabled = state == Qt.Checked
        self.idade_min_spin.setEnabled(enabled)
        self.idade_max_spin.setEnabled(enabled)

    def toggle_filtro_score(self, state):
        enabled = state == Qt.Checked
        self.score_min_spin.setEnabled(enabled)
        self.score_max_spin.setEnabled(enabled)

    def toggle_display(self, field):
        mapping = {
            "nome": "mostrar_nome", "cpf": "mostrar_cpf",
            "idade": "mostrar_idade", "data": "mostrar_data",
            "telefone": "mostrar_telefone", "score": "mostrar_score",
        }
        if field in mapping:
            cb = getattr(self, f"check_{field}", None)
            if cb:
                setattr(self, mapping[field], cb.isChecked())
        self.update_field_visibility()
        if self.current_pair:
            self.display_pair(self.current_pair)

    def update_field_visibility(self):
        pairs = [
            ("nome_label", self.mostrar_nome),
            ("cpf_label", self.mostrar_cpf),
            ("idade_label", self.mostrar_idade),
            ("nasc_label", self.mostrar_data),
            ("telefone_label", self.mostrar_telefone),
            ("score_label", self.mostrar_score),
        ]
        for attr, vis in pairs:
            w = getattr(self, attr, None)
            if w:
                w.setVisible(vis)

    def update_stats(self):
        stats = self.db.get_stats()
        txt = (f"📊 {stats['total']}  ✅ {stats['complete']}  "
               f"📅 {stats.get('with_birth',0)}  📞 {stats['with_phone']}  ⭐ {stats['with_score']}")
        self.stats_label.setText(txt)
        self.header.set_stats(txt)

    def generate_pair(self):
        filters = {"require_birth": True}
        if self.filtro_checkbox.isChecked():
            filters["idade_min"] = self.idade_min_spin.value()
            filters["idade_max"] = self.idade_max_spin.value()
        else:
            filters["idade_max"] = 59
        if self.filtro_score_checkbox.isChecked():
            filters["score_min"] = self.score_min_spin.value()
            filters["score_max"] = self.score_max_spin.value()
        pair = self.db.get_random_pair(filters)
        if pair:
            self.current_pair = pair
            try:
                self.db.record_draw(pair.get("id"))
            except Exception:
                pass
            self.display_pair(pair)
            self._flash_result_fields()
            self.status_bar.showMessage("✅ Par gerado com sucesso!", 1500)
        else:
            for attr in ["nome_label","cpf_label","idade_label","nasc_label","telefone_label","score_label"]:
                lbl = getattr(self, attr, None)
                if lbl: lbl.setText(lbl.text().split(":")[0] + ":  —")
            self.current_pair = None
            self.status_bar.showMessage("❌ Nenhum registro encontrado com os filtros aplicados", 3000)

    def _flash_result_fields(self):
        """Flash verde rápido nos campos de resultado para feedback visual."""
        flash_qss = ("QLabel{color:#10b981;font-family:'Consolas','Cascadia Code',monospace;"
                     "font-size:13px;font-weight:500;background:#071a10;"
                     "border:1px solid rgba(16,185,129,0.4);border-radius:7px;padding:8px 12px;}")
        normal_qss = ("QLabel{color:#22d3ee;font-family:'Consolas','Cascadia Code',monospace;"
                      "font-size:13px;font-weight:500;background:#07080f;"
                      "border:1px solid rgba(6,182,212,0.09);border-radius:7px;padding:8px 12px;}")
        labels = [getattr(self, a, None) for a in
                  ["nome_label","cpf_label","idade_label","nasc_label","telefone_label","score_label"]]
        labels = [l for l in labels if l]
        for l in labels:
            l.setStyleSheet(flash_qss)
        QTimer.singleShot(350, lambda: [l.setStyleSheet(normal_qss) for l in labels if l])

    def display_pair(self, pair):
        def _set(attr, prefix, key):
            lbl = getattr(self, f"{attr}_label", None)
            if lbl:
                val = pair.get(key, "")
                lbl.setText(f"{prefix}  {val}" if val else f"{prefix}  —")
        _set("nome",  "👤  Nome:", "nome")
        _set("cpf",   "🆔  CPF:", "cpf")
        idade_lbl = getattr(self, "idade_label", None)
        if idade_lbl:
            v = pair.get("idade")
            idade_lbl.setText(f"🎂  Idade:  {v} anos" if v else "🎂  Idade:  —")
        _set("nasc",  "📅  Nasc.:", "nascimento")
        _set("telefone", "📞  Tel.:", "telefone")
        _set("score", "⭐  Score:", "score")
        self.update_field_visibility()

    def copy_field(self, field):
        if not self.current_pair:
            self.status_bar.showMessage("⚠️ Nenhum dado para copiar", 2000)
            return
        key_map = {"nome":"nome","cpf":"cpf","idade":"idade","nasc":"nascimento",
                   "telefone":"telefone","score":"score"}
        key = key_map.get(field, field)
        val = self.current_pair.get(key)
        if val:
            _set_clipboard_text_safe(str(val))
            self.status_bar.showMessage(f"✅ {key.capitalize()} copiado!", 1500)
            # Flash verde no label copiado
            lbl_attr = f"{field}_label"
            lbl = getattr(self, lbl_attr, None)
            if lbl:
                orig = lbl.styleSheet()
                flash = orig.replace("#22d3ee", "#10b981").replace("#07080f", "#071a10").replace(
                    "rgba(6,182,212,0.09)", "rgba(16,185,129,0.35)")
                lbl.setStyleSheet(flash)
                QTimer.singleShot(400, lambda: lbl.setStyleSheet(orig))

    def copy_result(self):
        if not self.current_pair:
            self.status_bar.showMessage("⚠️ Nenhum dado para copiar", 2000)
            return
        p = self.current_pair
        lines = []
        if self.mostrar_nome and p.get("nome"): lines.append(f"👤 Nome: {p['nome']}")
        if self.mostrar_cpf and p.get("cpf"):   lines.append(f"🆔 CPF: {p['cpf']}")
        if self.mostrar_idade and p.get("idade"): lines.append(f"🎂 Idade: {p['idade']} anos")
        if self.mostrar_data and p.get("nascimento"): lines.append(f"📅 Nascimento: {p['nascimento']}")
        if self.mostrar_telefone and p.get("telefone"): lines.append(f"📞 Telefone: {p['telefone']}")
        if self.mostrar_score and p.get("score"): lines.append(f"⭐ Score: {p['score']}")
        if lines:
            _set_clipboard_text_safe("\n".join(lines))
            self.status_bar.showMessage("✅ Todos os dados copiados!", 2000)

    def show_tools(self):
        idx = self._page_index_by_name("Ferramentas")
        if idx < 0:
            return
        self.main_tabs.setCurrentIndex(idx)
        self.sidebar.set_current(idx)
        self.header.set_title(self.tab_titles[idx] if idx < len(self.tab_titles) else "🛠️  Ferramentas")

    def show_tools_tab(self, tab_index):
        self.show_tools()
        if 0 <= tab_index < self.tools_tabs.count():
            self.tools_tabs.setCurrentIndex(tab_index)
        elif tab_index == 6:
            self.open_page_by_name("Config")

    def show_groups_dialog(self):
        GroupManagerDialog(self).exec_()

    def show_contas_dialog(self):
        GerenciadorContas(self).exec_()
        self.config_manager.load_config()
        self.refresh_database()

    def show_config_dialog(self):
        if ConfigDialog(self).exec_() == QDialog.Accepted:
            self.update_stats()

    def start_collection(self):
        config_manager = ConfigManager()
        conta_ativa = config_manager.get_conta_ativa()
        if not settings.is_configured and not conta_ativa:
            QMessageBox.warning(self, "Configuração", "Configure as credenciais primeiro!")
            self.show_config_dialog()
            return
        groups_file = BASE_DIR / "grupos.json"
        groups = [settings.default_group]
        if groups_file.exists():
            try:
                with open(groups_file, "r") as f:
                    groups = json.load(f)
            except (json.JSONDecodeError, IOError, PermissionError) as e:
                print(f"Aviso: {e}")
        if len(groups) > 1:
            reply = QMessageBox.question(self, "Coletar Dados",
                f"Você tem {len(groups)} grupos.\nGrupos: {', '.join(groups)}\n\nColetar de TODOS?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel)
            if reply == QMessageBox.Cancel: return
            if reply == QMessageBox.No: groups = [groups[0]]
        else:
            if QMessageBox.question(self, "Coletar Dados",
                "Receberá um código SMS.\nContinuar?",
                QMessageBox.Yes | QMessageBox.No) == QMessageBox.No:
                return
        # Padrao automatico: exige data de nascimento e ignora 60+ quando a
        # idade puder ser detectada. Score nao e obrigatorio.
        exigir_data = True
        filtrar_idosos = True
        idade_maxima = 59
        self.status_bar.showMessage(
            "Coleta automatica: exige data de nascimento, nao exige score e ignora 60+.",
            6000
        )
        self.progress_bar.setVisible(True); self.progress_bar.setRange(0,0)
        self.generate_btn.setEnabled(False)
        conta_id = conta_ativa["id"] if conta_ativa else None
        self.collector_thread = CollectorThread(
            groups=groups, filtrar_idosos=filtrar_idosos,
            idade_maxima=idade_maxima, exigir_data_nascimento=exigir_data,
            conta_id=conta_id)
        self.collector_thread.progress.connect(self.show_progress)
        self.collector_thread.error.connect(self.show_error)
        self.collector_thread.finished.connect(self.collection_finished)
        self.collector_thread.code_requested.connect(self.show_code_dialog)
        self.collector_thread.password_requested.connect(self.show_password_dialog)
        self.collector_thread.start()

    def show_code_dialog(self, phone):
        dlg = CodeInputDialog(phone, self)
        if dlg.exec_() == QDialog.Accepted and dlg.code:
            self.collector_thread.set_verification_code(dlg.code)
        else:
            self.show_error("Autenticação cancelada.")

    def show_password_dialog(self):
        dlg = PasswordInputDialog(self)
        if dlg.exec_() == QDialog.Accepted and dlg.password:
            self.collector_thread.set_password(dlg.password)
        else:
            self.show_error("Autenticação 2FA cancelada.")

    def show_progress(self, msg):
        self.status_bar.showMessage(msg)

    def show_error(self, err):
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        QMessageBox.critical(self, "Erro", f"Erro na coleta:\n{err}")

    def collection_finished(self, collected):
        self.progress_bar.setVisible(False)
        self.generate_btn.setEnabled(True)
        self.refresh_database()
        QMessageBox.information(self, "Sucesso", f"Coleta concluída!\n\n{collected} novos registros.")

    def show_data(self):
        DataViewDialog(self.db, self).exec_()

    def export_data(self):
        fp, _ = QFileDialog.getSaveFileName(self, "Salvar CSV", "dados_completo.csv", "CSV (*.csv)")
        if fp:
            if self.db.export_csv(fp, "completo"):
                QMessageBox.information(self, "Sucesso", f"Exportado:\n{fp}")
            else:
                QMessageBox.critical(self, "Erro", "Erro ao exportar")
