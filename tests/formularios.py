"""Leer un `<form>` renderizado como lo leería el navegador.

Lo usan los tests que verifican que un formulario de edición venga **precargado**: es la única
forma de probarlo sin un navegador de verdad, y sin caer en escribir el POST a mano —que es
exactamente como se coló el bug que motivó este módulo—.
"""
from html.parser import HTMLParser


class _Formulario(HTMLParser):
    """Lo que el navegador mandaría al enviar un `<form>`, sacado del HTML renderizado.

    ⚠️ Existe porque un test que arma el POST a mano prueba el test, no la pantalla. Esa es la
    forma exacta en que se coló el bug de los cumpleaños: había un test para que editar no
    perdiera datos, pero mandaba `rtype=yearly` —una opción que el formulario de edición no
    tenía—, así que pasaba en verde mientras la app, con el valor que el navegador sí mandaba
    (ninguno), le cambiaba la frecuencia a "todos los días". Es el mismo agujero que ya tuvieron
    los smokes del escritorio: repetir a mano lo que hace la app en vez de usarla.

    Sigue las reglas del navegador, que son justamente las que hacen invisible este tipo de bug:
    un control sin `name` no viaja, un radio o checkbox sin marcar tampoco, y un `<select>` sin
    ninguna opción marcada manda la primera. Que un campo escondido por CSS sí viaje es a
    propósito: `display:none` no lo excluye, solo `disabled` lo haría.
    """

    def __init__(self, action):
        super().__init__(convert_charrefs=True)
        self._action = action
        self._dentro = False
        self._select = None          # (name, valor_elegido, primer_valor)
        self._textarea = None
        self.campos = []             # [(name, value)], con repetidos: son los checkbox múltiples

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "form":
            self._dentro = a.get("action", "") == self._action
            return
        if not self._dentro:
            return
        if tag == "input":
            if not a.get("name") or "disabled" in a:
                return
            if a.get("type") in ("radio", "checkbox") and "checked" not in a:
                return
            self.campos.append((a["name"], a.get("value", "")))
        elif tag == "select" and a.get("name") and "disabled" not in a:
            self._select = [a["name"], None, None]
        elif tag == "option" and self._select:
            valor = a.get("value", "")
            if self._select[2] is None:
                self._select[2] = valor
            if "selected" in a:
                self._select[1] = valor
        elif tag == "textarea" and a.get("name"):
            self._textarea = [a["name"], ""]

    def handle_data(self, data):
        if self._textarea is not None:
            self._textarea[1] += data

    def handle_endtag(self, tag):
        if tag == "form":
            self._dentro = False
        elif tag == "select" and self._select:
            nombre, elegido, primero = self._select
            self.campos.append((nombre, elegido if elegido is not None else (primero or "")))
            self._select = None
        elif tag == "textarea" and self._textarea is not None:
            self.campos.append(tuple(self._textarea))
            self._textarea = None


def lo_que_manda_el_form(html, action):
    """Los campos que un navegador enviaría desde el `<form>` con ese `action`.

    Se devuelve como lista de pares —no como dict— porque los checkbox múltiples (los días de la
    semana) mandan el mismo nombre varias veces, y `client.post(data=...)` de Flask acepta pares.
    """
    p = _Formulario(action)
    p.feed(html)
    assert p.campos, f"no se encontró ningún campo en el formulario {action}"
    return p.campos
