<div align="center">
  <img src="assets/banner.svg" alt="Telegram Collector Pro" width="100%"/>
</div>

# Estrutura do Projeto

> Mapa de pastas, convenções de nomenclatura e responsabilidade de cada módulo.

---

## Árvore principal

```
TelegramCollectorPro/
├── run.py                          # bootstrap + crash handler
├── main_app.py                     # janela principal (mixins)
├── settings.py                     # constantes globais (BASE_DIR, etc.)
├── build_exe.py                    # empacotamento PyInstaller
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
│
├── app/                            # ← núcleo modular (v12)
│   ├── __init__.py
│   ├── core/                       # estado, banco, workers, logger
│   ├── features/                   # módulos UI auto-registráveis
│   ├── services/                   # integrações de domínio
│   └── ui/                         # shell, layout, tema, diálogos
│
├── docs/                           # documentação técnica
│   ├── assets/                     # banner, logo, paleta (SVG)
│   ├── ARCHITECTURE.md
│   ├── DESIGN_SYSTEM.md
│   └── PROJECT_STRUCTURE.md
│
├── generators/                     # geradores standalone (cartão, fingerprint, endereço)
├── scripts/maintenance/            # auditorias, smoke checks, manutenção
├── services/                       # ⚠ legado — migrar para app/services/
├── ui/                             # ⚠ legado — migrar para app/ui/
├── _HOSPEDAR_CPANEL_*/             # artefatos de deploy do site companion
└── archive/                        # backups históricos (não-código de produção)
```

## `app/core/` — núcleo

| Arquivo | Responsabilidade |
|---|---|
| `app_context.py` | Contexto compartilhado entre features. |
| `app_metadata.py` | Versão, nome, build info. |
| `app_store.py` | Single source of truth de runtime. |
| `database.py` | Esquema SQLite, migrações, repositórios. |
| `clipboard_service.py` | Operações com clipboard centralizadas. |
| `config_manager.py` | Leitura/escrita de configuração persistida. |
| `error_service.py` | Crash logger e captura de erros fatais. |
| `exceptions.py` | Exceções de domínio. |
| `logger_manager.py` | Logger estruturado por módulo. |
| `paths.py` | Resolução de caminhos do app. |
| `workers.py` / `worker_threads.py` | Fila de tarefas + execução em thread. |

## `app/features/<nome>/` — features

Contrato de cada feature:

```
app/features/<nome>/
├── __init__.py        # expõe o widget principal
├── widget.py          # QWidget raiz
├── styles.py          # QSS local (consome tokens do tema)
└── dialog.py          # opcional
```

**Registry:** `app/features/registry.py` indexa todos os módulos. Para criar uma nova feature:

1. Criar a pasta seguindo o contrato acima.
2. Registrar no `registry.py`.
3. Adicionar o título da aba em `main_app.SimpleApp.TAB_TITLES`.
4. Implementar a página em `app/ui/main_pages.py` se precisar de roteamento custom.

## `app/services/` — serviços de domínio

| Módulo | O que faz |
|---|---|
| `account_formatter.py` | Formatação de contas em vários formatos. |
| `address_generator.py` / `address_reserve.py` | Geração e reserva de endereços. |
| `cloud_service.py` | Integração com armazenamento em nuvem. |
| `collector.py` | Pipeline de coleta principal. |
| `profile_defaults_manager.py` | Perfis-padrão de navegador. |
| `proxy_manager.py` | Gestão de proxies. |

## `app/ui/` — shell

| Arquivo | Responsabilidade |
|---|---|
| `app_bootstrap.py` | Cria `QApplication`, aplica paleta global. |
| `app_theme.py` | **Única** fonte de tokens visuais. |
| `app_state.py` | Mixin de estado da janela principal. |
| `main_layout.py` | Estrutura (sidebar + header + stack). |
| `main_pages.py` | Roteamento e ciclo de vida das páginas. |
| `main_actions.py` | Atalhos, menus e ações de tray. |
| `window_controls.py` | Controles de janela (compact/normal, on top). |
| `shell_widgets.py` | Componentes do shell (sidebar, header, etc.). |
| `components.py` | Componentes UI reutilizáveis. |
| `dialogs.py` | Diálogos genéricos. |
| `*_page.py` | Páginas específicas (browser, crunchyroll, tools, ...). |

## `scripts/maintenance/` — saúde do projeto

Pipeline de auditoria que pode ser executado manualmente ou em CI:

```bash
python scripts/maintenance/verify_all.py
```

Inclui: health check, structure guard, app store check, widget smoke, audit de estilos e relatório de armazenamento.

## Convenções

### Naming

- Módulos Python: `snake_case`.
- Classes: `PascalCase`.
- Constantes: `UPPER_SNAKE`.
- Arquivos de feature: sempre `widget.py`, `styles.py`, `dialog.py`.

### Imports

- **Absolutos** sempre (`from app.core.database import ...`).
- **Sem imports cruzados entre features.** Use serviços ou eventos.
- **`app/ui` consome `app/core` e `app/services`**, nunca o contrário.

### Estilos

- Cores: **proibido** hard-coded. Sempre via `app_theme`.
- QSS por feature em `<feature>/styles.py`.
- Selectores genéricos no tema, específicos na feature.

### Logs

- Sempre via `logger_manager.get_logger(__name__)`.
- `print()` é proibido em código de produção (somente em scripts utilitários).

## Arquivos & pastas legado

| Item | Status | Ação recomendada |
|---|---|---|
| `services/` (raiz) | legado | mover gradualmente para `app/services/` |
| `ui/` (raiz) | legado | mover gradualmente para `app/ui/` |
| `theme.py` (raiz) | legado | substituído por `app/ui/app_theme.py` |
| `*_widget.py` (raiz) | shims | mantêm compatibilidade; novo código em `app/features/` |

---

<div align="right">
  <sub>Estrutura · v12.0 preview</sub>
</div>
