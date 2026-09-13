"""Las confirmaciones son de la app, no del navegador.

El `confirm()` nativo aparecía en la ventana de escritorio encabezado por "127.0.0.1:65015 dice".
Eran 16 en 8 pantallas, todos con la misma forma, y ahora los maneja `static/js/confirmar.js` a
partir de lo que declara cada formulario.

Estos tests leen las **plantillas**, no las rutas: así cubren los 16 casos sin tener que armar los
datos que hace falta para que cada botón aparezca (dos perfiles, un gráfico, una previa de sync).
"""
import pathlib
import re

import pytest

RAIZ = pathlib.Path(__file__).resolve().parent.parent
PLANTILLAS = sorted((RAIZ / "bitacora" / "templates").glob("*.html"))
# `confirmar.js` queda afuera: es el que implementa el reemplazo y nombra lo que reemplazó.
SCRIPTS = [p for p in sorted((RAIZ / "bitacora" / "static" / "js").glob("*.js"))
           if p.name != "confirmar.js"]


def _texto(p):
    return p.read_text(encoding="utf-8")


# ── El tripwire ──────────────────────────────────────────────────────────────

@pytest.mark.parametrize("plantilla", PLANTILLAS, ids=lambda p: p.name)
def test_ninguna_plantilla_usa_los_dialogos_del_navegador(plantilla):
    """`confirm()`, `alert()` y `prompt()` son del navegador y se ven como tal: en la ventana de
    escritorio salen con el "127.0.0.1:xxxxx dice" encima. Lo que hay que usar es
    `data-confirmar`.
    """
    codigo = [l for l in _texto(plantilla).splitlines()
              if not l.strip().startswith(("{#", "//", "*"))]
    culpables = [l.strip()[:70] for l in codigo
                 if re.search(r"(?<![\w.])(confirm|alert|prompt)\s*\(", l)]
    assert culpables == [], f"{plantilla.name} usa un diálogo del navegador: {culpables}"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda p: p.name)
def test_ningun_script_usa_los_dialogos_del_navegador(script):
    """El JS también: quedaba un `alert('Seleccioná una categoría.')` en `day.js`. Una validación
    de formulario va **inline, al lado de lo que falta completar** (como el `#weekday-error` de
    Rutinas), no en un diálogo — y menos en uno que el usuario lee como del navegador.
    """
    codigo = [l for l in _texto(script).splitlines() if not l.strip().startswith(("//", "*", "/*"))]
    culpables = [l.strip()[:70] for l in codigo
                 if re.search(r"(?<![\w.])(confirm|alert|prompt)\s*\(", l)]
    assert culpables == [], f"{script.name} usa un diálogo del navegador: {culpables}"


def test_la_categoria_de_una_nota_especial_se_valida_inline(client):
    """⚠️ La categoría se elige con chips y viaja en un `<input type="hidden">`, y a un hidden no
    le aplica `required`: la validación es a mano y por eso es fácil que vuelva como diálogo.
    """
    import json

    from bitacora import database as db
    db.add_journal_category({"name": "Emociones", "color": "#6366f1", "show_in_calendar": 1,
                             "fields_json": json.dumps([{"label": "Qué sentí", "type": "text",
                                                         "placeholder": ""}])})
    html = client.get("/day/2026-06-10").data.decode()
    assert 'id="jday-cat-error"' in html
    assert "Elegí una categoría" in html


# ── La guarda que evita borrar sin preguntar ─────────────────────────────────

def _forms_con_confirmar():
    """Cada `<form>` que declara una confirmación, con su etiqueta de apertura completa."""
    encontrados = []
    for p in PLANTILLAS:
        for m in re.finditer(r"<form\b[^>]*>", _texto(p), re.S):
            if "data-confirmar" in m.group(0):
                encontrados.append((p.name, m.group(0)))
    return encontrados


def test_hay_formularios_con_confirmacion():
    """Si esto da cero, los tests de abajo no estarían probando nada."""
    assert len(_forms_con_confirmar()) >= 16


@pytest.mark.parametrize("caso", _forms_con_confirmar(),
                         ids=[f"{n}:{t[:40]}" for n, t in _forms_con_confirmar()])
def test_todo_formulario_con_confirmacion_lleva_la_guarda(caso):
    """⚠️ El `onsubmit="return false;"` es el fallback y no se puede sacar.

    El `confirm()` nativo lo ponía el navegador, así que aparecía aunque el JS de la app estuviera
    roto. Con un modal propio sin esta guarda, un JS roto enviaría el formulario **sin preguntar
    nada** — y varios de estos borran datos (vaciar perfil, eliminar perfil, borrar todos,
    restaurar un backup). Que sin JS no se pueda borrar es aceptable; que borre sin preguntar, no.
    """
    nombre, tag = caso
    assert 'onsubmit="return false;"' in tag, (
        f"{nombre}: un formulario con data-confirmar sin la guarda del onsubmit")


@pytest.mark.parametrize("caso", _forms_con_confirmar(),
                         ids=[f"{n}:{t[:40]}" for n, t in _forms_con_confirmar()])
def test_cada_confirmacion_dice_que_va_a_pasar(caso):
    """El botón nombra la acción ("Eliminar", "Vaciar el perfil") en vez de un "Aceptar" genérico,
    que era lo único que podía ofrecer el diálogo del navegador."""
    nombre, tag = caso
    assert "data-confirmar-ok=" in tag, f"{nombre}: confirmación sin texto de botón"


def test_los_mensajes_con_parrafos_no_llevan_escapes_de_javascript():
    """⚠️ Los `\\n` venían de los `confirm()`, donde eran saltos de línea de JavaScript. En un
    atributo HTML no significan nada: se verían como el texto literal `\\n`. Van como `&#10;`.
    """
    culpables = [f"{n}: {t[:60]}" for n, t in _forms_con_confirmar() if "\\n" in t]
    assert culpables == []


# ── Las piezas compartidas ───────────────────────────────────────────────────

def test_base_trae_el_modal_y_el_script():
    base = _texto(RAIZ / "bitacora" / "templates" / "base.html")
    for pieza in ('id="confirmar-modal"', 'id="confirmar-texto"', 'id="confirmar-ok"',
                  'id="confirmar-no"', "js/confirmar.js"):
        assert pieza in base, f"base.html perdió {pieza}"


def test_el_modal_tiene_estilo():
    css = _texto(RAIZ / "bitacora" / "static" / "css" / "pages.css")
    assert ".confirmar-texto" in css


def test_las_confirmaciones_viven_donde_esta_el_modal():
    """⚠️ `widget.html` es plantilla propia: no hereda de `base.html`, así que no tiene el modal
    ni carga el script. Un `data-confirmar` ahí no haría nada y, con la guarda del onsubmit, el
    formulario simplemente no se enviaría.
    """
    widget = _texto(RAIZ / "bitacora" / "templates" / "widget.html")
    assert "data-confirmar" not in widget


def _sembrar(fecha="2026-06-10"):
    """Los botones de borrar solo existen si hay algo que borrar."""
    import json

    from bitacora import database as db
    db.add_note(fecha, "una nota")
    db.add_todo(fecha, "una tarea")
    db.add_recurring_event({"title": "Gimnasio", "color": "#22c55e", "recurrence": "daily",
                            "start_date": "2020-01-01", "end_date": ""})
    db.add_journal_category({"name": "Emociones", "color": "#6366f1", "show_in_calendar": 1,
                             "fields_json": json.dumps([{"label": "Qué sentí", "type": "text",
                                                         "placeholder": ""}])})


@pytest.mark.parametrize("ruta", ["/day/2026-06-10", "/export", "/tareas", "/recurring",
                                  "/journal"])
def test_las_pantallas_sirven_la_confirmacion_renderizada(client, ruta):
    """Que Jinja no haya roto el atributo al renderizar (comillas, entidades)."""
    _sembrar()
    html = client.get(ruta, follow_redirects=True).data.decode()
    assert "data-confirmar=" in html, f"{ruta} no renderizó ninguna confirmación"
    assert 'onsubmit="return false;"' in html
    assert "confirm(" not in html


def test_los_parrafos_llegan_como_saltos_de_linea(client):
    """La entidad `&#10;` tiene que sobrevivir al render: es lo que separa los párrafos del
    mensaje de vaciar el perfil."""
    html = client.get("/export").data.decode()
    assert "&#10;" in html
    # La secuencia literal barra-ene (dos caracteres), que es como se vería un escape de JS
    # sobreviviendo al atributo.
    assert "\\n" not in html.split("data-confirmar=")[1][:400]
