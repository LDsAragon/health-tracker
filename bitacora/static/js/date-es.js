// Campo de fecha con formato configurable (Ajustes → date_format), independiente del navegador.
// Muestra la fecha en el formato elegido y guarda el valor canónico ISO (yyyy-mm-dd) en un
// <input type="hidden" name="..."> que lee el backend. window.DATE_FMT lo inyecta base.html.
//   dmy → dd/mm/aaaa (default)   mdy → mm/dd/aaaa   ymd → aaaa-mm-dd
// Estructura (macro date_field en templates/_macros.html):
//   <span class="date-es">
//     <input class="date-es-text">                 ← visible, formato elegido
//     <button class="date-es-cal">📅</button>       ← abre el calendario nativo
//     <input type="date" class="date-es-native">    ← oculto, solo para el picker del SO
//     <input type="hidden" class="date-es-iso" name="..."> ← lo que se envía (ISO)
//   </span>

function _deFmtConf() { return window.DATE_FMT || 'dmy'; }
function _dePlaceholder() {
  const f = _deFmtConf();
  return f === 'mdy' ? 'mm/dd/aaaa' : f === 'ymd' ? 'aaaa-mm-dd' : 'dd/mm/aaaa';
}
function _deFmt(iso) {                          // ISO → texto según formato
  const m = (iso || '').match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return '';
  const y = m[1], mo = m[2], d = m[3], f = _deFmtConf();
  if (f === 'mdy') return mo + '/' + d + '/' + y;
  if (f === 'ymd') return y + '-' + mo + '-' + d;
  return d + '/' + mo + '/' + y;
}
function _deParse(str) {                        // texto → ISO ("" si inválida)
  str = (str || '').trim();
  const f = _deFmtConf();
  let d, mo, y, m;
  if (f === 'ymd') {
    m = str.match(/^(\d{4})[\/\-.](\d{1,2})[\/\-.](\d{1,2})$/);
    if (!m) return '';
    y = +m[1]; mo = +m[2]; d = +m[3];
  } else {
    m = str.match(/^(\d{1,2})[\/\-.](\d{1,2})[\/\-.](\d{2,4})$/);
    if (!m) return '';
    if (f === 'mdy') { mo = +m[1]; d = +m[2]; } else { d = +m[1]; mo = +m[2]; }
    y = +m[3];
    if (y < 100) y += 2000;
  }
  if (mo < 1 || mo > 12 || d < 1 || d > 31) return '';
  const iso = String(y).padStart(4, '0') + '-' + String(mo).padStart(2, '0') + '-' + String(d).padStart(2, '0');
  const dt = new Date(iso + 'T00:00:00');       // valida días reales (31/02 → inválido)
  if (dt.getFullYear() !== y || dt.getMonth() + 1 !== mo || dt.getDate() !== d) return '';
  return iso;
}
function _deSetIso(wrap, iso) {
  wrap.querySelector('.date-es-iso').value = iso;
  const nat = wrap.querySelector('.date-es-native');
  if (nat) nat.value = iso;
}

function initDateEs(root) {
  (root || document).querySelectorAll('.date-es').forEach(wrap => {
    if (wrap.dataset.deReady) return;
    wrap.dataset.deReady = '1';
    const text = wrap.querySelector('.date-es-text');
    const iso = wrap.querySelector('.date-es-iso').value;
    text.placeholder = _dePlaceholder();
    if (iso) text.value = _deFmt(iso);
    _deSetIso(wrap, iso);
  });
}

document.addEventListener('input', function (e) {
  const text = e.target.closest && e.target.closest('.date-es-text');
  if (text) _deSetIso(text.closest('.date-es'), _deParse(text.value));
});
document.addEventListener('change', function (e) {
  const nat = e.target.closest && e.target.closest('.date-es-native');
  if (nat) {
    const wrap = nat.closest('.date-es');
    wrap.querySelector('.date-es-text').value = _deFmt(nat.value);
    wrap.querySelector('.date-es-iso').value = nat.value;
  }
});
document.addEventListener('click', function (e) {
  const btn = e.target.closest && e.target.closest('.date-es-cal');
  if (btn) {
    const nat = btn.closest('.date-es').querySelector('.date-es-native');
    if (nat) { if (nat.showPicker) nat.showPicker(); else { nat.focus(); nat.click(); } }
  }
});

document.addEventListener('DOMContentLoaded', function () { initDateEs(document); });
