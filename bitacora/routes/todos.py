"""Visor de tareas: vista transversal, acciones sobre las atrasadas y el aviso de pendientes."""
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from bitacora import database as db
from bitacora import services
from bitacora.appconfig import LAST_WEEK_SEEN_KEY
from bitacora.helpers import _setting, _week_start

bp = Blueprint("todos", __name__)

ESTADOS = (("pendientes", "Pendientes"), ("hechas", "Hechas"), ("todas", "Todas"))
# (valor, texto del botón, cómo se lee en el título del listado)
PERIODOS = (
    ("hoy",      "Hoy",      "Tareas de hoy"),
    ("7",        "1 sem",    "Tareas de la última semana"),
    ("14",       "2 sem",    "Tareas de las últimas 2 semanas"),
    ("21",       "3 sem",    "Tareas de las últimas 3 semanas"),
    ("30",       "1 mes",    "Tareas del último mes"),
    ("90",       "3 meses",  "Tareas de los últimos 3 meses"),
    ("proximas", "Próximas", "Tareas que vienen"),
    ("todo",     "Todo",     "Todas las tareas"),
)
PERIODO_DEFAULT = "hoy"
# Mover a hoy / mañana / la semana que viene, siempre relativo a hoy: un "+1 sem" sobre algo
# de julio tiene que caer la semana que viene, no seguir en el pasado.
MOVER_DIAS = ("0", "1", "7")
ALERTA_MAX = 8


def _filtros():
    """Filtros del visor, saneados por whitelist. Lee args y form para sobrevivir a los POST."""
    estado = request.values.get("estado", "pendientes")
    periodo = request.values.get("periodo", PERIODO_DEFAULT)
    return {
        "estado": estado if estado in dict(ESTADOS) else "pendientes",
        "periodo": periodo if periodo in dict((v, t) for v, _, t in PERIODOS) else PERIODO_DEFAULT,
        "q": request.values.get("q", "").strip(),
    }


def _back_to_todos(**extra):
    """Las acciones postean y vuelven al visor: sin esto se pierden los filtros activos."""
    args = {k: v for k, v in _filtros().items() if v}
    args.update({k: v for k, v in extra.items() if v})
    return redirect(url_for("todos.todos_view", **args))


def _fecha_valida(iso, fallback):
    """`add_todo`/`move_todo` no validan el formato y una fecha basura deja la tarea
    inaccesible desde toda vista: se filtra acá."""
    try:
        return date.fromisoformat(iso).isoformat()
    except (ValueError, TypeError):
        return fallback


def _cutoff(today):
    return services.overdue_cutoff(today, _setting("todo_overdue_from", "week"), _week_start)


def _overdue(today):
    return db.get_overdue_todos(_cutoff(today).isoformat())


@bp.route("/tareas")
def todos_view():
    f = _filtros()
    today = date.today()
    hoy_iso, manana_iso = today.isoformat(), (today + timedelta(days=1)).isoformat()
    start, end = services.periodo_ventana(f["periodo"], today)
    # El estado solo acota el listado de abajo: el conteo de hechas se saca del período entero
    # porque filtrado por "pendientes" daría siempre 0.
    del_periodo = db.get_todos_filtered(start=start, end=end, q=f["q"])
    if f["estado"] == "todas":
        listado = del_periodo
    else:
        abiertas = f["estado"] == "pendientes"
        listado = [t for t in del_periodo if bool(t["done"]) != abiertas]
    overdue = _overdue(today)

    por_dia = {}
    for t in listado:
        por_dia.setdefault(t["todo_date"], []).append(t)

    # Avisar de una tarea recién creada solo si no se ve en el listado (fuera de la ventana del
    # período, o filtrada por estado): si aparece abajo, el banner es ruido.
    nueva = _fecha_valida(request.args.get("nueva", ""), "")
    nueva_oculta = bool(nueva) and nueva not in por_dia

    return render_template(
        "todos.html",
        f=f,
        today=today.isoformat(),
        manana=manana_iso,
        estados=ESTADOS,
        periodos=PERIODOS,
        titulo_listado=dict((v, t) for v, _, t in PERIODOS)[f["periodo"]],
        overdue_total=len(overdue),
        buckets=services.overdue_buckets(overdue, today, _week_start),
        # "Para hoy" y "Próximas" son estados absolutos: atarlos a la ventana del período los
        # dejaba siempre en 0 (la ventana termina hoy). Solo "hechas" es relativo al período.
        resumen={
            "hoy": len(db.get_todos_filtered(start=hoy_iso, end=hoy_iso, status="pendientes")),
            "proximas": len(db.get_todos_filtered(start=manana_iso, status="pendientes")),
            "hechas": sum(1 for t in del_periodo if t["done"]),
        },
        listado_total=len(listado),
        nueva=nueva if nueva_oculta else "",
        por_dia=sorted(por_dia.items(), reverse=True),
    )


@bp.route("/tareas/agregar", methods=["POST"])
def todo_agregar():
    texto = request.form.get("text", "").strip()
    if not texto:
        return _back_to_todos()
    hoy = date.today().isoformat()
    fecha = _fecha_valida(request.form.get("fecha", ""), hoy)
    db.add_todo(fecha, texto)
    # `nueva` solo alimenta el aviso de "quedó fuera de la vista" (ver todos_view).
    return _back_to_todos(nueva=fecha)


@bp.route("/tareas/<int:todo_id>/toggle", methods=["POST"])
def todo_toggle(todo_id):
    db.toggle_todo(todo_id)
    return _back_to_todos()


@bp.route("/tareas/<int:todo_id>/mover", methods=["POST"])
def todo_mover(todo_id):
    """Hoy / mañana / la semana que viene. Un `dias` fuera de la whitelist no mueve nada:
    mover la tarea a una fecha equivocada es peor que no hacer nada."""
    dias = request.form.get("dias", "")
    if dias in MOVER_DIAS:
        db.move_todo(todo_id, (date.today() + timedelta(days=int(dias))).isoformat())
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
