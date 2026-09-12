"""Smoke del widget y la bandeja: lo que necesita ventanas de verdad y no entra en pytest.

Abre ventanas REALES por unos segundos y se cierra solo. Usa un LOCALAPPDATA temporal, así que
no toca tus datos.
Correr: venv/Scripts/python tools/smoke_widget.py
"""
import os
import sys
import tempfile
import threading
import time
from pathlib import Path

tmp = Path(tempfile.mkdtemp(prefix="ht-widget-"))
os.environ["LOCALAPPDATA"] = str(tmp)
os.environ["XDG_DATA_HOME"] = str(tmp)

root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

from bitacora.escritorio import main as desktop  # noqa: E402

desktop.APP_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HT_PERFILES"] = str(desktop.APP_DIR)
os.environ["HT_DB"] = str(desktop.DB_FILE)
desktop._migrate_a_perfiles()

from bitacora import database as db  # noqa: E402
from bitacora import profiles  # noqa: E402
from bitacora.escritorio import tray, widget  # noqa: E402

profiles.aplicar()
db.init_db()
db.add_todo(__import__("datetime").date.today().isoformat(), "tarea del smoke")

from bitacora.app import create_app  # noqa: E402
import webview  # noqa: E402

flask_app = create_app()
fallos = []


def _check(cond, msg):
    # flush=True en todo: os._exit() al final saltea el vaciado de buffers de stdout.
    print(("OK   " if cond else "FALLA") + " " + msg, flush=True)
    if not cond:
        fallos.append(msg)


def guion():
    time.sleep(3)
    try:
        principal = webview.windows[0]
        widget.configurar(principal, principal._url_prefix or "")
        _check(widget.hay_escritorio(), "la URL base se capturó del prefijo del servidor")

        puertos_antes = _puertos()
        _check(widget.abrir(), "el widget se abre desde un hilo que no es el principal")
        time.sleep(2)
        _check(widget.esta_abierto(), "la ventana del widget quedó registrada")
        # Lo que importa: pasarle la app Flask en vez de una URL levantaría OTRO servidor.
        _check(_puertos() == puertos_antes,
               f"NO se levantó un segundo servidor (puertos: {sorted(puertos_antes)})")

        widget.fijar(False)
        time.sleep(0.5)
        _check(widget.esta_fijado() is False, "on_top se puede soltar en caliente")
        widget.fijar(True)
        time.sleep(0.5)
        _check(widget.esta_fijado() is True, "on_top se puede volver a fijar")

        widget.guardar_geometria(x=50, y=60)
        _check(widget.leer_geometria().get("x") == 50,
               f"la geometría se guarda en {widget.GEOMETRIA} (no en settings)")

        # El punto del widget: la ventana grande se cierra y él sigue vivo.
        principal.destroy()
        time.sleep(2)
        _check(widget.esta_abierto(), "el widget SOBREVIVE a cerrar la ventana grande")
        _check(len(webview.windows) == 1, f"queda 1 ventana: {[w.title for w in webview.windows]}")

        widget.abrir_en_principal("/")
        time.sleep(2)
        _check(len(webview.windows) == 2,
               "con la ventana grande cerrada, abrir un día crea una nueva")

        arrancada = tray.iniciar(abrir_app=widget.mostrar_principal,
                                 mostrar_widget=widget.abrir, salir=lambda: None)
        if sys.platform == "win32":
            _check(arrancada and tray.disponible(), "la bandeja pone el icono en Windows")
            tray.quitar()
            _check(not tray.disponible(), "quitar() saca el icono (si no, queda el fantasma)")
        else:
            _check(not arrancada, "en Linux la bandeja degrada en silencio, sin tirar")
    except Exception as e:
        import traceback
        traceback.print_exc()
        fallos.append(str(e))
    finally:
        time.sleep(1)
        print("\n" + ("SMOKE OK" if not fallos else f"SMOKE CON {len(fallos)} FALLAS"))
        os._exit(0 if not fallos else 1)


def _puertos():
    """Direcciones de servidor en uso. Si a una ventana se le pasa el objeto Flask en vez de una
    URL, pywebview le levanta un Bottle propio y aparece un prefijo nuevo acá."""
    return {p for p in (getattr(w, "_url_prefix", None) for w in webview.windows) if p}


threading.Thread(target=guion, daemon=True).start()
webview.settings["ALLOW_DOWNLOADS"] = True
webview.create_window(desktop.WINDOW_TITLE, flask_app, width=900, height=600,
                      min_size=desktop.MIN_SIZE, text_select=True)
webview.start(private_mode=False, storage_path=str(desktop.APP_DIR / "webview"))
