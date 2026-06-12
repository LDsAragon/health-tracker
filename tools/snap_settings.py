"""Screenshot de /ajustes en WebKitGTK real, para verificar bugs de rendering
de controles nativos (selects) que no se reproducen en Windows/WebView2.

Uso (en Linux/WSL): venv-linux/bin/python tools/snap_settings.py salida.png
Forzar tema GTK claro (caso usuario afectado): GTK_THEME=Adwaita:light ...
Usa una DB temporal; no toca datos reales.
"""
import os
import sys
import tempfile
import threading
from pathlib import Path

salida = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ajustes.png"
os.environ["HT_DB"] = str(Path(tempfile.mkdtemp(prefix="bita-snap-")) / "health.db")

root = Path(__file__).resolve().parent.parent
os.chdir(root)
sys.path.insert(0, str(root))

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("WebKit2", "4.1")
from gi.repository import GLib, Gtk, WebKit2

from app import create_app
from werkzeug.serving import make_server

srv = make_server("127.0.0.1", 0, create_app())
threading.Thread(target=srv.serve_forever, daemon=True).start()

win = Gtk.OffscreenWindow()
view = WebKit2.WebView()
view.set_size_request(1100, 900)
win.add(view)
win.show_all()


def on_load(view, event):
    if event == WebKit2.LoadEvent.FINISHED:
        GLib.timeout_add(1000, lambda: view.get_snapshot(
            WebKit2.SnapshotRegion.VISIBLE,
            WebKit2.SnapshotOptions.NONE, None, on_snap) or False)


def on_snap(view, res):
    view.get_snapshot_finish(res).write_to_png(salida)
    print("OK:", salida, flush=True)
    Gtk.main_quit()


view.connect("load-changed", on_load)
view.load_uri(f"http://127.0.0.1:{srv.server_port}/ajustes")
GLib.timeout_add_seconds(30, Gtk.main_quit)  # red de seguridad
Gtk.main()
