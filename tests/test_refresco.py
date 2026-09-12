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
