import re
import json
import os
from typing import Dict, Optional

class AddressExtractor:
    """
    Extrai endereços de textos e gerencia um banco de dados local de reserva.
    """
    
    DB_FILE = "enderecos_reserva.json"
    
    def __init__(self):
        self.enderecos = self._carregar_banco()
        
    def _carregar_banco(self) -> list:
        """Carrega o banco de endereços do arquivo JSON"""
        if os.path.exists(self.DB_FILE):
            try:
                with open(self.DB_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError, PermissionError) as e:
                print(f"Aviso: Erro ao carregar banco de endereços: {e}")
                return []
        return []
        
    def _salvar_banco(self):
        """Salva o banco de endereços no arquivo JSON"""
        try:
            with open(self.DB_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.enderecos, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Erro ao salvar banco de endereços: {e}")

    def extrair_endereco(self, texto: str) -> Optional[Dict]:
        """
        Tenta extrair um endereço completo de um texto.
        Procura por padrões comuns de vazamento de dados (CEP, Rua, Bairro, Cidade, UF).
        """
        # Padrão simples para capturar CEP (xxxxx-xxx ou xxxxxxxx)
        cep_match = re.search(r'\b(\d{5}-?\d{3})\b', texto)
        if not cep_match:
            return None
            
        cep = cep_match.group(1)
        
        # Se já temos esse CEP no banco, ignoramos para evitar duplicatas
        if any(e['cep'] == cep for e in self.enderecos):
            return None

        # Tenta extrair outros campos baseados em palavras-chave comuns
        endereco = {
            'cep': cep,
            'logradouro': '',
            'bairro': '',
            'cidade': '',
            'estado': '',
            'uf': '',
            'numero': ''
        }
        
        # Regex para capturar campos (ex: "Rua: Flores", "Cidade: São Paulo")
        # Aceita variações como "Endereço:", "End:", "Rua", etc.
        
        # Logradouro
        log_match = re.search(r'(?:Rua|Av|Avenida|Logradouro|Endereço|End)[:\s]+([^,\n]+)', texto, re.IGNORECASE)
        if log_match:
            endereco['logradouro'] = log_match.group(1).strip()
            
        # Bairro
        bairro_match = re.search(r'(?:Bairro)[:\s]+([^,\n]+)', texto, re.IGNORECASE)
        if bairro_match:
            endereco['bairro'] = bairro_match.group(1).strip()
            
        # Cidade
        cidade_match = re.search(r'(?:Cidade|Município)[:\s]+([^,\n/-]+)', texto, re.IGNORECASE)
        if cidade_match:
            endereco['cidade'] = cidade_match.group(1).strip()
            
        # Estado/UF
        uf_match = re.search(r'(?:Estado|UF)[:\s]+([A-Z]{2})', texto, re.IGNORECASE)
        if uf_match:
            endereco['uf'] = uf_match.group(1).strip()
            endereco['estado'] = endereco['uf'] # Simplificação
            
        # Número
        num_match = re.search(r'(?:Número|Num|Nº)[:\s]+(\d+)', texto, re.IGNORECASE)
        if num_match:
            endereco['numero'] = num_match.group(1).strip()

        # Só salva se tiver pelo menos Logradouro e Cidade, ou se parecer muito completo
        if endereco['logradouro'] and endereco['cidade']:
            self.enderecos.append(endereco)
            self._salvar_banco()
            return endereco
            
        return None

    def get_reserva(self, uf: str = None) -> Optional[Dict]:
        """Retorna um endereço do banco de reserva, opcionalmente filtrado por UF"""
        import random
        
        candidatos = self.enderecos
        if uf:
            candidatos = [e for e in self.enderecos if e.get('uf') == uf or e.get('estado') == uf]
            
        if candidatos:
            return random.choice(candidatos)
        return None
