"""La muerte de una tarea: las animaciones ASCII del borrado.

Son decoración, así que casi todos estos tests son de lo mismo: **que la decoración no se meta en
el camino del borrado**. Una animación que se cuelga, un catálogo vacío o un archivo que no cargó
no pueden dejar una tarea sin borrar después de que confirmaste.
"""
import pathlib
import re

import pytest

from bitacora import database as db
from bitacora import despedidas
from bitacora.appconfig import SETTINGS

RAIZ = pathlib.Path(__file__).resolve().parent.parent


def _leer(*partes):
    return (RAIZ.joinpath(*partes)).read_text(encoding="utf-8")


# ── El catálogo ──────────────────────────────────────────────────────────────

def test_cada_animacion_tiene_su_coreografia():
    """⚠️ El catálogo de Python dice qué se puede elegir; el JS dice cómo se dibuja. Una animación
    elegible en Ajustes **sin coreografía** es un ajuste que no hace nada: se guarda, el chip queda
    marcado y al borrar no pasa nada. El fallo callado de siempre."""
    js = _leer("bitacora", "static", "js", "despedidas.js")
    bloque = js[js.index("const COREOGRAFIAS = {"):js.index("// ── El reproductor")]
    en_js = set(re.findall(r"^    (\w+): function \(e, tl\)", bloque, re.M))
    assert en_js == set(despedidas.SLUGS), (en_js, despedidas.SLUGS)


def test_todos_los_bichos_tienen_cuadros_propios():
    """El movimiento lo dan las transformaciones, pero el bicho además se anima por dentro: la
    mandíbula que se abre, la cresta que rompe, la estela que titila. Es la mitad que faltaba para
    poder usar arte de las galerías de ASCII animado (o el propio, hecho con ASCII Motion)."""
    js = _leer("bitacora", "static", "js", "despedidas.js")
    bloque = js[js.index("const COREOGRAFIAS = {"):js.index("// ── El reproductor")]
    for slug in despedidas.SLUGS:
        cuerpo = bloque[bloque.index(slug + ": function (e, tl)"):]
        cuerpo = cuerpo[:cuerpo.index("return tl")]
        # `pintar` es `cuadros` con el arte convertido por delante: las dos pintan un plano.
        assert ("cuadros(e, e.capas[" in cuerpo or "pintar(e, e.capas[" in cuerpo), slug


def test_cada_animacion_tiene_su_destruccion():
    """La escena y lo que le pasa al texto van separados: la escena es el planteo y `DESTRUCCION`
    es el golpe. Una escena sin su destrucción dejaría la tarea intacta en pantalla."""
    js = _leer("bitacora", "static", "js", "despedidas.js")
    bloque = js[js.index("const DESTRUCCION = {"):js.index("// ── El reproductor")]
    en_js = set(re.findall(r"^    (\w+): function \(e, tl\)", bloque, re.M))
    assert en_js == set(despedidas.SLUGS), (en_js, despedidas.SLUGS)


def test_la_escena_tiene_planos_y_camara():
    """Los planos son lo que da profundidad —el cielo lejos y quieto, el meteorito cerca— y la
    cámara es lo que convierte un dibujo que se mueve en un golpe. Sin esto, cada animación vuelve
    a ser un solo bicho cruzando la pantalla, que es de donde se venía."""
    html = _leer("bitacora", "templates", "base.html")
    for n in (0, 1, 2):
        assert 'id="despedida-capa%d"' % n in html, n
    assert 'id="despedida-flash"' in html

    js = _leer("bitacora", "static", "js", "despedidas.js")
    assert "function sacudir(e, tl" in js and "function destello(e, tl" in js
    # El temblor sacude la ESCENA entera, no el dibujo: si sacudiera el dibujo no sería un temblor.
    assert "targets: e.caja, keyframes: pasos" in js

    css = _leer("bitacora", "static", "css", "base.css")
    assert ".despedida-flash" in css
    # ⚠️ El destello tapa toda la escena: sin esto se comería el clic de lo que haya abajo.
    flash = css[css.index(".despedida-flash"):]
    assert "pointer-events: none;" in flash[:400]


# ⚠️ Medidos EN EL NAVEGADOR, en la fuente del bicho (16 caracteres seguidos, en px):
#     ~ ≈ V _ ‾ ▲ x . · '  →  228.72   ← la grilla
#     ∼ (U+223C)          →  296.36   un 30% más ancho
#     ⌓ (U+2313)          →  398.53
#     ☄ (U+2604)          →  378.63
# Un carácter fuera de la grilla hace que el dibujo TIEMBLE al cambiar de cuadro. Ya pasó: la
# estela del tiburón y la ola mezclaban `~` con `∼`.
GRILLA = {"·", "‾", "≈", "▲"}
# Excepción medida y aceptada: va sola al final de su línea y está en TODOS los cuadros por
# igual, así que corre el dibujo pero no lo hace temblar.
FUERA_DE_GRILLA_OK = {"☄"}


def _cuadros_del_arte():
    """Los literales de los `cuadros(e, capa, [...])`, que es donde vive el dibujo.

    Se lee por líneas y no con una expresión regular: el arte está lleno de barras invertidas
    (las mandíbulas, la estela del meteorito) y un patrón que las contemple es justo el tipo de
    cosa que se rompe sola. Los cuadros grandes se escriben como varias líneas concatenadas con
    `+`, así que cada una cuenta por separado: para lo que se mira acá —qué caracteres usa— da
    exactamente igual.
    """
    fuera = []
    dentro = False
    for linea in _leer("bitacora", "static", "js", "despedidas.js").splitlines():
        t = linea.strip()
        if t.startswith("cuadros(e, e.capas[") or "pintar(e, e.capas[" in t:
            dentro = True
        elif dentro and t.startswith("],"):
            dentro = False
        elif dentro and t.startswith("'"):
            fuera.append(t.rstrip("+").strip().rstrip(",").strip("'"))
    return fuera


def test_el_arte_no_usa_escapes(  ):
    """El dibujo tiene que leerse EN el archivo. Escrito con el escape de JavaScript es correcto para el
    navegador e ilegible para quien lo edita, que es justo lo contrario de lo que se busca."""
    assert _cuadros_del_arte(), "no se encontro ningun cuadro"
    for cuadro in _cuadros_del_arte():
        assert (chr(92) + "u") not in cuadro, cuadro


def test_el_arte_respeta_la_grilla_del_monoespaciado():
    """⚠️ El fallo es visual y callado: un carácter más ancho que los demás corre la fila y el
    dibujo tiembla al pasar de cuadro. Los anchos están medidos arriba."""
    for cuadro in _cuadros_del_arte():
        for c in cuadro:
            if ord(c) > 127:
                assert c in GRILLA or c in FUERA_DE_GRILLA_OK,                     "U+%04X (%s) no esta medido: ver GRILLA" % (ord(c), c)


def test_los_cuadros_los_manda_la_linea_de_tiempo():
    """⚠️ Antes cada plano corría con su `setInterval`, y eso tenía dos problemas. El visible: de
    un GIF de varios segundos se veía un bucle corto mientras la escena duraba el triple —había
    muchísimo más material del que se mostraba—. El callado: un intervalo que quedara vivo sobre
    una página que se está yendo, y el borrado recarga la página.

    Con los cuadros colgados del `update` de la línea de tiempo los dos desaparecen, y además
    buscar un instante con `seek()` muestra el cuadro que corresponde.
    """
    js = _leer("bitacora", "static", "js", "despedidas.js")
    for linea in js.splitlines():
        if linea.strip().startswith("//"):
            continue          # el comentario que explica por qué ya no hay ninguno
        assert "setInterval" not in linea, "volvio un reloj suelto: " + linea.strip()
    assert "update: function (anim) { avanzarCuadros(e, anim); }" in js
    # El convertido va una sola vez a lo largo de la escena; el de a mano sigue en bucle.
    assert "Math.min(n - 1, Math.floor(p * n))" in js


def test_el_texto_que_se_destruye_es_el_de_la_tarea():
    """Es el pedido: el render de la tarea siendo destruido, no un dibujo al lado. Las dos
    pantallas que borran una tarea la muestran en un `.todo-text`."""
    js = _leer("bitacora", "static", "js", "despedidas.js")
    assert "querySelector('.todo-text')" in js
    for plantilla in ("day.html", "todos.html"):
        assert 'class="todo-text"' in _leer("bitacora", "templates", plantilla), plantilla


def test_cada_letra_es_un_elemento():
    """Es lo que deja que cada una se vaya por su lado. Y el espacio va como espacio duro: un
    inline-block con un espacio normal mide cero y la frase se vería toda pegada."""
    js = _leer("bitacora", "static", "js", "despedidas.js")
    assert "ch === ' ' ? NBSP : ch" in js
    assert "const NBSP = String.fromCharCode(160);" in js
    css = _leer("bitacora", "static", "css", "base.css")
    assert ".despedida-l" in css and "display: inline-block;" in css
    # Sin perspective, los rotateX/rotateY se ven aplastados y no hay 3D.
    assert "perspective:" in css


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
    """El bicho se dibuja encima del texto, así que sin esto taparía lo que hay abajo."""
    assert "pointer-events: none;" in _leer("bitacora", "static", "css", "base.css")


def test_la_escena_y_el_motor_viajan_con_la_pagina(client, test_db):
    """El modal vive en base.html —lo necesitan las tres pantallas— y anime.js se carga ahí y no
    en el widget, que no tiene borrado. Mismo criterio que Chart.js, que solo lo trae stats."""
    html = client.get("/tareas").data.decode()
    assert 'id="despedida-modal"' in html and 'id="despedida-texto"' in html
    assert "js/vendor/anime.min.js" in html
    assert "anime.min.js" not in _leer("bitacora", "templates", "widget.html")


def test_escape_termina_la_animacion_en_vez_de_cancelarla():
    """⚠️ Ya confirmaste el borrado: si Escape cancelara, la tarea quedaría sin borrar después de
    haber dicho que sí. Y corta la propagación para que el handler global de base.html no te
    saque de la pantalla en el medio."""
    js = _leer("bitacora", "static", "js", "despedidas.js")
    bloque = js[js.index("ev.key === 'Escape'"):]
    assert "ev.stopPropagation();" in bloque[:200]
    assert "cerrarActual();" in bloque[:200]


# ── Que el archivo al menos PARSEE ─────────────────────────────────────────────

def test_todo_el_javascript_de_la_app_parsea():
    """⚠️ Dos veces quedó `despedidas.js` con un error de sintaxis y la suite entera siguió en
    verde: los tests leen los archivos como texto, así que un JS roto les da igual. En la app eso
    es una pantalla que se ve perfecta y una feature que no existe —el modal no abría y el
    borrado seguía andando por el camino de respaldo, que es justo el fallo callado de siempre—.

    Se saltea si no hay node: es una herramienta de desarrollo, no un requisito para correr.
    """
    import shutil
    import subprocess

    node = shutil.which("node")
    if not node:
        pytest.skip("sin node: el chequeo de sintaxis es opcional")

    rotos = []
    for f in sorted((RAIZ / "bitacora" / "static" / "js").rglob("*.js")):
        r = subprocess.run([node, "--check", str(f)], capture_output=True, text=True)
        if r.returncode:
            primera = (r.stderr or "").strip().splitlines()
            rotos.append("%s: %s" % (f.name, primera[3] if len(primera) > 3 else primera[:1]))
    assert rotos == [], rotos
