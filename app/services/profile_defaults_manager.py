#!/usr/bin/env python3
"""
Profile Defaults Manager - Gerenciador de Configurações Padrão para Perfis
Telegram Collector Pro v10.0

Este módulo gerencia:
- Abas favoritas padrão para novos perfis
- Extensões padrão para novos perfis
- Gerenciador de senhas portátil (exportável)

Autor: Telegram Collector Team
Versão: 1.0
"""

import os
import json
import shutil
import hashlib
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.paths import BASE_DIR, CONFIG_DIR
from app.core.error_service import log_exception


class FavoritesManager:
    """
    Gerenciador de abas favoritas padrão.
    Permite definir quais abas favoritas serão aplicadas automaticamente
    em todos os novos perfis do navegador.
    """
    
    def __init__(self, config_dir: str = None):
        """
        Inicializa o gerenciador de favoritos.
        
        Args:
            config_dir: Diretório para armazenar configurações
        """
        self.config_dir = Path(config_dir) if config_dir else CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.favorites_file = self.config_dir / "default_favorites.json"
        self.favorites: List[Dict] = []
        
        self._load_favorites()
    
    def _load_favorites(self):
        """Carrega favoritos do arquivo."""
        if self.favorites_file.exists():
            try:
                with open(self.favorites_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.favorites = data.get("favorites", [])
            except Exception as e:
                print(f"Erro ao carregar favoritos: {e}")
                self.favorites = []
    
    def _save_favorites(self):
        """Salva favoritos no arquivo."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "favorites": self.favorites
        }
        
        try:
            with open(self.favorites_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar favoritos: {e}")
    
    def add_favorite(self, name: str, url: str, folder: str = "Padrão", icon: str = None) -> bool:
        """
        Adiciona um favorito à lista padrão.
        
        Args:
            name: Nome do favorito
            url: URL do favorito
            folder: Pasta onde o favorito será organizado
            icon: Ícone opcional (emoji ou URL)
            
        Returns:
            True se adicionado com sucesso
        """
        # Verificar se já existe
        for fav in self.favorites:
            if fav.get("url") == url:
                return False
        
        favorite = {
            "id": hashlib.md5(f"{name}{url}{datetime.now()}".encode()).hexdigest()[:8],
            "name": name,
            "url": url,
            "folder": folder,
            "icon": icon,
            "added_at": datetime.now().isoformat()
        }
        
        self.favorites.append(favorite)
        self._save_favorites()
        return True
    
    def remove_favorite(self, favorite_id: str) -> bool:
        """
        Remove um favorito da lista.
        
        Args:
            favorite_id: ID do favorito
            
        Returns:
            True se removido com sucesso
        """
        for i, fav in enumerate(self.favorites):
            if fav.get("id") == favorite_id:
                del self.favorites[i]
                self._save_favorites()
                return True
        return False
    
    def update_favorite(self, favorite_id: str, name: str = None, url: str = None, 
                       folder: str = None, icon: str = None) -> bool:
        """
        Atualiza um favorito existente.
        
        Args:
            favorite_id: ID do favorito
            name: Novo nome (opcional)
            url: Nova URL (opcional)
            folder: Nova pasta (opcional)
            icon: Novo ícone (opcional)
            
        Returns:
            True se atualizado com sucesso
        """
        for fav in self.favorites:
            if fav.get("id") == favorite_id:
                if name is not None:
                    fav["name"] = name
                if url is not None:
                    fav["url"] = url
                if folder is not None:
                    fav["folder"] = folder
                if icon is not None:
                    fav["icon"] = icon
                fav["updated_at"] = datetime.now().isoformat()
                self._save_favorites()
                return True
        return False
    
    def get_favorites(self) -> List[Dict]:
        """
        Retorna todos os favoritos.
        
        Returns:
            Lista de favoritos
        """
        return self.favorites.copy()
    
    def get_favorites_by_folder(self) -> Dict[str, List[Dict]]:
        """
        Retorna favoritos organizados por pasta.
        
        Returns:
            Dicionário com pastas e seus favoritos
        """
        folders = {}
        for fav in self.favorites:
            folder = fav.get("folder", "Padrão")
            folder = (folder or "Barra de Favoritos").strip()
            if folder.lower() in ("fixados", "padrão", "padrao", "barra"):
                folder = "Barra de Favoritos"
            if folder not in folders:
                folders[folder] = []
            folders[folder].append(fav)
        return folders
    
    def import_favorites(self, favorites_list: List[Dict]) -> int:
        """
        Importa uma lista de favoritos.
        
        Args:
            favorites_list: Lista de favoritos para importar
            
        Returns:
            Número de favoritos importados
        """
        count = 0
        for fav in favorites_list:
            if self.add_favorite(
                name=fav.get("name", "Sem Nome"),
                url=fav.get("url", ""),
                folder=fav.get("folder", "Importados"),
                icon=fav.get("icon")
            ):
                count += 1
        return count
    
    def export_favorites(self) -> List[Dict]:
        """
        Exporta todos os favoritos.
        
        Returns:
            Lista de favoritos para exportação
        """
        return self.favorites.copy()
    
    def apply_to_chrome_profile(self, profile_data_dir: Path) -> bool:
        """
        Aplica os favoritos padrão a um perfil do Chrome.
        
        Args:
            profile_data_dir: Diretório de dados do perfil
            
        Returns:
            True se aplicado com sucesso
        """
        try:
            # Verificar se há favoritos para aplicar
            if not self.favorites:
                print("[Favoritos] Nenhum favorito configurado para aplicar")
                return True
            
            # Criar diretório Default se não existir
            default_dir = profile_data_dir / "Default"
            default_dir.mkdir(parents=True, exist_ok=True)
            
            bookmarks_file = default_dir / "Bookmarks"

            timestamp = str(int(datetime.now().timestamp() * 1000000))

            def create_base_bookmarks() -> Dict:
                return {
                    "checksum": "",
                    "roots": {
                        "bookmark_bar": {
                            "children": [],
                            "date_added": timestamp,
                            "date_modified": timestamp,
                            "guid": hashlib.md5(b"bookmark_bar").hexdigest(),
                            "id": "1",
                            "name": "Barra de favoritos",
                            "type": "folder",
                        },
                        "other": {
                            "children": [],
                            "date_added": timestamp,
                            "date_modified": timestamp,
                            "guid": hashlib.md5(b"other").hexdigest(),
                            "id": "2",
                            "name": "Outros favoritos",
                            "type": "folder",
                        },
                        "synced": {
                            "children": [],
                            "date_added": timestamp,
                            "date_modified": timestamp,
                            "guid": hashlib.md5(b"synced").hexdigest(),
                            "id": "3",
                            "name": "Favoritos do celular",
                            "type": "folder",
                        },
                    },
                    "version": 1,
                }

            bookmarks_data = create_base_bookmarks()
            if bookmarks_file.exists():
                try:
                    with open(bookmarks_file, "r", encoding="utf-8") as f:
                        existing_data = json.load(f)
                    if isinstance(existing_data, dict) and isinstance(existing_data.get("roots"), dict):
                        bookmarks_data = existing_data
                except Exception as e:
                    print(f"[Favoritos] Bookmarks existente invalido, recriando: {e}")

            roots = bookmarks_data.setdefault("roots", {})
            for root_name, root_data in create_base_bookmarks()["roots"].items():
                roots.setdefault(root_name, root_data)

            bookmark_bar = roots["bookmark_bar"]
            bookmark_bar.setdefault("children", [])

            legacy_default_urls = {
                "https://sso.crunchyroll.com/pt-br/login?return_url=%2Fauthorize%3Fclient_id%3Dnoaihdevm_6iyg0a8l0q%26redirect_uri%3Dhttps%253A%252F%252Fwww.crunchyroll.com%252Fcallback%26response_type%3Dcookie%26state%3D%252F",
                "https://auth.hbomax.com/login",
                "http://amazon.com.br",
                "https://www.primevideo.com/region/na/storefront",
                "https://sso.crunchyroll.com/pt-br/login/amazon",
                "https://www.amazon.com/cpe/yourpayments/wallet?ref_=ya_d_c_pmt_mpo#",
                "https://www.disneyplus.com/",
                "https://login.microsoftonline.com",
                "https://www.paramountplus.com/br/",
            }

            def prune_legacy_defaults(node: Dict):
                children = node.get("children")
                if not isinstance(children, list):
                    return
                node["children"] = [
                    child for child in children
                    if not (child.get("type") == "url" and child.get("url") in legacy_default_urls)
                ]
                for child in node["children"]:
                    if isinstance(child, dict):
                        prune_legacy_defaults(child)

            for root_node in roots.values():
                if isinstance(root_node, dict):
                    prune_legacy_defaults(root_node)

            default_urls = {
                (fav.get("url") or "").strip()
                for fav in self.favorites
                if (fav.get("url") or "").strip()
            }

            def flatten_default_favorites(node: Dict, keep_direct: bool = False):
                children = node.get("children")
                if not isinstance(children, list):
                    return

                new_children = []
                for child in children:
                    if not isinstance(child, dict):
                        continue
                    if child.get("type") == "folder":
                        flatten_default_favorites(child, keep_direct=False)
                        is_old_fixed_folder = (child.get("name") or "").strip().lower() == "fixados"
                        if child.get("children") or not is_old_fixed_folder:
                            new_children.append(child)
                        continue
                    if child.get("type") == "url" and child.get("url") in default_urls and not keep_direct:
                        continue
                    new_children.append(child)
                node["children"] = new_children

            # Tira favoritos padrão de pastas antigas e recoloca direto na barra.
            flatten_default_favorites(bookmark_bar, keep_direct=True)

            existing_urls = set()
            used_ids = set()

            def scan_node(node: Dict):
                node_id = str(node.get("id", ""))
                if node_id.isdigit():
                    used_ids.add(int(node_id))
                if node.get("type") == "url" and node.get("url"):
                    existing_urls.add(node.get("url"))
                for child in node.get("children", []) or []:
                    if isinstance(child, dict):
                        scan_node(child)

            for root_node in roots.values():
                if isinstance(root_node, dict):
                    scan_node(root_node)

            next_id = max(used_ids or {3}) + 1

            def allocate_id() -> str:
                nonlocal next_id
                value = str(next_id)
                next_id += 1
                return value

            def find_or_create_folder(folder_name: str) -> List[Dict]:
                normalized = (folder_name or "Padrao").strip()
                if normalized in ("Padrao", "Padrão", "Barra de Favoritos"):
                    return bookmark_bar["children"]

                for child in bookmark_bar["children"]:
                    if child.get("type") == "folder" and child.get("name") == normalized:
                        child.setdefault("children", [])
                        return child["children"]

                folder = {
                    "children": [],
                    "date_added": timestamp,
                    "date_modified": timestamp,
                    "guid": hashlib.md5(f"{normalized}{timestamp}".encode()).hexdigest(),
                    "id": allocate_id(),
                    "name": normalized,
                    "type": "folder",
                }
                bookmark_bar["children"].append(folder)
                return folder["children"]

            added_count = 0
            for folder_name, favs in self.get_favorites_by_folder().items():
                target_children = find_or_create_folder(folder_name)
                for fav in favs:
                    url = (fav.get("url") or "").strip()
                    if not url or url in existing_urls:
                        continue

                    target_children.append({
                        "date_added": timestamp,
                        "guid": hashlib.md5(f"{fav.get('id', '')}{url}".encode()).hexdigest(),
                        "id": allocate_id(),
                        "name": fav.get("name", ""),
                        "type": "url",
                        "url": url,
                    })
                    existing_urls.add(url)
                    added_count += 1

            bookmark_bar["date_modified"] = timestamp

            with open(bookmarks_file, "w", encoding="utf-8") as f:
                json.dump(bookmarks_data, f, indent=2, ensure_ascii=False)

            preferences_file = default_dir / "Preferences"
            preferences_data = {}
            if preferences_file.exists():
                try:
                    with open(preferences_file, "r", encoding="utf-8") as f:
                        loaded_preferences = json.load(f)
                    if isinstance(loaded_preferences, dict):
                        preferences_data = loaded_preferences
                except Exception:
                    preferences_data = {}

            preferences_data.setdefault("bookmark_bar", {})["show_on_all_tabs"] = True
            preferences_data.setdefault("browser", {})["show_home_button"] = True
            preferences_data.setdefault("credentials_enable_service", True)
            preferences_data.setdefault("profile", {})["password_manager_enabled"] = True
            preferences_data.setdefault("session", {})["restore_on_startup"] = 5
            with open(preferences_file, "w", encoding="utf-8") as f:
                json.dump(preferences_data, f, indent=2, ensure_ascii=False)

            print(f"[Favoritos] {added_count} favoritos adicionados ao perfil em {bookmarks_file}")
            return True
            
            # Estrutura de bookmarks do Chrome
            bookmarks_data = {
                "checksum": "",
                "roots": {
                    "bookmark_bar": {
                        "children": [],
                        "date_added": str(int(datetime.now().timestamp() * 1000000)),
                        "date_modified": str(int(datetime.now().timestamp() * 1000000)),
                        "guid": hashlib.md5(b"bookmark_bar").hexdigest(),
                        "id": "1",
                        "name": "Barra de favoritos",
                        "type": "folder"
                    },
                    "other": {
                        "children": [],
                        "date_added": str(int(datetime.now().timestamp() * 1000000)),
                        "date_modified": str(int(datetime.now().timestamp() * 1000000)),
                        "guid": hashlib.md5(b"other").hexdigest(),
                        "id": "2",
                        "name": "Outros favoritos",
                        "type": "folder"
                    },
                    "synced": {
                        "children": [],
                        "date_added": str(int(datetime.now().timestamp() * 1000000)),
                        "date_modified": str(int(datetime.now().timestamp() * 1000000)),
                        "guid": hashlib.md5(b"synced").hexdigest(),
                        "id": "3",
                        "name": "Favoritos do celular",
                        "type": "folder"
                    }
                },
                "version": 1
            }
            
            # Organizar favoritos por pasta
            folders_data = self.get_favorites_by_folder()
            
            id_counter = 4
            for folder_name, favs in folders_data.items():
                if folder_name == "Padrão" or folder_name == "Barra de Favoritos":
                    # Adicionar diretamente na barra de favoritos
                    for fav in favs:
                        bookmark = {
                            "date_added": str(int(datetime.now().timestamp() * 1000000)),
                            "guid": hashlib.md5(fav.get("id", "").encode()).hexdigest(),
                            "id": str(id_counter),
                            "name": fav.get("name", ""),
                            "type": "url",
                            "url": fav.get("url", "")
                        }
                        bookmarks_data["roots"]["bookmark_bar"]["children"].append(bookmark)
                        id_counter += 1
                else:
                    # Criar pasta
                    folder = {
                        "children": [],
                        "date_added": str(int(datetime.now().timestamp() * 1000000)),
                        "date_modified": str(int(datetime.now().timestamp() * 1000000)),
                        "guid": hashlib.md5(folder_name.encode()).hexdigest(),
                        "id": str(id_counter),
                        "name": folder_name,
                        "type": "folder"
                    }
                    id_counter += 1
                    
                    for fav in favs:
                        bookmark = {
                            "date_added": str(int(datetime.now().timestamp() * 1000000)),
                            "guid": hashlib.md5(fav.get("id", "").encode()).hexdigest(),
                            "id": str(id_counter),
                            "name": fav.get("name", ""),
                            "type": "url",
                            "url": fav.get("url", "")
                        }
                        folder["children"].append(bookmark)
                        id_counter += 1
                    
                    bookmarks_data["roots"]["bookmark_bar"]["children"].append(folder)
            
            # Salvar arquivo de bookmarks
            with open(bookmarks_file, "w", encoding="utf-8") as f:
                json.dump(bookmarks_data, f, indent=2, ensure_ascii=False)
            
            print(f"[Favoritos] {len(self.favorites)} favoritos aplicados ao perfil em {bookmarks_file}")
            return True
            
        except Exception as e:
            print(f"Erro ao aplicar favoritos ao perfil: {e}")
            log_exception(BASE_DIR, "browser_errors.log", "aplicar favoritos ao perfil", e)
            return False


class ExtensionsManager:
    """
    Gerenciador de extensões padrão.
    Permite definir quais extensões serão instaladas automaticamente
    em todos os novos perfis do navegador.
    """
    
    def __init__(self, config_dir: str = None, extensions_dir: str = None):
        """
        Inicializa o gerenciador de extensões.
        
        Args:
            config_dir: Diretório para armazenar configurações
            extensions_dir: Diretório para armazenar extensões
        """
        self.config_dir = Path(config_dir) if config_dir else CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.extensions_dir = Path(extensions_dir) if extensions_dir else BASE_DIR / "browser_extensions"
        self.extensions_dir.mkdir(parents=True, exist_ok=True)
        
        self.default_extensions_dir = self.extensions_dir / "default"
        self.default_extensions_dir.mkdir(parents=True, exist_ok=True)
        
        self.extensions_file = self.config_dir / "default_extensions.json"
        self.extensions: List[Dict] = []
        
        self._load_extensions()
    
    def _load_extensions(self):
        """Carrega configurações de extensões do arquivo."""
        if self.extensions_file.exists():
            try:
                with open(self.extensions_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.extensions = data.get("extensions", [])
            except Exception as e:
                print(f"Erro ao carregar extensões: {e}")
                self.extensions = []
        
        # Verificar se Privacy Guard está instalado
        self._ensure_privacy_guard()
    
    def _ensure_privacy_guard(self):
        """
        Garante que a extensão Privacy Guard esteja configurada.
        Esta extensão vem pré-instalada com o Telegram Collector.
        """
        # Verificar se já existe
        for ext in self.extensions:
            if ext.get("name") == "Privacy Guard":
                return
        
        # Caminho da extensão Privacy Guard
        privacy_guard_path = self.extensions_dir / "privacy_guard"
        
        if privacy_guard_path.exists():
            # Adicionar à lista de extensões
            extension = {
                "id": "privacy_guard_builtin",
                "name": "Privacy Guard",
                "source": str(privacy_guard_path),
                "source_type": "builtin",
                "local_path": str(privacy_guard_path),
                "enabled": True,
                "description": "Extensão de privacidade integrada. Bloqueia trackers, fingerprinting e protege sua navegação.",
                "added_at": datetime.now().isoformat(),
                "builtin": True  # Marca como extensão integrada
            }
            
            self.extensions.insert(0, extension)  # Colocar no início
            self._save_extensions()
            print("[Privacy Guard] Extensão de privacidade configurada automaticamente")
    
    def _save_extensions(self):
        """Salva configurações de extensões no arquivo."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "extensions": self.extensions
        }
        
        try:
            with open(self.extensions_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar extensões: {e}")
    
    def add_extension(self, name: str, source: str, source_type: str = "file", 
                     enabled: bool = True, description: str = "") -> Tuple[bool, str]:
        """
        Adiciona uma extensão à lista padrão.
        
        Args:
            name: Nome da extensão
            source: Caminho do arquivo ou URL da Chrome Web Store
            source_type: Tipo de fonte ("file", "crx", "webstore")
            enabled: Se a extensão está habilitada
            description: Descrição da extensão
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        ext_id = hashlib.md5(f"{name}{source}{datetime.now()}".encode()).hexdigest()[:12]
        
        # Se for arquivo, copiar para o diretório de extensões
        local_path = None
        if source_type in ["file", "crx"]:
            source_path = Path(source)
            if source_path.exists():
                if source_path.is_dir():
                    # Copiar pasta da extensão
                    dest_path = self.default_extensions_dir / ext_id
                    if dest_path.exists():
                        shutil.rmtree(dest_path)
                    shutil.copytree(source_path, dest_path)
                    local_path = str(dest_path)
                elif source_path.suffix in [".crx", ".zip"]:
                    # Copiar arquivo CRX/ZIP
                    dest_path = self.default_extensions_dir / f"{ext_id}{source_path.suffix}"
                    shutil.copy2(source_path, dest_path)
                    local_path = str(dest_path)
                else:
                    return False, "Formato de extensão não suportado"
            else:
                return False, f"Arquivo não encontrado: {source}"
        
        extension = {
            "id": ext_id,
            "name": name,
            "source": source,
            "source_type": source_type,
            "local_path": local_path,
            "enabled": enabled,
            "description": description,
            "added_at": datetime.now().isoformat()
        }
        
        self.extensions.append(extension)
        self._save_extensions()
        return True, f"Extensão '{name}' adicionada com sucesso"
    
    def remove_extension(self, ext_id: str) -> bool:
        """
        Remove uma extensão da lista.
        
        Args:
            ext_id: ID da extensão
            
        Returns:
            True se removida com sucesso
        """
        for i, ext in enumerate(self.extensions):
            if ext.get("id") == ext_id:
                # Remover arquivos locais
                local_path = ext.get("local_path")
                if local_path:
                    path = Path(local_path)
                    if path.exists():
                        if path.is_dir():
                            shutil.rmtree(path)
                        else:
                            path.unlink()
                
                del self.extensions[i]
                self._save_extensions()
                return True
        return False
    
    def toggle_extension(self, ext_id: str) -> bool:
        """
        Alterna o estado de uma extensão (habilitada/desabilitada).
        
        Args:
            ext_id: ID da extensão
            
        Returns:
            True se alternado com sucesso
        """
        for ext in self.extensions:
            if ext.get("id") == ext_id:
                ext["enabled"] = not ext.get("enabled", True)
                self._save_extensions()
                return True
        return False
    
    def get_extensions(self, enabled_only: bool = False) -> List[Dict]:
        """
        Retorna todas as extensões.
        
        Args:
            enabled_only: Se True, retorna apenas extensões habilitadas
            
        Returns:
            Lista de extensões
        """
        if enabled_only:
            return [ext for ext in self.extensions if ext.get("enabled", True)]
        return self.extensions.copy()
    
    def get_extension_paths(self) -> List[str]:
        """
        Retorna os caminhos das extensões habilitadas para carregar no Chrome.
        
        Returns:
            Lista de caminhos de extensões
        """
        paths = []
        for ext in self.extensions:
            if ext.get("enabled", True) and ext.get("local_path"):
                path = Path(ext["local_path"])
                if path.exists():
                    paths.append(str(path.absolute()))
        return paths
    
    def apply_to_chrome_options(self, chrome_options) -> None:
        """
        Aplica as extensões padrão às opções do Chrome.
        
        Args:
            chrome_options: Objeto Options do Selenium
        """
        paths = self.get_extension_paths()
        if paths:
            chrome_options.add_argument(f"--load-extension={','.join(paths)}")


class PasswordManager:
    """
    Gerenciador de senhas portátil.
    Salva todas as senhas em um arquivo criptografado que pode ser
    usado em qualquer navegador ou exportado para outros formatos.
    
    MELHORIAS DE SEGURANÇA:
    - Salt dinâmico por instalação
    - Verificação de senha mestra
    - Hash da senha mestra armazenado separadamente
    - 480.000 iterações PBKDF2 (recomendado OWASP 2023)
    """
    
    def __init__(self, config_dir: str = None, master_password: str = None):
        """
        Inicializa o gerenciador de senhas.
        
        Args:
            config_dir: Diretório para armazenar configurações
            master_password: Senha mestra para criptografia
        """
        self.config_dir = Path(config_dir) if config_dir else CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.passwords_file = self.config_dir / "passwords.enc"
        self.passwords_plain_file = self.config_dir / "passwords.json"
        self.salt_file = self.config_dir / "passwords.salt"
        self.master_hash_file = self.config_dir / "master.hash"
        
        self.master_password = master_password
        self.passwords: List[Dict] = []
        self._cipher = None
        self._salt = None
        
        # Carregar ou gerar salt
        self._load_or_create_salt()
        
        # Inicializar cipher se tiver senha
        if master_password:
            self._init_cipher(master_password)
        
        self._load_passwords()
    
    def _load_or_create_salt(self):
        """Carrega ou cria um salt único para esta instalação."""
        if self.salt_file.exists():
            with open(self.salt_file, "rb") as f:
                self._salt = f.read()
        else:
            # Gerar salt aleatório de 32 bytes
            import secrets
            self._salt = secrets.token_bytes(32)
            with open(self.salt_file, "wb") as f:
                f.write(self._salt)
    
    def _init_cipher(self, password: str):
        """Inicializa o cipher para criptografia com segurança aprimorada."""
        try:
            # Derivar chave da senha com salt dinâmico
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=self._salt,
                iterations=480000,  # Recomendado OWASP 2023
            )
            key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
            self._cipher = Fernet(key)
        except Exception as e:
            print(f"Erro ao inicializar criptografia: {e}")
            self._cipher = None
    
    def _hash_master_password(self, password: str) -> str:
        """Gera hash da senha mestra para verificação."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self._salt + b"_master_verify",
            iterations=480000,
        )
        return base64.b64encode(kdf.derive(password.encode())).decode()
    
    def is_master_password_set(self) -> bool:
        """Verifica se uma senha mestra já foi definida."""
        return self.master_hash_file.exists()
    
    def verify_master_password(self, password: str) -> bool:
        """
        Verifica se a senha mestra está correta.
        
        Args:
            password: Senha a verificar
            
        Returns:
            True se a senha está correta
        """
        if not self.master_hash_file.exists():
            return False
        
        try:
            with open(self.master_hash_file, "r") as f:
                stored_hash = f.read().strip()
            
            computed_hash = self._hash_master_password(password)
            return stored_hash == computed_hash
        except Exception as e:
            print(f"Erro ao verificar senha mestra: {e}")
            return False
    
    def create_master_password(self, password: str) -> Tuple[bool, str]:
        """
        Cria uma nova senha mestra.
        
        Args:
            password: Nova senha mestra
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        if len(password) < 8:
            return False, "A senha mestra deve ter pelo menos 8 caracteres"
        
        if self.master_hash_file.exists():
            return False, "Senha mestra já existe. Use change_master_password para alterar."
        
        try:
            # Salvar hash da senha
            password_hash = self._hash_master_password(password)
            with open(self.master_hash_file, "w") as f:
                f.write(password_hash)
            
            # Inicializar cipher
            self.master_password = password
            self._init_cipher(password)
            
            # Re-salvar senhas com criptografia
            self._save_passwords()
            
            return True, "Senha mestra criada com sucesso!"
        except Exception as e:
            return False, f"Erro ao criar senha mestra: {e}"
    
    def change_master_password(self, old_password: str, new_password: str) -> Tuple[bool, str]:
        """
        Altera a senha mestra.
        
        Args:
            old_password: Senha mestra atual
            new_password: Nova senha mestra
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        if not self.verify_master_password(old_password):
            return False, "Senha mestra atual incorreta"
        
        if len(new_password) < 8:
            return False, "A nova senha deve ter pelo menos 8 caracteres"
        
        try:
            # Carregar senhas com a senha antiga
            self._init_cipher(old_password)
            self._load_passwords()
            
            # Gerar novo salt
            import secrets
            self._salt = secrets.token_bytes(32)
            with open(self.salt_file, "wb") as f:
                f.write(self._salt)
            
            # Atualizar hash da senha
            password_hash = self._hash_master_password(new_password)
            with open(self.master_hash_file, "w") as f:
                f.write(password_hash)
            
            # Inicializar novo cipher
            self.master_password = new_password
            self._init_cipher(new_password)
            
            # Re-salvar senhas com nova criptografia
            self._save_passwords()
            
            return True, "Senha mestra alterada com sucesso!"
        except Exception as e:
            return False, f"Erro ao alterar senha mestra: {e}"
    
    def unlock(self, password: str) -> Tuple[bool, str]:
        """
        Desbloqueia o gerenciador de senhas com a senha mestra.
        
        Args:
            password: Senha mestra
            
        Returns:
            Tupla (sucesso, mensagem)
        """
        if not self.is_master_password_set():
            return False, "Nenhuma senha mestra configurada. Use create_master_password primeiro."
        
        if not self.verify_master_password(password):
            return False, "Senha mestra incorreta"
        
        self.master_password = password
        self._init_cipher(password)
        self._load_passwords()
        
        return True, f"Desbloqueado! {len(self.passwords)} senhas carregadas."
    
    def is_unlocked(self) -> bool:
        """Verifica se o gerenciador está desbloqueado."""
        return self._cipher is not None
    
    def set_master_password(self, password: str) -> bool:
        """
        Define a senha mestra.
        
        Args:
            password: Nova senha mestra
            
        Returns:
            True se definida com sucesso
        """
        self.master_password = password
        self._init_cipher(password)
        self._save_passwords()
        return True
    
    def _load_passwords(self):
        """Carrega senhas do arquivo."""
        # Tentar carregar arquivo criptografado
        if self.passwords_file.exists() and self._cipher:
            try:
                with open(self.passwords_file, "rb") as f:
                    encrypted_data = f.read()
                decrypted_data = self._cipher.decrypt(encrypted_data)
                data = json.loads(decrypted_data.decode())
                self.passwords = data.get("passwords", [])
                return
            except Exception as e:
                print(f"Erro ao carregar senhas criptografadas: {e}")
        
        # Fallback: carregar arquivo não criptografado
        if self.passwords_plain_file.exists():
            try:
                with open(self.passwords_plain_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.passwords = data.get("passwords", [])
            except Exception as e:
                print(f"Erro ao carregar senhas: {e}")
                self.passwords = []
    
    def _save_passwords(self):
        """Salva senhas no arquivo."""
        data = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "passwords": self.passwords
        }
        
        # Salvar arquivo criptografado se tiver cipher
        if self._cipher:
            try:
                json_data = json.dumps(data, ensure_ascii=False)
                encrypted_data = self._cipher.encrypt(json_data.encode())
                with open(self.passwords_file, "wb") as f:
                    f.write(encrypted_data)
            except Exception as e:
                print(f"Erro ao salvar senhas criptografadas: {e}")
        
        # Sempre salvar arquivo não criptografado também (para backup)
        try:
            # Mascarar senhas no arquivo plain
            plain_data = data.copy()
            plain_data["passwords"] = []
            for pwd in self.passwords:
                masked = pwd.copy()
                if "password" in masked:
                    masked["password"] = "***ENCRYPTED***"
                plain_data["passwords"].append(masked)
            
            with open(self.passwords_plain_file, "w", encoding="utf-8") as f:
                json.dump(plain_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erro ao salvar arquivo de senhas: {e}")
    
    def add_password(self, site: str, url: str, username: str, password: str,
                    notes: str = "", category: str = "Geral", 
                    auto_fill: bool = True) -> bool:
        """
        Adiciona uma senha ao gerenciador.
        
        Args:
            site: Nome do site
            url: URL do site
            username: Nome de usuário
            password: Senha
            notes: Notas adicionais
            category: Categoria da senha
            auto_fill: Se deve preencher automaticamente
            
        Returns:
            True se adicionada com sucesso
        """
        pwd_id = hashlib.md5(f"{site}{url}{username}{datetime.now()}".encode()).hexdigest()[:12]
        
        password_entry = {
            "id": pwd_id,
            "site": site,
            "url": url,
            "username": username,
            "password": password,
            "notes": notes,
            "category": category,
            "auto_fill": auto_fill,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        self.passwords.append(password_entry)
        self._save_passwords()
        return True
    
    def update_password(self, pwd_id: str, site: str = None, url: str = None,
                       username: str = None, password: str = None,
                       notes: str = None, category: str = None,
                       auto_fill: bool = None) -> bool:
        """
        Atualiza uma senha existente.
        
        Args:
            pwd_id: ID da senha
            site: Novo nome do site
            url: Nova URL
            username: Novo nome de usuário
            password: Nova senha
            notes: Novas notas
            category: Nova categoria
            auto_fill: Novo estado de auto-preenchimento
            
        Returns:
            True se atualizada com sucesso
        """
        for pwd in self.passwords:
            if pwd.get("id") == pwd_id:
                if site is not None:
                    pwd["site"] = site
                if url is not None:
                    pwd["url"] = url
                if username is not None:
                    pwd["username"] = username
                if password is not None:
                    pwd["password"] = password
                if notes is not None:
                    pwd["notes"] = notes
                if category is not None:
                    pwd["category"] = category
                if auto_fill is not None:
                    pwd["auto_fill"] = auto_fill
                pwd["updated_at"] = datetime.now().isoformat()
                self._save_passwords()
                return True
        return False
    
    def remove_password(self, pwd_id: str) -> bool:
        """
        Remove uma senha do gerenciador.
        
        Args:
            pwd_id: ID da senha
            
        Returns:
            True se removida com sucesso
        """
        for i, pwd in enumerate(self.passwords):
            if pwd.get("id") == pwd_id:
                del self.passwords[i]
                self._save_passwords()
                return True
        return False
    
    def get_passwords(self, category: str = None) -> List[Dict]:
        """
        Retorna todas as senhas.
        
        Args:
            category: Filtrar por categoria (opcional)
            
        Returns:
            Lista de senhas
        """
        if category:
            return [pwd for pwd in self.passwords if pwd.get("category") == category]
        return self.passwords.copy()
    
    def get_password_for_url(self, url: str) -> Optional[Dict]:
        """
        Busca uma senha para uma URL específica.
        
        Args:
            url: URL para buscar
            
        Returns:
            Senha encontrada ou None
        """
        for pwd in self.passwords:
            if pwd.get("url") and pwd.get("url") in url:
                return pwd.copy()
            if pwd.get("site") and pwd.get("site").lower() in url.lower():
                return pwd.copy()
        return None
    
    def get_categories(self) -> List[str]:
        """
        Retorna todas as categorias de senhas.
        
        Returns:
            Lista de categorias
        """
        categories = set()
        for pwd in self.passwords:
            categories.add(pwd.get("category", "Geral"))
        return sorted(list(categories))
    
    def search_passwords(self, query: str) -> List[Dict]:
        """
        Busca senhas por termo.
        
        Args:
            query: Termo de busca
            
        Returns:
            Lista de senhas encontradas
        """
        query_lower = query.lower()
        results = []
        for pwd in self.passwords:
            if (query_lower in pwd.get("site", "").lower() or
                query_lower in pwd.get("url", "").lower() or
                query_lower in pwd.get("username", "").lower() or
                query_lower in pwd.get("notes", "").lower()):
                results.append(pwd.copy())
        return results
    
    def export_to_csv(self, output_path: str, include_passwords: bool = False) -> bool:
        """
        Exporta senhas para CSV (compatível com navegadores).
        
        Args:
            output_path: Caminho do arquivo de saída
            include_passwords: Se deve incluir as senhas no export
            
        Returns:
            True se exportado com sucesso
        """
        try:
            import csv
            with open(output_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                # Cabeçalho padrão do Chrome
                writer.writerow(["name", "url", "username", "password", "note"])
                
                for pwd in self.passwords:
                    password_value = pwd.get("password", "") if include_passwords else ""
                    writer.writerow([
                        pwd.get("site", ""),
                        pwd.get("url", ""),
                        pwd.get("username", ""),
                        password_value,
                        pwd.get("notes", "")
                    ])
            return True
        except Exception as e:
            print(f"Erro ao exportar para CSV: {e}")
            return False
    
    def export_to_json(self, output_path: str, include_passwords: bool = False) -> bool:
        """
        Exporta senhas para JSON.
        
        Args:
            output_path: Caminho do arquivo de saída
            include_passwords: Se deve incluir as senhas no export
            
        Returns:
            True se exportado com sucesso
        """
        try:
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "source": "Telegram Collector Password Manager",
                "passwords": []
            }
            
            for pwd in self.passwords:
                entry = pwd.copy()
                if not include_passwords:
                    entry["password"] = ""
                export_data["passwords"].append(entry)
            
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erro ao exportar para JSON: {e}")
            return False
    
    def import_from_csv(self, input_path: str) -> int:
        """
        Importa senhas de um arquivo CSV (formato Chrome/Firefox).
        
        Args:
            input_path: Caminho do arquivo de entrada
            
        Returns:
            Número de senhas importadas
        """
        try:
            import csv
            count = 0
            with open(input_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Tentar diferentes formatos de CSV
                    site = row.get("name") or row.get("title") or row.get("site") or ""
                    url = row.get("url") or row.get("login_uri") or ""
                    username = row.get("username") or row.get("login_username") or ""
                    password = row.get("password") or row.get("login_password") or ""
                    notes = row.get("note") or row.get("notes") or ""
                    
                    if url or site:
                        self.add_password(
                            site=site,
                            url=url,
                            username=username,
                            password=password,
                            notes=notes,
                            category="Importado"
                        )
                        count += 1
            return count
        except Exception as e:
            print(f"Erro ao importar de CSV: {e}")
            return 0
    
    def import_from_json(self, input_path: str) -> int:
        """
        Importa senhas de um arquivo JSON.
        
        Args:
            input_path: Caminho do arquivo de entrada
            
        Returns:
            Número de senhas importadas
        """
        try:
            with open(input_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            count = 0
            passwords_list = data.get("passwords", data) if isinstance(data, dict) else data
            
            for pwd in passwords_list:
                site = pwd.get("site") or pwd.get("name") or ""
                url = pwd.get("url") or ""
                username = pwd.get("username") or ""
                password = pwd.get("password") or ""
                notes = pwd.get("notes") or pwd.get("note") or ""
                category = pwd.get("category") or "Importado"
                
                if url or site:
                    self.add_password(
                        site=site,
                        url=url,
                        username=username,
                        password=password,
                        notes=notes,
                        category=category
                    )
                    count += 1
            return count
        except Exception as e:
            print(f"Erro ao importar de JSON: {e}")
            return 0


class ProfileDefaultsManager:
    """
    Gerenciador unificado de configurações padrão para perfis.
    Combina favoritos, extensões e senhas em uma única interface.
    """
    
    def __init__(self, config_dir: str = None, extensions_dir: str = None):
        """
        Inicializa o gerenciador unificado.
        
        Args:
            config_dir: Diretório para armazenar configurações
            extensions_dir: Diretório para armazenar extensões
        """
        self.config_dir = Path(config_dir) if config_dir else CONFIG_DIR
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
        self.extensions_dir = Path(extensions_dir) if extensions_dir else BASE_DIR / "browser_extensions"
        
        self.favorites = FavoritesManager(str(self.config_dir))
        self.extensions = ExtensionsManager(str(self.config_dir), str(self.extensions_dir))
        self.passwords = PasswordManager(str(self.config_dir))
    
    def apply_defaults_to_profile(self, profile_data_dir: Path) -> Dict[str, bool]:
        """
        Aplica todas as configurações padrão a um novo perfil.
        
        Args:
            profile_data_dir: Diretório de dados do perfil
            
        Returns:
            Dicionário com resultado de cada operação
        """
        results = {
            "favorites": False,
            "extensions": False,
        }
        
        # Aplicar favoritos
        try:
            results["favorites"] = self.favorites.apply_to_chrome_profile(profile_data_dir)
        except Exception as e:
            print(f"Erro ao aplicar favoritos: {e}")
        
        # Extensões são aplicadas via chrome_options, não diretamente no perfil
        results["extensions"] = True
        
        return results
    
    def get_extension_paths_for_chrome(self) -> List[str]:
        """
        Retorna os caminhos das extensões para carregar no Chrome.
        
        Returns:
            Lista de caminhos
        """
        return self.extensions.get_extension_paths()
