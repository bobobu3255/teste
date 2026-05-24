# Organizacao Segura Da V11

Este documento marca a base de organizacao do Telegram Pro V11 sem mudar o comportamento atual do app.

## O Que Foi Feito Agora

- `app/core/paths.py` centraliza caminhos importantes do projeto.
- `app/core/config_manager.py` guarda a configuracao de contas e grupos Telegram.
- `app/core/exceptions.py` guarda a hierarquia de excecoes customizadas.
- `app/core/logger_manager.py` guarda o logger legado centralizado.
- `app/core/workers.py` guarda workers Qt reutilizaveis.
- `app/core/database.py` guarda o banco de dados principal.
- `app/ui/app_theme.py` guarda o tema principal da interface.
- `app/ui/components.py` guarda botoes, cards, labels e campos reutilizaveis para padronizar o design, incluindo a tela Config.
- `app/ui/app_bootstrap.py` guarda criacao do QApplication, estilo Fusion e paleta inicial.
- `app/ui/dialogs.py` guarda dialogos pequenos usados pelo app principal.
- `app/ui/shell_widgets.py` guarda sidebar, header, status bar, painel compacto e constantes visuais.
- `app/ui/app_state.py` guarda estado inicial, banco ativo, refresh de banco e aviso de configuracao.
- `app/ui/main_pages.py` orquestra a ordem das paginas da janela principal.
- `app/ui/generator_page.py` guarda o builder da pagina Gerador de Pares.
- `app/ui/crunchyroll_page.py` guarda o builder e acoes da pagina Crunchyroll.
- `app/ui/tools_page.py` guarda o builder visual da pagina Ferramentas, com cabecalho e abas maiores.
- `app/ui/tools_page_assets.py` guarda textos e estilos da pagina Ferramentas.
- `app/ui/browser_page.py` guarda o builder da pagina Navegador Seguro.
- `app/ui/simple_pages.py` guarda os builders das paginas Inicio, IA Local, Notas e Config.
- `app/ui/main_actions.py` guarda acoes de geracao, copia, coleta, dialogs de coleta e exportacao.
- `app/ui/window_controls.py` guarda setup da janela, bandeja, tela cheia, modo compacto, persistencia e fechamento.
- `app/ui/main_layout.py` guarda montagem da interface, navegacao principal, atalhos globais e busca global.
- `app/core/worker_threads.py` guarda threads Qt usadas por coleta e geradores.
- `app/features/registry.py` documenta as ferramentas ativas sem importar a interface real.
- `app/features/extra_tools/` guarda CPF/CNPJ, Fake, Busca e Dashboard antigos.
- `app/features/data_pro/` guarda a ferramenta Dados Pro.
- `app/features/text_corrector/` guarda a ferramenta Portugues.
- `app/features/profile_defaults/` guarda favoritos, extensoes e senhas padrao dos perfis.
- `app/features/app_hub/` guarda painel inicial, busca global, logs e configuracoes gerais com componentes visuais padronizados.
- `app/features/app_hub/logs_panel.py` guarda a central de logs e mensagens amigaveis.
- `app/features/app_hub/settings_widget.py` guarda Configuracoes Gerais em abas internas, backup e preferencias.
- `app/features/app_hub/maintenance_panel.py` guarda o painel visual para rodar checks da V11 pela aba Config.
- `app/features/performance/` guarda a ferramenta Desempenho Pro.
- `app/features/performance/styles.py` guarda os estilos compartilhados do Desempenho Pro.
- `app/features/data_organizer/` guarda a ferramenta de organizar/formatar dados.
- `app/features/account_manager/` guarda o gerenciador de contas e grupos Telegram.
- `app/features/browser/` guarda o Navegador Seguro e seu manager.
- `app/features/browser/styles.py` guarda estilos compartilhados do Navegador Seguro.
- `app/features/ai_assistant/` guarda a IA Local.
- `app/features/ai_assistant/styles.py` guarda estilos compartilhados da IA Local.
- `app/features/notepad/` guarda o Bloco de Notas.
- `app/features/notepad/styles.py` guarda estilos compartilhados do Bloco de Notas.
- `app/features/crunchyroll/` guarda os bots Crunchyroll.
- `app/features/crunchyroll/styles.py` guarda estilos compartilhados dos bots Crunchyroll.
- `app/features/tools/` guarda o construtor das abas de ferramentas auxiliares.
- `app/features/tools/styles.py` guarda o primeiro pacote de estilos compartilhados das ferramentas internas.
- `app/services/account_formatter.py` guarda a logica de formatacao de contas.
- `app/services/address_generator.py` guarda a logica atual de geracao de enderecos.
- `app/services/address_reserve.py` guarda o banco local reserva de enderecos.
- `app/services/cloud_service.py` guarda a integracao opcional com cPanel/cloud.
- `app/services/profile_defaults_manager.py` guarda favoritos, extensoes e senhas padrao.
- `app/services/proxy_manager.py` guarda geracao e parse de proxies do navegador.
- `app/services/collector.py` guarda o coletor Telegram.
- `generators/` guarda geradores reutilizaveis como cartoes e fingerprint.
- `scripts/maintenance/health_check.py` verifica se os arquivos Python compilam e pode abrir a `SimpleApp` em modo de teste.
- `scripts/maintenance/bridge_check.py` verifica se as pontes antigas continuam apontando para os modulos reais.
- `scripts/maintenance/import_time_report.py` mede gargalos de import/inicializacao.
- `scripts/maintenance/widget_smoke_check.py` abre widgets principais em modo invisivel para detectar ferramenta quebrada rapidamente.
- `scripts/maintenance/ui_components_check.py` valida o kit visual compartilhado em modo invisivel.
- `scripts/maintenance/ui_style_audit.py` gera um relatorio de dividas visuais e possiveis pontos de travamento de UI.
- `scripts/maintenance/storage_report.py` mostra onde a V11 esta usando mais espaco sem apagar nada.
- `scripts/maintenance/safe_cleanup.py` lista e limpa apenas caches seguros, mantendo perfis, cookies, backups, banco, IA e dependencias protegidos.
- `scripts/maintenance/structure_guard.py` protege a organizacao da V11 conferindo arquivos essenciais, pontes, documentacao e tamanho dos orquestradores.
- `scripts/maintenance/verify_all.py` roda a bateria principal de manutencao em um unico comando.
- `archive/dev_backups/` guarda snapshots antigos que antes ficavam soltos na raiz.

## Arquivos Ponte

Alguns arquivos continuam na raiz apenas para compatibilidade com imports antigos:

- `extra_tools.py`
- `data_pro_widget.py`
- `text_corrector_widget.py`
- `profile_defaults_widget.py`
- `profile_defaults_manager.py`
- `app_hub.py`
- `performance_widget.py`
- `data_organizer.py`
- `account_manager.py`
- `config_manager.py`
- `exceptions.py`
- `logger_manager.py`
- `workers.py`
- `database.py`
- `collector.py`
- `theme.py`
- `browser_manager.py`
- `browser_widget.py`
- `ai_assistant_widget.py`
- `notepad_widget.py`
- `crunchyroll_widget.py`
- `crunchyroll_login_widget.py`
- `account_formatter.py`
- `address_generator.py`
- `address_reserve.py`
- `cloud_service.py`
- `proxy_manager.py`
- `card_generator.py`
- `fingerprint_generator.py`

Eles importam as classes reais dos pacotes em `app/`, `generators/` ou `services/`.

## Arquivos Que Continuam Na Raiz Por Seguranca

Estes arquivos ainda sao pontos de entrada ou configuracao e nao foram movidos nesta fase:

- `main_app.py` (agora como orquestrador compacto da janela principal; dialogs, threads, shell, bootstrap, estado, layout, paginas, acoes, controles de janela e ferramentas ja foram separados)
- `settings.py`
- `run.py`
- `build_exe.py`
- `address_extractor.py`

Tambem nao mover agora:

- `browser_profiles/`
- `browser_config/`
- `IA_Saidas/`
- `dados.db`
- `notepad_session.json`
- `notepad_snippets.json`
- pastas de bots e dados reais

## Plano Profissional De Organizacao

1. Manter a V11 funcionando exatamente como esta.
2. Centralizar caminhos, logs e configuracoes compartilhadas em `app/core`.
3. Criar registros leves em `app/features` antes de mover qualquer ferramenta.
4. Extrair uma ferramenta por vez para pacotes menores, sempre testando depois.
5. Criar componentes visuais reutilizaveis para botoes, cards, abas e formularios.
6. So depois disso reduzir o tamanho do `main_app.py`.

## Regra De Ouro

Nada de mover modulo grande sem teste. Primeiro documenta, cria ponte segura, testa, e so depois migra uma parte pequena.
