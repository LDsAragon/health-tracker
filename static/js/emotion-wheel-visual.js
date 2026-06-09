// ── Rueda de emociones — 3 anillos concéntricos (base / media / específica) ─

let ewState = { angle: 0, picker: null };
let _ewAnimId = null;

// Radios (unidades SVG, viewBox "-130 -130 260 260")
const EW = {
  r0: 30,   // agujero central
  r1i: 32, r1o: 65,   // anillo 1 — emoción base
  r2i: 68, r2o: 96,   // anillo 2 — media
  r3i: 99, r3o: 120   // anillo 3 — específica
};

// ── Abrir / cerrar ────────────────────────────────────────────────────────

function openEWModal(pickerEl) {
  ewState = { angle: 0, picker: pickerEl };
  buildFullWheel();
  document.getElementById('ew-modal').style.display = 'flex';
  document.addEventListener('keydown', ewKeyHandler);
}

function closeEWModal() {
  document.getElementById('ew-modal').style.display = 'none';
  document.removeEventListener('keydown', ewKeyHandler);
  if (_ewAnimId) { cancelAnimationFrame(_ewAnimId); _ewAnimId = null; }
}

function ewOverlayClick(e) {
  if (e.target === document.getElementById('ew-modal')) closeEWModal();
}

// ── Teclado ───────────────────────────────────────────────────────────────

function ewKeyHandler(e) {
  if (document.getElementById('ew-modal').style.display === 'none') return;
  if (e.key === 'q' || e.key === 'Q' || e.key === 'ArrowLeft')  { e.preventDefault(); rotateWheel(-1); }
  if (e.key === 'e' || e.key === 'E' || e.key === 'ArrowRight') { e.preventDefault(); rotateWheel(+1); }
  if (e.key === 'Escape') { e.preventDefault(); closeEWModal(); }
}

// ── Rotación con snap a 60° ───────────────────────────────────────────────

function rotateWheel(dir) {
  if (_ewAnimId) { cancelAnimationFrame(_ewAnimId); _ewAnimId = null; }
  const from = ewState.angle;
  const to   = from + dir * 60;
  ewState.angle = to;
  animateWheelTo(from, to);
}

function animateWheelTo(from, to) {
  const start = performance.now(), dur = 320;
  function frame(now) {
    const t    = Math.min((now - start) / dur, 1);
    const ease = 1 - Math.pow(1 - t, 3); // ease-out cubic
    applyAngle(from + (to - from) * ease);
    if (t < 1) _ewAnimId = requestAnimationFrame(frame);
    else _ewAnimId = null;
  }
  _ewAnimId = requestAnimationFrame(frame);
}

function applyAngle(angle) {
  const g = document.getElementById('ew-wheel-g');
  if (!g) return;

  g.setAttribute('transform', `rotate(${angle})`);

  // Mantener texto del anillo 1 legible (contra-rotación inteligente)
  g.querySelectorAll('[data-r1lbl]').forEach(t => {
    const bi = +t.dataset.r1lbl;
    const tx = +t.getAttribute('x');
    const ty = +t.getAttribute('y');
    t.setAttribute('transform', `rotate(${textRot(bi * 60, angle)},${tx},${ty})`);
  });

  // Actualizar etiqueta central
  const bases   = Object.keys(EMOTION_WHEEL);
  const topBase = bases[topIdx(angle)];
  const cl = document.getElementById('ew-center-label');
  if (cl) { cl.textContent = topBase; cl.style.color = EMOTION_WHEEL[topBase].color; }
}

function textRot(baseAngle, wheelAngle) {
  // ángulo visual del sector en el mundo
  const w = ((baseAngle + wheelAngle) % 360 + 360) % 360;
  // si está en el semiciclo inferior, girar 180° para que no quede al revés
  const target = (w > 90 && w < 270) ? baseAngle + 180 : baseAngle;
  return target - wheelAngle;
}

function topIdx(angle) {
  let best = 0, bestDist = Infinity;
  for (let i = 0; i < 6; i++) {
    const pos  = ((i * 60 + angle) % 360 + 360) % 360;
    const dist = Math.min(pos, 360 - pos);
    if (dist < bestDist) { bestDist = dist; best = i; }
  }
  return best;
}

// ── Hover ─────────────────────────────────────────────────────────────────

function ewHover(base, mid, spec, depth, color) {
  const g = document.getElementById('ew-wheel-g');
  if (!g) return;

  g.querySelectorAll('[data-base]').forEach(el => {
    const eB = el.dataset.base, eM = el.dataset.mid,
          eS = el.dataset.specific, eD = +el.dataset.depth;

    // ¿es parte del camino hovered?
    const inPath = eB === base && (
      (eD === 1) ||
      (depth >= 2 && eD === 2 && eM === mid) ||
      (depth >= 3 && eD === 3 && eM === mid && eS === spec)
    );
    // ¿mismo base pero fuera del camino?
    const sameBase = eB === base && !inPath;

    el.style.opacity = inPath ? '1' : sameBase ? '0.55' : '0.12';
    el.style.filter  = inPath ? 'brightness(1.12)' : sameBase ? '' : 'saturate(0.25)';
  });

  const lbl = document.getElementById('ew-hover-label');
  if (!lbl) return;
  const sep = `<span class="ew-sep"> › </span>`;
  let html = `<span style="color:${color}">${base}</span>`;
  if (depth >= 2) html += sep + `<span style="color:${color}">${mid}</span>`;
  if (depth >= 3) html += sep + `<span style="color:${color}">${spec}</span>`;
  lbl.innerHTML = html;

  const hint = document.getElementById('ew-hover-hint');
  if (hint) hint.textContent = 'Click para guardar';
}

function ewHoverClear() {
  const g = document.getElementById('ew-wheel-g');
  if (!g) return;
  g.querySelectorAll('[data-base]').forEach(el => {
    el.style.opacity = '1';
    el.style.filter  = '';
  });
  const lbl  = document.getElementById('ew-hover-label');
  const hint = document.getElementById('ew-hover-hint');
  if (lbl)  lbl.innerHTML = '';
  if (hint) hint.textContent = 'Rotá para explorar · hover para ver · click para guardar';
}

// ── Selección ─────────────────────────────────────────────────────────────

function ewSelect(base, mid, spec, depth) {
  let val = base;
  if (depth >= 2 && mid)  val += ' > ' + mid;
  if (depth >= 3 && spec) val += ' > ' + spec;
  ewRestore(ewState.picker, val);
  closeEWModal();
}

// ── Construir SVG ─────────────────────────────────────────────────────────

function buildFullWheel() {
  const svg = document.getElementById('ew-svg');
  svg.innerHTML = '';

  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.id = 'ew-wheel-g';

  const bases = Object.keys(EMOTION_WHEEL);

  bases.forEach((base, bi) => {
    const baseColor = EMOTION_WHEEL[base].color;
    const mids      = Object.keys(EMOTION_WHEEL[base].children);
    const BASE_A    = bi * 60; // ángulo central del sector base (en grados, desde arriba)

    // ── Anillo 1 — base ────────────────────────────────────────────────
    const p1 = sector(EW.r1i, EW.r1o, BASE_A - 30, BASE_A + 30, baseColor, 0.6);
    p1.dataset.base  = base; p1.dataset.depth = '1';
    p1.style.cursor  = 'pointer';
    bindSlice(p1, base, null, null, 1, baseColor);
    g.appendChild(p1);

    // Texto del anillo 1 (contra-rotado dinámicamente)
    const r1mid = (EW.r1i + EW.r1o) / 2;
    const rad1  = BASE_A * Math.PI / 180;
    const tx = f(r1mid * Math.sin(rad1));
    const ty = f(-r1mid * Math.cos(rad1));
    const txt = svgText(base, tx, ty, '9px');
    txt.dataset.r1lbl = bi;
    g.appendChild(txt);

    mids.forEach((mid, mi) => {
      const MID_STEP = 60 / mids.length;       // 10°
      const midA1    = BASE_A - 30 + mi * MID_STEP;
      const midA2    = midA1 + MID_STEP;
      const midColor = tint(baseColor, 0.22 + 0.06 * (mi & 1));

      // ── Anillo 2 — media ───────────────────────────────────────────
      const p2 = sector(EW.r2i, EW.r2o, midA1, midA2, midColor, 0.4);
      p2.dataset.base  = base; p2.dataset.mid = mid; p2.dataset.depth = '2';
      p2.style.cursor  = 'pointer';
      bindSlice(p2, base, mid, null, 2, baseColor);
      g.appendChild(p2);

      const specs = EMOTION_WHEEL[base].children[mid];
      specs.forEach((spec, si) => {
        const SPEC_STEP = MID_STEP / 2;        // 5°
        const specA1    = midA1 + si * SPEC_STEP;
        const specA2    = specA1 + SPEC_STEP;
        const specColor = tint(baseColor, 0.38 + 0.08 * (si & 1));

        // ── Anillo 3 — específica ─────────────────────────────────────
        const p3 = sector(EW.r3i, EW.r3o, specA1, specA2, specColor, 0.3);
        p3.dataset.base     = base; p3.dataset.mid = mid;
        p3.dataset.specific = spec; p3.dataset.depth = '3';
        p3.style.cursor     = 'pointer';
        bindSlice(p3, base, mid, spec, 3, baseColor);
        g.appendChild(p3);
      });
    });
  });

  // Círculo central (tapa agujero)
  const hole = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  hole.setAttribute('cx', 0); hole.setAttribute('cy', 0); hole.setAttribute('r', EW.r0);
  hole.style.fill          = 'var(--surface2)';
  hole.style.stroke        = 'var(--border)';
  hole.style.strokeWidth   = '1';
  hole.style.pointerEvents = 'none';
  g.appendChild(hole);

  svg.appendChild(g);
  applyAngle(0);
  ewHoverClear();
}

function bindSlice(el, base, mid, spec, depth, color) {
  el.addEventListener('mouseover', () => ewHover(base, mid, spec, depth, color));
  el.addEventListener('mouseout',  ewHoverClear);
  el.addEventListener('click',     () => ewSelect(base, mid, spec, depth));
}

// ── Helpers SVG ───────────────────────────────────────────────────────────

function sector(ri, ro, a1deg, a2deg, color, sw) {
  const a1 = a1deg * Math.PI / 180, a2 = a2deg * Math.PI / 180;
  const lg = (a2deg - a1deg > 180) ? 1 : 0;
  const p  = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  p.setAttribute('d',
    `M${f(ro*Math.sin(a1))} ${f(-ro*Math.cos(a1))} ` +
    `A${ro} ${ro} 0 ${lg} 1 ${f(ro*Math.sin(a2))} ${f(-ro*Math.cos(a2))} ` +
    `L${f(ri*Math.sin(a2))} ${f(-ri*Math.cos(a2))} ` +
    `A${ri} ${ri} 0 ${lg} 0 ${f(ri*Math.sin(a1))} ${f(-ri*Math.cos(a1))}Z`
  );
  p.style.fill        = color;
  p.style.stroke      = 'rgba(0,0,0,0.18)';
  p.style.strokeWidth = String(sw);
  return p;
}

function svgText(label, tx, ty, size) {
  const t = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  t.setAttribute('x', tx); t.setAttribute('y', ty);
  t.setAttribute('text-anchor', 'middle');
  t.setAttribute('dominant-baseline', 'middle');
  t.style.fontSize     = size;
  t.style.fill         = 'rgba(255,255,255,0.9)';
  t.style.fontWeight   = '800';
  t.style.pointerEvents = 'none';
  t.style.userSelect   = 'none';
  t.textContent = label;
  return t;
}

// tint: mezcla color con blanco (factor 0=original, 1=blanco)
function tint(hex, factor) {
  const r = parseInt(hex.slice(1,3), 16);
  const g = parseInt(hex.slice(3,5), 16);
  const b = parseInt(hex.slice(5,7), 16);
  return `rgb(${~~(r+(255-r)*factor)},${~~(g+(255-g)*factor)},${~~(b+(255-b)*factor)})`;
}

function f(n) { return Math.round(n * 1000) / 1000; }
