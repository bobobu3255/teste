import json
import os
from typing import List, Dict, Optional
from app.core.paths import BASE_DIR

class ConfigManager:
    """Gerencia configurações de múltiplas contas e grupos"""
    
    def __init__(self, config_file: str = None):
        if config_file is None:
            config_file = os.path.join(str(BASE_DIR), 'contas.json')
        
        self.config_file = config_file
        self.load_config()
    
    def load_config(self):
        """Carrega configurações do arquivo"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    self.config = json.load(f)
            except (json.JSONDecodeError, IOError, PermissionError) as e:
                print(f"Aviso: Erro ao carregar configuração: {e}")
                self.config = self._default_config()
        else:
            self.config = self._default_config()
    
    def _default_config(self):
        """Retorna configuração padrão"""
        return {
            "contas": [],
            "conta_ativa": None,
            "grupos": []
        }
    
    def save_config(self):
        """Salva configurações no arquivo"""
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)
    
    def adicionar_conta(self, telefone: str, api_id: int, api_hash: str, nome: str = None) -> bool:
        """Adiciona uma nova conta do Telegram"""
        if nome is None:
            nome = f"Conta {len(self.config['contas']) + 1}"
        
        # Verificar se já existe
        for conta in self.config['contas']:
            if conta['telefone'] == telefone:
                return False
        
        conta = {
            "id": len(self.config['contas']) + 1,
            "nome": nome,
            "telefone": telefone,
            "api_id": api_id,
            "api_hash": api_hash
        }
        
        self.config['contas'].append(conta)
        
        # Se for a primeira, ativa automaticamente
        if self.config['conta_ativa'] is None:
            self.config['conta_ativa'] = conta['id']
        
        self.save_config()
        return True
    
    def listar_contas(self) -> List[Dict]:
        """Lista todas as contas"""
        return self.config['contas']
    
    def get_conta_ativa(self) -> Optional[Dict]:
        """Retorna a conta ativa"""
        if self.config['conta_ativa'] is None:
            return None
        
        for conta in self.config['contas']:
            if conta['id'] == self.config['conta_ativa']:
                return conta
        
        return None
    
    def set_conta_ativa(self, conta_id: int) -> bool:
        """Define a conta ativa"""
        for conta in self.config['contas']:
            if conta['id'] == conta_id:
                self.config['conta_ativa'] = conta_id
                self.save_config()
                return True
        
        return False
    
    def deletar_conta(self, conta_id: int) -> bool:
        """Deleta uma conta"""
        self.config['contas'] = [c for c in self.config['contas'] if c['id'] != conta_id]
        
        if self.config['conta_ativa'] == conta_id:
            if self.config['contas']:
                self.config['conta_ativa'] = self.config['contas'][0]['id']
            else:
                self.config['conta_ativa'] = None
        
        self.save_config()
        return True
    
    def adicionar_grupo(self, nome_grupo: str, username: str, conta_id: int) -> bool:
        """Adiciona um novo grupo para coletar"""
        # Verificar se já existe
        for grupo in self.config['grupos']:
            if grupo['username'] == username and grupo['conta_id'] == conta_id:
                return False
        
        grupo = {
            "id": len(self.config['grupos']) + 1,
            "nome": nome_grupo,
            "username": username,
            "conta_id": conta_id
        }
        
        self.config['grupos'].append(grupo)
        self.save_config()
        return True
    
    def listar_grupos(self, conta_id: int = None) -> List[Dict]:
        """Lista grupos de uma conta específica ou todos"""
        if conta_id is None:
            return self.config['grupos']
        
        return [g for g in self.config['grupos'] if g['conta_id'] == conta_id]
    
    def deletar_grupo(self, grupo_id: int) -> bool:
        """Deleta um grupo"""
        self.config['grupos'] = [g for g in self.config['grupos'] if g['id'] != grupo_id]
        self.save_config()
        return True
    
    def get_diretorio_conta(self, conta_id: int) -> str:
        """Retorna o diretório para armazenar dados da conta"""
        conta_dir = os.path.join(str(BASE_DIR), f"conta_{conta_id}")
        
        if not os.path.exists(conta_dir):
            os.makedirs(conta_dir)
        
        return conta_dir
    
    def get_caminho_banco(self, conta_id: int, grupo_id: int = None) -> str:
        """Retorna o caminho do banco de dados para uma conta/grupo"""
        conta_dir = self.get_diretorio_conta(conta_id)
        
        if grupo_id is None:
            # Banco geral da conta
            return os.path.join(conta_dir, 'dados.db')
        else:
            # Banco específico do grupo
            return os.path.join(conta_dir, f'grupo_{grupo_id}.db')
