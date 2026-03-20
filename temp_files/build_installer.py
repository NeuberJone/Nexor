"""
Build Script - Criar instaladores para Nexor
Gera executáveis para Windows, macOS e Linux
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

# Diretórios
PROJECT_DIR = Path(__file__).parent
DIST_DIR = PROJECT_DIR / 'dist'
BUILD_DIR = PROJECT_DIR / 'build'
SPEC_FILE = PROJECT_DIR / 'nexor.spec'

def clean_build():
    """Remove diretórios de build anteriores"""
    print("Limpando builds anteriores...")
    for directory in [BUILD_DIR, DIST_DIR]:
        if directory.exists():
            shutil.rmtree(directory)
    if SPEC_FILE.exists():
        SPEC_FILE.unlink()
    print("✓ Limpeza concluída")

def create_spec_file():
    """Cria arquivo .spec para PyInstaller"""
    print("Criando arquivo de especificação...")
    
    spec_content = '''# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['app_desktop.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('app/templates', 'app/templates'),
        ('app/static', 'app/static'),
        ('requirements.txt', '.'),
    ],
    hiddenimports=[
        'flask',
        'flask_cors',
        'requests',
        'jinja2',
        'werkzeug',
        'reportlab',
        'PIL',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludedimports=[],
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=None)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='Nexor',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app/static/icon.ico',
)
'''
    
    with open(SPEC_FILE, 'w') as f:
        f.write(spec_content)
    
    print("✓ Arquivo de especificação criado")

def build_windows():
    """Cria instalador para Windows"""
    print("\n" + "=" * 60)
    print("Compilando para Windows...")
    print("=" * 60)
    
    # Verificar se PyInstaller está instalado
    try:
        subprocess.run(['pyinstaller', '--version'], check=True, capture_output=True)
    except:
        print("✗ PyInstaller não está instalado")
        print("  Execute: pip install pyinstaller")
        return False
    
    # Executar PyInstaller
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=Nexor',
        '--icon=app/static/icon.ico',
        'app_desktop.py'
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    
    if result.returncode == 0:
        print("✓ Executável criado com sucesso!")
        print(f"  Localização: {DIST_DIR / 'Nexor.exe'}")
        return True
    else:
        print("✗ Erro ao compilar")
        return False

def build_macos():
    """Cria instalador para macOS"""
    print("\n" + "=" * 60)
    print("Compilando para macOS...")
    print("=" * 60)
    
    if sys.platform != 'darwin':
        print("⚠ Este script está rodando em Windows/Linux")
        print("  Para compilar para macOS, execute este script em um Mac")
        return False
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=Nexor',
        '--icon=app/static/icon.icns',
        'app_desktop.py'
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    
    if result.returncode == 0:
        print("✓ App para macOS criado com sucesso!")
        print(f"  Localização: {DIST_DIR / 'Nexor.app'}")
        return True
    else:
        print("✗ Erro ao compilar")
        return False

def build_linux():
    """Cria instalador para Linux"""
    print("\n" + "=" * 60)
    print("Compilando para Linux...")
    print("=" * 60)
    
    if sys.platform not in ['linux', 'linux2']:
        print("⚠ Este script está rodando em Windows/macOS")
        print("  Para compilar para Linux, execute este script em um Linux")
        return False
    
    cmd = [
        'pyinstaller',
        '--onefile',
        '--windowed',
        '--name=Nexor',
        'app_desktop.py'
    ]
    
    result = subprocess.run(cmd, cwd=PROJECT_DIR)
    
    if result.returncode == 0:
        print("✓ Executável para Linux criado com sucesso!")
        print(f"  Localização: {DIST_DIR / 'Nexor'}")
        return True
    else:
        print("✗ Erro ao compilar")
        return False

def create_installer_windows():
    """Cria instalador NSIS para Windows"""
    print("\nCriando instalador NSIS...")
    
    nsis_script = '''
; Nexor Installer Script
; Requer NSIS (https://nsis.sourceforge.io)

!include "MUI2.nsh"

Name "Nexor"
OutFile "Nexor-Setup.exe"
InstallDir "$PROGRAMFILES\\Nexor"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Portuguese"

Section "Install"
  SetOutPath "$INSTDIR"
  File "dist\\Nexor.exe"
  
  CreateDirectory "$SMPROGRAMS\\Nexor"
  CreateShortcut "$SMPROGRAMS\\Nexor\\Nexor.lnk" "$INSTDIR\\Nexor.exe"
  CreateShortcut "$DESKTOP\\Nexor.lnk" "$INSTDIR\\Nexor.exe"
  
  WriteUninstaller "$INSTDIR\\Uninstall.exe"
  CreateShortcut "$SMPROGRAMS\\Nexor\\Uninstall.lnk" "$INSTDIR\\Uninstall.exe"
SectionEnd

Section "Uninstall"
  Delete "$INSTDIR\\Nexor.exe"
  Delete "$INSTDIR\\Uninstall.exe"
  RMDir "$INSTDIR"
  
  Delete "$SMPROGRAMS\\Nexor\\Nexor.lnk"
  Delete "$SMPROGRAMS\\Nexor\\Uninstall.lnk"
  RMDir "$SMPROGRAMS\\Nexor"
  
  Delete "$DESKTOP\\Nexor.lnk"
SectionEnd
'''
    
    nsis_file = PROJECT_DIR / 'nexor_installer.nsi'
    with open(nsis_file, 'w') as f:
        f.write(nsis_script)
    
    print("✓ Script NSIS criado")
    print("  Para criar o instalador, instale NSIS e execute:")
    print(f"  makensis {nsis_file}")

def main():
    """Função principal"""
    print("=" * 60)
    print("  NEXOR - Build Installer")
    print("=" * 60)
    print()
    
    # Verificar dependências
    print("Verificando dependências...")
    try:
        import PyInstaller
        print("✓ PyInstaller instalado")
    except ImportError:
        print("✗ PyInstaller não está instalado")
        print("  Execute: pip install pyinstaller")
        sys.exit(1)
    
    # Menu
    print("\nEscolha a plataforma:")
    print("1. Windows (.exe)")
    print("2. macOS (.app)")
    print("3. Linux (executável)")
    print("4. Todas as plataformas")
    print("0. Sair")
    
    choice = input("\nOpção: ").strip()
    
    if choice == '0':
        sys.exit(0)
    
    # Limpar builds anteriores
    clean_build()
    
    # Criar arquivo .spec
    create_spec_file()
    
    # Compilar conforme escolha
    if choice == '1':
        build_windows()
        create_installer_windows()
    elif choice == '2':
        build_macos()
    elif choice == '3':
        build_linux()
    elif choice == '4':
        build_windows()
        build_macos()
        build_linux()
    else:
        print("Opção inválida")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("Build concluído!")
    print(f"Arquivos em: {DIST_DIR}")
    print("=" * 60)

if __name__ == '__main__':
    main()
