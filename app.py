from flask import Flask, render_template, request, redirect, url_for, make_response, send_file
from datetime import date, datetime
import calendar as cal
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
            return f"hoy {dt.strftime('%H:%M')}"
        if delta == 1:
            return f"ayer {dt.strftime('%H:%M')}"
        return dt.strftime('%d/%m/%Y')
    except Exception:
        return ''


@app.before_request
def setup():
    db.init_db()


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
            for ev in recurring if db.event_applies(ev, d)
        ]

    prev_month = month - 1 if month > 1 else 12
    prev_year  = year if month > 1 else year - 1
    next_month = month % 12 + 1
    next_year  = year if month < 12 else year + 1

    return render_template(
        "calendar.html",
        year=year, month=month,
        month_name=cal.month_name[month],
        weeks=cal.monthcalendar(year, month),
        notes_by_date=notes_by_date,
        events_by_date=events_by_date,
        today=today.isoformat(),
        prev_year=prev_year, prev_month=prev_month,
        next_year=next_year, next_month=next_month,
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

    from datetime import timedelta
    prev_day = (d - timedelta(days=1)).isoformat()
    next_day = (d + timedelta(days=1)).isoformat()

    return render_template(
        "day.html",
        date_str=date_str,
        d=d,
        notes=notes,
        day_events=day_events,
        prev_day=prev_day,
        next_day=next_day,
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
    if rtype == "daily":
        recurrence = "daily"
    elif rtype == "weekly":
        days = request.form.getlist("weekdays")
        recurrence = "weekly:" + ",".join(sorted(days)) if days else "daily"
    else:
        n = int(request.form.get("interval_days", 2))
        recurrence = f"every:{n}"

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
    if rtype == "daily":
        recurrence = "daily"
    elif rtype == "weekly":
        days = request.form.getlist("weekdays")
        recurrence = "weekly:" + ",".join(sorted(days)) if days else "daily"
    else:
        n = int(request.form.get("interval_days", 2))
        recurrence = f"every:{n}"
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
    db.delete_recurring_event(event_id)
    return redirect(url_for("recurring_view"))


# ── Week view ──────────────────────────────────────────────────────────────────

@app.route("/week/<date_str>")
def week_view(date_str):
    from datetime import timedelta
    today      = date.today()
    anchor     = date.fromisoformat(date_str)
    monday     = anchor - timedelta(days=anchor.weekday())
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
            for ev in recurring if db.event_applies(ev, d)
        ]

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
    )


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


if __name__ == "__main__":
    import webbrowser, threading
    db.init_db()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False, port=5000)
