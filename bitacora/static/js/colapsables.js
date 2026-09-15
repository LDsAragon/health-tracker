// Estado abierto/cerrado de un <details>, recordado en la base (vista-prefs.js): en
// localStorage se perdia en cada arranque de la app de escritorio.
// Tercer lugar que lo necesitaba (el visor de tareas y las dos zonas de Ajustes), así que
// vive acá en vez de copiado en cada plantilla.
(function () {
  window.recordarColapsable = function (id, key, abiertoPorDefecto) {
    const d = document.getElementById(id);
    if (!d) return;
    const guardado = window.prefLeer(key);
    d.open = guardado === null ? abiertoPorDefecto : guardado === '1';
    // ⚠️ Setear `.open` a mano dispara `toggle`, así que sin esta guarda la pantalla guardaba su
    // propio default apenas la abrías: una escritura al pedo (ahora son HTTP, no localStorage) y,
    // peor, "reiniciar esta vista" se deshacía solo en la recarga siguiente.
    d.addEventListener('toggle', () => {
      const valor = d.open ? '1' : '0';
      const actual = window.prefLeer(key);
      if (valor === actual || (actual === null && d.open === abiertoPorDefecto)) return;
      window.prefGuardar(key, valor);
    });
  };
})();
