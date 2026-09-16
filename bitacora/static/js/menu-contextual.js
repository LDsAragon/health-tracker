// Menú del clic derecho, con la estética de la app. Mismo camino que confirmar.js: el menú del
// navegador es el de un sitio web ("127.0.0.1:65015 dice"), no el de un programa propio.
//
// ⚠️ NO se intercepta sobre un campo de texto ni con algo seleccionado: ahí tiene que salir el
// menú nativo o se pierden *pegar* y *copiar*, que en el modo navegador es un costo real. Se gana
// poco y se rompe algo que la gente usa todos los días.
(function () {
  // El destino de una emoción anotada desde acá: la primera categoría con campo de rueda,
  // normalmente la "Emociones" que la app trae de fábrica. Si no hay ninguna, los dos ítems no
  // se ofrecen: es mejor que falte el atajo a inventarle una categoría a alguien.
  const DESTINO = window.EMOCION_DESTINO || null;

  function items() {
    const lista = [];
    if (DESTINO) {
      lista.push({
        texto: '🎯 Anotar emoción · Willcox',
        detalle: 'Abre la rueda y guarda lo que elijas en ' + DESTINO.nombre + ', con fecha de hoy.',
        accion: () => anotarEmocion('es'),
      });
      lista.push({
        texto: '🧭 Anotar emoción · Ekman',
        detalle: 'Abre la rueda y guarda lo que elijas en ' + DESTINO.nombre + ', con fecha de hoy.',
        accion: () => anotarEmocion('ek'),
      });
      lista.push({ separador: true });
    }
    lista.push({ texto: 'Ir a hoy', accion: () => { location.href = '/day/' + hoyISO(); } });
    lista.push({ texto: 'Ajustes',  accion: () => { location.href = '/ajustes'; } });
    lista.push({ separador: true });
    lista.push({
      texto: 'Reiniciar esta vista',
      detalle: 'Los tamaños, los desplegables y el zoom vuelven a como vienen de fábrica.',
      // El zoom es de toda la app y también se va: se pidió así, y por eso el detalle lo dice
      // en vez de sorprender — mismo criterio que los botones que nombran su acción.
      accion: () => window.prefReiniciarVista().then(() => location.reload()),
    });
    return lista;
  }

  // ── Anotar una emoción sin pasar por el día ───────────────────────────────
  // Se arma un picker de los de siempre —el mismo que usa el formulario del día— fuera de la
  // pantalla, se abre la rueda apuntándole, y al cerrarla se guarda lo que haya quedado adentro.
  // Reusar el picker es lo que evita una segunda forma de leer la selección de la rueda.
  function anotarEmocion(rueda) {
    const caja = document.createElement('div');
    caja.style.display = 'none';
    caja.innerHTML = buildEWPicker(DESTINO.campo);
    document.body.appendChild(caja);
    const picker = caja.querySelector('.emotion-wheel-picker');

    // La rueda no avisa cuando se cierra, así que se envuelve `closeEWModal` mientras dura este
    // uso y se restaura enseguida: es lo mismo que hace refresco.js con `fetch`.
    const original = window.closeEWModal;
    window.closeEWModal = function () {
      window.closeEWModal = original;
      original();
      const valor = (picker.querySelector('[data-ew-value]') || {}).value || '';
      caja.remove();
      if (valor) guardarEmocion(valor);
    };
    openEWModal(picker, rueda);
  }

  function guardarEmocion(valor) {
    const valores = {};
    valores[DESTINO.campo] = valor;
    const hoy = hoyISO();
    fetch('/day/' + hoy + '/journal/add', {
      method: 'POST',
      body: new URLSearchParams({ category_id: DESTINO.id, values_json: JSON.stringify(valores) }),
    }).then(() => {
      // Parado en el día de hoy la nota tiene que aparecer; en cualquier otra pantalla no se
      // vería nada, y guardar sin señal se siente como que no pasó.
      if (location.pathname === '/day/' + hoy) location.reload();
      else aviso('✓ Anotada en hoy: ' + valor, hoy);
    }).catch(() => aviso('No se pudo guardar la emoción', null));
  }

  function aviso(texto, dia) {
    const caja = document.createElement('div');
    caja.className = 'menu-ctx-aviso';
    caja.textContent = texto + ' ';
    if (dia) {
      const a = document.createElement('a');
      a.href = '/day/' + dia;
      a.textContent = 'Ver el día';
      caja.appendChild(a);
    }
    document.body.appendChild(caja);
    setTimeout(() => caja.remove(), 6000);
  }

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
    items().forEach((item) => {
      if (item.separador) {
        menu.appendChild(document.createElement('hr')).className = 'menu-ctx-sep';
        return;
      }
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
