"""Capa de servicios — lógica pura de presentación (sin HTTP, sin DB fixture)."""
from datetime import date, timedelta
from bitacora import services


def test_events_by_date_decora_y_filtra():
    recurring = [
        {"id": 1, "title": "A", "recurrence": "daily", "start_date": "2020-01-01", "end_date": "", "show_in_calendar": 1},
        {"id": 2, "title": "Oculto", "recurrence": "daily", "start_date": "2020-01-01", "end_date": "", "show_in_calendar": 0},
    ]
    completions = {"2026-06-09": {1: {"status": "done", "note": "ok"}}}
    out = services.events_by_date(recurring, completions, [date(2026, 6, 9)])
    evs = out["2026-06-09"]
    assert len(evs) == 1                         # el oculto del calendario se filtra
    assert evs[0]["id"] == 1
    assert evs[0]["done"] and not evs[0]["skipped"]
    assert evs[0]["completion_note"] == "ok"


def test_journal_badges_dedup_y_filtra():
    raw = {"2026-06-09": [
        {"category_id": 1, "category_name": "Sueño", "category_color": "#3b82f6", "show_in_calendar": 1},
        {"category_id": 1, "category_name": "Sueño", "category_color": "#3b82f6", "show_in_calendar": 1},
        {"category_id": 2, "category_name": "Oculto", "category_color": "#000000", "show_in_calendar": 0},
    ]}
    out = services.journal_badges(raw)
    assert out["2026-06-09"] == [{"name": "Sueño", "color": "#3b82f6"}]


# ── Visor de tareas ─────────────────────────────────────────────────────────────

def _lunes(d):
    """Inicio de semana en lunes, sin depender de los ajustes."""
    return d - timedelta(days=d.weekday())


def _t(fecha, done=0):
    return {"todo_date": fecha, "done": done, "text": fecha}


def test_overdue_buckets_reparte_por_antiguedad():
    hoy = date(2026, 6, 10)                      # miércoles; la semana arranca el 8
    todos = [_t("2026-06-09"), _t("2026-06-03"), _t("2026-05-20")]
    out = services.overdue_buckets(todos, hoy, _lunes)
    assert [b["key"] for b in out] == ["esta_semana", "semana_pasada", "antes"]
    assert [b["tareas"][0]["todo_date"] for b in out] == ["2026-06-09", "2026-06-03", "2026-05-20"]


def test_overdue_buckets_omite_tramos_vacios():
    out = services.overdue_buckets([_t("2026-05-20")], date(2026, 6, 10), _lunes)
    assert [b["key"] for b in out] == ["antes"]


def test_overdue_buckets_ignora_fechas_corruptas():
    """todo_date no se valida al guardar: una fecha basura no puede tumbar la vista."""
    out = services.overdue_buckets([_t("chau"), _t("2026-05-20")], date(2026, 6, 10), _lunes)
    assert sum(len(b["tareas"]) for b in out) == 1


def test_overdue_cutoff_segun_el_modo():
    hoy = date(2026, 6, 10)
    assert services.overdue_cutoff(hoy, "week", _lunes) == date(2026, 6, 8)
    assert services.overdue_cutoff(hoy, "day", _lunes) == hoy


def test_periodo_ventana_es_exacta():
    """El botón tiene que listar exactamente lo que dice: nada de futuro salvo donde corresponde."""
    hoy = date(2026, 6, 10)
    assert services.periodo_ventana("hoy", hoy) == ("2026-06-10", "2026-06-10")
    assert services.periodo_ventana("7", hoy) == ("2026-06-04", "2026-06-10")
    assert services.periodo_ventana("30", hoy) == ("2026-05-12", "2026-06-10")


def test_periodo_ventana_proximas_y_todo():
    hoy = date(2026, 6, 10)
    assert services.periodo_ventana("proximas", hoy) == ("2026-06-11", None)
    assert services.periodo_ventana("todo", hoy) == (None, None)
