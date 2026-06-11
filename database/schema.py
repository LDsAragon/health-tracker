"""Esquema y migraciones declarativas."""
from .conn import get_db, _columns

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
]


def init_db():
    with get_db() as conn:
        conn.executescript(SCHEMA)
        for table, col, ddl in MIGRATIONS:
            if col not in _columns(conn, table):
                conn.execute(ddl)
