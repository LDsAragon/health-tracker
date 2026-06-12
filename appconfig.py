"""Datos de configuración: temas y esquema de ajustes (fuente única)."""

# Temas: slug + nombre + 4 colores para el swatch (las paletas reales están en style.css → [data-theme]).
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

# Esquema de ajustes: clave → default + valores válidos. Agregar un ajuste = una entrada acá.
SETTINGS = {
    "date_format": {"default": "dmy",    "choices": ("dmy", "mdy", "ymd")},
    "time_format": {"default": "24h",    "choices": ("24h", "12h")},
    "theme":       {"default": "indigo", "choices": THEME_SLUGS},
    "week_start":  {"default": "mon",    "choices": ("mon", "sun")},
    "start_view":  {"default": "month",  "choices": ("month", "week", "today")},
    "show_stats":  {"default": "hide",   "choices": ("show", "hide")},
    "show_export": {"default": "hide",   "choices": ("show", "hide")},
    "note_form_default":    {"default": "open",      "choices": ("open", "collapsed")},
    "journal_form_default": {"default": "collapsed", "choices": ("open", "collapsed")},
}
DEFAULT_SETTINGS = {k: v["default"] for k, v in SETTINGS.items()}
