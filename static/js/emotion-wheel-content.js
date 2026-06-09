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
  },

  // ── MEDIAS (36) — definición del matiz; función y manifestación heredan de la base ──
  // IRA
  "Ira|Odioso":      { que: "Hostilidad intensa y sostenida hacia alguien, con deseo de que le vaya mal.", distinguir: "Más dirigida a una persona y más duradera que la irritación pasajera; suele cargar rencor acumulado." },
  "Ira|Amenazado":   { que: "Sensación de que algo o alguien pone en riesgo lo que valorás (tu lugar, un vínculo, tu seguridad).", distinguir: "Mezcla ira con miedo: la ira aparece para defender lo amenazado. Si predomina el peligro y no la defensa, mirá Miedo." },
  "Ira|Desquiciado": { que: "Ira desbordada en la que sentís que perdés el control.", distinguir: "Es el extremo más intenso de la ira (furia), donde la reacción supera a la causa." },
  "Ira|Agresivo":    { que: "Impulso de avanzar contra el obstáculo o la persona, de atacar o confrontar.", distinguir: "Acentúa la tendencia a la acción y al ataque de la ira, más que el sentir interno." },
  "Ira|Frustrado":   { que: "Malestar por encontrar un obstáculo entre vos y lo que querés lograr.", distinguir: "Es la forma más cotidiana y de menor intensidad de la ira; nace del bloqueo de una meta, no tanto de una injusticia." },
  "Ira|Distante":    { que: "Te apartás y te cerrás, manteniendo distancia de los demás.", distinguir: "La ira acá se vuelve fría: en vez de confrontar, te retirás y desconfiás." },

  // DISGUSTO
  "Disgusto|Crítico":      { que: "Rechazo que se expresa juzgando o señalando defectos.", distinguir: "Disgusto canalizado en juicio hacia ideas o personas; más mental que visceral." },
  "Disgusto|Desaprobado":  { que: "Sensación de que algo no está bien y no merece tu aprobación.", distinguir: "Marca una desaprobación moral o de criterio, menos corporal que el asco físico." },
  "Disgusto|Decepcionado": { que: "Desencanto cuando algo o alguien resultó mucho peor de lo que esperabas.", distinguir: "Suma al disgusto la sensación de expectativa traicionada." },
  "Disgusto|Terrible":     { que: "Algo te resulta tan desagradable que lo encontrás repulsivo o detestable.", distinguir: "Forma intensa del disgusto: aversión fuerte, cercana al asco profundo." },
  "Disgusto|Evasivo":      { que: "Impulso de evitar o esquivar aquello que te desagrada.", distinguir: "Acentúa la conducta de alejamiento propia del disgusto, con duda o reticencia." },
  "Disgusto|Culpable":     { que: "Malestar por algo que hiciste (o creés haber hecho) que va contra tus valores.", distinguir: "Es disgusto dirigido a vos mismo; cuando se enfoca en cómo te ven los demás, se acerca a la vergüenza." },

  // TRISTEZA
  "Tristeza|Ansioso":     { que: "Inquietud y desasosiego ante algo que te sobrepasa o que anhelás y no llega.", distinguir: "Acá la tristeza se tiñe de anticipación; si domina una amenaza concreta, mirá Miedo." },
  "Tristeza|Abandonado":  { que: "Sensación de haber sido dejado de lado o excluido por otros.", distinguir: "La pérdida es de pertenencia o vínculo; duele el ser apartado." },
  "Tristeza|Desesperado": { que: "Tristeza profunda en la que sentís que no hay salida ni nada que puedas hacer.", distinguir: "Suma impotencia a la pérdida; es de las formas más intensas de la tristeza." },
  "Tristeza|Deprimido":   { que: "Abatimiento persistente, con sensación de vacío o de valer poco.", distinguir: "Como matiz es una tristeza pesada y sostenida; la depresión clínica es un trastorno aparte (ver base)." },
  "Tristeza|Solitario":   { que: "Sensación dolorosa de estar solo o desconectado, aunque haya gente alrededor.", distinguir: "La pérdida es de conexión; se diferencia de estar solo por elección, que no duele." },
  "Tristeza|Aburrido":    { que: "Desgano y falta de interés o estímulo.", distinguir: "Forma apagada y leve de la tristeza: no hay una pérdida puntual, sino ausencia de sentido o estímulo." },

  // FELICIDAD
  "Felicidad|Optimista": { que: "Disposición esperanzada: confiás en que las cosas pueden salir bien.", distinguir: "Felicidad orientada al futuro y a lo posible, más que al placer del presente." },
  "Felicidad|Íntimo":    { que: "Calidez y cercanía en el vínculo con alguien.", distinguir: "Felicidad de la conexión afectiva y la confianza compartida." },
  "Felicidad|Pacífico":  { que: "Calma serena, sensación de estar en paz.", distinguir: "Forma tranquila y de baja activación de la felicidad (la rama «en paz» del modelo de Willcox)." },
  "Felicidad|Poderoso":  { que: "Sensación de capacidad, fuerza y confianza en vos mismo.", distinguir: "Felicidad ligada a sentirte capaz y con agencia (la rama «poderoso» del modelo de Willcox)." },
  "Felicidad|Aceptado":  { que: "Sentirte valorado e incluido tal como sos.", distinguir: "Felicidad que viene del reconocimiento y la pertenencia." },
  "Felicidad|Orgulloso": { que: "Satisfacción por un logro propio o de alguien cercano.", distinguir: "Felicidad ligada al mérito y al valor personal." },

  // SORPRESA
  "Sorpresa|Jubiloso":    { que: "Alegría intensa y desbordante, casi eufórica.", distinguir: "Es la sorpresa que se transforma en júbilo: un giro inesperado que resulta muy positivo." },
  "Sorpresa|Efusivo":     { que: "Reacción muy expresiva y cargada de energía.", distinguir: "Sorpresa con activación alta que te impulsa a moverte o a expresarte." },
  "Sorpresa|Asombrado":   { que: "Quedar maravillado o pasmado ante algo que excede lo esperado.", distinguir: "Sorpresa intensa y sostenida frente a algo grandioso o difícil de creer." },
  "Sorpresa|Confundido":  { que: "Desconcierto: no entendés qué pasó o qué significa.", distinguir: "La sorpresa todavía no se resolvió; falta información para interpretarla." },
  "Sorpresa|Sorprendido": { que: "El núcleo de la emoción: reacción breve ante lo inesperado.", distinguir: "Es la forma directa de la base, antes de teñirse de algo positivo o negativo." },
  "Sorpresa|Interesado":  { que: "Atención atraída hacia algo novedoso que querés explorar.", distinguir: "La sorpresa que deriva en curiosidad: ya no alarma, invita a indagar." },

  // MIEDO
  "Miedo|Inseguro":  { que: "Sensación de no estar a la altura o de no poder sostener lo que viene.", distinguir: "Miedo difuso sobre tu propia capacidad o valía, más que ante un peligro concreto." },
  "Miedo|Asustado":  { que: "Miedo agudo ante un peligro percibido como inminente.", distinguir: "Es la forma directa e intensa del miedo, con fuerte impulso de huir." },
  "Miedo|Sumiso":    { que: "Te achicás y cedés ante otro por temor.", distinguir: "El miedo te lleva a someterte en vez de huir o enfrentar." },
  "Miedo|Rechazado": { que: "Temor a no ser aceptado o a ser excluido por los demás.", distinguir: "Miedo social: el peligro es la pérdida del vínculo o la pertenencia." },
  "Miedo|Humillado": { que: "Sentirte rebajado o expuesto ante otros.", distinguir: "Miedo mezclado con vergüenza: temés el juicio y quedar disminuido." },
  "Miedo|Herido":    { que: "Dolor por haber sido lastimado, faltado el respeto o ridiculizado.", distinguir: "El miedo acá protege de un daño relacional ya recibido o que temés repetir." }
};
