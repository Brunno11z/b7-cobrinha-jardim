@echo off
cd /d "%~dp0"
py -3.12 -m venv .venv
if errorlevel 1 goto erro
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto erro
echo Instalado. Agora abra INICIAR.bat
pause
exit /b
:erro
echo Falha. Instale Python 3.12 de python.org e confira a internet.
pause
