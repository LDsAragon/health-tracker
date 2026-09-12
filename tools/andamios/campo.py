"""Agrega un tipo de campo de notas especiales: catálogo + registro + builder stub.

Hoy son tres lugares (`CLAUDE.md` § Convenciones): una entrada en `fieldtypes.FIELD_TYPES`, el
builder registrado en `static/js/field-registry.js`, y su display en `day.html`.

El **display es opcional**: la cadena de `{% elif %}` de `day.html` termina en un `else` que
muestra el valor crudo, así que un tipo nuevo se ve bien desde el principio y solo hay que tocar
`day.html` si querés un render propio.

Lo que el andamio NO puede escribir es el cuerpo del builder: armar el input es justamente la
lógica del tipo. Deja un stub que anda (un input de texto) y marcado con TODO.

    python tools/andamios/campo.py --tipo color --etiqueta "🎨 Color"
"""
import argparse
import sys

from comun import abortar_si_existe, insertar_en_ancla, leer, ruta


def camel(tipo):
    """color-favorito → ColorFavorito, para el nombre del builder."""
    return "".join(p.capitalize() for p in tipo.replace("_", "-").split("-") if p)


def main():
    ap = argparse.ArgumentParser(description="Agrega un tipo de campo de notas especiales.")
    ap.add_argument("--tipo", required=True,
                    help="slug del tipo, como se guarda en la DB (ej: color, humor-diario)")
    ap.add_argument("--etiqueta", required=True,
                    help="cómo se llama en el selector, con emoji si querés (ej: '🎨 Color')")
    a = ap.parse_args()

    if not a.tipo.replace("-", "").replace("_", "").isalnum():
        sys.exit("ERROR: --tipo solo puede tener letras, números, guiones y guiones bajos.")

    p_cat = ruta("bitacora", "fieldtypes.py")
    p_reg = ruta("bitacora", "static", "js", "field-registry.js")
    p_blo = ruta("bitacora", "static", "js", "field-blocks.js")
    builder = f"build{camel(a.tipo)}Field"

    abortar_si_existe(p_cat, f'("{a.tipo}"', f"el tipo '{a.tipo}'")
    abortar_si_existe(p_reg, f"'{a.tipo}'", f"el tipo '{a.tipo}'")
    if builder in leer(p_blo):
        sys.exit(f"ERROR: la función {builder} ya existe en field-blocks.js.")

    # ── 1. El catálogo del backend ───────────────────────────────────────────
    insertar_en_ancla(p_cat, "# ANDAMIO: campos",
                      f'("{a.tipo}",{" " * max(1, 14 - len(a.tipo))}"{a.etiqueta}"),')

    # ── 2. El despacho del front ─────────────────────────────────────────────
    insertar_en_ancla(p_reg, "// ANDAMIO: campos",
                      f"'{a.tipo}':{' ' * max(1, 14 - len(a.tipo))}"
                      f"(label, ph) => {builder}(label, ph),")

    # ── 3. El builder, como stub que ya anda ─────────────────────────────────
    stub = f"""
// {a.etiqueta} — TODO: armar el input de verdad.
// Contrato: devolver un elemento con un <input name="field_value[]"> adentro; `label` es la
// etiqueta del campo y `ph` el placeholder que configuró el usuario. Mirá buildNumeroField o
// buildSinoField acá mismo como ejemplos cortos.
function {builder}(label, ph) {{
  const wrap = document.createElement('div');
  wrap.className = 'fb-wrap';
  const input = document.createElement('input');
  input.type = 'text';
  input.name = 'field_value[]';
  input.placeholder = ph || label;
  wrap.appendChild(input);
  return wrap;
}}
"""
    insertar_en_ancla(p_blo, "// ANDAMIO: campos", stub.strip("\n"))

    print(f"Listo, el tipo '{a.tipo}' quedó en:")
    print("  bitacora/fieldtypes.py                    el catálogo (aparece en los selectores)")
    print("  bitacora/static/js/field-registry.js      el despacho tipo -> builder")
    print(f"  bitacora/static/js/field-blocks.js        {builder}(), como stub")
    print()
    print("Falta a mano:")
    print(f"  1. Escribir el cuerpo de {builder}() — el stub es un input de texto.")
    print("  2. Si querés un display propio, sumar un {% elif %} en templates/day.html.")
    print("     Sin eso hereda el genérico de la cadena y se ve el valor crudo.")
    print("  3. Correr los tests: .\\hacer.ps1 tests -k journal")


if __name__ == "__main__":
    main()
