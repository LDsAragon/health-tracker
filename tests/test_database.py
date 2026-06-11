"""
Operaciones de base de datos — cada test usa una DB temporal aislada.
Verifica CRUD de notas, eventos recurrentes y completaciones.
"""
from datetime import date, timedelta
import database as db

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
