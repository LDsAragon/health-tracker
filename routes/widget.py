"""Widget de escritorio: panel chico con tareas, calendario y nota rápida.

La página se ve igual en el navegador que en la ventana, así se puede desarrollar y verificar
sin abrir ventanas de verdad.
"""
import calendar as cal
from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for

import database as db
import services
import widget
from helpers import _first_weekday, _dow_names, _setting, _week_start, MESES

bp = Blueprint("widget", __name__)

PESTANAS = ("tareas", "calendario", "nota")


@bp.route("/widget")
def vista():
    pest = request.args.get("p", "tareas")
    hoy = date.today()
    corte = services.overdue_cutoff(hoy, _setting("todo_overdue_from", "week"), _week_start)

    año = int(request.args.get("anio") or hoy.year)
    mes = max(1, min(12, int(request.args.get("mes") or hoy.month)))
    dias = cal.monthrange(año, mes)[1]
    ini, fin = f"{año:04d}-{mes:02d}-01", f"{año:04d}-{mes:02d}-{dias:02d}"

    return render_template(
        "widget.html",
        pestana=pest if pest in PESTANAS else "tareas",
        hoy=hoy.isoformat(),
        tareas_hoy=db.get_todos_for_date(hoy.isoformat()),
        atrasadas=db.get_overdue_todos(corte.isoformat()),
        # Calendario compacto: los mismos datos que arma main.calendar_view
        anio=año, mes=mes, mes_nombre=MESES[mes],
        semanas=cal.Calendar(_first_weekday()).monthdayscalendar(año, mes),
        dow=[d[:2] for d in _dow_names()],   # la inicial repite M (martes/miércoles)
        notas_por_dia=db.get_notes_range(ini, fin),
        eventos_por_dia=services.events_by_date(
            db.get_recurring_events(), db.get_completions_range(ini, fin),
            [date(año, mes, d) for d in range(1, dias + 1)]),
        conteo_tareas=db.get_todo_counts_range(ini, fin),
        prev=(año - 1, 12) if mes == 1 else (año, mes - 1),
        sig=(año + 1, 1) if mes == 12 else (año, mes + 1),
        fijado=widget.esta_fijado(),
    )


def _volver(pest="tareas"):
    return redirect(url_for("widget.vista", p=pest))


@bp.route("/widget/tarea/<int:todo_id>/toggle", methods=["POST"])
def tarea_toggle(todo_id):
    db.toggle_todo(todo_id)
    return _volver("tareas")


@bp.route("/widget/tarea/agregar", methods=["POST"])
def tarea_agregar():
    texto = request.form.get("text", "").strip()
    if texto:
        db.add_todo(date.today().isoformat(), texto)
    return _volver("tareas")


@bp.route("/widget/nota", methods=["POST"])
def nota():
    texto = request.form.get("content", "").strip()
    if texto:
        db.add_note(date.today().isoformat(), texto)
    return _volver("nota")


# ── Control de la ventana (no hacen nada fuera del modo escritorio) ──────────

@bp.route("/widget/fijar", methods=["POST"])
def fijar():
    widget.fijar(not widget.esta_fijado())
    return _volver(request.form.get("p", "tareas"))


@bp.route("/widget/minimizar", methods=["POST"])
def minimizar():
    widget.minimizar()
    return _volver(request.form.get("p", "tareas"))


@bp.route("/widget/cerrar", methods=["POST"])
def cerrar():
    widget.cerrar()
    return _volver()


@bp.route("/widget/abrir", methods=["POST"])
def abrir():
    """Desde Ajustes. En el navegador no hay ventana que abrir: vuelve y ya."""
    widget.abrir()
    return redirect(url_for("main.settings_view"))


@bp.route("/instancia/mostrar", methods=["POST"])
def instancia_mostrar():
    """La llama por HTTP una segunda Bitácora que se está por cerrar sola.

    `mostrar_principal()` sirve los dos casos: la ventana escondida en la bandeja vuelve, y si
    la habías cerrado dejando solo el widget, se crea de nuevo. Se puede crear porque esto corre
    en el hilo de la request y no en el principal, que es lo que pide create_window.
    """
    widget.mostrar_principal()
    return "", 204


@bp.route("/widget/dia/<date_str>", methods=["POST"])
def dia(date_str):
    """Abre ese día en la ventana grande. Que no haya ventana grande es un caso NORMAL:
    es justamente para lo que existe el widget."""
    widget.abrir_en_principal(f"/day/{date_str}")
    return _volver("calendario")
