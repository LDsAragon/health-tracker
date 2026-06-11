"""Filtros Jinja de formato (fecha/hora/duración/rango). Registrados por register(app)."""
from datetime import date, datetime
from helpers import _fmt_clock


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


def fechacorta_filter(s):
    """'2026-06-10' → '10/06/2026' (formato local, sin ISO/anglicismo)."""
    if not s:
        return ''
    try:
        return date.fromisoformat(s).strftime('%d/%m/%Y')
    except (ValueError, TypeError):
        return s


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


def register(app):
    app.template_filter('humantime')(humantime_filter)
    app.template_filter('fechacorta')(fechacorta_filter)
    app.template_filter('dur_fmt')(dur_fmt_filter)
    app.template_filter('rango_fmt')(rango_fmt_filter)
