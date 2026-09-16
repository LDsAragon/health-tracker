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


def _esperar(cond, segundos=8):
    """Espera a que se cumpla, hasta `segundos`.

    ⚠️ Con un `sleep` fijo, un chequeo sobre una ventana real mide la velocidad del escritorio y
    no si la ventana cambió: en GTK el redimensionado pasa por el gestor de ventanas y el evento
    vuelve cuando vuelve —con 1 segundo daba en rojo algo que sí funcionaba—.
    """
    limite = time.time() + segundos
    while time.time() < limite and not cond():
        time.sleep(0.2)
    return cond()


def _geometria():
    g = widget.leer_geometria()
    return g.get("w"), g.get("h")


def guion():
    time.sleep(3)
    try:
        principal = webview.windows[0]
        widget.configurar(principal, principal._url_prefix or "")
        _check(widget.hay_escritorio(), "la URL base se capturó del prefijo del servidor")
        # Chromium rechaza ~85 puertos con ERR_UNSAFE_PORT y la app queda en blanco.
        puerto = int((principal._url_prefix or "").rsplit(":", 1)[-1].rstrip("/"))
        _check(puerto >= desktop.PUERTO_MINIMO,
               f"el servidor levantó en un puerto que Chromium acepta ({puerto})")

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

        # Estirar la ventana. ⚠️ Es `frameless`, o sea FormBorderStyle = None: NO tiene borde de
        # redimensionado y el `resizable=True` con el que se crea no hace nada. El agarre lo pone
        # la página y termina en `redimensionar()`, así que acá se prueba esa mitad —la otra, que
        # el mouse pueda agarrar la esquina, es de las que se miran.
        widget.redimensionar(480, 640)
        _check(_esperar(lambda: _geometria() == (480, 640)),
               f"redimensionar cambia la ventana Y queda guardado: {_geometria()}")
        # Lo anterior pasa solo si el evento `resized` salta con un resize NUESTRO y no solo con
        # el del mouse: si no saltara, el tamaño se perdería al cerrar y nadie se enteraría.
        widget.redimensionar(10, 10)
        _check(_esperar(lambda: _geometria() == widget.MIN_WIDGET),
               f"una medida imposible se acota al mínimo {widget.MIN_WIDGET}: {_geometria()}")
        widget.tamano_original()
        _check(_esperar(lambda: _geometria() == (widget.ANCHO, widget.ALTO)),
               f"el doble clic del agarre devuelve la medida de fábrica: {_geometria()}")

        # El borde con el que el SISTEMA redimensiona. En Windows es reponerle WS_THICKFRAME a
        # una ventana frameless; en Linux no aplica (ahí va begin_resize_drag de GTK).
        if sys.platform == "win32":
            import ctypes
            _check(widget.poner_borde_nativo(), "se le repone el borde de redimensionado")
            estilo = ctypes.windll.user32.GetWindowLongW(widget._hwnd(), widget.GWL_STYLE)
            _check(bool(estilo & widget.WS_THICKFRAME),
                   "WS_THICKFRAME quedó puesto: el borde de la ventana ya es el agarre del sistema")
            _check(widget.empezar_arrastre_de_tamano() is not None,
                   "pedirle el arrastre al sistema no explota")
        else:
            _check(widget.poner_borde_nativo() is False,
                   "en Linux el borde nativo no aplica y no rompe")

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
# ⚠️ El `http_port` NO es opcional acá: sin él pywebview sortea el puerto con randint(1023, 65535)
# y cae en uno de los ~85 que Chromium rechaza (ERR_UNSAFE_PORT) cada ~750 arranques. La app lo
# pasa en `escritorio/main.py`; este smoke repetía el arranque a mano y se lo había salteado, así
# que su propio chequeo del puerto venía en rojo —probaba el smoke y no la app—.
webview.create_window(desktop.WINDOW_TITLE, flask_app, width=900, height=600,
                      min_size=desktop.MIN_SIZE, text_select=True,
                      http_port=desktop.puerto_seguro())
webview.start(private_mode=False, storage_path=str(desktop.APP_DIR / "webview"))
