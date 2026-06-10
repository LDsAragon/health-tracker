import sqlite3
import json
from datetime import date

DB_PATH = "health.db"


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS notes (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                note_date   TEXT NOT NULL,
                content     TEXT NOT NULL,
                color       TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            );

            CREATE TABLE IF NOT EXISTS recurring_events (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                title       TEXT NOT NULL,
                color       TEXT DEFAULT '#6366f1',
                recurrence  TEXT NOT NULL,
                start_date  TEXT NOT NULL,
                active      INTEGER DEFAULT 1
            );

            CREATE TABLE IF NOT EXISTS completions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id    INTEGER NOT NULL,
                done_date   TEXT NOT NULL,
                note        TEXT,
                UNIQUE(event_id, done_date)
            );
        """)
    # Migraciones para DBs creadas antes
    try:
        with get_db() as conn:
            conn.execute("ALTER TABLE notes ADD COLUMN color TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        with get_db() as conn:
            conn.execute("ALTER TABLE completions ADD COLUMN status TEXT DEFAULT 'done'")
    except Exception:
        pass
    try:
        with get_db() as conn:
            conn.execute("ALTER TABLE recurring_events ADD COLUMN end_date TEXT DEFAULT ''")
    except Exception:
        pass
    try:
        with get_db() as conn:
            conn.execute("ALTER TABLE recurring_events ADD COLUMN show_in_calendar INTEGER DEFAULT 1")
    except Exception:
        pass
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS journal_categories (
                id               INTEGER PRIMARY KEY AUTOINCREMENT,
                name             TEXT NOT NULL,
                color            TEXT DEFAULT '#6366f1',
                fields_json      TEXT DEFAULT '[]',
                show_in_calendar INTEGER DEFAULT 0,
                active           INTEGER DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS journal_entries (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                entry_date  TEXT NOT NULL,
                values_json TEXT DEFAULT '{}',
                tags        TEXT DEFAULT '',
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            );
            CREATE TABLE IF NOT EXISTS todos (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                todo_date   TEXT NOT NULL,
                text        TEXT NOT NULL,
                done        INTEGER DEFAULT 0,
                position    INTEGER DEFAULT 0,
                created_at  TEXT DEFAULT (datetime('now','localtime'))
            );
        """)


# ── Notes ─────────────────────────────────────────────────────────────────────

def add_note(note_date: str, content: str, color: str = ""):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO notes (note_date, content, color, created_at)"
            " VALUES (?, ?, ?, datetime('now','localtime'))",
            (note_date, content, color),
        )


def update_note(note_id: int, content: str, color: str = ""):
    with get_db() as conn:
        conn.execute(
            "UPDATE notes SET content = ?, color = ? WHERE id = ?",
            (content, color, note_id),
        )


def delete_note(note_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))


def get_notes_for_date(note_date: str) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM notes WHERE note_date = ? ORDER BY created_at", (note_date,)
        ).fetchall()
    return [dict(r) for r in rows]


def get_notes_range(start: str, end: str) -> dict:
    """Returns {date_str: [note, ...]}."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM notes WHERE note_date BETWEEN ? AND ? ORDER BY note_date, created_at",
            (start, end),
        ).fetchall()
    result: dict = {}
    for r in rows:
        r = dict(r)
        result.setdefault(r["note_date"], []).append(r)
    return result


# ── Recurring events ───────────────────────────────────────────────────────────

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
        conn.execute(
            "UPDATE recurring_events SET end_date = ? WHERE id = ?", (cutoff, event_id)
        )
        conn.execute(
            "DELETE FROM completions WHERE event_id = ? AND done_date > ?", (event_id, cutoff)
        )


def set_recurring_visibility(event_id: int, show: bool):
    """Muestra/oculta el evento en calendario y semana (en la vista del día siempre se ve)."""
    with get_db() as conn:
        conn.execute(
            "UPDATE recurring_events SET show_in_calendar = ? WHERE id = ?",
            (1 if show else 0, event_id),
        )


def event_applies(event: dict, d: date) -> bool:
    """True if this recurring event should appear on date d."""
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


# ── Completions ────────────────────────────────────────────────────────────────

def get_completion(event_id: int, done_date: str) -> dict | None:
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
    """Returns {event_id: {done, applicable}} for the last N days."""
    from datetime import timedelta
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
        applicable = sum(
            1 for i in range(days)
            if event_applies(ev, today - timedelta(days=i))
        )
        result[ev["id"]] = {
            "done": done_counts.get(ev["id"], 0),
            "applicable": applicable,
        }
    return result


def search_notes(query: str) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM notes WHERE content LIKE ? ORDER BY note_date DESC, created_at DESC",
            (f"%{query}%",),
        ).fetchall()
    return [dict(r) for r in rows]


# ── Journal categories ─────────────────────────────────────────────────────────

def get_journal_categories() -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM journal_categories WHERE active = 1 ORDER BY id"
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["fields"] = json.loads(d["fields_json"] or "[]")
        result.append(d)
    return result


def add_journal_category(data: dict):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO journal_categories (name, color, fields_json, show_in_calendar) VALUES (?,?,?,?)",
            (data["name"], data.get("color", "#6366f1"),
             data.get("fields_json", "[]"), int(data.get("show_in_calendar", 0))),
        )


def update_journal_category(cat_id: int, data: dict):
    with get_db() as conn:
        conn.execute(
            "UPDATE journal_categories SET name=?, color=?, fields_json=?, show_in_calendar=? WHERE id=?",
            (data["name"], data.get("color", "#6366f1"),
             data.get("fields_json", "[]"), int(data.get("show_in_calendar", 0)), cat_id),
        )


def delete_journal_category(cat_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM journal_entries WHERE category_id = ?", (cat_id,))
        conn.execute("DELETE FROM journal_categories WHERE id = ?", (cat_id,))


# ── Journal entries ────────────────────────────────────────────────────────────

def get_journal_entries_for_date(entry_date: str) -> list:
    with get_db() as conn:
        rows = conn.execute(
            """SELECT je.*, jc.name AS category_name, jc.color AS category_color,
                      jc.fields_json AS category_fields_json
               FROM journal_entries je
               JOIN journal_categories jc ON je.category_id = jc.id
               WHERE je.entry_date = ?
               ORDER BY je.created_at""",
            (entry_date,),
        ).fetchall()
    result = []
    for r in rows:
        d = dict(r)
        d["values"] = json.loads(d["values_json"] or "{}")
        d["category_fields"] = json.loads(d["category_fields_json"] or "[]")
        result.append(d)
    return result


def get_journal_entries_range(start: str, end: str) -> dict:
    """Returns {date_str: [entry, ...]}."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT je.*, jc.name AS category_name, jc.color AS category_color,
                      jc.show_in_calendar AS show_in_calendar
               FROM journal_entries je
               JOIN journal_categories jc ON je.category_id = jc.id
               WHERE je.entry_date BETWEEN ? AND ?
               ORDER BY je.entry_date, je.created_at""",
            (start, end),
        ).fetchall()
    result: dict = {}
    for r in rows:
        d = dict(r)
        d["values"] = json.loads(d["values_json"] or "{}")
        result.setdefault(d["entry_date"], []).append(d)
    return result


def add_journal_entry(data: dict):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO journal_entries (category_id, entry_date, values_json, tags, created_at)"
            " VALUES (?,?,?,?, datetime('now','localtime'))",
            (data["category_id"], data["entry_date"],
             data.get("values_json", "{}"), data.get("tags", "")),
        )


def update_journal_entry(entry_id: int, data: dict):
    with get_db() as conn:
        conn.execute(
            "UPDATE journal_entries SET values_json=?, tags=? WHERE id=?",
            (data.get("values_json", "{}"), data.get("tags", ""), entry_id),
        )


def delete_journal_entry(entry_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM journal_entries WHERE id = ?", (entry_id,))


# ── To-dos diarios ───────────────────────────────────────────────────────────────

def get_todos_for_date(todo_date: str) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM todos WHERE todo_date = ? ORDER BY position, id",
            (todo_date,),
        ).fetchall()
    return [dict(r) for r in rows]


def _next_todo_position(conn, todo_date: str) -> int:
    row = conn.execute(
        "SELECT COALESCE(MAX(position), -1) + 1 AS pos FROM todos WHERE todo_date = ?",
        (todo_date,),
    ).fetchone()
    return row["pos"]


def add_todo(todo_date: str, text: str):
    with get_db() as conn:
        pos = _next_todo_position(conn, todo_date)
        conn.execute(
            "INSERT INTO todos (todo_date, text, position, created_at)"
            " VALUES (?,?,?, datetime('now','localtime'))",
            (todo_date, text, pos),
        )


def toggle_todo(todo_id: int):
    with get_db() as conn:
        conn.execute(
            "UPDATE todos SET done = CASE done WHEN 1 THEN 0 ELSE 1 END WHERE id = ?",
            (todo_id,),
        )


def update_todo(todo_id: int, text: str):
    with get_db() as conn:
        conn.execute("UPDATE todos SET text = ? WHERE id = ?", (text, todo_id))


def move_todo(todo_id: int, new_date: str):
    """Mueve el to-do a otro día, al final de la lista de ese día."""
    with get_db() as conn:
        pos = _next_todo_position(conn, new_date)
        conn.execute(
            "UPDATE todos SET todo_date = ?, position = ? WHERE id = ?",
            (new_date, pos, todo_id),
        )


def delete_todo(todo_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM todos WHERE id = ?", (todo_id,))


def reorder_todos(todo_date: str, ordered_ids: list):
    """Asigna position según el orden recibido (acotado a ese día)."""
    with get_db() as conn:
        for pos, tid in enumerate(ordered_ids):
            conn.execute(
                "UPDATE todos SET position = ? WHERE id = ? AND todo_date = ?",
                (pos, int(tid), todo_date),
            )


def get_todos_range(start: str, end: str) -> dict:
    """Returns {date_str: [todo, ...]} ordenados por position."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM todos WHERE todo_date BETWEEN ? AND ? ORDER BY todo_date, position, id",
            (start, end),
        ).fetchall()
    result: dict = {}
    for r in rows:
        result.setdefault(r["todo_date"], []).append(dict(r))
    return result


def get_todo_counts_range(start: str, end: str) -> dict:
    """Returns {date_str: {done, total}} para el indicador del calendario."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT todo_date, COUNT(*) AS total, SUM(done) AS done"
            " FROM todos WHERE todo_date BETWEEN ? AND ? GROUP BY todo_date",
            (start, end),
        ).fetchall()
    return {r["todo_date"]: {"done": r["done"] or 0, "total": r["total"]} for r in rows}
