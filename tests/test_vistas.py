"""Preferencias de vista: cómo dejaste acomodada cada pantalla.

Vivían en `localStorage` y la app de escritorio las perdía en CADA arranque (el origen incluye el
puerto y el puerto cambia siempre). Ahora viven en la base, por perfil.
"""
import pathlib
import re

from bitacora import database as db
from bitacora.appconfig import VISTAS
from bitacora.database.schema import SYNCABLE

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _leer(*partes):
    return (RAIZ.joinpath(*partes)).read_text(encoding="utf-8")


# ── El almacén ───────────────────────────────────────────────────────────────

def test_guardar_y_leer_una_preferencia(test_db):
    assert db.set_pref("dia", "day_side_width", "520") is True
    assert db.get_prefs()["day_side_width"] == "520"


def test_guardar_dos_veces_la_misma_clave_no_duplica(test_db):
    db.set_pref("dia", "day_side_width", "520")
    db.set_pref("dia", "day_side_width", "480")
    assert db.get_prefs() == {"day_side_width": "480"}


def test_una_clave_que_no_es_de_esa_vista_no_se_guarda(test_db):
    """Lo que llega del navegador no se guarda a ciegas: el registro de `VISTAS` es la whitelist,
    igual que `valor_valido()` con los ajustes."""
    assert db.set_pref("dia", "app_zoom", "2") is False
    assert db.set_pref("dia", "inventada", "x") is False
    assert db.get_prefs() == {}


def test_los_colapsables_de_rutinas_entran_por_prefijo(test_db):
    """Son uno por rutina (`recOpen-<id>`), así que no se pueden enumerar en el registro."""
    assert db.set_pref("rutinas", "recOpen-12", "1") is True
    assert db.set_pref("rutinas", "recOpen-", "1") is False


def test_reiniciar_una_vista_no_toca_las_otras(test_db):
    """Es la razón de ser de la columna `vista`: reiniciar el layout del día no puede llevarse
    puesto cómo dejaste Tareas."""
    db.set_pref("dia", "day_side_width", "520")
    db.set_pref("dia", "day_alto_tareas", "600")
    db.set_pref("tareas", "todosResumenOpen", "1")
    assert db.reset_vista("dia") == 2
    assert db.get_prefs() == {"todosResumenOpen": "1"}


def test_borrar_una_sola_preferencia(test_db):
    """El doble clic en un agarre: vuelve al ancho del CSS sin tocar el resto de la vista."""
    db.set_pref("dia", "day_side_width", "520")
    db.set_pref("dia", "day_alto_tareas", "600")
    db.borrar_pref("dia", "day_side_width")
    assert db.get_prefs() == {"day_alto_tareas": "600"}


def test_las_claves_no_se_repiten_entre_vistas():
    """La página recibe las preferencias como un mapa plano `{clave: valor}`, así que dos vistas
    con la misma clave se pisarían al leer."""
    todas = [c for claves in VISTAS.values() for c in claves]
    assert len(todas) == len(set(todas))


# ── Las dos cosas que romperían algo en silencio ─────────────────────────────

def test_la_tabla_no_sincroniza(test_db):
    """⚠️ Un ancho elegido en un monitor de 2560 no puede aterrizar en una laptop de 1366. Mismo
    motivo por el que la geometría del widget vive en `widget.json` y no en `settings`."""
    assert "vista_prefs" not in SYNCABLE
    sync = _leer("bitacora", "sync.py")
    assert "vista_prefs" not in sync


def test_guardar_una_preferencia_no_mueve_el_token_de_refresco(test_db):
    """⚠️ Si la tabla alimentara `token_datos()`, plegar un desplegable en una ventana recargaría
    la otra a los 3 segundos — el bug que ya tuvo esta feature, visto desde otro lado."""
    antes = db.token_datos()
    db.set_pref("tareas", "todosResumenOpen", "1")
    assert db.token_datos() == antes


def test_ninguna_preferencia_sigue_yendo_a_localStorage():
    """Tripwire de la mudanza: una sola que quede escribiendo en localStorage se pierde en cada
    arranque y nadie se entera, porque la pantalla se ve bien."""
    archivos = list((RAIZ / "bitacora" / "static" / "js").glob("*.js"))
    archivos += list((RAIZ / "bitacora" / "templates").glob("*.html"))
    for f in archivos:
        if "vendor" in f.parts:
            continue
        for linea in f.read_text(encoding="utf-8").splitlines():
            if linea.strip().startswith("//") or linea.strip().startswith("{#"):
                continue
            assert "localStorage." not in linea, f"{f.name}: {linea.strip()}"


def test_toda_pantalla_con_preferencias_declara_su_vista():
    """Sin el `{% block vista %}`, la pantalla cae en la vista "app" y sus preferencias se
    guardarían con la clave equivocada — o se rechazarían y no se guardaría nada. Es el mismo
    fallo callado que "una pantalla a medio marcar" del refresco."""
    for f in (RAIZ / "bitacora" / "templates").glob("*.html"):
        texto = f.read_text(encoding="utf-8")
        usa = re.search(r"recordarColapsable\(|prefGuardar\(", texto)
        if not usa or f.name in ("base.html", "widget.html"):
            continue
        assert "{% block vista %}" in texto, f.name


# ── Las rutas ────────────────────────────────────────────────────────────────

def test_ruta_set_guarda_y_rechaza(client, test_db):
    r = client.post("/vista/set", data={"vista": "dia", "clave": "day_side_width", "valor": "520"})
    assert r.status_code == 204
    assert db.get_prefs()["day_side_width"] == "520"

    r = client.post("/vista/set", data={"vista": "dia", "clave": "app_zoom", "valor": "2"})
    assert r.status_code == 400


def test_ruta_reiniciar_se_lleva_la_vista_y_el_zoom(client, test_db):
    """El zoom es de toda la app, así que reiniciar una vista también lo devuelve a 1. Se pidió
    así, y por eso el texto del menú lo dice en vez de sorprender."""
    db.set_pref("dia", "day_side_width", "520")
    db.set_pref("app", "app_zoom", "1.4")
    db.set_pref("tareas", "todosResumenOpen", "1")

    r = client.post("/vista/reiniciar", data={"vista": "dia"})
    assert r.status_code == 204
    assert db.get_prefs() == {"todosResumenOpen": "1"}


def test_ruta_reiniciar_rechaza_una_vista_inventada(client, test_db):
    r = client.post("/vista/reiniciar", data={"vista": "todas"})
    assert r.status_code == 400


def test_la_pagina_trae_las_preferencias_y_la_vista(client, test_db):
    """La lectura es síncrona —el valor ya viene en la página— y por eso el zoom no parpadea."""
    db.set_pref("dia", "day_side_width", "520")
    html = client.get("/day/2026-06-09").data.decode()
    assert 'data-vista="dia"' in html
    assert '"day_side_width": "520"' in html or '"day_side_width":"520"' in html


def test_un_colapsable_no_guarda_su_propio_default(client, test_db):
    """⚠️ Setear `.open` a mano dispara el evento `toggle`, así que la pantalla guardaba su default
    apenas la abrías. Ahora esas escrituras son HTTP, y encima hacían que "reiniciar esta vista"
    se deshiciera solo en la recarga siguiente. La guarda vive en colapsables.js."""
    js = _leer("bitacora", "static", "js", "colapsables.js")
    assert "if (valor === actual || (actual === null && d.open === abiertoPorDefecto)) return;" in js


# ── El menú del clic derecho ─────────────────────────────────────────────────

def test_toda_pantalla_trae_el_menu_contextual(client, test_db):
    # "/" redirige a la vista de inicio configurada, así que se piden las pantallas de verdad.
    for url in ("/calendar/2026/6", "/day/2026-06-09", "/tareas", "/ajustes",
                "/estadisticas", "/journal"):
        assert b"js/menu-contextual.js" in client.get(url).data, url


def test_el_widget_no_trae_el_menu(client, test_db):
    """Plantilla propia: no hereda de base.html, y en 340px un menú no tiene dónde caer."""
    assert b"js/menu-contextual.js" not in client.get("/widget").data


def test_el_menu_no_se_come_el_de_pegar_ni_el_de_copiar():
    """⚠️ Interceptar el clic derecho en toda la página cuesta *pegar* y *copiar*, que en el modo
    navegador se usan todos los días. La guarda es lo que hace aceptable el menú propio."""
    js = _leer("bitacora", "static", "js", "menu-contextual.js")
    assert "input, textarea, select, [contenteditable=" in js      # pegar
    assert "if (sel && String(sel).trim()) return;" in js          # copiar


def test_el_reiniciar_del_menu_recarga_recien_cuando_el_borrado_llego():
    """Si recargara sin esperar, la página volvería a renderizarse con las preferencias que
    todavía no se borraron y el reinicio se vería como que no hizo nada."""
    js = _leer("bitacora", "static", "js", "menu-contextual.js")
    assert "window.prefReiniciarVista().then(() => location.reload())" in js


def test_la_pagina_dice_adonde_va_una_emocion(client, test_db):
    """El menú vive en todas las pantallas, así que el destino se inyecta con la página."""
    import json as _json
    db.add_journal_category({"name": "Emociones", "color": "#ec4899", "show_in_calendar": 1,
                             "fields_json": _json.dumps([{"label": "Emoción",
                                                          "type": "emotion-wheel"}])})
    html = client.get("/tareas").data.decode()
    # tojson escapa los no-ASCII, así que la clave viaja escapada: se busca tal cual sale.
    assert r'"campo": "Emoci\u00f3n"' in html


def test_sin_categoria_con_rueda_la_pagina_no_ofrece_el_atajo(client, test_db):
    html = client.get("/tareas").data.decode()
    assert "window.EMOCION_DESTINO = null" in html
    js = _leer("bitacora", "static", "js", "menu-contextual.js")
    assert "if (DESTINO) {" in js            # sin destino, los dos ítems no se arman


def test_la_emocion_se_lee_del_mismo_picker_que_el_dia():
    """Reusar `buildEWPicker` es lo que evita una segunda forma de leer la selección de la rueda:
    dos lectores del mismo widget divergen, como ya pasó con el marcado de las filas de campos."""
    js = _leer("bitacora", "static", "js", "menu-contextual.js")
    assert "buildEWPicker(DESTINO.campo)" in js
    assert "openEWModal(picker, rueda)" in js
