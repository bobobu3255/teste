#!/usr/bin/env python3
"""
Telegram Collector Pro v12.0 Preview - Build Script
============================================

Script otimizado para criar executável funcional que pode ser fixado
na barra de tarefas do Windows.

Requisitos:
    pip install pyinstaller pyqt5 pillow

Uso:
    python build_exe.py
    
    ou no Windows:
    
    BUILD_EXE.bat
"""

import os
import sys
import shutil
import subprocess

# Diretório atual
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(CURRENT_DIR, 'dist')
BUILD_DIR = os.path.join(CURRENT_DIR, 'build')

# Nome do executável
APP_NAME = 'TelegramCollectorPro_v12_preview'
APP_ID = 'TelegramCollector.Pro.v12.preview'

# Ícone (será gerado se não existir)
ICON_PATH = os.path.join(CURRENT_DIR, 'app_icon.ico')


def create_icon():
    """Cria um ícone .ico para a aplicação"""
    print("🎨 Criando ícone da aplicação...")
    
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError:
        print("   ⚠️ Pillow não encontrado, instalando...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pillow'], check=True)
        from PIL import Image, ImageDraw, ImageFont
    
    # Criar imagem 256x256 com gradiente
    size = 256
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # Desenhar círculo com gradiente (simulado com círculos concêntricos)
    center = size // 2
    for i in range(center, 0, -1):
        # Interpolar cor do gradiente
        ratio = i / center
        r = int(139 * ratio + 109 * (1 - ratio))  # #8b5cf6 -> #6d28d9
        g = int(92 * ratio + 40 * (1 - ratio))
        b = int(246 * ratio + 217 * (1 - ratio))
        color = (r, g, b, 255)
        
        # Desenhar círculo
        draw.ellipse(
            [center - i, center - i, center + i, center + i],
            fill=color
        )
    
    # Adicionar texto "TC" no centro
    try:
        # Tentar usar fonte do sistema
        font = ImageFont.truetype("arial.ttf", 100)
    except:
        # Usar fonte padrão
        font = ImageFont.load_default()
    
    text = "TC"
    # Calcular posição do texto
    try:
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
    except:
        text_width, text_height = 80, 80
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 10
    
    # Desenhar texto
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    # Criar diferentes tamanhos para o .ico
    sizes = [16, 32, 48, 64, 128, 256]
    images = []
    for s in sizes:
        resized = img.resize((s, s), Image.Resampling.LANCZOS if hasattr(Image, 'Resampling') else Image.LANCZOS)
        images.append(resized)
    
    # Salvar como .ico
    img.save(ICON_PATH, format='ICO', sizes=[(s, s) for s in sizes])
    print(f"   ✅ Ícone criado: {ICON_PATH}")
    
    return ICON_PATH


def check_dependencies():
    """Verifica se as dependências estão instaladas."""
    print("🔍 Verificando dependências...")
    
    try:
        import PyInstaller
        print(f"   ✅ PyInstaller {PyInstaller.__version__}")
    except ImportError:
        print("   ❌ PyInstaller não encontrado!")
        print("   Instalando: pip install pyinstaller")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'], check=True)
    
    try:
        from PyQt5 import QtCore
        print(f"   ✅ PyQt5 {QtCore.PYQT_VERSION_STR}")
    except ImportError:
        print("   ❌ PyQt5 não encontrado!")
        print("   Instalando: pip install pyqt5")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyqt5'], check=True)
    
    try:
        import PIL
        print(f"   ✅ Pillow {PIL.__version__}")
    except ImportError:
        print("   ⚠️ Pillow não encontrado, instalando...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'pillow'], check=True)


def clean_build():
    """Limpa diretórios de build anteriores."""
    print("\n🧹 Limpando builds anteriores...")
    
    for dir_path in [DIST_DIR, BUILD_DIR]:
        if os.path.exists(dir_path):
            shutil.rmtree(dir_path)
            print(f"   Removido: {dir_path}")
    
    # Remover spec antigo
    spec_file = os.path.join(CURRENT_DIR, f'{APP_NAME}.spec')
    if os.path.exists(spec_file):
        os.remove(spec_file)


def create_version_info():
    """Cria arquivo de informações de versão para o executável Windows"""
    version_info = f'''
# UTF-8
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(10, 2, 0, 0),
    prodvers=(10, 2, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
      StringTable(
        u'040904B0',
        [StringStruct(u'CompanyName', u'Telegram Collector'),
        StringStruct(u'FileDescription', u'Telegram Collector Pro - Coletor de Dados'),
        StringStruct(u'FileVersion', u'10.2.0.0'),
        StringStruct(u'InternalName', u'{APP_NAME}'),
        StringStruct(u'LegalCopyright', u'Copyright 2025'),
        StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
        StringStruct(u'ProductName', u'Telegram Collector Pro'),
        StringStruct(u'ProductVersion', u'10.2.0.0')])
      ]),
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    version_file = os.path.join(CURRENT_DIR, 'version_info.txt')
    with open(version_file, 'w', encoding='utf-8') as f:
        f.write(version_info)
    
    return version_file


def build_exe():
    """Executa o PyInstaller para criar o executável."""
    print("\n🔨 Construindo executável...")
    print(f"   Nome: {APP_NAME}.exe")
    print(f"   Arquivo principal: main_app.py")
    
    import PyInstaller.__main__
    
    # Criar ícone se não existir
    icon_path = ICON_PATH if os.path.exists(ICON_PATH) else create_icon()
    
    # Criar arquivo de versão
    version_file = create_version_info()
    
    # Arquivo principal a ser compilado
    main_file = os.path.join(CURRENT_DIR, 'main_app.py')
    
    if not os.path.exists(main_file):
        print(f"   ❌ ERRO: Arquivo {main_file} não encontrado!")
        return False
    
    # Argumentos do PyInstaller
    args = [
        main_file,
        f'--name={APP_NAME}',
        '--onefile',
        '--windowed',  # Sem console
        f'--icon={icon_path}',
        
        # Informações de versão (Windows)
        f'--version-file={version_file}',
        
        # Imports ocultos necessários
        '--hidden-import=PyQt5',
        '--hidden-import=PyQt5.QtCore',
        '--hidden-import=PyQt5.QtGui',
        '--hidden-import=PyQt5.QtWidgets',
        '--hidden-import=PyQt5.sip',
        '--hidden-import=sqlite3',
        '--hidden-import=json',
        '--hidden-import=asyncio',
        '--hidden-import=ctypes',
        
        # Coletar módulos
        '--collect-submodules=PyQt5',
        
        # Otimizações
        '--noupx',  # Não usar UPX (mais estável)
        '--noconfirm',
        '--clean',
        
        # Diretórios de saída
        f'--distpath={DIST_DIR}',
        f'--workpath={BUILD_DIR}',
        f'--specpath={CURRENT_DIR}',
    ]
    
    # Adicionar dados adicionais se existirem
    data_dirs = [
        'crunchyroll_bot',
        'browser_extensions',
        'browser_profiles',
        'browser_config',
        'generators',
        'services',
        'ui',
        'crunchyroll_login_bot'
    ]
    
    for data_dir in data_dirs:
        dir_path = os.path.join(CURRENT_DIR, data_dir)
        if os.path.exists(dir_path):
            # Formato: source;dest (Windows) ou source:dest (Unix)
            separator = ';' if sys.platform == 'win32' else ':'
            args.append(f'--add-data={dir_path}{separator}{data_dir}')
            print(f"   📁 Incluindo: {data_dir}/")
    
    # Adicionar arquivos JSON
    json_files = ['enderecos_reserva.json', 'contas.json', 'grupos.json']
    for json_file in json_files:
        file_path = os.path.join(CURRENT_DIR, json_file)
        if os.path.exists(file_path):
            separator = ';' if sys.platform == 'win32' else ':'
            args.append(f'--add-data={file_path}{separator}.')
    
    # Executar PyInstaller
    try:
        PyInstaller.__main__.run(args)
    except Exception as e:
        print(f"   ❌ Erro durante build: {e}")
        return False
    
    # Limpar arquivo de versão temporário
    if os.path.exists(version_file):
        os.remove(version_file)
    
    return True


def copy_additional_files():
    """Copia arquivos adicionais necessários para a pasta dist."""
    print("\n📁 Copiando arquivos adicionais...")
    
    # Criar pasta data se não existir
    data_dir = os.path.join(DIST_DIR, 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    # Copiar crunchyroll_bot para dist (necessário para Node.js)
    for bot_dir in ['crunchyroll_bot', 'crunchyroll_login_bot']:
        src_bot = os.path.join(CURRENT_DIR, bot_dir)
        dst_bot = os.path.join(DIST_DIR, bot_dir)
        
        if os.path.exists(src_bot) and not os.path.exists(dst_bot):
            shutil.copytree(src_bot, dst_bot)
            print(f"   ✅ Copiado: {bot_dir}/")
    
    # Copiar ícone para dist
    if os.path.exists(ICON_PATH):
        shutil.copy(ICON_PATH, DIST_DIR)
        print(f"   ✅ Copiado: app_icon.ico")
    
    # Copiar enderecos_reserva.json
    endereco_file = os.path.join(CURRENT_DIR, 'enderecos_reserva.json')
    if os.path.exists(endereco_file):
        shutil.copy(endereco_file, DIST_DIR)
        print(f"   ✅ Copiado: enderecos_reserva.json")
    
    # Criar README
    readme_content = f"""
# Telegram Collector Pro v12.0 Preview
==============================

## Novidades da versão 10.2:

✅ **Modo Fixado (Always on Top)**: Mantenha a janela sempre visível
✅ **Modo Compacto Funcional**: Interface dedicada com Gerador de Pares e CEP
✅ **Fixar na Barra de Tarefas**: Agora funciona corretamente no Windows
✅ **Ícone na Bandeja**: Minimize para a bandeja do sistema

## Como usar:

1. Execute {APP_NAME}.exe

2. Use os botões no canto superior direito:
   - 📌 Fixar: Mantém a janela sempre no topo
   - 📱 Compacto: Interface compacta com Gerador de Pares e CEP

3. Para fixar na barra de tarefas do Windows:
   - Clique com botão direito no ícone na barra de tarefas
   - Selecione "Fixar na barra de tarefas"

## Modo Compacto:

No modo compacto você tem acesso a:
- Gerador de Pares (Nome + CPF)
- Gerador de CEP (Endereço completo)
- Botões de copiar individual e copiar tudo

## Arquivos:

- {APP_NAME}.exe - Aplicativo principal
- app_icon.ico - Ícone da aplicação
- crunchyroll_bot/ - Bot Node.js (se aplicável)
- data/ - Pasta de dados (criada automaticamente)

## Requisitos:

- Windows 10/11
- Node.js 18+ (apenas para bot Crunchyroll)
"""
    
    readme_path = os.path.join(DIST_DIR, 'LEIA-ME.txt')
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    print(f"   ✅ Criado: LEIA-ME.txt")


def create_launcher_bat():
    """Cria um arquivo .bat para facilitar a execução."""
    bat_content = f'''@echo off
title Telegram Collector Pro v12.0 Preview
echo.
echo ========================================
echo    Telegram Collector Pro v12.0 Preview
echo ========================================
echo.
echo Iniciando aplicativo...
echo.
start "" "{APP_NAME}.exe"
'''
    
    bat_path = os.path.join(DIST_DIR, 'INICIAR.bat')
    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(bat_content)
    print(f"   ✅ Criado: INICIAR.bat")


def main():
    """Função principal."""
    print("="*60)
    print("   🎲 Telegram Collector Pro v12.0 Preview - Build Script")
    print("="*60)
    
    # Verificar dependências
    check_dependencies()
    
    # Limpar builds anteriores
    clean_build()
    
    # Criar ícone
    if not os.path.exists(ICON_PATH):
        create_icon()
    
    # Construir executável
    success = build_exe()
    
    if success:
        # Copiar arquivos adicionais
        copy_additional_files()
        
        # Criar launcher
        create_launcher_bat()
    
    # Resultado final
    exe_path = os.path.join(DIST_DIR, f'{APP_NAME}.exe')
    
    print("\n" + "="*60)
    if os.path.exists(exe_path):
        exe_size = os.path.getsize(exe_path) / (1024 * 1024)  # MB
        print("   ✅ BUILD CONCLUÍDO COM SUCESSO!")
        print("="*60)
        print(f"\n   📦 Executável: {exe_path}")
        print(f"   📊 Tamanho: {exe_size:.1f} MB")
        print(f"\n   📁 Pasta de distribuição: {DIST_DIR}")
        print("\n   📌 Para fixar na barra de tarefas:")
        print("      1. Execute o aplicativo")
        print("      2. Clique com botão direito no ícone na barra")
        print("      3. Selecione 'Fixar na barra de tarefas'")
        print("\n   Para distribuir, copie toda a pasta 'dist'")
    else:
        print("   ❌ ERRO: Executável não foi criado!")
        print("="*60)
        print("\n   Verifique os erros acima e tente novamente.")
    
    print()


if __name__ == '__main__':
    main()
