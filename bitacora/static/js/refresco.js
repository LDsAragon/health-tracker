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
    // Se corta el parpadeo, pero la ventana queda sin refrescarse: eso tiene que verse.
    // `barraAviso` es una declaración, así que está disponible pese a este return temprano.
    barraAviso('El refresco automático se detuvo');
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
  // el widget dispara un cambio, la recarga te borraría el borrador.
  //
  // ⚠️ "Sin tocar" NO se decide comparando contra `defaultValue`, el valor con el que el
  // servidor renderizó el campo. Cualquier campo que el JS rellene al arrancar difiere de su
  // defaultValue **para siempre**, y eso deja la ventana marcada como "con borrador" y sin
  // refrescarse nunca. Ya pasó dos veces: el slider de tamaño de celda del calendario (que se
  // restaura de localStorage) y los dos campos de `date-es.js`, que dejaron la vista del día
  // sin enterarse de nada de lo que escribías en el widget.
  //
  // Hacen falta las dos condiciones: que el campo haya recibido un `input` de verdad —setear
  // `.value` desde JS no dispara ese evento, así que lo que rellena la página no cuenta— y que
  // su contenido difiera del que tenía cuando la página terminó de cargar, para que escribir y
  // volver atrás no lo deje marcado como sucio hasta la próxima recarga.
  const inicial = new WeakMap();
  const tocados = new WeakSet();

  document.addEventListener('input', function (e) { tocados.add(e.target); }, true);

  function anotarValores() {
    for (const el of document.querySelectorAll('input, textarea')) {
      if (esTipeable(el)) inicial.set(el, el.value);
    }
  }

  // Después del load y una vuelta más: así el snapshot ve lo que dejaron los scripts de la
  // página, incluso los que corren en su propio handler de load.
  if (document.readyState === 'complete') setTimeout(anotarValores, 0);
  else window.addEventListener('load', function () { setTimeout(anotarValores, 0); });

  // Un campo que nace después (agregar un bloque a una nota especial) no está en el snapshot:
  // ahí la referencia es el vacío, así que uno recién creado no cuenta y uno que llenaste sí.
  function estaSucio(el) {
    return tocados.has(el) && el.value !== (inicial.has(el) ? inicial.get(el) : '');
  }

  function hayBorrador() {
    const f = document.activeElement;
    // ⚠️ Tener el cursor en un campo NO alcanza: tiene que haber algo escrito. `/search` enfoca
    // el buscador al entrar, así que con la regla vieja esa pantalla tampoco se refrescaba
    // nunca. Estar escribiendo de verdad ya lo cubre `estaSucio`, y estar por escribir lo cubre
    // el segundo y medio de quietud de `puedeRecargar`.
    // Un <select> abierto sí cuenta: recargar una lista desplegada debajo del mouse molesta, y
    // se suelta en un instante.
    if (f && (f.isContentEditable || f.tagName === 'SELECT')) return true;
    if (f && esTipeable(f) && estaSucio(f)) return true;
    for (const el of document.querySelectorAll('input, textarea')) {
      if (esTipeable(el) && estaSucio(el)) return true;
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

  // ── Que no se pueda aplicar NO puede ser invisible ────────────────────────
  // El modo de falla de esta feature no es "se rompe", es "se queda callada": la ventana se ve
  // perfecta y muestra datos viejos. Pasó con los campos de `date-es.js`, que la dejaron sin
  // refrescarse **nunca**, y no había forma de notarlo desde la app. Si hay un cambio esperando
  // hace rato, se avisa y se ofrece el botón — que además es la salida manual si la heurística
  // vuelve a equivocarse.
  const AVISO_TRAS = 10000;
  let esperandoDesde = 0;
  let aviso = null;

  // Declaración y no `const`: el corta-circuitos la usa antes, con un return de por medio.
  function barraAviso(texto) {
    const caja = document.createElement('div');
    caja.className = 'refresco-aviso';
    const t = document.createElement('span');
    t.textContent = texto;
    caja.appendChild(t);
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.textContent = 'Actualizar';
    // Lo pide el usuario a mano, así que acá el borrador no manda: es su decisión.
    btn.addEventListener('click', function () { location.reload(); });
    caja.appendChild(btn);
    document.body.appendChild(caja);
    return caja;
  }

  function mostrarAviso() {
    if (!aviso) aviso = barraAviso('Hay cambios nuevos');
  }

  function sacarAviso() {
    if (aviso) { aviso.remove(); aviso = null; }
    esperandoDesde = 0;
  }

  // ── Actualizar sin recargar ───────────────────────────────────────────────
  // El `location.reload()` era la causa de raíz de los tres bugs de esta feature: como recargar
  // destruye lo que estés escribiendo, había que adivinar si estabas en el medio de algo, y esa
  // adivinanza era global (un campo apagaba la ventana entera), callada y permanente.
  //
  // Acá se reemplaza el CONTENIDO de las zonas marcadas con `data-refresco`. Lo que cambia de
  // fondo es el costo de equivocarse: una zona que no se puede tocar queda vieja, y **todas las
  // demás se actualizan igual**.
  //
  // ⚠️ Se reemplaza el `innerHTML` de la zona, NUNCA el nodo. Es lo que salva los listeners
  // enganchados al contenedor: el drag & drop de tareas vive en el `<ul id="todo-list">` y
  // resuelve con `closest('.todo-item')`, así que sobrevive a que cambien los `<li>` y muere si
  // se reemplaza el `<ul>`. Los `onclick` inline sobreviven siempre, son atributos.
  const ZONAS = '[data-refresco]';

  function nombreZona(el) { return el.getAttribute('data-refresco'); }

  function zonas(raiz) {
    const mapa = new Map();
    (raiz || document).querySelectorAll(ZONAS).forEach(function (el) {
      mapa.set(nombreZona(el), el);
    });
    return mapa;
  }

  // Una zona está en uso si tenés el cursor adentro o si adentro hay algo escrito sin guardar.
  function enUso(el) {
    if (el.contains(document.activeElement) && document.activeElement !== document.body) {
      return true;
    }
    for (const campo of el.querySelectorAll('input, textarea')) {
      if (esTipeable(campo) && estaSucio(campo)) return true;
    }
    return false;
  }

  // Lo que haya que volver a inicializar sobre el contenido nuevo se registra acá: los listeners
  // que estaban enganchados a elementos de adentro se fueron con el HTML viejo. Hoy lo usa la
  // rueda de emociones de las notas especiales (day.js).
  window.BITACORA_REINIT = window.BITACORA_REINIT || [];

  function reiniciar(el) {
    (window.BITACORA_REINIT || []).forEach(function (fn) {
      try { fn(el); } catch (e) { console.warn('Bitácora: falló un re-init del refresco', e); }
    });
  }

  // Devuelve true si pudo dejar la página al día (aunque haya salteado alguna zona en uso).
  // Devuelve false para que el llamador caiga al camino de recargar.
  // ⚠️ El TEMA vive en el `<html>`, fuera de toda zona, y es el único de su clase: cambiarlo en
  // una ventana dejaba a la otra con el estilo viejo **y convencida de estar al día** —las zonas
  // venían idénticas, así que ni recargaba ni mostraba el aviso—. Es el fallo callado de siempre,
  // y se ve tan claro como "el widget dejó de sincronizarse".
  //
  // Se sincroniza este atributo y no "todo lo que esté fuera de las zonas": el formulario de nota
  // trae un color sugerido que se sortea POR PÁGINA (`services.color_sugerido`), así que comparar
  // el documento entero daría distinto en cada vuelta y volvería el parpadeo que este rediseño
  // vino a sacar.
  function sincronizarTema(doc) {
    const nuevo = doc.documentElement.getAttribute('data-theme');
    const actual = document.documentElement.getAttribute('data-theme');
    if (nuevo && nuevo !== actual) document.documentElement.setAttribute('data-theme', nuevo);
  }

  function actualizarZonas(html) {
    const doc = new DOMParser().parseFromString(html, 'text/html');
    sincronizarTema(doc);
    const nuevas = zonas(doc);
    const actuales = zonas();
    if (!actuales.size || !nuevas.size) return false;

    // ⚠️ Si el conjunto de zonas cambió, lo que cambió es la ESTRUCTURA de la página (apareció o
    // desapareció un bloque entero, como el "⚠️ Sin cerrar" del widget). Eso no lo cubre
    // reemplazar contenido, y no tiene que fingir que sí: se recarga.
    if (actuales.size !== nuevas.size) return false;
    for (const nombre of actuales.keys()) if (!nuevas.has(nombre)) return false;

    let quedaronViejas = false;
    actuales.forEach(function (el, nombre) {
      const nueva = nuevas.get(nombre);
      if (el.innerHTML === nueva.innerHTML) return;
      if (enUso(el)) { quedaronViejas = true; return; }
      el.innerHTML = nueva.innerHTML;
      reiniciar(el);
    });

    if (doc.title) document.title = doc.title;
    return !quedaronViejas;
  }

  function intentar() {
    if (!pendiente) { sacarAviso(); return; }

    // El camino bueno: actualizar sin tocar lo que estás usando. No pasa por `puedeRecargar`
    // justamente porque no destruye nada.
    //
    // ⚠️ Manda la marca de PÁGINA, no la presencia de zonas: el navbar aporta una zona a todas
    // las pantallas, así que mirando zonas sueltas /journal o /ajustes se darían por al día
    // porque el contador de atrasadas no cambió. Una pantalla a medio marcar tiene que recargar.
    if (document.querySelector('[data-refresco-parcial]')) {
      fetchOriginal(location.href, { cache: 'no-store' })
        .then(function (r) { return r.ok ? r.text() : null; })
        .then(function (html) {
          if (html && actualizarZonas(html)) { pendiente = false; sacarAviso(); return; }
          // O la estructura cambió, o alguna zona estaba en uso: al camino de siempre.
          recargarSiSePuede(html === null);
        })
        .catch(function () { recargarSiSePuede(true); });
      return;
    }
    recargarSiSePuede(false);
  }

  // El camino de siempre, que sí destruye la página y por eso tiene que preguntar.
  function recargarSiSePuede(huboError) {
    if (huboError) return;              // si falló la red, ya reintentará el poleo
    if (!puedeRecargar()) {
      if (!esperandoDesde) esperandoDesde = Date.now();
      else if (Date.now() - esperandoDesde > AVISO_TRAS) mostrarAviso();
      return;
    }
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
