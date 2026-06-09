from flask import Flask, render_template, request, redirect, url_for
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
            {**ev, "done": ev["id"] in day_done, "completion_note": day_done.get(ev["id"], "")}
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
        {**ev, "done": ev["id"] in done, "completion_note": done.get(ev["id"], "")}
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
    if request.form.get("next") == "calendar":
        d = date.fromisoformat(date_str)
        return redirect(url_for("calendar_view", year=d.year, month=d.month))
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


@app.route("/day/<date_str>/event/<int:event_id>/uncomplete", methods=["POST"])
def event_uncomplete(date_str, event_id):
    db.uncomplete_event(event_id, date_str)
    return redirect(url_for("day_view", date_str=date_str))


# ── Recurring events ───────────────────────────────────────────────────────────

@app.route("/recurring")
def recurring_view():
    return render_template("recurring.html", events=db.get_recurring_events())


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
            "title": title,
            "color": request.form.get("color", "#6366f1"),
            "recurrence": recurrence,
            "start_date": request.form.get("start_date", date.today().isoformat()),
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
            "title": title,
            "color": request.form.get("color", "#6366f1"),
            "recurrence": recurrence,
            "start_date": request.form.get("start_date", date.today().isoformat()),
        })
    return redirect(url_for("recurring_view"))


@app.route("/recurring/<int:event_id>/delete", methods=["POST"])
def recurring_delete(event_id):
    db.delete_recurring_event(event_id)
    return redirect(url_for("recurring_view"))


if __name__ == "__main__":
    import webbrowser, threading
    db.init_db()
    threading.Timer(1.0, lambda: webbrowser.open("http://127.0.0.1:5000")).start()
    app.run(debug=False, port=5000)
