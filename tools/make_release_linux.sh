#!/usr/bin/env bash
# Genera dist/Bitacora-linux-<fecha>.tar.gz listo para compartir:
# carpeta Bitacora/ con el código de la app + instalador + LEEME + manual.
# Correr en Linux o WSL (release-linux.bat lo hace desde Windows).
set -e
cd "$(dirname "$0")/.."

FECHA=$(date +%F)
TGZ="dist/Bitacora-linux-$FECHA.tar.gz"
STAGE=$(mktemp -d)
trap 'rm -rf "$STAGE"' EXIT

APP="$STAGE/Bitacora"
mkdir -p "$APP"

# Solo lo que la app necesita en runtime: sin tests, scripts de build,
# ni la health.db personal (cada usuario arranca con su DB limpia).
cp app.py appconfig.py desktop.py fieldtypes.py filters.py helpers.py services.py \
   requirements.txt requirements-desktop.txt "$APP/"
cp -r database routes static templates "$APP/"
find "$APP" -type d -name __pycache__ -prune -exec rm -rf {} +

cp tools/linux/instalar.sh tools/linux/bitacora.sh "$APP/"
# _version.py: generado en el stage para que la app sepa su versión en runtime.
printf 'VERSION = "v%s"\n' "$FECHA" > "$APP/_version.py"
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
