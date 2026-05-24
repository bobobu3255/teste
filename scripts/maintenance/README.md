# Scripts De Manutencao

Scripts desta pasta servem para conferir a saude do projeto antes e depois de mexer em arquivos importantes.

## Verificacao Rapida

```powershell
python scripts\maintenance\health_check.py
```

## Verificacao Com Abertura Da Interface

```powershell
python scripts\maintenance\health_check.py --ui
```

O modo `--ui` usa `QT_QPA_PLATFORM=offscreen`, entao ele testa a criacao da janela sem precisar abrir a tela.

## Verificar Arquivos Ponte

```powershell
python scripts\maintenance\bridge_check.py
```

Use isso depois de mover arquivos para confirmar que imports antigos continuam funcionando.

## Relatorio De Tempo De Import

```powershell
python scripts\maintenance\import_time_report.py
```

Ajuda a descobrir quais modulos deixam a inicializacao mais pesada.

## structure_guard.py

Confere se a organizacao segura do V12 Core continua valida: arquivos essenciais, tamanho dos orquestradores, pontes antigas e documentacao. Use depois de mover/refatorar qualquer ferramenta.

Exemplo:

```powershell
python scripts/maintenance/structure_guard.py
```

## verify_all.py

Roda a bateria principal de seguranca do V12 Core: estrutura, compilacao/UI, pontes, kit visual, widgets e relatorio de imports.

Exemplo completo:

```powershell
python scripts/maintenance/verify_all.py
```

Exemplo rapido:

```powershell
python scripts/maintenance/verify_all.py --quick
```

