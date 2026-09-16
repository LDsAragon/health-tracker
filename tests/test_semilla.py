"""Las categorías que la app trae de fábrica (`plantillas.DE_FABRICA`).

Estos tests crean su base a mano y **no usan el fixture `test_db`**, que justamente las borra:
armar las tres categorías a mano era el primer trabajo antes de poder anotar nada, así que una
instalación nueva ya tiene que traerlas, y eso es lo que se prueba acá.
"""
import gc

from bitacora import database as db
from bitacora import plantillas
import bitacora.database.conn as conn
from bitacora import sync
from bitacora.database.schema import CLAVE_SEED_JOURNAL


def _base(tmp_path, nombre="nueva.db"):
    """Una base recién creada, como la de una instalación nueva."""
    ruta = str(tmp_path / nombre)
    conn.DB_PATH = ruta
    db.init_db()
    return ruta


def test_una_instalacion_nueva_trae_las_tres(tmp_path, monkeypatch):
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "x.db"))
    _base(tmp_path)
    nombres = [c["name"] for c in db.get_journal_categories()]
    assert nombres == ["Emociones", "Sueño", "Alimentación"]


def test_las_categorias_de_fabrica_vienen_con_sus_campos(tmp_path, monkeypatch):
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "x.db"))
    _base(tmp_path)
    cats = {c["name"]: c for c in db.get_journal_categories()}
    emociones = cats["Emociones"]["fields"]
    assert emociones[0]["type"] == "emotion-wheel"          # la que usa la rueda
    assert [f["label"] for f in cats["Alimentación"]["fields"]][0] == "Momento"
    # La lista de opciones tiene que viajar: sin ella el campo no se puede completar.
    assert "Desayuno" in cats["Alimentación"]["fields"][0]["placeholder"]


def test_borrar_una_de_fabrica_no_la_resucita(tmp_path, monkeypatch):
    """⚠️ Con un `WHERE NOT EXISTS` como el del grupo Cumpleaños volverían a aparecer. Borrar una
    categoría se lleva sus notas, así que resucitarla sería el peor de los finales."""
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "x.db"))
    _base(tmp_path)
    db.delete_journal_category(db.get_journal_categories()[0]["id"])
    db.init_db()
    assert [c["name"] for c in db.get_journal_categories()] == ["Sueño", "Alimentación"]


def test_un_perfil_que_ya_tiene_categorias_no_recibe_ninguna(tmp_path, monkeypatch):
    """Quien armó las suyas no tiene por qué encontrarse tres más una mañana."""
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "x.db"))
    _base(tmp_path)
    for c in db.get_journal_categories():
        db.delete_journal_category(c["id"])
    db.add_journal_category({"name": "La mía", "color": "#fff", "fields_json": "[]",
                             "show_in_calendar": 0})
    # Como si viniera de una versión anterior: nunca se sembró y hay que migrar el esquema.
    with db.get_db() as cx:
        cx.execute("DELETE FROM settings WHERE key = ?", (CLAVE_SEED_JOURNAL,))
        cx.execute("PRAGMA user_version = 0")
    db.init_db()
    assert [c["name"] for c in db.get_journal_categories()] == ["La mía"]


def test_la_marca_del_sembrado_queda_aunque_no_se_siembre(tmp_path, monkeypatch):
    """Se escribe siempre, así que la pregunta no se vuelve a hacer en cada migración."""
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "x.db"))
    _base(tmp_path)
    assert db.get_setting(CLAVE_SEED_JOURNAL) == "1"


def test_dos_maquinas_no_terminan_con_seis_categorias(tmp_path, monkeypatch):
    """⚠️ La razón del uid fijo. Cada instalación las crea por su cuenta: con un uid al azar el
    merge las vería como filas distintas y sincronizar dejaría dos "Sueño", dos "Emociones"...
    Es exactamente lo que ya pasó con el grupo Cumpleaños."""
    monkeypatch.setattr("bitacora.database.conn.DB_PATH", str(tmp_path / "pc.db"))
    pc = _base(tmp_path, "pc.db")
    lap = _base(tmp_path, "lap.db")          # la otra máquina las sembró por su cuenta
    paq = str(tmp_path / "paquete.db")

    conn.DB_PATH = lap
    sync.exportar(paq, {"uid": "p1", "nombre": "Principal", "slug": "principal"}, "portatil")
    gc.collect()

    conn.DB_PATH = pc
    sync.aplicar(paq)
    assert [c["name"] for c in db.get_journal_categories()] == ["Emociones", "Sueño", "Alimentación"]


def test_las_de_fabrica_salen_del_mismo_catalogo_que_los_chips():
    """Una sola tabla: los chips de "Empezá desde una plantilla" y las que vienen creadas son lo
    mismo, así que no pueden describir campos distintos."""
    for slug in plantillas.DE_FABRICA:
        p = plantillas.por_slug(slug)
        assert p is not None and p.get("uid"), slug
    # El uid fijo lo llevan solo las de fábrica: el resto son plantillas para aplicar a mano.
    con_uid = {p["slug"] for p in plantillas.PLANTILLAS if p.get("uid")}
    assert con_uid == set(plantillas.DE_FABRICA)
