"""Una sola Bitácora a la vez: la segunda vez que la abrís, vuelve la que ya está.

Dos piezas, y las dos hacen falta:

1. **Un lock del sistema operativo** sobre `instancia.lock` decide quién es la primera, sin
   carreras. Es un lock de verdad y no un archivo-bandera con el PID: si la app se cuelga o la
   matás desde el administrador de tareas, el sistema lo suelta solo. Un archivo-bandera
   quedaría ahí y la app no volvería a abrir nunca.
2. **Un archivo con la URL** del servidor para poder avisarle a la que ya corre. No se puede
   saber de antemano: pywebview le da un puerto al azar y recién se conoce cuando la ventana
   está en pantalla.

Todo va al lado de la DB pero **fuera del perfil** (`APP_DIR`): las instancias son de la
instalación, no de la bitácora que tengas abierta. Y todo degrada a no-op sin `HT_PERFILES`
(modo navegador y tests), igual que `widget.py`.
"""
import json
import os
import sys

LOCK = "instancia.lock"
DATOS = "instancia.json"
ESPERA = 2.0        # segundos para que la otra conteste; si no, arrancamos igual

_fd = None          # el handle del lock vive lo que vive el proceso: si se cierra, se suelta


def _base():
    return os.environ.get("HT_PERFILES")


def _ruta(nombre):
    base = _base()
    return os.path.join(base, nombre) if base else None


def tomar() -> bool:
    """True si somos la primera instancia. False si ya hay otra corriendo.

    Sin carpeta de datos (tests, navegador) devuelve True: no hay nada que coordinar.
    """
    global _fd
    ruta = _ruta(LOCK)
    if ruta is None:
        return True
    try:
        _fd = os.open(ruta, os.O_RDWR | os.O_CREAT)
    except OSError:
        return True                     # sin poder abrir el lock, mejor abrir la app que no abrir
    try:
        if sys.platform == "win32":
            import msvcrt
            msvcrt.locking(_fd, msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        os.close(_fd)
        _fd = None
        return False
    return True


def soltar():
    """Solo para los tests: en la app real lo suelta el sistema al terminar el proceso."""
    global _fd
    if _fd is None:
        return
    try:
        if sys.platform == "win32":
            import msvcrt
            os.lseek(_fd, 0, os.SEEK_SET)
            msvcrt.locking(_fd, msvcrt.LK_UNLCK, 1)
        else:
            import fcntl
            fcntl.flock(_fd, fcntl.LOCK_UN)
    except OSError:
        pass
    try:
        os.close(_fd)
    except OSError:
        pass
    _fd = None


def publicar_url(url: str):
    """La llama desktop cuando la ventana ya está en pantalla y el puerto se conoce."""
    ruta = _ruta(DATOS)
    if ruta is None or not url:
        return
    try:
        tmp = ruta + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "url": url.rstrip("/")}, f)
        os.replace(tmp, ruta)
    except OSError:
        pass


def leer_url():
    ruta = _ruta(DATOS)
    if ruta is None:
        return ""
    try:
        with open(ruta, encoding="utf-8") as f:
            d = json.load(f)
        return d.get("url", "") if isinstance(d, dict) else ""
    except (OSError, ValueError):
        return ""


def avisar_a_la_otra() -> bool:
    """Le pide a la instancia que ya corre que muestre su ventana.

    False cuando no se la pudo alcanzar, y ese es un caso NORMAL: la otra puede estar todavía
    arrancando y sin URL publicada. Igual hay que salir — la ventana la va a mostrar ella.
    """
    url = leer_url()
    if not url:
        return False
    import urllib.error
    import urllib.request
    try:
        req = urllib.request.Request(f"{url}/instancia/mostrar", data=b"", method="POST")
        with urllib.request.urlopen(req, timeout=ESPERA) as r:
            return r.status in (200, 204)
    except (urllib.error.URLError, OSError, ValueError):
        return False
