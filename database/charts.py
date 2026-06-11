"""Gráficos personalizados guardados (tabla charts)."""
from .conn import get_db


def get_charts() -> list:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM charts ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def add_chart(category_id: int, field_label: str, title: str = "", range_days: int = 90):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO charts (category_id, field_label, title, range_days) VALUES (?,?,?,?)",
            (category_id, field_label, title, range_days),
        )


def delete_chart(chart_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM charts WHERE id = ?", (chart_id,))
