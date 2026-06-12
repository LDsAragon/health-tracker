"""Smoke test del flujo de descarga en Linux: ventana GTK real + /backup.

Verifica que ALLOW_DOWNLOADS esté funcionando: navega a /backup y espera
que el health-backup-<fecha>.db aparezca en la carpeta de descargas XDG.
Usa XDG_DATA_HOME temporal para no tocar los datos reales. Necesita display
(WSLg o escritorio). Correr: venv-linux/bin/python tools/smoke_download_linux.py
"""
import os
import sys
import tempfile
import time
from pathlib import Path

tmp = Path(tempfile.mkdtemp(prefix="bita-dl-"))
os.environ["XDG_DATA_HOME"] = str(tmp / "data")

# Carpeta de descargas controlada (g_get_user_special_dir lee user-dirs.dirs)
dl_dir = tmp / "descargas"
dl_dir.mkdir(parents=True)
cfg = tmp / "config"
cfg.mkdir()
(cfg / "user-dirs.dirs").write_text(f'XDG_DOWNLOAD_DIR="{dl_dir}"\n')
os.environ["XDG_CONFIG_HOME"] = str(cfg)

root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

import desktop

assert str(desktop.APP_DIR).startswith(str(tmp)), desktop.APP_DIR
desktop.APP_DIR.mkdir(parents=True, exist_ok=True)
os.environ["HT_DB"] = str(desktop.DB_FILE)

from app import create_app

flask_app = create_app()

import webview

webview.settings["ALLOW_DOWNLOADS"] = True

# La descarga real abre un diálogo nativo "Guardar como" (igual que en Windows);
# acá lo parcheamos para que el test corra solo, sin clics.
import webview.platforms.gtk as gtk_platform


def _auto_guardar(self, dialog_type, directory, allow_multiple, save_filename, file_types):
    return (str(dl_dir / (save_filename or "descarga.bin")),)


gtk_platform.BrowserView.create_file_dialog = _auto_guardar

window = webview.create_window("smoke descarga", flask_app)
resultado = {"ok": False}


def driver():
    try:
        # Ojo: get_current_url() bloquea hasta el evento loaded; esperarlo
        # explícitamente con timeout para que el smoke no pueda colgarse.
        print("driver: esperando loaded...", flush=True)
        if not window.events.loaded.wait(30):
            print("DOWNLOAD_FAIL: la ventana nunca terminó de cargar", flush=True)
            return
        url = window.get_current_url()
        print("driver: cargó", url, flush=True)
        assert url and url.startswith("http"), url
        base = url.split("/", 3)
        window.load_url(f"{base[0]}//{base[2]}/backup")
        print("driver: navegando a /backup", flush=True)

        deadline = time.time() + 30
        while time.time() < deadline:
            if list(dl_dir.glob("health-backup-*.db")):
                print("DOWNLOAD_OK:", [p.name for p in dl_dir.glob("*")], flush=True)
                resultado["ok"] = True
                return
            time.sleep(0.5)
        print("DOWNLOAD_FAIL: no apareció el archivo en", dl_dir, flush=True)
    finally:
        window.destroy()


webview.start(driver, private_mode=True)
sys.exit(0 if resultado["ok"] else 1)
