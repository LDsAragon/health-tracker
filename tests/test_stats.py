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
