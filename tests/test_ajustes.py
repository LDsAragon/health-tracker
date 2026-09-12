"""La pantalla de Ajustes: switches, segmentados, secciones y guardado al instante.

Lo que fija este archivo es que el rediseño no rompió ninguno de los dos caminos de guardado
(el formulario de siempre y el AJAX nuevo) y que no se perdió ningún ajuste en la reescritura
de la plantilla.
"""
import re

import pytest

import database as db
from appconfig import SETTINGS

# Los 16 ajustes por tipo de control. La lista está a mano a propósito: si alguien agrega un
# ajuste a appconfig y no le da un control, `test_los_16_ajustes_tienen_un_control` lo grita.
SWITCHES = {
    "note_form_default": ("open", "collapsed"),
    "journal_form_default": ("open", "collapsed"),
    "todo_notify": ("on", "off"),
    "widget_autostart": ("on", "off"),
    "cerrar_a_bandeja": ("on", "off"),
    "show_todos": ("show", "hide"),
    "show_stats": ("show", "hide"),
    "show_export": ("show", "hide"),
}
SEGMENTADOS = ("date_format", "time_format", "week_start", "start_view",
               "todo_alert", "todo_overdue_from", "pet")
SECCIONES = ("apariencia", "calendario", "tareas", "escritorio", "menu", "detalles")


# ── Leer la página como la leería un navegador ───────────────────────────────

_TAG = re.compile(r"<input\b[^>]*>", re.S)


def _inputs(html, name):
    """Los <input> con ese name, en orden de aparición."""
    fuera = []
    for tag in _TAG.findall(html):
        n = re.search(r'name="([^"]+)"', tag)
        if not n or n.group(1) != name:
            continue
        v = re.search(r'value="([^"]*)"', tag)
        t = re.search(r'type="([^"]+)"', tag)
        fuera.append({
            "type": t.group(1) if t else "text",
            "value": v.group(1) if v else None,
            "checked": "checked" in tag,
        })
    return fuera


def valor_del_form(html, name):
    """Lo que mandaría el formulario para ese ajuste.

    Un radio o un checkbox solo viaja si está marcado; un hidden viaja siempre. Y cuando
    viajan dos, `request.form.get()` devuelve el primero — que es justo el truco del switch.
    """
    for i in _inputs(html, name):
        if i["type"] in ("radio", "checkbox") and not i["checked"]:
            continue
        return i["value"]
    return None


# ── La reescritura no se comió ningún ajuste ─────────────────────────────────

def test_los_16_ajustes_tienen_un_control():
    """El esquema es la fuente única: un ajuste nuevo sin control quedaría invisible."""
    assert set(SWITCHES) | set(SEGMENTADOS) | {"theme"} == set(SETTINGS)


def test_los_16_ajustes_estan_en_la_pagina(client):
    html = client.get("/ajustes").data.decode()
    faltan = [k for k in SETTINGS if not _inputs(html, k)]
    assert faltan == []


@pytest.mark.parametrize("key", sorted(SETTINGS))
def test_cada_ajuste_refleja_su_valor_guardado(client, key):
    """Con un valor no-default guardado, la página tiene que mostrar ESE y no el default."""
    otro = next(v for v in SETTINGS[key]["choices"] if v != SETTINGS[key]["default"])
    db.set_setting(key, otro)
    html = client.get("/ajustes").data.decode()
    assert valor_del_form(html, key) == otro


def test_ningun_ajuste_quedo_como_dropdown(client):
    """La queja que originó el rediseño: prender algo no puede pedir entrar a un <select>."""
    html = client.get("/ajustes").data.decode()
    selects = re.findall(r'<select\b[^>]*name="([^"]+)"', html)
    assert [s for s in selects if s in SETTINGS] == []


def test_el_select_de_borrar_perfil_no_se_toco(client, monkeypatch, tmp_path):
    """El rediseño saca los <select> de *ajustes*; el de elegir perfil es una lista de datos."""
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    import profiles
    profiles.usar(profiles.crear("Principal")["slug"])
    profiles.crear("Segundo")                      # el bloque de borrado pide dos
    html = client.get("/ajustes").data.decode()
    assert 'id="borrar-perfil-slug"' in html


# ── Secciones colapsables ────────────────────────────────────────────────────

@pytest.mark.parametrize("nombre", SECCIONES + ("atajos",))
def test_cada_seccion_es_un_details(client, nombre):
    html = client.get("/ajustes").data.decode()
    assert re.search(r'<details[^>]*id="set-%s"' % nombre, html)


def test_los_atajos_arrancan_cerrados_y_el_resto_abierto(client):
    """Los atajos son una referencia que no se toca; lo demás es lo que el usuario vino a ver."""
    html = client.get("/ajustes").data.decode()
    for n in SECCIONES:
        assert "recordarColapsable('set-' + n, 'setOpen-' + n, true)" in html
    assert "recordarColapsable('set-atajos', 'setOpen-atajos', false)" in html


def test_el_colapsable_es_el_compartido(client):
    """Tercer uso del helper: vive en un .js y no copiado en cada plantilla."""
    assert b"js/colapsables.js" in client.get("/ajustes").data
    assert b"js/colapsables.js" in client.get("/tareas").data


# ── Guardado al instante ─────────────────────────────────────────────────────

def test_set_guarda_y_devuelve_204(client):
    r = client.post("/ajustes/set", data={"key": "theme", "value": "oceano"})
    assert r.status_code == 204
    assert db.get_setting("theme") == "oceano"


def test_set_rechaza_una_clave_desconocida_sin_escribir_nada(client):
    r = client.post("/ajustes/set", data={"key": "no_existe", "value": "x"})
    assert r.status_code == 400
    with db.get_db() as c:
        assert c.execute("SELECT COUNT(*) FROM settings WHERE key='no_existe'").fetchone()[0] == 0


def test_set_rechaza_un_valor_fuera_de_choices_sin_escribir_nada(client):
    r = client.post("/ajustes/set", data={"key": "theme", "value": "fucsia-inventado"})
    assert r.status_code == 400
    assert db.get_setting("theme") == "indigo"


def test_set_sin_parametros_no_explota(client):
    assert client.post("/ajustes/set", data={}).status_code == 400


@pytest.mark.parametrize("key,valor", [("theme", "nope"), ("todo_alert", "gritando"),
                                       ("pet", "dragon"), ("week_start", "wed")])
def test_los_dos_caminos_de_guardado_rechazan_lo_mismo(client, key, valor):
    """La validación sale de un helper único: la previa y el merge del sync ya enseñaron lo
    que pasa cuando dos caminos deciden por separado qué aceptan."""
    antes = db.get_setting(key)
    assert client.post("/ajustes/set", data={"key": key, "value": valor}).status_code == 400
    client.post("/ajustes/guardar", data={key: valor})
    assert db.get_setting(key) == antes


# ── El truco del hidden: el switch sin JS ────────────────────────────────────

@pytest.mark.parametrize("key,on,off", [(k, v[0], v[1]) for k, v in sorted(SWITCHES.items())])
def test_el_switch_sin_marcar_manda_el_valor_apagado(client, key, on, off):
    """Un checkbox sin marcar no manda NADA. Sin el hidden, apagar un switch desde el
    formulario dejaría el ajuste en blanco en vez de apagado."""
    db.set_setting(key, on)
    client.post("/ajustes/guardar", data={key: off})     # lo que manda el navegador
    assert db.get_setting(key) == off


@pytest.mark.parametrize("key,on,off", [(k, v[0], v[1]) for k, v in sorted(SWITCHES.items())])
def test_el_switch_marcado_gana_al_hidden(client, key, on, off):
    """Marcado viajan los dos, y el checkbox va primero en el HTML. Si el orden se invierte,
    prender un switch no prendería nada."""
    db.set_setting(key, off)
    client.post("/ajustes/guardar", data={key: [on, off]})
    assert db.get_setting(key) == on


@pytest.mark.parametrize("key,on,off", [(k, v[0], v[1]) for k, v in sorted(SWITCHES.items())])
def test_el_checkbox_va_antes_del_hidden_en_el_html(client, key, on, off):
    html = client.get("/ajustes").data.decode()
    tipos = [i["type"] for i in _inputs(html, key)]
    assert tipos == ["checkbox", "hidden"]


# ── El camino sin JS sigue entero ────────────────────────────────────────────

def test_el_boton_guardar_sigue_en_la_plantilla(client):
    """Lo esconde ajustes.js. Si se borrara de la plantilla, un JS roto dejaría los ajustes
    imposibles de cambiar."""
    html = client.get("/ajustes").data.decode()
    assert "set-guardar-fallback" in html
    assert 'action="/ajustes/guardar"' in html


def test_guardar_el_formulario_completo_sigue_andando(client):
    datos = {k: next(v for v in SETTINGS[k]["choices"] if v != SETTINGS[k]["default"])
             for k in SETTINGS}
    r = client.post("/ajustes/guardar", data=datos)
    assert r.status_code == 302
    for k, v in datos.items():
        assert db.get_setting(k) == v


# ── Los que cambian el navbar necesitan recargar ─────────────────────────────

@pytest.mark.parametrize("key", ["show_todos", "show_stats", "show_export", "todo_alert"])
def test_los_que_cambian_el_navbar_piden_recarga(client, key):
    """El navbar se renderiza en el servidor: guardar sin recargar persiste el ajuste pero el
    tab no aparece, y se lee como que no pasó nada."""
    html = client.get("/ajustes").data.decode()
    fila = re.search(r'<div class="set-row[^"]*"([^>]*)>(?:(?!</div>\s*</div>).)*?name="%s"' % key,
                     html, re.S)
    assert fila and "data-recargar" in fila.group(1)


def test_el_widget_no_anida_un_formulario(client):
    """Anidar <form> es HTML inválido y el navegador se come el de adentro: el botón de abrir
    el widget apunta por id a un form de afuera."""
    html = client.get("/ajustes").data.decode()
    assert 'form="abrir-widget-form"' in html
    assert html.index('id="ajustes-form"') < html.index('id="abrir-widget-form"')
    dentro = html[html.index('id="ajustes-form"'):html.index("</form>")]
    assert "<form" not in dentro
