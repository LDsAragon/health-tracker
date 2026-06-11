@echo off
cd /d "%~dp0"
echo Iniciando Bitacora...

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python no encontrado. Instala Python desde https://python.org
    pause
    exit /b 1
)

if not exist venv (
    echo Creando entorno virtual...
    python -m venv venv
)

call venv\Scripts\activate.bat

pip show flask >nul 2>&1
if %errorlevel% neq 0 (
    echo Instalando dependencias...
    pip install -r requirements.txt
)

echo Abriendo en el navegador en http://127.0.0.1:5000
python app.py
pause
