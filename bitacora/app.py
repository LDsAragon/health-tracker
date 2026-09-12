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
from bitacora.routes import (
    main, day, recurring, journal, update, todos, perfiles, sync, widget,
    # ANDAMIO: blueprints (import) — `hacer.ps1 nuevo ruta` inserta aca. No mover ni borrar.
)
# Los blueprints se importan y se listan a mano, sin descubrimiento automatico: PyInstaller
# resuelve imports estaticamente y con un `importlib` dinamico no entrarian al bundle.
BLUEPRINTS = (
    main, day, recurring, journal, update, todos, perfiles, sync, widget,
    # ANDAMIO: blueprints (registro) — idem.
)


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
                "perfiles": profiles.listar(), "perfil_activo": profiles.activo(),
                # Acá y no en cada ruta: lo necesitan base.html y widget.html, que son los dos
                # árboles de plantillas. Servirlo con la página evita que la primera vuelta del
                # poleo tenga que establecer la referencia.
                "token_datos": db.token_datos()}

    for module in BLUEPRINTS:
        app.register_blueprint(module.bp)

    return app


app = create_app()
# El arranque del modo navegador vive en main.py (la raíz), que es el único entry point.
