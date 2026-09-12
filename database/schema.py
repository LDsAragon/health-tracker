"""Esquema, migraciones declarativas y triggers de identidad para sincronizar."""
from .conn import get_db, _columns

# Versión del esquema, en PRAGMA user_version. Dos usos:
#  1. init_db() la usa como guarda: corre en CADA request y sin esto pagaba los COMMIT/fsync
#     de dos executescript por página.
#  2. el import de sincronización va a poder rechazar un archivo incompatible.
# ⚠️ AL AGREGAR UNA MIGRACIÓN HAY QUE SUBIRLA. Si no, las DBs ya instaladas se saltean el
# paso y nunca reciben la columna nueva.
SCHEMA_VERSION = 2

# Tablas que participan de la sincronización entre dispositivos. `settings` queda afuera a
# propósito: mezcla preferencias de la persona (formato de fecha) con las del dispositivo
# (tema, vista de inicio), y sincronizarla pisaría las segundas. Las tablas legacy del
# tracker original (entries, goals, custom_events, event_logs) tampoco entran: siguen vivas
# con datos en las DBs instaladas pero la app ya no las usa.
SYNCABLE = ("notes", "recurring_events", "completions", "journal_categories",
            "journal_entries", "todos", "charts")

SCHEMA = """
    CREATE TABLE IF NOT EXISTS notes (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        note_date   TEXT NOT NULL,
        content     TEXT NOT NULL,
        color       TEXT DEFAULT '',
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS recurring_events (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        title       TEXT NOT NULL,
        color       TEXT DEFAULT '#6366f1',
        recurrence  TEXT NOT NULL,
        start_date  TEXT NOT NULL,
        active      INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS completions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        event_id    INTEGER NOT NULL,
        done_date   TEXT NOT NULL,
        note        TEXT,
        UNIQUE(event_id, done_date)
    );
    CREATE TABLE IF NOT EXISTS journal_categories (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        name             TEXT NOT NULL,
        color            TEXT DEFAULT '#6366f1',
        fields_json      TEXT DEFAULT '[]',
        show_in_calendar INTEGER DEFAULT 0,
        active           INTEGER DEFAULT 1
    );
    CREATE TABLE IF NOT EXISTS journal_entries (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        entry_date  TEXT NOT NULL,
        values_json TEXT DEFAULT '{}',
        tags        TEXT DEFAULT '',
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE TABLE IF NOT EXISTS todos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        todo_date   TEXT NOT NULL,
        text        TEXT NOT NULL,
        done        INTEGER DEFAULT 0,
        position    INTEGER DEFAULT 0,
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    );
    CREATE INDEX IF NOT EXISTS idx_todos_date ON todos(todo_date);
    CREATE TABLE IF NOT EXISTS settings (
        key   TEXT PRIMARY KEY,
        value TEXT
    );
    CREATE TABLE IF NOT EXISTS charts (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        category_id INTEGER NOT NULL,
        field_label TEXT NOT NULL,
        title       TEXT DEFAULT '',
        range_days  INTEGER DEFAULT 90,
        group_field TEXT DEFAULT '',
        bucket      TEXT DEFAULT 'day',
        tag_filter  TEXT DEFAULT '',
        created_at  TEXT DEFAULT (datetime('now','localtime'))
    );
"""

# Tombstones: sin esto, "lo borré en la portátil" y "todavía no existe en la portátil" son
# indistinguibles, y un merge resucitaría lo borrado.
SCHEMA += """
    CREATE TABLE IF NOT EXISTS deletions (
        tabla      TEXT NOT NULL,
        uid        TEXT NOT NULL,
        deleted_at TEXT NOT NULL,
        PRIMARY KEY (tabla, uid)
    );
"""

# Migraciones declarativas para DBs viejas: (tabla, columna, DDL). Idempotente.
MIGRATIONS = [
    ("notes",            "color",            "ALTER TABLE notes ADD COLUMN color TEXT DEFAULT ''"),
    ("completions",      "status",           "ALTER TABLE completions ADD COLUMN status TEXT DEFAULT 'done'"),
    ("recurring_events", "end_date",         "ALTER TABLE recurring_events ADD COLUMN end_date TEXT DEFAULT ''"),
    ("recurring_events", "show_in_calendar", "ALTER TABLE recurring_events ADD COLUMN show_in_calendar INTEGER DEFAULT 1"),
    # Gráficos desglosados/agregados (jun 2026): campo de desglose, período y filtro por etiqueta
    ("charts",           "group_field",      "ALTER TABLE charts ADD COLUMN group_field TEXT DEFAULT ''"),
    ("charts",           "bucket",           "ALTER TABLE charts ADD COLUMN bucket TEXT DEFAULT 'day'"),
    ("charts",           "tag_filter",       "ALTER TABLE charts ADD COLUMN tag_filter TEXT DEFAULT ''"),
    # Visor de tareas (sep 2026): cuando se cerro la tarea
    ("todos",            "done_at",          "ALTER TABLE todos ADD COLUMN done_at TEXT DEFAULT ''"),
]

# Identidad para sincronizar (sep 2026). Generadas y no escritas a mano: 14 entradas idénticas
# serían ruido. `uid` sobrevive entre dispositivos (las PK autoincrementales colisionan);
# `updated_at` es el desempate de "última escritura gana".
MIGRATIONS += [(t, c, f"ALTER TABLE {t} ADD COLUMN {c} TEXT DEFAULT ''")
               for t in SYNCABLE for c in ("uid", "updated_at")]
MIGRATIONS.append(("settings", "updated_at",
                   "ALTER TABLE settings ADD COLUMN updated_at TEXT DEFAULT ''"))

# Índice PARCIAL: las filas viejas arrancan con uid = '' y un único normal explotaría con la
# segunda. Así el orden del backfill deja de importar.
# settings viaja en el sync pero no está en SYNCABLE: su `key` ya es una identidad estable
# entre dispositivos, así que no necesita uid, solo la marca para desempatar por clave.
# set_setting es un UPSERT, por eso hacen falta los dos triggers; y la tabla no tiene `id`.
TRIGGERS_SETTINGS = """
    CREATE TRIGGER IF NOT EXISTS settings_ins AFTER INSERT ON settings
    WHEN COALESCE(NEW.updated_at, '') = ''
    BEGIN
        UPDATE settings SET updated_at = strftime('%Y-%m-%d %H:%M:%f','now') WHERE key = NEW.key;
    END;
    CREATE TRIGGER IF NOT EXISTS settings_upd AFTER UPDATE ON settings
    WHEN NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE settings SET updated_at = strftime('%Y-%m-%d %H:%M:%f','now') WHERE key = NEW.key;
    END;
"""

UID_INDEX = "".join(
    f'CREATE UNIQUE INDEX IF NOT EXISTS idx_{t}_uid ON {t}(uid) WHERE uid != "";'
    for t in SYNCABLE
)

# Tres triggers por tabla evitan tocar los 33 puntos de escritura de database/*.py.
# ⚠️ El de UPDATE lleva `WHEN NEW.updated_at = OLD.updated_at`: si el UPDATE trae su propia
# marca es el merge del sync trayendo la versión remota, y pisarla con la hora local haría que
# la fila mienta sobre cuándo se modificó (en el viaje de vuelta, una edición vieja le ganaría
# a una nueva). Si el UPDATE no toca updated_at es la app normal y ahí sí hay que sellar.
# ⚠️ Las marcas van en UTC y con MILISEGUNDOS, al revés que el resto de la app (que usa
# localtime y segundos): son para que dos máquinas comparen entre sí, y nunca se muestran en
# pantalla. Si el usuario viaja a otro huso, una comparación en hora local decide mal quién
# escribió último. Y con resolución de segundos, dos ediciones del mismo segundo empatan y
# "la más reciente gana" no dispara. Las marcas viejas en segundos siguen comparando bien:
# '...:10' < '...:10.001' < '...:11'.
TRIGGERS = "".join(f"""
    CREATE TRIGGER IF NOT EXISTS {t}_uid AFTER INSERT ON {t}
    WHEN COALESCE(NEW.uid, '') = ''
    BEGIN
        UPDATE {t} SET uid = lower(hex(randomblob(16))),
                       updated_at = strftime('%Y-%m-%d %H:%M:%f','now') WHERE id = NEW.id;
    END;
    CREATE TRIGGER IF NOT EXISTS {t}_upd AFTER UPDATE ON {t}
    WHEN NEW.updated_at = OLD.updated_at
    BEGIN
        UPDATE {t} SET updated_at = strftime('%Y-%m-%d %H:%M:%f','now') WHERE id = NEW.id;
    END;
    CREATE TRIGGER IF NOT EXISTS {t}_del AFTER DELETE ON {t}
    BEGIN
        INSERT OR REPLACE INTO deletions (tabla, uid, deleted_at)
        VALUES ('{t}', OLD.uid, strftime('%Y-%m-%d %H:%M:%f','now'));
    END;
""" for t in SYNCABLE)


def init_db():
    """Crea/migra el esquema. Idempotente: corre en cada request (app.before_request).

    El ORDEN NO SE PUEDE CAMBIAR. Los triggers referencian uid/updated_at, que las migraciones
    agregan recién en el paso 2. Y SQLite no resuelve las columnas al crear un trigger: el
    CREATE TRIGGER saldría bien y después explotaría CADA INSERT con "no such column: uid".
    """
    with get_db() as conn:
        if conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION:
            return                                      # ya está al día
        conn.executescript(SCHEMA)                      # 1) tablas e índices
        cols = {}                                       # 2) columnas nuevas
        for table, col, ddl in MIGRATIONS:
            # Cacheado por tabla: son 22 migraciones sobre 8 tablas y esto corre en cada
            # request. Un PRAGMA table_info por entrada costaba ~4 ms por página.
            if table not in cols:
                cols[table] = _columns(conn, table)
            if col not in cols[table]:
                conn.execute(ddl)
                cols[table].add(col)
                if col == "uid":
                    # Una sola vez, al agregar la columna: de ahí en más los llena el trigger.
                    # `updated_at` queda vacío a propósito y NO se rellena con la hora de la
                    # migración: eso haría que el dispositivo que migró último "gane" filas que
                    # nadie tocó. Vacío significa "original, nunca modificada" y ordena antes
                    # que cualquier fecha, que es justo lo que tiene que pasar en el merge.
                    conn.execute(f"UPDATE {table} SET uid = lower(hex(randomblob(16)))"
                                 " WHERE COALESCE(uid, '') = ''")
        # 3) Los triggers se DROPEAN y recrean: `CREATE TRIGGER IF NOT EXISTS` no reemplaza
        # uno existente, así que una DB de una versión anterior se quedaría con el viejo.
        drops = "".join(f"DROP TRIGGER IF EXISTS {t}_{suf};"
                        for t in SYNCABLE for suf in ("uid", "upd", "del"))
        drops += "DROP TRIGGER IF EXISTS settings_ins; DROP TRIGGER IF EXISTS settings_upd;"
        conn.executescript(drops + UID_INDEX + TRIGGERS + TRIGGERS_SETTINGS)
        conn.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
