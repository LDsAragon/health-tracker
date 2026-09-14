"""Notas especiales: categorías (tipos) y entradas."""
import json
from .conn import get_db, snapshot_to, backup_path


def get_journal_categories(incluir_archivadas: bool = False) -> list:
    """⚠️ Por default solo las activas, que es lo que corresponde en el único lugar donde se
    ELIGE una: el alta del día. Todo lo que LEE historia —Estadísticas, la pantalla de
    categorías— pide `incluir_archivadas=True`: si archivar sacara la categoría de ahí, meses de
    datos desaparecerían de los gráficos y del resumen sin que nada avise."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM journal_categories"
            + ("" if incluir_archivadas else " WHERE active = 1")
            + " ORDER BY id"
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
    snapshot_to(backup_path("health-prerename"))

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


def count_journal_entries_by_category() -> dict:
    """{cat_id: cuántas notas tiene} — para decir en pantalla qué se lleva un borrado."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT category_id, COUNT(*) AS n FROM journal_entries GROUP BY category_id"
        ).fetchall()
    return {r["category_id"]: r["n"] for r in rows}


def set_journal_category_active(cat_id: int, activa: bool):
    """Archivar / desarchivar.

    Archivar la saca de donde se ESCRIBE (el alta del día) y de ningún lado donde se LEE: las
    notas viejas se siguen viendo en su día, en el calendario y en Estadísticas. Es lo que la
    separa de borrar, y por eso no pide confirmación: no se pierde nada y se deshace con un clic.
    """
    with get_db() as conn:
        conn.execute("UPDATE journal_categories SET active = ? WHERE id = ?",
                     (1 if activa else 0, cat_id))


def journal_field_usage() -> dict:
    """{cat_id: {etiqueta: cuántas entradas tienen algo guardado ahí}}.

    Quitar un campo de la categoría esconde para siempre lo anotado: tanto la vista como la
    edición iteran la definición, así que un valor sin campo no se ve en ningún lado. Esto es lo
    que permite decirlo ANTES de quitarlo, que es cuando sirve.
    """
    uso: dict = {}
    with get_db() as conn:
        rows = conn.execute(
            "SELECT category_id, values_json FROM journal_entries").fetchall()
    for r in rows:
        try:
            vals = json.loads(r["values_json"] or "{}")
        except ValueError:
            continue
        por_cat = uso.setdefault(r["category_id"], {})
        for label, v in vals.items():
            if str(v).strip():
                por_cat[label] = por_cat.get(label, 0) + 1
    return uso


def delete_journal_category(cat_id: int):
    """⚠️ Se lleva TODAS las notas de la categoría. Backup previo, como cualquier camino
    destructivo de la app: hasta un renombre de campo hace el suyo (migrate_entry_values)."""
    snapshot_to(backup_path("health-prejournal"))
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
