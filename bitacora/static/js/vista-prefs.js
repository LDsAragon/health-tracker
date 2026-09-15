// Cómo dejaste acomodada la pantalla: anchos, altos, zoom y desplegables.
//
// Vivía en localStorage y la app de escritorio lo perdía en CADA arranque: localStorage va por
// origen, el origen es http://127.0.0.1:<puerto> y el puerto cambia siempre (puerto_seguro(),
// que nació para esquivar ERR_UNSAFE_PORT). Ahora vive en la base, por perfil.
//
// La LECTURA es síncrona: los valores ya vienen en la página (window.VISTA_PREFS, inyectado en
// el <head>), así que el zoom se aplica antes de pintar y los desplegables no parpadean.
// La ESCRITURA es un fetch que no se espera; si falla, la preferencia no se guarda y ya —
// nunca puede romper lo que estabas haciendo.
(function () {
  const PREFS = window.VISTA_PREFS || {};

  // Lazy: esto corre desde el <head>, donde todavía no hay <body>.
  function vistaActual() {
    return (document.body && document.body.dataset.vista) || 'app';
  }

  function post(url, datos) {
    try {
      const cuerpo = new URLSearchParams(datos);
      fetch(url, { method: 'POST', body: cuerpo }).catch(() => {});
    } catch (e) { /* sin fetch no se guarda, pero la página sigue andando */ }
  }

  window.prefLeer = function (clave) {
    const v = PREFS[clave];
    return v === undefined ? null : v;
  };

  window.prefGuardar = function (clave, valor, vista) {
    PREFS[clave] = String(valor);
    post('/vista/set', { vista: vista || vistaActual(), clave: clave, valor: String(valor) });
  };

  window.prefBorrar = function (clave, vista) {
    delete PREFS[clave];
    post('/vista/borrar', { vista: vista || vistaActual(), clave: clave });
  };

  window.prefReiniciarVista = function (vista) {
    post('/vista/reiniciar', { vista: vista || vistaActual() });
  };
})();
