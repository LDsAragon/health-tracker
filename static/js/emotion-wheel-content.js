// Contenido de la rueda Willcox (es) — keyeado por path "Base", "Base|Sec", "Base|Sec|Terc".
// Sourced y citado por entrada. El contenido viejo (Junto) está en emotion-wheel-content-old.js.
// Fase 2: los 6 centros. Secundarias/terciarias llegan en fases siguientes (heredan del centro).
const EMOTION_CONTENT = {
  "Enojado": {   // Mad / Anger
    que: "Surge cuando algo bloquea una meta o cuando percibís un trato injusto. Va de la irritación leve a la furia.",
    sirve: "Señala un obstáculo o una injusticia y te moviliza a enfrentarlo o a poner un límite.",
    manifiesta: "Calor, tensión muscular, mandíbula o puños apretados; cejas bajas y juntas, mirada fija; la voz toma filo y el cuerpo se inclina hacia adelante.",
    distinguir: "Lo gatillan la interferencia con tus planes, la injusticia, la traición o el rechazo. Si predomina el peligro y no la defensa, mirá Asustado.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Asustado": {  // Scared / Fear
    que: "Surge ante la amenaza de un daño —físico, emocional o psicológico, real o imaginado.",
    sirve: "Te moviliza para enfrentar el peligro y mantenerte a salvo (luchar, huir o paralizarte), sin pensarlo.",
    manifiesta: "Voz más aguda, frío, falta de aire, sudor, temblor; cejas levantadas y rectas, párpados muy abiertos. El cuerpo huye o se congela.",
    distinguir: "Su intensidad depende de la gravedad del daño, su inminencia y tu capacidad de afrontarlo.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Alegre": {    // Joyful / Joy
    que: "Familia de estados placenteros que va de la paz al éxtasis, por conexión o por placer sensorial.",
    sirve: "Le señala a los demás que no sos una amenaza y te motiva a vincularte. Es un motor central de la motivación.",
    manifiesta: "Liviandad, energía, calidez; sonrisa genuina (con «patas de gallo»), risa; postura erguida o relajada.",
    distinguir: "La gatillan los placeres de los sentidos, el humor, los logros, la belleza y sentirte conectado.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Poderoso": {  // Powerful (no es emoción básica de Ekman → empoderamiento/autoeficacia)
    que: "Sensación de fuerza, confianza y control sobre tu vida: que podés decidir, actuar y lograr lo que te proponés.",
    sirve: "Sostiene la agencia y la resiliencia: creer que sos capaz de afrontar los desafíos te impulsa a intentarlo.",
    manifiesta: "Postura erguida y firme, voz segura, sensación de energía y foco; disposición a tomar la iniciativa.",
    distinguir: "Se apoya en la autoeficacia (creer que podés) y en un locus de control interno. No es soberbia: es sentir que tu acción cuenta.",
    fuente: "Autoeficacia (Bandura) · APA"
  },
  "Apacible": {  // Peaceful (paz/calma/contento)
    que: "Calma serena: sentir que todo está en orden y que no hay nada que necesites hacer.",
    sirve: "Repone y da perspectiva: te permite vivir lo que sentís sin reaccionar en caliente, y disfrutar el momento.",
    manifiesta: "Respiración lenta, cuerpo relajado y distendido, mente quieta; sensación de plenitud y de suficiencia.",
    distinguir: "La «tranquilidad» es la paz de no tener nada pendiente; el «contento», la de haber terminado lo tuyo. Ekman ubica la paz dentro de la familia del disfrute.",
    fuente: "Atlas of the Heart (Brené Brown) · Atlas of Emotions (Ekman)"
  },
  "Triste": {    // Sad / Sadness
    que: "Surge por la pérdida de alguien o algo importante. Va de la melancolía leve al duelo profundo.",
    sirve: "Pide ayuda o consuelo y te da tiempo para recuperarte. Comunica que algo valioso se perdió.",
    manifiesta: "Opresión en el pecho, pesadez, ardor en la garganta, ojos llorosos; extremos internos de las cejas hacia arriba; cuerpo hundido.",
    distinguir: "La gatillan el rechazo, las despedidas, la enfermedad o muerte. No es lo mismo que la depresión (persistente). La tristeza responde a la pérdida; el duelo es el proceso activo de elaborarla.",
    fuente: "Atlas of Emotions (Ekman) · Atlas of the Heart (Brené Brown)"
  }
};
