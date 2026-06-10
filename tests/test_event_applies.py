"""
Lógica pura de event_applies — no necesita DB.
Cubre los tres tipos de recurrencia + start_date + end_date.
"""
from datetime import date, timedelta
from database import event_applies

# Fechas fijas: encontramos un lunes de referencia
_base = date(2026, 6, 1)
while _base.weekday() != 0:
    _base += timedelta(days=1)

LUNES     = _base
MARTES    = LUNES + timedelta(days=1)
MIERCOLES = LUNES + timedelta(days=2)
JUEVES    = LUNES + timedelta(days=3)
DOMINGO   = LUNES + timedelta(days=6)


def ev(recurrence, start="2020-01-01", end=""):
    return {"recurrence": recurrence, "start_date": start, "end_date": end}


# ── Diario ────────────────────────────────────────────────────────────────────

def test_daily_aplica():
    assert event_applies(ev("daily"), LUNES)

def test_daily_antes_de_start():
    assert not event_applies(ev("daily", start=MARTES.isoformat()), LUNES)

def test_daily_en_start():
    assert event_applies(ev("daily", start=LUNES.isoformat()), LUNES)

def test_daily_despues_de_end():
    assert not event_applies(ev("daily", end=LUNES.isoformat()), MARTES)

def test_daily_en_end():
    assert event_applies(ev("daily", end=LUNES.isoformat()), LUNES)

def test_daily_sin_start_date():
    assert not event_applies({"recurrence": "daily", "start_date": "", "end_date": ""}, LUNES)


# ── Semanal ───────────────────────────────────────────────────────────────────

def test_weekly_dia_correcto():
    assert event_applies(ev("weekly:0"), LUNES)      # 0 = lunes

def test_weekly_dia_incorrecto():
    assert not event_applies(ev("weekly:0"), MARTES)

def test_weekly_varios_dias():
    e = ev("weekly:0,2")   # lunes y miércoles
    assert event_applies(e, LUNES)
    assert event_applies(e, MIERCOLES)
    assert not event_applies(e, MARTES)
    assert not event_applies(e, JUEVES)

def test_weekly_antes_de_start():
    assert not event_applies(ev("weekly:0", start=MARTES.isoformat()), LUNES)

def test_weekly_domingo():
    assert event_applies(ev("weekly:6"), DOMINGO)


# ── Cada N días ───────────────────────────────────────────────────────────────

def test_every_n_en_start():
    assert event_applies(ev("every:3", start=LUNES.isoformat()), LUNES)

def test_every_n_en_intervalo():
    e = ev("every:3", start=LUNES.isoformat())
    assert event_applies(e, LUNES + timedelta(days=3))
    assert event_applies(e, LUNES + timedelta(days=6))
    assert event_applies(e, LUNES + timedelta(days=9))

def test_every_n_entre_intervalos():
    e = ev("every:3", start=LUNES.isoformat())
    assert not event_applies(e, LUNES + timedelta(days=1))
    assert not event_applies(e, LUNES + timedelta(days=2))
    assert not event_applies(e, LUNES + timedelta(days=4))

def test_every_n_antes_de_start():
    assert not event_applies(ev("every:3", start=MARTES.isoformat()), LUNES)

def test_every_n_despues_de_end():
    e = ev("every:3", start=LUNES.isoformat(), end=(LUNES + timedelta(days=3)).isoformat())
    assert not event_applies(e, LUNES + timedelta(days=6))


# ── Una sola vez (evento único) ────────────────────────────────────────────────

def test_once_en_start():
    assert event_applies(ev("once", start=LUNES.isoformat()), LUNES)

def test_once_otro_dia():
    e = ev("once", start=LUNES.isoformat())
    assert not event_applies(e, MARTES)
    assert not event_applies(e, LUNES + timedelta(days=7))

def test_once_antes_de_start():
    assert not event_applies(ev("once", start=MARTES.isoformat()), LUNES)
