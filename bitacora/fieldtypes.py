"""Tipos de campo de las notas especiales — fuente única (slug, etiqueta y configuración).

`config` es lo que el usuario escribe para terminar de definir el campo, y **cambia de significado
con el tipo**: las opciones de una lista, la unidad de un número, las etiquetas de una escala, el
texto de ayuda de un texto libre. Cuatro tipos no usan ninguna (`None`) y para esos el formulario
no muestra nada: antes había una columna "Ayuda" que significaba cuatro cosas distintas, no
significaba nada en la mitad de los casos, y hacía falta un párrafo arriba de la tabla para
explicarlo. Con el dato acá, cada fila se explica sola.

Lo consume el editor de categorías (`templates/_macros.html`, macro `campos_nota`) y lo leen los
builders del día por `static/js/field-blocks.js`.

Agregar un tipo: 1 entrada acá (selectores y JS lo toman solos) + 1 builder en
static/js/field-registry.js (`window.FIELD_BUILDERS`) + su display en day.html.
"""

FIELD_TYPES = [
    {"slug": "text", "label": "Texto libre",
     "config": {"label": "Texto de ayuda", "ph": "ej: ¿cómo te fue?"}},
    {"slug": "emotion-wheel", "label": "🎡 Rueda de emociones", "config": None},
    {"slug": "duracion",      "label": "⏱️ Duración",            "config": None},
    {"slug": "rango",         "label": "🕒 Rango horario",       "config": None},
    {"slug": "escala", "label": "📊 Escala",
     "config": {"label": "Etiquetas (opcional)", "ph": "😣, 😐, 😄 — vacío: del 1 al 5"}},
    {"slug": "sino",          "label": "☑️ Sí / No",             "config": None},
    {"slug": "opciones", "label": "🔘 Opciones",
     "config": {"label": "Opciones, separadas por coma", "ph": "Desayuno, Almuerzo, Cena",
                "requerida": True}},
    {"slug": "numero", "label": "🔢 Número",
     "config": {"label": "Unidad", "ph": "kg, vasos, km"}},
    # ANDAMIO: campos — `hacer.ps1 nuevo campo` inserta aca. No mover ni borrar.
]
