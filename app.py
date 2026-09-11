import os
import sys
from datetime import date

from flask import Flask, g
import database as db
import filters
import services
from fieldtypes import FIELD_TYPES
from appconfig import PET_ART
from helpers import _week_start
# Re-export para tests que hacen `from app import dur_fmt_filter, ...`
from filters import humantime_filter, fechacorta_filter, dur_fmt_filter, rango_fmt_filter
from routes import main, day, recurring, journal, update, todos


def _overdue_count(settings) -> int:
    """Contador del badge del navbar. Con los avisos apagados no se paga la query."""
    if settings.get("todo_alert") == "off":
        return 0
    today = date.today()
    cutoff = services.overdue_cutoff(today, settings.get("todo_overdue_from", "week"), _week_start)
    return db.count_overdue_todos(cutoff.isoformat())


def create_app():
    """App factory: crea y configura la app (filtros, handlers, blueprints)."""
    # Congelada con PyInstaller, templates/static viven bajo sys._MEIPASS (--add-data)
    frozen_base = getattr(sys, "_MEIPASS", None)
    if frozen_base:
        app = Flask(__name__,
                    template_folder=os.path.join(frozen_base, "templates"),
                    static_folder=os.path.join(frozen_base, "static"))
    else:
        app = Flask(__name__)
    filters.register(app)

    @app.before_request
    def _setup():
        db.init_db()
        g.settings = db.get_all_settings()

    @app.context_processor
    def _inject():
        """Expone ajustes y el catálogo de tipos de campo a todas las plantillas."""
        settings = db.get_all_settings()
        return {"settings": settings, "field_types": FIELD_TYPES, "pet_art": PET_ART,
                "overdue_count": _overdue_count(settings)}

    for module in (main, day, recurring, journal, update, todos):
        app.register_blueprint(module.bp)

    return app


app = create_app()


if __name__ == "__main__":
    import webbrowser, threading
    db.init_db()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False, port=5000)
