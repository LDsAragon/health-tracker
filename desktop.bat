@echo off
rem Modo ventana (pywebview) sin empaquetar. El .exe se genera con toolsmake_release.ps1.
cd /d "%~dp0"

if not exist venv (
    echo Falta el venv. Corre start.bat primero para crearlo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat

pip show pywebview >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias de escritorio...
    pip install -r requirements-desktop.txt
)

python main.py
