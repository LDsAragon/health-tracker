"""Rutinas vs. recordatorios: la frecuencia anual, los grupos y qué entra en la adherencia.

La distinción que ordena todo: **una rutina se mide, un recordatorio avisa**. De ahí salen las dos
reglas que fijan estos tests — los recordatorios no tienen porcentaje, y lo anual se repite por
mes-día y no por días transcurridos.
"""
from datetime import date

import pytest

from bitacora import database as db


def _cumple(fecha="1992-05-05", **extra):
    """Un cumpleaños como lo crea la app: recordatorio, anual, en el grupo de fábrica."""
    grupo = [g for g in db.get_event_groups() if g["especial"] == "cumpleanos"][0]
    datos = {"title": "Cumple de Pablo", "color": "#ec4899", "recurrence": "yearly",
             "start_date": fecha, "tipo": "recordatorio", "group_id": grupo["id"]}
    datos.update(extra)
    db.add_recurring_event(datos)
    return db.get_recurring_events()[-1]


# ── La frecuencia anual ──────────────────────────────────────────────────────

def test_lo_anual_cae_siempre_el_mismo_dia(test_db):
    """⚠️ La razón de existir de `yearly`.

    Un cumpleaños se venía modelando como `every:364`, y 364 no es un año: se corre un día por
    año. El "Cumple del pablo" del 5 de mayo de 2023 ya caía el 1 de mayo en 2026, el 26 de abril
    en 2030, y para 2078 en febrero.
    """
    ev = _cumple("1992-05-05")
    for anio in (2026, 2027, 2028, 2050, 2078):
        assert db.event_applies(ev, date(anio, 5, 5)), f"{anio} no cae el 5 de mayo"
        assert not db.event_applies(ev, date(anio, 5, 4))
        assert not db.event_applies(ev, date(anio, 5, 6))


def test_el_viejo_every_364_si_se_corre(test_db):
    """El contraste, para que quede claro qué se arregló y no vuelva como 'optimización'."""
    db.add_recurring_event({"title": "a la vieja usanza", "color": "#6366f1",
                            "recurrence": "every:364", "start_date": "2023-05-05"})
    ev = db.get_recurring_events()[-1]
    assert not db.event_applies(ev, date(2026, 5, 5))
    assert db.event_applies(ev, date(2026, 5, 1))        # cuatro días corrido


def test_lo_anual_no_empieza_antes_de_su_fecha(test_db):
    ev = _cumple("1992-05-05")
    assert not db.event_applies(ev, date(1991, 5, 5))


def test_lo_anual_respeta_el_fin(test_db):
    ev = _cumple("1992-05-05", end_date="2030-12-31")
    assert db.event_applies(ev, date(2030, 5, 5))
    assert not db.event_applies(ev, date(2031, 5, 5))


def test_el_29_de_febrero_se_festeja_el_28(test_db):
    """Desaparecer tres de cada cuatro años es peor que correrlo un día."""
    ev = _cumple("2000-02-29")
    assert db.event_applies(ev, date(2028, 2, 29))       # bisiesto: su día
    assert not db.event_applies(ev, date(2028, 2, 28))
    assert db.event_applies(ev, date(2027, 2, 28))       # no bisiesto: el 28
    assert not db.event_applies(ev, date(2027, 3, 1))


@pytest.mark.parametrize("anio,bisiesto", [(2024, True), (2027, False), (2000, True),
                                           (1900, False), (2100, False)])
def test_la_regla_de_los_bisiestos_contempla_los_siglos(anio, bisiesto):
    """1900 y 2100 NO son bisiestos aunque sean múltiplos de 4; 2000 sí."""
    from bitacora.database.events import _bisiesto
    assert _bisiesto(anio) is bisiesto


def test_un_29_de_febrero_lejano_cae_bien_en_un_siglo_no_bisiesto(test_db):
    """2100 no es bisiesto, así que ese año el cumpleaños cae el 28."""
    ev = _cumple("2000-02-29")
    assert db.event_applies(ev, date(2100, 2, 28))
    assert not db.event_applies(ev, date(2100, 3, 1))


# ── La adherencia es solo de las rutinas ─────────────────────────────────────

def test_un_recordatorio_no_tiene_porcentaje(test_db):
    """⚠️ "12 de 15 · 80%" sobre un cumpleaños no significa nada: el de Pablo arrastraba un 0%."""
    ev = _cumple(date.today().replace(year=1992).isoformat())
    stats = db.get_completion_stats(db.get_recurring_events())
    assert stats[ev["id"]]["applicable"] == 0


def test_una_rutina_sigue_teniendo_porcentaje(test_db):
    db.add_recurring_event({"title": "Caminadora", "color": "#6366f1", "recurrence": "daily",
                            "start_date": "2020-01-01"})
    ev = db.get_recurring_events()[-1]
    db.complete_event(ev["id"], date.today().isoformat())
    stats = db.get_completion_stats(db.get_recurring_events())
    assert stats[ev["id"]]["applicable"] == 30
    assert stats[ev["id"]]["done"] == 1


def test_un_recordatorio_igual_se_puede_tildar(test_db):
    """Se tilda —"saludé a mi amigo"— aunque no cuente para ningún porcentaje."""
    ev = _cumple()
    db.complete_event(ev["id"], "2026-05-05")
    assert db.get_completion(ev["id"], "2026-05-05")["status"] == "done"


# ── Los avisos con antelación ────────────────────────────────────────────────

def test_avisa_con_la_antelacion_que_le_pusiste(test_db):
    _cumple("1992-05-05", aviso_dias=7)
    eventos = db.get_recurring_events()
    assert len(db.avisos_proximos(eventos, date(2026, 4, 30))) == 1   # faltan 5
    assert db.avisos_proximos(eventos, date(2026, 4, 30))[0]["faltan"] == 5
    assert db.avisos_proximos(eventos, date(2026, 4, 20)) == []       # faltan 15


def test_el_dia_que_cae_no_es_un_aviso(test_db):
    """Ese ya aparece por el camino normal; avisarlo otra vez sería mostrarlo dos veces."""
    _cumple("1992-05-05", aviso_dias=7)
    assert db.avisos_proximos(db.get_recurring_events(), date(2026, 5, 5)) == []


def test_el_aviso_cruza_el_fin_de_ano(test_db):
    _cumple("1990-01-03", aviso_dias=7)
    avisos = db.avisos_proximos(db.get_recurring_events(), date(2026, 12, 28))
    assert len(avisos) == 1
    assert avisos[0]["faltan"] == 6 and avisos[0]["fecha"] == "2027-01-03"


def test_sin_antelacion_no_avisa_nada(test_db):
    _cumple("1992-05-05")                                 # aviso_dias = 0
    assert db.avisos_proximos(db.get_recurring_events(), date(2026, 5, 1)) == []


def test_una_rutina_no_avisa_aunque_le_pongan_dias(test_db):
    """Avisar "en 3 días vas al gimnasio" todos los días no ayuda a nadie."""
    db.add_recurring_event({"title": "Caminadora", "color": "#6366f1", "recurrence": "daily",
                            "start_date": "2020-01-01", "aviso_dias": 7})
    assert db.avisos_proximos(db.get_recurring_events(), date(2026, 5, 1)) == []


# ── Los grupos ───────────────────────────────────────────────────────────────

def test_el_grupo_de_cumpleanos_viene_de_fabrica(test_db):
    grupos = [g for g in db.get_event_groups() if g["especial"] == "cumpleanos"]
    assert len(grupos) == 1
    assert grupos[0]["tipo"] == "recordatorio"


def test_borrar_un_grupo_no_borra_sus_rutinas(test_db):
    """⚠️ Perder rutinas por reordenar una pantalla sería absurdo: quedan sin grupo."""
    gid = db.add_event_group({"name": "Salud", "tipo": "rutina"})
    db.add_recurring_event({"title": "Caminadora", "color": "#6366f1", "recurrence": "daily",
                            "start_date": "2020-01-01", "group_id": gid})
    assert db.delete_event_group(gid) is True
    quedan = db.get_recurring_events()
    assert len(quedan) == 1
    assert quedan[0]["group_id"] is None


def test_el_grupo_de_fabrica_no_se_puede_borrar(test_db):
    grupo = [g for g in db.get_event_groups() if g["especial"] == "cumpleanos"][0]
    assert db.delete_event_group(grupo["id"]) is False
    assert any(g["especial"] == "cumpleanos" for g in db.get_event_groups())


def test_el_grupo_de_fabrica_se_puede_renombrar(test_db):
    grupo = [g for g in db.get_event_groups() if g["especial"] == "cumpleanos"][0]
    db.update_event_group(grupo["id"], {"name": "Cumples de la familia", "color": "#ec4899",
                                        "tipo": "recordatorio"})
    de_nuevo = [g for g in db.get_event_groups() if g["especial"] == "cumpleanos"][0]
    assert de_nuevo["name"] == "Cumples de la familia"
    assert de_nuevo["especial"] == "cumpleanos"           # sigue siendo el especial


def test_el_seed_no_duplica_al_reabrir(test_db):
    db.init_db()
    db.init_db()
    assert len([g for g in db.get_event_groups() if g["especial"] == "cumpleanos"]) == 1


def test_el_grupo_de_fabrica_tiene_identidad_fija(test_db):
    """⚠️ Lo crea cada instalación por su cuenta. Con un uid al azar, dos máquinas tendrían dos
    "Cumpleaños" distintos y al sincronizar quedarían **los dos**. Con el uid fijo, el merge los
    reconoce como la misma fila."""
    from bitacora.database.schema import UID_CUMPLEANOS
    grupo = [g for g in db.get_event_groups() if g["especial"] == "cumpleanos"][0]
    assert grupo["uid"] == UID_CUMPLEANOS


# ── La migración de una base que ya existía ──────────────────────────────────

def test_una_base_vieja_conserva_sus_rutinas_tal_cual(test_db):
    """⚠️ El camino real al actualizar: la tabla nació sin `tipo`, `group_id`, `birth_year` ni
    `aviso_dias`, y la de grupos no existía.

    Lo acordado es que la migración **no toque nada**: las rutinas de siempre quedan como
    Rutina / Sin grupo, con su frecuencia intacta —incluido el `every:364` del cumpleaños mal
    modelado, que se convierte desde la pantalla y con un clic del usuario, no por heurística—.
    """
    with db.get_db() as conn:
        for col in ("tipo", "group_id", "birth_year", "aviso_dias"):
            conn.execute(f"ALTER TABLE recurring_events DROP COLUMN {col}")
        conn.execute("DROP TABLE recurring_groups")
        conn.execute("INSERT INTO recurring_events (title, color, recurrence, start_date)"
                     " VALUES ('Cumple del pablo', '#6366f1', 'every:364', '2023-05-05')")
        conn.execute("INSERT INTO recurring_events (title, color, recurrence, start_date)"
                     " VALUES ('Caminadora', '#6366f1', 'every:2', '2026-06-11')")
        # Una base vieja de verdad tiene el esquema viejo Y la versión vieja: init_db() usa
        # user_version como guarda.
        conn.execute("PRAGMA user_version = 0")

    db.init_db()

    eventos = {e["title"]: e for e in db.get_recurring_events()}
    assert set(eventos) == {"Cumple del pablo", "Caminadora"}
    for ev in eventos.values():
        assert ev["tipo"] == "rutina"
        assert ev["group_id"] is None
        assert ev["aviso_dias"] == 0
    assert eventos["Cumple del pablo"]["recurrence"] == "every:364"   # sin tocar
    assert any(g["especial"] == "cumpleanos" for g in db.get_event_groups())


def test_la_version_del_esquema_subio(test_db):
    """Si se agrega una migración sin subir SCHEMA_VERSION, las bases instaladas se la saltean."""
    from bitacora.database.schema import SCHEMA_VERSION
    assert SCHEMA_VERSION >= 3
    with db.get_db() as conn:
        assert conn.execute("PRAGMA user_version").fetchone()[0] == SCHEMA_VERSION


# ── El año de nacimiento ─────────────────────────────────────────────────────

def test_se_puede_cargar_el_ano_o_la_edad():
    """El año es el dato canónico; la edad es el atajo para cuando no lo sabés —el caso que
    planteó el usuario: "sé que cumple 34 y no le voy a preguntar la fecha de nacimiento"."""
    from bitacora import services
    hoy = date(2026, 9, 13)
    assert services.anio_de_nacimiento("1992", "", hoy) == 1992
    assert services.anio_de_nacimiento("", "34", hoy) == 1992
    assert services.anio_de_nacimiento("1990", "34", hoy) == 1990   # el año exacto manda
    assert services.anio_de_nacimiento("", "", hoy) is None


def test_un_ano_o_una_edad_imposibles_no_se_guardan():
    from bitacora import services
    hoy = date(2026, 9, 13)
    for anio, edad in [("ayer", ""), ("", "x"), ("1800", ""), ("2099", ""), ("", "500")]:
        assert services.anio_de_nacimiento(anio, edad, hoy) is None


def test_la_edad_no_depende_de_si_el_cumple_ya_paso():
    """Se lee como "los que cumple ESTE año". Si dependiera de si ya pasó, el mismo número
    daría dos años distintos según el día en que lo cargaste."""
    from bitacora import services
    assert (services.anio_de_nacimiento("", "34", date(2026, 1, 2)) ==
            services.anio_de_nacimiento("", "34", date(2026, 12, 30)))


# ── La pantalla ──────────────────────────────────────────────────────────────

def _donde(grupo=None, tipo="rutina"):
    """El campo "Dónde va": un solo valor que decide el grupo Y el tipo."""
    return f"g:{grupo['id']}" if grupo else f"sin:{tipo}"


def _grupo_cumples():
    return [g for g in db.get_event_groups() if g["especial"] == "cumpleanos"][0]


def _alta(client, **campos):
    datos = {"title": "Algo", "color": "#6366f1", "rtype": "daily",
             "start_date": "2026-05-05", "donde": "sin:rutina"}
    datos.update(campos)
    return client.post("/recurring/add", data=datos, follow_redirects=True)


def test_la_pantalla_separa_rutinas_de_recordatorios(client):
    html = client.get("/recurring").data.decode()
    assert "lo que se mide" in html and "lo que avisa" in html


def test_se_puede_crear_un_cumpleanos_desde_el_formulario(client):
    grupo = _grupo_cumples()
    _alta(client, title="Cumple de Pablo", rtype="yearly", donde=_donde(grupo),
          edad="34", aviso="7")
    ev = db.get_recurring_events()[-1]
    assert ev["tipo"] == "recordatorio"
    assert ev["recurrence"] == "yearly"
    assert ev["group_id"] == grupo["id"]
    assert ev["birth_year"] == date.today().year - 34
    assert ev["aviso_dias"] == 7


def test_una_rutina_no_guarda_antelacion_aunque_la_manden(client):
    _alta(client, title="Caminadora", aviso="7")
    assert db.get_recurring_events()[-1]["aviso_dias"] == 0


def test_la_antelacion_otro_acepta_un_numero_libre(client):
    _alta(client, title="Vence el seguro", rtype="yearly", donde=_donde(tipo="recordatorio"),
          aviso="otro", aviso_otro="21")
    assert db.get_recurring_events()[-1]["aviso_dias"] == 21


def test_una_antelacion_disparatada_se_acota(client):
    _alta(client, title="x", donde=_donde(tipo="recordatorio"), aviso="otro",
          aviso_otro="99999")
    assert db.get_recurring_events()[-1]["aviso_dias"] == 365


def test_el_porcentaje_no_se_muestra_en_un_recordatorio(client):
    """⚠️ Lo que empezó todo: el cumpleaños arrastraba un "0 / 15 0%" que no significaba nada."""
    _alta(client, title="Cumple de Pablo", rtype="yearly", donde=_donde(_grupo_cumples()))
    html = client.get("/recurring").data.decode()
    assert "Cumple de Pablo" in html
    assert "Últimos 30 días" not in html          # no hay ninguna rutina todavía

    _alta(client, title="Caminadora")
    assert "Últimos 30 días" in client.get("/recurring").data.decode()


def test_la_pantalla_muestra_la_edad_y_la_antelacion(client):
    _alta(client, title="Cumple de Pablo", rtype="yearly", start_date="2026-05-05",
          donde=_donde(_grupo_cumples()), edad="34", aviso="7")
    html = client.get("/recurring").data.decode()
    assert "Cada año, el 5 de mayo" in html
    assert "cumple 34" in html
    assert "avisa 7 días antes" in html


# ── Los grupos desde la pantalla ─────────────────────────────────────────────

def test_crear_renombrar_y_borrar_un_grupo(client):
    client.post("/recurring/grupo/add", data={"name": "Salud", "tipo": "rutina"},
                follow_redirects=True)
    grupo = [g for g in db.get_event_groups() if g["name"] == "Salud"][0]

    client.post(f"/recurring/grupo/{grupo['id']}/edit",
                data={"name": "Salud y cuerpo", "color": "#22c55e"},
                follow_redirects=True)
    assert any(g["name"] == "Salud y cuerpo" for g in db.get_event_groups())

    client.post(f"/recurring/grupo/{grupo['id']}/delete", follow_redirects=True)
    assert not any(g["id"] == grupo["id"] for g in db.get_event_groups())


def test_la_pantalla_no_deja_borrar_el_grupo_de_fabrica(client):
    grupo = [g for g in db.get_event_groups() if g["especial"] == "cumpleanos"][0]
    client.post(f"/recurring/grupo/{grupo['id']}/delete", follow_redirects=True)
    assert any(g["especial"] == "cumpleanos" for g in db.get_event_groups())


# ── Los recordatorios en el resto de la app ──────────────────────────────────

def _cumple_en(client, dias, **extra):
    """Un cumpleaños a N días de hoy, creado por la pantalla."""
    from datetime import timedelta
    cuando = date.today() + timedelta(days=dias)
    datos = {"title": "Cumple de mamá", "color": "#a855f7", "rtype": "yearly",
             "start_date": cuando.replace(year=1960).isoformat(),
             "donde": _donde(_grupo_cumples())}
    datos.update(extra)
    client.post("/recurring/add", data=datos, follow_redirects=True)
    return cuando


def test_el_dia_de_hoy_muestra_lo_que_se_viene(client):
    _cumple_en(client, 3, aviso="7")
    html = client.get(f"/day/{date.today().isoformat()}").data.decode()
    assert "day-aviso" in html
    assert "en 3 días" in html


def test_otro_dia_no_muestra_avisos(client):
    """⚠️ "En 3 días" solo significa algo parado en hoy: mirando un día del año pasado sería
    una cuenta contra una fecha que ya pasó."""
    from datetime import timedelta
    _cumple_en(client, 3, aviso="7")
    otro = (date.today() + timedelta(days=30)).isoformat()
    assert "day-aviso" not in client.get(f"/day/{otro}").data.decode()


def test_el_widget_muestra_lo_que_se_viene(client):
    _cumple_en(client, 3, aviso="7")
    html = client.get("/widget?p=tareas").data.decode()
    assert "Se viene" in html and "Cumple de mamá" in html


def test_el_calendario_muestra_el_cumpleanos_en_su_dia_y_no_antes(client):
    """⚠️ La antelación NO va al calendario: cada celda dice qué pasa ESE día, y llenar los días
    previos con el mismo cumpleaños lo ensucia. "Qué se viene" es del día de hoy y del widget."""
    cuando = _cumple_en(client, 3, aviso="7")
    html = client.get(f"/calendar/{cuando.year}/{cuando.month}").data.decode()
    assert "Cumple de mamá" in html
    assert "day-aviso" not in html


def test_un_cumpleanos_se_distingue_en_el_calendario(client):
    cuando = _cumple_en(client, 0)
    html = client.get(f"/calendar/{cuando.year}/{cuando.month}").data.decode()
    assert "🎂" in html


def test_las_rutinas_traen_su_grupo(client):
    """El `grupo_especial` viene en el mismo SELECT: lo necesitan el día, el calendario, la
    semana y el widget para saber si algo es un cumpleaños."""
    _cumple_en(client, 0)
    ev = db.get_recurring_events()[-1]
    assert ev["grupo_especial"] == "cumpleanos"
    assert ev["grupo_nombre"] == "Cumpleaños"


def test_una_rutina_sin_grupo_no_rompe_el_join(client):
    db.add_recurring_event({"title": "Caminadora", "color": "#6366f1", "recurrence": "daily",
                            "start_date": "2020-01-01"})
    ev = db.get_recurring_events()[-1]
    assert ev["grupo_especial"] is None and ev["grupo_nombre"] is None


# ── Un solo lugar donde se decide grupo y tipo ───────────────────────────────

def test_el_lugar_decide_el_tipo(client):
    """⚠️ Antes eran dos campos y podían contradecirse: una rutina metida en un grupo de
    Recordatorios salía en la sección equivocada. Ahora el tipo se deduce del grupo."""
    _alta(client, title="Vence el seguro", donde=_donde(_grupo_cumples()))
    assert db.get_recurring_events()[-1]["tipo"] == "recordatorio"


def test_sin_grupo_el_lugar_igual_decide_el_tipo(client):
    _alta(client, title="Trámite", donde="sin:recordatorio")
    ev = db.get_recurring_events()[-1]
    assert ev["tipo"] == "recordatorio" and ev["group_id"] is None


def test_un_lugar_que_no_existe_cae_en_rutina_sin_grupo(client):
    """Un `donde` inventado no puede dejar la rutina en un limbo."""
    _alta(client, title="Algo", donde="g:9999")
    ev = db.get_recurring_events()[-1]
    assert ev["tipo"] == "rutina" and ev["group_id"] is None


def test_crear_un_grupo_no_pide_color(client):
    """Las nueve bolitas en cada fila eran la mitad del ruido: el color se elige solo y se
    cambia después."""
    from bitacora.appconfig import NOTE_COLORS
    client.post("/recurring/grupo/add", data={"name": "Salud", "tipo": "rutina"},
                follow_redirects=True)
    nuevo = [g for g in db.get_event_groups() if g["name"] == "Salud"][0]
    assert nuevo["color"] in NOTE_COLORS


def test_los_grupos_no_nacen_todos_del_mismo_color(client):
    for n in ("Salud", "Ejercicio", "Casa"):
        client.post("/recurring/grupo/add", data={"name": n, "tipo": "rutina"},
                    follow_redirects=True)
    colores = [g["color"] for g in db.get_event_groups()]
    assert len(set(colores)) == len(colores)


def test_editar_un_grupo_no_le_cambia_el_tipo(client):
    """El formulario ya no manda el tipo; si alguien lo mandara, igual no tiene que moverse:
    arrastraría a todo lo que el grupo tiene adentro."""
    client.post("/recurring/grupo/add", data={"name": "Salud", "tipo": "rutina"},
                follow_redirects=True)
    grupo = [g for g in db.get_event_groups() if g["name"] == "Salud"][0]
    client.post(f"/recurring/grupo/{grupo['id']}/edit",
                data={"name": "Salud", "color": "#22c55e", "tipo": "recordatorio"},
                follow_redirects=True)
    assert [g for g in db.get_event_groups() if g["name"] == "Salud"][0]["tipo"] == "rutina"


def test_la_pantalla_ya_no_tiene_el_panel_de_grupos(client):
    """Los grupos se administran en su propia sección: el panel los listaba una segunda vez."""
    html = client.get("/recurring").data.decode()
    assert "rec-grupos-body" not in html
    assert "+ Nuevo grupo" in html


# ── La sugerencia sobre datos que ya existen ─────────────────────────────────

def _vieja(client, titulo="Cumple del pablo", cada=364, desde="2023-05-05"):
    """Una rutina como las que hay en las bases instaladas: el cumpleaños por días."""
    db.add_recurring_event({"title": titulo, "color": "#6366f1",
                            "recurrence": f"every:{cada}", "start_date": desde})
    return db.get_recurring_events()[-1]


def test_detecta_lo_que_se_va_a_correr_de_fecha(test_db):
    from bitacora import services
    db.add_recurring_event({"title": "Cumple del pablo", "color": "#6366f1",
                            "recurrence": "every:364", "start_date": "2023-05-05"})
    db.add_recurring_event({"title": "Caminadora", "color": "#6366f1",
                            "recurrence": "every:2", "start_date": "2026-06-11"})
    sug = services.sugerencias_de_arreglo(db.get_recurring_events(), date(2026, 9, 13))
    assert [s["ev"]["title"] for s in sug] == ["Cumple del pablo"]
    assert sug[0]["corrido"] == -4          # este año le cae el 1 de mayo, no el 5


@pytest.mark.parametrize("cada,detecta", [(2, False), (30, False), (359, False), (360, True),
                                          (364, True), (365, True), (366, True), (367, False)])
def test_la_deteccion_es_acotada(test_db, cada, detecta):
    """⚠️ Solo `every:N` con N cerca del año. Nada de mirar el contenido para adivinar
    intenciones: es la misma regla que los renombres."""
    from bitacora import services
    db.add_recurring_event({"title": "algo", "color": "#6366f1", "recurrence": f"every:{cada}",
                            "start_date": "2020-01-01"})
    sug = services.sugerencias_de_arreglo(db.get_recurring_events(), date(2026, 9, 13))
    assert bool(sug) is detecta


def test_el_grupo_de_cumpleanos_solo_se_sugiere_si_el_titulo_lo_dice(test_db):
    """Un "cada 365 días" puede ser un chequeo médico: meterlo en Cumpleaños sería inventar."""
    from bitacora import services
    db.add_recurring_event({"title": "Chequeo médico", "color": "#6366f1",
                            "recurrence": "every:365", "start_date": "2024-03-10"})
    sug = services.sugerencias_de_arreglo(db.get_recurring_events(), date(2026, 9, 13))
    assert sug[0]["parece_cumple"] is False


def test_arreglar_deja_la_fecha_quieta(client):
    """El `start_date` ya tenía el mes y el día correctos: de ahí sale la fecha buena."""
    ev = _vieja(client)
    client.post(f"/recurring/{ev['id']}/arreglar-frecuencia", data={"a_cumpleanos": "1"},
                follow_redirects=True)
    de_nuevo = db.get_recurring_events()[-1]
    assert de_nuevo["recurrence"] == "yearly"
    assert de_nuevo["tipo"] == "recordatorio"
    assert de_nuevo["group_id"] == _grupo_cumples()["id"]
    for anio in (2026, 2030, 2078):
        assert db.event_applies(de_nuevo, date(anio, 5, 5))


def test_arreglar_no_toca_lo_que_no_hace_falta(client):
    """Cambia la frecuencia y nada más: el título, el color, el desde y el hasta quedan."""
    db.add_recurring_event({"title": "Cumple del pablo", "color": "#eab308",
                            "recurrence": "every:364", "start_date": "2023-05-05",
                            "end_date": "2078-05-06"})
    antes = db.get_recurring_events()[-1]
    client.post(f"/recurring/{antes['id']}/arreglar-frecuencia", data={"a_cumpleanos": "1"},
                follow_redirects=True)
    despues = db.get_recurring_events()[-1]
    for campo in ("title", "color", "start_date", "end_date"):
        assert despues[campo] == antes[campo], campo


def test_arreglar_sin_cumpleanos_solo_cambia_la_frecuencia(client):
    """Un chequeo anual se arregla igual, pero no se muda a Recordatorios."""
    db.add_recurring_event({"title": "Chequeo médico", "color": "#6366f1",
                            "recurrence": "every:365", "start_date": "2024-03-10"})
    ev = db.get_recurring_events()[-1]
    client.post(f"/recurring/{ev['id']}/arreglar-frecuencia", data={}, follow_redirects=True)
    despues = db.get_recurring_events()[-1]
    assert despues["recurrence"] == "yearly"
    assert despues["tipo"] == "rutina" and despues["group_id"] is None


def test_la_pantalla_ofrece_el_arreglo(client):
    _vieja(client)
    html = client.get("/recurring").data.decode()
    assert "se va a correr de fecha" in html
    assert "Arreglarla" in html
    assert "Dejarla como está" in html


def test_sin_nada_para_arreglar_no_hay_aviso(client):
    db.add_recurring_event({"title": "Caminadora", "color": "#6366f1", "recurrence": "daily",
                            "start_date": "2026-01-01"})
    assert 'class="rec-sugerencia"' not in client.get("/recurring").data.decode()


def test_una_rutina_ya_anual_no_se_vuelve_a_ofrecer(client):
    _alta(client, title="Cumple de Pablo", rtype="yearly", donde=_donde(_grupo_cumples()))
    assert 'class="rec-sugerencia"' not in client.get("/recurring").data.decode()


# ── Editar no puede perder lo que no estás editando ──────────────────────────

def test_editar_una_rutina_no_le_borra_el_grupo(client):
    """⚠️ El formulario de edición nació sin los campos nuevos, así que guardar cualquier cambio
    —el color, el nombre— sacaba la rutina de su grupo, la volvía Rutina y le borraba la
    antelación y el año de nacimiento. Un formulario que pierde datos que no estás editando es
    peor que uno incompleto."""
    grupo = _grupo_cumples()
    _alta(client, title="Cumple de Pablo", rtype="yearly", start_date="1992-05-05",
          donde=_donde(grupo), edad="34", aviso="7")
    ev = db.get_recurring_events()[-1]

    # Editar cambiándole SOLO el color.
    client.post(f"/recurring/{ev['id']}/edit",
                data={"title": "Cumple de Pablo", "color": "#a855f7", "rtype": "yearly",
                      "start_date": "1992-05-05", "donde": _donde(grupo), "edad": "34",
                      "aviso": "7"},
                follow_redirects=True)
    de_nuevo = db.get_recurring_events()[-1]
    assert de_nuevo["color"] == "#a855f7"
    assert de_nuevo["group_id"] == grupo["id"]
    assert de_nuevo["tipo"] == "recordatorio"
    assert de_nuevo["aviso_dias"] == 7
    assert de_nuevo["birth_year"] == date.today().year - 34


def test_se_puede_cambiar_de_grupo_editando(client):
    """La pregunta del usuario: cómo se le pone un grupo a una rutina que no lo tiene."""
    client.post("/recurring/grupo/add", data={"name": "Salud", "tipo": "rutina"},
                follow_redirects=True)
    salud = [g for g in db.get_event_groups() if g["name"] == "Salud"][0]
    _alta(client, title="Caminadora 20 mins", donde="sin:rutina")
    ev = db.get_recurring_events()[-1]
    assert ev["group_id"] is None

    client.post(f"/recurring/{ev['id']}/edit",
                data={"title": "Caminadora 20 mins", "color": "#6366f1", "rtype": "daily",
                      "start_date": "2026-06-11", "donde": _donde(salud)},
                follow_redirects=True)
    assert db.get_recurring_events()[-1]["group_id"] == salud["id"]


def test_el_formulario_de_edicion_trae_los_campos_nuevos(client):
    """Si no los trae, el navegador no los manda y se pierden solos."""
    _alta(client, title="Caminadora", donde="sin:rutina")
    ev = db.get_recurring_events()[-1]
    html = client.get("/recurring").data.decode()
    assert f'name="donde"' in html
    # Uno por formulario: el de alta y el de esta rutina.
    assert html.count('name="donde"') >= 2
