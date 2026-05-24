# Infraestrutura V11 -> V12 Core

Atualizacao: a base central abaixo agora e a fundacao do **V12 Core
(`v12.0 Preview`)**. O nome da pasta pode continuar como V11 por compatibilidade
com atalhos e arquivos antigos, mas a identidade do app foi centralizada em
`app/core/app_metadata.py`.

Esta fase criou uma base central para o projeto crescer sem virar um monte de
JSONs soltos e automacoes brigando entre si.

## O que entrou

- Estado central em SQLite: `app_data/app_state.sqlite3`.
- Tabela de estado chave/valor para resumos de ferramentas.
- Tabela de eventos para logs bonitos e diagnostico.
- Tabela de tarefas com fluxo: `pending`, `running`, `success`, `error`, `review`, `cancelled`.
- Tabela de entidades centrais: perfis, contas, favoritos, backups e proximas ferramentas.
- Verificador: `python scripts/maintenance/app_store_check.py`.
- Sincronizacao dos JSONs atuais: `python scripts/maintenance/sync_app_store.py`.
- Resumo/backup do SQLite central: `python scripts/maintenance/app_store_maintenance.py --backup --snapshot`.
- Relatorio geral de saude: `python scripts/maintenance/project_health_report.py`.
- Bateria geral atualizada: `python scripts/maintenance/verify_all.py --quick`.

Pela interface, esses comandos ficam em `Config > Manutencao`.

## Estrategia

A migracao deve ser gradual. As ferramentas atuais continuam lendo e gravando
seus arquivos como antes, mas podem publicar resumo, erros e tarefas no
`AppStore`. Assim a interface ganha dashboard, logs e fila sem trocar tudo de
uma vez.

## Compatibilidade

Os JSONs antigos continuam sendo gravados. O SQLite central recebe espelhos e
status organizados para dashboard, logs e fila. Se algum arquivo antigo for
necessario por uma ferramenta, ela ainda encontra o mesmo formato de antes.

## Proximas migracoes seguras

1. Navegador Seguro: publicar status fino de cookies, favoritos e ultimo erro por perfil.
2. Backup: registrar historico detalhado de restauracoes no AppStore.
3. Configuracoes: centralizar preferencias gerais no SQLite, mantendo JSON como
   compatibilidade por algumas versoes.
4. Design system: mover cores, tamanhos e botoes para componentes compartilhados.

## Entidades sincronizadas agora

- `browser_profile`: perfis do Navegador Seguro.
- `paramount_account`: contas do Paramount Assist.
- `favorite`: favoritos padrao dos perfis.
- `backup`: backups encontrados nas pastas principais.
