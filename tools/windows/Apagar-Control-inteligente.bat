@echo off
rem Apaga "Control inteligente de aplicaciones" (Smart App Control) en TODA la PC.
rem Es una decision de la persona sobre su maquina, y por eso el script la toma solo despues
rem de explicarla y de una confirmacion: afecta a todos los programas, no solo a la Bitacora, y
rem en muchas versiones de Windows no se puede volver a prender sin reinstalar. La alternativa
rem que no apaga nada es el zip Bitacora-Compatible. Tampoco reinicia sin preguntar: se perderia
rem lo que la persona tenga abierto.
rem Sin acentos a proposito: cmd lee el .bat con la pagina de codigos de la consola.
setlocal
set "CLAVE=HKLM\SYSTEM\CurrentControlSet\Control\CI\Policy"
set "VALOR=VerifiedAndReputablePolicyState"

rem El registro de HKLM pide administrador: se relanza elevado (Windows pregunta). fltmc y no
rem "net session", que falla aun siendo administrador si el servicio Servidor esta apagado: el
rem script se relanzaria pidiendo permiso para siempre. Por lo mismo, "elevado" corta el bucle.
set "BAT=%~f0"
fltmc >nul 2>&1
if not errorlevel 1 goto es_admin
if /i "%~1"=="elevado" (
    echo No se pudo obtener permiso de administrador. No se cambio nada.
    pause
    exit /b 1
)
echo Windows va a pedir permiso de administrador.
powershell -NoProfile -Command "Start-Process -FilePath $env:BAT -ArgumentList 'elevado' -Verb RunAs" 2>nul
if errorlevel 1 (
    echo No se dio el permiso: no se cambio nada.
    pause
)
exit /b

:es_admin

cls
echo ==============================================================
echo   Apagar "Control inteligente de aplicaciones"
echo ==============================================================
echo.

rem 0 = apagado, 1 = prendido, 2 = en evaluacion. Si no esta, este Windows no lo tiene.
set "ESTADO="
for /f "tokens=3" %%v in ('reg query "%CLAVE%" /v %VALOR% 2^>nul ^| find "%VALOR%"') do set "ESTADO=%%v"
if not defined ESTADO goto no_existe
if "%ESTADO%"=="0x0" goto ya_apagado
if "%ESTADO%"=="0x1" echo   Estado actual: PRENDIDO
if "%ESTADO%"=="0x2" echo   Estado actual: EN EVALUACION

echo.
echo   Antes de seguir, lee esto:
echo.
echo   - Se apaga para TODA la computadora, no solo para la Bitacora.
echo     Es una proteccion que frena programas peligrosos.
echo   - En muchas versiones de Windows NO se puede volver a prender
echo     sin reinstalar Windows.
echo   - Hay otra opcion que no apaga nada: la version
echo     "Bitacora-Compatible", que Windows deja abrir tal como esta.
echo.
choice /c sn /n /m "Apagarlo igual? (s/n): "
if errorlevel 2 goto cancelado

reg add "%CLAVE%" /v %VALOR% /t REG_DWORD /d 0 /f >nul
if errorlevel 1 (
    echo.
    echo No se pudo cambiar el registro. No se cambio nada.
    pause
    exit /b 1
)

echo.
echo Listo. El cambio se aplica despues de reiniciar Windows.
echo Guarda lo que tengas abierto antes de seguir.
echo.
choice /c sn /n /m "Reiniciar ahora? (s/n): "
if errorlevel 2 (
    echo.
    echo Reinicia cuando puedas; hasta entonces sigue prendido.
    pause
    exit /b 0
)
shutdown /r /t 10 /c "Reiniciando para apagar Control inteligente de aplicaciones"
echo La PC se reinicia en 10 segundos.
pause
exit /b 0

:ya_apagado
echo   Ya esta apagado: no hay nada que cambiar.
echo   Si la Bitacora igual no abre, usa "Si-Windows-la-bloquea.bat".
echo.
pause
exit /b 0

:no_existe
echo   No se encontro el ajuste de "Control inteligente de aplicaciones":
echo   este Windows no lo tiene, o nunca lo prendio. No hay nada que apagar.
echo.
pause
exit /b 0

:cancelado
echo.
echo No se cambio nada.
pause
exit /b 0
