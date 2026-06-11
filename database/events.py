"""Eventos recurrentes (rutinas) + completaciones + lógica de recurrencia."""
from datetime import date, timedelta
from .conn import get_db


def get_recurring_events() -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM recurring_events WHERE active = 1 ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


def add_recurring_event(data: dict):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO recurring_events (title, color, recurrence, start_date, end_date) VALUES (?,?,?,?,?)",
            (data["title"], data["color"], data["recurrence"], data["start_date"], data.get("end_date", "")),
        )


def update_recurring_event(event_id: int, data: dict):
    with get_db() as conn:
        conn.execute(
            "UPDATE recurring_events SET title=?, color=?, recurrence=?, start_date=?, end_date=? WHERE id=?",
            (data["title"], data["color"], data["recurrence"], data["start_date"], data.get("end_date", ""), event_id),
        )


def delete_recurring_event(event_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM recurring_events WHERE id = ?", (event_id,))
        conn.execute("DELETE FROM completions WHERE event_id = ?", (event_id,))


def end_recurring_event(event_id: int, cutoff: str):
    """Borra las ocurrencias futuras conservando las pasadas: fija end_date al corte
    y limpia las completions posteriores (para no dejar huérfanas)."""
    with get_db() as conn:
        conn.execute("UPDATE recurring_events SET end_date = ? WHERE id = ?", (cutoff, event_id))
        conn.execute("DELETE FROM completions WHERE event_id = ? AND done_date > ?", (event_id, cutoff))


def set_recurring_visibility(event_id: int, show: bool):
    """Muestra/oculta el evento en calendario y semana (en la vista del día siempre se ve)."""
    with get_db() as conn:
        conn.execute(
            "UPDATE recurring_events SET show_in_calendar = ? WHERE id = ?",
            (1 if show else 0, event_id),
        )


def event_applies(event: dict, d: date) -> bool:
    """True si el evento recurrente aplica en la fecha d."""
    if not event.get("start_date"):
        return False
    start = date.fromisoformat(event["start_date"])
    if d < start:
        return False
    if event.get("end_date"):
        end = date.fromisoformat(event["end_date"])
        if d > end:
            return False
    rec = event["recurrence"]
    if rec == "once":
        return d == start
    if rec == "daily":
        return True
    if rec.startswith("weekly:"):
        weekdays = [int(x) for x in rec.split(":")[1].split(",")]
        return d.weekday() in weekdays
    if rec.startswith("every:"):
        n = int(rec.split(":")[1])
        return (d - start).days % n == 0
    return False


# ── Completaciones ───────────────────────────────────────────────────────────────

def get_completion(event_id: int, done_date: str):
    with get_db() as conn:
        row = conn.execute(
            "SELECT * FROM completions WHERE event_id = ? AND done_date = ?",
            (event_id, done_date),
        ).fetchone()
    return dict(row) if row else None


def complete_event(event_id: int, done_date: str, note: str = "", status: str = "done"):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO completions (event_id, done_date, note, status) VALUES (?,?,?,?)"
            " ON CONFLICT(event_id, done_date) DO UPDATE SET note=excluded.note, status=excluded.status",
            (event_id, done_date, note, status),
        )


def uncomplete_event(event_id: int, done_date: str):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM completions WHERE event_id = ? AND done_date = ?",
            (event_id, done_date),
        )


def get_completions_range(start: str, end: str) -> dict:
    """Returns {date_str: {event_id: {note, status}}}."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT event_id, done_date, note, status FROM completions WHERE done_date BETWEEN ? AND ?",
            (start, end),
        ).fetchall()
    result: dict = {}
    for r in rows:
        result.setdefault(r["done_date"], {})[r["event_id"]] = {
            "note": r["note"] or "",
            "status": r["status"] or "done",
        }
    return result


def get_completion_stats(events: list, days: int = 30) -> dict:
    """Returns {event_id: {done, applicable}} para los últimos N días."""
    today = date.today()
    start = (today - timedelta(days=days - 1)).isoformat()
    end   = today.isoformat()

    with get_db() as conn:
        rows = conn.execute(
            "SELECT event_id, COUNT(*) as n FROM completions"
            " WHERE done_date BETWEEN ? AND ? AND status = 'done'"
            " GROUP BY event_id",
            (start, end),
        ).fetchall()
    done_counts = {r["event_id"]: r["n"] for r in rows}

    result = {}
    for ev in events:
        applicable = sum(1 for i in range(days) if event_applies(ev, today - timedelta(days=i)))
        result[ev["id"]] = {"done": done_counts.get(ev["id"], 0), "applicable": applicable}
    return result
