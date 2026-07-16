@echo off
REM Script de compilação para Nexor Desktop (Windows)
REM Uso: compile.bat [opção]

setlocal enabledelayedexpansion

REM Cores (simuladas com modo de cor)
set "GREEN=[92m"
set "RED=[91m"
set "YELLOW=[93m"
set "BLUE=[94m"
set "NC=[0m"

REM Títulos
echo.
echo ========================================
echo   NEXOR - Build Script (Windows)
echo ========================================
echo.

REM Verificar Python
echo Verificando Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERRO] Python nao encontrado
    echo Instale Python de: https://www.python.org/downloads/
    pause
    exit /b 1
)
echo [OK] Python encontrado

REM Verificar PyInstaller
echo Verificando PyInstaller...
python -m pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [AVISO] PyInstaller nao instalado. Instalando...
    python -m pip install pyinstaller
)
echo [OK] PyInstaller encontrado

REM Verificar dependências do projeto
if exist requirements.txt (
    echo Instalando dependencias do projeto...
    python -m pip install -q -r requirements.txt
    echo [OK] Dependencias instaladas
)

REM Menu
:menu
echo.
echo Escolha uma opcao:
echo 1. Compilar para Windows
echo 2. Compilar para Windows + Criar Instalador
echo 3. Limpar builds anteriores
echo 4. Verificar dependencias
echo 0. Sair
echo.
set /p choice="Opcao: "

if "%choice%"=="1" goto compile
if "%choice%"=="2" goto compile_installer
if "%choice%"=="3" goto clean
if "%choice%"=="4" goto check
if "%choice%"=="0" goto end
echo [ERRO] Opcao invalida
goto menu

:compile
echo.
echo ========================================
echo   Compilando para Windows...
echo ========================================
echo.

REM Limpar builds anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist nexor.spec del nexor.spec

REM Compilar
pyinstaller ^
    --onefile ^
    --windowed ^
    --name=Nexor ^
    --icon=app/static/icon.ico ^
    --distpath=dist ^
    --buildpath=build ^
    nexor.spec

if errorlevel 1 (
    echo [ERRO] Erro durante compilacao
    pause
    exit /b 1
)

echo.
echo [OK] Compilacao concluida!
echo [INFO] Executavel: dist\Nexor.exe
echo.
pause
goto menu

:compile_installer
echo.
echo ========================================
echo   Compilando para Windows...
echo ========================================
echo.

REM Limpar builds anteriores
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist nexor.spec del nexor.spec

REM Compilar
pyinstaller ^
    --onefile ^
    --windowed ^
    --name=Nexor ^
    --icon=app/static/icon.ico ^
    --distpath=dist ^
    --buildpath=build ^
    nexor.spec

if errorlevel 1 (
    echo [ERRO] Erro durante compilacao
    pause
    exit /b 1
)

echo.
echo [OK] Compilacao concluida!
echo.

REM Verificar NSIS
where makensis >nul 2>&1
if errorlevel 1 (
    echo [AVISO] NSIS nao instalado
    echo [INFO] Para criar instalador, instale NSIS: https://nsis.sourceforge.io/
    pause
    goto menu
)

echo ========================================
echo   Criando Instalador NSIS...
echo ========================================
echo.

REM Criar script NSIS
(
echo !include "MUI2.nsh"
echo.
echo Name "Nexor"
echo OutFile "Nexor-Setup.exe"
echo InstallDir "$PROGRAMFILES\Nexor"
echo.
echo !insertmacro MUI_PAGE_WELCOME
echo !insertmacro MUI_PAGE_DIRECTORY
echo !insertmacro MUI_PAGE_INSTFILES
echo !insertmacro MUI_PAGE_FINISH
echo.
echo !insertmacro MUI_LANGUAGE "Portuguese"
echo.
echo Section "Instalar"
echo   SetOutPath "$INSTDIR"
echo   File "dist\Nexor.exe"
echo.
echo   CreateDirectory "$SMPROGRAMS\Nexor"
echo   CreateShortcut "$SMPROGRAMS\Nexor\Nexor.lnk" "$INSTDIR\Nexor.exe"
echo   CreateShortcut "$DESKTOP\Nexor.lnk" "$INSTDIR\Nexor.exe"
echo.
echo   WriteUninstaller "$INSTDIR\Uninstall.exe"
echo   CreateShortcut "$SMPROGRAMS\Nexor\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
echo SectionEnd
echo.
echo Section "Desinstalar"
echo   Delete "$INSTDIR\Nexor.exe"
echo   Delete "$INSTDIR\Uninstall.exe"
echo   RMDir "$INSTDIR"
echo.
echo   Delete "$SMPROGRAMS\Nexor\Nexor.lnk"
echo   Delete "$SMPROGRAMS\Nexor\Uninstall.lnk"
echo   RMDir "$SMPROGRAMS\Nexor"
echo.
echo   Delete "$DESKTOP\Nexor.lnk"
echo SectionEnd
) > nexor_installer.nsi

REM Executar NSIS
makensis nexor_installer.nsi

if errorlevel 1 (
    echo [ERRO] Erro ao criar instalador
    pause
    exit /b 1
)

echo.
echo [OK] Instalador criado: Nexor-Setup.exe
echo.
pause
goto menu

:clean
echo.
echo Limpando builds anteriores...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist nexor.spec del nexor.spec
echo [OK] Limpeza concluida
echo.
pause
goto menu

:check
echo.
echo ========================================
echo   Verificando Dependencias
echo ========================================
echo.
python --version
echo.
python -m pip show pyinstaller
echo.
python -m pip show flask
echo.
echo [OK] Dependencias verificadas
echo.
pause
goto menu

:end
echo.
echo Saindo...
exit /b 0
