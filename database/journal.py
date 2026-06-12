"""Notas especiales: categorías (tipos) y entradas."""
import json
import os
from datetime import datetime
from .conn import get_db, snapshot_to, db_path


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


def migrate_entry_values(cat_id: int, label_renames: dict | None = None,
                         option_renames: dict | None = None) -> int:
    """Acompaña renombres de la definición: re-clava etiquetas/valores guardados.

    Las entradas guardan {etiqueta: valor} literal: renombrar un campo o una
    opción sin esto deja los datos viejos invisibles para gráficos y resumen.
    label_renames: {etiqueta_vieja: nueva}. option_renames: {etiqueta: (de, a)}
    (etiqueta ya con su nombre NUEVO si se renombró a la vez).
    También actualiza los gráficos guardados (tabla charts) que referencien
    etiquetas renombradas. Backup automático previo (health-prerename-<ts>.db).
    Devuelve cuántas entradas se modificaron.
    """
    label_renames = label_renames or {}
    option_renames = option_renames or {}
    if not label_renames and not option_renames:
        return 0
    base = os.path.dirname(os.path.abspath(db_path())) or "."
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    snapshot_to(os.path.join(base, f"health-prerename-{ts}.db"))

    changed = 0
    with get_db() as conn:
        rows = conn.execute(
            "SELECT id, values_json FROM journal_entries WHERE category_id = ?",
            (cat_id,)).fetchall()
        for r in rows:
            try:
                vals = json.loads(r["values_json"] or "{}")
            except ValueError:
                continue
            dirty = False
            for old, new in label_renames.items():
                if old in vals and new not in vals:
                    vals[new] = vals.pop(old)
                    dirty = True
            for label, (de, a) in option_renames.items():
                if vals.get(label) == de:
                    vals[label] = a
                    dirty = True
            if dirty:
                conn.execute("UPDATE journal_entries SET values_json = ? WHERE id = ?",
                             (json.dumps(vals, ensure_ascii=False), r["id"]))
                changed += 1
        if label_renames:
            for ch in conn.execute(
                    "SELECT id, field_label, group_field FROM charts WHERE category_id = ?",
                    (cat_id,)).fetchall():
                fl = "|".join(label_renames.get(x, x)
                              for x in (ch["field_label"] or "").split("|") if x)
                gf = label_renames.get(ch["group_field"] or "", ch["group_field"] or "")
                if fl != (ch["field_label"] or "") or gf != (ch["group_field"] or ""):
                    conn.execute("UPDATE charts SET field_label = ?, group_field = ? WHERE id = ?",
                                 (fl, gf, ch["id"]))
    return changed


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
