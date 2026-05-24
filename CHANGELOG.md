# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota
[Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Unreleased]

### Adicionado
- **Reformulação visual completa do app (design rework v12)**:
  - `app/ui/components.py` ganha 21 novos símbolos: tokens `SPACING_*`, `RADIUS_*`,
    `TYPOGRAPHY`, `FONT_MONO`, helpers `accent_card_qss`, `divider_qss`, `pill_qss`,
    `make_pill`, `status_dot_qss`, `make_status_dot`, `kbd_qss`, `make_accent_card`,
    `make_status_row`. Glow simulado em `button_qss` no hover/focus.
  - `app/ui/app_theme.py` reescrito (sem remover seletores antigos):
    botões primários com gradient cyan, foco com borda 2px brilhante, novos seletores
    `QFrame#GlowCard`, `QFrame#NavSidebar`, `QFrame#HeaderBar`, `QFrame#FooterBar`,
    `QFrame#Divider`, `QPushButton[role="nav|ghost|icon"]`, `QLabel[variant="eyebrow|display"]`,
    `QLabel[role="kbd"]`, suporte completo a `QToolBar`, `QToolButton`, `QStatusBar`, `QSlider`.
  - `app/ui/app_motion.py` (NOVO): glow real via `QGraphicsDropShadowEffect`,
    sombras de elevação, fade-in animado, hover-glow filter.
  - `app/ui/splash.py` (NOVO): splash screen cyberpunk com logo hexagonal renderizado,
    barra de progresso animada e mensagens de bootstrap.
  - `app/ui/app_bootstrap.py`: paleta Qt sincronizada com o design system,
    fonte padrão configurada, `create_splash()` integrado.
- Identidade visual oficial do repositório (banner, logo e paleta em SVG).
- README profissional com hero, badges, tabela de features e navegação rápida.
- Documentação técnica em `docs/`: arquitetura, design system e estrutura.
- Arquivos de governança: `CHANGELOG`, `CONTRIBUTING`, `LICENSE`, `.editorconfig`, `.gitattributes`.

### Mudado
- Tipografia: `JetBrains Mono` (com fallback `Cascadia Code` / `Consolas`) agora
  é usada em headers de tabela, group titles, badges, status, kbd e logs.
- Estados de foco em campos: borda 2px `primary_light` (era 1px `border_strong`).
- Tabs selecionadas: ganham underline cyan brilhante de 2px.
- Sidebar: itens de navegação ganham barra cyan vertical + gradient horizontal sutil
  quando ativos.
- Progress bars e checkboxes ganham gradient cyan no preenchimento.

### Compatibilidade
- 100% retrocompatível. Todos os 25 símbolos da API legada e todos os seletores QSS
  pré-existentes foram preservados. As features podem opcionalmente adotar as novas
  variantes (`variant="eyebrow"`, `role="nav"`, etc.) sem alteração.

---

## [12.0-preview] — 2026-05-24

### Adicionado
- Núcleo modular em `app/core/`: `app_store`, `app_context`, fila de tarefas, eventos e relatório de saúde.
- Pacote `app/features/` com features auto-registráveis (browser, crunchyroll, ai_assistant, notepad, paramount_assist, temp_mail, etc.).
- Tema centralizado em `app/ui/app_theme.py` (Cyberpunk Neon).
- Pipeline de manutenção em `scripts/maintenance/` (smoke checks, structure guard, audit de estilos).
- Crash logger gráfico (fallback `QMessageBox`) em `run.py`.

### Mudado
- Reescrita visual completa: tema escuro premium com acentos cyan/teal, glow sutil e tipografia técnica.
- Janela principal migrada para arquitetura baseada em mixins (`MainLayoutMixin`, `MainPagesMixin`, `MainActionsMixin`, `MainWindowControlsMixin`, `MainStateMixin`).
- Tabs renomeadas e reorganizadas em `SimpleApp.TAB_TITLES`.

### Depreciado
- Pacotes `services/` e `ui/` (raiz) — substituídos por `app/services/` e `app/ui/`.
- `theme.py` (raiz) — substituído por `app/ui/app_theme.py`.
- `*_widget.py` (raiz) — agora são apenas shims para `app/features/<nome>/widget.py`.

### Removido
- Cores hard-coded espalhadas pelas features (centralizadas no tema).
- Código duplicado e módulos obsoletos identificados pela auditoria.

---

## [11.0]

### Adicionado
- Suite de coleta + ferramentas (gerador de pares, cartões, CEP, formatador, organizador, validador CPF/CNPJ).
- Navegador seguro com perfis isolados, fingerprint e proxy.
- Bots Crunchyroll (Node.js) integrados ao app via widgets dedicados.
- Cofre de senhas com `cryptography`.
- Build Windows via PyInstaller (`build_exe.py`).

---

[Unreleased]: https://github.com/bobobu3255/teste/compare/v12.0-preview...HEAD
[12.0-preview]: https://github.com/bobobu3255/teste/releases/tag/v12.0-preview
[11.0]: https://github.com/bobobu3255/teste/releases/tag/v11.0
