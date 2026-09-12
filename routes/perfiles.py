"""Gestión de perfiles: crear, renombrar, cambiar y borrar. Todo local."""
from flask import Blueprint, request, redirect, url_for

import profiles
from helpers import safe_back

bp = Blueprint("perfiles", __name__)

BORRAR_FRASE = "BORRAR PERFIL"


def _volver(back, msg=""):
    return redirect(url_for("main.settings_view", back=safe_back(back), perfiles=msg or None))


@bp.route("/perfiles/usar", methods=["POST"])
def usar():
    """Cambia de perfil en caliente y vuelve al inicio: seguir en la misma pantalla mostraría
    datos del perfil anterior en una URL que ya no les corresponde."""
    profiles.usar(request.form.get("slug", ""))
    return redirect(url_for("main.home"))


@bp.route("/perfiles/crear", methods=["POST"])
def crear():
    nombre = request.form.get("nombre", "").strip()
    if not nombre:
        return _volver(request.form.get("back"), "err-nombre")
    profiles.crear(nombre)
    return _volver(request.form.get("back"), "creado")


@bp.route("/perfiles/renombrar", methods=["POST"])
def renombrar():
    profiles.renombrar(request.form.get("slug", ""), request.form.get("nombre", ""))
    return _volver(request.form.get("back"), "renombrado")


@bp.route("/perfiles/borrar", methods=["POST"])
def borrar():
    """Borrar un perfil es borrar un diario entero: pide escribir la frase, como /reset."""
    if request.form.get("confirm_text", "").strip() != BORRAR_FRASE:
        return _volver(request.form.get("back"), "err-frase")
    ok, _msg = profiles.borrar(request.form.get("slug", ""))
    return _volver(request.form.get("back"), "borrado" if ok else "err-borrar")
