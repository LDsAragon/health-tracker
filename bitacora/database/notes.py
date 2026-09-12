"""Notas rápidas."""
from .conn import get_db


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


def search_notes(query: str) -> list:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM notes WHERE content LIKE ? ORDER BY note_date DESC, created_at DESC",
            (f"%{query}%",),
        ).fetchall()
    return [dict(r) for r in rows]
