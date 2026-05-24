# V12 Core Checklist

Este documento marca a transicao segura para V12 sem reescrever o projeto do
zero. A ideia e manter as ferramentas funcionando, mas criar uma base mais facil
de corrigir, testar e expandir.

## Status atual

- Identidade central do app em `app/core/app_metadata.py`.
- Titulo da janela, bandeja e rodape usando `v12.0 Preview`.
- SQLite central em `app_data/app_state.sqlite3`.
- Estado chave/valor para resumos gerais.
- Eventos centralizados para logs.
- Fila de tarefas com status: `pending`, `running`, `success`, `error`,
  `review`, `cancelled`.
- Entidades centrais para perfis, contas, favoritos e backups.
- Dashboard, busca global e logs lendo parte do estado central.
- Manutencao visual em `Config > Manutencao`.
- Bateria de verificacao com `python scripts/maintenance/verify_all.py --quick`.

## Antes de chamar de V12 final

1. Padronizar o design system em todas as ferramentas visiveis.
2. Migrar gradualmente JSONs criticos para SQLite, mantendo compatibilidade.
3. Fazer Paramount, Navegador Seguro, IA, Notas e Desempenho publicarem status
   completo na fila central.
4. Validar visualmente as telas principais em resolucao normal e compacta.
5. Criar rotina clara de backup/restauracao do estado central.
6. Melhorar o launcher/reinicio para aplicar atualizacoes sem confundir o uso.
7. Criar testes pequenos para fluxos que ja quebraram: copiar no painel
   compacto, preencher endereco, abrir perfil, remover perfil e salvar notas.

## Como verificar agora

```powershell
python scripts\maintenance\sync_app_store.py
python scripts\maintenance\project_health_report.py
python scripts\maintenance\verify_all.py --quick
```

Se esses comandos passarem, o projeto esta em estado bom para continuar
evoluindo como V12 Core.
