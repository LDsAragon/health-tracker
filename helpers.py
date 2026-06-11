"""Helpers de request/ajustes y de inicio de semana. Sin dependencias de las rutas."""
from datetime import timedelta
from flask import g

_DOW_MON = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']


def _setting(key, default=''):
    """Lee un ajuste de g.settings (cargado en before_request); default fuera de contexto."""
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
def _first_weekday():
    return 6 if _setting('week_start', 'mon') == 'sun' else 0   # 0=lunes, 6=domingo


def _week_start(d):
    fw = _first_weekday()
    return d - timedelta(days=(d.weekday() - fw) % 7)


def _dow_names():
    fw = _first_weekday()
    return _DOW_MON[fw:] + _DOW_MON[:fw]


def safe_back(url, fallback=None):
    """Valida que `url` sea una ruta interna relativa (evita open-redirect).

    Devuelve la URL saneada o `fallback` si no es interna. `request.full_path`
    agrega un '?' final cuando no hay query: lo limpiamos.
    """
    if url and url.startswith('/') and not url.startswith('//'):
        return url[:-1] if url.endswith('?') else url
    return fallback
