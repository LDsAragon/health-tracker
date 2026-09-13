"""La ventana grande y el widget se enteran de los cambios de la otra.

El mecanismo es un token de "versión de los datos" que las dos poletean. Lo que fija este
archivo es que el token se mueva cuando tiene que moverse y se quede quieto cuando no — si se
moviera solo, las dos ventanas se recargarían para siempre.
"""

import pytest

from bitacora import database as db


def test_el_token_no_se_mueve_solo(client):
    """Si cambiara entre dos lecturas sin escrituras, las ventanas se recargarían en loop."""
    assert db.token_datos() == db.token_datos()


def test_el_token_no_se_mueve_entre_REQUESTS(client):
    """⚠️ EL test de esta feature, y el que faltaba cuando el bug se publicó.

    La primera versión del token salía del `os.stat` del `.db` y del `-wal`, y llamarlo dos veces
    en el mismo proceso (el test de arriba) daba estable. Pero cada request abre y cierra
    conexiones, y **al cerrarse la última conexión de una base en WAL, SQLite hace checkpoint y
    BORRA el `-wal`**: que el archivo exista en el momento del stat era una carrera, el token
    alternaba y las dos ventanas se recargaban cada 3 segundos para siempre.

    Pedirlo por HTTP varias veces es lo único que reproduce esas conexiones abriéndose y
    cerrándose.
    """
    tokens = {client.get("/refresco").data for _ in range(12)}
    assert len(tokens) == 1, f"el token se movió sin escribir nada: {tokens}"


def test_el_token_no_se_mueve_navegando(client):
    """Cada página calcula el token en el context processor, así que navegar también abre y
    cierra conexiones. Tampoco puede moverlo."""
    inicial = client.get("/refresco").data
    for ruta in ("/calendar/2026/6", "/widget", "/tareas", "/day/2026-06-10", "/ajustes"):
        client.get(ruta)
        assert client.get("/refresco").data == inicial, f"{ruta} movió el token"


def test_el_token_cambia_al_escribir(client):
    antes = db.token_datos()
    db.add_note("2026-06-10", "una nota")
    assert db.token_datos() != antes


def test_el_token_cambia_al_tildar_una_tarea(client):
    db.add_todo("2026-06-10", "algo")
    tid = db.get_todos_for_date("2026-06-10")[0]["id"]
    # ⚠️ Es el único caso donde el alta y el cambio caen sobre la MISMA tabla, y `updated_at`
    # tiene resolución de milisegundos: si las dos operaciones entran en el mismo, el token no
    # se mueve y el test falla por timing y no por comportamiento (falló así una vez en la suite
    # completa). Se envejece la fila a mano —el trigger de UPDATE respeta un `updated_at`
    # explícito, que es como entra el merge del sync— para que la comparación sea determinista.
    with db.get_db() as conn:
        conn.execute("UPDATE todos SET updated_at = '2020-01-01 00:00:00.000' WHERE id = ?",
                     (tid,))
    antes = db.token_datos()
    db.toggle_todo(tid)
    assert db.token_datos() != antes


def test_el_token_NO_depende_de_los_archivos(client):
    """⚠️ La invariante que se rompió cuando el token salía de `os.stat`.

    Tocar las mtimes del `.db` y del `-wal` no puede mover el token: son justo los que cambian
    solos cuando SQLite abre, cierra y hace checkpoint, y por eso las ventanas se recargaban sin
    parar."""
    import os
    antes = db.token_datos()
    for p in (db.db_path(), db.db_path() + "-wal"):
        if os.path.exists(p):
            os.utime(p, ns=(0, 123456789))
    assert db.token_datos() == antes


def test_el_token_ve_los_borrados(client):
    """Borrar no toca ningún `updated_at`: el token tiene que salir del tombstone."""
    db.add_note("2026-06-10", "para borrar")
    nid = db.get_notes_for_date("2026-06-10")[0]["id"]
    antes = db.token_datos()
    db.delete_note(nid)
    assert db.token_datos() != antes


def test_el_token_ve_un_ajuste(client):
    """`settings` no está en SYNCABLE pero tiene su propio updated_at, y cambiar el tema tiene
    que refrescar la otra ventana."""
    antes = db.token_datos()
    db.set_setting("theme", "oceano")
    assert db.token_datos() != antes


def test_el_token_lleva_la_ruta(client):
    """Al cambiar de perfil cambia la base; sin la ruta el cambio podría pasar desapercibido."""
    assert db.token_datos().startswith(db.db_path())


def test_el_token_cambia_al_cambiar_de_perfil(tmp_path, monkeypatch):
    """Cambiar de perfil cambia la base entera: el widget tiene que dejar de mostrar el diario
    anterior."""
    from bitacora import profiles
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "sin-perfil.db"))

    uno = profiles.crear("Uno")
    otro = profiles.crear("Otro")
    profiles.usar(uno["slug"])
    db.init_db()
    antes = db.token_datos()

    profiles.usar(otro["slug"])
    db.init_db()
    assert db.token_datos() != antes


def test_sin_esquema_todavia_no_explota(tmp_path, monkeypatch):
    """Primer arranque: la DB puede no tener las tablas y el token igual tiene que salir, o la
    página entera se caería con un 500."""
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "no-existe.db"))
    t = db.token_datos()
    assert t.startswith(str(tmp_path))
    assert db.token_datos() == t        # y estable igual


# ── La ruta ──────────────────────────────────────────────────────────────────

def test_la_ruta_devuelve_el_token(client):
    r = client.get("/refresco")
    assert r.status_code == 200
    assert r.data.decode() == db.token_datos()


def test_la_ruta_no_se_puede_cachear(client):
    """Sin no-store el WebView se lo guarda y el poleo deja de ver los cambios."""
    assert "no-store" in client.get("/refresco").headers.get("Cache-Control", "")


def test_la_ruta_refleja_una_escritura(client):
    antes = client.get("/refresco").data
    client.post("/widget/tarea/agregar", data={"text": "desde el widget"})
    assert client.get("/refresco").data != antes


# ── Las dos plantillas lo traen ──────────────────────────────────────────────

@pytest.mark.parametrize("ruta", ["/calendar/2026/6", "/widget", "/tareas"])
def test_las_pantallas_traen_el_token_y_el_script(client, ruta):
    """`widget.html` es plantilla propia y no hereda de base.html: si el script se suma solo en
    una, esa ventana queda sin refrescarse."""
    html = client.get(ruta).data.decode()
    assert "window.TOKEN_DATOS" in html
    assert "js/refresco.js" in html


@pytest.mark.parametrize("ruta", ["/calendar/2026/6", "/widget", "/tareas", "/ajustes"])
def test_el_token_de_la_pagina_es_IGUAL_al_de_la_ruta(client, ruta):
    """⚠️ El otro bug que se publicó, y el más difícil de ver.

    El token lleva la ruta de la base, que en Windows tiene barras invertidas. Embutido como
    `window.TOKEN_DATOS = "{{ token_datos }}"`, JavaScript se comía esas barras (`\\U`, `\\T`… son
    escapes inválidos) y la página guardaba un valor que NUNCA iba a coincidir con lo que
    devuelve /refresco: recargaba cada 3 segundos para siempre. Se arregla con `| tojson`.

    El test compara el literal de la página, parseado como JSON igual que lo haría el navegador,
    contra la respuesta de la ruta.
    """
    import json
    import re
    html = client.get(ruta).data.decode()
    m = re.search(r"window\.TOKEN_DATOS = (.+?);", html)
    assert m, "no se encontró window.TOKEN_DATOS"
    del_html = json.loads(m.group(1))          # tal como lo lee el navegador
    assert del_html == client.get("/refresco").data.decode()


def test_el_borrador_no_se_decide_con_defaultValue():
    """⚠️ Tripwire, y va por la tercera vez.

    `value !== defaultValue` marca como "con borrador" **cualquier** campo que el JS rellene al
    cargar, y una ventana con borrador no se refresca nunca. Pasó con el slider de tamaño de
    celda del calendario (se restaura de localStorage) y después con los dos campos de
    `date-es.js`, que dejaron la vista del día sin enterarse de nada de lo que escribías en el
    widget. La referencia correcta es el snapshot tomado cuando la página terminó de cargar,
    más el evento `input` —que setear `.value` desde JS no dispara—.
    """
    import pathlib
    js = (pathlib.Path(__file__).resolve().parent.parent / "bitacora" / "static" / "js" /
          "refresco.js").read_text(encoding="utf-8")
    # Los comentarios sí lo nombran, justamente para explicar por qué no se usa.
    codigo = [l for l in js.splitlines() if not l.strip().startswith("//")]
    assert not [l for l in codigo if "defaultValue" in l]


# ── La red de seguridad ──────────────────────────────────────────────────────
# El modo de falla de esta feature es callado: la ventana se ve perfecta y muestra datos viejos.
# Se descubrió usando la app, no acá, y afectaba a 6 de las 14 pantallas. Estos tests recorren
# TODAS y fijan las condiciones que hacen falta para que el refresco pueda siquiera intentarlo.

PANTALLAS = ["/", "/calendar/2026/6", "/week/2026-06-10", "/day/2026-06-10", "/journal",
             "/recurring", "/estadisticas", "/tareas", "/search", "/ajustes", "/export",
             "/version", "/widget?p=nota", "/widget?p=tareas", "/widget?p=calendario"]


@pytest.mark.parametrize("ruta", PANTALLAS)
def test_todas_las_pantallas_entran_al_sistema_de_refresco(client, ruta):
    """Una pantalla sin `refresco.js` o sin token no se refresca, y no hay nada que lo delate."""
    r = client.get(ruta, follow_redirects=True)
    html = r.data.decode()
    assert "js/refresco.js" in html, f"{ruta} no carga refresco.js"
    assert "window.TOKEN_DATOS" in html, f"{ruta} no trae el token"


@pytest.mark.parametrize("ruta", PANTALLAS)
def test_ninguna_pantalla_nace_impedida_de_refrescarse(client, ruta):
    """⚠️ `autofocus` deja la ventana con el cursor puesto en un campo desde el arranque.

    Mientras la regla fue "el foco en un campo es un borrador", eso alcanzaba para que la
    pantalla **no se refrescara nunca** — le pasó a `/search`. Hoy la regla pide además que el
    campo tenga algo escrito. El test recorre las pantallas para encontrar las que arrancan
    enfocadas y, si hay alguna, exige que el refresco siga sin bloquear por el foco solo.
    """
    import re
    html = client.get(ruta, follow_redirects=True).data.decode()
    enfocada = re.search("<(?:input|textarea)[^>]*autofocus", html, re.I)
    if enfocada:
        assert "estaSucio(f)" in _refresco_js(), (
            f"{ruta} arranca con el foco en un campo y el refresco volvió a bloquear por el "
            f"foco solo: esa pantalla no se va a refrescar nunca")


def _refresco_js():
    import pathlib
    return (pathlib.Path(__file__).resolve().parent.parent / "bitacora" / "static" / "js" /
            "refresco.js").read_text(encoding="utf-8")


def test_el_aviso_existe_para_cuando_no_se_puede_aplicar():
    """Si el refresco no puede aplicar un cambio, tiene que verse en la app y no solo en la
    consola: es lo único que convierte "la ventana quedó vieja para siempre" en algo que el
    usuario nota y puede resolver con un botón."""
    js = _refresco_js()
    assert "refresco-aviso" in js
    assert "barraAviso" in js
    import pathlib
    css = (pathlib.Path(__file__).resolve().parent.parent / "bitacora" / "static" / "css" /
           "base.css").read_text(encoding="utf-8")
    assert ".refresco-aviso" in css, "el aviso no tiene estilo y saldría sin formato"


# ── Actualizar sin recargar ──────────────────────────────────────────────────

# ⚠️ Las zonas "rutinas" y "especiales" del día NO están acá: sus paneles viven dentro de un
# `if` (`day_events` y `journal_cats`), así que en un día pelado no existen. Que aparezca un panel
# entero es un cambio estructural de verdad, y ahí el refresco recarga, que es lo correcto. Las
# cubren los dos tests de abajo, que crean el dato primero.
CUBIERTAS = {
    "/day/2026-06-10":     ["tareas", "notas"],
    "/calendar/2026/6":    ["dia-2026-06-10"],
    "/week/2026-06-10":    ["dia-2026-06-10"],
    "/widget?p=tareas":    ["tareas", "rutinas"],
    "/widget?p=calendario": ["mes"],
}


@pytest.mark.parametrize("ruta,zonas", list(CUBIERTAS.items()))
def test_las_pantallas_cubiertas_traen_sus_zonas(client, ruta, zonas):
    """Sin la marca de página el refresco recarga, y sin las zonas no tiene qué actualizar."""
    html = client.get(ruta, follow_redirects=True).data.decode()
    assert "data-refresco-parcial" in html, f"{ruta} perdió la marca de página"
    for z in zonas:
        assert f'data-refresco="{z}"' in html, f"{ruta} perdió la zona {z}"


def test_la_marca_de_pagina_manda_sobre_las_zonas_sueltas():
    """⚠️ El navbar aporta una zona a TODAS las pantallas (el contador de atrasadas). Si el
    refresco se activara por "hay alguna zona", pantallas a medio marcar como /journal o /ajustes
    se darían por al día porque ese contador no cambió, y mostrarían datos viejos sin decir nada
    — el mismo fallo callado que este rediseño vino a sacar. Tiene que mirar la marca de página.
    """
    assert "data-refresco-parcial" in _refresco_js()


@pytest.mark.parametrize("ruta", ["/journal", "/recurring", "/tareas", "/ajustes",
                                  "/estadisticas", "/export"])
def test_las_pantallas_no_cubiertas_no_llevan_la_marca(client, ruta):
    """Una pantalla a medio marcar es peor que una sin marcar: la sin marcar recarga y queda al
    día. La marca solo se pone cuando TODO lo que cambia está dentro de una zona."""
    html = client.get(ruta, follow_redirects=True).data.decode()
    assert "data-refresco-parcial" not in html


def test_las_zonas_se_reemplazan_por_dentro():
    """⚠️ Se cambia el `innerHTML` de la zona, nunca el nodo: el drag & drop de tareas está
    enganchado al <ul id="todo-list"> y resuelve con closest(), así que sobrevive a que cambien
    los <li> y muere si se reemplaza el <ul>."""
    js = _refresco_js()
    assert "el.innerHTML = nueva.innerHTML" in js
    assert "replaceWith" not in js and "outerHTML" not in js


def test_la_lista_de_tareas_del_dia_existe_siempre(client):
    """Es zona del refresco y contenedor del drag & drop: si apareciera recién con la primera
    tarea, el conjunto de zonas cambiaría y habría que recargar."""
    html = client.get("/day/2026-06-10").data.decode()      # un día sin tareas
    assert 'id="todo-list"' in html


def test_el_dia_con_rutinas_trae_su_zona(client):
    db.add_recurring_event({"title": "Gimnasio", "color": "#22c55e", "recurrence": "daily",
                            "start_date": "2020-01-01", "end_date": ""})
    html = client.get("/day/2026-06-10").data.decode()
    assert 'data-refresco="rutinas"' in html


def test_el_dia_con_notas_especiales_trae_su_zona(client):
    import json
    db.add_journal_category({"name": "Emociones", "color": "#6366f1", "show_in_calendar": 1,
                             "fields_json": json.dumps([{"label": "Qué sentí", "type": "text",
                                                         "placeholder": ""}])})
    html = client.get("/day/2026-06-10").data.decode()
    assert 'data-refresco="especiales"' in html
