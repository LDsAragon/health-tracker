// Registro de builders de campo: tipo → función que arma el input.
// Fuente única del despacho (lo usa buildFields en day.html). Los builders viven en
// emotion-wheel.js / time-fields.js / field-blocks.js (globales). Agregar un tipo:
// sumar su entrada acá + la entrada en fieldtypes.py (backend).
window.FIELD_BUILDERS = {
  'emotion-wheel': (label, ph) => buildEWPicker(label),
  'duracion':      (label, ph) => buildDuracionField(label, ph),
  'rango':         (label, ph) => buildRangoField(label, ph),
  'escala':        (label, ph) => buildEscalaField(label, ph),
  'sino':          (label, ph) => buildSinoField(label, ph),
  'opciones':      (label, ph) => buildOpcionesField(label, ph),
  'numero':        (label, ph) => buildNumeroField(label, ph),
};
