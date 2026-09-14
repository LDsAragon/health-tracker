"""Ventana del widget de escritorio.

Todo degrada a no-op cuando no hay pywebview corriendo (modo navegador y tests), así que las
rutas pueden llamar a estas funciones sin preguntar.
"""
import json
import os
import threading

TITULO = "Bitácora"
ANCHO, ALTO = 340, 520
GEOMETRIA = "widget.json"

# La ventana y la URL base viven acá y no en webview.windows[n]: esa lista cambia de tamaño
# cuando se cierra cualquier ventana, así que indexarla es un bug esperando.
_ventana = None
_principal = None
_url_base = ""
_minimizada = False
_lock = threading.Lock()


def configurar(ventana_principal, url_base: str):
    """La llama bitacora/escritorio/main.py una vez, al arrancar."""
    global _principal, _url_base
    _principal = ventana_principal
    _url_base = (url_base or "").rstrip("/")
    _seguir_el_estado(ventana_principal)


def _seguir_el_estado(ventana):
    """Anotar si la ventana grande está minimizada.

    Hace falta porque `window.minimized` de pywebview es el flag con el que se CREÓ la ventana
    y nunca se actualiza: el estado vivo solo llega por estos eventos. Sin esto habría que
    llamar a `restore()` a ciegas, y `restore()` fuerza WindowState=Normal — o sea que
    desmaximizaría una ventana maximizada.
    """
    def marcar(valor):
        def _h():
            global _minimizada
            _minimizada = valor
        return _h
    try:
        ventana.events.minimized += marcar(True)
        ventana.events.restored += marcar(False)
        ventana.events.maximized += marcar(False)
    except Exception:
        pass


def hay_escritorio() -> bool:
    return bool(_url_base)


# ── Geometría (archivo de DISPOSITIVO, no de perfil) ─────────────────────────
# NO puede ir en la tabla settings: desde el sync los ajustes viajan entre máquinas, y la
# posición del widget terminaría corrida o fuera de pantalla en la otra computadora.

def _ruta_geometria() -> str:
    base = os.environ.get("HT_PERFILES") or "."
    return os.path.join(base, GEOMETRIA)


def leer_geometria() -> dict:
    try:
        with open(_ruta_geometria(), encoding="utf-8") as f:
            d = json.load(f)
        if isinstance(d, dict):
            return {k: int(d[k]) for k in ("x", "y", "w", "h") if isinstance(d.get(k), int)}
    except (OSError, ValueError, TypeError):
        pass
    return {}


def _escribir_geometria(d: dict):
    """Escritura atómica, como profiles.guardar(): un JSON a medio escribir dejaría al widget
    sin saber dónde ponerse."""
    try:
        tmp = _ruta_geometria() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, _ruta_geometria())
    except OSError:
        pass


def guardar_geometria(**campos):
    if not hay_escritorio():
        return
    d = leer_geometria()
    d.update({k: int(v) for k, v in campos.items() if isinstance(v, (int, float))})
    _escribir_geometria(d)


def olvidar_posicion():
    """Saca x/y y deja el tamaño: la posición guardada ya no cae en ninguna pantalla."""
    d = leer_geometria()
    if "x" in d or "y" in d:
        _escribir_geometria({k: v for k, v in d.items() if k in ("w", "h")})


# ⚠️ Cuánto del widget tiene que quedar dentro de una pantalla para poder agarrarlo. No alcanza
# con que "toque": la ventana es frameless y se arrastra desde cualquier lado, pero si asoma una
# franja de 3px no hay nada que agarrar.
VISIBLE_X, VISIBLE_Y = 120, 40


def _pantallas():
    """[(x, y, ancho, alto)] de cada monitor. webview.screens anda sin ventana creada."""
    try:
        import webview
        return [(p.x, p.y, p.width, p.height) for p in webview.screens]
    except Exception:
        return []


def posicion_visible(x, y, w=ANCHO, h=ALTO) -> bool:
    """¿Esa posición cae en algún monitor, con suficiente ventana adentro como para agarrarla?

    ⚠️ Windows le pone **(-32000, -32000)** a una ventana minimizada y pywebview lo dispara como
    un evento `moved`, así que minimizar el widget guardaba esa posición: al siguiente arranque
    la ventana nacía fuera de toda pantalla y quedaba **abierta, invisible y sin forma de
    traerla de vuelta** (la app decía que estaba abierta, que es lo peor del caso). El mismo
    agujero lo abre desenchufar el monitor donde vivía, o traerse un widget.json de otra máquina.
    """
    pantallas = _pantallas()
    if not pantallas:
        # Sin poder preguntar, al menos descartar el centinela: mejor eso que nada.
        return abs(int(x)) < 30000 and abs(int(y)) < 30000
    return any(min(x + w, px + pw) - max(x, px) >= VISIBLE_X
               and min(y + h, py + ph) - max(y, py) >= VISIBLE_Y
               for px, py, pw, ph in pantallas)


# ── La ventana ───────────────────────────────────────────────────────────────

def esta_abierto() -> bool:
    return _ventana is not None


def esta_fijado() -> bool:
    try:
        return bool(_ventana.on_top) if _ventana else True
    except Exception:
        return True


def abrir():
    """Crea la ventana del widget. Devuelve True si quedó abierta.

    Ojo con dos cosas: se le pasa una URL string y NO el objeto Flask (con la app, pywebview le
    levanta un servidor Bottle propio a cada ventana), y create_window solo crea en el acto si
    se la llama desde un hilo que no es el principal.
    """
    global _ventana
    if not hay_escritorio():
        return False
    with _lock:
        if _ventana is not None:
            try:
                _ventana.show()
                return True
            except Exception:
                _ventana = None
        import webview
        g = leer_geometria()
        ancho, alto = g.get("w", ANCHO), g.get("h", ALTO)
        x, y = g.get("x"), g.get("y")
        # Una posición que hoy no existe en ninguna pantalla se descarta y se olvida: la ventana
        # nace donde la pone el sistema, que es lo que pasaba la primera vez.
        if x is not None and y is not None and not posicion_visible(x, y, ancho, alto):
            x = y = None
            olvidar_posicion()
        try:
            _ventana = webview.create_window(
                TITULO, f"{_url_base}/widget",
                width=ancho, height=alto,
                x=x, y=y,
                frameless=True, easy_drag=True, on_top=True,
                resizable=True, min_size=(260, 320), text_select=True,
            )
        except Exception:
            _ventana = None
            return False
    _ventana.events.moved += _al_mover
    _ventana.events.resized += lambda w, h: guardar_geometria(w=w, h=h)
    _ventana.events.closed += _olvidar
    return True


def _al_mover(x, y):
    """Guardar la posición solo si es una posición de verdad — ver `posicion_visible`."""
    g = leer_geometria()
    if posicion_visible(x, y, g.get("w", ANCHO), g.get("h", ALTO)):
        guardar_geometria(x=x, y=y)


def _olvidar():
    global _ventana
    _ventana = None


def cerrar():
    global _ventana
    v, _ventana = _ventana, None
    if v is not None:
        try:
            v.destroy()
        except Exception:
            pass


def fijar(valor: bool):
    if _ventana is not None:
        try:
            _ventana.on_top = bool(valor)
        except Exception:
            pass


def minimizar():
    if _ventana is not None:
        try:
            _ventana.minimize()
        except Exception:
            pass


def _principal_viva():
    """Una ventana destruida NO tira excepción al navegarla: hay que preguntarle a pywebview si
    todavía la tiene en su lista, o el clic en un día se pierde en silencio."""
    global _principal
    if _principal is None:
        return False
    try:
        import webview
        if _principal not in webview.windows:
            _principal = None
    except Exception:
        _principal = None
    return _principal is not None


def abrir_en_principal(ruta: str):
    """Lleva la ventana grande a `ruta`. Que no exista es un caso NORMAL, no un error: el
    sentido del widget es poder cerrarla."""
    global _principal
    if not hay_escritorio():
        return False
    url = f"{_url_base}{ruta}"
    if _principal_viva():
        try:
            _principal.load_url(url)
            _principal.show()
            return True
        except Exception:
            _principal = None      # se cerró: abrimos una nueva abajo
    try:
        import webview
        _principal = webview.create_window(TITULO, url, width=1280, height=860,
                                           min_size=(420, 480), text_select=True)
        _principal.events.closed += _olvidar_principal
        return True
    except Exception:
        return False


def _olvidar_principal():
    global _principal
    _principal = None


def mostrar_principal():
    """Traer de vuelta la ventana grande, **donde la dejaste**.

    La usan el menú de la bandeja y una segunda Bitácora que se cierra sola. No navega a
    propósito: cargar "/" te sacaría del día que estabas mirando, y lo que se pidió fue que
    volviera la misma ventana. Si ya no queda ninguna (la cerraste y seguiste con el widget)
    ahí sí hay que crear una, y esa arranca en el inicio porque no hay nada que preservar.
    """
    if _principal_viva():
        # Escondida en la bandeja y minimizada son estados distintos y pueden darse los dos.
        # `restore()` va SOLO si está minimizada: fuerza WindowState=Normal, así que a una
        # ventana maximizada la desmaximizaría.
        if _minimizada:
            try:
                _principal.restore()
            except Exception:
                pass
        try:
            _principal.show()       # en Windows es Show() + Activate(): la trae al frente
        except Exception:
            return False
        return True
    return abrir_en_principal("/")
