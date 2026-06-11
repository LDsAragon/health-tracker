"""Notas especiales: categorías (tipos) y entradas."""
import json
from .conn import get_db


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
