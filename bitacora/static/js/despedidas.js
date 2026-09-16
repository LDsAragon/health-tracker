// La muerte de una tarea: la animación que se reproduce al borrarla.
//
// Se abre un modal, adentro va **el texto real de la tarea** y eso es lo que se destruye: cada
// letra es un elemento y se va por su lado. El motor es anime.js (vendorizado); por debajo son
// transformaciones 3D de CSS, así que hay profundidad sin WebGL — que es lo que descartó three.js:
// en Linux la app corre con el renderer acelerado de WebKitGTK apagado a propósito porque crashea.
//
// ⚠️ LA REGLA QUE NO SE NEGOCIA: borrar no puede depender de esto. `despedir()` recibe el callback
// que envía el formulario y **tiene que llamarlo siempre**: si anime.js no cargó, si el catálogo
// viene vacío, si una coreografía tira o si la animación se cuelga, igual se llama —hay un tope
// duro por encima de todo—. Es el mismo criterio que el `onsubmit="return false;"` de
// confirmar.js y que el botón Guardar que sigue en la plantilla de Ajustes: la parte decorativa
// puede fallar, la acción no.
(function () {
  const CATALOGO = window.DESPEDIDAS || [];
  const TOPE_MS = 5000;          // pase lo que pase, a los 5 s el formulario se envía
  const AZAR = 'aleatorio';
  const APAGADO = 'off';
  const NBSP = String.fromCharCode(160);

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
      caja: document.querySelector('.despedida-escena'),
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
      s.textContent = ch === ' ' ? NBSP : ch;
      cont.appendChild(s);
      letras.push(s);
    });
    return letras;
  }

  // ⚠️ Dónde quedó cada letra dentro de la escena. Es lo que hace que la destrucción **siga al
  // bicho** —la ola las arrastra de izquierda a derecha, el cocodrilo se las come de derecha a
  // izquierda, el meteorito las revienta desde donde cayó— en vez de ser un estallido al azar,
  // que era lo que hacía que la animación se viera simplona: pasaba algo, pero no pasaba por
  // culpa de nada.
  function ubicar(e) {
    const caja = e.caja.getBoundingClientRect();
    e.ancho = caja.width || 480;
    e.x = e.letras.map(function (l) {
      const r = l.getBoundingClientRect();
      return r.left + r.width / 2 - caja.left;
    });
  }

  // El bicho se mueve con transformaciones —eso lo hace anime.js y es lo que da la fluidez—,
  // pero ADEMÁS se anima por dentro cambiando de cuadro: la mandíbula que muerde, la cresta que
  // rompe, la estela que arde. Son las dos mitades y hacen falta las dos.
  //
  // Es también lo que deja usar arte de las galerías de ASCII animado (asciiart.eu, ascii.co.uk)
  // o dibujar el propio con ASCII Motion, que es MIT: son listas de cuadros y entran acá.
  // ⚠️ Los cuadros tienen que tener el mismo alto, o el dibujo salta al pasar. `cuadros()` los
  // empareja. Y todos los caracteres tienen que caer en la grilla del monoespaciado: hay un
  // tripwire con los anchos medidos, porque `~` y `∼` se ven igual y miden distinto.
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

  // ── El ritmo, que es de todas ──────────────────────────────────────────────
  // ⚠️ La primera versión duraba 1,2 s y "no se apreciaba": arrancaba con la destrucción ya
  // empezada y terminaba antes de que pudieras mirar. Ahora hay tres tiempos y los tres importan:
  // la tarea **aparece y se queda** un momento (la leés), pasa lo que pasa, y queda un respiro de
  // vacío antes de cerrar. Son ~2,4 s.

  function entrada(e, tl) {
    return tl
      .add({
        targets: e.letras,
        opacity: [0, 1],
        translateY: [16, 0],
        duration: 420,
        delay: anime.stagger(8),
        easing: 'easeOutQuad',
      })
      .add({ targets: e.texto, opacity: 1, duration: 380 });   // el respiro para leerla
  }

  function salida(e, tl) {
    return tl
      .add({ targets: e.bicho, opacity: 0, duration: 300, easing: 'easeOutQuad' }, '-=260')
      .add({ targets: e.texto, opacity: 0, duration: 320 });   // el vacío que queda
  }

  // ── Las coreografías ───────────────────────────────────────────────────────
  // Una por animación del catálogo. Le agregan su acto a la línea de tiempo, entre la entrada y
  // la salida.
  //
  // ⚠️ Las claves tienen que ser EXACTAMENTE los slugs de bitacora/despedidas.py, que es de donde
  // salen las opciones del ajuste. Una animación elegible sin coreografía es un ajuste que no
  // hace nada. Hay un tripwire.

  const COREOGRAFIAS = {
    meteorito: function (e, tl) {
      // La estela arde: cambia el fuego, la roca se queda quieta.
      cuadros(e, [
        '  \'\n   \\\n    \\\\\n     \\\\\n      ☄',
        '  ·\n   \\\n    \\\\\n     \\\\\\\n      ☄',
        '  .\n   \\\\\n    \\\\\n     \\\\\\\n      ☄',
      ], 80);
      const xi = e.ancho * 0.42;          // dónde pega
      return tl
        .add({
          targets: e.bicho,
          translateX: [-e.ancho * 0.5, xi - e.ancho * 0.5],
          translateY: [-230, 40],
          rotate: [-10, 12],
          opacity: [0, 1],
          duration: 760,
          easing: 'easeInQuad',
        })
        .add({
          // La onda expansiva: cada letra sale DESDE el impacto, y las de más lejos tardan más.
          targets: e.letras,
          translateX: function (l, i) {
            return (e.x[i] - xi) * 1.9 + anime.random(-45, 45);
          },
          translateY: function () { return anime.random(-190, 220); },
          translateZ: function () { return anime.random(-260, 340); },
          rotateX: function () { return anime.random(-720, 720); },
          rotateZ: function () { return anime.random(-380, 380); },
          opacity: [1, 0],
          duration: 1000,
          delay: function (l, i) { return 40 + Math.abs(e.x[i] - xi) * 0.95; },
          easing: 'easeOutQuint',
        }, '-=60');
    },

    ola: function (e, tl) {
      // Una ola con cresta, y el agua que se mueve por debajo.
      cuadros(e, [
        '    ____\n ≈≈/    \\≈≈≈≈≈≈\n≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈≈\n~~~~~~~~~~~~~~~~',
        '    ____\n ≈≈/    \\~≈~≈~≈\n~≈~≈~≈~≈~≈~≈~≈~≈\n≈~≈~≈~≈~≈~≈~≈~≈~',
        '    ____\n ≈≈/    \\≈~≈~≈~\n≈~≈~≈~≈~≈~≈~≈~≈\n~≈~≈~≈~≈~≈~≈~≈~≈',
      ], 110);
      return tl
        .add({
          targets: e.bicho,
          translateX: [-e.ancho * 0.95, e.ancho * 0.75],
          translateY: [60, 44],
          opacity: [0, 1],
          duration: 1150,
          easing: 'easeInOutSine',
        })
        .add({
          // Se las lleva: cada una arranca cuando la ola le llega, y todas para el mismo lado.
          targets: e.letras,
          translateX: function () { return anime.random(200, 430); },
          translateY: function (l, i) { return 55 + Math.sin(i * 0.7) * 34; },  // montadas en la cresta
          rotateZ: function () { return anime.random(-50, 50); },
          opacity: [1, 0],
          duration: 820,
          delay: function (l, i) { return e.x[i] * 1.15; },
          easing: 'easeInOutQuad',
        }, '-=1060');
    },

    parca: function (e, tl) {
      // La parca con su guadaña. ⚠️ Quieta y derecha: el mismo dibujo rotando se leía como un
      // garabato. Lo único que se mueve por dentro es la cara.
      cuadros(e, [
        '    ___\n   /   \\    |\n  | x x |   |\n  |  _  |  /\n   \\___/ _/',
        '    ___\n   /   \\    |\n  | x x |   |\n  |  o  |  /\n   \\___/ _/',
      ], 200);
      return tl
        .add({
          targets: e.bicho,
          translateX: [-e.ancho * 0.6, -e.ancho * 0.22],
          translateY: [-40, -30],
          opacity: [0, 1],
          duration: 620,
          easing: 'easeOutQuad',
        })
        .add({
          // El tajo pasa y lo que sigue es la gravedad: caen, no vuelan.
          targets: e.letras,
          translateY: [0, 330],
          rotateZ: function () { return anime.random(-150, 150); },
          opacity: [1, 0],
          duration: 880,
          delay: function (l, i) { return e.x[i] * 1.05; },
          easing: 'easeInQuad',
        }, '-=120');
    },

    cocodrilo: function (e, tl) {
      // La mandíbula se abre y se cierra mientras avanza: es la que se come las letras, así que
      // es la que tiene que moverse.
      cuadros(e, [
        '     ______\n  __/      \\\n /  VVVVVV  \\\n \\__________/',
        '     ______\n  __/      \\\n /  VVVV   /\n \\________/',
        '     ______\n  __/      \\\n /_________/',
      ], 130);
      return tl
        .add({
          targets: e.bicho,
          translateX: [e.ancho * 0.62, -e.ancho * 0.6],
          translateY: [10, 10],
          opacity: [0, 1],
          duration: 1200,
          easing: 'easeInOutQuad',
        })
        .add({
          // De derecha a izquierda, cada una justo cuando le llega la mandíbula: un tironcito
          // hacia adentro de la boca y adentro.
          targets: e.letras,
          translateX: 22,
          scale: [1, 0],
          rotateY: function () { return anime.random(-120, 120); },
          opacity: [1, 0],
          duration: 300,
          delay: function (l, i) { return (e.ancho - e.x[i]) * 1.15; },
          easing: 'easeInBack',
        }, '-=1120');
    },

    tiburon: function (e, tl) {
      // La aleta corta el agua y la estela corre por debajo.
      cuadros(e, [
        '      /|\n     / |\n~~~~~~~~~~~~~~~~\n  ≈≈≈≈≈≈≈≈≈≈≈≈',
        '      /|\n     / |\n≈~≈~≈~≈~≈~≈~≈~≈~\n  ~~~~~~~~~~~~',
        '      /|\n     / |\n~≈~≈~≈~≈~≈~≈~≈~≈\n  ≈≈≈≈≈≈≈≈≈≈≈≈',
      ], 100);
      return tl
        .add({
          targets: e.bicho,
          translateX: [e.ancho * 0.55, -e.ancho * 0.55],
          translateY: [86, 86],
          opacity: [0, 1],
          duration: 1150,
          easing: 'easeInOutSine',
        })
        .add({
          // Las chupa para abajo al pasar, aplastándolas contra el agua.
          targets: e.letras,
          translateY: [0, 175],
          scaleY: [1, 0.1],
          rotateX: [0, 80],
          opacity: [1, 0],
          duration: 460,
          delay: function (l, i) { return (e.ancho - e.x[i]) * 1.1; },
          easing: 'easeInQuad',
        }, '-=1080');
    },
  };

  // ── El reproductor ─────────────────────────────────────────────────────────

  let cerrarActual = null;

  function reproducir(anim, texto, fin) {
    const e = escena();
    if (!e.overlay || !e.bicho || !e.texto || !e.caja || typeof anime === 'undefined') return false;
    const coreo = COREOGRAFIAS[anim.slug];
    if (!coreo) return false;

    e.letras = repartir(e.texto, texto);
    anime.set(e.bicho, { translateX: 0, translateY: 0, rotate: 0, scale: 1, opacity: 0 });
    anime.set(e.texto, { opacity: 1 });
    e.overlay.style.display = 'flex';
    ubicar(e);                      // después de mostrarlo: antes las letras no miden nada

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
      setTimeout(terminar, 400);
      return true;
    }
    const tl = anime.timeline();
    entrada(e, tl);
    coreo(e, tl);
    salida(e, tl);
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
