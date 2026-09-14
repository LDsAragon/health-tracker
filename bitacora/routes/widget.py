"""Widget de escritorio: panel chico con tareas, calendario y nota rápida.

La página se ve igual en el navegador que en la ventana, así se puede desarrollar y verificar
sin abrir ventanas de verdad.
"""
import calendar as cal
from datetime import date

from flask import Blueprint, render_template, request, redirect, url_for

from bitacora import database as db
from bitacora import services
from bitacora.escritorio import widget
from bitacora.helpers import _first_weekday, _dow_names, _setting, _week_start, MESES

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
        notas_hoy=db.get_notes_for_date(hoy.isoformat()),
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
        # Rutinas de hoy: el mismo services.events_by_date que usa la vista del día, pedido para
        # un solo día. Detrás del ajuste, así el widget se puede dejar solo con tareas.
        rutinas_hoy=(services.events_by_date(
            db.get_recurring_events(),
            db.get_completions_range(hoy.isoformat(), hoy.isoformat()),
            [hoy]).get(hoy.isoformat(), [])
            if _setting("widget_rutinas", "show") == "show" else []),
        ver_rutinas=_setting("widget_rutinas", "show") == "show",
        # Lo que se viene, junto a las rutinas: el widget es el otro lugar donde se mira "qué hay
        # ahora", así que la antelación tiene el mismo sentido que en el día.
        avisos=(db.avisos_proximos(db.get_recurring_events(), hoy)
                if _setting("widget_rutinas", "show") == "show" else []),
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


@bp.route("/widget/rutina/<int:event_id>/toggle", methods=["POST"])
def rutina_toggle(event_id):
    """Marcar o desmarcar una rutina de hoy. Sin "saltear" ni nota de completado: eso vive en la
    ventana grande, y acá el espacio es de 340px."""
    hoy = date.today().isoformat()
    hecho = {e["id"] for e in services.events_by_date(
        db.get_recurring_events(), db.get_completions_range(hoy, hoy), [date.today()]
    ).get(hoy, []) if e.get("done")}
    if event_id in hecho:
        db.uncomplete_event(event_id, hoy)
    else:
        db.complete_event(event_id, hoy)
    return _volver("tareas")


@bp.route("/widget/tarea/<int:todo_id>/editar", methods=["POST"])
def tarea_editar(todo_id):
    """Cambiar el texto de una tarea sin salir del widget (204, como el resto del AJAX).

    Se acepta cualquier tarea que el widget MUESTRE: las de hoy y las que quedaron sin cerrar,
    que son de otros días. `update_todo` solo toca el texto, así que no hay nada más que
    preservar.
    """
    texto = request.form.get("text", "").strip()
    hoy = date.today()
    corte = services.overdue_cutoff(hoy, _setting("todo_overdue_from", "week"), _week_start)
    visibles = {t["id"] for t in db.get_todos_for_date(hoy.isoformat())}
    visibles |= {t["id"] for t in db.get_overdue_todos(corte.isoformat())}
    if not texto or todo_id not in visibles:
        return ("", 400)
    db.update_todo(todo_id, texto[:200])
    return ("", 204)


@bp.route("/widget/nota/<int:note_id>", methods=["POST"])
def nota_editar(note_id):
    """Editar el texto de una nota de hoy, sin salir del widget (204, como el resto del AJAX).

    ⚠️ Se relee la nota para volver a mandar su color: `update_note` reescribe la fila entera, y
    sin el color editar el texto desde acá se lo borraba. Y como se busca entre las de HOY, un id
    de otro día no se toca: el widget solo muestra las de hoy.
    """
    texto = request.form.get("content", "").strip()
    nota = next((n for n in db.get_notes_for_date(date.today().isoformat())
                 if n["id"] == note_id), None)
    if not nota or not texto:
        return ("", 400)
    db.update_note(note_id, texto, nota["color"])
    return ("", 204)


@bp.route("/widget/nota", methods=["POST"])
def nota():
    texto = request.form.get("content", "").strip()
    color = request.form.get("color", "").strip()
    if texto:
        db.add_note(date.today().isoformat(), texto, services.color_para_nota_nueva(color))
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
