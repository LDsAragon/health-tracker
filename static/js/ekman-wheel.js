// Rueda Ekman — basada 100% en el Atlas of Emotions (atlasofemotions.org).
// 5 emociones, 2 niveles (emoción → estados). En inglés con traducción al español.
// El Atlas NO incluye "Surprise", por eso no aparece.
const EKMAN_WHEEL = {
  "Anger": {
    en: "Anger", es: "Ira", color: "#e2403b",
    states: [
      { en: "Annoyance",        es: "Irritación" },
      { en: "Frustration",      es: "Frustración" },
      { en: "Exasperation",     es: "Exasperación" },
      { en: "Argumentativeness", es: "Beligerancia" },
      { en: "Bitterness",       es: "Amargura" },
      { en: "Vengefulness",     es: "Vengatividad" },
      { en: "Fury",             es: "Furia" }
    ]
  },
  "Fear": {
    en: "Fear", es: "Miedo", color: "#7c5cbf",
    states: [
      { en: "Trepidation", es: "Aprensión" },
      { en: "Nervousness", es: "Nerviosismo" },
      { en: "Anxiety",     es: "Ansiedad" },
      { en: "Dread",       es: "Pavor" },
      { en: "Desperation", es: "Desesperación" },
      { en: "Panic",       es: "Pánico" },
      { en: "Horror",      es: "Horror" },
      { en: "Terror",      es: "Terror" }
    ]
  },
  "Sadness": {
    en: "Sadness", es: "Tristeza", color: "#3b6fb5",
    states: [
      { en: "Disappointment", es: "Decepción" },
      { en: "Discouragement", es: "Desánimo" },
      { en: "Distraughtness", es: "Turbación" },
      { en: "Resignation",    es: "Resignación" },
      { en: "Helplessness",   es: "Impotencia" },
      { en: "Hopelessness",   es: "Desesperanza" },
      { en: "Misery",         es: "Desdicha" },
      { en: "Despair",        es: "Desolación" },
      { en: "Grief",          es: "Duelo" },
      { en: "Sorrow",         es: "Pesar" },
      { en: "Anguish",        es: "Angustia" }
    ]
  },
  "Disgust": {
    en: "Disgust", es: "Asco", color: "#4f9d69",
    states: [
      { en: "Dislike",    es: "Desagrado" },
      { en: "Aversion",   es: "Aversión" },
      { en: "Distaste",   es: "Disgusto" },
      { en: "Repugnance", es: "Repugnancia" },
      { en: "Revulsion",  es: "Repulsión" },
      { en: "Abhorrence", es: "Aborrecimiento" },
      { en: "Loathing",   es: "Execración" }
    ]
  },
  "Enjoyment": {
    en: "Enjoyment", es: "Disfrute", color: "#e6b53c",
    states: [
      { en: "Sensory pleasure", es: "Placer sensorial" },
      { en: "Rejoicing",        es: "Regocijo" },
      { en: "Compassion/joy",   es: "Compasión" },
      { en: "Amusement",        es: "Diversión" },
      { en: "Schadenfreude",    es: "Regodeo" },
      { en: "Relief",           es: "Alivio" },
      { en: "Peace",            es: "Paz" },
      { en: "Pride",            es: "Orgullo" },
      { en: "Fiero",            es: "Fiero" },
      { en: "Naches",           es: "Naches" },
      { en: "Wonder",           es: "Asombro" },
      { en: "Excitement",       es: "Entusiasmo" },
      { en: "Ecstasy",          es: "Éxtasis" }
    ]
  }
};
