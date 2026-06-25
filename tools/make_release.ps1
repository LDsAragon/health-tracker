# Genera el zip listo para compartir: build fresco + LEEME.txt + manual PDF
# → dist\Bitacora-Windows-<fecha>.zip
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

if (Get-Process Bitacora -ErrorAction SilentlyContinue) {
    Write-Error "Cerrá Bitácora antes de generar el release."
    exit 1
}

$fecha = Get-Date -Format yyyy-MM-dd
# _version.py se genera ANTES del build para que PyInstaller lo bundlee en _internal/.
# No se commitea (está en .gitignore): es un artefacto del build.
'VERSION = "v{0}"' -f $fecha | Set-Content -Path "$root\_version.py" -Encoding UTF8

Write-Output "Compilando Bitacora.exe..."
& "$root\venv\Scripts\pyinstaller.exe" --noconfirm --windowed --name Bitacora `
    --icon static\icon.ico `
    --add-data "templates;templates" --add-data "static;static" `
    desktop.py 2>&1 | Out-Null
Remove-Item "$root\_version.py" -ErrorAction SilentlyContinue
if (-not (Test-Path "$root\dist\Bitacora\Bitacora.exe")) {
    Write-Error "El build falló (no apareció dist\Bitacora\Bitacora.exe)."
    exit 1
}
$zip = "$root\dist\Bitacora-Windows-$fecha.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }

$contenido = @("$root\dist\Bitacora", "$root\docs\LEEME.txt")
if (Test-Path "$root\docs\Bitacora-Manual.pdf") { $contenido += "$root\docs\Bitacora-Manual.pdf" }
Compress-Archive -Path $contenido -DestinationPath $zip

Write-Output "OK: $zip ($([math]::Round((Get-Item $zip).Length/1MB, 1)) MB)"
Write-Output "Contiene: carpeta Bitacora (la app), LEEME.txt y el manual PDF."
