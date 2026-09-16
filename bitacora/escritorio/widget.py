"""Ventana del widget de escritorio.

Todo degrada a no-op cuando no hay pywebview corriendo (modo navegador y tests), así que las
rutas pueden llamar a estas funciones sin preguntar.
"""
import json
import os
import threading

TITULO = "Bitácora"
ANCHO, ALTO = 340, 520
# Lo más chico que puede quedar el widget. Es el `min_size` de su ventana Y el piso del acotado
# de `redimensionar()`: son el mismo límite y tenían que salir del mismo lugar.
MIN_WIDGET = (260, 320)
# Mínimo de la ventana GRANDE (el del widget es el min_size de su create_window).
MIN_PRINCIPAL = (420, 480)
GEOMETRIA = "widget.json"

# La ventana y la URL base viven acá y no en webview.windows[n]: esa lista cambia de tamaño
# cuando se cierra cualquier ventana, así que indexarla es un bug esperando.
_ventana = None
_principal = None
_url_base = ""
_minimizada = False
_lock = threading.Lock()
# ⚠️ Propio, y no el de arriba: la geometría la escriben los manejadores de eventos de la
# ventana (`moved` y `resized`), que corren por su cuenta y pueden pisarse —ver
# `_escribir_geometria`—, mientras que `_lock` protege la creación de la ventana.
_geo_lock = threading.Lock()


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
    sin saber dónde ponerse.

    ⚠️ **El leer-modificar-escribir va bajo `_geo_lock`** (en `guardar_geometria`). Los dos que
    escriben acá son manejadores de eventos de la ventana —`moved` y `resized`— y llegan JUNTOS:
    en GTK cada redimensionado viene con su `moved` pegado. Cada uno leía el archivo, cambiaba lo
    suyo y lo escribía entero, así que el que escribía último lo hacía sobre una foto vieja y le
    devolvía al archivo las claves del otro **como estaban antes**: movés el widget y pierde el
    tamaño recién elegido, o al revés. Lo cazó `hacer.ps1 smoke widget` en Linux y lo fija
    `test_mover_y_redimensionar_a_la_vez_no_se_pisan`.

    El temporal lleva además el id del hilo: compartido, uno podía truncarlo justo cuando el otro
    estaba por renombrarlo y lo que quedaba en disco era un JSON vacío. Es mucho más raro que lo
    anterior —y por eso no tiene test propio—, pero cuesta una línea evitarlo.
    """
    try:
        tmp = "{}.{}.tmp".format(_ruta_geometria(), threading.get_ident())
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(d, f)
        os.replace(tmp, _ruta_geometria())
    except OSError:
        pass


def guardar_geometria(**campos):
    if not hay_escritorio():
        return
    with _geo_lock:
        d = leer_geometria()
        d.update({k: int(v) for k, v in campos.items() if isinstance(v, (int, float))})
        _escribir_geometria(d)


def olvidar_posicion():
    """Saca x/y y deja el tamaño: la posición guardada ya no cae en ninguna pantalla."""
    with _geo_lock:
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
                resizable=True, min_size=MIN_WIDGET, text_select=True,
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


def _acotar(w, h):
    """El tamaño pedido, con piso en `MIN_WIDGET` y techo en la pantalla más grande."""
    w, h = int(w), int(h)
    w, h = max(w, MIN_WIDGET[0]), max(h, MIN_WIDGET[1])
    pantallas = _pantallas()
    if pantallas:
        w = min(w, max(p[2] for p in pantallas))
        h = min(h, max(p[3] for p in pantallas))
    return w, h


def redimensionar(w, h):
    """Cambiar el tamaño del widget. La pide la página mientras arrastrás el agarre.

    ⚠️ **El agarre lo tiene que poner la página.** La ventana es `frameless`, y en Windows eso es
    `FormBorderStyle = None`: no tiene borde de redimensionado, así que el `resizable=True` con el
    que se crea **no hace nada** y con el mouse no hay de dónde agarrarla. Renunciar a `frameless`
    para ganar el borde del sistema le devolvería la barra de título, que es justo lo que el
    widget no tiene.

    No guarda nada a propósito: `resize()` dispara el evento `resized` que ya está enganchado en
    `abrir()` (es el `Resize` de WinForms, que salta igual sea del mouse o nuestro), y ese escribe
    la geometría. Dos caminos de guardado serían dos verdades.

    Devuelve la medida que aplicó —o la que habría aplicado si no hay ventana—, y la página la
    usa para seguir el arrastre desde ahí: así el tope vive en un solo lado y el agarre no sigue
    contando por su cuenta una ventana que ya no se achicó más.
    """
    ancho, alto = _acotar(w, h)
    if _ventana is not None:
        try:
            _ventana.resize(ancho, alto)
        except Exception:
            pass
    return ancho, alto


def tamano_original():
    """Doble clic en el agarre: vuelve a la medida de fábrica.

    Es el mismo gesto que ya resetea el ancho de los paneles del día, así que no hay nada nuevo
    que aprender y la barra de 340px no pierde otro botón.
    """
    return redimensionar(ANCHO, ALTO)


def tamano_actual():
    """Con qué medida está el widget ahora, para que la página arranque el arrastre desde ahí.

    ⚠️ Sale de la geometría guardada —que el evento `resized` mantiene al día— y no de
    `_ventana.width`, que **espera hasta 15 segundos** a que la ventana se haya mostrado: esto lo
    lee un request que puede llegar justo mientras el widget se está abriendo.
    """
    g = leer_geometria()
    return g.get("w", ANCHO), g.get("h", ALTO)


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


# ── La medida de la ventana grande (ajuste `window_size`) ────────────────────

def medidas_ventana(valor: str):
    """(ancho, alto, maximizada) para la ventana grande, a partir del ajuste.

    ⚠️ Se acota a la pantalla. Los ajustes viajan en el sync, así que una medida elegida en un
    monitor de 2560 puede llegar a una máquina de 1366: una ventana más grande que la pantalla
    nace con los bordes afuera, y en Windows el borde de arriba se lleva la barra de título.
    """
    from bitacora.appconfig import SETTINGS, es_resolucion
    ancho, alto = (int(n) for n in SETTINGS["window_size"]["default"].split("x"))
    if valor == "maximizada":
        return ancho, alto, True                 # el default queda como tamaño de "restaurar"
    if es_resolucion(valor):
        ancho, alto = (int(n) for n in valor.split("x"))
    pantallas = _pantallas()
    if pantallas:
        # La más grande: es donde la ventana tiene chance de entrar entera.
        ancho = min(ancho, max(p[2] for p in pantallas))
        alto = min(alto, max(p[3] for p in pantallas) - 40)      # barra de tareas
    return max(ancho, MIN_PRINCIPAL[0]), max(alto, MIN_PRINCIPAL[1]), False


def aplicar_tamano_principal(valor: str) -> bool:
    """Cambiar la medida de la ventana grande **en caliente**, al elegirla en Ajustes.

    Aplicarlo solo al arrancar dejaba el ajuste sin efecto visible hasta el siguiente arranque,
    que para algo que se elige mirando la ventana es como no verlo.
    """
    if not hay_escritorio() or not _principal_viva():
        return False
    ancho, alto, maximizada = medidas_ventana(valor)
    try:
        if maximizada:
            _principal.maximize()
        else:
            _principal.restore()      # sin salir de maximizada, el resize no se ve
            _principal.resize(ancho, alto)
        return True
    except Exception:
        return False


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
