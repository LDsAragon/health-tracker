// Campos de tiempo estructurados: "duracion" (h/min) y "rango" (desde–hasta con cálculo).
// Patrón: inputs visibles + un <input type="hidden" data-label> con el valor canónico.
//   duracion → minutos totales como string  ("90")
//   rango    → "HH:MM-HH:MM" en 24h          ("23:00-08:00")  (cruce de medianoche soportado)
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

// "HH:MM","HH:MM" → minutos de diferencia (cruce de medianoche: 23:00→08:00 = 540)
function tfRangeMin(from, to) {
  const a = from.split(':'), b = to.split(':');
  const fa = (+a[0]) * 60 + (+a[1]), tb = (+b[0]) * 60 + (+b[1]);
  return ((tb - fa) % 1440 + 1440) % 1440;
}

// ── Fila de Rango: dos <input type="time"> (el browser maneja 12h/24h según locale) ──
function tfRangoRow() {
  return '<div class="tf-row">' +
    '<input type="time" class="tf-rng-from">' +
    '<span class="tf-u">→</span>' +
    '<input type="time" class="tf-rng-to">' +
    '<span class="tf-rh-calc"></span>' +
  '</div>';
}

// ── Fila de Duración: dos inputs numéricos conectados visualmente ──────────
function tfDurRow() {
  return '<div class="tf-row">' +
    '<div class="tf-dur-wrap">' +
      '<input type="number" class="tf-dur-h" min="0" max="99" placeholder="0">' +
      '<span class="tf-dur-sep">h</span>' +
      '<input type="number" class="tf-dur-m" min="0" max="59" placeholder="00">' +
      '<span class="tf-dur-sep">min</span>' +
    '</div>' +
    '<span class="tf-rh-calc"></span>' +
  '</div>';
}

// ── Builders (para formularios armados por JS) ─────────────────────────────
function buildDuracionField(label, ph) {
  return '<div class="day-journal-field-input time-field" data-tf="duracion">' +
    '<label>' + label + '</label>' +
    tfDurRow() +
    '<input type="hidden" data-label="' + _tfEsc(label) + '">' +
  '</div>';
}

function buildRangoField(label, ph) {
  return '<div class="day-journal-field-input time-field" data-tf="rango">' +
    '<label>' + label + '</label>' + tfRangoRow() +
    '<input type="hidden" data-label="' + _tfEsc(label) + '">' +
  '</div>';
}

// Asegura los inputs de rango/duración (para el form de edición, que llega como shell + hidden)
function _tfEnsureRango(tf) {
  if (tf.dataset.tf !== 'rango' || tf.querySelector('.tf-row')) return;
  const hidden = tf.querySelector('input[data-label]');
  const tmp = document.createElement('div');
  tmp.innerHTML = tfRangoRow();
  tf.insertBefore(tmp.firstChild, hidden);
}
function _tfEnsureDuracion(tf) {
  if (tf.dataset.tf !== 'duracion' || tf.querySelector('.tf-row')) return;
  const hidden = tf.querySelector('input[data-label]');
  const tmp = document.createElement('div');
  tmp.innerHTML = tfDurRow();
  tf.insertBefore(tmp.firstChild, hidden);
}

// ── Sincronización inputs → hidden (delegada) ──────────────────────────────
function _tfSync(tf) {
  const hidden = tf.querySelector('input[data-label]');
  if (!hidden) return;
  if (tf.dataset.tf === 'duracion') {
    const h = parseInt(tf.querySelector('.tf-dur-h').value, 10) || 0;
    const m = parseInt(tf.querySelector('.tf-dur-m').value, 10) || 0;
    const total = h * 60 + m;
    hidden.value = total > 0 ? String(total) : '';
    const calc = tf.querySelector('.tf-rh-calc');
    if (calc) calc.textContent = total > 0 ? tfFmtDur(total) : '';
  } else if (tf.dataset.tf === 'rango') {
    const from = tf.querySelector('.tf-rng-from').value;
    const to   = tf.querySelector('.tf-rng-to').value;
    const calc = tf.querySelector('.tf-rh-calc');
    if (from && to) { hidden.value = from + '-' + to; if (calc) calc.textContent = '· ' + tfFmtDur(tfRangeMin(from, to)); }
    else            { hidden.value = '';              if (calc) calc.textContent = ''; }
  }
}

function _tfOnEvt(e) {
  const tf = e.target.closest && e.target.closest('.time-field');
  if (tf) _tfSync(tf);
}
document.addEventListener('input', _tfOnEvt);
document.addEventListener('change', _tfOnEvt);

// ── Restaurar (edición): construye los inputs de rango si faltan y rellena desde el hidden ──
function restoreTimeFields(root) {
  (root || document).querySelectorAll('.time-field').forEach(tf => {
    if (tf.dataset.tf === 'rango')    _tfEnsureRango(tf);
    if (tf.dataset.tf === 'duracion') _tfEnsureDuracion(tf);
    const hidden = tf.querySelector('input[data-label]');
    const v = hidden && hidden.value;
    if (!v) return;
    if (tf.dataset.tf === 'duracion') {
      const total = parseInt(v, 10) || 0;
      tf.querySelector('.tf-dur-h').value = Math.floor(total / 60) || '';
      tf.querySelector('.tf-dur-m').value = (total % 60) || '';
      const calc = tf.querySelector('.tf-rh-calc');
      if (calc) calc.textContent = total > 0 ? tfFmtDur(total) : '';
    } else if (tf.dataset.tf === 'rango') {
      const parts = v.split('-');
      const from = parts[0] || '', to = parts[1] || '';
      if (from) tf.querySelector('.tf-rng-from').value = from;
      if (to)   tf.querySelector('.tf-rng-to').value   = to;
      if (from && to) {
        const calc = tf.querySelector('.tf-rh-calc');
        if (calc) calc.textContent = '· ' + tfFmtDur(tfRangeMin(from, to));
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', function () { restoreTimeFields(document); });
