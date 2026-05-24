#!/usr/bin/env python3
"""
Gerador de Endereços Brasileiros - Integração 4Devs
Versão 3.0 - Parser Robusto
Gera endereços completos e válidos utilizando a API do 4Devs
"""
import requests
import time
import urllib3
import re
from typing import List, Dict, Optional, Callable
from dataclasses import dataclass
from address_reserve import AddressExtractor

# Desativar avisos de SSL inseguro
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

@dataclass
class Endereco:
    """Classe para representar um endereço completo"""
    cep: str
    logradouro: str
    bairro: str
    cidade: str
    estado: str
    uf: str
    numero: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'cep': self.cep,
            'logradouro': self.logradouro,
            'bairro': self.bairro,
            'cidade': self.cidade,
            'estado': self.estado,
            'uf': self.uf,
            'numero': self.numero
        }
    
    def format_completo(self, com_pontuacao: bool = True) -> str:
        """Retorna endereço formatado completo"""
        cep = self.cep if com_pontuacao else self.cep.replace('-', '')
        return f"{self.logradouro}, {self.numero} - {self.bairro}, {self.cidade} - {self.uf}, {cep}"
    
    def format_linha(self, com_pontuacao: bool = True) -> str:
        """Retorna endereço em formato de linha única"""
        cep = self.cep if com_pontuacao else self.cep.replace('-', '')
        return f"{cep}|{self.logradouro}|{self.bairro}|{self.cidade}|{self.uf}"


class AddressGenerator:
    """Gerador de endereços brasileiros válidos via 4Devs"""
    
    API_URL = "https://www.4devs.com.br/ferramentas_online.php"
    
    # Estados brasileiros para referência
    ESTADOS = {
        'AC': 'Acre', 'AL': 'Alagoas', 'AM': 'Amazonas', 'AP': 'Amapá',
        'BA': 'Bahia', 'CE': 'Ceará', 'DF': 'Distrito Federal', 'ES': 'Espírito Santo',
        'GO': 'Goiás', 'MA': 'Maranhão', 'MG': 'Minas Gerais', 'MS': 'Mato Grosso do Sul',
        'MT': 'Mato Grosso', 'PA': 'Pará', 'PB': 'Paraíba', 'PE': 'Pernambuco',
        'PI': 'Piauí', 'PR': 'Paraná', 'RJ': 'Rio de Janeiro', 'RN': 'Rio Grande do Norte',
        'RO': 'Rondônia', 'RR': 'Roraima', 'RS': 'Rio Grande do Sul', 'SC': 'Santa Catarina',
        'SE': 'Sergipe', 'SP': 'São Paulo', 'TO': 'Tocantins'
    }
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://www.4devs.com.br',
            'Referer': 'https://www.4devs.com.br/gerador_de_cep',
            'X-Requested-With': 'XMLHttpRequest'
        })
        self._cancel = False
        self.last_source = ""
        self.extractor = AddressExtractor()

    def cancel(self):
        """Cancela a geração em andamento"""
        self._cancel = True

    def _fetch_address(self, uf: str = "", cidade: str = "") -> Optional[Endereco]:
        """Busca um único endereço na API do 4Devs"""
        try:
            payload = {
                'acao': 'gerar_cep',
                'cep_estado': uf if uf else '',
                'cep_cidade': cidade if cidade else '',
                'cep_pontuacao': 'S'
            }
            
            # verify=False ignora erros de certificado SSL
            response = self.session.post(self.API_URL, data=payload, timeout=15, verify=False)
            
            if response.status_code == 200:
                text = response.text
                data = {}
                
                # Parser atualizado para o novo formato HTML do 4Devs (div + span)
                # Exemplo: <div id="cep" class="output-txt"><span>13220-130</span>
                
                # Tenta extrair CEP
                cep_match = re.search(r'id="cep"[^>]*><span>([^<]+)</span>', text)
                if cep_match:
                    data['cep'] = cep_match.group(1)
                else:
                    # Fallback para formato antigo (input value)
                    cep_match_old = re.search(r'name="cep"[^>]*value="([^"]*)"', text) or re.search(r'id="cep"[^>]*value="([^"]*)"', text)
                    if cep_match_old:
                        data['cep'] = cep_match_old.group(1)

                # Se achou CEP, tenta extrair o resto
                if 'cep' in data:
                    # Logradouro
                    log_match = re.search(r'id="endereco"[^>]*><span>([^<]+)</span>', text)
                    data['logradouro'] = log_match.group(1) if log_match else ""
                    
                    # Bairro
                    bairro_match = re.search(r'id="bairro"[^>]*><span>([^<]+)</span>', text)
                    data['bairro'] = bairro_match.group(1) if bairro_match else ""
                    
                    # Cidade
                    cidade_match = re.search(r'id="cidade"[^>]*><span>([^<]+)</span>', text)
                    data['cidade'] = cidade_match.group(1) if cidade_match else ""
                    
                    # Estado
                    estado_match = re.search(r'id="estado"[^>]*><span>([^<]+)</span>', text)
                    data['estado'] = estado_match.group(1) if estado_match else ""

                    # Mapear Estado para UF
                    uf_found = 'SP' # Default
                    estado_raw = data.get('estado', '')
                    
                    if len(estado_raw) == 2:
                        uf_found = estado_raw
                    else:
                        for sigla, nome in self.ESTADOS.items():
                            if estado_raw == nome:
                                uf_found = sigla
                                break
                    
                    # Gerar número aleatório pois o CEP não define número
                    import random
                    numero = str(random.randint(1, 9999))
                    
                    return Endereco(
                        cep=data.get('cep', ''),
                        logradouro=data.get('logradouro', ''),
                        bairro=data.get('bairro', ''),
                        cidade=data.get('cidade', ''),
                        estado=data.get('estado', ''),
                        uf=uf_found,
                        numero=numero
                    )
            return None
            
        except Exception as e:
            print(f"Erro na requisição: {e}")
            return None

    def gerar_enderecos(self, quantidade: int = 1, uf: str = None, cidade: str = None, 
                       com_pontuacao: bool = True, callback: Callable = None) -> List[Endereco]:
        """
        Gera uma lista de endereços válidos
        """
        self._cancel = False
        enderecos = []
        
        for i in range(quantidade):
            if self._cancel:
                break
                
            # Tenta obter endereço até conseguir (com limite de tentativas)
            endereco = None
            
            # 1. Tenta API do 4Devs
            for _ in range(3):
                endereco = self._fetch_address(uf, cidade)
                if endereco:
                    self.last_source = "api"
                    break
                time.sleep(0.5) # Evitar flood
            
            # 2. Se falhar, tenta banco de reserva
            if not endereco:
                reserva = self.extractor.get_reserva(uf)
                if reserva:
                    endereco = Endereco(
                        cep=reserva.get('cep', ''),
                        logradouro=reserva.get('logradouro', ''),
                        bairro=reserva.get('bairro', ''),
                        cidade=reserva.get('cidade', ''),
                        estado=reserva.get('estado', ''),
                        uf=reserva.get('uf', ''),
                        numero=reserva.get('numero') or str(int(time.time()) % 1000) # Numero aleatorio se nao tiver
                    )
                    self.last_source = "reserva"
                else:
                    self.last_source = "erro"
            
            if endereco:
                enderecos.append(endereco)
            
            if callback:
                callback(i + 1, quantidade)
                
            # Pequeno delay para não sobrecarregar a API
            time.sleep(0.2)
            
        return enderecos

    def gerar_endereco(self, uf: str = None, cidade: str = None, com_pontuacao: bool = True) -> Optional[Endereco]:
        """
        Gera um único endereço (método de compatibilidade)
        """
        enderecos = self.gerar_enderecos(1, uf, cidade, com_pontuacao)
        return enderecos[0] if enderecos else None

    def get_estados(self) -> List[tuple]:
        """Retorna lista de tuplas (UF, Nome) dos estados"""
        return sorted([(k, v) for k, v in self.ESTADOS.items()], key=lambda x: x[1])

    def get_cidades(self, uf: str) -> List[tuple]:
        """
        Retorna lista de tuplas (ID, Nome) das cidades para um estado.
        """
        try:
            payload = {
                'acao': 'carregar_cidades',
                'cep_estado': uf
            }
            response = self.session.post(self.API_URL, data=payload, timeout=5, verify=False)
            if response.status_code == 200:
                # A resposta é HTML com <option value="ID">NOME</option>
                # Extrai (ID, NOME)
                cidades = re.findall(r'<option value="([^"]+)">([^<]+)</option>', response.text)
                # Ordena pelo nome da cidade
                return sorted([(id_cidade, nome) for id_cidade, nome in cidades if id_cidade and nome], key=lambda x: x[1])
        except:
            pass
        return []
