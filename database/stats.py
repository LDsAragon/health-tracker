"""Series para Estadísticas a partir de las entradas de notas especiales.
Funciones testeables; el shaping para Chart.js queda en build_series()."""
from .journal import get_journal_categories, get_journal_entries_range

NUMERIC_TYPES = ("numero", "escala", "duracion", "rango")


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
