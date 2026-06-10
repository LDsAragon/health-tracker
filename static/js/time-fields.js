// Campos de tiempo estructurados: "duracion" (h/min) y "rango" (desde–hasta con cálculo, 24h).
// Patrón (como la rueda): inputs visibles + un <input type="hidden" data-label> con el valor canónico.
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

// ── Fila de Rango: inputs numéricos HH:MM → HH:MM (24h, sin overlay) ────────
function tfRangoRow() {
  const hi = (cls, mx, ph) =>
    '<input type="number" class="' + cls + '" min="0" max="' + mx + '" placeholder="' + ph + '">';
  return '<div class="tf-row">' +
    hi('tf-rh-fh', 23, 'hh') + '<span class="tf-u">:</span>' + hi('tf-rh-fm', 59, 'mm') +
    '<span class="tf-u">→</span>' +
    hi('tf-rh-th', 23, 'hh') + '<span class="tf-u">:</span>' + hi('tf-rh-tm', 59, 'mm') +
    '<span class="tf-rh-calc"></span>' +
  '</div>';
}

// ── Builders (para formularios armados por JS) ─────────────────────────────
function buildDuracionField(label, ph) {
  return '<div class="day-journal-field-input time-field" data-tf="duracion">' +
    '<label>' + label + '</label>' +
    '<div class="tf-row">' +
      '<input type="number" class="tf-dur-h" min="0" max="99" placeholder="h"><span class="tf-u">h</span>' +
      '<input type="number" class="tf-dur-m" min="0" max="59" placeholder="min"><span class="tf-u">min</span>' +
    '</div>' +
    '<input type="hidden" data-label="' + _tfEsc(label) + '">' +
  '</div>';
}

function buildRangoField(label, ph) {
  return '<div class="day-journal-field-input time-field" data-tf="rango">' +
    '<label>' + label + '</label>' + tfRangoRow() +
    '<input type="hidden" data-label="' + _tfEsc(label) + '">' +
  '</div>';
}

// Asegura los inputs de rango (para el form de edición, que llega como shell + hidden)
function _tfEnsureRango(tf) {
  if (tf.dataset.tf !== 'rango' || tf.querySelector('.tf-row')) return;
  const hidden = tf.querySelector('input[data-label]');
  const tmp = document.createElement('div');
  tmp.innerHTML = tfRangoRow();
  tf.insertBefore(tmp.firstChild, hidden);
}

function _tfRangoVals(tf) {
  const val = c => { const el = tf.querySelector(c); return el && el.value !== '' ? el.value : null; };
  const cp  = (x, mx) => String(Math.min(mx, Math.max(0, parseInt(x, 10) || 0))).padStart(2, '0');
  const fh = val('.tf-rh-fh'), fm = val('.tf-rh-fm'), th = val('.tf-rh-th'), tm = val('.tf-rh-tm');
  return {
    from: (fh !== null && fm !== null) ? cp(fh, 23) + ':' + cp(fm, 59) : '',
    to:   (th !== null && tm !== null) ? cp(th, 23) + ':' + cp(tm, 59) : ''
  };
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
  } else if (tf.dataset.tf === 'rango') {
    const { from, to } = _tfRangoVals(tf);
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
    if (tf.dataset.tf === 'rango') _tfEnsureRango(tf);
    const hidden = tf.querySelector('input[data-label]');
    const v = hidden && hidden.value;
    if (!v) return;
    if (tf.dataset.tf === 'duracion') {
      const total = parseInt(v, 10) || 0;
      tf.querySelector('.tf-dur-h').value = Math.floor(total / 60) || '';
      tf.querySelector('.tf-dur-m').value = (total % 60) || '';
    } else if (tf.dataset.tf === 'rango') {
      const p = v.split('-');
      const f = (p[0] || '').split(':'), t = (p[1] || '').split(':');
      const set = (c, val) => { const el = tf.querySelector(c); if (el && val != null) el.value = val; };
      set('.tf-rh-fh', f[0]); set('.tf-rh-fm', f[1]); set('.tf-rh-th', t[0]); set('.tf-rh-tm', t[1]);
      if (p[0] && p[1]) {
        const calc = tf.querySelector('.tf-rh-calc');
        if (calc) calc.textContent = '· ' + tfFmtDur(tfRangeMin(p[0], p[1]));
      }
    }
  });
}

document.addEventListener('DOMContentLoaded', function () { restoreTimeFields(document); });
