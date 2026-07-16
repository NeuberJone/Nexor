#!/bin/bash
# Script de compilação simplificado para Nexor Desktop

set -e  # Parar em caso de erro

# Cores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Funções
print_header() {
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}========================================${NC}"
}

print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

# Detectar SO
detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "Linux";;
        Darwin*)    echo "macOS";;
        CYGWIN*)    echo "Windows";;
        MINGW*)     echo "Windows";;
        *)          echo "UNKNOWN";;
    esac
}

# Verificar dependências
check_dependencies() {
    print_header "Verificando Dependências"
    
    # Python
    if ! command -v python3 &> /dev/null; then
        print_error "Python3 não encontrado"
        exit 1
    fi
    print_success "Python3 encontrado: $(python3 --version)"
    
    # PyInstaller
    if ! python3 -m pip show pyinstaller &> /dev/null; then
        print_warning "PyInstaller não instalado. Instalando..."
        python3 -m pip install pyinstaller
    fi
    print_success "PyInstaller encontrado"
    
    # Dependências do projeto
    if [ -f "requirements.txt" ]; then
        print_warning "Instalando dependências do projeto..."
        python3 -m pip install -q -r requirements.txt
        print_success "Dependências instaladas"
    fi
}

# Limpar builds anteriores
clean_build() {
    print_header "Limpando Builds Anteriores"
    
    rm -rf build/ dist/ *.spec __pycache__ app/__pycache__
    print_success "Limpeza concluída"
}

# Compilar
compile_app() {
    local os_type=$1
    
    print_header "Compilando para $os_type"
    
    case "$os_type" in
        Windows)
            print_warning "Compilando para Windows..."
            pyinstaller \
                --onefile \
                --windowed \
                --name=Nexor \
                --icon=app/static/icon.ico \
                --distpath=dist \
                --buildpath=build \
                nexor.spec
            ;;
        macOS)
            print_warning "Compilando para macOS..."
            pyinstaller \
                --onefile \
                --windowed \
                --name=Nexor \
                --icon=app/static/icon.icns \
                --distpath=dist \
                --buildpath=build \
                nexor.spec
            ;;
        Linux)
            print_warning "Compilando para Linux..."
            pyinstaller \
                --onefile \
                --windowed \
                --name=Nexor \
                --distpath=dist \
                --buildpath=build \
                nexor.spec
            ;;
        *)
            print_error "SO desconhecido: $os_type"
            exit 1
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        print_success "Compilação concluída!"
    else
        print_error "Erro durante compilação"
        exit 1
    fi
}

# Testar executável
test_executable() {
    print_header "Testando Executável"
    
    local os_type=$(detect_os)
    local exe_path=""
    
    case "$os_type" in
        Windows)
            exe_path="dist/Nexor.exe"
            ;;
        macOS)
            exe_path="dist/Nexor.app/Contents/MacOS/Nexor"
            ;;
        Linux)
            exe_path="dist/Nexor"
            ;;
    esac
    
    if [ -f "$exe_path" ]; then
        print_success "Executável encontrado: $exe_path"
        print_warning "Para testar, execute: $exe_path"
    else
        print_error "Executável não encontrado: $exe_path"
    fi
}

# Criar instalador (Windows)
create_installer_windows() {
    print_header "Criando Instalador Windows"
    
    if ! command -v makensis &> /dev/null; then
        print_warning "NSIS não instalado. Pulando criação de instalador."
        print_warning "Para criar instalador, instale NSIS: https://nsis.sourceforge.io/"
        return
    fi
    
    # Criar script NSIS
    cat > nexor_installer.nsi << 'EOF'
!include "MUI2.nsh"

Name "Nexor"
OutFile "Nexor-Setup.exe"
InstallDir "$PROGRAMFILES\Nexor"

!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_LANGUAGE "Portuguese"

Section "Instalar"
  SetOutPath "$INSTDIR"
  File "dist\Nexor.exe"
  
  CreateDirectory "$SMPROGRAMS\Nexor"
  CreateShortcut "$SMPROGRAMS\Nexor\Nexor.lnk" "$INSTDIR\Nexor.exe"
  CreateShortcut "$DESKTOP\Nexor.lnk" "$INSTDIR\Nexor.exe"
  
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortcut "$SMPROGRAMS\Nexor\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
SectionEnd

Section "Desinstalar"
  Delete "$INSTDIR\Nexor.exe"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  
  Delete "$SMPROGRAMS\Nexor\Nexor.lnk"
  Delete "$SMPROGRAMS\Nexor\Uninstall.lnk"
  RMDir "$SMPROGRAMS\Nexor"
  
  Delete "$DESKTOP\Nexor.lnk"
SectionEnd
EOF
    
    makensis nexor_installer.nsi
    
    if [ $? -eq 0 ]; then
        print_success "Instalador criado: Nexor-Setup.exe"
    else
        print_error "Erro ao criar instalador"
    fi
}

# Menu principal
show_menu() {
    echo ""
    echo -e "${BLUE}Escolha uma opção:${NC}"
    echo "1. Compilar para SO atual"
    echo "2. Compilar para Windows"
    echo "3. Compilar para macOS"
    echo "4. Compilar para Linux"
    echo "5. Limpar builds"
    echo "6. Verificar dependências"
    echo "0. Sair"
    echo ""
}

# Main
main() {
    print_header "NEXOR - Build Script"
    
    # Se passar argumento, usar direto
    if [ $# -gt 0 ]; then
        case "$1" in
            clean)
                clean_build
                exit 0
                ;;
            check)
                check_dependencies
                exit 0
                ;;
            *)
                print_error "Opção desconhecida: $1"
                exit 1
                ;;
        esac
    fi
    
    # Menu interativo
    while true; do
        show_menu
        read -p "Opção: " choice
        
        case $choice in
            1)
                local os_type=$(detect_os)
                check_dependencies
                clean_build
                compile_app "$os_type"
                test_executable
                
                if [ "$os_type" = "Windows" ]; then
                    read -p "Criar instalador NSIS? (s/n): " create_inst
                    if [ "$create_inst" = "s" ] || [ "$create_inst" = "S" ]; then
                        create_installer_windows
                    fi
                fi
                ;;
            2)
                check_dependencies
                clean_build
                compile_app "Windows"
                test_executable
                ;;
            3)
                check_dependencies
                clean_build
                compile_app "macOS"
                test_executable
                ;;
            4)
                check_dependencies
                clean_build
                compile_app "Linux"
                test_executable
                ;;
            5)
                clean_build
                ;;
            6)
                check_dependencies
                ;;
            0)
                print_success "Saindo..."
                exit 0
                ;;
            *)
                print_error "Opção inválida"
                ;;
        esac
    done
}

# Executar
main "$@"
