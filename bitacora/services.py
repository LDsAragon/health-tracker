"""Lógica de presentación reutilizable entre vistas (calendario/semana).
Funciones puras y testeables sin HTTP."""
from datetime import date, timedelta

from bitacora import database as db


def events_by_date(recurring, completions, dates):
    """{date_str: [evento decorado con done/skipped/completion_note]} para cada fecha.
    Filtra los ocultos del calendario (show_in_calendar) y los que no aplican ese día."""
    out = {}
    for d in dates:
        d_str = d.isoformat()
        done = completions.get(d_str, {})
        out[d_str] = [
            {
                **ev,
                "done":    ev["id"] in done and done[ev["id"]]["status"] == "done",
                "skipped": ev["id"] in done and done[ev["id"]]["status"] == "skipped",
                "completion_note": done.get(ev["id"], {}).get("note", ""),
            }
            for ev in recurring
            if ev.get("show_in_calendar", 1) and db.event_applies(ev, d)
        ]
    return out


def journal_badges(journal_raw):
    """{date_str: [{name,color}]} — una badge por categoría (con show_in_calendar) por día."""
    out = {}
    for ds, entries in journal_raw.items():
        seen, badges = set(), []
        for e in entries:
            if e["show_in_calendar"] and e["category_id"] not in seen:
                seen.add(e["category_id"])
                badges.append({"name": e["category_name"], "color": e["category_color"]})
        if badges:
            out[ds] = badges
    return out


# --- Visor de tareas ---

_BUCKET_LABELS = (
    ("esta_semana",   "Esta semana"),
    ("semana_pasada", "La semana pasada"),
    ("antes",         "Más viejas"),
)


def _as_date(iso):
    """None si el texto no es una fecha ISO: todo_date no se valida al guardar."""
    try:
        return date.fromisoformat(iso)
    except (ValueError, TypeError):
        return None


def overdue_buckets(todos, today, week_start):
    """Agrupa las tareas atrasadas por antigüedad: [{key, label, tareas}], sin tramos vacíos.
    `week_start` es el callable de helpers, para no acoplar esto al ajuste week_start."""
    this_week = week_start(today)
    last_week = this_week - timedelta(days=7)
    groups = {key: [] for key, _ in _BUCKET_LABELS}
    for t in todos:
        d = _as_date(t["todo_date"])
        if d is None:
            continue
        key = "esta_semana" if d >= this_week else "semana_pasada" if d >= last_week else "antes"
        groups[key].append(t)
    # La clave no puede ser "items": en Jinja `b.items` resuelve al método del dict.
    return [{"key": k, "label": lbl, "tareas": groups[k]} for k, lbl in _BUCKET_LABELS if groups[k]]


def overdue_cutoff(today, mode, week_start):
    """Fecha exclusiva del corte: `week` deja pasar lo de la semana en curso, `day` solo hoy."""
    return week_start(today) if mode == "week" else today


def periodo_ventana(periodo, today):
    """(start, end) ISO inclusivos del período; None = sin cota.

    La ventana es exacta a propósito: el botón tiene que listar exactamente lo que dice, así
    que salvo "proximas" y "todo" ninguna incluye fechas futuras.
    """
    if periodo == "todo":
        return None, None
    if periodo == "proximas":
        return (today + timedelta(days=1)).isoformat(), None
    dias = 1 if periodo == "hoy" else int(periodo)
    return (today - timedelta(days=dias - 1)).isoformat(), today.isoformat()


def color_para_nota_nueva(elegido: str) -> str:
    """Color con el que se guarda una nota rápida nueva.

    Lo que elegiste a mano siempre gana. Si no elegiste nada, decide el ajuste `nota_color`:
    vacío deja la nota sin color (el comportamiento de siempre), `aleatorio` sortea uno de
    `NOTE_COLORS`, y cualquier otro valor es un color fijo.

    ⚠️ "No elegí color" llega como **string vacío, no como ausente**: los formularios del día y
    del calendario siempre mandan el campo `color`, con el radio de "sin color" (`value=""`)
    marcado por default. Por eso la condición es sobre el contenido y no sobre la presencia.
    """
    if elegido:
        return elegido
    return color_sugerido(db.get_setting("nota_color", ""))


def color_sugerido(ajuste: str) -> str:
    """Con qué color se va a guardar una nota si no elegís ninguno.

    Sale aparte de `color_para_nota_nueva` porque los formularios de alta lo necesitan **antes**
    de guardar, para dejar marcado ese color y que lo veas: con `aleatorio` el color se decidía
    recién al insertar y la nota aparecía pintada de un color que nunca habías visto.

    ⚠️ Con `aleatorio` sortea en cada llamada, así que el que se muestra es el que se manda: los
    formularios envían el color marcado y `color_para_nota_nueva` respeta lo que le llega. Si en
    vez de eso se mandara vacío, el servidor sortearía **otro** y la previsualización mentiría.
    """
    import random

    from bitacora.appconfig import NOTE_COLORS

    if ajuste == "aleatorio":
        return random.choice(NOTE_COLORS)
    return ajuste if ajuste in NOTE_COLORS else ""


# ── Cumpleaños: el año de nacimiento ─────────────────────────────────────────

def anio_de_nacimiento(anio_txt: str, edad_txt: str, hoy) -> int | None:
    """Se guarda el AÑO, pero se puede cargar la edad. Devuelve None si no se sabe ninguno.

    El año es el dato canónico porque no se desactualiza; la edad es el atajo para el caso
    real que planteó el usuario: *"sé que la persona cumple 34 pero no quiero ir a preguntarle
    la fecha de nacimiento"*. Si vienen los dos, manda el año — es el dato exacto.

    ⚠️ La edad se lee como "los que cumple ESTE año", no como "los que tiene hoy". Así el
    resultado no depende de si el cumpleaños ya pasó o no, que es justo lo que haría que el
    mismo número diera dos años distintos según el día en que lo cargaste.
    """
    anio_txt, edad_txt = (anio_txt or "").strip(), (edad_txt or "").strip()
    if anio_txt:
        try:
            anio = int(anio_txt)
        except ValueError:
            return None
        return anio if 1900 <= anio <= hoy.year else None
    if edad_txt:
        try:
            edad = int(edad_txt)
        except ValueError:
            return None
        return hoy.year - edad if 0 <= edad <= 130 else None
    return None


def edad_en(birth_year, anio: int):
    """Los años que cumple en `anio`, o None si no se guardó el año de nacimiento."""
    return anio - birth_year if birth_year else None


# ── Rutinas guardadas con una frecuencia que se corre ────────────────────────

def _corrimiento(start, anio: int, cada: int) -> int:
    """Cuántos días corrió ya respecto de su fecha original, en `anio`. Negativo = se adelantó."""
    from datetime import date as _date, timedelta

    d = start
    while d.year < anio:
        d += timedelta(days=cada)
    try:
        original = _date(anio, start.month, start.day)
    except ValueError:                      # 29 de febrero en un año no bisiesto
        original = _date(anio, start.month, 28)
    return (d - original).days


def sugerencias_de_arreglo(events, hoy) -> list:
    """Rutinas modeladas como "cada ~365 días", que es lo que hace que la fecha se corra.

    ⚠️ La detección es **explícita y acotada** —`every:N` con N entre 360 y 366— y no mira nunca
    el contenido para adivinar intenciones. Nada se reescribe acá: esto solo arma lo que la
    pantalla le va a **ofrecer** al usuario, que decide con un clic. Es la misma regla que los
    renombres de campos.

    El grupo de cumpleaños solo se sugiere si el título lo dice: un "cada 365 días" puede ser
    perfectamente un chequeo médico, y meterlo en Cumpleaños sería inventar.
    """
    from datetime import date as _date

    out = []
    for ev in events:
        rec = ev.get("recurrence", "")
        if not rec.startswith("every:"):
            continue
        try:
            n = int(rec.split(":")[1])
        except (IndexError, ValueError):
            continue
        if not 360 <= n <= 366:
            continue
        start = _date.fromisoformat(ev["start_date"])
        out.append({
            "ev": ev,
            "dias": n,
            "corrido": _corrimiento(start, hoy.year, n),
            "parece_cumple": "cumple" in (ev.get("title") or "").lower(),
        })
    return out
