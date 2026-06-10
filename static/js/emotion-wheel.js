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
  const p   = sel.closest('.emotion-wheel-picker');
  const l2  = p.querySelector('.ew-level2');
  const l3  = p.querySelector('.ew-level3');
  const hid = p.querySelector('[data-ew-value]');
  const base = sel.value;

  l2.innerHTML = '<option value="">Más específico...</option>';
  l3.innerHTML = '<option value="">Aún más específico...</option>';
  l3.style.display = 'none';
  l3.onchange = null;

  if (!base) {
    l2.style.display = 'none';
    hid.value = '';
    sel.style.color = '';
    sel.style.borderColor = '';
    return;
  }
  const cat = EMOTION_WHEEL[base];
  Object.keys(cat.children).forEach(m => l2.add(new Option(m, m)));
  l2.style.display = '';
  hid.value = base;
  _ewColor(sel, cat.color);
  _ewColor(l2, cat.color);
}

function ewL3(sel) {
  const p    = sel.closest('.emotion-wheel-picker');
  const l1   = p.querySelector('.ew-level1');
  const l3   = p.querySelector('.ew-level3');
  const hid  = p.querySelector('[data-ew-value]');
  const base = l1.value;
  const mid  = sel.value;

  l3.innerHTML = '<option value="">Aún más específico...</option>';
  l3.onchange  = null;

  if (!mid) {
    l3.style.display = 'none';
    hid.value = base;
    return;
  }
  const specific = EMOTION_WHEEL[base].children[mid];
  specific.forEach(sp => l3.add(new Option(sp, sp)));
  l3.style.display = '';
  hid.value = base + ' > ' + mid;
  const c = EMOTION_WHEEL[base].color;
  _ewColor(sel, c);
  _ewColor(l3, c);
  l3.onchange = function() {
    hid.value = this.value
      ? base + ' > ' + mid + ' > ' + this.value
      : base + ' > ' + mid;
    _ewColor(this, c);
  };
}

function _ewColor(el, color) {
  el.style.color       = color;
  el.style.borderColor = color;
}

// ── Restaurar valor guardado ────────────────────────────────────────────────

function ewRestore(picker, val) {
  if (!val) return;
  const hid     = picker.querySelector('[data-ew-value]');
  const selects = picker.querySelector('.ew-selects');
  const chip    = picker.querySelector('.ew-ek-chip');

  // Valor de la rueda Ekman: "ek::Ira > Frustración" → chip de solo lectura, sin cascada
  if (val.indexOf('ek::') === 0) {
    const path = val.slice(4);
    if (hid) hid.value = val;
    if (selects) selects.style.display = 'none';
    if (chip) { chip.style.display = ''; chip.textContent = path; chip.dataset.origin = 'ek'; }
    return;
  }
  // Valor de la rueda española (sin prefijo): cascada normal
  if (chip)    chip.style.display = 'none';
  if (selects) selects.style.display = '';

  const parts = val.split(' > ');
  const l1 = picker.querySelector('.ew-level1');
  if (!parts[0] || !EMOTION_WHEEL[parts[0]]) return;
  l1.value = parts[0];
  ewL2(l1);
  if (parts[1]) {
    const l2 = picker.querySelector('.ew-level2');
    l2.value = parts[1];
    ewL3(l2);
    if (parts[2]) {
      const l3  = picker.querySelector('.ew-level3');
      const hid = picker.querySelector('[data-ew-value]');
      l3.value  = parts[2];
      hid.value = parts[0] + ' > ' + parts[1] + ' > ' + parts[2];
      _ewColor(l3, EMOTION_WHEEL[parts[0]].color);
    }
  }
}

// ── Construir picker en formularios dinámicos ──────────────────────────────

function buildEWPicker(label) {
  const esc  = s => s.replace(/"/g, '&quot;');
  const opts = Object.keys(EMOTION_WHEEL)
    .map(e => `<option value="${e}">${e}</option>`).join('');
  return `<div class="day-journal-field-input">
    <label>${label}</label>
    <div class="emotion-wheel-picker" data-label="${esc(label)}">
      <div class="ew-open-btns">
        <button type="button" class="ew-open-btn"
                onclick="openEWModal(this.closest('.emotion-wheel-picker'),'es')">🎯 Rueda Willcox</button>
        <button type="button" class="ew-open-btn ew-open-btn-ek"
                onclick="openEWModal(this.closest('.emotion-wheel-picker'),'ek')">🧭 Rueda Ekman</button>
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
      </div>
      <div class="ew-ek-chip" style="display:none;"></div>
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
    <div class="ew-open-btns">
      <button type="button" class="ew-open-btn"
              onclick="openEWModal(this.closest('.emotion-wheel-picker'),'es')">🎯 Willcox</button>
      <button type="button" class="ew-open-btn ew-open-btn-ek"
              onclick="openEWModal(this.closest('.emotion-wheel-picker'),'ek')">🧭 Ekman</button>
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
    <div class="ew-ek-chip" style="display:none;"></div>
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
