"""Rutas de auto-actualización."""
import os
import threading
import updater
from flask import Blueprint, jsonify

bp = Blueprint("update", __name__)


@bp.route("/update/status")
def status():
    s = updater.get_status()
    return jsonify({
        "checked":   s["checked"],
        "available": s["available"],
        "current":   s["current"],
        "latest":    s["latest"],
    })


@bp.route("/update/download", methods=["POST"])
def download():
    ok = updater.start_download()
    return jsonify({"ok": ok})


@bp.route("/update/progress")
def progress():
    s = updater.get_status()
    return jsonify({
        "downloading": s["downloading"],
        "total":       s["dl_total"],
        "done":        s["dl_done"],
        "ready":       s["dl_ready"],
        "error":       s["dl_error"],
    })


@bp.route("/update/apply", methods=["POST"])
def apply():
    ok, err = updater.apply_update()
    return jsonify({"ok": ok, "error": err})


@bp.route("/update/quit", methods=["POST"])
def quit_app():
    threading.Timer(0.8, lambda: os._exit(0)).start()
    return jsonify({"ok": True})
