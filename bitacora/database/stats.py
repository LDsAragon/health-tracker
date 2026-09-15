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


# Cómo se junta lo de un mismo día cuando hay más de una nota. El gráfico automático dibujaba un
# punto POR NOTA: con dos bloques de trabajo el mismo día quedaban dos puntos sobre la misma fecha
# y la línea se leía como ruido —el caso se ve enseguida en `tools/datos_demo.py`—. Suma para lo
# que se acumula (el tiempo, las cantidades) y promedio para la escala, donde sumar del 1 al 5 no
# significaría nada. `grouped_series` ya juntaba por bucket: esto es lo que faltaba para que el
# camino automático y el del constructor digan lo mismo del mismo campo.
AGREGACION_DIARIA = {"duracion": "suma", "rango": "suma", "numero": "suma", "escala": "promedio"}


def _por_dia(pares, ftype):
    """[(fecha, valor)] con UN valor por fecha."""
    acum = {}
    for d, v in pares:
        acum.setdefault(d, []).append(v)
    out = []
    for d in sorted(acum):
        vals = acum[d]
        junto = sum(vals) / len(vals) if AGREGACION_DIARIA.get(ftype) == "promedio" else sum(vals)
        out.append((d, round(junto, 2) if isinstance(junto, float) else junto))
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
    for c in get_journal_categories(incluir_archivadas=True):
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


def build_series(cat_id, field_label, ftype, start, end):
    """Datos listos para Chart.js: {kind, labels, data}. Un valor POR DÍA (ver `_por_dia`)."""
    if ftype in NUMERIC_TYPES:
        s = _por_dia(numeric_series(cat_id, field_label, ftype, start, end), ftype)
        return {"kind": "line", "labels": [d for d, _ in s], "data": [v for _, v in s]}
    if ftype == "sino":
        c = bool_counts(cat_id, field_label, start, end)
        days = sorted(c)
        return {"kind": "bar", "labels": days, "data": [c[d] for d in days]}
    if ftype == "opciones":
        dist = option_distribution(cat_id, field_label, start, end)
        return {"kind": "bar", "labels": list(dist), "data": list(dist.values())}
    return {"kind": "line", "labels": [], "data": []}


# ── El resumen de lo que ya anotás ───────────────────────────────────────────

def resumen(start: str, end: str) -> dict:
    """Qué anotaste en el período, sin que haya que configurar nada.

    Es la respuesta al problema más grave de la pantalla: sin campos marcados con 📈 no mostraba
    **nada**, aunque hubieras anotado todos los días durante meses.

    Se arma con las funciones de rango que ya existen (`get_notes_range`,
    `get_todo_counts_range`, `get_journal_entries_range`): no hace falta SQL nuevo.
    """
    from .notes import get_notes_range
    from .todos import get_todo_counts_range

    notas = get_notes_range(start, end)
    tareas = get_todo_counts_range(start, end)
    especiales = get_journal_entries_range(start, end)

    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    dias = (d1 - d0).days + 1
    # "Un día con algo anotado" incluye cualquier cosa: una nota, una tarea o una nota especial.
    # Tildar una rutina no cuenta como anotar — es cumplir algo que ya estaba planeado.
    con_algo = set(notas) | set(especiales) | {d for d, c in tareas.items() if c["total"]}

    return {
        "dias": dias,
        "notas": sum(len(v) for v in notas.values()),
        "especiales": sum(len(v) for v in especiales.values()),
        "tareas_total": sum(c["total"] for c in tareas.values()),
        "tareas_hechas": sum(c["done"] for c in tareas.values()),
        "dias_con_algo": len(con_algo),
    }


def _periodo_anterior(start: str, end: str) -> tuple:
    """El período de igual largo que termina justo antes de `start`."""
    d0, d1 = date.fromisoformat(start), date.fromisoformat(end)
    largo = (d1 - d0).days + 1
    fin = d0 - timedelta(days=1)
    return (fin - timedelta(days=largo - 1)).isoformat(), fin.isoformat()


def resumen_comparado(start: str, end: str) -> dict:
    """El resumen del período + el del anterior de igual largo, con la diferencia de cada número.

    ⚠️ Un delta contra un período **sin datos** no es una mejora: si antes no usabas la app, un
    "▲ +23" es ruido que además se lee como un logro. Cuando el período anterior está vacío, el
    delta viaja como `None` y la pantalla muestra un guion.
    """
    actual = resumen(start, end)
    previo = resumen(*_periodo_anterior(start, end))
    hubo_antes = any(previo[k] for k in ("notas", "especiales", "tareas_total"))
    deltas = {k: (actual[k] - previo[k] if hubo_antes else None)
              for k in actual if k != "dias"}
    return {"actual": actual, "previo": previo, "deltas": deltas, "hubo_antes": hubo_antes}


# ── El tiempo por actividad ──────────────────────────────────────────────────

def _tiempo_por_actividad(start: str, end: str) -> dict:
    """{actividad: minutos} en el período.

    El uso central de Estadísticas: "le dediqué tantas horas a X, tantas a Y". Una clave por
    categoría con campos de tiempo (duración/rango, se suman); si la categoría tiene un campo
    `opciones`, una clave por opción ("Ejercicio · Correr").
    """
    info = {}
    for c in get_journal_categories(incluir_archivadas=True):
        tf = [(f["label"], f["type"]) for f in c.get("fields", []) if f.get("type") in TIME_TYPES]
        if tf:
            gf = next((f["label"] for f in c["fields"] if f.get("type") == "opciones"), "")
            info[c["id"]] = (c["name"], tf, gf)
    if not info:
        return {}

    rows = {}
    for _d, lst in get_journal_entries_range(start, end).items():
        for e in lst:
            meta = info.get(e["category_id"])
            if not meta:
                continue
            name, tf, gf = meta
            vals = [_parse_numeric(ft, e["values"].get(l)) for l, ft in tf]
            vals = [v for v in vals if v is not None]
            if not vals:
                continue
            g = (e["values"].get(gf) or "").strip() if gf else ""
            clave = f"{name} · {g}" if g else name
            rows[clave] = rows.get(clave, 0) + sum(vals)
    return rows


def tiempo_comparado(start: str, end: str) -> list:
    """[{name, minutos, previo, delta}] del período, de más tiempo a menos.

    ⚠️ Antes esto eran tres ventanas fijas —esta semana / este mes / últimos 3 meses— **ignorando
    el selector de rango de la pantalla**, que era la segunda noción de rango del lado del tiempo.
    Ahora la tabla habla del período elegido y trae la comparación, que es lo que hace que un
    número de horas signifique algo. El delta es `None` si no hay período anterior con qué
    comparar, igual que en `resumen_comparado`.
    """
    ahora = _tiempo_por_actividad(start, end)
    previo = _tiempo_por_actividad(*_periodo_anterior(start, end))
    return [{"name": k, "minutos": v, "previo": previo.get(k, 0),
             "delta": (v - previo.get(k, 0)) if previo else None}
            for k, v in sorted(ahora.items(), key=lambda kv: (-kv[1], kv[0]))]

# ── La rueda de emociones ────────────────────────────────────────────────────

def _emociones_de(raw) -> list:
    """[(rueda, base)] de un valor de rueda. `""` si no hay nada.

    El campo guarda texto: `"Alegre > Contento"`, varias separadas por `" | "`, y las de la rueda
    de Ekman con el prefijo `ek::`. Se cuenta por **emoción base** —el primer nivel— que es la
    que tiene color y la que se entiende de un vistazo; los niveles de abajo son matices y
    contarlos por separado dispersaría todo en frecuencia 1.
    """
    out = []
    for trozo in (raw or "").split("|"):
        emo = trozo.strip()
        if not emo:
            continue
        rueda = "ekman" if emo.startswith("ek::") else "willcox"
        base = (emo[4:] if rueda == "ekman" else emo).split(" > ")[0].strip()
        if base:
            out.append((rueda, base))
    return out


def emociones_frecuentes(start: str, end: str) -> dict:
    """{rueda: [{emocion, veces}]} + en cuántos días se registró alguna.

    Es la feature más rica de la app y Estadísticas no la miraba.
    """
    cats = get_journal_categories(incluir_archivadas=True)
    campos = {c["id"]: [f["label"] for f in c.get("fields", [])
                        if f.get("type") == "emotion-wheel"]
              for c in cats}
    campos = {k: v for k, v in campos.items() if v}
    if not campos:
        return {"ruedas": {}, "dias": 0}

    conteo = {"willcox": {}, "ekman": {}}
    dias = set()
    for d_str, lst in get_journal_entries_range(start, end).items():
        for e in lst:
            for label in campos.get(e["category_id"], ()):
                for rueda, base in _emociones_de(e["values"].get(label)):
                    conteo[rueda][base] = conteo[rueda].get(base, 0) + 1
                    dias.add(d_str)

    ruedas = {r: [{"emocion": k, "veces": v}
                  for k, v in sorted(c.items(), key=lambda kv: (-kv[1], kv[0]))]
              for r, c in conteo.items() if c}
    return {"ruedas": ruedas, "dias": len(dias)}
