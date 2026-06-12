#!/usr/bin/env bash
# Instala Bitácora en este equipo: paquetes del sistema (WebKitGTK + PyGObject),
# entorno de Python (venv con Flask/pywebview) y acceso directo en el menú.
# Soporta Ubuntu/Debian/Mint (apt), Fedora (dnf) y Arch/Manjaro (pacman).
# Uso: ./instalar.sh   (pide tu contraseña para los paquetes del sistema)
set -e
cd "$(dirname "$0")"

echo "== Paquetes del sistema (WebKitGTK + PyGObject) =="
SUDO=sudo; [ "$(id -u)" = 0 ] && SUDO=
if command -v apt-get >/dev/null; then
    $SUDO apt-get update -q
    $SUDO apt-get install -y -q python3-venv python3-pip python3-gi python3-gi-cairo \
        gir1.2-gtk-3.0 gir1.2-webkit2-4.1
elif command -v dnf >/dev/null; then
    $SUDO dnf install -y python3-pip python3-gobject python3-cairo gtk3 webkit2gtk4.1
elif command -v pacman >/dev/null; then
    # Keyring de pacman: en sistemas recién creados (imagen WSL, container)
    # puede faltar; en una Arch/Manjaro normal este if no hace nada.
    # (trustdb.gpg lo crea pacman-key --init; el directorio solo no alcanza)
    [ -f /etc/pacman.d/gnupg/trustdb.gpg ] || {
        $SUDO pacman-key --init
        $SUDO pacman-key --populate
    }
    # -Sy refresca la lista de paquetes; en Arch conviene tener el sistema
    # actualizado (pacman -Syu) antes de instalar, como siempre.
    $SUDO pacman -Sy --needed --noconfirm python python-pip python-gobject \
        python-cairo gtk3 webkit2gtk-4.1
else
    echo "No encontré apt, dnf ni pacman: instalá a mano PyGObject + WebKitGTK 4.1" >&2
    echo "y después corré: python3 -m venv --system-site-packages venv &&" >&2
    echo "venv/bin/pip install -r requirements-desktop.txt" >&2
    exit 1
fi

echo "== Entorno de Python (venv con acceso a los paquetes GI del sistema) =="
# Si el venv quedó roto (la distro actualizó Python), regenerarlo de cero.
[ ! -d venv ] || venv/bin/python -c '' 2>/dev/null || rm -rf venv
[ -d venv ] || python3 -m venv --system-site-packages venv
venv/bin/pip install --quiet -r requirements-desktop.txt

echo "== Acceso directo en el menú de aplicaciones =="
chmod +x bitacora.sh
APPS_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/applications"
mkdir -p "$APPS_DIR"
cat > "$APPS_DIR/bitacora.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Bitácora
Comment=Calendario personal de hábitos, registros y emociones
Exec=$PWD/bitacora.sh
Icon=$PWD/static/icon.png
Terminal=false
Categories=Office;Utility;
EOF

echo
echo "Listo. Buscá \"Bitácora\" en el menú de aplicaciones, o corré ./bitacora.sh"
echo "(tus datos quedan en ~/.local/share/Bitacora/health.db)"
