# Publica el release del día en GitHub Releases: builds frescos de ambas
# plataformas + gh release create v<fecha> con el zip y el tar.gz.
# Necesita gh CLI autenticada (gh auth login).
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

gh auth status *> $null
if ($LASTEXITCODE) {
    Write-Error "gh CLI sin autenticar: corré primero 'gh auth login'."
    exit 1
}

$fecha = Get-Date -Format yyyy-MM-dd
$tag = "v$fecha"
$zip = "dist\Bitacora-$fecha.zip"
$tgz = "dist\Bitacora-linux-$fecha.tar.gz"

Write-Output "== Build Windows =="
powershell -NoProfile -ExecutionPolicy Bypass -File tools\make_release.ps1
if ($LASTEXITCODE -or -not (Test-Path $zip)) { Write-Error "falló el build Windows"; exit 1 }

Write-Output "== Build Linux (WSL) =="
wsl -d Ubuntu-24.04 -- bash tools/make_release_linux.sh
if ($LASTEXITCODE -or -not (Test-Path $tgz)) { Write-Error "falló el build Linux"; exit 1 }

Write-Output "== Publicando $tag =="
gh release view $tag *> $null
if ($LASTEXITCODE) {
    gh release create $tag $zip $tgz --title "Bitácora $fecha" --generate-notes --latest
} else {
    # ya existe el release de hoy: reemplazar los archivos
    gh release upload $tag $zip $tgz --clobber
}
if ($LASTEXITCODE) { exit 1 }

Write-Output "OK: https://github.com/LDsAragon/health-tracker/releases/tag/$tag"
