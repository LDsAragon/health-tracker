// La muerte de una tarea: la animación ASCII que se reproduce sobre la fila al borrarla.
//
// El catálogo vive en el servidor (bitacora/despedidas.py) y llega en window.DESPEDIDAS; acá solo
// está el reproductor. Se lo llama desde confirmar.js, en el botón OK del modal: ya confirmaste y
// el formulario todavía no se envió.
//
// ⚠️ LA REGLA QUE NO SE NEGOCIA: borrar no puede depender de esto. `despedir()` recibe el callback
// que envía el formulario y **tiene que llamarlo siempre**: si el catálogo viene vacío, si el
// navegador no tiene lo que usamos, si algo tira a mitad de la animación o si un cuadro se cuelga,
// igual se llama —hay un timeout duro por encima de todo—. Es el mismo criterio que el
// `onsubmit="return false;"` de confirmar.js y que el botón Guardar que sigue en la plantilla de
// Ajustes: la parte decorativa puede fallar, la acción no.
(function () {
  const CATALOGO = window.DESPEDIDAS || [];
  const TOPE_MS = 1500;          // pase lo que pase, a los 1,5 s el formulario se envía
  const AZAR = 'aleatorio';
  const APAGADO = 'off';

  function elegir(slug) {
    if (!CATALOGO.length || slug === APAGADO) return null;
    if (!slug || slug === AZAR) return CATALOGO[Math.floor(Math.random() * CATALOGO.length)];
    return CATALOGO.find((d) => d.slug === slug) || null;
  }

  // Qué tan grande se dibuja. Son dos topes y hacen falta los dos, porque las dos pantallas donde
  // esto se ve son opuestas: el panel del día puede estar en su mínimo —ahí manda el ancho, y el
  // carácter monoespaciado mide ~0.6em, de ahí el divisor— y el visor de tareas es una fila de
  // 900px, donde manda el alto: sin ese tope el dibujo taparía las tres tareas de arriba y las
  // tres de abajo.
  function medida(anim, ancho, alto) {
    let cols = 0;
    let lineas = 1;
    anim.cuadros.forEach(function (c) {
      const filas = c.split('\n');
      if (filas.length > lineas) lineas = filas.length;
      filas.forEach(function (l) { if (l.length > cols) cols = l.length; });
    });
    return Math.max(7, Math.min(24,
                                Math.floor(ancho / (cols * 0.6)),
                                Math.floor((alto * 1.9) / lineas)));
  }

  // Reproduce `anim` encima de `fila` y llama a `fin()` al terminar. La caja va en el <body> con
  // position:fixed sobre el rectángulo de la fila: así no se le toca el layout a `.todo-row`, que
  // es un flex con su propio arreglo, ni se corre nada al aparecer.
  function reproducir(anim, fila, fin) {
    const r = fila.getBoundingClientRect();
    const caja = document.createElement('pre');
    caja.className = 'despedida-art';
    caja.style.left = r.left + 'px';
    caja.style.top = (r.top + r.height / 2) + 'px';
    caja.style.width = r.width + 'px';
    caja.style.fontSize = medida(anim, r.width, r.height) + 'px';
    document.body.appendChild(caja);
    fila.classList.add('despedida-yendo');

    let i = 0;
    caja.textContent = anim.cuadros[0];
    const reloj = setInterval(function () {
      i += 1;
      if (i >= anim.cuadros.length) {
        clearInterval(reloj);
        caja.remove();
        fin();
        return;
      }
      caja.textContent = anim.cuadros[i];
    }, anim.ms || 120);

    // Quien llame cancela con esto si el tope de tiempo llegó primero: no puede quedar una caja
    // pegada en la pantalla ni un intervalo corriendo sobre una página que ya se está yendo.
    return function () { clearInterval(reloj); caja.remove(); };
  }

  // La reproduce sobre un elemento cualquiera. La usa el control de Ajustes para previsualizar:
  // elegir entre cinco animaciones sin verlas no significa nada.
  let cancelarPrevia = null;

  window.despedirEn = function (elemento, slug) {
    // Tocar un chip tras otro no puede dejar dos animaciones encimadas en la misma caja.
    if (cancelarPrevia) { cancelarPrevia(); cancelarPrevia = null; }
    const anim = elegir(slug);
    if (!anim || !elemento) return;
    const limpiar = function () { elemento.classList.remove('despedida-yendo'); };
    const cancelar = reproducir(anim, elemento, limpiar);
    cancelarPrevia = function () { cancelar(); limpiar(); };
    setTimeout(function () {
      if (cancelarPrevia) { cancelarPrevia(); cancelarPrevia = null; }
    }, TOPE_MS);
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
      const fila = form.closest('.todo-row') || form.closest('.todo-item') || form;
      const anim = elegir(window.DESPEDIDA_ELEGIDA);
      if (!anim) { unaVez(); return; }
      reproducir(anim, fila, unaVez);
    } catch (e) {
      unaVez();
    }
  };
})();
