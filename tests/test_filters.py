"""Filtros Jinja de formato (puros, sin DB): duración, rango horario, fecha corta."""
from app import dur_fmt_filter, rango_fmt_filter, fechacorta_filter


# ── Duración (minutos → texto) ─────────────────────────────────────────────────

def test_dur_fmt_horas_y_min():
    assert dur_fmt_filter("90") == "1 h 30 min"

def test_dur_fmt_solo_horas():
    assert dur_fmt_filter("120") == "2 h"

def test_dur_fmt_solo_min():
    assert dur_fmt_filter("45") == "45 min"

def test_dur_fmt_cero_o_vacio():
    assert dur_fmt_filter("0") == ""
    assert dur_fmt_filter("") == ""

def test_dur_fmt_no_numerico():
    assert dur_fmt_filter("abc") == "abc"


# ── Rango horario ──────────────────────────────────────────────────────────────

def test_rango_fmt_normal():
    assert rango_fmt_filter("09:00-10:30") == "09:00 → 10:30 · 1 h 30 min"

def test_rango_fmt_cruce_medianoche():
    # acostarse 02:00, levantarse 09:00 → 7 h
    assert rango_fmt_filter("02:00-09:00") == "02:00 → 09:00 · 7 h"

def test_rango_fmt_cruce_real_nocturno():
    # 23:30 → 07:00 = 7 h 30 min
    assert rango_fmt_filter("23:30-07:00") == "23:30 → 07:00 · 7 h 30 min"

def test_rango_fmt_invalido():
    assert rango_fmt_filter("hola") == "hola"
    assert rango_fmt_filter("") == ""


# ── Fecha corta ────────────────────────────────────────────────────────────────

def test_fechacorta():
    assert fechacorta_filter("2026-06-10") == "10/06/2026"

def test_fechacorta_vacio():
    assert fechacorta_filter("") == ""
