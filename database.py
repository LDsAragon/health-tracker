import sqlite3
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
                created_at  TEXT DEFAULT (datetime('now'))
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
    # Migración: agregar columna color si no existe (para DBs creadas antes)
    try:
        with get_db() as conn:
            conn.execute("ALTER TABLE notes ADD COLUMN color TEXT DEFAULT ''")
    except Exception:
        pass


# ── Notes ─────────────────────────────────────────────────────────────────────

def add_note(note_date: str, content: str, color: str = ""):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO notes (note_date, content, color) VALUES (?, ?, ?)",
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
            "INSERT INTO recurring_events (title, color, recurrence, start_date) VALUES (?,?,?,?)",
            (data["title"], data["color"], data["recurrence"], data["start_date"]),
        )


def update_recurring_event(event_id: int, data: dict):
    with get_db() as conn:
        conn.execute(
            "UPDATE recurring_events SET title=?, color=?, recurrence=?, start_date=? WHERE id=?",
            (data["title"], data["color"], data["recurrence"], data["start_date"], event_id),
        )


def delete_recurring_event(event_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM recurring_events WHERE id = ?", (event_id,))
        conn.execute("DELETE FROM completions WHERE event_id = ?", (event_id,))


def event_applies(event: dict, d: date) -> bool:
    """True if this recurring event should appear on date d."""
    if not event.get("start_date"):
        return False
    start = date.fromisoformat(event["start_date"])
    if d < start:
        return False
    rec = event["recurrence"]
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


def complete_event(event_id: int, done_date: str, note: str = ""):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO completions (event_id, done_date, note) VALUES (?,?,?)"
            " ON CONFLICT(event_id, done_date) DO UPDATE SET note = ?",
            (event_id, done_date, note, note),
        )


def uncomplete_event(event_id: int, done_date: str):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM completions WHERE event_id = ? AND done_date = ?",
            (event_id, done_date),
        )


def get_completions_range(start: str, end: str) -> dict:
    """Returns {date_str: {event_id: note}}."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT event_id, done_date, note FROM completions WHERE done_date BETWEEN ? AND ?",
            (start, end),
        ).fetchall()
    result: dict = {}
    for r in rows:
        result.setdefault(r["done_date"], {})[r["event_id"]] = r["note"] or ""
    return result
