#!/usr/bin/env python3
"""
Formatador de Contas Premium
Processa e formata listas de credenciais (e-mail:senha) em modelos organizados.
"""
import re
from dataclasses import dataclass
from typing import List, Optional, Tuple


@dataclass
class Credential:
    """Representa uma credencial processada"""
    email: str
    password: str
    provider: str
    provider_link: str
    domain: str


class AccountFormatter:
    """Classe para processar e formatar credenciais de contas"""
    
    # Padrão regex para capturar email:senha com vários separadores
    CREDENTIAL_PATTERN = re.compile(
        r'([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\s*[:|\-\s]\s*([^\s\r\n]+)',
        re.MULTILINE
    )
    
    # Mapeamento de domínios para provedores e links
    PROVIDERS = {
        # Microsoft
        'outlook.com': ('Outlook', 'https://www.microsoft.com/pt-br/microsoft-365/outlook/log-in'),
        'hotmail.com': ('Hotmail', 'https://www.microsoft.com/pt-br/microsoft-365/outlook/log-in'),
        'hotmail.com.br': ('Hotmail', 'https://www.microsoft.com/pt-br/microsoft-365/outlook/log-in'),
        'live.com': ('Live', 'https://www.microsoft.com/pt-br/microsoft-365/outlook/log-in'),
        'msn.com': ('MSN', 'https://www.microsoft.com/pt-br/microsoft-365/outlook/log-in'),
        # Google
        'gmail.com': ('Gmail', 'https://mail.google.com/'),
        'googlemail.com': ('Gmail', 'https://mail.google.com/'),
        # Yahoo
        'yahoo.com': ('Yahoo', 'https://mail.yahoo.com/'),
        'yahoo.com.br': ('Yahoo', 'https://mail.yahoo.com/'),
        'ymail.com': ('Yahoo', 'https://mail.yahoo.com/'),
        # AOL
        'aol.com': ('AOL', 'https://mail.aol.com/'),
        # Apple
        'icloud.com': ('iCloud', 'https://www.icloud.com/mail'),
        'me.com': ('iCloud', 'https://www.icloud.com/mail'),
        'mac.com': ('iCloud', 'https://www.icloud.com/mail'),
        # Proton
        'protonmail.com': ('ProtonMail', 'https://mail.protonmail.com/'),
        'proton.me': ('ProtonMail', 'https://mail.protonmail.com/'),
        # Outros
        'edny.net': ('Mail.tm', 'https://mail.tm/pt/'),
        'mail.com': ('Mail.com', 'https://www.mail.com/int/'),
        'gmx.com': ('GMX', 'https://www.gmx.com/'),
        'zoho.com': ('Zoho', 'https://www.zoho.com/mail/login.html'),
        'bol.com.br': ('BOL', 'https://www.bol.uol.com.br/'),
        'uol.com.br': ('UOL', 'https://email.uol.com.br/'),
        'terra.com.br': ('Terra', 'https://mail.terra.com.br/'),
        'ig.com.br': ('iG', 'https://email.ig.com.br/'),
        'globo.com': ('Globo', 'https://email.globo.com/'),
        'globomail.com': ('Globo', 'https://email.globo.com/'),
        'zipmail.com.br': ('Zipmail', 'https://www.zipmail.com.br/'),
    }
    
    # Serviços pré-definidos com emojis
    SERVICES = {
        'Netflix': '🎬',
        'Spotify': '🎵',
        'Crunchyroll': '🍥',
        'Paramount+': '⭐',
        'Amazon Prime': '📦',
        'Disney+': '🏰',
        'HBO Max': '🎭',
        'Apple TV+': '🍎',
        'Globoplay': '🌐',
        'YouTube Premium': '▶️',
        'Deezer': '🎧',
        'Tidal': '🌊',
        'Xbox Game Pass': '🎮',
        'PlayStation Plus': '🎮',
        'Steam': '🎮',
        'EA Play': '⚽',
        'Ubisoft+': '🎯',
        'NordVPN': '🔒',
        'ExpressVPN': '🛡️',
        'Surfshark': '🦈',
        'Canva Pro': '🎨',
        'Adobe CC': '🖌️',
        'Office 365': '📊',
        'Dropbox': '📁',
        'Google One': '☁️',
        'iCloud+': '☁️',
        'ChatGPT Plus': '🤖',
        'Midjourney': '🖼️',
        'Duolingo Plus': '🦉',
        'Coursera Plus': '📚',
        'LinkedIn Premium': '💼',
        'Tinder Gold': '🔥',
        'Bumble Premium': '🐝',
        'Personalizado': '⚙️',
    }
    
    def __init__(self):
        self._cancelled = False
    
    def cancel(self):
        """Cancela o processamento"""
        self._cancelled = True
    
    def reset_cancel(self):
        """Reseta o flag de cancelamento"""
        self._cancelled = False
    
    def get_services(self) -> dict:
        """Retorna a lista de serviços disponíveis"""
        return self.SERVICES.copy()
    
    def parse_credentials(self, text: str) -> List[Credential]:
        """
        Processa o texto de entrada e extrai as credenciais.
        
        Args:
            text: Texto contendo as credenciais no formato email:senha
            
        Returns:
            Lista de objetos Credential
        """
        credentials = []
        matches = self.CREDENTIAL_PATTERN.findall(text)
        
        for email, password in matches:
            if self._cancelled:
                break
            
            email = email.strip().lower()
            password = password.strip()
            
            # Extrair domínio
            domain = email.split('@')[1] if '@' in email else ''
            
            # Identificar provedor
            provider, link = self._get_provider_info(domain)
            
            credentials.append(Credential(
                email=email,
                password=password,
                provider=provider,
                provider_link=link,
                domain=domain
            ))
        
        return credentials
    
    def _get_provider_info(self, domain: str) -> Tuple[str, str]:
        """
        Identifica o provedor de e-mail pelo domínio.
        
        Args:
            domain: Domínio do e-mail
            
        Returns:
            Tupla (nome_provedor, link_acesso)
        """
        domain = domain.lower()
        
        if domain in self.PROVIDERS:
            return self.PROVIDERS[domain]
        
        # Provedor desconhecido
        return ('Outro', f'https://mail.{domain}/')
    
    def format_model_classic(self, cred: Credential, service: str, service_emoji: str, 
                            service_password: Optional[str] = None) -> str:
        """
        Modelo 1: CLÁSSICO
        O formato mais usado e tradicional.
        """
        pwd = service_password if service_password else cred.password
        
        lines = [
            f"{service_emoji} {service.upper()}",
            f"📧 Email: {cred.email}",
            f"🔑 Senha: {pwd}",
            "=" * 35,
            f"📬 {cred.provider}",
            f"📧 Email: {cred.email}",
            f"🔐 Senha: {cred.password}",
            f"→ {cred.provider_link}",
            ""
        ]
        return '\n'.join(lines)
    
    def format_model_minimalist(self, cred: Credential, service: str, service_emoji: str,
                                service_password: Optional[str] = None) -> str:
        """
        Modelo 2: MINIMALISTA
        Formato limpo e direto.
        """
        pwd = service_password if service_password else cred.password
        
        lines = [
            f"{service_emoji} {service}",
            f"{cred.email} | {pwd}",
            f"→ {cred.provider_link}",
            ""
        ]
        return '\n'.join(lines)
    
    def format_model_detailed(self, cred: Credential, service: str, service_emoji: str,
                              service_password: Optional[str] = None) -> str:
        """
        Modelo 3: DETALHADO (BOX DESIGN)
        Estrutura organizada com bordas.
        """
        pwd = service_password if service_password else cred.password
        
        lines = [
            f"┌─────────────────────────────────────┐",
            f"│ {service_emoji} {service.upper():<32} │",
            f"├─────────────────────────────────────┤",
            f"│ 📧 Email Principal                  │",
            f"│    {cred.email:<32} │",
            f"│ 🔑 Senha Serviço                    │",
            f"│    {pwd:<32} │",
            f"├─────────────────────────────────────┤",
            f"│ 📬 Email Acesso ({cred.provider})".ljust(38) + "│",
            f"│    {cred.email:<32} │",
            f"│ 🔐 Senha Email                      │",
            f"│    {cred.password:<32} │",
            f"├─────────────────────────────────────┤",
            f"│ 🔗 Link: {cred.provider_link[:27]:<27} │",
            f"│ ✓ Status: Ativo                     │",
            f"└─────────────────────────────────────┘",
            ""
        ]
        return '\n'.join(lines)
    
    def format_model_compact(self, cred: Credential, service: str, service_emoji: str,
                             service_password: Optional[str] = None) -> str:
        """
        Modelo 4: COMPACTO (ONE-LINER)
        Todas as informações em uma única linha.
        """
        pwd = service_password if service_password else cred.password
        
        return f"[{service_emoji} {service}] {cred.email} | {pwd} | {cred.provider} | {cred.provider_link}\n"

    def format_model_pro_complete(self, cred: Credential, service: str, service_emoji: str,
                                  service_password: Optional[str] = None) -> str:
        """
        Modelo 5: PRO COMPLETO
        Inspirado no Organizador PRO em HTML.
        """
        pwd = service_password if service_password else cred.password
        lines = [
            f"{service_emoji} {service.upper()}",
            f"📧 Email: {cred.email}",
            f"🔑 Senha: {pwd}",
            "===================================",
            "📧 EMAIL (recuperação)",
            f"📧 Email: {cred.email}",
            f"🔑 Senha: {cred.password}",
            f"🔗 Link: {cred.provider_link}",
            "",
        ]
        return "\n".join(lines)

    def format_model_pro_simple(self, cred: Credential, service: str, service_emoji: str,
                                service_password: Optional[str] = None) -> str:
        """
        Modelo 6: PRO SIMPLES
        Apenas serviço, email e senha final.
        """
        pwd = service_password if service_password else cred.password
        return f"{service_emoji} {service.upper()}\n📧 {cred.email}\n🔑 {pwd}\n\n"

    def format_model_pro_minimal(self, cred: Credential, service: str, service_emoji: str,
                                 service_password: Optional[str] = None) -> str:
        """
        Modelo 7: PRO MINIMAL
        Uma linha curta para listas grandes.
        """
        pwd = service_password if service_password else cred.password
        return f"[{service_emoji} {service}] {cred.email} | {pwd} | Email | {cred.provider_link}\n"

    def format_model_pipe_table(self, cred: Credential, service: str, service_emoji: str,
                                service_password: Optional[str] = None) -> str:
        """
        Modelo 8: TABELA PIPE
        Bom para planilha, filtros e importação.
        """
        pwd = service_password if service_password else cred.password
        return f"{service}|{cred.email}|{pwd}|{cred.password}|{cred.domain}|{cred.provider}|{cred.provider_link}\n"

    def format_model_jsonl(self, cred: Credential, service: str, service_emoji: str,
                           service_password: Optional[str] = None) -> str:
        """
        Modelo 9: JSON LINES
        Uma conta por linha em JSON.
        """
        import json

        pwd = service_password if service_password else cred.password
        data = {
            "service": service,
            "email": cred.email,
            "service_password": pwd,
            "email_password": cred.password,
            "domain": cred.domain,
            "provider": cred.provider,
            "provider_link": cred.provider_link,
        }
        return json.dumps(data, ensure_ascii=False) + "\n"
    
    def format_credentials(self, credentials: List[Credential], model: int,
                          service: str, service_emoji: str,
                          service_password: Optional[str] = None,
                          progress_callback=None) -> str:
        """
        Formata uma lista de credenciais usando o modelo especificado.
        
        Args:
            credentials: Lista de credenciais
            model: Número do modelo (1-9)
            service: Nome do serviço
            service_emoji: Emoji do serviço
            service_password: Senha do serviço (opcional)
            progress_callback: Função de callback para progresso
            
        Returns:
            Texto formatado
        """
        self.reset_cancel()
        
        # Selecionar função de formatação
        formatters = {
            1: self.format_model_classic,
            2: self.format_model_minimalist,
            3: self.format_model_detailed,
            4: self.format_model_compact,
            5: self.format_model_pro_complete,
            6: self.format_model_pro_simple,
            7: self.format_model_pro_minimal,
            8: self.format_model_pipe_table,
            9: self.format_model_jsonl,
        }
        
        formatter = formatters.get(model, self.format_model_classic)
        
        result = []
        total = len(credentials)
        
        for i, cred in enumerate(credentials):
            if self._cancelled:
                break
            
            formatted = formatter(cred, service, service_emoji, service_password)
            result.append(formatted)
            
            if progress_callback:
                progress_callback(i + 1, total)
        
        return ''.join(result)
    
    def process_and_format(self, text: str, model: int, service: str,
                          service_password: Optional[str] = None,
                          progress_callback=None) -> Tuple[str, int]:
        """
        Processa o texto de entrada e retorna as credenciais formatadas.
        
        Args:
            text: Texto com credenciais
            model: Número do modelo de formatação
            service: Nome do serviço
            service_password: Senha do serviço (opcional)
            progress_callback: Função de callback para progresso
            
        Returns:
            Tupla (texto_formatado, quantidade_processada)
        """
        # Obter emoji do serviço
        service_emoji = self.SERVICES.get(service, '⚙️')
        
        # Processar credenciais
        credentials = self.parse_credentials(text)
        
        if not credentials:
            return "", 0
        
        # Formatar
        formatted = self.format_credentials(
            credentials, model, service, service_emoji,
            service_password, progress_callback
        )
        
        return formatted, len(credentials)


# Teste rápido
if __name__ == '__main__':
    formatter = AccountFormatter()
    
    test_input = """
    teste@gmail.com:senha123
    usuario@hotmail.com | minhasenha
    outro@yahoo.com - pass456
    email@outlook.com:teste789
    """
    
    print("=== TESTE DO FORMATADOR DE CONTAS ===\n")
    
    for model in range(1, 5):
        print(f"\n--- MODELO {model} ---\n")
        result, count = formatter.process_and_format(
            test_input, model, "Netflix"
        )
        print(result)
        print(f"Total processado: {count} contas")
