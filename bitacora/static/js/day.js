// JS de la vista del día. El contexto Jinja llega por window.DAY_CTX (ver day.html).
const today = DAY_CTX.today;

function openEvForm(id) {
  document.getElementById('ev-chip-' + id).style.display = 'none';
  const f = document.getElementById('ev-form-' + id);
  f.style.display = 'flex';
  f.querySelector('input').focus();
}
function closeEvForm(id) {
  document.getElementById('ev-form-' + id).style.display = 'none';
  document.getElementById('ev-chip-' + id).style.display = 'flex';
}

// ── To-dos ──────────────────────────────────────────────────────────────────
function editTodo(id) {
  document.getElementById('todo-row-' + id).style.display = 'none';
  document.getElementById('todo-move-' + id).style.display = 'none';
  const f = document.getElementById('todo-edit-' + id);
  f.style.display = 'flex';
  f.querySelector('input').focus();
}
function cancelTodo(id) {
  document.getElementById('todo-edit-' + id).style.display = 'none';
  document.getElementById('todo-row-' + id).style.display = 'flex';
}
function moveTodo(id) {
  document.getElementById('todo-row-' + id).style.display = 'none';
  document.getElementById('todo-edit-' + id).style.display = 'none';
  document.getElementById('todo-move-' + id).style.display = 'flex';
}
function cancelTodoMove(id) {
  document.getElementById('todo-move-' + id).style.display = 'none';
  document.getElementById('todo-row-' + id).style.display = 'flex';
}

// Drag & drop para reordenar dentro del día
(function () {
  const ul = document.getElementById('todo-list');
  if (!ul) return;
  const REORDER_URL = DAY_CTX.reorderUrl;
  let dragging = null;

  ul.addEventListener('dragstart', function (e) {
    const li = e.target.closest('.todo-item');
    if (!li) return;
    dragging = li;
    li.classList.add('todo-dragging');
    e.dataTransfer.effectAllowed = 'move';
  });

  ul.addEventListener('dragend', function () {
    if (!dragging) return;
    dragging.classList.remove('todo-dragging');
    dragging = null;
    persistOrder();
  });

  ul.addEventListener('dragover', function (e) {
    e.preventDefault();
    if (!dragging) return;
    const over = e.target.closest('.todo-item');
    if (!over || over === dragging) return;
    const rect = over.getBoundingClientRect();
    const after = (e.clientY - rect.top) > rect.height / 2;
    ul.insertBefore(dragging, after ? over.nextSibling : over);
  });

  function persistOrder() {
    const ids = Array.from(ul.querySelectorAll('.todo-item')).map(li => li.dataset.id);
    fetch(REORDER_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: 'order=' + ids.join(','),
    });
  }
})();
function editDayNote(id) {
  document.getElementById('dview-' + id).style.display = 'none';
  document.getElementById('dedit-' + id).style.display = 'flex';
}
function cancelDayNote(id) {
  document.getElementById('dedit-' + id).style.display = 'none';
  document.getElementById('dview-' + id).style.display = 'flex';
  const note = document.getElementById('dnote-' + id);
  applyNoteColor(note, note.dataset.color || '');   // revertir al color guardado
  document.getElementById('dedit-' + id).reset();     // y restaurar el radio elegido
}
// Pinta la nota con el color (vacío = sin color) — significador en vivo de la selección
function applyNoteColor(note, color) {
  if (color) { note.style.setProperty('--c', color); note.classList.add('day-note-colored'); }
  else       { note.style.removeProperty('--c');      note.classList.remove('day-note-colored'); }
}
function previewNoteColor(id, color) {
  applyNoteColor(document.getElementById('dnote-' + id), color);
}
// Ídem para el alta de nota rápida: tiñe el textarea con el color elegido
function previewAddColor(color) {
  const ta = document.querySelector('#rapida-form .day-add-input');
  if (color) { ta.style.setProperty('--c', color); ta.classList.add('day-add-colored'); }
  else       { ta.style.removeProperty('--c');      ta.classList.remove('day-add-colored'); }
}

// Journal
const DAY_JOURNAL_CATS = DAY_CTX.cats;

function buildFields(containerId, catId) {
  const container = document.getElementById(containerId);
  if (!catId) { container.innerHTML = ''; return; }
  const cat = DAY_JOURNAL_CATS.find(c => c.id == catId);
  if (!cat || !cat.fields || !cat.fields.length) { container.innerHTML = ''; return; }
  container.innerHTML = cat.fields.map(f => {
    const type = (f.type || 'text');
    const build = (window.FIELD_BUILDERS || {})[type];
    if (build) return build(f.label, f.placeholder);
    return '<div class="day-journal-field-input">' +
      '<label>' + f.label + '</label>' +
      '<textarea data-label="' + f.label.replace(/"/g, '&quot;') + '" placeholder="' +
      (f.placeholder || '').replace(/"/g, '&quot;') + '" rows="3" class="note-edit-ta"></textarea>' +
      '</div>';
  }).join('');
}

function updateDayFields(catId) { buildFields('jday-fields', catId); }

// ── Chips de categoría (alta de nota especial) ─────────────────────────────
function _jcatNorm(s) {
  return s.toLowerCase().normalize('NFD').replace(/[̀-ͯ]/g, '');
}
function selectJCat(btn) {
  document.querySelectorAll('#jday-cat-chips .jcat-chip').forEach(b =>
    b.classList.toggle('jcat-chip-sel', b === btn));
  const hidden = document.getElementById('jday-cat');
  const error  = document.getElementById('jday-cat-error');
  if (error) error.style.display = 'none';
  // Re-elegir la que ya estaba NO reconstruye los campos: eso vaciaría lo que ya escribiste.
  if (hidden.value !== btn.dataset.id) {
    hidden.value = btn.dataset.id;
    updateDayFields(btn.dataset.id);
  }
  _jcatColapsar(btn);
}

// Colapsar / expandir el selector. El estado "elegida" muestra solo el chip que clickeaste (el
// mismo elemento, con el mismo estilo) y tiñe el formulario con el color de la categoría, que es
// lo que ata visualmente "estoy escribiendo una nota de Sueño".
function _jcatColapsar(btn) {
  const chips = document.getElementById('jday-cat-chips');
  const eleg  = document.getElementById('jday-cat-elegida');
  const chip  = document.getElementById('jday-cat-chip');
  if (!chips || !eleg || !chip) return;
  const color = btn.dataset.color || '#6366f1';
  chip.textContent = btn.dataset.name;
  chip.style.setProperty('--c', color);
  chips.style.display = 'none';
  const f = document.getElementById('jday-cat-filter');
  if (f) { f.style.display = 'none'; f.value = ''; filterJCats(''); }
  eleg.style.display = 'flex';
  // Con una sola categoría no hay nada que cambiar.
  const cambiar = document.getElementById('jday-cat-cambiar');
  if (cambiar) {
    cambiar.style.display =
      document.querySelectorAll('#jday-cat-chips .jcat-chip').length > 1 ? '' : 'none';
  }
  const wrap = document.getElementById('jday-form-wrap');
  if (wrap) { wrap.style.setProperty('--c', color); wrap.classList.add('jday-form-cat'); }
}
function _jcatExpandir() {
  const chips = document.getElementById('jday-cat-chips');
  const eleg  = document.getElementById('jday-cat-elegida');
  const f     = document.getElementById('jday-cat-filter');
  if (chips) chips.style.display = '';
  if (f) f.style.display = '';
  if (eleg) eleg.style.display = 'none';
}
// No toca el hidden ni los campos: arrepentirse de cambiar no puede borrar lo que escribiste.
function cambiarJCat() { _jcatExpandir(); }

// Con una sola categoría se elige sola: pedir un clic entre una opción no decide nada. Corre al
// abrir el alta y también al cargar, porque con `journal_form_default = open` nadie la abre.
function _jcatAutoElegir() {
  const wrap = document.getElementById('jday-form-wrap');
  if (!wrap || wrap.style.display === 'none') return;
  const chips  = document.querySelectorAll('#jday-cat-chips .jcat-chip');
  const hidden = document.getElementById('jday-cat');
  if (chips.length === 1 && hidden && !hidden.value) selectJCat(chips[0]);
}
function filterJCats(q) {
  q = _jcatNorm(q.trim());
  document.querySelectorAll('#jday-cat-chips .jcat-chip').forEach(b => {
    b.style.display = !q || _jcatNorm(b.dataset.name).includes(q) ? '' : 'none';
  });
}

// Alternancia: solo una alta activa a la vez (cada una colapsable en su lugar).
function _setRapida(open) {
  const f = document.getElementById('rapida-form');
  const b = document.getElementById('rapida-collapsed');
  if (f) f.style.display = open ? '' : 'none';
  if (b) b.style.display = open ? 'none' : 'block';
}
function _setEspecial(open) {
  const w = document.getElementById('jday-form-wrap');
  const t = document.getElementById('jday-toggle');
  if (w) w.style.display = open ? 'block' : 'none';
  if (t) t.style.display = open ? 'none' : 'block';
  if (open) { _jcatAutoElegir(); return; }
  const c = document.getElementById('jday-cat'); if (c) c.value = '';
  const fl = document.getElementById('jday-fields'); if (fl) fl.innerHTML = '';
  document.querySelectorAll('#jday-cat-chips .jcat-chip-sel').forEach(b =>
    b.classList.remove('jcat-chip-sel'));
  const ff = document.getElementById('jday-cat-filter');
  if (ff) { ff.value = ''; filterJCats(''); }
  _jcatExpandir();
  if (w) { w.style.removeProperty('--c'); w.classList.remove('jday-form-cat'); }
}
function openEspecial()    { _setEspecial(true);  _setRapida(false); }
function closeEspecial()   { _setEspecial(false); _setRapida(true);  }
function openRapida()      { _setRapida(true);    _setEspecial(false); }
function collapseRapida()  { _setRapida(false); }

function collectValues(containerId) {
  const container = document.getElementById(containerId);
  const values = {};
  container.querySelectorAll('textarea[data-label], input[data-label]').forEach(el => {
    values[el.dataset.label] = el.value;
  });
  collectEWValues(container, values);
  return JSON.stringify(values);
}

function prepareNewValues() {
  const catId = document.getElementById('jday-cat').value;
  const error = document.getElementById('jday-cat-error');
  if (!catId) {
    // Inline y no un diálogo: es una validación de formulario, y el mensaje tiene que quedar al
    // lado de lo que falta completar. Mismo patrón que el #weekday-error de Rutinas.
    if (error) {
      error.style.display = 'block';
      document.getElementById('jday-cat-chips').scrollIntoView({ block: 'nearest' });
    }
    return false;
  }
  if (error) error.style.display = 'none';
  document.getElementById('jday-values-json').value = collectValues('jday-fields');
  return true;
}

function editJEntry(id) {
  document.getElementById('jview-' + id).style.display = 'none';
  document.getElementById('jedit-' + id).style.display = 'flex';
}
function cancelJEntry(id) {
  document.getElementById('jedit-' + id).style.display = 'none';
  document.getElementById('jview-' + id).style.display = 'flex';
}
function prepareEditValues(id) {
  document.getElementById('jedit-values-' + id).value = collectValues('jedit-' + id);
  return true;
}

// Restaurar valores de rueda de emociones en formularios de edición existentes.
function restaurarRuedas(raiz) {
  (raiz || document).querySelectorAll('.emotion-wheel-picker[data-ew-saved]').forEach(p => {
    if (p.dataset.ewSaved) ewRestore(p, p.dataset.ewSaved);
  });
}

window.addEventListener('DOMContentLoaded', function () {
  restaurarRuedas(document);
  _jcatAutoElegir();
});

// ⚠️ Las notas especiales son una zona `data-refresco`: cuando el refresco reemplaza su
// contenido, las ruedas que vengan adentro llegan sin restaurar. Es el único init por elemento
// que vive dentro de una zona — el drag & drop de tareas no hace falta porque está enganchado al
// <ul>, que no se reemplaza.
window.BITACORA_REINIT = window.BITACORA_REINIT || [];
window.BITACORA_REINIT.push(restaurarRuedas);


// ── Paneles del día: ancho y alto arrastrables ───────────────────────────────
// Un solo helper para los tres agarres (el ancho, y el alto de cada panel). Tres copias de esto
// serían tres copias de la misma trampa, la del "pedido vs. medido" que está anotada abajo.
(function () {
  /**
   * Cablea un agarre.
   *   grip      el elemento que se arrastra
   *   eje       'x' | 'y'
   *   variable  la custom property que se setea en :root
   *   pref      la clave de localStorage
   *   minimo    px
   *   maximo()  tope, calculado en el momento (depende del tamaño de la ventana)
   *   medir()   el tamaño actual, para arrancar el arrastre si no hay valor pedido
   */
  function arrastrable({ grip, eje, variable, pref, minimo, maximo, medir }) {
    if (!grip) return;
    const raiz = document.documentElement.style;

    // ⚠️ Se guarda el valor PEDIDO y no el medido. Midiendo, cada recarga lo encogía un poco
    // (402 → 354 → 306...): el tamaño real puede ser menor que el pedido si no hay lugar, y
    // guardar ese valor lo iba achicando en cada vuelta.
    let pedido = null;

    const acotar = (v) => Math.min(maximo(), Math.max(minimo, Math.round(v)));

    function aplicar(v) {
      pedido = acotar(v);
      raiz.setProperty(variable, pedido + 'px');
    }

    try {
      const v = parseInt(localStorage.getItem(pref), 10);
      if (Number.isFinite(v)) aplicar(v);
    } catch (e) { /* modo privado */ }

    let arrastrando = false, origen = 0, inicial = 0;
    const coord = (e) => (eje === 'x' ? e.clientX : e.clientY);

    grip.addEventListener('pointerdown', (e) => {
      arrastrando = true;
      origen = coord(e);
      inicial = pedido || medir();
      grip.classList.add('arrastrando');
      document.body.classList.add('day-redimensionando');
      // Capturar el puntero: sin esto, al salirse del agarre el arrastre se corta. Tira si el
      // pointerId no está activo (un evento sintético), y ahí el arrastre igual funciona.
      try { grip.setPointerCapture(e.pointerId); } catch (err) { /* sin captura */ }
      e.preventDefault();
    });

    grip.addEventListener('pointermove', (e) => {
      if (arrastrando) aplicar(inicial + (coord(e) - origen));
    });

    function terminar() {
      if (!arrastrando) return;
      arrastrando = false;
      grip.classList.remove('arrastrando');
      document.body.classList.remove('day-redimensionando');
      try { localStorage.setItem(pref, String(pedido)); } catch (e) { /* modo privado */ }
    }
    grip.addEventListener('pointerup', terminar);
    grip.addEventListener('pointercancel', terminar);

    grip.addEventListener('dblclick', () => {
      pedido = null;
      raiz.removeProperty(variable);          // vuelve al default del CSS
      try { localStorage.removeItem(pref); } catch (e) { /* modo privado */ }
    });

    // Al achicar la ventana, re-acotar sin pisar lo elegido: un tamaño de un monitor grande no
    // puede romper el layout en una ventana chica, pero al volver a agrandarla tiene que volver.
    window.addEventListener('resize', () => {
      if (pedido !== null) raiz.setProperty(variable, acotar(pedido) + 'px');
    });
  }

  // ── El ancho, compartido por los dos paneles ──────────────────────────────
  // El tope sale de la pantalla y no es un número fijo: el conjunto mide 2 paneles + la card
  // (760) + los gaps, así que lo que sobra se reparte entre los dos lados. En un monitor de
  // 2560 eso da ~856 por lado; con un 560 fijo quedaba media pantalla sin usar.
  const ANCHO_MIN = 200, ANCHO_TOPE = 900, CARD = 760, GAPS = 40;
  const gripAncho = document.getElementById('day-side-grip');
  const panelIzq = gripAncho && gripAncho.closest('.day-side');
  // ⚠️ El tope depende de cuántos paneles haya. Con los dos, lo que sobra se reparte en dos
  // (mover un agarre ensancha los dos lados). Sin el de rutinas hay una columna menos y un gap
  // menos, así que dividir igual dejaba la mitad del espacio libre sin poder usar.
  const hayPanelDerecho = !!document.querySelector('.day-side-right');
  arrastrable({
    grip: gripAncho, eje: 'x', variable: '--day-side', pref: 'day_side_width',
    minimo: ANCHO_MIN,
    maximo: () => {
      const libre = document.documentElement.clientWidth - 48 - CARD
                    - (hayPanelDerecho ? GAPS : GAPS / 2);
      return Math.max(ANCHO_MIN,
                      Math.min(ANCHO_TOPE, Math.floor(hayPanelDerecho ? libre / 2 : libre)));
    },
    medir: () => panelIzq.getBoundingClientRect().width,
  });

  // ── El alto, uno por panel ────────────────────────────────────────────────
  // ⚠️ El tope va acá y NO como max-height en el CSS: un max-height fijo también aplicaría en
  // modo automático, y a alguien con treinta tareas le aparecería un scroll interno que hoy no
  // tiene. Y el tope es la ventana porque .day-side es `position: sticky`: un panel más alto que
  // la ventana deja de quedarse pegado y se va con el scroll.
  const ALTO_MIN = 140;
  const altoMaximo = () => Math.max(ALTO_MIN, document.documentElement.clientHeight - 40);

  document.querySelectorAll('.day-alto-grip').forEach((grip) => {
    const panel = grip.closest('.day-side').querySelector(grip.dataset.panel);
    if (!panel) return;
    arrastrable({
      grip, eje: 'y', variable: grip.dataset.var, pref: grip.dataset.pref,
      minimo: ALTO_MIN, maximo: altoMaximo,
      medir: () => panel.getBoundingClientRect().height,
    });
  });
})();
