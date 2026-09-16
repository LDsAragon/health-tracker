"""Convierte un GIF o un video en cuadros ASCII para las animaciones de borrado.

Dibujar ASCII a mano tiene un techo bajo: sirve para un cocodrilo de tres líneas y no para una
ola que se te viene encima. Esto convierte material de verdad, cuadro por cuadro, que es como se
hacen las animaciones ASCII que valen la pena.

    .\\hacer.ps1 ascii material\\ola.mp4 --nombre ola
    .\\hacer.ps1 ascii material\\meteorito.gif --nombre meteorito --cols 80 --cuadros 18

Una escena puede componerse con VARIOS materiales, uno por plano, con la convencion
`escena.plano`. El de fondo va mas chico, mas lento y mas apagado que el de adelante: eso es el
parallax, y sin esa diferencia los dos dibujos se leen como uno encima del otro.

    .\\hacer.ps1 ascii material\\asteroide.gif --nombre meteorito.fondo

Sale a `bitacora/static/js/despedidas-arte.js`, que define `window.DESPEDIDAS_ARTE[nombre]` y lo
lee `despedidas.js`. Se regenera entero cada vez a partir de lo que haya en el JSON de al lado,
así agregar una animación no pisa las otras.

⚠️ El material de origen NO se commitea ni se distribuye: solo viaja el ASCII resultante. Y la
procedencia de cada uno se anota en `docs/material-ascii.md`, porque la app se publica y el arte
de terceros necesita saber de dónde salió.
"""
import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
SALIDA_JS = RAIZ / "bitacora" / "static" / "js" / "despedidas-arte.js"
SALIDA_JSON = RAIZ / "tools" / "ascii_arte.json"

# De menos a más tinta. En la app el texto es claro sobre fondo oscuro, así que más brillo en el
# original = carácter más denso acá.
RAMPA = " .:-=+*#%@"

# ⚠️ Una celda monoespaciada es mucho más alta que ancha (~0.5), así que hay que achatar el alto
# o todo sale estirado al doble. Es el error clásico de estas conversiones.
PROPORCION_CELDA = 0.5


def _ffmpeg(*args):
    exe = shutil.which("ffmpeg")
    if not exe:
        sys.exit("Falta ffmpeg en el PATH.")
    r = subprocess.run([exe, "-v", "error", *args], capture_output=True, text=True)
    if r.returncode:
        sys.exit("ffmpeg fallo:\n" + r.stderr.strip())


def extraer(origen: Path, carpeta: Path, cols: int, cuadros: int) -> list:
    """Saca `cuadros` PNG en escala de grises, ya con la grilla de caracteres como resolución."""
    filas = max(6, int(round(cols * PROPORCION_CELDA * 0.62)))
    # `fps` se calcula para repartir los cuadros a lo largo de TODO el material: con un fps fijo,
    # un clip largo daba 200 cuadros y uno corto tres.
    dur = duracion(origen)
    fps = max(1e-3, cuadros / dur) if dur else 12
    _ffmpeg("-i", str(origen),
            "-vf", "fps={:.4f},scale={}:{}:flags=lanczos,format=gray".format(fps, cols, filas),
            "-frames:v", str(cuadros),
            str(carpeta / "c%04d.png"))
    return sorted(carpeta.glob("*.png"))


def duracion(origen: Path) -> float:
    exe = shutil.which("ffprobe")
    if not exe:
        return 0.0
    r = subprocess.run([exe, "-v", "error", "-show_entries", "format=duration",
                        "-of", "csv=p=0", str(origen)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except ValueError:
        return 0.0


def a_ascii(png: Path, invertir: bool, piso: int) -> str:
    from PIL import Image
    with Image.open(png) as im:
        im = im.convert("L")
        ancho, alto = im.size
        pix = im.load()
        filas = []
        for y in range(alto):
            fila = []
            for x in range(ancho):
                v = pix[x, y]
                if invertir:
                    v = 255 - v
                # Por debajo del piso es fondo: en una escena oscura, el ruido de compresión
                # llenaba todo de puntos y el dibujo se perdía.
                if v < piso:
                    fila.append(" ")
                    continue
                i = int((v - piso) / max(1, 255 - piso) * (len(RAMPA) - 1))
                fila.append(RAMPA[min(len(RAMPA) - 1, max(0, i))])
            filas.append("".join(fila).rstrip())
        return "\n".join(filas)


def escribir_js(arte: dict):
    SALIDA_JSON.write_text(json.dumps(arte, ensure_ascii=False, indent=1), encoding="utf-8")
    cuerpo = json.dumps(arte, ensure_ascii=False)
    SALIDA_JS.write_text(
        "// GENERADO por tools/ascii_video.py — no editar a mano.\n"
        "// Cada entrada son los cuadros ASCII de un material convertido; la procedencia de cada\n"
        "// uno esta en docs/material-ascii.md. Lo lee static/js/despedidas.js.\n"
        "window.DESPEDIDAS_ARTE = " + cuerpo + ";\n",
        encoding="utf-8")


def main():
    p = argparse.ArgumentParser(description="GIF o video -> cuadros ASCII")
    p.add_argument("origen", help="el gif o video de entrada")
    p.add_argument("--nombre", required=True, help="con que slug se guarda (meteorito, ola, ...)")
    p.add_argument("--cols", type=int, default=86, help="ancho en caracteres (86)")
    p.add_argument("--cuadros", type=int, default=20, help="cuantos cuadros (20)")
    p.add_argument("--ms", type=int, default=90, help="milisegundos por cuadro (90)")
    p.add_argument("--invertir", action="store_true", help="para material claro sobre fondo claro")
    p.add_argument("--piso", type=int, default=28, help="por debajo de esto es fondo (28)")
    a = p.parse_args()

    origen = Path(a.origen)
    if not origen.exists():
        sys.exit("No existe: " + str(origen))

    arte = {}
    if SALIDA_JSON.exists():
        arte = json.loads(SALIDA_JSON.read_text(encoding="utf-8"))

    tmp = Path(tempfile.mkdtemp(prefix="ascii-"))
    try:
        pngs = extraer(origen, tmp, a.cols, a.cuadros)
        if not pngs:
            sys.exit("ffmpeg no saco ningun cuadro.")
        cuadros = [a_ascii(f, a.invertir, a.piso) for f in pngs]
        arte[a.nombre] = {"ms": a.ms, "cols": a.cols, "cuadros": cuadros}
        escribir_js(arte)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    peso = SALIDA_JS.stat().st_size / 1024
    print("OK: {} cuadros de {} -> {} ({:.0f} KB en total, {} animacion/es)".format(
        len(cuadros), a.nombre, SALIDA_JS.relative_to(RAIZ), peso, len(arte)))
    print("Vista previa del cuadro del medio:\n")
    print(cuadros[len(cuadros) // 2])


if __name__ == "__main__":
    main()
