"""Gestión de perfiles: crear, renombrar, cambiar y borrar. Todo local."""
from flask import Blueprint, request, redirect, url_for

from bitacora import profiles
from bitacora.helpers import safe_back

bp = Blueprint("perfiles", __name__)

BORRAR_FRASE = "BORRAR PERFIL"
# Larga y explícita a propósito: nadie la tipea por costumbre, así que un hábito viejo no
# puede disparar el borrado más grande de todos.
FRASE_BORRAR_TODOS = "BORRAR TODOS LOS PERFILES"


def _volver(back, msg=""):
    """Vuelve a la pantalla desde la que se posteó. Sin esto, borrar el perfil desde Datos te
    dejaba en Ajustes, que no es donde estabas."""
    if request.form.get("volver_a") == "datos":
        return redirect(url_for("main.export_view", datos=f"perfil-{msg or 'ok'}",
                                back=safe_back(back)))
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


@bp.route("/perfiles/borrar-todos", methods=["POST"])
def borrar_todos():
    """Arrasa todos los perfiles. Los backups quedan en APP_DIR/backups/, fuera de lo borrado."""
    back = request.form.get("back")
    if request.form.get("confirm_text", "").strip() != FRASE_BORRAR_TODOS:
        return redirect(url_for("main.export_view", datos="err-todos-confirm",
                                back=safe_back(back)))
    cuantos, _backups = profiles.borrar_todos()
    return redirect(url_for("main.export_view", datos=f"todos-ok-{cuantos}",
                            back=safe_back(back)))
