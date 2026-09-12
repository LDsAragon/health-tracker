// Guardado al instante de la pantalla de Ajustes.
//
// El botón "Guardar" NO se borra de la plantilla: lo esconde este archivo. Si el JS se rompe
// o no carga, queda visible y el <form> de siempre sigue andando — sin eso, un JS muerto
// dejaría los ajustes imposibles de cambiar.
(function () {
  const form = document.getElementById('ajustes-form');
  if (!form) return;

  document.querySelectorAll('.set-guardar-fallback').forEach(el => { el.hidden = true; });

  const aviso = document.getElementById('set-guardado');
  let timer = null;
  function confirmar() {
    if (!aviso) return;
    aviso.classList.add('visible');
    clearTimeout(timer);
    timer = setTimeout(() => aviso.classList.remove('visible'), 1400);
  }

  function guardar(key, value) {
    const body = new URLSearchParams({ key: key, value: value });
    return fetch(SET_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: body.toString(),
    });
  }

  form.addEventListener('change', ev => {
    const el = ev.target;
    if (!el.name) return;

    // El checkbox del switch manda el par que le toca a ESE ajuste: los 8 switches no
    // comparten vocabulario (on/off, show/hide, open/collapsed).
    const value = el.type === 'checkbox'
      ? (el.checked ? el.dataset.on : el.dataset.off)
      : el.value;
    if (value === undefined) return;

    // El tema se aplica en el acto y ya queda guardado: no hay más previsualizar-y-confirmar.
    if (el.name === 'theme') {
      document.documentElement.setAttribute('data-theme', value);
      form.querySelectorAll('.theme-swatch').forEach(s => {
        s.classList.toggle('active', s.contains(el));
      });
    }

    // ⚠️ Estos cambian el navbar, que se renderiza en el servidor: guardar sin recargar los
    // persiste pero el tab no aparece, y se lee como "no pasó nada".
    const recargar = el.closest('[data-recargar]') !== null;

    guardar(el.name, value).then(r => {
      if (!r.ok) { window.location.reload(); return; }   // rechazado: volver a la verdad
      if (recargar) { window.location.reload(); return; }
      confirmar();
    }).catch(() => window.location.reload());
  });
})();
