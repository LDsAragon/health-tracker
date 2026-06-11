"""
Tests para el sistema de journal — categorías y entradas.
"""
import json
import database as db

DATE = "2026-06-09"
DATE2 = "2026-06-10"

CAT_BASE = {
    "name": "Emociones",
    "color": "#6366f1",
    "fields_json": json.dumps([
        {"label": "¿Qué sentí?", "placeholder": "Describí..."},
        {"label": "¿Qué pensé?", "placeholder": "Pensamientos..."},
    ]),
    "show_in_calendar": 1,
}


def _add_cat(test_db, **overrides):
    data = {**CAT_BASE, **overrides}
    db.add_journal_category(data)
    return db.get_journal_categories()[0]["id"]


def _add_entry(test_db, cat_id, entry_date=DATE, values=None, tags=""):
    values_json = json.dumps(values or {"¿Qué sentí?": "ansioso"})
    db.add_journal_entry({
        "category_id": cat_id,
        "entry_date": entry_date,
        "values_json": values_json,
        "tags": tags,
    })
    return db.get_journal_entries_for_date(entry_date)[0]["id"]


# ── Categorías ────────────────────────────────────────────────────────────────

def test_add_and_get_category(test_db):
    _add_cat(test_db)
    cats = db.get_journal_categories()
    assert len(cats) == 1
    assert cats[0]["name"] == "Emociones"
    assert cats[0]["show_in_calendar"] == 1
    assert isinstance(cats[0]["fields"], list)
    assert len(cats[0]["fields"]) == 2


def test_category_fields_parsed(test_db):
    _add_cat(test_db)
    cat = db.get_journal_categories()[0]
    assert cat["fields"][0]["label"] == "¿Qué sentí?"
    assert cat["fields"][1]["label"] == "¿Qué pensé?"


def test_update_category(test_db):
    cid = _add_cat(test_db)
    db.update_journal_category(cid, {
        "name": "Sueño",
        "color": "#22c55e",
        "fields_json": json.dumps([{"label": "Horas", "placeholder": ""}]),
        "show_in_calendar": 0,
    })
    cat = db.get_journal_categories()[0]
    assert cat["name"] == "Sueño"
    assert cat["show_in_calendar"] == 0
    assert len(cat["fields"]) == 1


def test_delete_category(test_db):
    cid = _add_cat(test_db)
    db.delete_journal_category(cid)
    assert db.get_journal_categories() == []


def test_delete_category_cascades_entries(test_db):
    cid = _add_cat(test_db)
    _add_entry(test_db, cid)
    db.delete_journal_category(cid)
    assert db.get_journal_entries_for_date(DATE) == []


def test_no_active_categories_returns_empty(test_db):
    assert db.get_journal_categories() == []


# ── Entradas ──────────────────────────────────────────────────────────────────

def test_add_and_get_entry(test_db):
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, values={"¿Qué sentí?": "feliz"})
    entries = db.get_journal_entries_for_date(DATE)
    assert len(entries) == 1
    assert entries[0]["values"]["¿Qué sentí?"] == "feliz"
    assert entries[0]["category_name"] == "Emociones"
    assert entries[0]["category_color"] == "#6366f1"


def test_entry_has_category_fields(test_db):
    cid = _add_cat(test_db)
    _add_entry(test_db, cid)
    entry = db.get_journal_entries_for_date(DATE)[0]
    assert isinstance(entry["category_fields"], list)
    assert entry["category_fields"][0]["label"] == "¿Qué sentí?"


def test_multiple_entries_same_day(test_db):
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, values={"¿Qué sentí?": "mañana"})
    _add_entry(test_db, cid, values={"¿Qué sentí?": "tarde"})
    entries = db.get_journal_entries_for_date(DATE)
    assert len(entries) == 2


def test_entry_with_tags(test_db):
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, tags="ansiedad,trabajo")
    entry = db.get_journal_entries_for_date(DATE)[0]
    assert entry["tags"] == "ansiedad,trabajo"


def test_update_entry(test_db):
    cid = _add_cat(test_db)
    eid = _add_entry(test_db, cid, values={"¿Qué sentí?": "original"})
    db.update_journal_entry(eid, {
        "values_json": json.dumps({"¿Qué sentí?": "actualizado"}),
        "tags": "nuevo-tag",
    })
    entry = db.get_journal_entries_for_date(DATE)[0]
    assert entry["values"]["¿Qué sentí?"] == "actualizado"
    assert entry["tags"] == "nuevo-tag"


def test_delete_entry(test_db):
    cid = _add_cat(test_db)
    eid = _add_entry(test_db, cid)
    db.delete_journal_entry(eid)
    assert db.get_journal_entries_for_date(DATE) == []


def test_get_entries_for_date_excludes_other_dates(test_db):
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, entry_date=DATE)
    _add_entry(test_db, cid, entry_date=DATE2)
    assert len(db.get_journal_entries_for_date(DATE)) == 1
    assert len(db.get_journal_entries_for_date(DATE2)) == 1


def test_get_entries_range(test_db):
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, entry_date="2026-06-01")
    _add_entry(test_db, cid, entry_date="2026-06-15")
    _add_entry(test_db, cid, entry_date="2026-07-01")
    result = db.get_journal_entries_range("2026-06-01", "2026-06-30")
    assert "2026-06-01" in result
    assert "2026-06-15" in result
    assert "2026-07-01" not in result


def test_get_entries_range_includes_show_in_calendar(test_db):
    cid = _add_cat(test_db, show_in_calendar=1)
    _add_entry(test_db, cid)
    result = db.get_journal_entries_range(DATE, DATE)
    entry = result[DATE][0]
    assert entry["show_in_calendar"] == 1


# ── Rutas ─────────────────────────────────────────────────────────────────────

def test_pagina_journal(client):
    r = client.get("/journal")
    assert r.status_code == 200
    assert "Notas especiales".encode() in r.data


def test_agregar_categoria(client):
    r = client.post("/journal/add", data={
        "name": "Emociones",
        "color": "#6366f1",
        "show_in_calendar": "1",
        "field_label[]": ["¿Qué sentí?"],
        "field_placeholder[]": ["Describí..."],
    })
    assert r.status_code == 302
    cats = db.get_journal_categories()
    assert len(cats) == 1
    assert cats[0]["name"] == "Emociones"
    assert len(cats[0]["fields"]) == 1


def test_agregar_categoria_sin_nombre_no_guarda(client):
    client.post("/journal/add", data={"name": "  ", "color": "#6366f1"})
    assert db.get_journal_categories() == []


def test_editar_categoria(client):
    client.post("/journal/add", data={"name": "Original", "color": "#6366f1"})
    cid = db.get_journal_categories()[0]["id"]
    client.post(f"/journal/{cid}/edit", data={
        "name": "Modificada", "color": "#22c55e",
    })
    assert db.get_journal_categories()[0]["name"] == "Modificada"


def test_eliminar_categoria(client):
    client.post("/journal/add", data={"name": "Test", "color": "#6366f1"})
    cid = db.get_journal_categories()[0]["id"]
    r = client.post(f"/journal/{cid}/delete")
    assert r.status_code == 302
    assert db.get_journal_categories() == []


def test_agregar_entry_desde_dia(client):
    client.post("/journal/add", data={"name": "Emociones", "color": "#6366f1"})
    cid = db.get_journal_categories()[0]["id"]
    r = client.post(f"/day/{DATE}/journal/add", data={
        "category_id": cid,
        "values_json": json.dumps({"campo": "valor"}),
        "tags": "test",
        "next": "day",
    })
    assert r.status_code == 302
    entries = db.get_journal_entries_for_date(DATE)
    assert len(entries) == 1
    assert entries[0]["tags"] == "test"


def test_agregar_entry_redirige_a_calendario(client):
    client.post("/journal/add", data={"name": "Test", "color": "#6366f1"})
    cid = db.get_journal_categories()[0]["id"]
    r = client.post(f"/day/{DATE}/journal/add", data={
        "category_id": cid, "values_json": "{}", "next": "calendar",
    })
    assert "/calendar/" in r.headers["Location"]


def test_agregar_entry_redirige_a_semana(client):
    client.post("/journal/add", data={"name": "Test", "color": "#6366f1"})
    cid = db.get_journal_categories()[0]["id"]
    r = client.post(f"/day/{DATE}/journal/add", data={
        "category_id": cid, "values_json": "{}", "next": "week",
    })
    assert "/week/" in r.headers["Location"]


def test_editar_entry(client):
    client.post("/journal/add", data={"name": "Test", "color": "#6366f1"})
    cid = db.get_journal_categories()[0]["id"]
    client.post(f"/day/{DATE}/journal/add", data={
        "category_id": cid, "values_json": json.dumps({"f": "original"}), "next": "day",
    })
    eid = db.get_journal_entries_for_date(DATE)[0]["id"]
    client.post(f"/day/{DATE}/journal/{eid}/edit", data={
        "values_json": json.dumps({"f": "editado"}), "tags": "nuevo",
    })
    entry = db.get_journal_entries_for_date(DATE)[0]
    assert entry["values"]["f"] == "editado"
    assert entry["tags"] == "nuevo"


def test_eliminar_entry(client):
    client.post("/journal/add", data={"name": "Test", "color": "#6366f1"})
    cid = db.get_journal_categories()[0]["id"]
    client.post(f"/day/{DATE}/journal/add", data={
        "category_id": cid, "values_json": "{}", "next": "day",
    })
    eid = db.get_journal_entries_for_date(DATE)[0]["id"]
    r = client.post(f"/day/{DATE}/journal/{eid}/delete")
    assert r.status_code == 302
    assert db.get_journal_entries_for_date(DATE) == []


def test_entry_aparece_en_dia(client):
    client.post("/journal/add", data={
        "name": "Emociones", "color": "#ef4444",
        "field_label[]": ["¿Qué sentí?"],
        "field_placeholder[]": [""],
    })
    cid = db.get_journal_categories()[0]["id"]
    client.post(f"/day/{DATE}/journal/add", data={
        "category_id": cid,
        "values_json": json.dumps({"¿Qué sentí?": "ansioso hoy"}),
        "next": "day",
    })
    r = client.get(f"/day/{DATE}")
    assert b"Emociones" in r.data
    assert "ansioso hoy".encode() in r.data


def test_campo_emotion_wheel_guardado(test_db):
    """Un campo tipo emotion-wheel se guarda y recupera como string con separador >."""
    eid = _add_cat(test_db, fields_json=json.dumps([
        {"label": "Emoción", "type": "emotion-wheel", "placeholder": ""},
    ]))
    ew_val = "Tristeza > Deprimido > Impotente"
    db.add_journal_entry({
        "category_id": eid,
        "entry_date": DATE,
        "values_json": json.dumps({"Emoción": ew_val}),
        "tags": "",
    })
    entries = db.get_journal_entries_for_date(DATE)
    assert entries[0]["values"]["Emoción"] == ew_val


def test_categoria_con_tipo_emotion_wheel(test_db):
    """El tipo de campo se preserva en fields_json al guardar y recuperar."""
    fields = [{"label": "Estado", "type": "emotion-wheel", "placeholder": ""}]
    db.add_journal_category({
        "name": "Estado emocional",
        "color": "#a855f7",
        "fields_json": json.dumps(fields),
        "show_in_calendar": 0,
    })
    cat = db.get_journal_categories()[0]
    assert cat["fields"][0]["type"] == "emotion-wheel"
    assert cat["fields"][0]["label"] == "Estado"


def test_badge_aparece_en_calendario(client):
    client.post("/journal/add", data={
        "name": "Estados", "color": "#6366f1", "show_in_calendar": "1",
    })
    cid = db.get_journal_categories()[0]["id"]
    client.post(f"/day/{DATE}/journal/add", data={
        "category_id": cid, "values_json": "{}", "next": "day",
    })
    r = client.get("/calendar/2026/6")
    assert b"chip-journal" in r.data


# ── Tipos de campo nuevos (escala / sino / opciones / numero) ────────────────────

def test_agregar_categoria_con_tipos_nuevos(client):
    r = client.post("/journal/add", data={
        "name": "Bienestar", "color": "#6366f1",
        "field_label[]": ["Ánimo", "Cumplí", "Momento", "Peso"],
        "field_type[]": ["escala", "sino", "opciones", "numero"],
        "field_placeholder[]": ["", "", "Desayuno, Almuerzo, Cena", "kg"],
    })
    assert r.status_code == 302
    fields = db.get_journal_categories()[0]["fields"]
    assert [f["type"] for f in fields] == ["escala", "sino", "opciones", "numero"]
    assert fields[2]["placeholder"] == "Desayuno, Almuerzo, Cena"

def test_entry_round_trip_tipos_nuevos(client):
    client.post("/journal/add", data={
        "name": "Bienestar", "color": "#6366f1",
        "field_label[]": ["Ánimo", "Cumplí", "Momento", "Peso"],
        "field_type[]": ["escala", "sino", "opciones", "numero"],
        "field_placeholder[]": ["", "", "Desayuno, Almuerzo, Cena", "kg"],
    })
    cid = db.get_journal_categories()[0]["id"]
    vals = {"Ánimo": "4", "Cumplí": "1", "Momento": "Almuerzo", "Peso": "82"}
    client.post(f"/day/{DATE}/journal/add", data={
        "category_id": cid, "values_json": json.dumps(vals), "next": "day",
    })
    entry = db.get_journal_entries_for_date(DATE)[0]
    assert entry["values"] == vals
    body = client.get(f"/day/{DATE}").data.decode("utf-8")
    assert "Almuerzo" in body           # opciones (chip)
    assert "✓ Sí" in body               # sino
    assert "82 kg" in body              # numero + unidad
    assert "fb-scale-display" in body   # escala numérica (puntos)

def test_escala_con_etiquetas_muestra_label(client):
    client.post("/journal/add", data={
        "name": "Ánimo", "color": "#6366f1",
        "field_label[]": ["Ánimo"],
        "field_type[]": ["escala"],
        "field_placeholder[]": ["Mal, Regular, Bien"],
    })
    cid = db.get_journal_categories()[0]["id"]
    client.post(f"/day/{DATE}/journal/add", data={
        "category_id": cid, "values_json": json.dumps({"Ánimo": "3"}), "next": "day",
    })
    body = client.get(f"/day/{DATE}").data.decode("utf-8")
    assert "Bien" in body   # 3ª etiqueta de la escala
