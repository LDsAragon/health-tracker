# Genera el zip listo para compartir: build fresco + LEEME.txt + manual PDF
# → dist\Bitacora-Windows-<fecha>.zip
# -Version: tag a estampar en _version.py (default v<fecha>). Tiene que coincidir
# con el tag del release o el updater ofrece actualizar en loop.
param([string]$Version = "")
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

# Solo importa el .exe que este build va a sobreescribir: uno corriendo desde otra carpeta
# (una copia vieja en el Escritorio, la version instalada) no tiene ningun lock sobre dist\ y
# abortar por eso obligaba a cerrar la app del dia a dia para poder publicar.
$propio = Join-Path $root "dist\Bitacora\Bitacora.exe"
$corriendo = @(Get-CimInstance Win32_Process -Filter "Name='Bitacora.exe'" |
               Where-Object { $_.ExecutablePath -eq $propio })
if ($corriendo.Count) {
    Write-Error "Cerrá la Bitácora de dist\Bitacora (PID $($corriendo[0].ProcessId)) antes de generar el release."
    exit 1
}

$fecha = Get-Date -Format yyyy-MM-dd
# _version.py se genera ANTES del build para que PyInstaller lo bundlee en _internal/.
# No se commitea (está en .gitignore): es un artefacto del build.
$ver = if ($Version) { $Version } else { "v$fecha" }
'VERSION = "{0}"' -f $ver | Set-Content -Path "$root\_version.py" -Encoding UTF8

Write-Output "Compilando Bitacora.exe..."
# Las plantillas y static viven en bitacora/ pero se bundlean en la RAIZ del bundle:
# app.py las busca en sys._MEIPASS/templates, no en _MEIPASS/bitacora/templates.
& "$root\venv\Scripts\pyinstaller.exe" --noconfirm --windowed --name Bitacora `
    --icon bitacora\static\icon.ico `
    --add-data "bitacora/templates;templates" --add-data "bitacora/static;static" `
    main.py 2>&1 | Out-Null
Remove-Item "$root\_version.py" -ErrorAction SilentlyContinue
if (-not (Test-Path "$root\dist\Bitacora\Bitacora.exe")) {
    Write-Error "El build falló (no apareció dist\Bitacora\Bitacora.exe)."
    exit 1
}
$zip = "$root\dist\Bitacora-Windows-$fecha.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }

# El LEEME y el manual van DENTRO de la carpeta Bitacora, no sueltos al lado.
# No es cosmetico: la auto-actualizacion espeja la carpeta Bitacora del zip sobre la carpeta
# del .exe (updater.apply_update -> robocopy /MIR), asi que todo lo que quede afuera NUNCA se
# actualiza. Antes el manual y el LEEME se quedaban con la version del dia que descomprimiste,
# para siempre. Es lo que ya venia haciendo bien el tarball de Linux.
Copy-Item "$root\docs\LEEME.txt" "$root\dist\Bitacora\LEEME.txt" -Force
if (Test-Path "$root\docs\Bitacora-Manual.pdf") {
    Copy-Item "$root\docs\Bitacora-Manual.pdf" "$root\dist\Bitacora\Bitacora-Manual.pdf" -Force
}
Compress-Archive -Path "$root\dist\Bitacora" -DestinationPath $zip

Write-Output "OK: $zip ($([math]::Round((Get-Item $zip).Length/1MB, 1)) MB)"
Write-Output "Contiene: la carpeta Bitacora con la app, LEEME.txt y el manual PDF adentro."
