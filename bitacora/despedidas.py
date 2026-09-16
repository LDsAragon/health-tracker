"""Cómo se muere una tarea: el catálogo de animaciones de borrado — fuente única.

Acá vive la **identidad** de cada animación: su slug, cómo se llama y con qué se la reconoce en
Ajustes. De esta lista salen las `choices` del ajuste `animacion_borrado`, igual que
`TIPOS_GRAFICABLES` sale de `FIELD_TYPES`: sumar una animación es agregar una entrada.

La **coreografía** —el dibujo, la trayectoria y cómo se destruye el texto de la tarea— vive en
`static/js/despedidas.js`, en `COREOGRAFIAS`, porque es comportamiento y corre en el navegador.
⚠️ Las dos listas tienen que coincidir: una animación elegible en Ajustes sin coreografía es un
ajuste que no hace nada. Lo fija un tripwire en `tests/test_despedidas.py`.
"""

DESPEDIDAS = [
    {"slug": "meteorito", "nombre": "Meteorito", "icono": "☄️"},
    {"slug": "ola", "nombre": "Ola", "icono": "🌊"},
    {"slug": "parca", "nombre": "La parca", "icono": "💀"},
    {"slug": "cocodrilo", "nombre": "Cocodrilo", "icono": "🐊"},
    {"slug": "tiburon", "nombre": "Tiburón", "icono": "🦈"},
]

SLUGS = tuple(d["slug"] for d in DESPEDIDAS)

# Los dos valores que no son una animación. `aleatorio` es el default del ajuste: la gracia es no
# saber cuál te toca.
AZAR = "aleatorio"
APAGADO = "off"
OPCIONES = (AZAR,) + SLUGS + (APAGADO,)


def por_slug(slug):
    return next((d for d in DESPEDIDAS if d["slug"] == slug), None)
