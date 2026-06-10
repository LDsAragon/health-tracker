// Campos de tiempo estructurados: "duracion" (h/min) y "rango" (desde–hasta con cálculo).
// Patrón (como la rueda): inputs visibles + un <input type="hidden" data-label> con el valor canónico.
//   duracion → minutos totales como string  ("90")
//   rango    → "HH:MM-HH:MM"                  ("02:00-09:00")  (cruce de medianoche soportado)
// El colector lee input[data-label]; restoreTimeFields() rellena los inputs desde el hidden (edición).

function _tfEsc(s) { return String(s).replace(/"/g, '&quot;'); }

// minutos → "1 h 30 min" / "45 min" / "2 h"
function tfFmtDur(mins) {
  const m = parseInt(mins, 10);
  if (isNaN(m) || m <= 0) return '';
  const h = Math.floor(m / 60), mm = m % 60;
  const parts = [];
  if (h)  parts.push(h + ' h');
  if (mm) parts.push(mm + ' min');
  return parts.join(' ') || '0 min';
}

// "HH:MM","HH:MM" → minutos de diferencia (cruce de medianoche: 02:00→09:00 = 420)
function tfRangeMin(from, to) {
  const a = from.split(':'), b = to.split(':');
  const fa = (+a[0]) * 60 + (+a[1]), tb = (+b[0]) * 60 + (+b[1]);
  return ((tb - fa) % 1440 + 1440) % 1440;
}

// ── Builders (para formularios armados por JS) ─────────────────────────────
function buildDuracionField(label, ph) {
  const l = _tfEsc(label);
  return '<div class="day-journal-field-input time-field" data-tf="duracion">' +
    '<label>' + label + '</label>' +
    '<div class="tf-row">' +
      '<input type="number" class="tf-dur-h" min="0" max="99" placeholder="h"><span class="tf-u">h</span>' +
      '<input type="number" class="tf-dur-m" min="0" max="59" placeholder="min"><span class="tf-u">min</span>' +
    '</div>' +
    '<input type="hidden" data-label="' + l + '">' +
  '</div>';
}

function buildRangoField(label, ph) {
  const l = _tfEsc(label);
  return '<div class="day-journal-field-input time-field" data-tf="rango">' +
    '<label>' + label + '</label>' +
    '<div class="tf-row">' +
      '<input type="time" class="tf-rh-from"><span class="tf-u">→</span>' +
      '<input type="time" class="tf-rh-to"><span class="tf-rh-calc"></span>' +
    '</div>' +
    '<input type="hidden" data-label="' + l + '">' +
  '</div>';
}

// ── Sincronización inputs → hidden (delegada, sirve para campos dinámicos y estáticos) ──
function _tfSync(tf) {
  const hidden = tf.querySelector('input[data-label]');
  if (!hidden) return;
  if (tf.dataset.tf === 'duracion') {
    const h = parseInt(tf.querySelector('.tf-dur-h').value, 10) || 0;
    const m = parseInt(tf.querySelector('.tf-dur-m').value, 10) || 0;
    const total = h * 60 + m;
    hidden.value = total > 0 ? String(total) : '';
  } else if (tf.dataset.tf === 'rango') {
    const f = tf.querySelector('.tf-rh-from').value;
    const t = tf.querySelector('.tf-rh-to').value;
    const calc = tf.querySelector('.tf-rh-calc');
    if (f && t) { hidden.value = f + '-' + t; calc.textContent = '· ' + tfFmtDur(tfRangeMin(f, t)); }
    else        { hidden.value = '';          calc.textContent = ''; }
  }
}

document.addEventListener('input', function (e) {
  const tf = e.target.closest && e.target.closest('.time-field');
  if (tf) _tfSync(tf);
});

// ── Restaurar (edición): parsea el hidden y rellena los inputs visibles ────
function restoreTimeFields(root) {
  (root || document).querySelectorAll('.time-field').forEach(tf => {
    const hidden = tf.querySelector('input[data-label]');
    const v = hidden && hidden.value;
    if (!v) return;
    if (tf.dataset.tf === 'duracion') {
      const total = parseInt(v, 10) || 0;
      tf.querySelector('.tf-dur-h').value = Math.floor(total / 60) || '';
      tf.querySelector('.tf-dur-m').value = (total % 60) || '';
    } else if (tf.dataset.tf === 'rango') {
      const parts = v.split('-');
      if (parts[0]) tf.querySelector('.tf-rh-from').value = parts[0];
      if (parts[1]) tf.querySelector('.tf-rh-to').value = parts[1];
      if (parts[0] && parts[1]) {
        tf.querySelector('.tf-rh-calc').textContent = '· ' + tfFmtDur(tfRangeMin(parts[0], parts[1]));
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', function () { restoreTimeFields(document); });
