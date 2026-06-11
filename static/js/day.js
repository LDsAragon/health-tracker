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
  if (!open) {
    const c = document.getElementById('jday-cat'); if (c) c.value = '';
    const fl = document.getElementById('jday-fields'); if (fl) fl.innerHTML = '';
  }
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
  if (!catId) { alert('Seleccioná una categoría.'); return false; }
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
window.addEventListener('DOMContentLoaded', function () {
  document.querySelectorAll('.emotion-wheel-picker[data-ew-saved]').forEach(p => {
    if (p.dataset.ewSaved) ewRestore(p, p.dataset.ewSaved);
  });
});
