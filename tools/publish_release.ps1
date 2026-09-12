# Publica el release del día en GitHub Releases: builds frescos de ambas
# plataformas + gh release create v<fecha> con el zip y el tar.gz.
# Necesita gh CLI autenticada (gh auth login).
# -Tag para un tag distinto al del día (ej: v2026-06-12.1 si hubo que re-publicar).
# -Aviso: advertencia para los usuarios (cambio de comportamiento, migracion a mano).
# Va como primer bullet y no como parrafo aparte a proposito: updater.changelog() se
# queda solo con los bullets, asi que un parrafo no llegaria al tab Version de la app.
param([string]$Tag = "", [string]$Aviso = "")
# PS 5.1 defaults $OutputEncoding to ASCII; los caracteres no-ASCII (tildes, em dash)
# se corrompen al pasarlos a procesos externos como gh CLI. Forzar UTF-8.
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
$OutputEncoding = [System.Text.Encoding]::UTF8

$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

gh auth status *> $null
if ($LASTEXITCODE) {
    Write-Error "gh CLI sin autenticar: corré primero 'gh auth login'."
    exit 1
}

$pending = git status --porcelain 2>$null
if ($pending) {
    Write-Error "Hay cambios sin commitear. Commiteá o descartá antes de publicar."
    exit 1
}
Write-Output "== Push a main =="
git push
if ($LASTEXITCODE) { Write-Error "git push falló"; exit 1 }
# gh release create crea el tag SOLO en el remoto: sin este fetch los tags de los
# releases anteriores no existen localmente, git describe devuelve uno viejisimo y
# el changelog repite todo lo ya publicado.
git fetch --tags --quiet

$fecha = Get-Date -Format yyyy-MM-dd

function Test-ReleaseExiste($t) {
    gh release view $t *> $null
    return ($LASTEXITCODE -eq 0)
}

# Sin -Tag NUNCA se pisa un release existente: se busca el primer sufijo libre.
# El default era "v<fecha>" a secas, asi que en un dia con un release ya publicado caia en
# la rama de "ya existe" de abajo y le reemplazaba los archivos y las notas sin avisar. Y
# encima el tag repetido compara MENOR que el del dia con sufijo (updater._version_tuple:
# (2026,9,12) < (2026,9,12,2)), asi que el release nuevo no se le ofrecia a nadie.
if ($Tag) {
    $tag = $Tag
} else {
    $tag = "v$fecha"
    $n = 0
    while (Test-ReleaseExiste $tag) {
        $n++
        if ($n -gt 50) { Write-Error "mas de 50 releases hoy: pasa -Tag a mano"; exit 1 }
        $tag = "v$fecha.$n"
    }
    if ($n) { Write-Output "Ya habia releases de hoy: publico como $tag" }
}
$zip = "dist\Bitacora-Windows-$fecha.zip"

# Fecha en español para el título y el cuerpo del release
$meses = @('enero','febrero','marzo','abril','mayo','junio','julio','agosto','septiembre','octubre','noviembre','diciembre')
$hoy = Get-Date
$fechaEs = "$($hoy.Day) de $($meses[$hoy.Month - 1]) de $($hoy.Year)"
$titulo = "Bitácora $([char]0x2014) $fechaEs"

Write-Output "== Build Windows =="
powershell -NoProfile -ExecutionPolicy Bypass -File tools\make_release.ps1 -Version $tag
if ($LASTEXITCODE -or -not (Test-Path $zip)) { Write-Error "falló el build Windows"; exit 1 }

Write-Output "== Build Linux (WSL) =="
wsl -d Ubuntu-24.04 -- bash tools/make_release_linux.sh $tag
if ($LASTEXITCODE) { Write-Error "falló el build Linux"; exit 1 }

# WSL puede usar UTC y generar una fecha distinta a la de Windows; buscamos el tar.gz más reciente
$tgz = Get-ChildItem "dist\Bitacora-linux-*.tar.gz" | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty FullName
if (-not $tgz) { Write-Error "no se encontró el tar.gz de Linux en dist\"; exit 1 }

# Changelog: commits desde el tag anterior hasta HEAD.
# Ojo: gh release create crea el tag SOLO en el remoto, asi que aca el tag nuevo
# todavia no existe localmente y describe sobre "$tag^" falla — caiamos al commit
# raiz y el changelog salia con la historia entera del proyecto.
$prevTag = git describe --tags --abbrev=0 HEAD 2>$null
if ($prevTag -eq $tag) {
    # Re-publicacion de un tag que ya existe: saltar al anterior.
    $prevTag = git describe --tags --abbrev=0 "$tag^" 2>$null
}
if (-not $prevTag) { $prevTag = git rev-list --max-parents=0 HEAD }
$commitLines = git log "$prevTag..HEAD" --pretty=format:"- %s" --no-merges 2>$null
$commits = if ($commitLines) { $commitLines -join "`n" } else { "- Mejoras y correcciones" }
if ($Aviso) { $commits = "- $([char]0x26A0)$([char]0xFE0F) $Aviso`n$commits" }
$notesFile = [System.IO.Path]::GetTempFileName()
# Set-Content -Encoding UTF8 en PS 5.1 escribe con BOM; usar WriteAllText con UTF8 sin BOM.
$notesBody = @"
## Cambios

$commits

---
**Windows:** descomprimí el zip, entrá a la carpeta ``Bitacora`` y ejecutá ``Bitacora.exe``.
**Linux:** descomprimí el tar.gz, entrá a la carpeta ``Bitacora`` y ejecutá ``./instalar.sh``.
"@
[System.IO.File]::WriteAllText($notesFile, $notesBody, (New-Object System.Text.UTF8Encoding $false))

Write-Output "== Publicando $tag =="
gh release view $tag *> $null
if ($LASTEXITCODE) {
    gh release create $tag $zip $tgz --title $titulo --notes-file $notesFile --latest
} else {
    # Solo se llega aca con -Tag explicito (el default ya eligio un tag libre):
    # re-publicar a proposito un tag que existe, reemplazando archivos y notas.
    gh release upload $tag $zip $tgz --clobber
    gh release edit $tag --title $titulo --notes-file $notesFile
}
Remove-Item $notesFile -ErrorAction SilentlyContinue
if ($LASTEXITCODE) { exit 1 }

Write-Output "OK: https://github.com/LDsAragon/health-tracker/releases/tag/$tag"
