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
  "Ira|Odioso":      { que: "Animadversión intensa hacia alguien; en el uso corriente, estar arisco y de muy mal carácter.", distinguir: "Más dirigida a una persona y más duradera que la irritación pasajera; suele cargar rencor acumulado.", fdef: "Wikcionario" },
  "Ira|Amenazado":   { que: "Sentir que alguien da a entender que va a hacerte un mal, o que algo representa un peligro para lo que valorás.", distinguir: "Mezcla ira con miedo: la ira aparece para defender lo amenazado. Si predomina el peligro y no la defensa, mirá Miedo.", fdef: "Wikcionario" },
  "Ira|Desquiciado": { que: "Sacado de quicio: tan trastornado por la ira que perdés el equilibrio y el control.", distinguir: "Es el extremo más intenso de la ira (furia), donde la reacción supera a la causa.", fdef: "Wikcionario" },
  "Ira|Agresivo":    { que: "Con agresividad, como si fueras a agredir o arremeter contra alguien.", distinguir: "Acentúa la tendencia a la acción y al ataque de la ira, más que el sentir interno.", fdef: "Wikcionario" },
  "Ira|Frustrado":   { que: "Malestar por no lograr superar un obstáculo que se interpone con lo que querés, pese a intentarlo.", distinguir: "Es la forma más cotidiana y de menor intensidad de la ira; nace del bloqueo de una meta, no tanto de una injusticia.", fdef: "Wikcionario · Atlas of Emotions" },
  "Ira|Distante":    { que: "Que evita la comunicación, el trato y la cercanía emocional; te mantenés alejado.", distinguir: "La ira acá se vuelve fría: en vez de confrontar, te retirás y desconfiás.", fdef: "Wikcionario" },

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
  "Miedo|Herido":    { que: "Dolor por haber sido lastimado, faltado el respeto o ridiculizado.", distinguir: "El miedo acá protege de un daño relacional ya recibido o que temés repetir." },

  // ── ESPECÍFICAS (72) — definición + distinción frente a su hermana del par ──
  // IRA
  "Ira|Odioso|Resentido":        { que: "Que siente resentimiento: guardás dolor o enojo por algo que viviste como injusto.", distinguir: "A diferencia de «violado», el daño quedó macerando en el tiempo.", fdef: "Wikcionario" },
  "Ira|Odioso|Violado":          { que: "Sentir que cruzaron tus límites o pasaron por encima de tus derechos.", distinguir: "El foco está en la transgresión de tu espacio o derechos, más que en el rencor acumulado." },
  "Ira|Amenazado|Celoso":        { que: "Que tiene celos: temés perder a alguien querido frente a un tercero.", distinguir: "Hay un rival concreto; mezcla ira con miedo a la pérdida.", fdef: "Wikcionario" },
  "Ira|Amenazado|Inseguro":      { que: "Que siente que le falta seguridad o respaldo, sin confianza firme en su posición.", distinguir: "No hay un rival puntual como en los celos; es una falta de respaldo difusa.", fdef: "Wikcionario" },
  "Ira|Desquiciado|Enfurecido":  { que: "Lleno de furia, con la ira encendida al máximo.", distinguir: "Furia caliente y explosiva.", fdef: "Wikcionario" },
  "Ira|Desquiciado|Rabioso":     { que: "Colérico, con un enfado muy grande y vehemente.", distinguir: "Aún más desbordada que «enfurecido»: cuesta razonar.", fdef: "Wikcionario" },
  "Ira|Agresivo|Provocado":      { que: "Incitado o pinchado por algo o alguien hasta reaccionar.", distinguir: "La agresividad responde a un estímulo externo puntual.", fdef: "Wikcionario" },
  "Ira|Agresivo|Hostil":         { que: "Que se comporta como enemigo o en contra, en actitud de antagonismo.", distinguir: "Es una disposición a atacar más estable, no una reacción puntual.", fdef: "Wikcionario" },
  "Ira|Frustrado|Enfadado":      { que: "Contrariado o disgustado por algo que salió mal o te molestó.", distinguir: "Más marcado y expresado que la irritación.", fdef: "Wikcionario" },
  "Ira|Frustrado|Irritado":      { que: "De mal humor por una molestia; enojo leve y superficial.", distinguir: "Fastidio de baja intensidad, fácil de gatillar y de pasar.", fdef: "Wikcionario · Atlas of Emotions" },
  "Ira|Distante|Retraído":       { que: "De poco contacto social: te recogés y rehuís el trato.", distinguir: "El acento está en el repliegue.", fdef: "Wikcionario" },
  "Ira|Distante|Sospechoso":     { que: "Suspicaz: desconfiás y esperás malas intenciones en el otro.", distinguir: "El acento está en la desconfianza, no solo en alejarte.", fdef: "Wikcionario" },

  // DISGUSTO
  "Disgusto|Crítico|Sarcástico":       { que: "Rechazo expresado con ironía mordaz.", distinguir: "Ataca con humor hiriente." },
  "Disgusto|Crítico|Escéptico":        { que: "Duda y desconfianza ante lo que te presentan.", distinguir: "Rechazo desde la incredulidad, no desde la burla." },
  "Disgusto|Desaprobado|Sentencioso":  { que: "Juzgás con dureza, como dictando sentencia.", distinguir: "Desaprobación moralizante." },
  "Disgusto|Desaprobado|Aborrecido":   { que: "Rechazo profundo hacia algo que no soportás.", distinguir: "Más visceral y total que el juicio sentencioso." },
  "Disgusto|Decepcionado|Repugnante":  { que: "Algo que te da asco directo.", distinguir: "Aversión física inmediata." },
  "Disgusto|Decepcionado|Rebelado":    { que: "Te alzás en contra de algo que te resulta inaceptable.", distinguir: "El disgusto se vuelve rechazo activo y oposición." },
  "Disgusto|Terrible|Repulsivo":       { que: "Algo que te expulsa, que no podés ni mirar.", distinguir: "Aversión que empuja a alejarte." },
  "Disgusto|Terrible|Detestable":      { que: "Algo que merece tu desprecio absoluto.", distinguir: "El rechazo es un juicio de valor fuerte sobre algo o alguien." },
  "Disgusto|Evasivo|Aversivo":         { que: "Tendencia a rechazar y evitar.", distinguir: "El acento está en el rechazo activo." },
  "Disgusto|Evasivo|Indeciso":         { que: "No te decidís, oscilás por reticencia.", distinguir: "El acento está en la duda que frena, más que en el rechazo." },
  "Disgusto|Culpable|Atormentado":     { que: "Culpa que te carcome y no te deja en paz.", distinguir: "Sufrimiento interno intenso por lo hecho." },
  "Disgusto|Culpable|Avergonzado":     { que: "Malestar por cómo quedaste ante los demás.", distinguir: "El foco está en la mirada ajena, no solo en tu conciencia." },

  // TRISTEZA
  "Tristeza|Ansioso|Anhelante":        { que: "Deseo intenso de algo que todavía no llega.", distinguir: "La inquietud nace de la espera y el querer." },
  "Tristeza|Ansioso|Abrumado":         { que: "Sentir que la situación te supera y no das abasto.", distinguir: "La inquietud nace del exceso de demandas." },
  "Tristeza|Abandonado|Ignorado":      { que: "Sentir que no te registran ni te tienen en cuenta.", distinguir: "Te dejan de lado por indiferencia." },
  "Tristeza|Abandonado|Discriminado":  { que: "Sentir que te tratan distinto y peor por lo que sos.", distinguir: "El rechazo es activo y por una característica tuya." },
  "Tristeza|Desesperado|Impotente":    { que: "Sentir que no podés hacer nada para cambiar lo que pasa.", distinguir: "El foco está en la falta de poder." },
  "Tristeza|Desesperado|Vulnerable":   { que: "Sentirte expuesto y sin protección.", distinguir: "El foco está en la fragilidad ante el daño." },
  "Tristeza|Deprimido|Inferior":       { que: "Sentirte menos que los demás.", distinguir: "El abatimiento se centra en la comparación y la autoestima." },
  "Tristeza|Deprimido|Vacío":          { que: "Sensación de hueco interno, sin sentido ni energía.", distinguir: "El abatimiento se centra en la ausencia, no en la comparación." },
  "Tristeza|Solitario|Abandonado":     { que: "Sentir que te dejaron solo quienes deberían estar.", distinguir: "Hay otros que se fueron o fallaron." },
  "Tristeza|Solitario|Apartado":       { que: "Sentirte al margen, fuera del grupo.", distinguir: "Es estar afuera, sin necesariamente un abandono activo." },
  "Tristeza|Aburrido|Apático":         { que: "Falta de ganas y de energía para hacer algo.", distinguir: "El desgano apunta a la acción." },
  "Tristeza|Aburrido|Indiferente":     { que: "Nada te moviliza ni te importa demasiado.", distinguir: "El desgano apunta al interés y el afecto." },

  // FELICIDAD
  "Felicidad|Optimista|Inspirado":   { que: "Sentirte movido a crear o a actuar con entusiasmo.", distinguir: "Hay un impulso creativo hacia adelante." },
  "Felicidad|Optimista|Receptivo":   { que: "Abierto a recibir ideas, vínculos y experiencias.", distinguir: "Es apertura, más que impulso a crear." },
  "Felicidad|Íntimo|Juguetón":       { que: "Disfrute liviano y lúdico en el vínculo.", distinguir: "La cercanía se vive con juego y humor." },
  "Felicidad|Íntimo|Sensible":       { que: "Apertura emocional y delicadeza con el otro.", distinguir: "La cercanía se vive desde la ternura y la receptividad." },
  "Felicidad|Pacífico|Esperanzado":  { que: "Confianza serena en que todo va a estar bien.", distinguir: "La paz mira al futuro con esperanza." },
  "Felicidad|Pacífico|Amoroso":      { que: "Sentir y dar cariño desde la calma.", distinguir: "La paz se vive en el afecto presente." },
  "Felicidad|Poderoso|Provocativo":  { que: "Seguridad que se anima a desafiar o estimular.", distinguir: "La fuerza se expresa retando o incitando." },
  "Felicidad|Poderoso|Valiente":     { que: "Coraje para enfrentar lo difícil.", distinguir: "La fuerza se expresa afrontando el miedo." },
  "Felicidad|Aceptado|Realizado":    { que: "Sentir que cumpliste y estás pleno.", distinguir: "El valor viene de logros propios." },
  "Felicidad|Aceptado|Respetado":    { que: "Sentir que los demás valoran lo que sos y hacés.", distinguir: "El valor viene del reconocimiento ajeno." },
  "Felicidad|Orgulloso|Confiado":    { que: "Seguridad en tus capacidades.", distinguir: "El orgullo mira hacia adentro, a tu confianza." },
  "Felicidad|Orgulloso|Importante":  { que: "Sentir que contás y que tu presencia pesa.", distinguir: "El orgullo mira al lugar que ocupás ante otros." },

  // SORPRESA
  "Sorpresa|Jubiloso|Liberado":         { que: "Alivio gozoso de haberte sacado un peso de encima.", distinguir: "El júbilo viene de soltar una carga." },
  "Sorpresa|Jubiloso|Eufórico":         { que: "Alegría altísima, exaltada.", distinguir: "El júbilo en su punto más intenso." },
  "Sorpresa|Efusivo|Enérgico":          { que: "Lleno de vitalidad y empuje.", distinguir: "La energía es positiva y canalizada." },
  "Sorpresa|Efusivo|Inquieto":          { que: "Activación que no para quieta.", distinguir: "La energía es agitada, difícil de contener." },
  "Sorpresa|Asombrado|Pasmado":         { que: "Quedar paralizado por el asombro.", distinguir: "El asombro te deja sin reacción." },
  "Sorpresa|Asombrado|Atónito":         { que: "Quedar mudo, sin poder creerlo.", distinguir: "El asombro te deja sin palabras." },
  "Sorpresa|Confundido|Perplejo":       { que: "Desconcierto total: no sabés qué pensar.", distinguir: "La confusión es intelectual, ante lo incomprensible." },
  "Sorpresa|Confundido|Desilusionado":  { que: "La sorpresa resultó en decepción.", distinguir: "La confusión vira a negativo: no era lo que creías." },
  "Sorpresa|Sorprendido|Consternado":   { que: "Sorpresa que cae mal y te deja afligido.", distinguir: "El giro inesperado es negativo y te golpea." },
  "Sorpresa|Sorprendido|Impresionado":  { que: "Sorpresa que te marca y te deja impactado.", distinguir: "El impacto es fuerte, sin la aflicción de «consternado»." },
  "Sorpresa|Interesado|Curioso":        { que: "Ganas de saber más y explorar.", distinguir: "El interés busca conocer." },
  "Sorpresa|Interesado|Entretenido":    { que: "Disfrute de estar atento y pasarla bien.", distinguir: "El interés se vive como disfrute del momento." },

  // MIEDO
  "Miedo|Inseguro|Devastado":        { que: "Sentirte arrasado, sin fuerzas frente a lo que pasó.", distinguir: "El miedo a no poder se vuelve derrumbe." },
  "Miedo|Inseguro|Apenado":          { que: "Pena y encogimiento por sentirte en falta o expuesto.", distinguir: "Forma más leve y triste de la inseguridad." },
  "Miedo|Asustado|Aterrado":         { que: "Miedo extremo que te paraliza.", distinguir: "Terror en su punto máximo." },
  "Miedo|Asustado|Espantado":        { que: "Susto fuerte y repentino que te hace retroceder.", distinguir: "Reacción de rechazo y huida ante algo horroroso." },
  "Miedo|Sumiso|Pobre":              { que: "Sentirte disminuido, sin recursos frente al otro.", distinguir: "La sumisión nace de sentirte carente." },
  "Miedo|Sumiso|Inferior":           { que: "Sentirte por debajo de los demás.", distinguir: "La sumisión nace de la comparación desfavorable." },
  "Miedo|Rechazado|Indignado":       { que: "Enojo por sentir un rechazo injusto.", distinguir: "El miedo al rechazo reacciona con protesta." },
  "Miedo|Rechazado|Insignificante":  { que: "Sentir que no valés ni contás para nadie.", distinguir: "El rechazo se vive como quedar anulado." },
  "Miedo|Humillado|Inadecuado":      { que: "Sentir que no encajás o que no das la talla.", distinguir: "La humillación se centra en no estar a la altura." },
  "Miedo|Humillado|Perturbado":      { que: "Quedar trastornado o removido por lo vivido.", distinguir: "La humillación deja una alteración interna fuerte." },
  "Miedo|Herido|Irrespetado":        { que: "Sentir que te trataron sin la consideración que merecés.", distinguir: "El daño es a tu dignidad." },
  "Miedo|Herido|Ridiculizado":       { que: "Sentir que te pusieron en ridículo ante otros.", distinguir: "El daño es la burla pública." }
};
