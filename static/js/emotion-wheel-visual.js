// ── Rueda de emociones — 3 anillos concéntricos ────────────────────────────
// Dos grupos SVG independientes:
//   ew-wheel-g  → paths que ROTAN con la rueda
//   ew-label-g  → textos FIJOS (posición se actualiza, nunca rotan)

let ewState = { angle: 0, picker: null };
let _ewAnimId = null;

// Geometría (unidades SVG, viewBox "-180 -180 360 360", display 600×600)
const EW = {
  r0: 30,               // agujero central
  r1i: 32,  r1o: 80,   // anillo 1 — base      (label r=56)
  r2i: 84,  r2o: 128,  // anillo 2 — media      (label r=106)
  r3i: 132, r3o: 170,  // anillo 3 — específica (label r=151)
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
  const start = performance.now(), dur = 340;
  function frame(now) {
    const t    = Math.min((now - start) / dur, 1);
    const ease = 1 - Math.pow(1 - t, 3);
    applyAngle(from + (to - from) * ease);
    if (t < 1) _ewAnimId = requestAnimationFrame(frame);
    else _ewAnimId = null;
  }
  _ewAnimId = requestAnimationFrame(frame);
}

// ── Aplicar ángulo (llamado en cada frame) ────────────────────────────────

function applyAngle(angle) {
  // 1. Rotar el grupo de paths
  const gWheel = document.getElementById('ew-wheel-g');
  if (!gWheel) return;
  gWheel.setAttribute('transform', `rotate(${angle})`);

  // 2. Actualizar posición (no rotación) de todos los labels
  const bases   = Object.keys(EMOTION_WHEEL);
  const top     = topIdx(angle);
  const topBase = bases[top];

  const gLabel = document.getElementById('ew-label-g');
  if (!gLabel) return;

  gLabel.querySelectorAll('[data-la]').forEach(el => {
    // data-la = ángulo inicial del sector (grados desde arriba)
    // data-lr = radio del label
    const initA    = +el.dataset.la;
    const r        = +el.dataset.lr;
    const worldRad = (initA + angle) * Math.PI / 180;
    el.setAttribute('x', f(r * Math.sin(worldRad)));
    el.setAttribute('y', f(-r * Math.cos(worldRad)));

    // Opacidad: ring1 siempre visible, ring2/3 resaltan la base en el tope
    const ring = +el.dataset.ring;
    if (ring === 1) {
      el.style.opacity = '1';
    } else {
      el.style.opacity = el.dataset.base === topBase ? '0.92' : '0.18';
    }
  });

  // 3. Etiqueta central
  const cl = document.getElementById('ew-center-label');
  if (cl) { cl.textContent = topBase; cl.style.color = EMOTION_WHEEL[topBase].color; }
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
  const gWheel = document.getElementById('ew-wheel-g');
  if (gWheel) {
    gWheel.querySelectorAll('[data-base]').forEach(el => {
      const eB = el.dataset.base, eM = el.dataset.mid,
            eS = el.dataset.specific, eD = +el.dataset.depth;
      const inPath = eB === base && (
        eD === 1 ||
        (depth >= 2 && eD === 2 && eM === mid) ||
        (depth >= 3 && eD === 3 && eM === mid && eS === spec)
      );
      el.style.opacity = inPath ? '1' : (eB === base ? '0.55' : '0.1');
      el.style.filter  = inPath ? 'brightness(1.15)' : '';
    });
  }

  const lbl = document.getElementById('ew-hover-label');
  if (!lbl) return;
  const sep  = '<span class="ew-sep"> › </span>';
  let   html = `<span style="color:${color};font-weight:700">${base}</span>`;
  if (depth >= 2) html += sep + `<span style="color:${color};font-weight:700">${mid}</span>`;
  if (depth >= 3) html += sep + `<span style="color:${color};font-weight:700">${spec}</span>`;
  lbl.innerHTML = html;

  const hint = document.getElementById('ew-hover-hint');
  if (hint) hint.textContent = 'Click para guardar';
}

function ewHoverClear() {
  const gWheel = document.getElementById('ew-wheel-g');
  if (gWheel) {
    gWheel.querySelectorAll('[data-base]').forEach(el => {
      el.style.opacity = '1';
      el.style.filter  = '';
    });
  }
  const lbl  = document.getElementById('ew-hover-label');
  const hint = document.getElementById('ew-hover-hint');
  if (lbl)  lbl.innerHTML = '';
  if (hint) hint.textContent = 'Rotá para explorar · hover para leer · click para guardar';
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

  const gWheel = svgG('ew-wheel-g'); // paths rotantes
  const gLabel = svgG('ew-label-g'); // labels fijos

  const bases = Object.keys(EMOTION_WHEEL);

  bases.forEach((base, bi) => {
    const baseColor = EMOTION_WHEEL[base].color;
    const mids      = Object.keys(EMOTION_WHEEL[base].children);
    const BASE_A    = bi * 60; // ángulo central del sector base (0° = arriba)

    // ── Anillo 1 paths ────────────────────────────────────────────────
    const p1 = sector(EW.r1i, EW.r1o, BASE_A - 30, BASE_A + 30, baseColor, 0.7);
    p1.dataset.base  = base; p1.dataset.depth = '1';
    p1.style.cursor  = 'pointer';
    bindSlice(p1, base, null, null, 1, baseColor);
    gWheel.appendChild(p1);

    // Anillo 1 label (dentro del sector)
    gLabel.appendChild(makeLabel(base, BASE_A, EW.r1i + (EW.r1o - EW.r1i) / 2, '9.5px', '800', base, 1));

    mids.forEach((mid, mi) => {
      const MID_STEP = 60 / mids.length; // 10°
      const midA1    = BASE_A - 30 + mi * MID_STEP;
      const midA2    = midA1 + MID_STEP;
      const midCtr   = midA1 + MID_STEP / 2;
      const midColor = tint(baseColor, 0.20 + 0.06 * (mi & 1));

      // ── Anillo 2 paths ──────────────────────────────────────────────
      const p2 = sector(EW.r2i, EW.r2o, midA1, midA2, midColor, 0.45);
      p2.dataset.base  = base; p2.dataset.mid = mid; p2.dataset.depth = '2';
      p2.style.cursor  = 'pointer';
      bindSlice(p2, base, mid, null, 2, baseColor);
      gWheel.appendChild(p2);

      // Anillo 2 label
      gLabel.appendChild(makeLabel(mid, midCtr, EW.r2i + (EW.r2o - EW.r2i) / 2, '7px', '700', base, 2));

      const specs = EMOTION_WHEEL[base].children[mid];
      specs.forEach((spec, si) => {
        const SPEC_STEP = MID_STEP / 2; // 5°
        const specA1    = midA1 + si * SPEC_STEP;
        const specCtr   = specA1 + SPEC_STEP / 2;
        const specColor = tint(baseColor, 0.36 + 0.08 * (si & 1));

        // ── Anillo 3 paths ────────────────────────────────────────────
        const p3 = sector(EW.r3i, EW.r3o, specA1, specA1 + SPEC_STEP, specColor, 0.3);
        p3.dataset.base     = base; p3.dataset.mid = mid;
        p3.dataset.specific = spec; p3.dataset.depth = '3';
        p3.style.cursor     = 'pointer';
        bindSlice(p3, base, mid, spec, 3, baseColor);
        gWheel.appendChild(p3);

        // Anillo 3 label
        gLabel.appendChild(makeLabel(spec, specCtr, EW.r3i + (EW.r3o - EW.r3i) / 2, '6.5px', '600', base, 3));
      });
    });
  });

  // Círculo central (en gLabel para que no rote)
  const hole = svgEl('circle');
  hole.setAttribute('cx', 0); hole.setAttribute('cy', 0); hole.setAttribute('r', EW.r0);
  hole.style.fill          = 'var(--surface2)';
  hole.style.stroke        = 'var(--border)';
  hole.style.strokeWidth   = '1.5';
  hole.style.pointerEvents = 'none';
  gLabel.appendChild(hole);

  svg.appendChild(gWheel);
  svg.appendChild(gLabel);
  applyAngle(0);
  ewHoverClear();
}

// ── Helpers ───────────────────────────────────────────────────────────────

function makeLabel(text, initAngle, r, fontSize, fontWeight, base, ring) {
  const rad = initAngle * Math.PI / 180;
  const el  = svgEl('text');
  el.setAttribute('x', f(r * Math.sin(rad)));
  el.setAttribute('y', f(-r * Math.cos(rad)));
  el.setAttribute('text-anchor', 'middle');
  el.setAttribute('dominant-baseline', 'middle');
  el.dataset.la   = initAngle; // ángulo inicial
  el.dataset.lr   = r;         // radio del label
  el.dataset.base = base;
  el.dataset.ring = ring;
  el.style.fontSize    = fontSize;
  el.style.fill        = ring === 1 ? 'rgba(255,255,255,0.92)' : 'rgba(255,255,255,0.88)';
  el.style.fontWeight  = fontWeight;
  el.style.pointerEvents = 'none';
  el.style.userSelect  = 'none';
  el.textContent = text;
  return el;
}

function bindSlice(el, base, mid, spec, depth, color) {
  el.addEventListener('mouseover', () => ewHover(base, mid, spec, depth, color));
  el.addEventListener('mouseout',  ewHoverClear);
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
  p.style.stroke      = 'rgba(0,0,0,0.16)';
  p.style.strokeWidth = String(sw);
  return p;
}

function svgEl(tag) { return document.createElementNS('http://www.w3.org/2000/svg', tag); }
function svgG(id)  { const g = svgEl('g'); g.id = id; return g; }
function tint(hex, f2) {
  const r = parseInt(hex.slice(1,3), 16), g = parseInt(hex.slice(3,5), 16), b = parseInt(hex.slice(5,7), 16);
  return `rgb(${~~(r+(255-r)*f2)},${~~(g+(255-g)*f2)},${~~(b+(255-b)*f2)})`;
}
function f(n) { return Math.round(n * 1000) / 1000; }
