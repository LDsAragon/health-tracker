"""Sincronizar con otro dispositivo: exportar el paquete, previsualizar e importar."""
import io
import os
import tempfile

from flask import (Blueprint, render_template, request, redirect, url_for, send_file)

from bitacora import database as db
from bitacora import profiles
from bitacora import sync
from bitacora.helpers import safe_back

bp = Blueprint("sync", __name__)


def _volver(msg):
    return redirect(url_for("main.export_view", datos=msg,
                            back=safe_back(request.form.get("back"))))


@bp.route("/sync/exportar")
def exportar():
    """Mismo patrón que /backup: a un temp, a memoria, y el temp se borra enseguida."""
    perfil = profiles.activo()
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        sync.exportar(tmp, perfil, profiles.dispositivo())
        with open(tmp, "rb") as f:
            data = f.read()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    return send_file(io.BytesIO(data), as_attachment=True,
                     download_name=sync.nombre_archivo(perfil),
                     mimetype="application/octet-stream")


@bp.route("/sync/importar", methods=["POST"])
def importar():
    """Recibe el paquete, lo valida y lo deja en la ruta FIJA. No aplica nada todavía."""
    f = request.files.get("paquete")
    if not f or not f.filename:
        return _volver("sync-err-nofile")
    destino = sync.ruta_pendiente()
    f.save(destino)
    ok, _msg = sync.validar(destino)
    if not ok:
        os.remove(destino)
        return _volver("sync-err-invalid")
    return redirect(url_for("sync.previa", back=safe_back(request.form.get("back"))))


@bp.route("/sync/previa")
def previa():
    """Qué haría el merge, antes de tocar nada."""
    paquete = sync.ruta_pendiente()
    if not os.path.exists(paquete):
        return redirect(url_for("main.export_view"))
    perfil = profiles.activo()
    resumen = sync.analizar(paquete)
    meta = resumen["meta"]
    # Si el paquete no es de este perfil hay que confirmarlo a mano: un archivo equivocado
    # mezclaría dos diarios distintos, y deshacer eso es ir al backup.
    ajeno = not profiles.es_conocido(perfil, meta.get("perfil_uid", ""))
    return render_template("sync_previa.html", resumen=resumen, meta=meta, ajeno=ajeno,
                           perfil=perfil, back=safe_back(request.args.get("back")))


@bp.route("/sync/aplicar", methods=["POST"])
def aplicar():
    paquete = sync.ruta_pendiente()
    if not os.path.exists(paquete):
        return _volver("sync-err-nofile")
    meta = sync.meta_de(paquete)
    perfil = profiles.activo()
    ajeno = not profiles.es_conocido(perfil, meta.get("perfil_uid", ""))
    if ajeno and request.form.get("confirmo_ajeno") != "si":
        return redirect(url_for("sync.previa"))
    resumen = sync.aplicar(paquete)
    os.remove(paquete)
    if ajeno:
        profiles.emparejar(perfil["slug"], meta["perfil_uid"])
    total = resumen["total"]
    return _volver(f"sync-ok-{total['altas']}-{total['updates']}-{total['bajas']}")


@bp.route("/sync/descartar", methods=["POST"])
def descartar():
    paquete = sync.ruta_pendiente()
    if os.path.exists(paquete):
        os.remove(paquete)
    return _volver("sync-descartado")
