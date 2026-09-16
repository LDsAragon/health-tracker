"""Las plantillas de categoría de nota especial — fuente única.

Son categorías ya armadas con los campos genéricos, para no arrancar de cero. Se usan en dos
lados y por eso viven acá y no en el JavaScript de la pantalla:

- los chips de **Empezá desde una plantilla** en `/journal`, que las aplican al formulario;
- y las tres que **vienen de fábrica** (`DE_FABRICA`), que una instalación nueva ya trae creadas.

⚠️ Las tres de fábrica llevan un **uid fijo**. Cada instalación las crea por su cuenta, así que
con un uid al azar dos máquinas generarían dos "Sueño" distintas y sincronizar dejaría las dos
—es exactamente lo que ya pasó con el grupo Cumpleaños (`schema.UID_CUMPLEANOS`)—. Con la
identidad fija el merge las reconoce como la misma fila.
"""

PLANTILLAS = [
    {"slug": "emociones", "nombre": "Emociones", "icono": "🎡", "color": "#ec4899",
     "uid": "00000000000000000000000000000010",
     "campos": [
         {"label": "Emoción", "type": "emotion-wheel", "ph": ""},
         {"label": "¿Qué la disparó?", "type": "text", "ph": "situación, pensamiento..."},
         {"label": "¿Cómo la manejé?", "type": "text", "ph": ""},
     ]},
    {"slug": "sueno", "nombre": "Sueño", "icono": "😴", "color": "#3b82f6",
     "uid": "00000000000000000000000000000011",
     "campos": [
         {"label": "Acostarse → Levantarse", "type": "rango", "ph": "", "chart": True},
         {"label": "Calidad", "type": "escala", "ph": ""},
         {"label": "Notas", "type": "text", "ph": "cómo dormí, despertares..."},
     ]},
    {"slug": "alimentacion", "nombre": "Alimentación", "icono": "🍎", "color": "#22c55e",
     "uid": "00000000000000000000000000000012",
     "campos": [
         {"label": "Momento", "type": "opciones", "ph": "Desayuno, Almuerzo, Merienda, Cena, Snack"},
         {"label": "¿Qué comí?", "type": "text", "ph": ""},
         {"label": "Saciedad", "type": "escala", "ph": ""},
         {"label": "Antojos", "type": "text", "ph": ""},
     ]},
    {"slug": "estudio", "nombre": "Estudio", "icono": "📚", "color": "#a855f7",
     "campos": [
         {"label": "Tiempo estudiado", "type": "duracion", "ph": "", "chart": True},
         {"label": "Qué estudié", "type": "text", "ph": "tema, materia..."},
         {"label": "Foco", "type": "escala", "ph": ""},
     ]},
    {"slug": "social", "nombre": "Social", "icono": "👥", "color": "#f97316",
     "campos": [
         {"label": "¿Con quién?", "type": "opciones", "ph": "Familia, Amigos, Pareja, Trabajo, Solo"},
         {"label": "Actividad", "type": "text", "ph": ""},
         {"label": "Tiempo compartido", "type": "duracion", "ph": ""},
         {"label": "¿Cómo me sentí?", "type": "escala", "ph": ""},
     ]},
    {"slug": "aficiones", "nombre": "Aficiones", "icono": "🎨", "color": "#6366f1",
     "campos": [
         {"label": "Afición", "type": "text", "ph": "qué hice"},
         {"label": "Tiempo dedicado", "type": "duracion", "ph": "", "chart": True},
         {"label": "Disfrute", "type": "escala", "ph": ""},
     ]},
    {"slug": "trabajo", "nombre": "Trabajo", "icono": "💼", "color": "#14b8a6",
     "campos": [
         {"label": "Proyecto", "type": "opciones", "ph": "ClienteA, ClienteB, Proyecto propio"},
         {"label": "Franja", "type": "rango", "ph": ""},
         {"label": "Horas", "type": "duracion", "ph": "", "chart": True},
         {"label": "Notas", "type": "text", "ph": "en qué trabajé..."},
     ]},
]

# Las que trae la app ya creadas: registrar lo que comés, cómo dormís y cómo te sentís es con lo
# que arranca cualquiera, y armarlas a mano era el primer trabajo antes de poder anotar nada.
# Son las únicas con `uid` fijo, justamente porque son las que existen en todas las instalaciones.
DE_FABRICA = ("emociones", "sueno", "alimentacion")


def por_slug(slug):
    return next((p for p in PLANTILLAS if p["slug"] == slug), None)


def campos_json(plantilla) -> list:
    """Los campos como los guarda la DB: `ph` es el `placeholder` de la definición."""
    out = []
    for c in plantilla["campos"]:
        campo = {"label": c["label"], "type": c["type"], "placeholder": c.get("ph", "")}
        if c.get("chart"):
            campo["chart"] = True
        out.append(campo)
    return out
