"""Genera el material que no se puede conseguir: la onda expansiva y la pantalla rajada.

No hay explosion libre que convierta bien a ASCII (se probaron varias: son humo y tono parejo, y
dan mancha). Pero una onda de choque es geometria pura -un anillo que se abre- y una rajadura son
lineas desde un punto, y eso es justamente lo que el ASCII dibuja bien: contraste alto y formas
grandes.

Asi que en vez de buscarlas, se generan. Sale material propio, sin licencia de nadie y
reproducible desde el repo, que despues pasa por el mismo conversor que el resto:

    venv\\Scripts\\python tools\\material_generado.py
    .\\hacer.ps1 ascii material\\onda.gif   --nombre meteorito.onda --cols 128 --cuadros 30
    .\\hacer.ps1 ascii material\\grieta.gif --nombre parca.grieta   --cols 128 --cuadros 22
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


def grieta(cuadros_n=22):
    """La pantalla rajandose: la parca es un rostro que se estrella contra el vidrio.

    Las rajaduras salen del punto de impacto y CRECEN cuadro a cuadro; no aparecen enteras. Las
    direcciones y los quiebres se sortean una sola vez, o cada cuadro seria una rajadura distinta
    y se veria como ruido en vez de un vidrio partido.
    """
    random.seed(19)
    centro = (ANCHO // 2, int(ALTO * 0.48))

    ramas = []
    for k in range(13):
        ang = k * math.tau / 13 + random.uniform(-0.18, 0.18)
        largo = random.uniform(0.55, 1.15)
        # Cada rajadura es una quebrada: unos pocos tramos con angulo apenas distinto.
        quiebres = [random.uniform(-0.30, 0.30) for _ in range(3)]
        hijas = [(random.uniform(0.35, 0.8), random.choice((-1, 1)) * random.uniform(0.5, 1.0),
                  random.uniform(0.2, 0.42)) for _ in range(random.randint(1, 2))]
        ramas.append((ang, largo, quiebres, hijas))

    def trazar(d, ang, largo, quiebres, avance, brillo, grosor):
        x, y = centro
        a = ang
        tramos = len(quiebres)
        puntos = [(x, y)]
        for j, q in enumerate(quiebres):
            a += q
            paso = (ANCHO * 0.55) * largo / tramos * min(1, max(0, avance * tramos - j))
            if paso <= 0:
                break
            x += math.cos(a) * paso
            y += math.sin(a) * paso * 0.62
            puntos.append((x, y))
        if len(puntos) > 1:
            d.line(puntos, fill=brillo, width=grosor, joint="curve")
        return puntos, a

    fuera = []
    for i in range(cuadros_n):
        t = i / (cuadros_n - 1)
        avance = 1 - math.pow(1 - t, 2.6)      # rapido al principio, despues se frena
        im = Image.new("L", (ANCHO, ALTO), 0)
        d = ImageDraw.Draw(im)

        for ang, largo, quiebres, hijas in ramas:
            puntos, a = trazar(d, ang, largo, quiebres, avance, 255, max(2, int(7 * (1 - t * 0.5))))
            for desde, giro, corto in hijas:
                if avance <= desde or len(puntos) < 2:
                    continue
                base = puntos[min(len(puntos) - 1, max(1, int(desde * len(puntos))))]
                av = (avance - desde) / (1 - desde)
                bx = base[0] + math.cos(a + giro) * (ANCHO * 0.55) * corto * av
                by = base[1] + math.sin(a + giro) * (ANCHO * 0.55) * corto * av * 0.62
                d.line([base, (bx, by)], fill=190, width=max(1, int(4 * (1 - t * 0.5))))

        # El fogonazo del punto de impacto, que se apaga enseguida.
        if t < 0.3:
            rc = ANCHO * 0.07 * (1 - t / 0.3)
            d.ellipse([centro[0] - rc, centro[1] - rc * 0.6,
                       centro[0] + rc, centro[1] + rc * 0.6], fill=255)
        fuera.append(im.convert("P"))
    _guardar(fuera, "grieta.gif", 40)


if __name__ == "__main__":
    onda()
    grieta()
