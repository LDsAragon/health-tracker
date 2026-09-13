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
#
# Con -Version manda el que pasa publish_release.ps1, que elige el tag ANTES de compilar para
# que el .exe publicado se identifique con su propio release.
#
# Sin -Version esto es un build local, y estampaba "v<fecha>" a secas: el mismo tag que la
# PRIMERA release del dia. O sea que el .exe se hacia pasar por una version publicada que no es
# la que tiene adentro, y el updater le ofrecia "actualizar" a algo con menos codigo del que
# acabas de compilar. Se usa el sufijo que le tocaria al publicarse: queda por encima de todo lo
# publicado (el updater no ofrece nada) y coincide con el tag que va a llevar cuando se publique.
if ($Version) {
    $ver = $Version
} else {
    # Mejor esfuerzo: sin red o sin remoto seguimos con los tags que haya localmente. El tag lo
    # crea `gh release create`, asi que sin este fetch los locales quedan un paso atras.
    git fetch --tags --quiet 2>$null | Out-Null
    $usados = @(git tag -l "v$fecha*")
    $ver = "v$fecha"
    $n = 0
    while ($usados -contains $ver) {
        $n++
        if ($n -gt 99) { Write-Error "mas de 99 tags hoy: pasa -Version a mano"; exit 1 }
        $ver = "v$fecha.$n"
    }
    Write-Output "Build local: se estampa $ver (el sufijo que le tocaria al publicar)"
}
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
