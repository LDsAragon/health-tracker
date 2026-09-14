"""Capa de datos de Estadísticas (database/stats.py)."""
import json
from bitacora import database as db


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


def test_el_tiempo_por_actividad_se_desglosa_por_opcion(test_db):
    cid = _cat(test_db, WORK_FIELDS)              # Proyecto (opciones) + Franja + Horas
    _entry(cid, "2026-06-10", {"Proyecto": "A", "Horas": "120"})
    _entry(cid, "2026-06-02", {"Proyecto": "A", "Horas": "60"})
    _entry(cid, "2026-06-05", {"Proyecto": "B", "Horas": "30"})
    _entry(cid, "2025-12-01", {"Proyecto": "B", "Horas": "999"})   # fuera del período
    filas = db.tiempo_comparado("2026-06-01", "2026-06-30")
    assert [(f["name"], f["minutos"]) for f in filas] == [("T · A", 180), ("T · B", 30)]


def test_el_tiempo_sin_opciones_va_por_categoria(test_db):
    cid = _cat(test_db, [{"label": "Dormido", "type": "rango"}])
    _entry(cid, "2026-06-12", {"Dormido": "23:00-07:00"})
    filas = db.tiempo_comparado("2026-06-01", "2026-06-30")
    assert [(f["name"], f["minutos"]) for f in filas] == [("T", 480)]


def test_el_tiempo_se_compara_con_el_periodo_anterior(test_db):
    """Lo que le da sentido a un número de horas: si subió o bajó contra el mes pasado."""
    cid = _cat(test_db, [{"label": "Horas", "type": "duracion"}])
    _entry(cid, "2026-05-10", {"Horas": "60"})    # período anterior (mayo)
    _entry(cid, "2026-06-10", {"Horas": "90"})    # el período (junio)
    fila = db.tiempo_comparado("2026-06-01", "2026-06-30")[0]
    assert (fila["minutos"], fila["previo"], fila["delta"]) == (90, 60, 30)


def test_una_actividad_sin_nada_antes_no_finge_una_mejora(test_db):
    """Igual que el resumen: sin período anterior con datos, no hay flecha."""
    cid = _cat(test_db, [{"label": "Horas", "type": "duracion"}])
    _entry(cid, "2026-06-10", {"Horas": "90"})
    assert db.tiempo_comparado("2026-06-01", "2026-06-30")[0]["delta"] is None


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


# ── El resumen de lo que ya anotás ───────────────────────────────────────────

def test_el_resumen_cuenta_lo_que_hay_sin_configurar_nada(test_db):
    """⚠️ El problema que vino a resolver: sin campos marcados con 📈, la pantalla no mostraba
    **nada** aunque hubieras anotado todos los días durante meses."""
    db.add_note("2026-06-02", "una")
    db.add_note("2026-06-02", "otra")
    db.add_note("2026-06-05", "tercera")
    db.add_todo("2026-06-03", "hacer algo")
    db.add_todo("2026-06-03", "y otra cosa")
    db.toggle_todo(db.get_todos_for_date("2026-06-03")[0]["id"])
    cid = _cat(test_db, [{"label": "Ánimo", "type": "escala"}])
    _entry(cid, "2026-06-04", {"Ánimo": "4"})

    r = db.resumen("2026-06-01", "2026-06-30")
    assert r["notas"] == 3
    assert r["especiales"] == 1
    assert r["tareas_total"] == 2 and r["tareas_hechas"] == 1
    assert r["dias"] == 30
    assert r["dias_con_algo"] == 4          # 2, 3, 4 y 5 de junio


def test_tildar_una_rutina_no_cuenta_como_anotar(test_db):
    """Cumplir algo que ya estaba planeado no es lo mismo que registrar algo: si contara, la
    constancia diría "30 de 30 días" solo por tener una rutina diaria."""
    db.add_recurring_event({"title": "Caminadora", "color": "#6366f1", "recurrence": "daily",
                            "start_date": "2026-06-01"})
    ev = db.get_recurring_events()[0]["id"]
    for d in range(1, 11):
        db.complete_event(ev, f"2026-06-{d:02d}")
    assert db.resumen("2026-06-01", "2026-06-30")["dias_con_algo"] == 0


def test_una_tarea_sin_cerrar_igual_cuenta_como_dia_anotado(test_db):
    db.add_todo("2026-06-07", "pendiente")
    r = db.resumen("2026-06-01", "2026-06-30")
    assert r["dias_con_algo"] == 1 and r["tareas_hechas"] == 0


def test_el_resumen_de_una_base_vacia_no_explota(test_db):
    r = db.resumen("2026-06-01", "2026-06-30")
    assert r == {"dias": 30, "notas": 0, "especiales": 0, "tareas_total": 0,
                 "tareas_hechas": 0, "dias_con_algo": 0}


# ── La comparación con el período anterior ───────────────────────────────────

def test_el_periodo_anterior_es_de_igual_largo_y_pegado(test_db):
    from bitacora.database.stats import _periodo_anterior
    assert _periodo_anterior("2026-06-01", "2026-06-30") == ("2026-05-02", "2026-05-31")
    assert _periodo_anterior("2026-06-13", "2026-06-13") == ("2026-06-12", "2026-06-12")


def test_la_comparacion_dice_cuanto_subio_o_bajo(test_db):
    for d in ("2026-05-10", "2026-05-11"):
        db.add_note(d, "del mes pasado")
    for d in ("2026-06-10", "2026-06-11", "2026-06-12", "2026-06-13", "2026-06-14"):
        db.add_note(d, "de este mes")

    c = db.resumen_comparado("2026-06-01", "2026-06-30")
    assert c["actual"]["notas"] == 5
    assert c["previo"]["notas"] == 2
    assert c["deltas"]["notas"] == 3


def test_sin_datos_antes_no_hay_delta(test_db):
    """⚠️ Un "▲ +23" contra un período vacío no es una mejora: es ruido, y encima se lee como un
    logro. Ahí el delta viaja como None y la pantalla muestra un guion."""
    db.add_note("2026-06-10", "la primera nota de mi vida")
    c = db.resumen_comparado("2026-06-01", "2026-06-30")
    assert c["hubo_antes"] is False
    assert all(v is None for v in c["deltas"].values())


def test_con_datos_antes_si_hay_delta_aunque_baje(test_db):
    db.add_note("2026-05-10", "antes")
    c = db.resumen_comparado("2026-06-01", "2026-06-30")
    assert c["hubo_antes"] is True
    assert c["deltas"]["notas"] == -1


# ── La rueda de emociones ────────────────────────────────────────────────────

def _cat_rueda(test_db):
    return _cat(test_db, [{"label": "¿Qué sentí?", "type": "emotion-wheel"}])


def test_cuenta_las_emociones_por_base(test_db):
    """Se cuenta el primer nivel: los de abajo son matices y contarlos aparte dispersaría todo
    en frecuencia 1."""
    cid = _cat_rueda(test_db)
    _entry(cid, "2026-06-01", {"¿Qué sentí?": "Alegre > Contento"})
    _entry(cid, "2026-06-02", {"¿Qué sentí?": "Alegre > Feliz"})
    _entry(cid, "2026-06-03", {"¿Qué sentí?": "Triste > Solo"})

    e = db.emociones_frecuentes("2026-06-01", "2026-06-30")
    assert e["ruedas"]["willcox"] == [{"emocion": "Alegre", "veces": 2},
                                      {"emocion": "Triste", "veces": 1}]
    assert e["dias"] == 3


def test_las_dos_ruedas_no_se_mezclan(test_db):
    """⚠️ Willcox y Ekman son taxonomías distintas: sumar "Ira" con "Enojado" sería inventar una
    equivalencia que nadie definió."""
    cid = _cat_rueda(test_db)
    _entry(cid, "2026-06-01", {"¿Qué sentí?": "Enojado > Furioso | ek::Ira > Furia"})
    e = db.emociones_frecuentes("2026-06-01", "2026-06-30")
    assert e["ruedas"]["willcox"] == [{"emocion": "Enojado", "veces": 1}]
    assert e["ruedas"]["ekman"] == [{"emocion": "Ira", "veces": 1}]
    assert e["dias"] == 1                    # el mismo día, no dos


def test_varias_emociones_el_mismo_dia_cuentan_todas(test_db):
    cid = _cat_rueda(test_db)
    _entry(cid, "2026-06-01", {"¿Qué sentí?": "Alegre > Feliz | Apacible > Sereno"})
    e = db.emociones_frecuentes("2026-06-01", "2026-06-30")
    assert sum(x["veces"] for x in e["ruedas"]["willcox"]) == 2
    assert e["dias"] == 1


def test_sin_campos_de_rueda_no_hay_nada_que_contar(test_db):
    _cat(test_db, [{"label": "Peso", "type": "numero"}])
    assert db.emociones_frecuentes("2026-06-01", "2026-06-30") == {"ruedas": {}, "dias": 0}


def test_los_colores_de_las_emociones_estan_en_un_solo_lugar():
    """Estaban como literales dentro de `day.html`, y Estadísticas necesita los mismos: un color
    por emoción tiene que ser el mismo en las dos pantallas."""
    import pathlib

    from bitacora.appconfig import EMOTION_COLORS
    assert set(EMOTION_COLORS) == {"willcox", "ekman"}
    day = (pathlib.Path(__file__).resolve().parent.parent / "bitacora" / "templates"
           / "day.html").read_text(encoding="utf-8")
    assert "'Enojado':'#e8643c'" not in day, "volvieron los colores copiados a day.html"


# ── La pantalla: un solo período, y que cuente algo sin configurar nada ──────

def test_la_pantalla_vacia_no_dice_nada_raro(client):
    """⚠️ Con una base vacía la pantalla tiene que decir algo sensato, no flechas sobre la nada.

    Y el estado vacío viejo ("Todavía no hay nada para graficar") no vuelve: era todo lo que
    mostraba la pantalla aunque hubieras anotado meses, que es el problema que se arregló.
    """
    body = client.get("/estadisticas").data.decode("utf-8")
    assert "Lo que anotaste" in body
    assert "No hay nada anotado en este período" in body
    assert "Todavía no hay nada para graficar" not in body
    assert "stats-delta-sube" not in body and "stats-delta-baja" not in body


def test_el_resumen_sale_en_la_pantalla_con_lo_que_ya_hay(client):
    from datetime import date
    hoy = date.today().isoformat()
    db.add_note(hoy, "algo", "")
    db.add_todo(hoy, "una tarea")
    body = client.get("/estadisticas").data.decode("utf-8")
    assert "stats-resumen" in body
    assert "No hay nada anotado" not in body


def test_el_periodo_manda_sobre_los_graficos_personalizados(client):
    """⚠️ El cambio que puede sorprender a quien ya tenía un gráfico con rango propio: antes cada
    tarjeta usaba su `charts.range_days` guardado y dos gráficos al lado mostraban ventanas
    distintas sin decirlo."""
    from datetime import date, timedelta
    viejo = (date.today() - timedelta(days=200)).isoformat()
    db.add_journal_category({"name": "Peso", "color": "#000",
        "fields_json": json.dumps([{"label": "Peso", "type": "numero"}]), "show_in_calendar": 0})
    cid = db.get_journal_categories()[0]["id"]
    _entry(cid, viejo, {"Peso": "80"})
    db.add_chart(cid, "Peso", "Mi peso", 365)

    en_un_mes = client.get("/estadisticas?range=30").data.decode("utf-8")
    assert "Sin datos en este período" in en_un_mes, "el gráfico usó su rango guardado, no el de la pantalla"
    en_un_anio = client.get("/estadisticas?range=365").data.decode("utf-8")
    assert '"data": [80.0]' in en_un_anio


def test_este_mes_es_el_mes_calendario(client):
    """"Este mes" no son 30 días para atrás: arranca el 1° y por eso es de largo variable."""
    from datetime import date
    hoy = date.today()
    body = client.get("/estadisticas?range=mes").data.decode("utf-8")
    assert "en lo que va del mes" in body
    assert f"de {hoy.day}" in body            # "N días con algo anotado de <día del mes>"


def test_un_periodo_inventado_cae_en_el_default(client):
    body = client.get("/estadisticas?range=7").data.decode("utf-8")
    assert "últimos 30 días" in body


def test_la_adherencia_se_compara_con_el_periodo_anterior(client):
    """Un 80% suelto no dice si venís mejorando: el delta es lo que lo hace accionable."""
    from datetime import date, timedelta
    hoy = date.today()
    db.add_recurring_event({"title": "Medicación", "color": "#000", "recurrence": "daily",
                            "interval": 1, "weekdays": "", "start_date": (hoy - timedelta(days=120)).isoformat(),
                            "end_date": "", "notes": ""})
    ev = db.get_recurring_events()[0]["id"]
    for i in range(10):                       # el período: 10 de 30
        db.complete_event(ev, (hoy - timedelta(days=i)).isoformat())
    for i in range(30, 35):                   # el anterior: 5 de 30
        db.complete_event(ev, (hoy - timedelta(days=i)).isoformat())

    body = client.get("/estadisticas?range=30").data.decode("utf-8")
    assert "Adherencia de rutinas" in body
    assert "10/30 · 33%" in body
    assert "16 pts" in body and "stats-delta-sube" in body    # 33% - 17% = 16 puntos


def test_sin_rutinas_marcadas_antes_la_adherencia_no_finge_una_mejora(client):
    """⚠️ Si entonces no marcabas rutinas, el período anterior da 0% para todo y cualquier rutina
    aparecería con un "▲ +93" que no es una mejora: es la app vacía."""
    from datetime import date, timedelta
    hoy = date.today()
    db.add_recurring_event({"title": "Medicación", "color": "#000", "recurrence": "daily",
                            "interval": 1, "weekdays": "", "start_date": (hoy - timedelta(days=120)).isoformat(),
                            "end_date": "", "notes": ""})
    ev = db.get_recurring_events()[0]["id"]
    for i in range(28):
        db.complete_event(ev, (hoy - timedelta(days=i)).isoformat())
    body = client.get("/estadisticas?range=30").data.decode("utf-8")
    assert "28/30 · 93%" in body
    assert "stats-delta-sube" not in body
    assert "No hay período anterior con qué comparar" in body


def test_los_colores_cubren_TODAS_las_emociones_base_de_las_dos_ruedas():
    """⚠️ Tripwire del color gris. Las barras de Estadísticas pintan con `EMOTION_COLORS`, y una
    emoción que falte ahí sale del color de fallback sin que nada avise: la rueda sigue andando y
    la estadística miente el color. Los nombres y los colores salen del JS de cada rueda.
    """
    import pathlib
    import re

    from bitacora.appconfig import EMOTION_COLORS
    js = pathlib.Path(__file__).resolve().parent.parent / "bitacora" / "static" / "js"

    # Willcox: `"Enojado": {        // Mad` y en la línea de abajo `color: "#e8643c",`
    wheel = (js / "emotion-wheel.js").read_text(encoding="utf-8")
    willcox = dict(re.findall(r'"([^"]+)":\s*\{[^\n]*\n\s*color:\s*"(#[0-9a-fA-F]{6})"', wheel))
    assert len(willcox) == 6, willcox
    assert EMOTION_COLORS["willcox"] == willcox

    # Ekman: `en: "Anger", es: "Ira", color: "#e2403b",`
    ekman_js = (js / "ekman-wheel.js").read_text(encoding="utf-8")
    ekman = dict(re.findall(r'es:\s*"([^"]+)",\s*color:\s*"(#[0-9a-fA-F]{6})"', ekman_js))
    assert len(ekman) == 5, ekman
    assert EMOTION_COLORS["ekman"] == ekman
