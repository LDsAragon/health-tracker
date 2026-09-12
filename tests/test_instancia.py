"""Una sola Bitácora a la vez.

El caso que decide el diseño es el último: la app muerta a lo bruto. Con un archivo-bandera
con el PID, ese archivo queda y la app no vuelve a abrir nunca; con un lock del sistema
operativo, se suelta solo.
"""
import json
import os
import subprocess
import sys
import textwrap

import pytest

import instancia


@pytest.fixture
def datos(tmp_path, monkeypatch):
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    yield tmp_path
    instancia.soltar()


# ── El lock ──────────────────────────────────────────────────────────────────

def test_la_primera_se_queda_con_el_lock(datos):
    assert instancia.tomar() is True
    assert (datos / instancia.LOCK).exists()


def test_soltar_deja_tomarlo_de_nuevo(datos):
    assert instancia.tomar() is True
    instancia.soltar()
    assert instancia.tomar() is True


def test_sin_carpeta_de_datos_nunca_bloquea(monkeypatch):
    """Modo navegador y tests: no hay instancias que coordinar, la app tiene que arrancar."""
    monkeypatch.delenv("HT_PERFILES", raising=False)
    assert instancia.tomar() is True
    assert instancia.leer_url() == ""
    assert instancia.avisar_a_la_otra() is False


def test_una_carpeta_que_no_se_puede_escribir_no_impide_arrancar(tmp_path, monkeypatch):
    """Preferimos abrir la app sin control de instancias antes que no abrirla."""
    monkeypatch.setenv("HT_PERFILES", str(tmp_path / "no-existe" / "tampoco"))
    assert instancia.tomar() is True


# ── La URL para avisarle a la que ya corre ───────────────────────────────────

def test_publicar_y_leer_la_url(datos):
    instancia.publicar_url("http://127.0.0.1:44065/")
    assert instancia.leer_url() == "http://127.0.0.1:44065"      # sin la barra final
    guardado = json.loads((datos / instancia.DATOS).read_text(encoding="utf-8"))
    assert guardado["pid"] == os.getpid()


def test_una_url_vacia_no_escribe_nada(datos):
    instancia.publicar_url("")
    assert not (datos / instancia.DATOS).exists()


def test_un_json_corrupto_no_tumba_nada(datos):
    (datos / instancia.DATOS).write_text("{ roto", encoding="utf-8")
    assert instancia.leer_url() == ""
    assert instancia.avisar_a_la_otra() is False


def test_avisar_a_una_url_muerta_devuelve_false(datos):
    """Caso NORMAL: la otra instancia todavía está arrancando y no publicó su URL. La segunda
    igual se cierra — la ventana la muestra la primera cuando termine de abrir."""
    instancia.publicar_url("http://127.0.0.1:1")
    assert instancia.avisar_a_la_otra() is False


def test_avisar_le_pega_a_la_ruta_correcta(datos, monkeypatch):
    vistas = []

    class _Resp:
        status = 204
        def __enter__(self): return self
        def __exit__(self, *a): return False

    import urllib.request
    def falso(req, timeout=None):
        vistas.append((req.full_url, req.get_method()))
        return _Resp()
    monkeypatch.setattr(urllib.request, "urlopen", falso)

    instancia.publicar_url("http://127.0.0.1:5000")
    assert instancia.avisar_a_la_otra() is True
    assert vistas == [("http://127.0.0.1:5000/instancia/mostrar", "POST")]


# ── La ruta que recibe el aviso ──────────────────────────────────────────────

def test_la_ruta_mostrar_no_explota_sin_ventana(tmp_path, monkeypatch):
    """En el navegador y en los tests no hay ventana grande que traer."""
    import database as db
    import app as flask_app
    monkeypatch.setattr("database.conn.DB_PATH", str(tmp_path / "t.db"))
    db.init_db()
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        assert c.post("/instancia/mostrar").status_code == 204


def test_la_ruta_mostrar_trae_la_ventana(tmp_path, monkeypatch):
    import database as db
    import widget
    import app as flask_app
    monkeypatch.setattr("database.conn.DB_PATH", str(tmp_path / "t.db"))
    db.init_db()
    llamadas = []
    monkeypatch.setattr(widget, "mostrar_principal", lambda: llamadas.append(1) or True)
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        c.post("/instancia/mostrar")
    assert llamadas == [1]


# ── Dos procesos de verdad ───────────────────────────────────────────────────

_GUION = textwrap.dedent("""
    import os, sys
    os.environ["HT_PERFILES"] = sys.argv[1]
    sys.path.insert(0, sys.argv[2])
    import instancia
    print("SI" if instancia.tomar() else "NO", flush=True)
    if len(sys.argv) > 3 and sys.argv[3] == "esperar":
        sys.stdin.read(1)          # queda vivo con el lock tomado
""")


def _lanzar(datos, tmp_path, *extra):
    guion = tmp_path / "g.py"
    guion.write_text(_GUION, encoding="utf-8")
    raiz = os.path.dirname(os.path.abspath(instancia.__file__))
    return subprocess.Popen([sys.executable, str(guion), str(datos), raiz, *extra],
                            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True)


def test_la_segunda_instancia_no_consigue_el_lock(datos, tmp_path):
    primera = _lanzar(datos, tmp_path, "esperar")
    try:
        assert primera.stdout.readline().strip() == "SI"
        segunda = _lanzar(datos, tmp_path)
        assert segunda.stdout.readline().strip() == "NO"
        segunda.wait(timeout=15)
    finally:
        primera.kill()
        primera.wait(timeout=15)


def test_matar_la_app_a_lo_bruto_libera_el_lock(datos, tmp_path):
    """LA razón de usar un lock del sistema y no un archivo con el PID: si la app se cuelga y
    la matás desde el administrador de tareas, el archivo quedaría y no abriría nunca más."""
    primera = _lanzar(datos, tmp_path, "esperar")
    assert primera.stdout.readline().strip() == "SI"
    primera.kill()                      # sin limpiar nada, como el administrador de tareas
    primera.wait(timeout=15)

    segunda = _lanzar(datos, tmp_path)
    try:
        assert segunda.stdout.readline().strip() == "SI"
    finally:
        segunda.wait(timeout=15)


# ── Volver "donde la dejaste", no al inicio ──────────────────────────────────

class _VentanaViva:
    """Lo mínimo que mostrar_principal() le toca a la ventana grande."""
    def __init__(self):
        self.hecho = []
    def show(self):
        self.hecho.append("show")
    def restore(self):
        self.hecho.append("restore")
    def load_url(self, url):
        self.hecho.append(f"load_url:{url}")


def test_volver_no_navega_si_la_ventana_sigue_viva(monkeypatch):
    """Lo que se pidió: que vuelva LA MISMA. Un load_url("/") te sacaría del día que estabas
    mirando. En Windows `show()` es Show() + Activate(), así que alcanza para traerla al frente."""
    import webview
    import widget
    v = _VentanaViva()
    monkeypatch.setattr(widget, "_principal", v)
    monkeypatch.setattr(widget, "_minimizada", False)
    monkeypatch.setattr(webview, "windows", [v])

    assert widget.mostrar_principal() is True
    assert v.hecho == ["show"]
    assert not [h for h in v.hecho if h.startswith("load_url")]


def test_volver_no_desmaximiza_una_ventana_maximizada(monkeypatch):
    """`restore()` fuerza WindowState=Normal. Llamarlo a ciegas le sacaba el maximizado a una
    ventana que estaba maximizada y visible."""
    import webview
    import widget
    v = _VentanaViva()
    monkeypatch.setattr(widget, "_principal", v)
    monkeypatch.setattr(widget, "_minimizada", False)
    monkeypatch.setattr(webview, "windows", [v])

    widget.mostrar_principal()
    assert "restore" not in v.hecho


def test_volver_desminimiza_solo_si_estaba_minimizada(monkeypatch):
    import webview
    import widget
    v = _VentanaViva()
    monkeypatch.setattr(widget, "_principal", v)
    monkeypatch.setattr(widget, "_minimizada", True)
    monkeypatch.setattr(webview, "windows", [v])

    assert widget.mostrar_principal() is True
    assert v.hecho == ["restore", "show"]       # desminimizar y recién después activar


def test_el_estado_de_minimizado_se_sigue_por_eventos(monkeypatch):
    """`window.minimized` de pywebview es el flag de creación y nunca se actualiza: el estado
    vivo solo llega por los eventos."""
    import widget

    class _Ev:
        def __init__(self): self.handlers = []
        def __iadd__(self, h): self.handlers.append(h); return self
        def disparar(self):
            for h in self.handlers:
                h()

    class _V:
        def __init__(self):
            class _E:
                minimized = _Ev()
                restored = _Ev()
                maximized = _Ev()
            self.events = _E()

    v = _V()
    monkeypatch.setattr(widget, "_minimizada", False)
    widget._seguir_el_estado(v)

    v.events.minimized.disparar()
    assert widget._minimizada is True
    v.events.restored.disparar()
    assert widget._minimizada is False
    v.events.minimized.disparar()
    v.events.maximized.disparar()
    assert widget._minimizada is False


def test_volver_crea_una_ventana_si_no_quedaba_ninguna(monkeypatch):
    """Cerraste la grande y seguiste con el widget: ahí sí hay que crear una, y empieza en el
    inicio porque no hay nada que preservar."""
    import webview
    import widget
    creadas = []
    monkeypatch.setattr(widget, "_principal", None)
    monkeypatch.setattr(widget, "_url_base", "http://127.0.0.1:1")
    monkeypatch.setattr(webview, "windows", [])
    monkeypatch.setattr(webview, "create_window",
                        lambda *a, **k: creadas.append(a[1]) or _VentanaConEventos())

    assert widget.mostrar_principal() is True
    assert creadas == ["http://127.0.0.1:1/"]


class _VentanaConEventos(_VentanaViva):
    def __init__(self):
        super().__init__()
        class _Closed:
            def __iadd__(self, h): return self
        class _Events:
            closed = _Closed()
        self.events = _Events()
