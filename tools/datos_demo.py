"""Datos inventados para VER la pantalla de Estadísticas: una forma de gráfico por tipo de campo.

No es un fixture de tests —los tests fijan números, esto es para mirar—. `servidor_prueba.py
--demo` lo siembra en su base temporal, así se puede recorrer la pantalla con datos que ejercitan
las cuatro formas de serie que sabe armar `build_series()` más las que arma el constructor
(`grouped_series`). Sirve para responder de un vistazo "¿qué se grafica si tildo esto?".

Qué tipo produce qué:
    numero, escala, duracion, rango  → línea por día (los de tiempo, en horas)
    sino                             → barras: cuántos "sí" por día
    opciones                         → barras: cuántas veces cada opción en el período
    text, emotion-wheel              → nada, y por eso no se les ofrece el tilde
"""
import json
import random
from datetime import date, timedelta

DIAS = 45                       # un mes y medio: alcanza para ver tendencia por semana y por mes
PROYECTOS = ["ClienteA", "ClienteB", "Proyecto propio"]


def _fechas(dias=DIAS):
    hoy = date.today()
    return [(hoy - timedelta(days=n)) for n in range(dias, -1, -1)]


def sembrar(db):
    """Llena la base con categorías, entradas y gráficos guardados. `db` es bitacora.database."""
    r = random.Random(7)          # fijo: dos corridas muestran lo mismo y se pueden comparar

    # ── Trabajo: opciones + los dos tipos de tiempo ──────────────────────────
    db.add_journal_category({
        "name": "Trabajo", "color": "#14b8a6", "show_in_calendar": 1,
        "fields_json": json.dumps([
            {"label": "Proyecto", "type": "opciones", "chart": True,
             "placeholder": ", ".join(PROYECTOS)},
            {"label": "Franja", "type": "rango",    "chart": True},
            {"label": "Horas",  "type": "duracion", "chart": True},
            {"label": "Notas",  "type": "text", "placeholder": "en qué trabajé..."},
        ]),
    })
    # ── Cuerpo: número, escala y sí/no ──────────────────────────────────────
    db.add_journal_category({
        "name": "Cuerpo", "color": "#f97316", "show_in_calendar": 1,
        "fields_json": json.dumps([
            {"label": "Peso",      "type": "numero", "chart": True, "placeholder": "kg"},
            {"label": "Ánimo",     "type": "escala", "chart": True,
             "placeholder": "Muy mal, Mal, Normal, Bien, Muy bien"},
            {"label": "¿Entrené?", "type": "sino",   "chart": True},
        ]),
    })
    cats = {c["name"]: c["id"] for c in db.get_journal_categories()}

    peso = 79.4
    for d in _fechas():
        iso = d.isoformat()
        laborable = d.weekday() < 5

        if laborable:
            for _ in range(r.choice([1, 1, 1, 2])):        # a veces dos bloques en el día
                ini = r.choice([8, 9, 9, 10, 14])
                largo = r.choice([90, 120, 150, 180, 240])
                fin = (ini * 60 + largo) % 1440
                db.add_journal_entry({
                    "category_id": cats["Trabajo"], "entry_date": iso, "tags": "",
                    "values_json": json.dumps({
                        "Proyecto": r.choice(PROYECTOS),
                        "Franja": f"{ini:02d}:00-{fin // 60:02d}:{fin % 60:02d}",
                        "Horas": str(largo),
                        "Notas": r.choice(["revisión de PRs", "reunión + seguimiento",
                                           "arreglé el reporte mensual", ""]),
                    }, ensure_ascii=False),
                })

        if r.random() < 0.85:                              # algún día sin registrar, como en la vida
            peso = round(peso + r.uniform(-0.35, 0.3), 1)
            db.add_journal_entry({
                "category_id": cats["Cuerpo"], "entry_date": iso, "tags": "",
                "values_json": json.dumps({
                    "Peso": str(peso),
                    "Ánimo": str(r.choice([2, 3, 3, 4, 4, 5])),
                    "¿Entrené?": "1" if (laborable and r.random() < 0.55) else "0",
                }, ensure_ascii=False),
            })

        if r.random() < 0.5:
            db.add_note(iso, r.choice(["día tranquilo", "dormí mal", "salí a caminar",
                                       "llamada larga con mamá"]),
                        r.choice(["", "#6366f1", "#22c55e"]))
        if laborable and r.random() < 0.6:
            db.add_todo(iso, r.choice(["mandar la factura", "comprar café",
                                       "contestar el mail de ClienteB"]))

    # ── Rutinas, para que la adherencia tampoco esté vacía ───────────────────
    db.add_recurring_event({"title": "Caminar 30 min", "color": "#22c55e", "recurrence": "daily",
                            "start_date": _fechas()[0].isoformat(), "end_date": ""})
    db.add_recurring_event({"title": "Leer", "color": "#a855f7", "recurrence": "daily",
                            "start_date": _fechas()[0].isoformat(), "end_date": ""})
    for ev in db.get_recurring_events():
        for d in _fechas():
            if r.random() < 0.6:
                db.complete_event(ev["id"], d.isoformat())

    # ── Gráficos del constructor: lo que el tilde NO puede armar ─────────────
    # Apilado por opción y por semana, sumando los dos campos de tiempo (ambos son minutos).
    db.add_chart(cats["Trabajo"], "Horas|Franja", "Horas por cliente, por semana",
                 group_field="Proyecto", bucket="week")
    # Un solo campo agrupado por mes: la otra forma que el tilde no da. Va un campo de tiempo
    # porque el bucket SUMA lo del período, y sumar una escala del 1 al 5 no significaría nada.
    db.add_chart(cats["Trabajo"], "Horas", "Horas trabajadas por mes", bucket="month")


def resumen() -> str:
    return (
        "Datos de ejemplo sembrados. En Estadísticas tendrías que ver:\n"
        "  automáticos (el tilde En Estadísticas)\n"
        "    Trabajo · Proyecto   barras con cuántas veces cada cliente\n"
        "    Trabajo · Franja     línea de horas por día (rango horario)\n"
        "    Trabajo · Horas      línea de horas por día (duración)\n"
        "    Cuerpo · Peso        línea de kg por día\n"
        "    Cuerpo · Ánimo       línea de 1 a 5 por día\n"
        "    Cuerpo · ¿Entrené?   barras con los días que sí\n"
        "  del constructor\n"
        "    Horas por cliente, por semana   barras apiladas + tabla de totales\n"
        "    Horas trabajadas por mes        barras por mes"
    )
