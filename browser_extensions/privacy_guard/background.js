/**
 * Privacy Guard - Background Service Worker
 * Telegram Collector Pro
 * 
 * Este script roda em segundo plano e gerencia:
 * - Bloqueio de trackers conhecidos
 * - Remoção de headers de rastreamento
 * - Estatísticas de bloqueio
 */

// Estatísticas de bloqueio
let stats = {
    trackersBlocked: 0,
    fingerprintAttempts: 0,
    cookiesBlocked: 0,
    startTime: Date.now()
};

// Lista de domínios de trackers conhecidos
const TRACKER_DOMAINS = [
    'google-analytics.com',
    'googletagmanager.com',
    'doubleclick.net',
    'facebook.net',
    'facebook.com/tr',
    'connect.facebook.net',
    'pixel.facebook.com',
    'analytics.twitter.com',
    'ads.twitter.com',
    'amazon-adsystem.com',
    'advertising.com',
    'adnxs.com',
    'adsrvr.org',
    'criteo.com',
    'criteo.net',
    'outbrain.com',
    'taboola.com',
    'hotjar.com',
    'fullstory.com',
    'mouseflow.com',
    'crazyegg.com',
    'luckyorange.com',
    'clarity.ms',
    'newrelic.com',
    'nr-data.net',
    'sentry.io',
    'bugsnag.com',
    'rollbar.com',
    'mixpanel.com',
    'amplitude.com',
    'segment.io',
    'segment.com',
    'heap.io',
    'heapanalytics.com',
    'intercom.io',
    'drift.com',
    'hubspot.com',
    'hs-analytics.net',
    'marketo.com',
    'mktoresp.com',
    'pardot.com',
    'eloqua.com',
    'omtrdc.net',
    'demdex.net',
    'everesttech.net',
    'rlcdn.com',
    'bluekai.com',
    'exelator.com',
    'quantserve.com',
    'scorecardresearch.com',
    'imrworldwide.com',
    'chartbeat.com',
    'parsely.com'
];

// Headers que devem ser removidos/modificados
const HEADERS_TO_REMOVE = [
    'x-client-data',
    'x-chrome-connected',
    'x-chrome-uma-enabled',
    'x-chrome-variations'
];

// Inicialização
chrome.runtime.onInstalled.addListener(() => {
    console.log('[Privacy Guard] Extensão instalada e ativa!');
    
    // Salvar estatísticas iniciais
    chrome.storage.local.set({ privacyStats: stats });
});

// Listener para mensagens do content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.type === 'fingerprintAttempt') {
        stats.fingerprintAttempts++;
        chrome.storage.local.set({ privacyStats: stats });
        console.log('[Privacy Guard] Tentativa de fingerprint bloqueada:', message.api);
    }
    
    if (message.type === 'getStats') {
        sendResponse(stats);
    }
    
    return true;
});

// Verificar se URL é de tracker
function isTrackerUrl(url) {
    try {
        const urlObj = new URL(url);
        const hostname = urlObj.hostname.toLowerCase();
        
        for (const tracker of TRACKER_DOMAINS) {
            if (hostname.includes(tracker) || hostname.endsWith('.' + tracker)) {
                return true;
            }
        }
    } catch (e) {
        // URL inválida
    }
    return false;
}

// Log de atividade
console.log('[Privacy Guard] Service Worker iniciado');
console.log('[Privacy Guard] Monitorando', TRACKER_DOMAINS.length, 'domínios de trackers');
