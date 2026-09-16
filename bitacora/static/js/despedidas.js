// La muerte de una tarea: la animación que se reproduce al borrarla.
//
// La primera versión la dibujaba ENCIMA de la fila, con cuadros ASCII intercambiados cada 110ms.
// No se apreciaba —se encimaba con el texto que estaba borrando, en una fila de 34px— y seis
// cuadros no pueden verse fluidos. Ahora abre un modal, pone adentro **el texto de la tarea** y
// lo destruye de verdad: cada letra es un elemento y se va con su propia trayectoria.
//
// El motor es anime.js (vendorizado). Por debajo son transformaciones 3D de CSS, así que hay
// profundidad sin WebGL — que es lo que descartó three.js: en Linux la app corre con el renderer
// acelerado de WebKitGTK apagado a propósito porque crashea.
//
// ⚠️ LA REGLA QUE NO SE NEGOCIA: borrar no puede depender de esto. `despedir()` recibe el callback
// que envía el formulario y **tiene que llamarlo siempre**: si anime.js no cargó, si el catálogo
// viene vacío, si una coreografía tira o si la animación se cuelga, igual se llama —hay un tope
// duro por encima de todo—. Es el mismo criterio que el `onsubmit="return false;"` de
// confirmar.js y que el botón Guardar que sigue en la plantilla de Ajustes: la parte decorativa
// puede fallar, la acción no.
(function () {
  const CATALOGO = window.DESPEDIDAS || [];
  const TOPE_MS = 3000;          // pase lo que pase, a los 3 s el formulario se envía
  const AZAR = 'aleatorio';
  const APAGADO = 'off';

  function elegir(slug) {
    if (!CATALOGO.length || slug === APAGADO) return null;
    if (!slug || slug === AZAR) return CATALOGO[Math.floor(Math.random() * CATALOGO.length)];
    return CATALOGO.find((d) => d.slug === slug) || null;
  }

  function quietito() {
    try {
      return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    } catch (e) {
      return false;
    }
  }

  // ── La escena ──────────────────────────────────────────────────────────────

  function escena() {
    return {
      overlay: document.getElementById('despedida-modal'),
      bicho: document.getElementById('despedida-bicho'),
      texto: document.getElementById('despedida-texto'),
    };
  }

  // Una letra por elemento: es lo que permite que cada una se vaya por su lado. El espacio va
  // como espacio duro porque un <span> inline-block con un espacio normal mide cero.
  function repartir(cont, texto) {
    cont.textContent = '';
    const letras = [];
    Array.from(String(texto || '').slice(0, 120)).forEach(function (ch) {
      const s = document.createElement('span');
      s.className = 'despedida-l';
      s.textContent = ch === ' ' ? '\u00a0' : ch;
      cont.appendChild(s);
      letras.push(s);
    });
    return letras;
  }

  // El bicho se mueve con transformaciones —eso lo hace anime.js y es lo que da la fluidez—,
  // pero ADEMÁS puede animarse por dentro, cambiando de cuadro: la mandíbula que se abre y se
  // cierra, la cresta de la ola que rompe, la estela del meteorito que titila. Son las dos
  // mitades y hacen falta las dos: sin cuadros, un dibujo que se desplaza tieso; sin
  // transformaciones, la animación a saltos de una celda que ya se descartó.
  //
  // Es también lo que deja usar arte de las galerías de ASCII animado (asciiart.eu, ascii.co.uk)
  // o dibujar el propio con ASCII Motion, que es MIT: son listas de cuadros y entran acá.
  // ⚠️ Los cuadros de un bicho tienen que tener el mismo alto, o el dibujo salta de lugar al
  // pasar. `cuadros()` lo empareja.
  function cuadros(e, lista, ms) {
    const alto = Math.max.apply(null, lista.map(function (c) { return c.split('\n').length; }));
    const parejos = lista.map(function (c) {
      const filas = c.split('\n');
      while (filas.length < alto) filas.push('');
      return filas.join('\n');
    });
    let i = 0;
    e.bicho.textContent = parejos[0];
    e.reloj = setInterval(function () {
      i = (i + 1) % parejos.length;
      e.bicho.textContent = parejos[i];
    }, ms || 90);
  }

  // ── Las coreografías ───────────────────────────────────────────────────────
  // Una por animación del catálogo. Reciben el escenario ya armado y devuelven la línea de
  // tiempo; quien las llama engancha el final.
  //
  // ⚠️ Las claves tienen que ser EXACTAMENTE los slugs de bitacora/despedidas.py, que es de donde
  // salen las opciones del ajuste. Una animación elegible sin coreografía es un ajuste que no
  // hace nada. Hay un tripwire.

  const COREOGRAFIAS = {
    meteorito: function (e) {
      // La estela titila: tres cuadros y la roca siempre en el mismo lugar.
      cuadros(e, [
        '  .\n   \\\n    ☄',
        ' ·\n  \\\n    ☄',
        '  \'\n   \\\n    ☄',
      ], 70);
      return anime.timeline()
        .add({
          targets: e.bicho,
          translateX: [-e.ancho * 0.55, e.ancho * 0.30],
          translateY: [-170, 60],
          rotate: [-8, 14],
          opacity: [0, 1],
          duration: 560,
          easing: 'easeInQuad',
        })
        .add({
          // El impacto: las letras salen para todos lados y para el fondo.
          targets: e.letras,
          translateX: function () { return anime.random(-190, 190); },
          translateY: function () { return anime.random(-130, 210); },
          translateZ: function () { return anime.random(-240, 320); },
          rotateX: function () { return anime.random(-720, 720); },
          rotateZ: function () { return anime.random(-360, 360); },
          opacity: [1, 0],
          duration: 880,
          delay: anime.stagger(11, { from: 'center' }),
          easing: 'easeOutQuint',
        }, '-=90')
        .add({ targets: e.bicho, opacity: 0, scale: 2.4, duration: 320 }, '-=860');
    },

    ola: function (e) {
      // La cresta rompe: las dos filas de agua se corren una contra otra.
      cuadros(e, [
        '≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈\n ~~~~~~~~~~~~~~~',
        ' ≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈\n~~~~~~~~~~~~~~~~',
        '~≈~≈~≈~≈~≈~≈~≈~≈\n ≈~≈~≈~≈~≈~≈~≈~≈',
      ], 100);
      return anime.timeline()
        .add({
          targets: e.bicho,
          translateX: [-e.ancho * 0.9, e.ancho * 0.7],
          translateY: [50, 34],
          opacity: [0, 1],
          duration: 1050,
          easing: 'easeInOutSine',
        })
        .add({
          // Se la lleva: todas para el mismo lado, con la cresta.
          targets: e.letras,
          translateX: function () { return anime.random(150, 360); },
          translateY: function () { return anime.random(10, 95); },
          rotateZ: function () { return anime.random(-45, 45); },
          opacity: [1, 0],
          duration: 780,
          delay: anime.stagger(21, { from: 'first' }),
          easing: 'easeInOutQuad',
        }, '-=880')
        .add({ targets: e.bicho, opacity: 0, duration: 260 }, '-=240');
    },

    parca: function (e) {
      // ⚠️ Una calavera derecha y no un monigote que rota: el mismo dibujo girado se leía como un
      // garabato. Acá el sprite se queda en su lugar y el trabajo lo hacen las letras cayendo;
      // lo único que se mueve por dentro es la mandíbula, que castañetea.
      cuadros(e, [
        ' .----.\n( x  x )\n|  ||  |\n \'-\\/-\'',
        ' .----.\n( x  x )\n|  ||  |\n \'-||-\'',
      ], 150);
      return anime.timeline()
        .add({
          targets: e.bicho,
          translateY: [-120, -58],
          scale: [0.7, 1],
          opacity: [0, 1],
          duration: 430,
          easing: 'easeOutQuad',
        })
        .add({
          // El tajo y la gravedad: caen, no vuelan.
          targets: e.letras,
          translateY: [0, 280],
          rotateZ: function () { return anime.random(-140, 140); },
          opacity: [1, 0],
          duration: 700,
          delay: anime.stagger(9, { from: 'first' }),
          easing: 'easeInQuad',
        }, '-=60')
        .add({ targets: e.bicho, opacity: 0, duration: 300 }, '-=420');
    },

    cocodrilo: function (e) {
      // La mandíbula se abre y se cierra mientras avanza: es la que se come las letras, así que
      // es la que tiene que moverse. Tres cuadros, siempre el mismo alto.
      cuadros(e, [
        '  ____\n /VVVV\\\n \\____/',
        '  ____\n /VVVV\\\n  \\VV/ ',
        '  ____\n /‾‾‾‾\\\n  \\__/ ',
      ], 110);
      return anime.timeline()
        .add({
          targets: e.bicho,
          translateX: [e.ancho * 0.6, -e.ancho * 0.55],
          translateY: [8, 8],
          opacity: [0, 1],
          duration: 980,
          easing: 'easeInOutQuad',
        })
        .add({
          // Se las traga de a una, de derecha a izquierda, justo cuando pasa la mandíbula.
          targets: e.letras,
          scale: [1, 0],
          rotateY: function () { return anime.random(-110, 110); },
          opacity: [1, 0],
          duration: 240,
          delay: anime.stagger(25, { from: 'last' }),
          easing: 'easeInBack',
        }, '-=900')
        .add({ targets: e.bicho, opacity: 0, duration: 240 }, '-=120');
    },

    tiburon: function (e) {
      // La aleta queda quieta y lo que se mueve es la estela: es lo que la hace leer como que
      // avanza cortando el agua.
      cuadros(e, [
        '   ▲\n~~~~~~~~~~~~~~~~',
        '   ▲\n≈~≈~≈~≈~≈~≈~≈~≈~',
        '   ▲\n~≈~≈~≈~≈~≈~≈~≈~≈',
      ], 90);
      return anime.timeline()
        .add({
          targets: e.bicho,
          translateX: [e.ancho * 0.5, -e.ancho * 0.5],
          translateY: [72, 72],
          opacity: [0, 1],
          duration: 930,
          easing: 'easeInOutSine',
        })
        .add({
          // Las chupa para abajo, aplastándolas contra el agua.
          targets: e.letras,
          translateY: [0, 150],
          scaleY: [1, 0.12],
          rotateX: [0, 75],
          opacity: [1, 0],
          duration: 400,
          delay: anime.stagger(19, { from: 'last' }),
          easing: 'easeInQuad',
        }, '-=830')
        .add({ targets: e.bicho, opacity: 0, duration: 240 }, '-=180');
    },
  };

  // ── El reproductor ─────────────────────────────────────────────────────────

  let cerrarActual = null;

  function reproducir(anim, texto, fin) {
    const e = escena();
    if (!e.overlay || !e.bicho || !e.texto || typeof anime === 'undefined') return false;
    const coreo = COREOGRAFIAS[anim.slug];
    if (!coreo) return false;

    e.letras = repartir(e.texto, texto);
    anime.set(e.bicho, { translateX: 0, translateY: 0, rotate: 0, scale: 1, opacity: 0 });
    e.overlay.style.display = 'flex';
    e.ancho = e.overlay.querySelector('.despedida-escena').clientWidth || 480;

    let listo = false;
    const terminar = function () {
      if (listo) return;
      listo = true;
      cerrarActual = null;
      // El reloj de los cuadros del bicho sigue corriendo por su cuenta: si no se corta acá,
      // queda un intervalo vivo sobre una página que se está yendo.
      if (e.reloj) { clearInterval(e.reloj); e.reloj = null; }
      e.overlay.style.display = 'none';
      e.texto.textContent = '';
      fin();
    };
    cerrarActual = terminar;

    if (quietito()) {                 // sin animación, pero el modal no se saltea en silencio
      setTimeout(terminar, 260);
      return true;
    }
    const tl = coreo(e);
    tl.finished.then(terminar).catch(terminar);
    return true;
  }

  // Escape termina YA en vez de cancelar: ya confirmaste el borrado, y dejar la tarea sin borrar
  // después de confirmar sería el peor de los finales. Corta la propagación para que el handler
  // global de base.html no te saque de la pantalla en el medio.
  document.addEventListener('keydown', function (ev) {
    if (ev.key === 'Escape' && cerrarActual) {
      ev.stopPropagation();
      cerrarActual();
    }
  }, true);

  // La previsualización de Ajustes: el mismo modal, con una tarea de mentira. Sin esto, elegir
  // entre cinco nombres no significa nada.
  window.despedirEn = function (texto, slug) {
    if (cerrarActual) cerrarActual();
    const anim = elegir(slug);
    if (!anim) return;
    try {
      reproducir(anim, texto, function () {});
    } catch (e) { /* una previsualización rota no puede romper Ajustes */ }
  };

  window.despedir = function (form, seguir) {
    let hecho = false;
    function unaVez() {
      if (hecho) return;
      hecho = true;
      seguir();
    }
    // El tope va PRIMERO y afuera del try: si lo que sigue explota antes de armarse, esto ya
    // quedó agendado y la tarea se borra igual.
    setTimeout(unaVez, TOPE_MS);
    try {
      const anim = elegir(window.DESPEDIDA_ELEGIDA);
      if (!anim) { unaVez(); return; }
      const fila = form.closest('.todo-row') || form.closest('.todo-item');
      const txt = fila && fila.querySelector('.todo-text');
      if (!reproducir(anim, txt ? txt.textContent.trim() : 'la tarea', unaVez)) unaVez();
    } catch (e) {
      unaVez();
    }
  };
})();
