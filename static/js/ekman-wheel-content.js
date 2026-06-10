// Contenido de la rueda Ekman — 100% del Atlas of Emotions (atlasofemotions.org).
// Keyeado por path en INGLÉS (igual que EKMAN_WHEEL): "Anger", "Anger|Frustration".
// Base: qué es / para qué sirve / cómo se manifiesta / disparadores (Paul Ekman Group).
// Estados: "que" = definición del estado según el Atlas; función y manifestación heredan de la base.
const EKMAN_CONTENT = {
  // ── BASES (Paul Ekman Group · Atlas of Emotions) ──────────────────────────
  "Anger": {
    que: "Surge cuando algo bloquea una meta o cuando percibís un trato injusto. Va de la irritación leve a la furia.",
    sirve: "Señala un obstáculo o una injusticia y te moviliza a enfrentarlo o a poner un límite. Su mensaje de fondo es «apartate de mi camino».",
    manifiesta: "Calor, sudor, tensión muscular, mandíbula o puños apretados. Cejas bajas y juntas, mirada fija, labios tensos. La voz toma filo y puede escalar al grito; el cuerpo se inclina hacia adelante.",
    distinguir: "La gatillan la interferencia deliberada con tus planes, la injusticia, la traición, el rechazo o ver que se rompe una regla.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Fear": {
    que: "Surge ante la amenaza de un daño —físico, emocional o psicológico, real o imaginado.",
    sirve: "Te moviliza para enfrentar el peligro y mantenerte a salvo, disparando reacciones instintivas (luchar, huir o paralizarte) sin pensarlas.",
    manifiesta: "Voz más aguda o tensa, frío, falta de aire, sudor, temblor o tensión muscular. Cejas levantadas y rectas, párpados muy abiertos (se ve el blanco), labios estirados. El cuerpo huye o se congela.",
    distinguir: "Lo gatillan la oscuridad, las alturas, el rechazo social, ciertos animales o la muerte. Su intensidad depende de la gravedad del daño, su inminencia y tu capacidad de afrontarlo.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Sadness": {
    que: "Surge por la pérdida de alguien o algo importante. Va de la melancolía leve al duelo profundo.",
    sirve: "Pide ayuda o consuelo a los demás y te da tiempo para recuperarte. Comunica que algo valioso se perdió.",
    manifiesta: "Opresión en el pecho, pesadez en el cuerpo, ardor en la garganta, ojos llorosos. Extremos internos de las cejas hacia arriba. El cuerpo se hunde, la mirada baja y se pierde tono muscular.",
    distinguir: "La gatillan el rechazo, las despedidas, la enfermedad o muerte de seres queridos y los cambios de vida. No es lo mismo que la depresión, que es persistente.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Disgust": {
    que: "Sensación de aversión o rechazo hacia algo que te resulta repugnante. Va del desagrado leve al asco intenso.",
    sirve: "Te protege: te aleja de lo que podría enfermarte o contaminarte —comida en mal estado, toxinas, situaciones nocivas. También puede marcar transgresiones morales.",
    manifiesta: "Nariz arrugada (la señal más clara), náusea o impulso de vomitar, sonidos como «puaj». Tendés a girar la cabeza o el cuerpo para alejarte, o a taparte la nariz y la boca.",
    distinguir: "Lo gatillan los desechos corporales, lo podrido o enfermo, ciertas comidas y las transgresiones percibidas. Se diferencia del desprecio: el asco rechaza algo repugnante.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Enjoyment": {
    que: "Familia de estados placenteros que va de la paz al éxtasis, normalmente por conexión o por placer sensorial.",
    sirve: "Le señala a los demás que no sos una amenaza y te motiva a conductas buenas para vos y para vincularte. Es un motor central de la motivación.",
    manifiesta: "Sensación de liviandad, energía, calidez o calma. Sonrisa genuina (de Duchenne, con «patas de gallo»), suspiros, risa. Postura erguida y elevada, o quieta y relajada.",
    distinguir: "Lo gatillan los placeres de los sentidos, el humor, los logros propios o ajenos, la belleza y sentirte conectado (con personas, la naturaleza, una causa).",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },

  // ── ESTADOS (definición del Atlas) ────────────────────────────────────────
  // Anger
  "Anger|Annoyance":        { que: "Ira muy leve.", fuente: "Atlas of Emotions" },
  "Anger|Frustration":      { que: "Respuesta a no poder superar un obstáculo pese a intentarlo repetidamente.", fuente: "Atlas of Emotions" },
  "Anger|Exasperation":     { que: "Pérdida de la paciencia ante el fracaso repetido en resolver un problema.", fuente: "Atlas of Emotions" },
  "Anger|Argumentativeness": { que: "Inclinación a prolongar los desacuerdos.", fuente: "Atlas of Emotions" },
  "Anger|Bitterness":       { que: "Amargura por el desencanto de que nadie quiso resolver el problema.", fuente: "Atlas of Emotions" },
  "Anger|Vengefulness":     { que: "Deseo de tomar represalia.", fuente: "Atlas of Emotions" },
  "Anger|Fury":             { que: "Ira intensa.", fuente: "Atlas of Emotions" },

  // Fear
  "Fear|Trepidation": { que: "Anticipación de la posibilidad de un peligro.", fuente: "Atlas of Emotions" },
  "Fear|Nervousness": { que: "Incertidumbre sobre si hay peligro.", fuente: "Atlas of Emotions" },
  "Fear|Anxiety":     { que: "Miedo ante una amenaza anticipada o real, con incertidumbre sobre tu capacidad de afrontarla.", fuente: "Atlas of Emotions" },
  "Fear|Dread":       { que: "Anticipación de un peligro grave.", fuente: "Atlas of Emotions" },
  "Fear|Desperation": { que: "Respuesta a la incapacidad de reducir el peligro.", fuente: "Atlas of Emotions" },
  "Fear|Panic":       { que: "Miedo súbito y abrumador, consecuencia de la desesperación.", fuente: "Atlas of Emotions" },
  "Fear|Horror":      { que: "Mezcla de miedo y asco.", fuente: "Atlas of Emotions" },
  "Fear|Terror":      { que: "Miedo máximo.", fuente: "Atlas of Emotions" },

  // Sadness
  "Sadness|Disappointment": { que: "Sensación de que las expectativas no se cumplen.", fuente: "Atlas of Emotions" },
  "Sadness|Discouragement": { que: "Sensación de que no hay manera de afrontarlo.", fuente: "Atlas of Emotions" },
  "Sadness|Distraughtness": { que: "Tristeza agitada.", fuente: "Atlas of Emotions" },
  "Sadness|Resignation":    { que: "Aceptación de que no hay nada que hacer.", fuente: "Atlas of Emotions" },
  "Sadness|Helplessness":   { que: "Darte cuenta de que no podés evitar ni afrontar la pérdida.", fuente: "Atlas of Emotions" },
  "Sadness|Hopelessness":   { que: "Sensación de que nada bueno va a venir.", fuente: "Atlas of Emotions" },
  "Sadness|Misery":         { que: "Tristeza angustiosa, normalmente prolongada.", fuente: "Atlas of Emotions" },
  "Sadness|Despair":        { que: "Angustia resignada: sufrir sin creer que puedas hacer algo.", fuente: "Atlas of Emotions" },
  "Sadness|Grief":          { que: "Tristeza angustiosa por la pérdida de seres queridos.", fuente: "Atlas of Emotions" },
  "Sadness|Sorrow":         { que: "Tristeza por una pérdida.", fuente: "Atlas of Emotions" },
  "Sadness|Anguish":        { que: "Tristeza intensa y agitada.", fuente: "Atlas of Emotions" },

  // Disgust
  "Disgust|Dislike":    { que: "La forma más leve del asco.", fuente: "Atlas of Emotions" },
  "Disgust|Aversion":   { que: "Deseo de evitar algo que da asco.", fuente: "Atlas of Emotions" },
  "Disgust|Distaste":   { que: "Reacción a un mal sabor u olor; también en sentido figurado.", fuente: "Atlas of Emotions" },
  "Disgust|Repugnance": { que: "Repulsión hacia algo tóxico, literal o figuradamente.", fuente: "Atlas of Emotions" },
  "Disgust|Revulsion":  { que: "Asco muy intenso.", fuente: "Atlas of Emotions" },
  "Disgust|Abhorrence": { que: "Repulsión extrema.", fuente: "Atlas of Emotions" },
  "Disgust|Loathing":   { que: "Asco intenso centrado en una persona.", fuente: "Atlas of Emotions" },

  // Enjoyment
  "Enjoyment|Sensory pleasure": { que: "Disfrute a través de los cinco sentidos.", fuente: "Atlas of Emotions" },
  "Enjoyment|Rejoicing":        { que: "Alegría que se celebra; gozo compartido.", fuente: "Atlas of Emotions" },
  "Enjoyment|Compassion/joy":   { que: "Disfrute al actuar para aliviar el sufrimiento de otro.", fuente: "Atlas of Emotions" },
  "Enjoyment|Amusement":        { que: "Disfrute liviano y juguetón, de buen humor.", fuente: "Atlas of Emotions" },
  "Enjoyment|Schadenfreude":    { que: "Placer al enterarte de que a un rival le fue mal (palabra alemana).", fuente: "Atlas of Emotions" },
  "Enjoyment|Relief":           { que: "El placer cuando algo que te tenía en vilo (a menudo miedo) por fin afloja.", fuente: "Atlas of Emotions" },
  "Enjoyment|Peace":            { que: "Sentir que todo está bien y que no hay nada que necesites hacer.", fuente: "Atlas of Emotions" },
  "Enjoyment|Pride":            { que: "Placer por un logro propio (o de alguien que nutriste) que querés que otros conozcan.", fuente: "Atlas of Emotions" },
  "Enjoyment|Fiero":            { que: "El disfrute de haber superado un desafío que te exigió (palabra italiana).", fuente: "Atlas of Emotions" },
  "Enjoyment|Naches":           { que: "El orgullo por el logro de un hijo o discípulo (palabra del yidis).", fuente: "Atlas of Emotions" },
  "Enjoyment|Wonder":           { que: "Algo muy sorprendente, bello, increíble o difícil de creer.", fuente: "Atlas of Emotions" },
  "Enjoyment|Excitement":       { que: "Energía que rara vez se siente leve; va de media a alta.", fuente: "Atlas of Emotions" },
  "Enjoyment|Ecstasy":          { que: "Deleite arrebatador; felicidad altísima, casi abrumadora.", fuente: "Atlas of Emotions" }
};
