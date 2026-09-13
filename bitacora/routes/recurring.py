"""Rutinas y recordatorios (eventos recurrentes).

Una rutina se mide, un recordatorio avisa: ver `CLAUDE.md` § "Rutinas y recordatorios".
"""
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for
from bitacora import database as db
from bitacora import services

bp = Blueprint("recurring", __name__)

# El orden y los textos de las dos secciones. El subtítulo va en la pantalla a propósito: es la
# única forma de que la diferencia entre una y otra sea obvia sin tener que explicarla.
TIPOS = (
    ("rutina",       "Rutinas",       "lo que se mide"),
    ("recordatorio", "Recordatorios", "lo que avisa"),
)


def _secciones(events, grupos):
    """[(tipo, título, subtítulo, [(grupo|None, eventos)])] para la pantalla.

    Se listan **todos** los grupos del tipo aunque estén vacíos —si acabás de crear uno, tenés que
    verlo— y "Sin grupo" solo cuando tiene algo adentro.
    """
    out = []
    for tipo, titulo, sub in TIPOS:
        bloques = []
        for g in grupos:
            if g["tipo"] == tipo:
                bloques.append((g, [e for e in events if e["group_id"] == g["id"]]))
        sueltos = [e for e in events
                   if (e.get("tipo") or "rutina") == tipo and not e["group_id"]]
        if sueltos:
            bloques.append((None, sueltos))
        out.append({"tipo": tipo, "titulo": titulo, "sub": sub, "bloques": bloques,
                    "total": sum(len(evs) for _, evs in bloques)})
    return out


@bp.route("/recurring")
def recurring_view():
    events = db.get_recurring_events()
    grupos = db.get_event_groups()
    hoy = date.today()
    return render_template("recurring.html",
                           secciones=_secciones(events, grupos),
                           grupos=grupos,
                           stats=db.get_completion_stats(events),
                           edades={e["id"]: services.edad_en(e.get("birth_year"), hoy.year)
                                   for e in events},
                           anio_actual=hoy.year,
                           today=hoy.isoformat())


def _recurrence_from_form(form):
    rtype = form.get("rtype", "daily")
    if rtype == "weekly":
        days = form.getlist("weekdays")
        return "weekly:" + ",".join(sorted(days)) if days else "daily"
    if rtype == "every":
        return f"every:{int(form.get('interval_days', 2))}"
    if rtype == "once":
        return "once"
    if rtype == "yearly":
        return "yearly"
    return "daily"


def _aviso_from_form(form) -> int:
    """Los presets (2 y 7) y el "otro", que solo se lee si elegiste esa opción."""
    valor = form.get("aviso", "0")
    if valor == "otro":
        try:
            return max(0, min(365, int(form.get("aviso_otro", 0))))
        except ValueError:
            return 0
    try:
        return max(0, min(365, int(valor)))
    except ValueError:
        return 0


def _donde_from_form(form, grupos) -> tuple:
    """El campo "Dónde va" decide el grupo Y el tipo, que es su razón de ser.

    ⚠️ Antes eran dos campos y podían contradecirse: una rutina dentro de un grupo de
    Recordatorios aparecía en la sección de Recordatorios pero se comportaba como rutina. Con un
    solo lugar donde se decide, eso deja de poder pasar.

    El valor es `g:<id>` para un grupo, o `sin:<tipo>` para los que no llevan grupo.
    """
    valor = form.get("donde", "sin:rutina")
    if valor.startswith("g:"):
        gid = valor[2:]
        grupo = next((g for g in grupos if str(g["id"]) == gid), None)
        if grupo:
            return grupo["id"], grupo["tipo"]
    tipo = "recordatorio" if valor.endswith(":recordatorio") else "rutina"
    return None, tipo


def _datos_from_form(form) -> dict:
    group_id, tipo = _donde_from_form(form, db.get_event_groups())
    return {
        "title":      form.get("title", "").strip(),
        "color":      form.get("color", "#6366f1"),
        "recurrence": _recurrence_from_form(form),
        "start_date": form.get("start_date", date.today().isoformat()),
        "end_date":   form.get("end_date", "").strip(),
        "tipo":       tipo,
        "group_id":   group_id,
        "birth_year": services.anio_de_nacimiento(form.get("birth_year", ""),
                                                  form.get("edad", ""), date.today()),
        # Solo los recordatorios avisan: "en 3 días vas al gimnasio" todos los días no ayuda.
        "aviso_dias": _aviso_from_form(form) if tipo == "recordatorio" else 0,
    }


@bp.route("/recurring/add", methods=["POST"])
def recurring_add():
    datos = _datos_from_form(request.form)
    if datos["title"]:
        db.add_recurring_event(datos)
    return redirect(url_for("recurring.recurring_view"))


@bp.route("/recurring/<int:event_id>/edit", methods=["POST"])
def recurring_edit(event_id):
    datos = _datos_from_form(request.form)
    if datos["title"]:
        db.update_recurring_event(event_id, datos)
    return redirect(url_for("recurring.recurring_view"))


@bp.route("/recurring/<int:event_id>/delete", methods=["POST"])
def recurring_delete(event_id):
    mode = request.form.get("mode", "all")
    if mode == "future":
        cutoff = (date.today() - timedelta(days=1)).isoformat()   # conserva el historial hasta ayer
        db.end_recurring_event(event_id, cutoff)
    else:
        db.delete_recurring_event(event_id)
    return redirect(url_for("recurring.recurring_view"))


@bp.route("/recurring/<int:event_id>/visibility", methods=["POST"])
def recurring_visibility(event_id):
    db.set_recurring_visibility(event_id, request.form.get("show") == "1")
    return redirect(url_for("recurring.recurring_view"))


# ── Grupos ───────────────────────────────────────────────────────────────────

def _color_libre(grupos) -> str:
    """El primer color de la paleta que ningún grupo esté usando.

    Se elige solo para que crear un grupo sea nombre y nada más: las nueve bolitas en cada fila
    eran la mitad del ruido de la pantalla, y el color se cambia después al editar.
    """
    from bitacora.appconfig import NOTE_COLORS
    usados = {g["color"] for g in grupos}
    for c in NOTE_COLORS:
        if c not in usados:
            return c
    return NOTE_COLORS[len(grupos) % len(NOTE_COLORS)]


@bp.route("/recurring/grupo/add", methods=["POST"])
def grupo_add():
    """El tipo NO viene de un campo: sale de la sección desde la que se creó."""
    nombre = request.form.get("name", "").strip()
    if nombre:
        grupos = db.get_event_groups()
        db.add_event_group({
            "name":  nombre,
            "color": _color_libre(grupos),
            "tipo":  "recordatorio" if request.form.get("tipo") == "recordatorio" else "rutina",
        })
    return redirect(url_for("recurring.recurring_view"))


@bp.route("/recurring/grupo/<int:group_id>/edit", methods=["POST"])
def grupo_edit(group_id):
    """Nombre y color. El tipo no se toca: mover un grupo de sección arrastraría todo lo que
    tiene adentro (sus rutinas perderían el porcentaje, o al revés), y no se vio la necesidad."""
    nombre = request.form.get("name", "").strip()
    actual = next((g for g in db.get_event_groups() if g["id"] == group_id), None)
    if nombre and actual:
        db.update_event_group(group_id, {
            "name":  nombre,
            "color": request.form.get("color", actual["color"]),
            "tipo":  actual["tipo"],
        })
    return redirect(url_for("recurring.recurring_view"))


@bp.route("/recurring/grupo/<int:group_id>/delete", methods=["POST"])
def grupo_delete(group_id):
    db.delete_event_group(group_id)      # devuelve False en el de fábrica; las rutinas no se tocan
    return redirect(url_for("recurring.recurring_view"))
