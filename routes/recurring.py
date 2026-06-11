"""Rutinas y recordatorios (eventos recurrentes)."""
from datetime import date, timedelta
from flask import Blueprint, render_template, request, redirect, url_for
import database as db

bp = Blueprint("recurring", __name__)


@bp.route("/recurring")
def recurring_view():
    events = db.get_recurring_events()
    stats  = db.get_completion_stats(events)
    return render_template("recurring.html",
                           events=events,
                           stats=stats,
                           today=date.today().isoformat())


def _recurrence_from_form(form):
    rtype = form.get("rtype", "daily")
    if rtype == "weekly":
        days = form.getlist("weekdays")
        return "weekly:" + ",".join(sorted(days)) if days else "daily"
    if rtype == "every":
        return f"every:{int(form.get('interval_days', 2))}"
    if rtype == "once":
        return "once"
    return "daily"


@bp.route("/recurring/add", methods=["POST"])
def recurring_add():
    title = request.form.get("title", "").strip()
    if title:
        db.add_recurring_event({
            "title":      title,
            "color":      request.form.get("color", "#6366f1"),
            "recurrence": _recurrence_from_form(request.form),
            "start_date": request.form.get("start_date", date.today().isoformat()),
            "end_date":   request.form.get("end_date", "").strip(),
        })
    return redirect(url_for("recurring.recurring_view"))


@bp.route("/recurring/<int:event_id>/edit", methods=["POST"])
def recurring_edit(event_id):
    title = request.form.get("title", "").strip()
    if title:
        db.update_recurring_event(event_id, {
            "title":      title,
            "color":      request.form.get("color", "#6366f1"),
            "recurrence": _recurrence_from_form(request.form),
            "start_date": request.form.get("start_date", date.today().isoformat()),
            "end_date":   request.form.get("end_date", "").strip(),
        })
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
