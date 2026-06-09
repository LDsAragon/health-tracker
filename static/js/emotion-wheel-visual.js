// ── Rueda de emociones — 3 anillos concéntricos ────────────────────────────
// ew-wheel-g → paths que ROTAN
// ew-label-g → textos FIJOS (posición orbita, orientación siempre horizontal)
// Selector (◄) fijo a la derecha (3 en punto, 90°)

let ewState   = { angle: 90, picker: null };
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
            +el.dataset.depth, EMOTION_WHEEL[el.dataset.base].color);
  }
}

// Geometría (viewBox "-180 -180 360 360")
const EW = {
  r0:  30,
  r1i: 32,  r1o: 80,    // base      — label r=56
  r2i: 84,  r2o: 128,   // media     — label r=106
  r3i: 132, r3o: 170,   // específica — label r=151
};
const ACTIVE_DEG = 90; // el sector activo es el que está en 90° (derecha)

// ── Abrir / cerrar ────────────────────────────────────────────────────────

function openEWModal(pickerEl) {
  ewState = { angle: 90, picker: pickerEl };
  buildFullWheel();
  document.getElementById('ew-modal').style.display = 'flex';
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

// ── Teclado ───────────────────────────────────────────────────────────────

function ewKeyHandler(e) {
  if (document.getElementById('ew-modal').style.display === 'none') return;
  if (e.key === 'q' || e.key === 'Q' || e.key === 'ArrowLeft')  { e.preventDefault(); rotateWheel(-1); }
  if (e.key === 'e' || e.key === 'E' || e.key === 'ArrowRight') { e.preventDefault(); rotateWheel(+1); }
  if (e.key === 'Escape') { e.preventDefault(); closeEWModal(); }
}

// ── Rotación — snap de 60° con ease-out cúbico ────────────────────────────

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

  const bases   = Object.keys(EMOTION_WHEEL);
  const top     = topIdx(angle);
  const topBase = bases[top];

  // ── 1. Highlight del sector activo en los paths ───────────────────────
  gWheel.querySelectorAll('[data-base]').forEach(el => {
    el.removeAttribute('transform'); // limpia rotación individual del hover anterior
    const isActive = el.dataset.base === topBase && el.dataset.depth === '1';
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

    // Orientación radial: texto sigue la dirección de su sector
    // Mitad izquierda (worldDeg > 180) se voltea para no quedar al revés
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
  if (cl) { cl.textContent = topBase; cl.style.color = EMOTION_WHEEL[topBase].color; }
}

// Índice del sector más cercano a ACTIVE_DEG (90°, derecha)
function topIdx(angle) {
  let best = 0, bestDist = Infinity;
  for (let i = 0; i < 6; i++) {
    const pos  = ((i * 60 + angle) % 360 + 360) % 360;
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
  const gWheel = document.getElementById('ew-wheel-g');
  let   cloneSrc = null;
  if (gWheel) {
    gWheel.querySelectorAll('[data-base]').forEach(el => {
      const eB = el.dataset.base, eM = el.dataset.mid,
            eS = el.dataset.specific, eD = +el.dataset.depth;

      const inPath = eB === base && (
        eD === 1 ||
        (depth >= 2 && eD === 2 && eM === mid) ||
        (depth >= 3 && eD === 3 && eM === mid && eS === spec)
      );
      const exactMatch = inPath && eD === depth &&
        (depth < 2 || eM === mid) && (depth < 3 || eS === spec);
      const sameBase = eB === base && !inPath;

      if (exactMatch) cloneSrc = el;
      el.style.opacity     = exactMatch ? '0' : inPath ? '1' : sameBase ? '0.5' : '0.08';
      el.style.stroke      = inPath ? 'rgba(255,255,255,0.55)' : 'rgba(0,0,0,0.16)';
      el.style.strokeWidth = inPath ? '1.5'  : strokeW(el.dataset.depth);
      el.style.filter      = inPath ? 'brightness(1.15)' : '';
    });

    // Clon visual del sector exacto — rota hasta 90°, sin pointer events
    const gClone = document.getElementById('ew-hover-clone-g');
    if (gClone && cloneSrc) {
      gClone.innerHTML = '';
      const clone = cloneSrc.cloneNode(true);
      clone.style.pointerEvents = 'none';
      clone.style.opacity       = '1';
      clone.style.filter        = 'brightness(1.12)';
      clone.style.stroke        = 'rgba(255,255,255,0.55)';
      clone.style.strokeWidth   = '1.5';
      gClone.appendChild(clone);
      const initA = parseFloat(cloneSrc.dataset.initAngle);
      _animSectorClone(clone, ewState.angle, 90 - initA);
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
      }
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
  // Vuelve al estado "activo" (sin hover)
  applyAngle(ewState.angle);
  const lbl  = document.getElementById('ew-hover-label');
  const hint = document.getElementById('ew-hover-hint');
  if (lbl)  lbl.innerHTML = '';
  if (hint) hint.textContent = 'Rotá para explorar · hover para leer · click para guardar';
}

// Anima el label desde su rotación radial actual hasta 0° (horizontal)
function _animLabelTo0(el, tx, ty) {
  if (el._animId) { cancelAnimationFrame(el._animId); el._animId = null; }
  const match   = (el.getAttribute('transform') || '').match(/rotate\(([-\d.]+)/);
  const fromRot = match ? parseFloat(match[1]) : 0;
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

// Anima el clon del sector desde fromRot hasta toRot alrededor del centro (0,0)
function _animSectorClone(clone, fromRot, toRot) {
  const delta = toRot - fromRot;
  if (Math.abs(delta) < 0.5) { clone.setAttribute('transform', `rotate(${toRot})`); return; }
  const start = performance.now(), dur = 130;
  function tick(now) {
    const t    = Math.min((now - start) / dur, 1);
    const ease = 1 - Math.pow(1 - t, 3);
    clone.setAttribute('transform', `rotate(${f(fromRot + delta * ease)})`);
    if (t < 1) requestAnimationFrame(tick);
  }
  requestAnimationFrame(tick);
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

  const gWheel = svgG('ew-wheel-g');
  const gClone = svgG('ew-hover-clone-g');
  const gLabel = svgG('ew-label-g');

  const bases = Object.keys(EMOTION_WHEEL);

  bases.forEach((base, bi) => {
    const baseColor = EMOTION_WHEEL[base].color;
    const mids      = Object.keys(EMOTION_WHEEL[base].children);
    const BASE_A    = bi * 60;

    // Anillo 1 — base
    const p1 = sector(EW.r1i, EW.r1o, BASE_A - 30, BASE_A + 30, baseColor, 0.7);
    p1.dataset.base      = base; p1.dataset.depth = '1';
    p1.dataset.initAngle = BASE_A;
    p1.style.cursor      = 'pointer';
    bindSlice(p1, base, null, null, 1, baseColor);
    gWheel.appendChild(p1);
    gLabel.appendChild(makeLabel(base, BASE_A, (EW.r1i+EW.r1o)/2, '8px', '800', base, 1));

    mids.forEach((mid, mi) => {
      const MID  = 60 / mids.length; // 10°
      const midA = BASE_A - 30 + (mi + 0.5) * MID;
      const midColor = tint(baseColor, 0.20 + 0.06 * (mi & 1));

      const p2 = sector(EW.r2i, EW.r2o, BASE_A-30+mi*MID, BASE_A-30+(mi+1)*MID, midColor, 0.45);
      p2.dataset.base      = base; p2.dataset.mid = mid; p2.dataset.depth = '2';
      p2.dataset.initAngle = f(midA);
      p2.style.cursor      = 'pointer';
      bindSlice(p2, base, mid, null, 2, baseColor);
      gWheel.appendChild(p2);
      const lbl2 = makeLabel(mid, midA, (EW.r2i+EW.r2o)/2, '6px', '700', base, 2);
      lbl2.dataset.mid = mid;
      gLabel.appendChild(lbl2);

      const specs = EMOTION_WHEEL[base].children[mid];
      specs.forEach((spec, si) => {
        const SPEC  = MID / 2; // 5°
        const specA = BASE_A - 30 + mi*MID + (si+0.5)*SPEC;
        const specColor = tint(baseColor, 0.36 + 0.08 * (si & 1));

        const p3 = sector(EW.r3i, EW.r3o, BASE_A-30+mi*MID+si*SPEC, BASE_A-30+mi*MID+(si+1)*SPEC, specColor, 0.3);
        p3.dataset.base      = base; p3.dataset.mid = mid;
        p3.dataset.specific  = spec; p3.dataset.depth = '3';
        p3.dataset.initAngle = f(specA);
        p3.style.cursor      = 'pointer';
        bindSlice(p3, base, mid, spec, 3, baseColor);
        gWheel.appendChild(p3);
        const lbl3 = makeLabel(spec, specA, (EW.r3i+EW.r3o)/2, '5.5px', '600', base, 3);
        lbl3.dataset.mid      = mid;
        lbl3.dataset.specific = spec;
        gLabel.appendChild(lbl3);
      });
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
  ptr.style.fill         = 'rgba(255,255,255,0.92)';
  ptr.style.pointerEvents = 'none';
  ptr.style.filter       = 'drop-shadow(-1px 0 4px rgba(0,0,0,0.7))';
  svg.appendChild(ptr);

  applyAngle(ewState.angle);
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
  el.dataset.la   = initAngle;
  el.dataset.lr   = r;
  el.dataset.base = base;
  el.dataset.ring = ring;
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
function svgG(id)   { const g = svgEl('g'); g.id = id; return g; }
function tint(hex, f2) {
  const r = parseInt(hex.slice(1,3), 16), g = parseInt(hex.slice(3,5), 16), b = parseInt(hex.slice(5,7), 16);
  return `rgb(${~~(r+(255-r)*f2)},${~~(g+(255-g)*f2)},${~~(b+(255-b)*f2)})`;
}
function f(n) { return Math.round(n * 1000) / 1000; }
