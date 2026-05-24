#!/usr/bin/env python3
"""Builder da pagina Gerador de Pares.

Separado de main_pages.py para deixar a janela principal mais simples sem alterar comportamento.
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox, QFrame, QGridLayout, QHBoxLayout, QLabel, QProgressBar,
    QPushButton, QScrollArea, QSizePolicy, QSpinBox, QSplitter,
    QVBoxLayout, QWidget,
)

from app.ui.components import PALETTE, button_qss, card_qss, label_qss


def build_generator_page(owner):
    page = QWidget()
    page.setStyleSheet("background: #07080f;")

    root_lay = QVBoxLayout(page)
    root_lay.setContentsMargins(10, 8, 10, 8)
    root_lay.setSpacing(0)

    splitter = QSplitter(Qt.Horizontal)
    splitter.setHandleWidth(6)
    splitter.setStyleSheet("""
        QSplitter::handle {
            background: transparent;
            width: 6px;
        }
        QSplitter::handle:hover {
            background: rgba(6,182,212,0.25);
            border-radius: 3px;
        }
        QSplitter::handle:pressed {
            background: rgba(6,182,212,0.45);
        }
    """)
    splitter.setChildrenCollapsible(False)

    # === PAINEL ESQUERDO (scroll) ===
    left_scroll = QScrollArea()
    left_scroll.setWidgetResizable(True)
    left_scroll.setFrameShape(QFrame.NoFrame)
    left_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
    left_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
    left_scroll.setStyleSheet(
        "QScrollArea{background:transparent;border:none;}"
        "QScrollBar:vertical{background:#07080f;width:5px;border-radius:2px;}"
        "QScrollBar::handle:vertical{background:#1a2540;border-radius:2px;min-height:20px;}"
        "QScrollBar::handle:vertical:hover{background:#06b6d4;}"
        "QScrollBar::add-line:vertical,QScrollBar::sub-line:vertical{height:0;}"
    )

    left_widget = QWidget()
    left_widget.setStyleSheet("background:transparent;")
    left_lay = QVBoxLayout(left_widget)
    left_lay.setContentsMargins(0, 0, 6, 0)
    left_lay.setSpacing(6)

    sp_qss = ("QSpinBox{background:#0d1525;border:1px solid rgba(6,182,212,0.2);"
              "border-radius:6px;color:#e2e8f0;padding:3px 6px;font-size:12px;min-width:52px;}"
              "QSpinBox::up-button,QSpinBox::down-button{width:14px;border:none;background:transparent;}")
    cb_qss = ("QCheckBox{color:#94a3b8;font-size:12px;spacing:5px;}"
              "QCheckBox::indicator{width:15px;height:15px;"
              "border:1px solid rgba(6,182,212,0.3);border-radius:3px;background:#0d1525;}"
              "QCheckBox::indicator:checked{background:#06b6d4;border-color:#06b6d4;}")
    sec_btn_qss = button_qss("secondary", "sm")

    def sec_lbl(txt):
        l = QLabel(txt)
        l.setStyleSheet(label_qss("section") + " letter-spacing:1px; padding:2px 0 0 0;")
        return l

    def card(build_fn):
        f = QFrame()
        f.setStyleSheet(card_qss("default", radius=8))
        f.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        lay = QVBoxLayout(f)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(7)
        build_fn(lay)
        return f

    # CARD FILTROS
    def build_filters(lay):
        lay.addWidget(sec_lbl("FILTROS"))
        row = QHBoxLayout(); row.setSpacing(8)
        owner.filtro_checkbox = QCheckBox("Idade")
        owner.filtro_checkbox.setStyleSheet(cb_qss)
        owner.filtro_checkbox.stateChanged.connect(owner.toggle_filtro)
        owner.idade_min_spin = QSpinBox()
        owner.idade_min_spin.setRange(0,120); owner.idade_min_spin.setValue(0)
        owner.idade_min_spin.setEnabled(True); owner.idade_min_spin.setStyleSheet(sp_qss)
        owner.idade_max_spin = QSpinBox()
        owner.idade_max_spin.setRange(0,120); owner.idade_max_spin.setValue(59)
        owner.idade_max_spin.setEnabled(True); owner.idade_max_spin.setStyleSheet(sp_qss)
        owner.filtro_checkbox.setChecked(True)
        s1 = QLabel("–"); s1.setStyleSheet("color:#334155;")
        row.addWidget(owner.filtro_checkbox)
        row.addWidget(owner.idade_min_spin)
        row.addWidget(s1)
        row.addWidget(owner.idade_max_spin)
        row.addSpacing(12)
        owner.filtro_score_checkbox = QCheckBox("Score")
        owner.filtro_score_checkbox.setStyleSheet(cb_qss)
        owner.filtro_score_checkbox.stateChanged.connect(owner.toggle_filtro_score)
        owner.score_min_spin = QSpinBox()
        owner.score_min_spin.setRange(0,1000); owner.score_min_spin.setValue(500)
        owner.score_min_spin.setEnabled(False); owner.score_min_spin.setStyleSheet(sp_qss)
        owner.score_max_spin = QSpinBox()
        owner.score_max_spin.setRange(0,1000); owner.score_max_spin.setValue(1000)
        owner.score_max_spin.setEnabled(False); owner.score_max_spin.setStyleSheet(sp_qss)
        s2 = QLabel("–"); s2.setStyleSheet("color:#334155;")
        row.addWidget(owner.filtro_score_checkbox)
        row.addWidget(owner.score_min_spin)
        row.addWidget(s2)
        row.addWidget(owner.score_max_spin)
        row.addStretch()
        lay.addLayout(row)
        disp = QHBoxLayout(); disp.setSpacing(10)
        lbl_e = QLabel("Exibir:"); lbl_e.setStyleSheet(label_qss("muted") + f" color:{PALETTE.faint}; font-size:11px;")
        disp.addWidget(lbl_e)
        for field, txt in [("nome","Nome"),("cpf","CPF"),("idade","Idade"),
                           ("data","Nasc."),("telefone","Tel."),("score","Score")]:
            cb = QCheckBox(txt); cb.setChecked(True); cb.setStyleSheet(cb_qss)
            cb.stateChanged.connect(lambda _, f=field: owner.toggle_display(f))
            setattr(owner, f"check_{field}", cb)
            disp.addWidget(cb)
        disp.addStretch()
        lay.addLayout(disp)
    left_lay.addWidget(card(build_filters))

    # CARD ACOES
    def build_acoes(lay):
        lay.addWidget(sec_lbl("AÇÕES"))
        mrow = QHBoxLayout(); mrow.setSpacing(8)
        owner.generate_btn = QPushButton("🎲  GERAR PAR")
        owner.generate_btn.setCursor(Qt.PointingHandCursor)
        owner.generate_btn.setFixedHeight(40)
        owner.generate_btn.setStyleSheet(button_qss("success", "lg"))
        owner.generate_btn.clicked.connect(owner.generate_pair)
        cbtn = QPushButton("📋  COPIAR")
        cbtn.setCursor(Qt.PointingHandCursor)
        cbtn.setFixedHeight(40)
        cbtn.setStyleSheet(button_qss("primary", "lg"))
        cbtn.clicked.connect(owner.copy_result)
        mrow.addWidget(owner.generate_btn, 3)
        mrow.addWidget(cbtn, 2)
        lay.addLayout(mrow)
        grid = QGridLayout(); grid.setSpacing(5)
        for i, (txt, fn) in enumerate([
            ("📥 Coletar", owner.start_collection), ("📊 Ver Dados", owner.show_data),
            ("💾 Exportar", owner.export_data), ("📋 Grupos", owner.show_groups_dialog),
            ("⚙️ Config.", owner.show_config_dialog), ("📱 Contas", owner.show_contas_dialog),
        ]):
            b = QPushButton(txt); b.setFixedHeight(36); b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(sec_btn_qss); b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.clicked.connect(fn)
            grid.addWidget(b, i // 3, i % 3)
        lay.addLayout(grid)
    left_lay.addWidget(card(build_acoes))

    # CARD RAPIDO
    def build_rapido(lay):
        lay.addWidget(sec_lbl("ACESSO RÁPIDO"))
        grid = QGridLayout(); grid.setSpacing(5)
        items = [("💳 Cartões",0,"#10b981"),("🏠 CEP",1,"#06b6d4"),
                 ("✅ CPF/CNPJ",4,"#8b5cf6"),("📧 Organizador",2,"#0ea5e9"),
                 ("⚡ Desempenho",5,"#fbbf24"),("✍️ Português",7,"#22d3ee")]
        for i, (txt, ti, color) in enumerate(items):
            b = QPushButton(txt); b.setFixedHeight(36); b.setCursor(Qt.PointingHandCursor)
            b.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            b.setStyleSheet(f"QPushButton{{background:rgba(6,182,212,0.05);color:{color};"
                           f"border:1px solid {color}28;border-radius:6px;font-size:11px;font-weight:600;}}"
                           f"QPushButton:hover{{background:{color}18;border-color:{color}55;}}")
            b.clicked.connect(lambda _, i=ti: owner.show_tools_tab(i))
            grid.addWidget(b, i // 3, i % 3)
        lay.addLayout(grid)
    left_lay.addWidget(card(build_rapido))

    owner.progress_bar = QProgressBar()
    owner.progress_bar.setVisible(False)
    owner.progress_bar.setFixedHeight(3)
    owner.progress_bar.setStyleSheet("QProgressBar{background:#0d1525;border:none;border-radius:1px;}"
                                    "QProgressBar::chunk{background:#06b6d4;border-radius:1px;}")
    owner.progress_bar.setTextVisible(False)
    left_lay.addWidget(owner.progress_bar)

    owner.stats_label = QLabel("—")
    owner.stats_label.setAlignment(Qt.AlignCenter)
    owner.stats_label.setStyleSheet(label_qss("muted") + f" color:{PALETTE.faint}; font-size:10px;")
    owner.stats_label.setWordWrap(True)
    left_lay.addWidget(owner.stats_label)
    left_lay.addStretch(1)

    left_scroll.setWidget(left_widget)
    splitter.addWidget(left_scroll)

    # === PAINEL DIREITO — RESULTADO ===
    right_widget = QWidget()
    right_widget.setStyleSheet("background:transparent;")
    right_lay = QVBoxLayout(right_widget)
    right_lay.setContentsMargins(6, 0, 0, 0)
    right_lay.setSpacing(6)
    right_lay.addWidget(sec_lbl("RESULTADO"))

    rc = QFrame()
    rc.setStyleSheet(card_qss("default", radius=8))
    rc.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
    rc_lay = QVBoxLayout(rc)
    rc_lay.setContentsMargins(12, 10, 12, 10)
    rc_lay.setSpacing(7)

    field_qss = ("QLabel{color:#22d3ee;font-family:'Consolas','Cascadia Code',monospace;"
                 "font-size:13px;font-weight:500;background:#07080f;"
                 "border:1px solid rgba(6,182,212,0.09);border-radius:7px;"
                 "padding:8px 12px;}")
    cp_qss = ("QPushButton{background:rgba(6,182,212,0.07);border:1px solid rgba(6,182,212,0.15);"
              "border-radius:6px;font-size:12px;color:#06b6d4;"
              "min-width:28px;max-width:28px;min-height:28px;max-height:28px;}"
              "QPushButton:hover{background:rgba(6,182,212,0.22);}")

    for icon, attr, label_txt in [
        ("👤","nome","Nome"), ("🆔","cpf","CPF"), ("🎂","idade","Idade"),
        ("📅","nasc","Nascimento"), ("📞","telefone","Telefone"), ("⭐","score","Score"),
    ]:
        row = QHBoxLayout(); row.setSpacing(8)
        lbl = QLabel(f"{icon}   {label_txt}: —")
        lbl.setStyleSheet(field_qss)
        lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        cp = QPushButton("⎘")
        cp.setStyleSheet(cp_qss); cp.setCursor(Qt.PointingHandCursor)
        cp.setToolTip(f"Copiar {label_txt}")
        cp.clicked.connect(lambda _, a=attr: owner.copy_field(a))
        row.addWidget(lbl, 1); row.addWidget(cp)
        rc_lay.addLayout(row)
        setattr(owner, f"{attr}_label", lbl)
    rc_lay.addStretch(1)

    right_lay.addWidget(rc, 1)
    splitter.addWidget(right_widget)

    splitter.setSizes([420, 580])
    splitter.setStretchFactor(0, 42)
    splitter.setStretchFactor(1, 58)
    root_lay.addWidget(splitter, 1)

    owner.nome_label.setText("👤   Nome: —")
    owner.cpf_label.setText("🆔   CPF: —")
    owner.idade_label.setText("🎂   Idade: —")
    owner.nasc_label.setText("📅   Nascimento: —")
    owner.telefone_label.setText("📞   Telefone: —")
    owner.score_label.setText("⭐   Score: —")

    return page
