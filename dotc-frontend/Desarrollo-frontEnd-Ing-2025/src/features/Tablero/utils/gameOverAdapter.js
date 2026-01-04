/**
 * Normaliza eventos de fin de partida desde diferentes formatos de WebSocket
 * a un formato interno consistente.
 * 
 * Soporta:
 * - Evento actual: SECRET_REVEALED con role MURDERER
 * - Evento futuro: GAME_OVER con reason y jugadores detallados
 */
export function normalizeGameOverEvent(wsPayload, players = []) {
  // Caso actual: detectar revelación del asesino
  if (wsPayload?.event === "SECRET_REVEALED" && wsPayload?.role === "MURDERER") {
    const murdererId = wsPayload.player_id;
    const murderer = players.find(p => p.player_id === murdererId);
    
    return {
      reason: "INNOCENTS_WIN",
      murderer: { 
        player_id: murdererId, 
        name: murderer?.player_name || "Desconocido" 
      },
      accomplice: null,
      innocents: players.filter(p => p.player_id !== murdererId)
    };
  }

  // Caso futuro: evento GAME_OVER del backend
  if (wsPayload?.event === "GAME_OVER") {
    return {
      reason: wsPayload.reason,
      murderer: wsPayload.murderer,
      accomplice: wsPayload.accomplice || null,
      innocents: wsPayload.innocents || []
    };
  }

  return null;
}
