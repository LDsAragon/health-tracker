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
