"""Conexión a SQLite. DB_PATH desde env HT_DB (default health.db).
get_db lee DB_PATH dinámicamente → los tests parchean database.conn.DB_PATH."""
import os
import sqlite3

DB_PATH = os.environ.get("HT_DB", "health.db")


def db_path():
    return DB_PATH


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def _columns(conn, table):
    return {r["name"] for r in conn.execute(f"PRAGMA table_info({table})").fetchall()}
