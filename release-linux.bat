@echo off
rem Genera dist\Bitacora-linux-<fecha>.tar.gz listo para compartir (corre en WSL).
cd /d "%~dp0"
wsl -d Ubuntu-24.04 -- bash tools/make_release_linux.sh
pause
