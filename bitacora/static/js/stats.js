// Constructor de gráficos: pobla los selects según la categoría elegida.
// Campos llegan como {label, type}; los `opciones` también van al select de desglose.
const STATS_NUM_TYPES = ['numero', 'escala', 'duracion', 'rango'];

function statsPopulateFields() {
  const cats = window.BUILDER_CATS || [];
  const catSel = document.getElementById('builder-cat');
  const cat = cats.find(c => String(c.id) === catSel.value);
  const esc = s => s.replace(/"/g, '&quot;');
  const opt = f => '<option value="' + esc(f.label) + '">' + f.label + '</option>';

  const fields = cat ? cat.fields : [];
  document.getElementById('builder-field').innerHTML =
    '<option value="">Campo…</option>' + fields.map(opt).join('');

  // Desglose: solo si la categoría tiene campos `opciones`
  const groupSel = document.getElementById('builder-group');
  const groups = cat ? cat.group_fields : [];
  groupSel.innerHTML = '<option value="">Sin desglose</option>' +
    groups.map(g => '<option value="' + esc(g) + '">por ' + g + '</option>').join('');
  groupSel.style.display = groups.length ? '' : 'none';
  if (!groups.length) groupSel.value = '';

  // Campo extra a sumar: solo si hay 2+ campos numéricos (ej. Horas + Franja)
  const numFields = fields.filter(f => STATS_NUM_TYPES.includes(f.type));
  const f2 = document.getElementById('builder-field2');
  f2.innerHTML = '<option value="">+ sumar otro campo…</option>' + numFields.map(opt).join('');
  f2.style.display = numFields.length >= 2 ? '' : 'none';
  if (numFields.length < 2) f2.value = '';
  statsGroupChanged();
}

// Al desglosar, el campo a graficar tiene que ser numérico (las sumas por grupo
// no tienen sentido para sino/opciones).
function statsGroupChanged() {
  const cats = window.BUILDER_CATS || [];
  const cat = cats.find(c => String(c.id) === document.getElementById('builder-cat').value);
  if (!cat) return;
  const grouped = document.getElementById('builder-group').value !== '';
  const fieldSel = document.getElementById('builder-field');
  const prev = fieldSel.value;
  const esc = s => s.replace(/"/g, '&quot;');
  const pool = grouped ? cat.fields.filter(f => STATS_NUM_TYPES.includes(f.type)) : cat.fields;
  fieldSel.innerHTML = '<option value="">Campo…</option>' +
    pool.map(f => '<option value="' + esc(f.label) + '">' + f.label + '</option>').join('');
  if (pool.some(f => f.label === prev)) fieldSel.value = prev;
}

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
