#!/usr/bin/env python3
"""
Proxy Manager - Módulo de Gerenciamento de Proxies
Telegram Collector Pro v9.0 - Navegador Seguro

Este módulo gerencia a configuração de proxies, incluindo suporte
a autenticação via extensão do Chrome.
"""

import os
import json
import zipfile
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple
from dataclasses import dataclass

from app.core.paths import BASE_DIR


@dataclass
class ProxyConfig:
    """Configuração de proxy."""
    host: str
    port: int
    username: Optional[str] = None
    password: Optional[str] = None
    
    @property
    def requires_auth(self) -> bool:
        """Verifica se o proxy requer autenticação."""
        return bool(self.username and self.password)
    
    @property
    def address(self) -> str:
        """Retorna o endereço do proxy no formato host:port."""
        return f"{self.host}:{self.port}"
    
    def to_dict(self) -> Dict:
        """Converte para dicionário."""
        return {
            "host": self.host,
            "port": self.port,
            "username": self.username,
            "password": self.password,
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> "ProxyConfig":
        """Cria uma instância a partir de um dicionário."""
        return cls(
            host=data.get("host", ""),
            port=data.get("port", 0),
            username=data.get("username"),
            password=data.get("password"),
        )


class ProxyManager:
    """
    Gerenciador de proxies para o navegador.
    Suporta proxies com e sem autenticação.
    """
    
    def __init__(self, extensions_dir: Optional[Path] = None):
        """
        Inicializa o gerenciador de proxies.
        
        Args:
            extensions_dir: Diretório para armazenar extensões geradas
        """
        if extensions_dir is None:
            self.extensions_dir = BASE_DIR / "browser_extensions" / "proxy"
        elif isinstance(extensions_dir, str):
            self.extensions_dir = Path(extensions_dir)
        else:
            self.extensions_dir = extensions_dir
        self.extensions_dir.mkdir(parents=True, exist_ok=True)
        self._temp_extensions = []
    
    def parse_proxy_string(self, proxy_string: str) -> Optional[ProxyConfig]:
        """
        Parseia uma string de proxy nos formatos suportados.
        
        Formatos suportados:
        - IP:Porta
        - IP:Porta:Usuario:Senha
        - host:porta
        - host:porta:usuario:senha
        
        Args:
            proxy_string: String do proxy
            
        Returns:
            ProxyConfig ou None se inválido
        """
        if not proxy_string or not proxy_string.strip():
            return None
        
        proxy_string = proxy_string.strip()
        parts = proxy_string.split(":")
        
        if len(parts) < 2:
            return None
        
        try:
            host = parts[0]
            port = int(parts[1])
            
            if len(parts) == 2:
                # Formato: IP:Porta
                return ProxyConfig(host=host, port=port)
            elif len(parts) == 4:
                # Formato: IP:Porta:Usuario:Senha
                username = parts[2]
                password = parts[3]
                return ProxyConfig(
                    host=host,
                    port=port,
                    username=username,
                    password=password
                )
            else:
                # Formato inválido
                return None
                
        except (ValueError, IndexError):
            return None
    
    def create_proxy_extension(self, proxy: ProxyConfig) -> Optional[str]:
        """
        Cria uma extensão do Chrome para autenticação de proxy.
        
        Args:
            proxy: Configuração do proxy
            
        Returns:
            Caminho para a extensão ou None se não for necessária
        """
        if not proxy.requires_auth:
            return None
        
        # Criar diretório temporário para a extensão
        ext_dir = self.extensions_dir / f"proxy_auth_{proxy.host}_{proxy.port}"
        ext_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar manifest.json
        manifest = {
            "version": "1.0.0",
            "manifest_version": 3,
            "name": "Proxy Auth Helper",
            "description": "Helper extension for proxy authentication",
            "permissions": [
                "proxy",
                "tabs",
                "webRequest",
                "webRequestAuthProvider",
                "storage"
            ],
            "host_permissions": [
                "<all_urls>"
            ],
            "background": {
                "service_worker": "background.js"
            },
            "minimum_chrome_version": "88"
        }
        
        manifest_path = ext_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Criar background.js com a lógica de autenticação
        background_js = f"""
// Configuração do proxy
const proxyConfig = {{
    host: "{proxy.host}",
    port: {proxy.port},
    username: "{proxy.username}",
    password: "{proxy.password}"
}};

// Configurar proxy
chrome.proxy.settings.set({{
    value: {{
        mode: "fixed_servers",
        rules: {{
            singleProxy: {{
                scheme: "http",
                host: proxyConfig.host,
                port: proxyConfig.port
            }},
            bypassList: ["localhost", "127.0.0.1"]
        }}
    }},
    scope: "regular"
}});

// Handler para autenticação
chrome.webRequest.onAuthRequired.addListener(
    function(details, callbackFn) {{
        console.log("Auth required for:", details.url);
        callbackFn({{
            authCredentials: {{
                username: proxyConfig.username,
                password: proxyConfig.password
            }}
        }});
    }},
    {{ urls: ["<all_urls>"] }},
    ["asyncBlocking"]
);

console.log("Proxy Auth Helper loaded for", proxyConfig.host + ":" + proxyConfig.port);
"""
        
        background_path = ext_dir / "background.js"
        with open(background_path, "w") as f:
            f.write(background_js)
        
        self._temp_extensions.append(str(ext_dir))
        return str(ext_dir)
    
    def create_proxy_extension_mv2(self, proxy: ProxyConfig) -> Optional[str]:
        """
        Cria uma extensão do Chrome (Manifest V2) para autenticação de proxy.
        Compatível com versões mais antigas do Chrome e undetected-chromedriver.
        
        Args:
            proxy: Configuração do proxy
            
        Returns:
            Caminho para a extensão ou None se não for necessária
        """
        if not proxy.requires_auth:
            return None
        
        # Criar diretório temporário para a extensão
        ext_dir = self.extensions_dir / f"proxy_auth_mv2_{proxy.host}_{proxy.port}"
        ext_dir.mkdir(parents=True, exist_ok=True)
        
        # Criar manifest.json (Manifest V2)
        manifest = {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth Helper",
            "description": "Helper extension for proxy authentication",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"],
                "persistent": True
            },
            "minimum_chrome_version": "76.0.0"
        }
        
        manifest_path = ext_dir / "manifest.json"
        with open(manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        
        # Criar background.js com a lógica de autenticação (MV2)
        background_js = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{proxy.host}",
            port: parseInt({proxy.port})
        }},
        bypassList: ["localhost"]
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{proxy.username}",
            password: "{proxy.password}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);

console.log("Proxy configured: {proxy.host}:{proxy.port}");
"""
        
        background_path = ext_dir / "background.js"
        with open(background_path, "w") as f:
            f.write(background_js)
        
        self._temp_extensions.append(str(ext_dir))
        return str(ext_dir)
    
    def create_proxy_extension_zip(self, proxy: ProxyConfig) -> Optional[str]:
        """
        Cria uma extensão do Chrome em formato ZIP para autenticação de proxy.
        
        Args:
            proxy: Configuração do proxy
            
        Returns:
            Caminho para o arquivo ZIP ou None se não for necessária
        """
        if not proxy.requires_auth:
            return None
        
        # Criar arquivos da extensão
        manifest = {
            "version": "1.0.0",
            "manifest_version": 2,
            "name": "Proxy Auth Helper",
            "permissions": [
                "proxy",
                "tabs",
                "unlimitedStorage",
                "storage",
                "<all_urls>",
                "webRequest",
                "webRequestBlocking"
            ],
            "background": {
                "scripts": ["background.js"]
            },
            "minimum_chrome_version": "76.0.0"
        }
        
        background_js = f"""
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{proxy.host}",
            port: parseInt({proxy.port})
        }},
        bypassList: ["localhost"]
    }}
}};

chrome.proxy.settings.set({{value: config, scope: "regular"}}, function() {{}});

function callbackFn(details) {{
    return {{
        authCredentials: {{
            username: "{proxy.username}",
            password: "{proxy.password}"
        }}
    }};
}}

chrome.webRequest.onAuthRequired.addListener(
    callbackFn,
    {{urls: ["<all_urls>"]}},
    ['blocking']
);
"""
        
        # Criar arquivo ZIP
        zip_path = self.extensions_dir / f"proxy_auth_{proxy.host}_{proxy.port}.zip"
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("manifest.json", json.dumps(manifest, indent=2))
            zf.writestr("background.js", background_js)
        
        self._temp_extensions.append(str(zip_path))
        return str(zip_path)
    
    def get_chrome_proxy_args(self, proxy: ProxyConfig) -> list:
        """
        Retorna os argumentos do Chrome para configurar proxy sem autenticação.
        
        Args:
            proxy: Configuração do proxy
            
        Returns:
            Lista de argumentos para o Chrome
        """
        if proxy.requires_auth:
            # Para proxies autenticados, usar extensão
            return []
        
        return [f"--proxy-server=http://{proxy.host}:{proxy.port}"]
    
    def validate_proxy(self, proxy_string: str) -> Tuple[bool, str]:
        """
        Valida uma string de proxy.
        
        Args:
            proxy_string: String do proxy para validar
            
        Returns:
            Tupla (válido, mensagem)
        """
        if not proxy_string or not proxy_string.strip():
            return False, "Proxy não pode estar vazio"
        
        proxy = self.parse_proxy_string(proxy_string)
        
        if proxy is None:
            return False, "Formato inválido. Use IP:Porta ou IP:Porta:Usuario:Senha"
        
        if not proxy.host:
            return False, "Host do proxy não pode estar vazio"
        
        if proxy.port <= 0 or proxy.port > 65535:
            return False, "Porta deve estar entre 1 e 65535"
        
        if proxy.requires_auth:
            if not proxy.username:
                return False, "Usuário não pode estar vazio para proxy autenticado"
            if not proxy.password:
                return False, "Senha não pode estar vazia para proxy autenticado"
        
        return True, "Proxy válido"
    
    def cleanup_temp_extensions(self):
        """Remove extensões temporárias criadas."""
        import shutil
        
        for ext_path in self._temp_extensions:
            try:
                path = Path(ext_path)
                if path.exists():
                    if path.is_dir():
                        shutil.rmtree(path)
                    else:
                        path.unlink()
            except Exception as e:
                print(f"Erro ao remover extensão temporária {ext_path}: {e}")
        
        self._temp_extensions.clear()
    
    def get_proxy_info(self, proxy: ProxyConfig) -> Dict:
        """
        Retorna informações formatadas sobre o proxy.
        
        Args:
            proxy: Configuração do proxy
            
        Returns:
            Dicionário com informações do proxy
        """
        return {
            "address": proxy.address,
            "host": proxy.host,
            "port": proxy.port,
            "authenticated": proxy.requires_auth,
            "username": proxy.username if proxy.requires_auth else None,
        }


class ProxyRotator:
    """
    Rotacionador de proxies para alternar entre múltiplos proxies.
    """
    
    def __init__(self, proxies: list = None):
        """
        Inicializa o rotacionador.
        
        Args:
            proxies: Lista de strings de proxy
        """
        self.proxy_manager = ProxyManager()
        self.proxies = []
        self.current_index = 0
        
        if proxies:
            for proxy_str in proxies:
                proxy = self.proxy_manager.parse_proxy_string(proxy_str)
                if proxy:
                    self.proxies.append(proxy)
    
    def add_proxy(self, proxy_string: str) -> bool:
        """
        Adiciona um proxy à lista.
        
        Args:
            proxy_string: String do proxy
            
        Returns:
            True se adicionado com sucesso
        """
        proxy = self.proxy_manager.parse_proxy_string(proxy_string)
        if proxy:
            self.proxies.append(proxy)
            return True
        return False
    
    def remove_proxy(self, index: int) -> bool:
        """
        Remove um proxy da lista.
        
        Args:
            index: Índice do proxy
            
        Returns:
            True se removido com sucesso
        """
        if 0 <= index < len(self.proxies):
            del self.proxies[index]
            if self.current_index >= len(self.proxies):
                self.current_index = 0
            return True
        return False
    
    def get_next(self) -> Optional[ProxyConfig]:
        """
        Retorna o próximo proxy na rotação.
        
        Returns:
            ProxyConfig ou None se não houver proxies
        """
        if not self.proxies:
            return None
        
        proxy = self.proxies[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxies)
        return proxy
    
    def get_current(self) -> Optional[ProxyConfig]:
        """
        Retorna o proxy atual sem avançar.
        
        Returns:
            ProxyConfig ou None se não houver proxies
        """
        if not self.proxies:
            return None
        return self.proxies[self.current_index]
    
    def get_random(self) -> Optional[ProxyConfig]:
        """
        Retorna um proxy aleatório.
        
        Returns:
            ProxyConfig ou None se não houver proxies
        """
        import random
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def count(self) -> int:
        """Retorna o número de proxies na lista."""
        return len(self.proxies)
    
    def clear(self):
        """Remove todos os proxies."""
        self.proxies.clear()
        self.current_index = 0


# Teste do módulo
if __name__ == "__main__":
    print("=== Teste do Proxy Manager ===\n")
    
    manager = ProxyManager()
    
    # Testar parsing de proxies
    test_proxies = [
        "192.168.1.1:8080",
        "proxy.example.com:3128",
        "10.0.0.1:8080:user:pass123",
        "proxy.test.com:3128:admin:secret",
        "invalid",
        "192.168.1.1",
        "",
    ]
    
    for proxy_str in test_proxies:
        proxy = manager.parse_proxy_string(proxy_str)
        valid, msg = manager.validate_proxy(proxy_str)
        
        print(f"Proxy: '{proxy_str}'")
        print(f"  Válido: {valid}")
        print(f"  Mensagem: {msg}")
        
        if proxy:
            print(f"  Host: {proxy.host}")
            print(f"  Porta: {proxy.port}")
            print(f"  Autenticado: {proxy.requires_auth}")
            if proxy.requires_auth:
                print(f"  Usuário: {proxy.username}")
        print()
    
    # Testar criação de extensão
    print("\n=== Teste de Extensão de Proxy ===\n")
    
    auth_proxy = manager.parse_proxy_string("192.168.1.1:8080:user:pass123")
    if auth_proxy:
        ext_path = manager.create_proxy_extension_mv2(auth_proxy)
        print(f"Extensão criada em: {ext_path}")
        
        # Verificar arquivos criados
        if ext_path:
            from pathlib import Path
            ext_dir = Path(ext_path)
            print(f"Arquivos na extensão:")
            for f in ext_dir.iterdir():
                print(f"  - {f.name}")
    
    # Testar rotacionador
    print("\n=== Teste do Proxy Rotator ===\n")
    
    rotator = ProxyRotator([
        "192.168.1.1:8080",
        "192.168.1.2:8080",
        "192.168.1.3:8080",
    ])
    
    print(f"Total de proxies: {rotator.count()}")
    
    for i in range(5):
        proxy = rotator.get_next()
        print(f"Rotação {i+1}: {proxy.address if proxy else 'None'}")
    
    # Cleanup
    manager.cleanup_temp_extensions()
    print("\nExtensões temporárias removidas.")
