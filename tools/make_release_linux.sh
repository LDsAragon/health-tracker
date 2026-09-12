#!/usr/bin/env bash
# Genera dist/Bitacora-linux-<fecha>.tar.gz listo para compartir:
# carpeta Bitacora/ con el código de la app + instalador + LEEME + manual.
# Correr en Linux o WSL (hacer.ps1 build-linux lo hace desde Windows).
set -e
cd "$(dirname "$0")/.."

FECHA=$(date +%F)
# Version a estampar: por defecto la fecha, pero publish_release.ps1 pasa el tag
# real (puede ser v<fecha>.1 en una re-publicacion). Si no coincide con el tag del
# release, el updater compara mal y ofrece actualizar en loop para siempre.
VERSION="${1:-v$FECHA}"
TGZ="dist/Bitacora-linux-$FECHA.tar.gz"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

APP="$STAGE/Bitacora"
mkdir -p "$APP"

# Solo lo que la app necesita en runtime: sin tests, scripts de build,
# ni la health.db personal (cada usuario arranca con su DB limpia).
# El paquete entero, sin lista de modulos: una lista explicita se desactualiza sola
# (updater.py falto desde v2026-06-25 y la app de Linux ni arrancaba).
cp main.py "$APP/"
cp requirements.txt requirements-desktop.txt "$APP/"
cp -r bitacora "$APP/"
find "$APP" -type d -name __pycache__ -prune -exec rm -rf {} +

cp tools/linux/instalar.sh tools/linux/bitacora.sh "$APP/"
# _version.py: generado en el stage para que la app sepa su versión en runtime.
printf 'VERSION = "%s"\n' "$VERSION" > "$APP/_version.py"
cp docs/LEEME-Linux.txt "$APP/LEEME.txt"
[ -f docs/Bitacora-Manual.pdf ] && cp docs/Bitacora-Manual.pdf "$APP/"

# Permisos sanos (copiar desde NTFS deja todo 777): solo los .sh ejecutables
find "$APP" -type d -exec chmod 755 {} +
find "$APP" -type f -exec chmod 644 {} +
chmod +x "$APP/instalar.sh" "$APP/bitacora.sh"

mkdir -p dist
rm -f "$TGZ"
tar -czf "$TGZ" -C "$STAGE" Bitacora
echo "OK: $TGZ ($(du -h "$TGZ" | cut -f1))"
echo "Contiene: carpeta Bitacora con la app, instalar.sh, LEEME.txt y el manual PDF."
