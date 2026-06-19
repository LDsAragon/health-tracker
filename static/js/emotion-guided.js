// Exploración guiada — árbol de decisión para identificar emociones paso a paso.
// Se renderiza en #ew-guided dentro del modal de la rueda.

const EG_TREE = {
  s1: {
    q: '¿Cómo describirías lo que sentís en general?',
    opts: [
      { t: '🌟 Algo se siente bien',    n: 's2a' },
      { t: '⚡ Algo se siente mal',     n: 's2b' },
      { t: '🌫️ No sé / es confuso',    n: 's2c' }
    ]
  },
  s2a: {
    q: '¿Qué tipo de bienestar es?',
    opts: [
      { t: '⚡ Energía, euforia, entusiasmo', r: [
        { name:'Entusiasmado', desc:'Ganas de hacer, energía desbordante',     val:'Alegre > Entusiasmado' },
        { name:'Enérgico',     desc:'Activo y con fuerza para moverse',        val:'Alegre > Enérgico' },
        { name:'Juguetón',     desc:'Levedad, ganas de reírse y experimentar', val:'Alegre > Juguetón' },
        { name:'Creativo',     desc:'Flujo de ideas, impulso de crear',         val:'Alegre > Creativo' },
        { name:'Orgulloso',    desc:'Satisfacción profunda por algo logrado',   val:'Poderoso > Orgulloso' },
      ]},
      { t: '🌊 Calma, paz, serenidad', r: [
        { name:'Conforme',    desc:'Satisfecho con cómo están las cosas',     val:'Apacible > Conforme' },
        { name:'Amoroso',     desc:'Ternura y afecto hacia alguien o algo',    val:'Apacible > Amoroso' },
        { name:'Confiado',    desc:'Seguridad en uno mismo o en el entorno',   val:'Apacible > Confiado' },
        { name:'Agradecido',  desc:'Reconocimiento de algo bueno recibido',    val:'Apacible > Protector > Agradecido' },
        { name:'Sereno',      desc:'Quietud profunda, sin tensión',             val:'Apacible > Amoroso > Sereno' },
      ]},
      { t: '💪 Me siento capaz, valioso o respetado', r: [
        { name:'Respetado',   desc:'Reconocimiento genuino por parte de otros',val:'Poderoso > Respetado' },
        { name:'Importante',  desc:'Lo que hacés tiene peso para alguien',     val:'Poderoso > Importante' },
        { name:'Esperanzado', desc:'Confianza en que las cosas van a mejorar', val:'Poderoso > Esperanzado' },
        { name:'Apreciado',   desc:'Sentido de ser valorado por los demás',    val:'Poderoso > Apreciado' },
        { name:'Orgulloso',   desc:'Logro reconocido, propio o por otros',     val:'Poderoso > Orgulloso' },
      ]}
    ]
  },
  s2b: {
    q: '¿Qué tipo de malestar sentís?',
    opts: [
      { t: '⚠️ Tensión, amenaza, miedo',        n: 's3_miedo' },
      { t: '🔥 Enojo, injusticia, frustración',  n: 's3_enojo' },
      { t: '🪨 Pesadez, vacío, pérdida',         n: 's3_tristeza' },
      { t: '🚫 Repulsión o rechazo', r: [
        { name:'Crítico',   desc:'Juicio negativo fuerte hacia algo o alguien', val:'Enojado > Crítico' },
        { name:'Hostil',    desc:'Actitud de rechazo activo hacia el entorno',  val:'Enojado > Hostil' },
        { name:'Rencoroso', desc:'Enojo acumulado que no encontró salida',      val:'Enojado > Rencoroso' },
        { name:'Rechazado', desc:'Sentirse excluido o no bienvenido',            val:'Asustado > Rechazado' },
      ]}
    ]
  },
  s2c: {
    q: '¿Qué sentís en el cuerpo en este momento?',
    opts: [
      { t: '🔥 Tensión, calor, mandíbula apretada',    n: 's2b' },
      { t: '🦋 Mariposas, agitación, inquietud',       n: 's3_miedo' },
      { t: '🪨 Pesadez, cansancio, lentitud', r: [
        { name:'Adormecido', desc:'Como anestesiado emocionalmente',         val:'Triste > Adormecido' },
        { name:'Aburrido',   desc:'Todo parece plano o sin sentido',          val:'Triste > Aburrido' },
        { name:'Solo',       desc:'Desconectado, sin energía para conectar',  val:'Triste > Solo' },
      ]},
      { t: '💭 No siento nada en particular', r: [
        { name:'Conforme',  desc:'Tranquilo, neutro, sin tensión',            val:'Apacible > Conforme' },
        { name:'Pensativo', desc:'Procesando algo internamente',               val:'Apacible > Conforme > Pensativo' },
        { name:'Receptivo', desc:'Abierto y presente, sin emoción fuerte',    val:'Apacible > Íntimo > Receptivo' },
      ]}
    ]
  },
  s3_miedo: {
    q: '¿Qué tan intensa es esa sensación de amenaza?',
    opts: [
      { t: '🟡 Leve — algo me preocupa o incomoda', r: [
        { name:'Ansioso',    desc:'Preocupación anticipatoria, mente agitada',  val:'Asustado > Ansioso' },
        { name:'Inseguro',   desc:'Duda sobre uno mismo o sobre la situación',   val:'Asustado > Inseguro' },
        { name:'Confundido', desc:'No sé cómo leer lo que está pasando',         val:'Asustado > Confundido' },
        { name:'Nervioso',   desc:'Agitación ante algo incierto o próximo',      val:'Asustado > Ansioso' },
      ]},
      { t: '🔴 Fuerte — siento que no puedo con esto', r: [
        { name:'Indefenso',  desc:'Sin recursos para enfrentar la situación',    val:'Asustado > Indefenso' },
        { name:'Sumiso',     desc:'Resignación ante algo que parece inevitable', val:'Asustado > Sumiso' },
        { name:'Rechazado',  desc:'Excluido y sin apoyo para atravesar esto',    val:'Asustado > Rechazado' },
        { name:'Agobiado',   desc:'El peso de todo junto desborda la capacidad', val:'Asustado > Indefenso' },
      ]}
    ]
  },
  s3_enojo: {
    q: '¿Qué tipo de enojo es?',
    opts: [
      { t: '💔 Me lastimaron o traicionaron', r: [
        { name:'Herido',    desc:'Dolor por algo que alguien hizo o dijo',    val:'Enojado > Herido' },
        { name:'Rencoroso', desc:'El dolor se convirtió en enojo guardado',   val:'Enojado > Rencoroso' },
        { name:'Inseguro',  desc:'Dificultad para confiar tras una traición',  val:'Asustado > Inseguro' },
      ]},
      { t: '⚖️ Algo fue injusto o no sale como quiero', r: [
        { name:'Enfadado',  desc:'Reacción ante algo que no debería pasar',   val:'Enojado > Enfadado' },
        { name:'Frustrado', desc:'Esfuerzo sin resultado, obstáculo',          val:'Enojado > Enfadado' },
        { name:'Crítico',   desc:'Juicio fuerte hacia la situación',           val:'Enojado > Crítico' },
        { name:'Hostil',    desc:'Rechazo activo hacia quien provocó esto',    val:'Enojado > Hostil' },
      ]},
      { t: '🌋 Estoy muy furioso', r: [
        { name:'Rabioso',   desc:'Enojo intenso que desborda',                 val:'Enojado > Rabioso' },
        { name:'Hostil',    desc:'Actitud agresiva hacia el entorno',          val:'Enojado > Hostil' },
        { name:'Rencoroso', desc:'Furia que quedó atrapada adentro',           val:'Enojado > Rencoroso' },
      ]}
    ]
  },
  s3_tristeza: {
    q: '¿Qué tipo de pesadez sentís?',
    opts: [
      { t: '🏝️ Me siento solo o desconectado', r: [
        { name:'Solo',       desc:'Ausencia de conexión genuina con otros',     val:'Triste > Solo' },
        { name:'Adormecido', desc:'Como si las emociones estuvieran apagadas',  val:'Triste > Adormecido' },
        { name:'Rechazado',  desc:'Sensación de no encajar o no ser bienvenido',val:'Asustado > Rechazado' },
        { name:'Aburrido',   desc:'Todo parece plano y sin sentido',             val:'Triste > Aburrido' },
      ]},
      { t: '😔 Me siento culpable o avergonzado', r: [
        { name:'Culpable',    desc:'Responsabilidad por algo que salió mal',    val:'Triste > Culpable' },
        { name:'Avergonzado', desc:'Sensación de no estar a la altura',          val:'Triste > Avergonzado' },
        { name:'Indefenso',   desc:'No pude evitarlo y eso pesa',               val:'Asustado > Indefenso' },
      ]},
      { t: '💧 Pérdida, duelo, desesperanza', r: [
        { name:'Deprimido',   desc:'Tristeza profunda y sostenida',              val:'Triste > Deprimido' },
        { name:'Solo',        desc:'Vacío que no se llena con nada',             val:'Triste > Solo' },
        { name:'Adormecido',  desc:'Como en piloto automático',                  val:'Triste > Adormecido' },
        { name:'Avergonzado', desc:'Sensación de no poder con lo que pasa',     val:'Triste > Avergonzado' },
      ]}
    ]
  }
};

let _egHistory = [];
let _egPicker  = null;

function ewGuidedOpen(picker) {
  _egPicker  = picker;
  _egHistory = [];
  _egRender('s1');
}

function _egRender(stepId, push) {
  if (push !== false) _egHistory.push(stepId);
  const panel = document.getElementById('ew-guided');
  if (!panel) return;
  const step = EG_TREE[stepId];
  if (!step) return;

  let html = '<div class="eg-step">';
  html += '<p class="eg-question">' + _egEsc(step.q) + '</p>';
  html += '<div class="eg-choices">';
  step.opts.forEach(function(opt) {
    if (opt.r) {
      html += '<button type="button" class="eg-choice-btn" data-eg-r="' + _egEsc(JSON.stringify(opt.r)) + '" onclick="_egShowResults(this)">' + _egEsc(opt.t) + '</button>';
    } else {
      html += '<button type="button" class="eg-choice-btn" onclick="_egRender(\'' + opt.n + '\')">' + _egEsc(opt.t) + '</button>';
    }
  });
  html += '</div>';
  if (_egHistory.length > 1) {
    html += '<div class="eg-nav">';
    html += '<button type="button" class="eg-back-btn" onclick="_egBack()">← Volver</button>';
    html += '<button type="button" class="eg-restart-btn" onclick="_egRestart()">↺ Reiniciar</button>';
    html += '</div>';
  }
  html += '</div>';
  panel.innerHTML = html;
}

function _egShowResults(btn) {
  const results = JSON.parse(btn.dataset.egR);
  const panel = document.getElementById('ew-guided');
  if (!panel) return;

  let html = '<div class="eg-results">';
  html += '<p class="eg-results-hint">Elegí la que más se parece a lo que sentís para agregarla:</p>';
  html += '<div class="eg-cards">';
  results.forEach(function(r) {
    html += '<button type="button" class="eg-card" style="--eg-accent:' + _egColor(r.val) + '" data-eg-val="' + _egEsc(r.val) + '" onclick="_egPick(this)">';
    html += '<span class="eg-card-name">' + _egEsc(r.name) + '</span>';
    html += '<span class="eg-card-desc">' + _egEsc(r.desc) + '</span>';
    html += '</button>';
  });
  html += '</div>';
  html += '<div class="eg-nav">';
  html += '<button type="button" class="eg-back-btn" onclick="_egRenderCurrent()">← Volver</button>';
  html += '<button type="button" class="eg-restart-btn" onclick="_egRestart()">↺ Reiniciar</button>';
  html += '</div>';
  html += '</div>';
  panel.innerHTML = html;
}

function _egPick(btn) {
  if (!_egPicker) return;
  btn.classList.add('eg-card-picked');
  ewAddValue(_egPicker, btn.dataset.egVal);
  setTimeout(function() { _egRestart(); }, 700);
}

function _egBack() {
  if (_egHistory.length <= 1) return;
  _egHistory.pop();
  _egRender(_egHistory[_egHistory.length - 1], false);
}

function _egRenderCurrent() {
  _egRender(_egHistory[_egHistory.length - 1], false);
}

function _egRestart() {
  _egHistory = [];
  _egRender('s1');
}

function _egEsc(s) {
  return String(s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;')
    .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

function _egColor(val) {
  const base = val.replace(/^ek::/, '').split(' > ')[0];
  return (EMOTION_WHEEL[base] && EMOTION_WHEEL[base].color) || '#8892a4';
}
