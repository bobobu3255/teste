#!/usr/bin/env python3
"""
Fingerprint Generator - Módulo de Geração de Fingerprints Anti-Detecção
Telegram Collector Pro v9.0 - Navegador Seguro

Este módulo gera fingerprints realistas e customizáveis para evitar
rastreamento e detecção de automação.
"""

import random
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class FingerprintGenerator:
    """
    Gerador de fingerprints para navegação anônima.
    Suporta User-Agent, resolução, WebGL, Canvas, timezone e idioma.
    """
    
    # Lista de User-Agents recentes do Chrome no Windows 10/11
    USER_AGENTS = [
        # Chrome 120+ no Windows 11
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        # Chrome no Windows 10
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.6099.130 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.6167.85 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.6261.94 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.6312.86 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.6367.91 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.6422.76 Safari/537.36",
        # Edge no Windows
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Edg/120.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36 Edg/121.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36 Edg/124.0.0.0",
        # Chrome no macOS
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        # Chrome no Linux
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        # Variações adicionais
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/116.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
    ]
    
    # Resoluções de tela comuns
    SCREEN_RESOLUTIONS = [
        (1920, 1080),  # Full HD - mais comum
        (1366, 768),   # HD - notebooks
        (1536, 864),   # Comum em laptops
        (1440, 900),   # MacBook Air
        (1280, 720),   # HD
        (2560, 1440),  # QHD
        (1600, 900),   # HD+
        (1280, 800),   # WXGA
        (1680, 1050),  # WSXGA+
        (1920, 1200),  # WUXGA
        (2560, 1080),  # Ultra-wide
        (3840, 2160),  # 4K
    ]
    
    # Configurações de WebGL
    WEBGL_VENDORS = [
        "Google Inc. (NVIDIA)",
        "Google Inc. (AMD)",
        "Google Inc. (Intel)",
        "Google Inc.",
        "Intel Inc.",
        "NVIDIA Corporation",
        "AMD",
    ]
    
    WEBGL_RENDERERS = [
        "ANGLE (NVIDIA GeForce GTX 1660 SUPER Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (NVIDIA GeForce RTX 3060 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (NVIDIA GeForce RTX 3070 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (NVIDIA GeForce RTX 3080 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (NVIDIA GeForce RTX 4060 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (NVIDIA GeForce RTX 4070 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (AMD Radeon RX 580 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (AMD Radeon RX 5700 XT Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (AMD Radeon RX 6700 XT Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (AMD Radeon RX 6800 XT Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (Intel(R) UHD Graphics 630 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (Intel(R) UHD Graphics 770 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (Intel(R) Iris(R) Xe Graphics Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (Intel(R) HD Graphics 620 Direct3D11 vs_5_0 ps_5_0)",
        "ANGLE (Intel(R) HD Graphics 530 Direct3D11 vs_5_0 ps_5_0)",
    ]
    
    # Timezones por país
    TIMEZONES = {
        "BR": {
            "timezone": "America/Sao_Paulo",
            "offset": -180,  # UTC-3 em minutos
            "locale": "pt-BR",
            "languages": ["pt-BR", "pt", "en-US", "en"],
        },
        "US": {
            "timezone": "America/New_York",
            "offset": -300,  # UTC-5
            "locale": "en-US",
            "languages": ["en-US", "en"],
        },
        "UK": {
            "timezone": "Europe/London",
            "offset": 0,
            "locale": "en-GB",
            "languages": ["en-GB", "en"],
        },
        "DE": {
            "timezone": "Europe/Berlin",
            "offset": 60,  # UTC+1
            "locale": "de-DE",
            "languages": ["de-DE", "de", "en-US", "en"],
        },
        "FR": {
            "timezone": "Europe/Paris",
            "offset": 60,
            "locale": "fr-FR",
            "languages": ["fr-FR", "fr", "en-US", "en"],
        },
        "ES": {
            "timezone": "Europe/Madrid",
            "offset": 60,
            "locale": "es-ES",
            "languages": ["es-ES", "es", "en-US", "en"],
        },
        "PT": {
            "timezone": "Europe/Lisbon",
            "offset": 0,
            "locale": "pt-PT",
            "languages": ["pt-PT", "pt", "en-US", "en"],
        },
        "JP": {
            "timezone": "Asia/Tokyo",
            "offset": 540,  # UTC+9
            "locale": "ja-JP",
            "languages": ["ja-JP", "ja", "en-US", "en"],
        },
        "CN": {
            "timezone": "Asia/Shanghai",
            "offset": 480,  # UTC+8
            "locale": "zh-CN",
            "languages": ["zh-CN", "zh", "en-US", "en"],
        },
        "AU": {
            "timezone": "Australia/Sydney",
            "offset": 600,  # UTC+10
            "locale": "en-AU",
            "languages": ["en-AU", "en"],
        },
    }
    
    # Plataformas
    PLATFORMS = {
        "Windows": "Win32",
        "macOS": "MacIntel",
        "Linux": "Linux x86_64",
    }
    
    # Número de cores de CPU comuns
    CPU_CORES = [2, 4, 6, 8, 12, 16]
    
    # Quantidade de memória em GB
    DEVICE_MEMORY = [2, 4, 8, 16, 32]
    
    def __init__(self):
        """Inicializa o gerador de fingerprints."""
        self.profiles_dir = Path("browser_profiles")
        self.profiles_dir.mkdir(exist_ok=True)
    
    def generate_random_fingerprint(self, country: str = "BR") -> Dict:
        """
        Gera um fingerprint completamente aleatório.
        
        Args:
            country: Código do país para timezone e idioma
            
        Returns:
            Dicionário com todas as configurações do fingerprint
        """
        # Selecionar User-Agent aleatório
        user_agent = random.choice(self.USER_AGENTS)
        
        # Determinar plataforma baseado no User-Agent
        if "Windows" in user_agent:
            platform = self.PLATFORMS["Windows"]
            platform_name = "Windows"
        elif "Macintosh" in user_agent:
            platform = self.PLATFORMS["macOS"]
            platform_name = "macOS"
        else:
            platform = self.PLATFORMS["Linux"]
            platform_name = "Linux"
        
        # Resolução de tela
        resolution = random.choice(self.SCREEN_RESOLUTIONS)
        
        # WebGL
        webgl_vendor = random.choice(self.WEBGL_VENDORS)
        webgl_renderer = random.choice(self.WEBGL_RENDERERS)
        
        # Timezone
        tz_config = self.TIMEZONES.get(country, self.TIMEZONES["BR"])
        
        # Hardware
        cpu_cores = random.choice(self.CPU_CORES)
        device_memory = random.choice(self.DEVICE_MEMORY)
        
        # Gerar seed para Canvas noise
        canvas_seed = random.randint(1, 1000000)
        
        fingerprint = {
            "id": self._generate_profile_id(),
            "created_at": datetime.now().isoformat(),
            "user_agent": user_agent,
            "platform": platform,
            "platform_name": platform_name,
            "screen": {
                "width": resolution[0],
                "height": resolution[1],
                "color_depth": 24,
                "pixel_ratio": random.choice([1, 1.25, 1.5, 2]),
            },
            "webgl": {
                "vendor": webgl_vendor,
                "renderer": webgl_renderer,
            },
            "timezone": {
                "name": tz_config["timezone"],
                "offset": tz_config["offset"],
            },
            "locale": tz_config["locale"],
            "languages": tz_config["languages"],
            "hardware": {
                "cpu_cores": cpu_cores,
                "device_memory": device_memory,
            },
            "canvas_seed": canvas_seed,
            "country": country,
        }
        
        return fingerprint
    
    def generate_brazilian_fingerprint(self) -> Dict:
        """
        Gera um fingerprint otimizado para uso no Brasil.
        
        Returns:
            Dicionário com fingerprint brasileiro
        """
        fingerprint = self.generate_random_fingerprint(country="BR")
        
        # Preferir User-Agents do Windows (mais comum no Brasil)
        windows_agents = [ua for ua in self.USER_AGENTS if "Windows" in ua]
        fingerprint["user_agent"] = random.choice(windows_agents)
        fingerprint["platform"] = self.PLATFORMS["Windows"]
        fingerprint["platform_name"] = "Windows"
        
        # Resoluções mais comuns no Brasil
        common_br_resolutions = [
            (1920, 1080),
            (1366, 768),
            (1536, 864),
            (1280, 720),
        ]
        resolution = random.choice(common_br_resolutions)
        fingerprint["screen"]["width"] = resolution[0]
        fingerprint["screen"]["height"] = resolution[1]
        
        return fingerprint
    
    def generate_custom_fingerprint(
        self,
        user_agent: Optional[str] = None,
        resolution: Optional[Tuple[int, int]] = None,
        country: str = "BR",
        webgl_vendor: Optional[str] = None,
        webgl_renderer: Optional[str] = None,
    ) -> Dict:
        """
        Gera um fingerprint customizado com parâmetros específicos.
        
        Args:
            user_agent: User-Agent customizado
            resolution: Tupla (largura, altura) da resolução
            country: Código do país
            webgl_vendor: Vendor WebGL customizado
            webgl_renderer: Renderer WebGL customizado
            
        Returns:
            Dicionário com fingerprint customizado
        """
        # Começar com fingerprint aleatório
        fingerprint = self.generate_random_fingerprint(country)
        
        # Aplicar customizações
        if user_agent:
            fingerprint["user_agent"] = user_agent
            # Atualizar plataforma baseado no User-Agent
            if "Windows" in user_agent:
                fingerprint["platform"] = self.PLATFORMS["Windows"]
                fingerprint["platform_name"] = "Windows"
            elif "Macintosh" in user_agent:
                fingerprint["platform"] = self.PLATFORMS["macOS"]
                fingerprint["platform_name"] = "macOS"
            else:
                fingerprint["platform"] = self.PLATFORMS["Linux"]
                fingerprint["platform_name"] = "Linux"
        
        if resolution:
            fingerprint["screen"]["width"] = resolution[0]
            fingerprint["screen"]["height"] = resolution[1]
        
        if webgl_vendor:
            fingerprint["webgl"]["vendor"] = webgl_vendor
        
        if webgl_renderer:
            fingerprint["webgl"]["renderer"] = webgl_renderer
        
        return fingerprint
    
    def _generate_profile_id(self) -> str:
        """Gera um ID único para o perfil."""
        timestamp = datetime.now().timestamp()
        random_part = random.randint(1000, 9999)
        raw = f"{timestamp}{random_part}"
        return hashlib.md5(raw.encode()).hexdigest()[:12]
    
    def get_canvas_noise_script(self, seed: int) -> str:
        """
        Retorna o script JavaScript para adicionar ruído ao Canvas.
        
        Args:
            seed: Seed para geração de ruído consistente
            
        Returns:
            Script JavaScript para injeção
        """
        return f"""
        (function() {{
            const seed = {seed};
            
            // Função de hash simples para gerar números pseudo-aleatórios
            function seededRandom(s) {{
                s = Math.sin(s) * 10000;
                return s - Math.floor(s);
            }}
            
            // Override do toDataURL
            const originalToDataURL = HTMLCanvasElement.prototype.toDataURL;
            HTMLCanvasElement.prototype.toDataURL = function(type) {{
                if (type === 'image/png' || type === undefined) {{
                    const ctx = this.getContext('2d');
                    if (ctx) {{
                        const imageData = ctx.getImageData(0, 0, this.width, this.height);
                        const data = imageData.data;
                        
                        // Adicionar ruído sutil aos pixels
                        for (let i = 0; i < data.length; i += 4) {{
                            const noise = Math.floor(seededRandom(seed + i) * 2) - 1;
                            data[i] = Math.max(0, Math.min(255, data[i] + noise));
                            data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
                            data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
                        }}
                        
                        ctx.putImageData(imageData, 0, 0);
                    }}
                }}
                return originalToDataURL.apply(this, arguments);
            }};
            
            // Override do toBlob
            const originalToBlob = HTMLCanvasElement.prototype.toBlob;
            HTMLCanvasElement.prototype.toBlob = function(callback, type, quality) {{
                if (type === 'image/png' || type === undefined) {{
                    const ctx = this.getContext('2d');
                    if (ctx) {{
                        const imageData = ctx.getImageData(0, 0, this.width, this.height);
                        const data = imageData.data;
                        
                        for (let i = 0; i < data.length; i += 4) {{
                            const noise = Math.floor(seededRandom(seed + i) * 2) - 1;
                            data[i] = Math.max(0, Math.min(255, data[i] + noise));
                            data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
                            data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
                        }}
                        
                        ctx.putImageData(imageData, 0, 0);
                    }}
                }}
                return originalToBlob.apply(this, arguments);
            }};
            
            // Override do getImageData
            const originalGetImageData = CanvasRenderingContext2D.prototype.getImageData;
            CanvasRenderingContext2D.prototype.getImageData = function(sx, sy, sw, sh) {{
                const imageData = originalGetImageData.apply(this, arguments);
                const data = imageData.data;
                
                for (let i = 0; i < data.length; i += 4) {{
                    const noise = Math.floor(seededRandom(seed + i) * 2) - 1;
                    data[i] = Math.max(0, Math.min(255, data[i] + noise));
                    data[i + 1] = Math.max(0, Math.min(255, data[i + 1] + noise));
                    data[i + 2] = Math.max(0, Math.min(255, data[i + 2] + noise));
                }}
                
                return imageData;
            }};
        }})();
        """
    
    def get_webgl_spoof_script(self, vendor: str, renderer: str) -> str:
        """
        Retorna o script JavaScript para spoofing de WebGL.
        
        Args:
            vendor: Vendor WebGL a ser reportado
            renderer: Renderer WebGL a ser reportado
            
        Returns:
            Script JavaScript para injeção
        """
        return f"""
        (function() {{
            const vendor = "{vendor}";
            const renderer = "{renderer}";
            
            // Override WebGL getParameter
            const getParameterProxyHandler = {{
                apply: function(target, thisArg, args) {{
                    const param = args[0];
                    
                    // UNMASKED_VENDOR_WEBGL
                    if (param === 37445) {{
                        return vendor;
                    }}
                    
                    // UNMASKED_RENDERER_WEBGL
                    if (param === 37446) {{
                        return renderer;
                    }}
                    
                    return Reflect.apply(target, thisArg, args);
                }}
            }};
            
            // Aplicar para WebGL1
            const originalGetParameter = WebGLRenderingContext.prototype.getParameter;
            WebGLRenderingContext.prototype.getParameter = new Proxy(originalGetParameter, getParameterProxyHandler);
            
            // Aplicar para WebGL2
            if (typeof WebGL2RenderingContext !== 'undefined') {{
                const originalGetParameter2 = WebGL2RenderingContext.prototype.getParameter;
                WebGL2RenderingContext.prototype.getParameter = new Proxy(originalGetParameter2, getParameterProxyHandler);
            }}
            
            // Override getExtension para debug renderer info
            const originalGetExtension = WebGLRenderingContext.prototype.getExtension;
            WebGLRenderingContext.prototype.getExtension = function(name) {{
                const ext = originalGetExtension.apply(this, arguments);
                if (name === 'WEBGL_debug_renderer_info' && ext) {{
                    return {{
                        UNMASKED_VENDOR_WEBGL: 37445,
                        UNMASKED_RENDERER_WEBGL: 37446
                    }};
                }}
                return ext;
            }};
        }})();
        """
    
    def get_navigator_spoof_script(self, fingerprint: Dict) -> str:
        """
        Retorna o script JavaScript para spoofing do navigator.
        
        Args:
            fingerprint: Dicionário com configurações do fingerprint
            
        Returns:
            Script JavaScript para injeção
        """
        languages_json = json.dumps(fingerprint["languages"])
        
        return f"""
        (function() {{
            // Spoofing de propriedades do navigator
            const spoofedProps = {{
                platform: "{fingerprint['platform']}",
                hardwareConcurrency: {fingerprint['hardware']['cpu_cores']},
                deviceMemory: {fingerprint['hardware']['device_memory']},
                languages: {languages_json},
                language: "{fingerprint['locale']}"
            }};
            
            // Override usando defineProperty
            for (const [prop, value] of Object.entries(spoofedProps)) {{
                try {{
                    Object.defineProperty(navigator, prop, {{
                        get: function() {{ return value; }},
                        configurable: true
                    }});
                }} catch (e) {{
                    // Algumas propriedades podem não ser sobrescrevíveis
                }}
            }}
            
            // Spoofing de screen
            const screenProps = {{
                width: {fingerprint['screen']['width']},
                height: {fingerprint['screen']['height']},
                availWidth: {fingerprint['screen']['width']},
                availHeight: {fingerprint['screen']['height'] - 40},
                colorDepth: {fingerprint['screen']['color_depth']},
                pixelDepth: {fingerprint['screen']['color_depth']}
            }};
            
            for (const [prop, value] of Object.entries(screenProps)) {{
                try {{
                    Object.defineProperty(screen, prop, {{
                        get: function() {{ return value; }},
                        configurable: true
                    }});
                }} catch (e) {{}}
            }}
            
            // Spoofing de devicePixelRatio
            try {{
                Object.defineProperty(window, 'devicePixelRatio', {{
                    get: function() {{ return {fingerprint['screen']['pixel_ratio']}; }},
                    configurable: true
                }});
            }} catch (e) {{}}
            
            // Remover indicadores de automação
            try {{
                delete navigator.webdriver;
                Object.defineProperty(navigator, 'webdriver', {{
                    get: function() {{ return undefined; }},
                    configurable: true
                }});
            }} catch (e) {{}}
            
            // Remover propriedades do Chrome DevTools
            try {{
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
                delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
            }} catch (e) {{}}
            
            // Override do Permissions API
            const originalQuery = navigator.permissions.query;
            navigator.permissions.query = function(parameters) {{
                if (parameters.name === 'notifications') {{
                    return Promise.resolve({{ state: 'prompt', onchange: null }});
                }}
                return originalQuery.apply(this, arguments);
            }};
            
            // Spoofing de plugins (simular plugins comuns)
            try {{
                Object.defineProperty(navigator, 'plugins', {{
                    get: function() {{
                        return {{
                            length: 5,
                            item: function(i) {{
                                const plugins = [
                                    {{ name: 'Chrome PDF Plugin', filename: 'internal-pdf-viewer' }},
                                    {{ name: 'Chrome PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' }},
                                    {{ name: 'Native Client', filename: 'internal-nacl-plugin' }},
                                    {{ name: 'Chromium PDF Plugin', filename: 'internal-pdf-viewer' }},
                                    {{ name: 'Chromium PDF Viewer', filename: 'mhjfbmdgcfjbbpaeojofohoefgiehjai' }}
                                ];
                                return plugins[i] || null;
                            }},
                            namedItem: function(name) {{ return null; }},
                            refresh: function() {{}}
                        }};
                    }},
                    configurable: true
                }});
            }} catch (e) {{}}
        }})();
        """
    
    def get_timezone_spoof_script(self, timezone_name: str, offset: int) -> str:
        """
        Retorna o script JavaScript para spoofing de timezone.
        
        Args:
            timezone_name: Nome do timezone (ex: America/Sao_Paulo)
            offset: Offset em minutos do UTC
            
        Returns:
            Script JavaScript para injeção
        """
        return f"""
        (function() {{
            const targetTimezone = "{timezone_name}";
            const targetOffset = {offset};
            
            // Override Date.prototype.getTimezoneOffset
            const originalGetTimezoneOffset = Date.prototype.getTimezoneOffset;
            Date.prototype.getTimezoneOffset = function() {{
                return targetOffset;
            }};
            
            // Override Intl.DateTimeFormat
            const originalDateTimeFormat = Intl.DateTimeFormat;
            Intl.DateTimeFormat = function(locales, options) {{
                if (options && !options.timeZone) {{
                    options.timeZone = targetTimezone;
                }} else if (!options) {{
                    options = {{ timeZone: targetTimezone }};
                }}
                return new originalDateTimeFormat(locales, options);
            }};
            Intl.DateTimeFormat.prototype = originalDateTimeFormat.prototype;
            
            // Override resolvedOptions
            const originalResolvedOptions = Intl.DateTimeFormat.prototype.resolvedOptions;
            Intl.DateTimeFormat.prototype.resolvedOptions = function() {{
                const result = originalResolvedOptions.apply(this, arguments);
                result.timeZone = targetTimezone;
                return result;
            }};
        }})();
        """
    
    def get_full_spoof_script(self, fingerprint: Dict) -> str:
        """
        Retorna o script completo de spoofing combinando todos os scripts.
        
        Args:
            fingerprint: Dicionário com configurações do fingerprint
            
        Returns:
            Script JavaScript completo para injeção
        """
        scripts = [
            self.get_canvas_noise_script(fingerprint["canvas_seed"]),
            self.get_webgl_spoof_script(
                fingerprint["webgl"]["vendor"],
                fingerprint["webgl"]["renderer"]
            ),
            self.get_navigator_spoof_script(fingerprint),
            self.get_timezone_spoof_script(
                fingerprint["timezone"]["name"],
                fingerprint["timezone"]["offset"]
            ),
        ]
        
        return "\n\n".join(scripts)
    
    def get_available_user_agents(self) -> List[str]:
        """Retorna a lista de User-Agents disponíveis."""
        return self.USER_AGENTS.copy()
    
    def get_available_resolutions(self) -> List[Tuple[int, int]]:
        """Retorna a lista de resoluções disponíveis."""
        return self.SCREEN_RESOLUTIONS.copy()
    
    def get_available_countries(self) -> List[str]:
        """Retorna a lista de países disponíveis."""
        return list(self.TIMEZONES.keys())
    
    def get_available_webgl_vendors(self) -> List[str]:
        """Retorna a lista de vendors WebGL disponíveis."""
        return self.WEBGL_VENDORS.copy()
    
    def get_available_webgl_renderers(self) -> List[str]:
        """Retorna a lista de renderers WebGL disponíveis."""
        return self.WEBGL_RENDERERS.copy()


# Teste do módulo
if __name__ == "__main__":
    generator = FingerprintGenerator()
    
    print("=== Teste do Fingerprint Generator ===\n")
    
    # Gerar fingerprint brasileiro
    fp = generator.generate_brazilian_fingerprint()
    print("Fingerprint Brasileiro:")
    print(json.dumps(fp, indent=2))
    
    print("\n" + "="*50 + "\n")
    
    # Gerar fingerprint customizado
    fp_custom = generator.generate_custom_fingerprint(
        resolution=(1920, 1080),
        country="US"
    )
    print("Fingerprint Customizado (US):")
    print(json.dumps(fp_custom, indent=2))
