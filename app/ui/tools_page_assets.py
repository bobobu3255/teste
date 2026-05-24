#!/usr/bin/env python3
"""Textos e estilos da pagina Ferramentas."""

TOOLS_METADATA = [
    ("Cartoes", "Gere listas no formato numero, mes, ano e CVV."),
    ("CEP", "Gere enderecos e copie campos separados com rapidez."),
    ("Organizador", "Organize contas em modelos prontos para uso."),
    ("Formatar", "Formate e limpe listas de dados em massa."),
    ("CPF/CNPJ", "Valide e confira documentos brasileiros."),
    ("Desempenho", "Monitore hardware e rode acoes seguras de sistema."),
    ("Dados Pro", "Analise qualidade, higiene e enriquecimento de registros."),
    ("Portugues", "Corrija, reescreva e traduza textos com modos de portugues."),
    ("Paramount", "Organize contas, perfis, enderecos e fluxo visivel da Paramount."),
    ("Codigos", "Crie acessos temporarios e veja codigos de email pelo cPanel."),
    ("Leads Site", "Receba contatos enviados pela pagina inicial BOBOBU."),
    ("Email Temp", "Gere contas temporarias Mail.tm em lote e copie email:senha."),
]

TOOLS_TAB_QSS = """
    QTabWidget::pane { border: 1px solid rgba(34,211,238,0.10); border-radius: 12px; background: #05070d; margin-top: 8px; }
    QTabBar { background: #07080f; }
    QTabBar::tab {
        background: #101827; color: #94a3b8; min-height: 38px; min-width: 108px; padding: 8px 16px;
        margin-right: 6px; border: 1px solid rgba(148,163,184,0.12); border-top-left-radius: 10px;
        border-top-right-radius: 10px; font-size: 12px; font-weight: 800;
    }
    QTabBar::tab:selected { color: #67e8f9; background: #0b2c3a; border-color: rgba(34,211,238,0.42); }
    QTabBar::tab:hover:!selected { color: #e2e8f0; background: #111c2f; }
    QTabBar::scroller { width: 34px; }
    QTabBar QToolButton {
        background: #101827; border: 1px solid rgba(34,211,238,0.24); color: #67e8f9;
        border-radius: 8px; min-width: 28px; min-height: 28px;
    }
    QTabBar QToolButton:hover { background: rgba(34,211,238,0.16); }
"""

COUNTER_QSS = (
    "QLabel{background:#08111f;color:#67e8f9;border:1px solid rgba(34,211,238,0.16);"
    "border-radius:10px;padding:10px;font-weight:900;}"
)
