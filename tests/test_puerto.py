"""El puerto del servidor interno tiene que ser uno que Chromium acepte.

Chromium —y con él WebView2 y WebKitGTK— se niega a cargar una página servida desde una lista de
puertos "no seguros" y muestra ERR_UNSAFE_PORT: la app queda en blanco hasta reiniciarla.
pywebview sortea el puerto en `random.randint(1023, 65535)`, así que cae en uno cada ~750
arranques. Pasó de verdad, con el 1719.
"""
import socket

from bitacora.escritorio.main import PUERTO_MINIMO, puerto_seguro

# net/base/port_util.cc de Chromium, `kRestrictedPorts`. Está acá para verificar que el umbral
# los cubra a TODOS: si Chromium agrega uno más alto que 10080, este test lo cuenta.
BLOQUEADOS_POR_CHROMIUM = (
    1, 7, 9, 11, 13, 15, 17, 19, 20, 21, 22, 23, 25, 37, 42, 43, 53, 69, 77, 79, 87, 95,
    101, 102, 103, 104, 109, 110, 111, 113, 115, 117, 119, 123, 135, 137, 139, 143, 161, 179,
    389, 427, 465, 512, 513, 514, 515, 526, 530, 531, 532, 540, 548, 554, 556, 563, 587, 601,
    636, 989, 990, 993, 995, 1719, 1720, 1723, 2049, 3659, 4045, 4190, 5060, 5061, 6000, 6566,
    6665, 6666, 6667, 6668, 6669, 6679, 6697, 10080,
)


def test_el_umbral_deja_afuera_todos_los_puertos_bloqueados():
    """LA razón de que alcance un umbral en vez de una lista a mantener."""
    assert PUERTO_MINIMO > max(BLOQUEADOS_POR_CHROMIUM)


def test_el_1719_que_rompio_de_verdad_esta_cubierto():
    assert 1719 in BLOQUEADOS_POR_CHROMIUM
    assert 1719 < PUERTO_MINIMO


def test_devuelve_un_puerto_por_encima_del_umbral():
    p = puerto_seguro()
    assert p is not None
    assert p >= PUERTO_MINIMO


def test_el_puerto_que_devuelve_esta_libre():
    """Se lo pide al sistema operativo, así que tiene que poder tomarse."""
    p = puerto_seguro()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", p))       # si estuviera ocupado, esto tira OSError


def test_nunca_devuelve_uno_bloqueado():
    vistos = {puerto_seguro() for _ in range(60)}
    assert not (vistos & set(BLOQUEADOS_POR_CHROMIUM))


def test_si_no_se_puede_reservar_devuelve_none_y_no_explota(monkeypatch):
    """None significa "elegí vos, pywebview". Preferimos arrancar y quizá fallar en el puerto
    antes que no abrir la app por no poder reservar uno."""
    class _SockRoto:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def bind(self, *a): raise OSError("sin sockets")

    monkeypatch.setattr(socket, "socket", lambda *a, **k: _SockRoto())
    assert puerto_seguro() is None


def test_si_el_so_solo_da_puertos_bajos_devuelve_none(monkeypatch):
    """Un rango efímero configurado abajo de 10081 no puede hacer que devolvamos uno inseguro."""
    class _SockBajo:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def bind(self, *a): pass
        def getsockname(self): return ("127.0.0.1", 1719)

    monkeypatch.setattr(socket, "socket", lambda *a, **k: _SockBajo())
    assert puerto_seguro() is None
