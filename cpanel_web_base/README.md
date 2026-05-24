# Base cPanel para Telegram Pro V11

Esta pasta e uma base para subir no seu cPanel/domino.

## Como usar

1. Entre no cPanel.
2. Abra o Gerenciador de Arquivos.
3. Va em `public_html`.
4. Envie a pasta `v11` que esta dentro de `public_html`.
5. Acesse:

`https://bobobu.com.br/v11/api/ping.php`

Se aparecer `ok`, a base esta funcionando.

## Arquivos principais

- `version.json`: versao atual do app e link de download.
- `ai_models.json`: catalogo de modelos recomendados para IA.
- `prompts.json`: prompts/instrucoes que o app pode sincronizar.
- `api/ping.php`: teste simples.
- `api/log.php`: recebe logs tecnicos do app.

## Seguranca

Antes de usar logs online:

1. Abra `public_html/v11/api/config.php`.
2. Troque `CHANGE_ME_STRONG_KEY` por uma chave sua.
3. Coloque a mesma chave no V11 quando configurarmos a tela de nuvem.

Nao envie contas, senhas, cartoes, banco de dados ou informacoes sensiveis sem criptografia local.

