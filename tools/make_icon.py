"""Genera static/icon.ico: calendario con corazón sobre fondo índigo (tema default).

Correr con el venv (necesita pillow): venv/Scripts/python tools/make_icon.py
"""
from pathlib import Path

from PIL import Image, ImageDraw

S = 256
INDIGO = (99, 102, 241, 255)     # accent del tema índigo
DARK = (30, 27, 75, 255)         # header oscuro
WHITE = (255, 255, 255, 255)
HEART = (244, 63, 94, 255)       # rosa/rojo

img = Image.new("RGBA", (S, S), (0, 0, 0, 0))
d = ImageDraw.Draw(img)

# Fondo: cuadrado redondeado índigo
d.rounded_rectangle([10, 10, S - 10, S - 10], radius=56, fill=INDIGO)

# Tarjeta de calendario blanca con header oscuro
d.rounded_rectangle([52, 66, 204, 206], radius=18, fill=WHITE)
d.rounded_rectangle([52, 66, 204, 110], radius=18, fill=DARK)
d.rectangle([52, 92, 204, 110], fill=DARK)  # cuadrar el borde inferior del header

# Anillas del calendario
d.rounded_rectangle([82, 46, 98, 88], radius=8, fill=WHITE)
d.rounded_rectangle([158, 46, 174, 88], radius=8, fill=WHITE)

# Corazón centrado en el cuerpo de la tarjeta
cx, cy, r = 128, 146, 21
d.ellipse([cx - 2 * r, cy - r, cx, cy + r], fill=HEART)
d.ellipse([cx, cy - r, cx + 2 * r, cy + r], fill=HEART)
d.polygon([(cx - 2 * r + 3, cy + r * 0.42),
           (cx + 2 * r - 3, cy + r * 0.42),
           (cx, cy + 2.35 * r)], fill=HEART)

out = Path(__file__).resolve().parent.parent / "static" / "icon.ico"
img.save(out, sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)])
print(f"OK: {out}")
