"""Notas especiales: configurar categorías (tipos) y sus campos."""
import json
from flask import Blueprint, render_template, request, redirect, url_for
import database as db

bp = Blueprint("journal", __name__)


@bp.route("/journal")
def journal_view():
    categories = db.get_journal_categories()
    return render_template("journal.html", categories=categories)


def _parse_fields(form) -> list:
    labels       = form.getlist("field_label[]")
    placeholders = form.getlist("field_placeholder[]")
    types        = form.getlist("field_type[]")
    charts       = form.getlist("field_chart[]")   # "1"/"0" por fila (alineado con labels)
    fields = []
    for i, label in enumerate(labels):
        if label.strip():
            f = {
                "label":       label.strip(),
                "placeholder": placeholders[i].strip() if i < len(placeholders) else "",
                "type":        types[i].strip() if i < len(types) else "text",
            }
            if i < len(charts) and charts[i] == "1":
                f["chart"] = True
            fields.append(f)
    return fields


@bp.route("/journal/add", methods=["POST"])
def journal_category_add():
    name  = request.form.get("name", "").strip()
    color = request.form.get("color", "#6366f1").strip()
    show  = 1 if request.form.get("show_in_calendar") else 0
    if name:
        db.add_journal_category({
            "name":             name,
            "color":            color,
            "fields_json":      json.dumps(_parse_fields(request.form), ensure_ascii=False),
            "show_in_calendar": show,
        })
    return redirect(url_for("journal.journal_view"))


@bp.route("/journal/<int:cat_id>/edit", methods=["POST"])
def journal_category_edit(cat_id):
    name  = request.form.get("name", "").strip()
    color = request.form.get("color", "#6366f1").strip()
    show  = 1 if request.form.get("show_in_calendar") else 0
    if name:
        db.update_journal_category(cat_id, {
            "name":             name,
            "color":            color,
            "fields_json":      json.dumps(_parse_fields(request.form), ensure_ascii=False),
            "show_in_calendar": show,
        })
    return redirect(url_for("journal.journal_view"))


@bp.route("/journal/<int:cat_id>/delete", methods=["POST"])
def journal_category_delete(cat_id):
    db.delete_journal_category(cat_id)
    return redirect(url_for("journal.journal_view"))
