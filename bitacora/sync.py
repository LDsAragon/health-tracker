"""Sincronización entre dos dispositivos de la misma persona.

El paquete es un archivo .db (un snapshot del perfil) que el usuario mueve como quiera. El
merge es fila por fila, última escritura gana, resuelto en SQL con ATTACH.

Todo local: no hay servidor, ni cuentas, ni nada que salga a internet.
"""
import os
import sqlite3
from datetime import datetime, timezone

from bitacora import database as db
import bitacora.database.conn as conn
from bitacora.database.schema import SCHEMA_VERSION

PENDIENTE = "sync-pendiente.db"

# Claves que el paquete lleva para identificarse. Van en su tabla settings porque es el único
# lugar del archivo donde se puede guardar algo sin inventar una tabla, y se excluyen del
# merge de ajustes para que no contaminen la base que recibe.
META = ("_sync_perfil_uid", "_sync_perfil_nombre", "_sync_dispositivo", "_sync_exportado")

# Hijo -> (columna con el id del padre, tabla padre). Esos enteros son LOCALES: la misma
# categoría es la 1 en una máquina y la 5 en la otra, así que hay que traducirlos por uid.
PADRES = {
    "journal_entries": ("category_id", "journal_categories"),
    "charts": ("category_id", "journal_categories"),
    "completions": ("event_id", "recurring_events"),
}

# Padres antes que hijos: un hijo necesita que su padre ya exista para traducir la referencia.
ORDEN = ("journal_categories", "recurring_events", "notes", "todos",
         "journal_entries", "charts", "completions")


# ── Exportar ─────────────────────────────────────────────────────────────────

def exportar(dest: str, perfil: dict | None = None, dispositivo: str = "") -> str:
    """Snapshot del perfil activo + la metadata de identidad dentro del propio archivo."""
    db.snapshot_to(dest)
    vals = {
        "_sync_perfil_uid": (perfil or {}).get("uid", ""),
        "_sync_perfil_nombre": (perfil or {}).get("nombre", ""),
        "_sync_dispositivo": dispositivo,
        "_sync_exportado": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S"),
    }
    c = sqlite3.connect(dest)
    try:
        for k, v in vals.items():
            c.execute("INSERT INTO settings (key, value) VALUES (?,?)"
                      " ON CONFLICT(key) DO UPDATE SET value = excluded.value", (k, v))
        c.commit()
    finally:
        c.close()
    return dest


def nombre_archivo(perfil: dict | None = None) -> str:
    slug = (perfil or {}).get("slug", "bitacora")
    return f"bitacora-sync-{slug}-{datetime.now().strftime('%Y-%m-%d')}.db"


def ruta_pendiente() -> str:
    """Ruta FIJA del paquete subido. Fija a propósito: así entre la vista previa y el aplicar
    no viaja ninguna ruta por el formulario y no hay que defenderse de un path traversal."""
    base = os.path.dirname(os.path.abspath(conn.DB_PATH)) or "."
    return os.path.join(base, PENDIENTE)


# ── Validación e identidad ───────────────────────────────────────────────────

def meta_de(paquete: str) -> dict:
    """Identidad que el paquete trae: de qué perfil y dispositivo salió, y de qué esquema."""
    c = sqlite3.connect(paquete)
    try:
        marcas = ",".join("?" * len(META))
        filas = c.execute(f"SELECT key, value FROM settings WHERE key IN ({marcas})",
                          META).fetchall()
        version = c.execute("PRAGMA user_version").fetchone()[0]
    finally:
        c.close()
    d = {k.replace("_sync_", ""): v for k, v in filas}
    d["version"] = version
    return d


def validar(paquete: str) -> tuple[bool, str]:
    if not db.is_valid_db(paquete):
        return False, "El archivo no parece una base de datos de Bitácora."
    version = meta_de(paquete)["version"]
    if version != SCHEMA_VERSION:
        return False, (f"El paquete es de otra versión de la app (esquema {version}, esta usa "
                       f"{SCHEMA_VERSION}). Actualizá las dos máquinas y volvé a exportar.")
    return True, ""


# ── SQL del merge ────────────────────────────────────────────────────────────

def _columnas(c, tabla) -> list:
    """Columnas comunes a las dos bases, sin `id`: es local y no significa nada afuera."""
    loc = [r[1] for r in c.execute(f"PRAGMA main.table_info({tabla})")]
    rem = {r[1] for r in c.execute(f"PRAGMA remoto.table_info({tabla})")}
    return [x for x in loc if x != "id" and x in rem]


def _id_padre(tabla) -> str:
    """Expresión que traduce el id del padre remoto al id que ese padre tiene acá."""
    _, padre = PADRES[tabla]
    return f"(SELECT l.id FROM main.{padre} l WHERE l.uid = rp.uid)"


def _join_padre(tabla) -> str:
    fk, padre = PADRES[tabla]
    return f"JOIN remoto.{padre} rp ON rp.id = r.{fk}"


def _where_altas(tabla) -> str:
    w = ["COALESCE(r.uid,'') != ''",
         f"r.uid NOT IN (SELECT uid FROM main.{tabla})",
         f"r.uid NOT IN (SELECT uid FROM main.deletions WHERE tabla = '{tabla}')"]
    if tabla in PADRES:
        # Si el padre no existe acá (lo borramos), la fila entraría con NULL y violaría el
        # NOT NULL. Se saltea en vez de reventar el merge entero.
        w.append(f"{_id_padre(tabla)} IS NOT NULL")
    if tabla == "completions":
        # Única tabla con otra clave única: UNIQUE(event_id, done_date). Si la misma rutina se
        # marcó hecha el mismo día en las dos máquinas por separado, los uid difieren pero la
        # clave natural choca. Representan el mismo hecho: se conserva la local.
        w.append("NOT EXISTS (SELECT 1 FROM main.completions mc WHERE"
                 f" mc.event_id = {_id_padre(tabla)} AND mc.done_date = r.done_date)")
    return " AND ".join(w)


def _where_updates(tabla) -> str:
    return (f"r.uid IN (SELECT uid FROM main.{tabla}) AND r.updated_at >"
            f" (SELECT COALESCE(m.updated_at,'') FROM main.{tabla} m WHERE m.uid = r.uid)")


def _where_bajas(tabla) -> str:
    return (f"d.tabla = '{tabla}' AND d.uid IN (SELECT uid FROM main.{tabla})"
            f" AND d.deleted_at > (SELECT COALESCE(m.updated_at,'')"
            f" FROM main.{tabla} m WHERE m.uid = d.uid)")


def _sql_altas(c, tabla) -> str:
    cols = _columnas(c, tabla)
    fk = PADRES[tabla][0] if tabla in PADRES else None
    join = _join_padre(tabla) if fk else ""
    sel = ", ".join(_id_padre(tabla) if x == fk else f"r.{x}" for x in cols)
    return (f"INSERT INTO {tabla} ({', '.join(cols)}) SELECT {sel}"
            f" FROM remoto.{tabla} r {join} WHERE {_where_altas(tabla)}")


def _sql_updates(c, tabla) -> str:
    """UPDATE ... FROM (SQLite >= 3.33). Copia el updated_at remoto tal cual: por eso el
    trigger de UPDATE lleva la guarda `WHEN NEW.updated_at = OLD.updated_at`."""
    cols = [x for x in _columnas(c, tabla) if x != "uid"]
    fk = PADRES[tabla][0] if tabla in PADRES else None
    sets = ", ".join(f"{x} = {_id_padre(tabla)}" if x == fk else f"{x} = r.{x}" for x in cols)
    origen = f"remoto.{tabla} r"
    extra = ""
    if fk:
        origen += f", remoto.{PADRES[tabla][1]} rp"
        extra = f" AND rp.id = r.{fk}"
    return (f"UPDATE {tabla} SET {sets} FROM {origen} WHERE {tabla}.uid = r.uid"
            f" AND r.updated_at > {tabla}.updated_at{extra}")


# ── Analizar y aplicar ───────────────────────────────────────────────────────

SQL_AJUSTES_NUEVOS = (
    "FROM remoto.settings r WHERE r.key NOT LIKE '_sync_%'"
    " AND COALESCE(r.updated_at,'') > COALESCE("
    "     (SELECT m.updated_at FROM main.settings m WHERE m.key = r.key), '')")


def _abrir(paquete):
    c = sqlite3.connect(conn.DB_PATH)
    c.row_factory = sqlite3.Row
    c.execute("ATTACH DATABASE ? AS remoto", (paquete,))
    return c


def analizar(paquete: str) -> dict:
    """Qué haría el merge, sin tocar nada. Usa exactamente los mismos WHERE que aplicar()."""
    c = _abrir(paquete)
    try:
        tablas, total = {}, {"altas": 0, "updates": 0, "bajas": 0}
        for t in ORDEN:
            join = _join_padre(t) if t in PADRES else ""
            altas = c.execute(f"SELECT COUNT(*) FROM remoto.{t} r {join}"
                              f" WHERE {_where_altas(t)}").fetchone()[0]
            ups = c.execute(f"SELECT COUNT(*) FROM remoto.{t} r"
                            f" WHERE {_where_updates(t)}").fetchone()[0]
            bajas = c.execute("SELECT COUNT(*) FROM remoto.deletions d"
                              f" WHERE {_where_bajas(t)}").fetchone()[0]
            if altas or ups or bajas:
                tablas[t] = {"altas": altas, "updates": ups, "bajas": bajas}
            total["altas"] += altas
            total["updates"] += ups
            total["bajas"] += bajas
        ajustes = c.execute(f"SELECT COUNT(*) {SQL_AJUSTES_NUEVOS}").fetchone()[0]
    finally:
        c.close()
    return {"tablas": tablas, "total": total, "ajustes": ajustes, "meta": meta_de(paquete)}


def aplicar(paquete: str) -> dict:
    """Backup previo + merge en una transacción. Devuelve el mismo resumen que analizar()."""
    resumen = analizar(paquete)
    db.snapshot_to(db.backup_path("health-presync"))
    c = _abrir(paquete)
    try:
        c.execute("BEGIN")
        for t in ORDEN:
            c.execute(_sql_altas(c, t))
            c.execute(_sql_updates(c, t))
            c.execute(f"DELETE FROM {t} WHERE uid IN (SELECT d.uid FROM remoto.deletions d"
                      f" WHERE {_where_bajas(t)})")
        # Los tombstones remotos se propagan DESPUÉS de borrar: el trigger de DELETE ya dejó
        # uno local con la hora de ahora, y este lo pisa con la fecha real del borrado.
        c.execute("INSERT OR REPLACE INTO deletions (tabla, uid, deleted_at)"
                  " SELECT tabla, uid, deleted_at FROM remoto.deletions")
        # Ajustes: última escritura gana por clave. La metadata del paquete no viaja.
        c.execute("INSERT INTO settings (key, value, updated_at)"
                  f" SELECT r.key, r.value, r.updated_at {SQL_AJUSTES_NUEVOS}"
                  " ON CONFLICT(key) DO UPDATE SET value = excluded.value,"
                  " updated_at = excluded.updated_at")
        # Las dos máquinas calculan position con MAX(position)+1, así que generan las mismas.
        # Solo importa el orden relativo (get_todos_for_date ordena por position, id).
        c.execute("UPDATE todos SET position = (SELECT COUNT(*) FROM todos t2"
                  " WHERE t2.todo_date = todos.todo_date"
                  " AND (t2.position < todos.position"
                  "      OR (t2.position = todos.position AND t2.id < todos.id)))")
        c.commit()
    except Exception:
        c.rollback()
        raise
    finally:
        c.close()
    return resumen
