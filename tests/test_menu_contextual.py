"""Los atajos del menú del clic derecho: qué categorías entran y cuál rueda.

El menú tiene DOS conceptos conviviendo a propósito, y está bien que así sea:
- las **ruedas** guardan directo sin abrir nada, porque elegir una emoción es un gesto único;
- una **categoría** abre el día de hoy con ella ya elegida, porque un formulario de cuatro campos
  no se llena desde un menú contextual.
"""
import json

from bitacora import database as db
from bitacora.database import schema


def _cat(nombre, **extra):
    datos = {"name": nombre, "color": "#6366f1", "show_in_calendar": 0,
             "fields_json": json.dumps([{"label": "Notas", "type": "text"}])}
    datos.update(extra)
    db.add_journal_category(datos)
    return [c for c in db.get_journal_categories() if c["name"] == nombre][0]


# ── Qué entra al menú ────────────────────────────────────────────────────────

def test_una_categoria_propia_NO_se_mete_sola_en_el_menu(test_db):
    """El flag arranca en 0. Una categoría que armaste vos no decide sola aparecer en un menú
    global: es la misma regla que el tilde de Estadísticas, que también hay que poner."""
    _cat("Entrenamiento")
    assert db.categorias_en_menu() == []


def test_marcarla_la_pone_en_el_menu(test_db):
    cat = _cat("Entrenamiento", show_in_menu=1)
    assert [c["id"] for c in db.categorias_en_menu()] == [cat["id"]]
    assert db.categorias_en_menu()[0]["nombre"] == "Entrenamiento"


def test_una_categoria_ARCHIVADA_sale_del_menu(test_db):
    """Archivar afecta dónde se ESCRIBE, y el menú es justamente un atajo para escribir: un
    atajo a una categoría archivada llevaría a un alta que el día ya no deja elegir."""
    cat = _cat("Entrenamiento", show_in_menu=1)
    db.set_journal_category_active(cat["id"], False)
    assert db.categorias_en_menu() == []


def test_el_flag_sobrevive_a_editar_la_categoria(test_db):
    """⚠️ El navegador no manda lo que el formulario no tiene. Si la edición se olvidara del
    tilde, guardar cualquier cambio sacaría la categoría del menú sin decir nada — que es el
    mismo bug que tuvo el formulario de rutinas con la frecuencia anual."""
    cat = _cat("Entrenamiento", show_in_menu=1)
    db.update_journal_category(cat["id"], {
        "name": "Entrenamiento", "color": "#ef4444", "show_in_calendar": 0,
        "show_in_menu": 1, "fields_json": cat["fields_json"]})
    assert len(db.categorias_en_menu()) == 1


# ── Las de fábrica ───────────────────────────────────────────────────────────

def test_las_tres_de_fabrica_vienen_en_el_menu(tmp_path, monkeypatch):
    """Son las que trae la app: tienen que servir desde el primer arranque, sin configurar."""
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "nueva.db"))
    db.init_db()
    assert sorted(c["nombre"] for c in db.categorias_en_menu()) == \
        ["Alimentación", "Emociones", "Sueño"]


def test_una_base_YA_INSTALADA_tambien_las_recibe(tmp_path, monkeypatch):
    """⚠️ Se identifican por su **uid fijo**, no por el nombre.

    El uid es identidad —es la razón por la que las de fábrica lo tienen— y el nombre lo pudiste
    cambiar. Eso saca al marcado de la clase de cosas que este repo no hace: no se adivina nada
    sobre los datos del usuario."""
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "vieja.db"))
    db.init_db()
    with db.get_db() as c:                      # la base tal como viene de la version anterior
        c.execute("UPDATE journal_categories SET name = 'Mis emociones' WHERE name = 'Emociones'")
        c.execute("UPDATE journal_categories SET show_in_menu = 0")
        c.execute("DELETE FROM settings WHERE key = ?", (schema.CLAVE_MENU_FABRICA,))
        # ⚠️ Y el `user_version` viejo: es la guarda que decide si `init_db()` hace algo. Sin
        # bajarlo, el setup sale antes de empezar y el test probaria la guarda, no la migracion.
        c.execute(f"PRAGMA user_version = {schema.SCHEMA_VERSION - 1}")
    db.init_db()
    nombres = sorted(c["nombre"] for c in db.categorias_en_menu())
    assert "Mis emociones" in nombres, "se las busca por uid, no por nombre"
    assert len(nombres) == 3


def test_sacarlas_del_menu_NO_se_deshace_en_el_request_siguiente(tmp_path, monkeypatch):
    """⚠️ `init_db()` corre en CADA request, así que el marcado va con una guarda en `settings`.
    Sin ella, desmarcar una categoría duraba hasta que cargaras la página siguiente."""
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "x.db"))
    db.init_db()
    with db.get_db() as c:
        c.execute("UPDATE journal_categories SET show_in_menu = 0")
    db.init_db(); db.init_db()
    assert db.categorias_en_menu() == []


# ── La rueda ─────────────────────────────────────────────────────────────────

def test_la_rueda_conserva_su_propio_criterio(test_db):
    """Los dos conceptos conviven a propósito: la rueda sale de la primera categoría que tenga
    campo de rueda, esté o no marcada para el menú."""
    db.add_journal_category({
        "name": "Emociones", "color": "#ec4899", "show_in_calendar": 0, "show_in_menu": 0,
        "fields_json": json.dumps([{"label": "Emoción", "type": "emotion-wheel"}])})
    destino = db.categoria_con_rueda()
    assert destino and destino["nombre"] == "Emociones"
    assert db.categorias_en_menu() == [], "la rueda no depende del tilde del menú"


def test_la_pagina_lleva_las_categorias_y_la_rueda_elegida(client):
    """El menú se arma en el navegador, así que lo que importa es qué le llega."""
    _cat("Entrenamiento", show_in_menu=1)
    html = client.get("/day/2026-10-01").data.decode()
    assert "window.MENU_CATEGORIAS" in html and "Entrenamiento" in html
    assert 'window.MENU_RUEDAS = "ambas"' in html, "el default son las dos ruedas"

    client.post("/ajustes/set", data={"key": "menu_ruedas", "value": "ekman"})
    assert 'window.MENU_RUEDAS = "ekman"' in client.get("/day/2026-10-01").data.decode()
