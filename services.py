"""Lógica de presentación reutilizable entre vistas (calendario/semana).
Funciones puras y testeables sin HTTP."""
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
