# Arma el zip COMPATIBLE de Windows: la Bitacora sin un solo binario propio.
# -> dist\Bitacora-Compatible-<version>.zip
#
# Es para las maquinas con Smart App Control, que bloquea todo .exe o DLL sin firma y no
# acepta excepciones por app. En vez de PyInstaller lleva el Python embebido oficial (firmado
# por la PSF) y la ventana es Edge en modo app (bitacora/escritorio/compatible.py). Lo que se
# pierde es lo que es pywebview: el widget y la bandeja.
#
# OJO: El ultimo paso VERIFICA que todo .exe/.dll/.pyd del zip tenga una firma valida y aborta
# si no. Es la unica garantia del zip: un solo binario sin firma (un .pyd nuevo que traiga una
# dependencia, el flask.exe que deja pip) y Smart App Control lo bloquea en la cara del usuario.
#
# Corre con Windows PowerShell 5.1 (lo llama make_release.ps1): nada de sintaxis de pwsh 7.
param([Parameter(Mandatory = $true)][string]$Version)
$ErrorActionPreference = "Stop"
$root = Split-Path $PSScriptRoot -Parent
Set-Location $root

$py = "$root\venv\Scripts\python.exe"
$pyVer = (& $py -c "import platform; print(platform.python_version())").Trim()
$mm = ($pyVer -split '\.')[0..1] -join ''          # 3.14.7 -> 314
$mmPunto = ($pyVer -split '\.')[0..1] -join '.'    # 3.14.7 -> 3.14

# El Python embebido se baja una vez y queda en cache: es el mismo para cada build.
$cache = "$root\dist\cache"
New-Item -ItemType Directory -Force $cache | Out-Null
$embed = "$cache\python-$pyVer-embed-amd64.zip"
if (-not (Test-Path $embed)) {
    Write-Output "Bajando Python $pyVer embebido..."
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest "https://www.python.org/ftp/python/$pyVer/python-$pyVer-embed-amd64.zip" `
        -OutFile "$embed.tmp" -UseBasicParsing
    Move-Item "$embed.tmp" $embed -Force
}

# La carpeta se llama Bitacora porque el updater espera extracted/Bitacora, como en el zip normal.
$out = "$root\dist\compatible\Bitacora"
if (Test-Path "$root\dist\compatible") { Remove-Item "$root\dist\compatible" -Recurse -Force }
New-Item -ItemType Directory -Force $out | Out-Null

Expand-Archive $embed -DestinationPath "$out\python"
# El ._pth reemplaza a sys.path entero. ".." es la carpeta de la app: de ahi salen main.py, el
# paquete bitacora y _version.py.
@("python$mm.zip", ".", "Lib\site-packages", "..") |
    Set-Content "$out\python\python$mm._pth" -Encoding ASCII

Write-Output "Instalando Flask para Python $mmPunto..."
& $py -m pip install -r "$root\requirements.txt" --target "$out\python\Lib\site-packages" `
    --only-binary=:all: --platform win_amd64 --python-version $mmPunto --implementation cp `
    --no-compile --quiet --disable-pip-version-check
if ($LASTEXITCODE) { Write-Error "pip fallo"; exit 1 }
# Los lanzadores de consola que deja pip (flask.exe) son .exe sin firma y nadie los usa.
Remove-Item "$out\python\Lib\site-packages\bin" -Recurse -Force -ErrorAction SilentlyContinue
# El acelerador en C de markupsafe no esta firmado. Sin el, markupsafe usa su version en
# Python puro (lo hace solo ante un ImportError): mas lenta, pero no se nota en una app local.
Get-ChildItem "$out\python\Lib\site-packages\markupsafe" -Filter "_speedups*.pyd" |
    Remove-Item -Force

Copy-Item "$root\main.py" $out
robocopy "$root\bitacora" "$out\bitacora" /E /XD __pycache__ /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) { Write-Error "robocopy fallo copiando el paquete"; exit 1 }
# CANAL le dice al updater que baje ESTE zip y como relanzarse (sin Bitacora.exe).
@("VERSION = `"$Version`"", "CANAL = `"compatible`"") |
    Set-Content "$out\_version.py" -Encoding ASCII

# El lanzador. Un .bat y no un .exe: un .exe propio seria justo lo que Smart App Control
# bloquea. pythonw.exe no abre consola; start hace que el .bat termine en el acto.
$lanzador = @(
    '@echo off',
    'rem Abre la Bitacora (version compatible) con el Python que viene en la carpeta "python".',
    'start "" "%~dp0python\pythonw.exe" "%~dp0main.py" --compatible'
)
[IO.File]::WriteAllText("$out\Bitacora.bat", ($lanzador -join "`r`n") + "`r`n",
    (New-Object Text.ASCIIEncoding))

Copy-Item "$root\docs\LEEME-Compatible.txt" "$out\LEEME.txt"
if (Test-Path "$root\docs\Bitacora-Manual.pdf") { Copy-Item "$root\docs\Bitacora-Manual.pdf" $out }

Write-Output "Verificando que no quede ningun binario sin firma..."
$sinFirma = @(Get-ChildItem $out -Recurse -File -Include *.exe, *.dll, *.pyd |
    Where-Object { (Get-AuthenticodeSignature $_.FullName).Status -ne "Valid" })
if ($sinFirma.Count) {
    $sinFirma | ForEach-Object { Write-Output "  SIN FIRMA: $($_.FullName.Substring($out.Length + 1))" }
    Write-Error "Hay $($sinFirma.Count) binarios sin firma: Smart App Control los bloquearia."
    exit 1
}

# OJO: Sin "Windows" en el nombre: ver updater.PREFIJO_COMPATIBLE.
$zip = "$root\dist\Bitacora-Compatible-$Version.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $out -DestinationPath $zip
Write-Output "OK: $zip ($([math]::Round((Get-Item $zip).Length/1MB, 1)) MB)"
# Sin esto el codigo de salida seria el del ultimo robocopy, que devuelve 1 cuando COPIO bien.
exit 0
