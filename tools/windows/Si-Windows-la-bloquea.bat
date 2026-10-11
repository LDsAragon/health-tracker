@echo off
rem Ayuda para cuando Windows no deja abrir Bitacora.exe, que no esta firmada digitalmente.
rem Todo lo que hace se limita a la carpeta de la Bitacora y se puede deshacer: NO apaga
rem Defender, SmartScreen ni Smart App Control para todo el sistema. Apagarlos dejaria la
rem maquina entera expuesta por una sola app, y Smart App Control en muchas versiones no se
rem puede volver a prender sin reinstalar Windows.
rem Va DENTRO de la carpeta Bitacora (make_release.ps1), al lado de Bitacora.exe: asi la
rem auto-actualizacion lo mantiene al dia y %~dp0 es la carpeta de la app.
rem Sin acentos a proposito: cmd lee el .bat con la pagina de codigos de la consola.
setlocal
set "DIR=%~dp0"
set "DIR=%DIR:~0,-1%"
set "BAT=%~f0"

rem Las acciones que piden administrador se relanzan elevadas con un argumento.
if /i "%~1"=="excluir" goto hacer_excluir
if /i "%~1"=="quitar" goto hacer_quitar

:menu
cls
echo ==============================================================
echo   Bitacora - si Windows no la deja abrir
echo ==============================================================
echo   Carpeta: %DIR%
echo.
echo   1. Ver que la esta bloqueando
echo   2. Desbloquear los archivos  (quita la marca "bajado de internet")
echo   3. Que Windows Defender no revise esta carpeta  [pide permiso]
echo   4. Deshacer el 3: que Defender vuelva a revisarla  [pide permiso]
echo   5. Abrir la configuracion de "Control inteligente de aplicaciones"
echo   0. Salir
echo.
rem choice y no set /p: una tecla sin Enter, y no hay texto tipeado que expandir en un if.
choice /c 123450 /n /m "Elegi una opcion (1-5, o 0 para salir): "
rem 255 = choice no pudo leer la consola; sin esta salida el menu giraria para siempre.
if errorlevel 255 exit /b 1
if errorlevel 6 exit /b 0
if errorlevel 5 goto sac
if errorlevel 4 goto quitar
if errorlevel 3 goto excluir
if errorlevel 2 goto desbloquear
if errorlevel 1 goto diagnostico
goto menu

:diagnostico
cls
echo Revisando...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$d = $env:DIR;" ^
  "if (Test-Path -LiteralPath (Join-Path $d 'Bitacora.exe')) { '[ok] Bitacora.exe esta en la carpeta.' }" ^
  "else { '[!] Falta Bitacora.exe. Si la descomprimiste entera, probablemente el antivirus la borro: usa la opcion 3 y volve a descomprimir el zip.' };" ^
  "$m = @(Get-ChildItem -LiteralPath $d -Recurse -File | Where-Object { Get-Item -LiteralPath $_.FullName -Stream Zone.Identifier -ErrorAction SilentlyContinue }).Count;" ^
  "if ($m) { \"[!] $m archivos tienen la marca 'bajado de internet'. Usa la opcion 2.\" } else { '[ok] Ningun archivo tiene la marca de internet.' };" ^
  "$s = $null; try { $s = (Get-MpComputerStatus -ErrorAction Stop).SmartAppControlState } catch {};" ^
  "if ($s -eq 'On') { '[!] Control inteligente de aplicaciones esta PRENDIDO. Bloquea toda app sin firma y no se puede saltear para una sola: mira la opcion 5.' }" ^
  "elseif ($s -eq 'Eval') { '[i] Control inteligente de aplicaciones esta en evaluacion: puede llegar a bloquearla.' }" ^
  "elseif ($s) { '[ok] Control inteligente de aplicaciones esta apagado.' }" ^
  "else { '[i] No se pudo leer el estado del Control inteligente de aplicaciones (Windows 10, u otro antivirus).' }"
echo.
pause
goto menu

:desbloquear
cls
echo Desbloqueando los archivos de %DIR% ...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "Get-ChildItem -LiteralPath $env:DIR -Recurse -File | Unblock-File; 'Listo. Proba abrir Bitacora.exe de nuevo.'"
echo.
pause
goto menu

:excluir
cls
echo Windows va a pedir permiso de administrador para agregar la excepcion.
echo Solo esta carpeta queda sin revisar; el resto de la PC sigue protegida.
echo.
powershell -NoProfile -Command "Start-Process -FilePath $env:BAT -ArgumentList 'excluir' -Verb RunAs -Wait" 2>nul
if errorlevel 1 echo No se dio el permiso: no se cambio nada.
echo.
pause
goto menu

:quitar
cls
echo Windows va a pedir permiso de administrador para quitar la excepcion.
echo.
powershell -NoProfile -Command "Start-Process -FilePath $env:BAT -ArgumentList 'quitar' -Verb RunAs -Wait" 2>nul
if errorlevel 1 echo No se dio el permiso: no se cambio nada.
echo.
pause
goto menu

:sac
cls
echo Control inteligente de aplicaciones (Windows 11) bloquea TODA app sin firma
echo digital, y no deja hacer una excepcion para una sola.
echo.
echo Lo recomendado es bajar la version "Bitacora-Compatible", que abre sin
echo apagar nada.
echo.
echo Este menu NO lo apaga. Apagarlo afecta a toda la PC y en muchas versiones
echo de Windows no se puede volver a prender sin reinstalar. Si igual queres
echo hacerlo, es tu decision: usa "Apagar-Control-inteligente.bat", en esta
echo misma carpeta, o la pantalla de Seguridad de Windows que se abre ahora
echo ("Control de aplicaciones y navegador").
echo.
choice /c sn /n /m "Abrir esa pantalla? (s/n): "
if errorlevel 255 exit /b 1
if not errorlevel 2 start "" "windowsdefender://appbrowser"
goto menu

rem --- Elevadas: corren en su propia ventana de administrador ---

:hacer_excluir
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { Add-MpPreference -ExclusionPath $env:DIR -ErrorAction Stop; 'Listo: Defender ya no revisa ' + $env:DIR }" ^
  "catch { 'No se pudo: ' + $_.Exception.Message; 'Si usas otro antivirus (no Defender), la excepcion se agrega desde ese programa.' }"
echo.
pause
exit /b 0

:hacer_quitar
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "try { Remove-MpPreference -ExclusionPath $env:DIR -ErrorAction Stop; 'Listo: Defender vuelve a revisar ' + $env:DIR }" ^
  "catch { 'No se pudo: ' + $_.Exception.Message }"
echo.
pause
exit /b 0
