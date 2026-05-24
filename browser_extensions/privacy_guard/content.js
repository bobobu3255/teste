/**
 * Privacy Guard - Content Script
 * Telegram Collector Pro
 * 
 * Este script é injetado em todas as páginas e:
 * - Bloqueia tentativas de fingerprinting
 * - Remove scripts de rastreamento
 * - Protege APIs sensíveis
 */

(function() {
    'use strict';
    
    // Notificar background sobre tentativas de fingerprint
    function reportFingerprint(api) {
        try {
            chrome.runtime.sendMessage({
                type: 'fingerprintAttempt',
                api: api,
                url: window.location.href
            });
        } catch (e) {
            // Extensão pode não estar disponível
        }
    }
    
    // ===== PROTEÇÃO DE CANVAS =====
    const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
    HTMLCanvasElement.prototype.toDataURL = function(type) {
        // Adicionar ruído imperceptível ao canvas
        const ctx = this.getContext('2d');
        if (ctx) {
            const imageData = ctx.getImageData(0, 0, this.width, this.height);
            const data = imageData.data;
            
            // Adicionar ruído mínimo (imperceptível visualmente)
            for (let i = 0; i < data.length; i += 4) {
                // Modificar apenas alguns pixels aleatoriamente
                if (Math.random() < 0.01) {
                    data[i] = Math.max(0, Math.min(255, data[i] + Math.floor(Math.random() * 3 - 1)));
                }
            }
            
            ctx.putImageData(imageData, 0, 0);
        }
        
        reportFingerprint('canvas.toDataURL');
        return originalToDataURL.apply(this, arguments);
    };
    
    // ===== PROTEÇÃO DE WEBGL =====
    const getParameterOriginal = WebGLRenderingContext.prototype.getParameter;
    WebGLRenderingContext.prototype.getParameter = function(parameter) {
        // UNMASKED_VENDOR_WEBGL
        if (parameter === 37445) {
            reportFingerprint('webgl.vendor');
            return 'Google Inc. (Intel)';
        }
        // UNMASKED_RENDERER_WEBGL
        if (parameter === 37446) {
            reportFingerprint('webgl.renderer');
            return 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)';
        }
        return getParameterOriginal.apply(this, arguments);
    };
    
    // WebGL2
    if (typeof WebGL2RenderingContext !== 'undefined') {
        const getParameter2Original = WebGL2RenderingContext.prototype.getParameter;
        WebGL2RenderingContext.prototype.getParameter = function(parameter) {
            if (parameter === 37445) {
                return 'Google Inc. (Intel)';
            }
            if (parameter === 37446) {
                return 'ANGLE (Intel, Intel(R) UHD Graphics 620 Direct3D11 vs_5_0 ps_5_0, D3D11)';
            }
            return getParameter2Original.apply(this, arguments);
        };
    }
    
    // ===== PROTEÇÃO DE AUDIO =====
    if (window.AudioContext || window.webkitAudioContext) {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        
        // Override getFloatFrequencyData
        const originalGetFloatFrequencyData = AnalyserNode.prototype.getFloatFrequencyData;
        AnalyserNode.prototype.getFloatFrequencyData = function(array) {
            originalGetFloatFrequencyData.call(this, array);
            // Adicionar ruído
            for (let i = 0; i < array.length; i++) {
                array[i] = array[i] + (Math.random() * 0.0001 - 0.00005);
            }
            reportFingerprint('audio.getFloatFrequencyData');
        };
    }
    
    // ===== PROTEÇÃO DE NAVIGATOR =====
    
    // Remover webdriver
    Object.defineProperty(navigator, 'webdriver', {
        get: () => undefined,
        configurable: true
    });
    
    // Plugins consistentes
    Object.defineProperty(navigator, 'plugins', {
        get: () => {
            return {
                length: 5,
                item: (i) => ({
                    name: ['Chrome PDF Plugin', 'Chrome PDF Viewer', 'Native Client', 'Chromium PDF Plugin', 'Chromium PDF Viewer'][i] || null,
                    filename: ['internal-pdf-viewer', 'mhjfbmdgcfjbbpaeojofohoefgiehjai', 'internal-nacl-plugin', 'internal-pdf-viewer', 'mhjfbmdgcfjbbpaeojofohoefgiehjai'][i] || null
                }),
                namedItem: (name) => null,
                refresh: () => {}
            };
        },
        configurable: true
    });
    
    // ===== BLOQUEIO DE SCRIPTS DE TRACKING =====
    const BLOCKED_SCRIPTS = [
        'google-analytics.com',
        'googletagmanager.com',
        'facebook.net',
        'connect.facebook.net',
        'doubleclick.net',
        'hotjar.com',
        'clarity.ms',
        'fullstory.com'
    ];
    
    // Observer para bloquear scripts de tracking
    const observer = new MutationObserver((mutations) => {
        mutations.forEach((mutation) => {
            mutation.addedNodes.forEach((node) => {
                if (node.tagName === 'SCRIPT' && node.src) {
                    for (const blocked of BLOCKED_SCRIPTS) {
                        if (node.src.includes(blocked)) {
                            node.remove();
                            console.log('[Privacy Guard] Script bloqueado:', node.src);
                            reportFingerprint('script.' + blocked);
                        }
                    }
                }
            });
        });
    });
    
    // Iniciar observer quando DOM estiver pronto
    if (document.body) {
        observer.observe(document.body, { childList: true, subtree: true });
    } else {
        document.addEventListener('DOMContentLoaded', () => {
            observer.observe(document.body, { childList: true, subtree: true });
        });
    }
    
    // ===== PROTEÇÃO DE STORAGE =====
    
    // Limpar cookies de tracking conhecidos periodicamente
    const TRACKING_COOKIES = ['_ga', '_gid', '_fbp', '_fbc', 'fr', 'tr'];
    
    function cleanTrackingCookies() {
        TRACKING_COOKIES.forEach(cookieName => {
            document.cookie = `${cookieName}=; expires=Thu, 01 Jan 1970 00:00:00 UTC; path=/;`;
        });
    }
    
    // Limpar a cada 5 minutos
    setInterval(cleanTrackingCookies, 5 * 60 * 1000);
    
    // ===== LOG =====
    console.log('[Privacy Guard] Proteção ativa nesta página');
    
})();
