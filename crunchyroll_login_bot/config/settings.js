/**
 * @fileoverview Configurações do Bot Crunchyroll Login
 * @module config/settings
 * @version 1.0.0
 * 
 * @description
 * Bot que faz login em contas existentes e testa cartões.
 * Diferente do bot principal que cria contas novas.
 */

// ============================================
// CONFIGURAÇÕES PRINCIPAIS
// ============================================

export const CONFIG = {
  VERSION: '1.0.0',
  
  // PROXY SETTINGS (Charles Proxy / HTTP Proxy)
  // Configurar via variáveis de ambiente ou diretamente aqui
  PROXY: {
    ENABLED: process.env.PROXY_ENABLED === 'true' || false,
    HOST: process.env.PROXY_HOST || '127.0.0.1',
    PORT: process.env.PROXY_PORT || '8888',  // Charles Proxy padrão
    USERNAME: process.env.PROXY_USERNAME || '',
    PASSWORD: process.env.PROXY_PASSWORD || '',
    // Ignorar erros de certificado SSL (necessário para Charles Proxy)
    IGNORE_SSL_ERRORS: process.env.PROXY_IGNORE_SSL === 'true' || true
  },
  
  // TIMEOUTS
  GLOBAL_TIMEOUT_MS: 10 * 60 * 1000, // 10 minutos
  PAGE_TIMEOUT_MS: 60000, // 60 segundos
  ELEMENT_TIMEOUT_MS: 30000, // 30 segundos
  
  // LIMITES
  MAX_CARDS_PER_ACCOUNT: 3, // Máximo de cartões por conta
  MAX_PAGE_RELOADS: 5, // Máximo de reloads por conta
  MAX_CONSECUTIVE_ERRORS: 5, // Máximo de erros antes de reiniciar browser

  // Pagamento/cartoes
  // Modo seguro por padrao: verifica login e organiza dados locais,
  // sem automatizar envio de cartao em site real.
  PAYMENT: {
    AUTO_SUBMIT_CARDS: process.env.CRUNCHYROLL_ALLOW_PAYMENT_AUTOMATION === 'true'
  },
  
  // URLs
  URLS: {
    LOGIN: 'https://sso.crunchyroll.com/login',
    PAGAMENTO: 'https://www.crunchyroll.com/pt-br/premium/fan/checkout?plan=fan_monthly',
    HOME: 'https://www.crunchyroll.com/pt-br/',
    PERFIL: 'https://www.crunchyroll.com/pt-br/account/profile'
  },
  
  // DELAYS (em ms)
  DELAYS: {
    AFTER_PAGE_LOAD: 3000,
    AFTER_CLICK: 1000,
    BETWEEN_FIELDS: 500,
    AFTER_SUBMIT: 5000,
    BETWEEN_ACCOUNTS: 3000,
    AFTER_SELECT_CARD: 2000,
    TYPING_MIN: 50,
    TYPING_MAX: 150,
    BETWEEN_WORKERS: 2000
  }
};

// ============================================
// SELETORES CSS
// ============================================

export const SELECTORS = {
  // Autenticação (Login)
  AUTH: {
    EMAIL_INPUT: 'input[name="username"], input[type="email"], input[name="email"], input[autocomplete="username"], #email, #username',
    PASSWORD_INPUT: 'input[name="password"], input[type="password"], input[autocomplete="current-password"], #password',
    SUBMIT_BUTTON: 'button[type="submit"], input[type="submit"]'
  },
  
  // Botões
  BUTTONS: {
    PROXIMO: ['Próximo', 'Next', 'Continuar', 'Continue', 'Avançar'],
    ENTRAR: ['Entrar', 'Login', 'Log In', 'Sign In', 'Acessar'],
    FINALIZAR: ['Concluir compra', 'Finalizar', 'Complete Purchase', 'Submit', 'Confirmar']
  },
  
  // Método de Pagamento
  PAYMENT_METHOD: {
    CARD_HEADER: 'h3[class*="_header_"], div[class*="payment-method"], label[class*="payment"]',
    CARD_TEXTS: ['Cartão de Crédito', 'Credit Card', 'Cartão', 'Card', 'Crédito ou Débito'],
    CARD_RADIO: 'input[type="radio"][value*="card"], input[type="radio"][name*="payment"]'
  },
  
  // Formulário de Cartão
  CARD_FORM: {
    // Campos principais
    NAME: 'input[name*="name"], input[id*="name"], input[autocomplete="cc-name"], input[placeholder*="nome"], input[placeholder*="Name"]',
    CPF: 'input[name*="cpf"], input[id*="cpf"], input[name*="document"], input[placeholder*="CPF"]',
    NUMBER: 'input[name*="number"], input[id*="number"], input[autocomplete="cc-number"], input[placeholder*="número"], input[placeholder*="Number"]',
    EXPIRY: 'input[name*="expir"], input[id*="expir"], input[autocomplete="cc-exp"], input[placeholder*="validade"]',
    EXPIRY_MONTH: 'input[name*="month"], select[name*="month"], input[placeholder*="MM"]',
    EXPIRY_YEAR: 'input[name*="year"], select[name*="year"], input[placeholder*="AA"], input[placeholder*="YY"]',
    CVV: 'input[name*="cvv"], input[name*="cvc"], input[name*="security"], input[autocomplete="cc-csc"], input[placeholder*="CVV"], input[placeholder*="CVC"]',
    
    // Seletores alternativos por iframe
    IFRAME: 'iframe[name*="card"], iframe[src*="payment"], iframe[id*="card"]'
  },
  
  // Cookies
  COOKIES: {
    BANNER: '#onetrust-banner-sdk, .onetrust-pc-dark-filter, [class*="cookie-banner"], [class*="consent"]',
    ACCEPT_BUTTON: '#onetrust-accept-btn-handler, button[class*="accept"], button[class*="consent"]',
    CLOSE_BUTTON: '.onetrust-close-btn-handler, button[class*="close"]'
  }
};

// ============================================
// INDICADORES DE RESULTADO
// ============================================

export const INDICATORS = {
  // Login bem-sucedido
  LOGIN_SUCCESS: [
    'bem-vindo',
    'welcome',
    'minha conta',
    'my account',
    'perfil',
    'profile',
    'sair',
    'logout',
    'assistir',
    'watch'
  ],
  
  // Login falhou
  LOGIN_FAILED: [
    'senha incorreta',
    'incorrect password',
    'wrong password',
    'credenciais inválidas',
    'invalid credentials',
    'não encontrada',
    'not found',
    'tente novamente',
    'try again',
    'erro ao entrar',
    'login failed',
    'usuário ou senha',
    'email ou senha'
  ],
  
  // Pagamento aprovado
  PAYMENT_SUCCESS: [
    'parabéns',
    'congratulations',
    'assinatura ativada',
    'subscription activated',
    'bem-vindo ao premium',
    'welcome to premium',
    'pagamento aprovado',
    'payment approved',
    'compra realizada',
    'purchase complete',
    'obrigado',
    'thank you',
    'obrigado por ser membro',
    'thank you for being a member',
    'mega fan membership',
    'fan membership',
    'você evoluiu',
    'you evolved',
    'assinatura confirmada',
    'subscription confirmed',
    'premium ativo',
    'premium active',
    'você maximizou seu fandom',
    'you maximized your fandom',
    'aproveite suas vantagens',
    'enjoy your benefits',
    'membro premium',
    'premium member'
  ],
  
  // Pagamento recusado
  PAYMENT_FAILED: [
    'pagamento recusado',
    'payment declined',
    'cartão recusado',
    'card declined',
    'transação negada',
    'transaction denied',
    'erro no pagamento',
    'payment error',
    'tente outro cartão',
    'try another card',
    'dados inválidos',
    'invalid data',
    'não autorizado',
    'not authorized'
  ],
  
  // Conta já tem assinatura
  ALREADY_SUBSCRIBED: [
    'já possui assinatura',
    'already subscribed',
    'assinatura ativa',
    'active subscription',
    'você já é premium',
    'you are already premium'
  ],
  
  // Página de erro
  ERROR_PAGE: {
    ENABLED: true,
    URL_PATTERNS: ['/error', '/500', '/404', '/503'],
    URL_WHITELIST: ['/login', '/checkout', '/premium', '/payment'],
    TEXT_PATTERNS: ['erro 500', 'error 500', 'internal server error', 'página não encontrada']
  }
};

// ============================================
// USER AGENTS
// ============================================

const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15'
];

export function getRandomUserAgent() {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

// ============================================
// CONFIGURAÇÃO DO BROWSER
// ============================================

// Função para obter argumentos do browser com proxy
export function getBrowserArgs() {
  const baseArgs = [
    '--no-sandbox',
    '--disable-setuid-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--disable-infobars',
    '--window-size=1366,768',
    '--start-maximized',
    '--disable-web-security',
    '--disable-features=IsolateOrigins,site-per-process',
    '--lang=pt-BR'
  ];
  
  // Adicionar configurações de proxy se habilitado
  if (CONFIG.PROXY.ENABLED) {
    const proxyUrl = `${CONFIG.PROXY.HOST}:${CONFIG.PROXY.PORT}`;
    baseArgs.push(`--proxy-server=http://${proxyUrl}`);
    
    // Ignorar erros de certificado SSL (necessário para Charles Proxy)
    if (CONFIG.PROXY.IGNORE_SSL_ERRORS) {
      baseArgs.push('--ignore-certificate-errors');
      baseArgs.push('--ignore-ssl-errors');
      baseArgs.push('--allow-insecure-localhost');
    }
    
    console.log(`[PROXY] Configurado: http://${proxyUrl}`);
  }
  
  return baseArgs;
}

export const BROWSER_CONFIG = {
  headless: false,
  defaultViewport: null,
  ignoreDefaultArgs: ['--enable-automation'],
  args: getBrowserArgs()
};

export default CONFIG;
