"""La muerte de una tarea: las animaciones ASCII del borrado.

Son decoración, así que casi todos estos tests son de lo mismo: **que la decoración no se meta en
el camino del borrado**. Una animación que se cuelga, un catálogo vacío o un archivo que no cargó
no pueden dejar una tarea sin borrar después de que confirmaste.
"""
import pathlib
import re

from bitacora import database as db
from bitacora import despedidas
from bitacora.appconfig import SETTINGS

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _leer(*partes):
    return (RAIZ.joinpath(*partes)).read_text(encoding="utf-8")


# ── El catálogo ──────────────────────────────────────────────────────────────

def test_cada_animacion_tiene_varios_cuadros():
    for a in despedidas.DESPEDIDAS:
        assert len(a["cuadros"]) >= 2, a["slug"]


def test_los_cuadros_de_una_animacion_estan_en_la_misma_grilla():
    """⚠️ Un cuadro más angosto o más bajo que el anterior mueve el dibujo entero al pasar, y la
    animación se ve como un temblor. Lo garantiza `_cuadros()`, que normaliza lo que se escribe
    suelto; este test es de que siga haciéndolo."""
    for a in despedidas.DESPEDIDAS:
        grillas = {(len(c.split("\n")), max(len(l) for l in c.split("\n")))
                   for c in a["cuadros"]}
        assert len(grillas) == 1, (a["slug"], grillas)
        # Y que cada línea llegue hasta el borde: si no, las de la derecha no se recortan igual.
        for c in a["cuadros"]:
            anchos = {len(l) for l in c.split("\n")}
            assert len(anchos) == 1, (a["slug"], anchos)


def test_las_lineas_en_blanco_a_proposito_sobreviven():
    """El cuadro 1 de la ola es una línea vacía y después la barra: es lo que la deja abajo. Con
    un `strip()` en vez del salto de línea justo, el dibujo arrancaría una fila más arriba."""
    ola = despedidas.por_slug("ola")
    assert ola["cuadros"][0].split("\n")[0].strip() == ""


def test_las_opciones_del_ajuste_salen_del_catalogo():
    """Sumar una animación tiene que ser una entrada y nada más: una lista copiada en appconfig
    se desincroniza sola, que es de lo que ya vino `TIPOS_GRAFICABLES`."""
    assert SETTINGS["animacion_borrado"]["choices"] == despedidas.OPCIONES
    for a in despedidas.DESPEDIDAS:
        assert a["slug"] in SETTINGS["animacion_borrado"]["choices"]
    assert SETTINGS["animacion_borrado"]["default"] == despedidas.AZAR


def test_un_valor_inventado_no_se_guarda(client, test_db):
    r = client.post("/ajustes/set", data={"key": "animacion_borrado", "value": "godzilla"})
    assert r.status_code == 400
    assert db.get_all_settings()["animacion_borrado"] == despedidas.AZAR


def test_se_puede_apagar(client, test_db):
    assert client.post("/ajustes/set",
                       data={"key": "animacion_borrado", "value": "off"}).status_code == 204
    assert db.get_all_settings()["animacion_borrado"] == "off"


# ── Quién la pide ────────────────────────────────────────────────────────────

FORMULARIOS = re.compile(r"<form[^>]*>", re.S)


def _forms_con_despedida():
    fuera = []
    for f in (RAIZ / "bitacora" / "templates").glob("*.html"):
        for tag in FORMULARIOS.findall(f.read_text(encoding="utf-8")):
            if "data-despedida" in tag:
                fuera.append((f.name, tag))
    return fuera


def test_la_piden_los_dos_formularios_que_borran_una_tarea():
    """El día y el visor de tareas: son los dos lugares donde se borra una tarea."""
    assert sorted(n for n, _ in _forms_con_despedida()) == ["day.html", "todos.html"]


def test_no_la_pide_ningun_otro_borrado():
    """⚠️ Un meteorito arriba de "Eliminar este perfil" es un chiste sobre un borrado grande. Se
    pidió para las tareas: notas, notas especiales y perfiles se borran sin ceremonia."""
    for nombre, tag in _forms_con_despedida():
        assert "todo" in tag, (nombre, tag)


def test_la_pagina_trae_el_catalogo_y_la_elegida(client, test_db):
    html = client.get("/tareas").data.decode()
    assert "window.DESPEDIDAS =" in html and "js/despedidas.js" in html
    assert '"meteorito"' in html
    assert 'window.DESPEDIDA_ELEGIDA = "aleatorio"' in html


def test_el_widget_no_las_trae():
    """Plantilla propia y sin botón de borrar: ahí una tarea se tilda o se edita."""
    assert "despedidas.js" not in _leer("bitacora", "templates", "widget.html")


# ── Que la decoración no se meta en el camino ────────────────────────────────

def test_confirmar_envia_el_formulario_aunque_no_haya_animacion():
    """⚠️ El tripwire principal. `despedidas.js` puede no haber cargado, o el formulario puede no
    pedir animación: en los dos casos el botón del modal tiene que enviar igual. Es el mismo
    criterio que el `onsubmit="return false;"` que ya tiene ese archivo."""
    js = _leer("bitacora", "static", "js", "confirmar.js")
    assert "&& window.despedir) window.despedir(form, enviar);" in js
    assert "else enviar();" in js


def test_la_animacion_tiene_un_tope_de_tiempo_y_va_antes_del_try():
    """Si el reproductor se cuelga —o explota antes de armarse— la tarea se borra igual. El
    `setTimeout` va AFUERA del try justamente para cubrir el segundo caso."""
    js = _leer("bitacora", "static", "js", "despedidas.js")
    cuerpo = js[js.index("window.despedir ="):]
    assert cuerpo.index("setTimeout(unaVez, TOPE_MS);") < cuerpo.index("try {")
    assert "catch (e) {\n      unaVez();" in cuerpo
    # Y una sola vez: el tope y el final de la animación pueden llegar los dos.
    assert "if (hecho) return;" in cuerpo


def test_la_animacion_no_se_come_un_clic():
    """Se dibuja encima de la fila, así que sin esto taparía el botón de al lado."""
    assert "pointer-events: none;" in _leer("bitacora", "static", "css", "base.css")
