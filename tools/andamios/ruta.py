"""Agrega una pantalla nueva: blueprint + registro + plantilla + archivo de tests.

Los blueprints se importan y se listan a mano en `app.py`, sin descubrimiento automático:
PyInstaller resuelve imports estáticamente y con un `importlib` dinámico las rutas no entrarían
al bundle. Por eso el andamio inserta en las dos anclas de `app.py`.

    python tools/andamios/ruta.py --nombre habitos --titulo "Hábitos"
"""
import argparse
import sys

from comun import abortar_si_existe, crear_archivo, insertar_en_ancla, ruta


def main():
    ap = argparse.ArgumentParser(description="Agrega una pantalla nueva a Bitácora.")
    ap.add_argument("--nombre", required=True,
                    help="slug del blueprint y de la URL, en minúsculas (ej: habitos)")
    ap.add_argument("--titulo", required=True, help="título en español de la pantalla")
    a = ap.parse_args()

    if not a.nombre.isidentifier() or not a.nombre.islower():
        sys.exit("ERROR: --nombre tiene que ser un identificador en minúsculas (ej: habitos).")

    p_app = ruta("bitacora", "app.py")
    p_ruta = ruta("bitacora", "routes", f"{a.nombre}.py")
    p_tpl = ruta("bitacora", "templates", f"{a.nombre}.html")
    p_test = ruta("tests", f"test_{a.nombre}.py")

    abortar_si_existe(p_app, f" {a.nombre},", f"el blueprint '{a.nombre}'")

    crear_archivo(p_ruta, f'''"""{a.titulo}."""
from flask import Blueprint, render_template, request

from bitacora import database as db
from bitacora.helpers import safe_back

bp = Blueprint("{a.nombre}", __name__)


@bp.route("/{a.nombre}")
def vista():
    return render_template("{a.nombre}.html", back=safe_back(request.args.get("back")))
''')

    crear_archivo(p_tpl, f'''{{% extends "base.html" %}}
{{% block title %}}{a.titulo}{{% endblock %}}

{{% block content %}}
<div class="page-back" style="margin-bottom:14px;">
  <a href="{{{{ back or url_for('main.home') }}}}" class="back-link">&#8592; {{{{ 'Volver' if back else 'Calendario' }}}}</a>
</div>

<div class="page-top">
  <h1 class="page-title">{a.titulo}</h1>
  <p class="page-sub">TODO: de qué se trata esta pantalla.</p>
</div>
{{% endblock %}}
''')

    crear_archivo(p_test, f'''"""{a.titulo}."""


def test_la_pantalla_carga(client):
    r = client.get("/{a.nombre}")
    assert r.status_code == 200
    assert "{a.titulo}".encode() in r.data


def test_volver_contextual(client):
    """Como el resto de la app: el Volver respeta de dónde viniste."""
    assert b"/week/2026-06-11" in client.get("/{a.nombre}?back=/week/2026-06-11").data
''')

    # Las dos anclas de app.py: el import y la tupla de registro.
    insertar_en_ancla(p_app, "# ANDAMIO: blueprints (import)", f"{a.nombre},")
    insertar_en_ancla(p_app, "# ANDAMIO: blueprints (registro)", f"{a.nombre},")

    print(f"Listo, la pantalla '{a.nombre}' quedó en:")
    print(f"  bitacora/routes/{a.nombre}.py           el blueprint, con GET /{a.nombre}")
    print(f"  bitacora/templates/{a.nombre}.html      la plantilla, heredando de base.html")
    print(f"  tests/test_{a.nombre}.py                dos tests que ya pasan")
    print("  bitacora/app.py                     importada y registrada")
    print()
    print("Falta a mano:")
    print("  1. El contenido de la pantalla y sus acciones.")
    print(f"  2. Si querés que esté en el navbar: el enlace en templates/base.html. Y si va a ser")
    print("     ocultable, un ajuste con `hacer.ps1 nuevo ajuste` + `data-recargar` en su fila.")
    print("  3. Correr los tests: .\\hacer.ps1 tests -k " + a.nombre)


if __name__ == "__main__":
    main()
