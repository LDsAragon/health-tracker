"""Widget de escritorio y área de notificación.

Lo que necesita una ventana real va a tools/smoke_widget.py; acá va todo lo que se puede
verificar sin display.
"""
import json
from datetime import date, timedelta

import pytest

import database as db
import tray
import widget
import app as flask_app
from appconfig import SETTINGS


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr("database.conn.DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    db.init_db()
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


HOY = date.today().isoformat()
VIEJA = (date.today() - timedelta(days=20)).isoformat()


# ── La página ────────────────────────────────────────────────────────────────

def test_el_widget_muestra_lo_de_hoy_y_lo_sin_cerrar(cliente):
    db.add_todo(HOY, "para hoy")
    db.add_todo(VIEJA, "quedo colgada")
    html = cliente.get("/widget").data.decode()
    assert "para hoy" in html and "quedo colgada" in html

def test_las_tres_pestanas_renderizan(cliente):
    for p in ("tareas", "calendario", "nota"):
        assert cliente.get(f"/widget?p={p}").status_code == 200

def test_una_pestana_inventada_cae_a_tareas(cliente):
    assert b"Agregar una tarea" in cliente.get("/widget?p=zzz").data

def test_el_widget_no_arrastra_el_navbar(cliente):
    """Plantilla propia: sin navbar ni rueda de emociones, que en 340px no entran."""
    html = cliente.get("/widget").data.decode()
    assert "nav-link" not in html and "ew-modal" not in html

def test_el_calendario_no_repite_inicial_de_dia(cliente):
    """Con una sola letra, martes y miércoles quedaban los dos en M."""
    html = cliente.get("/widget?p=calendario").data.decode()
    assert "<th>Mi</th>" in html

def test_el_calendario_acepta_mes_fuera_de_rango(cliente):
    assert cliente.get("/widget?p=calendario&anio=2026&mes=77").status_code == 200


# ── Acciones ─────────────────────────────────────────────────────────────────

def test_tildar_desde_el_widget(cliente):
    db.add_todo(HOY, "x")
    tid = db.get_todos_for_date(HOY)[0]["id"]
    r = cliente.post(f"/widget/tarea/{tid}/toggle")
    assert r.status_code == 302 and "/widget" in r.headers["Location"]
    assert db.get_todos_for_date(HOY)[0]["done"] == 1

def test_agregar_tarea_desde_el_widget(cliente):
    cliente.post("/widget/tarea/agregar", data={"text": "desde el widget"})
    assert [t["text"] for t in db.get_todos_for_date(HOY)] == ["desde el widget"]

def test_no_agrega_una_tarea_vacia(cliente):
    cliente.post("/widget/tarea/agregar", data={"text": "   "})
    assert db.get_todos_for_date(HOY) == []

def test_guardar_nota_desde_el_widget(cliente):
    cliente.post("/widget/nota", data={"content": "anotada al vuelo"})
    assert [n["content"] for n in db.get_notes_for_date(HOY)] == ["anotada al vuelo"]

def test_no_guarda_una_nota_vacia(cliente):
    cliente.post("/widget/nota", data={"content": "  "})
    assert db.get_notes_for_date(HOY) == []


# ── Sin escritorio, las rutas de ventana no pueden explotar ──────────────────

def test_las_acciones_de_ventana_no_explotan_sin_escritorio(cliente):
    """En el navegador y en los tests no hay ventana que fijar ni cerrar."""
    for ruta in ("/widget/fijar", "/widget/minimizar", "/widget/cerrar"):
        assert cliente.post(ruta).status_code == 302
    assert cliente.post("/widget/dia/2026-09-15").status_code == 302
    assert cliente.post("/widget/abrir").status_code == 302

def test_abrir_sin_escritorio_devuelve_false():
    assert widget.hay_escritorio() is False
    assert widget.abrir() is False
    assert widget.abrir_en_principal("/") is False


# ── Geometría: archivo de dispositivo, NO la tabla settings ─────────────────

def test_la_geometria_va_a_un_archivo_y_no_a_settings(tmp_path, monkeypatch):
    """Desde el sync los ajustes viajan entre máquinas: si la posición del widget fuera un
    ajuste, en la otra computadora aparecería corrido o fuera de pantalla."""
    monkeypatch.setattr("database.conn.DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    monkeypatch.setattr(widget, "_url_base", "http://127.0.0.1:1")   # simular escritorio
    db.init_db()
    widget.guardar_geometria(x=100, y=200, w=300, h=400)
    assert widget.leer_geometria() == {"x": 100, "y": 200, "w": 300, "h": 400}
    assert (tmp_path / widget.GEOMETRIA).exists()
    with db.get_db() as c:
        claves = [r["key"] for r in c.execute("SELECT key FROM settings").fetchall()]
    assert not [k for k in claves if "widget" in k and k != "widget_autostart"]

def test_geometria_corrupta_no_tumba_nada(tmp_path, monkeypatch):
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    (tmp_path / widget.GEOMETRIA).write_text("{ roto", encoding="utf-8")
    assert widget.leer_geometria() == {}

def test_geometria_ignora_valores_que_no_son_numeros(tmp_path, monkeypatch):
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    (tmp_path / widget.GEOMETRIA).write_text(json.dumps({"x": "chau", "y": 5}), encoding="utf-8")
    assert widget.leer_geometria() == {"y": 5}


# ── Bandeja ──────────────────────────────────────────────────────────────────

def test_los_ajustes_nuevos_existen():
    assert SETTINGS["widget_autostart"]["default"] == "off"
    assert SETTINGS["cerrar_a_bandeja"]["default"] == "on"

def test_la_bandeja_no_se_intenta_en_linux(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    assert tray.iniciar(lambda: None, lambda: None, lambda: None) is False
    assert tray.disponible() is False

class _VentanaFalsa:
    """Lo mínimo que _al_mostrarse le toca a la ventana grande."""
    def __init__(self):
        self._url_prefix = "http://127.0.0.1:1"
        self.enganchados = []
        ventana = self

        class _Closing:
            def __iadd__(self, h):
                ventana.enganchados.append(h)
                return self

        class _Events:
            closing = _Closing()
        self.events = _Events()


def test_sin_bandeja_no_se_engancha_el_cierre(cliente, monkeypatch):
    """LA regla de seguridad: esconder la ventana al cerrar SIN icono en la bandeja dejaría el
    programa corriendo sin forma de mostrarlo ni de cerrarlo, salvo el administrador de tareas.
    Es el caso de Linux y el de un NotifyIcon que falla."""
    import desktop
    monkeypatch.setattr(tray, "iniciar", lambda **kw: False)
    db.set_setting("cerrar_a_bandeja", "on")     # aun prendido, no debe engancharse
    v = _VentanaFalsa()
    desktop._al_mostrarse(v)
    assert v.enganchados == []


def test_con_bandeja_si_se_engancha_el_cierre(cliente, monkeypatch):
    import desktop
    monkeypatch.setattr(tray, "iniciar", lambda **kw: True)
    db.set_setting("cerrar_a_bandeja", "on")
    v = _VentanaFalsa()
    desktop._al_mostrarse(v)
    assert len(v.enganchados) == 1


def test_con_bandeja_pero_el_ajuste_apagado_no_engancha(cliente, monkeypatch):
    import desktop
    monkeypatch.setattr(tray, "iniciar", lambda **kw: True)
    db.set_setting("cerrar_a_bandeja", "off")
    v = _VentanaFalsa()
    desktop._al_mostrarse(v)
    assert v.enganchados == []


def test_a_la_bandeja_cancela_el_cierre_y_esconde():
    import desktop

    class V:
        escondida = False
        def hide(self):
            V.escondida = True
    v = V()
    assert desktop._a_la_bandeja(v) is False   # False = cancelar el cierre
    assert V.escondida

def test_si_no_se_puede_esconder_deja_cerrar():
    """Preferible cerrar de verdad antes que quedar con una ventana que no se va ni se ve."""
    import desktop

    class V:
        def hide(self):
            raise RuntimeError("no se pudo")
    assert desktop._a_la_bandeja(V()) is True
