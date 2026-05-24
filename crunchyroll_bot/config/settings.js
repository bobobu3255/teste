/**
 * @fileoverview Configurações Centralizadas do Bot Crunchyroll
 * @module config/settings
 * @version 9.2.0
 * 
 * @description
 * Este módulo contém todas as configurações do bot, incluindo timeouts,
 * limites, seletores CSS, indicadores de sucesso/falha e configurações
 * de proxy. Todas as configurações são exportadas como constantes imutáveis.
 * 
 * @example
 * import CONFIG, { SELECTORS, INDICATORS } from './config/settings.js';
 * 
 * // Usar configurações
 * const timeout = CONFIG.PAGE_TIMEOUT_MS;
 * const emailSelector = SELECTORS.AUTH.EMAIL_INPUT;
 */

// ============================================
// TIPOS E INTERFACES (JSDoc)
// ============================================

/**
 * @typedef {Object} DelayConfig
 * @property {number} AFTER_PAGE_LOAD - Delay após carregar página (ms)
 * @property {number} AFTER_CLICK - Delay após clicar em elemento (ms)
 * @property {number} BETWEEN_FIELDS - Delay entre campos (ms)
 * @property {number} AFTER_SUBMIT - Delay após submeter formulário (ms)
 * @property {number} BETWEEN_ACCOUNTS - Delay entre contas (ms)
 * @property {number} AFTER_SELECT_CARD - Delay após selecionar cartão (ms)
 * @property {number} TYPING_MIN - Delay mínimo de digitação (ms)
 * @property {number} TYPING_MAX - Delay máximo de digitação (ms)
 * @property {number} BETWEEN_WORKERS - Delay entre workers (ms)
 */

/**
 * @typedef {Object} StateConfig
 * @property {number} maxRetries - Número máximo de tentativas
 * @property {number} timeout - Timeout em milissegundos
 * @property {number} [waitAfterNavigation] - Espera após navegação
 * @property {number} [pollInterval] - Intervalo de polling
 * @property {number} [waitAfterSelect] - Espera após seleção
 * @property {number} [delayBetweenFields] - Delay entre campos
 * @property {number} [waitBeforeClick] - Espera antes de clicar
 * @property {number} [maxPolls] - Máximo de polls
 */

/**
 * @typedef {Object} ProxyConfig
 * @property {boolean} ENABLED - Se proxy está habilitado
 * @property {string} HOST - Host do proxy
 * @property {number} PORT - Porta do proxy
 * @property {string} USERNAME - Usuário do proxy
 * @property {string} PASSWORD - Senha do proxy
 * @property {string} TYPE - Tipo de proxy (http/socks5)
 * @property {string} COUNTRY - País alvo
 * @property {Object} ROTATION - Configurações de rotação
 * @property {number} TIMEOUT - Timeout de conexão
 */

/**
 * @typedef {Object} BrowserConfig
 * @property {boolean} headless - Modo headless
 * @property {null} defaultViewport - Viewport padrão
 * @property {string[]} ignoreDefaultArgs - Args a ignorar
 * @property {string[]} args - Argumentos do browser
 */

// ============================================
// CONFIGURAÇÕES PRINCIPAIS
// ============================================

/**
 * Configurações principais do bot
 * @constant
 * @type {Object}
 */
export const CONFIG = {
  /**
   * Versão atual do bot
   * @type {string}
   */
  VERSION: '9.2.0',
  
  // ============================================
  // TIMEOUTS GLOBAIS
  // ============================================
  
  /**
   * Timeout total da execução (10 minutos)
   * @type {number}
   */
  GLOBAL_TIMEOUT_MS: 10 * 60 * 1000,
  
  /**
   * Timeout padrão de página (60 segundos)
   * @type {number}
   */
  PAGE_TIMEOUT_MS: 60000,
  
  /**
   * Timeout de navegação (120 segundos)
   * @type {number}
   */
  NAVIGATION_TIMEOUT_MS: 120000,
  
  // ============================================
  // LIMITES DE PROTEÇÃO
  // ============================================
  
  /**
   * Máximo de reloads por cartão
   * @type {number}
   */
  MAX_PAGE_RELOADS: 3,
  
  /**
   * Máximo de cartões testados por conta
   * @type {number}
   */
  MAX_CARDS_PER_ACCOUNT: 3,
  
  /**
   * Máximo de verificações de resultado
   * @type {number}
   */
  MAX_VERIFICACOES_RESULTADO: 25,
  
  /**
   * Intervalo entre verificações (ms)
   * @type {number}
   */
  INTERVALO_VERIFICACAO_MS: 3000,
  
  /**
   * Máximo de erros consecutivos antes de reiniciar
   * @type {number}
   */
  MAX_CONSECUTIVE_ERRORS: 5,
  
  // ============================================
  // DELAYS (em milissegundos)
  // ============================================
  
  /**
   * Configurações de delay (valores base)
   * NOTA: Para delays humanizados variáveis, veja config/humanization.js
   * @type {DelayConfig}
   */
  DELAYS: {
    AFTER_PAGE_LOAD: 15000,
    AFTER_CLICK: 2000,
    BETWEEN_FIELDS: 400,
    AFTER_SUBMIT: 8000,
    BETWEEN_ACCOUNTS: 5000,
    AFTER_SELECT_CARD: 5000,
    TYPING_MIN: 40,
    TYPING_MAX: 80,
    BETWEEN_WORKERS: 3000,
  },
  
  // ============================================
  // CONFIGURAÇÕES POR ESTADO
  // ============================================
  
  /**
   * Configurações específicas por estado da máquina de estados
   * @type {Object.<string, StateConfig>}
   */
  STATES: {
    INIT: {
      maxRetries: 1,
      timeout: 30000,
    },
    OPEN_CHECKOUT: {
      maxRetries: 3,
      timeout: 60000,
      waitAfterNavigation: 5000,
    },
    WAIT_UI_READY: {
      maxRetries: 5,
      timeout: 30000,
      pollInterval: 2000,
    },
    SELECT_METHOD: {
      maxRetries: 3,
      timeout: 20000,
      waitAfterSelect: 3000,
    },
    FILL_FORM: {
      maxRetries: 2,
      timeout: 45000,
      delayBetweenFields: 400,
    },
    SUBMIT: {
      maxRetries: 2,
      timeout: 15000,
      waitBeforeClick: 2000,
    },
    WAIT_RESULT: {
      maxRetries: 1,
      timeout: 90000,
      pollInterval: 3000,
      maxPolls: 30,
    },
  },
  
  // ============================================
  // DADOS DE ACESSO
  // ============================================
  
  /**
   * Senha padrão para tentativa de login
   * @type {string}
   */
  SENHA_PADRAO_LOGIN: '12344321',
  
  /**
   * Idade máxima permitida para dados de pessoa
   * @type {number}
   */
  IDADE_MAXIMA: 40,
  
  /**
   * Tempo de cooldown para reutilização de dados (minutos)
   * @type {number}
   */
  TEMPO_ESPERA_REUTILIZACAO: 30,
  
  // ============================================
  // URLs
  // ============================================
  
  /**
   * URLs do Crunchyroll
   * @type {Object.<string, string>}
   */
  URLS: {
    REGISTRO: 'https://sso.crunchyroll.com/pt-br/register?return_url=%2Fauthorize%3Fclient_id%3Dkmj7imhjt_q90lcbzzsj%26redirect_uri%3Dhttps%253A%252F%252Fcrunchyroll.com%252Fpremium%252Fredirects%26response_type%3Dcookie%26state%3Dis_skip_freetrial%253Dtrue%2526ref%253Dnewweb_organic_header%2526return_url%253Dhttps%25253A%25252F%25252Fwww.crunchyroll.com%25252Fpt-br%25252F',
    PAGAMENTO: 'https://www.crunchyroll.com/pt-br/payments/checkout?client_type=com.crunchyroll.static&failure_url=https%3A%2F%2Fwww.crunchyroll.com%2Fpt-br%2Fpremium%2Ferror%3Freturn_url%253Dhttps%25253A%25252F%25252Fwww.crunchyroll.com%25252Fpt-br%25252Fvideos%25252Fpopular%2526selected_sku%253Dcr_fan_pack.1_month&ref=newweb_organic_header&return_url=https%3A%2F%2Fwww.crunchyroll.com%2Fpt-br%2Fpremium%2Fsuccess%3Freturn_url%253Dhttps%25253A%25252F%25252Fwww.crunchyroll.com%25252Fpt-br%25252Fvideos%25252Fpopular%2526selected_sku%253Dcr_fan_pack.1_month&sku=cr_fan_pack.1_month',
    LOGIN: 'https://sso.crunchyroll.com/pt-br/login',
  },
  
  // ============================================
  // CONFIGURAÇÕES DE PROXY
  // ============================================
  
  /**
   * Configurações de proxy
   * @type {ProxyConfig}
   */
  PROXY: {
    ENABLED: process.env.PROXY_ENABLED === 'true' || false,
    HOST: process.env.PROXY_HOST || '',
    PORT: parseInt(process.env.PROXY_PORT) || 0,
    USERNAME: process.env.PROXY_USERNAME || '',
    PASSWORD: process.env.PROXY_PASSWORD || '',
    TYPE: process.env.PROXY_TYPE || 'http',
    COUNTRY: process.env.PROXY_COUNTRY || 'BR',
    ROTATION: {
      ENABLED: true,
      INTERVAL: parseInt(process.env.PROXY_ROTATION_INTERVAL) || 0,
    },
    TIMEOUT: 30000,
  },
  
  // ============================================
  // CONFIGURAÇÕES DO CHARLES PROXY
  // ============================================
  
  /**
   * Configurações do Charles Proxy
   * 
   * Para usar o Charles Proxy:
   * 1. Abra o Charles Proxy
   * 2. Vá em Proxy > Web Interface Settings e habilite
   * 3. Vá em Tools > Rewrite e importe o arquivo crunchyroll.xml
   * 4. Defina CHARLES_ENABLED=true nas variáveis de ambiente
   * 
   * Ou use a interceptação direta (sem Charles):
   * - INTERCEPT_ENABLED=true (padrão: habilitado)
   * 
   * @type {Object}
   */
  CHARLES: {
    ENABLED: process.env.CHARLES_ENABLED === 'true' || false,
    HOST: process.env.CHARLES_HOST || '127.0.0.1',
    PORT: parseInt(process.env.CHARLES_PORT) || 8888,
    WEB_INTERFACE: true,
    SSL_PROXYING: true,
    IGNORE_SSL_ERRORS: true,
  },
  
  /**
   * Configurações de interceptação de requests (sem Charles)
   * 
   * Quando habilitado, o bot intercepta requests diretamente
   * no Puppeteer e aplica regras de rewrite (ex: remover CVC)
   * 
   * @type {Object}
   */
  INTERCEPT: {
    ENABLED: process.env.INTERCEPT_ENABLED !== 'false', // Habilitado por padrão
    LOG_REQUESTS: process.env.LOG_REQUESTS === 'true' || false,
    RULES: {
      REMOVE_CVC: true,    // Remove campo CVC das requisições
      REMOVE_CVV: true,    // Remove campo CVV das requisições
      REMOVE_SECURITY_CODE: true, // Remove security_code
    }
  },
  
  // ============================================
  // CONFIGURAÇÕES DO BROWSER
  // ============================================
  
  /**
   * Configurações do Puppeteer
   * @type {BrowserConfig}
   */
  BROWSER: {
    headless: false,
    defaultViewport: null,
    ignoreDefaultArgs: ['--enable-automation'],
    args: [
      '--start-maximized',
      '--no-sandbox',
      '--disable-setuid-sandbox',
      '--disable-blink-features=AutomationControlled',
      '--disable-infobars',
      '--lang=pt-BR',
      '--disable-web-security',
      '--disable-features=IsolateOrigins,site-per-process'
    ]
  },
  
  // ============================================
  // ARQUIVOS DE DADOS
  // ============================================
  
  /**
   * Nomes dos arquivos de dados
   * @type {Object.<string, string>}
   */
  FILES: {
    CONTAS: 'contas.txt',
    CARTOES: 'cartoes.txt',
    DADOS_CSV: 'dados.csv',
    CONTAS_PREMIUM: 'contas_premium.txt',
    CONTAS_PREMIUM_SIMPLES: 'contas_premium_simples.txt',
    CONTAS_CRIADAS: 'contas_criadas.txt',
    CONTAS_LOGIN_SUCESSO: 'contas_login_sucesso.txt',
    CONTAS_LOGIN_FALHOU: 'contas_login_falhou.txt',
    CONTAS_SEM_CARTAO: 'contas_sem_cartao.txt',
    CONTAS_SEM_PAGAMENTO: 'contas_sem_pagamento.txt',
    CARTOES_APROVADOS: 'cartoes_aprovados.txt',
    CARTOES_FALHOS: 'cartoes_falhos.txt',
    COOLDOWNS: 'cooldowns.json',
  },
};

// ============================================
// SELETORES DE ELEMENTOS
// ============================================

/**
 * @typedef {Object} FieldSelector
 * @property {string[]} selectors - Lista de seletores CSS
 * @property {string[]} placeholders - Lista de placeholders
 */

/**
 * Seletores CSS para elementos da página
 * @constant
 * @type {Object}
 */
export const SELECTORS = {
  /**
   * Seletores de autenticação
   */
  AUTH: {
    /** @type {string} Seletor do campo de email */
    EMAIL_INPUT: 'input[name="login"]',
    /** @type {string} Seletor do campo de senha */
    PASSWORD_INPUT: 'input[name="password"]',
  },
  
  /**
   * Seletores de método de pagamento
   */
  PAYMENT_METHOD: {
    /** @type {string} Seletor do header de cartão */
    CARD_HEADER: 'h3[class*="_header_"]',
    
    /** @type {string[]} Textos para identificar opção de cartão */
    CARD_TEXTS: [
      'Cartão de Crédito ou Débito',
      'Cartao de Credito ou Debito',
      'Cartão de Crédito',
      'Cartao de Credito',
      'Credit or Debit Card',
      'Credit Card'
    ],
    
    /** @type {string} Seletor de radio buttons */
    RADIO_BUTTONS: 'input[type="radio"]',
  },
  
  /**
   * Seletores do formulário de pagamento
   * @type {Object.<string, FieldSelector|string>}
   */
  PAYMENT_FORM: {
    NAME: {
      selectors: ['#name', '[name="cardHolderName"]', '[name="name"]'],
      placeholders: ['Nome', 'Nome do titular', 'Cardholder name']
    },
    CPF: {
      selectors: ['#documentId', '#cpf', '[name="document"]', '[name="cpf"]'],
      placeholders: ['CPF', 'Documento', 'Document']
    },
    CARD_NUMBER: {
      selectors: ['#cardNumber', '[name="cardNumber"]', '[name="number"]'],
      placeholders: ['Número do cartão', 'Card number', 'Número']
    },
    EXPIRY: {
      selectors: ['#expirationDate', '[name="expiry"]', '[name="expirationDate"]'],
      placeholders: ['MM / AA', 'MM/AA', 'Validade', 'Expiry']
    },
    CVC: {
      selectors: ['#cvc', '[name="cvc"]', '[name="cvv"]', '[name="securityCode"]'],
      placeholders: ['CVC', 'CVV', 'Código de segurança', 'Security code']
    },
    SUBMIT_BUTTON: 'button[type="submit"]',
  },
  
  /**
   * Textos de botões
   * @type {Object.<string, string[]>}
   */
  BUTTONS: {
    PROXIMO: ['PRÓXIMO', 'Próximo', 'NEXT', 'Next', 'Continuar', 'CONTINUAR'],
    CRIAR_CONTA: ['CRIAR CONTA', 'Criar Conta', 'CREATE ACCOUNT', 'Create Account'],
    ENTRAR: ['ENTRAR', 'Entrar', 'LOGIN', 'Login', 'SIGN IN', 'Sign In'],
    ACEITAR_COOKIES: ['Aceitar Todos', 'Accept All', 'OK', 'Aceitar', 'Accept'],
    FINALIZAR: [
      'CONCLUIR COMPRA', 'Concluir Compra', 'Concluir compra',
      'INICIAR ASSINATURA', 'Iniciar Assinatura', 'Iniciar assinatura',
      'ASSINAR', 'Assinar',
      'FINALIZAR', 'Finalizar',
      'CONFIRMAR', 'Confirmar',
      'PAGAR', 'Pagar',
      'CONTINUAR', 'Continuar',
      'SUBSCRIBE', 'Subscribe',
      'COMPLETE PURCHASE', 'Complete Purchase',
      'START SUBSCRIPTION', 'Start Subscription'
    ],
  },
};

// ============================================
// INDICADORES DE SUCESSO/FALHA
// ============================================

/**
 * Indicadores para detecção de estados
 * @constant
 * @type {Object}
 */
export const INDICATORS = {
  /**
   * Indicadores de sucesso
   */
  SUCCESS: {
    /** @type {string[]} Padrões de URL de sucesso */
    URL_PATTERNS: [
      '/premium/success',
      'success?',
      '/success',
      '/premium/already',
      'already?',
    ],
    /** @type {string[]} Padrões de texto de sucesso */
    TEXT_PATTERNS: [
      'Você Evoluiu para',
      'Bem-vindo ao Premium',
      'Assinatura ativada',
      'Parabéns! Sua assinatura',
      'Premium ativo',
      'Welcome to Premium',
      'Subscription activated',
      'Congratulations',
      'Your subscription is now active',
      'Obrigado por ser Membro',
      'Thank you for being a Member',
      'Mega Fan Membership',
      'Fan Membership',
      'Você maximizou seu fandom',
      'You maximized your fandom',
      'Aproveite suas Vantagens',
      'Enjoy your Benefits',
      'Membro Premium',
      'Premium Member',
      'Assinatura confirmada',
      'Subscription confirmed',
      'Pagamento aprovado',
      'Payment approved',
    ],
  },
  
  /**
   * Indicadores de falha
   */
  FAIL: {
    /** @type {string[]} Padrões de texto de falha */
    TEXT_PATTERNS: [
      'cartão recusado',
      'pagamento falhou',
      'pagamento recusado',
      'erro no pagamento',
      'declined',
      'payment failed',
      'invalid card',
      'cartão inválido',
      'dados incorretos',
      'insufficient funds',
      'saldo insuficiente',
      'transação não autorizada',
      'transaction declined',
      'card declined',
      'do not honor',
      'não foi possível processar',
      'unable to process',
      'tente novamente',
      'try again',
    ],
  },
  
  /**
   * Indicadores de páginas de erro que requerem atualização
   * CORRIGIDO v9.1.2: Removido failure_url= que causava falsos positivos
   * A URL de checkout contém failure_url= como PARÂMETRO, não como erro
   */
  ERROR_PAGE: {
    /** @type {boolean} Habilitar detecção de páginas de erro */
    ENABLED: true,
    
    /** @type {string[]} Padrões de texto de erro ESPECÍFICOS (devem aparecer como mensagem principal) */
    TEXT_PATTERNS: [
      'something went wrong. please try again',
      'algo deu errado. tente novamente',
      'page not found',
      'página não encontrada',
      'serviço indisponível',
      'service unavailable',
      'internal server error',
      'erro interno do servidor',
    ],
    
    /** @type {string[]} Padrões de URL de erro (APENAS quando é a página de erro real) */
    URL_PATTERNS: [
      // REMOVIDO: 'failure_url=' - isso é um PARÂMETRO na URL de checkout, não indica erro
      // Só detectar erro quando a URL ATUAL é a página de erro
    ],
    
    /** @type {string[]} URLs que NUNCA devem ser consideradas erro (whitelist) */
    URL_WHITELIST: [
      '/register',
      '/login',
      '/premium',
      '/checkout',
      '/payment',
      '/payments',
      '/subscribe',
      'sso.crunchyroll',
    ],
    
    /** @type {string[]} Seletores de elementos de erro (mais específicos) */
    SELECTORS: [
      '.error-page',
      '.error-page-container',
    ],
  },
  
  /**
   * Indicadores de bloqueio/captcha
   */
  BLOCKED: {
    /** @type {string[]} Seletores de captcha */
    CAPTCHA_SELECTORS: [
      'iframe[src*="recaptcha"]',
      'iframe[src*="hcaptcha"]',
      '.g-recaptcha',
      '.h-captcha',
      '[data-sitekey]',
      '#captcha',
      '.captcha',
    ],
    /** @type {string[]} Padrões de texto de bloqueio */
    TEXT_PATTERNS: [
      'verificação de segurança',
      'security check',
      'prove you are human',
      'não é um robô',
      'are you a robot',
      'too many requests',
      'rate limit',
      'blocked',
      'access denied',
      'suspicious activity',
    ],
  },
  
  /**
   * Indicadores de processamento
   */
  PENDING: {
    /** @type {string[]} Seletores de loading */
    LOADING_SELECTORS: [
      '.loading',
      '.spinner',
      '[class*="loading"]',
      '[class*="spinner"]',
      '[class*="processing"]',
    ],
    /** @type {string[]} Padrões de texto de loading */
    TEXT_PATTERNS: [
      'processando',
      'processing',
      'aguarde',
      'please wait',
      'carregando',
      'loading',
    ],
  },
  
  /**
   * Indicadores de conta existente
   * @type {string[]}
   */
  ACCOUNT_EXISTS: [
    'conta já existe',
    'email já cadastrado',
    'e-mail já está em uso',
    'already exists',
    'already registered',
    'email is already',
    'já possui uma conta',
    'account already exists',
    'Digite um endereço de e-mail válido',
  ],
  
  /**
   * Indicadores de login falhou
   * @type {string[]}
   */
  LOGIN_FAILED: [
    'senha incorreta',
    'senha inválida',
    'credenciais inválidas',
    'incorrect password',
    'invalid password',
    'invalid credentials',
    'login failed',
    'falha no login',
  ],
};

// ============================================
// USER AGENTS
// ============================================

/**
 * Lista de User Agents para rotação
 * @constant
 * @type {string[]}
 */
export const USER_AGENTS = [
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0',
  'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
  'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0',
];

/**
 * Retorna um User Agent aleatório
 * @returns {string}
 */
export function getRandomUserAgent() {
  return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

// ============================================
// FUNÇÕES UTILITÁRIAS
// ============================================

/**
 * Obtém configuração de estado
 * @param {string} stateName - Nome do estado
 * @returns {StateConfig|null}
 */
export function getStateConfig(stateName) {
  return CONFIG.STATES[stateName] || null;
}

/**
 * Verifica se proxy está configurado
 * @returns {boolean}
 */
export function isProxyConfigured() {
  return CONFIG.PROXY.ENABLED && CONFIG.PROXY.HOST && CONFIG.PROXY.PORT > 0;
}

/**
 * Obtém delay com variação aleatória
 * @param {string} delayName - Nome do delay
 * @param {number} [variance=0.2] - Variação (0-1)
 * @returns {number}
 */
export function getDelayWithVariance(delayName, variance = 0.2) {
  const baseDelay = CONFIG.DELAYS[delayName] || 1000;
  const variation = baseDelay * variance;
  return baseDelay + (Math.random() * variation * 2 - variation);
}

// Export default
export default CONFIG;
