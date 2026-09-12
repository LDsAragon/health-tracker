"""Series para Estadísticas a partir de las entradas de notas especiales.
Funciones testeables; el shaping para Chart.js queda en build_series()/grouped_series()."""
from datetime import date, timedelta

from .journal import get_journal_categories, get_journal_entries_range
from .settings import get_setting

NUMERIC_TYPES = ("numero", "escala", "duracion", "rango")
TIME_TYPES = ("duracion", "rango")   # se miden en minutos


def _parse_numeric(ftype, raw):
    """Valor numérico de un campo según su tipo (None si vacío/inválido).
    numero→float · escala→int · duracion→min · rango→min (cruce de medianoche)."""
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        if ftype == "numero":
            return float(raw)
        if ftype in ("escala", "duracion"):
            return int(raw)
        if ftype == "rango":
            a, b = raw.split("-", 1)
            ah, am = (int(x) for x in a.split(":"))
            bh, bm = (int(x) for x in b.split(":"))
            return ((bh * 60 + bm) - (ah * 60 + am)) % 1440
    except (ValueError, TypeError):
        return None
    return None


def numeric_series(cat_id, field_label, ftype, start, end):
    """[(date_str, valor)] ordenado por fecha, para un campo numérico de una categoría."""
    entries = get_journal_entries_range(start, end)
    out = []
    for d_str in sorted(entries):
        for e in entries[d_str]:
            if e["category_id"] == cat_id:
                v = _parse_numeric(ftype, e["values"].get(field_label))
                if v is not None:
                    out.append((d_str, v))
    return out


def bool_counts(cat_id, field_label, start, end):
    """{date_str: conteo de 'sí' (valor '1')} por día."""
    entries = get_journal_entries_range(start, end)
    out = {}
    for d_str, lst in entries.items():
        c = sum(1 for e in lst if e["category_id"] == cat_id and e["values"].get(field_label) == "1")
        if c:
            out[d_str] = c
    return out


def option_distribution(cat_id, field_label, start, end):
    """{opción: conteo} sobre el rango."""
    entries = get_journal_entries_range(start, end)
    dist = {}
    for lst in entries.values():
        for e in lst:
            if e["category_id"] == cat_id:
                v = (e["values"].get(field_label) or "").strip()
                if v:
                    dist[v] = dist.get(v, 0) + 1
    return dist


def chartable_fields():
    """Campos marcados con 'graficar' (chart=true) en alguna categoría."""
    out = []
    for c in get_journal_categories():
        for f in c.get("fields", []):
            if f.get("chart"):
                out.append({
                    "category_id": c["id"], "category_name": c["name"],
                    "label": f["label"], "type": f.get("type", "text"),
                })
    return out


def _bucket_key(d_str, bucket, first_weekday):
    """Clave de agrupación temporal: día (ISO), semana (ISO del 1er día) o mes (aaaa-mm)."""
    if bucket == "month":
        return d_str[:7]
    if bucket == "week":
        d = date.fromisoformat(d_str)
        return (d - timedelta(days=(d.weekday() - first_weekday) % 7)).isoformat()
    return d_str


def _entry_tags(e):
    return {t.strip().lower() for t in (e.get("tags") or "").split(",") if t.strip()}


def grouped_series(cat_id, value_fields, group_label, start, end, bucket="day", tag_filter=""):
    """Serie agregada para Chart.js apilado + totales.

    value_fields: [(label, ftype)] — el valor de una entrada es la SUMA de esos
    campos (permite mezclar duración y rango: ambos → minutos). group_label:
    campo `opciones` que separa los grupos (vacío → un solo grupo "Total").
    bucket: day|week|month (la semana respeta el ajuste week_start).
    tag_filter: si se da, solo cuentan entradas con esa etiqueta.

    Devuelve {kind, labels, datasets: [{label, data}], totals: {grupo: suma},
    time_based: True si todos los campos son de tiempo (minutos)}.
    """
    fw = 6 if get_setting("week_start", "mon") == "sun" else 0
    tag = (tag_filter or "").strip().lower()
    entries = get_journal_entries_range(start, end)

    groups = {}     # grupo -> {bucket_key: suma}
    buckets = set()
    for d_str, lst in entries.items():
        for e in lst:
            if e["category_id"] != cat_id:
                continue
            if tag and tag not in _entry_tags(e):
                continue
            v, has = 0, False
            for label, ftype in value_fields:
                pv = _parse_numeric(ftype, e["values"].get(label))
                if pv is not None:
                    v, has = v + pv, True
            if not has:
                continue
            g = ((e["values"].get(group_label) or "").strip() or "Sin asignar") if group_label else "Total"
            b = _bucket_key(d_str, bucket, fw)
            buckets.add(b)
            gb = groups.setdefault(g, {})
            gb[b] = gb.get(b, 0) + v

    labels = sorted(buckets)
    return {
        "kind": "stacked",
        "labels": labels,
        "datasets": [{"label": g, "data": [groups[g].get(b, 0) for b in labels]}
                     for g in sorted(groups)],
        "totals": {g: sum(gb.values()) for g, gb in groups.items()},
        "time_based": bool(value_fields) and all(ft in TIME_TYPES for _, ft in value_fields),
    }


def time_summary(today=None):
    """Horas por actividad: esta semana / este mes / últimos 90 días.

    El uso central de Estadísticas: "trabajé tantas horas en X, tantas en Y".
    Una fila por categoría con campos de tiempo (duración/rango, se suman);
    si la categoría tiene un campo `opciones`, una fila por opción
    ("Ejercicio · Correr"). Valores en minutos; orden: más tiempo en 90 días.
    """
    today = today or date.today()
    fw = 6 if get_setting("week_start", "mon") == "sun" else 0
    week_start = today - timedelta(days=(today.weekday() - fw) % 7)
    month_start = today.replace(day=1)
    quarter_start = today - timedelta(days=89)
    start = min(week_start, month_start, quarter_start)

    info = {}
    for c in get_journal_categories():
        tf = [(f["label"], f["type"]) for f in c.get("fields", []) if f.get("type") in TIME_TYPES]
        if tf:
            gf = next((f["label"] for f in c["fields"] if f.get("type") == "opciones"), "")
            info[c["id"]] = (c["name"], tf, gf)
    if not info:
        return []

    rows = {}
    entries = get_journal_entries_range(start.isoformat(), today.isoformat())
    for d_str, lst in entries.items():
        d = date.fromisoformat(d_str)
        for e in lst:
            meta = info.get(e["category_id"])
            if not meta:
                continue
            name, tf, gf = meta
            vals = [_parse_numeric(ft, e["values"].get(l)) for l, ft in tf]
            vals = [v for v in vals if v is not None]
            if not vals:
                continue
            v = sum(vals)
            g = (e["values"].get(gf) or "").strip() if gf else ""
            r = rows.setdefault(f"{name} · {g}" if g else name, [0, 0, 0])
            if d >= week_start:
                r[0] += v
            if d >= month_start:
                r[1] += v
            r[2] += v
    return [{"name": k, "week": r[0], "month": r[1], "quarter": r[2]}
            for k, r in sorted(rows.items(), key=lambda kv: -kv[1][2])]


def build_series(cat_id, field_label, ftype, start, end):
    """Datos listos para Chart.js: {kind, labels, data}."""
    if ftype in NUMERIC_TYPES:
        s = numeric_series(cat_id, field_label, ftype, start, end)
        return {"kind": "line", "labels": [d for d, _ in s], "data": [v for _, v in s]}
    if ftype == "sino":
        c = bool_counts(cat_id, field_label, start, end)
        days = sorted(c)
        return {"kind": "bar", "labels": days, "data": [c[d] for d in days]}
    if ftype == "opciones":
        dist = option_distribution(cat_id, field_label, start, end)
        return {"kind": "bar", "labels": list(dist), "data": list(dist.values())}
    return {"kind": "line", "labels": [], "data": []}
