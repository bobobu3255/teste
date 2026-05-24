# Roadmap Seguro Do V12 Core

Este plano existe para melhorar o projeto sem repetir o erro de reescrever tudo de uma vez.

## Estado Atual

- Base principal reorganizada em `app/core`, `app/ui`, `app/features` e `app/services`.
- Pontes antigas mantidas para nao quebrar imports existentes.
- Checks de manutencao criados para testar estrutura, UI, ferramentas, imports e dividas visuais.
- Kit visual compartilhado iniciado em `app/ui/components.py`.
- Ferramentas internas come?aram a receber estilos centralizados em `app/features/tools/styles.py`.
- Desempenho Pro comecou a migrar estilos para `app/features/performance/styles.py`.
- Bloco de Notas comecou a migrar estilos para `app/features/notepad/styles.py`.
- IA Local comecou a migrar estilos para `app/features/ai_assistant/styles.py`.
- Navegador Seguro comecou a migrar estilos para `app/features/browser/styles.py`.
- Crunchyroll comecou a migrar estilos para `app/features/crunchyroll/styles.py`.
- Auditoria de espaco criada em `scripts/maintenance/storage_report.py` para controlar crescimento de perfis, backups e caches sem apagar nada.
- Limpeza segura criada em `scripts/maintenance/safe_cleanup.py`, com simulacao padrao e protecao de perfis/cookies/backups.

## Fases Restantes Estimadas

1. Polimento visual por ferramenta: corrigir botoes, cards, espacamentos e telas poluidas uma por vez.
2. Otimizacao de travamentos: remover operacoes pesadas do thread principal e melhorar exclusao/refresh de listas.
3. Inteligencia local: fortalecer IA, criacao de arquivos, leitura de anexos e acoes assistidas com seguranca.
4. Navegador Seguro: limpar interface, melhorar preenchimento automatico, detector de erro e perfis arquivados.
5. Ferramentas especificas: Cartoes, CEP, Desempenho, Notas e Crunchyroll com passagens focadas.
6. Empacotamento e launcher: abrir sem CMD, reparar dependencias e preparar uso em pendrive/PC novo.
7. QA final: bateria completa, revisao visual, backup e documentacao simples para uso.

## Criterio De Qualidade

Cada fase deve ter backup, mudanca pequena, teste rapido e, quando possivel, `verify_all.py` completo.
