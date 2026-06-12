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
    r = client.get("/", follow_redirects=True)   # "/" redirige a la vista de inicio (default: mes)
    assert r.status_code == 200
    assert b"Lunes" in r.data

def test_toggle_todo_preserva_ref_de_semana(client):
    """Tildar un to-do desde el día (llegado con ?ref=week) no rompe el volver contextual."""
    db.add_todo(DATE, "comprar pan")
    tid = db.get_todos_for_date(DATE)[0]["id"]
    r = client.post(f"/day/{DATE}/todo/{tid}/toggle",
                    headers={"Referer": f"http://localhost/day/{DATE}?ref=week"})
    assert r.headers["Location"] == f"/day/{DATE}?ref=week"
    # sin referer (o de otra página) cae al default sano
    r = client.post(f"/day/{DATE}/todo/{tid}/toggle")
    assert r.headers["Location"] == f"/day/{DATE}"


def test_dia_chips_de_categorias(client):
    """El alta de nota especial ofrece chips por categoría (no dropdown)."""
    import json
    db.add_journal_category({"name": "Ánimo", "color": "#e879b9",
        "fields_json": json.dumps([{"label": "Detalle", "type": "text"}]),
        "show_in_calendar": 1})
    body = client.get(f"/day/{DATE}").data.decode("utf-8")
    assert 'class="jcat-chip"' in body and "Ánimo" in body
    assert 'id="jday-cat-filter"' not in body   # filtro recién con 7+ categorías
    for i in range(7):
        db.add_journal_category({"name": f"Cat{i}", "color": "#6366f1",
            "fields_json": "[]", "show_in_calendar": 1})
    body = client.get(f"/day/{DATE}").data.decode("utf-8")
    assert 'id="jday-cat-filter"' in body


def test_home_redirige_segun_start_view(client):
    assert "/calendar/" in client.get("/").headers["Location"]   # default month
    db.set_setting("start_view", "today")
    assert "/day/" in client.get("/").headers["Location"]
    db.set_setting("start_view", "week")
    assert "/week/" in client.get("/").headers["Location"]

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


# ── Volver contextual (día → semana / calendario) ────────────────────────────────

def test_volver_desde_semana(client):
    r = client.get(f"/day/{DATE}?ref=week").data
    assert ("/week/" + DATE).encode() in r

def test_volver_desde_calendario(client):
    assert b"/calendar/2026/6" in client.get(f"/day/{DATE}?ref=cal").data

def test_volver_default_es_calendario(client):
    assert b"/calendar/2026/6" in client.get(f"/day/{DATE}").data

def test_guardar_tema(client):
    r = client.post("/ajustes/guardar", data={"theme": "oceano"})
    assert r.status_code == 302
    assert db.get_setting("theme") == "oceano"

def test_guardar_tema_invalido_se_ignora(client):
    client.post("/ajustes/guardar", data={"theme": "nope-no-existe"})
    assert db.get_setting("theme") == "indigo"

def test_ajustes_muestra_swatches(client):
    body = client.get("/ajustes").data
    assert b"theme-swatch" in body
    assert "Bosque".encode() in body

def test_ajustes_volver_contextual(client):
    body = client.get("/ajustes?back=/calendar/2026/6").data
    assert b'href="/calendar/2026/6"' in body

def test_ajustes_volver_default_calendario(client):
    body = client.get("/ajustes").data
    assert b"Calendario" in body   # fallback cuando no hay back

def test_guardar_ajustes_preserva_back(client):
    r = client.post("/ajustes/guardar", data={"theme": "oceano", "back": "/week/2026-06-11"})
    assert r.status_code == 302
    assert "2026-06-11" in r.headers["Location"]   # back propagado a /ajustes

def test_back_externo_se_ignora(client):
    r = client.post("/ajustes/guardar", data={"theme": "oceano", "back": "https://evil.com"})
    assert "evil.com" not in r.headers["Location"]

def test_journal_preserva_back(client):
    r = client.post("/journal/add", data={"name": "Test", "back": "/calendar/2026/6"})
    assert r.status_code == 302
    assert "calendar" in r.headers["Location"] and "journal" in r.headers["Location"]

def test_backup_descarga_db_valida(client):
    r = client.get("/backup")
    assert r.status_code == 200
    assert "attachment" in r.headers.get("Content-Disposition", "")
    assert r.data[:16] == b"SQLite format 3\x00"

def test_restore_valido_reemplaza_datos(client, tmp_path):
    import io
    other = str(tmp_path / "other.db")
    db.snapshot_to(other)                      # copia válida de la DB de test
    import sqlite3
    con = sqlite3.connect(other)
    con.execute("INSERT INTO notes (note_date, content) VALUES ('2026-06-11','desde-backup')")
    con.commit(); con.close()
    data = open(other, "rb").read()
    r = client.post("/restore", data={"dbfile": (io.BytesIO(data), "backup.db")},
                    content_type="multipart/form-data")
    assert r.status_code == 302
    assert "datos=ok" in r.headers["Location"]
    assert any(n["content"] == "desde-backup" for n in db.get_notes_for_date("2026-06-11"))

def test_restore_invalido_rechazado(client):
    import io
    r = client.post("/restore", data={"dbfile": (io.BytesIO(b"no db"), "x.db")},
                    content_type="multipart/form-data")
    assert r.status_code == 302
    assert "err-invalid" in r.headers["Location"]

def test_restore_sin_archivo(client):
    r = client.post("/restore", data={}, content_type="multipart/form-data")
    assert r.status_code == 302
    assert "err-nofile" in r.headers["Location"]

def test_reset_borra_todo_con_frase_exacta(client):
    db.add_note("2026-06-11", "se-va-a-borrar")
    r = client.post("/reset", data={"confirm_text": "BORRAR TODO"})
    assert r.status_code == 302
    assert "reset-ok" in r.headers["Location"]
    assert db.get_notes_for_date("2026-06-11") == []

def test_reset_sin_frase_no_borra(client):
    db.add_note("2026-06-11", "sobrevive")
    for malo in ("", "borrar todo", "BORRAR", "BORRARTODO"):
        r = client.post("/reset", data={"confirm_text": malo})
        assert r.status_code == 302
        assert "err-reset-confirm" in r.headers["Location"]
    assert len(db.get_notes_for_date("2026-06-11")) == 1

def test_reset_deja_backup_prereset(client, test_db):
    import os, glob
    db.add_note("2026-06-11", "estaba-antes")
    client.post("/reset", data={"confirm_text": "BORRAR TODO"})
    backups = glob.glob(os.path.join(os.path.dirname(test_db), "health-prereset-*.db"))
    assert backups, "no se creó el backup pre-reset"
    assert db.is_valid_db(backups[0])   # el backup conserva el estado previo

def test_reset_app_sigue_funcionando(client):
    client.post("/reset", data={"confirm_text": "BORRAR TODO"})
    assert client.get("/", follow_redirects=True).status_code == 200

def test_reset_preserva_back(client):
    r = client.post("/reset", data={"confirm_text": "nope", "back": "/week/2026-06-11"})
    assert "2026-06-11" in r.headers["Location"]

def test_datos_volver_contextual(client):
    body = client.get("/export?back=/calendar/2026/6").data
    assert b'href="/calendar/2026/6"' in body

def test_restore_preserva_back(client):
    import io
    r = client.post("/restore", data={"dbfile": (io.BytesIO(b"no db"), "x.db"), "back": "/week/2026-06-11"},
                    content_type="multipart/form-data")
    assert r.status_code == 302
    assert "2026-06-11" in r.headers["Location"]

def test_guardar_inicio_semana(client):
    client.post("/ajustes/guardar", data={"week_start": "sun"})
    assert db.get_setting("week_start") == "sun"

def test_agenda_dow_por_celda(client):
    # El weekday por celda (visible solo en modo agenda) sale en mes y semana.
    mes = client.get("/calendar/2026/6").data.decode("utf-8")
    sem = client.get("/week/2026-06-11").data.decode("utf-8")
    assert 'cal-agenda-dow">Jueves' in mes   # 2026-06-11 es jueves
    assert 'cal-agenda-dow">Jueves' in sem

def test_agenda_dow_respeta_inicio_de_semana(client):
    # Con semana iniciando en domingo, la primera columna del mes es Domingo.
    client.post("/ajustes/guardar", data={"week_start": "sun"})
    mes = client.get("/calendar/2026/6").data.decode("utf-8")
    assert 'cal-agenda-dow">Domingo' in mes

def test_calendario_inicio_domingo(client):
    db.set_setting("week_start", "sun")
    body = client.get("/calendar/2026/6").data.decode("utf-8")
    assert body.index("Domingo") < body.index("Lunes")

def test_calendario_inicio_lunes(client):
    body = client.get("/calendar/2026/6").data.decode("utf-8")
    assert body.index("Lunes") < body.index("Domingo")
