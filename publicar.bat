@echo off
rem Publica el release del dia en GitHub Releases (build Windows + Linux + gh release).
rem Usa pwsh (PS 7+) para evitar problemas de encoding con tildes en PS 5.1.
cd /d "%~dp0"
pwsh -NoProfile -ExecutionPolicy Bypass -File tools\publish_release.ps1
pause
