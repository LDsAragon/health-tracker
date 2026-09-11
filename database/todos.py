"""Tareas (Lista de tareas) por día."""
from .conn import get_db


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


def toggle_todo(todo_id: int) -> bool:
    """Invierte el estado done del to-do y retorna True si quedó como hecho."""
    with get_db() as conn:
        # Los CASE se evalúan contra la fila original, así que done_at sigue al done nuevo.
        conn.execute(
            "UPDATE todos SET done = CASE done WHEN 1 THEN 0 ELSE 1 END,"
            " done_at = CASE done WHEN 1 THEN '' ELSE datetime('now','localtime') END"
            " WHERE id = ?",
            (todo_id,),
        )
        row = conn.execute("SELECT done FROM todos WHERE id = ?", (todo_id,)).fetchone()
        return bool(row and row["done"])


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


# --- Visor de tareas: atrasadas, postergación y filtros transversales ---

# Una tarea atrasada es la que sigue abierta, quedó antes del corte y no está postergada.
_OVERDUE_WHERE = (
    "done = 0 AND todo_date < ? AND (COALESCE(snoozed_until, '') = '' OR snoozed_until <= ?)"
)


def get_overdue_todos(before: str, today: str) -> list:
    """Tareas abiertas anteriores a `before` cuya postergación ya venció."""
    with get_db() as conn:
        rows = conn.execute(
            f"SELECT * FROM todos WHERE {_OVERDUE_WHERE} ORDER BY todo_date, position, id",
            (before, today),
        ).fetchall()
    return [dict(r) for r in rows]


def count_overdue_todos(before: str, today: str) -> int:
    """Solo el conteo: la usa el badge del navbar en cada request."""
    with get_db() as conn:
        row = conn.execute(
            f"SELECT COUNT(*) AS n FROM todos WHERE {_OVERDUE_WHERE}", (before, today)
        ).fetchone()
    return row["n"]


def snooze_todo(todo_id: int, until: str):
    """Silencia el aviso hasta `until` sin mover la tarea de día."""
    with get_db() as conn:
        conn.execute("UPDATE todos SET snoozed_until = ? WHERE id = ?", (until, todo_id))


def move_todos(ids: list, new_date: str):
    """Mueve varias tareas al final de `new_date`, conservando el orden recibido."""
    if not ids:
        return
    with get_db() as conn:
        pos = _next_todo_position(conn, new_date)
        for tid in ids:
            conn.execute(
                "UPDATE todos SET todo_date = ?, position = ? WHERE id = ?",
                (new_date, pos, int(tid)),
            )
            pos += 1


def get_todos_filtered(start=None, end=None, status: str = "todas", q: str = "") -> list:
    """Tareas del rango (cotas opcionales) filtradas por estado y texto."""
    where, params = [], []
    if start:
        where.append("todo_date >= ?")
        params.append(start)
    if end:
        where.append("todo_date <= ?")
        params.append(end)
    if status == "pendientes":
        where.append("done = 0")
    elif status == "hechas":
        where.append("done = 1")
    if q:
        where.append("text LIKE ?")
        params.append(f"%{q}%")
    sql = "SELECT * FROM todos"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY todo_date, position, id"
    with get_db() as conn:
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]
