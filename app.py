from flask import Flask, render_template, request, redirect, url_for, make_response, send_file, g
from datetime import date, datetime, timedelta
import calendar as cal
import json
import database as db

app = Flask(__name__)


@app.template_filter('humantime')
def humantime_filter(ts):
    if not ts:
        return ''
    try:
        dt = datetime.fromisoformat(ts[:19])
        delta = (date.today() - dt.date()).days
        if delta == 0:
            return f"hoy {_fmt_clock(dt.strftime('%H:%M'))}"
        if delta == 1:
            return f"ayer {_fmt_clock(dt.strftime('%H:%M'))}"
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return ''


@app.template_filter('fechacorta')
def fechacorta_filter(s):
    """'2026-06-10' → '10/06/2026' (formato local, sin ISO/anglicismo)."""
    if not s:
        return ''
    try:
        return date.fromisoformat(s).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return s


@app.template_filter('dur_fmt')
def dur_fmt_filter(s):
    """Minutos ('90') → '1 h 30 min'. Vacío/0 → ''."""
    try:
        m = int(s)
    except (ValueError, TypeError):
        return s
    if m <= 0:
        return ''
    h, mm = divmod(m, 60)
    parts = []
    if h:
        parts.append(f"{h} h")
    if mm:
        parts.append(f"{mm} min")
    return " ".join(parts) or "0 min"


@app.template_filter('rango_fmt')
def rango_fmt_filter(s):
    """'02:00-09:00' → '02:00 → 09:00 · 7 h' (cruce de medianoche soportado)."""
    if not s or '-' not in s:
        return s
    try:
        a, b = s.split('-', 1)
        ah, am = (int(x) for x in a.split(':'))
        bh, bm = (int(x) for x in b.split(':'))
        dur = ((bh * 60 + bm) - (ah * 60 + am)) % 1440
        return f"{_fmt_clock(a)} → {_fmt_clock(b)} · {dur_fmt_filter(str(dur))}"
    except (ValueError, TypeError):
        return s


@app.before_request
def setup():
    db.init_db()
    g.settings = db.get_all_settings()


@app.context_processor
def inject_settings():
    """Expone los ajustes (ej. date_format) a todas las plantillas."""
    return {"settings": db.get_all_settings()}


def _setting(key, default=''):
    try:
        return getattr(g, 'settings', {}).get(key, default)
    except Exception:
        return default


def _fmt_clock(hhmm):
    """'23:30' → '23:30' (24h) o '11:30 PM' (12h) según el ajuste time_format."""
    try:
        h, m = hhmm.split(':')
        H = int(h)
    except (ValueError, AttributeError):
        return hhmm
    if _setting('time_format', '24h') == '12h':
        ap = 'AM' if H < 12 else 'PM'
        h12 = H % 12 or 12
        return f"{h12}:{m} {ap}"
    return hhmm


# ── Inicio de semana (mon|sun) ───────────────────────────────────────────────────
_DOW_MON = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']

def _first_weekday():
    return 6 if _setting('week_start', 'mon') == 'sun' else 0   # 0=lunes, 6=domingo

def _week_start(d):
    fw = _first_weekday()
    return d - timedelta(days=(d.weekday() - fw) % 7)

def _dow_names():
    fw = _first_weekday()
    return _DOW_MON[fw:] + _DOW_MON[:fw]


# ── Calendar ───────────────────────────────────────────────────────────────────

@app.route("/")
@app.route("/calendar/<int:year>/<int:month>")
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

    # pre-compute which events apply per day
    events_by_date: dict = {}
    for day in range(1, month_days + 1):
        d = date(year, month, day)
        d_str = d.isoformat()
        day_done = completions.get(d_str, {})
        events_by_date[d_str] = [
            {
                **ev,
                "done":    ev["id"] in day_done and day_done[ev["id"]]["status"] == "done",
                "skipped": ev["id"] in day_done and day_done[ev["id"]]["status"] == "skipped",
                "completion_note": day_done.get(ev["id"], {}).get("note", ""),
            }
            for ev in recurring
            if ev.get("show_in_calendar", 1) and db.event_applies(ev, d)
        ]

    journal_cats  = db.get_journal_categories()
    journal_raw   = db.get_journal_entries_range(month_start, month_end)
    journal_badges: dict = {}
    for ds_str, entries in journal_raw.items():
        seen: set = set()
        badges = []
        for e in entries:
            if e["show_in_calendar"] and e["category_id"] not in seen:
                seen.add(e["category_id"])
                badges.append({"name": e["category_name"], "color": e["category_color"]})
        if badges:
            journal_badges[ds_str] = badges

    todo_counts = db.get_todo_counts_range(month_start, month_end)

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


# ── Day view ───────────────────────────────────────────────────────────────────

@app.route("/day/<date_str>")
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
        date_str=date_str,
        d=d,
        notes=notes,
        day_events=day_events,
        journal_entries=journal_entries,
        journal_cats=journal_cats,
        todos=todos,
        prev_day=prev_day,
        next_day=next_day,
        ref=ref,
        today=date.today().isoformat(),
    )


@app.route("/day/<date_str>/note/add", methods=["POST"])
def note_add(date_str):
    content = request.form.get("content", "").strip()
    color   = request.form.get("color", "").strip()
    if content:
        db.add_note(date_str, content, color)
    next_page = request.form.get("next")
    if next_page == "calendar":
        d = date.fromisoformat(date_str)
        return redirect(url_for("calendar_view", year=d.year, month=d.month))
    if next_page == "week":
        return redirect(url_for("week_view", date_str=date_str))
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/note/<int:note_id>/edit", methods=["POST"])
def note_edit(date_str, note_id):
    content = request.form.get("content", "").strip()
    color   = request.form.get("color", "").strip()
    if content:
        db.update_note(note_id, content, color)
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/note/<int:note_id>/delete", methods=["POST"])
def note_delete(date_str, note_id):
    db.delete_note(note_id)
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/todo/add", methods=["POST"])
def todo_add(date_str):
    text = request.form.get("text", "").strip()
    if text:
        db.add_todo(date_str, text)
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/todo/<int:todo_id>/toggle", methods=["POST"])
def todo_toggle(date_str, todo_id):
    db.toggle_todo(todo_id)
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/todo/<int:todo_id>/edit", methods=["POST"])
def todo_edit(date_str, todo_id):
    text = request.form.get("text", "").strip()
    if text:
        db.update_todo(todo_id, text)
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/todo/<int:todo_id>/move", methods=["POST"])
def todo_move(date_str, todo_id):
    new_date = request.form.get("new_date", "").strip()
    if new_date:
        db.move_todo(todo_id, new_date)
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/todo/<int:todo_id>/delete", methods=["POST"])
def todo_delete(date_str, todo_id):
    db.delete_todo(todo_id)
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/todos/reorder", methods=["POST"])
def todos_reorder(date_str):
    order = request.form.get("order", "")
    ids = [int(x) for x in order.split(",") if x.strip().isdigit()]
    if ids:
        db.reorder_todos(date_str, ids)
    return ("", 204)


@app.route("/todos/<int:todo_id>/move", methods=["POST"])
def todo_move_ajax(todo_id):
    """Mover un to-do a otro día (drag entre días en la vista semanal)."""
    new_date = request.form.get("date", "").strip()
    if new_date:
        db.move_todo(todo_id, new_date)
    return ("", 204)


@app.route("/day/<date_str>/event/<int:event_id>/complete", methods=["POST"])
def event_complete(date_str, event_id):
    note = request.form.get("note", "").strip()
    db.complete_event(event_id, date_str, note)
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/event/<int:event_id>/skip", methods=["POST"])
def event_skip(date_str, event_id):
    note = request.form.get("note", "").strip()
    db.complete_event(event_id, date_str, note, status="skipped")
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/event/<int:event_id>/uncomplete", methods=["POST"])
def event_uncomplete(date_str, event_id):
    db.uncomplete_event(event_id, date_str)
    return redirect(url_for("day_view", date_str=date_str))


# ── Recurring events ───────────────────────────────────────────────────────────

@app.route("/recurring")
def recurring_view():
    events = db.get_recurring_events()
    stats  = db.get_completion_stats(events)
    return render_template("recurring.html",
                           events=events,
                           stats=stats,
                           today=date.today().isoformat())


@app.route("/recurring/add", methods=["POST"])
def recurring_add():
    rtype = request.form.get("rtype", "daily")
    if rtype == "weekly":
        days = request.form.getlist("weekdays")
        recurrence = "weekly:" + ",".join(sorted(days)) if days else "daily"
    elif rtype == "every":
        n = int(request.form.get("interval_days", 2))
        recurrence = f"every:{n}"
    elif rtype == "once":
        recurrence = "once"
    else:
        recurrence = "daily"

    title = request.form.get("title", "").strip()
    if title:
        db.add_recurring_event({
            "title":      title,
            "color":      request.form.get("color", "#6366f1"),
            "recurrence": recurrence,
            "start_date": request.form.get("start_date", date.today().isoformat()),
            "end_date":   request.form.get("end_date", "").strip(),
        })
    return redirect(url_for("recurring_view"))


@app.route("/recurring/<int:event_id>/edit", methods=["POST"])
def recurring_edit(event_id):
    rtype = request.form.get("rtype", "daily")
    if rtype == "weekly":
        days = request.form.getlist("weekdays")
        recurrence = "weekly:" + ",".join(sorted(days)) if days else "daily"
    elif rtype == "every":
        n = int(request.form.get("interval_days", 2))
        recurrence = f"every:{n}"
    elif rtype == "once":
        recurrence = "once"
    else:
        recurrence = "daily"
    title = request.form.get("title", "").strip()
    if title:
        db.update_recurring_event(event_id, {
            "title":      title,
            "color":      request.form.get("color", "#6366f1"),
            "recurrence": recurrence,
            "start_date": request.form.get("start_date", date.today().isoformat()),
            "end_date":   request.form.get("end_date", "").strip(),
        })
    return redirect(url_for("recurring_view"))


@app.route("/recurring/<int:event_id>/delete", methods=["POST"])
def recurring_delete(event_id):
    mode = request.form.get("mode", "all")
    if mode == "future":
        # corta a futuro: conserva el historial hasta ayer
        cutoff = (date.today() - timedelta(days=1)).isoformat()
        db.end_recurring_event(event_id, cutoff)
    else:
        db.delete_recurring_event(event_id)
    return redirect(url_for("recurring_view"))


@app.route("/recurring/<int:event_id>/visibility", methods=["POST"])
def recurring_visibility(event_id):
    show = request.form.get("show") == "1"
    db.set_recurring_visibility(event_id, show)
    return redirect(url_for("recurring_view"))


# ── Week view ──────────────────────────────────────────────────────────────────

@app.route("/week/<date_str>")
def week_view(date_str):
    from datetime import timedelta
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

    events_by_date = {}
    for d in week_dates:
        d_str    = d.isoformat()
        day_done = completions.get(d_str, {})
        events_by_date[d_str] = [
            {
                **ev,
                "done":    ev["id"] in day_done and day_done[ev["id"]]["status"] == "done",
                "skipped": ev["id"] in day_done and day_done[ev["id"]]["status"] == "skipped",
                "completion_note": day_done.get(ev["id"], {}).get("note", ""),
            }
            for ev in recurring
            if ev.get("show_in_calendar", 1) and db.event_applies(ev, d)
        ]

    journal_cats  = db.get_journal_categories()
    journal_raw   = db.get_journal_entries_range(start, end)
    journal_badges: dict = {}
    for ds_str, entries in journal_raw.items():
        seen: set = set()
        badges = []
        for e in entries:
            if e["show_in_calendar"] and e["category_id"] not in seen:
                seen.add(e["category_id"])
                badges.append({"name": e["category_name"], "color": e["category_color"]})
        if badges:
            journal_badges[ds_str] = badges

    todo_counts  = db.get_todo_counts_range(start, end)
    todos_by_date = db.get_todos_range(start, end)

    prev_week = (monday - timedelta(days=7)).isoformat()
    next_week = (monday + timedelta(days=7)).isoformat()

    MONTHS = ['enero','febrero','marzo','abril','mayo','junio',
              'julio','agosto','septiembre','octubre','noviembre','diciembre']

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
        anchor_month_url=url_for("calendar_view", year=anchor.year, month=anchor.month),
        journal_cats=journal_cats,
        journal_badges=journal_badges,
        todo_counts=todo_counts,
        todos_by_date=todos_by_date,
    )


# ── Ajustes ────────────────────────────────────────────────────────────────────

# Temas: slug + nombre + 4 colores para el swatch (las paletas reales están en style.css → [data-theme]).
THEMES = [
    {"slug": "indigo",     "name": "Índigo",     "dark": True,  "bg": "#0f1117", "surface": "#1a1d27", "text": "#e2e8f0", "accent": "#6366f1"},
    {"slug": "medianoche", "name": "Medianoche", "dark": True,  "bg": "#0d1117", "surface": "#161b22", "text": "#c9d1d9", "accent": "#539bf5"},
    {"slug": "bosque",     "name": "Bosque",     "dark": True,  "bg": "#14211a", "surface": "#1b2a1b", "text": "#cfe8c8", "accent": "#6fbf73"},
    {"slug": "oceano",     "name": "Océano",     "dark": True,  "bg": "#0b1a2c", "surface": "#112334", "text": "#cfe9ff", "accent": "#4facfe"},
    {"slug": "ciruela",    "name": "Ciruela",    "dark": True,  "bg": "#1e1420", "surface": "#2b1b2e", "text": "#f5d8ec", "accent": "#e879b9"},
    {"slug": "cobre",      "name": "Cobre",      "dark": True,  "bg": "#140f0a", "surface": "#1c1410", "text": "#e8c39e", "accent": "#d4764e"},
    {"slug": "claude",     "name": "Claude",     "dark": True,  "bg": "#1f1e1c", "surface": "#262624", "text": "#f5f4f0", "accent": "#c6613f"},
    {"slug": "cyberpunk",  "name": "Cyberpunk",  "dark": True,  "bg": "#0a0a0f", "surface": "#12101a", "text": "#0ff0fc", "accent": "#e040fb"},
    {"slug": "retrowave",  "name": "Retrowave",  "dark": True,  "bg": "#1a1a2e", "surface": "#16213e", "text": "#f0e9ff", "accent": "#e94560"},
    {"slug": "papel",      "name": "Papel",      "dark": False, "bg": "#faf8f5", "surface": "#ffffff", "text": "#3b3836", "accent": "#b0832e"},
    {"slug": "claro",      "name": "Claro",      "dark": False, "bg": "#f0ebe3", "surface": "#faf6f0", "text": "#4a443c", "accent": "#c47d5a"},
    {"slug": "lavanda",    "name": "Lavanda",    "dark": False, "bg": "#f3eef8", "surface": "#faf7ff", "text": "#3d3551", "accent": "#9b6dcc"},
]
THEME_SLUGS = {t["slug"] for t in THEMES}


@app.route("/ajustes")
def settings_view():
    return render_template("settings.html", themes=THEMES)


@app.route("/ajustes/guardar", methods=["POST"])
def settings_save():
    fmt = request.form.get("date_format", "dmy")
    if fmt in ("dmy", "mdy", "ymd"):
        db.set_setting("date_format", fmt)
    tfmt = request.form.get("time_format", "24h")
    if tfmt in ("24h", "12h"):
        db.set_setting("time_format", tfmt)
    theme = request.form.get("theme", "indigo")
    if theme in THEME_SLUGS:
        db.set_setting("theme", theme)
    wstart = request.form.get("week_start", "mon")
    if wstart in ("mon", "sun"):
        db.set_setting("week_start", wstart)
    return redirect(url_for("settings_view"))


# ── Export ─────────────────────────────────────────────────────────────────────

@app.route("/export")
def export_view():
    today = date.today().isoformat()
    first_of_month = date.today().replace(day=1).isoformat()
    return render_template("export.html", today=today, first_of_month=first_of_month)


@app.route("/export/download")
def export_download():
    import io, csv
    start = request.args.get("start", "").strip()
    end   = request.args.get("end", "").strip()
    if not start or not end:
        return redirect(url_for("export_view"))

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

@app.route("/backup")
def backup_download():
    import os
    db_path = os.path.abspath(db.DB_PATH)
    today   = date.today().isoformat()
    return send_file(db_path, as_attachment=True,
                     download_name=f"health-backup-{today}.db")


# ── Search ─────────────────────────────────────────────────────────────────────

@app.route("/search")
def search_view():
    query   = request.args.get("q", "").strip()
    results = db.search_notes(query) if query else []
    return render_template("search.html", query=query, results=results)


# ── Journal categories ─────────────────────────────────────────────────────────

@app.route("/journal")
def journal_view():
    categories = db.get_journal_categories()
    return render_template("journal.html", categories=categories)


def _parse_fields(form) -> list:
    labels       = form.getlist("field_label[]")
    placeholders = form.getlist("field_placeholder[]")
    types        = form.getlist("field_type[]")
    fields = []
    for i, label in enumerate(labels):
        if label.strip():
            fields.append({
                "label":       label.strip(),
                "placeholder": placeholders[i].strip() if i < len(placeholders) else "",
                "type":        types[i].strip() if i < len(types) else "text",
            })
    return fields


@app.route("/journal/add", methods=["POST"])
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
    return redirect(url_for("journal_view"))


@app.route("/journal/<int:cat_id>/edit", methods=["POST"])
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
    return redirect(url_for("journal_view"))


@app.route("/journal/<int:cat_id>/delete", methods=["POST"])
def journal_category_delete(cat_id):
    db.delete_journal_category(cat_id)
    return redirect(url_for("journal_view"))


# ── Journal entries ────────────────────────────────────────────────────────────

@app.route("/day/<date_str>/journal/add", methods=["POST"])
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
        return redirect(url_for("calendar_view", year=d.year, month=d.month))
    if next_page == "week":
        return redirect(url_for("week_view", date_str=date_str))
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/journal/<int:entry_id>/edit", methods=["POST"])
def journal_entry_edit(date_str, entry_id):
    values_json = request.form.get("values_json", "{}").strip() or "{}"
    tags        = request.form.get("tags", "").strip()
    db.update_journal_entry(entry_id, {"values_json": values_json, "tags": tags})
    return redirect(url_for("day_view", date_str=date_str))


@app.route("/day/<date_str>/journal/<int:entry_id>/delete", methods=["POST"])
def journal_entry_delete(date_str, entry_id):
    db.delete_journal_entry(entry_id)
    return redirect(url_for("day_view", date_str=date_str))


if __name__ == "__main__":
    import webbrowser, threading
    db.init_db()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False, port=5000)
