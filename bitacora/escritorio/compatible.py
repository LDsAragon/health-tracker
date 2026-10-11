"""Modo compatible: la Bitácora sin un solo binario propio, para Windows con Smart App Control.

Smart App Control bloquea todo .exe o DLL que nadie haya firmado y no acepta excepciones por
app. El build normal no tiene cómo pasarlo: PyInstaller genera un `Bitacora.exe` sin firma, y
pywebview carga `Python.Runtime.dll`, tampoco firmada. Este modo corre sobre el **Python
embebido oficial** (firmado por la PSF) y la ventana es **Edge en modo app** (firmado por
Microsoft), así que todo lo que se ejecuta viene firmado por otro. Lo arma
`tools/make_release_compatible.ps1`, que además se niega a terminar si en el zip queda un solo
binario sin firma.

Lo que se pierde es lo que es pywebview: el widget y el icono de la bandeja.

⚠️ Edge corre con un perfil PROPIO (`APP_DIR/edge`), y no es por prolijidad: con su perfil, el
proceso que lanzamos es el navegador y vive exactamente lo que vive la ventana (medido), que es
lo que le dice al servidor cuándo apagarse. Con el perfil del usuario, el lanzamiento le pasaría
la ventana a su Edge ya abierto y el proceso saldría en el acto.
"""
import os
import subprocess
import threading
import time
import webbrowser
from pathlib import Path

# Si el proceso de Edge sale antes de esto, no era el navegador: le pasó la ventana a un Edge
# que ya corría con nuestro perfil (uno que sobrevivió a un servidor caído). Ahí la única señal
# de que la ventana sigue abierta son sus pedidos: el refresco poletea cada 3 s.
ENTREGA = 5.0
# Sin pedidos durante esto, nadie está mirando. Largo a propósito: una ventana oculta no poletea.
SIN_PEDIDOS = 30 * 60

_ultimo_pedido = time.monotonic()


def buscar_edge():
    """La ruta de msedge.exe, o None. Viene con Windows 10 y 11, pero se puede desinstalar."""
    try:
        import winreg
        for raiz in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
            try:
                with winreg.OpenKey(raiz, r"SOFTWARE\Microsoft\Windows\CurrentVersion"
                                          r"\App Paths\msedge.exe") as k:
                    ruta = winreg.QueryValue(k, None)
                if ruta and Path(ruta).exists():
                    return ruta
            except OSError:
                pass
    except ImportError:
        pass
    for base in (os.environ.get("PROGRAMFILES(X86)"), os.environ.get("PROGRAMFILES")):
        if base:
            ruta = Path(base) / "Microsoft" / "Edge" / "Application" / "msedge.exe"
            if ruta.exists():
                return str(ruta)
    return None


def abrir_ventana(edge, url, app_dir):
    """Abre la Bitácora en una ventana de Edge sin barra de direcciones. Devuelve el proceso, o
    None si no hay Edge y quedó en el navegador por defecto."""
    if not edge:
        webbrowser.open(url)
        return None
    from bitacora.escritorio.main import tamano_inicial
    try:
        ancho, alto, maximizada = tamano_inicial()
    except Exception:
        ancho, alto, maximizada = 1280, 860, False
    args = [edge, f"--app={url}", f"--user-data-dir={Path(app_dir) / 'edge'}",
            "--no-first-run", "--no-default-browser-check"]
    args.append("--start-maximized" if maximizada else f"--window-size={ancho},{alto}")
    return subprocess.Popen(args)


def _esperar(proc):
    """Bloquea mientras la ventana siga abierta."""
    if proc is not None:
        inicio = time.monotonic()
        proc.wait()
        if time.monotonic() - inicio > ENTREGA:
            return                                  # era el navegador y se cerró: listo
    while time.monotonic() - _ultimo_pedido < SIN_PEDIDOS:
        time.sleep(5)


def main():
    global _ultimo_pedido
    from bitacora.escritorio import instancia, updater
    from bitacora.escritorio import main as escritorio

    escritorio.preparar_entorno()
    edge = buscar_edge()

    # Una sola a la vez, como la ventana normal. Acá "traer la que ya está" es abrirle una
    # ventana más: Edge se la pasa al proceso que ya corre con nuestro perfil.
    if not instancia.tomar():
        url = instancia.leer_url()
        if url:
            abrir_ventana(edge, url, escritorio.APP_DIR)
        return

    escritorio.preparar_datos()

    from werkzeug.serving import make_server
    from bitacora.app import create_app
    flask_app = create_app()

    @flask_app.before_request
    def _visto():
        global _ultimo_pedido
        _ultimo_pedido = time.monotonic()

    servidor = make_server("127.0.0.1", escritorio.puerto_seguro() or 0, flask_app,
                           threaded=True)
    url = f"http://127.0.0.1:{servidor.server_port}"
    threading.Thread(target=servidor.serve_forever, daemon=True).start()
    instancia.publicar_url(url)

    updater.check_in_background()
    aviso = threading.Timer(4.0, escritorio._notify_overdue, args=(flask_app,))
    aviso.daemon = True
    aviso.start()

    _ultimo_pedido = time.monotonic()
    proc = abrir_ventana(edge, url, escritorio.APP_DIR)
    if proc is not None:
        # Al instalar una actualización la app sale con os._exit: sin esto la ventana quedaría
        # abierta sobre un servidor muerto, y al relanzarse aparecería otra al lado.
        updater.al_salir.append(proc.terminate)
    _esperar(proc)
    servidor.shutdown()


def arrancar():
    from bitacora.escritorio.main import arrancar as con_reporte
    con_reporte(main)
