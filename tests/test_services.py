"""Capa de servicios — lógica pura de presentación (sin HTTP, sin DB fixture)."""
from datetime import date
import services


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
