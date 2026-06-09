// Contenido psicológico por emoción — VERIFICADO contra fuentes, no inventar.
// Fuente base (6 emociones): Paul Ekman Group · Atlas of Emotions (atlasofemotions.org).
// Keyeado por path, mismo esquema que el hover: "Base", "Base|Media", "Base|Media|Específica".
// Campos: que (qué es) · sirve (para qué sirve) · manifiesta (cómo se manifiesta) ·
//         distinguir (disparadores y cómo distinguirla) · fuente.
// Las medias/específicas que falten heredan los campos de su base (ver ewContent()).
const EMOTION_CONTENT = {
  "Ira": {
    que: "Surge cuando algo bloquea una meta o cuando percibís un trato injusto. Va de la irritación leve a la furia.",
    sirve: "Señala un obstáculo o una injusticia y te moviliza a enfrentarlo o a poner un límite. Su mensaje de fondo es «apartate de mi camino».",
    manifiesta: "Calor, sudor, tensión muscular, mandíbula o puños apretados. La cara muestra cejas bajas y juntas, mirada fija y labios tensos. La voz toma filo y puede escalar al grito; el cuerpo se inclina hacia adelante.",
    distinguir: "La gatillan la interferencia deliberada con tus planes, la injusticia, la traición, el rechazo o ver que se rompe una regla. Puede mezclarse con miedo (a hacer daño) o disgusto (hacia quien la provoca).",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Disgusto": {
    que: "Sensación de aversión o rechazo hacia algo que te resulta repugnante. Va del desagrado leve al asco intenso.",
    sirve: "Te protege: te aleja de lo que podría enfermarte o contaminarte —comida en mal estado, toxinas, situaciones nocivas. También puede marcar transgresiones morales.",
    manifiesta: "Nariz arrugada (la señal más clara), náusea o impulso de vomitar, sonidos como «puaj». Tendés a girar la cabeza o el cuerpo para alejarte, o a taparte la nariz y la boca.",
    distinguir: "Lo gatillan los desechos corporales, lo podrido o enfermo, ciertas comidas (varía por cultura) y las transgresiones percibidas. Se diferencia del desprecio: el disgusto rechaza algo repugnante; el desprecio mira a alguien por encima del hombro.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Tristeza": {
    que: "Surge por la pérdida de alguien o algo importante. Va de la melancolía leve al duelo profundo.",
    sirve: "Pide ayuda o consuelo a los demás y te da tiempo para recuperarte. Comunica que algo valioso se perdió.",
    manifiesta: "Opresión en el pecho, pesadez en el cuerpo, ardor en la garganta, ojos llorosos. La cara levanta los extremos internos de las cejas (gesto difícil de fingir). El cuerpo se hunde, la mirada baja y se pierde tono muscular.",
    distinguir: "La gatillan el rechazo, las despedidas, la enfermedad o muerte de seres queridos y los cambios de vida. No es lo mismo que la depresión, que es persistente e interfiere con el día a día.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Felicidad": {
    que: "Familia de estados placenteros que va de la paz al éxtasis, normalmente por conexión o por placer sensorial.",
    sirve: "Le señala a los demás que no sos una amenaza y te motiva a conductas buenas para vos y para vincularte. Es un motor central de la motivación.",
    manifiesta: "Sensación de liviandad, energía, calidez o calma. Sonrisa genuina (de Duchenne, con «patas de gallo» en los ojos), suspiros, risa. Postura erguida y elevada, o quieta y relajada según la intensidad.",
    distinguir: "La gatillan los placeres de los sentidos, el humor, los logros propios o ajenos, la belleza y sentirte conectado (con personas, la naturaleza, una causa). La sonrisa social, a diferencia de la genuina, no marca los ojos.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Sorpresa": {
    que: "Reacción brevísima (segundos) ante algo súbito e inesperado.",
    sirve: "Enfoca tu atención para que averigües qué está pasando y si hay peligro o no.",
    manifiesta: "Ojos muy abiertos, cejas levantadas y curvas, mandíbula caída. Inhalación o gasto rápido; podés retroceder o llevarte las manos a la cara.",
    distinguir: "La gatillan sonidos fuertes o movimientos repentinos. Se parece al miedo, pero en la sorpresa las cejas son más curvas, los párpados más relajados y la mandíbula más abierta. (El sobresalto es un reflejo físico, no una emoción.)",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  },
  "Miedo": {
    que: "Surge ante la amenaza de un daño —físico, emocional o psicológico, real o imaginado.",
    sirve: "Te moviliza para enfrentar el peligro y mantenerte a salvo, disparando reacciones instintivas (luchar, huir o paralizarte) sin necesidad de pensarlas.",
    manifiesta: "Voz más aguda o tensa, frío, falta de aire, sudor, temblor o tensión muscular. La cara levanta las cejas más rectas y horizontales, abre mucho los párpados superiores (se ve el blanco) y estira los labios. El cuerpo huye o se congela.",
    distinguir: "Lo gatillan la oscuridad, las alturas, el rechazo social, ciertos animales o la muerte. Su intensidad depende de la gravedad del daño, su inminencia y tu capacidad de afrontarlo. Se distingue de la sorpresa por las cejas más rectas y los párpados más tensos.",
    fuente: "Paul Ekman Group · Atlas of Emotions"
  }
};
