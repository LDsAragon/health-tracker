// Constructor de gráficos: pobla los selects según la categoría elegida.
// Campos llegan como {label, type}; los `opciones` también van al select de desglose.
const STATS_NUM_TYPES = ['numero', 'escala', 'duracion', 'rango'];

// Todas estas funciones reciben un `suf` —vacío en el alta, "-<id>" en cada tarjeta que se
// edita— porque el mismo constructor se rinde varias veces en la pantalla. Con ids fijos, editar
// un gráfico habría rellenado los selects del alta.
const _sel = (base, suf) => document.getElementById(base + (suf || ''));
const _esc = s => s.replace(/"/g, '&quot;');
const _opt = f => '<option value="' + _esc(f.label) + '">' + f.label + '</option>';
const _cat = suf => (window.BUILDER_CATS || [])
  .find(c => String(c.id) === (_sel('builder-cat', suf) || {}).value);

function statsPopulateFields(suf) {
  const catSel = _sel('builder-cat', suf);
  if (!catSel) return;
  const cat = _cat(suf);

  const fields = cat ? cat.fields : [];
  _sel('builder-field', suf).innerHTML =
    '<option value="">Campo…</option>' + fields.map(_opt).join('');

  // Desglose: solo si la categoría tiene campos `opciones`
  const groupSel = _sel('builder-group', suf);
  const groups = cat ? cat.group_fields : [];
  groupSel.innerHTML = '<option value="">Sin desglose</option>' +
    groups.map(g => '<option value="' + _esc(g) + '">por ' + g + '</option>').join('');
  groupSel.style.display = groups.length ? '' : 'none';
  if (!groups.length) groupSel.value = '';

  // Campo extra a sumar: solo si hay 2+ campos numéricos (ej. Horas + Franja)
  const numFields = fields.filter(f => STATS_NUM_TYPES.includes(f.type));
  const f2 = _sel('builder-field2', suf);
  f2.innerHTML = '<option value="">+ sumar otro campo…</option>' + numFields.map(_opt).join('');
  f2.style.display = numFields.length >= 2 ? '' : 'none';
  if (numFields.length < 2) f2.value = '';
  statsGroupChanged(suf);
}

// Al desglosar, el campo a graficar tiene que ser numérico (las sumas por grupo
// no tienen sentido para sino/opciones).
function statsGroupChanged(suf) {
  const cat = _cat(suf);
  if (!cat) return;
  const grouped = _sel('builder-group', suf).value !== '';
  const fieldSel = _sel('builder-field', suf);
  const prev = fieldSel.value;
  const pool = grouped ? cat.fields.filter(f => STATS_NUM_TYPES.includes(f.type)) : cat.fields;
  fieldSel.innerHTML = '<option value="">Campo…</option>' + pool.map(_opt).join('');
  if (pool.some(f => f.label === prev)) fieldSel.value = prev;
}

// ── Editar un gráfico guardado ──────────────────────────────────────────────

function statsEditar(id) {
  const f = document.getElementById('stats-edit-' + id);
  f.style.display = f.style.display === 'none' ? 'flex' : 'none';
}

// ⚠️ El ORDEN acá no es libre: las opciones de Campo dependen de la categoría, y encima
// `statsGroupChanged` vuelve a armar ese select filtrando a los numéricos cuando hay desglose.
// Así que primero las opciones, después el desglose, y el campo AL FINAL — al revés, elegir el
// desglose le borraría al campo el valor recién puesto y la tarjeta abriría con "Campo…" vacío
// justo en los gráficos más armados, que son los que menos ganas dan de rehacer.
function statsInicializar(form) {
  const suf = form.dataset.suf;
  statsPopulateFields(suf);
  _elegir(_sel('builder-group', suf), form.dataset.grupo);
  statsGroupChanged(suf);
  _elegir(_sel('builder-field', suf), form.dataset.campo);
  _elegir(_sel('builder-field2', suf), form.dataset.campo2);
}

// ⚠️ Un valor que ya no está entre las opciones deja al `<select>` en selectedIndex = -1, que se
// dibuja **en blanco** — ni el campo viejo ni el "Campo…". Justo en la tarjeta rota, que es la
// que más necesita decir qué hay que elegir. Así cae en el placeholder.
function _elegir(select, valor) {
  if (!select) return;
  select.value = [...select.options].some(o => o.value === valor) ? valor : '';
}

document.querySelectorAll('.stats-card-edit').forEach(statsInicializar);

// Instancia un Chart.js por cada gráfico que pasó el backend (window.STATS_CHARTS).
(function () {
  const charts = window.STATS_CHARTS || [];
  const css = getComputedStyle(document.documentElement);
  const accent = (css.getPropertyValue('--accent').trim() || '#6366f1');
  const muted = (css.getPropertyValue('--muted').trim() || '#8892a4');
  const grid = (css.getPropertyValue('--border').trim() || '#2e3148');
  const PALETTE = ['#6366f1', '#22c55e', '#f97316', '#3b82f6', '#ef4444',
                   '#a855f7', '#ec4899', '#eab308', '#14b8a6'];

  charts.forEach((c, i) => {
    const el = document.getElementById('chart-' + i);
    if (!el || typeof Chart === 'undefined') return;

    if (c.kind === 'stacked') {
      // Barras apiladas: una serie por grupo (desglose), sumadas por día/semana/mes
      new Chart(el, {
        type: 'bar',
        data: {
          labels: c.labels,
          datasets: c.datasets.map((d, j) => ({
            label: d.label,
            data: d.data,
            backgroundColor: PALETTE[j % PALETTE.length] + 'cc',
          })),
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: c.datasets.length > 1, labels: { color: muted } } },
          scales: {
            x: { stacked: true, ticks: { color: muted, maxRotation: 0, autoSkip: true }, grid: { color: grid } },
            y: { stacked: true, beginAtZero: true, ticks: { color: muted },
                 grid: { color: grid },
                 title: c.unit ? { display: true, text: c.unit, color: muted } : undefined },
          },
        },
      });
      return;
    }

    new Chart(el, {
      type: c.kind,
      data: {
        labels: c.labels,
        datasets: [{
          label: c.title,
          data: c.data,
          borderColor: accent,
          backgroundColor: c.kind === 'bar' ? accent + '99' : accent + '33',
          tension: 0.25,
          pointRadius: 2,
          fill: c.kind === 'line',
        }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { ticks: { color: muted, maxRotation: 0, autoSkip: true }, grid: { color: grid } },
          y: { ticks: { color: muted }, grid: { color: grid }, beginAtZero: c.kind === 'bar',
               title: c.unit ? { display: true, text: c.unit, color: muted } : undefined },
        },
      },
    });
  });
})();
