import os
import sys
from datetime import date

from flask import Flask, g
from bitacora import database as db
from bitacora import filters
from bitacora import services
from bitacora import profiles
from bitacora.fieldtypes import FIELD_TYPES
from bitacora.appconfig import PET_ART
from bitacora.helpers import _week_start
# Re-export para tests que hacen `from app import dur_fmt_filter, ...`
from bitacora.filters import humantime_filter, fechacorta_filter, dur_fmt_filter, rango_fmt_filter
from bitacora.routes import main, day, recurring, journal, update, todos, perfiles, sync, widget


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
                "overdue_count": _overdue_count(settings),
                "perfiles": profiles.listar(), "perfil_activo": profiles.activo()}

    for module in (main, day, recurring, journal, update, todos, perfiles, sync, widget):
        app.register_blueprint(module.bp)

    return app


app = create_app()
# El arranque del modo navegador vive en main.py (la raíz), que es el único entry point.
