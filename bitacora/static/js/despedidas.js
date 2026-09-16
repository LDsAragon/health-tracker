// La muerte de una tarea: la escena que se reproduce al borrarla.
//
// Se abre un modal, adentro va **el texto real de la tarea** y eso es lo que se destruye: cada
// letra es un elemento y se va por su lado. El motor es anime.js (vendorizado); por debajo son
// transformaciones 3D de CSS, así que hay profundidad sin WebGL — que es lo que descartó three.js:
// en Linux la app corre con el renderer acelerado de WebKitGTK apagado a propósito porque crashea.
//
// ⚠️ LA REGLA QUE NO SE NEGOCIA: borrar no puede depender de esto. `despedir()` recibe el callback
// que envía el formulario y **tiene que llamarlo siempre**: si anime.js no cargó, si el catálogo
// viene vacío, si una escena tira o si la animación se cuelga, igual se llama —hay un tope duro
// por encima de todo—. Es el mismo criterio que el `onsubmit="return false;"` de confirmar.js y
// que el botón Guardar que sigue en la plantilla de Ajustes: la parte decorativa puede fallar, la
// acción no.
(function () {
  const CATALOGO = window.DESPEDIDAS || [];
  const TOPE_MS = 8000;          // pase lo que pase, a los 8 s el formulario se envía
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
  // Tres planos de dibujo: dos detrás del texto y uno adelante. Es lo que permite que una escena
  // tenga profundidad —el cielo estrellado lejos y quieto, el meteorito cerca y rápido— en vez de
  // un solo dibujo que cruza la pantalla.

  function escena() {
    const e = {
      overlay: document.getElementById('despedida-modal'),
      caja: document.getElementById('despedida-escena'),
      texto: document.getElementById('despedida-texto'),
      flash: document.getElementById('despedida-flash'),
      relojes: [],
    };
    e.capas = [0, 1, 2].map(function (n) { return document.getElementById('despedida-capa' + n); });
    return e;
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
    e.ancho = caja.width || 560;
    e.alto = caja.height || 420;
    e.x = e.letras.map(function (l) {
      const r = l.getBoundingClientRect();
      return r.left + r.width / 2 - caja.left;
    });
  }

  // Un plano se anima por dentro cambiando de cuadro: la mandíbula que muerde, la cresta que
  // rompe, la estela que arde. Va junto con las transformaciones, no en su lugar.
  //
  // Es también lo que deja usar arte de las galerías de ASCII animado (asciiart.eu, ascii.co.uk)
  // o dibujar el propio con ASCII Motion, que es MIT: son listas de cuadros y entran acá.
  // ⚠️ Los cuadros tienen que tener el mismo alto, o el dibujo salta al pasar. `cuadros()` los
  // empareja. Y todos los caracteres tienen que caer en la grilla del monoespaciado: hay un
  // tripwire con los anchos medidos, porque `~` y `∼` se ven igual y miden distinto.
  function cuadros(e, capa, lista, ms) {
    const alto = Math.max.apply(null, lista.map(function (c) { return c.split('\n').length; }));
    const parejos = lista.map(function (c) {
      const filas = c.split('\n');
      while (filas.length < alto) filas.push('');
      return filas.join('\n');
    });
    let i = 0;
    capa.textContent = parejos[0];
    if (parejos.length < 2) return;
    e.relojes.push(setInterval(function () {
      i = (i + 1) % parejos.length;
      capa.textContent = parejos[i];
    }, ms || 90));
  }

  // ⚠️ El arte convertido de material real (tools/ascii_video.py) le GANA al dibujado a mano.
  // Dibujar ASCII a mano tiene un techo bajo —sirve para un cocodrilo de tres líneas, no para una
  // ola que se te viene encima—, así que cada escena pide el suyo por slug y usa el de a mano solo
  // como respaldo, para que la app funcione igual sin el archivo generado.
  //
  // El tamaño de letra sale del ANCHO EN COLUMNAS del arte: el convertido tiene ~100 y el de a
  // mano ~35, así que con un tamaño fijo uno de los dos se sale de la escena.
  function pintar(e, capa, slug, alternativa, ms) {
    const conv = (window.DESPEDIDAS_ARTE || {})[slug];
    const lista = (conv && conv.cuadros && conv.cuadros.length) ? conv.cuadros : alternativa;
    let cols = 0;
    lista.forEach(function (c) {
      c.split('\n').forEach(function (l) { if (l.length > cols) cols = l.length; });
    });
    capa.style.fontSize = Math.max(6, Math.min(26, e.ancho / (cols * 0.62))) + 'px';
    cuadros(e, capa, lista, (conv && conv.ms) || ms);
  }

  // ── La cámara ──────────────────────────────────────────────────────────────
  // Los dos efectos que convierten un dibujo que se mueve en un golpe: el temblor sacude la
  // escena entera y el destello tapa todo un instante. Son los que dan el impacto del meteorito
  // y el flash del guadañazo.

  function sacudir(e, tl, fuerza, duracion, desfase) {
    const pasos = [];
    for (let i = 0; i < 9; i++) {
      const f = fuerza * (1 - i / 9);           // se va apagando, como un temblor de verdad
      pasos.push({
        translateX: anime.random(-f, f),
        translateY: anime.random(-f, f),
        duration: duracion / 9,
      });
    }
    pasos.push({ translateX: 0, translateY: 0, duration: duracion / 9 });
    return tl.add({ targets: e.caja, keyframes: pasos, easing: 'linear' }, desfase);
  }

  function destello(e, tl, pico, duracion, desfase) {
    return tl.add({
      targets: e.flash,
      keyframes: [
        { opacity: pico, duration: duracion * 0.18, easing: 'linear' },
        { opacity: 0, duration: duracion * 0.82, easing: 'easeOutQuad' },
      ],
    }, desfase);
  }

  // ── El ritmo, que es de todas ──────────────────────────────────────────────
  // ⚠️ La primera versión duraba 1,2 s y "no se apreciaba": arrancaba con la destrucción ya
  // empezada y terminaba antes de que pudieras mirar. Ahora cada animación es una ESCENA con
  // planteo, golpe y final: la tarea aparece y se queda, pasa lo que pasa, y queda un respiro de
  // vacío antes de cerrar.

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
      .add({ targets: e.texto, opacity: 1, duration: 340 });   // el respiro para leerla
  }

  function salida(e, tl) {
    return tl
      .add({ targets: e.capas, opacity: 0, duration: 420, easing: 'easeOutQuad' }, '-=380')
      .add({ targets: e.texto, opacity: 0, duration: 300 });   // el vacío que queda
  }

  // ── Las escenas ────────────────────────────────────────────────────────────
  // ⚠️ Las claves tienen que ser EXACTAMENTE los slugs de bitacora/despedidas.py, que es de donde
  // salen las opciones del ajuste. Una animación elegible sin escena es un ajuste que no hace
  // nada. Hay un tripwire.

  const COREOGRAFIAS = {
    // Baja desde el espacio: el cielo estrellado queda atrás y quieto mientras la roca crece y
    // entra en la atmósfera. Cuando pega: destello, temblor y onda expansiva.
    meteorito: function (e, tl) {
      cuadros(e, e.capas[0], [
        '  .      ·        .       ·      .        ·\n' +
        '       ·      .        ·      .       ·\n' +
        '  ·        .       ·        .      ·       .\n' +
        '      .        ·       .        ·      .\n' +
        '  ·       .        ·       .        ·      .',
      ]);
      cuadros(e, e.capas[2], [
        '    .\n   \'\\\n  . \\\\\n    \\\\\\\n   \' \\\\\\\n      \\\\\\\\\n       ☄',
        '    ·\n   .\\\n  \' \\\\\n    \\\\\n   . \\\\\\\n      \\\\\\\n       ☄',
        '    \'\n   ·\\\n  . \\\\\n    \\\\\\\n   \' \\\\\n      \\\\\\\\\n       ☄',
      ], 70);
      const xi = e.ancho * 0.44;          // dónde pega
      return tl
        .add({                            // el cielo, lejos: casi no se mueve
          targets: e.capas[0],
          opacity: [0, 0.75],
          translateY: [-16, 10],
          duration: 1500,
          easing: 'linear',
        })
        .add({                            // la roca, desde muy lejos y muy chica
          targets: e.capas[2],
          translateX: [-e.ancho * 0.42, xi - e.ancho * 0.5],
          translateY: [-e.alto * 0.62, e.alto * 0.10],
          scale: [0.18, 1.75],
          rotate: [-6, 10],
          opacity: [0, 1],
          duration: 1550,
          easing: 'easeInQuad',
        }, '-=1400')
        .add({ targets: e.capas[2], opacity: 0, scale: 3.4, duration: 260, easing: 'easeOutQuad' });
    },

    // Se la ve venir de lejos, se acerca de golpe, pega un guadañazo y el flash parte el texto
    // en dos mitades que salen para lados opuestos.
    parca: function (e, tl) {
      cuadros(e, e.capas[1], [
        '     ___\n   /     \\      |\n  |  x x  |     |\n  |   _   |    /\n   \\_____/  __/',
        '     ___\n   /     \\      |\n  |  x x  |     |\n  |   o   |    /\n   \\_____/  __/',
      ], 220);
      cuadros(e, e.capas[2], [
        '        /\n       /\n      /\n     /\n    /\n   /\n  /',
      ]);
      return tl
        .add({                            // lejos, chiquita, esperando
          targets: e.capas[1],
          opacity: [0, 0.8],
          scale: [0.3, 0.38],
          translateY: [-e.alto * 0.26, -e.alto * 0.24],
          duration: 900,
          easing: 'easeOutQuad',
        })
        .add({                            // y encima tuyo en un parpadeo
          targets: e.capas[1],
          scale: 2.6,
          opacity: 1,
          translateY: -e.alto * 0.06,
          duration: 260,
          easing: 'easeInQuad',
        })
        .add({                            // el guadañazo
          targets: e.capas[2],
          opacity: [0, 1],
          translateX: [-e.ancho * 0.55, e.ancho * 0.55],
          scaleY: [2.4, 2.4],
          scaleX: [1, 1.6],
          duration: 190,
          easing: 'linear',
        });
    },

    // El mar. El texto flota, y desde el fondo sube lentamente algo enorme que se lo traga.
    tiburon: function (e, tl) {
      cuadros(e, e.capas[0], [
        '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n   ≈      ≈       ≈      ≈       ≈      ≈',
        '≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~\n     ≈      ≈       ≈      ≈       ≈     ≈',
        '~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈\n   ≈      ≈       ≈      ≈       ≈      ≈',
      ], 190);
      cuadros(e, e.capas[1], [
        '      \\               /\n' +
        '       \\_____________/\n' +
        '      / VVVVVVVVVVVVV \\\n' +
        '     |                 |\n' +
        '      \\ ^^^^^^^^^^^^^ /\n' +
        '       \\_____________/',
        '      \\               /\n' +
        '       \\_____________/\n' +
        '      / VVVVVVVVVVVVV \\\n' +
        '     |                 |\n' +
        '      \\ ^^^^^^^^^^^^^ /\n' +
        '        \\___________/',
      ], 260);
      return tl
        .add({                            // la superficie, a la altura del texto
          targets: e.capas[0],
          opacity: [0, 0.85],
          translateY: [e.alto * 0.09, e.alto * 0.09],
          duration: 700,
          easing: 'easeOutQuad',
        })
        .add({                            // el texto flota encima
          targets: e.texto,
          keyframes: [
            { translateY: -40, rotate: -1.2, duration: 640 },
            { translateY: -22, rotate: 1.2, duration: 640 },
            { translateY: -34, rotate: 0, duration: 520 },
          ],
          easing: 'easeInOutSine',
        }, '-=520')
        .add({                            // y desde el fondo sube, enorme
          // ⚠️ Arranca en +0.46 y no más abajo: la escena mide 420px, así que todo lo que pase
          // de la mitad para abajo está fuera de cuadro y la subida no se veía —el tiburón
          // aparecía casi arriba del texto, sin el viaje que es lo que se pidió—.
          targets: e.capas[1],
          opacity: [0, 1],
          translateY: [e.alto * 0.46, -e.alto * 0.07],
          scale: [0.14, 2.4],
          duration: 2000,
          easing: 'easeInQuad',
        }, '-=1500');
    },

    // Una tormenta: llueve, y por la izquierda se levanta una ola enorme que se curva sobre el
    // texto y se lo lleva puesto.
    ola: function (e, tl) {
      cuadros(e, e.capas[0], [
        '  /  /  /  /  /  /  /  /  /  /  /  /  /  /\n' +
        ' /  /  /  /  /  /  /  /  /  /  /  /  /  / \n' +
        '/  /  /  /  /  /  /  /  /  /  /  /  /  /  \n' +
        '  /  /  /  /  /  /  /  /  /  /  /  /  /  /',
        ' /  /  /  /  /  /  /  /  /  /  /  /  /  / \n' +
        '/  /  /  /  /  /  /  /  /  /  /  /  /  /  \n' +
        '  /  /  /  /  /  /  /  /  /  /  /  /  /  /\n' +
        ' /  /  /  /  /  /  /  /  /  /  /  /  /  / ',
      ], 85);
      // ⚠️ Asimétrica a propósito: la primera versión era un montículo con la misma rampa de los
      // dos lados y se leía como una loma, no como una ola. La de Hokusai sube por la izquierda,
      // rompe arriba a la derecha y deja las garras de espuma colgando sobre lo que va a tapar.
      pintar(e, e.capas[1], 'ola', [
        '                      ,   ,   ,\n' +
        '                     /|  /|  /|\n' +
        '              _,-~~~~ \'   \'   \'\n' +
        '          _,-~        ~-,_\n' +
        '       _,-~                ~-,\n' +
        '    _,-~                      ~,\n' +
        ' _,-~                           \\\n' +
        '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',
        '                     ,   ,   ,\n' +
        '                    /|  /|  /|\n' +
        '              _,-~~~ \'   \'   \'\n' +
        '          _,-~        ~-,_\n' +
        '       _,-~                ~-,\n' +
        '    _,-~                      ~,\n' +
        ' _,-~                           \\\n' +
        '≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈',
      ], 150);
      return tl
        .add({                            // la tormenta
          targets: e.capas[0],
          opacity: [0, 0.55],
          translateY: [-e.alto * 0.36, -e.alto * 0.30],
          duration: 800,
          easing: 'linear',
        })
        .add({                            // y la ola, que crece hasta taparlo todo
          targets: e.capas[1],
          opacity: [0, 1],
          translateX: [-e.ancho * 0.85, -e.ancho * 0.10],
          translateY: [e.alto * 0.34, -e.alto * 0.17],
          scale: [0.45, 2.7],
          duration: 1850,
          easing: 'easeInQuad',
        }, '-=620');
    },

    // El pantano: primero los ojos que se acercan, después la cabeza que sale del agua.
    cocodrilo: function (e, tl) {
      cuadros(e, e.capas[0], [
        '~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~',
        '≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~≈~',
      ], 220);
      cuadros(e, e.capas[1], [
        '        ______________\n' +
        '     __/              \\\n' +
        '    /   VVVVVVVVVVVV   \\\n' +
        '   <                    >\n' +
        '    \\   ^^^^^^^^^^^^   /\n' +
        '     \\________________/',
        '        ______________\n' +
        '     __/              \\\n' +
        '    /   VVVVVVVVVV    /\n' +
        '   <                 /\n' +
        '    \\   ^^^^^^^^^   /\n' +
        '     \\_____________/',
        '        ______________\n' +
        '     __/              \\\n' +
        '    /_________________/',
      ], 150);
      return tl
        .add({                            // el agua quieta
          targets: e.capas[0],
          opacity: [0, 0.7],
          translateY: [e.alto * 0.26, e.alto * 0.26],
          duration: 620,
          easing: 'easeOutQuad',
        })
        .add({                            // y algo que se acerca y crece
          targets: e.capas[1],
          opacity: [0, 1],
          translateX: [e.ancho * 0.62, -e.ancho * 0.10],
          translateY: [e.alto * 0.24, e.alto * 0.02],
          scale: [0.35, 1.9],
          duration: 1700,
          easing: 'easeInQuad',
        }, '-=380');
    },
  };

  // Lo que le pasa al texto en cada escena, aparte. Se separa de la escena porque el momento en
  // que la tarea se rompe es el golpe, y así se lee de un vistazo qué hace cada una.
  const DESTRUCCION = {
    meteorito: function (e, tl) {
      const xi = e.ancho * 0.44;
      destello(e, tl, 0.85, 420, '-=180');
      sacudir(e, tl, 26, 700, '-=400');
      return tl.add({
        // La onda expansiva: cada letra sale DESDE el impacto, y las de más lejos tardan más.
        targets: e.letras,
        translateX: function (l, i) { return (e.x[i] - xi) * 2.2 + anime.random(-50, 50); },
        translateY: function () { return anime.random(-230, 260); },
        translateZ: function () { return anime.random(-300, 420); },
        rotateX: function () { return anime.random(-760, 760); },
        rotateZ: function () { return anime.random(-420, 420); },
        opacity: [1, 0],
        duration: 1100,
        delay: function (l, i) { return Math.abs(e.x[i] - xi) * 0.9; },
        easing: 'easeOutQuint',
      }, '-=640');
    },

    parca: function (e, tl) {
      destello(e, tl, 1, 300, '-=120');
      sacudir(e, tl, 16, 420, '-=280');
      return tl.add({
        // Se despedaza en dos mitades: lo que quedó de un lado del tajo y lo del otro.
        targets: e.letras,
        translateX: function (l, i) {
          return (e.x[i] < e.ancho / 2 ? -1 : 1) * anime.random(90, 320);
        },
        translateY: function (l, i) {
          return (e.x[i] < e.ancho / 2 ? 1 : -1) * anime.random(60, 280);
        },
        rotateZ: function (l, i) { return (e.x[i] < e.ancho / 2 ? -1 : 1) * anime.random(60, 300); },
        translateZ: function () { return anime.random(-200, 260); },
        opacity: [1, 0],
        duration: 900,
        delay: anime.stagger(5, { from: 'center' }),
        easing: 'easeOutQuint',
      }, '-=300');
    },

    tiburon: function (e, tl) {
      const xc = e.ancho / 2;
      return tl.add({
        // Se las traga: convergen a la boca y desaparecen adentro.
        targets: e.letras,
        translateX: function (l, i) { return (xc - e.x[i]) * 0.8; },
        translateY: 46,
        scale: [1, 0],
        rotateX: [0, 90],
        opacity: [1, 0],
        duration: 620,
        delay: function (l, i) { return Math.abs(e.x[i] - xc) * 0.7; },
        easing: 'easeInBack',
      }, '-=520');
    },

    ola: function (e, tl) {
      sacudir(e, tl, 12, 600, '-=900');
      return tl.add({
        // Se la lleva puesta: cada una arranca cuando la ola le llega, todas para el mismo lado.
        targets: e.letras,
        translateX: function () { return anime.random(260, 560); },
        translateY: function (l, i) { return 70 + Math.sin(i * 0.7) * 44; },
        rotateZ: function () { return anime.random(-70, 70); },
        opacity: [1, 0],
        duration: 820,
        delay: function (l, i) { return e.x[i] * 1.15; },
        easing: 'easeInOutQuad',
      }, '-=1000');
    },

    cocodrilo: function (e, tl) {
      return tl.add({
        // De derecha a izquierda, cada una justo cuando le llega la mandíbula.
        targets: e.letras,
        translateX: 26,
        scale: [1, 0],
        rotateY: function () { return anime.random(-120, 120); },
        opacity: [1, 0],
        duration: 320,
        delay: function (l, i) { return (e.ancho - e.x[i]) * 1.15; },
        easing: 'easeInBack',
      }, '-=1250');
    },
  };

  // ── El reproductor ─────────────────────────────────────────────────────────

  let cerrarActual = null;

  function reproducir(anim, texto, fin) {
    const e = escena();
    if (!e.overlay || !e.caja || !e.texto || !e.flash || typeof anime === 'undefined') return false;
    const coreo = COREOGRAFIAS[anim.slug];
    const romper = DESTRUCCION[anim.slug];
    if (!coreo || !romper) return false;

    e.letras = repartir(e.texto, texto);
    e.capas.forEach(function (c) {
      c.textContent = '';
      anime.set(c, { translateX: 0, translateY: 0, rotate: 0, scale: 1, opacity: 0 });
    });
    anime.set(e.caja, { translateX: 0, translateY: 0 });
    anime.set(e.texto, { opacity: 1, translateX: 0, translateY: 0, rotate: 0 });
    anime.set(e.flash, { opacity: 0 });
    e.overlay.style.display = 'flex';
    ubicar(e);                      // después de mostrarlo: antes las letras no miden nada

    let listo = false;
    const terminar = function () {
      if (listo) return;
      listo = true;
      cerrarActual = null;
      // Los relojes de los cuadros siguen corriendo por su cuenta: si no se cortan acá, quedan
      // intervalos vivos sobre una página que se está yendo.
      e.relojes.forEach(clearInterval);
      e.relojes = [];
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
    romper(e, tl);
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
