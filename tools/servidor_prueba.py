"""Levanta Bitácora contra una base TEMPORAL, con unos pocos datos de ejemplo.

Es el servidor que usan las auditorías de navegador (`tools/refresco_audit.mjs`) y el que
conviene usar a mano para probar algo sin riesgo.

⚠️ El punto de este archivo es el aislamiento. Un servidor de prueba apuntado al `APP_DIR` real
una vez le borró la base al usuario: `profiles.aplicar()` sin `HT_PERFILES` propio escribe donde
vive la bitácora de verdad. Acá las tres variables se fijan a un directorio temporal **antes** de
importar nada de la app, y además se verifica que la ruta final no caiga adentro del APP_DIR real.

Uso:  python tools/servidor_prueba.py [puerto] [--demo]
Imprime `URL: http://127.0.0.1:<puerto>` cuando está listo.

Con `--demo` siembra los datos inventados de `datos_demo.py`: mes y medio de notas especiales de
todos los tipos de campo, para poder MIRAR la pantalla de Estadísticas con algo adentro.
"""
import json
import os
import sys
import tempfile
from datetime import date

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _app_dir_real() -> str:
    """Dónde vive la bitácora de verdad, para no escribir nunca ahí."""
    if sys.platform == "win32":
        base = os.environ.get("LOCALAPPDATA", "")
        return os.path.join(base, "Bitacora") if base else ""
    return os.path.expanduser("~/.local/share/Bitacora")


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    puerto = int(args[0]) if args else 5199
    demo = "--demo" in sys.argv

    real = os.path.abspath(_app_dir_real()) if _app_dir_real() else None
    tmp = tempfile.mkdtemp(prefix="bitacora-prueba-")
    if real and os.path.abspath(tmp).startswith(real):
        print("ABORTA: el temporal caería dentro del APP_DIR real", file=sys.stderr)
        return 2

    # Antes de importar la app: conn.py lee HT_DB una sola vez, al importarse.
    os.environ["HT_PERFILES"] = tmp
    os.environ["HT_DB"] = os.path.join(tmp, "health.db")
    os.environ["LOCALAPPDATA"] = tmp
    os.environ["XDG_DATA_HOME"] = tmp
    sys.path.insert(0, RAIZ)

    import bitacora.database.conn as conn
    conn.DB_PATH = os.environ["HT_DB"]
    from bitacora import database as db

    if real and os.path.abspath(conn.DB_PATH).startswith(real):
        print("ABORTA: la base quedó apuntando al APP_DIR real", file=sys.stderr)
        return 2

    db.init_db()
    hoy = date.today().isoformat()
    db.add_note(hoy, "una nota de ejemplo")
    db.add_todo(hoy, "una tarea de ejemplo")
    db.add_recurring_event({"title": "Gimnasio", "color": "#22c55e", "recurrence": "daily",
                            "start_date": "2020-01-01", "end_date": ""})
    db.add_journal_category({
        "name": "Emociones", "color": "#6366f1", "show_in_calendar": 1,
        "fields_json": json.dumps([{"label": "Qué sentí", "type": "text", "placeholder": ""}]),
    })

    if demo:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from datos_demo import sembrar, resumen
        sembrar(db)
        print(resumen(), flush=True)

    print("DB:", conn.DB_PATH, flush=True)
    print(f"URL: http://127.0.0.1:{puerto}", flush=True)
    from bitacora.app import app
    # Jinja cachea las plantillas y su `auto_reload` va atado a `debug`, que acá queda en False.
    # Sin esto, editar una plantilla no se ve hasta reiniciar el servidor y uno termina
    # persiguiendo un bug que ya había arreglado.
    app.config["TEMPLATES_AUTO_RELOAD"] = True
    app.jinja_env.auto_reload = True
    app.run(host="127.0.0.1", port=puerto, debug=False, use_reloader=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
