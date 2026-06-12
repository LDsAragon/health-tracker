#!/usr/bin/env bash
# Prepara Bitácora para correr en Linux: ventana GTK/WebKitGTK (Wayland nativo).
# Uso: bash tools/setup_linux.sh   (pide sudo para los paquetes del sistema)
set -e
cd "$(dirname "$0")/.."

echo "== Paquetes del sistema (WebKitGTK + PyGObject) =="
SUDO=sudo; [ "$(id -u)" = 0 ] && SUDO=
$SUDO apt-get update -q
$SUDO apt-get install -y -q python3-venv python3-pip python3-gi python3-gi-cairo \
    gir1.2-gtk-3.0 gir1.2-webkit2-4.1

echo "== venv (con acceso a los paquetes GI del sistema) =="
[ -d venv-linux ] || python3 -m venv --system-site-packages venv-linux
venv-linux/bin/pip install --quiet -r requirements-desktop.txt

echo
echo "Listo. Para abrir la ventana:  venv-linux/bin/python desktop.py"
echo "(la DB vive en ~/.local/share/Bitacora/health.db)"
