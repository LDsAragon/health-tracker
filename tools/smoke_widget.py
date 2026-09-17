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
            _check(widget.preparar_marco_nativo(), "se le repone el borde de redimensionado")
            estilo = ctypes.windll.user32.GetWindowLongW(widget._hwnd(), widget.GWL_STYLE)
            _check(bool(estilo & widget.WS_THICKFRAME),
                   "WS_THICKFRAME quedó puesto: el borde de la ventana ya es el agarre del sistema")
            # ⚠️ Y el de maximizar SACADO. Con el arrastre en manos del sistema, ese bit hace que
            # llevar el widget contra un borde de la pantalla dispare Aero Snap: medido, al borde
            # izquierdo se estiraba a media pantalla y arriba se maximizaba.
            _check(not (estilo & widget.WS_MAXIMIZEBOX),
                   "WS_MAXIMIZEBOX quedó sacado: el borde de la pantalla no deforma el widget")
            # ⚠️ Que el agarre de la esquina ARRANQUE de verdad el bucle del sistema. Devolver
            # True no alcanza: la primera versión devolvía True y no pasaba nada, porque llamaba
            # a ReleaseCapture() desde el hilo del request —que no suelta la captura del hilo de
            # la ventana— y el agarre quedaba de adorno. `GUI_INMOVESIZE` lo dice sin tener que
            # mover el mouse de nadie.
            class GUITHREADINFO(ctypes.Structure):
                _fields_ = [("cbSize", ctypes.c_ulong), ("flags", ctypes.c_ulong),
                            ("hwndActive", ctypes.c_void_p), ("hwndFocus", ctypes.c_void_p),
                            ("hwndCapture", ctypes.c_void_p), ("hwndMenuOwner", ctypes.c_void_p),
                            ("hwndMoveSize", ctypes.c_void_p), ("hwndCaret", ctypes.c_void_p),
                            ("rcCaret", ctypes.c_long * 4)]

            u32 = ctypes.windll.user32
            hilo = u32.GetWindowThreadProcessId(widget._hwnd(), None)

            def _en_bucle():
                gi = GUITHREADINFO()
                gi.cbSize = ctypes.sizeof(GUITHREADINFO)
                u32.GetGUIThreadInfo(hilo, ctypes.byref(gi))
                return bool(gi.flags & 0x00000002)      # GUI_INMOVESIZE

            _check(not _en_bucle(), "antes de pedirlo, la ventana no está redimensionando")
            widget.empezar_arrastre_de_tamano()
            _check(_esperar(_en_bucle, 3),
                   "el agarre le pasa el arrastre AL SISTEMA (entra al bucle de resize)")
            u32.PostMessageW(widget._hwnd(), 0x0100, 0x1B, 0)     # Escape: salir del bucle
            _check(_esperar(lambda: not _en_bucle(), 3), "y sale del bucle al cancelarlo")

            # ⚠️ Lo mismo para MOVER la ventana, que es lo que antes hacía `easy_drag` desde
            # JavaScript: un mensaje al proceso por cada mousemove, la ventana atrasada del
            # cursor y el arrastre cortándose solo en cuanto el cursor salía del WebView.
            #
            # ⚠️ Y acá el chequeo TIENE que apretar el botón de verdad, que es lo que hace la
            # app: la página pide el arrastre desde un `mousemove`, o sea con el mouse apretado.
            # Medido: `HTCAPTION` **no entra al bucle** sin un botón apretado (Windows lo
            # descarta, no hay arrastre que seguir) mientras que `HTBOTTOMRIGHT` entra igual. Con
            # la copia del chequeo del agarre —que no aprieta nada— esto salía en rojo y lo que
            # fallaba era el andamio. Mismo agujero que ya tuvieron smoke_desktop y este mismo
            # smoke: un smoke que no hace lo que hace la app se prueba a sí mismo.
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            class RECT(ctypes.Structure):
                _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                            ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

            def _posicion():
                r = RECT()
                u32.GetWindowRect(widget._hwnd(), ctypes.byref(r))
                return r.left, r.top

            def _mover_cursor(x, y):
                ancho, alto = u32.GetSystemMetrics(0), u32.GetSystemMetrics(1)
                u32.mouse_event(0x0001 | 0x8000,                 # MOVE | ABSOLUTE
                                int(x * 65535 / (ancho - 1)), int(y * 65535 / (alto - 1)), 0, 0)

            guardado = POINT()
            u32.GetCursorPos(ctypes.byref(guardado))
            desde = _posicion()
            _mover_cursor(desde[0] + 170, desde[1] + 10)          # la barra de arriba del widget
            time.sleep(0.2)
            u32.mouse_event(0x0002, 0, 0, 0, 0)                   # LEFTDOWN
            time.sleep(0.1)
            widget.empezar_arrastre_de_ventana()
            entro = _esperar(_en_bucle, 3)
            _check(entro, "arrastrar la ventana se lo queda EL SISTEMA (entra al bucle de move)")
            _mover_cursor(desde[0] + 250, desde[1] + 90)          # 80 px en diagonal
            time.sleep(0.3)
            # Que la ventana SIGA al cursor es el punto: con easy_drag se quedaba atrás y, en
            # cuanto el cursor se le adelantaba y salía del WebView, el arrastre se cortaba.
            llego = _esperar(lambda: _posicion() != desde, 3)
            u32.mouse_event(0x0004, 0, 0, 0, 0)                   # LEFTUP
            time.sleep(0.4)
            _check(llego, f"y la ventana SIGUE al cursor: {desde} -> {_posicion()}")
            _check(_esperar(lambda: not _en_bucle(), 3), "y sale del bucle al soltar")
            _check(_esperar(lambda: widget.leer_geometria().get("x") == _posicion()[0], 3),
                   "la posición nueva queda guardada (el evento `moved` salta igual)")
            u32.SetCursorPos(guardado.x, guardado.y)              # devolverle el mouse a quien mire
        else:
            _check(widget.preparar_marco_nativo() is False,
                   "en Linux el borde nativo no aplica y no rompe")
            # ⚠️ Allá los dos arrastres son los `begin_*_drag` de GTK, y `_arrastre_del_sistema`
            # se traga cualquier excepción: si el método no existiera, las dos funciones
            # devolverían False y el widget quedaría sin arrastre **sin decir nada**. No se los
            # llama de verdad porque sin un botón apretado GTK hace un grab del puntero y el
            # smoke podría quedarse colgado: que el arrastre se sienta bien es de los que se
            # miran a mano.
            nativa = widget._ventana.native
            for metodo in ("begin_move_drag", "begin_resize_drag"):
                _check(hasattr(nativa, metodo),
                       f"la ventana GTK tiene {metodo}: el arrastre no queda de adorno")

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
