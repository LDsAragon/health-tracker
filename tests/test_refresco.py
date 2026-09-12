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


def test_el_token_lleva_el_wal_y_no_solo_el_db(client, tmp_path):
    """⚠️ La app corre en WAL: un commit puede tocar solo el sidecar y dejar la mtime del .db
    igual. Mirando solo el .db, los cambios recién se verían en el próximo checkpoint.

    Se toca el `-wal` a mano en vez de confiar en cuándo SQLite hace checkpoint, que es lo que
    haría el test intermitente."""
    import os
    wal = db.db_path() + "-wal"
    open(wal, "ab").close()
    antes = db.token_datos()
    os.utime(wal, ns=(0, 123456789))
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


def test_sin_archivos_todavia_no_explota(tmp_path, monkeypatch):
    """Primer arranque: la DB puede no existir aún y el token igual tiene que salir."""
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "no-existe.db"))
    t = db.token_datos()
    assert t.endswith("|-|-")       # ni .db ni -wal


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
