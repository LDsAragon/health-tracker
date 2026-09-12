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

  // ⚠️ Las escrituras PROPIAS de esta página no son "cambios de la otra ventana": si contaran,
  // tocar un switch en Ajustes (que guarda al instante por AJAX) o tildar el aviso de tareas
  // haría que la página se recargue sola a los 3 segundos. Los formularios normales no tienen el
  // problema porque recargan y traen un token nuevo; los que hacen fetch, sí.
  //
  // Se envuelve fetch en vez de avisar desde cada llamador: hoy hay cuatro (ajustes.js, day.js,
  // week.html y el "visto" del aviso), y el quinto que alguien agregue volvería a traer el bug.
  // Acá solo se OBSERVA: la respuesta se devuelve intacta.
  const fetchOriginal = window.fetch;
  window.fetch = function (recurso, opciones) {
    const metodo = ((opciones && opciones.method) || 'GET').toUpperCase();
    const p = fetchOriginal.apply(this, arguments);
    if (metodo !== 'GET' && metodo !== 'HEAD') {
      p.then(function (r) {
        if (r && r.ok) alDia();
      }).catch(function () { /* que falle el POST no es asunto del refresco */ });
    }
    return p;
  };

  function alDia() {
    fetchOriginal('/refresco', { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.text() : null; })
      .then(function (t) { if (t) referencia = t; })
      .catch(function () {});
  }

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

  setInterval(function () {
    if (document.hidden) return;            // el widget tapado o la ventana minimizada
    fetchOriginal('/refresco', { cache: 'no-store' })
      .then(function (r) { return r.ok ? r.text() : null; })
      .then(function (token) {
        // Con borrador no se recarga, pero tampoco se pierde el aviso: al tick siguiente el
        // token sigue distinto y se reintenta.
        if (token && token !== referencia && !hayBorrador()) location.reload();
      })
      .catch(function () { /* la app se está cerrando, o el server todavía no levantó */ });
  }, INTERVALO);
})();
