# Un solo lugar para todos los comandos del proyecto.
#
# Sin argumentos los lista: antes habia que saber de memoria que existian publicar.bat,
# release-linux.bat, tools/make_manual.ps1 y cuatro smoke tests.
#
# NO duplica logica: cada subcomando despacha al script de tools/ que ya hacia el trabajo, asi
# que el que ya se los sabe puede seguir llamandolos directo.
#
#   .\hacer.ps1                     lista los comandos
#   .\hacer.ps1 tests
#   .\hacer.ps1 publicar -Aviso "..."
param(
    [Parameter(Position = 0)][string]$Comando = "",
    [Parameter(Position = 1, ValueFromRemainingArguments = $true)][string[]]$Resto = @()
)

$ErrorActionPreference = "Stop"
$raiz = $PSScriptRoot
Set-Location $raiz

$py = Join-Path $raiz "venv\Scripts\python.exe"

# nombre → @{ d = descripcion; f = que hacer }
$COMANDOS = [ordered]@{
    "abrir" = @{
        d = "Abre la ventana de la app sin empaquetar (modo desarrollo)"
        f = {
            # Lo que hacia desktop.bat: el venv base solo trae flask, y la ventana necesita
            # pywebview. Sin esto el primer `abrir` es un ImportError pelado.
            & $py -c "import webview" 2>$null
            if ($LASTEXITCODE -ne 0) {
                Write-Output "Falta pywebview, lo instalo..."
                & $py "-m" "pip" "install" "-q" "-r" "requirements-desktop.txt"
            }
            & $py "main.py" @Resto
        }
    }
    "navegador" = @{
        d = "Levanta el servidor y abre la app en el navegador"
        f = { & $py "main.py" "--navegador" @Resto }
    }
    "tests" = @{
        d = "pytest de toda la suite (pasa -k, -x, etc. tal cual)"
        f = { & $py "-m" "pytest" "tests/" @Resto }
    }
    "smoke" = @{
        d = "Smoke tests con ventanas reales: widget | instancia | desktop | descargas | captura"
        f = {
            # Ordenada: el mensaje de abajo lista las claves y una hashtable comun las devuelve
            # en cualquier orden.
            $mapa = [ordered]@{
                widget    = "tools\smoke_widget.py"
                instancia = "tools\smoke_instancia.py"
                desktop   = "tools\smoke_desktop.py"
                descargas = "tools\smoke_download_linux.py"
                captura   = "tools\snap_settings.py"
            }
            $cual = if ($Resto.Count) { $Resto[0] } else { "" }
            if (-not $mapa.Contains($cual)) {
                Write-Output "Cual: $($mapa.Keys -join ' | ')"
                Write-Output "'descargas' y 'captura' solo corren en Linux (GTK)."
                return
            }
            & $py $mapa[$cual] @($Resto | Select-Object -Skip 1)
        }
    }
    "manual" = @{
        d = "Regenera docs/Bitacora-Manual.pdf desde docs/manual.html (Edge headless)"
        f = { & powershell -NoProfile -ExecutionPolicy Bypass -File "tools\make_manual.ps1" @Resto }
    }
    "build" = @{
        d = "Build de Windows: dist\Bitacora-Windows-<fecha>.zip"
        f = { & powershell -NoProfile -ExecutionPolicy Bypass -File "tools\make_release.ps1" @Resto }
    }
    "build-linux" = @{
        d = "Build de Linux via WSL: dist\Bitacora-linux-<fecha>.tar.gz"
        f = { & wsl -d Ubuntu-24.04 -- bash tools/make_release_linux.sh @Resto }
    }
    "publicar" = @{
        d = "Build de las dos plataformas + release en GitHub. Acepta -Aviso '...' y -Tag v..."
        f = { & pwsh -NoProfile -ExecutionPolicy Bypass -File "tools\publish_release.ps1" @Resto }
    }
    "capturas" = @{
        d = "Screenshots de todas las pantallas para auditar un cambio de UI (necesita el navegador andando)"
        f = { & node "tools\screenshots_audit.mjs" @Resto }
    }
    "icono" = @{
        d = "Regenera bitacora/static/icon.ico y icon.png"
        f = { & $py "tools\make_icon.py" @Resto }
    }
    "comparar" = @{
        d = "Compara conteos de filas entre dos bases (chequeo post-migracion)"
        f = { & $py "tools\compare_dbs.py" @Resto }
    }
    "nuevo" = @{
        d = "Andamios: nuevo ajuste | campo | ruta (agregan las 3-4 piezas que pide la convencion)"
        f = {
            $mapa = [ordered]@{
                ajuste = "tools\andamios\ajuste.py"
                campo  = "tools\andamios\campo.py"
                ruta   = "tools\andamios\ruta.py"
            }
            $cual = if ($Resto.Count) { $Resto[0] } else { "" }
            if (-not $mapa.Contains($cual)) {
                Write-Output "Que cosa nueva: $($mapa.Keys -join ' | ')"
                Write-Output ""
                Write-Output "  ajuste   un ajuste de la pantalla de Ajustes (esquema + control + manual)"
                Write-Output "  campo    un tipo de campo de notas especiales (catalogo + builder)"
                Write-Output "  ruta     una pantalla nueva (blueprint + plantilla + tests + registro)"
                Write-Output ""
                Write-Output "  Cada uno con --help explica sus argumentos. Ejemplo:"
                Write-Output "    .\hacer.ps1 nuevo ajuste --help"
                return
            }
            & $py $mapa[$cual] @($Resto | Select-Object -Skip 1)
        }
    }
}

function Mostrar-Ayuda {
    Write-Output ""
    Write-Output "Bitacora - comandos del proyecto"
    Write-Output ""
    $ancho = ($COMANDOS.Keys | Measure-Object -Maximum -Property Length).Maximum
    foreach ($k in $COMANDOS.Keys) {
        Write-Output ("  {0}  {1}" -f $k.PadRight($ancho), $COMANDOS[$k].d)
    }
    Write-Output ""
    Write-Output "  Ejemplos:  .\hacer.ps1 tests -k ajustes"
    Write-Output "             .\hacer.ps1 smoke instancia"
    Write-Output "             .\hacer.ps1 publicar -Aviso 'Cambia el formato de fecha por defecto.'"
    Write-Output ""
}

if (-not $Comando) { Mostrar-Ayuda; exit 0 }

if (-not $COMANDOS.Contains($Comando)) {
    Write-Output "No existe el comando '$Comando'."
    Mostrar-Ayuda
    exit 1
}

# El venv hace falta para todo lo que corre Python; los builds de PowerShell lo chequean solos.
if (-not (Test-Path $py) -and $Comando -notin @("manual", "build-linux", "capturas")) {
    Write-Error "Falta el venv. Corre start.bat una vez y se crea solo."
    exit 1
}

& $COMANDOS[$Comando].f
exit $LASTEXITCODE
