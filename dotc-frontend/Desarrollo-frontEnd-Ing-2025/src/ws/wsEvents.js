// Lista centralizada de todos los eventos WS posibles en el sistema.
// Útil para autocompletado, validación, documentación y para mantener el contrato claro.

export const WSEVENTS = [
  // Eventos de cartas
  "CARD_DISCARDED",
  "CARD_PLAYED",  // cuando se juega una carta individual
  "CARDS_PLAYED", // cuando se juega un set de cartas
  "CARDS_NSF_DISCARDED", // cuando se descartan cartas NSF por efecto de Cards off the table
  "DECK_UPDATED",
  "DRAFT_UPDATED",
  "NEW_TURN",
  // Eventos de jugador
  "PLAYER_DREW_FROM_DECK",
  "PLAYER_JOINED",
  "PLAYER_LEFT",
  // Eventos de partida
  "GAME_CREATED",
  "GAME_CANCELLED",
  "GAME_STARTED",
  "GAME_UPDATED",
  // Eventos personalizados de mano
  "HAND_UPDATED",
  // Eventos 
  "ACTION_RESOLVED", 
  "PROMPT_REVEAL", // cuando un jugador es OBLIGADO a elegir uno de sus secretos para revelarlo
  // Eventos de secretos
  "SECRET_REVEALED",
  "SECRET_STOLEN",
  "SECRET_HIDDEN",

  "VOTE_STARTED",
  "SD_APPLIED",
  "SD_REMOVED",
  "SET_STOLEN",
  "GAME_OVER",
  "TRADE_REQUESTED",
];
