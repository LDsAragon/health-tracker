"""Eventos recurrentes (rutinas) + completaciones + lógica de recurrencia."""
from datetime import date, timedelta
from .conn import get_db


def get_recurring_events() -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM recurring_events WHERE active = 1 ORDER BY id"
        ).fetchall()
    return [dict(r) for r in rows]


# Lo que comparten el alta y la edición. `tipo` default 'rutina' y el resto en blanco: así un
# caller viejo (o un test) que solo pase título y frecuencia sigue creando lo mismo de antes.
_CAMPOS = ("title", "color", "recurrence", "start_date", "end_date", "tipo", "group_id",
           "birth_year", "aviso_dias")


def _valores(data: dict) -> tuple:
    return (
        data["title"], data["color"], data["recurrence"], data["start_date"],
        data.get("end_date", ""), data.get("tipo", "rutina"), data.get("group_id") or None,
        data.get("birth_year") or None, int(data.get("aviso_dias") or 0),
    )


def add_recurring_event(data: dict):
    cols = ", ".join(_CAMPOS)
    huecos = ", ".join("?" * len(_CAMPOS))
    with get_db() as conn:
        conn.execute(f"INSERT INTO recurring_events ({cols}) VALUES ({huecos})", _valores(data))


def update_recurring_event(event_id: int, data: dict):
    sets = ", ".join(f"{c}=?" for c in _CAMPOS)
    with get_db() as conn:
        conn.execute(f"UPDATE recurring_events SET {sets} WHERE id=?",
                     _valores(data) + (event_id,))


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
    if rec == "yearly":
        # ⚠️ Por MES-DÍA, no por días transcurridos. Un año son 365 o 366, así que con `every:365`
        # —o el `every:364` con el que se venía modelando un cumpleaños— la fecha se corre solita:
        # el "Cumple del pablo" del 5 de mayo caía el 1 en 2026 y en febrero para 2078.
        if (start.month, start.day) == (2, 29) and not _bisiesto(d.year):
            # El 29 de febrero se festeja el 28: desaparecer tres de cada cuatro años es peor.
            return (d.month, d.day) == (2, 28)
        return (d.month, d.day) == (start.month, start.day)
    return False


def _bisiesto(anio: int) -> bool:
    return anio % 4 == 0 and (anio % 100 != 0 or anio % 400 == 0)


def proxima_fecha(event: dict, desde: date):
    """La próxima vez que cae el evento a partir de `desde` (incluido), o None.

    Se usa para los avisos con antelación, que preguntan "¿cuánto falta?" y no "¿es hoy?".
    Busca día a día hasta un año y medio: cubre lo anual sin volverse una fórmula por frecuencia,
    que es donde se coló el error de los 364 días.
    """
    for i in range(550):
        d = desde + timedelta(days=i)
        if event_applies(event, d):
            return d
    return None


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
        # ⚠️ Los recordatorios no tienen adherencia: una rutina se mide, un recordatorio avisa.
        # Un "12 de 15 · 80%" sobre un cumpleaños no significa nada —el de Pablo arrastraba un
        # 0%—, así que se devuelven con applicable en 0 y la pantalla no renderiza el porcentaje.
        if ev.get("tipo") == "recordatorio":
            result[ev["id"]] = {"done": done_counts.get(ev["id"], 0), "applicable": 0}
            continue
        applicable = sum(1 for i in range(days) if event_applies(ev, today - timedelta(days=i)))
        result[ev["id"]] = {"done": done_counts.get(ev["id"], 0), "applicable": applicable}
    return result


def avisos_proximos(events: list, desde: date) -> list:
    """Recordatorios que se vienen dentro de su antelación, con cuántos días faltan.

    Separado de `event_applies` a propósito: "¿aplica hoy?" y "¿cuánto falta?" son dos preguntas
    distintas, y mezclarlas haría que un recordatorio con aviso apareciera como si el día fuera
    hoy. El que cae **hoy** no es un aviso: ese ya sale por el camino normal.
    """
    out = []
    for ev in events:
        dias_aviso = ev.get("aviso_dias") or 0
        if ev.get("tipo") != "recordatorio" or dias_aviso <= 0:
            continue
        prox = proxima_fecha(ev, desde + timedelta(days=1))
        if prox and (prox - desde).days <= dias_aviso:
            out.append({**ev, "fecha": prox.isoformat(), "faltan": (prox - desde).days})
    return sorted(out, key=lambda e: e["faltan"])


# ── Grupos (las secciones de la pantalla de Rutinas) ─────────────────────────────

def get_event_groups() -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM recurring_groups ORDER BY tipo, position, name"
        ).fetchall()
    return [dict(r) for r in rows]


def add_event_group(data: dict) -> int:
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO recurring_groups (name, color, tipo, especial) VALUES (?,?,?,?)",
            (data["name"], data.get("color", "#6366f1"), data.get("tipo", "rutina"),
             data.get("especial", "")),
        )
        return cur.lastrowid


def update_event_group(group_id: int, data: dict):
    """Nombre, color y tipo. `especial` NO se edita: es lo que define el comportamiento."""
    with get_db() as conn:
        conn.execute(
            "UPDATE recurring_groups SET name = ?, color = ?, tipo = ? WHERE id = ?",
            (data["name"], data.get("color", "#6366f1"), data.get("tipo", "rutina"), group_id),
        )


def delete_event_group(group_id: int) -> bool:
    """Borra el grupo y deja sus rutinas SIN grupo. Devuelve si se pudo.

    ⚠️ Dos cosas que no se negocian: las rutinas **nunca** se borran con el grupo (perder datos
    del usuario por reordenar una pantalla sería absurdo), y un grupo `especial` no se puede
    borrar —es el que enciende el comportamiento de los cumpleaños—.
    """
    with get_db() as conn:
        row = conn.execute("SELECT especial FROM recurring_groups WHERE id = ?",
                           (group_id,)).fetchone()
        if not row or row["especial"]:
            return False
        conn.execute("UPDATE recurring_events SET group_id = NULL WHERE group_id = ?", (group_id,))
        conn.execute("DELETE FROM recurring_groups WHERE id = ?", (group_id,))
    return True
