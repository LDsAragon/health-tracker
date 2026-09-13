"""Color por defecto de las notas rápidas, y la paleta como fuente única.

La regla que manda: **lo que elegís a mano siempre gana**. El ajuste solo decide qué pasa cuando
no elegiste nada.
"""
import pytest

from bitacora import database as db
from bitacora import services
from bitacora.appconfig import NOTE_COLORS, SETTINGS

DIA = "2026-06-10"


def _colores_de(dia=DIA):
    return [n["color"] for n in db.get_notes_for_date(dia)]


# ── El helper ────────────────────────────────────────────────────────────────

def test_el_color_elegido_siempre_gana(client):
    db.set_setting("nota_color", "aleatorio")
    assert services.color_para_nota_nueva("#ef4444") == "#ef4444"
    db.set_setting("nota_color", "#22c55e")
    assert services.color_para_nota_nueva("#ef4444") == "#ef4444"


def test_sin_ajuste_la_nota_queda_sin_color(client):
    """El default es "": la app se comporta como siempre hasta que lo cambies."""
    assert SETTINGS["nota_color"]["default"] == ""
    assert services.color_para_nota_nueva("") == ""


def test_un_color_fijo_se_aplica(client):
    db.set_setting("nota_color", "#3b82f6")
    assert services.color_para_nota_nueva("") == "#3b82f6"


def test_aleatorio_sale_de_la_paleta(client):
    db.set_setting("nota_color", "aleatorio")
    for _ in range(30):
        assert services.color_para_nota_nueva("") in NOTE_COLORS


def test_aleatorio_varia(client):
    """No es determinista, pero con 9 colores y 40 tiradas ver uno solo sería un bug."""
    db.set_setting("nota_color", "aleatorio")
    vistos = {services.color_para_nota_nueva("") for _ in range(40)}
    assert len(vistos) > 1


def test_un_ajuste_con_basura_no_pinta_nada(client):
    """Defensa en profundidad: get_all_settings clampea, pero el helper no puede devolver algo
    que no sea un color."""
    db.set_setting("nota_color", "no-es-un-color")
    assert services.color_para_nota_nueva("") == ""


# ── Las dos rutas de alta ────────────────────────────────────────────────────

def test_la_ruta_del_dia_aplica_el_ajuste(client):
    """`day.note_add` recibe las altas del día, del calendario Y de la semana."""
    db.set_setting("nota_color", "#eab308")
    client.post(f"/day/{DIA}/note/add", data={"content": "sin elegir color", "color": ""})
    assert _colores_de() == ["#eab308"]


def test_la_ruta_del_dia_respeta_lo_elegido(client):
    db.set_setting("nota_color", "#eab308")
    client.post(f"/day/{DIA}/note/add", data={"content": "elegí este", "color": "#ec4899"})
    assert _colores_de() == ["#ec4899"]


def test_el_widget_aplica_el_ajuste(client):
    import datetime
    hoy = datetime.date.today().isoformat()
    db.set_setting("nota_color", "#14b8a6")
    client.post("/widget/nota", data={"content": "desde el widget"})
    assert _colores_de(hoy) == ["#14b8a6"]


def test_el_widget_respeta_lo_elegido(client):
    import datetime
    hoy = datetime.date.today().isoformat()
    db.set_setting("nota_color", "aleatorio")
    client.post("/widget/nota", data={"content": "con color", "color": "#f97316"})
    assert _colores_de(hoy) == ["#f97316"]


def test_el_widget_tiene_selector_de_color(client):
    html = client.get("/widget?p=nota").data.decode()
    assert 'name="color"' in html
    for c in NOTE_COLORS:
        assert c in html


# ── La paleta es una sola ────────────────────────────────────────────────────

def test_la_paleta_no_esta_repetida_en_las_plantillas():
    """Estaba como literal en SEIS plantillas. El ajuste la necesita como `choices`, así que
    ahora vive en appconfig y se inyecta.

    Busca **varios colores de la paleta en una misma línea**, que es la forma que tiene una
    paleta copiada. Un color suelto es otra cosa y es legítimo: `journal.html` usa `#6366f1`
    como el color de una de sus categorías predefinidas.
    """
    import pathlib
    raiz = pathlib.Path(__file__).resolve().parent.parent / "bitacora" / "templates"
    culpables = []
    for p in raiz.glob("*.html"):
        for n, linea in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            if sum(c in linea for c in NOTE_COLORS) >= 3:
                culpables.append(f"{p.name}:{n}")
    assert culpables == []


@pytest.mark.parametrize("ruta", ["/day/2026-06-10", "/calendar/2026/6", "/week/2026-06-10",
                                  "/recurring", "/journal", "/widget?p=nota"])
def test_las_pantallas_siguen_ofreciendo_la_paleta(client, ruta):
    """Que la paleta se centralizara no puede haber dejado una pantalla sin colores."""
    html = client.get(ruta).data.decode()
    assert NOTE_COLORS[0] in html and NOTE_COLORS[-1] in html
