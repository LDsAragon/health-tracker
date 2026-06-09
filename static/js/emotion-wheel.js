// Rueda de emociones — 6 emociones base, 6 medias cada una, 2 específicas cada media
const EMOTION_WHEEL = {
  "Ira": {
    color: "#ef4444",
    children: {
      "Odioso":      ["Resentido",    "Violado"],
      "Amenazado":   ["Celoso",       "Inseguro"],
      "Desquiciado": ["Enfurecido",   "Rabioso"],
      "Agresivo":    ["Provocado",    "Hostil"],
      "Frustrado":   ["Enfadado",     "Irritado"],
      "Distante":    ["Retraído",     "Sospechoso"]
    }
  },
  "Disgusto": {
    color: "#f97316",
    children: {
      "Crítico":      ["Sarcástico",   "Escéptico"],
      "Desaprobado":  ["Sentencioso",  "Aborrecido"],
      "Decepcionado": ["Repugnante",   "Rebelado"],
      "Terrible":     ["Repulsivo",    "Detestable"],
      "Evasivo":      ["Aversivo",     "Indeciso"],
      "Culpable":     ["Atormentado",  "Avergonzado"]
    }
  },
  "Tristeza": {
    color: "#84cc16",
    children: {
      "Ansioso":     ["Anhelante",    "Abrumado"],
      "Abandonado":  ["Ignorado",     "Discriminado"],
      "Desesperado": ["Impotente",    "Vulnerable"],
      "Deprimido":   ["Inferior",     "Vacío"],
      "Solitario":   ["Abandonado",   "Apartado"],
      "Aburrido":    ["Apático",      "Indiferente"]
    }
  },
  "Felicidad": {
    color: "#eab308",
    children: {
      "Optimista": ["Inspirado",    "Receptivo"],
      "Íntimo":    ["Juguetón",     "Sensible"],
      "Pacífico":  ["Esperanzado",  "Amoroso"],
      "Poderoso":  ["Provocativo",  "Valiente"],
      "Aceptado":  ["Realizado",    "Respetado"],
      "Orgulloso": ["Confiado",     "Importante"]
    }
  },
  "Sorpresa": {
    color: "#3b82f6",
    children: {
      "Jubiloso":    ["Liberado",     "Eufórico"],
      "Efusivo":     ["Enérgico",     "Inquieto"],
      "Asombrado":   ["Pasmado",      "Atónito"],
      "Confundido":  ["Perplejo",     "Desilusionado"],
      "Sorprendido": ["Consternado",  "Impresionado"],
      "Interesado":  ["Curioso",      "Entretenido"]
    }
  },
  "Miedo": {
    color: "#a855f7",
    children: {
      "Inseguro":  ["Devastado",    "Apenado"],
      "Asustado":  ["Aterrado",     "Espantado"],
      "Sumiso":    ["Pobre",        "Inferior"],
      "Rechazado": ["Indignado",    "Insignificante"],
      "Humillado": ["Inadecuado",   "Perturbado"],
      "Herido":    ["Irrespetado",  "Ridiculizado"]
    }
  },

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
    <select class="ew-select ew-level1" onchange="ewL2(this)">
      <option value="">Emoción base...</option>${opts}
    </select>
    <select class="ew-select ew-level2" style="display:none;" onchange="ewL3(this)">
      <option value="">Más específico...</option>
    </select>
    <select class="ew-select ew-level3" style="display:none;">
      <option value="">Aún más específico...</option>
    </select>
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
