"""Health Tracker como app de escritorio: ventana nativa (pywebview / Edge WebView2).

Modo ventana: la DB vive en %LOCALAPPDATA%\\HealthTracker\\health.db (via env HT_DB),
así el .exe puede vivir en cualquier carpeta sin problemas de permisos de escritura.
El modo navegador (start.bat / python app.py) sigue funcionando igual que siempre,
con su health.db al lado del código.

Primer arranque: si no hay DB en appdata pero hay una health.db al lado del
exe/script, se copia (snapshot consistente via API de backup de SQLite, incluye WAL).
"""
import os
import sys
import sqlite3
import traceback
from pathlib import Path

APP_DIR = Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "HealthTracker"
DB_FILE = APP_DIR / "health.db"

WINDOW_TITLE = "Health Tracker"
WINDOW_SIZE = (1280, 860)
# Mínimo chico a propósito: la app es responsive (<600px = modo agenda) y así
# la ventana sirve como "columnita" al costado de la pantalla.
MIN_SIZE = (420, 480)


def _base_dir():
    """Carpeta del .exe (congelada) o del script (desarrollo)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(__file__).parent


def _copy_db(src_path, dest_path):
    """Copia consistente src → dest con la API de backup de SQLite (incluye WAL)."""
    src = sqlite3.connect(str(src_path))
    try:
        dst = sqlite3.connect(str(dest_path))
        try:
            src.backup(dst)
        finally:
            dst.close()
    finally:
        src.close()


def _migrate_first_run():
    """Si no hay DB en appdata pero hay una health.db al lado, traerla.

    Importa `database` recién acá: HT_DB ya tiene que estar seteado en el env
    (database.conn lee HT_DB al importarse).
    """
    if DB_FILE.exists():
        return
    old = _base_dir() / "health.db"
    if not old.exists():
        return  # arranque limpio: init_db crea la DB nueva en appdata
    import database as db
    if db.is_valid_db(str(old)):
        _copy_db(old, DB_FILE)


def main():
    APP_DIR.mkdir(parents=True, exist_ok=True)
    os.environ["HT_DB"] = str(DB_FILE)
    _migrate_first_run()

    from app import create_app
    flask_app = create_app()

    import webview
    webview.create_window(
        WINDOW_TITLE,
        flask_app,
        width=WINDOW_SIZE[0],
        height=WINDOW_SIZE[1],
        min_size=MIN_SIZE,
        text_select=True,   # permitir seleccionar/copiar texto (notas, etc.)
    )
    # private_mode=False + storage_path: persistir localStorage (zoom, tamaño de
    # celdas) entre sesiones — en modo privado pywebview lo borra al cerrar.
    webview.start(private_mode=False, storage_path=str(APP_DIR / "webview"))


if __name__ == "__main__":
    try:
        main()
    except Exception:
        # Congelada con --windowed no hay consola: dejar rastro y avisar.
        APP_DIR.mkdir(parents=True, exist_ok=True)
        log = APP_DIR / "error.log"
        log.write_text(traceback.format_exc(), encoding="utf-8")
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(
                None,
                f"Health Tracker no pudo arrancar.\nDetalle en: {log}",
                WINDOW_TITLE, 0x10)
        except Exception:
            pass
        raise
