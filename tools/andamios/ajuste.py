"""Agrega un ajuste nuevo: esquema + control en la pantalla + fila en el manual.

Hoy eso son tres archivos y hay que acordarse de los tres (`CLAUDE.md` § Convenciones).

Inserta en **anclas** (`# ANDAMIO: ...`), no adivinando dónde va cada cosa parseando el archivo:
si el ancla no está, aborta y lo dice. Heurísticas sobre el código son la misma clase de error
que ya se rechazó para los datos del usuario.

    python tools/andamios/ajuste.py --clave mostrar_racha --tipo switch \
        --on on --off off --seccion detalles \
        --titulo "Mostrar la racha" --desc "Cuántos días seguidos venís cumpliendo."
"""
import argparse
import sys

from comun import abortar_si_existe, insertar_en_ancla, ruta

SECCIONES = ("apariencia", "calendario", "tareas", "escritorio", "menu", "detalles")

# Los que cambian el navbar, que se renderiza en el servidor, necesitan data-recargar.
# (Ver CLAUDE.md § La pantalla de Ajustes.)
AVISO_NAVBAR = ("Si el ajuste cambia la barra de navegación, agregale `data-recargar` a la"
                " fila a mano:\n     sin eso se guarda pero el tab no aparece hasta recargar.")


def main():
    ap = argparse.ArgumentParser(description="Agrega un ajuste nuevo a Bitácora.")
    ap.add_argument("--clave", required=True, help="clave en appconfig.SETTINGS (snake_case)")
    ap.add_argument("--tipo", required=True, choices=("switch", "segmentado"))
    ap.add_argument("--seccion", required=True, choices=SECCIONES)
    ap.add_argument("--titulo", required=True, help="etiqueta en español que se ve en pantalla")
    ap.add_argument("--desc", required=True, help="texto explicativo debajo del título")
    ap.add_argument("--on", help="switch: valor prendido (ej. on, show, open)")
    ap.add_argument("--off", help="switch: valor apagado (ej. off, hide, collapsed)")
    ap.add_argument("--opciones", help="segmentado: valor=Etiqueta,valor=Etiqueta,...")
    ap.add_argument("--default", help="valor por defecto (por defecto: el primero)")
    a = ap.parse_args()

    if a.tipo == "switch":
        if not (a.on and a.off):
            sys.exit("ERROR: un switch necesita --on y --off.")
        valores = [a.on, a.off]
        etiquetas = None
    else:
        if not a.opciones:
            sys.exit("ERROR: un segmentado necesita --opciones valor=Etiqueta,valor=Etiqueta")
        pares = [p.split("=", 1) for p in a.opciones.split(",")]
        if any(len(p) != 2 for p in pares):
            sys.exit("ERROR: --opciones va como valor=Etiqueta,valor=Etiqueta")
        valores = [v.strip() for v, _ in pares]
        etiquetas = [e.strip() for _, e in pares]

    por_defecto = a.default or valores[0]
    if por_defecto not in valores:
        sys.exit(f"ERROR: el default '{por_defecto}' no está entre {valores}.")

    # ── 1. El esquema ────────────────────────────────────────────────────────
    p_cfg = ruta("bitacora", "appconfig.py")
    abortar_si_existe(p_cfg, f'"{a.clave}"', f"la clave '{a.clave}'")
    tupla = ", ".join(f'"{v}"' for v in valores)
    insertar_en_ancla(p_cfg, "# ANDAMIO: ajustes",
                      f'"{a.clave}": {{"default": "{por_defecto}", "choices": ({tupla})}},')

    # ── 2. El control en la pantalla ─────────────────────────────────────────
    p_html = ruta("bitacora", "templates", "settings.html")
    if a.tipo == "switch":
        control = f"{{{{ switch('{a.clave}', '{a.on}', '{a.off}') }}}}"
        fila_abre = '<div class="set-row">'
    else:
        lista = ", ".join(f"('{v}', '{e}')" for v, e in zip(valores, etiquetas))
        control = f"{{{{ seg('{a.clave}', [{lista}]) }}}}"
        # Tres o más opciones no entran al costado del texto: van debajo.
        fila_abre = ('<div class="set-row set-ancho">' if len(valores) > 2
                     else '<div class="set-row">')
    bloque = f"""
{fila_abre}
  <div class="set-texto">
    <label for="{a.clave}">{a.titulo}</label>
    <p class="set-desc">{a.desc}</p>
  </div>
  <div class="set-control">{control}</div>
</div>
"""
    insertar_en_ancla(p_html, f"{{# ANDAMIO: {a.seccion} #}}", bloque.strip("\n"))

    # ── 3. La fila del manual ────────────────────────────────────────────────
    p_man = ruta("docs", "manual.html")
    insertar_en_ancla(p_man, "<!-- ANDAMIO: ajustes -->",
                      f"<tr><td><b>{a.titulo}</b></td><td>{a.desc}</td></tr>")

    # ── 4. La lista del test ─────────────────────────────────────────────────
    # `test_todos_los_ajustes_tienen_un_control` compara el esquema contra una lista escrita a
    # mano: es el tripwire para el que agrega un ajuste SIN darle control. Acá el control está
    # garantizado, así que el andamio mantiene la lista y deja la suite en verde.
    p_test = ruta("tests", "test_ajustes.py")
    if a.tipo == "switch":
        insertar_en_ancla(p_test, "# ANDAMIO: switches",
                          f'"{a.clave}": ("{a.on}", "{a.off}"),')
    else:
        insertar_en_ancla(p_test, "# ANDAMIO: segmentados", f'"{a.clave}",')

    print(f"Listo, el ajuste '{a.clave}' quedó en:")
    print("  bitacora/appconfig.py              el esquema (default + choices)")
    print(f"  bitacora/templates/settings.html   un {a.tipo} en la sección '{a.seccion}'")
    print("  docs/manual.html                   una fila en la tabla de Ajustes")
    print("  tests/test_ajustes.py              la lista de controles, para que la suite pase")
    print()
    print("Falta a mano:")
    print(f"  1. Leer el ajuste donde haga falta: db.get_setting('{a.clave}') o g.settings.")
    print(f"  2. {AVISO_NAVBAR}")
    print("  3. Regenerar el PDF del manual: .\\hacer.ps1 manual")
    print("  4. Correr los tests: .\\hacer.ps1 tests -k ajustes")


if __name__ == "__main__":
    main()
