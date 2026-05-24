# Crunchyroll Login Bot v1.0.0

Bot que faz **LOGIN em contas existentes** e testa cartões. Diferente do bot principal que cria contas novas.

## 📋 Características

- **Login em contas existentes** (email:senha)
- **Teste de até 3 cartões por conta**
- **3 navegadores simultâneos** (configurável de 1 a 5)
- **Remoção automática** de contas/cartões processados
- **Detecção de contas já assinantes**
- **Sistema anti-detecção** com Puppeteer Stealth

## 📁 Estrutura de Arquivos

```
crunchyroll_login_bot/
├── config/
│   └── settings.js       # Configurações do bot
├── lib/
│   ├── helpers/
│   │   ├── logger.js         # Sistema de logs
│   │   ├── page-helpers.js   # Helpers de página
│   │   ├── cookie-handler.js # Tratamento de cookies
│   │   ├── file-helpers.js   # Helpers de arquivo
│   │   ├── queue-manager.js  # Gerenciador de filas
│   │   └── data-manager.js   # Gerenciador de dados
│   ├── worker.js         # Worker (navegador)
│   └── orchestrator.js   # Orquestrador de workers
├── data/
│   ├── contas.txt        # Contas para login (email:senha)
│   ├── cartoes.txt       # Cartões para teste
│   ├── contas_premium.txt    # Resultados: contas premium
│   ├── login_sucesso.txt     # Resultados: login OK
│   ├── login_falha.txt       # Resultados: login falhou
│   ├── cartoes_aprovados.txt # Resultados: cartões aprovados
│   └── cartoes_falhos.txt    # Resultados: cartões recusados
├── logs/                 # Logs do bot
├── index.js              # Arquivo principal
└── package.json          # Dependências
```

## 🚀 Como Usar

### 1. Instalar Dependências

```bash
cd crunchyroll_login_bot
npm install
```

### 2. Preparar Arquivos

**data/contas.txt** - Contas para login:
```
email1@exemplo.com:senha123
email2@exemplo.com|senha456
```

**data/cartoes.txt** - Cartões para teste:
```
4111111111111111|12|2025|123
5500000000000004|06|2026|456
```

### 3. Executar

```bash
# Com 3 navegadores (padrão)
npm start

# Com 1 navegador
npm run start:1

# Com 5 navegadores
npm run start:5

# Personalizado
NUM_WORKERS=4 node index.js
```

## ⌨️ Controles

- **Q** ou **Ctrl+C** - Parar todos os navegadores

## 📊 Fluxo de Processamento

1. **Login** - Faz login na conta existente
2. **Verificação** - Verifica se já é assinante
3. **Pagamento** - Navega para página de pagamento
4. **Teste de Cartões** - Testa até 3 cartões
5. **Resultado** - Registra sucesso ou falha

## 📝 Arquivos de Resultado

| Arquivo | Descrição |
|---------|-----------|
| `contas_premium.txt` | Contas que viraram premium (completo) |
| `contas_premium_simples.txt` | Contas premium (email:senha) |
| `login_sucesso.txt` | Contas com login OK |
| `login_falha.txt` | Contas com login falhou |
| `cartoes_aprovados.txt` | Cartões aprovados |
| `cartoes_falhos.txt` | Cartões recusados |
| `ja_assinante.txt` | Contas que já eram assinantes |
| `sem_pagamento.txt` | Contas sem cartão aprovado |

## ⚙️ Configurações

Edite `config/settings.js` para personalizar:

```javascript
// Limites
MAX_CARDS_PER_ACCOUNT: 3,  // Máximo de cartões por conta
MAX_PAGE_RELOADS: 5,       // Máximo de reloads por conta

// Timeouts
PAGE_TIMEOUT_MS: 60000,    // Timeout de página (60s)

// Delays
DELAYS: {
  AFTER_PAGE_LOAD: 3000,   // Após carregar página
  BETWEEN_ACCOUNTS: 3000,  // Entre contas
  // ...
}
```

## 🔧 Diferenças do Bot Principal

| Característica | Bot Principal | Bot Login |
|---------------|---------------|-----------|
| Cria contas | ✅ Sim | ❌ Não |
| Faz login | ⚠️ Se conta existir | ✅ Sempre |
| Testa cartões | ✅ Sim | ✅ Sim |
| Detecta já assinante | ❌ Não | ✅ Sim |

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs em `logs/`
2. Verifique os arquivos de resultado em `data/`
3. Verifique se as dependências estão instaladas
