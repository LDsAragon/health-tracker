"""Smoke de instancia única: dos Bitácoras de verdad, con ventana y todo.

Lo que los tests no pueden probar: que la segunda que arranca se cierre sola, que la primera
siga viva, y que el aviso por HTTP le llegue. Usa un LOCALAPPDATA temporal, así que no toca
tus datos.
Correr: venv/Scripts/python tools/smoke_instancia.py
"""
import json
import os
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
tmp = Path(tempfile.mkdtemp(prefix="ht-inst-"))
fallos = []


def _check(cond, msg):
    print(("OK   " if cond else "FALLA") + " " + msg, flush=True)
    if not cond:
        fallos.append(msg)


def _lanzar():
    entorno = dict(os.environ, LOCALAPPDATA=str(tmp), XDG_DATA_HOME=str(tmp))
    return subprocess.Popen([sys.executable, "desktop.py"], cwd=str(RAIZ), env=entorno,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _esperar_url(limite=40):
    """La URL aparece recién cuando la ventana está en pantalla."""
    archivo = tmp / "Bitacora" / "instancia.json"
    for _ in range(limite):
        if archivo.exists():
            try:
                return json.loads(archivo.read_text(encoding="utf-8"))
            except ValueError:
                pass
        time.sleep(0.5)
    return None


primera = _lanzar()
try:
    datos = _esperar_url()
    _check(datos is not None, "la primera instancia publica su URL al mostrarse")
    if datos:
        # El pid es solo para depurar (ningún camino lo usa) y acá no se puede comparar con
        # Popen.pid: el python.exe del venv es un stub que lanza el intérprete real aparte.
        _check(str(datos.get("url", "")).startswith("http://127.0.0.1:"),
               f"la URL publicada es local y con puerto: {datos.get('url')!r}")

        req = urllib.request.Request(f"{datos['url'].rstrip('/')}/instancia/mostrar",
                                     data=b"", method="POST")
        with urllib.request.urlopen(req, timeout=5) as r:
            _check(r.status == 204, "la ruta /instancia/mostrar contesta 204")

    # Lo que pasa cuando hacés doble clic con la app ya abierta.
    segunda = _lanzar()
    salida = None
    for _ in range(40):
        salida = segunda.poll()
        if salida is not None:
            break
        time.sleep(0.5)
    _check(salida == 0, f"la segunda se cierra sola y sin error (exit={salida})")
    if salida is None:
        segunda.kill()

    _check(primera.poll() is None, "la primera sigue viva")

    # Y una tercera, para que no sea casualidad de la segunda.
    tercera = _lanzar()
    try:
        tercera.wait(timeout=20)
        _check(tercera.returncode == 0, "una tercera también se cierra sola")
    except subprocess.TimeoutExpired:
        tercera.kill()
        _check(False, "una tercera también se cierra sola (se colgó)")

    _check(primera.poll() is None, "y la primera sigue viva después de las dos")
finally:
    primera.kill()
    primera.wait(timeout=15)
    print("\n" + ("SMOKE OK" if not fallos else f"SMOKE CON {len(fallos)} FALLAS"), flush=True)
    sys.exit(1 if fallos else 0)
