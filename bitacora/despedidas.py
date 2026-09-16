"""Cómo se muere una tarea: las animaciones ASCII del borrado — fuente única.

Se reproducen sobre la fila de la tarea **después** de confirmar y antes de que el formulario se
envíe. Son decoración, así que la regla de oro vive del otro lado (`static/js/despedidas.js`):
si algo de esto falla, la tarea se borra igual.

Vive en Python y no en el JavaScript porque hay tres lectores —la vista del día, el visor de
tareas y el control de Ajustes que las previsualiza—, que es exactamente el caso que ya resolvieron
`appconfig.NOTE_COLORS` (estaba copiada en seis plantillas) y `plantillas.PLANTILLAS` (que era una
copia en JS de lo que también necesitaba el servidor). De acá sale además la whitelist del ajuste,
igual que `TIPOS_GRAFICABLES` sale de `FIELD_TYPES`: sumar una animación es agregar una entrada.

⚠️ Los cuadros se escriben sueltos y los normaliza `_cuadros()`. Emparejar a mano el ancho y el
alto de cinco animaciones es el trabajo que, hecho mal, convierte la animación en un temblor: una
línea más corta que la anterior mueve todo el dibujo un carácter.
"""

SEPARADOR = "\n--\n"


def _cuadros(bloque: str) -> tuple:
    """Los cuadros de un bloque, todos en la misma grilla (mismo ancho y mismo alto).

    ⚠️ Se saca UN salto de línea de cada punta —los que pone el `\"\"\"`— y nada más. Un `strip()`
    se comería también las líneas en blanco que un cuadro tiene a propósito: son las que dejan al
    meteorito arriba y a la ola abajo, así que borrarlas mueve el dibujo entero una fila.
    """
    bloque = bloque[1:] if bloque.startswith("\n") else bloque
    bloque = bloque[:-1] if bloque.endswith("\n") else bloque
    crudos = [c.split("\n") for c in bloque.split(SEPARADOR)]
    alto = max(len(c) for c in crudos)
    ancho = max(len(linea) for c in crudos for linea in c)
    return tuple(
        "\n".join([linea.ljust(ancho) for linea in c] + [" " * ancho] * (alto - len(c)))
        for c in crudos
    )


# La barra de bloques es la tarea. Es la misma en las cinco: lo que cambia es cómo se la llevan.
DESPEDIDAS = [
    {"slug": "meteorito", "nombre": "Meteorito", "icono": "☄️", "ms": 110, "cuadros": _cuadros(r"""
   \
    ☄
▀▀▀▀▀▀▀▀▀▀▀▀▀▀
--
       \
        ☄
▀▀▀▀▀▀▀▀▀▀▀▀▀▀
--

          ☄
▀▀▀▀▀▀▀▀▀▀▀▀▀▀
--
     ·  ✷  ·
   ▄  ▄   ▄  ▄
  ▀▀▀      ▀▀▀
--
    ˙  ·   ˙
      ▄   ▄
--
       ˙  ·
""")},
    {"slug": "ola", "nombre": "Ola", "icono": "🌊", "ms": 110, "cuadros": _cuadros(r"""

▀▀▀▀▀▀▀▀▀▀▀▀▀▀
--
 ≈
  ≈▀▀▀▀▀▀▀▀▀▀▀▀
--
 ≈≈≈≈
  ≈≈≈≈▀▀▀▀▀▀▀▀
--
 ≈≈≈≈≈≈≈≈
  ≈≈≈≈≈≈≈≈~▀▀▀
--
 ≈≈≈≈≈≈≈≈≈≈≈≈≈
  ≈≈≈≈≈≈≈≈≈≈≈≈≈
--
   ≈    ~    ≈
     ~     ≈
""")},
    {"slug": "parca", "nombre": "La parca", "icono": "💀", "ms": 130, "cuadros": _cuadros(r"""
  (˘_˘)
  /|\   /
▀▀▀▀▀▀▀▀▀▀▀▀▀▀
--
  (˘_˘)
  /|\ __
▀▀▀▀▀▀▀▀▀▀▀▀▀▀
--
  (˘_˘)
  /|\____
▀▀▀▀▀  ▀▀▀▀▀▀▀
--
  (◕‿◕)
  /|\
  ▀▀      ▀▀
--
  (◕‿◕)
  /|\
""")},
    {"slug": "cocodrilo", "nombre": "Cocodrilo", "icono": "🐊", "ms": 120, "cuadros": _cuadros(r"""

▀▀▀▀▀▀▀▀▀▀▀▀▀▀
--
          ____
▀▀▀▀▀▀▀▀_/    \
--
      ____
▀▀▀▀_/VVVV\
--
   ____
_/VVVVVV\
--
  ______
_/______\    ˙
""")},
    {"slug": "tiburon", "nombre": "Tiburón", "icono": "🦈", "ms": 120, "cuadros": _cuadros(r"""
            ^
▀▀▀▀▀▀▀▀▀▀▀▀▀▀
~~~~~~~~~~~~~~
--
        ^
▀▀▀▀▀▀▀▀▀
~~~~~~~~~~~~~~
--
     ^
▀▀▀▀▀
~~~~~~~~~~~~~~
--
  ^

~~~~~~~~~~~~~~
--

   ˙  ~   ˙
~~~~~~~~~~~~~~
""")},
]

SLUGS = tuple(d["slug"] for d in DESPEDIDAS)

# Los dos valores que no son una animación. `aleatorio` es el default del ajuste: la gracia es no
# saber cuál te toca.
AZAR = "aleatorio"
APAGADO = "off"
OPCIONES = (AZAR,) + SLUGS + (APAGADO,)


def por_slug(slug):
    return next((d for d in DESPEDIDAS if d["slug"] == slug), None)
