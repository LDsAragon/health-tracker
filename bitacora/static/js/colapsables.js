// Estado abierto/cerrado de un <details>, recordado en localStorage.
// Tercer lugar que lo necesitaba (el visor de tareas y las dos zonas de Ajustes), así que
// vive acá en vez de copiado en cada plantilla.
(function () {
  window.recordarColapsable = function (id, key, abiertoPorDefecto) {
    const d = document.getElementById(id);
    if (!d) return;
    let guardado = null;
    try { guardado = localStorage.getItem(key); } catch (e) { /* modo privado */ }
    d.open = guardado === null ? abiertoPorDefecto : guardado === '1';
    d.addEventListener('toggle', () => {
      try { localStorage.setItem(key, d.open ? '1' : '0'); } catch (e) { /* idem */ }
    });
  };
})();
