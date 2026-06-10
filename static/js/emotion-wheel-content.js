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
  },

  // ── SECUNDARIAS (36) — qué es + distinción; función/manifestación heredan del centro ──
  // Enojado
  "Enojado|Herido":    { que: "Dolor emocional por algo que te lastimó (palabras o actos de otro).", distinguir: "Es la cara vulnerable del enojo: debajo de la bronca suele haber una herida.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Enojado|Hostil":    { que: "Actitud de antagonismo y rechazo hacia alguien.", distinguir: "El enojo se vuelve disposición a atacar o a tratar al otro como enemigo.", fuente: "RAE / uso común" },
  "Enojado|Enfadado":  { que: "Enojo manifiesto por algo que salió mal o te molestó.", distinguir: "Es el enojo en su forma directa y declarada.", fuente: "Atlas of Emotions (Ekman)" },
  "Enojado|Rabioso":   { que: "Enojo muy intenso y desbordado.", distinguir: "Más extremo que el enfado: la reacción puede superar a la causa.", fuente: "Atlas of Emotions (Ekman)" },
  "Enojado|Rencoroso": { que: "Enojo cargado de odio o animadversión sostenida hacia alguien.", distinguir: "A diferencia del enfado pasajero, guarda y macera el odio en el tiempo.", fuente: "RAE / uso común" },
  "Enojado|Crítico":   { que: "Enojo que se expresa juzgando y señalando defectos.", distinguir: "Canaliza la bronca en juicio hacia ideas o personas.", fuente: "RAE / uso común" },

  // Asustado
  "Asustado|Confundido": { que: "Desconcierto: no entendés qué pasa ni qué hacer.", distinguir: "El miedo todavía no se resolvió, por falta de información.", fuente: "RAE / uso común" },
  "Asustado|Rechazado":  { que: "Temor o dolor de no ser aceptado o de ser excluido.", distinguir: "El peligro es social: la pérdida del vínculo o la pertenencia.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Asustado|Indefenso":  { que: "Sentir que no podés protegerte ni hacer nada ante la amenaza.", distinguir: "El foco está en la falta de recursos para afrontar el peligro.", fuente: "Atlas of Emotions (Ekman)" },
  "Asustado|Sumiso":     { que: "Te achicás y cedés ante otro por temor.", distinguir: "El miedo lleva a someterse en vez de huir o enfrentar.", fuente: "RAE / uso común" },
  "Asustado|Inseguro":   { que: "Falta de seguridad o confianza en vos mismo ante lo que viene.", distinguir: "Miedo difuso sobre tu capacidad o valía, sin un peligro concreto.", fuente: "RAE / uso común" },
  "Asustado|Ansioso":    { que: "Inquietud ante una amenaza anticipada, con incertidumbre sobre si podrás afrontarla.", distinguir: "El miedo apunta al futuro; si el peligro es inmediato, es más bien susto.", fuente: "Atlas of Emotions (Ekman)" },

  // Alegre
  "Alegre|Entusiasmado": { que: "Energía y ganas intensas ante algo que esperás o disfrutás.", distinguir: "Alegría con activación alta, orientada a la acción.", fuente: "RAE / uso común" },
  "Alegre|Sensual":      { que: "Disfrute ligado a la atracción y al placer del cuerpo.", distinguir: "La alegría se vive desde lo sensual y la seducción.", fuente: "RAE / uso común" },
  "Alegre|Enérgico":     { que: "Lleno de vitalidad y empuje.", distinguir: "La alegría se expresa como energía y vigor.", fuente: "RAE / uso común" },
  "Alegre|Juguetón":     { que: "Disfrute liviano, lúdico y de buen humor.", distinguir: "La alegría se vive con juego y humor.", fuente: "RAE / uso común" },
  "Alegre|Creativo":     { que: "Impulso a crear, imaginar y producir algo nuevo.", distinguir: "La alegría se canaliza en la expresión y la inventiva.", fuente: "RAE / uso común" },
  "Alegre|Consciente":   { que: "Presencia y apertura atenta a lo que pasa dentro y fuera.", distinguir: "La alegría serena de estar despierto y receptivo al momento.", fuente: "RAE / uso común" },

  // Poderoso
  "Poderoso|Fiel":        { que: "Compromiso y lealtad firmes con alguien o algo.", distinguir: "La fuerza se expresa en sostener tu palabra y tus vínculos.", fuente: "RAE / uso común" },
  "Poderoso|Importante":  { que: "Sentir que contás, que tu presencia y aporte pesan.", distinguir: "El poder viene del lugar que ocupás ante otros.", fuente: "RAE / uso común" },
  "Poderoso|Esperanzado": { que: "Confianza en que las cosas pueden salir bien y vale la pena intentarlo.", distinguir: "La fuerza mira al futuro con expectativa positiva.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Poderoso|Apreciado":   { que: "Sentirte valorado y reconocido por los demás.", distinguir: "El poder viene del reconocimiento ajeno.", fuente: "RAE / uso común" },
  "Poderoso|Respetado":   { que: "Sentir que los demás valoran lo que sos y hacés.", distinguir: "La fuerza se apoya en la consideración recibida.", fuente: "RAE / uso común" },
  "Poderoso|Orgulloso":   { que: "Placer por un logro propio (o de alguien que querés) que querés que se conozca.", distinguir: "El poder ligado al mérito y al valor personal.", fuente: "Atlas of Emotions (Ekman) · Atlas of the Heart (Brené Brown)" },

  // Apacible
  "Apacible|Conforme":    { que: "Sentir que tus necesidades están satisfechas: completo y suficiente.", distinguir: "El contento de que lo que hay alcanza, sin necesitar más.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Apacible|Considerado": { que: "Atención cuidadosa y reflexiva hacia los demás.", distinguir: "La paz se expresa en el cuidado atento del otro.", fuente: "RAE / uso común" },
  "Apacible|Íntimo":      { que: "Cercanía y confianza profunda en un vínculo.", distinguir: "La paz de sentirse cerca y a salvo con alguien.", fuente: "RAE / uso común" },
  "Apacible|Amoroso":     { que: "Sentir y dar cariño desde la calma.", distinguir: "La paz se vive en el afecto presente.", fuente: "RAE / uso común" },
  "Apacible|Confiado":    { que: "Entregarte con confianza, sin recelo, a alguien o algo.", distinguir: "La paz de no tener que cuidarte ni desconfiar.", fuente: "RAE / uso común" },
  "Apacible|Protector":   { que: "Impulso de cuidar y sostener a otro.", distinguir: "La paz que da acompañar y nutrir.", fuente: "RAE / uso común" },

  // Triste
  "Triste|Adormecido":  { que: "Apagamiento y falta de energía; ganas de retirarte.", distinguir: "La tristeza baja la activación: el cuerpo se aletarga.", fuente: "RAE / uso común" },
  "Triste|Aburrido":    { que: "Desgano y falta de interés o estímulo.", distinguir: "Forma apagada de la tristeza: no hay una pérdida puntual, sino ausencia de sentido.", fuente: "RAE / uso común" },
  "Triste|Solo":        { que: "Sensación dolorosa de estar desconectado, aunque haya gente alrededor.", distinguir: "La pérdida es de conexión; distinto de estar solo por elección, que no duele.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Triste|Deprimido":   { que: "Abatimiento pesado y persistente, con sensación de vacío.", distinguir: "Como matiz es tristeza honda; la depresión clínica es un trastorno aparte.", fuente: "Atlas of Emotions (Ekman)" },
  "Triste|Avergonzado": { que: "Dolor de creer que algo está mal con vos mismo, no solo con lo que hiciste.", distinguir: "La culpa dice «hice algo malo»; la vergüenza dice «soy malo».", fuente: "Atlas of the Heart (Brené Brown)" },
  "Triste|Culpable":    { que: "Malestar por algo que hiciste (o creés haber hecho) que va contra tus valores.", distinguir: "La culpa apunta a la conducta («hice algo malo»), no a tu identidad.", fuente: "Atlas of the Heart (Brené Brown)" },

  // ── TERCIARIAS (36) — una por secundaria; función/manifestación heredan del centro ──
  // Enojado
  "Enojado|Herido|Celoso":      { que: "Temor a perder un vínculo importante frente a un tercero.", distinguir: "Los celos defienden una relación amenazada; la envidia quiere lo que otro tiene.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Enojado|Hostil|Egoísta":     { que: "Priorizar lo propio sin registrar al otro.", distinguir: "El enojo se cierra en uno mismo.", fuente: "RAE / uso común" },
  "Enojado|Enfadado|Frustrado": { que: "Malestar por no poder superar un obstáculo pese a intentarlo.", distinguir: "Nace del bloqueo de una meta, no de una injusticia.", fuente: "Atlas of Emotions (Ekman)" },
  "Enojado|Rabioso|Furioso":    { que: "Enojo encendido, muy intenso.", distinguir: "Cerca del extremo de la ira (furia).", fuente: "Atlas of Emotions (Ekman)" },
  "Enojado|Rencoroso|Irritado": { que: "Molestia leve y superficial.", distinguir: "Fastidio de baja intensidad, fácil de gatillar y de pasar.", fuente: "Atlas of Emotions (Ekman)" },
  "Enojado|Crítico|Escéptico":  { que: "Duda y desconfianza ante lo que te presentan.", distinguir: "El enojo se vuelve incredulidad crítica.", fuente: "RAE / uso común" },

  // Asustado
  "Asustado|Confundido|Desconcertado": { que: "Aturdido, sin entender qué pasa.", distinguir: "Confusión intensa ante lo inesperado.", fuente: "RAE / uso común" },
  "Asustado|Rechazado|Desanimado":     { que: "Sensación de que no hay manera de afrontarlo.", distinguir: "El miedo apaga las ganas de intentar.", fuente: "Atlas of Emotions (Ekman)" },
  "Asustado|Indefenso|Insignificante": { que: "Sentir que no valés ni contás para nadie.", distinguir: "El miedo se vive como quedar anulado.", fuente: "RAE / uso común" },
  "Asustado|Sumiso|Débil":             { que: "Sentirte sin fuerzas ni recursos.", distinguir: "El miedo expone tu fragilidad.", fuente: "RAE / uso común" },
  "Asustado|Inseguro|Ridículo":        { que: "Temor a quedar en ridículo o a parecer tonto.", distinguir: "El peligro es el juicio y la burla de otros.", fuente: "RAE / uso común" },
  "Asustado|Ansioso|Apenado":          { que: "Incomodidad por quedar expuesto ante otros.", distinguir: "Más leve y social que la vergüenza profunda.", fuente: "Atlas of the Heart (Brené Brown)" },

  // Alegre
  "Alegre|Entusiasmado|Atrevido":   { que: "Animarte a algo arriesgado con entusiasmo.", distinguir: "La alegría se anima a desafiar.", fuente: "RAE / uso común" },
  "Alegre|Sensual|Fascinado":       { que: "Quedar cautivado por algo que te atrae.", distinguir: "La alegría absorta en lo que admira.", fuente: "RAE / uso común" },
  "Alegre|Enérgico|Estimulado":     { que: "Activado e inspirado por un estímulo.", distinguir: "La alegría que despierta y moviliza.", fuente: "RAE / uso común" },
  "Alegre|Juguetón|Divertido":      { que: "Disfrute liviano y risueño.", distinguir: "La alegría del humor y el juego.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Alegre|Creativo|Extravagante":   { que: "Disfrute desbordante, sin medida.", distinguir: "La alegría que se permite el exceso.", fuente: "RAE / uso común" },
  "Alegre|Consciente|Encantado":    { que: "Deleite y gusto pleno por algo.", distinguir: "La alegría del encanto y el deleite.", fuente: "RAE / uso común" },

  // Poderoso
  "Poderoso|Fiel|Seguro":          { que: "Confianza firme en tus capacidades.", distinguir: "El poder mira hacia adentro, a tu autoconfianza.", fuente: "Autoeficacia (Bandura)" },
  "Poderoso|Importante|Inteligente": { que: "Sentirte capaz, lúcido y competente.", distinguir: "El poder ligado a tu capacidad de comprender y resolver.", fuente: "RAE / uso común" },
  "Poderoso|Esperanzado|Digno":    { que: "Sentir que valés la pena, que merecés y sos suficiente.", distinguir: "El poder de reconocer tu propio valor.", fuente: "RAE / uso común" },
  "Poderoso|Apreciado|Valioso":    { que: "Sentir que tenés valor para los demás y el mundo.", distinguir: "Cercano a Digno, pero centrado en el valor que aportás.", fuente: "RAE / uso común" },
  "Poderoso|Respetado|Satisfecho": { que: "Plenitud por haber logrado o cumplido algo.", distinguir: "El poder de lo realizado.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Poderoso|Orgulloso|Animado":    { que: "Ánimo alto y disposición positiva.", distinguir: "El poder se vive como buen ánimo y empuje.", fuente: "RAE / uso común" },

  // Apacible
  "Apacible|Conforme|Pensativo":     { que: "Quietud reflexiva, mente en calma pensando.", distinguir: "La paz de la introspección serena.", fuente: "RAE / uso común" },
  "Apacible|Considerado|Relajado":   { que: "Cuerpo y mente distendidos, sin tensión.", distinguir: "La paz física de soltar la tensión.", fuente: "RAE / uso común" },
  "Apacible|Íntimo|Receptivo":       { que: "Abierto a recibir y responder con calma.", distinguir: "La paz de la apertura sin defensa.", fuente: "RAE / uso común" },
  "Apacible|Amoroso|Sereno":         { que: "Calma profunda y estable.", distinguir: "La paz que no se altera fácil.", fuente: "RAE / uso común" },
  "Apacible|Confiado|Sentimental":   { que: "Ternura y afecto a flor de piel.", distinguir: "La paz teñida de emoción cálida.", fuente: "RAE / uso común" },
  "Apacible|Protector|Agradecido":   { que: "Reconocer y valorar lo bueno que recibís.", distinguir: "La gratitud, fuente de bienestar y conexión.", fuente: "Atlas of the Heart (Brené Brown)" },

  // Triste
  "Triste|Adormecido|Apático":    { que: "Falta de ganas, energía e interés.", distinguir: "El desgano apunta a la acción.", fuente: "RAE / uso común" },
  "Triste|Aburrido|Inferior":     { que: "Sentirte menos que los demás.", distinguir: "La tristeza se centra en la comparación desfavorable.", fuente: "RAE / uso común" },
  "Triste|Solo|Inadecuado":       { que: "Sentir que no estás a la altura o no encajás.", distinguir: "La tristeza de no dar la talla.", fuente: "RAE / uso común" },
  "Triste|Deprimido|Miserable":   { que: "Tristeza angustiosa, normalmente prolongada.", distinguir: "Forma honda y sostenida del abatimiento.", fuente: "Atlas of Emotions (Ekman)" },
  "Triste|Avergonzado|Tonto":     { que: "Sentirte torpe o poco capaz.", distinguir: "La tristeza se vuelve autodescalificación.", fuente: "RAE / uso común" },
  "Triste|Culpable|Tímido":       { que: "Encogimiento y reparo ante los demás.", distinguir: "La tristeza que se retrae del contacto.", fuente: "RAE / uso común" }
};
