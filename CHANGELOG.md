# Changelog

Todas as mudanças notáveis deste projeto serão documentadas neste arquivo.

O formato segue [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/) e o projeto adota
[Semantic Versioning](https://semver.org/lang/pt-BR/).

---

## [Unreleased]

### Adicionado
- Identidade visual oficial do projeto (banner, logo e paleta em SVG).
- README profissional com hero, badges, tabela de features e navegação rápida.
- Documentação técnica em `docs/`: arquitetura, design system e estrutura.
- Arquivos de governança: `CHANGELOG`, `CONTRIBUTING`, `LICENSE`, `.editorconfig`, `.gitattributes`.

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
