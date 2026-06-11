"""Vistas de nivel sitio: home, calendario, semana, búsqueda, export, backup, ajustes."""
from datetime import date, timedelta
import calendar as cal
from flask import Blueprint, render_template, request, redirect, url_for, make_response, send_file
import database as db
import services
from appconfig import THEMES, SETTINGS
from helpers import _setting, _first_weekday, _week_start, _dow_names, safe_back

bp = Blueprint("main", __name__)


@bp.route("/")
def home():
    today = date.today()
    sv = _setting("start_view", "month")
    if sv == "week":
        return redirect(url_for("main.week_view", date_str=today.isoformat()))
    if sv == "today":
        return redirect(url_for("day.day_view", date_str=today.isoformat()))
    return redirect(url_for("main.calendar_view", year=today.year, month=today.month))


@bp.route("/calendar/<int:year>/<int:month>")
def calendar_view(year=None, month=None):
    today = date.today()
    if year is None:
        year, month = today.year, today.month
    month = max(1, min(12, month))

    month_days = cal.monthrange(year, month)[1]
    month_start = f"{year:04d}-{month:02d}-01"
    month_end   = f"{year:04d}-{month:02d}-{month_days:02d}"

    notes_by_date   = db.get_notes_range(month_start, month_end)
    completions     = db.get_completions_range(month_start, month_end)
    recurring       = db.get_recurring_events()
    dates           = [date(year, month, day) for day in range(1, month_days + 1)]

    events_by_date = services.events_by_date(recurring, completions, dates)
    journal_cats   = db.get_journal_categories()
    journal_badges = services.journal_badges(db.get_journal_entries_range(month_start, month_end))
    todo_counts    = db.get_todo_counts_range(month_start, month_end)

    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    next_month = month % 12 + 1
    next_year  = year if month < 12 else year + 1

    return render_template(
        "calendar.html",
        year=year, month=month,
        month_name=cal.month_name[month],
        weeks=cal.Calendar(_first_weekday()).monthdayscalendar(year, month),
        dow_names=_dow_names(),
        notes_by_date=notes_by_date,
        events_by_date=events_by_date,
        today=today.isoformat(),
        prev_year=prev_year, prev_month=prev_month,
        next_year=next_year, next_month=next_month,
        journal_cats=journal_cats,
        journal_badges=journal_badges,
        todo_counts=todo_counts,
    )


@bp.route("/week/<date_str>")
def week_view(date_str):
    today      = date.today()
    anchor     = date.fromisoformat(date_str)
    monday     = _week_start(anchor)   # inicio de semana según ajuste (lun|dom)
    sunday     = monday + timedelta(days=6)

    week_dates = [monday + timedelta(days=i) for i in range(7)]
    start      = monday.isoformat()
    end        = sunday.isoformat()

    notes_by_date   = db.get_notes_range(start, end)
    completions     = db.get_completions_range(start, end)
    recurring       = db.get_recurring_events()

    events_by_date = services.events_by_date(recurring, completions, week_dates)
    journal_cats   = db.get_journal_categories()
    journal_badges = services.journal_badges(db.get_journal_entries_range(start, end))
    todo_counts    = db.get_todo_counts_range(start, end)
    todos_by_date  = db.get_todos_range(start, end)

    prev_week = (monday - timedelta(days=7)).isoformat()
    next_week = (monday + timedelta(days=7)).isoformat()

    MONTHS = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio',
              'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre']

    if monday.month == sunday.month:
        week_label = f"{monday.day}–{sunday.day} de {MONTHS[monday.month-1]} {monday.year}"
    else:
        week_label = f"{monday.day} {MONTHS[monday.month-1]} – {sunday.day} {MONTHS[sunday.month-1]} {sunday.year}"

    return render_template(
        "week.html",
        week_dates=week_dates,
        week_label=week_label,
        notes_by_date=notes_by_date,
        events_by_date=events_by_date,
        today=today.isoformat(),
        prev_week=prev_week,
        next_week=next_week,
        anchor_month_url=url_for("main.calendar_view", year=anchor.year, month=anchor.month),
        journal_cats=journal_cats,
        journal_badges=journal_badges,
        todo_counts=todo_counts,
        todos_by_date=todos_by_date,
    )


# ── Ajustes ────────────────────────────────────────────────────────────────────

@bp.route("/ajustes")
def settings_view():
    return render_template("settings.html", themes=THEMES,
                           back=safe_back(request.args.get("back")))


@bp.route("/ajustes/guardar", methods=["POST"])
def settings_save():
    # Valida e itera el esquema único (appconfig.SETTINGS): agregar un ajuste = 1 entrada allá.
    for key, spec in SETTINGS.items():
        val = request.form.get(key)
        if val is not None and val in spec["choices"]:
            db.set_setting(key, val)
    # Se queda en /ajustes tras guardar; preserva el destino del botón "Volver".
    return redirect(url_for("main.settings_view", back=safe_back(request.form.get("back"))))


# ── Estadísticas ─────────────────────────────────────────────────────────────────

_CHARTABLE_TYPES = ("numero", "escala", "duracion", "rango", "sino", "opciones")


@bp.route("/estadisticas")
def stats_view():
    today = date.today()
    range_days = request.args.get("range", "90")
    range_days = int(range_days) if range_days in ("30", "90", "180", "365") else 90
    start = (today - timedelta(days=range_days - 1)).isoformat()
    end   = today.isoformat()

    cats = db.get_journal_categories()
    fieldinfo = {(c["id"], f["label"]): (f.get("type", "text"), c["name"])
                 for c in cats for f in c.get("fields", [])}

    charts = []
    # Automáticos: campos marcados con "graficar"
    for f in db.chartable_fields():
        s = db.build_series(f["category_id"], f["label"], f["type"], start, end)
        if s["data"]:
            charts.append({"title": f"{f['category_name']} · {f['label']}", **s})
    # Personalizados: tabla charts (cada uno con su propio rango)
    for ch in db.get_charts():
        info = fieldinfo.get((ch["category_id"], ch["field_label"]))
        if not info:
            continue   # categoría/campo borrado
        ftype, cname = info
        cstart = (today - timedelta(days=ch["range_days"] - 1)).isoformat()
        s = db.build_series(ch["category_id"], ch["field_label"], ftype, cstart, end)
        charts.append({"title": ch["title"] or f"{cname} · {ch['field_label']}",
                       "chart_id": ch["id"], **s})

    events = db.get_recurring_events()
    adh = db.get_completion_stats(events, days=range_days)
    adherence = [
        {"title": ev["title"], "color": ev["color"],
         "done": adh[ev["id"]]["done"], "applicable": adh[ev["id"]]["applicable"],
         "pct": round(adh[ev["id"]]["done"] / adh[ev["id"]]["applicable"] * 100)}
        for ev in events if adh[ev["id"]]["applicable"]
    ]

    # Para el constructor: categorías con sus campos graficables (numérico/sino/opciones)
    builder_cats = [
        {"id": c["id"], "name": c["name"],
         "fields": [f["label"] for f in c.get("fields", []) if f.get("type") in _CHARTABLE_TYPES]}
        for c in cats
    ]
    builder_cats = [c for c in builder_cats if c["fields"]]

    return render_template("stats.html", charts=charts, adherence=adherence,
                           range_days=range_days, builder_cats=builder_cats)


@bp.route("/estadisticas/grafico/add", methods=["POST"])
def charts_add():
    cat_id = request.form.get("category_id", "").strip()
    field  = request.form.get("field_label", "").strip()
    title  = request.form.get("title", "").strip()
    rng    = request.form.get("range_days", "90")
    rng    = int(rng) if rng in ("30", "90", "180", "365") else 90
    if cat_id and field:
        db.add_chart(int(cat_id), field, title, rng)
    return redirect(url_for("main.stats_view"))


@bp.route("/estadisticas/grafico/<int:chart_id>/delete", methods=["POST"])
def charts_delete(chart_id):
    db.delete_chart(chart_id)
    return redirect(url_for("main.stats_view"))


# ── Export ─────────────────────────────────────────────────────────────────────

@bp.route("/export")
def export_view():
    today = date.today().isoformat()
    first_of_month = date.today().replace(day=1).isoformat()
    return render_template("export.html", today=today, first_of_month=first_of_month,
                           datos=request.args.get("datos"),
                           back=safe_back(request.args.get("back")))


@bp.route("/export/download")
def export_download():
    import io, csv
    start = request.args.get("start", "").strip()
    end   = request.args.get("end", "").strip()
    if not start or not end:
        return redirect(url_for("main.export_view"))

    notes       = db.get_notes_range(start, end)
    completions = db.get_completions_range(start, end)
    ev_index    = {ev["id"]: ev["title"] for ev in db.get_recurring_events()}

    rows = []
    for date_str, day_notes in notes.items():
        for n in day_notes:
            rows.append((date_str, "nota", n["content"], n["created_at"][:16] if n["created_at"] else ""))

    for date_str, day_done in completions.items():
        for event_id, comp in day_done.items():
            title  = ev_index.get(event_id, f"evento #{event_id}")
            status = comp["status"]
            detail = f"[salteé] {title}" if status == "skipped" else title
            if comp["note"]:
                detail += f" — {comp['note']}"
            rows.append((date_str, "completacion", detail, ""))

    rows.sort(key=lambda r: r[0])

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["fecha", "tipo", "detalle", "hora"])
    writer.writerows(rows)

    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = f"attachment; filename=registros-{start}-al-{end}.csv"
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    return response


# ── Backup ─────────────────────────────────────────────────────────────────────

@bp.route("/backup")
def backup_download():
    # Snapshot consistente (incluye datos del WAL) a un temp; se envía y se borra.
    import os, io, tempfile
    fd, tmp = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    try:
        db.snapshot_to(tmp)
        with open(tmp, "rb") as f:
            data = f.read()
    finally:
        if os.path.exists(tmp):
            os.remove(tmp)
    today = date.today().isoformat()
    return send_file(io.BytesIO(data), as_attachment=True,
                     download_name=f"health-backup-{today}.db",
                     mimetype="application/octet-stream")


@bp.route("/restore", methods=["POST"])
def restore_upload():
    # Restaura la DB desde un .db subido. Destructivo: reemplaza todos los datos.
    import os, tempfile
    back = safe_back(request.form.get("back"))
    f = request.files.get("dbfile")
    if not f or not f.filename:
        return redirect(url_for("main.export_view", datos="err-nofile", back=back))
    base = os.path.dirname(os.path.abspath(db.db_path())) or "."
    fd, tmp = tempfile.mkstemp(suffix=".db", dir=base)   # mismo dir → os.replace atómico
    os.close(fd)
    try:
        f.save(tmp)
        ok, _msg = db.restore_from(tmp)
    finally:
        for p in (tmp, tmp + "-wal", tmp + "-shm"):
            if os.path.exists(p):
                os.remove(p)
    return redirect(url_for("main.export_view", datos="ok" if ok else "err-invalid", back=back))


# ── Search ─────────────────────────────────────────────────────────────────────

@bp.route("/search")
def search_view():
    query   = request.args.get("q", "").strip()
    results = db.search_notes(query) if query else []
    return render_template("search.html", query=query, results=results)
