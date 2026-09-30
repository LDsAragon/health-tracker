"""Gráficos personalizados guardados (tabla charts)."""
from .conn import get_db

# Lo que define un gráfico. Está acá y no repartido entre el INSERT y el UPDATE porque los dos
# tienen que escribir exactamente lo mismo: un campo que entre solo por uno de los dos caminos es
# un campo que se pierde al editar.
CAMPOS = ("category_id", "field_label", "title", "group_field", "bucket", "tag_filter")


def get_charts() -> list:
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM charts ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def add_chart(category_id: int, field_label: str, title: str = "",
              group_field: str = "", bucket: str = "day", tag_filter: str = ""):
    """field_label admite varios campos unidos con '|' (se suman en el gráfico).

    ⚠️ `range_days` no se escribe más. La columna sigue existiendo —y por eso lleva un DEFAULT—
    pero **nadie la lee** desde que hay un solo período para toda la pantalla: el render usa el
    que sale del selector. Se seguía guardando un 90 fijo, tomado de un campo que el formulario
    ya no tiene. Un dato que nada consulta y que nadie puede cambiar solo sirve para confundir al
    que lo encuentre. No se borra la columna porque `init_db()` corre en cada request y un
    `DROP COLUMN` ahí sería un camino destructivo por request; queda vestigial, como
    `todos.snoozed_until`.
    """
    with get_db() as conn:
        conn.execute(
            "INSERT INTO charts (category_id, field_label, title,"
            " group_field, bucket, tag_filter) VALUES (?,?,?,?,?,?)",
            (category_id, field_label, title, group_field, bucket, tag_filter),
        )


def update_chart(chart_id: int, datos: dict):
    """Reescribe el gráfico entero, con los mismos campos que el alta (`CAMPOS`).

    Entero y no por campo: un UPDATE parcial vuelve a abrir la puerta a que la pantalla mande
    menos de lo que define un gráfico y el resto se quede con lo viejo a medias.
    """
    with get_db() as conn:
        conn.execute(
            "UPDATE charts SET " + ", ".join(f"{c} = ?" for c in CAMPOS) + " WHERE id = ?",
            tuple(datos[c] for c in CAMPOS) + (chart_id,),
        )


def delete_chart(chart_id: int):
    with get_db() as conn:
        conn.execute("DELETE FROM charts WHERE id = ?", (chart_id,))
