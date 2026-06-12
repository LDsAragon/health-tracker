#!/usr/bin/env bash
# Abre la ventana de Bitácora. Antes hay que correr ./instalar.sh (una sola vez).
cd "$(dirname "$0")"
[ -x venv/bin/python ] || {
    echo "Bitácora todavía no está instalada acá: corré ./instalar.sh primero." >&2
    exit 1
}
exec venv/bin/python desktop.py "$@"
