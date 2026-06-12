#!/usr/bin/env bash
# Abre la ventana de Bitácora. Antes hay que correr ./instalar.sh (una sola vez).
cd "$(dirname "$0")"

# GTK directo, sin que pywebview pruebe QT (evita el traceback "No module named qtpy").
export PYWEBVIEW_GUI=gtk
# El renderer DMABUF de WebKitGTK crashea en NVIDIA + Wayland
# ("Error 71 (Protocol error) dispatching to Wayland display").
export WEBKIT_DISABLE_DMABUF_RENDERER=1
# No alcanza con que venv/ exista: cuando la distro actualiza Python
# (ej. Arch 3.14 -> 3.15) el venv queda apuntando a un intérprete que ya no está.
venv/bin/python -c '' 2>/dev/null || {
    echo "El entorno de Python falta o quedó roto (¿se actualizó la distro?)." >&2
    echo "Corré ./instalar.sh y se regenera solo." >&2
    exit 1
}
exec venv/bin/python desktop.py "$@"
