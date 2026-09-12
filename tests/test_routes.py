"""
Tests de rutas HTTP — verifica status codes, redirects y contenido clave.
Usa el fixture `client` (Flask test client con DB aislada).
"""
from datetime import date, timedelta

from bitacora import database as db

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

def _dado(monkeypatch, sale):
    """Fija el dado de la mascotita: sale=True gana siempre, False pierde siempre."""
    from bitacora.routes import day
    monkeypatch.setattr(day.random, "random", lambda: 0.0 if sale else 0.99)


def test_toggle_todo_preserva_ref_de_semana(client, monkeypatch):
    """Tildar un to-do desde el día (llegado con ?ref=week) no rompe el volver contextual."""
    _dado(monkeypatch, False)   # sin mascotita, para aislar lo que importa acá
    db.add_todo(DATE, "comprar pan")
    tid = db.get_todos_for_date(DATE)[0]["id"]
    r = client.post(f"/day/{DATE}/todo/{tid}/toggle",
                    headers={"Referer": f"http://localhost/day/{DATE}?ref=week"})
    assert r.headers["Location"] == f"/day/{DATE}?ref=week"
    # sin referer (al desmarcar: no celebra)
    r = client.post(f"/day/{DATE}/todo/{tid}/toggle")
    assert r.headers["Location"] == f"/day/{DATE}"


def test_mascotita_no_sale_en_cada_completado(client, monkeypatch):
    """Aun activada sale solo a veces: en cada tilde se vuelve invasiva."""
    db.add_todo(DATE, "comprar pan")
    tid = db.get_todos_for_date(DATE)[0]["id"]
    ref = {"Referer": f"http://localhost/day/{DATE}?ref=week"}

    _dado(monkeypatch, True)
    assert "pet=1" in client.post(f"/day/{DATE}/todo/{tid}/toggle", headers=ref).headers["Location"]

    client.post(f"/day/{DATE}/todo/{tid}/toggle")          # destildar para volver a tildar
    _dado(monkeypatch, False)
    assert "pet=1" not in client.post(f"/day/{DATE}/todo/{tid}/toggle", headers=ref).headers["Location"]


def test_mascotita_prendida_por_defecto(client):
    """Una base nueva trae el gatito. Ojo: asoma solo a veces, no en cada completado."""
    from bitacora.appconfig import DEFAULT_SETTINGS
    assert DEFAULT_SETTINGS["pet"] == "cat"
    assert db.get_all_settings()["pet"] == "cat"


def test_mascotita_apagada_no_dibuja_aunque_gane_el_dado(client, monkeypatch):
    """El ?pet=1 puede quedar en la URL (link pegado, recarga): con la mascota apagada la
    plantilla igual no la dibuja. Apaga a mano porque ya no es el default."""
    _dado(monkeypatch, True)
    db.set_setting("pet", "none")
    assert "pet-overlay" not in client.get(f"/day/{DATE}?pet=1").data.decode()
    db.set_setting("pet", "cat")
    assert "pet-overlay" in client.get(f"/day/{DATE}?pet=1").data.decode()


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
    assert "/week/" in client.get("/").headers["Location"]       # default: semana
    db.set_setting("start_view", "month")
    assert "/calendar/" in client.get("/").headers["Location"]
    db.set_setting("start_view", "today")
    assert "/day/" in client.get("/").headers["Location"]

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

def test_pagina_version(client):
    """Sin _version.py (modo dev) la pagina lo dice, en vez de mentir una version."""
    body = client.get("/version").data.decode()
    assert "developer" in body
    assert "Buscar actualizaciones" in body


def test_version_tiene_tab_propio_en_el_navbar(client):
    """El tab sale de base.html: tiene que aparecer en cualquier pagina."""
    for ruta in ("/ajustes", "/journal", "/recurring"):
        assert 'href="/version' in client.get(ruta).data.decode(), ruta


def test_ajustes_ya_no_tiene_la_seccion_de_version(client):
    """Se mudo a su propio tab: no duplicar el chequeo en dos paginas."""
    body = client.get("/ajustes").data.decode()
    assert "upd-check-btn" not in body


def test_update_status_expone_notas_y_reinstalable(client):
    j = client.get("/update/status").get_json()
    assert set(("checked", "available", "current", "latest", "notes", "can_reinstall")) <= set(j)
    # En dev no hay version propia: reinstalar copiaria el release sobre el repo.
    assert j["can_reinstall"] is False


def test_update_check_responde(client, monkeypatch):
    """Sin red: _do_check traga la excepcion y deja checked=True."""
    from bitacora.escritorio import updater
    previo = dict(updater._state)
    def _sin_red(*a, **k):
        raise OSError("sin red")
    monkeypatch.setattr(updater.urllib.request, "urlopen", _sin_red)
    monkeypatch.setattr(updater.threading, "Thread",
                        lambda target, args=(), daemon=None: type(
                            "T", (), {"start": lambda self: target(*args)})())
    try:
        assert client.post("/update/check").get_json()["ok"] is True
        assert client.get("/update/status").get_json()["checked"] is True
    finally:
        updater._state.clear()
        updater._state.update(previo)


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

def test_vaciar_el_perfil_con_frase_exacta(client):
    db.add_note("2026-06-11", "se-va-a-borrar")
    r = client.post("/reset", data={"confirm_text": "BORRAR DATOS"})
    assert r.status_code == 302
    assert "reset-ok" in r.headers["Location"]
    assert db.get_notes_for_date("2026-06-11") == []

def test_vaciar_sin_frase_no_borra(client):
    db.add_note("2026-06-11", "sobrevive")
    # "BORRAR TODO" es la frase VIEJA: sonaba a que borraba todos los perfiles cuando en
    # realidad vaciaba uno. Tiene que fallar, para que el hábito no dispare nada.
    for malo in ("", "BORRAR TODO", "borrar datos", "BORRAR", "BORRARDATOS"):
        r = client.post("/reset", data={"confirm_text": malo})
        assert r.status_code == 302
        assert "err-reset-confirm" in r.headers["Location"]
    assert len(db.get_notes_for_date("2026-06-11")) == 1

def test_vaciar_deja_backup_previo(client, test_db):
    import os, glob
    db.add_note("2026-06-11", "estaba-antes")
    client.post("/reset", data={"confirm_text": "BORRAR DATOS"})
    backups = glob.glob(os.path.join(os.path.dirname(test_db), "backups", "health-prereset-*.db"))
    assert backups, "no se creó el backup pre-reset en backups/"
    assert db.is_valid_db(backups[0])   # el backup conserva el estado previo

def test_vaciar_deja_la_app_funcionando(client):
    client.post("/reset", data={"confirm_text": "BORRAR DATOS"})
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


# ── Visor de tareas (/tareas) ─────────────────────────────────────────────────
# Las rutas usan date.today(), así que las fechas van relativas a hoy. "Atrasada" con el
# default (todo_overdue_from=week) exige cruzar el inicio de semana: 10 días lo garantiza.

HOY = date.today()
VIEJA = (HOY - timedelta(days=10)).isoformat()
MAS_VIEJA = (HOY - timedelta(days=40)).isoformat()


def _tid(fecha, texto):
    return [t for t in db.get_todos_for_date(fecha) if t["text"] == texto][0]["id"]


def test_visor_tareas_carga(client):
    db.add_todo(VIEJA, "pendiente vieja")
    db.add_todo(HOY.isoformat(), "para hoy")
    r = client.get("/tareas")
    assert r.status_code == 200
    assert b"pendiente vieja" in r.data
    assert "Quedaron sin cerrar".encode() in r.data

def test_visor_sin_atrasadas_no_muestra_el_bloque(client):
    db.add_todo(HOY.isoformat(), "para hoy")
    r = client.get("/tareas")
    assert "Quedaron sin cerrar".encode() not in r.data

def test_visor_filtros_basura_no_rompen(client):
    db.add_todo(HOY.isoformat(), "x")
    assert client.get("/tareas?estado=zzz&periodo=nada").status_code == 200

def test_visor_busqueda_filtra(client):
    db.add_todo(HOY.isoformat(), "comprar pan")
    db.add_todo(HOY.isoformat(), "correr")
    r = client.get("/tareas?estado=todas&q=comprar")
    assert b"comprar pan" in r.data and b"correr" not in r.data

def test_visor_periodo_acota_el_listado(client):
    """Una tarea cerrada solo sale por el listado, que sí respeta el período."""
    db.add_todo(MAS_VIEJA, "muy vieja")
    db.toggle_todo(_tid(MAS_VIEJA, "muy vieja"))
    assert b"muy vieja" not in client.get("/tareas?estado=hechas&periodo=30").data
    assert b"muy vieja" in client.get("/tareas?estado=hechas&periodo=todo").data

def test_visor_atrasadas_ignoran_el_periodo(client):
    """Lo que quedó sin cerrar se avisa siempre, por viejo que sea."""
    db.add_todo(MAS_VIEJA, "muy vieja")
    assert b"muy vieja" in client.get("/tareas?periodo=30").data

def test_contadores_no_dependen_del_periodo(client):
    """"Para hoy" y "Próximas" son estados absolutos: con una ventana que termina hoy,
    atarlos al período los dejaba siempre en 0."""
    db.add_todo(HOY.isoformat(), "de hoy")
    db.add_todo((HOY + timedelta(days=5)).isoformat(), "futura")
    for periodo in ("hoy", "7", "30"):
        html = client.get(f"/tareas?periodo={periodo}").data.decode()
        # El bloque del resumen trae los cuatro números; buscamos el de Próximas
        i = html.index("Próximas")
        assert ">1<" in html[i - 120:i], f"Próximas quedó en 0 con periodo={periodo}"

def test_agregar_tarea_desde_el_visor(client):
    fecha = (HOY + timedelta(days=4)).isoformat()
    client.post("/tareas/agregar", data={"text": "comprar pan", "fecha": fecha})
    assert [t["text"] for t in db.get_todos_for_date(fecha)] == ["comprar pan"]

def test_agregar_sin_fecha_cae_a_hoy(client):
    client.post("/tareas/agregar", data={"text": "para hoy", "fecha": ""})
    assert [t["text"] for t in db.get_todos_for_date(HOY.isoformat())] == ["para hoy"]

def test_agregar_con_fecha_basura_no_guarda_fecha_invalida(client):
    """add_todo no valida el formato: una fecha basura dejaría la tarea inaccesible."""
    client.post("/tareas/agregar", data={"text": "sana", "fecha": "chau"})
    assert [t["todo_date"] for t in db.get_todos_filtered()] == [HOY.isoformat()]

def test_agregar_texto_vacio_no_crea_nada(client):
    client.post("/tareas/agregar", data={"text": "   ", "fecha": HOY.isoformat()})
    assert db.get_todos_filtered() == []

def test_agregar_preserva_los_filtros(client):
    r = client.post("/tareas/agregar", data={
        "text": "x", "fecha": HOY.isoformat(), "estado": "hechas", "periodo": "7", "q": "z"})
    loc = r.headers["Location"]
    assert "estado=hechas" in loc and "periodo=7" in loc and "q=z" in loc

def test_avisa_cuando_la_tarea_nueva_cae_fuera_de_la_vista(client):
    """Con período Hoy, algo agendado para dentro de 10 días no se vería: sin el aviso
    parecería que no se guardó."""
    lejos = (HOY + timedelta(days=10)).isoformat()
    db.add_todo(lejos, "lejana")
    assert "Tarea agregada".encode() in client.get(f"/tareas?periodo=hoy&nueva={lejos}").data

def test_no_avisa_si_la_tarea_nueva_se_ve(client):
    db.add_todo(HOY.isoformat(), "de hoy")
    r = client.get(f"/tareas?periodo=hoy&nueva={HOY.isoformat()}")
    assert "Tarea agregada".encode() not in r.data

def test_aviso_con_fecha_basura_se_ignora(client):
    assert client.get("/tareas?nueva=chau").status_code == 200

def test_visor_abre_en_hoy(client):
    """El visor arranca en Hoy: es lo que se mira el 90% de las veces."""
    db.add_todo(HOY.isoformat(), "de hoy")
    db.add_todo((HOY - timedelta(days=20)).isoformat(), "de hace 20 dias")
    html = client.get("/tareas?estado=todas").data.decode()
    assert "Tareas de hoy" in html
    assert "de hace 20 dias" not in html.split("stats-section")[-1]

def test_periodo_hoy_es_una_ventana_exacta(client):
    """Ni ayer ni mañana: el botón lista exactamente lo que dice."""
    db.add_todo((HOY - timedelta(days=1)).isoformat(), "de ayer")
    db.add_todo(HOY.isoformat(), "de hoy")
    db.add_todo((HOY + timedelta(days=1)).isoformat(), "de manana")
    r = client.get("/tareas?periodo=hoy&estado=todas")
    assert b"de hoy" in r.data
    assert b"de ayer" not in r.data and b"de manana" not in r.data

def test_periodo_proximas_lista_solo_futuro(client):
    db.add_todo(HOY.isoformat(), "de hoy")
    db.add_todo((HOY + timedelta(days=3)).isoformat(), "en tres dias")
    r = client.get("/tareas?periodo=proximas&estado=todas")
    assert b"en tres dias" in r.data and b"de hoy" not in r.data

def test_sin_cerrar_se_ve_con_cualquier_periodo(client):
    """El bloque de atrasadas ignora el período: lo viejo se avisa siempre."""
    db.add_todo(MAS_VIEJA, "muy vieja")
    for periodo in ("hoy", "7", "proximas"):
        assert b"muy vieja" in client.get(f"/tareas?periodo={periodo}").data

def test_mover_a_hoy_desde_el_visor(client):
    db.add_todo(VIEJA, "traeme")
    client.post(f"/tareas/{_tid(VIEJA, 'traeme')}/mover", data={"dias": "0"})
    assert [t["text"] for t in db.get_todos_for_date(HOY.isoformat())] == ["traeme"]

def test_mover_a_manana(client):
    db.add_todo(VIEJA, "manana")
    client.post(f"/tareas/{_tid(VIEJA, 'manana')}/mover", data={"dias": "1"})
    esperado = (HOY + timedelta(days=1)).isoformat()
    assert [t["text"] for t in db.get_todos_for_date(esperado)] == ["manana"]
    assert db.get_todos_for_date(VIEJA) == []

def test_mover_una_semana_es_relativo_a_hoy(client):
    """+1 sem sobre algo viejo tiene que caer la semana que viene, no seguir en el pasado."""
    db.add_todo(MAS_VIEJA, "semana")
    client.post(f"/tareas/{_tid(MAS_VIEJA, 'semana')}/mover", data={"dias": "7"})
    esperado = (HOY + timedelta(days=7)).isoformat()
    assert [t["text"] for t in db.get_todos_for_date(esperado)] == ["semana"]

def test_mover_con_dias_invalido_no_mueve_nada(client):
    db.add_todo(VIEJA, "quieta")
    client.post(f"/tareas/{_tid(VIEJA, 'quieta')}/mover", data={"dias": "999"})
    assert [t["text"] for t in db.get_todos_for_date(VIEJA)] == ["quieta"]

def test_toggle_y_borrar_desde_el_visor(client):
    db.add_todo(VIEJA, "a"); tid = _tid(VIEJA, "a")
    client.post(f"/tareas/{tid}/toggle")
    assert db.get_todos_for_date(VIEJA)[0]["done"] == 1
    client.post(f"/tareas/{tid}/borrar")
    assert db.get_todos_for_date(VIEJA) == []

def test_traer_todas_a_hoy(client):
    db.add_todo(VIEJA, "a")
    db.add_todo(MAS_VIEJA, "b")
    client.post("/tareas/traer-todas")
    assert sorted(t["text"] for t in db.get_todos_for_date(HOY.isoformat())) == ["a", "b"]

def test_acciones_del_visor_preservan_filtros(client):
    db.add_todo(VIEJA, "a")
    r = client.post(f"/tareas/{_tid(VIEJA, 'a')}/toggle",
                    data={"estado": "hechas", "periodo": "7", "q": "a"})
    assert r.status_code == 302
    assert "estado=hechas" in r.headers["Location"]
    assert "periodo=7" in r.headers["Location"]
    assert "q=a" in r.headers["Location"]


# ── Aviso de tareas sin cerrar ────────────────────────────────────────────────

def test_alerta_json(client):
    db.add_todo(VIEJA, "sin cerrar")
    a = client.get("/tareas/alerta").get_json()
    assert a["count"] == 1 and a["should_alert"] is True
    assert a["oldest"] == VIEJA
    assert a["items"][0]["text"] == "sin cerrar"
    assert a["week_changed"] is False        # primer aviso: no hay semana previa registrada

def test_alerta_sin_atrasadas_no_avisa(client):
    db.add_todo(HOY.isoformat(), "de hoy")
    assert client.get("/tareas/alerta").get_json()["should_alert"] is False

def test_alerta_respeta_el_ajuste(client):
    db.add_todo(VIEJA, "x")
    db.set_setting("todo_alert", "badge")
    a = client.get("/tareas/alerta").get_json()
    assert a["count"] == 1 and a["should_alert"] is False   # cuenta, pero no interrumpe

def test_alerta_detecta_la_semana_nueva(client):
    db.add_todo(VIEJA, "x")
    client.post("/tareas/alerta/visto")
    assert client.get("/tareas/alerta").get_json()["week_changed"] is False
    db.set_setting("todos_last_week_seen", (HOY - timedelta(days=21)).isoformat())
    assert client.get("/tareas/alerta").get_json()["week_changed"] is True

def test_overdue_from_day_incluye_ayer(client):
    ayer = (HOY - timedelta(days=1)).isoformat()
    db.add_todo(ayer, "de ayer")
    db.set_setting("todo_overdue_from", "day")
    assert client.get("/tareas/alerta").get_json()["count"] == 1

def test_badge_de_atrasadas_en_el_navbar(client):
    db.add_todo(VIEJA, "x")
    assert b"nav-badge" in client.get("/tareas").data
    db.set_setting("todo_alert", "off")
    assert b"nav-badge" not in client.get("/tareas").data

def test_tab_tareas_se_puede_ocultar(client):
    assert "📋 Tareas".encode() in client.get("/calendar/2026/6").data
    db.set_setting("show_todos", "hide")
    assert "📋 Tareas".encode() not in client.get("/calendar/2026/6").data


# ── Zona peligrosa: las tres acciones y sus frases ───────────────────────────

def _con_perfiles(tmp_path, monkeypatch, cuantos=2):
    from bitacora import profiles
    monkeypatch.setenv("HT_PERFILES", str(tmp_path))
    p = profiles.crear("Principal")
    profiles.usar(p["slug"])
    for i in range(cuantos - 1):
        profiles.crear(f"Otro {i}")
    db.init_db()
    return profiles

def test_borrar_todos_los_perfiles_desde_datos(client, tmp_path, monkeypatch):
    profs = _con_perfiles(tmp_path, monkeypatch)
    r = client.post("/perfiles/borrar-todos",
                    data={"confirm_text": "BORRAR TODOS LOS PERFILES"})
    assert r.status_code == 302 and "todos-ok-2" in r.headers["Location"]
    assert len(profs.listar()) == 1

def test_borrar_todos_con_la_frase_mal_no_borra_nada(client, tmp_path, monkeypatch):
    profs = _con_perfiles(tmp_path, monkeypatch)
    # "BORRAR TODO" es la frase vieja del vaciado: acá tampoco tiene que servir, o el hábito
    # de tipearla borraría TODOS los perfiles en vez de vaciar uno.
    for malo in ("", "BORRAR TODO", "BORRAR DATOS", "borrar todos los perfiles"):
        r = client.post("/perfiles/borrar-todos", data={"confirm_text": malo})
        assert "err-todos-confirm" in r.headers["Location"], malo
    assert len(profs.listar()) == 2

def test_borrar_el_perfil_activo_desde_datos(client, tmp_path, monkeypatch):
    profs = _con_perfiles(tmp_path, monkeypatch)
    activo = profs.activo()["slug"]
    r = client.post("/perfiles/borrar",
                    data={"slug": activo, "confirm_text": "BORRAR PERFIL"})
    assert r.status_code == 302
    assert activo not in {p["slug"] for p in profs.listar()}

def test_con_un_solo_perfil_el_boton_de_eliminar_esta_deshabilitado(client, tmp_path, monkeypatch):
    _con_perfiles(tmp_path, monkeypatch, cuantos=1)
    html = client.get("/export").data.decode()
    assert "único perfil que tenés" in html
    assert "BORRAR PERFIL" not in html        # ni siquiera se ofrece la frase

def test_con_dos_perfiles_se_ofrecen_las_tres_acciones(client, tmp_path, monkeypatch):
    _con_perfiles(tmp_path, monkeypatch, cuantos=2)
    html = client.get("/export").data.decode()
    for frase in ("BORRAR DATOS", "BORRAR PERFIL", "BORRAR TODOS LOS PERFILES"):
        assert frase in html, frase

def test_ajustes_ofrece_borrar_el_perfil_activo(client, tmp_path, monkeypatch):
    """El selector de borrado excluía el activo. Ahora lo incluye, como pidió Matías: la misma
    capacidad en los dos lados. Hay que mirar DENTRO del selector: el slug del activo también
    aparece en el form de "Usar este", así que buscarlo en todo el HTML no probaría nada."""
    profs = _con_perfiles(tmp_path, monkeypatch, cuantos=2)
    html = client.get("/ajustes").data.decode()
    ini = html.index('id="borrar-perfil-slug"')
    selector = html[ini:html.index("</select>", ini)]
    assert f'value="{profs.activo()["slug"]}"' in selector
    assert "el que estás usando" in selector

def test_borrar_el_perfil_desde_datos_vuelve_a_datos(client, tmp_path, monkeypatch):
    """Sin el campo volver_a, borrar desde Datos te dejaba en Ajustes, que no es donde estabas."""
    profs = _con_perfiles(tmp_path, monkeypatch, cuantos=2)
    r = client.post("/perfiles/borrar", data={"slug": profs.activo()["slug"],
                                              "confirm_text": "BORRAR PERFIL",
                                              "volver_a": "datos"})
    assert "/export" in r.headers["Location"] and "perfil-borrado" in r.headers["Location"]

def test_borrar_el_perfil_desde_ajustes_vuelve_a_ajustes(client, tmp_path, monkeypatch):
    profs = _con_perfiles(tmp_path, monkeypatch, cuantos=2)
    r = client.post("/perfiles/borrar", data={"slug": profs.activo()["slug"],
                                              "confirm_text": "BORRAR PERFIL"})
    assert "/ajustes" in r.headers["Location"]
