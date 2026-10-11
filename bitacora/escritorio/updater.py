"""Auto-actualización via GitHub Releases.

Flujo:
  check_in_background() — lanza hilo daemon que consulta la API de GitHub.
  get_status()          — devuelve el resultado (usado por /update/status).
  start_download()      — descarga el asset de la plataforma actual.
  apply_update()        — backup DB → extrae zip/tar → lanza script externo.
"""
import os
import sys
import json
import shutil
import stat
import threading
import tempfile
import urllib.request
from datetime import datetime
from pathlib import Path

GITHUB_REPO = "LDsAragon/health-tracker"
_API_URL    = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

_lock  = threading.Lock()
_state = {
    "checked":     False,
    "available":   False,
    "current":     None,
    "latest":      None,
    "notes":       [],
    "asset_url":   None,
    "asset_name":  None,
    "downloading": False,
    "dl_total":    0,
    "dl_done":     0,
    "dl_error":    None,
    "dl_ready":    False,
    "dl_path":     None,
}


def base_dir():
    """La carpeta de la INSTALACIÓN: la que tiene el programa adentro.

    Dos usos, y por eso vive en un solo lugar: acá es el destino de la actualización, y en
    `escritorio/main.py` es dónde buscar una `health.db` vieja al lado del programa para
    migrarla. Ya estuvo duplicada y **divergió** —esta copia devolvía otra carpeta—, que es
    justamente lo que no puede pasar con algo que se usa para copiar archivos encima.

    ⚠️ Congelada es la carpeta del `.exe`. Sin congelar hay que subir **tres** niveles: este
    archivo vive en `bitacora/escritorio/`, así que `Path(__file__).parent` es `escritorio/` y
    no la raíz. En Linux la app corre **desde el código** (no se empaqueta con PyInstaller
    porque WebKitGTK es frágil de bundlear), así que ese es el camino real allá: con el valor
    mal, `apply_update` volcaba la carpeta nueva **dentro de `bitacora/escritorio/`** y después
    buscaba ahí `venv/bin/pip`, `instalar.sh` y `bitacora.sh`, que están en la raíz. No borraba
    nada —el rsync no lleva `--delete`— pero la actualización no se aplicaba, la app no se
    relanzaba y quedaba una copia anidada.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).resolve().parent.parent.parent


def current_version():
    """Versión desde _version.py, generado por el build e incluido en el bundle.
    Devuelve None en modo dev (el archivo no existe en el repo)."""
    try:
        import _version
        return _version.VERSION
    except (ImportError, AttributeError):
        return None


def canal():
    """'compatible' en el build sin binarios propios (`make_release_compatible.ps1` lo escribe
    en `_version.py`); 'normal' en todo lo demás. Decide qué asset bajar y cómo relanzarse."""
    try:
        import _version
        return getattr(_version, "CANAL", "normal")
    except ImportError:
        return "normal"


# Lo que hay que cerrar antes del os._exit de /update/quit (la ventana de Edge del modo
# compatible, que si no queda abierta sobre un servidor muerto).
al_salir = []

# ⚠️ El zip compatible NO puede llevar "windows" en el nombre: las instalaciones ya
# repartidas eligen su asset con `"windows" in nombre and nombre.endswith(".zip")`, y con
# ese nombre podrían bajar el compatible y espejarlo sobre una carpeta con Bitacora.exe.
PREFIJO_COMPATIBLE = "Bitacora-Compatible-"


def elegir_asset(assets, plataforma=None, canal_actual=None):
    plataforma = plataforma or sys.platform
    canal_actual = canal_actual or canal()
    if plataforma == "win32" and canal_actual == "compatible":
        ok = lambda n: n.startswith(PREFIJO_COMPATIBLE) and n.endswith(".zip")
    elif plataforma == "win32":
        ok = lambda n: ("windows" in n.lower() and n.endswith(".zip")
                        and not n.startswith(PREFIJO_COMPATIBLE))
    else:
        ok = lambda n: "linux" in n.lower() and n.endswith(".tar.gz")
    return next((a for a in assets if ok(a["name"])), None)


def _version_tuple(tag):
    """v2026-06-12.1 → (2026, 6, 12, 1); v2026-06-24 → (2026, 6, 24, 0)"""
    import re
    m = re.match(r"v?(\d+)-(\d+)-(\d+)(?:\.(\d+))?", tag or "")
    if not m:
        return (0,)
    return (int(m.group(1)), int(m.group(2)), int(m.group(3)), int(m.group(4) or 0))


def changelog(body):
    """Lista de cambios del cuerpo del release (el formato que arma publish_release.ps1).

    El cuerpo es '## Cambios' + bullets '- <asunto>' + '---' + instrucciones de
    instalación; esas instrucciones no sirven acá adentro (la app se instala sola),
    así que cortamos en el separador. Si no hay bullets (release escrito a mano),
    devolvemos el texto como está.
    """
    text = (body or "").split("\n---")[0]
    bullets = [l.strip()[1:].strip() for l in text.splitlines() if l.strip().startswith("- ")]
    if bullets:
        return bullets
    return [l.strip() for l in text.splitlines()
            if l.strip() and not l.strip().startswith("#")]


def check_in_background():
    """Consulta GitHub en un hilo daemon. No bloquea el arranque."""
    ver = current_version()
    if not ver:
        return
    threading.Thread(target=_do_check, args=(ver,), daemon=True).start()


def force_check():
    """Re-consulta GitHub ahora, en background (el botón de Ajustes).

    A diferencia de check_in_background() no exige tener versión propia: en dev
    sirve para ver cuál es el último release publicado. Devuelve False si hay una
    descarga en curso — resetear dl_* debajo de ese hilo lo dejaría escribiendo
    sobre un asset que ya no corresponde.
    """
    with _lock:
        if _state["downloading"]:
            return False
        _state.update(checked=False, available=False, notes=[],
                      dl_total=0, dl_done=0, dl_error=None,
                      dl_ready=False, dl_path=None)
    threading.Thread(target=_do_check, args=(current_version(),), daemon=True).start()
    return True


def _do_check(current):
    try:
        req = urllib.request.Request(
            _API_URL,
            headers={"User-Agent": "Bitacora-updater/1.0",
                     "Accept":     "application/vnd.github+json"},
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())

        latest = data.get("tag_name", "")
        asset = elegir_asset(data.get("assets", []))
        with _lock:
            _state["checked"]   = True
            _state["current"]   = current
            _state["latest"]    = latest
            _state["notes"]     = changelog(data.get("body"))
            # `current` es None en dev: sin versión propia no hay con qué comparar, y
            # ofrecer instalar sobreescribiría el repo (apply_update copia sobre base_dir).
            _state["available"] = bool(current and latest
                                       and _version_tuple(latest) > _version_tuple(current) and asset)
            _state["asset_url"]  = asset["browser_download_url"] if asset else None
            _state["asset_name"] = asset["name"] if asset else None
    except Exception:
        with _lock:
            _state["checked"] = True  # falló en silencio — sin internet es normal


def get_status():
    with _lock:
        return dict(_state)


def start_download():
    """Inicia la descarga en background. Idempotente si ya está en curso o lista."""
    with _lock:
        if _state["downloading"] or _state["dl_ready"]:
            return True
        url  = _state["asset_url"]
        name = _state["asset_name"]
        if not url:
            return False
        _state["downloading"] = True
        _state["dl_total"]    = 0
        _state["dl_done"]     = 0
        _state["dl_error"]    = None

    threading.Thread(target=_do_download, args=(url, name), daemon=True).start()
    return True


def _do_download(url, filename):
    tmp_dir = Path(tempfile.gettempdir()) / "bitacora-update"
    tmp_dir.mkdir(parents=True, exist_ok=True)
    dest = tmp_dir / filename
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Bitacora-updater/1.0"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            with _lock:
                _state["dl_total"] = total
            done = 0
            with open(dest, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    done += len(chunk)
                    with _lock:
                        _state["dl_done"] = done
        with _lock:
            _state["dl_ready"]    = True
            _state["dl_path"]     = str(dest)
            _state["downloading"] = False
    except Exception as exc:
        with _lock:
            _state["dl_error"]    = str(exc)
            _state["downloading"] = False


def apply_update():
    """Backup DB → extrae zip/tar.gz → lanza updater externo. Devuelve (ok, error)."""
    with _lock:
        ready = _state["dl_ready"]
        path  = _state["dl_path"]
        error = _state["dl_error"]
    if not ready or not path:
        return False, error or "Descarga incompleta"

    try:
        _pre_update_backup()
    except Exception as exc:
        return False, f"Backup previo falló: {exc}"

    extract_dir = Path(tempfile.gettempdir()) / "bitacora-update" / "extracted"
    if extract_dir.exists():
        shutil.rmtree(extract_dir)
    extract_dir.mkdir(parents=True)

    try:
        if path.endswith(".zip"):
            import zipfile
            with zipfile.ZipFile(path) as z:
                z.extractall(extract_dir)
        else:
            import tarfile
            with tarfile.open(path) as t:
                t.extractall(extract_dir)
    except Exception as exc:
        return False, f"Extracción falló: {exc}"

    src = extract_dir / "Bitacora"
    if not src.exists():
        return False, "El archivo no tiene la estructura esperada (falta carpeta Bitacora/)"

    dst = base_dir()
    pid = os.getpid()

    try:
        if sys.platform == "win32":
            _launch_win(src, dst, pid)
        else:
            _launch_linux(src, dst, pid)
    except Exception as exc:
        return False, f"No se pudo lanzar el actualizador: {exc}"

    return True, None


def _pre_update_backup():
    from bitacora.database.conn import DB_PATH, backup_path, snapshot_to
    if not Path(DB_PATH).exists():
        return
    snapshot_to(backup_path("health-preupdate"))


def _ps(p):
    """Ruta como string PS literal (single-quoted): escapa comillas simples."""
    return str(p).replace("'", "''")


def _launch_win(src, dst, pid):
    import subprocess
    log = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "Bitacora" / "update.log"
    if canal() == "compatible":
        # Sin .exe propio: el lanzador es el Python embebido, firmado, con el main.py.
        relanzar = (f"Start-Process '{_ps(dst / 'python' / 'pythonw.exe')}' "
                    f"-ArgumentList '\"{_ps(dst / 'main.py')}\" --compatible' "
                    f"-WorkingDirectory '{_ps(dst)}'")
    else:
        relanzar = f"Start-Process '{_ps(dst / 'Bitacora.exe')}'"

    # Dejar rastro ANTES de lanzar: si el script externo no llega a loguear, el
    # problema fue el lanzamiento y no el script (así se diagnosticó este bug).
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(f"{datetime.now().isoformat(timespec='seconds')}: lanzando actualizador externo\n")

    script = f"""
$log = '{_ps(log)}'
function Log($m) {{ "$(Get-Date -f s): $m" | Add-Content $log }}
Log "Actualizador iniciado (PID padre: {pid})"

$deadline = (Get-Date).AddSeconds(30)
while ((Get-Process -Id {pid} -EA SilentlyContinue) -and (Get-Date) -lt $deadline) {{
    Start-Sleep -Milliseconds 300
}}
Log "Proceso principal terminado. Aplicando archivos..."

robocopy '{_ps(src)}' '{_ps(dst)}' /MIR /NFL /NDL /NJH /NJS | Out-Null
if ($LASTEXITCODE -ge 8) {{
    Log "ERROR: robocopy fallo con codigo $LASTEXITCODE"
    Add-Type -AssemblyName System.Windows.Forms
    [System.Windows.Forms.MessageBox]::Show(
        "La actualizacion fallo (robocopy $LASTEXITCODE).`nRevisa: $log", "Bitacora") | Out-Null
    exit 1
}}
Log "Archivos reemplazados. Desbloqueando Zone.Identifier..."
Get-ChildItem '{_ps(dst)}' -Recurse -File | ForEach-Object {{
    Remove-Item "$($_.FullName):Zone.Identifier" -EA SilentlyContinue
}}
Log "Relanzando aplicacion..."
{relanzar}
Log "OK"
"""
    ps_path = Path(tempfile.gettempdir()) / "bitacora_updater.ps1"
    ps_path.write_text(script, encoding="utf-8")
    # CREATE_NO_WINDOW, NO DETACHED_PROCESS: powershell.exe es una app de consola y
    # con DETACHED_PROCESS arranca sin consola, no ejecuta el script y sale con 0 en
    # silencio — la actualización en Windows nunca se aplicaba. CREATE_NO_WINDOW le da
    # una consola oculta, y el hijo igual sobrevive al os._exit() de /update/quit.
    subprocess.Popen(
        ["powershell", "-NoProfile", "-WindowStyle", "Hidden",
         "-ExecutionPolicy", "Bypass", "-File", str(ps_path)],
        creationflags=subprocess.CREATE_NO_WINDOW | subprocess.CREATE_NEW_PROCESS_GROUP,
    )


def _launch_linux(src, dst, pid):
    import subprocess
    xdg = os.environ.get("XDG_DATA_HOME", str(Path.home() / ".local" / "share"))
    log = Path(xdg) / "Bitacora" / "update.log"

    script = f"""#!/bin/bash
LOG='{log}'
log() {{ echo "$(date -Iseconds): $1" >> "$LOG"; }}
log "Actualizador iniciado (PID padre: {pid})"

for i in $(seq 100); do kill -0 {pid} 2>/dev/null || break; sleep 0.3; done
log "Proceso principal terminado. Copiando archivos..."

if command -v rsync >/dev/null 2>&1; then
    rsync -a --exclude='venv/' --exclude='health.db' '{src}/' '{dst}/' >> "$LOG" 2>&1
else
    for item in '{src}'/*; do
        name=$(basename "$item")
        [ "$name" = venv ] && continue
        [ "$name" = health.db ] && continue
        cp -r "$item" '{dst}/'
    done
fi
COPY_EXIT=$?
if [ $COPY_EXIT -ne 0 ]; then
    log "ERROR: copia de archivos fallo (codigo $COPY_EXIT)"
    command -v notify-send >/dev/null 2>&1 && \\
        DISPLAY="$DISPLAY" notify-send "Bitácora" "Actualización falló. Revisá: $LOG"
    exit 1
fi
log "Archivos copiados."

cd '{dst}'
if [ -x venv/bin/pip ]; then
    log "Actualizando dependencias Python..."
    venv/bin/pip install -q -r requirements-desktop.txt >> "$LOG" 2>&1
fi

log "Actualizando paquetes del sistema (requiere permisos)..."
if command -v pkexec >/dev/null 2>&1; then
    pkexec env DISPLAY="$DISPLAY" XAUTHORITY="$XAUTHORITY" bash '{dst}/instalar.sh' >> "$LOG" 2>&1
elif sudo -n bash '{dst}/instalar.sh' >> "$LOG" 2>&1; then
    true
else
    log "Sin privilegios para paquetes del sistema — correr instalar.sh si hay problemas"
    command -v notify-send >/dev/null 2>&1 && \\
        DISPLAY="$DISPLAY" notify-send "Bitácora actualizada" \\
        "Si hay problemas iniciando la app, ejecutá ./instalar.sh manualmente"
fi

log "Relanzando..."
exec bash '{dst}/bitacora.sh'
"""
    sh_path = Path(tempfile.gettempdir()) / "bitacora_updater.sh"
    sh_path.write_text(script, encoding="utf-8")
    sh_path.chmod(sh_path.stat().st_mode | stat.S_IXUSR)
    subprocess.Popen(
        ["bash", str(sh_path)],
        start_new_session=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
