// Bloques de campo estructurados para los seguimientos: escala / sino / opciones / numero.
// Mismo patrón que time-fields.js: control visible + <input type="hidden" data-label> con el valor
// canónico. collectValues() lee el hidden. En edición el form llega como shell (.field-block + hidden)
// y restoreFieldBlocks() construye el control y lo rellena.
//
// Config por campo = el texto del campo "Ayuda" (placeholder), sin tocar la DB:
//   escala   → vacío: 1–5 numérico (puntos).  "Mal,Bien" o "😣,😐,😄": escala con etiquetas.
//   opciones → lista separada por coma: "Desayuno, Almuerzo, Cena".
//   numero   → la unidad: "kg", "vasos".
// Valor guardado:
//   escala → "1".."N"   sino → "1"/""   opciones → texto elegido   numero → el número

function _fbEsc(s) { return String(s == null ? '' : s).replace(/"/g, '&quot;'); }
function _fbLabels(config) {
  return (config || '').split(',').map(s => s.trim()).filter(Boolean);
}

// ── Controles (sin wrapper ni hidden) ──────────────────────────────────────────
function _escalaControl(config) {
  const labels = _fbLabels(config);
  const labeled = labels.length >= 2;
  const steps = labeled ? labels : ['1', '2', '3', '4', '5'];
  let h = '<div class="fb-scale">';
  steps.forEach((s, i) => {
    h += '<button type="button" class="fb-step" data-idx="' + (i + 1) + '" title="' + _fbEsc(s) + '">' +
      (labeled ? _fbEsc(s) : '<span class="fb-dot"></span>') + '</button>';
  });
  return h + '</div>';
}
function _sinoControl() {
  return '<button type="button" class="fb-sino">No</button>';
}
function _opcionesControl(config) {
  const opts = _fbLabels(config);
  if (!opts.length) return '<span class="fb-hint">Definí las opciones en "Ayuda", separadas por coma.</span>';
  return '<div class="fb-opts">' +
    opts.map(o => '<button type="button" class="fb-opt" data-val="' + _fbEsc(o) + '">' + _fbEsc(o) + '</button>').join('') +
    '</div>';
}
function _numeroControl(config) {
  return '<div class="fb-numero">' +
    '<input type="number" class="fb-num" step="any">' +
    '<span class="fb-unit">' + _fbEsc((config || '').trim()) + '</span>' +
  '</div>';
}
function _fbControl(fb, config) {
  if (fb === 'escala')   return _escalaControl(config);
  if (fb === 'sino')     return _sinoControl();
  if (fb === 'opciones') return _opcionesControl(config);
  if (fb === 'numero')   return _numeroControl(config);
  return '';
}

// ── Builders (bloque completo para forms armados por JS) ────────────────────────
function _fbField(fb, label, config) {
  return '<div class="day-journal-field-input field-block" data-fb="' + fb + '" data-config="' + _fbEsc(config || '') + '">' +
    '<label>' + label + '</label>' +
    _fbControl(fb, config) +
    '<input type="hidden" data-label="' + _fbEsc(label) + '">' +
  '</div>';
}
function buildEscalaField(label, config)   { return _fbField('escala', label, config); }
function buildSinoField(label, config)     { return _fbField('sino', label, config); }
function buildOpcionesField(label, config) { return _fbField('opciones', label, config); }
function buildNumeroField(label, config)   { return _fbField('numero', label, config); }

// ── Estado: refleja un valor en la UI y lo escribe en el hidden ────────────────
function _fbApply(block, value) {
  const fb = block.dataset.fb;
  if (fb === 'escala') {
    const labeled = _fbLabels(block.dataset.config).length >= 2;
    block.querySelectorAll('.fb-step').forEach(b => {
      const idx = +b.dataset.idx;
      b.classList.toggle('active', value !== '' && idx === +value);
      b.classList.toggle('filled', !labeled && value !== '' && idx <= +value);
    });
  } else if (fb === 'sino') {
    const b = block.querySelector('.fb-sino');
    if (b) { const on = value === '1'; b.classList.toggle('on', on); b.textContent = on ? '✓ Sí' : 'No'; }
  } else if (fb === 'opciones') {
    block.querySelectorAll('.fb-opt').forEach(b => b.classList.toggle('active', b.dataset.val === value));
  } else if (fb === 'numero') {
    const inp = block.querySelector('.fb-num');
    if (inp && inp.value !== value) inp.value = value;
  }
}
function _fbSet(block, value) {
  const hidden = block.querySelector('input[data-label]');
  if (hidden) hidden.value = value;
  _fbApply(block, value);
}

// ── Interacción (delegada) ─────────────────────────────────────────────────────
document.addEventListener('click', function (e) {
  const step = e.target.closest && e.target.closest('.fb-step');
  if (step) { _fbSet(step.closest('.field-block'), step.dataset.idx); return; }
  const sino = e.target.closest && e.target.closest('.fb-sino');
  if (sino) {
    const block = sino.closest('.field-block');
    const cur = block.querySelector('input[data-label]').value;
    _fbSet(block, cur === '1' ? '' : '1');
    return;
  }
  const opt = e.target.closest && e.target.closest('.fb-opt');
  if (opt) {
    const block = opt.closest('.field-block');
    const cur = block.querySelector('input[data-label]').value;
    _fbSet(block, cur === opt.dataset.val ? '' : opt.dataset.val);  // re-clic = deseleccionar
    return;
  }
});
document.addEventListener('input', function (e) {
  const num = e.target.closest && e.target.closest('.fb-num');
  if (num) num.closest('.field-block').querySelector('input[data-label]').value = num.value;
});

// ── Restaurar (edición): construye el control desde el shell y aplica el valor ──
function _fbEnsure(block) {
  if (block.querySelector('.fb-scale, .fb-sino, .fb-opts, .fb-numero, .fb-hint')) return;
  const hidden = block.querySelector('input[data-label]');
  const tmp = document.createElement('div');
  tmp.innerHTML = _fbControl(block.dataset.fb, block.dataset.config || '');
  if (tmp.firstChild) block.insertBefore(tmp.firstChild, hidden);
}
function restoreFieldBlocks(root) {
  (root || document).querySelectorAll('.field-block').forEach(block => {
    _fbEnsure(block);
    const hidden = block.querySelector('input[data-label]');
    _fbApply(block, hidden ? hidden.value : '');
  });
}
document.addEventListener('DOMContentLoaded', function () { restoreFieldBlocks(document); });
