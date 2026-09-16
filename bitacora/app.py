import os
import sys
from datetime import date

from flask import Flask, g
from bitacora import database as db
from bitacora import filters
from bitacora import services
from bitacora import profiles
from bitacora.fieldtypes import FIELD_TYPES
from bitacora.despedidas import DESPEDIDAS
from bitacora.appconfig import PET_ART, NOTE_COLORS, EMOTION_COLORS, EMOTION_FALLBACK
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
                "note_colors": NOTE_COLORS,
                # Cómo se muere una tarea al borrarla. Van a todas las pantallas, como el resto
                # del catálogo: el día que otra sume un borrado de tareas tiene que andar sola,
                # que es lo contrario del "a medio marcar" que ya costó caro con el refresco.
                "despedidas": DESPEDIDAS,
                # Un color por emoción, igual en el día y en Estadísticas: estaban
                # copiados como literales dentro de `day.html`.
                "emotion_colors": EMOTION_COLORS,
                "emotion_fallback": EMOTION_FALLBACK,
                # El color que van a tener las notas nuevas, para dejarlo marcado en los
                # formularios de alta. Con `nota_color=aleatorio` cambia en cada página.
                "color_sugerido": services.color_sugerido(settings.get("nota_color", "")),
                # Acá y no en cada ruta: lo necesitan base.html y widget.html, que son los dos
                # árboles de plantillas. Servirlo con la página evita que la primera vuelta del
                # poleo tenga que establecer la referencia.
                "token_datos": db.token_datos(),
                # Cómo dejaste acomodada cada pantalla. Van TODAS las claves y no solo las de la
                # vista actual: son un puñado de filas (el registro de `appconfig.VISTAS` acota
                # cuáles pueden existir) y así el JS las lee sin saber en qué vista está, que es
                # lo que permite aplicar el zoom en el <head> sin un salto.
                "vista_prefs": db.get_prefs(),
                # Adónde manda una emoción anotada desde el menú del clic derecho. Va acá
                # porque el menú vive en todas las pantallas; es None si no hay ninguna
                # categoría con rueda y entonces el atajo no se ofrece.
                "emocion_destino": db.categoria_con_rueda()}

    for module in BLUEPRINTS:
        app.register_blueprint(module.bp)

    return app


app = create_app()
# El arranque del modo navegador vive en main.py (la raíz), que es el único entry point.
