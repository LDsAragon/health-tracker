# Publica el release del día en GitHub Releases: builds frescos de ambas
# plataformas + gh release create v<fecha> con el zip y el tar.gz.
# Necesita gh CLI autenticada (gh auth login).
# -Tag para un tag distinto al del día (ej: v2026-06-12.1 si hubo que re-publicar).
param([string]$Tag = "")
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

gh auth status *> $null
if ($LASTEXITCODE) {
    Write-Error "gh CLI sin autenticar: corré primero 'gh auth login'."
    exit 1
}

$fecha = Get-Date -Format yyyy-MM-dd
$tag = if ($Tag) { $Tag } else { "v$fecha" }
$zip = "dist\Bitacora-Windows-$fecha.zip"

# Fecha en español para el título y el cuerpo del release
$meses = @('enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre')
$hoy = Get-Date
$fechaEs = "$($hoy.Day) de $($meses[$hoy.Month - 1]) de $($hoy.Year)"

Write-Output "== Build Windows =="
powershell -NoProfile -ExecutionPolicy Bypass -File tools\make_release.ps1
if ($LASTEXITCODE -or -not (Test-Path $zip)) { Write-Error "falló el build Windows"; exit 1 }

Write-Output "== Build Linux (WSL) =="
wsl -d Ubuntu-24.04 -- bash tools/make_release_linux.sh
if ($LASTEXITCODE) { Write-Error "falló el build Linux"; exit 1 }

# WSL puede usar UTC y generar una fecha distinta a la de Windows; buscamos el tar.gz más reciente
$tgz = Get-ChildItem "dist\Bitacora-linux-*.tar.gz" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $tgz) { Write-Error "no se encontró el tar.gz de Linux en dist\"; exit 1 }

# Changelog: commits desde el tag anterior hasta HEAD
$prevTag = git describe --tags --abbrev=0 "$tag^" 2>$null
if (-not $prevTag) { $prevTag = git rev-list --max-parents=0 HEAD }
$commitLines = git log "$prevTag..HEAD" --pretty=format:"- %s" --no-merges 2>$null
$commits = if ($commitLines) { $commitLines -join "`n" } else { "- Mejoras y correcciones" }
$notesFile = [System.IO.Path]::GetTempFileName()
@"
## Cambios

$commits

---
**Windows:** descomprimí el zip, entrá a la carpeta `Bitacora` y ejecutá `Bitacora.exe`.
**Linux:** descomprimí el tar.gz, entrá a la carpeta `Bitacora` y ejecutá `./instalar.sh`.
"@ | Set-Content -Path $notesFile -Encoding UTF8

Write-Output "== Publicando $tag =="
gh release view $tag *> $null
if ($LASTEXITCODE) {
    gh release create $tag $zip $tgz --title "Bitácora — $fechaEs" --notes-file $notesFile --latest
} else {
    # ya existe el release de hoy: reemplazar archivos y actualizar notas
    gh release upload $tag $zip $tgz --clobber
    gh release edit $tag --title "Bitácora — $fechaEs" --notes-file $notesFile
}
Remove-Item $notesFile -ErrorAction SilentlyContinue
if ($LASTEXITCODE) { exit 1 }

Write-Output "OK: https://github.com/LDsAragon/health-tracker/releases/tag/$tag"
