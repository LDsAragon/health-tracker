@echo off
rem Publica el release del dia en GitHub Releases (build Windows + Linux + gh release).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File tools\publish_release.ps1
pause
