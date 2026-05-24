# Crunchyroll Bot v6.2.0 - Parallel & Lite Edition

Bot automatizado para Crunchyroll com suporte a múltiplos navegadores e remoção automática de dados.

## 🚀 Novidades da v6.2.0

- **Processamento Paralelo**: 3 navegadores executando ao mesmo tempo (Velocidade 3x).
- **Modo Lite**: Versão otimizada para computadores com pouca memória RAM.
- **Remoção Automática**: Contas e cartões são removidos da interface e dos arquivos após o uso.
- **Rotação de User-Agents**: 15 User-Agents diferentes com sistema de remoção após uso.
- **Sistema de Filas**: Gerenciamento inteligente para evitar que dois navegadores usem o mesmo dado.

## 🛠️ Modos de Execução

### 1. Modo Paralelo (Recomendado)
Executa 3 navegadores simultaneamente. Ideal para quem tem 8GB+ de RAM.
```bash
npm start
# ou
npm run parallel
```

### 2. Modo Lite (Single)
Executa apenas 1 navegador. Ideal para computadores mais simples ou com pouca RAM.
```bash
npm run single
```

## 📁 Estrutura do Projeto

- `index.js`: Arquivo principal do Modo Paralelo.
- `index_single.js`: Arquivo principal do Modo Lite.
- `config/settings.js`: Central de configurações e seletores.
- `lib/helpers/queue-manager.js`: Gerenciador de filas para o modo paralelo.
- `lib/helpers/file-helpers.js`: Responsável pela remoção automática de dados.

## ⚙️ Configurações (settings.js)

Você pode ajustar os seguintes parâmetros:
- `MAX_PAGE_RELOADS`: Quantas vezes tentar recarregar a página por cartão.
- `MAX_CARDS_PER_ACCOUNT`: Limite de cartões testados por conta.
- `DELAYS`: Ajuste de velocidade entre cliques e digitação.

## 📝 Como usar

1. Coloque suas contas em `data/contas.txt` (email|senha).
2. Coloque seus cartões em `data/cartoes.txt` (numero|mes|ano|cvv).
3. Execute `npm install` para instalar as dependências.
4. Escolha o modo (start ou single) e execute.

---
**Desenvolvido para máxima eficiência e discrição.**
