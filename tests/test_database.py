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
