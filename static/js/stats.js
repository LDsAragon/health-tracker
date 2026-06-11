// Constructor de gráficos: pobla el select de campos según la categoría elegida.
function statsPopulateFields() {
  const cats = window.BUILDER_CATS || [];
  const catSel = document.getElementById('builder-cat');
  const fieldSel = document.getElementById('builder-field');
  if (!catSel || !fieldSel) return;
  const cat = cats.find(c => String(c.id) === catSel.value);
  const esc = s => s.replace(/"/g, '&quot;');
  fieldSel.innerHTML = '<option value="">Campo…</option>' +
    (cat ? cat.fields.map(f => '<option value="' + esc(f) + '">' + f + '</option>').join('') : '');
}

// Instancia un Chart.js por cada gráfico que pasó el backend (window.STATS_CHARTS).
(function () {
  const charts = window.STATS_CHARTS || [];
  const css = getComputedStyle(document.documentElement);
  const accent = (css.getPropertyValue('--accent').trim() || '#6366f1');
  const muted = (css.getPropertyValue('--muted').trim() || '#8892a4');
  const grid = (css.getPropertyValue('--border').trim() || '#2e3148');

  charts.forEach((c, i) => {
    const el = document.getElementById('chart-' + i);
    if (!el || typeof Chart === 'undefined') return;
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
          y: { ticks: { color: muted }, grid: { color: grid }, beginAtZero: c.kind === 'bar' },
        },
      },
    });
  });
})();
