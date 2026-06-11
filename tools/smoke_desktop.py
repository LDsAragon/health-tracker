"""Smoke test headless de desktop.py: migración de primer arranque + app servida.

Usa un LOCALAPPDATA temporal para no tocar el real. No abre la ventana.
Correr: venv/Scripts/python tools/smoke_desktop.py
"""
import os
import sys
import tempfile
from pathlib import Path

tmp = Path(tempfile.mkdtemp(prefix="ht-smoke-"))
os.environ["LOCALAPPDATA"] = str(tmp)

root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

import desktop

assert str(desktop.APP_DIR).startswith(str(tmp)), desktop.APP_DIR

desktop.APP_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HT_DB"] = str(desktop.DB_FILE)
desktop._migrate_first_run()

real_db = root / "health.db"
if real_db.exists():
    assert desktop.DB_FILE.exists(), "la migración no copió la DB local a appdata"
    print(f"OK migración: {real_db.stat().st_size}b -> {desktop.DB_FILE.stat().st_size}b")
else:
    print("(no hay health.db local; arranque limpio)")

from app import create_app
app = create_app()
client = app.test_client()

r = client.get("/", follow_redirects=True)
assert r.status_code == 200, r.status_code
import database as db
assert db.db_path() == str(desktop.DB_FILE), db.db_path()
print(f"OK app sirve con DB en {db.db_path()}")

import webview  # noqa: F401  (solo validar que importa)
print("OK pywebview importa")
print("SMOKE OK")
