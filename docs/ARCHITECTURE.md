<div align="center">
  <img src="assets/banner.svg" alt="Telegram Collector Pro" width="100%"/>
</div>

# Arquitetura — v12.0

> Visão de alto nível de como a aplicação é organizada, como o estado flui e como as features se conectam ao núcleo.

---

## 1. Visão em camadas

```
┌──────────────────────────────────────────────────────────────────┐
│                         run.py  (bootstrap)                      │
│   verifica python · configura logging · captura crash fatal      │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                       app/ui  (shell)                            │
│   app_bootstrap · main_layout · main_actions · main_pages        │
│   shell_widgets · window_controls · app_theme · dialogs          │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                   app/features  (módulos UI)                     │
│  browser · crunchyroll · ai_assistant · notepad · temp_mail …    │
│  cada feature: widget.py · styles.py · (dialog.py opcional)      │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                    app/core  (núcleo)                            │
│  app_store · app_context · database · workers · worker_threads   │
│  config_manager · error_service · logger_manager · paths         │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
┌──────────────────────────────────────────────────────────────────┐
│                  app/services  (integrações)                     │
│  collector · proxy_manager · cloud_service · address_*           │
│  account_formatter · profile_defaults_manager                    │
└──────────────────────────────────────────────────────────────────┘
                                 │
                                 ▼
                         External · OS · Disk
                  (SQLite · Selenium · Telethon · Node)
```

## 2. Princípios

| Princípio | Como é aplicado |
|---|---|
| **Separação UI / domínio** | `app/ui` e `app/features` consomem `app/core` e `app/services`, nunca o contrário. |
| **Estado central** | `app/core/app_store.py` e `database.py` formam a "single source of truth" persistida em SQLite. |
| **Workers desacoplados** | `app/core/workers.py` + `worker_threads.py` isolam I/O pesado em `QThread`s, mantendo a UI fluida. |
| **Features auto-registráveis** | `app/features/registry.py` indexa cada módulo em `app/features/<nome>/` sem acoplamento explícito. |
| **Tema centralizado** | `app/ui/app_theme.py` é a única fonte de tokens visuais; cada feature define apenas seu `styles.py`. |
| **Falhas observáveis** | `error_service.py` instala um crash logger e `logger_manager.py` provê logs estruturados. |

## 3. Fluxo de inicialização

1. `run.py` valida o Python, configura logging e chama `main_app.main()`.
2. `main_app.SimpleApp` herda mixins de `app/ui/*` que montam a janela:
   - `MainLayoutMixin` — estrutura (sidebar + header + stack).
   - `MainPagesMixin` — registra cada página/feature.
   - `MainActionsMixin` — atalhos, ações de menu e tray.
   - `MainWindowControlsMixin` — controles de janela (compact/normal, sempre no topo, etc.).
   - `MainStateMixin` — restaura o estado salvo no app store.
3. `app_bootstrap.create_application` aplica `QApplication` + paleta global.
4. As features são instanciadas sob demanda quando a aba correspondente é aberta.

## 4. Camada de features

Cada feature segue o contrato:

```
app/features/<nome>/
├── __init__.py        # exporta o widget principal
├── widget.py          # QWidget raiz da aba (lógica + composição)
├── styles.py          # QSS específico da feature (consome tokens do tema)
└── dialog.py          # opcional — diálogos auxiliares
```

Regras:
- **Não acessam a UI shell diretamente.** Comunicação é feita via app store / sinais.
- **Não importam outras features.** Para fluxos cross-feature, usar serviços ou eventos.
- **Estilos usam tokens.** Cores hard-coded são proibidas — sempre referenciar `app_theme`.

## 5. Persistência e configuração

| Arquivo | Papel |
|---|---|
| `app/core/database.py` | Esquema SQLite, migrações, repositórios. |
| `app/core/app_store.py` | Estado de runtime + cache leve (settings, sessão UI). |
| `app/core/config_manager.py` | Leitura/escrita de configurações persistidas. |
| `app/core/paths.py` | Resolução de caminhos (data dir, logs, profiles). |
| `settings.py` | Constantes globais e `BASE_DIR`. |

## 6. Concorrência

- `QThread`-based workers em `app/core/worker_threads.py`.
- Tarefas longas são submetidas via `app/core/workers.py` (fila + relatório de progresso).
- A UI **nunca** bloqueia: callbacks são roteados via sinais Qt para a thread principal.

## 7. Observabilidade & saúde

A pasta `scripts/maintenance/` provê auditorias automatizadas:

| Script | Função |
|---|---|
| `health_check.py` | Smoke test geral do projeto. |
| `project_health_report.py` | Relatório consolidado de saúde. |
| `app_store_check.py` / `app_store_maintenance.py` | Sanity do app store. |
| `widget_smoke_check.py` | Verifica que cada widget de feature carrega. |
| `ui_style_audit.py` | Audita uso correto dos tokens do tema. |
| `structure_guard.py` | Garante que a estrutura modular não regrediu. |
| `verify_all.py` | Pipeline que executa todas as checagens acima. |

## 8. Pacotes legado

`services/` (raiz) e `ui/` (raiz) são pacotes **legado** mantidos para compatibilidade durante a migração para `app/`. Novos códigos devem ir em `app/services/` e `app/ui/`.

## 9. Diagrama de dependências (resumo)

```
run.py ──► main_app.py ──► app/ui/* ──► app/features/* ──► app/core/* ──► app/services/*
                                              │                  ▲
                                              └────── tema ◄─────┘
```

---

<div align="right">
  <sub>Arquitetura · v12.0 preview</sub>
</div>
