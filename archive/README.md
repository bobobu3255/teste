# archive/

Pasta reservada para artefatos históricos e snapshots manuais que **não fazem parte do código de produção**.

## Política

- `archive/dev_backups/` é **ignorada pelo git** (`.gitignore`) — o histórico oficial é o próprio git.
- Arquivos colocados aqui ficam disponíveis apenas localmente, para consulta rápida durante refatorações.
- Antes de remover qualquer pasta de `dev_backups/`, confirme que não há referência ativa em código vivo.

## Como criar um backup pontual

```bash
mkdir -p archive/dev_backups/<feature>_<motivo>_$(date +%Y%m%d_%H%M%S)
cp -r app/features/<feature>/ archive/dev_backups/<feature>_<motivo>_$(date +%Y%m%d_%H%M%S)/
```

> Para revisões de PR ou auditorias, prefira `git log` / `git show` ao invés de criar cópias manuais.
