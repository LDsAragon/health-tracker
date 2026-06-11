# Genera docs/Bitacora-Manual.pdf desde docs/manual.html (Edge headless, sin dependencias).
$root = Split-Path $PSScriptRoot -Parent
$src  = Join-Path $root "docs\manual.html"
$out  = Join-Path $root "docs\Bitacora-Manual.pdf"

$edge = @("${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe",
          "$env:ProgramFiles\Microsoft\Edge\Application\msedge.exe") |
        Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $edge) { Write-Error "No se encontró Edge."; exit 1 }

& $edge --headless --disable-gpu --no-pdf-header-footer `
        --print-to-pdf="$out" "file:///$($src -replace '\\','/')" 2>$null | Out-Null
Start-Sleep -Seconds 2
if (Test-Path $out) { Write-Output "OK: $out ($([math]::Round((Get-Item $out).Length/1KB)) KB)" }
else { Write-Error "No se generó el PDF."; exit 1 }
