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
      planos: [],
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
  // bicho** —la ola las arrastra de izquierda a derecha, el tiburón las chupa al pasar por
  // debajo, el meteorito las revienta desde donde cayó— en vez de ser un estallido al azar,
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
  function cuadros(e, capa, lista, ms, unaVez, ventana) {
    const alto = Math.max.apply(null, lista.map(function (c) { return c.split('\n').length; }));
    const parejos = lista.map(function (c) {
      const filas = c.split('\n');
      while (filas.length < alto) filas.push('');
      return filas.join('\n');
    });
    capa.textContent = parejos[0];
    // `ventana` acota el plano a un TRAMO de la escena, en fracciones del total. La onda
    // expansiva dura el impacto, no los cinco segundos: sin esto se abriria durante toda la
    // aproximacion y no seria una explosion, seria un fondo.
    e.planos.push({ capa: capa, cuadros: parejos, ms: ms || 90, unaVez: !!unaVez, i: 0,
                    desde: (ventana && ventana[0]) || 0, hasta: (ventana && ventana[1]) || 1 });
  }

  // ⚠️ **Los cuadros los manda la línea de tiempo, no un reloj aparte.** Antes cada plano
  // corría con su `setInterval`, o sea que de un GIF de varios segundos se veía un bucle corto
  // mientras la escena duraba el triple: había muchísimo más material del que se mostraba. Ahora
  // el material **convertido se reproduce entero y una sola vez** a lo largo de la escena, y el
  // dibujado a mano —que son dos o tres cuadros pensados para ciclar rápido— sigue en bucle,
  // pero contra el mismo reloj.
  //
  // De paso desaparecen los intervalos sueltos: no puede quedar ninguno vivo sobre una página
  // que se está yendo, y buscar un instante con `seek()` muestra el cuadro que corresponde.
  function avanzarCuadros(e, anim) {
    const p = Math.max(0, Math.min(1, (anim.progress || 0) / 100));
    e.planos.forEach(function (pl) {
      const n = pl.cuadros.length;
      if (n < 2) return;
      const local = pl.hasta > pl.desde
        ? Math.max(0, Math.min(1, (p - pl.desde) / (pl.hasta - pl.desde)))
        : p;
      const i = pl.unaVez
        ? Math.min(n - 1, Math.floor(local * n))
        : Math.floor((anim.currentTime || 0) / pl.ms) % n;
      if (i !== pl.i) {
        pl.i = i;
        pl.capa.textContent = pl.cuadros[i];
      }
    });
  }

  // ⚠️ El arte convertido de material real (tools/ascii_video.py) le GANA al dibujado a mano.
  // Dibujar ASCII a mano tiene un techo bajo —sirve para una aleta de tres líneas, no para una
  // ola que se te viene encima—, así que cada escena pide el suyo por slug y usa el de a mano solo
  // como respaldo, para que la app funcione igual sin el archivo generado.
  //
  // El tamaño de letra sale del ANCHO EN COLUMNAS del arte: el convertido tiene ~100 y el de a
  // mano ~35, así que con un tamaño fijo uno de los dos se sale de la escena.
  function pintar(e, capa, slug, alternativa, ms, ventana) {
    const conv = (window.DESPEDIDAS_ARTE || {})[slug];
    const lista = (conv && conv.cuadros && conv.cuadros.length) ? conv.cuadros : alternativa;
    let cols = 0;
    lista.forEach(function (c) {
      c.split('\n').forEach(function (l) { if (l.length > cols) cols = l.length; });
    });
    capa.style.fontSize = Math.max(6, Math.min(26, e.ancho / (cols * 0.62))) + 'px';
    const convertida = !!(conv && conv.cuadros && conv.cuadros.length);
    // El material largo se reproduce entero UNA vez a lo largo de la escena; el corto
    // —medio segundo de bucle— cicla a su ritmo, o iria en cámara lentísima.
    cuadros(e, capa, lista, (conv && conv.ms) || ms,
            convertida && !(conv && conv.bucle), ventana);
    // ⚠️ Devuelve si el arte es convertido, y no es un detalle: el dibujado a mano son ~35
    // columnas y hay que AGRANDARLO para que llene la escena, mientras que el convertido ya
    // entra justo y ampliarlo 2,7× destruye el detalle que es justamente su valor. Cada escena
    // elige su recorrido de escala con esto.
    return convertida;
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
      const fondo = pintar(e, e.capas[0], 'meteorito.fondo', [
        '  .      ·        .       ·      .        ·\n' +
        '       ·      .        ·      .       ·\n' +
        '  ·        .       ·        .      ·       .\n' +
        '      .        ·       .        ·      .\n' +
        '  ·       .        ·       .        ·      .',
      ], 260);
      const conv = pintar(e, e.capas[2], 'meteorito', [
        '    .\n   \'\\\n  . \\\\\n    \\\\\\\n   \' \\\\\\\n      \\\\\\\\\n       ☄',
        '    ·\n   .\\\n  \' \\\\\n    \\\\\n   . \\\\\\\n      \\\\\\\n       ☄',
        '    \'\n   ·\\\n  . \\\\\n    \\\\\\\n   \' \\\\\n      \\\\\\\\\n       ☄',
      ], 70);
      // La onda expansiva, en el plano del medio y solo durante el impacto. El material es
      // generado (tools/onda_choque.py): no hay explosión libre que convierta bien, pero un
      // anillo que se abre es geometría pura y eso el ASCII lo dibuja perfecto.
      const onda = pintar(e, e.capas[1], 'meteorito.onda', [' '], 40, [0.60, 0.97]);
      const xi = e.ancho * 0.44;          // dónde pega
      return tl
        .add({                            // el cielo, lejos: casi no se mueve
          targets: e.capas[0],
          opacity: [0, fondo ? 0.5 : 0.75],
          // ⚠️ Con otro material atrás, el plano de fondo tiene que ir MÁS CHICO, MÁS LENTO y
          // MÁS APAGADO que el de adelante. Eso es el parallax; sin esa diferencia los dos
          // dibujos se leen como uno encima del otro y la profundidad desaparece.
          scale: fondo ? [0.5, 0.62] : [1, 1],
          translateX: fondo ? [e.ancho * 0.16, e.ancho * 0.05] : [0, 0],
          translateY: fondo ? [-e.alto * 0.24, -e.alto * 0.10] : [-16, 10],
          duration: 1500,
          easing: 'linear',
        })
        .add({                            // la roca, desde muy lejos y muy chica
          targets: e.capas[2],
          // ⚠️ La roca NO está en el centro del cuadro del material —vive abajo a la derecha, con
          // la estela subiendo a la izquierda—, así que al agrandar el plano se corre sola hacia
          // esa esquina. El destino compensa ese corrimiento: sin esto la roca terminaba fuera de
          // cuadro y el impacto pasaba en un lugar donde no había nada.
          translateX: conv ? [-e.ancho * 0.34, -e.ancho * 0.46]
                           : [-e.ancho * 0.42, xi - e.ancho * 0.5],
          translateY: conv ? [-e.alto * 0.78, -e.alto * 0.33]
                           : [-e.alto * 0.62, e.alto * 0.10],
          // ⚠️ El material es un BUCLE sin impacto —la roca se queda en su lugar y lo que se
          // mueve es el chisporroteo de la estela—, así que la llegada la cuenta entera la
          // cámara: de muy chica y muy arriba a encima del texto. Por eso el recorrido de escala
          // es largo, al revés que en el resto del material convertido.
          scale: conv ? [0.4, 1.62] : [0.18, 1.75],
          rotate: [-8, 6],
          opacity: [0, 1],
          duration: 2000,
          easing: 'easeInQuad',
        }, '-=1400')
        .add({ targets: e.capas[2], opacity: 0, scale: conv ? 2.3 : 3.4,
               duration: 280, easing: 'easeOutQuad' });
    },

    // Se la ve venir de lejos, se acerca de golpe, pega un guadañazo y el flash parte el texto
    // en dos mitades que salen para lados opuestos.
    parca: function (e, tl) {
      const conv = pintar(e, e.capas[1], 'parca', [
        '     ___\n   /     \\      |\n  |  x x  |     |\n  |   _   |    /\n   \\_____/  __/',
        '     ___\n   /     \\      |\n  |  x x  |     |\n  |   o   |    /\n   \\_____/  __/',
      ], 220);
      return tl
        .add({                            // ronda arriba a la izquierda, lejos
          targets: e.capas[1],
          opacity: [0, 0.6],
          scale: conv ? [0.26, 0.34] : [0.3, 0.38],
          translateX: [-e.ancho * 0.30, -e.ancho * 0.24],
          translateY: [-e.alto * 0.30, -e.alto * 0.26],
          rotate: [-3, 1],
          duration: 1050,
          easing: 'easeOutQuad',
        })
        .add({                            // y se tira ENCIMA DE LAS PALABRAS
          // ⚠️ Ataca al TEXTO, no a la pantalla: cae sobre la linea de la tarea y se queda del
          // tamano en que todavia se lee que es un rostro. Escalarlo hasta tapar la escena lo
          // convertia en una pared de textura y contaba otra cosa —un choque contra el vidrio—.
          targets: e.capas[1],
          scale: conv ? 1.45 : 2.6,
          opacity: 1,
          translateX: 0,
          translateY: 0,
          rotate: 0,
          duration: 240,
          easing: 'easeInQuad',
        })
        .add({                            // y sigue de largo, atravesandolas
          targets: e.capas[1],
          translateX: e.ancho * 0.30,
          translateY: e.alto * 0.16,
          scale: conv ? 1.7 : 2.2,
          opacity: 0,
          duration: 900,
          easing: 'easeInQuad',
        }, '-=120');
    },

  };

  // Lo que le pasa al texto en cada escena, aparte. Se separa de la escena porque el momento en
  // que la tarea se rompe es el golpe, y así se lee de un vistazo qué hace cada una.
  const DESTRUCCION = {
    meteorito: function (e, tl) {
      const xi = e.ancho * 0.44;
      // ⚠️ El golpe es lo más largo de la escena, no un parpadeo: dos destellos —uno seco y
      // uno que se apaga despacio— y un temblor que dura casi un segundo y medio.
      destello(e, tl, 1, 260, '-=200');
      destello(e, tl, 0.5, 900, '-=120');
      sacudir(e, tl, 46, 1500, '-=1050');
      // La onda se abre sola en el material; la escala la hace pasar de largo el borde, que es lo
      // que la vuelve grande en vez de un anillo prolijo en el medio de la pantalla.
      tl.add({ targets: e.capas[1], opacity: [0, 0.95], scale: [0.55, 1.35],
               duration: 460, easing: 'easeOutQuad' }, '-=1480')
        .add({ targets: e.capas[1], opacity: 0, scale: 2.4,
               duration: 1000, easing: 'easeOutQuad' }, '-=760');
      return tl.add({
        // La onda expansiva: cada letra sale DESDE el impacto, y las de más lejos tardan más.
        targets: e.letras,
        translateX: function (l, i) { return (e.x[i] - xi) * 3.1 + anime.random(-70, 70); },
        translateY: function () { return anime.random(-330, 360); },
        translateZ: function () { return anime.random(-420, 620); },
        rotateX: function () { return anime.random(-1080, 1080); },
        rotateZ: function () { return anime.random(-620, 620); },
        opacity: [1, 0],
        duration: 1900,
        delay: function (l, i) { return Math.abs(e.x[i] - xi) * 0.9; },
        easing: 'easeOutQuint',
      }, '-=1700');
    },

    parca: function (e, tl) {
      const xc = e.ancho / 2;
      // Un golpe seco y corto, no el fogonazo largo del meteorito.
      destello(e, tl, 0.8, 200, '-=210');
      sacudir(e, tl, 34, 800, '-=740');
      return tl.add({
        // ⚠️ Las letras salen DESPEDIDAS POR EL BICHO, no hacia la camara: el rostro cae sobre
        // la linea y las manda para los costados y hacia abajo, en la direccion en que sigue de
        // largo. Tirarlas hacia adelante contaba un vidrio rompiendose, que es otra escena.
        targets: e.letras,
        translateX: function (l, i) { return (e.x[i] - xc) * 2.4 + anime.random(20, 120); },
        translateY: function () { return anime.random(40, 320); },
        translateZ: function () { return anime.random(-260, 120); },
        rotateX: function () { return anime.random(-620, 620); },
        rotateZ: function () { return anime.random(-480, 480); },
        opacity: [1, 0],
        // De izquierda a derecha, siguiendo por donde pasa el rostro.
        delay: function (l, i) { return e.x[i] * 0.7; },
        duration: 1300,
        easing: 'easeOutQuint',
      }, '-=760');
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
      e.planos = [];
      e.overlay.style.display = 'none';
      e.texto.textContent = '';
      fin();
    };
    cerrarActual = terminar;

    if (quietito()) {                 // sin animación, pero el modal no se saltea en silencio
      setTimeout(terminar, 400);
      return true;
    }
    const tl = anime.timeline({
      update: function (anim) { avanzarCuadros(e, anim); },
    });
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
