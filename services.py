"""Lógica de presentación reutilizable entre vistas (calendario/semana).
Funciones puras y testeables sin HTTP."""
from datetime import date, timedelta

import database as db


def events_by_date(recurring, completions, dates):
    """{date_str: [evento decorado con done/skipped/completion_note]} para cada fecha.
    Filtra los ocultos del calendario (show_in_calendar) y los que no aplican ese día."""
    out = {}
    for d in dates:
        d_str = d.isoformat()
        done = completions.get(d_str, {})
        out[d_str] = [
            {
                **ev,
                "done":    ev["id"] in done and done[ev["id"]]["status"] == "done",
                "skipped": ev["id"] in done and done[ev["id"]]["status"] == "skipped",
                "completion_note": done.get(ev["id"], {}).get("note", ""),
            }
            for ev in recurring
            if ev.get("show_in_calendar", 1) and db.event_applies(ev, d)
        ]
    return out


def journal_badges(journal_raw):
    """{date_str: [{name,color}]} — una badge por categoría (con show_in_calendar) por día."""
    out = {}
    for ds, entries in journal_raw.items():
        seen, badges = set(), []
        for e in entries:
            if e["show_in_calendar"] and e["category_id"] not in seen:
                seen.add(e["category_id"])
                badges.append({"name": e["category_name"], "color": e["category_color"]})
        if badges:
            out[ds] = badges
    return out


# --- Visor de tareas ---

_BUCKET_LABELS = (
    ("esta_semana",   "Esta semana"),
    ("semana_pasada", "La semana pasada"),
    ("antes",         "Más viejas"),
)


def _as_date(iso):
    """None si el texto no es una fecha ISO: todo_date no se valida al guardar."""
    try:
        return date.fromisoformat(iso)
    except (ValueError, TypeError):
        return None


def overdue_buckets(todos, today, week_start):
    """Agrupa las tareas atrasadas por antigüedad: [{key, label, tareas}], sin tramos vacíos.
    `week_start` es el callable de helpers, para no acoplar esto al ajuste week_start."""
    this_week = week_start(today)
    last_week = this_week - timedelta(days=7)
    groups = {key: [] for key, _ in _BUCKET_LABELS}
    for t in todos:
        d = _as_date(t["todo_date"])
        if d is None:
            continue
        key = "esta_semana" if d >= this_week else "semana_pasada" if d >= last_week else "antes"
        groups[key].append(t)
    # La clave no puede ser "items": en Jinja `b.items` resuelve al método del dict.
    return [{"key": k, "label": lbl, "tareas": groups[k]} for k, lbl in _BUCKET_LABELS if groups[k]]


def todos_overview(todos, today):
    """Conteos por estado del conjunto recibido."""
    out = {"total": len(todos), "hechas": 0, "pendientes": 0, "hoy": 0, "proximas": 0, "vencidas": 0}
    for t in todos:
        d = _as_date(t["todo_date"])
        if t["done"]:
            out["hechas"] += 1
            continue
        out["pendientes"] += 1
        if d == today:
            out["hoy"] += 1
        elif d is not None and d > today:
            out["proximas"] += 1
        elif d is not None:
            out["vencidas"] += 1
    return out


def overdue_cutoff(today, mode, week_start):
    """Fecha exclusiva del corte: `week` deja pasar lo de la semana en curso, `day` solo hoy."""
    return week_start(today) if mode == "week" else today
