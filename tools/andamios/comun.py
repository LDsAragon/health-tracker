"""Lo que comparten los andamios: leer, escribir e insertar en un ancla.

La inserción es **por ancla y no por heurística**. Un andamio que adivine dónde va cada cosa
parseando el archivo es la misma clase de error que ya se rechazó para los datos del usuario
(`CLAUDE.md` § Convenciones): si el ancla no está, se aborta y se dice, no se improvisa.
"""
import io
import os
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Con la salida redirigida a un pipe, Windows le pone cp1252 y cualquier caracter fuera de esa
# tabla (una flecha →, un guion largo) tira UnicodeEncodeError DESPUES de haber escrito los
# archivos: el andamio quedaba a medias y con un traceback en vez de su resumen.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except (AttributeError, OSError):
    pass


def ruta(*partes):
    return os.path.join(RAIZ, *partes)


def leer(p):
    return io.open(p, encoding="utf-8").read()


def escribir(p, s):
    io.open(p, "w", encoding="utf-8", newline="").write(s)


def insertar_en_ancla(p, ancla, bloque):
    """Pone `bloque` justo antes de la línea del ancla, con su misma sangría.

    Exige que el ancla aparezca **exactamente una vez**: dos anclas iguales significan que el
    archivo se editó de una forma que el andamio no entiende, y ahí es mejor no tocar nada.
    """
    lineas = leer(p).split("\n")
    idx = [i for i, l in enumerate(lineas) if ancla in l]
    if len(idx) != 1:
        sys.exit(f"ERROR: el ancla '{ancla}' aparece {len(idx)} veces en {p} "
                 "(tiene que ser exactamente 1).\n"
                 "       El andamio no adivina dónde insertar. Arreglá el ancla y reintentá.")
    i = idx[0]
    sangria = lineas[i][:len(lineas[i]) - len(lineas[i].lstrip())]
    lineas[i:i] = [sangria + l if l.strip() else l for l in bloque.split("\n")]
    escribir(p, "\n".join(lineas))


def abortar_si_existe(p, aguja, que):
    if aguja in leer(p):
        sys.exit(f"ERROR: {que} ya existe en {os.path.relpath(p, RAIZ)}.")


def crear_archivo(p, contenido):
    if os.path.exists(p):
        sys.exit(f"ERROR: {os.path.relpath(p, RAIZ)} ya existe; no lo piso.")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    escribir(p, contenido)
