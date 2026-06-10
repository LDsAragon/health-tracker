// Contenido de la rueda Willcox (es) — keyeado por path "Base", "Base|Sec", "Base|Sec|Terc".
// Sourced y citado por entrada. El contenido viejo (Junto) está en emotion-wheel-content-old.js.
// La rueda en sí: Feeling Wheel · Gloria Willcox (1982). Las definiciones se apoyan en literatura
// psicológica (Ekman, Cowen & Keltner 2017, Brené Brown, Plutchik, Bandura, Adler, Gilbert,
// Ryan & Deci, Silvia, Csikszentmihalyi…); las pocas puramente léxicas citan el propio wheel.
const EMOTION_CONTENT = {
  // ── CENTROS (6) ───────────────────────────────────────────────────────────
  "Enojado": {
    que: "Surge cuando algo bloquea una meta o cuando percibís un trato injusto. Va de la irritación leve a la furia.",
    sirve: "Señala un obstáculo o una injusticia y te moviliza a enfrentarlo o a poner un límite.",
    manifiesta: "Calor, tensión muscular, mandíbula o puños apretados; cejas bajas y juntas, mirada fija; la voz toma filo y el cuerpo se inclina hacia adelante.",
    distinguir: "Lo gatillan la interferencia con tus planes, la injusticia, la traición o el rechazo. Si predomina el peligro y no la defensa, mirá Asustado.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Asustado": {
    que: "Surge ante la amenaza de un daño —físico, emocional o psicológico, real o imaginado.",
    sirve: "Te moviliza para enfrentar el peligro y mantenerte a salvo (luchar, huir o paralizarte), sin pensarlo.",
    manifiesta: "Voz más aguda, frío, falta de aire, sudor, temblor; cejas levantadas y rectas, párpados muy abiertos. El cuerpo huye o se congela.",
    distinguir: "Su intensidad depende de la gravedad del daño, su inminencia y tu capacidad de afrontarlo.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Alegre": {
    que: "Familia de estados placenteros que va de la paz al éxtasis, por conexión o por placer sensorial.",
    sirve: "Le señala a los demás que no sos una amenaza y te motiva a vincularte. Es un motor central de la motivación.",
    manifiesta: "Liviandad, energía, calidez; sonrisa genuina (con «patas de gallo»), risa; postura erguida o relajada.",
    distinguir: "La gatillan los placeres de los sentidos, el humor, los logros, la belleza y sentirte conectado.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Poderoso": {
    que: "Sensación de fuerza, confianza y control sobre tu vida: que podés decidir, actuar y lograr lo que te proponés.",
    sirve: "Sostiene la agencia y la resiliencia: creer que sos capaz de afrontar los desafíos te impulsa a intentarlo.",
    manifiesta: "Postura erguida y firme, voz segura, sensación de energía y foco; disposición a tomar la iniciativa.",
    distinguir: "Se apoya en la autoeficacia (creer que podés) y en un locus de control interno. No es soberbia: es sentir que tu acción cuenta.",
    fuente: "Autoeficacia (Bandura) · APA"
  },
  "Apacible": {
    que: "Calma serena: sentir que todo está en orden y que no hay nada que necesites hacer.",
    sirve: "Repone y da perspectiva: te permite vivir lo que sentís sin reaccionar en caliente, y disfrutar el momento.",
    manifiesta: "Respiración lenta, cuerpo relajado y distendido, mente quieta; sensación de plenitud y de suficiencia.",
    distinguir: "La «tranquilidad» es la paz de no tener nada pendiente; el «contento», la de haber terminado lo tuyo. Ekman ubica la paz dentro de la familia del disfrute.",
    fuente: "Atlas of the Heart (Brené Brown) · Atlas of Emotions (Ekman)"
  },
  "Triste": {
    que: "Surge por la pérdida de alguien o algo importante. Va de la melancolía leve al duelo profundo.",
    sirve: "Pide ayuda o consuelo y te da tiempo para recuperarte. Comunica que algo valioso se perdió.",
    manifiesta: "Opresión en el pecho, pesadez, ardor en la garganta, ojos llorosos; extremos internos de las cejas hacia arriba; cuerpo hundido.",
    distinguir: "La gatillan el rechazo, las despedidas, la enfermedad o muerte. No es lo mismo que la depresión (persistente). La tristeza responde a la pérdida; el duelo es el proceso activo de elaborarla.",
    fuente: "Atlas of Emotions (Ekman) · Atlas of the Heart (Brené Brown)"
  },

  // ── SECUNDARIAS (36) ──────────────────────────────────────────────────────
  // Enojado
  "Enojado|Herido":    { que: "Dolor emocional por algo que te lastimó (palabras o actos de otro).", distinguir: "Es la cara vulnerable del enojo: debajo de la bronca suele haber una herida.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Enojado|Hostil":    { que: "Disposición estable de antagonismo y mala voluntad hacia otros.", distinguir: "A diferencia del enojo puntual, la hostilidad persiste: es una orientación negativa que espera lo peor del otro (componente cognitivo, afectivo y conductual).", fuente: "Psicología de la hostilidad" },
  "Enojado|Enfadado":  { que: "Enojo manifiesto por algo que salió mal o te molestó.", distinguir: "Es el enojo en su forma directa y declarada.", fuente: "Atlas of Emotions (Ekman)" },
  "Enojado|Rabioso":   { que: "Enojo muy intenso y desbordado.", distinguir: "Más extremo que el enfado: la reacción puede superar a la causa.", fuente: "Atlas of Emotions (Ekman)" },
  "Enojado|Rencoroso": { que: "Enojo guardado y duradero hacia alguien que te ofendió o trató injustamente.", distinguir: "El enojo es por la situación inmediata; el rencor la macera en el tiempo (suele dirigirse a quien sentís por encima tuyo).", fuente: "Psicología del resentimiento" },
  "Enojado|Crítico":   { que: "Enojo que se expresa juzgando y señalando defectos.", distinguir: "Cercano al desprecio (enojo hacia alguien que ubicás por debajo); canaliza la bronca en juicio.", fuente: "Psicología del desprecio" },

  // Asustado
  "Asustado|Confundido": { que: "Desconcierto: no entendés qué pasa ni qué hacer.", distinguir: "Una «emoción del conocimiento»: el miedo no se resuelve por falta de información.", fuente: "Cowen & Keltner (2017) · emociones del conocimiento (Silvia)" },
  "Asustado|Rechazado":  { que: "Temor o dolor de no ser aceptado o de ser excluido.", distinguir: "El peligro es social: la pérdida del vínculo o la pertenencia.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Asustado|Indefenso":  { que: "Sentir que no podés protegerte ni hacer nada ante la amenaza.", distinguir: "El foco está en la falta de recursos para afrontar el peligro.", fuente: "Atlas of Emotions (Ekman)" },
  "Asustado|Sumiso":     { que: "Te achicás y cedés ante otro, señalando que no querés competir.", distinguir: "Estrategia defensiva ante una posición de menor rango; busca evitar el conflicto.", fuente: "Teoría del rango social (Gilbert)" },
  "Asustado|Inseguro":   { que: "Falta de seguridad o confianza en vos mismo ante lo que viene.", distinguir: "Miedo difuso sobre tu capacidad o valía; se vincula a un apego inseguro, sin un peligro concreto.", fuente: "Teoría del apego" },
  "Asustado|Ansioso":    { que: "Inquietud ante una amenaza anticipada, con incertidumbre sobre si podrás afrontarla.", distinguir: "El miedo apunta al futuro; si el peligro es inmediato, es más bien susto.", fuente: "Atlas of Emotions (Ekman)" },

  // Alegre
  "Alegre|Entusiasmado": { que: "Energía y ganas intensas ante algo que esperás o disfrutás.", distinguir: "Alegría con activación alta, orientada a la acción.", fuente: "Cowen & Keltner (2017), excitement · vitalidad (Ryan & Frederick)" },
  "Alegre|Sensual":      { que: "Disfrute ligado al deseo y la atracción física.", distinguir: "La alegría se vive desde lo sensual y la seducción.", fuente: "Cowen & Keltner (2017), deseo sexual" },
  "Alegre|Enérgico":     { que: "Sensación de vitalidad y aliveness: entusiasmo y empuje vital.", distinguir: "La vitalidad es energía positiva, distinta de la activación nerviosa o por enojo.", fuente: "Vitalidad subjetiva (Ryan & Frederick, 1997)" },
  "Alegre|Juguetón":     { que: "Disfrute liviano, lúdico y de buen humor.", distinguir: "La actitud juguetona acompaña a la creatividad y al disfrute del momento.", fuente: "Juego y creatividad (Csikszentmihalyi)" },
  "Alegre|Creativo":     { que: "Impulso a crear e imaginar; absorción plena en una actividad que te desafía.", distinguir: "Cercano al «flow»: inmersión total en lo que hacés.", fuente: "Flow (Csikszentmihalyi)" },
  "Alegre|Consciente":   { que: "Atención plena y abierta al momento presente, sin juzgar.", distinguir: "La alegría serena de estar despierto y receptivo al ahora.", fuente: "Mindfulness (atención plena)" },

  // Poderoso
  "Poderoso|Fiel":        { que: "Compromiso y lealtad firmes con alguien o algo.", distinguir: "La fuerza se expresa en sostener tu palabra y tus vínculos.", fuente: "Psicología del compromiso" },
  "Poderoso|Importante":  { que: "Sentir que contás, que sos significativo para otros.", distinguir: "El «mattering»: percibir que importás y que se te tiene en cuenta.", fuente: "Mattering (Rosenberg, 1985; Flett)" },
  "Poderoso|Esperanzado": { que: "Confianza en que las cosas pueden salir bien y vale la pena intentarlo.", distinguir: "La fuerza mira al futuro con expectativa positiva.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Poderoso|Apreciado":   { que: "Sentirte valorado y reconocido por los demás.", distinguir: "Componente del mattering: sentirte apreciado y tenido en cuenta.", fuente: "Mattering (Rosenberg · Schlossberg)" },
  "Poderoso|Respetado":   { que: "Sentir que los demás valoran lo que sos y hacés.", distinguir: "La fuerza se apoya en el reconocimiento y la consideración recibidos.", fuente: "Mattering · psicología del reconocimiento" },
  "Poderoso|Orgulloso":   { que: "Placer por un logro propio (o de alguien que querés) que querés que se conozca.", distinguir: "El poder ligado al mérito y al valor personal.", fuente: "Atlas of Emotions (Ekman) · Atlas of the Heart (Brené Brown)" },

  // Apacible
  "Apacible|Conforme":    { que: "Sentir que tus necesidades están satisfechas: completo y suficiente.", distinguir: "El contento de que lo que hay alcanza, sin necesitar más.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Apacible|Considerado": { que: "Atención cuidadosa y reflexiva hacia los demás.", distinguir: "La paz se expresa en el cuidado atento del otro (cercano a la compasión).", fuente: "Psicología de la compasión/empatía" },
  "Apacible|Íntimo":      { que: "Cercanía y confianza profunda en un vínculo.", distinguir: "La paz de sentirse cerca y a salvo; el amor surge de combinar alegría y confianza.", fuente: "Amor y apego (Plutchik: alegría + confianza)" },
  "Apacible|Amoroso":     { que: "Sentir y dar cariño desde la calma.", distinguir: "El amor como combinación de alegría y confianza; se vive en el afecto presente.", fuente: "Amor (Plutchik) · apego" },
  "Apacible|Confiado":    { que: "Entregarte con confianza, sin recelo, a alguien o algo.", distinguir: "La confianza —una de las emociones primarias de Plutchik— habilita el vínculo y baja la guardia.", fuente: "Confianza (Plutchik, emoción primaria)" },
  "Apacible|Protector":   { que: "Impulso de cuidar, sostener y nutrir a otro.", distinguir: "La paz de acompañar; activa los sistemas de cuidado (caregiving) ligados a la compasión.", fuente: "Psicología del cuidado · compasión" },

  // Triste
  "Triste|Adormecido":  { que: "Apagamiento y fatiga: el cuerpo se aletarga y querés retirarte.", distinguir: "El letargo, baja activación típica de los estados depresivos.", fuente: "Letargo (síntoma depresivo)" },
  "Triste|Aburrido":    { que: "Desgano y falta de interés o estímulo.", distinguir: "El aburrimiento: no hay una pérdida puntual, sino ausencia de sentido o estímulo.", fuente: "Aburrimiento (Cowen & Keltner, 2017)" },
  "Triste|Deprimido":   { que: "Abatimiento pesado y persistente, con sensación de vacío.", distinguir: "Como matiz es tristeza honda; la depresión clínica es un trastorno aparte.", fuente: "Atlas of Emotions (Ekman)" },
  "Triste|Solo":        { que: "Sensación dolorosa de estar desconectado, aunque haya gente alrededor.", distinguir: "La pérdida es de conexión; distinto de estar solo por elección, que no duele.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Triste|Avergonzado": { que: "Dolor de creer que algo está mal con vos mismo, no solo con lo que hiciste.", distinguir: "La culpa dice «hice algo malo»; la vergüenza dice «soy malo».", fuente: "Atlas of the Heart (Brené Brown)" },
  "Triste|Culpable":    { que: "Malestar por algo que hiciste (o creés haber hecho) que va contra tus valores.", distinguir: "La culpa apunta a la conducta («hice algo malo»), no a tu identidad.", fuente: "Atlas of the Heart (Brené Brown)" },

  // ── TERCIARIAS (36) ───────────────────────────────────────────────────────
  // Enojado
  "Enojado|Herido|Celoso":      { que: "Temor a perder un vínculo importante frente a un tercero.", distinguir: "Los celos defienden una relación amenazada; la envidia quiere lo que otro tiene.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Enojado|Hostil|Egoísta":     { que: "Priorizar lo propio sin registrar al otro.", distinguir: "El enojo se cierra en uno mismo.", fuente: "Feeling Wheel · Willcox (1982)" },
  "Enojado|Enfadado|Frustrado": { que: "Malestar por no poder superar un obstáculo pese a intentarlo.", distinguir: "Nace del bloqueo de una meta, no de una injusticia.", fuente: "Atlas of Emotions (Ekman)" },
  "Enojado|Rabioso|Furioso":    { que: "Enojo encendido, muy intenso.", distinguir: "Cerca del extremo de la ira (furia).", fuente: "Atlas of Emotions (Ekman)" },
  "Enojado|Rencoroso|Irritado": { que: "Molestia leve y superficial.", distinguir: "Fastidio de baja intensidad, fácil de gatillar y de pasar.", fuente: "Atlas of Emotions (Ekman)" },
  "Enojado|Crítico|Escéptico":  { que: "Duda y desconfianza ante lo que te presentan.", distinguir: "El cinismo/escepticismo es el componente cognitivo de la hostilidad: esperar lo peor.", fuente: "Cinismo/escepticismo (psicología de la hostilidad)" },

  // Asustado
  "Asustado|Confundido|Desconcertado": { que: "Aturdido, sin entender qué pasa.", distinguir: "Confusión intensa ante lo inesperado.", fuente: "Cowen & Keltner (2017) · emociones del conocimiento" },
  "Asustado|Rechazado|Desanimado":     { que: "Sensación de que no hay manera de afrontarlo.", distinguir: "El miedo apaga las ganas de intentar.", fuente: "Atlas of Emotions (Ekman)" },
  "Asustado|Indefenso|Insignificante": { que: "Sentir que no valés ni contás para nadie.", distinguir: "Rango social bajo y falta de mattering: el miedo se vive como quedar anulado.", fuente: "Teoría del rango social (Gilbert) · mattering (Rosenberg)" },
  "Asustado|Sumiso|Débil":             { que: "Sentirte sin fuerzas ni recursos.", distinguir: "Percepción de bajo rango: el miedo expone tu fragilidad.", fuente: "Teoría del rango social (Gilbert)" },
  "Asustado|Inseguro|Ridículo":        { que: "Temor a quedar en ridículo o a parecer tonto.", distinguir: "El peligro es el juicio y la burla de otros (vergüenza social).", fuente: "Psicología de la vergüenza" },
  "Asustado|Ansioso|Apenado":          { que: "Incomodidad por quedar expuesto ante otros.", distinguir: "Más leve y social que la vergüenza profunda.", fuente: "Atlas of the Heart (Brené Brown)" },

  // Alegre
  "Alegre|Entusiasmado|Atrevido":   { que: "Animarte a algo arriesgado a pesar del miedo.", distinguir: "Ligado al coraje (actuar pese al miedo) y a la búsqueda de sensaciones.", fuente: "Coraje (psicología) · búsqueda de sensaciones (Zuckerman)" },
  "Alegre|Sensual|Fascinado":       { que: "Quedar cautivado y absorto por algo que te atrae.", distinguir: "Es la forma intensa del interés (fascinación), cercana al embeleso.", fuente: "Interés/fascinación (Silvia; Izard)" },
  "Alegre|Enérgico|Estimulado":     { que: "Activado e inspirado por un estímulo.", distinguir: "El interés que despierta y moviliza la exploración.", fuente: "Interés (Silvia) · vitalidad (Ryan & Frederick)" },
  "Alegre|Juguetón|Divertido":      { que: "Disfrute liviano y risueño.", distinguir: "La alegría del humor y el juego.", fuente: "Atlas of the Heart (Brené Brown)" },
  "Alegre|Creativo|Extravagante":   { que: "Disfrute desbordante, sin medida.", distinguir: "La alegría que se permite el exceso.", fuente: "Feeling Wheel · Willcox (1982)" },
  "Alegre|Consciente|Encantado":    { que: "Deleite y gusto pleno por algo bello o placentero.", distinguir: "Cercano a la apreciación estética: el encanto de lo que te gusta.", fuente: "Cowen & Keltner (2017), apreciación estética" },

  // Poderoso
  "Poderoso|Fiel|Seguro":            { que: "Confianza firme en tus capacidades.", distinguir: "Autoeficacia: el poder mira hacia adentro, a tu autoconfianza.", fuente: "Autoeficacia (Bandura)" },
  "Poderoso|Importante|Inteligente": { que: "Sentirte capaz, lúcido y competente para resolver.", distinguir: "Competencia percibida: creer que podés comprender y resolver.", fuente: "Competencia · autoeficacia (Bandura)" },
  "Poderoso|Esperanzado|Digno":      { que: "Sentir que valés la pena, que merecés y sos suficiente.", distinguir: "El reverso sano de la inferioridad (Adler): reconocer tu propio valor.", fuente: "Autovalía · psicología individual (Adler)" },
  "Poderoso|Apreciado|Valioso":      { que: "Sentir que tenés valor para los demás y el mundo.", distinguir: "Cercano a Digno, pero centrado en el valor que aportás (mattering).", fuente: "Mattering (Rosenberg) · autovalía" },
  "Poderoso|Respetado|Satisfecho":   { que: "Plenitud por haber logrado o cumplido algo.", distinguir: "La satisfacción de lo realizado.", fuente: "Atlas of the Heart (Brené Brown) · Cowen & Keltner (2017)" },
  "Poderoso|Orgulloso|Animado":      { que: "Ánimo alto y disposición positiva.", distinguir: "Afecto positivo: el poder se vive como buen ánimo y empuje.", fuente: "Afecto positivo (psicología)" },

  // Apacible
  "Apacible|Conforme|Pensativo":     { que: "Quietud reflexiva, mente en calma pensando.", distinguir: "La paz de la introspección serena (calma contemplativa).", fuente: "Calma (Cowen & Keltner, 2017) · contemplación" },
  "Apacible|Considerado|Relajado":   { que: "Cuerpo y mente distendidos, sin tensión.", distinguir: "La calma de soltar la tensión física y mental.", fuente: "Calma (Cowen & Keltner, 2017)" },
  "Apacible|Íntimo|Receptivo":       { que: "Abierto a recibir y responder con calma.", distinguir: "La paz de la apertura sin defensa.", fuente: "Feeling Wheel · Willcox (1982)" },
  "Apacible|Amoroso|Sereno":         { que: "Calma profunda, estable y duradera.", distinguir: "La serenidad: paz que no se altera con facilidad.", fuente: "Serenidad (psicología positiva)" },
  "Apacible|Confiado|Sentimental":   { que: "Ternura y afecto a flor de piel.", distinguir: "La paz teñida de emoción cálida (cercana a la ternura/nostalgia).", fuente: "Ternura/nostalgia (Cowen & Keltner, 2017)" },
  "Apacible|Protector|Agradecido":   { que: "Reconocer y valorar lo bueno que recibís.", distinguir: "La gratitud, fuente de bienestar y conexión.", fuente: "Atlas of the Heart (Brené Brown)" },

  // Triste
  "Triste|Adormecido|Apático":    { que: "Falta de motivación e interés; indiferencia hacia lo que te rodea.", distinguir: "La apatía es falta de motivación; la anhedonia, falta de placer (relacionadas, distintas).", fuente: "Apatía (psicología clínica)" },
  "Triste|Aburrido|Inferior":     { que: "Sentirte por debajo o menos que los demás.", distinguir: "El sentimiento de inferioridad (Adler); en exceso puede volverse complejo.", fuente: "Sentimiento de inferioridad (Adler) · rango social (Gilbert)" },
  "Triste|Solo|Inadecuado":       { que: "Sentir que no estás a la altura o que no encajás.", distinguir: "Inadecuación: una cara del sentimiento de inferioridad.", fuente: "Sentimiento de inferioridad (Adler)" },
  "Triste|Deprimido|Miserable":   { que: "Tristeza angustiosa, normalmente prolongada.", distinguir: "Forma honda y sostenida del abatimiento.", fuente: "Atlas of Emotions (Ekman)" },
  "Triste|Avergonzado|Tonto":     { que: "Sentirte torpe o poco capaz.", distinguir: "Autocrítica: la tristeza se vuelve autodescalificación (cercana a la inferioridad).", fuente: "Autocrítica · inferioridad (Adler)" },
  "Triste|Culpable|Tímido":       { que: "Encogimiento y reparo ante los demás.", distinguir: "La timidez/inhibición social: la tristeza que se retrae del contacto.", fuente: "Psicología de la timidez" }
};
