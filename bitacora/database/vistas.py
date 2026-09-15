"""Cómo dejaste acomodada cada pantalla: anchos, altos, zoom y desplegables.

Vivía en `localStorage` y se perdía en cada arranque de la app de escritorio (el origen cambia
con el puerto). Acá se guarda **solo lo que el usuario cambió**: los defaults siguen declarados
donde ya estaban —las custom properties del CSS, el `abiertoPorDefecto` de cada colapsable, el
zoom en 1—, así que "reiniciar una vista" es borrarle las filas y dejar que vuelva el default.

El esquema y el porqué de que esta tabla no sincronice están en `schema.py`.
"""
from bitacora.appconfig import clave_de_vista_valida
from .conn import get_db


def get_prefs() -> dict:
    """{clave: valor} de todas las vistas. Se inyectan enteras en la página: son un puñado de
    filas —el registro de `appconfig.VISTAS` acota cuáles pueden existir— y así la lectura desde
    el JS es síncrona y no hay que saber en qué vista estás para leer."""
    with get_db() as conn:
        return {r["clave"]: r["valor"]
                for r in conn.execute("SELECT clave, valor FROM vista_prefs").fetchall()}


def set_pref(vista: str, clave: str, valor: str) -> bool:
    """Guarda una preferencia. Devuelve False si la clave no es de esa vista."""
    if not clave_de_vista_valida(vista, clave):
        return False
    with get_db() as conn:
        conn.execute(
            "INSERT INTO vista_prefs (vista, clave, valor) VALUES (?,?,?)"
            " ON CONFLICT(vista, clave) DO UPDATE SET valor = excluded.valor",
            (vista, clave, valor),
        )
    return True


def borrar_pref(vista: str, clave: str):
    """Saca la fila: el valor vuelve al default de donde salga (el CSS, el colapsable)."""
    with get_db() as conn:
        conn.execute("DELETE FROM vista_prefs WHERE vista = ? AND clave = ?", (vista, clave))


def reset_vista(vista: str) -> int:
    """Devuelve una vista a como viene de fábrica. Las otras no se tocan: es la razón de ser de
    que la tabla tenga columna `vista` y no sea un blob de preferencias sueltas."""
    with get_db() as conn:
        cur = conn.execute("DELETE FROM vista_prefs WHERE vista = ?", (vista,))
        return cur.rowcount
