"""
Operaciones de base de datos — cada test usa una DB temporal aislada.
Verifica CRUD de notas, eventos recurrentes y completaciones.
"""
from datetime import date, timedelta
from datetime import datetime, timezone

from bitacora import database as db

EV_BASE = {
    "title": "Caminadora",
    "color": "#22c55e",
    "recurrence": "daily",
    "start_date": "2020-01-01",
    "end_date": "",
}

DATE = "2026-06-09"


# ── Notas ─────────────────────────────────────────────────────────────────────

def test_add_and_get_note(test_db):
    db.add_note(DATE, "hice ejercicio", "#6366f1")
    notes = db.get_notes_for_date(DATE)
    assert len(notes) == 1
    assert notes[0]["content"] == "hice ejercicio"
    assert notes[0]["color"] == "#6366f1"

def test_day_sin_notas_retorna_lista_vacia(test_db):
    assert db.get_notes_for_date(DATE) == []

def test_update_note(test_db):
    db.add_note(DATE, "original", "")
    nid = db.get_notes_for_date(DATE)[0]["id"]
    db.update_note(nid, "editada", "#22c55e")
    note = db.get_notes_for_date(DATE)[0]
    assert note["content"] == "editada"
    assert note["color"] == "#22c55e"

def test_delete_note(test_db):
    db.add_note(DATE, "borrar", "")
    nid = db.get_notes_for_date(DATE)[0]["id"]
    db.delete_note(nid)
    assert db.get_notes_for_date(DATE) == []

def test_notes_range_acota_por_fecha(test_db):
    db.add_note("2026-06-01", "principio", "")
    db.add_note("2026-06-15", "mitad", "")
    db.add_note("2026-07-01", "otro mes", "")
    result = db.get_notes_range("2026-06-01", "2026-06-30")
    assert "2026-06-01" in result
    assert "2026-06-15" in result
    assert "2026-07-01" not in result

def test_search_notes_encuentra_coincidencia(test_db):
    db.add_note(DATE, "fui al gimnasio hoy", "")
    db.add_note("2026-06-10", "comi bien", "")
    results = db.search_notes("gimnasio")
    assert len(results) == 1
    assert results[0]["content"] == "fui al gimnasio hoy"

def test_search_notes_sin_resultados(test_db):
    db.add_note(DATE, "nota normal", "")
    assert db.search_notes("xyz_inexistente") == []

def test_search_notes_case_insensitive_no_requerido(test_db):
    # LIKE en SQLite es case-sensitive para ASCII pero útil igualmente
    db.add_note(DATE, "camine en la caminadora", "")
    assert len(db.search_notes("caminadora")) == 1


# ── Eventos recurrentes ───────────────────────────────────────────────────────

def test_add_and_get_recurring(test_db):
    db.add_recurring_event(EV_BASE)
    events = db.get_recurring_events()
    assert len(events) == 1
    assert events[0]["title"] == "Caminadora"

def test_update_recurring_event(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.update_recurring_event(eid, {
        "title": "Actualizado", "color": "#ef4444",
        "recurrence": "weekly:1", "start_date": "2026-01-01",
        "end_date": "2026-12-31",
    })
    ev = db.get_recurring_events()[0]
    assert ev["title"] == "Actualizado"
    assert ev["recurrence"] == "weekly:1"
    assert ev["end_date"] == "2026-12-31"

def test_delete_recurring_event(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.delete_recurring_event(eid)
    assert db.get_recurring_events() == []

def test_delete_recurr_event_cascadea_completaciones(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.complete_event(eid, DATE, "nota")
    db.delete_recurring_event(eid)
    assert db.get_completions_range(DATE, DATE) == {}


# ── Borrado granular (cortar a futuro) ──────────────────────────────────────────

def test_end_recurring_event_fija_end_date(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.end_recurring_event(eid, "2026-06-08")
    ev = db.get_recurring_events()[0]
    assert ev["end_date"] == "2026-06-08"

def test_end_recurring_event_conserva_pasado_corta_futuro(test_db):
    db.add_recurring_event(EV_BASE)
    ev = db.get_recurring_events()[0]
    eid = ev["id"]
    cutoff = "2026-06-08"
    db.end_recurring_event(eid, cutoff)
    ev = db.get_recurring_events()[0]
    # pasado/igual al corte sigue aplicando; posterior, no
    assert db.event_applies(ev, date(2026, 6, 7))
    assert db.event_applies(ev, date(2026, 6, 8))
    assert not db.event_applies(ev, date(2026, 6, 9))

def test_end_recurring_event_limpia_completions_posteriores(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.complete_event(eid, "2026-06-07", "antes")
    db.complete_event(eid, "2026-06-09", "despues")
    db.end_recurring_event(eid, "2026-06-08")
    comps = db.get_completions_range("2026-06-01", "2026-06-30")
    assert "2026-06-07" in comps          # historial conservado
    assert "2026-06-09" not in comps      # huérfana futura eliminada


# ── Visibilidad en calendario ───────────────────────────────────────────────────

def test_recurring_visibilidad_default_visible(test_db):
    db.add_recurring_event(EV_BASE)
    assert db.get_recurring_events()[0]["show_in_calendar"] == 1

def test_set_recurring_visibility_oculta_y_muestra(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.set_recurring_visibility(eid, False)
    assert db.get_recurring_events()[0]["show_in_calendar"] == 0
    db.set_recurring_visibility(eid, True)
    assert db.get_recurring_events()[0]["show_in_calendar"] == 1


# ── Completaciones ────────────────────────────────────────────────────────────

def test_complete_event_done(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.complete_event(eid, DATE, "comentario")
    comps = db.get_completions_range(DATE, DATE)
    assert comps[DATE][eid]["status"] == "done"
    assert comps[DATE][eid]["note"] == "comentario"

def test_skip_event(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.complete_event(eid, DATE, "estaba ocupado", status="skipped")
    comps = db.get_completions_range(DATE, DATE)
    assert comps[DATE][eid]["status"] == "skipped"

def test_uncomplete_event(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.complete_event(eid, DATE)
    db.uncomplete_event(eid, DATE)
    assert db.get_completions_range(DATE, DATE) == {}

def test_complete_actualiza_nota(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.complete_event(eid, DATE, "primera nota")
    db.complete_event(eid, DATE, "nota actualizada")
    comps = db.get_completions_range(DATE, DATE)
    assert comps[DATE][eid]["note"] == "nota actualizada"

def test_completions_range_no_incluye_fuera_del_rango(test_db):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    db.complete_event(eid, "2026-05-31")
    db.complete_event(eid, DATE)
    comps = db.get_completions_range(DATE, DATE)
    assert "2026-05-31" not in comps
    assert DATE in comps

def test_completion_stats(test_db):
    db.add_recurring_event(EV_BASE)
    events = db.get_recurring_events()
    eid = events[0]["id"]
    today = date.today()
    for i in range(5):
        db.complete_event(eid, (today - timedelta(days=i)).isoformat())
    stats = db.get_completion_stats(events, days=30)
    assert stats[eid]["done"] == 5
    assert stats[eid]["applicable"] == 30


# ── To-dos diarios ──────────────────────────────────────────────────────────────

TDATE = "2026-06-09"

def test_add_and_get_todo(test_db):
    db.add_todo(TDATE, "Caminar 30 min")
    todos = db.get_todos_for_date(TDATE)
    assert len(todos) == 1
    assert todos[0]["text"] == "Caminar 30 min"
    assert todos[0]["done"] == 0

def test_todo_position_incremental(test_db):
    db.add_todo(TDATE, "a")
    db.add_todo(TDATE, "b")
    todos = db.get_todos_for_date(TDATE)
    assert [t["position"] for t in todos] == [0, 1]
    assert [t["text"] for t in todos] == ["a", "b"]

def test_toggle_todo(test_db):
    db.add_todo(TDATE, "x")
    tid = db.get_todos_for_date(TDATE)[0]["id"]
    db.toggle_todo(tid)
    assert db.get_todos_for_date(TDATE)[0]["done"] == 1
    db.toggle_todo(tid)
    assert db.get_todos_for_date(TDATE)[0]["done"] == 0

def test_update_todo(test_db):
    db.add_todo(TDATE, "viejo")
    tid = db.get_todos_for_date(TDATE)[0]["id"]
    db.update_todo(tid, "nuevo")
    assert db.get_todos_for_date(TDATE)[0]["text"] == "nuevo"

def test_move_todo_cambia_dia(test_db):
    db.add_todo(TDATE, "mover")
    tid = db.get_todos_for_date(TDATE)[0]["id"]
    other = "2026-06-10"
    db.move_todo(tid, other)
    assert db.get_todos_for_date(TDATE) == []
    assert db.get_todos_for_date(other)[0]["text"] == "mover"

def test_move_todo_va_al_final(test_db):
    db.add_todo("2026-06-10", "existente")
    db.add_todo(TDATE, "movido")
    tid = db.get_todos_for_date(TDATE)[0]["id"]
    db.move_todo(tid, "2026-06-10")
    todos = db.get_todos_for_date("2026-06-10")
    assert [t["text"] for t in todos] == ["existente", "movido"]

def test_delete_todo(test_db):
    db.add_todo(TDATE, "borrar")
    tid = db.get_todos_for_date(TDATE)[0]["id"]
    db.delete_todo(tid)
    assert db.get_todos_for_date(TDATE) == []

def test_todo_counts_range(test_db):
    db.add_todo(TDATE, "a")
    db.add_todo(TDATE, "b")
    tid = db.get_todos_for_date(TDATE)[1]["id"]
    db.toggle_todo(tid)
    counts = db.get_todo_counts_range("2026-06-01", "2026-06-30")
    assert counts[TDATE] == {"done": 1, "total": 2}

def test_reorder_todos(test_db):
    db.add_todo(TDATE, "a")
    db.add_todo(TDATE, "b")
    db.add_todo(TDATE, "c")
    ids = [t["id"] for t in db.get_todos_for_date(TDATE)]   # a, b, c
    db.reorder_todos(TDATE, [ids[2], ids[0], ids[1]])        # c, a, b
    todos = db.get_todos_for_date(TDATE)
    assert [t["text"] for t in todos] == ["c", "a", "b"]

def test_reorder_todos_acotado_al_dia(test_db):
    db.add_todo(TDATE, "propio")
    db.add_todo("2026-06-10", "ajeno")
    ajeno = db.get_todos_for_date("2026-06-10")[0]["id"]
    propio = db.get_todos_for_date(TDATE)[0]["id"]
    db.reorder_todos(TDATE, [ajeno, propio])   # el ajeno no debe verse afectado
    assert db.get_todos_for_date("2026-06-10")[0]["text"] == "ajeno"

def test_get_todos_range(test_db):
    db.add_todo("2026-06-08", "lun")
    db.add_todo("2026-06-09", "mar")
    db.add_todo("2026-07-01", "fuera")
    r = db.get_todos_range("2026-06-01", "2026-06-30")
    assert "2026-06-08" in r and "2026-06-09" in r
    assert "2026-07-01" not in r
    assert r["2026-06-08"][0]["text"] == "lun"


# ── Ajustes (settings) ───────────────────────────────────────────────────────────

def test_setting_default(test_db):
    assert db.get_setting("date_format") == "dmy"
    assert db.get_setting("inexistente", "x") == "x"

def test_set_and_get_setting(test_db):
    db.set_setting("date_format", "ymd")
    assert db.get_setting("date_format") == "ymd"

def test_set_setting_upsert(test_db):
    db.set_setting("k", "1")
    db.set_setting("k", "2")
    assert db.get_setting("k") == "2"

def test_get_all_settings_incluye_defaults(test_db):
    assert db.get_all_settings()["date_format"] == "dmy"
    db.set_setting("date_format", "mdy")
    assert db.get_all_settings()["date_format"] == "mdy"

def test_time_format_default(test_db):
    assert db.get_setting("time_format") == "24h"
    db.set_setting("time_format", "12h")
    assert db.get_setting("time_format") == "12h"

def test_theme_default(test_db):
    assert db.get_setting("theme") == "indigo"

def test_setting_huerfano_cae_al_default(test_db):
    # Un valor guardado que ya no es válido (ej. tema removido) cae al default en get_all_settings.
    db.set_setting("theme", "cobre")          # tema eliminado
    assert db.get_all_settings()["theme"] == "indigo"

def test_is_valid_db_rechaza_basura(test_db, tmp_path):
    bad = tmp_path / "bad.db"
    bad.write_bytes(b"no soy una base de datos")
    assert db.is_valid_db(str(bad)) is False

def test_snapshot_es_db_valida(test_db, tmp_path):
    snap = str(tmp_path / "snap.db")
    db.snapshot_to(snap)
    assert db.is_valid_db(snap) is True

def test_restore_reemplaza_y_hace_prerestore(test_db, tmp_path):
    db.add_note("2026-06-11", "original")
    snap = str(tmp_path / "snap.db")
    db.snapshot_to(snap)                       # snapshot con 1 nota
    db.add_note("2026-06-11", "nueva")         # ahora hay 2 en la DB activa
    assert len(db.get_notes_for_date("2026-06-11")) == 2
    ok, _ = db.restore_from(snap)              # restauro el snapshot (1 nota)
    assert ok is True
    assert len(db.get_notes_for_date("2026-06-11")) == 1
    # se generó un pre-restore backup en backups/ junto a la DB
    assert any(p.name.startswith("health-prerestore-") for p in (tmp_path / "backups").iterdir())

def test_restore_invalido_no_toca_nada(test_db, tmp_path):
    db.add_note("2026-06-11", "intacta")
    bad = tmp_path / "bad.db"
    bad.write_bytes(b"basura")
    ok, _ = db.restore_from(str(bad))
    assert ok is False
    assert len(db.get_notes_for_date("2026-06-11")) == 1   # sigue ahí

def test_week_start_default(test_db):
    assert db.get_setting("week_start") == "mon"

def test_start_view_default(test_db):
    assert db.get_setting("start_view") == "week"


# ── Visor de tareas: done_at, atrasadas y filtros ───────────────────────────────

def test_done_at_se_setea_y_se_limpia(test_db):
    db.add_todo(TDATE, "x")
    tid = db.get_todos_for_date(TDATE)[0]["id"]
    db.toggle_todo(tid)
    assert db.get_todos_for_date(TDATE)[0]["done_at"]        # timestamp local al cerrar
    db.toggle_todo(tid)
    assert db.get_todos_for_date(TDATE)[0]["done_at"] == ""  # reabrir lo borra

def test_get_overdue_todos_respeta_el_corte(test_db):
    db.add_todo("2026-06-01", "vieja")
    db.add_todo("2026-06-09", "del corte")
    db.add_todo("2026-06-15", "nueva")
    textos = [t["text"] for t in db.get_overdue_todos("2026-06-09")]
    assert textos == ["vieja"]   # el corte es exclusivo

def test_get_overdue_todos_ignora_las_hechas(test_db):
    db.add_todo("2026-06-01", "vieja")
    db.toggle_todo(db.get_todos_for_date("2026-06-01")[0]["id"])
    assert db.get_overdue_todos("2026-06-09") == []

def test_atrasada_no_se_puede_silenciar(test_db):
    """Una tarea vieja y abierta cuenta como atrasada siempre: no hay forma de silenciarla.
    Si alguien vuelve a colar lógica de silencio (la columna snoozed_until quedó vestigial
    en las DBs de sep 2026), este test lo caza."""
    db.add_todo("2026-06-01", "vieja")
    with db.get_db() as conn:
        if "snoozed_until" in db._columns(conn, "todos"):
            conn.execute("UPDATE todos SET snoozed_until = '2099-01-01'")
    assert len(db.get_overdue_todos("2026-06-09")) == 1

def test_count_overdue_todos(test_db):
    db.add_todo("2026-06-01", "a")
    db.add_todo("2026-06-02", "b")
    db.add_todo("2026-06-15", "c")
    assert db.count_overdue_todos("2026-06-09") == 2

def test_move_todos_bulk_deja_posiciones_densas(test_db):
    db.add_todo(TDATE, "ya estaba")
    db.add_todo("2026-06-01", "a")
    db.add_todo("2026-06-02", "b")
    ids = [db.get_todos_for_date("2026-06-01")[0]["id"], db.get_todos_for_date("2026-06-02")[0]["id"]]
    db.move_todos(ids, TDATE)
    assert [(t["text"], t["position"]) for t in db.get_todos_for_date(TDATE)] == [
        ("ya estaba", 0), ("a", 1), ("b", 2)]

def test_move_todos_lista_vacia_no_hace_nada(test_db):
    db.add_todo(TDATE, "a")
    db.move_todos([], TDATE)
    assert len(db.get_todos_for_date(TDATE)) == 1

def test_get_todos_filtered_por_estado(test_db):
    db.add_todo(TDATE, "hecha")
    db.add_todo(TDATE, "abierta")
    db.toggle_todo(db.get_todos_for_date(TDATE)[0]["id"])
    assert [t["text"] for t in db.get_todos_filtered(status="hechas")] == ["hecha"]
    assert [t["text"] for t in db.get_todos_filtered(status="pendientes")] == ["abierta"]
    assert len(db.get_todos_filtered(status="todas")) == 2

def test_get_todos_filtered_por_texto_y_fechas(test_db):
    db.add_todo("2026-06-01", "comprar pan")
    db.add_todo("2026-06-09", "comprar leche")
    db.add_todo("2026-07-01", "correr")
    assert len(db.get_todos_filtered(q="comprar")) == 2
    assert [t["text"] for t in db.get_todos_filtered(start="2026-06-05", end="2026-06-30")] == ["comprar leche"]
    assert len(db.get_todos_filtered()) == 3   # sin cotas trae todo

def test_migracion_agrega_columnas_sin_perder_filas(test_db):
    """Camino real de las DBs ya instaladas: la tabla todos nació sin done_at."""
    with db.get_db() as conn:
        conn.execute("DROP TABLE todos")
        conn.execute("CREATE TABLE todos (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     " todo_date TEXT NOT NULL, text TEXT NOT NULL, done INTEGER DEFAULT 0,"
                     " position INTEGER DEFAULT 0, created_at TEXT)")
        conn.execute("INSERT INTO todos (todo_date, text) VALUES (?,?)", (TDATE, "anterior"))
        # Una DB realmente vieja tiene el esquema viejo Y la versión vieja: init_db() usa
        # user_version como guarda, así que simular solo la mitad no es el caso real.
        conn.execute("PRAGMA user_version = 0")
    db.init_db()
    t = db.get_todos_for_date(TDATE)[0]
    assert t["text"] == "anterior"
    assert t["done_at"] == ""
    assert db.count_overdue_todos("2026-06-10") == 1


# ── Cimientos de sincronización: uid, updated_at y tombstones ────────────────────

def _utc_ahora():
    return datetime.now(timezone.utc).replace(tzinfo=None)

def test_toda_tabla_sincronizable_recibe_uid_y_updated_at(test_db):
    """Los triggers cubren las 7 tablas: si alguien agrega una a SYNCABLE sin trigger, cae acá."""
    db.add_note("2026-06-09", "n")
    db.add_todo("2026-06-09", "t")
    db.add_recurring_event({"title": "e", "color": "#fff", "recurrence": "daily",
                            "start_date": "2026-01-01", "end_date": ""})
    eid = db.get_recurring_events()[0]["id"]
    db.complete_event(eid, "2026-06-09")
    db.add_journal_category({"name": "c", "color": "#fff", "fields_json": "[]",
                             "show_in_calendar": 0})
    cid = db.get_journal_categories()[0]["id"]
    db.add_journal_entry({"category_id": cid, "entry_date": "2026-06-09",
                          "values_json": "{}", "tags": ""})
    db.add_chart(cid, "campo")
    with db.get_db() as conn:
        for t in db.SYNCABLE:
            faltan = conn.execute(
                f"SELECT COUNT(*) FROM {t} WHERE COALESCE(uid,'') = '' OR COALESCE(updated_at,'') = ''"
            ).fetchone()[0]
            assert faltan == 0, f"{t} quedó sin uid/updated_at"

def test_uid_es_unico_y_el_update_no_lo_cambia(test_db):
    db.add_note("2026-06-09", "a")
    db.add_note("2026-06-09", "b")
    n1, n2 = db.get_notes_for_date("2026-06-09")
    assert n1["uid"] != n2["uid"]
    db.update_note(n1["id"], "editada")
    assert db.get_notes_for_date("2026-06-09")[0]["uid"] == n1["uid"]

def test_update_mueve_updated_at(test_db):
    db.add_todo("2026-06-09", "x")
    tid = db.get_todos_for_date("2026-06-09")[0]["id"]
    with db.get_db() as conn:   # envejecer a mano para no depender del reloj
        conn.execute("UPDATE todos SET updated_at = '2020-01-01 00:00:00' WHERE id = ?", (tid,))
    db.update_todo(tid, "editada")
    assert db.get_todos_for_date("2026-06-09")[0]["updated_at"] > "2020-01-01 00:00:00"

def test_updated_at_es_utc_no_hora_local(test_db):
    """Va en UTC a propósito, al revés que created_at: es para comparar entre dispositivos y
    el caso de uso es viajar a otro huso. Si alguien lo 'corrige' a localtime, cae acá."""
    db.add_note("2026-06-09", "x")
    n = db.get_notes_for_date("2026-06-09")[0]
    delta = abs((datetime.fromisoformat(n["updated_at"]) - _utc_ahora()).total_seconds())
    assert delta < 60, f"updated_at={n['updated_at']} no parece UTC (delta {delta}s)"

def test_delete_deja_tombstone(test_db):
    db.add_note("2026-06-09", "borrame")
    n = db.get_notes_for_date("2026-06-09")[0]
    db.delete_note(n["id"])
    with db.get_db() as conn:
        row = conn.execute("SELECT tabla, uid FROM deletions").fetchone()
    assert (row["tabla"], row["uid"]) == ("notes", n["uid"])

def test_borrar_categoria_deja_tombstones_de_la_cascada(test_db):
    """delete_journal_category borra las entradas a mano (journal.py): los triggers tienen que
    dejar tombstone de la categoría Y de cada entrada, o el merge las resucitaría."""
    db.add_journal_category({"name": "c", "color": "#fff", "fields_json": "[]",
                             "show_in_calendar": 0})
    cid = db.get_journal_categories()[0]["id"]
    db.add_journal_entry({"category_id": cid, "entry_date": "2026-06-09",
                          "values_json": "{}", "tags": ""})
    db.delete_journal_category(cid)
    with db.get_db() as conn:
        tablas = {r["tabla"] for r in conn.execute("SELECT tabla FROM deletions").fetchall()}
    assert tablas == {"journal_categories", "journal_entries"}

def test_backfill_de_uid_en_filas_preexistentes(test_db):
    """Camino real de una DB instalada: la tabla no tiene ni la columna uid ni los triggers."""
    with db.get_db() as conn:
        conn.execute("DROP TABLE notes")
        conn.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY AUTOINCREMENT,"
                     " note_date TEXT NOT NULL, content TEXT NOT NULL, color TEXT DEFAULT '',"
                     " created_at TEXT)")
        conn.execute("INSERT INTO notes (note_date, content) VALUES ('2026-06-09','vieja')")
        conn.execute("PRAGMA user_version = 0")
    db.init_db()
    n = db.get_notes_for_date("2026-06-09")[0]
    assert n["content"] == "vieja"
    assert n["uid"] and len(n["uid"]) == 32
    # updated_at queda vacío a propósito: "original, nunca modificada" ordena antes que
    # cualquier fecha en el merge. Rellenarlo haría ganar al dispositivo que migró último.
    assert n["updated_at"] == ""

def test_reset_deja_la_db_usable(test_db):
    """user_version sobrevive al DROP y al VACUUM; si reset_db no la baja, el init_db()
    posterior se saltearía todo y la DB quedaría sin tablas."""
    db.add_note("2026-06-09", "x")
    db.reset_db()
    db.init_db()
    db.add_note("2026-06-10", "despues del reset")
    assert [n["content"] for n in db.get_notes_for_date("2026-06-10")] == ["despues del reset"]
    with db.get_db() as conn:
        trig = {r["name"] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='trigger'").fetchall()}
    # Derivado del esquema y no un número fijo: agregar una tabla sincronizable no debería
    # romper este test, pero olvidarse de sus triggers sí.
    esperados = {f"{t}_{suf}" for t in db.SYNCABLE for suf in ("uid", "upd", "del")}
    esperados |= {"settings_ins", "settings_upd"}
    assert trig == esperados
