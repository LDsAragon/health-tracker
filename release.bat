@echo off
rem Genera dist\Bitacora-<fecha>.zip listo para compartir (app + LEEME + manual).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File tools\make_release.ps1
pause
