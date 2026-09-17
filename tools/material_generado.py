"""Genera el material que no se puede conseguir: la onda expansiva del impacto.

No hay explosion libre que convierta bien a ASCII (se probaron varias: son humo y tono parejo, y
dan mancha). Pero una onda de choque es geometria pura -un anillo que se abre- y eso es justamente
lo que el ASCII dibuja bien: contraste alto y formas grandes.

Asi que en vez de buscarlas, se generan. Sale material propio, sin licencia de nadie y
reproducible desde el repo, que despues pasa por el mismo conversor que el resto:

    venv\\Scripts\\python tools\\material_generado.py
    .\\hacer.ps1 ascii material\\onda.gif --nombre meteorito.onda --cols 128 --cuadros 30
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parent.parent
MATERIAL = RAIZ / "material"

ANCHO, ALTO = 900, 500


def _guardar(cuadros, nombre, ms):
    MATERIAL.mkdir(parents=True, exist_ok=True)
    salida = MATERIAL / nombre
    cuadros[0].save(salida, save_all=True, append_images=cuadros[1:], duration=ms, loop=0)
    print("OK: %s (%d cuadros, %.0f KB)" % (salida, len(cuadros), salida.stat().st_size / 1024))


def onda(cuadros_n=30):
    """La onda expansiva del impacto del meteorito: un anillo que se abre y se apaga."""
    random.seed(7)          # mismo dibujo en cada corrida: el arte no puede cambiar solo
    centro = (ANCHO // 2, int(ALTO * 0.56))
    trozos = [(random.uniform(0, math.tau), random.uniform(0.55, 1.0),
               random.randint(2, 5)) for _ in range(46)]

    fuera = []
    for i in range(cuadros_n):
        t = i / (cuadros_n - 1)
        im = Image.new("L", (ANCHO, ALTO), 0)
        d = ImageDraw.Draw(im)

        # Se abre rapido al principio y se va frenando, afinandose y apagandose.
        r = (ANCHO * 0.62) * (1 - math.pow(1 - t, 2.2))
        grosor = max(1, int(26 * (1 - t) ** 1.4))
        brillo = int(255 * (1 - t) ** 0.9)
        if r > 2 and brillo > 6:
            d.ellipse([centro[0] - r, centro[1] - r * 0.52,
                       centro[0] + r, centro[1] + r * 0.52], outline=brillo, width=grosor)
        r2 = r * 0.72          # un segundo anillo atrasado, que le da cuerpo al frente
        if r2 > 2:
            d.ellipse([centro[0] - r2, centro[1] - r2 * 0.52,
                       centro[0] + r2, centro[1] + r2 * 0.52],
                      outline=int(brillo * 0.55), width=max(1, grosor // 2))
        if t < 0.45:           # el fogonazo del centro, que dura poco
            rc = ANCHO * 0.10 * (1 - t / 0.45)
            d.ellipse([centro[0] - rc, centro[1] - rc * 0.6,
                       centro[0] + rc, centro[1] + rc * 0.6], fill=255)

        # Los escombros, cada uno con su direccion FIJA: sorteadas por cuadro titilarian en vez
        # de volar.
        for ang, vel, tam in trozos:
            dist = r * vel * 1.25
            x = centro[0] + math.cos(ang) * dist
            y = centro[1] + math.sin(ang) * dist * 0.55
            b = int(255 * (1 - t) ** 1.6)
            if b > 10:
                d.ellipse([x - tam, y - tam, x + tam, y + tam], fill=b)
        fuera.append(im.convert("P"))
    _guardar(fuera, "onda.gif", 40)


if __name__ == "__main__":
    onda()
