"""Merge entre dos dispositivos. Es la parte donde un bug corrompe el diario, así que los
casos van con marcas de tiempo puestas a mano y no dependiendo del reloj."""
import gc
import os

import pytest

import database as db
import database.conn as conn
import sync


@pytest.fixture
def dos_equipos(tmp_path, monkeypatch):
    """(pc, portatil, paquete): dos bases con el mismo estado inicial y un uid compartido.

    Devuelve también `usar`, que cambia cuál es la base activa (es lo que hace el switcher
    de perfiles: rebindear database.conn.DB_PATH).
    """
    pc = str(tmp_path / "pc.db")
    lap = str(tmp_path / "lap.db")
    paq = str(tmp_path / "paquete.db")
    monkeypatch.setattr("database.conn.DB_PATH", pc)

    def usar(p):
        conn.DB_PATH = p
        db.init_db()

    usar(pc)
    db.add_note("2026-09-01", "comun")
    _clonar(lap)                 # la portátil arranca del mismo estado
    usar(lap)
    db.init_db()
    return pc, lap, paq, usar


def _clonar(dest):
    """snapshot_to sobre una DB que ya se usó en el test. El gc es necesario porque los
    callers hacen `with get_db()`, que commitea pero no cierra: sin esto SQLite dice
    "database is locked". En producción el destino de snapshot_to siempre es un archivo nuevo."""
    gc.collect()
    db.snapshot_to(dest)


def _marcar(ruta, tabla, campo, valor, marca):
    """Fija updated_at a mano: con el reloj real todo el test cae en el mismo milisegundo."""
    c = conn.sqlite3.connect(ruta)
    c.execute(f"UPDATE {tabla} SET updated_at = ? WHERE {campo} = ?", (marca, valor))
    c.commit()
    c.close()


def _exportar(desde, paq, usar, uid="p1"):
    usar(desde)
    return sync.exportar(paq, {"uid": uid, "nombre": "Principal", "slug": "principal"}, "dev")


# ── Altas ────────────────────────────────────────────────────────────────────

def test_trae_lo_que_solo_existe_del_otro_lado(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.add_note("2026-09-10", "del viaje")
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)
    assert [n["content"] for n in db.get_notes_for_date("2026-09-10")] == ["del viaje"]

def test_no_toca_lo_que_solo_existe_de_este_lado(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    usar(pc)
    db.add_note("2026-09-11", "de la PC")
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)
    assert [n["content"] for n in db.get_notes_for_date("2026-09-11")] == ["de la PC"]


# ── Conflictos: última escritura gana ────────────────────────────────────────

def test_gana_la_edicion_mas_reciente(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.update_note(db.get_notes_for_date("2026-09-01")[0]["id"], "editada alla")
    _marcar(lap, "notes", "content", "editada alla", "2030-01-01 00:00:00.000")
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)
    assert db.get_notes_for_date("2026-09-01")[0]["content"] == "editada alla"

def test_no_pisa_con_una_edicion_mas_vieja(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.update_note(db.get_notes_for_date("2026-09-01")[0]["id"], "vieja de alla")
    _marcar(lap, "notes", "content", "vieja de alla", "2000-01-01 00:00:00.000")
    _exportar(lap, paq, usar)
    usar(pc)
    db.update_note(db.get_notes_for_date("2026-09-01")[0]["id"], "nueva de aca")
    sync.aplicar(paq)
    assert db.get_notes_for_date("2026-09-01")[0]["content"] == "nueva de aca"

def test_el_merge_conserva_la_marca_remota(dos_equipos):
    """Si el trigger de UPDATE pisara updated_at con la hora local, en el viaje de vuelta una
    edición vieja le ganaría a una nueva."""
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.update_note(db.get_notes_for_date("2026-09-01")[0]["id"], "alla")
    _marcar(lap, "notes", "content", "alla", "2030-01-01 00:00:00.000")
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)
    assert db.get_notes_for_date("2026-09-01")[0]["updated_at"] == "2030-01-01 00:00:00.000"


# ── Borrados ─────────────────────────────────────────────────────────────────

def test_el_borrado_se_propaga(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.delete_note(db.get_notes_for_date("2026-09-01")[0]["id"])
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)
    assert db.get_notes_for_date("2026-09-01") == []

def test_el_borrado_no_gana_si_de_este_lado_se_edito_despues(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.delete_note(db.get_notes_for_date("2026-09-01")[0]["id"])
    c = conn.sqlite3.connect(lap)
    c.execute("UPDATE deletions SET deleted_at = '2000-01-01 00:00:00.000'")
    c.commit(); c.close()
    _exportar(lap, paq, usar)
    usar(pc)
    db.update_note(db.get_notes_for_date("2026-09-01")[0]["id"], "la salve editandola")
    sync.aplicar(paq)
    assert [n["content"] for n in db.get_notes_for_date("2026-09-01")] == ["la salve editandola"]

def test_no_resucita_lo_borrado_de_este_lado(dos_equipos):
    """La fila sigue viva allá porque todavía no se sincronizó; acá ya se borró."""
    pc, lap, paq, usar = dos_equipos
    _exportar(lap, paq, usar)
    usar(pc)
    db.delete_note(db.get_notes_for_date("2026-09-01")[0]["id"])
    sync.aplicar(paq)
    assert db.get_notes_for_date("2026-09-01") == []


# ── Referencias entre tablas ─────────────────────────────────────────────────

def test_traduce_el_id_del_padre_entre_equipos(dos_equipos):
    """category_id es un entero LOCAL: la misma categoría es la 1 acá y la 77 allá."""
    pc, lap, paq, usar = dos_equipos
    usar(pc)
    db.add_journal_category({"name": "Sueno", "color": "#fff", "fields_json": "[]",
                             "show_in_calendar": 0})
    cid_pc = db.get_journal_categories()[0]["id"]
    _clonar(lap)
    usar(lap)
    c = conn.sqlite3.connect(lap)
    c.execute("UPDATE journal_categories SET id = 77")
    c.commit(); c.close()
    db.add_journal_entry({"category_id": 77, "entry_date": "2026-09-10",
                          "values_json": "{}", "tags": ""})
    _exportar(lap, paq, usar)

    usar(pc)
    sync.aplicar(paq)
    with db.get_db() as cx:
        cats = [r["category_id"] for r in cx.execute("SELECT category_id FROM journal_entries")]
    assert cats == [cid_pc], f"no tradujo el padre: {cats}"

def test_saltea_al_huerfano_en_vez_de_reventar(dos_equipos):
    """Si el padre se borró acá, el hijo entraría con NULL y violaría el NOT NULL."""
    pc, lap, paq, usar = dos_equipos
    usar(pc)
    db.add_journal_category({"name": "Sueno", "color": "#fff", "fields_json": "[]",
                             "show_in_calendar": 0})
    _clonar(lap)
    usar(lap)
    cid = db.get_journal_categories()[0]["id"]
    db.add_journal_entry({"category_id": cid, "entry_date": "2026-09-10",
                          "values_json": "{}", "tags": ""})
    _exportar(lap, paq, usar)
    usar(pc)
    db.delete_journal_category(db.get_journal_categories()[0]["id"])
    sync.aplicar(paq)          # no debe tirar
    with db.get_db() as cx:
        assert cx.execute("SELECT COUNT(*) FROM journal_entries").fetchone()[0] == 0

def test_completions_con_clave_natural_repetida(dos_equipos):
    """UNIQUE(event_id, done_date): la misma rutina marcada el mismo día en las dos máquinas
    tiene uid distinto pero choca. Representan el mismo hecho."""
    pc, lap, paq, usar = dos_equipos
    usar(pc)
    db.add_recurring_event({"title": "Correr", "color": "#fff", "recurrence": "daily",
                            "start_date": "2026-01-01", "end_date": ""})
    _clonar(lap)
    eid_pc = db.get_recurring_events()[0]["id"]
    db.complete_event(eid_pc, "2026-09-05")
    usar(lap)
    db.complete_event(db.get_recurring_events()[0]["id"], "2026-09-05")
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)          # no debe tirar por el UNIQUE
    with db.get_db() as cx:
        assert cx.execute("SELECT COUNT(*) FROM completions").fetchone()[0] == 1


# ── Tareas, ajustes y tablas legacy ──────────────────────────────────────────

def test_recompacta_las_posiciones_de_las_tareas(dos_equipos):
    """Las dos máquinas calculan position con MAX(position)+1, así que generan las mismas."""
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.add_todo("2026-09-10", "de alla")
    _exportar(lap, paq, usar)
    usar(pc)
    db.add_todo("2026-09-10", "de aca")
    sync.aplicar(paq)
    pos = [t["position"] for t in db.get_todos_for_date("2026-09-10")]
    assert sorted(pos) == list(range(len(pos))), pos

def test_los_ajustes_viajan_y_gana_el_mas_nuevo(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.set_setting("theme", "bosque")
    _marcar(lap, "settings", "key", "theme", "2030-01-01 00:00:00.000")
    _exportar(lap, paq, usar)
    usar(pc)
    db.set_setting("theme", "oceano")
    _marcar(pc, "settings", "key", "theme", "2000-01-01 00:00:00.000")
    sync.aplicar(paq)
    assert db.get_setting("theme") == "bosque"

def test_la_metadata_del_paquete_no_viaja(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)
    with db.get_db() as cx:
        metas = cx.execute("SELECT COUNT(*) FROM settings WHERE key LIKE '_sync_%'").fetchone()[0]
    assert metas == 0

def test_no_toca_las_tablas_legacy(dos_equipos):
    """entries/goals/custom_events/event_logs siguen con datos en las DBs reales y viajan
    dentro del archivo, pero el merge trabaja solo sobre SYNCABLE."""
    pc, lap, paq, usar = dos_equipos
    for ruta in (pc, lap):
        c = conn.sqlite3.connect(ruta)
        c.execute("CREATE TABLE IF NOT EXISTS goals (id INTEGER PRIMARY KEY, nombre TEXT)")
        c.commit(); c.close()
    c = conn.sqlite3.connect(lap)
    c.execute("INSERT INTO goals (nombre) VALUES ('solo de alla')")
    c.commit(); c.close()
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)
    with db.get_db() as cx:
        assert cx.execute("SELECT COUNT(*) FROM goals").fetchone()[0] == 0


# ── Idempotencia, ida y vuelta, rechazos ─────────────────────────────────────

def test_aplicar_dos_veces_no_cambia_nada(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.add_note("2026-09-10", "del viaje")
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)
    antes = db.table_counts(pc)
    sync.aplicar(paq)
    assert db.table_counts(pc) == antes

def test_ida_y_vuelta_deja_las_dos_iguales(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.add_note("2026-09-10", "del viaje")
    usar(pc)
    db.add_note("2026-09-11", "de la PC")
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)
    paq2 = paq + ".vuelta"
    _exportar(pc, paq2, usar)
    usar(lap)
    sync.aplicar(paq2)
    interes = ("notes", "todos", "journal_entries", "journal_categories")
    assert {t: db.table_counts(pc).get(t) for t in interes} == \
           {t: db.table_counts(lap).get(t) for t in interes}

def test_analizar_no_toca_nada(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    usar(lap)
    db.add_note("2026-09-10", "del viaje")
    _exportar(lap, paq, usar)
    usar(pc)
    antes = db.table_counts(pc)
    resumen = sync.analizar(paq)
    assert resumen["total"]["altas"] == 1
    assert db.table_counts(pc) == antes

def test_rechaza_un_archivo_que_no_es_de_la_app(tmp_path, monkeypatch):
    monkeypatch.setattr("database.conn.DB_PATH", str(tmp_path / "x.db"))
    db.init_db()
    basura = tmp_path / "basura.db"
    basura.write_bytes(b"esto no es sqlite")
    ok, msg = sync.validar(str(basura))
    assert not ok and "Bitácora" in msg

def test_rechaza_otra_version_de_esquema(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    _exportar(lap, paq, usar)
    c = conn.sqlite3.connect(paq)
    c.execute("PRAGMA user_version = 99")
    c.commit(); c.close()
    usar(pc)
    ok, msg = sync.validar(paq)
    assert not ok and "versión" in msg

def test_el_paquete_dice_de_donde_viene(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    _exportar(lap, paq, usar, uid="perfil-abc")
    m = sync.meta_de(paq)
    assert m["perfil_uid"] == "perfil-abc" and m["perfil_nombre"] == "Principal"
    assert m["version"] == sync.SCHEMA_VERSION and m["exportado"]

def test_aplicar_deja_backup_previo(dos_equipos):
    pc, lap, paq, usar = dos_equipos
    _exportar(lap, paq, usar)
    usar(pc)
    sync.aplicar(paq)
    carpeta = os.path.join(os.path.dirname(pc), "backups")
    assert [f for f in os.listdir(carpeta) if f.startswith("health-presync-")]


# ── Rutas ────────────────────────────────────────────────────────────────────

@pytest.fixture
def equipo_web(tmp_path, monkeypatch):
    """Una instalación con perfiles, servida por el test client."""
    import app as flask_app
    import profiles
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    monkeypatch.setattr("database.conn.DB_PATH", str(tmp_path / "x.db"))
    p = profiles.crear("Principal")
    profiles.usar(p["slug"])
    db.init_db()
    flask_app.app.config["TESTING"] = True
    with flask_app.app.test_client() as c:
        yield c, p


def test_exportar_da_un_paquete_valido(equipo_web):
    cliente, _ = equipo_web
    r = cliente.get("/sync/exportar")
    assert r.status_code == 200
    assert "bitacora-sync-" in r.headers["Content-Disposition"]
    assert r.data[:15] == b"SQLite format 3"

def test_importar_deja_el_paquete_pendiente_y_no_aplica(equipo_web, tmp_path):
    import io as _io
    cliente, _ = equipo_web
    db.add_note("2026-09-01", "de aca")
    paq = str(tmp_path / "paq.db")
    sync.exportar(paq, {"uid": "otro-equipo", "nombre": "P", "slug": "p"}, "d")
    _marcar(paq, "notes", "content", "de aca", "2030-01-01 00:00:00.000")
    antes = db.table_counts(db.db_path())
    with open(paq, "rb") as f:
        r = cliente.post("/sync/importar", data={"paquete": (_io.BytesIO(f.read()), "p.db")},
                         content_type="multipart/form-data")
    assert r.status_code == 302 and "/sync/previa" in r.headers["Location"]
    assert os.path.exists(sync.ruta_pendiente())
    assert db.table_counts(db.db_path()) == antes   # todavía no tocó nada

def test_importar_rechaza_un_archivo_cualquiera(equipo_web):
    import io as _io
    cliente, _ = equipo_web
    r = cliente.post("/sync/importar",
                     data={"paquete": (_io.BytesIO(b"no soy sqlite"), "x.db")},
                     content_type="multipart/form-data")
    assert "sync-err-invalid" in r.headers["Location"]
    assert not os.path.exists(sync.ruta_pendiente())

def test_un_paquete_ajeno_no_se_aplica_sin_confirmar(equipo_web, tmp_path):
    import io as _io
    cliente, _ = equipo_web
    db.add_note("2026-09-01", "de aca")
    paq = str(tmp_path / "ajeno.db")
    sync.exportar(paq, {"uid": "PERFIL-DE-OTRO", "nombre": "Otro", "slug": "otro"}, "d")
    with open(paq, "rb") as f:
        cliente.post("/sync/importar", data={"paquete": (_io.BytesIO(f.read()), "p.db")},
                     content_type="multipart/form-data")
    assert b"datos-err" in cliente.get("/sync/previa").data      # la previa avisa
    r = cliente.post("/sync/aplicar")                            # sin confirmar
    assert "/sync/previa" in r.headers["Location"]
    assert os.path.exists(sync.ruta_pendiente())                 # sigue pendiente

def test_confirmar_un_ajeno_lo_empareja(equipo_web, tmp_path):
    import io as _io
    import profiles
    cliente, perfil = equipo_web
    paq = str(tmp_path / "ajeno.db")
    sync.exportar(paq, {"uid": "PERFIL-DE-OTRO", "nombre": "Otro", "slug": "otro"}, "d")
    with open(paq, "rb") as f:
        cliente.post("/sync/importar", data={"paquete": (_io.BytesIO(f.read()), "p.db")},
                     content_type="multipart/form-data")
    r = cliente.post("/sync/aplicar", data={"confirmo_ajeno": "si"})
    assert "sync-ok-" in r.headers["Location"]
    actual = [p for p in profiles.listar() if p["slug"] == perfil["slug"]][0]
    assert "PERFIL-DE-OTRO" in actual.get("emparejados", [])

def test_descartar_borra_el_pendiente(equipo_web, tmp_path):
    import io as _io
    cliente, _ = equipo_web
    paq = str(tmp_path / "paq.db")
    sync.exportar(paq, {"uid": "x", "nombre": "P", "slug": "p"}, "d")
    with open(paq, "rb") as f:
        cliente.post("/sync/importar", data={"paquete": (_io.BytesIO(f.read()), "p.db")},
                     content_type="multipart/form-data")
    cliente.post("/sync/descartar")
    assert not os.path.exists(sync.ruta_pendiente())

def test_la_previa_sin_paquete_vuelve_a_datos(equipo_web):
    cliente, _ = equipo_web
    r = cliente.get("/sync/previa")
    assert r.status_code == 302 and "/export" in r.headers["Location"]
