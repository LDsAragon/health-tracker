// Rueda de emociones — Feeling Wheel de Gloria Willcox (1982), traducida al español.
// 6 centros (adjetivos) × 6 secundarias × 1 terciaria. Misma forma {base:{color,children:{sec:[terc]}}}.
// La versión vieja (Junto, mal traducida) quedó archivada en emotion-wheel-old.js.
// ⚠️ Traducciones BORRADOR — a verificar/afinar contra la imagen fuente.
const EMOTION_WHEEL = {
  "Enojado": {        // Mad
    color: "#e8643c",
    children: {
      "Herido":    ["Celoso"],      // Hurt → Jealous
      "Hostil":    ["Egoísta"],     // Hostile → Selfish
      "Enfadado":  ["Frustrado"],   // Angry → Frustrated
      "Rabioso":   ["Furioso"],     // Rage → Furious
      "Rencoroso": ["Irritado"],    // Hateful → Irritated
      "Crítico":   ["Escéptico"]    // Critical → Skeptical
    }
  },
  "Asustado": {       // Scared
    color: "#8e7cc3",
    children: {
      "Confundido": ["Desconcertado"],  // Confused → Bewildered
      "Rechazado":  ["Desanimado"],     // Rejected → Discouraged
      "Indefenso":  ["Insignificante"], // Helpless → Insignificant
      "Sumiso":     ["Débil"],          // Submissive → Weak
      "Inseguro":   ["Ridículo"],       // Insecure → Foolish
      "Ansioso":    ["Apenado"]         // Anxious → Embarrassed
    }
  },
  "Alegre": {         // Joyful
    color: "#e79ab0",
    children: {
      "Entusiasmado": ["Atrevido"],     // Excited → Daring
      "Sensual":      ["Fascinado"],    // Sexy → Fascinating
      "Enérgico":     ["Estimulado"],   // Energetic → Stimulating
      "Juguetón":     ["Divertido"],    // Playful → Amused
      "Creativo":     ["Extravagante"], // Creative → Extravagant
      "Consciente":   ["Encantado"]     // Aware → Delightful
    }
  },
  "Poderoso": {       // Powerful
    color: "#e8b93f",
    children: {
      "Fiel":        ["Seguro"],        // Faithful → Confident
      "Importante":  ["Inteligente"],   // Important → Intelligent
      "Esperanzado": ["Digno"],         // Hopeful → Worthwhile
      "Apreciado":   ["Valioso"],       // Appreciated → Valuable
      "Respetado":   ["Satisfecho"],    // Respected → Satisfied
      "Orgulloso":   ["Animado"]        // Proud → Cheerful
    }
  },
  "Apacible": {       // Peaceful
    color: "#6cab6c",
    children: {
      "Conforme":    ["Pensativo"],     // Content → Pensive
      "Considerado": ["Relajado"],      // Thoughtful → Relaxed
      "Íntimo":      ["Receptivo"],     // Intimate → Responsive
      "Amoroso":     ["Sereno"],        // Loving → Serene
      "Confiado":    ["Sentimental"],   // Trusting → Sentimental
      "Protector":   ["Agradecido"]     // Nurturing → Thankful
    }
  },
  "Triste": {         // Sad
    color: "#5b8fc7",
    children: {
      "Adormecido":  ["Apático"],       // Sleepy → Apathetic
      "Aburrido":    ["Inferior"],      // Bored → Inferior
      "Solo":        ["Inadecuado"],    // Lonely → Inadequate
      "Deprimido":   ["Miserable"],     // Depressed → Miserable
      "Avergonzado": ["Tonto"],         // Ashamed → Stupid
      "Culpable":    ["Tímido"]         // Guilty → Bashful
    }
  }
};

// ── Handlers de cascada ────────────────────────────────────────────────────

function ewL2(sel) {
  const p      = sel.closest('.emotion-wheel-picker');
  const l2     = p.querySelector('.ew-level2');
  const l3     = p.querySelector('.ew-level3');
  const addBtn = p.querySelector('.ew-cascade-add');
  const base   = sel.value;

  l2.innerHTML = '<option value="">Más específico...</option>';
  l3.innerHTML = '<option value="">Aún más específico...</option>';
  l3.style.display = 'none';
  l3.onchange = null;

  if (!base) {
    l2.style.display = 'none';
    delete p.dataset.ewPending;
    if (addBtn) addBtn.style.display = 'none';
    sel.style.color = '';
    sel.style.borderColor = '';
    return;
  }
  const cat = EMOTION_WHEEL[base];
  Object.keys(cat.children).forEach(m => l2.add(new Option(m, m)));
  l2.style.display = '';
  p.dataset.ewPending = base;
  if (addBtn) addBtn.style.display = '';
  _ewColor(sel, cat.color);
  _ewColor(l2, cat.color);
}

function ewL3(sel) {
  const p    = sel.closest('.emotion-wheel-picker');
  const l1   = p.querySelector('.ew-level1');
  const l3   = p.querySelector('.ew-level3');
  const base = l1.value;
  const mid  = sel.value;

  l3.innerHTML = '<option value="">Aún más específico...</option>';
  l3.onchange  = null;

  if (!mid) {
    l3.style.display = 'none';
    p.dataset.ewPending = base;
    return;
  }
  const specific = EMOTION_WHEEL[base].children[mid];
  specific.forEach(sp => l3.add(new Option(sp, sp)));
  l3.style.display = '';
  p.dataset.ewPending = base + ' > ' + mid;
  const c = EMOTION_WHEEL[base].color;
  _ewColor(sel, c);
  _ewColor(l3, c);
  l3.onchange = function() {
    p.dataset.ewPending = this.value
      ? base + ' > ' + mid + ' > ' + this.value
      : base + ' > ' + mid;
    _ewColor(this, c);
  };
}

function _ewColor(el, color) {
  el.style.color       = color;
  el.style.borderColor = color;
}

// ── Gestión multi-valor ─────────────────────────────────────────────────────

function ewGetValues(picker) {
  const hid = picker.querySelector('[data-ew-value]');
  const raw = hid ? hid.value.trim() : '';
  return raw ? raw.split(' | ').filter(Boolean) : [];
}

function ewSetValues(picker, vals) {
  const hid = picker.querySelector('[data-ew-value]');
  if (hid) hid.value = vals.join(' | ');
  ewRenderChips(picker, vals);
}

function ewAddValue(picker, val) {
  if (!val) return;
  const vals = ewGetValues(picker);
  if (!vals.includes(val)) vals.push(val);
  ewSetValues(picker, vals);
}

function ewRenderChips(picker, vals) {
  const cont = picker.querySelector('.ew-chips');
  if (!cont) return;
  cont.innerHTML = vals.map((v, i) => {
    const isEk  = v.startsWith('ek::');
    const clean = isEk ? v.slice(4) : v;
    const col   = _ewValColor(v);
    const label = clean.replace(/ > /g, ' › ');
    const badge = isEk ? ' <span class="ew-chip-src">Ekman</span>' : '';
    return `<span class="ew-chip-item" style="--c:${col};" data-ew-idx="${i}">` +
           `<span>${label}${badge}</span>` +
           `<button type="button" class="ew-chip-x" onclick="ewRemoveChipAt(this)">×</button></span>`;
  }).join('');
}

function _ewValColor(val) {
  const isEk  = val.startsWith('ek::');
  const base0 = (isEk ? val.slice(4) : val).split(' > ')[0];
  if (isEk) {
    const EK_COLORS = { 'Ira':'#e2403b','Miedo':'#7c5cbf','Tristeza':'#3b6fb5',
                        'Asco':'#4f9d69','Disfrute':'#e6b53c','Felicidad':'#e6b53c','Sorpresa':'#8e7cc3' };
    return EK_COLORS[base0] || '#8892a4';
  }
  return (EMOTION_WHEEL[base0] && EMOTION_WHEEL[base0].color) || '#8892a4';
}

function ewRemoveChipAt(btn) {
  const picker = btn.closest('.emotion-wheel-picker');
  const chip   = btn.closest('.ew-chip-item');
  const idx    = parseInt(chip.dataset.ewIdx, 10);
  const vals   = ewGetValues(picker);
  vals.splice(idx, 1);
  ewSetValues(picker, vals);
}

function ewCascadeAdd(picker) {
  const val = picker.dataset.ewPending;
  if (!val) return;
  ewAddValue(picker, val);
  _ewCascadeReset(picker);
}

function _ewCascadeReset(picker) {
  const l1 = picker.querySelector('.ew-level1');
  const l2 = picker.querySelector('.ew-level2');
  const l3 = picker.querySelector('.ew-level3');
  const addBtn = picker.querySelector('.ew-cascade-add');
  if (l1) { l1.value = ''; l1.style.color = ''; l1.style.borderColor = ''; }
  if (l2) { l2.innerHTML = '<option value="">Más específico...</option>'; l2.style.display = 'none'; l2.style.color = ''; l2.style.borderColor = ''; }
  if (l3) { l3.innerHTML = '<option value="">Aún más específico...</option>'; l3.style.display = 'none'; l3.style.color = ''; l3.style.borderColor = ''; l3.onchange = null; }
  if (addBtn) addBtn.style.display = 'none';
  delete picker.dataset.ewPending;
}

// ── Restaurar valor guardado ────────────────────────────────────────────────

function ewRestore(picker, val) {
  if (!val) return;
  const vals = val.split(' | ').filter(Boolean);
  ewSetValues(picker, vals);
}

// ── Construir picker en formularios dinámicos ──────────────────────────────

function buildEWPicker(label) {
  const esc  = s => s.replace(/"/g, '&quot;');
  const opts = Object.keys(EMOTION_WHEEL)
    .map(e => `<option value="${e}">${e}</option>`).join('');
  return `<div class="day-journal-field-input">
    <label>${label}</label>
    <div class="emotion-wheel-picker" data-label="${esc(label)}">
      <div class="ew-chips"></div>
      <div class="ew-open-btns">
        <button type="button" class="ew-open-btn"
                onclick="openEWModal(this.closest('.emotion-wheel-picker'),'es')">🎯 Rueda Willcox</button>
        <button type="button" class="ew-open-btn ew-open-btn-ek"
                onclick="openEWModal(this.closest('.emotion-wheel-picker'),'ek')">🧭 Rueda Ekman</button>
        <button type="button" class="ew-open-btn ew-open-btn-guided"
                onclick="openEWModal(this.closest('.emotion-wheel-picker'),'guided')">🌿 Exploración guiada</button>
      </div>
      <div class="ew-selects">
        <select class="ew-select ew-level1" onchange="ewL2(this)">
          <option value="">Emoción base...</option>${opts}
        </select>
        <select class="ew-select ew-level2" style="display:none;" onchange="ewL3(this)">
          <option value="">Más específico...</option>
        </select>
        <select class="ew-select ew-level3" style="display:none;">
          <option value="">Aún más específico...</option>
        </select>
        <button type="button" class="ew-cascade-add" style="display:none;"
                onclick="ewCascadeAdd(this.closest('.emotion-wheel-picker'))">+ Agregar emoción</button>
      </div>
      <input type="hidden" data-ew-value="">
    </div>
  </div>`;
}

// Versión compacta para celdas del calendario
function buildEWPickerCompact(label) {
  const esc  = s => s.replace(/"/g, '&quot;');
  const opts = Object.keys(EMOTION_WHEEL)
    .map(e => `<option value="${e}">${e}</option>`).join('');
  return `<div class="emotion-wheel-picker ew-compact" data-label="${esc(label)}">
    <div class="ew-chips"></div>
    <div class="ew-open-btns">
      <button type="button" class="ew-open-btn"
              onclick="openEWModal(this.closest('.emotion-wheel-picker'),'es')">🎯 Willcox</button>
      <button type="button" class="ew-open-btn ew-open-btn-ek"
              onclick="openEWModal(this.closest('.emotion-wheel-picker'),'ek')">🧭 Ekman</button>
      <button type="button" class="ew-open-btn ew-open-btn-guided"
              onclick="openEWModal(this.closest('.emotion-wheel-picker'),'guided')">🌿 Guiada</button>
    </div>
    <select class="ew-select ew-level1" onchange="ewL2(this)">
      <option value="">Emoción base...</option>${opts}
    </select>
    <select class="ew-select ew-level2" style="display:none;" onchange="ewL3(this)">
      <option value="">Más específico...</option>
    </select>
    <select class="ew-select ew-level3" style="display:none;">
      <option value="">Aún más específico...</option>
    </select>
    <button type="button" class="ew-cascade-add" style="display:none;"
            onclick="ewCascadeAdd(this.closest('.emotion-wheel-picker'))">+ Agregar emoción</button>
    <input type="hidden" data-ew-value="">
  </div>`;
}

// ── Recolectar valores de pickers en un contenedor ─────────────────────────

function collectEWValues(container, values) {
  container.querySelectorAll('.emotion-wheel-picker').forEach(picker => {
    const label = picker.dataset.label;
    const hid   = picker.querySelector('[data-ew-value]');
    if (hid && hid.value) values[label] = hid.value;
  });
}
