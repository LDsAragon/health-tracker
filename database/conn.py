"""Conexión a SQLite. DB_PATH desde env HT_DB (default health.db).
get_db lee DB_PATH dinámicamente → los tests parchean database.conn.DB_PATH."""
import os
import sqlite3
from datetime import datetime

DB_PATH = os.environ.get("HT_DB", "health.db")

# Tablas que existen desde el inicio: sirven para reconocer una DB válida de la app.
CORE_TABLES = {"notes", "recurring_events", "settings"}


def db_path():
    return DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _columns(conn, table):
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}


# ── Backup / restore ─────────────────────────────────────────────────────────────

def snapshot_to(dest_path):
    """Copia consistente de la DB actual a dest_path (incluye datos del WAL).

    Usa la API de backup de SQLite (snapshot atómico) y deja el destino en modo
    rollback (DELETE) para que el archivo descargado no arrastre sidecars -wal/-shm.
    """
    src = sqlite3.connect(DB_PATH)
    try:
        dst = sqlite3.connect(dest_path)
        try:
            src.backup(dst)
            dst.execute("PRAGMA journal_mode=DELETE")
        finally:
            dst.close()
    finally:
        src.close()


def is_valid_db(path):
    """True si `path` es una SQLite íntegra con las tablas core de la app."""
    try:
        conn = sqlite3.connect(path)
        try:
            integrity = conn.execute("PRAGMA integrity_check").fetchone()
            tables = {r[0] for r in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        finally:
            conn.close()
    except sqlite3.Error:
        return False
    return bool(integrity) and integrity[0] == "ok" and CORE_TABLES.issubset(tables)


def backup_path(prefix: str) -> str:
    """Ruta para un backup automático: <dir de la DB>/backups/<prefix>-<ts>.db.

    Todos los backups (diarios y pre-operación) viven en la misma carpeta
    backups/, en vez de ensuciar la raíz de los datos.
    """
    base = os.path.join(os.path.dirname(os.path.abspath(DB_PATH)) or ".", "backups")
    os.makedirs(base, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d-%H%M%S")
    return os.path.join(base, f"{prefix}-{ts}.db")


def reset_db():
    """Borra TODOS los datos: backup automático previo + drop de todas las tablas.

    Devuelve el nombre del backup pre-reset (queda en backups/ junto a la DB).
    No recrea el esquema: el caller debe llamar a init_db() después.
    """
    dest = backup_path("health-prereset")
    backup_name = os.path.basename(dest)
    snapshot_to(dest)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute("PRAGMA busy_timeout=5000")
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()]
        for t in tables:
            conn.execute(f'DROP TABLE IF EXISTS "{t}"')
        conn.commit()
        conn.execute("VACUUM")
    finally:
        conn.close()
    return backup_name


def restore_from(src_path):
    """Valida `src_path` y reemplaza el contenido de la DB actual (con pre-restore backup).

    Devuelve (ok: bool, mensaje: str). Si la validación falla no toca nada.
    Usa la API de backup de SQLite (copia páginas de src → DB activa) en vez de
    reemplazar el archivo: maneja los locks internamente y evita el problema de
    "archivo en uso" de Windows con os.replace.
    """
    if not is_valid_db(src_path):
        return False, "El archivo no parece una base de datos válida de la app."
    snapshot_to(backup_path("health-prerestore"))
    src = sqlite3.connect(src_path)
    try:
        dst = sqlite3.connect(DB_PATH)
        try:
            dst.execute("PRAGMA busy_timeout=5000")
            src.backup(dst)          # sobreescribe el contenido de la DB activa
        finally:
            dst.close()
    finally:
        src.close()
    return True, "Base de datos restaurada correctamente."
