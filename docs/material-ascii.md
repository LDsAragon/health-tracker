# De dónde sale el arte ASCII de las animaciones de borrado

Los cuadros de `bitacora/static/js/despedidas-arte.js` los genera `tools/ascii_video.py` a partir
de material real. **El material de origen no se commitea** (`material/` está en el `.gitignore`):
solo viaja el ASCII resultante.

⚠️ La app se publica en GitHub Releases, así que lo que entre acá tiene que poder redistribuirse.
Dominio público o CC0. Nada de Giphy, Tenor ni bancos de imágenes: esas piezas tienen dueño y
convertirlas a ASCII sigue siendo una obra derivada.

| Escena | Origen | Autor | Licencia |
|---|---|---|---|
| `ola` | [La gran ola de Kanagawa](https://commons.wikimedia.org/wiki/File:Tsunami_by_hokusai_19th_century.jpg) (1831) | Katsushika Hokusai | Dominio público |
| `meteorito` | [GIF de Giphy](https://giphy.com/gifs/mograph-meteor-end-of-the-world-l46CvyAn1oBTOZtZK) (`l46CvyAn1oBTOZtZK`) | sin identificar | ⚠️ de terceros |
| `parca` | [GIF de Giphy](https://giphy.com/gifs/wave-xcopy-deathwave-xfkB0MewxbRt9BMxIK) (`xfkB0MewxbRt9BMxIK`) | atribuido a xcopy | ⚠️ de terceros |
| `ola.fondo` | el mismo Hokusai, sin recortar | Katsushika Hokusai | Dominio público |
| `meteorito.fondo` | [GIF de Giphy](https://giphy.com/gifs/earth-super-asteroid-YQPVI7u1Cue1W) (`YQPVI7u1Cue1W`) | sin identificar | ⚠️ de terceros |

⚠️ **Las dos últimas son obra de terceros y entran por decisión expresa del dueño del repo**
(2026-09-16), sobre la premisa de que el material de Giphy es re-subida de contenido ajeno. Queda
anotado acá porque una decisión así tiene que poder revisarse: si alguna vez hay que sacarlas,
basta con borrar su entrada de `tools/ascii_arte.json` y regenerar —las escenas vuelven solas al
dibujo a mano, que sigue en `despedidas.js` como respaldo—.

## Varios materiales en una misma escena

La escena tiene **tres planos** y cada uno puede venir de un material distinto, con la convención
`escena.plano`:

    hacer.ps1 ascii material\asteroide.gif --nombre meteorito.fondo
    hacer.ps1 ascii material\meteoro.gif   --nombre meteorito

⚠️ El plano de fondo tiene que ir **más chico, más lento y más apagado** que el de adelante. Eso
es el parallax y es lo único que hace que se lea "lejos": sin esa diferencia los dos dibujos se
ven como uno encima del otro y la profundidad desaparece.

## Cuántos cuadros pedirle

`ffprobe` dice cuántos trae el material y el conversor **acota solo**: pedir más de los que hay
solo los duplica —pesan igual y no se ven—. Pasó con la parca, que trae 10 y tenía 56: 180 KB de
duplicados.

- `--interpolar` genera intermedios de verdad, calculando el movimiento. Es la única forma de
  tener **más** cuadros que el original (el meteorito va de 60 a 117 así).
- `--bucle` es para el material corto: medio segundo estirado sobre una escena de cuatro va en
  cámara lentísima, así que cicla a su ritmo en vez de reproducirse una sola vez.
- `--recorte ancho:alto:x:y` acerca la cámara antes de convertir. Es lo que le dio escala a la
  ola: con la estampa entera se leía "un cuadro de una ola"; recortada al rompiente, se te viene
  encima.

## Qué material convierte bien

Salió de probar tres cosas distintas y mirar el resultado:

- **Sí**: contraste alto y formas grandes. Estampas, siluetas, grafismos, cosas con contorno
  grueso. Hokusai se lee perfecto a 100 columnas: la cresta, la espuma y hasta el Fuji al fondo.
- **No**: fotografía natural de tono parejo y grabado de línea fina. Probado con un caimán, un
  Holbein de 1538, un acuario y **tres GIF de tiburones**: todos dan mancha.

⚠️ **Lo que falla no es el contraste, es la silueta.** En una toma submarina el bicho y el agua
son el mismo gris: no hay contorno que reducir. Se intentó rescatarlos con `--bordes` (detección
de contorno antes de convertir) y `--normalizar` (estirar los niveles, porque el contorno sale
tenue —llega a 84 de 255— y cae entero por debajo del piso). Las dos opciones **funcionan y
quedan**, porque sirven para material fotográfico con un sujeto recortado contra el fondo; pero
ninguna inventa un contorno que no está.

El criterio corto: **si el material se ve bien en blanco y negro puro, convierte bien**. Un
tiburón en silueta contra el agua clara entra; el mismo tiburón filmado de costado en penumbra,
no.

La regla es que a 100 columnas cada carácter se come ~20×40 píxeles del original. Lo que no
sobreviva a esa reducción no va a estar en el ASCII.
