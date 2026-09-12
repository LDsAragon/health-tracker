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
os.environ["HT_PERFILES"] = str(desktop.APP_DIR)
os.environ["HT_DB"] = str(desktop.DB_FILE)
desktop._migrate_first_run()

real_db = root / "health.db"
if real_db.exists():
    assert desktop.DB_FILE.exists(), "la migración no copió la DB local a appdata"
    print(f"OK migración de primer arranque: {real_db.stat().st_size}b -> {desktop.DB_FILE.stat().st_size}b")
else:
    print("(no hay health.db local; arranque limpio)")

# Migración al layout de perfiles: el camino que corre en la máquina de cada usuario
import database as db
import profiles

antes = db.table_counts(str(desktop.DB_FILE)) if desktop.DB_FILE.exists() else {}
desktop._migrate_a_perfiles()
profiles.aplicar()
activo = profiles.activo()
assert activo, "no quedó ningún perfil activo"
assert db.db_path() == profiles.db_de(activo["slug"]), db.db_path()
assert not desktop.DB_FILE.exists(), "quedó la health.db vieja en la raíz de APP_DIR"
if antes:
    assert db.table_counts(db.db_path()) == antes, "la migración perdió filas"
assert (desktop.APP_DIR / "LEEME-perfiles.txt").exists(), "falta el LEEME del downgrade"
desktop._migrate_a_perfiles()   # idempotente
assert len(profiles.listar()) == 1, profiles.listar()
print(f"OK migración a perfiles: {activo['nombre']} ({len(antes)} tablas intactas)")

# Backup automático: en la carpeta DEL PERFIL, no en APP_DIR
backups = Path(db.db_path()).parent / "backups"
backups.mkdir(parents=True, exist_ok=True)
for i in range(desktop.AUTO_BACKUPS + 3):
    (backups / f"health-auto-2000-01-{i+1:02d}.db").touch()
desktop._auto_backup()
from datetime import date
hoy = backups / f"health-auto-{date.today().isoformat()}.db"
assert hoy.exists(), "no creó el backup de hoy"
restantes = sorted(backups.glob("health-auto-*.db"))
assert len(restantes) == desktop.AUTO_BACKUPS, restantes
desktop._auto_backup()   # segunda corrida el mismo día: no duplica
assert len(sorted(backups.glob("health-auto-*.db"))) == len(restantes)
print(f"OK auto-backup del perfil: {hoy.name}, rotación a {desktop.AUTO_BACKUPS}")

from app import create_app
app = create_app()
client = app.test_client()

r = client.get("/", follow_redirects=True)
assert r.status_code == 200, r.status_code
assert db.db_path() == profiles.db_de(activo["slug"]), db.db_path()
print(f"OK app sirve desde el perfil: {db.db_path()}")

import webview  # noqa: F401  (solo validar que importa)
print("OK pywebview importa")
print("SMOKE OK")
