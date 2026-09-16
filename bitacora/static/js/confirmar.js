// Confirmaciones con la estética de la app, en vez del `confirm()` del navegador.
//
// En la ventana de escritorio ese diálogo aparece encabezado por "127.0.0.1:65015 dice", que es
// justo lo contrario de una app propia. Eran 16 repartidos en 8 pantallas, todos con la misma
// forma (`onsubmit="return confirm('...')"` sobre un <form>), así que se resuelven declarando el
// texto en el form y dejando el diálogo en un solo lugar.
//
// Cómo se usa:
//   <form ... data-confirmar="¿Eliminar esta tarea?" onsubmit="return false;">
//   <form ... data-confirmar="..." data-confirmar-ok="Vaciar el perfil" onsubmit="return false;">
//   <form ... data-confirmar="..." data-confirmar-suave onsubmit="return false;">
//
// ⚠️ El `onsubmit="return false;"` no es decorativo y no se puede sacar: es el fallback. El
// `confirm()` nativo lo ponía el navegador, así que aparecía aunque el JS de la app estuviera
// roto; un modal propio sin esa guarda haría que un JS roto envíe el formulario **sin preguntar
// nada**, y cuatro de estos borran datos (vaciar perfil, eliminar perfil, borrar todos, restaurar
// un backup). Con el `return false` inline, si este archivo no corre el formulario no se envía:
// que sin JS no se pueda borrar es aceptable, que borre sin preguntar no. Es el mismo criterio
// que mantiene el botón Guardar en la plantilla de Ajustes.
(function () {
  const overlay = document.getElementById('confirmar-modal');
  if (!overlay) return;

  const texto   = document.getElementById('confirmar-texto');
  const btnOk   = document.getElementById('confirmar-ok');
  const btnNo   = document.getElementById('confirmar-no');
  let pendiente = null;

  function abrir(form) {
    pendiente = form;
    // Los mensajes venían del `confirm()`, donde el salto de línea era \n. Se respetan.
    texto.textContent = form.dataset.confirmar || '¿Confirmás?';
    btnOk.textContent = form.dataset.confirmarOk || 'Confirmar';
    // La mayoría de estas acciones borra o reemplaza datos, así que el botón es rojo por
    // defecto y se pide `data-confirmar-suave` para las que no (combinar datos, mover tareas).
    btnOk.className = form.hasAttribute('data-confirmar-suave') ? 'btn-primary' : 'btn-delete-sm';
    overlay.style.display = 'flex';
    btnNo.focus();                    // el default es cancelar, no aceptar
  }

  function cerrar() {
    overlay.style.display = 'none';
    pendiente = null;
  }

  btnNo.addEventListener('click', cerrar);

  btnOk.addEventListener('click', function () {
    const form = pendiente;
    cerrar();
    // `form.submit()` y no `requestSubmit()`: el segundo volvería a disparar el evento submit y
    // caería otra vez acá. La validación HTML5 ya corrió (el evento submit no llega si falla).
    const enviar = function () { if (form) form.submit(); };
    // Acá se reproduce la animación de borrado (despedidas.js): ya confirmaste y el formulario
    // todavía no se envió. ⚠️ Si ese archivo no cargó, o el formulario no la pide, se envía igual:
    // la parte decorativa no puede quedar en el camino de un borrado.
    if (form && form.hasAttribute('data-despedida') && window.despedir) window.despedir(form, enviar);
    else enviar();
  });

  // Clic afuera y Escape cancelan, como el resto de los modales de la app.
  overlay.addEventListener('click', function (e) { if (e.target === overlay) cerrar(); });
  document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape' && overlay.style.display === 'flex') cerrar();
  });

  document.querySelectorAll('form[data-confirmar]').forEach(function (form) {
    // Se saca el `return false` del atributo: ya cumplió su función de fallback y desde acá el
    // submit lo controla el listener.
    form.removeAttribute('onsubmit');
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      abrir(form);
    });
  });
})();
