@echo off
cd /d "%~dp0"
if not exist .venv\Scripts\python.exe (
echo Execute INSTALAR.bat primeiro.
pause
exit /b
)
if exist CHAVE_GROQ_LOCAL.bat call CHAVE_GROQ_LOCAL.bat
if exist CHAVE_GROK_LOCAL.bat call CHAVE_GROK_LOCAL.bat
start "Painel B7" http://127.0.0.1:8765
.venv\Scripts\python.exe main.py
pause
