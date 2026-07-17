@echo off
setlocal
set "VERSION=0.2.8"
set "SOURCE=%~dp0..\dist\%VERSION%\installable"
set "TARGET=%LOCALAPPDATA%\Programs\Nexor"
if not exist "%SOURCE%\Nexor-v%VERSION%.exe" exit /b 1
if not exist "%TARGET%" mkdir "%TARGET%"
xcopy "%SOURCE%\*" "%TARGET%\" /E /I /Y >nul
start "" "%TARGET%\Nexor-v%VERSION%.exe"
endlocal
