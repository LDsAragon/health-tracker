"""Widget de escritorio y área de notificación.

Lo que necesita una ventana real va a tools/smoke_widget.py; acá va todo lo que se puede
verificar sin display.
"""
import json
import pathlib
from datetime import date, timedelta

import pytest

from bitacora import database as db
from bitacora.escritorio import tray
from bitacora.escritorio import widget
from bitacora import app as flask_app
from bitacora.appconfig import SETTINGS


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    db.init_db()
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c


RAIZ = pathlib.Path(__file__).resolve().parent.parent

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


# ── Editar una nota desde el widget ──────────────────────────────────────────

def test_el_widget_lista_las_notas_de_hoy_con_su_lapiz(cliente):
    """La pestaña de Nota solo dejaba escribir una nueva: lo anotado no se veía ni se tocaba."""
    db.add_note(HOY, "algo anotado", "#ef4444")
    html = cliente.get("/widget?p=nota").data.decode()
    assert "algo anotado" in html
    assert "w-lapiz" in html
    assert 'data-refresco="notas"' in html


def test_lo_de_hoy_arranca_colapsado(cliente):
    """El widget tiene que ocupar lo mínimo: la lista está para consultarla de vez en cuando.

    ⚠️ El <details> va FUERA de la zona de refresco: adentro, cada actualización de la lista le
    cerraría el desplegable en la cara.
    """
    db.add_note(HOY, "algo anotado")
    html = cliente.get("/widget?p=nota").data.decode()
    detalles = html[html.index('id="w-notas-hoy"'):]
    assert "<details" in html[:html.index('id="w-notas-hoy"')][-60:]
    assert "open" not in html[html.index('<details'):html.index('id="w-notas-hoy"') + 20]
    assert detalles.index('data-refresco="notas"') < detalles.index("</details>")


def test_el_widget_deja_editar_una_tarea(cliente):
    """Lo que se pidió primero: el lápiz también en las tareas."""
    db.add_todo(HOY, "compar pan")
    tid = db.get_todos_for_date(HOY)[0]["id"]
    html = cliente.get("/widget").data.decode()
    assert f"/widget/tarea/{tid}/editar" in html and "w-lapiz" in html

    r = cliente.post(f"/widget/tarea/{tid}/editar", data={"text": "comprar pan"})
    assert r.status_code == 204
    assert db.get_todos_for_date(HOY)[0]["text"] == "comprar pan"


def test_el_widget_edita_tambien_una_tarea_ATRASADA(cliente):
    """Las sin cerrar son de otros días y el widget las muestra igual: se pueden editar."""
    db.add_todo(VIEJA, "algo viejo")
    tid = db.get_todos_for_date(VIEJA)[0]["id"]
    assert cliente.post(f"/widget/tarea/{tid}/editar",
                        data={"text": "algo viejo, corregido"}).status_code == 204
    assert db.get_todos_for_date(VIEJA)[0]["text"] == "algo viejo, corregido"


def test_el_widget_no_edita_una_tarea_que_no_muestra(cliente):
    """Una de mañana no está en el widget: no se toca desde acá."""
    manana = (date.today() + timedelta(days=1)).isoformat()
    db.add_todo(manana, "la de mañana")
    tid = db.get_todos_for_date(manana)[0]["id"]
    assert cliente.post(f"/widget/tarea/{tid}/editar", data={"text": "pisada"}).status_code == 400
    assert db.get_todos_for_date(manana)[0]["text"] == "la de mañana"


def test_el_widget_no_guarda_una_tarea_vacia(cliente):
    db.add_todo(HOY, "algo")
    tid = db.get_todos_for_date(HOY)[0]["id"]
    assert cliente.post(f"/widget/tarea/{tid}/editar", data={"text": "  "}).status_code == 400
    assert db.get_todos_for_date(HOY)[0]["text"] == "algo"


def test_editar_una_nota_desde_el_widget(cliente):
    db.add_note(HOY, "a medio escribir")
    nid = db.get_notes_for_date(HOY)[0]["id"]
    r = cliente.post(f"/widget/nota/{nid}", data={"content": "a medio escribir, ya no"})
    assert r.status_code == 204
    assert db.get_notes_for_date(HOY)[0]["content"] == "a medio escribir, ya no"


def test_editar_desde_el_widget_NO_le_borra_el_color_a_la_nota(cliente):
    """⚠️ `update_note` reescribe la fila entera, color incluido.

    Sin releer la nota para devolverle el suyo, editar el texto desde el widget le apagaba el
    color a una nota que sí lo tenía — un dato del usuario perdido sin que nada avise.
    """
    db.add_note(HOY, "roja", "#ef4444")
    nid = db.get_notes_for_date(HOY)[0]["id"]
    cliente.post(f"/widget/nota/{nid}", data={"content": "sigue roja"})
    assert db.get_notes_for_date(HOY)[0]["color"] == "#ef4444"


def test_el_widget_solo_edita_notas_de_hoy(cliente):
    """El widget muestra las de hoy: un id de otro día no se toca."""
    db.add_note(VIEJA, "de hace veinte días")
    nid = db.get_notes_for_date(VIEJA)[0]["id"]
    assert cliente.post(f"/widget/nota/{nid}", data={"content": "pisada"}).status_code == 400
    assert db.get_notes_for_date(VIEJA)[0]["content"] == "de hace veinte días"


def test_el_widget_no_guarda_una_edicion_vacia(cliente):
    db.add_note(HOY, "algo")
    nid = db.get_notes_for_date(HOY)[0]["id"]
    assert cliente.post(f"/widget/nota/{nid}", data={"content": "   "}).status_code == 400
    assert db.get_notes_for_date(HOY)[0]["content"] == "algo"


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
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "t.db"))
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    monkeypatch.setattr(widget, "_url_base", "http://127.0.0.1:1")   # simular escritorio
    db.init_db()
    widget.guardar_geometria(x=100, y=200, w=300, h=400)
    assert widget.leer_geometria() == {"x": 100, "y": 200, "w": 300, "h": 400}
    assert (tmp_path / widget.GEOMETRIA).exists()
    with db.get_db() as c:
        claves = [r["key"] for r in c.execute("SELECT key FROM settings").fetchall()]
    assert not [k for k in claves if "widget" in k and k != "widget_autostart"]

# ── La medida de la ventana grande ───────────────────────────────────────────

def test_la_medida_de_la_ventana_sale_del_ajuste(monkeypatch):
    monkeypatch.setattr(widget, "_pantallas", lambda: [(0, 0, 1920, 1080)])
    assert widget.medidas_ventana("1366x768") == (1366, 768, False)
    assert widget.medidas_ventana("maximizada")[2] is True
    assert widget.medidas_ventana("")[:2] == (1280, 860)        # el default del esquema
    assert widget.medidas_ventana("basura")[:2] == (1280, 860)


def test_una_medida_mas_grande_que_la_pantalla_se_acota(monkeypatch):
    """⚠️ Los ajustes viajan en el sync: una medida elegida en un monitor de 2560 puede llegar a
    una máquina de 1366, y una ventana más grande que la pantalla nace con los bordes —y la
    barra de título— afuera."""
    monkeypatch.setattr(widget, "_pantallas", lambda: [(0, 0, 1366, 768)])
    assert widget.medidas_ventana("1920x1080") == (1366, 728, False)


def test_aplicar_el_tamano_sin_escritorio_no_explota(monkeypatch):
    """En el navegador y en los tests no hay ventana que redimensionar."""
    monkeypatch.setattr(widget, "_url_base", "")
    assert widget.aplicar_tamano_principal("1600x900") is False


def test_no_se_guarda_la_posicion_de_una_ventana_MINIMIZADA(tmp_path, monkeypatch):
    """⚠️ El bug que dejaba el widget abierto e invisible.

    Windows le pone (-32000, -32000) a una ventana minimizada y pywebview lo dispara como un
    evento `moved`: minimizar el widget guardaba esa posición y al siguiente arranque nacía
    fuera de toda pantalla, con la app diciendo que estaba abierto.
    """
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    monkeypatch.setattr(widget, "_url_base", "http://127.0.0.1:1")
    monkeypatch.setattr(widget, "_pantallas", lambda: [(0, 0, 1920, 1080)])

    widget._al_mover(300, 200)
    assert widget.leer_geometria() == {"x": 300, "y": 200}
    widget._al_mover(-32000, -32000)                       # minimizar
    assert widget.leer_geometria() == {"x": 300, "y": 200}  # la buena sobrevive


def test_una_posicion_que_no_cae_en_ninguna_pantalla_se_descarta(tmp_path, monkeypatch):
    """Vale para el centinela, para el monitor que se desenchufó y para un widget.json ajeno."""
    monkeypatch.setattr(widget, "_pantallas", lambda: [(0, 0, 1920, 1080), (-1920, 0, 1920, 1080)])
    assert widget.posicion_visible(100, 100) is True
    assert widget.posicion_visible(-1800, 300) is True      # el monitor de la izquierda
    assert widget.posicion_visible(-32000, -32000) is False
    assert widget.posicion_visible(4000, 200) is False      # el monitor que ya no está
    assert widget.posicion_visible(1910, 500) is False      # asomando 10px, nada que agarrar


def test_sin_poder_preguntar_por_las_pantallas_igual_se_descarta_el_centinela(monkeypatch):
    monkeypatch.setattr(widget, "_pantallas", lambda: [])
    assert widget.posicion_visible(-32000, -32000) is False
    assert widget.posicion_visible(100, 100) is True


def test_olvidar_posicion_deja_el_tamano(tmp_path, monkeypatch):
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    monkeypatch.setattr(widget, "_url_base", "http://127.0.0.1:1")
    widget.guardar_geometria(x=-32000, y=-32000, w=400, h=600)
    widget.olvidar_posicion()
    assert widget.leer_geometria() == {"w": 400, "h": 600}


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
    assert SETTINGS["widget_autostart"]["default"] == "on"
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
    from bitacora.escritorio import main as desktop
    monkeypatch.setattr(tray, "iniciar", lambda **kw: False)
    monkeypatch.setattr(widget, "abrir", lambda: False)
    db.set_setting("cerrar_a_bandeja", "on")     # aun prendido, no debe engancharse
    v = _VentanaFalsa()
    desktop._al_mostrarse(v)
    assert v.enganchados == []


def test_con_bandeja_si_se_engancha_el_cierre(cliente, monkeypatch):
    from bitacora.escritorio import main as desktop
    monkeypatch.setattr(tray, "iniciar", lambda **kw: True)
    monkeypatch.setattr(widget, "abrir", lambda: False)
    db.set_setting("cerrar_a_bandeja", "on")
    v = _VentanaFalsa()
    desktop._al_mostrarse(v)
    assert len(v.enganchados) == 1


def test_con_bandeja_pero_el_ajuste_apagado_no_engancha(cliente, monkeypatch):
    from bitacora.escritorio import main as desktop
    monkeypatch.setattr(tray, "iniciar", lambda **kw: True)
    monkeypatch.setattr(widget, "abrir", lambda: False)
    db.set_setting("cerrar_a_bandeja", "off")
    v = _VentanaFalsa()
    desktop._al_mostrarse(v)
    assert v.enganchados == []


def test_el_widget_se_abre_solo_con_el_autostart_prendido(cliente, monkeypatch):
    """Default desde sep 2026: el widget arranca con la app. Lo abre _al_mostrarse, que corre
    en el hilo del evento `shown` — el único desde el que create_window crea en el acto."""
    from bitacora.escritorio import main as desktop
    abiertos = []
    monkeypatch.setattr(tray, "iniciar", lambda **kw: False)
    monkeypatch.setattr(widget, "abrir", lambda: abiertos.append(1) or True)

    db.set_setting("widget_autostart", "on")
    desktop._al_mostrarse(_VentanaFalsa())
    assert len(abiertos) == 1

    db.set_setting("widget_autostart", "off")
    desktop._al_mostrarse(_VentanaFalsa())
    assert len(abiertos) == 1          # apagado no abre nada


def test_a_la_bandeja_cancela_el_cierre_y_esconde():
    from bitacora.escritorio import main as desktop

    class V:
        escondida = False
        def hide(self):
            V.escondida = True
    v = V()
    assert desktop._a_la_bandeja(v) is False   # False = cancelar el cierre
    assert V.escondida

def test_si_no_se_puede_esconder_deja_cerrar():
    """Preferible cerrar de verdad antes que quedar con una ventana que no se va ni se ve."""
    from bitacora.escritorio import main as desktop

    class V:
        def hide(self):
            raise RuntimeError("no se pudo")
    assert desktop._a_la_bandeja(V()) is True


# ── Rutinas de hoy en el widget (ajuste widget_rutinas) ─────────────────────

def _rutina_de_hoy():
    """Una rutina diaria, que por definición aplica hoy."""
    db.add_recurring_event({"title": "Caminar", "color": "#22c55e", "recurrence": "daily",
                            "start_date": "2020-01-01", "end_date": ""})
    return db.get_recurring_events()[0]["id"]


def test_el_widget_muestra_las_rutinas_de_hoy(cliente):
    _rutina_de_hoy()
    html = cliente.get("/widget").data.decode()
    assert "Rutinas" in html and "Caminar" in html


def test_con_el_ajuste_apagado_no_aparecen(cliente):
    _rutina_de_hoy()
    db.set_setting("widget_rutinas", "hide")
    html = cliente.get("/widget").data.decode()
    assert "Caminar" not in html


def test_tildar_una_rutina_desde_el_widget(cliente):
    ev = _rutina_de_hoy()
    r = cliente.post(f"/widget/rutina/{ev}/toggle")
    assert r.status_code == 302 and "/widget" in r.headers["Location"]
    assert db.get_completions_range(HOY, HOY).get(HOY)


def test_destildarla_la_deja_como_estaba(cliente):
    """El mismo botón marca y desmarca, como el de las tareas."""
    ev = _rutina_de_hoy()
    cliente.post(f"/widget/rutina/{ev}/toggle")
    cliente.post(f"/widget/rutina/{ev}/toggle")
    assert not db.get_completions_range(HOY, HOY).get(HOY)


def test_el_acceso_a_nota_especial_abre_el_dia(cliente):
    """Las notas especiales no entran en 340px: el camino es abrir el día en la ventana grande."""
    html = cliente.get("/widget?p=nota").data.decode()
    assert "Nota especial" in html
    assert f"/widget/dia/{HOY}" in html


# ── Estirar la ventana ───────────────────────────────────────────────────────
# ⚠️ El widget es `frameless`, y en Windows eso es FormBorderStyle = None: NO tiene borde de
# redimensionado. El `resizable=True` con el que se crea la ventana no hace nada — con el mouse
# no había de dónde agarrarla. El agarre lo pone la página y termina en estas rutas.

def test_el_minimo_de_la_ventana_y_el_del_acotado_son_el_mismo():
    """Son el mismo límite: con dos números sueltos, subir uno dejaba al otro atrás."""
    assert widget._acotar(10, 10) == widget.MIN_WIDGET


def test_redimensionar_devuelve_la_medida_que_aplico(cliente):
    """La página sigue el arrastre desde lo que devuelve la ruta, así el tope vive en un solo
    lado y el agarre no sigue contando por su cuenta una ventana que ya no se achicó más."""
    r = cliente.post("/widget/tamano", data={"w": "480", "h": "700"})
    assert r.status_code == 200 and r.get_json() == {"w": 480, "h": 700}

    chico = cliente.post("/widget/tamano", data={"w": "10", "h": "10"}).get_json()
    assert (chico["w"], chico["h"]) == widget.MIN_WIDGET


def test_una_medida_que_no_es_un_par_de_numeros_no_hace_nada(cliente):
    """Redimensionar a cualquier cosa es peor que no redimensionar."""
    assert cliente.post("/widget/tamano", data={"w": "ancho", "h": "700"}).status_code == 400
    assert cliente.post("/widget/tamano", data={"h": "700"}).status_code == 400


def test_el_doble_clic_vuelve_a_la_medida_de_fabrica(cliente):
    r = cliente.post("/widget/tamano/original")
    assert r.get_json() == {"w": widget.ANCHO, "h": widget.ALTO}


def test_sin_ventana_no_explota(cliente):
    """Modo navegador y tests: como todo el módulo, degrada a no-op."""
    assert widget.esta_abierto() is False
    assert widget.redimensionar(500, 600) == (500, 600)


def test_la_pagina_trae_el_agarre_y_la_medida_de_la_que_parte(cliente):
    html = cliente.get("/widget").data.decode()
    assert 'id="w-grip"' in html
    assert "window.WIDGET_TAMANO = [340, 520]" in html


def test_el_agarre_corta_la_propagacion_del_mousedown():
    """⚠️ Tripwire de un fallo callado: `easy_drag` de pywebview engancha su `mousedown` en
    `window`, así que sin el stopPropagation arrastrar el agarre MOVERÍA la ventana mientras se
    redimensiona — se ve como que el widget se escapa, y no hay error en ningún lado."""
    html = (RAIZ / "bitacora" / "templates" / "widget.html").read_text(encoding="utf-8")
    mousedown = html[html.index("agarre.addEventListener('mousedown'"):]
    assert "e.stopPropagation();" in mousedown[:600]


def test_el_tamano_no_viaja_en_el_sync():
    """Sigue en widget.json, como la posición: una medida elegida en un monitor de 2560 no tiene
    sentido en una laptop de 1366. Es el mismo motivo que dejó las preferencias de vista fuera
    del sync, y por eso tampoco puede aparecer como ajuste ni como preferencia de vista."""
    assert widget.GEOMETRIA == "widget.json"
    assert "widget.json" not in (RAIZ / "bitacora" / "sync.py").read_text(encoding="utf-8")
    assert "widget" not in SETTINGS.get("window_size", {}).get("choices", ())
    from bitacora.appconfig import VISTAS
    assert [c for c in VISTAS["widget"] if "tamano" in c or "grip" in c] == []


def test_mover_y_redimensionar_a_la_vez_no_se_pisan(tmp_path, monkeypatch):
    """⚠️ Los dos que escriben widget.json son manejadores de eventos de la ventana —`moved` y
    `resized`— y llegan JUNTOS: en GTK cada redimensionado viene con su `moved` pegado. Cada uno
    hacía leer-modificar-escribir por su cuenta, así que el que escribía último lo hacía sobre una
    foto vieja y le devolvía al archivo las claves del otro como estaban antes: **mover el widget
    le borraba el tamaño recién elegido**, y al revés. Sin error en ningún lado.

    Lo cazó `hacer.ps1 smoke widget` en Linux, donde los dos eventos llegan de a pares. Acá la
    lectura se hace lenta a propósito: si no, el choque depende de cómo caiga el planificador y
    el test no probaría nada.
    """
    import threading
    import time as _t

    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    monkeypatch.setattr(widget, "_url_base", "http://127.0.0.1:1")   # hay_escritorio()

    real_leer = widget.leer_geometria

    def lenta():
        d = real_leer()
        _t.sleep(0.003)          # ensancha el hueco entre leer y escribir
        return d

    monkeypatch.setattr(widget, "leer_geometria", lenta)
    widget.guardar_geometria(x=0, y=0, w=340, h=520)

    def mover():
        for i in range(30):
            widget.guardar_geometria(x=i, y=i)

    def estirar():
        for i in range(30):
            widget.guardar_geometria(w=300 + i, h=500 + i)

    hilos = [threading.Thread(target=mover), threading.Thread(target=estirar)]
    for t in hilos:
        t.start()
    for t in hilos:
        t.join()

    # Lo último que pidió cada uno tiene que seguir ahí: ninguno pisó al otro con una foto vieja.
    assert real_leer() == {"x": 29, "y": 29, "w": 329, "h": 529}, real_leer()
    assert not list(tmp_path.glob("*.tmp")), "quedó un temporal sin renombrar"
