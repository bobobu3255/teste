# Extensões do Navegador

Este diretório contém as extensões do navegador para o Telegram Collector Pro.

## Extensões Incluídas

### 🛡️ Privacy Guard (Integrada)
Extensão de privacidade integrada que protege sua navegação:
- **Bloqueio de Trackers**: Bloqueia Google Analytics, Facebook Pixel, Hotjar, etc.
- **Anti-Fingerprinting**: Protege contra Canvas, WebGL e Audio fingerprinting
- **Remoção de Scripts**: Remove scripts de rastreamento automaticamente
- **Limpeza de Cookies**: Remove cookies de tracking conhecidos

## Como Adicionar Novas Extensões

1. Baixe a extensão descompactada (pasta com manifest.json)
2. Coloque a pasta neste diretório
3. No aplicativo, vá em **Config. Perfis > Extensões**
4. Clique em **Adicionar** e selecione a pasta da extensão

## Formatos Suportados

- **Pasta descompactada**: Pasta contendo `manifest.json`
- **Arquivo CRX**: Extensão empacotada do Chrome
- **Arquivo ZIP**: Extensão compactada

## Extensões Recomendadas

| Extensão | Descrição |
|----------|-----------|
| uBlock Origin | Bloqueador de anúncios |
| Privacy Badger | Bloqueador de trackers |
| HTTPS Everywhere | Força conexões HTTPS |
| Cookie AutoDelete | Remove cookies automaticamente |

## Notas

- Extensões adicionadas aqui serão instaladas automaticamente em novos perfis
- Você pode habilitar/desabilitar extensões individualmente
- A extensão Privacy Guard é integrada e não pode ser removida
