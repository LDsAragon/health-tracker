#!/usr/bin/env bash
# Abre la ventana de Bitácora. Antes hay que correr ./instalar.sh (una sola vez).
cd "$(dirname "$0")"

# GTK directo, sin que pywebview pruebe QT (evita el traceback "No module named qtpy").
export PYWEBVIEW_GUI=gtk
# El renderer DMABUF de WebKitGTK crashea en NVIDIA + Wayland
# ("Error 71 (Protocol error) dispatching to Wayland display").
export WEBKIT_DISABLE_DMABUF_RENDERER=1
[ -x venv/bin/python ] || {
    echo "Bitácora todavía no está instalada acá: corré ./instalar.sh primero." >&2
    exit 1
}
exec venv/bin/python desktop.py "$@"
