"""Datos de configuración: temas y esquema de ajustes (fuente única)."""
import re

# Temas: slug + nombre + 4 colores para el swatch (las paletas reales están en base.css → [data-theme]).
THEMES = [
    {"slug": "indigo",     "name": "Índigo",     "dark": True,  "bg": "#0f1117", "surface": "#1a1d27", "text": "#e2e8f0", "accent": "#6366f1"},
    {"slug": "bosque",     "name": "Bosque",     "dark": True,  "bg": "#14211a", "surface": "#1b2a1b", "text": "#cfe8c8", "accent": "#6fbf73"},
    {"slug": "oceano",     "name": "Océano",     "dark": True,  "bg": "#0b1a2c", "surface": "#112334", "text": "#cfe9ff", "accent": "#4facfe"},
    {"slug": "ciruela",    "name": "Ciruela",    "dark": True,  "bg": "#1e1420", "surface": "#2b1b2e", "text": "#f5d8ec", "accent": "#e879b9"},
    {"slug": "claude",     "name": "Claude",     "dark": True,  "bg": "#1f1e1c", "surface": "#262624", "text": "#f5f4f0", "accent": "#c6613f"},
    {"slug": "cyberpunk",  "name": "Cyberpunk",  "dark": True,  "bg": "#0a0a0f", "surface": "#12101a", "text": "#0ff0fc", "accent": "#e040fb"},
    {"slug": "retrowave",  "name": "Retrowave",  "dark": True,  "bg": "#1a1a2e", "surface": "#16213e", "text": "#f0e9ff", "accent": "#e94560"},
    {"slug": "lavanda",    "name": "Lavanda",    "dark": False, "bg": "#f3eef8", "surface": "#faf7ff", "text": "#3d3551", "accent": "#9b6dcc"},
]
THEME_SLUGS = {t["slug"] for t in THEMES}

# Paleta de las notas, rutinas y categorias. Estaba repetida como literal en SEIS
# plantillas; tambien es el `choices` del ajuste `nota_color`.
NOTE_COLORS = ("#6366f1", "#22c55e", "#3b82f6", "#f97316", "#ef4444",
               "#a855f7", "#ec4899", "#eab308", "#14b8a6")

# Medidas con las que puede abrir la ventana de escritorio. Son las comunes; el control deja
# escribir cualquier otra, y "maximizada" abre ocupando el monitor entero.
VENTANA_PRESETS = ("1280x860", "1366x768", "1600x900", "1920x1080")
VENTANA_MIN = (640, 480)
VENTANA_MAX = (10000, 10000)


def es_resolucion(valor) -> bool:
    """`<ancho>x<alto>` dentro de límites razonables.

    Es lo que hace válida una medida escrita a mano sin abrir la puerta a cualquier cosa: el
    resto de los ajustes se valida contra una whitelist y este no puede tenerla.
    """
    m = re.fullmatch(r"(\d{3,5})x(\d{3,5})", (valor or "").strip())
    if not m:
        return False
    ancho, alto = int(m.group(1)), int(m.group(2))
    return (VENTANA_MIN[0] <= ancho <= VENTANA_MAX[0]
            and VENTANA_MIN[1] <= alto <= VENTANA_MAX[1])


def valor_valido(key, valor) -> bool:
    """¿Ese valor es aceptable para ese ajuste?

    Fuente única de la validación: la usan el guardado (los dos caminos) y la lectura, que
    clampea al default lo que ya no sirve. Casi todos se validan con su whitelist; el que
    además admite un valor libre trae su propio validador en el esquema.
    """
    spec = SETTINGS.get(key)
    if spec is None or valor is None:
        return False
    return valor in spec["choices"] or bool(spec.get("valida") and spec["valida"](valor))


# Esquema de ajustes: clave → default + valores válidos. Agregar un ajuste = una entrada acá.
SETTINGS = {
    "date_format": {"default": "dmy",    "choices": ("dmy", "mdy", "ymd")},
    "time_format": {"default": "24h",    "choices": ("24h", "12h")},
    "theme":       {"default": "indigo", "choices": THEME_SLUGS},
    "week_start":  {"default": "mon",    "choices": ("mon", "sun")},
    "start_view":  {"default": "week",   "choices": ("month", "week", "today")},
    "show_stats":  {"default": "hide",   "choices": ("show", "hide")},
    "show_export": {"default": "hide",   "choices": ("show", "hide")},
    "note_form_default":    {"default": "collapsed", "choices": ("open", "collapsed")},
    "journal_form_default": {"default": "collapsed", "choices": ("open", "collapsed")},
    "pet":                  {"default": "cat",       "choices": ("cat", "dog", "none")},
    "show_todos":        {"default": "show",  "choices": ("show", "hide")},
    "todo_alert":        {"default": "modal", "choices": ("off", "badge", "modal")},
    "todo_overdue_from": {"default": "week",  "choices": ("week", "day")},
    "todo_notify":       {"default": "off",   "choices": ("on", "off")},
    "widget_autostart":  {"default": "on",    "choices": ("on", "off")},
    "cerrar_a_bandeja":  {"default": "on",    "choices": ("on", "off")},
    "widget_rutinas": {"default": "show", "choices": ("show", "hide")},
    # Color con el que sale una nota rapida cuando NO elegis ninguno. "" = sin color
    # (como siempre); "aleatorio" = uno sorteado de NOTE_COLORS; o un color fijo.
    "nota_color": {"default": "", "choices": ("", "aleatorio") + NOTE_COLORS},
    # Con qué medida abre la VENTANA de escritorio. "maximizada" = el monitor entero; si no,
    # "<ancho>x<alto>", de la lista o escrita a mano (de ahí el validador propio). En el modo
    # navegador no aplica: ahí el tamaño lo pone el navegador.
    "window_size": {"default": "1280x860", "choices": ("maximizada",) + VENTANA_PRESETS,
                    "valida": es_resolucion},
    # ANDAMIO: ajustes — `hacer.ps1 nuevo ajuste` inserta aca. No mover ni borrar.
}

# Clave de la tabla settings que NO va en SETTINGS: guarda una fecha ISO libre (el lunes de
# la última semana en que se avisó de tareas atrasadas) y get_all_settings solo clampea las
# claves que están en el esquema.
LAST_WEEK_SEEN_KEY = "todos_last_week_seen"
DEFAULT_SETTINGS = {k: v["default"] for k, v in SETTINGS.items()}

# Aun activada, la mascotita sale solo a veces: si apareciera en cada tilde se
# vuelve invasiva y deja de causar gracia a los dos dias.
PET_CHANCE = 0.10

PET_ART = {
    "cat": "  /\\_/\\ \n ( ^.^ )\n  > ♥ < ",
    "dog": "  ∩   ∩\n ( ^ᴥ^ )\n  >  ω <",
}


# Colores de las emociones, por rueda. Estaban como literales dentro de `day.html`, y
# Estadísticas los necesita para el mismo dato: un color por emoción base tiene que ser el mismo
# en las dos pantallas o serían dos cosas distintas con el mismo nombre.
#
# ⚠️ Las dos ruedas van SEPARADAS a propósito: Willcox y Ekman son taxonomías distintas, y
# mapear "Ira" con "Enojado" sería inventar una equivalencia que nadie definió.
EMOTION_COLORS = {
    "willcox": {"Enojado": "#e8643c", "Asustado": "#8e7cc3", "Alegre": "#e79ab0",
                "Poderoso": "#e8b93f", "Apacible": "#6cab6c", "Triste": "#5b8fc7"},
    "ekman":   {"Ira": "#e2403b", "Miedo": "#7c5cbf", "Tristeza": "#3b6fb5",
                "Asco": "#4f9d69", "Disfrute": "#e6b53c"},
}
EMOTION_FALLBACK = "#8892a4"
