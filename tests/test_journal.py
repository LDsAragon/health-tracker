"""
Tests para el sistema de journal — categorías y entradas.
"""
import json
from bitacora import database as db
from bitacora.fieldtypes import FIELD_TYPES

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


def test_badge_calendario_tildado_por_defecto(client):
    """El form de nueva categoría arranca con 'mostrar en calendario' tildado."""
    body = client.get("/journal").data.decode("utf-8")
    assert 'name="show_in_calendar" value="1" checked' in body


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
    })
    assert r.status_code == 302
    entries = db.get_journal_entries_for_date(DATE)
    assert len(entries) == 1
    assert entries[0]["tags"] == "test"


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


# ── Migración de renombres (campos y opciones) ──────────────────────────────

def _cat_trabajo(client):
    client.post("/journal/add", data={
        "name": "Trabajo", "color": "#14b8a6", "show_in_calendar": "1",
        "field_label[]": ["Proyecto", "Horas"],
        "field_type[]": ["opciones", "duracion"],
        "field_placeholder[]": ["A, B", ""],
        "field_chart[]": ["0", "1"],
    })
    cid = db.get_journal_categories()[0]["id"]
    db.add_journal_entry({"category_id": cid, "entry_date": DATE,
                          "values_json": json.dumps({"Proyecto": "A", "Horas": "120"}),
                          "tags": ""})
    return cid


def test_renombrar_campo_migra_entradas_y_graficos(client):
    cid = _cat_trabajo(client)
    db.add_chart(cid, "Horas", "", 90, "Proyecto", "week", "")
    client.post(f"/journal/{cid}/edit", data={
        "name": "Trabajo", "color": "#14b8a6", "show_in_calendar": "1",
        "field_oldlabel[]": ["Proyecto", "Horas"],
        "field_label[]": ["Proyecto", "Tiempo"],          # Horas → Tiempo
        "field_type[]": ["opciones", "duracion"],
        "field_placeholder[]": ["A, B", ""],
        "field_chart[]": ["0", "1"],
    })
    vals = db.get_journal_entries_for_date(DATE)[0]["values"]
    assert vals == {"Proyecto": "A", "Tiempo": "120"}
    assert db.get_charts()[0]["field_label"] == "Tiempo"


def test_fila_reemplazada_o_tipo_cambiado_no_migra(client):
    cid = _cat_trabajo(client)
    client.post(f"/journal/{cid}/edit", data={
        "name": "Trabajo", "color": "#14b8a6", "show_in_calendar": "1",
        "field_oldlabel[]": ["Proyecto", "Horas", ""],
        "field_label[]": ["Proyecto", "Calidad", "Foco"],  # Horas→Calidad CON cambio de tipo + fila nueva
        "field_type[]": ["opciones", "escala", "escala"],
        "field_placeholder[]": ["A, B", "", ""],
        "field_chart[]": ["0", "0", "0"],
    })
    vals = db.get_journal_entries_for_date(DATE)[0]["values"]
    assert vals == {"Proyecto": "A", "Horas": "120"}      # intacto


def test_agregar_y_quitar_opciones_no_toca_entradas(client):
    cid = _cat_trabajo(client)
    client.post(f"/journal/{cid}/edit", data={
        "name": "Trabajo", "color": "#14b8a6", "show_in_calendar": "1",
        "field_oldlabel[]": ["Proyecto", "Horas"],
        "field_label[]": ["Proyecto", "Horas"],
        "field_type[]": ["opciones", "duracion"],
        "field_placeholder[]": ["B, C", ""],               # salió A, entró C: NO es rename
        "field_chart[]": ["0", "1"],
    })
    vals = db.get_journal_entries_for_date(DATE)[0]["values"]
    assert vals["Proyecto"] == "A"                         # el histórico conserva su valor


def test_renombrar_opcion_explicito_migra_y_actualiza_lista(client):
    cid = _cat_trabajo(client)
    client.post(f"/journal/{cid}/edit", data={
        "name": "Trabajo", "color": "#14b8a6", "show_in_calendar": "1",
        "field_oldlabel[]": ["Proyecto", "Horas"],
        "field_label[]": ["Proyecto", "Horas"],
        "field_type[]": ["opciones", "duracion"],
        "field_placeholder[]": ["A, B", ""],
        "field_chart[]": ["0", "1"],
        "opt_rename_sel": "Proyecto||A",
        "opt_rename_to": "Cliente A",
    })
    vals = db.get_journal_entries_for_date(DATE)[0]["values"]
    assert vals["Proyecto"] == "Cliente A"
    cat = db.get_journal_categories()[0]
    assert cat["fields"][0]["placeholder"] == "Cliente A, B"


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


def test_rango_display_12h(client):
    db.set_setting("time_format", "12h")
    client.post("/journal/add", data={
        "name": "Sueño", "color": "#6366f1",
        "field_label[]": ["Horario"], "field_type[]": ["rango"], "field_placeholder[]": [""],
    })
    cid = db.get_journal_categories()[0]["id"]
    client.post(f"/day/{DATE}/journal/add", data={
        "category_id": cid, "values_json": json.dumps({"Horario": "23:00-08:00"}), "next": "day",
    })
    body = client.get(f"/day/{DATE}").data.decode("utf-8")
    assert "11:00 PM" in body
    assert "8:00 AM" in body


def test_dia_alta_rapida_colapsable(client):
    client.post("/journal/add", data={"name": "Sueño", "color": "#3b82f6"})
    body = client.get(f"/day/{DATE}").data.decode("utf-8")
    assert "Agregar nota especial" in body   # toggle de nota especial
    assert "rapida-collapsed" in body        # botón colapsado de la nota rápida


def test_categoria_campo_chart_flag(client):
    client.post("/journal/add", data={
        "name": "Peso", "color": "#6366f1",
        "field_label[]": ["Peso", "Nota"],
        "field_type[]": ["numero", "text"],
        "field_placeholder[]": ["kg", ""],
        "field_chart[]": ["1", "0"],
    })
    fields = db.get_journal_categories()[0]["fields"]
    assert fields[0].get("chart") is True
    assert "chart" not in fields[1]


def test_la_lista_de_especiales_se_renderiza_vacia(client, test_db):
    """Las dos secciones del día tienen que verse iguales, y el que da el aire es el contenedor
    de la lista. Estaba detrás de un `if journal_entries`, así que en un día sin notas especiales
    el título quedaba pegado al "+ Agregar" mientras el de notas rápidas mantenía su espacio.
    """
    _add_cat(test_db)
    html = client.get(f"/day/{DATE}").data.decode()
    assert 'class="day-journal-list"' in html


# ── El selector de categoría del alta ────────────────────────────────────────

def test_el_selector_de_categoria_colapsa_al_elegir(client, test_db):
    """Elegida la categoría, la fila de chips se reemplaza por el chip elegido + "Cambiar".

    Lo arma el JS, así que acá se fija lo que necesita para poder hacerlo: la fila de destino y
    el color de cada chip (el formulario se tiñe con él).
    """
    _add_cat(test_db)
    html = client.get(f"/day/{DATE}").data.decode()
    assert 'id="jday-cat-elegida"' in html
    assert 'id="jday-cat-cambiar"' in html
    assert 'data-color="#6366f1"' in html


def test_el_calendario_y_la_semana_no_traen_alta_de_notas_especiales(client, test_db):
    """El alta de nota especial vive solo en el día (446638b: "vista muy cargada").

    Cuando se sacó el formulario de esas dos celdas quedó vivo todo su JavaScript, llamando a
    elementos que ya no existían: ~45 líneas por plantilla que nunca corrieron, más el JSON de
    todas las categorías serializado en cada carga para nadie. Tripwire para que no vuelva.
    """
    _add_cat(test_db)
    for url in ("/calendar/2026/6", f"/week/{DATE}"):
        html = client.get(url).data.decode()
        for muerto in ("toggleJForm", "updateJFields", "submitJEntry", "JCATS"):
            assert muerto not in html, f"{muerto} en {url}"


# ── Borrar una categoría ─────────────────────────────────────────────────────

def test_borrar_una_categoria_hace_backup_antes(test_db, tmp_path):
    """Es la operación más destructiva de la feature: se lleva la categoría Y todas sus notas.

    Cualquier camino destructivo de la app deja su snapshot antes; hasta un renombre de campo
    hace el suyo. Este era el único que borraba sin red.
    """
    cid = _add_cat(test_db)
    _add_entry(test_db, cid)
    db.delete_journal_category(cid)
    assert any(p.name.startswith("health-prejournal-")
               for p in (tmp_path / "backups").iterdir())


def test_la_confirmacion_de_borrar_dice_cuantas_notas_se_van(client, test_db):
    """"y todas sus notas" no deja saber si son dos o doscientas."""
    cid = _add_cat(test_db)
    assert "No tiene ninguna nota guardada" in client.get("/journal").data.decode()

    _add_entry(test_db, cid, entry_date=DATE)
    assert "la nota que tiene guardada" in client.get("/journal").data.decode()

    _add_entry(test_db, cid, entry_date=DATE2)
    html = client.get("/journal").data.decode()
    assert "y sus 2 notas" in html
    assert "Se guarda un backup antes de borrar" in html


def test_el_conteo_por_categoria_no_mezcla_categorias(test_db):
    uno = _add_cat(test_db)
    db.add_journal_category({**CAT_BASE, "name": "Sueño"})
    otro = [c["id"] for c in db.get_journal_categories() if c["id"] != uno][0]
    _add_entry(test_db, uno)
    _add_entry(test_db, otro, entry_date=DATE2)
    _add_entry(test_db, otro, entry_date=DATE2)
    assert db.count_journal_entries_by_category() == {uno: 1, otro: 2}


# ── El editor de campos ──────────────────────────────────────────────────────

def test_la_fila_de_un_campo_dice_cuantas_notas_lo_usan(client, test_db):
    """Quitar un campo esconde para siempre lo guardado, y antes no había forma de saberlo."""
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, values={"¿Qué sentí?": "ansioso", "¿Qué pensé?": ""})
    _add_entry(test_db, cid, entry_date=DATE2, values={"¿Qué sentí?": "tranquilo"})
    assert db.journal_field_usage() == {cid: {"¿Qué sentí?": 2}}   # el vacío no cuenta
    assert 'data-usos="2"' in client.get("/journal").data.decode()


def test_reordenar_campos_no_se_lee_como_un_renombre(client, test_db):
    """Mover una fila mueve su `field_oldlabel[]` con ella, así que no hay nada que migrar.

    Si se leyera como renombre, reordenar dos campos intercambiaría los valores guardados de
    todas las entradas — justo el daño que el orden venía a evitar.
    """
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, values={"¿Qué sentí?": "ansioso", "¿Qué pensé?": "nada"})
    client.post(f"/journal/{cid}/edit", data={
        "name": "Emociones", "color": "#6366f1",
        "field_oldlabel[]":    ["¿Qué pensé?", "¿Qué sentí?"],
        "field_label[]":       ["¿Qué pensé?", "¿Qué sentí?"],
        "field_type[]":        ["text", "text"],
        "field_placeholder[]": ["", ""],
        "field_chart[]":       ["0", "0"],
    })
    assert [f["label"] for f in db.get_journal_categories()[0]["fields"]] ==         ["¿Qué pensé?", "¿Qué sentí?"]
    vals = db.get_journal_entries_for_date(DATE)[0]["values"]
    assert vals == {"¿Qué sentí?": "ansioso", "¿Qué pensé?": "nada"}


def test_una_fila_que_no_viaja_quita_el_campo_y_deja_el_resto_alineado(client, test_db):
    """Es lo que hace el ✕ confirmado: la fila entera va `disabled`, así que no postea ninguno de
    sus arreglos paralelos y los índices de los demás campos siguen coincidiendo."""
    cid = _add_cat(test_db)
    client.post(f"/journal/{cid}/edit", data={
        "name": "Emociones", "color": "#6366f1",
        "field_oldlabel[]":    ["¿Qué pensé?"],
        "field_label[]":       ["¿Qué pensé?"],
        "field_type[]":        ["text"],
        "field_placeholder[]": ["Pensamientos..."],
        "field_chart[]":       ["0"],
    })
    fields = db.get_journal_categories()[0]["fields"]
    assert [f["label"] for f in fields] == ["¿Qué pensé?"]
    assert fields[0]["placeholder"] == "Pensamientos..."


# ── Archivar ─────────────────────────────────────────────────────────────────

def test_archivar_la_saca_del_alta_del_dia_pero_no_de_lo_anotado(client, test_db):
    cid = _add_cat(test_db)
    _add_entry(test_db, cid)
    client.post(f"/journal/{cid}/archivar", data={"activa": "0"})

    html = client.get(f"/day/{DATE}").data.decode()
    assert 'data-id="%d"' % cid not in html      # ya no se puede elegir para una nota nueva
    assert "ansioso" in html                     # pero lo anotado sigue ahí
    assert db.get_journal_categories() == []
    assert len(db.get_journal_categories(incluir_archivadas=True)) == 1


def test_archivar_no_saca_lo_anotado_de_estadisticas(client, test_db):
    """⚠️ Tripwire del fallo callado de esta feature.

    Si archivar filtrara también donde se LEE, meses de datos desaparecerían de los gráficos, de
    "Tiempo por actividad" y de las emociones sin que nada avise. Archivar es sobre dónde se
    escribe, nunca sobre dónde se lee.
    """
    db.add_journal_category({
        "name": "Sueño", "color": "#3b82f6", "show_in_calendar": 1,
        "fields_json": json.dumps([
            {"label": "Horas", "type": "duracion", "chart": True},
            {"label": "Emoción", "type": "emotion-wheel"},
        ]),
    })
    cid = db.get_journal_categories()[0]["id"]
    _add_entry(test_db, cid, values={"Horas": "480", "Emoción": "Alegre > Contento"})
    client.post(f"/journal/{cid}/archivar", data={"activa": "0"})

    assert [f["label"] for f in db.chartable_fields()] == ["Horas"]
    assert [t["name"] for t in db.tiempo_comparado(DATE, DATE)] == ["Sueño"]
    assert db.emociones_frecuentes(DATE, DATE)["ruedas"]["willcox"]


def test_desarchivar_la_devuelve_al_alta(client, test_db):
    cid = _add_cat(test_db)
    client.post(f"/journal/{cid}/archivar", data={"activa": "0"})
    client.post(f"/journal/{cid}/archivar", data={"activa": "1"})
    assert len(db.get_journal_categories()) == 1
    assert 'data-id="%d"' % cid in client.get(f"/day/{DATE}").data.decode()


def test_una_categoria_archivada_se_sigue_pudiendo_editar(client, test_db):
    """journal_view y el edit leen con incluir_archivadas: sin eso, guardar una archivada
    perdería sus campos (old_cat sale None y no hay con qué comparar)."""
    cid = _add_cat(test_db)
    client.post(f"/journal/{cid}/archivar", data={"activa": "0"})
    html = client.get("/journal").data.decode()
    assert "Archivadas" in html and "Desarchivar" in html


# ── Búsqueda ─────────────────────────────────────────────────────────────────

def test_la_busqueda_encuentra_una_nota_especial_por_su_texto(client, test_db):
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, values={"¿Qué sentí?": "una ansiedad rara antes de la reunión"})
    html = client.get("/search?q=ansiedad").data.decode()
    assert "una ansiedad rara" in html
    assert "Emociones" in html                 # con el chip de su categoría
    assert "1 resultado" in html


def test_la_busqueda_encuentra_una_nota_especial_por_su_tag(client, test_db):
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, values={"¿Qué sentí?": "tranquilo"}, tags="trabajo, tarde")
    assert "tranquilo" in client.get("/search?q=trabajo").data.decode()


def test_la_busqueda_NO_matchea_la_etiqueta_de_un_campo(client, test_db):
    """⚠️ Tripwire del LIKE sobre values_json.

    Ese JSON guarda {etiqueta: valor}, así que un LIKE crudo devuelve toda categoría que tenga
    un campo con esa palabra en el nombre. Se busca lo que escribiste, no cómo se llama el
    casillero.
    """
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, values={"¿Qué sentí?": "tranquilo"})
    assert db.search_journal_entries("sentí") == []
    assert "No se encontraron notas" in client.get("/search?q=sent%C3%AD").data.decode()


def test_la_busqueda_sigue_encontrando_las_notas_rapidas(client, test_db):
    db.add_note(DATE, "una nota rápida cualquiera")
    cid = _add_cat(test_db)
    _add_entry(test_db, cid, values={"¿Qué sentí?": "una nota especial cualquiera"})
    html = client.get("/search?q=cualquiera").data.decode()
    assert "nota rápida cualquiera" in html and "nota especial cualquiera" in html
    assert "2 resultados" in html


# ── El editor de campos: la configuración la manda el tipo ───────────────────
# El rediseño de la pantalla salió de que el formulario necesitaba párrafos para explicarse. Estos
# fijan lo que los sacó: que el dato esté en el catálogo y que cada fila lo diga cuando aplica.

def test_cada_tipo_declara_si_lleva_configuracion():
    """Los cuatro que la ignoran van con `config: None` — `field-registry.js` ni se la pasa a sus
    builders, así que ofrecerles una caja era ofrecer algo que no hace nada."""
    por_slug = {t["slug"]: t for t in FIELD_TYPES}
    for slug in ("duracion", "rango", "sino", "emotion-wheel"):
        assert por_slug[slug]["config"] is None, slug
    for slug in ("text", "escala", "opciones", "numero"):
        assert por_slug[slug]["config"]["label"], slug
    # Sin opciones, el campo no se puede completar al cargar la nota: es la única obligatoria.
    assert por_slug["opciones"]["config"]["requerida"] is True


def test_la_pantalla_lleva_la_configuracion_de_cada_tipo(client, test_db):
    """Va a la página con el catálogo: la sub-línea toma de ahí su etiqueta y su ejemplo."""
    html = client.get("/journal").data.decode()
    for etiqueta in ("Opciones, separadas por coma", "Unidad", "Texto de ayuda",
                     "Desayuno, Almuerzo, Cena"):
        assert etiqueta in html, etiqueta


def test_el_alta_ya_no_explica_la_configuracion_en_un_parrafo(client, test_db):
    """Tripwire del rediseño: una sola columna significaba cuatro cosas según el tipo y nada en
    otros cuatro, así que hacía falta un párrafo arriba de la tabla explicando todos los casos
    juntos. Hoy cada fila lo dice al lado, y solo cuando aplica."""
    html = client.get("/journal").data.decode()
    for muerto in ("Ayuda / configuración", "Ayuda / opciones / unidad", "El campo <b>Ayuda</b>"):
        assert muerto not in html, muerto


def test_la_columna_de_notas_es_solo_de_la_edicion(client, test_db):
    """Una categoría nueva no tiene ninguna nota: en el alta esa columna estaría siempre vacía."""
    _add_cat(test_db)
    html = client.get("/journal").data.decode()
    assert html.count("journal-fields sin-usos") == 1      # el alta
    assert html.count('class="journal-fields"') == 1       # la edición de la única categoría


def test_el_marcado_de_una_fila_esta_una_sola_vez(client, test_db):
    """Estaba tres veces —el alta, la edición y otra copia armada a mano en JavaScript— y la de JS
    era la que divergía. Hoy el macro rinde la fila y el JS clona su <template>."""
    html = client.get("/journal").data.decode()
    assert 'id="jcat-row-tpl"' in html
    assert "_fieldRow" not in html


def test_las_plantillas_van_antes_del_nombre(client, test_db):
    """Estaban abajo del nombre y el color y los pisaban al aplicarse: escribías el nombre, tocabas
    una plantilla y lo perdías. Arriba son el punto de partida y no hay nada que pisar."""
    html = client.get("/journal").data.decode()
    assert html.index('id="jcat-plantillas"') < html.index('id="jcat-name"')


def test_los_tipos_graficables_salen_del_catalogo_y_no_de_una_lista_suelta():
    """`TIPOS_GRAFICABLES` tiene que ser exactamente lo que `build_series()` sabe graficar. Era una
    tupla escrita a mano en `routes/main.py`, lejos del motor y lejos del catálogo."""
    from bitacora.fieldtypes import TIPOS_GRAFICABLES
    from bitacora.database.stats import NUMERIC_TYPES
    assert set(TIPOS_GRAFICABLES) == set(NUMERIC_TYPES) | {"sino", "opciones"}


def test_un_campo_de_texto_tildado_no_produce_ningun_grafico(test_db):
    """El porqué de que el tilde no se ofrezca ahí: el motor devuelve una serie vacía y la pantalla
    la saltea, así que tildarlo no hacía nada en ningún estado."""
    cid = _add_cat(test_db, fields_json=json.dumps([
        {"label": "Notas", "type": "text", "chart": True},
        {"label": "Ánimo", "type": "escala", "chart": True},
    ]))
    _add_entry(test_db, cid, values={"Notas": "un texto largo", "Ánimo": "4"})
    assert db.build_series(cid, "Notas", "text", DATE, DATE)["data"] == []
    assert db.build_series(cid, "Ánimo", "escala", DATE, DATE)["data"] == [4]


def test_los_datos_de_ejemplo_ejercitan_todos_los_tipos_graficables(test_db):
    """`tools/datos_demo.py` existe para MIRAR Estadísticas con algo adentro; si un tipo deja de
    producir serie, el ejemplo miente y se ve una tarjeta vacía. Acá se fija que cada tipo
    graficable produzca datos de verdad, que es lo que un test de unidad por función no cubre.

    Se recorren los campos **sembrados** y no los tildados: el ejemplo tilda solo donde el gráfico
    automático dice algo, y los que van sin tilde tienen que graficarse igual desde el
    constructor."""
    import pathlib
    import sys
    from datetime import date, timedelta
    from bitacora.fieldtypes import TIPOS_GRAFICABLES

    sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "tools"))
    from datos_demo import sembrar
    sembrar(db)

    fin = date.today().isoformat()
    ini = (date.today() - timedelta(days=60)).isoformat()
    vistos = set()
    for c in db.get_journal_categories():
        for f in c["fields"]:
            tipo = f.get("type", "text")
            if tipo not in TIPOS_GRAFICABLES:
                continue
            serie = db.build_series(c["id"], f["label"], tipo, ini, fin)
            assert serie["data"], f"{f['label']} ({tipo}) no produjo ningún dato"
            vistos.add(tipo)
    assert vistos == set(TIPOS_GRAFICABLES)
