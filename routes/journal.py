"""Notas especiales: configurar categorías (tipos) y sus campos."""
import json
from flask import Blueprint, render_template, request, redirect, url_for
import database as db
from helpers import safe_back

bp = Blueprint("journal", __name__)


@bp.route("/journal")
def journal_view():
    categories = db.get_journal_categories()
    return render_template("journal.html", categories=categories, back=safe_back(request.args.get("back")))


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
    return redirect(url_for("journal.journal_view", back=safe_back(request.form.get("back"))))


def _opts(placeholder) -> list:
    return [s.strip() for s in (placeholder or "").split(",") if s.strip()]


def _detect_label_renames(form, old_fields: dict) -> dict:
    """{etiqueta_vieja: nueva} — solo filas existentes (field_oldlabel[]) cuyo
    texto cambió y conservan el tipo (editar la fila = renombrar; borrar una
    fila y agregar otra NO migra nada)."""
    oldlabels = form.getlist("field_oldlabel[]")
    labels    = form.getlist("field_label[]")
    types     = form.getlist("field_type[]")
    renames = {}
    for i, lab in enumerate(labels):
        lab = lab.strip()
        old = oldlabels[i].strip() if i < len(oldlabels) else ""
        if not lab or not old or old == lab:
            continue
        of = old_fields.get(old)
        new_type = types[i].strip() if i < len(types) else "text"
        if of and of.get("type", "text") == new_type:
            renames[old] = lab
    return renames


@bp.route("/journal/<int:cat_id>/edit", methods=["POST"])
def journal_category_edit(cat_id):
    name  = request.form.get("name", "").strip()
    color = request.form.get("color", "#6366f1").strip()
    show  = 1 if request.form.get("show_in_calendar") else 0
    if not name:
        return redirect(url_for("journal.journal_view", back=safe_back(request.form.get("back"))))

    old_cat = next((c for c in db.get_journal_categories() if c["id"] == cat_id), None)
    old_fields = {f["label"]: f for f in (old_cat or {}).get("fields", [])}
    new_fields = _parse_fields(request.form)
    label_renames = _detect_label_renames(request.form, old_fields)

    # Rename explícito de una opción (control "Renombrar una opción" del form):
    # actualiza la lista del campo y migra las entradas. Agregar/quitar opciones
    # editando la lista a mano nunca toca lo guardado.
    option_renames = {}
    sel = request.form.get("opt_rename_sel", "")
    to  = request.form.get("opt_rename_to", "").strip()
    if sel and to and "||" in sel:
        flabel, de = sel.split("||", 1)
        flabel = label_renames.get(flabel, flabel)
        for f in new_fields:
            if f["label"] == flabel and f.get("type") == "opciones":
                opts = _opts(f.get("placeholder"))
                if de in opts and to not in opts:
                    f["placeholder"] = ", ".join(to if x == de else x for x in opts)
                    option_renames[flabel] = (de, to)
                break

    db.update_journal_category(cat_id, {
        "name":             name,
        "color":            color,
        "fields_json":      json.dumps(new_fields, ensure_ascii=False),
        "show_in_calendar": show,
    })
    db.migrate_entry_values(cat_id, label_renames, option_renames)
    return redirect(url_for("journal.journal_view", back=safe_back(request.form.get("back"))))


@bp.route("/journal/<int:cat_id>/delete", methods=["POST"])
def journal_category_delete(cat_id):
    db.delete_journal_category(cat_id)
    return redirect(url_for("journal.journal_view", back=safe_back(request.form.get("back"))))
