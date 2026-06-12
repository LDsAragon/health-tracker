"""Screenshot de una página de la app en WebKitGTK real, para verificar bugs
de rendering/locale que no se reproducen en Windows/WebView2.

Uso (en Linux/WSL): venv-linux/bin/python tools/snap_settings.py salida.png [/ruta]
(ruta default: /ajustes). Forzar tema GTK claro: GTK_THEME=Adwaita:light ...
Usa una DB temporal; no toca datos reales.
"""
import os
import sys
import tempfile
import threading
from pathlib import Path

salida = sys.argv[1] if len(sys.argv) > 1 else "/tmp/ajustes.png"
ruta = sys.argv[2] if len(sys.argv) > 2 else "/ajustes"
seed = len(sys.argv) > 3 and sys.argv[3] == "seed"
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

application = create_app()

if seed:
    # Datos de muestra: categorías suficientes para que aparezca el filtro,
    # el form de nota especial abierto, y datos graficables del último mes
    # (para inspeccionar /estadisticas con todos los tipos de campo).
    import json
    import random
    from datetime import date as _date, timedelta as _td
    import database as dbm
    dbm.init_db()
    random.seed(42)

    def cat(n, c, fields):
        dbm.add_journal_category({"name": n, "color": c, "show_in_calendar": 1,
                                  "fields_json": json.dumps(fields)})
        return dbm.get_journal_categories()[-1]["id"]

    cid_suenio = cat("Sueño", "#6366f1", [{"label": "Dormido", "type": "rango", "chart": True}])
    cid_animo = cat("Ánimo", "#ec4899", [{"label": "Nivel", "type": "escala", "chart": True}])
    cid_ejer = cat("Ejercicio", "#22c55e", [
        {"label": "Tipo", "type": "opciones", "placeholder": "Correr, Pesas, Yoga"},
        {"label": "Tiempo", "type": "duracion", "chart": True}])
    cid_medic = cat("Medicación", "#ef4444", [{"label": "Tomada", "type": "sino", "chart": True}])
    for n, c in [("Comidas", "#f97316"), ("Trabajo", "#a855f7"),
                 ("Lectura", "#3b82f6"), ("Meditación", "#eab308")]:
        cat(n, c, [{"label": "Detalle", "type": "text"}])

    hoy = _date.today()
    for i in range(30):
        d = (hoy - _td(days=i)).isoformat()
        def e(cid, vals):
            dbm.add_journal_entry({"category_id": cid, "entry_date": d,
                                   "values_json": json.dumps(vals), "tags": ""})
        e(cid_suenio, {"Dormido": f"23:{random.randint(0,5)*10:02d}-0{random.randint(6,8)}:30"})
        e(cid_animo, {"Nivel": str(random.randint(2, 9))})
        if i % 2 == 0:
            e(cid_ejer, {"Tipo": random.choice(["Correr", "Pesas", "Yoga"]),
                         "Tiempo": str(random.choice([30, 45, 60, 90]))})
        e(cid_medic, {"Tomada": "1" if random.random() < 0.8 else ""})
    # Un gráfico personalizado: ejercicio por tipo, semanal
    dbm.add_chart(cid_ejer, "Tiempo", "", 90, "Tipo", "week", "")
    dbm.set_setting("journal_form_default", "open")
    dbm.set_setting("show_stats", "show")

srv = make_server("127.0.0.1", 0, application)
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
view.load_uri(f"http://127.0.0.1:{srv.server_port}{ruta}")
GLib.timeout_add_seconds(30, Gtk.main_quit)  # red de seguridad
Gtk.main()
