"""Vista del día y sus acciones: notas, to-dos, eventos, entradas de notas especiales."""
from datetime import date, timedelta
from urllib.parse import urlsplit
from flask import Blueprint, render_template, request, redirect, url_for
import database as db

bp = Blueprint("day", __name__)


def _back_to_day(date_str):
    """Redirect a la vista del día preservando su query string (?ref=week).

    Las acciones del día (tildar to-do, marcar rutina, notas...) postean y
    vuelven al día: sin esto pierden el `ref` y el volver contextual cae al mes.
    Solo se respeta el referer si es exactamente esta misma vista del día.
    """
    r = urlsplit(request.referrer or "")
    if r.path == f"/day/{date_str}" and r.query:
        return redirect(f"{r.path}?{r.query}")
    return redirect(url_for("day.day_view", date_str=date_str))


@bp.route("/day/<date_str>")
def day_view(date_str):
    d = date.fromisoformat(date_str)
    notes     = db.get_notes_for_date(date_str)
    done      = db.get_completions_range(date_str, date_str).get(date_str, {})
    recurring = db.get_recurring_events()

    day_events = [
        {
            **ev,
            "done":    ev["id"] in done and done[ev["id"]]["status"] == "done",
            "skipped": ev["id"] in done and done[ev["id"]]["status"] == "skipped",
            "completion_note": done.get(ev["id"], {}).get("note", ""),
        }
        for ev in recurring if db.event_applies(ev, d)
    ]

    journal_entries = db.get_journal_entries_for_date(date_str)
    journal_cats    = db.get_journal_categories()
    todos           = db.get_todos_for_date(date_str)

    prev_day = (d - timedelta(days=1)).isoformat()
    next_day = (d + timedelta(days=1)).isoformat()
    ref      = request.args.get("ref", "cal")   # de dónde venimos: 'cal' | 'week'

    return render_template(
        "day.html",
        date_str=date_str, d=d, notes=notes, day_events=day_events,
        journal_entries=journal_entries, journal_cats=journal_cats, todos=todos,
        prev_day=prev_day, next_day=next_day, ref=ref,
        today=date.today().isoformat(),
    )


# ── Notas ─────────────────────────────────────────────────────────────────────

@bp.route("/day/<date_str>/note/add", methods=["POST"])
def note_add(date_str):
    content = request.form.get("content", "").strip()
    color   = request.form.get("color", "").strip()
    if content:
        db.add_note(date_str, content, color)
    next_page = request.form.get("next")
    if next_page == "calendar":
        d = date.fromisoformat(date_str)
        return redirect(url_for("main.calendar_view", year=d.year, month=d.month))
    if next_page == "week":
        return redirect(url_for("main.week_view", date_str=date_str))
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/note/<int:note_id>/edit", methods=["POST"])
def note_edit(date_str, note_id):
    content = request.form.get("content", "").strip()
    color   = request.form.get("color", "").strip()
    if content:
        db.update_note(note_id, content, color)
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/note/<int:note_id>/delete", methods=["POST"])
def note_delete(date_str, note_id):
    db.delete_note(note_id)
    return _back_to_day(date_str)


# ── To-dos ──────────────────────────────────────────────────────────────────────

@bp.route("/day/<date_str>/todo/add", methods=["POST"])
def todo_add(date_str):
    text = request.form.get("text", "").strip()
    if text:
        db.add_todo(date_str, text)
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/todo/<int:todo_id>/toggle", methods=["POST"])
def todo_toggle(date_str, todo_id):
    db.toggle_todo(todo_id)
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/todo/<int:todo_id>/edit", methods=["POST"])
def todo_edit(date_str, todo_id):
    text = request.form.get("text", "").strip()
    if text:
        db.update_todo(todo_id, text)
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/todo/<int:todo_id>/move", methods=["POST"])
def todo_move(date_str, todo_id):
    new_date = request.form.get("new_date", "").strip()
    if new_date:
        db.move_todo(todo_id, new_date)
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/todo/<int:todo_id>/delete", methods=["POST"])
def todo_delete(date_str, todo_id):
    db.delete_todo(todo_id)
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/todos/reorder", methods=["POST"])
def todos_reorder(date_str):
    order = request.form.get("order", "")
    ids = [int(x) for x in order.split(",") if x.strip().isdigit()]
    if ids:
        db.reorder_todos(date_str, ids)
    return ("", 204)


@bp.route("/todos/<int:todo_id>/move", methods=["POST"])
def todo_move_ajax(todo_id):
    """Mover un to-do a otro día (drag entre días en la vista semanal)."""
    new_date = request.form.get("date", "").strip()
    if new_date:
        db.move_todo(todo_id, new_date)
    return ("", 204)


# ── Eventos recurrentes (marcar en el día) ──────────────────────────────────────

@bp.route("/day/<date_str>/event/<int:event_id>/complete", methods=["POST"])
def event_complete(date_str, event_id):
    note = request.form.get("note", "").strip()
    db.complete_event(event_id, date_str, note)
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/event/<int:event_id>/skip", methods=["POST"])
def event_skip(date_str, event_id):
    note = request.form.get("note", "").strip()
    db.complete_event(event_id, date_str, note, status="skipped")
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/event/<int:event_id>/uncomplete", methods=["POST"])
def event_uncomplete(date_str, event_id):
    db.uncomplete_event(event_id, date_str)
    return _back_to_day(date_str)


# ── Entradas de notas especiales ────────────────────────────────────────────────

@bp.route("/day/<date_str>/journal/add", methods=["POST"])
def journal_entry_add(date_str):
    cat_id_str  = request.form.get("category_id", "").strip()
    values_json = request.form.get("values_json", "{}").strip() or "{}"
    tags        = request.form.get("tags", "").strip()
    if cat_id_str:
        db.add_journal_entry({
            "category_id": int(cat_id_str),
            "entry_date":  date_str,
            "values_json": values_json,
            "tags":        tags,
        })
    next_page = request.form.get("next")
    if next_page == "calendar":
        d = date.fromisoformat(date_str)
        return redirect(url_for("main.calendar_view", year=d.year, month=d.month))
    if next_page == "week":
        return redirect(url_for("main.week_view", date_str=date_str))
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/journal/<int:entry_id>/edit", methods=["POST"])
def journal_entry_edit(date_str, entry_id):
    values_json = request.form.get("values_json", "{}").strip() or "{}"
    tags        = request.form.get("tags", "").strip()
    db.update_journal_entry(entry_id, {"values_json": values_json, "tags": tags})
    return _back_to_day(date_str)


@bp.route("/day/<date_str>/journal/<int:entry_id>/delete", methods=["POST"])
def journal_entry_delete(date_str, entry_id):
    db.delete_journal_entry(entry_id)
    return _back_to_day(date_str)
