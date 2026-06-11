// ── Rueda de emociones — motor data-driven (soporta 2 o 3 anillos) ─────────
// ew-wheel-g → paths que ROTAN · ew-label-g → textos · Selector (◄) a la derecha (90°)
// La rueda activa vive en ewState.wheel (spec normalizado): española (3 niveles) o Ekman (2).

let ewState   = { angle: 90, picker: null, wheel: null };
let _ewAnimId = null;
let _ewMouse  = { x: null, y: null };

function _ewTrackMouse(e) { _ewMouse.x = e.clientX; _ewMouse.y = e.clientY; }

// Después de rotar: busca el sector bajo el cursor y reactiva hover
function _reapplyHover() {
  if (_ewMouse.x === null) return;
  let el = document.elementFromPoint(_ewMouse.x, _ewMouse.y);
  while (el && !el.dataset.depth) el = el.parentElement;
  if (el && el.dataset.depth) {
    ewHover(el.dataset.base, el.dataset.mid || null, el.dataset.specific || null,
            +el.dataset.depth, _colorOf(ewState.wheel, el.dataset.base));
  }
}

// Geometría (viewBox "-180 -180 360 360")
const EW = { r0: 30, r1i: 32, r1o: 80, r2i: 84, r2o: 128, r3i: 132, r3o: 170 };
const ACTIVE_DEG = 90; // el sector activo es el que está en 90° (derecha)

// Radios/labels por anillo, según la cantidad de niveles
const ES_RINGS = {
  1: { ri: 32,  ro: 80,  lr: 56,  fs: '8px',   fw: '800' },
  2: { ri: 84,  ro: 128, lr: 106, fs: '6px',   fw: '700' },
  3: { ri: 132, ro: 170, lr: 151, fs: '5.5px', fw: '600' }
};
const EK_RINGS = {                       // 2 niveles → anillo exterior más amplio
  1: { ri: 32, ro: 80,  lr: 56,  fs: '8px', fw: '800' },
  2: { ri: 84, ro: 170, lr: 124, fs: '6px', fw: '700' }
};

// ── Spec de la rueda activa (normaliza ambas estructuras) ──────────────────

function ewWheelSpec(id) {
  if (id === 'ek' && typeof EKMAN_WHEEL !== 'undefined') {
    const bases = Object.keys(EKMAN_WHEEL).map(k => {
      const b = EKMAN_WHEEL[k];
      // id en INGLÉS (keys de EKMAN_CONTENT); label en ESPAÑOL (lo que se dibuja en la rueda)
      return {
        id: k, label: b.es, es: b.es, en: b.en, color: b.color,
        children: b.states.map(s => ({ id: s.en, label: s.es, es: s.es, en: s.en, children: [] }))
      };
    });
    return { id: 'ek', levels: 2, bases, rings: EK_RINGS, nodeStyle: 'noun', bilingual: true,
             coreNoun: true, // centros sustantivos (la Ira, el Miedo)
             content: (typeof EKMAN_CONTENT !== 'undefined' ? EKMAN_CONTENT : {}) };
  }
  // Por defecto: rueda española (3 niveles)
  const bases = Object.keys(EMOTION_WHEEL).map(k => {
    const b = EMOTION_WHEEL[k];
    return {
      id: k, label: k, es: k, color: b.color,
      children: Object.keys(b.children).map(m => ({
        id: m, label: m, es: m,
        children: b.children[m].map(s => ({ id: s, label: s, es: s, children: [] }))
      }))
    };
  });
  return { id: 'es', levels: 3, bases, rings: ES_RINGS, nodeStyle: 'adj', bilingual: false,
           coreNoun: false, // centros adjetivos (estar Enojado, estar Triste)
           content: (typeof EMOTION_CONTENT !== 'undefined' ? EMOTION_CONTENT : {}) };
}

function _specBase(W, baseId) { return W && W.bases.find(b => b.id === baseId) || null; }
function _specNode(W, baseId, midId, specId) {
  const b = _specBase(W, baseId); if (!b) return null;
  if (!midId) return b;
  const m = b.children.find(c => c.id === midId); if (!m) return null;
  if (!specId) return m;
  return m.children.find(c => c.id === specId) || null;
}
function _esOf(W, baseId, midId, specId) {
  const n = _specNode(W, baseId, midId, specId);
  return n ? n.es : (specId || midId || baseId);
}
function _colorOf(W, baseId) { const b = _specBase(W, baseId); return b ? b.color : '#8892a4'; }

// Distinción por intensidad (Atlas ordena los estados de leve→intenso; los arrays lo respetan)
function _ekIntensity(W, baseId, stateId) {
  const b = _specBase(W, baseId); if (!b) return '';
  const arr = b.children, i = arr.findIndex(s => s.id === stateId);
  if (i < 0) return '';
  const name = b.es.toLowerCase();
  const emo  = (EW_ART[b.es] === 'el') ? `del ${name}` : `de la ${name}`; // "de la ira", "del miedo"
  if (i === 0)            return `El estado más leve ${emo}; más suave que «${arr[i+1].es}».`;
  if (i === arr.length-1) return `El estado más intenso ${emo}; más fuerte que «${arr[i-1].es}».`;
  return `Más intenso que «${arr[i-1].es}», más leve que «${arr[i+1].es}».`;
}

// ── Ajuste al viewport efectivo ───────────────────────────────────────────
// Los vh/vw y media queries no se enteran del zoom web (CSS zoom en :root):
// medimos la ventana real, la dividimos por el zoom y publicamos el espacio
// disponible como variables CSS (--ew-w/--ew-h) + la clase .ew-stack que
// apila el panel lateral cuando el ancho efectivo no alcanza.
function ewFitModal() {
  const overlay = document.getElementById('ew-modal');
  if (!overlay) return;
  const z = parseFloat(document.documentElement.style.zoom) || 1;
  const w = window.innerWidth / z, h = window.innerHeight / z;
  overlay.style.setProperty('--ew-w', w + 'px');
  overlay.style.setProperty('--ew-h', h + 'px');
  overlay.classList.toggle('ew-stack', w < 980);
}
window.addEventListener('resize', ewFitModal);
window.addEventListener('app-zoom', ewFitModal);

// ── Abrir / cerrar ────────────────────────────────────────────────────────

function openEWModal(pickerEl, wheelId) {
  ewState = { angle: 90, picker: pickerEl, wheel: ewWheelSpec(wheelId || 'es') };
  buildFullWheel();
  ewFitModal();
  document.getElementById('ew-modal').style.display = 'flex';
  document.querySelectorAll('.ew-wheel-tab').forEach(t =>
    t.classList.toggle('active', t.dataset.wheel === ewState.wheel.id));
  document.addEventListener('keydown',    ewKeyHandler);
  document.addEventListener('mousemove',  _ewTrackMouse);
}

function closeEWModal() {
  document.getElementById('ew-modal').style.display = 'none';
  document.removeEventListener('keydown',    ewKeyHandler);
  document.removeEventListener('mousemove',  _ewTrackMouse);
  _ewMouse.x = null;
  if (_ewAnimId) { cancelAnimationFrame(_ewAnimId); _ewAnimId = null; }
}

function ewOverlayClick(e) {
  if (e.target === document.getElementById('ew-modal')) closeEWModal();
}

// Cambiar de rueda en vivo (toggle dentro del modal)
function ewSwitchWheel(wheelId) {
  if (!ewState.wheel || ewState.wheel.id === wheelId) return;
  ewState.angle = 90;
  ewState.wheel = ewWheelSpec(wheelId);
  buildFullWheel();
  document.querySelectorAll('.ew-wheel-tab').forEach(t => {
    t.classList.toggle('active', t.dataset.wheel === wheelId);
  });
}

// ── Teclado ───────────────────────────────────────────────────────────────

function ewKeyHandler(e) {
  if (document.getElementById('ew-modal').style.display === 'none') return;
  if (e.key === 'q' || e.key === 'Q' || e.key === 'ArrowLeft')  { e.preventDefault(); rotateWheel(-1); }
  if (e.key === 'e' || e.key === 'E' || e.key === 'ArrowRight') { e.preventDefault(); rotateWheel(+1); }
  if (e.key === 'Escape') { e.preventDefault(); closeEWModal(); }
}

// ── Rotación — snap de un sector con ease-out cúbico ───────────────────────

function rotateWheel(dir) {
  if (_ewAnimId) { cancelAnimationFrame(_ewAnimId); _ewAnimId = null; }
  const step = 360 / ewState.wheel.bases.length;
  const from = ewState.angle;
  const to   = from + dir * step;
  ewState.angle = to;
  animateWheelTo(from, to);
}

function animateWheelTo(from, to) {
  const start = performance.now(), dur = 340;
  function frame(now) {
    const t    = Math.min((now - start) / dur, 1);
    const ease = 1 - Math.pow(1 - t, 3);
    applyAngle(from + (to - from) * ease);
    if (t < 1) _ewAnimId = requestAnimationFrame(frame);
    else { _ewAnimId = null; _reapplyHover(); }
  }
  _ewAnimId = requestAnimationFrame(frame);
}

// ── applyAngle — núcleo de la actualización visual ────────────────────────

function applyAngle(angle) {
  const gWheel = document.getElementById('ew-wheel-g');
  const gLabel = document.getElementById('ew-label-g');
  const gClone = document.getElementById('ew-hover-clone-g');
  if (!gWheel || !gLabel) return;

  if (gClone && gClone.firstChild) gClone.innerHTML = '';
  gWheel.setAttribute('transform', `rotate(${angle})`);

  const W        = ewState.wheel;
  const topNode  = W.bases[topIdx(angle)];
  const topBase  = topNode.id;

  // ── 1. Highlight del sector activo en los paths ───────────────────────
  gWheel.querySelectorAll('[data-base]').forEach(el => {
    el.removeAttribute('transform');
    const isActive = el.dataset.base === topBase && el.dataset.depth === '1';
    if (el.dataset.fill0) el.style.fill = el.dataset.fill0;
    el.style.opacity     = '1';
    el.style.stroke      = isActive ? 'rgba(255,255,255,0.55)' : 'rgba(0,0,0,0.16)';
    el.style.strokeWidth = isActive ? '1.5' : strokeW(el.dataset.depth);
    el.style.filter      = isActive ? 'brightness(1.15)' : '';
  });

  // ── 2. Posición y orientación radial de labels ────────────────────────
  gLabel.querySelectorAll('[data-la]').forEach(el => {
    const initA    = +el.dataset.la;
    const r        = +el.dataset.lr;
    const worldDeg = ((initA + angle) % 360 + 360) % 360;
    const worldRad = worldDeg * Math.PI / 180;
    const wx = f(r * Math.sin(worldRad));
    const wy = f(-r * Math.cos(worldRad));
    el.setAttribute('x', wx);
    el.setAttribute('y', wy);

    let rot = worldDeg - 90;
    if (worldDeg > 180) rot += 180;
    el.setAttribute('transform', `rotate(${f(rot)},${wx},${wy})`);

    if (el._animId) { cancelAnimationFrame(el._animId); el._animId = null; }
    const ring     = +el.dataset.ring;
    const isActive = el.dataset.base === topBase;
    el.style.fill    = 'rgba(0,0,0,0.82)';
    el.style.opacity = ring === 1 ? '1' : (isActive ? '0.92' : '0.62');
  });

  // ── 3. Etiqueta central ───────────────────────────────────────────────
  const cl = document.getElementById('ew-center-label');
  if (cl) {
    cl.style.color = topNode.color;
    cl.innerHTML = W.bilingual
      ? `${topNode.label}<span style="display:block;font-size:8px;font-weight:600;opacity:.7">${topNode.en}</span>`
      : topNode.label;
  }
}

// Índice del sector más cercano a ACTIVE_DEG (90°, derecha)
function topIdx(angle) {
  const N = ewState.wheel.bases.length, span = 360 / N;
  let best = 0, bestDist = Infinity;
  for (let i = 0; i < N; i++) {
    const pos  = ((i * span + angle) % 360 + 360) % 360;
    const diff = Math.abs(((pos - ACTIVE_DEG + 180 + 360) % 360) - 180);
    if (diff < bestDist) { bestDist = diff; best = i; }
  }
  return best;
}

function strokeW(depth) {
  return depth === '1' ? '0.7' : depth === '2' ? '0.45' : '0.3';
}

// ── Hover — idéntico visualmente al sector activo ─────────────────────────

function ewHover(base, mid, spec, depth, color) {
  if (_ewAnimId) return; // durante el giro se ignora; _reapplyHover lo aplica al terminar

  const id2 = depth >= 2 ? base + '|' + mid : null;
  const id3 = depth >= 3 ? base + '|' + mid + '|' + spec : null;

  const gWheel = document.getElementById('ew-wheel-g');
  const srcByRing = {};
  if (gWheel) {
    gWheel.querySelectorAll('[data-base]').forEach(el => {
      const eB = el.dataset.base, eM = el.dataset.mid,
            eS = el.dataset.specific, eD = +el.dataset.depth;

      const inPath = eB === base && (
        eD === 1 ||
        (depth >= 2 && eD === 2 && eM === mid) ||
        (depth >= 3 && eD === 3 && eM === mid && eS === spec)
      );
      const sameBase = eB === base && !inPath;
      const lifted   = inPath && eD >= 2; // anillos 2 y 3 se clonan/rotan; el 1 no

      if (lifted) srcByRing[eD] = el;
      el.style.opacity     = lifted ? '0' : inPath ? '1' : sameBase ? '0.5' : '0.08';
      el.style.fill        = inPath ? solidFill(color, eD) : (el.dataset.fill0 || el.style.fill);
      el.style.stroke      = inPath ? 'rgba(255,255,255,0.55)' : 'rgba(0,0,0,0.16)';
      el.style.strokeWidth = inPath ? '1.5'  : strokeW(el.dataset.depth);
      el.style.filter      = '';
    });

    const gClone = document.getElementById('ew-hover-clone-g');
    if (gClone) {
      [[2, id2], [3, id3]].forEach(([ring, id]) => {
        let existing = gClone.querySelector(`[data-lift-ring="${ring}"]`);
        if (existing && existing.dataset.liftId === (id || '')) return;
        if (existing) existing.remove();
        if (!id || !srcByRing[ring]) return;
        const src   = srcByRing[ring];
        const clone = src.cloneNode(true);
        clone.dataset.liftRing  = String(ring);
        clone.dataset.liftId    = id;
        clone.style.pointerEvents = 'none';
        clone.style.opacity       = '1';
        clone.style.fill          = solidFill(color, ring);
        clone.style.filter        = '';
        clone.style.stroke        = 'rgba(255,255,255,0.55)';
        clone.style.strokeWidth   = '1.5';
        gClone.appendChild(clone);
        _animSectorClone(clone, ewState.angle, parseFloat(src.dataset.initAngle), ring);
      });
    }
  }

  const gLabel = document.getElementById('ew-label-g');
  if (gLabel) {
    gLabel.querySelectorAll('[data-la]').forEach(el => {
      const eB = el.dataset.base, eR = +el.dataset.ring;
      const eM = el.dataset.mid,  eS = el.dataset.specific;

      const inPath = eB === base && (
        eR === 1 ||
        (depth >= 2 && eR === 2 && eM === mid) ||
        (depth >= 3 && eR === 3 && eM === mid && eS === spec)
      );

      if (inPath) {
        el.style.fill    = 'rgba(0,0,0,0.90)';
        el.style.opacity = '1';
        _animLabelTo0(el, el.getAttribute('x'), el.getAttribute('y'));
      } else {
        el.style.opacity = '0.28';
        _setLabelRadial(el);
      }
    });
  }

  ewRenderInfo(base, mid, spec, depth, color);

  const lbl = document.getElementById('ew-hover-label');
  if (!lbl) return;
  const W    = ewState.wheel;
  const sep  = '<span class="ew-sep"> › </span>';
  const bEs  = _esOf(W, base);
  const mEs  = depth >= 2 ? _esOf(W, base, mid) : null;
  const sEs  = depth >= 3 ? _esOf(W, base, mid, spec) : null;
  let   html = `<span style="color:${color};font-weight:700">${bEs}</span>`;
  if (mEs) html += sep + `<span style="color:${color};font-weight:700">${mEs}</span>`;
  if (sEs) html += sep + `<span style="color:${color};font-weight:700">${sEs}</span>`;
  lbl.innerHTML = html;

  const hint = document.getElementById('ew-hover-hint');
  if (hint) hint.textContent = 'Click para guardar';
}

function ewHoverClear() {
  applyAngle(ewState.angle);
  const lbl  = document.getElementById('ew-hover-label');
  const hint = document.getElementById('ew-hover-hint');
  if (lbl)  lbl.innerHTML = '';
  if (hint) hint.textContent = 'Rotá para explorar · hover para leer · click para guardar';
  // El panel nunca queda vacío: muestra la emoción base activa (centro)
  const tb = ewState.wheel.bases[topIdx(ewState.angle)];
  ewRenderInfo(tb.id, null, null, 1, tb.color);
}

// ── Panel lateral de contexto ─────────────────────────────────────────────

// Resuelve los 4 campos del más profundo disponible, cayendo al ancestro (spec→mid→base)
function ewContent(base, mid, spec, depth) {
  const C = (ewState.wheel && ewState.wheel.content) || {};
  const deepest = depth >= 3 ? C[base + '|' + mid + '|' + spec]
                : depth >= 2 ? C[base + '|' + mid]
                :              C[base];
  const chain = [];
  if (depth >= 3 && spec) chain.push(C[base + '|' + mid + '|' + spec]);
  if (depth >= 2 && mid)  chain.push(C[base + '|' + mid]);
  chain.push(C[base]);
  const out = {};
  // Propios del nodo (NO heredan → evita repetir el de la base en estados sin distinguir)
  ['que', 'distinguir', 'fdef'].forEach(field => { if (deepest && deepest[field]) out[field] = deepest[field]; });
  // Heredables del ancestro (función/manifestación son de la base)
  ['sirve', 'manifiesta', 'fuente'].forEach(field => {
    for (const obj of chain) { if (obj && obj[field]) { out[field] = obj[field]; break; } }
  });
  return out;
}

const EW_ART = { Ira: 'la', Disgusto: 'el', Tristeza: 'la', Felicidad: 'la',
                 Sorpresa: 'la', Miedo: 'el', Asco: 'el', Disfrute: 'el' };

function ewRenderInfo(base, mid, spec, depth, color) {
  const panel = document.getElementById('ew-info-panel');
  if (!panel) return;
  const W = ewState.wheel;
  const c = ewContent(base, mid, spec, depth);

  // Ekman: si el estado no trae distinción propia, derivar la intensidad del Atlas
  if (W.id === 'ek' && depth >= 2 && !c.distinguir) c.distinguir = _ekIntensity(W, base, mid);

  // Breadcrumb en español (la "traducción"); la rueda muestra el idioma propio
  const baseEs = _esOf(W, base);
  const midEs  = depth >= 2 ? _esOf(W, base, mid) : null;
  const specEs = depth >= 3 ? _esOf(W, base, mid, spec) : null;
  let crumb = `<span style="color:${color}">${baseEs}</span>`;
  if (midEs)  crumb += ` <span class="ew-sep">›</span> ${midEs}`;
  if (specEs) crumb += ` <span class="ew-sep">›</span> ${specEs}`;

  const art     = EW_ART[baseEs] || 'la';
  const baseTxt = W.coreNoun ? `${art} ${baseEs}` : `estar ${baseEs}`; // "el Disfrute" / "estar Enojado"
  const baseN   = `<span style="color:${color}">${baseTxt}</span>`;     // raíz pintada con su color

  // Nombre del segmento: bilingüe "es/inglés" cuando la rueda es bilingüe (Ekman); pintado de blanco
  const nodeId  = depth >= 3 ? spec : depth >= 2 ? mid : null;          // id = inglés en la rueda Ekman
  const nodoEs  = specEs || midEs || baseEs;
  const nodoTxt = (W.bilingual && nodeId && nodeId !== nodoEs) ? `${nodoEs}/${nodeId}` : nodoEs;
  const nodeN   = `<span style="color:#fff">${nodoTxt}</span>`;

  const manifLabel = `Cómo se manifiesta ${baseN}`;
  const sirveLabel = `Para qué sirve ${baseN}`;
  let queLabel, distLabel;
  if (depth >= 2) {
    queLabel  = W.nodeStyle === 'noun' ? `Qué es «${nodeN}»` : `Qué es sentirse ${nodeN}`;
    distLabel = `Cómo distinguir «${nodeN}»`;
  } else {
    queLabel  = `Qué es ${baseN}`;
    distLabel = `Disparadores y cómo distinguir ${baseN}`;
  }

  const sec = (label, val) =>
    val ? `<div class="ew-info-sec"><h4>${label}</h4><p>${val}</p></div>` : '';

  // Atribución data-driven: cada entrada trae su fuente/origen; sin contenido → sin línea.
  const _src = [];
  if (c.fdef)   _src.push(`Definición: ${c.fdef}`);
  if (c.fuente) _src.push(`Fuente: ${c.fuente}`);
  const srcLine = _src.join(' · ');

  panel.innerHTML =
    `<div class="ew-info-title">${crumb}</div>` +
    sec(manifLabel, c.manifiesta) +
    sec(sirveLabel, c.sirve) +
    '<div class="ew-info-divider"></div>' +
    sec(queLabel, c.que) +
    sec(distLabel, c.distinguir) +
    (srcLine ? `<div class="ew-info-src">${srcLine}</div>` : '');
}

// Restaura un label a su orientación radial de reposo (snap, sin animar)
function _setLabelRadial(el) {
  if (el._animId) { cancelAnimationFrame(el._animId); el._animId = null; }
  const w = ((+el.dataset.la + ewState.angle) % 360 + 360) % 360;
  let rot = w - 90; if (w > 180) rot += 180;
  el.setAttribute('transform', `rotate(${f(rot)},${el.getAttribute('x')},${el.getAttribute('y')})`);
}

// Anima el label desde su rotación radial actual hasta 0° (horizontal)
function _animLabelTo0(el, tx, ty) {
  if (el._animId) { cancelAnimationFrame(el._animId); el._animId = null; }
  const match   = (el.getAttribute('transform') || '').match(/rotate\(([-\d.]+)/);
  const fromRot = _norm180(match ? parseFloat(match[1]) : 0);
  if (Math.abs(fromRot) < 0.5) { el.setAttribute('transform', `rotate(0,${tx},${ty})`); return; }
  const start = performance.now(), dur = 130;
  function tick(now) {
    const t = Math.min((now - start) / dur, 1);
    el.setAttribute('transform', `rotate(${f(fromRot * Math.pow(1 - t, 3))},${tx},${ty})`);
    if (t < 1) el._animId = requestAnimationFrame(tick);
    else el._animId = null;
  }
  el._animId = requestAnimationFrame(tick);
}

// Anima el clon del sector: lo inclina alrededor de su centro hasta quedar horizontal.
function _animSectorClone(clone, ewAngle, initA, depth) {
  const ring   = ewState.wheel.rings[depth] || ewState.wheel.rings[1];
  const r      = (ring.ri + ring.ro) / 2;
  const wDeg   = ((initA + ewAngle) % 360 + 360) % 360;
  const wRad   = wDeg * Math.PI / 180;
  const wx     = f(r * Math.sin(wRad));
  const wy     = f(-r * Math.cos(wRad));
  let   radAng = wDeg - 90;
  if (wDeg > 180) radAng += 180;
  radAng = _norm180(radAng); // camino más corto: ningún segmento gira más de 90°

  if (Math.abs(radAng) < 0.5) { clone.setAttribute('transform', `rotate(${ewAngle})`); return; }
  const start = performance.now(), dur = 130;
  function tick(now) {
    const t    = Math.min((now - start) / dur, 1);
    const ease = 1 - Math.pow(1 - t, 3);
    const tilt = f(-radAng * ease);
    clone.setAttribute('transform', `rotate(${tilt},${wx},${wy}) rotate(${ewAngle})`);
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
}

// ── Selección ─────────────────────────────────────────────────────────────

function ewSelect(base, mid, spec, depth) {
  const W = ewState.wheel;
  const parts = [ _esOf(W, base) ];
  if (depth >= 2 && mid)  parts.push(_esOf(W, base, mid));
  if (depth >= 3 && spec) parts.push(_esOf(W, base, mid, spec));
  let val = parts.join(' > ');
  if (W.id !== 'es') val = W.id + '::' + val; // origen de taxonomía (ej. "ek::Ira > Frustración")
  ewRestore(ewState.picker, val);
  closeEWModal();
}

// ── Construir SVG (genérico según el spec activo) ──────────────────────────

function buildFullWheel() {
  const W   = ewState.wheel;
  const svg = document.getElementById('ew-svg');
  svg.innerHTML = '';
  svg.onmouseleave = ewHoverClear; // reset total solo al salir de la rueda

  const gWheel = svgG('ew-wheel-g');
  const gClone = svgG('ew-hover-clone-g');
  const gLabel = svgG('ew-label-g');

  const N = W.bases.length, span = 360 / N;
  const R1 = W.rings[1], R2 = W.rings[2], R3 = W.rings[3];

  W.bases.forEach((b, bi) => {
    const baseColor = b.color;
    const baseC = bi * span;          // ángulo central de la base
    const start = baseC - span / 2;

    // Anillo 1 — base
    const p1 = sector(R1.ri, R1.ro, start, start + span, baseColor, 0.7);
    p1.dataset.base = b.id; p1.dataset.depth = '1'; p1.dataset.initAngle = f(baseC);
    p1.style.cursor = 'pointer';
    bindSlice(p1, b.id, null, null, 1, baseColor);
    gWheel.appendChild(p1);
    gLabel.appendChild(makeLabel(b.label, baseC, R1.lr, R1.fs, R1.fw, b.id, 1, b.es));

    const mids = b.children, M = mids.length, midArc = span / M;
    mids.forEach((m, mi) => {
      const mStart = start + mi * midArc;
      const midC   = mStart + midArc / 2;
      const midColor = tint(baseColor, 0.20 + 0.06 * (mi & 1));

      const p2 = sector(R2.ri, R2.ro, mStart, mStart + midArc, midColor, 0.45);
      p2.dataset.base = b.id; p2.dataset.mid = m.id; p2.dataset.depth = '2'; p2.dataset.initAngle = f(midC);
      p2.style.cursor = 'pointer';
      bindSlice(p2, b.id, m.id, null, 2, baseColor);
      gWheel.appendChild(p2);
      const lbl2 = makeLabel(m.label, midC, R2.lr, R2.fs, R2.fw, b.id, 2, m.es);
      lbl2.dataset.mid = m.id;
      gLabel.appendChild(lbl2);

      if (W.levels >= 3 && m.children.length) {
        const specs = m.children, K = specs.length, specArc = midArc / K;
        specs.forEach((s, si) => {
          const sStart = mStart + si * specArc;
          const specC  = sStart + specArc / 2;
          const specColor = tint(baseColor, 0.36 + 0.08 * (si & 1));

          const p3 = sector(R3.ri, R3.ro, sStart, sStart + specArc, specColor, 0.3);
          p3.dataset.base = b.id; p3.dataset.mid = m.id; p3.dataset.specific = s.id;
          p3.dataset.depth = '3'; p3.dataset.initAngle = f(specC);
          p3.style.cursor = 'pointer';
          bindSlice(p3, b.id, m.id, s.id, 3, baseColor);
          gWheel.appendChild(p3);
          const lbl3 = makeLabel(s.label, specC, R3.lr, R3.fs, R3.fw, b.id, 3, s.es);
          lbl3.dataset.mid = m.id; lbl3.dataset.specific = s.id;
          gLabel.appendChild(lbl3);
        });
      }
    });
  });

  // Agujero central (no rota)
  const hole = svgEl('circle');
  hole.setAttribute('r', EW.r0);
  hole.setAttribute('cx', 0); hole.setAttribute('cy', 0);
  hole.style.fill          = 'var(--surface2)';
  hole.style.stroke        = 'var(--border)';
  hole.style.strokeWidth   = '1.5';
  hole.style.pointerEvents = 'none';
  gLabel.appendChild(hole);

  svg.appendChild(gWheel);
  svg.appendChild(gClone);
  svg.appendChild(gLabel);

  // Selector ◄ fijo a la derecha (90° = eje X positivo)
  const ptr = svgEl('polygon');
  ptr.setAttribute('points', '177,-9 177,9 165,0');
  ptr.style.fill          = 'rgba(255,255,255,0.92)';
  ptr.style.pointerEvents = 'none';
  ptr.style.filter        = 'drop-shadow(-1px 0 4px rgba(0,0,0,0.7))';
  svg.appendChild(ptr);

  applyAngle(ewState.angle);
  ewHoverClear();
}

// ── Helpers ───────────────────────────────────────────────────────────────

function makeLabel(text, initAngle, r, fontSize, fontWeight, base, ring, esText) {
  const rad = initAngle * Math.PI / 180;
  const el  = svgEl('text');
  el.setAttribute('x', f(r * Math.sin(rad)));
  el.setAttribute('y', f(-r * Math.cos(rad)));
  el.setAttribute('text-anchor', 'middle');
  el.setAttribute('dominant-baseline', 'middle');
  el.dataset.la   = initAngle;
  el.dataset.lr   = r;
  el.dataset.base = base;
  el.dataset.ring = ring;
  if (esText) el.dataset.es = esText;
  el.style.fontSize      = fontSize;
  el.style.fill          = 'rgba(255,255,255,0.92)';
  el.style.fontWeight    = fontWeight;
  el.style.pointerEvents = 'none';
  el.style.userSelect    = 'none';
  el.textContent = text;
  return el;
}

function bindSlice(el, base, mid, spec, depth, color) {
  el.addEventListener('mouseover', () => ewHover(base, mid, spec, depth, color));
  el.addEventListener('click',     () => ewSelect(base, mid, spec, depth));
}

function sector(ri, ro, a1deg, a2deg, color, sw) {
  const a1 = a1deg * Math.PI / 180, a2 = a2deg * Math.PI / 180;
  const lg = (a2deg - a1deg > 180) ? 1 : 0;
  const p  = svgEl('path');
  p.setAttribute('d',
    `M${f(ro*Math.sin(a1))} ${f(-ro*Math.cos(a1))} ` +
    `A${ro} ${ro} 0 ${lg} 1 ${f(ro*Math.sin(a2))} ${f(-ro*Math.cos(a2))} ` +
    `L${f(ri*Math.sin(a2))} ${f(-ri*Math.cos(a2))} ` +
    `A${ri} ${ri} 0 ${lg} 0 ${f(ri*Math.sin(a1))} ${f(-ri*Math.cos(a1))}Z`
  );
  p.style.fill        = color;
  p.dataset.fill0     = color;
  p.style.stroke      = 'rgba(0,0,0,0.16)';
  p.style.strokeWidth = String(sw);
  return p;
}

function svgEl(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }
function svgG(id)   { const g = svgEl('g'); g.id = id; return g; }
function tint(hex, f2) {
  const r = parseInt(hex.slice(1,3), 16), g = parseInt(hex.slice(3,5), 16), b = parseInt(hex.slice(5,7), 16);
  return `rgb(${~~(r+(255-r)*f2)},${~~(g+(255-g)*f2)},${~~(b+(255-b)*f2)})`;
}
// Color sólido para hover — casi el color base, apenas un toque más claro hacia afuera
function solidFill(baseHex, depth) {
  const f2 = depth === 1 ? 0 : depth === 2 ? 0.05 : 0.10;
  return f2 === 0 ? baseHex : tint(baseHex, f2);
}
function f(n) { return Math.round(n * 1000) / 1000; }
// Normaliza un ángulo al rango (-180, 180] — camino de rotación más corto
function _norm180(a) { return ((a + 180) % 360 + 360) % 360 - 180; }
