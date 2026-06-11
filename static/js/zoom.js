// Zoom estilo navegador, a nivel web (portable navegador ↔ pywebview/WebView2).
// Ctrl+rueda y Ctrl + +/- ajustan; Ctrl+0 (o Ctrl+Shift+R) resetea. Persistido en localStorage.
(function () {
  var KEY = 'app_zoom';
  var MIN = 0.5, MAX = 2.5, STEP = 0.1;
  var zoom = parseFloat(localStorage.getItem(KEY)) || 1;

  function clamp(z) { return Math.min(MAX, Math.max(MIN, Math.round(z * 100) / 100)); }
  function apply() { document.documentElement.style.zoom = zoom; }
  function set(z) { zoom = clamp(z); apply(); localStorage.setItem(KEY, String(zoom)); }

  apply();   // aplica el zoom guardado lo antes posible (script en <head>)

  // Ctrl + rueda del mouse
  window.addEventListener('wheel', function (e) {
    if (!e.ctrlKey) return;
    e.preventDefault();
    set(zoom + (e.deltaY < 0 ? STEP : -STEP));
  }, { passive: false });

  // Ctrl + (+/-/0) y Ctrl+Shift+R para resetear; Ctrl+R recarga (la ventana
  // nativa pywebview no tiene botón de refresh — en navegador es lo mismo que el default)
  window.addEventListener('keydown', function (e) {
    if (!e.ctrlKey) return;
    var k = e.key;
    if (k === '+' || k === '=') { e.preventDefault(); set(zoom + STEP); }
    else if (k === '-' || k === '_') { e.preventDefault(); set(zoom - STEP); }
    else if (k === '0') { e.preventDefault(); set(1); }
    else if (e.shiftKey && (k === 'R' || k === 'r')) { e.preventDefault(); set(1); }
    else if (k === 'r' || k === 'R') { e.preventDefault(); location.reload(); }
  });
})();
