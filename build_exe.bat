@echo off
rem Genera dist\HealthTracker\HealthTracker.exe (PyInstaller one-dir).
cd /d "%~dp0"

call venv\Scripts\activate.bat

pip show pyinstaller >nul 2>&1
if %errorlevel% neq 0 pip install pyinstaller
pip show pywebview >nul 2>&1
if %errorlevel% neq 0 pip install -r requirements-desktop.txt

pyinstaller --noconfirm --clean --windowed ^
    --name HealthTracker ^
    --icon static\icon.ico ^
    --add-data "templates;templates" ^
    --add-data "static;static" ^
    desktop.py

echo.
echo Listo: dist\HealthTracker\HealthTracker.exe
pause
