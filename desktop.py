"""Bitácora (ex Health Tracker) como app de escritorio: ventana nativa (pywebview / Edge WebView2).

Modo ventana: la DB vive en %LOCALAPPDATA%\\Bitacora\\health.db (via env HT_DB),
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

_LOCALAPPDATA = Path(os.environ.get("LOCALAPPDATA", str(Path.home())))
APP_DIR = _LOCALAPPDATA / "Bitacora"
_OLD_APP_DIR = _LOCALAPPDATA / "HealthTracker"   # nombre previo al rename (jun 2026)
DB_FILE = APP_DIR / "health.db"

WINDOW_TITLE = "Bitácora"
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


def _migrate_from_old_appdata():
    """Migración del rename (jun 2026): la carpeta de appdata era HealthTracker.

    Intenta renombrar la carpeta entera; si algo la tiene lockeada (WebView2,
    antivirus), copia solo la DB — el storage del webview se recrea solo.
    """
    if DB_FILE.exists():
        return
    old_db = _OLD_APP_DIR / "health.db"
    if not old_db.exists():
        return
    if not APP_DIR.exists():
        try:
            os.rename(_OLD_APP_DIR, APP_DIR)
            return
        except OSError:
            pass
    APP_DIR.mkdir(parents=True, exist_ok=True)
    _copy_db(old_db, DB_FILE)


def _unblock_dlls():
    """Quita el "Mark of the Web" de las DLLs del bundle.

    Si la app viajó en un zip (OneDrive, mail, descarga), Windows marca los
    archivos extraídos y .NET se niega a cargar Python.Runtime.dll con un
    "Failed to resolve Python.Runtime.Loader.Initialize". Borrar el stream
    Zone.Identifier antes de importar webview lo cura.
    """
    if not getattr(sys, "frozen", False):
        return
    internal = Path(sys.executable).parent / "_internal"
    for p in internal.rglob("*.dll"):
        try:
            os.remove(f"{p}:Zone.Identifier")
        except OSError:
            pass   # no estaba marcada (lo normal)


def main():
    _unblock_dlls()
    _migrate_from_old_appdata()
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
        tb = traceback.format_exc()
        log.write_text(tb, encoding="utf-8")
        msg = f"Bitácora no pudo arrancar.\nDetalle en: {log}"
        if "Python.Runtime" in tb:
            msg += ("\n\nPosibles causas:\n"
                    "• Archivos bloqueados por venir de internet: clic derecho sobre el .zip\n"
                    "  → Propiedades → Desbloquear (antes de extraer), o reintentá: la app\n"
                    "  intenta desbloquearse sola en cada arranque.\n"
                    "• Falta .NET Framework 4.7.2+ (Windows Update lo trae).\n"
                    "• El antivirus puso una DLL en cuarentena.")
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(None, msg, WINDOW_TITLE, 0x10)
        except Exception:
            pass
        raise
