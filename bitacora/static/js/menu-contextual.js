// Menú del clic derecho, con la estética de la app. Mismo camino que confirmar.js: el menú del
// navegador es el de un sitio web ("127.0.0.1:65015 dice"), no el de un programa propio.
//
// ⚠️ NO se intercepta sobre un campo de texto ni con algo seleccionado: ahí tiene que salir el
// menú nativo o se pierden *pegar* y *copiar*, que en el modo navegador es un costo real. Se gana
// poco y se rompe algo que la gente usa todos los días.
(function () {
  const ITEMS = [
    {
      texto: 'Reiniciar esta vista',
      detalle: 'Los tamaños, los desplegables y el zoom vuelven a como vienen de fábrica.',
      // El zoom es de toda la app y también se va: se pidió así, y por eso el detalle lo dice
      // en vez de sorprender — mismo criterio que los botones que nombran su acción.
      accion: () => window.prefReiniciarVista().then(() => location.reload()),
    },
    { texto: 'Ir a hoy', accion: () => { location.href = '/day/' + hoyISO(); } },
    { texto: 'Ajustes',  accion: () => { location.href = '/ajustes'; } },
  ];

  function hoyISO() {
    const d = new Date();
    const p = (n) => String(n).padStart(2, '0');
    return d.getFullYear() + '-' + p(d.getMonth() + 1) + '-' + p(d.getDate());
  }

  let menu = null;

  function cerrar() {
    if (!menu) return;
    menu.remove();
    menu = null;
  }

  function abrir(x, y) {
    cerrar();
    menu = document.createElement('div');
    menu.className = 'menu-ctx';
    ITEMS.forEach((item) => {
      const b = document.createElement('button');
      b.type = 'button';
      b.className = 'menu-ctx-item';
      b.textContent = item.texto;
      if (item.detalle) b.title = item.detalle;
      b.addEventListener('click', () => { cerrar(); item.accion(); });
      menu.appendChild(b);
    });
    document.body.appendChild(menu);

    // Que no se salga de la ventana: se mide después de insertarlo porque el alto depende de
    // cuántos ítems tenga, que es lo que va a ir cambiando.
    const r = menu.getBoundingClientRect();
    const ancho = document.documentElement.clientWidth;
    const alto = document.documentElement.clientHeight;
    menu.style.left = Math.min(x, ancho - r.width - 8) + 'px';
    menu.style.top = Math.min(y, alto - r.height - 8) + 'px';
  }

  function esCampoDeTexto(el) {
    return !!(el && el.closest && el.closest('input, textarea, select, [contenteditable="true"]'));
  }

  document.addEventListener('contextmenu', (e) => {
    if (esCampoDeTexto(e.target)) return;                       // pegar
    const sel = window.getSelection();
    if (sel && String(sel).trim()) return;                      // copiar
    e.preventDefault();
    abrir(e.clientX, e.clientY);
  });

  document.addEventListener('click', (e) => { if (!menu || !menu.contains(e.target)) cerrar(); });
  window.addEventListener('blur', cerrar);
  window.addEventListener('resize', cerrar);
  document.addEventListener('scroll', cerrar, true);
  // Primero en la cadena de Escape de base.html: lo último que abriste es lo primero que se
  // cierra, y el handler global no tiene que enterarse.
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape' && menu) { e.stopPropagation(); cerrar(); }
  }, true);
})();
