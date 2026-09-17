"""Genera el GIF de la onda expansiva del impacto del meteorito.

No hay material libre de una explosion que convierta bien a ASCII (se probaron varios: son humo
y tono parejo, y dan mancha). Pero una onda de choque es geometria pura -un anillo que se abre-,
y eso es justamente lo que el ASCII dibuja bien: contraste alto y formas grandes.

Asi que en vez de buscarla, se genera. Sale material propio, sin licencia de nadie y reproducible
desde el repo, que despues pasa por el mismo conversor que el resto:

    venv\\Scripts\\python tools\\onda_choque.py
    .\\hacer.ps1 ascii material\\onda.gif --nombre meteorito.onda --cols 128 --cuadros 30

El anillo se abre y se afina mientras se apaga, con escombros que salen despedidos en direcciones
fijas -fijas a proposito: si se sortearan por cuadro, titilarian en vez de volar-.
"""
import math
import random
from pathlib import Path

from PIL import Image, ImageDraw

RAIZ = Path(__file__).resolve().parent.parent
SALIDA = RAIZ / "material" / "onda.gif"

ANCHO, ALTO = 900, 500
CUADROS = 30
CENTRO = (ANCHO // 2, int(ALTO * 0.56))
ESCOMBROS = 46


def main():
    random.seed(7)          # mismo dibujo en cada corrida: el arte no puede cambiar solo
    trozos = [(random.uniform(0, math.tau), random.uniform(0.55, 1.0),
               random.randint(2, 5)) for _ in range(ESCOMBROS)]

    cuadros = []
    for i in range(CUADROS):
        t = i / (CUADROS - 1)
        im = Image.new("L", (ANCHO, ALTO), 0)
        d = ImageDraw.Draw(im)

        # El anillo: se abre rapido al principio y se va frenando, afinandose y apagandose.
        r = (ANCHO * 0.62) * (1 - math.pow(1 - t, 2.2))
        grosor = max(1, int(26 * (1 - t) ** 1.4))
        brillo = int(255 * (1 - t) ** 0.9)
        if r > 2 and brillo > 6:
            d.ellipse([CENTRO[0] - r, CENTRO[1] - r * 0.52,
                       CENTRO[0] + r, CENTRO[1] + r * 0.52],
                      outline=brillo, width=grosor)

        # Un segundo anillo, mas atrasado: le da cuerpo al frente de la onda.
        r2 = r * 0.72
        if r2 > 2:
            d.ellipse([CENTRO[0] - r2, CENTRO[1] - r2 * 0.52,
                       CENTRO[0] + r2, CENTRO[1] + r2 * 0.52],
                      outline=int(brillo * 0.55), width=max(1, grosor // 2))

        # El fogonazo del centro, que dura poco.
        if t < 0.45:
            rc = ANCHO * 0.10 * (1 - t / 0.45)
            d.ellipse([CENTRO[0] - rc, CENTRO[1] - rc * 0.6,
                       CENTRO[0] + rc, CENTRO[1] + rc * 0.6], fill=255)

        # Y los escombros, cada uno con su direccion FIJA.
        for ang, vel, tam in trozos:
            dist = r * vel * 1.25
            x = CENTRO[0] + math.cos(ang) * dist
            y = CENTRO[1] + math.sin(ang) * dist * 0.55
            b = int(255 * (1 - t) ** 1.6)
            if b > 10:
                d.ellipse([x - tam, y - tam, x + tam, y + tam], fill=b)

        cuadros.append(im.convert("P"))

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    cuadros[0].save(SALIDA, save_all=True, append_images=cuadros[1:], duration=40, loop=0)
    print("OK: %s (%d cuadros, %.0f KB)" % (SALIDA, len(cuadros), SALIDA.stat().st_size / 1024))


if __name__ == "__main__":
    main()
