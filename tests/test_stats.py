"""Capa de datos de Estadísticas (database/stats.py)."""
import json
import database as db


def _cat(test_db, fields):
    db.add_journal_category({"name": "T", "color": "#000", "fields_json": json.dumps(fields), "show_in_calendar": 0})
    return db.get_journal_categories()[0]["id"]


def _entry(cid, d, values):
    db.add_journal_entry({"category_id": cid, "entry_date": d, "values_json": json.dumps(values), "tags": ""})


def test_numeric_series_numero(test_db):
    cid = _cat(test_db, [{"label": "Peso", "type": "numero", "placeholder": "kg"}])
    _entry(cid, "2026-06-01", {"Peso": "100"})
    _entry(cid, "2026-06-05", {"Peso": "98.5"})
    _entry(cid, "2026-06-03", {"Peso": ""})   # vacío se ignora
    s = db.numeric_series(cid, "Peso", "numero", "2026-06-01", "2026-06-30")
    assert s == [("2026-06-01", 100.0), ("2026-06-05", 98.5)]


def test_numeric_series_rango_minutos(test_db):
    cid = _cat(test_db, [{"label": "Sueño", "type": "rango"}])
    _entry(cid, "2026-06-01", {"Sueño": "23:00-07:00"})   # cruce de medianoche = 8 h
    s = db.numeric_series(cid, "Sueño", "rango", "2026-06-01", "2026-06-30")
    assert s == [("2026-06-01", 480)]


def test_bool_counts(test_db):
    cid = _cat(test_db, [{"label": "Cumplí", "type": "sino"}])
    _entry(cid, "2026-06-01", {"Cumplí": "1"})
    _entry(cid, "2026-06-01", {"Cumplí": ""})
    _entry(cid, "2026-06-02", {"Cumplí": "1"})
    assert db.bool_counts(cid, "Cumplí", "2026-06-01", "2026-06-30") == {"2026-06-01": 1, "2026-06-02": 1}


def test_option_distribution(test_db):
    cid = _cat(test_db, [{"label": "Momento", "type": "opciones", "placeholder": "Desayuno, Cena"}])
    _entry(cid, "2026-06-01", {"Momento": "Desayuno"})
    _entry(cid, "2026-06-02", {"Momento": "Cena"})
    _entry(cid, "2026-06-03", {"Momento": "Desayuno"})
    assert db.option_distribution(cid, "Momento", "2026-06-01", "2026-06-30") == {"Desayuno": 2, "Cena": 1}


def test_chartable_fields(test_db):
    _cat(test_db, [{"label": "Peso", "type": "numero", "chart": True}, {"label": "Nota", "type": "text"}])
    cf = db.chartable_fields()
    assert len(cf) == 1 and cf[0]["label"] == "Peso" and cf[0]["type"] == "numero"


def test_build_series_numero(test_db):
    cid = _cat(test_db, [{"label": "Peso", "type": "numero"}])
    _entry(cid, "2026-06-01", {"Peso": "100"})
    out = db.build_series(cid, "Peso", "numero", "2026-06-01", "2026-06-30")
    assert out == {"kind": "line", "labels": ["2026-06-01"], "data": [100.0]}


def _entry_tagged(cid, d, values, tags=""):
    db.add_journal_entry({"category_id": cid, "entry_date": d,
                          "values_json": json.dumps(values), "tags": tags})


WORK_FIELDS = [{"label": "Proyecto", "type": "opciones", "placeholder": "A, B"},
               {"label": "Franja", "type": "rango"},
               {"label": "Horas", "type": "duracion"}]


def test_grouped_series_desglose_y_totales(test_db):
    cid = _cat(test_db, WORK_FIELDS)
    _entry(cid, "2026-06-01", {"Proyecto": "A", "Horas": "120"})
    _entry(cid, "2026-06-01", {"Proyecto": "B", "Franja": "09:00-11:30"})            # 150 min
    _entry(cid, "2026-06-02", {"Proyecto": "A", "Horas": "60", "Franja": "20:00-21:00"})  # suma ambos = 120
    s = db.grouped_series(cid, [("Horas", "duracion"), ("Franja", "rango")], "Proyecto",
                          "2026-06-01", "2026-06-30", bucket="day")
    assert s["labels"] == ["2026-06-01", "2026-06-02"]
    byname = {d["label"]: d["data"] for d in s["datasets"]}
    assert byname["A"] == [120, 120]
    assert byname["B"] == [150, 0]
    assert s["totals"] == {"A": 240, "B": 150}
    assert s["time_based"] is True


def test_grouped_series_buckets_semana_y_mes(test_db):
    cid = _cat(test_db, [{"label": "Horas", "type": "duracion"}])
    _entry(cid, "2026-06-01", {"Horas": "60"})   # lunes
    _entry(cid, "2026-06-07", {"Horas": "30"})   # domingo (misma semana, lunes-inicio)
    _entry(cid, "2026-06-08", {"Horas": "45"})   # lunes siguiente
    _entry(cid, "2026-07-01", {"Horas": "10"})
    s = db.grouped_series(cid, [("Horas", "duracion")], "", "2026-06-01", "2026-07-31", bucket="week")
    assert s["labels"] == ["2026-06-01", "2026-06-08", "2026-06-29"]
    assert s["datasets"] == [{"label": "Total", "data": [90, 45, 10]}]
    m = db.grouped_series(cid, [("Horas", "duracion")], "", "2026-06-01", "2026-07-31", bucket="month")
    assert m["labels"] == ["2026-06", "2026-07"]
    assert m["datasets"][0]["data"] == [135, 10]


def test_grouped_series_respeta_week_start_domingo(test_db):
    db.set_setting("week_start", "sun")
    cid = _cat(test_db, [{"label": "Horas", "type": "duracion"}])
    _entry(cid, "2026-06-07", {"Horas": "30"})   # domingo
    _entry(cid, "2026-06-08", {"Horas": "45"})   # lunes → misma semana si empieza en domingo
    s = db.grouped_series(cid, [("Horas", "duracion")], "", "2026-06-01", "2026-06-30", bucket="week")
    assert s["labels"] == ["2026-06-07"]
    assert s["datasets"][0]["data"] == [75]


def test_grouped_series_filtro_por_etiqueta(test_db):
    cid = _cat(test_db, [{"label": "Horas", "type": "duracion"}])
    _entry_tagged(cid, "2026-06-01", {"Horas": "60"}, tags="ClienteA, urgente")
    _entry_tagged(cid, "2026-06-02", {"Horas": "30"}, tags="clienteB")
    s = db.grouped_series(cid, [("Horas", "duracion")], "", "2026-06-01", "2026-06-30",
                          tag_filter="clientea")   # case-insensitive
    assert s["totals"] == {"Total": 60}


def test_grouped_series_sin_asignar(test_db):
    cid = _cat(test_db, WORK_FIELDS)
    _entry(cid, "2026-06-01", {"Horas": "90"})   # sin Proyecto
    s = db.grouped_series(cid, [("Horas", "duracion")], "Proyecto", "2026-06-01", "2026-06-30")
    assert s["totals"] == {"Sin asignar": 90}


def test_chart_desglosado_via_ruta(client):
    from datetime import date
    hoy = date.today().isoformat()
    db.add_journal_category({"name": "Trabajo", "color": "#14b8a6",
        "fields_json": json.dumps(WORK_FIELDS), "show_in_calendar": 0})
    cid = db.get_journal_categories()[0]["id"]
    _entry_tagged(cid, hoy, {"Proyecto": "A", "Horas": "120"})
    _entry_tagged(cid, hoy, {"Proyecto": "B", "Franja": "09:00-10:30"})
    client.post("/estadisticas/grafico/add", data={
        "category_id": str(cid), "field_label": "Horas", "field_label2": "Franja",
        "group_field": "Proyecto", "bucket": "week", "range_days": "90"})
    ch = db.get_charts()[0]
    assert ch["field_label"] == "Horas|Franja"
    assert ch["group_field"] == "Proyecto" and ch["bucket"] == "week"
    body = client.get("/estadisticas").data.decode("utf-8")
    assert '"kind": "stacked"' in body
    assert "2 h" in body            # total de A (120 min) formateado en la tabla
    assert "stats-totals" in body


def test_grafico_simple_de_tiempo_en_horas_via_ruta(client):
    """Los gráficos simples de duración/rango van en horas con unidad (no minutos crudos)."""
    from datetime import date
    hoy = date.today().isoformat()
    db.add_journal_category({"name": "Descanso", "color": "#000",
        "fields_json": json.dumps([{"label": "Sueño", "type": "rango", "chart": True}]),
        "show_in_calendar": 0})
    cid = db.get_journal_categories()[0]["id"]
    _entry(cid, hoy, {"Sueño": "23:00-07:00"})   # 480 min = 8 h
    body = client.get("/estadisticas").data.decode("utf-8")
    assert '"data": [8.0]' in body
    assert '"unit": "horas"' in body


def test_charts_crud_via_ruta(client):
    db.add_journal_category({"name": "Peso", "color": "#000",
        "fields_json": json.dumps([{"label": "Peso", "type": "numero"}]), "show_in_calendar": 0})
    cid = db.get_journal_categories()[0]["id"]
    client.post("/estadisticas/grafico/add", data={"category_id": str(cid), "field_label": "Peso", "title": "Mi peso", "range_days": "180"})
    charts = db.get_charts()
    assert len(charts) == 1 and charts[0]["field_label"] == "Peso" and charts[0]["range_days"] == 180
    client.post(f"/estadisticas/grafico/{charts[0]['id']}/delete")
    assert db.get_charts() == []
