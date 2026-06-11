"""Ajustes clave/valor (esquema en appconfig.SETTINGS)."""
from appconfig import DEFAULT_SETTINGS, SETTINGS
from .conn import get_db


def get_setting(key: str, default: str = "") -> str:
    with get_db() as conn:
        row = conn.execute("SELECT value FROM settings WHERE key = ?", (key,)).fetchone()
    if row is not None:
        return row["value"]
    return DEFAULT_SETTINGS.get(key, default)


def set_setting(key: str, value: str):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO settings (key, value) VALUES (?,?)"
            " ON CONFLICT(key) DO UPDATE SET value = excluded.value",
            (key, value),
        )


def get_all_settings() -> dict:
    s = dict(DEFAULT_SETTINGS)
    with get_db() as conn:
        for r in conn.execute("SELECT key, value FROM settings").fetchall():
            s[r["key"]] = r["value"]
    # Clamp: un valor guardado que ya no es válido (ej. tema removido) cae al default.
    for key, spec in SETTINGS.items():
        if s.get(key) not in spec["choices"]:
            s[key] = spec["default"]
    return s
