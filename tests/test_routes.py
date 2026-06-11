"""
Tests de rutas HTTP — verifica status codes, redirects y contenido clave.
Usa el fixture `client` (Flask test client con DB aislada).
"""
import database as db

DATE = "2026-06-09"

EV_BASE = {
    "title": "Evento test",
    "color": "#6366f1",
    "recurrence": "daily",
    "start_date": "2020-01-01",
    "end_date": "",
}


# ── Vistas principales ────────────────────────────────────────────────────────

def test_calendario_carga(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"Lunes" in r.data

def test_calendario_mes_especifico(client):
    assert client.get("/calendar/2026/6").status_code == 200

def test_vista_dia(client):
    assert client.get(f"/day/{DATE}").status_code == 200

def test_vista_semana(client):
    r = client.get(f"/week/{DATE}")
    assert r.status_code == 200
    assert b"Lunes" in r.data

def test_pagina_recurring(client):
    assert client.get("/recurring").status_code == 200

def test_pagina_export(client):
    assert client.get("/export").status_code == 200

def test_busqueda_sin_query(client):
    assert client.get("/search").status_code == 200

def test_busqueda_con_resultados(client):
    client.post(f"/day/{DATE}/note/add",
                data={"content": "fui al gimnasio", "color": "", "next": "day"})
    r = client.get("/search?q=gimnasio")
    assert r.status_code == 200
    assert b"gimnasio" in r.data

def test_busqueda_sin_resultados(client):
    r = client.get("/search?q=xyz_inexistente")
    assert r.status_code == 200
    assert b"xyz_inexistente" in r.data  # query aparece en el mensaje "no se encontró"


# ── Notas ─────────────────────────────────────────────────────────────────────

def test_agregar_nota_redirige_a_dia(client):
    r = client.post(f"/day/{DATE}/note/add",
                    data={"content": "nota", "color": "", "next": "day"})
    assert r.status_code == 302
    assert f"/day/{DATE}" in r.headers["Location"]

def test_agregar_nota_redirige_a_calendario(client):
    r = client.post(f"/day/{DATE}/note/add",
                    data={"content": "nota", "color": "", "next": "calendar"})
    assert r.status_code == 302
    assert "/calendar/" in r.headers["Location"]

def test_agregar_nota_redirige_a_semana(client):
    r = client.post(f"/day/{DATE}/note/add",
                    data={"content": "nota", "color": "", "next": "week"})
    assert r.status_code == 302
    assert "/week/" in r.headers["Location"]

def test_nota_aparece_en_dia(client):
    client.post(f"/day/{DATE}/note/add",
                data={"content": "nota visible unica", "color": "", "next": "day"})
    r = client.get(f"/day/{DATE}")
    assert b"nota visible unica" in r.data

def test_editar_nota(client):
    client.post(f"/day/{DATE}/note/add",
                data={"content": "original", "color": "", "next": "day"})
    nid = db.get_notes_for_date(DATE)[0]["id"]
    client.post(f"/day/{DATE}/note/{nid}/edit",
                data={"content": "editada", "color": "#22c55e"})
    r = client.get(f"/day/{DATE}")
    assert b"editada" in r.data

def test_eliminar_nota(client):
    client.post(f"/day/{DATE}/note/add",
                data={"content": "borrar esta", "color": "", "next": "day"})
    nid = db.get_notes_for_date(DATE)[0]["id"]
    client.post(f"/day/{DATE}/note/{nid}/delete")
    assert db.get_notes_for_date(DATE) == []

def test_nota_vacia_no_se_guarda(client):
    client.post(f"/day/{DATE}/note/add",
                data={"content": "   ", "color": "", "next": "day"})
    assert db.get_notes_for_date(DATE) == []


# ── Eventos recurrentes ───────────────────────────────────────────────────────

def test_agregar_evento_recurrente(client):
    client.post("/recurring/add", data={
        "title": "Medicacion", "color": "#6366f1",
        "rtype": "daily", "start_date": "2026-01-01",
    })
    assert client.get("/recurring").status_code == 200
    assert len(db.get_recurring_events()) == 1

def test_evento_semanal_guarda_dias(client):
    client.post("/recurring/add", data={
        "title": "Gym", "color": "#22c55e",
        "rtype": "weekly", "weekdays": ["1", "3", "5"],
        "start_date": "2026-01-01",
    })
    ev = db.get_recurring_events()[0]
    assert ev["recurrence"] == "weekly:1,3,5"

def test_editar_evento_recurrente(client):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    client.post(f"/recurring/{eid}/edit", data={
        "title": "Nombre nuevo", "color": "#ef4444",
        "rtype": "daily", "start_date": "2026-01-01", "end_date": "2026-12-31",
    })
    ev = db.get_recurring_events()[0]
    assert ev["title"] == "Nombre nuevo"
    assert ev["end_date"] == "2026-12-31"

def test_eliminar_evento_recurrente(client):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    r = client.post(f"/recurring/{eid}/delete")
    assert r.status_code == 302
    assert db.get_recurring_events() == []

def test_eliminar_evento_modo_all(client):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    client.post(f"/recurring/{eid}/delete", data={"mode": "all"})
    assert db.get_recurring_events() == []

def test_eliminar_evento_modo_future_conserva_evento(client):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    r = client.post(f"/recurring/{eid}/delete", data={"mode": "future"})
    assert r.status_code == 302
    events = db.get_recurring_events()
    assert len(events) == 1                 # el evento sigue (no se borra)
    assert events[0]["end_date"]            # quedó con fecha de corte

def test_toggle_visibilidad_recurrente(client):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    client.post(f"/recurring/{eid}/visibility", data={"show": "0"})
    assert db.get_recurring_events()[0]["show_in_calendar"] == 0
    client.post(f"/recurring/{eid}/visibility", data={"show": "1"})
    assert db.get_recurring_events()[0]["show_in_calendar"] == 1


# ── Completaciones ────────────────────────────────────────────────────────────

def test_completar_evento(client):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    r = client.post(f"/day/{DATE}/event/{eid}/complete",
                    data={"note": "lo hice"})
    assert r.status_code == 302
    comps = db.get_completions_range(DATE, DATE)
    assert comps[DATE][eid]["status"] == "done"

def test_saltear_evento(client):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    r = client.post(f"/day/{DATE}/event/{eid}/skip",
                    data={"note": "estaba ocupado"})
    assert r.status_code == 302
    comps = db.get_completions_range(DATE, DATE)
    assert comps[DATE][eid]["status"] == "skipped"

def test_deshacer_completacion(client):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    client.post(f"/day/{DATE}/event/{eid}/complete", data={"note": ""})
    client.post(f"/day/{DATE}/event/{eid}/uncomplete")
    assert db.get_completions_range(DATE, DATE) == {}

def test_chip_hecho_aparece_en_dia(client):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    client.post(f"/day/{DATE}/event/{eid}/complete", data={"note": ""})
    r = client.get(f"/day/{DATE}")
    assert b"day-chip-done" in r.data

def test_chip_salteado_aparece_en_dia(client):
    db.add_recurring_event(EV_BASE)
    eid = db.get_recurring_events()[0]["id"]
    client.post(f"/day/{DATE}/event/{eid}/skip", data={"note": ""})
    r = client.get(f"/day/{DATE}")
    assert b"day-chip-skipped" in r.data


# ── Exportar y backup ─────────────────────────────────────────────────────────

def test_export_download_retorna_csv(client):
    client.post(f"/day/{DATE}/note/add",
                data={"content": "nota para exportar", "color": "", "next": "day"})
    r = client.get("/export/download?start=2026-06-01&end=2026-06-30")
    assert r.status_code == 200
    assert b"fecha,tipo,detalle" in r.data
    assert b"nota" in r.data

def test_export_download_sin_params_redirige(client):
    r = client.get("/export/download")
    assert r.status_code == 302

def test_backup_descarga_archivo(client):
    r = client.get("/backup")
    assert r.status_code == 200
    assert "attachment" in r.headers.get("Content-Disposition", "")


# ── To-dos diarios ──────────────────────────────────────────────────────────────

def test_agregar_todo(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "objetivo"})
    todos = db.get_todos_for_date(DATE)
    assert len(todos) == 1 and todos[0]["text"] == "objetivo"

def test_todo_vacio_no_se_guarda(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "   "})
    assert db.get_todos_for_date(DATE) == []

def test_toggle_todo_ruta(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "x"})
    tid = db.get_todos_for_date(DATE)[0]["id"]
    r = client.post(f"/day/{DATE}/todo/{tid}/toggle")
    assert r.status_code == 302
    assert db.get_todos_for_date(DATE)[0]["done"] == 1

def test_editar_todo_ruta(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "viejo"})
    tid = db.get_todos_for_date(DATE)[0]["id"]
    client.post(f"/day/{DATE}/todo/{tid}/edit", data={"text": "nuevo"})
    assert db.get_todos_for_date(DATE)[0]["text"] == "nuevo"

def test_mover_todo_ruta(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "m"})
    tid = db.get_todos_for_date(DATE)[0]["id"]
    client.post(f"/day/{DATE}/todo/{tid}/move", data={"new_date": "2026-06-15"})
    assert db.get_todos_for_date(DATE) == []
    assert db.get_todos_for_date("2026-06-15")[0]["text"] == "m"

def test_eliminar_todo_ruta(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "d"})
    tid = db.get_todos_for_date(DATE)[0]["id"]
    client.post(f"/day/{DATE}/todo/{tid}/delete")
    assert db.get_todos_for_date(DATE) == []

def test_contador_todos_en_calendario(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "a"})
    client.post(f"/day/{DATE}/todo/add", data={"text": "b"})
    r = client.get("/calendar/2026/6")
    assert b"cal-todo-badge" in r.data
    assert b"0/2" in r.data

def test_contador_todos_en_semana(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "a"})
    r = client.get(f"/week/{DATE}")
    assert b"cal-todo-badge" in r.data

def test_sin_todos_no_hay_badge_en_calendario(client):
    r = client.get("/calendar/2026/6")
    assert b"cal-todo-badge" not in r.data

def test_reordenar_todos_ruta(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "a"})
    client.post(f"/day/{DATE}/todo/add", data={"text": "b"})
    ids = [t["id"] for t in db.get_todos_for_date(DATE)]
    r = client.post(f"/day/{DATE}/todos/reorder", data={"order": f"{ids[1]},{ids[0]}"})
    assert r.status_code == 204
    assert [t["text"] for t in db.get_todos_for_date(DATE)] == ["b", "a"]

def test_mover_todo_ajax(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "m"})
    tid = db.get_todos_for_date(DATE)[0]["id"]
    r = client.post(f"/todos/{tid}/move", data={"date": "2026-06-15"})
    assert r.status_code == 204
    assert db.get_todos_for_date(DATE) == []
    assert db.get_todos_for_date("2026-06-15")[0]["text"] == "m"

def test_todos_aparecen_en_semana(client):
    client.post(f"/day/{DATE}/todo/add", data={"text": "semana visible"})
    r = client.get(f"/week/{DATE}")
    assert b"week-todo" in r.data
    assert "semana visible".encode() in r.data


# ── Ajustes ──────────────────────────────────────────────────────────────────────

def test_pagina_ajustes(client):
    r = client.get("/ajustes")
    assert r.status_code == 200
    assert "Ajustes".encode() in r.data

def test_guardar_ajuste_formato_fecha(client):
    r = client.post("/ajustes/guardar", data={"date_format": "mdy"})
    assert r.status_code == 302
    assert db.get_setting("date_format") == "mdy"

def test_guardar_ajuste_formato_invalido_se_ignora(client):
    client.post("/ajustes/guardar", data={"date_format": "xxx"})
    assert db.get_setting("date_format") == "dmy"

def test_guardar_ajuste_formato_hora(client):
    r = client.post("/ajustes/guardar", data={"date_format": "dmy", "time_format": "12h"})
    assert r.status_code == 302
    assert db.get_setting("time_format") == "12h"
