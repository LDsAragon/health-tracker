"""Visor de tareas: vista transversal, acciones sobre las atrasadas y el aviso de pendientes."""
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
import database as db
import services
from appconfig import LAST_WEEK_SEEN_KEY
from helpers import _setting, _week_start

bp = Blueprint("todos", __name__)

ESTADOS = (("pendientes", "Pendientes"), ("hechas", "Hechas"), ("todas", "Todas"))
# (valor, texto del botón, cómo se lee en el título del listado)
PERIODOS = (
    ("30",   "1 mes",   "Tareas del último mes"),
    ("90",   "3 meses", "Tareas de los últimos 3 meses"),
    ("365",  "1 año",   "Tareas del último año"),
    ("todo", "Todo",    "Todas las tareas"),
)
PERIODO_DIAS = {"30": 30, "90": 90, "365": 365, "todo": None}
ALERTA_MAX = 8


def _filtros():
    """Filtros del visor, saneados por whitelist. Lee args y form para sobrevivir a los POST."""
    estado = request.values.get("estado", "pendientes")
    periodo = request.values.get("periodo", "90")
    return {
        "estado": estado if estado in dict(ESTADOS) else "pendientes",
        "periodo": periodo if periodo in PERIODO_DIAS else "90",
        "q": request.values.get("q", "").strip(),
    }


def _back_to_todos():
    """Las acciones postean y vuelven al visor: sin esto se pierden los filtros activos."""
    return redirect(url_for("todos.todos_view", **{k: v for k, v in _filtros().items() if v}))


def _cutoff(today):
    return services.overdue_cutoff(today, _setting("todo_overdue_from", "week"), _week_start)


def _overdue(today):
    return db.get_overdue_todos(_cutoff(today).isoformat(), today.isoformat())


@bp.route("/tareas")
def todos_view():
    f = _filtros()
    today = date.today()
    dias = PERIODO_DIAS[f["periodo"]]
    # El período acota solo hacia atrás: lo que viene no se esconde nunca.
    start = (today - timedelta(days=dias - 1)).isoformat() if dias else None
    # Los contadores se calculan sobre todo el período: filtrados por "pendientes" darían
    # siempre 0 hechas. El estado solo acota el listado de abajo.
    del_periodo = db.get_todos_filtered(start=start, q=f["q"])
    if f["estado"] == "todas":
        listado = del_periodo
    else:
        abiertas = f["estado"] == "pendientes"
        listado = [t for t in del_periodo if bool(t["done"]) != abiertas]
    overdue = _overdue(today)

    por_dia = {}
    for t in listado:
        por_dia.setdefault(t["todo_date"], []).append(t)

    return render_template(
        "todos.html",
        f=f,
        today=today.isoformat(),
        estados=ESTADOS,
        periodos=PERIODOS,
        titulo_listado=dict((v, t) for v, _, t in PERIODOS)[f["periodo"]],
        overdue_total=len(overdue),
        buckets=services.overdue_buckets(overdue, today, _week_start),
        resumen=services.todos_overview(del_periodo, today),
        listado_total=len(listado),
        por_dia=sorted(por_dia.items(), reverse=True),
    )


@bp.route("/tareas/<int:todo_id>/toggle", methods=["POST"])
def todo_toggle(todo_id):
    db.toggle_todo(todo_id)
    return _back_to_todos()


@bp.route("/tareas/<int:todo_id>/hoy", methods=["POST"])
def todo_hoy(todo_id):
    db.move_todo(todo_id, date.today().isoformat())
    return _back_to_todos()


@bp.route("/tareas/<int:todo_id>/posponer", methods=["POST"])
def todo_posponer(todo_id):
    dias = request.form.get("dias", "1")
    dias = int(dias) if dias in ("1", "7") else 1
    db.snooze_todo(todo_id, (date.today() + timedelta(days=dias)).isoformat())
    return _back_to_todos()


@bp.route("/tareas/<int:todo_id>/borrar", methods=["POST"])
def todo_borrar(todo_id):
    db.delete_todo(todo_id)
    return _back_to_todos()


@bp.route("/tareas/traer-todas", methods=["POST"])
def traer_todas():
    today = date.today()
    db.move_todos([t["id"] for t in _overdue(today)], today.isoformat())
    return _back_to_todos()


@bp.route("/tareas/alerta")
def alerta():
    """Estado del aviso de atrasadas. El servidor decide si corresponde avisar."""
    today = date.today()
    items = _overdue(today)
    lunes = _week_start(today).isoformat()
    visto = db.get_setting(LAST_WEEK_SEEN_KEY, "")
    return jsonify({
        "count": len(items),
        "oldest": items[0]["todo_date"] if items else "",
        # Sin registro previo no hay "semana nueva": es el primer aviso, no un cambio.
        "week_changed": bool(items) and visto != "" and visto != lunes,
        "should_alert": bool(items) and _setting("todo_alert", "modal") == "modal",
        "items": [{"id": t["id"], "text": t["text"], "date": t["todo_date"]}
                  for t in items[:ALERTA_MAX]],
    })


@bp.route("/tareas/alerta/visto", methods=["POST"])
def alerta_visto():
    db.set_setting(LAST_WEEK_SEEN_KEY, _week_start(date.today()).isoformat())
    return ("", 204)
