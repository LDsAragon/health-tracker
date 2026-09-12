// Dos ventanas abiertas (la grande y el widget) tienen que ver los cambios de la otra.
//
// Poleo y no un aviso directo de una ventana a la otra: así también anda con dos pestañas del
// navegador, y cubre los cambios que no vienen de un POST de la otra ventana — restaurar un
// backup, aplicar un sync, cambiar de perfil.
//
// El token viene servido con la página (window.TOKEN_DATOS), así que la primera vuelta ya tiene
// con qué comparar.
(function () {
  const INTERVALO = 3000;
  let referencia = window.TOKEN_DATOS;
  if (!referencia) return;

  // ── Corta-circuitos ───────────────────────────────────────────────────────
  // ⚠️ Un token que oscile deja la app recargándose sin parar, y es exactamente lo que pasó
  // cuando salía de la mtime de los archivos. Esto no arregla la causa, la acota: convierte
  // "la app es inusable" en "el refresco dejó de andar", que se nota mucho menos y se ve en la
  // consola.
  const TOPE = 3, VENTANA = 30000;
  const CLAVE = 'refresco_recargas';

  function recargasRecientes() {
    try {
      const t = JSON.parse(sessionStorage.getItem(CLAVE) || '[]');
      return t.filter((ts) => Date.now() - ts < VENTANA);
    } catch (e) { return []; }
  }

  function anotarRecarga() {
    try {
      sessionStorage.setItem(CLAVE, JSON.stringify(recargasRecientes().concat(Date.now())));
    } catch (e) { /* modo privado */ }
  }

  if (recargasRecientes().length > TOPE) {
    console.warn('Bitácora: el refresco recargó ' + recargasRecientes().length +
                 ' veces en ' + (VENTANA / 1000) + ' s. Lo corto para no seguir parpadeando; ' +
                 'el token de /refresco debe estar inestable.');
    return;
  }

  // ── Las escrituras propias no son cambios de la otra ventana ──────────────
  // Sin esto, tocar un switch en Ajustes (que guarda al instante por AJAX) o cerrar el aviso de
  // tareas haría que la página se recargue sola a los 3 segundos. Los formularios normales no
  // tienen el problema porque recargan y traen un token nuevo; los que hacen fetch, sí.
  //
  // Se envuelve fetch en vez de avisar desde cada llamador: hoy hay cuatro (ajustes.js, day.js,
  // week.html y el "visto" del aviso), y el quinto que alguien agregue volvería a traer el bug.
  // Acá solo se OBSERVA: la respuesta se devuelve intacta.
  const fetchOriginal = window.fetch;
  window.fetch = function (recurso, opciones) {
    const metodo = ((opciones && opciones.method) || 'GET').toUpperCase();
    const p = fetchOriginal.apply(this, arguments);
    if (metodo !== 'GET' && metodo !== 'HEAD') {
      p.then(function (r) { if (r && r.ok) alDia(); })
       .catch(function () { /* que falle el POST no es asunto del refresco */ });
    }
    return p;
  };

  function alDia() {
    pedirToken().then(function (t) { if (t) { referencia = t; pendiente = false; } });
  }

  // Si el servidor se fue, dejar de polear. Pasa al cerrar la app: la página sobrevive un rato
  // al server y cada vuelta dejaba un ERR_CONNECTION_REFUSED en la consola, para siempre.
  const FALLOS_TOPE = 5;
  let fallos = 0;

  function pedirToken() {
    return fetchOriginal('/refresco', { cache: 'no-store' })
      .then(function (r) {
        fallos = 0;
        return r.ok ? r.text() : null;
      })
      .catch(function () { fallos++; return null; });
  }

  // ── Cuándo se puede recargar ──────────────────────────────────────────────
  // ⚠️ Solo los campos donde se TIPEA cuentan como borrador. Con "cualquier input cuyo value
  // difiera del defaultValue" el calendario no se refrescaba nunca: el slider de tamaño de celda
  // se restaura de localStorage al cargar, así que su value siempre difiere del HTML. Un slider,
  // un radio o un checkbox no son texto a medio escribir — su estado ya está guardado en otro
  // lado.
  const TIPEABLES = ['text', 'search', 'url', 'email', 'tel', 'number', 'password',
                     'date', 'time', 'datetime-local', 'month', 'week'];

  function esTipeable(el) {
    if (!el) return false;
    if (el.tagName === 'TEXTAREA') return true;
    return el.tagName === 'INPUT' && TIPEABLES.indexOf(el.type) !== -1;
  }

  // Nunca recargar encima de algo tipeado: si estás escribiendo una nota rápida en una celda y
  // el widget dispara un cambio, la recarga te borraría el borrador. `defaultValue` es el valor
  // con el que el servidor renderizó el campo, así que "sucio" sale del DOM sin snapshot.
  function hayBorrador() {
    const f = document.activeElement;
    // Un <select> abierto no es un borrador, pero recargar debajo del mouse igual molesta; se
    // espera a que suelte el foco, que es un instante.
    if (f && (f.isContentEditable || f.tagName === 'SELECT' || esTipeable(f))) return true;
    for (const el of document.querySelectorAll('input, textarea')) {
      if (esTipeable(el) && el.value !== el.defaultValue) return true;
    }
    return false;
  }

  let pendiente = false;

  // Cuándo fue la última vez que el usuario hizo algo en esta ventana.
  const QUIETO = 1500;
  let ultimaInteraccion = 0;
  ['pointerdown', 'pointermove', 'keydown', 'wheel', 'scroll'].forEach(function (ev) {
    window.addEventListener(ev, function () { ultimaInteraccion = Date.now(); },
                            { passive: true });
  });

  // ⚠️ No recargar ENCIMA de lo que estás haciendo — el parpadeo justo abajo del mouse es lo
  // que se ve mal. Pero "tiene el foco" solo no sirve como regla: una ventana enfocada y quieta
  // se quedaría desactualizada para siempre. Así que la de atrás recarga ya, y la de adelante
  // espera a que sueltes el mouse y el teclado un segundo y medio.
  function puedeRecargar() {
    if (hayBorrador()) return false;
    if (!document.hasFocus()) return true;
    return Date.now() - ultimaInteraccion > QUIETO;
  }

  function intentar() {
    if (!pendiente || !puedeRecargar()) return;
    anotarRecarga();
    location.reload();
  }

  window.addEventListener('blur', intentar);

  // Al volver a verse (el widget que estaba tapado, una pestaña de atrás) se chequea en el
  // acto: mientras estuvo oculta no poleó, así que puede estar vieja.
  document.addEventListener('visibilitychange', function () {
    if (!document.hidden) revisar();
  });

  function revisar() {
    return pedirToken().then(function (token) {
      if (token && token !== referencia) pendiente = true;
      intentar();
    });
  }

  const timer = setInterval(function () {
    if (fallos >= FALLOS_TOPE) { clearInterval(timer); return; }
    if (document.hidden) return;            // el widget tapado o la ventana minimizada
    revisar();
  }, INTERVALO);
})();
