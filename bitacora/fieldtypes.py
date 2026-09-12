"""Tipos de campo de las notas especiales — fuente única (slug + etiqueta).

Agregar un tipo: 1 entrada acá (selects/JS lo toman solos) + 1 builder en
static/js/field-registry.js (`window.FIELD_BUILDERS`) + su display en day.html.
"""

FIELD_TYPES = [
    ("text",          "Texto libre"),
    ("emotion-wheel", "🎡 Rueda de emociones"),
    ("duracion",      "⏱️ Duración"),
    ("rango",         "🕒 Rango horario"),
    ("escala",        "📊 Escala"),
    ("sino",          "☑️ Sí / No"),
    ("opciones",      "🔘 Opciones"),
    ("numero",        "🔢 Número"),
]
