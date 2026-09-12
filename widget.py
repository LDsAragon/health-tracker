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
_lock = threading.Lock()


def configurar(ventana_principal, url_base: str):
    """La llama desktop.py una vez, al arrancar."""
    global _principal, _url_base
    _principal = ventana_principal
    _url_base = (url_base or "").rstrip("/")


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


def guardar_geometria(**campos):
    """Escritura atómica, como profiles.guardar(): un JSON a medio escribir dejaría al widget
    sin saber dónde ponerse."""
    if not hay_escritorio():
        return
    d = leer_geometria()
    d.update({k: int(v) for k, v in campos.items() if isinstance(v, (int, float))})
    try:
        tmp = _ruta_geometria() + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, _ruta_geometria())
    except OSError:
        pass


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
        try:
            _ventana = webview.create_window(
                TITULO, f"{_url_base}/widget",
                width=g.get("w", ANCHO), height=g.get("h", ALTO),
                x=g.get("x"), y=g.get("y"),
                frameless=True, easy_drag=True, on_top=True,
                resizable=True, min_size=(260, 320), text_select=True,
            )
        except Exception:
            _ventana = None
            return False
    _ventana.events.moved += lambda x, y: guardar_geometria(x=x, y=y)
    _ventana.events.resized += lambda w, h: guardar_geometria(w=w, h=h)
    _ventana.events.closed += _olvidar
    return True


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
    """Para el menú de la bandeja: traer de vuelta la ventana grande."""
    return abrir_en_principal("/")
