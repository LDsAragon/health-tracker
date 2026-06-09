// ── Rueda de emociones — modal SVG giratorio ───────────────────────────────

let ewState = { level: 1, base: null, mid: null, angle: 0, picker: null };
let ewEmotions = [];
let ewColors   = [];

// ── Abrir / cerrar modal ───────────────────────────────────────────────────

function openEWModal(pickerEl) {
  ewState = { level: 1, base: null, mid: null, angle: 0, picker: pickerEl };
  const bases = Object.keys(EMOTION_WHEEL);
  ewEmotions = bases;
  ewColors   = bases.map(b => EMOTION_WHEEL[b].color);
  buildWheelStructure();
  updateBreadcrumb();
  document.getElementById('ew-modal').style.display = 'flex';
  document.addEventListener('keydown', ewKeyHandler);
}

function closeEWModal() {
  document.getElementById('ew-modal').style.display = 'none';
  document.removeEventListener('keydown', ewKeyHandler);
  ewState = { level: 1, base: null, mid: null, angle: 0, picker: null };
}

function ewOverlayClick(e) {
  if (e.target === document.getElementById('ew-modal')) closeEWModal();
}

// ── Teclado ────────────────────────────────────────────────────────────────

function ewKeyHandler(e) {
  if (document.getElementById('ew-modal').style.display === 'none') return;
  if (e.key === 'q' || e.key === 'Q' || e.key === 'ArrowLeft')  { e.preventDefault(); rotateWheel(-1); }
  if (e.key === 'e' || e.key === 'E' || e.key === 'ArrowRight') { e.preventDefault(); rotateWheel(+1); }
  if (e.key === 'Enter')     { e.preventDefault(); selectTopEmotion(); }
  if (e.key === 'Escape')    { e.preventDefault(); closeEWModal(); }
  if (e.key === 'Backspace') { e.preventDefault(); ewBack(); }
}

// ── Rotación ───────────────────────────────────────────────────────────────

function rotateWheel(dir) {
  const step = 360 / ewEmotions.length;
  const from = ewState.angle;
  const to   = from + dir * step;
  ewState.angle = to;
  animateWheelTo(from, to);
}

let _ewAnimId = null;

function animateWheelTo(from, to) {
  if (_ewAnimId) cancelAnimationFrame(_ewAnimId);
  const start = performance.now();
  const duration = 200;
  function frame(now) {
    const t = Math.min((now - start) / duration, 1);
    const ease = t < 0.5 ? 2*t*t : -1 + (4 - 2*t)*t;
    applyWheelAngle(from + (to - from) * ease);
    if (t < 1) _ewAnimId = requestAnimationFrame(frame);
    else _ewAnimId = null;
  }
  _ewAnimId = requestAnimationFrame(frame);
}

function applyWheelAngle(angle) {
  const g = document.getElementById('ew-wheel-g');
  if (!g) return;
  const N    = ewEmotions.length;
  const step = 360 / N;

  g.setAttribute('transform', `rotate(${angle})`);

  const topIdx = calcTopIndex(angle, N);
  g.querySelectorAll('.ew-slice').forEach((p, i) => {
    if (i === topIdx) {
      p.style.opacity     = '1';
      p.style.stroke      = 'rgba(255,255,255,0.85)';
      p.style.strokeWidth = '2.5';
      p.style.filter      = 'brightness(1.2)';
    } else {
      p.style.opacity     = '0.65';
      p.style.stroke      = 'rgba(0,0,0,0.3)';
      p.style.strokeWidth = '1';
      p.style.filter      = '';
    }
  });

  g.querySelectorAll('[data-slice-text]').forEach(t => {
    const i  = parseInt(t.dataset.sliceText);
    const tx = parseFloat(t.getAttribute('x'));
    const ty = parseFloat(t.getAttribute('y'));
    t.setAttribute('transform', `rotate(${-angle},${tx},${ty})`);
  });

  document.getElementById('ew-current-label').textContent =
    ewEmotions[topIdx] || '';
}

function calcTopIndex(angle, N) {
  const step = 360 / N;
  let best = 0, bestDist = Infinity;
  for (let i = 0; i < N; i++) {
    const pos  = ((i * step + angle) % 360 + 360) % 360;
    const dist = Math.min(pos, 360 - pos);
    if (dist < bestDist) { bestDist = dist; best = i; }
  }
  return best;
}

function getTopIndex() {
  return calcTopIndex(ewState.angle, ewEmotions.length);
}

// ── Selección ──────────────────────────────────────────────────────────────

function selectTopEmotion() {
  const emotion = ewEmotions[getTopIndex()];
  if (ewState.level === 3) finalizeSelection(emotion);
  else advanceLevel(emotion);
}

function handleSliceClick(i, emotion) {
  const step = 360 / ewEmotions.length;
  const from = ewState.angle;
  const to   = -i * step;
  ewState.angle = to;
  animateWheelTo(from, to);
  setTimeout(() => {
    if (ewState.level === 3) finalizeSelection(emotion);
    else advanceLevel(emotion);
  }, 230);
}

function advanceLevel(emotion) {
  if (ewState.level === 1) {
    ewState.base  = emotion;
    ewState.level = 2;
    const mids = Object.keys(EMOTION_WHEEL[emotion].children);
    ewEmotions = mids;
    ewColors   = mids.map(() => EMOTION_WHEEL[emotion].color);
  } else {
    ewState.mid   = emotion;
    ewState.level = 3;
    const specs = EMOTION_WHEEL[ewState.base].children[emotion];
    ewEmotions = specs;
    ewColors   = specs.map(() => EMOTION_WHEEL[ewState.base].color);
  }
  ewState.angle = 0;
  buildWheelStructure();
  updateBreadcrumb();
}

function ewBack() {
  if (ewState.level === 1) { closeEWModal(); return; }
  if (ewState.level === 2) {
    ewState.level = 1; ewState.base = null;
    const bases = Object.keys(EMOTION_WHEEL);
    ewEmotions = bases;
    ewColors   = bases.map(b => EMOTION_WHEEL[b].color);
  } else {
    ewState.level = 2; ewState.mid = null;
    const mids = Object.keys(EMOTION_WHEEL[ewState.base].children);
    ewEmotions = mids;
    ewColors   = mids.map(() => EMOTION_WHEEL[ewState.base].color);
  }
  ewState.angle = 0;
  buildWheelStructure();
  updateBreadcrumb();
}

function finalizeSelection(emotion) {
  const val = ewState.base + ' > ' + ewState.mid + ' > ' + emotion;
  ewRestore(ewState.picker, val);
  closeEWModal();
}

// ── Construir SVG ──────────────────────────────────────────────────────────

function buildWheelStructure() {
  const svg = document.getElementById('ew-svg');
  svg.innerHTML = '';

  const N      = ewEmotions.length;
  const step   = 360 / N;
  const R      = 100, ri = 26;
  const rLabel = (R + ri) / 2;

  const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
  g.id = 'ew-wheel-g';

  for (let i = 0; i < N; i++) {
    const a1   = (i - 0.5) * step;
    const a2   = (i + 0.5) * step;
    const path = makeSlicePath(R, ri, a1, a2, ewColors[i]);
    path.classList.add('ew-slice');
    const em   = ewEmotions[i];
    path.addEventListener('click', () => handleSliceClick(i, em));
    path.style.cursor = 'pointer';
    g.appendChild(path);

    const rad = i * step * Math.PI / 180;
    const tx  = rLabel * Math.sin(rad);
    const ty  = -rLabel * Math.cos(rad);
    g.appendChild(makeSvgLabel(em, tx, ty, N, i));
  }

  const center = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
  center.setAttribute('cx', 0); center.setAttribute('cy', 0);
  center.setAttribute('r', ri - 1);
  center.style.fill         = 'var(--surface2)';
  center.style.stroke       = 'var(--border)';
  center.style.strokeWidth  = '1';
  center.style.pointerEvents = 'none';
  g.appendChild(center);

  svg.appendChild(g);
  applyWheelAngle(0);
}

function makeSlicePath(R, ri, a1deg, a2deg, color) {
  const a1   = a1deg * Math.PI / 180;
  const a2   = a2deg * Math.PI / 180;
  const large = (a2deg - a1deg > 180) ? 1 : 0;
  const ox1 = R * Math.sin(a1),  oy1 = -R * Math.cos(a1);
  const ox2 = R * Math.sin(a2),  oy2 = -R * Math.cos(a2);
  const ix1 = ri * Math.sin(a1), iy1 = -ri * Math.cos(a1);
  const ix2 = ri * Math.sin(a2), iy2 = -ri * Math.cos(a2);

  const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
  path.setAttribute('d',
    `M${f(ox1)} ${f(oy1)} A${R} ${R} 0 ${large} 1 ${f(ox2)} ${f(oy2)} ` +
    `L${f(ix2)} ${f(iy2)} A${ri} ${ri} 0 ${large} 0 ${f(ix1)} ${f(iy1)}Z`
  );
  path.style.fill        = color;
  path.style.stroke      = 'rgba(0,0,0,0.3)';
  path.style.strokeWidth = '1';
  return path;
}

function makeSvgLabel(label, tx, ty, N, idx) {
  const text = document.createElementNS('http://www.w3.org/2000/svg', 'text');
  text.setAttribute('x', f(tx));
  text.setAttribute('y', f(ty));
  text.setAttribute('text-anchor', 'middle');
  text.setAttribute('dominant-baseline', 'middle');
  text.dataset.sliceText = idx;
  text.style.fontSize    = N <= 2 ? '13px' : '9px';
  text.style.fill        = '#fff';
  text.style.fontWeight  = '700';
  text.style.pointerEvents = 'none';
  text.style.userSelect  = 'none';

  const words = label.split(' ');
  if (words.length > 1 && N > 2) {
    const t1 = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
    t1.setAttribute('x', f(tx)); t1.setAttribute('dy', '-0.55em');
    t1.textContent = words[0];
    text.appendChild(t1);
    const t2 = document.createElementNS('http://www.w3.org/2000/svg', 'tspan');
    t2.setAttribute('x', f(tx)); t2.setAttribute('dy', '1.1em');
    t2.textContent = words.slice(1).join(' ');
    text.appendChild(t2);
  } else {
    text.textContent = label;
  }
  return text;
}

function f(n) { return Math.round(n * 100) / 100; }

// ── Breadcrumb ─────────────────────────────────────────────────────────────

function updateBreadcrumb() {
  const bc = document.getElementById('ew-breadcrumb');
  if (ewState.level === 1) bc.textContent = '';
  else if (ewState.level === 2) bc.textContent = ewState.base + ' ›';
  else bc.textContent = ewState.base + ' › ' + ewState.mid + ' ›';
}
