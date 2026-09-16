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

## Qué material convierte bien

Salió de probar tres cosas distintas y mirar el resultado:

- **Sí**: contraste alto y formas grandes. Estampas, siluetas, grafismos, cosas con contorno
  grueso. Hokusai se lee perfecto a 100 columnas: la cresta, la espuma y hasta el Fuji al fondo.
- **No**: fotografía natural de tono parejo (probado con un caimán: sale una mancha) y grabado de
  línea fina (probado con un Holbein de 1538: el entramado se vuelve ruido).

La regla es que a 100 columnas cada carácter se come ~20×40 píxeles del original. Lo que no
sobreviva a esa reducción no va a estar en el ASCII.
